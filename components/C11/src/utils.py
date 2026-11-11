from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd


def ensure_dirs(paths: Iterable[Path]) -> None:
    """Create directories if they do not already exist.

    This helper accepts directory paths. File paths should be passed as
    path.parent by the calling function.
    """
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def ensure_parent_dir(path: Path) -> None:
    """Create the parent directory for a file path."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def safe_read_csv(path: Path, **kwargs) -> Optional[pd.DataFrame]:
    """Read a CSV file if it exists and contains rows.

    Returns None when the file is missing, unreadable, or empty. This is useful
    for optional governance, validation, and source-status artifacts.
    """
    try:
        if path is None:
            return None

        path = Path(path)

        if not path.exists():
            return None

        df = pd.read_csv(path, **kwargs)

        if df.empty:
            return None

        return df

    except Exception:
        return None


def safe_write_csv(df: pd.DataFrame, path: Path, index: bool = False, **kwargs) -> None:
    """Write a CSV after ensuring the parent directory exists."""
    ensure_parent_dir(path)
    df.to_csv(path, index=index, **kwargs)


def min_max_scale(
    series: pd.Series,
    floor: float = 0,
    ceiling: float = 100,
) -> pd.Series:
    """Scale a numeric series to a floor-ceiling range.

    Missing/non-numeric values are treated as zero. If all values are equal,
    the function returns the floor value for every row.
    """
    series = pd.to_numeric(series, errors="coerce").fillna(0)

    min_v = series.min()
    max_v = series.max()

    if math.isclose(float(max_v), float(min_v)):
        return pd.Series([floor for _ in series], index=series.index)

    return floor + (series - min_v) * (ceiling - floor) / (max_v - min_v)


def clip_0_100(series: pd.Series) -> pd.Series:
    """Coerce a series to numeric values and clip to the 0-100 score range."""
    return pd.to_numeric(series, errors="coerce").fillna(0).clip(0, 100)


def normalize_bool_series(series: pd.Series, default: bool = False) -> pd.Series:
    """Normalize mixed boolean/string fields into booleans.

    Useful for artifact fields such as success_status, has_observations,
    candidate_available, and official_baseline_used_in_scoring.
    """
    if series is None:
        return pd.Series(dtype=bool)

    truthy = {
        "true",
        "1",
        "yes",
        "y",
        "live",
        "available",
        "pass",
        "passed",
        "created",
        "fresh",
    }
    falsy = {
        "false",
        "0",
        "no",
        "n",
        "fallback",
        "not_available",
        "missing",
        "empty",
        "failed",
        "fail",
        "",
    }

    def normalize(value: object) -> bool:
        if isinstance(value, bool):
            return value

        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default

        text = str(value).strip().lower()

        if text in truthy:
            return True

        if text in falsy:
            return False

        return default

    return series.apply(normalize).astype(bool)


def safe_unique_text(
    df: Optional[pd.DataFrame],
    column: str,
    max_items: int = 5,
    fallback: str = "",
) -> str:
    """Return a compact semicolon-separated list of unique text values."""
    if df is None or df.empty or column not in df.columns:
        return fallback

    values = (
        df[column]
        .dropna()
        .astype(str)
        .map(str.strip)
        .loc[lambda s: s.ne("")]
        .drop_duplicates()
        .head(max_items)
        .tolist()
    )

    if not values:
        return fallback

    return "; ".join(values)


def unique_text_values(
    df: Optional[pd.DataFrame],
    column: str,
    max_items: int | None = None,
) -> list[str]:
    """Return unique non-empty string values from an optional dataframe column."""
    if df is None or df.empty or column not in df.columns:
        return []

    values = (
        df[column]
        .dropna()
        .astype(str)
        .map(str.strip)
        .loc[lambda s: s.ne("")]
        .drop_duplicates()
        .tolist()
    )

    if max_items is not None:
        return values[:max_items]

    return values


def unique_values_from_tables(
    tables: Iterable[Optional[pd.DataFrame]],
    column: str,
    max_items: int | None = None,
) -> list[str]:
    """Return sorted unique non-empty values from one column across tables."""
    values: set[str] = set()

    for table in tables:
        if table is None or table.empty or column not in table.columns:
            continue

        for value in table[column].dropna().astype(str):
            cleaned = value.strip()
            if cleaned:
                values.add(cleaned)

    out = sorted(values)

    if max_items is not None:
        return out[:max_items]

    return out


def count_true_values(df: Optional[pd.DataFrame], column: str) -> int:
    """Count truthy values in an optional dataframe column."""
    if df is None or df.empty or column not in df.columns:
        return 0

    return int(normalize_bool_series(df[column]).sum())


def boolean_field_ok(
    tables: Iterable[Optional[pd.DataFrame]],
    column: str,
    expected: bool = False,
) -> bool:
    """Return True when all present boolean-like values match expected.

    This is useful for governance artifacts where fields such as
    used_in_waris_scoring and used_in_monte_carlo must remain False.
    """
    found_any = False

    for table in tables:
        if table is None or table.empty or column not in table.columns:
            continue

        found_any = True
        normalized = normalize_bool_series(table[column], default=expected)

        if not bool((normalized == expected).all()):
            return False

    return found_any


def add_constant_control_fields(
    df: pd.DataFrame,
    controls: dict[str, Any],
) -> pd.DataFrame:
    """Attach constant control/governance fields to an artifact dataframe."""
    if df is None or df.empty:
        return df

    out = df.copy()

    for column, value in controls.items():
        out[column] = value

    return out


def latest_period_value(
    df: Optional[pd.DataFrame],
    period_col: str,
    value_col: str,
) -> tuple[str, object]:
    """Return the latest period and value from a dataframe.

    This helper is intentionally generic. It is useful for validation-only
    official baseline artifacts where the model needs to display the latest
    available observation without blending it into scoring.
    """
    if (
        df is None
        or df.empty
        or period_col not in df.columns
        or value_col not in df.columns
    ):
        return "", ""

    working = df[[period_col, value_col]].copy()
    working["_period_dt"] = pd.to_datetime(working[period_col], errors="coerce")
    working = working.dropna(subset=["_period_dt"])

    if working.empty:
        return "", ""

    row = working.sort_values("_period_dt").tail(1).iloc[0]

    return row["_period_dt"].strftime("%Y-%m-%d"), row[value_col]


def normalize_waris_oblast_name(value: object) -> str:
    """Normalize common Ukrstat/source oblast labels to WARIS canonical names.

    The function is kept in utils so modules that need lightweight geography
    alignment do not need to import data_collection.py and risk circular imports.
    Unknown values are returned as stripped text for downstream validation.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""

    text = str(value).strip()

    if not text:
        return ""

    mapping = {
        "Cherkaska": "Cherkasy",
        "Chernihivska": "Chernihiv",
        "Chernivetska": "Chernivtsi",
        "Dnipropetrovska": "Dnipropetrovsk",
        "Donetska": "Donetsk",
        "Ivano-Frankivska": "Ivano-Frankivsk",
        "Kharkivska": "Kharkiv",
        "Khersonska": "Kherson",
        "Khmelnytska": "Khmelnytskyi",
        "Kirovohradska": "Kirovohrad",
        "Kyivska": "Kyiv",
        "Luhanska": "Luhansk",
        "Lvivska": "Lviv",
        "Mykolaivska": "Mykolaiv",
        "Odeska": "Odesa",
        "Poltavska": "Poltava",
        "Rivnenska": "Rivne",
        "Sumska": "Sumy",
        "Ternopilska": "Ternopil",
        "Vinnytska": "Vinnytsia",
        "Volynska": "Volyn",
        "Zakarpatska": "Zakarpattia",
        "Zaporizka": "Zaporizhzhia",
        "Zhytomyrska": "Zhytomyr",
        "Kyiv": "Kyiv City",
        "Kyiv City": "Kyiv City",
        "City of Kyiv": "Kyiv City",
    }

    return mapping.get(text, text)


