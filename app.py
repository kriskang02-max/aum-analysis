"""운용사별 수탁고(설정규모) 증감 분석 대시보드."""

from __future__ import annotations

import locale

import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots

from src.data_loader import (
    ASSET_CLASSES,
    FUND_TYPES,
    UNIT_LABEL,
    add_period_changes,
    aggregate_type_date,
    compare_dates,
    excel_files_signature,
    filter_aum,
    load_all_aum,
)
from src.ceo_summary import build_company_ceo_summary, build_compare_ceo_summary
from src.report_tables import (
    build_weekly_aum_delta,
    build_weekly_aum_snapshot,
    build_weekly_aum_summary_lines,
    default_base_date as report_default_base_date,
    format_aum_table,
    sorted_dates as report_sorted_dates,
)
from src.daily_compare import (
    build_daily_company_metrics,
    build_daily_type_metrics,
    daily_pair_dates,
    daily_summary_counts,
    format_daily_table,
    sorted_dates,
)
from src.formatting import (
    apply_jo_eok_yaxis,
    fmt_jo_eok,
    jo_eok_yaxis_kwargs,
    jo_eok_yaxes_update_kwargs,
)

st.set_page_config(
    page_title="수탁고 증감 분석",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TYPE_LABELS = {"공모": "공모펀드", "사모": "사모펀드", "일임": "투자일임"}
# 데이터 스키마 변경 시 캐시 무효화용
DATA_SCHEMA_VERSION = "v3-exclude-gita"
CHART_VERSION = "v15-company-3panel"
TYPE_LINE_COLORS = {"공모": "#636efa", "사모": "#ef553b", "일임": "#2ecc71"}
PANEL_BG_A = "rgba(38, 44, 56, 0.6)"
PANEL_BG_B = "rgba(22, 27, 36, 0.75)"
PANEL_BORDER = "rgba(148, 163, 184, 0.5)"
SUBPLOT_V_SPACING = 0.14
DEFAULT_COMPANY = "신한자산운용"
DEFAULT_COMPARE_A = "신한자산운용"
DEFAULT_COMPARE_B = "KB자산운용"
COMPARE_B_ALIASES = ("KB자산운용", "케이비자산운용")
COMPARE_COLORS = ("#4dabf7", "#ffa94d")
TOP20_N = 20
TOP20_SPLIT = 10

pio.templates.default = "plotly_dark"


def inject_compact_layout() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 0.75rem;
            padding-bottom: 0.75rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
        header[data-testid="stHeader"] {
            background: transparent;
            height: 2.5rem;
        }
        h1 {
            margin-top: 0 !important;
            margin-bottom: 0.35rem !important;
            padding-top: 0 !important;
        }
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] > div {
            gap: 0.35rem;
        }
        hr {
            margin: 0.4rem 0 !important;
        }
        [data-testid="stTabs"] {
            margin-top: 0.15rem;
        }
        [data-testid="stTabContent"] {
            padding-top: 0.5rem;
        }
        h2, h3 {
            margin-top: 0.4rem !important;
            margin-bottom: 0.35rem !important;
            font-size: 1.05rem !important;
        }
        div[data-testid="stMetric"] {
            background-color: #1A1D24;
            padding: 0.45rem 0.65rem;
            border-radius: 0.4rem;
        }
        [data-testid="stAlert"] {
            margin-top: 0.25rem;
            margin-bottom: 0.25rem;
            padding: 0.5rem 0.75rem;
        }
        /* Streamlit 헤더(Deploy·⋮) 왼쪽 — 겹침 방지 */
        [class*="st-key-toolbar_refresh"] {
            position: fixed !important;
            top: 0.875rem !important;
            right: 11.75rem !important;
            z-index: 999999 !important;
            width: auto !important;
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            pointer-events: none !important;
        }
        [class*="st-key-toolbar_refresh"] > div {
            pointer-events: auto !important;
        }
        [class*="st-key-toolbar_refresh"] button,
        [class*="st-key-toolbar_refresh"] [data-testid="stBaseButton-tertiary"] {
            background: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(250, 250, 250, 0.2) !important;
            color: rgb(250, 250, 250) !important;
            font-size: 12px !important;
            font-weight: 400 !important;
            padding: 0.18rem 0.6rem !important;
            min-height: 1.85rem !important;
            border-radius: 0.5rem !important;
            box-shadow: none !important;
        }
        [class*="st-key-toolbar_refresh"] button:hover,
        [class*="st-key-toolbar_refresh"] [data-testid="stBaseButton-tertiary"]:hover {
            border-color: rgba(250, 250, 250, 0.35) !important;
            color: rgb(255, 255, 255) !important;
            background: rgba(255, 255, 255, 0.12) !important;
        }
        [class*="st-key-ceo_briefing"] {
            background: rgba(30, 41, 59, 0.55);
            border: 1px solid rgba(77, 171, 247, 0.35);
            border-radius: 0.4rem;
            padding: 0.65rem 0.95rem 0.9rem;
            margin-bottom: 0.45rem;
            max-width: 100%;
            overflow-x: hidden;
            overflow-y: visible;
            box-sizing: border-box;
        }
        [class*="st-key-ceo_briefing"] > div {
            overflow: visible !important;
        }
        [class*="st-key-ceo_briefing"] [data-testid="stMarkdownContainer"],
        [class*="st-key-ceo_briefing"] .stMarkdown {
            max-width: 100%;
            overflow: visible !important;
            overflow-wrap: anywhere;
            word-break: break-word;
            padding-bottom: 0.15rem;
        }
        [class*="st-key-ceo_briefing"] [data-testid="stMarkdownContainer"] p,
        [class*="st-key-ceo_briefing"] [data-testid="stMarkdownContainer"] li,
        [class*="st-key-ceo_briefing"] [data-testid="stMarkdownContainer"] strong,
        [class*="st-key-ceo_briefing"] .stMarkdown p,
        [class*="st-key-ceo_briefing"] .stMarkdown li,
        [class*="st-key-ceo_briefing"] .stMarkdown strong {
            font-size: calc(11px + 2pt) !important;
            line-height: 1.5 !important;
            max-width: 100%;
            overflow-wrap: anywhere;
            word-break: break-word;
            white-space: normal !important;
        }
        [class*="st-key-ceo_briefing"] [data-testid="stMarkdownContainer"] h4,
        [class*="st-key-ceo_briefing"] .stMarkdown h4 {
            margin: 0 0 0.35rem 0 !important;
            font-size: calc(12px + 2pt) !important;
            line-height: 1.45 !important;
            max-width: 100%;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        [class*="st-key-ceo_briefing"] [data-testid="stMarkdownContainer"] p,
        [class*="st-key-ceo_briefing"] .stMarkdown p {
            margin: 0.15rem 0 0.28rem 0 !important;
            padding-bottom: 0.05rem !important;
        }
        [class*="st-key-ceo_briefing"] [data-testid="stMarkdownContainer"] p:last-child,
        [class*="st-key-ceo_briefing"] .stMarkdown p:last-child {
            margin-bottom: 0.35rem !important;
            padding-bottom: 0.12rem !important;
        }
        [class*="st-key-ceo_briefing"] [data-testid="stMarkdownContainer"] strong,
        [class*="st-key-ceo_briefing"] .stMarkdown strong {
            font-weight: 600;
        }
        [class*="st-key-top20_table_scope"] table.top20-rank-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        [class*="st-key-top20_table_scope"] table.top20-rank-table th,
        [class*="st-key-top20_table_scope"] table.top20-rank-table td {
            padding: 5px 8px;
            text-align: center;
            border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        }
        [class*="st-key-top20_table_scope"] table.top20-rank-table thead th {
            background: rgba(30, 41, 59, 0.85);
            font-weight: 600;
        }
        [class*="st-key-top20_table_scope"] table.top20-rank-table tbody tr.top20-row-highlight td {
            background: rgba(250, 176, 5, 0.16);
            font-weight: 600;
        }
        [class*="st-key-top20_table_scope"] table.top20-rank-table tbody tr.top20-row-highlight td:first-child {
            box-shadow: inset 3px 0 0 #fab005;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_detail_tab_styles() -> None:
    """상세 데이터 탭 — HTML 테이블용 컴팩트 스타일 (st.dataframe 캔버스는 CSS 미적용)."""
    st.markdown(
        """
        <style>
        [class*="st-key-detail_tab_scope"] [data-testid="stCaptionContainer"] {
            font-size: 0.8rem !important;
            margin-bottom: 0.2rem !important;
            padding-top: 0 !important;
        }
        [class*="st-key-detail_tab_scope"] [data-testid="stDownloadButton"] {
            margin-top: 0 !important;
            margin-bottom: 0.15rem !important;
        }
        [class*="st-key-detail_tab_scope"] [data-testid="stDownloadButton"] button {
            font-size: 0.85rem !important;
            padding: 0.2rem 0.65rem !important;
            min-height: 1.65rem !important;
            background: rgba(77, 171, 247, 0.2) !important;
            border: 1px solid rgba(77, 171, 247, 0.5) !important;
            color: #bfdbfe !important;
        }
        [class*="st-key-detail_tab_scope"] [data-testid="stDownloadButton"] button:hover {
            background: rgba(77, 171, 247, 0.32) !important;
            border-color: rgba(147, 197, 253, 0.65) !important;
            color: #e0f2fe !important;
        }
        [class*="st-key-detail_tab_scope"] .aum-detail-scroll {
            max-height: 75vh;
            overflow: auto;
            width: 100%;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 0.35rem;
        }
        [class*="st-key-detail_tab_scope"] table.aum-detail-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            line-height: 1.25;
            color: #e2e8f0;
        }
        [class*="st-key-detail_tab_scope"] table.aum-detail-table thead th {
            position: sticky;
            top: 0;
            z-index: 1;
            background: #1a1d24;
            font-size: 13px;
            font-weight: 600;
            padding: 4px 7px;
            text-align: center;
            white-space: nowrap;
            border-bottom: 1px solid rgba(148, 163, 184, 0.35);
        }
        [class*="st-key-detail_tab_scope"] table.aum-detail-table tbody td {
            font-size: 13px;
            padding: 3px 7px;
            text-align: center;
            white-space: nowrap;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }
        [class*="st-key-detail_tab_scope"] table.aum-detail-table tbody tr:hover td {
            background: rgba(148, 163, 184, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


TOP20_HIGHLIGHT_FILL = "#fab005"
TOP20_OTHER_FILL = "rgba(148, 163, 184, 0.45)"


def _top20_bar_colors(companies: list[str]) -> list[str]:
    return [
        TOP20_HIGHLIGHT_FILL if c == DEFAULT_COMPANY else TOP20_OTHER_FILL
        for c in companies
    ]


def _top20_bar_line_widths(companies: list[str]) -> list[float]:
    return [2.5 if c == DEFAULT_COMPANY else 0 for c in companies]


def _top20_delta_colors(companies: list[str], deltas: list[float]) -> list[str]:
    colors = []
    for company, delta in zip(companies, deltas):
        if company == DEFAULT_COMPANY:
            if delta > 0:
                colors.append(_COLOR_UP)
            elif delta < 0:
                colors.append(_COLOR_DOWN)
            else:
                colors.append(TOP20_OTHER_FILL)
        else:
            colors.append(TOP20_OTHER_FILL)
    return colors


def _y_categories_on_fig(fig: go.Figure) -> list[str]:
    """차트 Y축에 실제 표시된 운용사 순서."""
    arr = fig.layout.yaxis.categoryarray
    if arr:
        return list(arr)
    for trace in fig.data:
        ys = getattr(trace, "y", None)
        if ys is not None:
            return list(dict.fromkeys(ys))
    return []


def _add_top20_highlight_band(
    fig: go.Figure,
    *,
    company: str = DEFAULT_COMPANY,
    present_categories: list[str] | None = None,
) -> None:
    """가로 막대 차트 — 해당 운용사 행 전체를 넓은 배경으로 강조."""
    cats = present_categories if present_categories is not None else _y_categories_on_fig(fig)
    if not cats or company not in cats:
        return
    idx = cats.index(company)
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="y",
        x0=0,
        x1=1,
        y0=idx - 0.46,
        y1=idx + 0.46,
        fillcolor="rgba(250, 176, 5, 0.18)",
        line=dict(color=TOP20_HIGHLIGHT_FILL, width=1.5),
        layer="below",
    )


def _html_cell_style(val: object) -> str:
    if not isinstance(val, str) or val.strip() in ("", "-"):
        return ""
    s = val.strip()
    if s.startswith("+"):
        return f' style="color: {_COLOR_UP}; font-weight: 600;"'
    if s.startswith("-"):
        return f' style="color: {_COLOR_DOWN}; font-weight: 600;"'
    return ""


def render_top20_rank_table(table: pd.DataFrame) -> None:
    """TOP20 순위표 — 전체 행 표시 + 신한자산운용 행 강조."""
    if table.empty:
        st.info("표시할 순위 데이터가 없습니다.")
        return

    headers = "".join(f"<th>{c}</th>" for c in table.columns)
    body_rows = []
    for _, row in table.iterrows():
        row_cls = (
            ' class="top20-row-highlight"'
            if row.get("운용사") == DEFAULT_COMPANY
            else ""
        )
        cells = []
        for col in table.columns:
            val = row[col]
            text = "-" if pd.isna(val) else str(val)
            extra = _html_cell_style(text) if col not in ("순위", "운용사") else ""
            cells.append(f"<td{extra}>{text}</td>")
        body_rows.append(f"<tr{row_cls}>{''.join(cells)}</tr>")

    html = (
        '<table class="top20-rank-table">'
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_detail_table(display: pd.DataFrame) -> None:
    """상세 데이터 — CSS 적용 가능한 HTML 테이블."""
    labels = {
        "수탁고": f"수탁고 ({UNIT_LABEL})",
        "이전_수탁고": f"이전 수탁고 ({UNIT_LABEL})",
        "증감": f"증감 ({UNIT_LABEL})",
        "증감률": "증감률",
    }
    tbl = display.rename(columns=labels)

    for col in (f"수탁고 ({UNIT_LABEL})", f"이전 수탁고 ({UNIT_LABEL})"):
        tbl[col] = tbl[col].map(
            lambda v: "-" if pd.isna(v) else f"{float(v):,.0f}"
        )
    tbl[f"증감 ({UNIT_LABEL})"] = tbl[f"증감 ({UNIT_LABEL})"].map(
        lambda v: "-" if pd.isna(v) else f"{float(v):+,.0f}"
    )
    tbl["증감률"] = tbl["증감률"].map(
        lambda v: "-" if pd.isna(v) else f"{float(v):+.2f}%"
    )

    html = tbl.to_html(index=False, classes="aum-detail-table", border=0)
    st.markdown(
        f'<div class="aum-detail-scroll">{html}</div>',
        unsafe_allow_html=True,
    )


def inject_toolbar_refresh_font() -> None:
    """Streamlit emotion 스타일보다 뒤에 로드 — 버튼 라벨 12px 고정."""
    st.markdown(
        """
        <style>
        html body [class*="st-key-toolbar_refresh"] button,
        html body [class*="st-key-toolbar_refresh"] button *,
        html body [class*="st-key-toolbar_refresh"] [data-testid="stBaseButton-tertiary"],
        html body [class*="st-key-toolbar_refresh"] [data-testid="stBaseButton-tertiary"] * {
            font-size: 12px !important;
            line-height: 1.25 !important;
        }
        html body [class*="st-key-toolbar_refresh"] button p,
        html body [class*="st-key-toolbar_refresh"] [data-testid="stBaseButton-tertiary"] p {
            font-size: 12px !important;
            line-height: 1.25 !important;
            margin: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def toolbar_refresh_button() -> None:
    if st.button(
        "새로고침",
        type="tertiary",
        help="엑셀 변경 반영·캐시 초기화",
        key="toolbar_refresh",
    ):
        get_data.clear()
        st.session_state["chart_nonce"] = (
            st.session_state.get("chart_nonce", 0) + 1
        )
        st.rerun()


@st.cache_data(show_spinner="엑셀 데이터 로딩 중…")
def get_data(file_signature: str):
    df = load_all_aum()
    if "자산" not in df.columns:
        raise ValueError("데이터 형식이 올바르지 않습니다. 캐시를 지운 뒤 다시 시도해 주세요.")
    return df


def load_data():
    signature = f"{excel_files_signature()}|{DATA_SCHEMA_VERSION}"
    return get_data(signature)


def fmt_amount(v: float | None) -> str:
    if v is None or pd.isna(v):
        return "-"
    return f"{v:,.0f}"


def fmt_delta(v: float | None) -> str:
    if v is None or pd.isna(v):
        return "-"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:,.0f}"


def companies_by_total_aum(df: pd.DataFrame) -> list[str]:
    """전 기간·유형 수탁고 합계 기준 내림차순 운용사 목록."""
    return (
        df.groupby("운용사", as_index=False)["수탁고"]
        .sum()
        .sort_values("수탁고", ascending=False)["운용사"]
        .tolist()
    )


_KOREAN_COLLATE_OK = False


def _korean_sort_key(name: str) -> str:
    """가나다순 정렬용 (로케일 미지원 시 문자열 순)."""
    global _KOREAN_COLLATE_OK
    if not _KOREAN_COLLATE_OK:
        for loc in (
            "ko_KR.UTF-8",
            "Korean_Korea.utf8",
            "Korean_Korea.949",
            "ko-KR",
        ):
            try:
                locale.setlocale(locale.LC_COLLATE, loc)
                _KOREAN_COLLATE_OK = True
                break
            except locale.Error:
                continue
    if _KOREAN_COLLATE_OK:
        try:
            return locale.strxfrm(name)
        except ValueError:
            pass
    return name


def companies_top_n_at_date(
    agg: pd.DataFrame, date: pd.Timestamp, *, n: int = TOP20_N
) -> list[str]:
    """특정 기준일 수탁고 합계(유형 합산) 상위 N개 운용사."""
    d = _norm_date(date)
    snap = agg[agg["기준일"].apply(_norm_date) == d]
    if snap.empty:
        return []
    return (
        snap.groupby("운용사")["수탁고"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .index.tolist()
    )


def build_top20_metrics(
    agg: pd.DataFrame,
    chg: pd.DataFrame,
    companies: list[str],
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
) -> pd.DataFrame:
    """TOP20 순위표용 지표(비교일·기준일·증감·유형별 비교일)."""
    if not companies:
        return pd.DataFrame()

    cmp_d = _norm_date(compare_date)
    base_d = _norm_date(base_date)
    snap = agg[agg["기준일"].apply(_norm_date) == cmp_d]
    by_type = (
        snap.groupby(["운용사", "유형"], as_index=False)["수탁고"]
        .sum()
        .pivot(index="운용사", columns="유형", values="수탁고")
        .fillna(0)
    )

    rows: list[dict] = []
    chg_co = (
        chg.groupby("운용사", as_index=False)
        .agg(기준_수탁고=("기준_수탁고", "sum"), 비교_수탁고=("비교_수탁고", "sum"))
        .assign(증감=lambda x: x["비교_수탁고"] - x["기준_수탁고"])
    )
    chg_map = chg_co.set_index("운용사")

    for rank, name in enumerate(companies, start=1):
        base_v = (
            float(chg_map.loc[name, "기준_수탁고"])
            if name in chg_map.index
            else 0.0
        )
        cmp_v = (
            float(chg_map.loc[name, "비교_수탁고"])
            if name in chg_map.index
            else 0.0
        )
        delta = cmp_v - base_v
        rate = (delta / base_v * 100) if base_v else None
        row: dict = {
            "순위": rank,
            "운용사": name,
            "기준_수탁고": base_v,
            "비교_수탁고": cmp_v,
            "증감": delta,
            "증감률": rate,
        }
        for t in ["공모", "사모", "일임"]:
            if name in by_type.index and t in by_type.columns:
                row[f"_{t}"] = float(by_type.loc[name, t])
            else:
                row[f"_{t}"] = 0.0
        rows.append(row)

    return pd.DataFrame(rows)


def build_top20_metrics_for_type(
    chg: pd.DataFrame,
    companies: list[str],
    fund_type: str,
) -> pd.DataFrame:
    """TOP20 동일 목록 · 단일 유형(공모/사모/일임) 지표."""
    chg_t = chg[chg["유형"] == fund_type]
    rows: list[dict] = []
    for rank, name in enumerate(companies, start=1):
        part = chg_t[chg_t["운용사"] == name]
        if part.empty:
            base_v = cmp_v = delta = 0.0
            rate = None
        else:
            row0 = part.iloc[0]
            base_v = float(row0["기준_수탁고"])
            cmp_v = float(row0["비교_수탁고"])
            delta = float(row0["증감"])
            pct = row0["증감률"]
            rate = float(pct) if pd.notna(pct) else None
        rows.append(
            {
                "순위": rank,
                "운용사": name,
                "기준_수탁고": base_v,
                "비교_수탁고": cmp_v,
                "증감": delta,
                "증감률": rate,
            }
        )
    return pd.DataFrame(rows)


def _top20_bar_height(n: int) -> int:
    return max(380, 22 * max(n, 1))


def _render_top20_rank_delta_row(
    metrics: pd.DataFrame,
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
    key_prefix: str,
    *,
    rank_title: str | None = None,
    delta_title: str | None = None,
) -> None:
    col_rank, col_delta = st.columns(2)
    with col_rank:
        st.plotly_chart(
            build_top20_rank_chart(
                metrics, compare_date, title=rank_title
            ),
            use_container_width=True,
            key=f"{key_prefix}_rank_{st.session_state.chart_nonce}",
        )
    with col_delta:
        st.plotly_chart(
            build_top20_delta_chart(
                metrics, base_date, compare_date, title=delta_title
            ),
            use_container_width=True,
            key=f"{key_prefix}_delta_{st.session_state.chart_nonce}",
        )


def format_top20_table(
    metrics: pd.DataFrame, base_date: pd.Timestamp, compare_date: pd.Timestamp
) -> pd.DataFrame:
    """표시용 문자열 포맷."""
    if metrics.empty:
        return metrics

    delta_col = _delta_col_label(base_date, compare_date)
    out = metrics.copy()
    out["기준일 합계"] = out["기준_수탁고"].map(fmt_jo_eok)
    out[f"{_yy_mm_dd(compare_date)} 합계"] = out["비교_수탁고"].map(fmt_jo_eok)
    out[delta_col] = out["증감"].map(lambda v: fmt_jo_eok(v, signed=True))
    out["증감률"] = out["증감률"].map(
        lambda v: f"{v:+.2f}%" if v is not None and pd.notna(v) else "-"
    )
    for t, label in TYPE_LABELS.items():
        out[label] = out[f"_{t}"].map(fmt_jo_eok)
    cols = [
        "순위",
        "운용사",
        "기준일 합계",
        f"{_yy_mm_dd(compare_date)} 합계",
        delta_col,
        "증감률",
        *TYPE_LABELS.values(),
    ]
    return out[cols]


def _apply_jo_eok_xaxis(
    fig: go.Figure,
    values: list[float],
    *,
    title: str = "수탁고 (조·억)",
    autoscale: bool = True,
) -> None:
    cfg = jo_eok_yaxes_update_kwargs(values, autoscale=autoscale, title=title)
    if cfg:
        fig.update_xaxes(**cfg)
    if autoscale:
        fig.update_xaxes(autorange=True, rangemode="tozero")


def top20_kpi_row(
    metrics: pd.DataFrame,
    agg: pd.DataFrame,
    compare_date: pd.Timestamp,
    base_date: pd.Timestamp,
):
    """TOP20 합산 KPI."""
    if metrics.empty:
        return
    base_tot = metrics["기준_수탁고"].sum()
    cmp_tot = metrics["비교_수탁고"].sum()
    delta = cmp_tot - base_tot
    rate = (delta / base_tot * 100) if base_tot else 0
    base_lbl = pd.Timestamp(base_date).strftime("%Y/%m/%d")
    cmp_lbl = pd.Timestamp(compare_date).strftime("%Y/%m/%d")

    cmp_d = _norm_date(compare_date)
    market_tot = agg.loc[agg["기준일"].apply(_norm_date) == cmp_d, "수탁고"].sum()
    share = (cmp_tot / market_tot * 100) if market_tot else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"TOP20 · {cmp_lbl} 합계", fmt_jo_eok(cmp_tot))
    c2.metric(f"TOP20 · {base_lbl} 합계", fmt_jo_eok(base_tot))
    c3.metric("TOP20 · 증감", fmt_jo_eok(delta, signed=True))
    c4.metric("TOP20 · 증감률", f"{rate:+.2f}%" if base_tot else "-")
    c5.metric("전체 대비 TOP20 비중", f"{share:.1f}%")


def build_top20_rank_chart(
    metrics: pd.DataFrame,
    compare_date: pd.Timestamp,
    *,
    title: str | None = None,
) -> go.Figure:
    plot = metrics.sort_values("비교_수탁고", ascending=True).copy()
    plot["라벨"] = plot["비교_수탁고"].map(fmt_jo_eok)
    companies = plot["운용사"].tolist()
    fig = go.Figure(
        go.Bar(
            x=plot["비교_수탁고"],
            y=plot["운용사"],
            orientation="h",
            text=plot["라벨"],
            textposition="outside",
            marker=dict(
                color=_top20_bar_colors(companies),
                line=dict(
                    color=TOP20_HIGHLIGHT_FILL,
                    width=_top20_bar_line_widths(companies),
                ),
            ),
            hovertemplate="%{y}<br>%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        height=_top20_bar_height(len(plot)),
        title=title or f"비교일({_yy_mm_dd(compare_date)}) 수탁고 순위",
        showlegend=False,
        margin=dict(l=120, r=40, t=48, b=32),
        yaxis=dict(categoryorder="array", categoryarray=companies),
    )
    _add_top20_highlight_band(fig, present_categories=companies)
    fig.update_traces(cliponaxis=False)
    _apply_jo_eok_xaxis(fig, plot["비교_수탁고"].astype(float).tolist())
    return fig


def build_top20_delta_chart(
    metrics: pd.DataFrame,
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
    *,
    title: str | None = None,
) -> go.Figure:
    plot = metrics.sort_values("증감", ascending=True).copy()
    plot["라벨"] = plot["증감"].map(lambda v: fmt_jo_eok(v, signed=True))
    companies = plot["운용사"].tolist()
    deltas = plot["증감"].astype(float).tolist()
    fig = go.Figure(
        go.Bar(
            x=plot["증감"],
            y=plot["운용사"],
            orientation="h",
            text=plot["라벨"],
            textposition="outside",
            marker=dict(
                color=_top20_delta_colors(companies, deltas),
                line=dict(
                    color=TOP20_HIGHLIGHT_FILL,
                    width=_top20_bar_line_widths(companies),
                ),
            ),
            hovertemplate="%{y}<br>증감: %{text}<extra></extra>",
        )
    )
    fig.update_layout(
        height=_top20_bar_height(len(plot)),
        title=title
        or f"기간 증감({_yy_mm_dd(base_date)}→{_yy_mm_dd(compare_date)})",
        showlegend=False,
        margin=dict(l=120, r=40, t=48, b=32),
        yaxis=dict(categoryorder="array", categoryarray=companies),
    )
    _add_top20_highlight_band(fig, present_categories=companies)
    fig.update_traces(cliponaxis=False)
    _apply_jo_eok_xaxis(fig, deltas)
    return fig


def build_top20_type_chart(
    metrics: pd.DataFrame,
    compare_date: pd.Timestamp,
    *,
    title: str | None = None,
) -> go.Figure:
    rows = []
    for _, r in metrics.iterrows():
        for t, label in TYPE_LABELS.items():
            rows.append(
                {
                    "운용사": r["운용사"],
                    "유형명": label,
                    "수탁고": r[f"_{t}"],
                }
            )
    plot = pd.DataFrame(rows)
    plot = plot[plot["수탁고"] > 0]
    plot["라벨"] = plot["수탁고"].map(fmt_jo_eok)
    order = metrics.sort_values("비교_수탁고", ascending=False)["운용사"].tolist()
    y_order = order[::-1]
    present = [c for c in y_order if c in set(plot["운용사"])]
    fig = px.bar(
        plot,
        x="수탁고",
        y="운용사",
        color="유형명",
        orientation="h",
        barmode="stack",
        text="라벨",
        category_orders={"운용사": present},
        labels={"수탁고": "수탁고", "운용사": ""},
        color_discrete_map=TYPE_LINE_COLORS,
    )
    n_rows = max(len(present), 1)
    fig.update_layout(
        height=max(340, 26 * n_rows),
        title=title or f"유형별 구성 · 비교일({_yy_mm_dd(compare_date)})",
        legend_title="유형",
        margin=dict(l=120, r=40, t=48, b=32),
        yaxis=dict(categoryorder="array", categoryarray=present),
    )
    _add_top20_highlight_band(fig, present_categories=present)
    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        cliponaxis=False,
    )
    stack_totals = plot.groupby("운용사")["수탁고"].sum().astype(float).tolist()
    x_vals = plot["수탁고"].astype(float).tolist()
    _apply_jo_eok_xaxis(
        fig,
        stack_totals if stack_totals else x_vals,
        autoscale=True,
    )
    return fig


def companies_for_select(df: pd.DataFrame, *, top_n: int = 15) -> list[str]:
    """상위 N개사(전체 수탁고 합계)는 가나다순, 나머지는 수탁고 내림차순."""
    by_aum = companies_by_total_aum(df)
    top = by_aum[:top_n]
    rest = by_aum[top_n:]
    return sorted(top, key=_korean_sort_key) + rest


def _company_index(
    companies: list[str],
    name: str,
    *,
    fallback: int = 0,
    aliases: tuple[str, ...] = (),
) -> int:
    if name in companies:
        return companies.index(name)
    for alt in aliases:
        if alt in companies:
            return companies.index(alt)
    return fallback


def top_filters(df: pd.DataFrame):
    dates = sorted(df["기준일"].unique())
    date_labels = [d.strftime("%Y/%m/%d") for d in dates]

    col_base, col_cmp, col_type, col_asset = st.columns(4)

    with col_base:
        if len(dates) < 2:
            st.selectbox("기준일", date_labels, index=0, disabled=True)
            base_idx = 0
        else:
            base_idx = st.selectbox(
                "기준일",
                range(len(dates)),
                format_func=lambda i: date_labels[i],
                index=0,
            )

    with col_cmp:
        if len(dates) < 2:
            st.selectbox("비교일", date_labels, index=0, disabled=True)
            cmp_idx = 0
        else:
            cmp_idx = st.selectbox(
                "비교일",
                range(len(dates)),
                format_func=lambda i: date_labels[i],
                index=len(dates) - 1,
            )

    with col_type:
        types = st.multiselect(
            "유형",
            options=list(FUND_TYPES),
            default=list(FUND_TYPES),
            format_func=lambda t: TYPE_LABELS.get(t, t),
        )

    with col_asset:
        assets = st.multiselect(
            "자산",
            options=list(ASSET_CLASSES),
            default=["채권"],
        )

    if len(dates) < 2:
        st.warning("증감 비교를 위해 서로 다른 기준일 파일이 2개 이상 필요합니다.")

    return dates[base_idx], dates[cmp_idx], types, assets


def kpi_row(
    df: pd.DataFrame,
    base: pd.Timestamp,
    compare: pd.Timestamp,
    types: list[str],
    assets: list[str],
    *,
    use_jo_eok: bool = False,
):
    subset = aggregate_type_date(filter_aum(df, fund_types=types, assets=assets))
    base_tot = subset[subset["기준일"] == base]["수탁고"].sum()
    cmp_tot = subset[subset["기준일"] == compare]["수탁고"].sum()
    delta = cmp_tot - base_tot
    rate = (delta / base_tot * 100) if base_tot else 0

    if use_jo_eok:
        fmt_val = fmt_jo_eok
        fmt_chg = lambda v: fmt_jo_eok(v, signed=True)
        unit_hint = ""
    else:
        fmt_val = fmt_amount
        fmt_chg = fmt_delta
        unit_hint = f" ({UNIT_LABEL})"

    base_lbl = pd.Timestamp(base).strftime("%Y/%m/%d")
    cmp_lbl = pd.Timestamp(compare).strftime("%Y/%m/%d")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{base_lbl} 합계{unit_hint}", fmt_val(base_tot))
    c2.metric(f"{cmp_lbl} 합계{unit_hint}", fmt_val(cmp_tot))
    c3.metric(f"증감{unit_hint}", fmt_chg(delta))
    c4.metric("증감률 (%)", f"{rate:+.2f}%" if base_tot else "-")


def _slim_grouped_bar(fig, n_dates: int, n_series: int):
    """기준일 카테고리 간 막대·레이블 겹침 완화."""
    per_group = max(n_series, 1)
    width = min(0.55 / per_group, 0.22)
    fig.update_traces(width=width, textposition="outside", cliponaxis=False)
    fig.update_layout(
        bargap=0.38,
        bargroupgap=0.12,
        xaxis=dict(type="category", tickangle=0),
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )
    if n_dates <= 3:
        fig.update_layout(margin=dict(b=60))


def _yy_mm_dd(ts) -> str:
    return pd.Timestamp(ts).strftime("%y/%m/%d")


def _norm_date(ts) -> pd.Timestamp:
    return pd.Timestamp(ts).normalize()


def _delta_col_label(base_date: pd.Timestamp, compare_date: pd.Timestamp) -> str:
    """상단 기준일·비교일 필터에 연동되는 증감 열/행 제목."""
    return f"증감({_yy_mm_dd(base_date)}→{_yy_mm_dd(compare_date)})"


def filter_through_compare_date(
    df: pd.DataFrame, compare_date: pd.Timestamp
) -> pd.DataFrame:
    """비교일(당일 포함)까지의 기준일만 표시."""
    if df.empty:
        return df
    end = _norm_date(compare_date)
    mask = df["기준일"].apply(lambda x: _norm_date(x) <= end)
    return df.loc[mask].copy()


def build_company_table(
    sub: pd.DataFrame,
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
    chg_co: pd.DataFrame,
) -> pd.DataFrame:
    """유형별 전체 기준일 수탁고 + 기준일·비교일 선택 증감."""
    if sub.empty:
        return pd.DataFrame()

    dates = sorted(sub["기준일"].unique())
    date_cols = [_yy_mm_dd(d) for d in dates]

    rows: list[dict] = []
    for fund_type in ["공모", "사모", "일임"]:
        part = sub[sub["유형"] == fund_type]
        if part.empty:
            continue
        row: dict = {"유형": TYPE_LABELS.get(fund_type, fund_type)}
        for d, col in zip(dates, date_cols):
            vals = part.loc[part["기준일"] == d, "수탁고"]
            if vals.empty or pd.isna(vals.iloc[0]):
                row[col] = "-"
            else:
                row[col] = fmt_jo_eok(float(vals.iloc[0]))
        rows.append(row)

    table = pd.DataFrame(rows)

    delta_col = _delta_col_label(base_date, compare_date)
    if chg_co.empty or _norm_date(base_date) == _norm_date(compare_date):
        table[delta_col] = "-"
        table["증감률"] = "-"
    else:
        chg = chg_co[["유형", "증감", "증감률"]].copy()
        chg["유형"] = chg["유형"].map(lambda u: TYPE_LABELS.get(u, u))
        table = table.merge(chg, on="유형", how="left")
        table[delta_col] = table["증감"].map(
            lambda v: fmt_jo_eok(v, signed=True) if pd.notna(v) else "-"
        )
        table["증감률"] = table["증감률"].map(
            lambda v: f"{v:+.2f}%" if pd.notna(v) else "-"
        )
        table = table.drop(columns=["증감"], errors="ignore")

    col_order = ["유형", *date_cols, delta_col, "증감률"]
    return table[[c for c in col_order if c in table.columns]]


_COLOR_UP = "#ff6b6b"
_COLOR_DOWN = "#4dabf7"


def _signed_cell_style(val: object) -> str:
    base = "text-align: center"
    if not isinstance(val, str) or val.strip() in ("", "-"):
        return base
    s = val.strip()
    if s.startswith("+"):
        return f"{base}; color: {_COLOR_UP}; font-weight: 600"
    if s.startswith("-"):
        return f"{base}; color: {_COLOR_DOWN}; font-weight: 600"
    return base


def build_daily_movers_chart(
    metrics: pd.DataFrame,
    *,
    title: str,
    top_n: int = 18,
    only_changed: bool = True,
) -> go.Figure:
    """일별 증감 절대값 상위 운용사 (가로 막대)."""
    plot = metrics[~metrics["변동없음"]].copy() if only_changed else metrics.copy()
    if plot.empty:
        return go.Figure()

    plot = plot.nlargest(top_n, "절대증감").sort_values("증감", ascending=True)
    plot["라벨"] = plot["증감"].map(lambda v: fmt_jo_eok(v, signed=True))
    companies = plot["운용사"].tolist()
    colors = [
        _COLOR_UP if v > 0 else _COLOR_DOWN if v < 0 else TOP20_OTHER_FILL
        for v in plot["증감"]
    ]
    line_widths = [2.5 if c == DEFAULT_COMPANY else 0 for c in companies]

    fig = go.Figure(
        go.Bar(
            x=plot["증감"],
            y=plot["운용사"],
            orientation="h",
            text=plot["라벨"],
            textposition="outside",
            marker=dict(
                color=colors,
                line=dict(color=TOP20_HIGHLIGHT_FILL, width=line_widths),
            ),
            hovertemplate="%{y}<br>일별 증감: %{text}<extra></extra>",
        )
    )
    fig.update_layout(
        height=_top20_bar_height(len(plot)),
        title=title,
        showlegend=False,
        margin=dict(l=120, r=40, t=48, b=32),
        yaxis=dict(categoryorder="array", categoryarray=companies),
    )
    if DEFAULT_COMPANY in companies:
        _add_top20_highlight_band(fig, present_categories=companies)
    fig.update_traces(cliponaxis=False)
    _apply_jo_eok_xaxis(fig, plot["증감"].astype(float).tolist())
    return fig


def build_daily_type_delta_chart(
    type_metrics: pd.DataFrame,
    prev_date: pd.Timestamp,
    latest_date: pd.Timestamp,
) -> go.Figure:
    if type_metrics.empty:
        return go.Figure()
    plot = type_metrics.copy()
    plot["라벨"] = plot["증감"].map(lambda v: fmt_jo_eok(v, signed=True))
    fig = px.bar(
        plot,
        x="유형명",
        y="증감",
        color="증감",
        color_continuous_scale=["#4dabf7", "#f0f0f0", "#ff6b6b"],
        color_continuous_midpoint=0,
        text="라벨",
        labels={"증감": "일별 증감", "유형명": "유형"},
    )
    fig.update_layout(
        height=340,
        title=f"유형별 일별 증감 ({_yy_mm_dd(prev_date)}→{_yy_mm_dd(latest_date)})",
        showlegend=False,
    )
    fig.update_traces(textposition="outside", cliponaxis=False, width=0.45)
    apply_jo_eok_yaxis(fig, plot["증감"].astype(float).tolist())
    return fig


def _render_daily_up_down_charts(
    metrics: pd.DataFrame,
    *,
    top_n: int,
    key_prefix: str,
    up_chart_title: str,
    down_chart_title: str,
    up_label: str = "증가 상위",
    down_label: str = "감소 상위",
) -> None:
    """일별 증가/감소 상위 막대 차트 (2열)."""
    changed = metrics[~metrics["변동없음"]]
    col_up, col_down = st.columns(2)
    nonce = st.session_state.chart_nonce
    with col_up:
        st.caption(up_label)
        up_only = changed[changed["증감"] > 0].nlargest(top_n, "증감")
        if up_only.empty:
            st.info("증가한 운용사가 없습니다.")
        else:
            st.plotly_chart(
                build_daily_movers_chart(
                    up_only,
                    title=up_chart_title,
                    top_n=len(up_only),
                    only_changed=False,
                ),
                use_container_width=True,
                key=f"{key_prefix}_up_{nonce}",
            )
    with col_down:
        st.caption(down_label)
        down_only = changed[changed["증감"] < 0].nsmallest(top_n, "증감")
        if down_only.empty:
            st.info("감소한 운용사가 없습니다.")
        else:
            st.plotly_chart(
                build_daily_movers_chart(
                    down_only,
                    title=down_chart_title,
                    top_n=len(down_only),
                    only_changed=False,
                ),
                use_container_width=True,
                key=f"{key_prefix}_down_{nonce}",
            )


def style_daily_table(table: pd.DataFrame) -> pd.io.formats.style.Styler:
    """변동 없음 행 흐리게, 신한자산운용 강조."""
    skip_signed = {"순위", "운용사", "변동"}
    value_cols = [c for c in table.columns if c not in skip_signed]

    def _row_style(row: pd.Series) -> list[str]:
        base = "text-align: center"
        if row.get("운용사") == DEFAULT_COMPANY:
            return [
                f"{base}; background-color: rgba(250, 176, 5, 0.14); font-weight: 600"
            ] * len(row)
        if row.get("변동") == "없음":
            return [f"{base}; color: #94a3b8; font-style: italic"] * len(row)
        return [base] * len(row)

    styler = table.style.set_table_styles(
        [
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("text-align", "center")]},
        ]
    )
    styler = styler.apply(_row_style, axis=1)
    for col in value_cols:
        styler = styler.map(_signed_cell_style, subset=[col])
    return styler.hide(axis="index")


def style_company_table(table: pd.DataFrame) -> pd.io.formats.style.Styler:
    """가운데 정렬 + +/- 값 부호별 색상(증감·차이·운용사 증감 행 등)."""
    skip_signed = {"기준일", "유형"}
    value_cols = [c for c in table.columns if c not in skip_signed]

    styler = table.style.set_table_styles(
        [
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("text-align", "center")]},
        ]
    ).map(lambda _: "text-align: center")

    for col in value_cols:
        styler = styler.map(_signed_cell_style, subset=[col])

    return styler.hide(axis="index")


