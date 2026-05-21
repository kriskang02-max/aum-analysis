"""엑셀 수탁고(설정규모) 데이터 로드 및 증감 계산."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

FUND_TYPES = ("공모", "사모", "일임")
ASSET_CLASSES = (
    "채권",
    "단기금융",
    "주식",
    "혼합채권",
    "혼합주식",
    "파생형",
    "부동산",
    "특별자산",
    "혼합자산",
    "투자일임기타",
)
ASSET_CLASS_SET = frozenset(ASSET_CLASSES)
FILE_PATTERN = re.compile(r"^(공모|사모|일임)_(\d{6})\.xlsx$", re.IGNORECASE)
SKIP_COMPANY = re.compile(r"소계|^\s*합계\s*$")
EXCLUDED_COMPANY_NAMES = frozenset({"(기타)", "（기타）"})
UNIT_LABEL = "억원"


def is_excluded_company(name: str) -> bool:
    """소계·합계·(기타) 등 집계/기타 행 제외."""
    if not name or SKIP_COMPANY.search(name):
        return True
    normalized = re.sub(r"\s+", "", str(name).strip())
    return normalized in EXCLUDED_COMPANY_NAMES


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def discover_data_dirs() -> list[Path]:
    root = project_root()
    dirs = [root / "data", root]
    return [d for d in dirs if d.is_dir()]


def parse_filename(path: Path) -> tuple[str, str] | None:
    m = FILE_PATTERN.match(path.name)
    if not m:
        return None
    fund_type, yymmdd = m.group(1), m.group(2)
    yy, mm, dd = int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:6])
    year = 2000 + yy
    date_str = f"{year:04d}-{mm:02d}-{dd:02d}"
    return fund_type, date_str


def _normalize_label(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", "", str(value).replace("\n", ""))


def asset_columns_for_file(path: Path) -> dict[str, str]:
    """자산군 라벨 -> header=2 기준 DataFrame 컬럼명."""
    preview = pd.read_excel(path, header=None, nrows=4)
    row2 = [_normalize_label(preview.iloc[2, c]) for c in preview.columns]
    row3 = [_normalize_label(preview.iloc[3, c]) for c in preview.columns]
    raw_cols = list(pd.read_excel(path, header=2, nrows=0).columns)

    mapping: dict[str, str] = {}
    for idx, col_name in enumerate(raw_cols):
        sub = row3[idx] if idx < len(row3) else ""
        top = row2[idx] if idx < len(row2) else ""
        label = sub if sub in ASSET_CLASS_SET else top
        if label in ASSET_CLASS_SET:
            mapping[label] = col_name
    return mapping


def parse_amount(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip().replace(",", "")
    if s in ("", "-", "nan", "NaN"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_single_file(path: Path) -> pd.DataFrame:
    meta = parse_filename(path)
    if meta is None:
        raise ValueError(f"파일명 형식이 올바르지 않습니다: {path.name}")

    fund_type, as_of = meta
    asset_cols = asset_columns_for_file(path)
    if not asset_cols:
        raise ValueError(f"자산군 컬럼을 찾을 수 없습니다: {path}")

    raw = pd.read_excel(path, header=2, sheet_name=0)
    if "회사명" not in raw.columns:
        raise ValueError(f"필수 컬럼(회사명)이 없습니다: {path}")

    rows = []
    for _, row in raw.iterrows():
        name = row.get("회사명")
        if pd.isna(name):
            continue
        name = str(name).strip()
        if is_excluded_company(name):
            continue

        for asset, col in asset_cols.items():
            amount = parse_amount(row.get(col))
            if amount is None:
                continue
            rows.append(
                {
                    "운용사": name,
                    "유형": fund_type,
                    "자산": asset,
                    "기준일": as_of,
                    "수탁고": amount,
                    "파일": path.name,
                }
            )

    return pd.DataFrame(rows)


def filter_aum(
    df: pd.DataFrame,
    *,
    fund_types: list[str] | None = None,
    assets: list[str] | None = None,
) -> pd.DataFrame:
    if assets and "자산" not in df.columns:
        raise KeyError(
            "데이터에 '자산' 컬럼이 없습니다. "
            "Streamlit 메뉴(⋮) → Clear cache 후 페이지를 새로고침해 주세요."
        )
    out = df
    if fund_types:
        out = out[out["유형"].isin(fund_types)]
    if assets:
        out = out[out["자산"].isin(assets)]
    return out


def aggregate_type_date(df: pd.DataFrame) -> pd.DataFrame:
    """선택 자산 합산: 운용사·유형·기준일 단위."""
    return (
        df.groupby(["운용사", "유형", "기준일"], as_index=False)["수탁고"]
        .sum()
        .sort_values(["기준일", "유형", "운용사"])
    )


def find_excel_files() -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for directory in discover_data_dirs():
        for path in sorted(directory.glob("*.xlsx")):
            resolved = path.resolve()
            if resolved in seen or parse_filename(path) is None:
                continue
            seen.add(resolved)
            files.append(path)
    return files


def excel_files_signature() -> str:
    """엑셀 추가·수정 시 캐시 무효화용 (파일명 + 수정 시각)."""
    parts = []
    for path in find_excel_files():
        stat = path.stat()
        parts.append(f"{path.name}:{stat.st_mtime_ns}:{stat.st_size}")
    return "|".join(parts)


def load_all_aum() -> pd.DataFrame:
    paths = find_excel_files()
    if not paths:
        raise FileNotFoundError(
            "엑셀 파일을 찾을 수 없습니다. "
            f"'{{유형}}_YYMMDD.xlsx' 형식(예: 공모_251231.xlsx)으로 "
            f"{project_root() / 'data'} 또는 프로젝트 루트에 넣어 주세요."
        )

    frames = [load_single_file(p) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    df["기준일"] = pd.to_datetime(df["기준일"])
    df = df[~df["운용사"].map(lambda n: is_excluded_company(str(n)))].copy()
    return df.sort_values(
        ["기준일", "유형", "자산", "운용사"]
    ).reset_index(drop=True)


def add_period_changes(df: pd.DataFrame) -> pd.DataFrame:
    """동일 유형·자산·운용사 기준 직전 기준일 대비 증감."""
    out = df.copy()
    out = out.sort_values(["유형", "자산", "운용사", "기준일"])
    out["이전_수탁고"] = out.groupby(["유형", "자산", "운용사"])["수탁고"].shift(1)
    out["증감"] = out["수탁고"] - out["이전_수탁고"]
    out["증감률"] = (out["증감"] / out["이전_수탁고"].replace(0, pd.NA)) * 100
    return out


def compare_dates(
    df: pd.DataFrame,
    base_date: pd.Timestamp,
    compare_date: pd.Timestamp,
    fund_types: list[str] | None = None,
    assets: list[str] | None = None,
) -> pd.DataFrame:
    """두 기준일 간 운용사·유형별 증감 (선택 자산 합산)."""
    subset = aggregate_type_date(filter_aum(df, fund_types=fund_types, assets=assets))
    base_ts = pd.Timestamp(base_date).normalize()
    cmp_ts = pd.Timestamp(compare_date).normalize()
    day = subset["기준일"].apply(lambda x: pd.Timestamp(x).normalize())

    base = subset.loc[day == base_ts, ["운용사", "유형", "수탁고"]].rename(
        columns={"수탁고": "기준_수탁고"}
    )
    comp = subset.loc[day == cmp_ts, ["운용사", "유형", "수탁고"]].rename(
        columns={"수탁고": "비교_수탁고"}
    )
    merged = base.merge(comp, on=["운용사", "유형"], how="outer")
    merged["기준일"] = base_ts
    merged["비교일"] = cmp_ts
    merged["기준_수탁고"] = merged["기준_수탁고"].fillna(0)
    merged["비교_수탁고"] = merged["비교_수탁고"].fillna(0)
    merged["증감"] = merged["비교_수탁고"] - merged["기준_수탁고"]
    merged["증감률"] = (
        merged["증감"] / merged["기준_수탁고"].replace(0, pd.NA) * 100
    )
    return merged.sort_values(["유형", "증감"], ascending=[True, False])
