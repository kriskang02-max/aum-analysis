"""보고자료 탭 - 정해진 포맷의 보고용 테이블."""

from __future__ import annotations

import pandas as pd

from src.formatting import fmt_jo_eok

TYPE_ORDER = ["공모", "사모", "일임"]
TYPE_LABELS = {"공모": "공모펀드", "사모": "사모펀드", "일임": "투자일임"}

DEFAULT_COMPARE_LAG_DAYS = 7


def _norm(ts) -> pd.Timestamp:
    return pd.Timestamp(ts).normalize()


def sorted_dates(df: pd.DataFrame) -> list[pd.Timestamp]:
    return sorted({_norm(d) for d in df["기준일"].unique()})


def default_base_date(dates: list[pd.Timestamp], compare_date: pd.Timestamp) -> pd.Timestamp:
    """비교일에서 7일 전 이하 중 가장 가까운(가장 늦은) 가용 기준일."""
    if not dates:
        return compare_date
    target = _norm(compare_date) - pd.Timedelta(days=DEFAULT_COMPARE_LAG_DAYS)
    candidates = [d for d in dates if d <= target]
    if candidates:
        return candidates[-1]
    earlier = [d for d in dates if d < _norm(compare_date)]
    if earlier:
        return earlier[-1]
    return dates[0]


def _match_company(df: pd.DataFrame, names: tuple[str, ...]) -> pd.Series:
    if not names:
        return pd.Series([False] * len(df), index=df.index)
    mask = df["운용사"].isin(names)
    return mask


def _aum_total(
    df: pd.DataFrame,
    date: pd.Timestamp,
    *,
    company_names: tuple[str, ...] | None,
    fund_type: str | None,
) -> float:
    d = _norm(date)
    mask = df["기준일"].apply(_norm) == d
    part = df[mask]
    if company_names is not None:
        part = part[_match_company(part, company_names)]
    if fund_type is not None:
        part = part[part["유형"] == fund_type]
    if part.empty:
        return 0.0
    return float(part["수탁고"].sum())


def build_weekly_aum_report(
    df: pd.DataFrame,
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
    *,
    row_specs: list[tuple[str, tuple[str, ...] | None]] | None = None,
) -> pd.DataFrame:
    """주간 수탁고 변동 - 행: 전체/신한/KB, 열: 전체/공모/사모/일임 (MultiIndex 행: 운용사 × 구분)."""
    if row_specs is None:
        row_specs = [
            ("전체", None),
            ("신한자산운용", ("신한자산운용",)),
            ("KB자산운용", ("KB자산운용", "케이비자산운용")),
        ]

    col_specs: list[tuple[str, str | None]] = [
        ("전체", None),
        ("공모펀드", "공모"),
        ("사모펀드", "사모"),
        ("투자일임", "일임"),
    ]

    metric_keys = ["기준일 수탁고", "비교일 수탁고", "증감", "증감률"]
    rows: list[dict] = []

    for row_label, company_names in row_specs:
        bucket: dict[str, dict[str, float | None]] = {m: {} for m in metric_keys}
        for col_label, fund_type in col_specs:
            base_v = _aum_total(
                df, base_date, company_names=company_names, fund_type=fund_type
            )
            cmp_v = _aum_total(
                df, compare_date, company_names=company_names, fund_type=fund_type
            )
            delta = cmp_v - base_v
            rate = (delta / base_v * 100) if base_v else None
            bucket["기준일 수탁고"][col_label] = base_v
            bucket["비교일 수탁고"][col_label] = cmp_v
            bucket["증감"][col_label] = delta
            bucket["증감률"][col_label] = rate

        for metric in metric_keys:
            row = {"운용사": row_label, "구분": metric}
            for col_label, _ in col_specs:
                row[col_label] = bucket[metric][col_label]
            rows.append(row)

    return pd.DataFrame(rows)


def format_weekly_aum_report(report: pd.DataFrame) -> pd.DataFrame:
    """수치 컬럼을 표시용 문자열로 변환 (조·억 / +% 포맷)."""
    if report.empty:
        return report
    value_cols = [c for c in report.columns if c not in ("운용사", "구분")]
    out = report.copy()

    def _fmt_cell(metric: str, value: float | None) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "-"
        if metric == "증감률":
            return f"{value:+.2f}%"
        if metric == "증감":
            return fmt_jo_eok(value, signed=True)
        return fmt_jo_eok(value)

    for col in value_cols:
        out[col] = [
            _fmt_cell(metric, val)
            for metric, val in zip(out["구분"], out[col])
        ]
    return out


def to_excel_copy_text(report_display: pd.DataFrame) -> str:
    """엑셀 붙여넣기용 TSV 텍스트."""
    if report_display.empty:
        return ""
    return report_display.to_csv(sep="\t", index=False)