def _yaxis_name(row: int) -> str:
    return "yaxis" if row == 1 else f"yaxis{row}"


def apply_panel_separation(fig: go.Figure, n_rows: int) -> None:
    """다단 패널 배경·구분선·축 테두리로 영역 구분."""
    if n_rows < 1:
        return

    shapes: list[dict] = []

    for row in range(1, n_rows + 1):
        ax = getattr(fig.layout, _yaxis_name(row), None)
        if ax is None or ax.domain is None:
            continue
        d = (float(ax.domain[0]), float(ax.domain[1]))
        shapes.append(
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0,
                x1=1,
                y0=d[0],
                y1=d[1],
                fillcolor=PANEL_BG_A if row % 2 == 1 else PANEL_BG_B,
                line=dict(color=PANEL_BORDER, width=1.5),
                layer="below",
            )
        )

    existing = list(fig.layout.shapes) if fig.layout.shapes else []
    fig.update_layout(shapes=[*existing, *shapes])

    fig.for_each_annotation(
        lambda a: a.update(
            font=dict(size=13, color="rgba(203, 213, 225, 0.9)"),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            showarrow=False,
        )
    )

    axis_frame = dict(
        showline=True,
        linewidth=1.2,
        linecolor=PANEL_BORDER,
        mirror=False,
        gridcolor="rgba(148, 163, 184, 0.18)",
        zeroline=False,
    )
    for row in range(1, n_rows + 1):
        fig.update_xaxes(row=row, col=1, **axis_frame)
        fig.update_yaxes(row=row, col=1, **axis_frame)


