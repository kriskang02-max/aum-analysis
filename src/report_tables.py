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


_DEFAULT_ROW_SPECS: list[tuple[str, tuple[str, ...] | None]] = [
    ("전체", None),
    ("신한자산운용", ("신한자산운용",)),
    ("KB자산운용", ("KB자산운용", "케이비자산운용")),
]

_DEFAULT_COL_SPECS: list[tuple[str, str | None]] = [
    ("전체", None),
    ("공모펀드", "공모"),
    ("사모펀드", "사모"),
    ("투자일임", "일임"),
]


def _build_snapshot(
    df: pd.DataFrame,
    date: pd.Timestamp,
    row_specs: list[tuple[str, tuple[str, ...] | None]],
    col_specs: list[tuple[str, str | None]],
) -> pd.DataFrame:
    rows: list[dict] = []
    for row_label, company_names in row_specs:
        row = {"운용사": row_label}
        for col_label, fund_type in col_specs:
            row[col_label] = _aum_total(
                df, date, company_names=company_names, fund_type=fund_type
            )
        rows.append(row)
    return pd.DataFrame(rows)


def build_weekly_aum_snapshot(
    df: pd.DataFrame,
    compare_date: pd.Timestamp,
    *,
    row_specs: list[tuple[str, tuple[str, ...] | None]] | None = None,
) -> pd.DataFrame:
    """수탁고 테이블 - 행: 전체/신한/KB, 열: 전체/공모/사모/일임 (비교일 시점 수탁고)."""
    return _build_snapshot(
        df,
        compare_date,
        row_specs or _DEFAULT_ROW_SPECS,
        _DEFAULT_COL_SPECS,
    )


def build_weekly_aum_delta(
    df: pd.DataFrame,
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
    *,
    row_specs: list[tuple[str, tuple[str, ...] | None]] | None = None,
) -> pd.DataFrame:
    """변동 테이블 - 비교일 − 기준일 (값만, 증감률 없음)."""
    rows: list[dict] = []
    for row_label, company_names in (row_specs or _DEFAULT_ROW_SPECS):
        row = {"운용사": row_label}
        for col_label, fund_type in _DEFAULT_COL_SPECS:
            base_v = _aum_total(
                df, base_date, company_names=company_names, fund_type=fund_type
            )
            cmp_v = _aum_total(
                df, compare_date, company_names=company_names, fund_type=fund_type
            )
            row[col_label] = cmp_v - base_v
        rows.append(row)
    return pd.DataFrame(rows)


def format_aum_table(report: pd.DataFrame, *, signed: bool = False) -> pd.DataFrame:
    """수치 컬럼을 조·억 포맷으로 변환."""
    if report.empty:
        return report
    out = report.copy()
    value_cols = [c for c in out.columns if c != "운용사"]
    for col in value_cols:
        out[col] = out[col].map(lambda v: fmt_jo_eok(v, signed=signed))
    return out


def to_excel_copy_text(report_display: pd.DataFrame) -> str:
    """엑셀 붙여넣기용 TSV 텍스트."""
    if report_display.empty:
        return ""
    return report_display.to_csv(sep="\t", index=False)
