"""최신 거래일 vs 직전 거래일 일별 운용사 수탁고 비교."""

from __future__ import annotations

import pandas as pd

from src.formatting import fmt_jo_eok

TYPE_ORDER = ["공모", "사모", "일임"]
TYPE_LABELS = {"공모": "공모펀드", "사모": "사모펀드", "일임": "투자일임"}


def _norm(ts) -> pd.Timestamp:
    return pd.Timestamp(ts).normalize()


def sorted_dates(agg: pd.DataFrame) -> list[pd.Timestamp]:
    return sorted({_norm(d) for d in agg["기준일"].unique()})


def daily_pair_dates(agg: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """데이터에 존재하는 직전일·최신일."""
    dates = sorted_dates(agg)
    if len(dates) < 2:
        return None
    return dates[-2], dates[-1]


def _company_totals_at(agg: pd.DataFrame, date: pd.Timestamp) -> pd.Series:
    d = _norm(date)
    snap = agg[agg["기준일"].apply(_norm) == d]
    if snap.empty:
        return pd.Series(dtype=float)
    return snap.groupby("운용사")["수탁고"].sum()


def build_daily_company_metrics(
    agg: pd.DataFrame, prev_date: pd.Timestamp, latest_date: pd.Timestamp
) -> pd.DataFrame:
    """운용사별 직전·최신 합계 및 일별 증감 (유형 합산)."""
    prev_s = _company_totals_at(agg, prev_date)
    latest_s = _company_totals_at(agg, latest_date)
    companies = sorted(set(prev_s.index) | set(latest_s.index))

    rows: list[dict] = []
    for name in companies:
        prev_v = float(prev_s.get(name, 0.0) or 0.0)
        latest_v = float(latest_s.get(name, 0.0) or 0.0)
        delta = latest_v - prev_v
        rate = (delta / prev_v * 100) if prev_v else None
        rows.append(
            {
                "운용사": name,
                "직전_수탁고": prev_v,
                "최신_수탁고": latest_v,
                "증감": delta,
                "증감률": rate,
                "절대증감": abs(delta),
                "변동없음": delta == 0,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values(
        ["절대증감", "증감", "운용사"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    df.insert(0, "순위", range(1, len(df) + 1))
    return df


def build_daily_type_metrics(
    agg: pd.DataFrame, prev_date: pd.Timestamp, latest_date: pd.Timestamp
) -> pd.DataFrame:
    """유형별 직전·최신·증감."""
    rows: list[dict] = []
    for t in TYPE_ORDER:
        part = agg[agg["유형"] == t]
        if part.empty:
            continue
        prev_v = _company_totals_at(part, prev_date).sum()
        latest_v = _company_totals_at(part, latest_date).sum()
        delta = latest_v - prev_v
        rows.append(
            {
                "유형": t,
                "유형명": TYPE_LABELS.get(t, t),
                "직전_수탁고": prev_v,
                "최신_수탁고": latest_v,
                "증감": delta,
                "증감률": (delta / prev_v * 100) if prev_v else None,
            }
        )
    return pd.DataFrame(rows)


def format_daily_table(
    metrics: pd.DataFrame,
    prev_date: pd.Timestamp,
    latest_date: pd.Timestamp,
) -> pd.DataFrame:
    if metrics.empty:
        return metrics

    prev_lbl = _norm(prev_date).strftime("%y/%m/%d")
    latest_lbl = _norm(latest_date).strftime("%y/%m/%d")
    out = metrics.copy()
    out[f"{prev_lbl} 합계"] = out["직전_수탁고"].map(fmt_jo_eok)
    out[f"{latest_lbl} 합계"] = out["최신_수탁고"].map(fmt_jo_eok)
    out["일별 증감"] = out["증감"].map(lambda v: fmt_jo_eok(v, signed=True))
    out["증감률"] = out["증감률"].map(
        lambda v: f"{v:+.2f}%" if v is not None and pd.notna(v) else "-"
    )
    out["변동"] = out["변동없음"].map(lambda x: "없음" if x else "있음")
    return out[
        [
            "순위",
            "운용사",
            f"{prev_lbl} 합계",
            f"{latest_lbl} 합계",
            "일별 증감",
            "증감률",
            "변동",
        ]
    ]


def daily_summary_counts(metrics: pd.DataFrame) -> dict[str, int]:
    if metrics.empty:
        return {"up": 0, "down": 0, "flat": 0, "total": 0}
    up = int((metrics["증감"] > 0).sum())
    down = int((metrics["증감"] < 0).sum())
    flat = int(metrics["변동없음"].sum())
    return {"up": up, "down": down, "flat": flat, "total": len(metrics)}