def build_company_chart(sub: pd.DataFrame) -> go.Figure:
    """공모·사모·일임 유형별 3단(또는 선택 유형 수) 패널."""
    active = [t for t in ["공모", "사모", "일임"] if (sub["유형"] == t).any()]
    if not active:
        return go.Figure()

    n = len(active)
    fig = make_subplots(
        rows=n,
        cols=1,
        shared_xaxes=True,
        row_heights=[1 / n] * n,
        vertical_spacing=SUBPLOT_V_SPACING,
        subplot_titles=[TYPE_LABELS.get(t, t) for t in active],
    )

    axis_style = dict(automargin=False, fixedrange=True)

    for row_idx, fund_type in enumerate(active, start=1):
        part = sub[sub["유형"] == fund_type].sort_values("기준일")
        if part.empty:
            continue
        label = TYPE_LABELS.get(fund_type, fund_type)
        labels = [fmt_jo_eok(v) for v in part["수탁고"]]
        y_vals = part["수탁고"].dropna().astype(float).tolist()

        fig.add_trace(
            go.Scatter(
                x=part["기준일"],
                y=part["수탁고"].astype(float),
                mode="lines+markers+text",
                name=label,
                line=dict(
                    color=TYPE_LINE_COLORS.get(fund_type, "#94a3b8"),
                    width=2,
                ),
                text=labels,
                textposition="top center",
                textfont=dict(size=10),
                customdata=labels,
                showlegend=False,
                hovertemplate=(
                    "%{x|%Y/%m/%d}<br>%{fullData.name}: %{customdata}<extra></extra>"
                ),
            ),
            row=row_idx,
            col=1,
        )

        if y_vals:
            fig.update_yaxes(
                **jo_eok_yaxes_update_kwargs(
                    y_vals,
                    autoscale=True,
                    title=f"{label} (조·억)",
                ),
                **axis_style,
                row=row_idx,
                col=1,
            )

    fig.update_xaxes(title_text="기준일", type="date", row=n, col=1)
    fig.update_layout(
        template="plotly_dark",
        height=260 * n + 90,
        showlegend=False,
        margin={"r": 40, "l": 72, "t": 72, "b": 44},
        hovermode="x unified",
        uirevision=CHART_VERSION,
    )
    apply_panel_separation(fig, n)
    fig.update_traces(cliponaxis=False)
    return fig


