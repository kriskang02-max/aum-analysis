"""운용사별·비교 화면 분석 요약 문구 생성."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.formatting import fmt_jo_eok

TYPE_LABELS = {"공모": "공모펀드", "사모": "사모펀드", "일임": "투자일임"}
TYPE_ORDER = ["공모", "사모", "일임"]
_SUMMARY_TITLE = "#### 분석 요약"


@dataclass
class _TypePeriod:
    label: str
    base: float | None
    compare: float | None
    delta: float | None
    delta_pct: float | None
    trend: str


def _norm(ts) -> pd.Timestamp:
    return pd.Timestamp(ts).normalize()


def _aum(part: pd.DataFrame, date: pd.Timestamp) -> float | None:
    d = _norm(date)
    mask = part["기준일"].apply(lambda x: _norm(x) == d)
    vals = part.loc[mask, "수탁고"]
    if vals.empty or pd.isna(vals.iloc[0]):
        return None
    return float(vals.iloc[0])


def _pct(delta: float | None, base: float | None) -> float | None:
    if delta is None or base is None or base == 0:
        return None
    return delta / base * 100


def _trend(part: pd.DataFrame) -> str:
    dates = sorted(part["기준일"].unique(), key=lambda x: _norm(x))
    if len(dates) < 2:
        return "관측 구간이 짧아 추세 해석은 제한적입니다"
    v0, v1 = _aum(part, dates[0]), _aum(part, dates[-1])
    if v0 is None or v1 is None or v0 == 0:
        return "기간 중 일부 시점 결측으로 추세는 참고용입니다"
    chg = (v1 - v0) / v0
    if chg > 0.03:
        return "기간 내 우상향 흐름입니다"
    if chg < -0.03:
        return "기간 내 우하향 흐름입니다"
    return "기간 내 방향성은 크지 않고 보합권입니다"


def _type_period(
    sub: pd.DataFrame, fund_type: str, base_date: pd.Timestamp, compare_date: pd.Timestamp
) -> _TypePeriod | None:
    part = sub[sub["유형"] == fund_type]
    if part.empty:
        return None
    base_v, cmp_v = _aum(part, base_date), _aum(part, compare_date)
    delta = None if base_v is None or cmp_v is None else cmp_v - base_v
    return _TypePeriod(
        label=TYPE_LABELS.get(fund_type, fund_type),
        base=base_v,
        compare=cmp_v,
        delta=delta,
        delta_pct=_pct(delta, base_v),
        trend=_trend(part),
    )


def _signed_pct(p: float | None) -> str:
    if p is None:
        return ""
    return f" ({p:+.1f}%)"


def _company_delta_line(tp: _TypePeriod) -> str:
    if tp.delta is None:
        return f"**{tp.label}** · 증감 산출 불가"
    amt = fmt_jo_eok(tp.delta, signed=True)
    return f"**{tp.label}** · **{amt}**{_signed_pct(tp.delta_pct)}"


def _compare_type_line(
    label: str,
    company_a: str,
    company_b: str,
    ca: float,
    cb: float,
    gap: float,
    gap_chg: float | None,
) -> str:
    """유형 1줄: 비교일 수탁고 + 격차·기간 변화."""
    aum = (
        f"**{company_a}** {fmt_jo_eok(ca)} / **{company_b}** {fmt_jo_eok(cb)}"
    )
    if gap_chg is None:
        gap_txt = (
            f"격차 **{fmt_jo_eok(gap, signed=True)}** (A−B) · 기간 변화 산출 불가"
        )
    else:
        gap_txt = (
            f"격차 **{fmt_jo_eok(gap, signed=True)}** (A−B) · "
            f"기간 변화 **{fmt_jo_eok(gap_chg, signed=True)}**"
        )
    return f"{label}: {aum} · {gap_txt}"


def _company_total_at(
    sub: pd.DataFrame, date: pd.Timestamp, types_to_sum: list[str] | None = None
) -> float | None:
    """공모+사모+일임 등 지정 유형 수탁고 합계."""
    d = _norm(date)
    fund_types = types_to_sum or TYPE_ORDER
    total = 0.0
    found = False
    for fund_type in fund_types:
        part = sub[sub["유형"] == fund_type]
        part = part[part["기준일"].map(_norm) == d]
        if part.empty:
            continue
        total += float(part["수탁고"].sum())
        found = True
    return total if found else None


def _compare_total_line(
    company_a: str,
    company_b: str,
    sub_a: pd.DataFrame,
    sub_b: pd.DataFrame,
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
) -> str:
    """전체 = 공모 + 사모 + 투자일임 합계."""
    ca = _company_total_at(sub_a, compare_date, TYPE_ORDER)
    cb = _company_total_at(sub_b, compare_date, TYPE_ORDER)
    if ca is None or cb is None:
        return "전체: 비교일 수치 미확보"

    gap = ca - cb
    base_a = _company_total_at(sub_a, base_date, TYPE_ORDER)
    base_b = _company_total_at(sub_b, base_date, TYPE_ORDER)
    gap_chg = None if base_a is None or base_b is None else gap - (base_a - base_b)
    return _compare_type_line("전체", company_a, company_b, ca, cb, gap, gap_chg)


def build_company_ceo_summary(
    company: str,
    sub: pd.DataFrame,
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
    types: list[str],
) -> str:
    """단일 운용사 — 유형별 증감 3줄(증감액·증감률)."""
    if _norm(base_date) == _norm(compare_date):
        return (
            f"{_SUMMARY_TITLE}\n\n"
            "기준일과 비교일이 동일하여 증감 요약은 생략합니다. "
            "비교일을 변경해 주세요."
        )

    lines: list[str] = []
    for t in TYPE_ORDER:
        if t not in types:
            continue
        tp = _type_period(sub, t, base_date, compare_date)
        if tp is None:
            lines.append(f"**{TYPE_LABELS[t]}** · 데이터 없음")
            continue
        if tp.compare is None:
            lines.append(f"**{tp.label}** · 비교일 수치 미확보")
            continue
        lines.append(_company_delta_line(tp))

    body = "\n\n".join(lines) if lines else "표시 가능한 유형 데이터가 없습니다."
    return f"{_SUMMARY_TITLE}\n\n{body}"


def build_compare_ceo_summary(
    company_a: str,
    company_b: str,
    agg: pd.DataFrame,
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
    types: list[str],
) -> str:
    """두 운용사 — 유형별 비교일 수탁고·격차 변화(유형당 1줄)."""
    if company_a == company_b:
        return f"{_SUMMARY_TITLE}\n\n비교를 위해 서로 다른 운용사를 선택해 주세요."

    if _norm(base_date) == _norm(compare_date):
        return (
            f"{_SUMMARY_TITLE}\n\n"
            "기준일과 비교일이 동일하여 격차 변화 요약은 생략합니다."
        )

    sub_a = agg[agg["운용사"] == company_a]
    sub_b = agg[agg["운용사"] == company_b]

    lines: list[str] = [
        _compare_total_line(company_a, company_b, sub_a, sub_b, base_date, compare_date)
    ]
    for t in TYPE_ORDER:
        if t not in types:
            continue
        pa, pb = sub_a[sub_a["유형"] == t], sub_b[sub_b["유형"] == t]
        if pa.empty and pb.empty:
            lines.append(f"{TYPE_LABELS[t]}: 양사 데이터 없음")
            continue

        ta, tb = _type_period(pa, t, base_date, compare_date), _type_period(
            pb, t, base_date, compare_date
        )
        if ta is None or tb is None:
            lines.append(f"{TYPE_LABELS[t]}: 비교 가능 수치 부족")
            continue

        ca, cb = ta.compare, tb.compare
        if ca is None or cb is None:
            lines.append(f"{ta.label}: 비교일 수치 미확보")
            continue

        gap = ca - cb
        gap_base = None
        if ta.base is not None and tb.base is not None:
            gap_base = ta.base - tb.base

        gap_chg = gap - gap_base if gap_base is not None else None
        lines.append(
            _compare_type_line(
                ta.label, company_a, company_b, ca, cb, gap, gap_chg
            )
        )

    body = "\n".join(lines) if lines else "비교 가능 유형이 없습니다."
    return f"{_SUMMARY_TITLE}\n\n{body}"