def normalize_waris_oblast_series(series: pd.Series) -> pd.Series:
    """Normalize a pandas Series of oblast labels to WARIS canonical names."""
    if series is None:
        return pd.Series(dtype=str)

    return series.apply(normalize_waris_oblast_name).astype(str)


def artifact_exists(path: Path | str | None) -> bool:
    """Return True when an artifact path exists and has nonzero size.

    This is shared by governance, run-manifest, source-freshness, and reporting
    modules so artifact availability is evaluated consistently.
    """
    try:
        if path is None:
            return False

        path = Path(path)
        return path.exists() and path.stat().st_size > 0
    except Exception:
        return False


def artifact_file_size(path: Path | str | None) -> int:
    """Return artifact file size in bytes or zero if unavailable."""
    try:
        if path is None:
            return 0

        path = Path(path)

        if not path.exists():
            return 0

        return int(path.stat().st_size)
    except Exception:
        return 0


def artifact_row_count(path: Path | str | None) -> int:
    """Return CSV row count for an optional artifact."""
    if path is None:
        return 0

    df = safe_read_csv(Path(path))
    return 0 if df is None else int(len(df))


def summary_value_for_area(
    df: Optional[pd.DataFrame],
    summary_area: str,
    value_column: str = "value",
    fallback: str = "not_available",
) -> str:
    """Return one value from a standard summary table.

    Many WARIS governance artifacts use a summary table with summary_area,
    status, value, and recommended_next_action columns. This helper keeps
    lookups consistent across model governance, source confidence, live status,
    run manifest, Monte Carlo controls, and report generation.
    """
    if df is None or df.empty or "summary_area" not in df.columns:
        return fallback

    rows = df[
        df["summary_area"]
        .fillna("")
        .astype(str)
        .eq(summary_area)
    ]

    if rows.empty:
        return fallback

    value = rows.iloc[0].get(value_column, fallback)

    if pd.isna(value):
        return fallback

    return str(value)