def _merge_type_series(
    part_a: pd.DataFrame, part_b: pd.DataFrame
) -> pd.DataFrame:
    """동일 유형·기준일 기준 두 운용사 수탁고 병합."""
    a = part_a[["기준일", "수탁고"]].rename(columns={"수탁고": "a"})
    b = part_b[["기준일", "수탁고"]].rename(columns={"수탁고": "b"})
    return a.merge(b, on="기준일", how="outer").sort_values("기준일")


def build_compare_chart(
    agg: pd.DataFrame,
    company_a: str,
    company_b: str,
    types: list[str],
) -> go.Figure:
    """공모·사모·일임 3단 — 두 운용사 라인 비교."""
    active = [t for t in ["공모", "사모", "일임"] if t in types]
    if not active:
        return go.Figure()

    n = len(active)
    fig = make_subplots(
        rows=n,
        cols=1,
        shared_xaxes=True,
        row_heights=[1 / n] * n,
        vertical_spacing=SUBPLOT_V_SPACING,
        subplot_titles=[TYPE_LABELS.get(t, t) for t in active],
    )

    sub_a = agg[agg["운용사"] == company_a]
    sub_b = agg[agg["운용사"] == company_b]
    axis_style = dict(automargin=False, fixedrange=True)

    for row_idx, fund_type in enumerate(active, start=1):
        pa = sub_a[sub_a["유형"] == fund_type]
        pb = sub_b[sub_b["유형"] == fund_type]
        merged = _merge_type_series(pa, pb)
        if merged.empty:
            continue

        x = merged["기준일"]
        ya = merged["a"]
        yb = merged["b"]
        y_all = pd.concat([ya.dropna(), yb.dropna()]).astype(float).tolist()

        labels_a = [
            fmt_jo_eok(v) if pd.notna(v) else "-" for v in ya
        ]
        labels_b = [
            fmt_jo_eok(v) if pd.notna(v) else "-" for v in yb
        ]

        fig.add_trace(
            go.Scatter(
                x=x,
                y=ya,
                mode="lines+markers+text",
                name=company_a,
                legendgroup="co_a",
                showlegend=row_idx == 1,
                line=dict(color=COMPARE_COLORS[0], width=2),
                text=labels_a,
                textposition="top center",
                textfont=dict(size=9),
                customdata=labels_a,
                hovertemplate=(
                    "%{x|%Y/%m/%d}<br>"
                    f"{company_a}: %{{customdata}}<extra></extra>"
                ),
            ),
            row=row_idx,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=x,
                y=yb,
                mode="lines+markers+text",
                name=company_b,
                legendgroup="co_b",
                showlegend=row_idx == 1,
                line=dict(color=COMPARE_COLORS[1], width=2),
                text=labels_b,
                textposition="top center",
                textfont=dict(size=9),
                customdata=labels_b,
                hovertemplate=(
                    "%{x|%Y/%m/%d}<br>"
                    f"{company_b}: %{{customdata}}<extra></extra>"
                ),
            ),
            row=row_idx,
            col=1,
        )

        if y_all:
            fig.update_yaxes(
                **jo_eok_yaxes_update_kwargs(
                    y_all,
                    autoscale=True,
                    title=f"{TYPE_LABELS.get(fund_type, fund_type)} (조·억)",
                ),
                **axis_style,
                row=row_idx,
                col=1,
            )

    fig.update_xaxes(title_text="기준일", type="date", row=n, col=1)
    fig.update_layout(
        template="plotly_dark",
        height=260 * n + 90,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 0,
            "xanchor": "left",
        },
        margin={"r": 40, "l": 72, "t": 72, "b": 44},
        hovermode="x unified",
        uirevision=CHART_VERSION,
    )
    apply_panel_separation(fig, n)
    fig.update_traces(cliponaxis=False)
    return fig


def _aum_at(part: pd.DataFrame, date: pd.Timestamp) -> float | None:
    d = _norm_date(date)
    mask = part["기준일"].apply(lambda x: _norm_date(x) == d)
    vals = part.loc[mask, "수탁고"]
    if vals.empty or pd.isna(vals.iloc[0]):
        return None
    return float(vals.iloc[0])


def _compare_change_row(
    pa: pd.DataFrame,
    pb: pd.DataFrame,
    company_a: str,
    company_b: str,
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
) -> dict:
    """상단 기준일·비교일 필터 기준 증감 요약 행 (비교일 − 기준일)."""
    label = _delta_col_label(base_date, compare_date)
    row: dict = {"기준일": label}

    if _norm_date(base_date) == _norm_date(compare_date):
        row[company_a] = "-"
        row[company_b] = "-"
        row["차이"] = "-"
        return row

    va_base, va_cmp = _aum_at(pa, base_date), _aum_at(pa, compare_date)
    vb_base, vb_cmp = _aum_at(pb, base_date), _aum_at(pb, compare_date)

    row[company_a] = (
        fmt_jo_eok(va_cmp - va_base, signed=True)
        if va_base is not None and va_cmp is not None
        else "-"
    )
    row[company_b] = (
        fmt_jo_eok(vb_cmp - vb_base, signed=True)
        if vb_base is not None and vb_cmp is not None
        else "-"
    )
    if (
        va_base is not None
        and va_cmp is not None
        and vb_base is not None
        and vb_cmp is not None
    ):
        gap_cmp = va_cmp - vb_cmp
        gap_base = va_base - vb_base
        row["차이"] = fmt_jo_eok(gap_cmp - gap_base, signed=True)
    else:
        row["차이"] = "-"
    return row