def summary_status_for_area(
    df: Optional[pd.DataFrame],
    summary_area: str,
    fallback: str = "not_available",
) -> str:
    """Return one status value from a standard summary table."""
    return summary_value_for_area(
        df=df,
        summary_area=summary_area,
        value_column="status",
        fallback=fallback,
    )


def summary_action_for_area(
    df: Optional[pd.DataFrame],
    summary_area: str,
    fallback: str = "not_available",
) -> str:
    """Return one recommended action from a standard summary table."""
    return summary_value_for_area(
        df=df,
        summary_area=summary_area,
        value_column="recommended_next_action",
        fallback=fallback,
    )


def table_status(
    path: Path | str | None,
    required_columns: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Return a compact status dictionary for an optional CSV table.

    This helper is intended for source-freshness, run-manifest, and governance
    controls. It does not validate analytical quality; it only documents whether
    an expected artifact is present, populated, and structurally usable.
    """
    exists = artifact_exists(path)
    row_count = artifact_row_count(path) if exists else 0
    columns_present: list[str] = []
    missing_columns: list[str] = []

    df = safe_read_csv(Path(path)) if exists and path is not None else None

    if df is not None:
        columns_present = list(df.columns)

    if required_columns is not None:
        required = [str(col) for col in required_columns]
        missing_columns = [
            col for col in required if col not in set(columns_present)
        ]

    if not exists:
        status = "missing"
    elif row_count <= 0:
        status = "empty"
    elif missing_columns:
        status = "missing_required_columns"
    else:
        status = "available"

    return {
        "path": "" if path is None else str(path),
        "exists": exists,
        "row_count": row_count,
        "file_size_bytes": artifact_file_size(path),
        "columns_present": columns_present,
        "missing_columns": missing_columns,
        "status": status,
    }


def controls_no_score_change_ok(
    tables: Iterable[Optional[pd.DataFrame]],
    production_score_change_column: str = "production_score_change",
    expected_value: str = "none",
) -> bool:
    """Return True when all present score-change fields match the expected value."""
    found_any = False

    for table in tables:
        if (
            table is None
            or table.empty
            or production_score_change_column not in table.columns
        ):
            continue

        found_any = True
        values = (
            table[production_score_change_column]
            .fillna("")
            .astype(str)
            .map(str.strip)
            .str.lower()
        )

        if not bool(values.eq(expected_value.lower()).all()):
            return False

    return found_any


def non_scoring_control_ok(
    tables: Iterable[Optional[pd.DataFrame]],
    scoring_column: str = "used_in_waris_scoring",
    monte_carlo_column: str = "used_in_monte_carlo",
    production_score_change_column: str = "production_score_change",
) -> bool:
    """Return True when no-scoring, no-Monte-Carlo, and no-score-change controls hold.

    This is designed for review-only and operational-control artifacts such as
    expanded Prozorro, FIU/SFMS context, wartime typology, analyst-review,
    false-positive, source-freshness, and run-manifest outputs.
    """
    score_change_ok = controls_no_score_change_ok(
        tables=tables,
        production_score_change_column=production_score_change_column,
        expected_value="none",
    )
    scoring_ok = boolean_field_ok(tables, scoring_column, expected=False)
    monte_carlo_ok = boolean_field_ok(tables, monte_carlo_column, expected=False)

    return bool(score_change_ok and scoring_ok and monte_carlo_ok)


def standard_non_scoring_note(
    artifact_label: str,
    current_use: str,
    production_score_change: str = "none",
) -> str:
    """Return standard plain-language no-scoring note for generated artifacts."""
    return (
        f"{artifact_label} is a review, source-support, governance, or "
        f"operational-control artifact only. current_use={current_use}; "
        f"production_score_change={production_score_change}. It is not used in "
        "WARIS risk-layer calculation, composite scoring, risk-band assignment, "
        "review-rationale generation, automated adverse action, entity-level "
        "findings, or Monte Carlo score simulation unless a future governed model "
        "change explicitly approves that use."
    )


def current_use_is_review_only(value: object) -> bool:
    """Return True for common WARIS review-only/control-only current-use labels."""
    text = "" if value is None else str(value).strip().lower()

    review_only_markers = [
        "review",
        "context",
        "benchmark",
        "support",
        "documentation",
        "freshness",
        "manifest",
        "workflow",
        "lineage",
        "governance",
        "typology_reference",
        "source_confidence",
    ]

    return any(marker in text for marker in review_only_markers)


def compact_counts(values: pd.Series | Iterable[Any]) -> dict[str, int]:
    """Return compact value counts as a normal dict with string keys."""
    if isinstance(values, pd.Series):
        series = values
    else:
        series = pd.Series(list(values))

    if series.empty:
        return {}

    return (
        series.fillna("missing")
        .astype(str)
        .map(str.strip)
        .replace("", "missing")
        .value_counts()
        .to_dict()
    )


def normalize_status_text(value: object, fallback: str = "not_available") -> str:
    """Normalize status-like values into compact text for reports/tables."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback

    text = str(value).strip()

    if not text:
        return fallback

    return text


def official_baseline_observations(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep actual finite, positive, dated GRP rows, not availability notices.

    This identifies observations only; it does not validate geography, units,
    source rights, or approve benchmark/scoring use.
    """
    required = {"oblast", "official_regional_baseline_proxy", "latest_period"}
    if frame.empty or not required.issubset(frame.columns):
        return frame.iloc[:0].copy()
    values = pd.to_numeric(frame["official_regional_baseline_proxy"], errors="coerce")
    periods = frame["latest_period"].astype(str).str.replace(r"^(\d{4})\.0$", r"\1", regex=True)
    dates = pd.to_datetime(periods, errors="coerce", format="mixed")
    mask = (frame["oblast"].fillna("").astype(str).str.strip().ne("")
            & values.between(0, float("inf"), inclusive="neither") & dates.notna())
    if "source_status" in frame:
        mask &= ~frame["source_status"].fillna("").astype(str).str.contains(
            "unavailable|missing|not_parsed", case=False, regex=True)
    return frame.loc[mask].copy()


def read_optional_dashboard_csv(path: Path) -> pd.DataFrame | None:
    """Treat missing or columnless optional artifacts as unavailable.

    Parse failures in populated artifacts remain errors; they must not silently
    become an absent source or a successful empty dataset.
    """
    try:
        return pd.read_csv(path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return None