def build_compare_tables_by_type(
    agg: pd.DataFrame,
    company_a: str,
    company_b: str,
    types: list[str],
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
) -> dict[str, pd.DataFrame]:
    """유형별 테이블(공모/사모/일임) — 행=기준일, 열=두 운용사·차이(A−B)."""
    sub_a = agg[agg["운용사"] == company_a]
    sub_b = agg[agg["운용사"] == company_b]
    tables: dict[str, pd.DataFrame] = {}

    for fund_type in ["공모", "사모", "일임"]:
        if fund_type not in types:
            continue
        pa = sub_a[sub_a["유형"] == fund_type]
        pb = sub_b[sub_b["유형"] == fund_type]
        if pa.empty and pb.empty:
            continue

        dates = sorted(set(pa["기준일"].unique()) | set(pb["기준일"].unique()))
        rows: list[dict] = []
        for d in dates:
            a_val = _aum_at(pa, d)
            b_val = _aum_at(pb, d)

            rows.append(
                {
                    "기준일": _yy_mm_dd(d),
                    company_a: fmt_jo_eok(a_val) if a_val is not None else "-",
                    company_b: fmt_jo_eok(b_val) if b_val is not None else "-",
                    "차이": (
                        fmt_jo_eok(a_val - b_val, signed=True)
                        if a_val is not None and b_val is not None
                        else "-"
                    ),
                }
            )

        if rows:
            rows.append(
                _compare_change_row(pa, pb, company_a, company_b, base_date, compare_date)
            )
            tables[fund_type] = pd.DataFrame(rows)

    return tables


def main():
    if "chart_nonce" not in st.session_state:
        st.session_state.chart_nonce = 0

    inject_compact_layout()
    toolbar_refresh_button()
    st.title("운용사별 수탁고 증감 분석")

    try:
        df = load_data()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

    base_date, compare_date, types, assets = top_filters(df)
    if not types:
        st.warning("유형을 하나 이상 선택해 주세요.")
        st.stop()
    if not assets:
        st.warning("자산을 하나 이상 선택해 주세요.")
        st.stop()

    filtered = filter_aum(df, fund_types=types, assets=assets)
    agg = aggregate_type_date(filtered)

    if base_date == compare_date:
        st.info("기준일과 비교일이 같습니다. 서로 다른 날짜를 선택하면 증감이 표시됩니다.")

    st.markdown("---")

    (
        tab_summary,
        tab_top20,
        tab_daily,
        tab_weekly,
        tab_company,
        tab_compare,
        tab_table,
        tab_report,
    ) = st.tabs(
        [
            "전체 수탁고",
            "TOP20 비교",
            "Daily 비교",
            "Weekly 비교",
            "운용사별 수탁고",
            "운용사 비교",
            "상세 데이터",
            "보고자료",
        ]
    )

    # --- 전체 수탁고 ---
    with tab_summary:
        kpi_row(df, base_date, compare_date, types, assets, use_jo_eok=True)
        st.subheader("유형별 수탁고 추이")
        trend = agg.groupby(["기준일", "유형"], as_index=False)["수탁고"].sum()
        trend["유형명"] = trend["유형"].map(TYPE_LABELS)
        trend["기준일_str"] = trend["기준일"].dt.strftime("%Y-%m-%d")
        trend["라벨"] = trend["수탁고"].map(fmt_jo_eok)
        n_dates = trend["기준일_str"].nunique()
        fig = px.bar(
            trend,
            x="기준일_str",
            y="수탁고",
            color="유형명",
            barmode="group",
            labels={"수탁고": "수탁고", "기준일_str": "기준일"},
            text="라벨",
        )
        fig.update_layout(height=420, legend_title="유형")
        _slim_grouped_bar(fig, n_dates=n_dates, n_series=trend["유형명"].nunique())
        fig.update_traces(
            hovertemplate="%{x}<br>%{fullData.name}: %{text}<extra></extra>",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("유형별 수탁고 증감")
        chg = compare_dates(df, base_date, compare_date, types, assets)
        by_type = (
            chg.groupby("유형", as_index=False)
            .agg(기준=("기준_수탁고", "sum"), 비교=("비교_수탁고", "sum"))
        )
        by_type["증감"] = by_type["비교"] - by_type["기준"]
        by_type["유형명"] = by_type["유형"].map(TYPE_LABELS)
        by_type["라벨"] = by_type["증감"].map(lambda v: fmt_jo_eok(v, signed=True))
        fig2 = px.bar(
            by_type,
            x="유형명",
            y="증감",
            color="증감",
            color_continuous_scale=["#d62728", "#f0f0f0", "#2ca02c"],
            color_continuous_midpoint=0,
            labels={"증감": "증감"},
            text="라벨",
        )
        fig2.update_layout(height=380, showlegend=False)
        fig2.update_traces(
            textposition="outside",
            cliponaxis=False,
            width=0.45,
            hovertemplate="%{x}<br>증감: %{text}<extra></extra>",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # --- TOP20 비교 ---
    with tab_top20:
        top20 = companies_top_n_at_date(agg, compare_date, n=TOP20_N)
        if not top20:
            st.warning("비교일 기준 TOP20을 산출할 수 없습니다. 비교일·필터를 확인해 주세요.")
        else:
            chg_top = compare_dates(df, base_date, compare_date, types, assets)
            metrics = build_top20_metrics(
                agg, chg_top, top20, base_date, compare_date
            )
            st.caption(
                f"**비교일({_yy_mm_dd(compare_date)})** 수탁고 합계 기준 상위 **{len(top20)}**개사 · "
                "상단 **기준일·비교일·유형·자산** 필터 적용 · "
                f"차트·표에서 **{DEFAULT_COMPANY}**는 **노란색**으로 강조"
            )
            top20_kpi_row(metrics, agg, compare_date, base_date)

            st.subheader("전체 (합산)")
            _render_top20_rank_delta_row(
                metrics,
                base_date,
                compare_date,
                f"top20_all_{_norm_date(compare_date)}_{'-'.join(types)}",
            )

            cmp_lbl = _yy_mm_dd(compare_date)
            delta_lbl = f"{_yy_mm_dd(base_date)}→{_yy_mm_dd(compare_date)}"
            top10 = metrics.iloc[:TOP20_SPLIT]
            top11_20 = metrics.iloc[TOP20_SPLIT:TOP20_N]

            for fund_type in ["공모", "사모", "일임"]:
                if fund_type not in types:
                    continue
                type_label = TYPE_LABELS[fund_type]
                st.subheader(type_label)
                metrics_type = build_top20_metrics_for_type(chg_top, top20, fund_type)
                _render_top20_rank_delta_row(
                    metrics_type,
                    base_date,
                    compare_date,
                    f"top20_{fund_type}_{_norm_date(compare_date)}",
                    rank_title=f"{type_label} · 비교일({cmp_lbl}) 수탁고 순위",
                    delta_title=f"{type_label} · 기간 증감({delta_lbl})",
                )

            st.subheader("유형별 수탁고 구성")
            col_type_l, col_type_r = st.columns(2)
            with col_type_l:
                st.caption("TOP 1~10")
                st.plotly_chart(
                    build_top20_type_chart(
                        top10,
                        compare_date,
                        title=f"TOP 1~10 · 비교일({cmp_lbl})",
                    ),
                    use_container_width=True,
                    key=f"top20_type_10_{st.session_state.chart_nonce}",
                )
            with col_type_r:
                st.caption("TOP 11~20")
                if top11_20.empty:
                    st.info("11~20위 데이터가 없습니다.")
                else:
                    st.plotly_chart(
                        build_top20_type_chart(
                            top11_20,
                            compare_date,
                            title=f"TOP 11~20 · 비교일({cmp_lbl})",
                        ),
                        use_container_width=True,
                        key=f"top20_type_20_{st.session_state.chart_nonce}",
                    )

            st.subheader("TOP20 순위표")
            st.caption(f"**{DEFAULT_COMPANY}** 행은 노란색으로 강조됩니다.")
            rank_table = format_top20_table(metrics, base_date, compare_date)
            with st.container(key="top20_table_scope"):
                render_top20_rank_table(rank_table)

    # --- Daily 비교 ---
    with tab_daily:
        pair = daily_pair_dates(agg)
        if pair is None:
            dates = sorted_dates(agg)
            st.warning(
                "일별 비교를 위해 서로 다른 기준일 데이터가 2개 이상 필요합니다. "
                f"(현재 {len(dates)}개 일자)"
            )
        else:
            prev_date, latest_date = pair
            daily_metrics = build_daily_company_metrics(agg, prev_date, latest_date)
            type_daily = build_daily_type_metrics(agg, prev_date, latest_date)
            counts = daily_summary_counts(daily_metrics)

            total_prev = daily_metrics["직전_수탁고"].sum()
            total_latest = daily_metrics["최신_수탁고"].sum()
            total_delta = total_latest - total_prev
            total_rate = (total_delta / total_prev * 100) if total_prev else 0

            st.caption(
                f"**최신일 {_yy_mm_dd(latest_date)}** vs **직전일 {_yy_mm_dd(prev_date)}** "
                "(데이터가 있는 연속 기준일) · 상단 유형·자산 필터 적용 · "
                "정렬은 **변동폭(절대값)** 기준"
            )

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric(f"{_yy_mm_dd(latest_date)} 합계", fmt_jo_eok(total_latest))
            k2.metric("일별 증감", fmt_jo_eok(total_delta, signed=True))
            k3.metric("증감률", f"{total_rate:+.2f}%" if total_prev else "-")
            k4.metric("증가 / 감소", f"{counts['up']} / {counts['down']}")
            k5.metric("변동 없음", f"{counts['flat']}개사")

            st.plotly_chart(
                build_daily_type_delta_chart(type_daily, prev_date, latest_date),
                use_container_width=True,
                key=f"daily_type_{st.session_state.chart_nonce}_{_norm_date(latest_date)}",
            )

            changed = daily_metrics[~daily_metrics["변동없음"]]

            st.subheader("전체 · 증가/감소 상위")
            _render_daily_up_down_charts(
                daily_metrics,
                top_n=12,
                key_prefix="daily_all",
                up_chart_title="증가 TOP (일별·전체)",
                down_chart_title="감소 TOP (일별·전체)",
            )

            st.subheader("유형별 · 증가/감소 상위")
            for fund_type in ("공모", "사모", "일임"):
                type_agg = agg[agg["유형"] == fund_type]
                if type_agg.empty:
                    continue
                type_label = TYPE_LABELS[fund_type]
                type_metrics = build_daily_company_metrics(
                    type_agg, prev_date, latest_date
                )
                type_counts = daily_summary_counts(type_metrics)
                st.markdown(
                    f"**{type_label}** · 증가 {type_counts['up']} / "
                    f"감소 {type_counts['down']} / 무변동 {type_counts['flat']}"
                )
                _render_daily_up_down_charts(
                    type_metrics,
                    top_n=10,
                    key_prefix=f"daily_{fund_type}",
                    up_chart_title=f"증가 TOP · {type_label}",
                    down_chart_title=f"감소 TOP · {type_label}",
                    up_label=f"{type_label} 증가 상위",
                    down_label=f"{type_label} 감소 상위",
                )

            st.subheader("변동폭 상위 (전체)")
            st.plotly_chart(
                build_daily_movers_chart(
                    daily_metrics,
                    title=f"일별 변동폭 TOP · {_yy_mm_dd(prev_date)}→{_yy_mm_dd(latest_date)}",
                    top_n=20,
                    only_changed=True,
                ),
                use_container_width=True,
                key=f"daily_abs_{st.session_state.chart_nonce}",
            )

            show_flat = st.checkbox(
                "변동 없는 운용사 표에 포함",
                value=True,
                key="daily_show_flat",
            )
            table_src = daily_metrics if show_flat else changed
            st.subheader("운용사별 일별 비교")
            st.caption(
                f"**{DEFAULT_COMPANY}** 행 강조 · 변동 없음은 회색 이탤릭"
            )
            daily_table = format_daily_table(table_src, prev_date, latest_date)
            table_height = 48 + len(daily_table) * 34
            st.dataframe(
                style_daily_table(daily_table),
                use_container_width=True,
                hide_index=True,
                height=min(table_height, 900),
                key=f"daily_table_{_norm_date(prev_date)}_{_norm_date(latest_date)}",
            )

    # --- Weekly 비교 ---
    with tab_weekly:
        dates = sorted_dates(agg)
        if len(dates) < 2:
            st.warning(
                "주간 비교를 위해 서로 다른 기준일 데이터가 2개 이상 필요합니다. "
                f"(현재 {len(dates)}개 일자)"
            )
        else:
            latest_date = dates[-1]
            prev_date = report_default_base_date(dates, latest_date)

            weekly_metrics = build_daily_company_metrics(agg, prev_date, latest_date)
            type_weekly = build_daily_type_metrics(agg, prev_date, latest_date)
            counts_w = daily_summary_counts(weekly_metrics)

            total_prev_w = weekly_metrics["직전_수탁고"].sum()
            total_latest_w = weekly_metrics["최신_수탁고"].sum()
            total_delta_w = total_latest_w - total_prev_w
            total_rate_w = (total_delta_w / total_prev_w * 100) if total_prev_w else 0

            st.caption(
                f"**Weekly 비교** · 최신일 {_yy_mm_dd(latest_date)} 기준 "
                f"**{_yy_mm_dd(prev_date)} → {_yy_mm_dd(latest_date)}** (약 7일 전 대비) · "
                "상단 유형·자산 필터 적용 · 정렬은 **변동폭(절대값)** 기준"
            )

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric(f"{_yy_mm_dd(latest_date)} 합계", fmt_jo_eok(total_latest_w))
            k2.metric("주간 증감", fmt_jo_eok(total_delta_w, signed=True))
            k3.metric("증감률", f"{total_rate_w:+.2f}%" if total_prev_w else "-")
            k4.metric("증가 / 감소", f"{counts_w['up']} / {counts_w['down']}")
            k5.metric("변동 없음", f"{counts_w['flat']}개사")

            st.plotly_chart(
                build_daily_type_delta_chart(type_weekly, prev_date, latest_date),
                use_container_width=True,
                key=f"weekly_type_{st.session_state.chart_nonce}_{_norm_date(latest_date)}",
            )

            changed_w = weekly_metrics[~weekly_metrics["변동없음"]]

            st.subheader("전체 · 주간 증가/감소 상위")
            _render_daily_up_down_charts(
                weekly_metrics,
                top_n=12,
                key_prefix="weekly_all",
                up_chart_title="증가 TOP (주간·전체)",
                down_chart_title="감소 TOP (주간·전체)",
            )

            st.subheader("유형별 · 주간 증가/감소 상위")
            for fund_type in ("공모", "사모", "일임"):
                type_agg = agg[agg["유형"] == fund_type]
                if type_agg.empty:
                    continue
                type_label = TYPE_LABELS[fund_type]
                type_metrics_w = build_daily_company_metrics(
                    type_agg, prev_date, latest_date
                )
                type_counts_w = daily_summary_counts(type_metrics_w)
                st.markdown(
                    f"**{type_label}** · 증가 {type_counts_w['up']} / "
                    f"감소 {type_counts_w['down']} / 무변동 {type_counts_w['flat']}"
                )
                _render_daily_up_down_charts(
                    type_metrics_w,
                    top_n=10,
                    key_prefix=f"weekly_{fund_type}",
                    up_chart_title=f"증가 TOP · {type_label} (주간)",
                    down_chart_title=f"감소 TOP · {type_label} (주간)",
                    up_label=f"{type_label} 증가 상위",
                    down_label=f"{type_label} 감소 상위",
                )

            st.subheader("주간 변동폭 상위 (전체)")
            st.plotly_chart(
                build_daily_movers_chart(
                    weekly_metrics,
                    title=f"주간 변동폭 TOP · {_yy_mm_dd(prev_date)}→{_yy_mm_dd(latest_date)}",
                    top_n=20,
                    only_changed=True,
                ),
                use_container_width=True,
                key=f"weekly_abs_{st.session_state.chart_nonce}",
            )

            show_flat_w = st.checkbox(
                "변동 없는 운용사 표에 포함 (주간)",
                value=True,
                key="weekly_show_flat",
            )
            table_src_w = weekly_metrics if show_flat_w else changed_w
            st.subheader("운용사별 주간 비교")
            st.caption(
                f"**{DEFAULT_COMPANY}** 행 강조 · 변동 없음은 회색 이탤릭"
            )
            weekly_table = format_daily_table(table_src_w, prev_date, latest_date)
            table_height_w = 48 + len(weekly_table) * 34
            st.dataframe(
                style_daily_table(weekly_table),
                use_container_width=True,
                hide_index=True,
                height=min(table_height_w, 900),
                key=f"weekly_table_{_norm_date(prev_date)}_{_norm_date(latest_date)}",
            )

    # --- 운용사별 수탁고 ---
    with tab_company:
        companies = companies_for_select(agg)
        pick = st.selectbox(
            "운용사 선택",
            options=companies,
            index=_company_index(companies, DEFAULT_COMPANY),
            key="company_pick",
        )
        sub = filter_through_compare_date(
            agg[agg["운용사"] == pick], compare_date
        )
        if sub.empty:
            st.warning("선택한 유형에 해당 운용사 데이터가 없습니다.")
        else:
            with st.container(key="ceo_briefing_company"):
                st.markdown(
                    build_company_ceo_summary(
                        pick, sub, base_date, compare_date, types
                    )
                )
            st.caption(
                f"**{_yy_mm_dd(compare_date)}**까지의 데이터만 표시합니다. "
                "공모·사모·일임은 유형별 패널에 각각 표시됩니다."
            )
            fig_co = build_company_chart(sub)
            chart_key = (
                f"company_{CHART_VERSION}_{st.session_state.chart_nonce}_{pick}_"
                f"{base_date.date()}_{compare_date.date()}_"
                f"{'-'.join(types)}_{'-'.join(assets)}"
            )
            st.plotly_chart(fig_co, use_container_width=True, key=chart_key)

            chg_co = compare_dates(df, base_date, compare_date, types, assets)
            chg_co = chg_co[chg_co["운용사"] == pick]
            table = build_company_table(sub, base_date, compare_date, chg_co)
            st.dataframe(
                style_company_table(table),
                use_container_width=True,
                hide_index=True,
                key=(
                    f"company_table_{pick}_{_norm_date(base_date)}_"
                    f"{_norm_date(compare_date)}"
                ),
            )

    # --- 운용사 비교 ---
    with tab_compare:
        companies = companies_for_select(agg)
        col_a, col_b = st.columns(2)
        with col_a:
            pick_a = st.selectbox(
                "운용사 A",
                options=companies,
                index=_company_index(companies, DEFAULT_COMPARE_A),
                key="compare_pick_a",
            )
        with col_b:
            pick_b = st.selectbox(
                "운용사 B",
                options=companies,
                index=_company_index(
                    companies,
                    DEFAULT_COMPARE_B,
                    fallback=min(1, len(companies) - 1),
                    aliases=COMPARE_B_ALIASES,
                ),
                key="compare_pick_b",
            )

        if pick_a == pick_b:
            st.warning("서로 다른 운용사를 선택하면 비교 차트가 표시됩니다.")

        agg_through = filter_through_compare_date(agg, compare_date)
        sub_a = agg_through[agg_through["운용사"] == pick_a]
        sub_b = agg_through[agg_through["운용사"] == pick_b]
        if sub_a.empty and sub_b.empty:
            st.warning("선택한 유형에 해당 운용사 데이터가 없습니다.")
        else:
            with st.container(key="ceo_briefing_compare"):
                st.markdown(
                    build_compare_ceo_summary(
                        pick_a, pick_b, agg_through, base_date, compare_date, types
                    )
                )
            st.caption(
                f"**{pick_a}**와 **{pick_b}**의 유형별 수탁고 추이 "
                f"(**{_yy_mm_dd(compare_date)}**까지 표시)"
            )
            fig_cmp = build_compare_chart(agg_through, pick_a, pick_b, types)
            cmp_key = (
                f"compare_{CHART_VERSION}_{st.session_state.chart_nonce}_"
                f"{pick_a}_{pick_b}_{'-'.join(types)}_{'-'.join(assets)}"
            )
            st.plotly_chart(fig_cmp, use_container_width=True, key=cmp_key)

            cmp_tables = build_compare_tables_by_type(
                agg_through, pick_a, pick_b, types, base_date, compare_date
            )
            if not cmp_tables:
                st.info("표시할 비교 데이터가 없습니다.")
            else:
                for fund_type in ["공모", "사모", "일임"]:
                    tbl = cmp_tables.get(fund_type)
                    if tbl is None or tbl.empty:
                        continue
                    st.markdown(f"**{TYPE_LABELS.get(fund_type, fund_type)}**")
                    st.dataframe(
                        style_company_table(tbl),
                        use_container_width=True,
                        hide_index=True,
                        key=(
                            f"compare_table_{fund_type}_{pick_a}_{pick_b}_"
                            f"{_norm_date(base_date)}_{_norm_date(compare_date)}"
                        ),
                    )

    # --- 상세 데이터 ---
    with tab_table:
        inject_detail_tab_styles()
        enriched = add_period_changes(filtered)
        view = enriched.copy()
        view["기준일"] = view["기준일"].dt.strftime("%Y-%m-%d")
        detail_cols = [
            "기준일",
            "유형",
            "자산",
            "운용사",
            "수탁고",
            "이전_수탁고",
            "증감",
            "증감률",
        ]
        display = view[detail_cols].sort_values(
            ["기준일", "유형", "자산", "운용사"],
            ascending=[False, True, True, True],
        )
        csv = display.to_csv(index=False).encode("utf-8-sig")

        with st.container(key="detail_tab_scope"):
            hdr_l, hdr_r = st.columns([6, 1])
            with hdr_l:
                st.caption(
                    f"수치 단위: **{UNIT_LABEL}** · "
                    "동일 운용사·유형·자산 기준 직전 기준일 대비 증감"
                )
            with hdr_r:
                st.download_button(
                    "csv 파일 저장",
                    data=csv,
                    file_name="aum_analysis.csv",
                    mime="text/csv",
                    key="detail_csv_dl",
                    type="tertiary",
                    use_container_width=True,
                )
            render_detail_table(display)

    # --- 보고자료 ---
    with tab_report:
        report_source = filter_aum(df, fund_types=list(FUND_TYPES), assets=assets)
        report_dates = report_sorted_dates(report_source)
        if len(report_dates) < 2:
            st.warning(
                "보고자료 작성을 위해 서로 다른 기준일 데이터가 2개 이상 필요합니다."
            )
        else:
            st.subheader("주간 수탁고 변동")
            st.caption(
                "상단 **자산** 필터 적용 · "
                f"자산 선택: {', '.join(assets) if assets else '없음'} · "
                "비교일 기본값: 데이터 최신일 / 기준일 기본값: 비교일 7일 전 이하 가장 가까운 가용일"
            )

            date_labels = [d.strftime("%Y/%m/%d") for d in report_dates]
            n_dates = len(report_dates)

            col_cmp, col_base, _spacer = st.columns([1, 1, 4])

            with col_cmp:
                default_cmp_idx = n_dates - 1
                if (
                    st.session_state.get("report_compare_dates_signature")
                    != tuple(report_dates)
                ):
                    st.session_state["report_compare_dates_signature"] = tuple(
                        report_dates
                    )
                    st.session_state["report_compare_idx"] = default_cmp_idx
                cmp_idx = st.selectbox(
                    "비교일",
                    range(n_dates),
                    format_func=lambda i: date_labels[i],
                    key="report_compare_idx",
                )

            selected_compare = report_dates[cmp_idx]
            auto_base = report_default_base_date(report_dates, selected_compare)
            auto_base_idx = report_dates.index(auto_base)

            with col_base:
                base_state_key = "report_base_idx"
                last_cmp_key = "report_last_cmp_idx"
                if st.session_state.get(last_cmp_key) != cmp_idx:
                    st.session_state[last_cmp_key] = cmp_idx
                    st.session_state[base_state_key] = auto_base_idx
                if base_state_key not in st.session_state:
                    st.session_state[base_state_key] = auto_base_idx
                base_idx = st.selectbox(
                    "기준일 (수정 가능)",
                    range(n_dates),
                    format_func=lambda i: date_labels[i],
                    key=base_state_key,
                )

            base_date_r = report_dates[base_idx]
            compare_date_r = report_dates[cmp_idx]

            if base_date_r == compare_date_r:
                st.info(
                    "기준일과 비교일이 같습니다. 다른 날짜를 선택하면 증감이 표시됩니다."
                )

            day_gap = (compare_date_r - base_date_r).days
            st.markdown(
                f"**기준일** {base_date_r.strftime('%Y-%m-%d')}  →  "
                f"**비교일** {compare_date_r.strftime('%Y-%m-%d')}  "
                f"(간격: **{day_gap}일**)"
            )

            snapshot_raw = build_weekly_aum_snapshot(
                report_source, compare_date_r
            )
            delta_raw = build_weekly_aum_delta(
                report_source, base_date_r, compare_date_r
            )
            snapshot_display = format_aum_table(snapshot_raw, signed=False)
            delta_display = format_aum_table(delta_raw, signed=True)

            def _signed_color(val: str) -> str:
                if not isinstance(val, str):
                    return ""
                if val.startswith("+"):
                    return "color: #ff6b6b; font-weight: 600"
                if val.startswith("-") and val != "-":
                    return "color: #4dabf7; font-weight: 600"
                return ""

            common_styles = [
                {"selector": "th", "props": [("text-align", "center")]},
                {"selector": "td", "props": [("text-align", "center")]},
            ]

            col_snap, col_delta = st.columns(2)
            with col_snap:
                st.markdown(
                    f"##### 수탁고 · {compare_date_r.strftime('%Y-%m-%d')} 기준"
                )
                snap_idx = snapshot_display.set_index("운용사")
                snap_styler = snap_idx.style.set_table_styles(common_styles)
                st.dataframe(
                    snap_styler,
                    use_container_width=True,
                    height=48 + len(snap_idx) * 38,
                )

            with col_delta:
                st.markdown(
                    f"##### 변동 · {base_date_r.strftime('%y/%m/%d')} → "
                    f"{compare_date_r.strftime('%y/%m/%d')}"
                )
                delta_idx = delta_display.set_index("운용사")
                delta_styler = delta_idx.style.set_table_styles(common_styles)
                for col in delta_idx.columns:
                    delta_styler = delta_styler.map(_signed_color, subset=[col])
                st.dataframe(
                    delta_styler,
                    use_container_width=True,
                    height=48 + len(delta_idx) * 38,
                )

            summary_lines = build_weekly_aum_summary_lines(
                snapshot_raw, delta_raw
            )
            st.markdown("---")
            st.caption("보고용 요약 (복사용)")
            st.text("\n".join(summary_lines))

    inject_toolbar_refresh_font()


if __name__ == "__main__":
    main()
