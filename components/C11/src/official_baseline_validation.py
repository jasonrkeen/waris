"""Official baseline validation controls for WARIS.

This module validates official Ukrstat regional baseline candidate readiness
before any scoring integration. It does not blend official values into WARIS
scoring.

Confirmed candidate pattern:
    DF_REGIONAL_ACCOUNTS
    GRP.<REGION>._Z.A
    dimensionAtObservation=TIME_PERIOD

Latest enhancement:
    If a Ukrstat Dataset Explorer CSV export is available in data/raw, this
    module uses it as official unit/scale evidence for the GRP series.

    The current validation decision also points to the controlled merge-review
    outputs, the official-baseline-to-Prozorro context-review outputs, the
    official-baseline-to-wartime-typology context-review outputs, the
    official-baseline-to-FIU/SFMS context-review outputs, and the
    official-baseline-to-operational-controls context-review outputs as the next
    review layer before any future scoring-integration discussion.

    Expanded Prozorro procurement features, wartime AML/CFT typology artifacts,
    official FIU/SFMS context artifacts, analyst-review outputs, false-positive
    controls, source-freshness outputs, and run-manifest artifacts remain
    review/source-support/documentation artifacts. They are not official baseline
    inputs and are not scoring inputs.

Expected Dataset Explorer export filename pattern:
    dataset_*DF_REGIONAL_ACCOUNTS*.csv

Decision posture:
    GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION
        Official values have enough source, unit, coverage, geography, endpoint,
        parser, merge-planning, and merge-review evidence to support controlled
        benchmarking against WARIS synthetic baselines, but they still do not
        affect scoring.

    CONDITIONAL_GO_FOR_VALIDATION_AND_BENCHMARKING_ONLY
        Official values may be used for validation, reporting context, source
        lineage, and benchmark comparison, but not for risk-layer calculation or
        composite scoring.

    GO_FOR_SCORING_AFTER_VALIDATION
        Reserved for a later version after transformation logic, SME review, and
        controlled scoring-integration change management are documented.

    NO_GO
        Required artifacts are missing or a critical scoring-control failure is
        detected.
"""

from __future__ import annotations

from .utils import official_baseline_observations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config import RAW_DIR, TABLE_DIR
from .utils import ensure_dirs

try:
    from .config import (
        UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE,
        UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE,
        UKRSTAT_CONFIRMED_SERIES_PARSED_TABLE,
    )
except ImportError:
    UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE = (
        TABLE_DIR / "ukrstat_oblast_baseline_candidates.csv"
    )
    UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE = (
        TABLE_DIR / "ukrstat_oblast_baseline_probe_results.csv"
    )
    UKRSTAT_CONFIRMED_SERIES_PARSED_TABLE = (
        TABLE_DIR / "ukrstat_confirmed_series_parsed.csv"
    )


OFFICIAL_BASELINE_VALIDATION_REGISTER_TABLE = (
    TABLE_DIR / "official_baseline_validation_register.csv"
)
OFFICIAL_BASELINE_VALIDATION_SUMMARY_TABLE = (
    TABLE_DIR / "official_baseline_validation_summary.csv"
)
OFFICIAL_BASELINE_GEOGRAPHY_CROSSWALK_CHECK_TABLE = (
    TABLE_DIR / "official_baseline_geography_crosswalk_check.csv"
)
OFFICIAL_BASELINE_PERIOD_COVERAGE_TABLE = (
    TABLE_DIR / "official_baseline_period_coverage.csv"
)
OFFICIAL_BASELINE_READINESS_DECISION_TABLE = (
    TABLE_DIR / "official_baseline_readiness_decision.csv"
)
OFFICIAL_BASELINE_UNIT_EVIDENCE_TABLE = (
    TABLE_DIR / "official_baseline_unit_evidence.csv"
)
OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE = (
    TABLE_DIR / "official_baseline_unit_evidence_summary.csv"
)

# Downstream controlled benchmark artifacts. These are not required to decide
# whether official GRP can be benchmarked, but when present they improve the
# next-decision guidance emitted by this validation module.
OFFICIAL_BASELINE_MERGE_PLAN_TABLE = (
    TABLE_DIR / "official_baseline_merge_plan.csv"
)
OFFICIAL_BASELINE_BENCHMARK_COMPARISON_TABLE = (
    TABLE_DIR / "official_baseline_benchmark_comparison.csv"
)
OFFICIAL_BASELINE_RESCALE_SCENARIO_TABLE = (
    TABLE_DIR / "official_baseline_rescale_scenario.csv"
)
OFFICIAL_BASELINE_REPLACE_OBLAST_BASELINE_SCENARIO_TABLE = (
    TABLE_DIR / "official_baseline_replace_oblast_baseline_scenario.csv"
)
OFFICIAL_BASELINE_MERGE_READINESS_SUMMARY_TABLE = (
    TABLE_DIR / "official_baseline_merge_readiness_summary.csv"
)
OFFICIAL_BASELINE_GAP_REVIEW_TABLE = (
    TABLE_DIR / "official_baseline_gap_review.csv"
)
OFFICIAL_BASELINE_SCENARIO_RECOMMENDATIONS_TABLE = (
    TABLE_DIR / "official_baseline_scenario_recommendations.csv"
)
OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_TABLE = (
    TABLE_DIR / "official_baseline_merge_review_summary.csv"
)
OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE = (
    TABLE_DIR / "official_baseline_prozorro_context_bridge.csv"
)
OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE = (
    TABLE_DIR / "official_baseline_prozorro_context_review.csv"
)
OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_TABLE = (
    TABLE_DIR / "official_baseline_wartime_typology_context_bridge.csv"
)
OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE = (
    TABLE_DIR / "official_baseline_wartime_typology_context_review.csv"
)
OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_TABLE = (
    TABLE_DIR / "official_baseline_fiu_context_bridge.csv"
)
OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE = (
    TABLE_DIR / "official_baseline_fiu_context_review.csv"
)
OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_TABLE = (
    TABLE_DIR / "official_baseline_operational_controls_context_bridge.csv"
)
OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE = (
    TABLE_DIR / "official_baseline_operational_controls_context_review.csv"
)

OFFICIAL_BASELINE_VALIDATION_AUDIT_RAW = (
    RAW_DIR / "official_baseline_validation_audit.csv"
)


DECISION_GO_FOR_SCORING = "GO_FOR_SCORING_AFTER_VALIDATION"
DECISION_GO_FOR_BENCHMARK_INTEGRATION = "GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION"
DECISION_CONDITIONAL_GO = "CONDITIONAL_GO_FOR_VALIDATION_AND_BENCHMARKING_ONLY"
DECISION_NO_GO = "NO_GO"

APPROVED_USE_SCORING = "controlled_scoring_integration_after_documented_validation"
APPROVED_USE_BENCHMARK_INTEGRATION = "controlled_benchmark_integration_only"
APPROVED_USE_BENCHMARKING = "validation_reporting_benchmarking_context_only"
APPROVED_USE_NONE = "no_use_until_artifacts_are_regenerated"

PROHIBITED_USE_SCORING = "risk_layer_calculation_or_composite_scoring"
PROHIBITED_USE_NONE_AFTER_VALIDATION = "none_after_approved_change_control"

try:
    from .config import (
        PROZORRO_PROCUREMENT_CURRENT_USE,
        PROZORRO_PROCUREMENT_PROHIBITED_USE,
        PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE,
    )
except ImportError:
    PROZORRO_PROCUREMENT_CURRENT_USE = "review_artifact_only"
    PROZORRO_PROCUREMENT_PROHIBITED_USE = "direct_scoring_without_change_control"
    PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE = "none"

try:
    from .config import (
        WARTIME_AML_TYPOLOGY_CURRENT_USE,
        WARTIME_AML_TYPOLOGY_PROHIBITED_USE,
        WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE,
        FIU_CONTEXT_CURRENT_USE,
        FIU_CONTEXT_PROHIBITED_USE,
        FIU_CONTEXT_PRODUCTION_SCORE_CHANGE,
    )
except ImportError:
    WARTIME_AML_TYPOLOGY_CURRENT_USE = (
        "literature_support_and_typology_reference_only"
    )
    WARTIME_AML_TYPOLOGY_PROHIBITED_USE = "direct_scoring_without_change_control"
    WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE = "none"
    FIU_CONTEXT_CURRENT_USE = "official_fiu_context_and_typology_support_only"
    FIU_CONTEXT_PROHIBITED_USE = "direct_scoring_without_change_control"
    FIU_CONTEXT_PRODUCTION_SCORE_CHANGE = "none"

try:
    from .config import (
        ANALYST_REVIEW_CURRENT_USE,
        ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
        FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
        SOURCE_FRESHNESS_CURRENT_USE,
        SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
        RUN_MANIFEST_CURRENT_USE,
        RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
    )
except ImportError:
    ANALYST_REVIEW_CURRENT_USE = "analyst_review_workflow_only"
    ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE = "none"
    FALSE_POSITIVE_CONTROLS_CURRENT_USE = "human_review_support_only"
    FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE = "none"
    SOURCE_FRESHNESS_CURRENT_USE = "source_freshness_monitoring_only"
    SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE = "none"
    RUN_MANIFEST_CURRENT_USE = "run_manifest_documentation"
    RUN_MANIFEST_PRODUCTION_SCORE_CHANGE = "none"


EXPECTED_WARIS_OBLASTS = [
    "Cherkasy",
    "Chernihiv",
    "Chernivtsi",
    "Dnipropetrovsk",
    "Donetsk",
    "Ivano-Frankivsk",
    "Kharkiv",
    "Kherson",
    "Khmelnytskyi",
    "Kirovohrad",
    "Kyiv",
    "Luhansk",
    "Lviv",
    "Mykolaiv",
    "Odesa",
    "Poltava",
    "Rivne",
    "Sumy",
    "Ternopil",
    "Vinnytsia",
    "Volyn",
    "Zakarpattia",
    "Zaporizhzhia",
    "Zhytomyr",
    "Kyiv City",
]


UKRSTAT_TO_WARIS_OBLAST = {
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


@dataclass(frozen=True)
class ValidationCheck:
    check_id: str
    validation_area: str
    check_name: str
    status: str
    severity: str
    evidence: str
    result_value: str
    expected_value: str
    current_use_in_scoring: str
    recommended_next_action: str
    notes: str


def _safe_read_csv(path: Path) -> pd.DataFrame:
    try:
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _normalize_oblast_name(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return UKRSTAT_TO_WARIS_OBLAST.get(text, text)


def _status_from_bool(ok: bool) -> str:
    return "pass" if ok else "review_required"


def _severity_from_bool(ok: bool, fail_severity: str = "high") -> str:
    return "info" if ok else fail_severity


def _unique_join(series: pd.Series, max_items: int = 6) -> str:
    values = (
        series.dropna()
        .astype(str)
        .map(str.strip)
        .loc[lambda s: s.ne("")]
        .drop_duplicates()
        .head(max_items)
        .tolist()
    )
    return "; ".join(values)


def _unique_values(df: pd.DataFrame, column: str) -> list[str]:
    """Return unique non-empty values from a dataframe column."""
    if df.empty or column not in df.columns:
        return []
    return (
        df[column]
        .fillna("")
        .astype(str)
        .map(str.strip)
        .loc[lambda s: s.ne("")]
        .drop_duplicates()
        .tolist()
    )


def _control_false_values_ok(df: pd.DataFrame, column: str) -> bool:
    """Return True if a boolean-like control column is present and all values are false."""
    if df.empty or column not in df.columns:
        return False
    values = set(df[column].fillna("").astype(str).str.lower().tolist())
    return values == {"false"}


def _candidate_columns() -> list[str]:
    return [
        "oblast",
        "waris_oblast",
        "region_code",
        "indicator_code",
        "indicator_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "latest_period",
        "official_regional_baseline_proxy",
        "unit",
        "updated",
        "source_status",
        "validation_status",
        "current_use_in_scoring",
        "geography_mapping_status",
        "period_validation_status",
        "unit_validation_status",
        "indicator_validation_status",
        "nace_validation_status",
        "scoring_gate_status",
        "candidate_readiness_status",
        "recommended_next_action",
        "notes",
    ]


def _find_dataset_explorer_exports() -> list[Path]:
    """Find Ukrstat Dataset Explorer regional accounts exports in data/raw."""
    if not RAW_DIR.exists():
        return []

    candidates = sorted(
        RAW_DIR.glob("dataset_*DF_REGIONAL_ACCOUNTS*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    return candidates


def _load_dataset_explorer_export() -> tuple[pd.DataFrame, Path | None]:
    """Load the newest Dataset Explorer export matching DF_REGIONAL_ACCOUNTS.

    Supports both Dataset Explorer export shapes seen in practice:

    1. Long SDMX-like format with code/name pairs:
       Indicator, Indicator.1, Region, Region.1, Time period, Observation value

    2. Wide Dataset Explorer format with year columns:
       Indicator, Region, Economic activity type, Frequency, Unit of measure,
       Scaling, Decimals displayed, 2002, 2003, ...
    """
    for path in _find_dataset_explorer_exports():
        df = _safe_read_csv(path)

        if df.empty:
            continue

        cols = set(df.columns)

        long_required = {
            "Indicator",
            "Indicator.1",
            "Region",
            "Region.1",
            "Economic activity type",
            "Economic activity type.1",
            "Frequency",
            "Frequency.1",
            "Time period",
            "Observation value",
            "Unit of measure",
            "Unit of measure.1",
            "Scaling",
            "Scaling.1",
        }

        wide_required = {
            "Indicator",
            "Region",
            "Economic activity type",
            "Frequency",
            "Unit of measure",
            "Scaling",
            "Decimals displayed",
        }

        year_cols = [col for col in df.columns if str(col).isdigit()]

        if long_required.issubset(cols) or (
            wide_required.issubset(cols) and len(year_cols) > 0
        ):
            return df, path

    return pd.DataFrame(), None


def _normalize_dataset_explorer_export(explorer: pd.DataFrame) -> pd.DataFrame:
    """Normalize long or wide Dataset Explorer exports to a common format."""
    if explorer.empty:
        return pd.DataFrame()

    cols = set(explorer.columns)

    long_required = {
        "Indicator",
        "Indicator.1",
        "Region",
        "Region.1",
        "Economic activity type",
        "Economic activity type.1",
        "Frequency",
        "Frequency.1",
        "Time period",
        "Observation value",
        "Unit of measure",
        "Unit of measure.1",
        "Scaling",
        "Scaling.1",
    }

    if long_required.issubset(cols):
        out = explorer.copy()

        for col in [
            "Indicator",
            "Indicator.1",
            "Region",
            "Region.1",
            "Economic activity type",
            "Economic activity type.1",
            "Frequency",
            "Frequency.1",
            "Time period",
            "Observation value",
            "Unit of measure",
            "Unit of measure.1",
            "Scaling",
            "Scaling.1",
            "Decimals displayed",
            "Decimals displayed.1",
        ]:
            if col not in out.columns:
                out[col] = ""

        normalized = pd.DataFrame(
            {
                "indicator_code": out["Indicator"],
                "indicator_name": out["Indicator.1"],
                "region_code": out["Region"],
                "region_name": out["Region.1"],
                "nace_code": out["Economic activity type"],
                "nace_name": out["Economic activity type.1"],
                "freq_code": out["Frequency"],
                "freq_name": out["Frequency.1"],
                "time_period": out["Time period"],
                "observation_value": out["Observation value"],
                "unit_code": out["Unit of measure"],
                "unit_name": out["Unit of measure.1"],
                "scaling_code": out["Scaling"],
                "scaling_name": out["Scaling.1"],
                "decimals_code": out["Decimals displayed"],
                "decimals_name": out["Decimals displayed.1"],
            }
        )

        return normalized

    # Wide Dataset Explorer export.
    working = explorer.copy()

    year_cols = [col for col in working.columns if str(col).isdigit()]

    for col in [
        "Indicator",
        "Region",
        "Economic activity type",
        "Frequency",
        "Unit of measure",
        "Scaling",
        "Decimals displayed",
    ]:
        if col not in working.columns:
            working[col] = ""

    id_vars = [
        "Indicator",
        "Region",
        "Economic activity type",
        "Frequency",
        "Unit of measure",
        "Scaling",
        "Decimals displayed",
    ]

    optional_note_cols = [
        "Observation flag",
        "Dataset notes",
        "Timeseries notes",
        "Observation notes",
    ]

    for col in optional_note_cols:
        if col in working.columns:
            id_vars.append(col)

    melted = working.melt(
        id_vars=id_vars,
        value_vars=year_cols,
        var_name="time_period",
        value_name="observation_value",
    )

    melted = melted.dropna(subset=["observation_value"]).copy()

    def indicator_code(value: object) -> str:
        text = str(value).strip()
        if text.lower() == "gross regional product":
            return "GRP"
        if text.lower() == "per capita gross regional product":
            return "GRP_PC"
        if text.lower() == "gross regional product per person employed":
            return "GRP_EMP"
        return text

    def nace_code(value: object) -> str:
        text = str(value).strip()
        if text.lower() == "not applicable":
            return "_Z"
        return text

    def freq_code(value: object) -> str:
        text = str(value).strip()
        if text.lower() == "annual":
            return "A"
        return text

    normalized = pd.DataFrame(
        {
            "indicator_code": melted["Indicator"].apply(indicator_code),
            "indicator_name": melted["Indicator"].fillna("").astype(str),
            "region_code": melted["Region"].fillna("").astype(str),
            "region_name": melted["Region"].fillna("").astype(str),
            "nace_code": melted["Economic activity type"].apply(nace_code),
            "nace_name": melted["Economic activity type"].fillna("").astype(str),
            "freq_code": melted["Frequency"].apply(freq_code),
            "freq_name": melted["Frequency"].fillna("").astype(str),
            "time_period": melted["time_period"],
            "observation_value": melted["observation_value"],
            "unit_code": melted["Unit of measure"].fillna("").astype(str),
            "unit_name": melted["Unit of measure"].fillna("").astype(str),
            "scaling_code": melted["Scaling"].fillna("").astype(str),
            "scaling_name": melted["Scaling"].fillna("").astype(str),
            "decimals_code": melted["Decimals displayed"].fillna("").astype(str),
            "decimals_name": melted["Decimals displayed"].fillna("").astype(str),
        }
    )

    return normalized


def build_official_baseline_unit_evidence() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build unit/scale evidence from a downloaded Dataset Explorer CSV.

    The target evidence confirms the official interpretation of:
        GRP.<REGION>._Z.A

    Expected evidence:
        indicator_name = Gross regional product
        nace_name = Not applicable
        freq_name = Annual
        unit_name = UAH
        scaling_name = Millions
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    explorer, source_path = _load_dataset_explorer_export()

    evidence_cols = [
        "source_file",
        "source_export_format",
        "indicator_code",
        "indicator_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "unit_code",
        "unit_name",
        "scaling_code",
        "scaling_name",
        "decimals_code",
        "decimals_name",
        "period_min",
        "period_max",
        "row_count",
        "region_count",
        "waris_region_count",
        "unit_interpretation",
        "validation_status",
        "current_use_in_scoring",
        "notes",
    ]

    if explorer.empty or source_path is None:
        evidence = pd.DataFrame(
            [
                {
                    "source_file": "",
                    "source_export_format": "",
                    "indicator_code": "GRP",
                    "indicator_name": "",
                    "nace_code": "_Z",
                    "nace_name": "",
                    "freq_code": "A",
                    "freq_name": "",
                    "unit_code": "",
                    "unit_name": "",
                    "scaling_code": "",
                    "scaling_name": "",
                    "decimals_code": "",
                    "decimals_name": "",
                    "period_min": "",
                    "period_max": "",
                    "row_count": 0,
                    "region_count": 0,
                    "waris_region_count": 0,
                    "unit_interpretation": "",
                    "validation_status": "dataset_explorer_export_not_found",
                    "current_use_in_scoring": "not_yet_used",
                    "notes": (
                        "Place the Ukrstat Dataset Explorer export CSV in data/raw. "
                        "Expected filename pattern: dataset_*DF_REGIONAL_ACCOUNTS*.csv."
                    ),
                }
            ],
            columns=evidence_cols,
        )
        evidence.to_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_TABLE, index=False)
        evidence.to_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE, index=False)
        return evidence, evidence.copy()

    source_format = "long_code_name_pairs" if "Indicator.1" in explorer.columns else "wide_year_columns"
    normalized = _normalize_dataset_explorer_export(explorer)

    if normalized.empty:
        evidence = pd.DataFrame(
            [
                {
                    "source_file": str(source_path),
                    "source_export_format": source_format,
                    "indicator_code": "GRP",
                    "indicator_name": "",
                    "nace_code": "_Z",
                    "nace_name": "",
                    "freq_code": "A",
                    "freq_name": "",
                    "unit_code": "",
                    "unit_name": "",
                    "scaling_code": "",
                    "scaling_name": "",
                    "decimals_code": "",
                    "decimals_name": "",
                    "period_min": "",
                    "period_max": "",
                    "row_count": 0,
                    "region_count": 0,
                    "waris_region_count": 0,
                    "unit_interpretation": "",
                    "validation_status": "dataset_explorer_export_normalization_failed",
                    "current_use_in_scoring": "not_yet_used",
                    "notes": "Dataset Explorer export was found but could not be normalized.",
                }
            ],
            columns=evidence_cols,
        )
        evidence.to_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_TABLE, index=False)
        evidence.to_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE, index=False)
        return evidence, evidence.copy()

    grp = normalized[
        normalized["indicator_code"].fillna("").astype(str).str.upper().eq("GRP")
        & normalized["nace_code"].fillna("").astype(str).str.upper().eq("_Z")
        & normalized["freq_code"].fillna("").astype(str).str.upper().eq("A")
    ].copy()

    if grp.empty:
        evidence = pd.DataFrame(
            [
                {
                    "source_file": str(source_path),
                    "source_export_format": source_format,
                    "indicator_code": "GRP",
                    "indicator_name": "",
                    "nace_code": "_Z",
                    "nace_name": "",
                    "freq_code": "A",
                    "freq_name": "",
                    "unit_code": "",
                    "unit_name": "",
                    "scaling_code": "",
                    "scaling_name": "",
                    "decimals_code": "",
                    "decimals_name": "",
                    "period_min": "",
                    "period_max": "",
                    "row_count": 0,
                    "region_count": 0,
                    "waris_region_count": 0,
                    "unit_interpretation": "",
                    "validation_status": "grp_z_annual_series_not_found",
                    "current_use_in_scoring": "not_yet_used",
                    "notes": (
                        "Dataset Explorer export was found, but GRP/_Z/A rows were "
                        "not detected."
                    ),
                }
            ],
            columns=evidence_cols,
        )
        evidence.to_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_TABLE, index=False)
        evidence.to_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE, index=False)
        return evidence, evidence.copy()

    grp["waris_oblast"] = grp["region_name"].apply(_normalize_oblast_name)
    grp["time_period_numeric"] = pd.to_numeric(grp["time_period"], errors="coerce")
    grp["observation_value_numeric"] = pd.to_numeric(
        grp["observation_value"],
        errors="coerce",
    )

    unique_waris_region_count = int(
        grp.loc[grp["waris_oblast"].isin(EXPECTED_WARIS_OBLASTS), "waris_oblast"]
        .drop_duplicates()
        .shape[0]
    )

    unit_names = grp["unit_name"].fillna("").astype(str).drop_duplicates().tolist()
    scaling_names = grp["scaling_name"].fillna("").astype(str).drop_duplicates().tolist()
    indicator_names = grp["indicator_name"].fillna("").astype(str).drop_duplicates().tolist()
    nace_names = grp["nace_name"].fillna("").astype(str).drop_duplicates().tolist()
    freq_names = grp["freq_name"].fillna("").astype(str).drop_duplicates().tolist()

    unit_ok = set(unit_names) == {"UAH"}
    scaling_ok = set(scaling_names) == {"Millions"}
    indicator_ok = "Gross regional product" in indicator_names
    nace_ok = "Not applicable" in nace_names
    freq_ok = "Annual" in freq_names

    validation_status = (
        "unit_scale_frequency_indicator_evidence_found"
        if all([unit_ok, scaling_ok, indicator_ok, nace_ok, freq_ok])
        else "unit_scale_frequency_indicator_review_required"
    )

    unit_interpretation = (
        "million UAH"
        if unit_ok and scaling_ok
        else f"{'; '.join(unit_names)} / {'; '.join(scaling_names)}"
    )

    evidence = pd.DataFrame(
        [
            {
                "source_file": str(source_path),
                "source_export_format": source_format,
                "indicator_code": _unique_join(grp["indicator_code"]),
                "indicator_name": _unique_join(grp["indicator_name"]),
                "nace_code": _unique_join(grp["nace_code"]),
                "nace_name": _unique_join(grp["nace_name"]),
                "freq_code": _unique_join(grp["freq_code"]),
                "freq_name": _unique_join(grp["freq_name"]),
                "unit_code": _unique_join(grp["unit_code"]),
                "unit_name": _unique_join(grp["unit_name"]),
                "scaling_code": _unique_join(grp["scaling_code"]),
                "scaling_name": _unique_join(grp["scaling_name"]),
                "decimals_code": _unique_join(grp["decimals_code"]),
                "decimals_name": _unique_join(grp["decimals_name"]),
                "period_min": str(int(grp["time_period_numeric"].min()))
                if pd.notna(grp["time_period_numeric"].min())
                else "",
                "period_max": str(int(grp["time_period_numeric"].max()))
                if pd.notna(grp["time_period_numeric"].max())
                else "",
                "row_count": len(grp),
                "region_count": int(grp["region_name"].drop_duplicates().shape[0]),
                "waris_region_count": unique_waris_region_count,
                "unit_interpretation": unit_interpretation,
                "validation_status": validation_status,
                "current_use_in_scoring": "not_yet_used",
                "notes": (
                    "Dataset Explorer export supports official interpretation of "
                    "GRP._Z.A as annual gross regional product in million UAH. "
                    "This supports controlled benchmarking, but does not automatically "
                    "approve risk-layer or composite-score use."
                ),
            }
        ],
        columns=evidence_cols,
    )

    detail_cols = [
        "indicator_code",
        "indicator_name",
        "region_code",
        "region_name",
        "waris_oblast",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "time_period",
        "observation_value",
        "unit_code",
        "unit_name",
        "scaling_code",
        "scaling_name",
        "decimals_code",
        "decimals_name",
    ]
    detail_cols = [col for col in detail_cols if col in grp.columns]

    grp[detail_cols].to_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_TABLE, index=False)
    evidence.to_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE, index=False)

    return grp[detail_cols], evidence



def _unit_evidence_status(unit_summary: pd.DataFrame) -> dict[str, str]:
    """Return compact unit-evidence status for validation checks."""
    if unit_summary is None or unit_summary.empty:
        return {
            "status": "dataset_explorer_export_not_found",
            "unit_interpretation": "",
            "evidence": str(OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE),
            "notes": "No unit-evidence summary was available.",
        }

    row = unit_summary.iloc[0]

    return {
        "status": str(row.get("validation_status", "")),
        "unit_interpretation": str(row.get("unit_interpretation", "")),
        "unit_name": str(row.get("unit_name", "")),
        "scaling_name": str(row.get("scaling_name", "")),
        "indicator_name": str(row.get("indicator_name", "")),
        "nace_name": str(row.get("nace_name", "")),
        "freq_name": str(row.get("freq_name", "")),
        "period_min": str(row.get("period_min", "")),
        "period_max": str(row.get("period_max", "")),
        "row_count": str(row.get("row_count", "")),
        "region_count": str(row.get("region_count", "")),
        "waris_region_count": str(row.get("waris_region_count", "")),
        "evidence": str(OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE),
        "notes": str(row.get("notes", "")),
    }


def load_and_normalize_candidates(
    candidates_path: Path = UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE,
) -> pd.DataFrame:
    """Load official baseline candidates and add validation helper columns."""
    candidates = _safe_read_csv(candidates_path)
    candidates = official_baseline_observations(candidates)

    if candidates.empty:
        return pd.DataFrame(columns=_candidate_columns())

    out = candidates.copy()

    for col in [
        "oblast",
        "region_code",
        "indicator_code",
        "indicator_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "latest_period",
        "official_regional_baseline_proxy",
        "unit",
        "updated",
        "source_status",
        "validation_status",
        "current_use_in_scoring",
        "recommended_next_action",
        "notes",
    ]:
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].fillna("").astype(str)

    out["waris_oblast"] = out["oblast"].apply(_normalize_oblast_name)
    out["official_regional_baseline_proxy_numeric"] = pd.to_numeric(
        out["official_regional_baseline_proxy"],
        errors="coerce",
    )
    out["latest_period_dt"] = pd.to_datetime(out["latest_period"], errors="coerce")

    out["geography_mapping_status"] = out["waris_oblast"].apply(
        lambda value: "mapped_to_expected_waris_oblast"
        if value in EXPECTED_WARIS_OBLASTS
        else "unmapped_or_unexpected_oblast"
    )
    out["period_validation_status"] = out["latest_period_dt"].apply(
        lambda value: "period_parseable_pending_coverage_validation"
        if pd.notna(value)
        else "period_unparseable"
    )
    out["unit_validation_status"] = out["unit"].apply(
        lambda value: "unit_missing_requires_validation"
        if str(value).strip() == ""
        else "unit_present_requires_meaning_validation"
    )
    out["indicator_validation_status"] = out["indicator_code"].apply(
        lambda value: "expected_grp_pending_meaning_validation"
        if str(value).strip().upper() == "GRP"
        else "unexpected_indicator_review_required"
    )
    out["nace_validation_status"] = out["nace_code"].apply(
        lambda value: "expected_z_pending_nace_meaning_validation"
        if str(value).strip().upper() == "_Z"
        else "unexpected_nace_review_required"
    )
    out["scoring_gate_status"] = out["current_use_in_scoring"].apply(
        lambda value: "scoring_gate_closed"
        if str(value).strip().lower() == "not_yet_used"
        else "scoring_gate_review_required"
    )
    out["candidate_readiness_status"] = "not_ready_for_scoring"

    return out[
        _candidate_columns()
        + ["official_regional_baseline_proxy_numeric", "latest_period_dt"]
    ]


def build_geography_crosswalk_check(candidates: pd.DataFrame) -> pd.DataFrame:
    """Build a geography coverage/crosswalk check table."""
    rows = []

    if candidates.empty:
        out = pd.DataFrame(
            [
                {
                    "waris_oblast": "",
                    "ukrstat_oblast": "",
                    "region_code": "",
                    "mapping_status": "candidate_table_missing_or_empty",
                    "coverage_status": "missing",
                    "notes": "No official baseline candidate rows were available.",
                }
            ]
        )
        out.to_csv(OFFICIAL_BASELINE_GEOGRAPHY_CROSSWALK_CHECK_TABLE, index=False)
        return out

    grouped = (
        candidates.groupby("waris_oblast", as_index=False)
        .agg(
            ukrstat_oblast=("oblast", lambda s: "; ".join(sorted(set(s.astype(str))))),
            region_code=("region_code", lambda s: "; ".join(sorted(set(s.astype(str))))),
            row_count=("waris_oblast", "size"),
            mapping_status=("geography_mapping_status", "first"),
        )
    )

    observed = set(grouped["waris_oblast"].dropna().astype(str))
    expected = set(EXPECTED_WARIS_OBLASTS)

    for oblast in EXPECTED_WARIS_OBLASTS:
        subset = grouped[grouped["waris_oblast"].eq(oblast)]

        if subset.empty:
            rows.append(
                {
                    "waris_oblast": oblast,
                    "ukrstat_oblast": "",
                    "region_code": "",
                    "mapping_status": "missing_mapping",
                    "coverage_status": "missing",
                    "notes": (
                        "Expected WARIS oblast did not appear in official candidate mapping."
                    ),
                }
            )
            continue

        row = subset.iloc[0].to_dict()
        duplicate_status = (
            "duplicate_candidate_rows"
            if int(row["row_count"]) > 1
            else "single_candidate_row"
        )

        rows.append(
            {
                "waris_oblast": oblast,
                "ukrstat_oblast": row.get("ukrstat_oblast", ""),
                "region_code": row.get("region_code", ""),
                "mapping_status": row.get("mapping_status", ""),
                "coverage_status": duplicate_status,
                "notes": (
                    "Official Ukrstat candidate maps to expected WARIS geography. "
                    "Still requires region-code and KATOTTG validation."
                ),
            }
        )

    for oblast in sorted(observed - expected):
        subset = grouped[grouped["waris_oblast"].eq(oblast)].iloc[0].to_dict()
        rows.append(
            {
                "waris_oblast": oblast,
                "ukrstat_oblast": subset.get("ukrstat_oblast", ""),
                "region_code": subset.get("region_code", ""),
                "mapping_status": "unexpected_mapping",
                "coverage_status": "unexpected",
                "notes": "Mapped oblast is not in the expected WARIS geography list.",
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(OFFICIAL_BASELINE_GEOGRAPHY_CROSSWALK_CHECK_TABLE, index=False)
    return out


def build_period_coverage(candidates: pd.DataFrame) -> pd.DataFrame:
    """Build a latest-period coverage table."""
    columns = [
        "latest_period",
        "candidate_count",
        "period_parseable_count",
        "period_coverage_status",
        "current_use_in_scoring",
        "notes",
    ]

    if candidates.empty:
        out = pd.DataFrame(
            [
                {
                    "latest_period": "",
                    "candidate_count": 0,
                    "period_parseable_count": 0,
                    "period_coverage_status": "candidate_table_missing_or_empty",
                    "current_use_in_scoring": "not_yet_used",
                    "notes": "No official baseline candidates were available.",
                }
            ],
            columns=columns,
        )
        out.to_csv(OFFICIAL_BASELINE_PERIOD_COVERAGE_TABLE, index=False)
        return out

    working = candidates.copy()
    working["latest_period"] = working["latest_period"].fillna("").astype(str)

    coverage = (
        working.groupby("latest_period", as_index=False)
        .agg(
            candidate_count=("latest_period", "size"),
            period_parseable_count=("latest_period_dt", lambda s: int(s.notna().sum())),
            current_use_in_scoring=(
                "current_use_in_scoring",
                lambda s: "; ".join(sorted(set(s.astype(str)))),
            ),
        )
    )

    expected_count = len(EXPECTED_WARIS_OBLASTS)

    coverage["period_coverage_status"] = coverage["candidate_count"].apply(
        lambda value: "full_expected_coverage_for_period"
        if int(value) == expected_count
        else "partial_or_unexpected_period_coverage"
    )
    coverage["notes"] = (
        "Latest-period coverage is a readiness check only. Confirm whether this "
        "period is appropriate for the intended revenue-baseline use before scoring."
    )

    coverage = coverage[columns]
    coverage.to_csv(OFFICIAL_BASELINE_PERIOD_COVERAGE_TABLE, index=False)
    return coverage


def build_validation_register(
    candidates: pd.DataFrame,
    probes: pd.DataFrame,
    confirmed_series: pd.DataFrame,
    geography_check: pd.DataFrame,
    period_coverage: pd.DataFrame,
    unit_evidence_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Build a control-by-control validation register."""
    checks: list[ValidationCheck] = []
    expected_count = len(EXPECTED_WARIS_OBLASTS)
    candidate_count = len(candidates)
    if {"obs_value", "time_period", "region_code"}.issubset(confirmed_series.columns):
        confirmed_series = confirmed_series.loc[
            pd.to_numeric(confirmed_series["obs_value"], errors="coerce").notna()
            & confirmed_series["time_period"].fillna("").astype(str).str.strip().ne("")
            & confirmed_series["region_code"].fillna("").astype(str).str.strip().ne("")
        ]
    else:
        confirmed_series = confirmed_series.iloc[:0]
    unit_status = _unit_evidence_status(unit_evidence_summary)

    checks.append(
        ValidationCheck(
            "OBV-001",
            "Artifact availability",
            "Official baseline candidate table exists and has rows",
            _status_from_bool(candidate_count > 0),
            _severity_from_bool(candidate_count > 0),
            str(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE),
            str(candidate_count),
            "> 0",
            "not_yet_used",
            "Run python -m src.ukrstat_observations if the artifact is missing.",
            "This confirms candidate availability only, not scoring readiness.",
        )
    )

    full_coverage = candidate_count == expected_count
    checks.append(
        ValidationCheck(
            "OBV-002",
            "Coverage",
            "Expected 25-region candidate coverage",
            _status_from_bool(full_coverage),
            _severity_from_bool(full_coverage),
            str(OFFICIAL_BASELINE_GEOGRAPHY_CROSSWALK_CHECK_TABLE),
            str(candidate_count),
            str(expected_count),
            "not_yet_used",
            "Investigate missing or duplicate geography rows before integration.",
            "WARIS expects 24 oblasts plus Kyiv City.",
        )
    )

    geography_failures = 0
    if not geography_check.empty and "coverage_status" in geography_check.columns:
        geography_failures = int(
            geography_check["coverage_status"]
            .astype(str)
            .isin(["missing", "unexpected", "duplicate_candidate_rows"])
            .sum()
        )
    geography_ok = geography_failures == 0 and full_coverage
    checks.append(
        ValidationCheck(
            "OBV-003",
            "Geography mapping",
            "Ukrstat names map to canonical WARIS oblast names",
            _status_from_bool(geography_ok),
            _severity_from_bool(geography_ok),
            str(OFFICIAL_BASELINE_GEOGRAPHY_CROSSWALK_CHECK_TABLE),
            f"{geography_failures} geography issues",
            "0 geography issues",
            "not_yet_used",
            "Validate KATOTTG region codes and name crosswalk with source documentation.",
            "Ukrstat uses adjectival oblast labels such as Dnipropetrovska.",
        )
    )

    scoring_values = []
    if not candidates.empty and "current_use_in_scoring" in candidates.columns:
        scoring_values = (
            candidates["current_use_in_scoring"]
            .fillna("")
            .astype(str)
            .drop_duplicates()
            .tolist()
        )
    scoring_gate_ok = set(scoring_values) == {"not_yet_used"}
    checks.append(
        ValidationCheck(
            "OBV-004",
            "Scoring gate",
            "Official baseline candidates are not used in scoring",
            _status_from_bool(scoring_gate_ok),
            _severity_from_bool(scoring_gate_ok, "critical"),
            str(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE),
            str(scoring_values),
            "['not_yet_used']",
            "not_yet_used",
            "Block release if official baseline values enter scoring before validation.",
            "This is the most important current model-risk control.",
        )
    )

    validation_values = []
    if not candidates.empty and "validation_status" in candidates.columns:
        validation_values = (
            candidates["validation_status"]
            .fillna("")
            .astype(str)
            .drop_duplicates()
            .tolist()
        )
    validation_gate_ok = set(validation_values) == {"pending_unit_and_mapping_validation"}
    checks.append(
        ValidationCheck(
            "OBV-005",
            "Validation gate",
            "Official baseline candidates remain pending validation",
            _status_from_bool(validation_gate_ok),
            _severity_from_bool(validation_gate_ok),
            str(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE),
            str(validation_values),
            "['pending_unit_and_mapping_validation']",
            "not_yet_used",
            (
                "Maintain pending status until unit, NACE, geography, indicator, "
                "period, transformation, and SME validation are documented."
            ),
            "A pending status is expected at this stage.",
        )
    )

    unit_evidence_ok = (
        unit_status["status"] == "unit_scale_frequency_indicator_evidence_found"
        and unit_status["unit_interpretation"] == "million UAH"
    )

    checks.append(
        ValidationCheck(
            "OBV-006",
            "Unit validation",
            "Unit, scaling, frequency, and indicator evidence found in Dataset Explorer export",
            _status_from_bool(unit_evidence_ok),
            _severity_from_bool(unit_evidence_ok, "high"),
            unit_status["evidence"],
            (
                f"{unit_status.get('indicator_name', '')}; "
                f"{unit_status.get('freq_name', '')}; "
                f"{unit_status.get('unit_interpretation', '')}; "
                f"periods {unit_status.get('period_min', '')}-{unit_status.get('period_max', '')}"
            ),
            "Gross regional product; Annual; million UAH",
            "not_yet_used",
            (
                "Use official GRP values for controlled benchmarking only until "
                "transformation logic and SME review approve scoring integration."
            ),
            unit_status["notes"],
        )
    )

    indicator_values = []
    if not candidates.empty and "indicator_code" in candidates.columns:
        indicator_values = (
            candidates["indicator_code"].fillna("").astype(str).drop_duplicates().tolist()
        )
    indicator_ok = set(indicator_values) == {"GRP"}
    checks.append(
        ValidationCheck(
            "OBV-007",
            "Indicator validation",
            "Indicator code is GRP",
            _status_from_bool(indicator_ok),
            _severity_from_bool(indicator_ok),
            str(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE),
            str(indicator_values),
            "['GRP']",
            "not_yet_used",
            "Confirm GRP measure definition and suitability as a regional baseline.",
            "GRP appears consistent and Dataset Explorer evidence supports gross regional product.",
        )
    )

    nace_values = []
    if not candidates.empty and "nace_code" in candidates.columns:
        nace_values = candidates["nace_code"].fillna("").astype(str).drop_duplicates().tolist()
    nace_ok = set(nace_values) == {"_Z"}
    checks.append(
        ValidationCheck(
            "OBV-008",
            "NACE validation",
            "NACE code is _Z",
            _status_from_bool(nace_ok),
            _severity_from_bool(nace_ok),
            str(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE),
            str(nace_values),
            "['_Z']",
            "not_yet_used",
            "Confirm whether _Z is the correct total/regional-account category.",
            (
                "The code is consistent. Dataset Explorer evidence describes _Z as "
                "Not applicable for this GRP regional-account series."
            ),
        )
    )

    freq_values = []
    if not candidates.empty and "freq_code" in candidates.columns:
        freq_values = candidates["freq_code"].fillna("").astype(str).drop_duplicates().tolist()
    freq_ok = set(freq_values) == {"A"}
    checks.append(
        ValidationCheck(
            "OBV-009",
            "Frequency validation",
            "Frequency code is annual",
            _status_from_bool(freq_ok),
            _severity_from_bool(freq_ok, "medium"),
            str(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE),
            str(freq_values),
            "['A']",
            "not_yet_used",
            "Confirm annual frequency is appropriate for baseline use.",
            "Annual frequency is expected for GRP and confirmed in Dataset Explorer evidence.",
        )
    )

    period_values = []
    if not candidates.empty and "latest_period" in candidates.columns:
        period_values = candidates["latest_period"].fillna("").astype(str).drop_duplicates().tolist()
    period_consistent = len(period_values) == 1 and period_values[0] != ""
    checks.append(
        ValidationCheck(
            "OBV-010",
            "Period coverage",
            "Latest period is consistent across candidates",
            _status_from_bool(period_consistent),
            _severity_from_bool(period_consistent, "medium"),
            str(OFFICIAL_BASELINE_PERIOD_COVERAGE_TABLE),
            str(period_values),
            "One consistent latest_period across expected coverage",
            "not_yet_used",
            "Confirm whether the latest available year is appropriate as baseline year.",
            "A consistent period is necessary but not sufficient for scoring integration.",
        )
    )

    positive_values = False
    if not candidates.empty and "official_regional_baseline_proxy_numeric" in candidates.columns:
        positive_values = bool(
            candidates["official_regional_baseline_proxy_numeric"]
            .dropna()
            .gt(0)
            .all()
        )
    checks.append(
        ValidationCheck(
            "OBV-011",
            "Value sanity",
            "Official baseline proxy values are numeric and positive",
            _status_from_bool(positive_values),
            _severity_from_bool(positive_values, "medium"),
            str(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE),
            "all_positive" if positive_values else "missing_or_non_positive_values_detected",
            "All values numeric and > 0",
            "not_yet_used",
            "Review outliers before scaling or replacing synthetic fields.",
            "Positive numeric values support candidate readiness but not scoring readiness.",
        )
    )

    probe_success_count = 0
    probe_observation_count = 0
    if not probes.empty:
        if "success_status" in probes.columns:
            probe_success_count = int(probes["success_status"].apply(_normalize_bool).sum())
        if "has_observations" in probes.columns:
            probe_observation_count = int(probes["has_observations"].apply(_normalize_bool).sum())
    probe_ok = probe_success_count == expected_count and probe_observation_count == expected_count
    checks.append(
        ValidationCheck(
            "OBV-012",
            "Endpoint evidence",
            "All oblast probes returned successful observation responses",
            _status_from_bool(probe_ok),
            _severity_from_bool(probe_ok, "medium"),
            str(UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE),
            f"{probe_success_count} successful probes; {probe_observation_count} probes with observations",
            f"{expected_count} successful probes and observations",
            "not_yet_used",
            "Retain raw response evidence and monitor endpoint changes before each refresh.",
            "Endpoint evidence supports source availability, not final analytical validity.",
        )
    )

    confirmed_count = len(confirmed_series)
    checks.append(
        ValidationCheck(
            "OBV-013",
            "Parser evidence",
            "Confirmed single-series parsed observation evidence exists",
            _status_from_bool(confirmed_count > 0),
            _severity_from_bool(confirmed_count > 0, "medium"),
            str(UKRSTAT_CONFIRMED_SERIES_PARSED_TABLE),
            str(confirmed_count),
            "> 0 parsed observations",
            "not_yet_used",
            "Use parsed series evidence to validate period-label mapping and raw response parsing.",
            "This confirms parser behavior for the known test series.",
        )
    )

    # This check intentionally blocks full scoring integration while still allowing
    # controlled benchmarking. It should move to pass only after the benchmark
    # merge plan and SME review are documented.
    checks.append(
        ValidationCheck(
            "OBV-014",
            "Scoring integration change control",
            "Transformation logic and SME review documented before scoring integration",
            "review_required",
            "high",
            str(OFFICIAL_BASELINE_READINESS_DECISION_TABLE),
            "benchmarking_ready_but_scoring_integration_not_approved",
            "documented transformation logic and SME review",
            "not_yet_used",
            (
                "Review official_baseline_gap_review.csv, "
                "official_baseline_scenario_recommendations.csv, and "
                "official_baseline_merge_review_summary.csv before any future "
                "scoring-integration discussion."
            ),
            (
                "This control allows benchmark integration and merge review while "
                "preserving the block on scoring integration."
            ),
        )
    )

    context_bridge_rows = _artifact_row_count(OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE)
    context_review_rows = _artifact_row_count(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE)
    context_artifacts_available = context_bridge_rows > 0 and context_review_rows > 0

    checks.append(
        ValidationCheck(
            "OBV-015",
            "Expanded Prozorro context bridge",
            "Official-baseline-to-Prozorro context bridge is available for review",
            _status_from_bool(context_artifacts_available),
            _severity_from_bool(context_artifacts_available, "medium"),
            (
                f"{OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE}; "
                f"{OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE}"
            ),
            (
                f"bridge_rows={context_bridge_rows}; "
                f"context_review_rows={context_review_rows}"
            ),
            "> 0 bridge rows and > 0 context-review rows",
            "not_a_scoring_field",
            (
                "Run official_baseline_merge_plan.py and "
                "official_baseline_merge_review.py after generating expanded "
                "Prozorro procurement feature artifacts."
            ),
            (
                "This check validates review-context availability only. Expanded "
                "Prozorro features remain outside official baseline scoring."
            ),
        )
    )

    context_review = _safe_read_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE)

    prozorro_current_use_values: list[str] = []
    prozorro_prohibited_use_values: list[str] = []
    prozorro_score_change_values: list[str] = []
    prozorro_scoring_use_values: list[str] = []
    prozorro_monte_carlo_use_values: list[str] = []

    if not context_review.empty:
        if "current_use" in context_review.columns:
            prozorro_current_use_values = (
                context_review["current_use"]
                .fillna("")
                .astype(str)
                .drop_duplicates()
                .tolist()
            )

        if "prohibited_use" in context_review.columns:
            prozorro_prohibited_use_values = (
                context_review["prohibited_use"]
                .fillna("")
                .astype(str)
                .drop_duplicates()
                .tolist()
            )

        if "production_score_change" in context_review.columns:
            prozorro_score_change_values = (
                context_review["production_score_change"]
                .fillna("")
                .astype(str)
                .drop_duplicates()
                .tolist()
            )

        if "used_in_scoring" in context_review.columns:
            prozorro_scoring_use_values = (
                context_review["used_in_scoring"]
                .fillna("")
                .astype(str)
                .drop_duplicates()
                .tolist()
            )

        if "used_in_monte_carlo" in context_review.columns:
            prozorro_monte_carlo_use_values = (
                context_review["used_in_monte_carlo"]
                .fillna("")
                .astype(str)
                .drop_duplicates()
                .tolist()
            )

    prozorro_control_ok = (
        set(prozorro_current_use_values) == {PROZORRO_PROCUREMENT_CURRENT_USE}
        and set(prozorro_prohibited_use_values)
        == {PROZORRO_PROCUREMENT_PROHIBITED_USE}
        and set(prozorro_score_change_values)
        == {PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE}
        and set(value.lower() for value in prozorro_scoring_use_values) == {"false"}
        and set(value.lower() for value in prozorro_monte_carlo_use_values) == {"false"}
    )

    checks.append(
        ValidationCheck(
            "OBV-016",
            "Expanded Prozorro scoring gate",
            "Expanded Prozorro context-review artifacts remain review-only and out of scoring",
            _status_from_bool(prozorro_control_ok),
            _severity_from_bool(prozorro_control_ok, "high"),
            str(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE),
            (
                f"current_use={prozorro_current_use_values}; "
                f"prohibited_use={prozorro_prohibited_use_values}; "
                f"production_score_change={prozorro_score_change_values}; "
                f"used_in_scoring={prozorro_scoring_use_values}; "
                f"used_in_monte_carlo={prozorro_monte_carlo_use_values}"
            ),
            (
                f"current_use={PROZORRO_PROCUREMENT_CURRENT_USE}; "
                f"prohibited_use={PROZORRO_PROCUREMENT_PROHIBITED_USE}; "
                f"production_score_change={PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE}; "
                "used_in_scoring=False; used_in_monte_carlo=False"
            ),
            "not_a_scoring_field",
            (
                "Block any expanded Prozorro scoring use until procurement coverage, "
                "mapping, false-positive controls, SME review, and model change-control "
                "approval are documented."
            ),
            (
                "This control prevents a review-only procurement feature from being "
                "misread as official baseline scoring evidence."
            ),
        )
    )

    typology_bridge_rows = _artifact_row_count(
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_TABLE
    )
    typology_review_rows = _artifact_row_count(
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE
    )
    typology_artifacts_available = typology_bridge_rows > 0 and typology_review_rows > 0

    checks.append(
        ValidationCheck(
            "OBV-017",
            "Wartime AML typology context bridge",
            "Official-baseline-to-wartime-AML-typology context bridge is available for review",
            _status_from_bool(typology_artifacts_available),
            _severity_from_bool(typology_artifacts_available, "medium"),
            (
                f"{OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_TABLE}; "
                f"{OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE}"
            ),
            (
                f"bridge_rows={typology_bridge_rows}; "
                f"context_review_rows={typology_review_rows}"
            ),
            "> 0 bridge rows and > 0 context-review rows",
            "not_a_scoring_field",
            (
                "Run official_baseline_merge_plan.py and "
                "official_baseline_merge_review.py after generating wartime AML/CFT "
                "typology artifacts."
            ),
            (
                "This check validates review-context availability only. Wartime AML/CFT "
                "typology artifacts remain literature-support references outside scoring."
            ),
        )
    )

    typology_review = _safe_read_csv(
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE
    )

    typology_current_use_values = _unique_values(typology_review, "current_use")
    typology_prohibited_use_values = _unique_values(typology_review, "prohibited_use")
    typology_score_change_values = _unique_values(
        typology_review,
        "production_score_change",
    )
    typology_scoring_ok = _control_false_values_ok(typology_review, "used_in_scoring")
    typology_monte_carlo_ok = _control_false_values_ok(
        typology_review,
        "used_in_monte_carlo",
    )

    typology_control_ok = (
        set(typology_current_use_values) == {WARTIME_AML_TYPOLOGY_CURRENT_USE}
        and set(typology_prohibited_use_values)
        == {WARTIME_AML_TYPOLOGY_PROHIBITED_USE}
        and set(typology_score_change_values)
        == {WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE}
        and typology_scoring_ok
        and typology_monte_carlo_ok
    )

    checks.append(
        ValidationCheck(
            "OBV-018",
            "Wartime AML typology scoring gate",
            "Wartime AML typology context-review artifacts remain reference-only and out of scoring",
            _status_from_bool(typology_control_ok),
            _severity_from_bool(typology_control_ok, "high"),
            str(OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE),
            (
                f"current_use={typology_current_use_values}; "
                f"prohibited_use={typology_prohibited_use_values}; "
                f"production_score_change={typology_score_change_values}; "
                f"used_in_scoring_ok={typology_scoring_ok}; "
                f"used_in_monte_carlo_ok={typology_monte_carlo_ok}"
            ),
            (
                f"current_use={WARTIME_AML_TYPOLOGY_CURRENT_USE}; "
                f"prohibited_use={WARTIME_AML_TYPOLOGY_PROHIBITED_USE}; "
                f"production_score_change={WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE}; "
                "used_in_scoring=False; used_in_monte_carlo=False"
            ),
            "not_a_scoring_field",
            (
                "Block any wartime typology scoring use until measurable indicators, "
                "SME review, false-positive controls, and model change-control "
                "approval are documented."
            ),
            (
                "This control prevents a literature-support typology layer from being "
                "misread as official baseline scoring evidence."
            ),
        )
    )

    fiu_bridge_rows = _artifact_row_count(OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_TABLE)
    fiu_review_rows = _artifact_row_count(OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE)
    fiu_artifacts_available = fiu_bridge_rows > 0 and fiu_review_rows > 0

    checks.append(
        ValidationCheck(
            "OBV-019",
            "Official FIU/SFMS context bridge",
            "Official-baseline-to-FIU/SFMS context bridge is available for review",
            _status_from_bool(fiu_artifacts_available),
            _severity_from_bool(fiu_artifacts_available, "medium"),
            (
                f"{OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_TABLE}; "
                f"{OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE}"
            ),
            f"bridge_rows={fiu_bridge_rows}; context_review_rows={fiu_review_rows}",
            "> 0 bridge rows and > 0 context-review rows",
            "not_a_scoring_field",
            (
                "Run official_baseline_merge_plan.py and "
                "official_baseline_merge_review.py after generating official FIU/SFMS "
                "context artifacts."
            ),
            (
                "This check validates review-context availability only. Official FIU/SFMS "
                "context remains national source support outside scoring."
            ),
        )
    )

    fiu_review = _safe_read_csv(OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE)

    fiu_current_use_values = _unique_values(fiu_review, "current_use")
    fiu_prohibited_use_values = _unique_values(fiu_review, "prohibited_use")
    fiu_score_change_values = _unique_values(fiu_review, "production_score_change")
    fiu_scoring_ok = _control_false_values_ok(fiu_review, "used_in_scoring")
    fiu_monte_carlo_ok = _control_false_values_ok(fiu_review, "used_in_monte_carlo")

    fiu_control_ok = (
        set(fiu_current_use_values) == {FIU_CONTEXT_CURRENT_USE}
        and set(fiu_prohibited_use_values) == {FIU_CONTEXT_PROHIBITED_USE}
        and set(fiu_score_change_values) == {FIU_CONTEXT_PRODUCTION_SCORE_CHANGE}
        and fiu_scoring_ok
        and fiu_monte_carlo_ok
    )

    checks.append(
        ValidationCheck(
            "OBV-020",
            "Official FIU/SFMS scoring gate",
            "Official FIU/SFMS context-review artifacts remain source-support only and out of scoring",
            _status_from_bool(fiu_control_ok),
            _severity_from_bool(fiu_control_ok, "high"),
            str(OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE),
            (
                f"current_use={fiu_current_use_values}; "
                f"prohibited_use={fiu_prohibited_use_values}; "
                f"production_score_change={fiu_score_change_values}; "
                f"used_in_scoring_ok={fiu_scoring_ok}; "
                f"used_in_monte_carlo_ok={fiu_monte_carlo_ok}"
            ),
            (
                f"current_use={FIU_CONTEXT_CURRENT_USE}; "
                f"prohibited_use={FIU_CONTEXT_PROHIBITED_USE}; "
                f"production_score_change={FIU_CONTEXT_PRODUCTION_SCORE_CHANGE}; "
                "used_in_scoring=False; used_in_monte_carlo=False"
            ),
            "not_a_scoring_field",
            (
                "Block any FIU/SFMS-context scoring use until measurable oblast/sector "
                "indicators, SME review, false-positive controls, and model "
                "change-control approval are documented."
            ),
            (
                "This control prevents national FIU/SFMS context from being misread "
                "as official baseline scoring evidence."
            ),
        )
    )

    operational_bridge_rows = _artifact_row_count(
        OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_TABLE
    )
    operational_review_rows = _artifact_row_count(
        OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE
    )
    operational_artifacts_available = (
        operational_bridge_rows > 0 and operational_review_rows > 0
    )

    checks.append(
        ValidationCheck(
            "OBV-021",
            "Operational controls context bridge",
            "Official-baseline-to-operational-controls context bridge is available for review",
            _status_from_bool(operational_artifacts_available),
            _severity_from_bool(operational_artifacts_available, "medium"),
            (
                f"{OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_TABLE}; "
                f"{OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE}"
            ),
            (
                f"bridge_rows={operational_bridge_rows}; "
                f"context_review_rows={operational_review_rows}"
            ),
            "> 0 bridge rows and > 0 context-review rows",
            "not_a_scoring_field",
            (
                "Run official_baseline_merge_plan.py and "
                "official_baseline_merge_review.py after generating analyst-review, "
                "false-positive, source-freshness, and run-manifest artifacts."
            ),
            (
                "This check validates operational-control review-context availability "
                "only. Operational controls remain documentation and human-review "
                "support outside official baseline scoring."
            ),
        )
    )

    operational_review = _safe_read_csv(
        OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE
    )

    operational_current_use_values = _unique_values(operational_review, "current_use")
    operational_score_change_values = _unique_values(
        operational_review,
        "production_score_change",
    )
    operational_scoring_ok = _control_false_values_ok(
        operational_review,
        "used_in_scoring",
    )
    operational_monte_carlo_ok = _control_false_values_ok(
        operational_review,
        "used_in_monte_carlo",
    )

    operational_control_ok = (
        operational_review_rows > 0
        and set(operational_score_change_values) == {"none"}
        and operational_scoring_ok
        and operational_monte_carlo_ok
    )

    checks.append(
        ValidationCheck(
            "OBV-022",
            "Operational controls scoring gate",
            "Operational-control context-review artifacts remain documentation-only and out of scoring",
            _status_from_bool(operational_control_ok),
            _severity_from_bool(operational_control_ok, "high"),
            str(OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE),
            (
                f"current_use={operational_current_use_values}; "
                f"production_score_change={operational_score_change_values}; "
                f"used_in_scoring_ok={operational_scoring_ok}; "
                f"used_in_monte_carlo_ok={operational_monte_carlo_ok}"
            ),
            (
                "production_score_change=none; used_in_scoring=False; "
                "used_in_monte_carlo=False"
            ),
            "not_a_scoring_field",
            (
                "Block any interpretation that analyst-review, false-positive, "
                "source-freshness, or run-manifest artifacts authorize official "
                "baseline scoring use."
            ),
            (
                "This control prevents operational documentation artifacts from being "
                "misread as official baseline scoring evidence."
            ),
        )
    )

    register = pd.DataFrame([check.__dict__ for check in checks])
    register.to_csv(OFFICIAL_BASELINE_VALIDATION_REGISTER_TABLE, index=False)
    return register


def _artifact_row_count(path: Path) -> int:
    """Return row count for an optional generated artifact."""
    df = _safe_read_csv(path)
    return 0 if df.empty else len(df)


def _merge_planning_artifacts_available() -> bool:
    """Check whether controlled merge-planning artifacts exist."""
    required_paths = [
        OFFICIAL_BASELINE_MERGE_PLAN_TABLE,
        OFFICIAL_BASELINE_BENCHMARK_COMPARISON_TABLE,
        OFFICIAL_BASELINE_RESCALE_SCENARIO_TABLE,
        OFFICIAL_BASELINE_REPLACE_OBLAST_BASELINE_SCENARIO_TABLE,
        OFFICIAL_BASELINE_MERGE_READINESS_SUMMARY_TABLE,
        OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE,
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_TABLE,
        OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_TABLE,
        OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_TABLE,
    ]

    return all(_artifact_row_count(path) > 0 for path in required_paths)


def _merge_review_artifacts_available() -> bool:
    """Check whether controlled merge-review artifacts exist."""
    required_paths = [
        OFFICIAL_BASELINE_GAP_REVIEW_TABLE,
        OFFICIAL_BASELINE_SCENARIO_RECOMMENDATIONS_TABLE,
        OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_TABLE,
        OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE,
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE,
        OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE,
        OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE,
    ]

    return all(_artifact_row_count(path) > 0 for path in required_paths)


def _merge_review_recommended_posture() -> str:
    """Return current recommended posture from scenario recommendations."""
    recommendations = _safe_read_csv(OFFICIAL_BASELINE_SCENARIO_RECOMMENDATIONS_TABLE)

    if recommendations.empty:
        return "not_available"

    if {"scenario_name", "current_recommendation"}.issubset(recommendations.columns):
        current = recommendations[
            recommendations["current_recommendation"]
            .fillna("")
            .astype(str)
            .eq("recommended_current_posture")
        ]

        if not current.empty:
            return str(current.iloc[0].get("scenario_name", "not_available"))

    return "not_available"


def _merge_review_gap_note() -> str:
    """Return compact note from merge-review summary/gap review."""
    summary = _safe_read_csv(OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_TABLE)
    gap_review = _safe_read_csv(OFFICIAL_BASELINE_GAP_REVIEW_TABLE)

    if summary.empty and gap_review.empty:
        return "Merge-review artifacts not found."

    recommended_posture = _merge_review_recommended_posture()

    largest_gap = "not_available"
    average_abs_gap = "not_available"
    gap_distribution = "not_available"

    if not gap_review.empty:
        working = gap_review.copy()

        if "absolute_index_gap" in working.columns:
            working["absolute_index_gap"] = pd.to_numeric(
                working["absolute_index_gap"],
                errors="coerce",
            )
            average = working["absolute_index_gap"].mean()

            if pd.notna(average):
                average_abs_gap = f"{average:.2f}"

            working = working.sort_values("absolute_index_gap", ascending=False)

        if not working.empty:
            largest_gap = (
                f"{working.iloc[0].get('waris_oblast', 'not_available')} "
                f"({working.iloc[0].get('official_vs_synthetic_index_gap', 'not_available')})"
            )

        if "gap_band" in working.columns:
            gap_distribution = str(
                working["gap_band"]
                .fillna("missing_gap")
                .astype(str)
                .value_counts()
                .to_dict()
            )

    return (
        f"Recommended current posture: {recommended_posture}. "
        f"Largest official-vs-synthetic gap: {largest_gap}. "
        f"Average absolute index gap: {average_abs_gap}. "
        f"Gap distribution: {gap_distribution}."
    )


def _prozorro_context_review_note() -> str:
    """Return compact note from official-baseline-to-Prozorro context review."""
    context_review = _safe_read_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE)

    if context_review.empty:
        return "Official-baseline-to-Prozorro context-review artifact not found."

    top_oblast = "not_available"
    top_score = "not_available"
    band_distribution = "not_available"

    working = context_review.copy()

    if "procurement_review_priority_candidate" in working.columns:
        working["procurement_review_priority_candidate"] = pd.to_numeric(
            working["procurement_review_priority_candidate"],
            errors="coerce",
        )
        working = working.sort_values(
            "procurement_review_priority_candidate",
            ascending=False,
        )

        if not working.empty:
            top_oblast = str(working.iloc[0].get("waris_oblast", "not_available"))
            top_score = str(
                working.iloc[0].get(
                    "procurement_review_priority_candidate",
                    "not_available",
                )
            )

    if "procurement_candidate_band" in working.columns:
        band_distribution = str(
            working["procurement_candidate_band"]
            .fillna("missing_band")
            .astype(str)
            .value_counts()
            .to_dict()
        )

    return (
        f"Official-baseline-to-Prozorro context-review rows: {len(context_review)}. "
        f"Top procurement context candidate: {top_oblast} ({top_score}). "
        f"Procurement context band distribution: {band_distribution}. "
        "Expanded Prozorro features remain review-only and production_score_change=none."
    )


def _source_context_review_note(
    path: Path,
    label: str,
    expected_current_use: str,
) -> str:
    """Return compact note from a source-support context review table."""
    review = _safe_read_csv(path)

    if review.empty:
        return f"{label} context-review artifact not found."

    family_distribution = "not_available"
    if "typology_family" in review.columns:
        family_distribution = str(
            review["typology_family"]
            .fillna("missing_family")
            .astype(str)
            .value_counts()
            .to_dict()
        )

    current_use_values = _unique_values(review, "current_use")

    return (
        f"{label} context-review rows: {len(review)}. "
        f"Typology family distribution: {family_distribution}. "
        f"Current use values: {current_use_values}; expected {expected_current_use}. "
        "Context remains source support only and production_score_change=none."
    )


def _wartime_typology_context_review_note() -> str:
    """Return compact note from official-baseline-to-wartime-typology context review."""
    return _source_context_review_note(
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE,
        "Official-baseline-to-wartime-AML-typology",
        WARTIME_AML_TYPOLOGY_CURRENT_USE,
    )


def _fiu_context_review_note() -> str:
    """Return compact note from official-baseline-to-FIU/SFMS context review."""
    return _source_context_review_note(
        OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE,
        "Official-baseline-to-FIU/SFMS",
        FIU_CONTEXT_CURRENT_USE,
    )


def _operational_controls_context_review_note() -> str:
    """Return compact note from operational-controls context review."""
    review = _safe_read_csv(OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE)

    if review.empty:
        return "Official-baseline-to-operational-controls context-review artifact not found."

    status_distribution = "not_available"
    if "artifact_status" in review.columns:
        status_distribution = str(
            review["artifact_status"]
            .fillna("missing_status")
            .astype(str)
            .value_counts()
            .to_dict()
        )

    family_distribution = "not_available"
    if "operational_artifact_family" in review.columns:
        family_distribution = str(
            review["operational_artifact_family"]
            .fillna("missing_family")
            .astype(str)
            .value_counts()
            .to_dict()
        )

    score_change_values = _unique_values(review, "production_score_change")

    return (
        f"Official-baseline-to-operational-controls context-review rows: {len(review)}. "
        f"Artifact status distribution: {status_distribution}. "
        f"Operational family distribution: {family_distribution}. "
        f"Production score change values: {score_change_values}. "
        "Operational controls remain documentation and human-review support only."
    )


def _next_decision_point_for_benchmark_integration() -> str:
    """Build next-decision guidance based on downstream artifacts."""
    merge_plan_ready = _merge_planning_artifacts_available()
    merge_review_ready = _merge_review_artifacts_available()
    recommended_posture = _merge_review_recommended_posture()

    if merge_review_ready:
        return (
            "Review official_baseline_gap_review.csv, "
            "official_baseline_scenario_recommendations.csv, "
            "official_baseline_prozorro_context_review.csv, "
            "official_baseline_wartime_typology_context_review.csv, "
            "official_baseline_fiu_context_review.csv, "
            "official_baseline_operational_controls_context_review.csv, and "
            "official_baseline_merge_review_summary.csv. Maintain "
            f"{recommended_posture} posture until transformation logic, source "
            "coverage validation, SME review, and scoring change-control approval "
            "are documented."
        )

    if merge_plan_ready:
        return (
            "Build or rerun official_baseline_merge_review.py to summarize "
            "official-vs-synthetic gaps, scenario recommendations, the "
            "official-baseline-to-Prozorro context review, the "
            "official-baseline-to-wartime-typology context review, the "
            "official-baseline-to-FIU/SFMS context review, the "
            "official-baseline-to-operational-controls context review, and the current "
            "benchmark_only posture before any scoring-integration discussion."
        )

    return (
        "Build official_baseline_merge_plan.py to compare benchmark_only, "
        "rescale_revenue_baseline, replace_oblast_baseline, the "
        "official-baseline-to-Prozorro context bridge, the "
        "official-baseline-to-wartime-typology context bridge, and the "
        "official-baseline-to-FIU/SFMS context bridge, and the "
        "official-baseline-to-operational-controls context bridge without changing "
        "production WARIS scores."
    )


def _derive_readiness_decision(register: pd.DataFrame) -> dict[str, object]:
    """Derive staged readiness decision from validation-register controls."""
    if register is None or register.empty:
        return {
            "decision": DECISION_NO_GO,
            "approved_current_use": APPROVED_USE_NONE,
            "prohibited_current_use": PROHIBITED_USE_SCORING,
            "rationale": (
                "Validation register is missing or empty. Official baseline values "
                "cannot be used until artifacts are regenerated."
            ),
            "blocking_item_count": 0,
            "high_or_critical_blocking_item_count": 0,
            "next_decision_point": (
                "Regenerate official baseline candidates and validation artifacts."
            ),
        }

    expected_ids = {f"OBV-{i:03d}" for i in range(1, 23)}
    required_columns = {"check_id", "status", "severity"}
    complete = required_columns.issubset(register.columns)
    if complete:
        complete = (set(register["check_id"]) == expected_ids
                    and not register["check_id"].duplicated().any())
    core_ids = {f"OBV-{i:03d}" for i in (1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13)}
    core_pass = complete and register.loc[
        register["check_id"].isin(core_ids), "status"
    ].eq("pass").all()
    if not core_pass:
        return {
            "decision": DECISION_NO_GO,
            "approved_current_use": APPROVED_USE_NONE,
            "prohibited_current_use": PROHIBITED_USE_SCORING,
            "rationale": "Official observation, coverage, parsing or unit evidence is missing or incomplete. No benchmark-readiness approval is established.",
            "blocking_item_count": int(register["status"].ne("pass").sum()) if "status" in register else len(register),
            "high_or_critical_blocking_item_count": int((register["status"].ne("pass") & register["severity"].isin(["high", "critical"])).sum()) if {"status", "severity"}.issubset(register.columns) else 0,
            "next_decision_point": "Retrieve and validate complete official evidence, then regenerate all 22 checks.",
        }

    working = register.copy()
    working["status"] = working["status"].fillna("").astype(str)
    working["severity"] = working["severity"].fillna("").astype(str)

    blocking_items = working[working["status"].ne("pass")]
    high_or_critical = blocking_items[
        blocking_items["severity"].isin(["critical", "high"])
    ]
    critical_failures = blocking_items[blocking_items["severity"].eq("critical")]

    if not critical_failures.empty:
        return {
            "decision": DECISION_NO_GO,
            "approved_current_use": APPROVED_USE_NONE,
            "prohibited_current_use": PROHIBITED_USE_SCORING,
            "rationale": (
                "One or more critical official-baseline controls failed. Official "
                "baseline values are not approved even for benchmarking until the "
                "critical control is resolved."
            ),
            "blocking_item_count": len(blocking_items),
            "high_or_critical_blocking_item_count": len(high_or_critical),
            "next_decision_point": (
                "Resolve critical validation controls and rerun "
                "python -m src.official_baseline_validation."
            ),
        }

    # Passing a register never authorizes a scoring change in this release.
    if blocking_items.empty:
        return {
            "decision": DECISION_GO_FOR_BENCHMARK_INTEGRATION,
            "approved_current_use": APPROVED_USE_BENCHMARK_INTEGRATION,
            "prohibited_current_use": PROHIBITED_USE_SCORING,
            "rationale": (
                "All checks passed, but this release remains benchmark-only. "
                "A validation register cannot authorize scoring integration."
            ),
            "blocking_item_count": 0,
            "high_or_critical_blocking_item_count": 0,
            "next_decision_point": (
                "Retain benchmark_only. Any proposed scoring change requires a separate "
                "methodological review and explicit change-control approval."
            ),
        }

    # If the only remaining blocker is transformation/SME change control, the
    # model is ready for controlled benchmark integration but not scoring.
    blocking_ids = set(blocking_items["check_id"].astype(str).tolist())
    if blocking_ids == {"OBV-014"}:
        return {
            "decision": DECISION_GO_FOR_BENCHMARK_INTEGRATION,
            "approved_current_use": APPROVED_USE_BENCHMARK_INTEGRATION,
            "prohibited_current_use": PROHIBITED_USE_SCORING,
            "rationale": (
                "Official GRP candidates have source, unit, scaling, frequency, "
                "coverage, geography, endpoint, parser, and scoring-gate evidence "
                "sufficient for controlled benchmark integration. Merge-planning "
                "and merge-review artifacts should guide benchmark_only, rescale, "
                "or replace-baseline discussion. Official values remain prohibited "
                "from risk-layer or composite-score use until transformation logic "
                "and SME review are documented."
            ),
            "blocking_item_count": len(blocking_items),
            "high_or_critical_blocking_item_count": len(high_or_critical),
            "next_decision_point": _next_decision_point_for_benchmark_integration(),
        }

    return {
        "decision": DECISION_CONDITIONAL_GO,
        "approved_current_use": APPROVED_USE_BENCHMARKING,
        "prohibited_current_use": PROHIBITED_USE_SCORING,
        "rationale": (
            "Official baseline candidates have sufficient source, coverage, geography, "
            "endpoint, and scoring-gate evidence for validation/reporting/benchmarking "
            "context, but unresolved validation blockers prevent risk-layer or "
            "composite-score use."
        ),
        "blocking_item_count": len(blocking_items),
        "high_or_critical_blocking_item_count": len(high_or_critical),
        "next_decision_point": (
            "Resolve remaining validation blockers, then reassess whether controlled "
            "benchmark integration or controlled scoring integration is appropriate."
        ),
    }


def build_validation_summary(register: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    """Build high-level validation summary."""
    if register.empty:
        out = pd.DataFrame(
            [
                {
                    "summary_area": "Overall readiness",
                    "status": "not_ready_for_any_use",
                    "value": "No validation checks were available.",
                    "recommended_next_action": (
                        "Regenerate official baseline artifacts and rerun validation."
                    ),
                }
            ]
        )
        out.to_csv(OFFICIAL_BASELINE_VALIDATION_SUMMARY_TABLE, index=False)
        return out

    status_counts = register["status"].value_counts().to_dict()
    pass_count = int((register["status"] == "pass").sum())
    review_count = int(register["status"].isin(["review_required", "partial"]).sum())
    decision_context = _derive_readiness_decision(register)

    high_review_items = int(
        (
            register["severity"].astype(str).eq("high")
            & register["status"].astype(str).isin(["review_required", "partial"])
        ).sum()
    )
    critical_failures = int(
        (
            register["severity"].astype(str).eq("critical")
            & register["status"].astype(str).ne("pass")
        ).sum()
    )

    latest_period = (
        _unique_join(candidates["latest_period"], max_items=4)
        if not candidates.empty and "latest_period" in candidates.columns
        else ""
    )
    scoring_use = (
        _unique_join(candidates["current_use_in_scoring"], max_items=4)
        if not candidates.empty and "current_use_in_scoring" in candidates.columns
        else ""
    )
    validation_status = (
        _unique_join(candidates["validation_status"], max_items=4)
        if not candidates.empty and "validation_status" in candidates.columns
        else ""
    )

    if critical_failures > 0:
        overall_status = "blocked_critical_control_failure"
    elif decision_context["decision"] == DECISION_GO_FOR_SCORING:
        overall_status = "ready_for_scoring_after_validation"
    elif decision_context["decision"] == DECISION_GO_FOR_BENCHMARK_INTEGRATION:
        overall_status = "ready_for_controlled_benchmark_integration"
    elif decision_context["decision"] == DECISION_CONDITIONAL_GO:
        overall_status = "conditional_go_for_validation_and_benchmarking_only"
    else:
        overall_status = "not_ready_for_any_use"

    rows = [
        {
            "summary_area": "Overall readiness",
            "status": overall_status,
            "value": (
                f"{pass_count} checks passed; {review_count} checks require review. "
                f"Status mix: {status_counts}."
            ),
            "recommended_next_action": (
                "Proceed to controlled merge-review analysis and maintain benchmark_only "
                "unless transformation logic, SME review, and scoring change control are documented."
                if decision_context["decision"] == DECISION_GO_FOR_BENCHMARK_INTEGRATION
                else "Use official GRP candidates for validation/reporting/benchmarking only "
                "until remaining validation blockers are resolved."
                if decision_context["decision"] == DECISION_CONDITIONAL_GO
                else "Do not use official baseline values until critical controls are resolved."
                if decision_context["decision"] == DECISION_NO_GO
                else "Proceed only through controlled scoring-integration change management."
            ),
        },
        {
            "summary_area": "Candidate coverage",
            "status": "validation_only",
            "value": f"{len(candidates)} official baseline candidates loaded.",
            "recommended_next_action": "Confirm all 25 mapped geographies are expected and unique.",
        },
        {
            "summary_area": "Latest period",
            "status": "validated_for_benchmarking_pending_scoring_review",
            "value": latest_period,
            "recommended_next_action": (
                "Use 2021 as a prewar benchmark period unless SME review identifies "
                "a better baseline period."
            ),
        },
        {
            "summary_area": "Scoring use",
            "status": "control_active",
            "value": scoring_use,
            "recommended_next_action": (
                "Keep current_use_in_scoring as not_yet_used until scoring integration is approved."
            ),
        },
        {
            "summary_area": "Validation status",
            "status": "benchmark_ready_scoring_pending",
            "value": validation_status,
            "recommended_next_action": (
                "Update candidate validation status only after benchmark plan and SME review."
            ),
        },
        {
            "summary_area": "High-severity review items",
            "status": "review_required" if high_review_items > 0 else "none_detected",
            "value": str(high_review_items),
            "recommended_next_action": (
                "Resolve all high-severity validation items before controlled scoring integration."
            ),
        },
        {
            "summary_area": "Recommended integration decision",
            "status": decision_context["decision"],
            "value": decision_context["rationale"],
            "recommended_next_action": decision_context["next_decision_point"],
        },
        {
            "summary_area": "Merge-review status",
            "status": _merge_review_recommended_posture(),
            "value": _merge_review_gap_note(),
            "recommended_next_action": (
                "Document a benchmark review memo and keep official GRP excluded "
                "from scoring until change control is approved."
            ),
        },
        {
            "summary_area": "Official baseline to Prozorro context review",
            "status": (
                "available"
                if _artifact_row_count(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE) > 0
                else "missing"
            ),
            "value": _prozorro_context_review_note(),
            "recommended_next_action": (
                "Keep expanded Prozorro procurement features as review-only "
                "candidate artifacts until coverage, mapping, false-positive controls, "
                "SME review, and change-control approval are documented."
            ),
        },
        {
            "summary_area": "Official baseline to wartime AML typology context review",
            "status": (
                "available"
                if _artifact_row_count(
                    OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE
                )
                > 0
                else "missing"
            ),
            "value": _wartime_typology_context_review_note(),
            "recommended_next_action": (
                "Keep wartime AML/CFT typology artifacts as literature-support "
                "references until measurable indicators, SME review, false-positive "
                "controls, and change-control approval are documented."
            ),
        },
        {
            "summary_area": "Official baseline to FIU/SFMS context review",
            "status": (
                "available"
                if _artifact_row_count(OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE) > 0
                else "missing"
            ),
            "value": _fiu_context_review_note(),
            "recommended_next_action": (
                "Keep official FIU/SFMS context artifacts as source-support context "
                "until measurable oblast/sector indicators, SME review, false-positive "
                "controls, and change-control approval are documented."
            ),
        },
    ]

    out = pd.DataFrame(rows)
    out.to_csv(OFFICIAL_BASELINE_VALIDATION_SUMMARY_TABLE, index=False)
    return out


def build_readiness_decision(register: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    """Create a compact staged readiness decision table."""
    decision_context = _derive_readiness_decision(register)

    out = pd.DataFrame(
        [
            {
                "decision_area": "Official baseline scoring integration",
                "decision": decision_context["decision"],
                "blocking_item_count": decision_context["blocking_item_count"],
                "high_or_critical_blocking_item_count": decision_context[
                    "high_or_critical_blocking_item_count"
                ],
                "rationale": decision_context["rationale"],
                "approved_current_use": decision_context["approved_current_use"],
                "prohibited_current_use": decision_context["prohibited_current_use"],
                "next_decision_point": decision_context["next_decision_point"],
            }
        ]
    )
    out.to_csv(OFFICIAL_BASELINE_READINESS_DECISION_TABLE, index=False)
    return out


def build_official_baseline_validation_artifacts() -> dict[str, pd.DataFrame]:
    """Build all official baseline validation artifacts."""
    ensure_dirs([RAW_DIR, TABLE_DIR])

    candidates = load_and_normalize_candidates()
    probes = _safe_read_csv(UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE)
    confirmed_series = _safe_read_csv(UKRSTAT_CONFIRMED_SERIES_PARSED_TABLE)
    unit_evidence, unit_evidence_summary = build_official_baseline_unit_evidence()

    if not candidates.empty:
        candidates.to_csv(OFFICIAL_BASELINE_VALIDATION_AUDIT_RAW, index=False)

    geography_check = build_geography_crosswalk_check(candidates)
    period_coverage = build_period_coverage(candidates)

    register = build_validation_register(
        candidates=candidates,
        probes=probes,
        confirmed_series=confirmed_series,
        geography_check=geography_check,
        period_coverage=period_coverage,
        unit_evidence_summary=unit_evidence_summary,
    )
    summary = build_validation_summary(register, candidates)
    readiness = build_readiness_decision(register, summary)

    return {
        "candidates_normalized": candidates,
        "geography_crosswalk_check": geography_check,
        "period_coverage": period_coverage,
        "unit_evidence": unit_evidence,
        "unit_evidence_summary": unit_evidence_summary,
        "validation_register": register,
        "validation_summary": summary,
        "readiness_decision": readiness,
    }


def main() -> None:
    artifacts = build_official_baseline_validation_artifacts()

    print("\\nOfficial baseline validation artifacts created.")
    print(f"- Normalized candidate rows: {len(artifacts['candidates_normalized'])}")
    print(f"- Geography check rows: {len(artifacts['geography_crosswalk_check'])}")
    print(f"- Period coverage rows: {len(artifacts['period_coverage'])}")
    print(f"- Unit evidence rows: {len(artifacts['unit_evidence'])}")
    print(f"- Unit evidence summary rows: {len(artifacts['unit_evidence_summary'])}")
    print(f"- Validation checks: {len(artifacts['validation_register'])}")
    print(f"- Validation summary rows: {len(artifacts['validation_summary'])}")
    print(f"- Readiness decision rows: {len(artifacts['readiness_decision'])}")

    if not artifacts["readiness_decision"].empty:
        decision_row = artifacts["readiness_decision"].iloc[0]
        print(f"- Decision: {decision_row.get('decision', 'UNKNOWN')}")
        print(
            f"- Approved current use: "
            f"{decision_row.get('approved_current_use', 'UNKNOWN')}"
        )
        print(
            f"- Prohibited current use: "
            f"{decision_row.get('prohibited_current_use', 'UNKNOWN')}"
        )
        print(f"- Rationale: {decision_row.get('rationale', '')}")
        print(
            f"- Next decision point: "
            f"{decision_row.get('next_decision_point', '')}"
        )

    print(f"- Unit evidence table: {OFFICIAL_BASELINE_UNIT_EVIDENCE_TABLE}")
    print(f"- Unit evidence summary: {OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE}")
    print(f"- Validation register: {OFFICIAL_BASELINE_VALIDATION_REGISTER_TABLE}")
    print(f"- Validation summary: {OFFICIAL_BASELINE_VALIDATION_SUMMARY_TABLE}")
    print(f"- Geography crosswalk check: {OFFICIAL_BASELINE_GEOGRAPHY_CROSSWALK_CHECK_TABLE}")
    print(f"- Period coverage: {OFFICIAL_BASELINE_PERIOD_COVERAGE_TABLE}")
    print(f"- Readiness decision: {OFFICIAL_BASELINE_READINESS_DECISION_TABLE}")
    print(f"- Raw validation audit: {OFFICIAL_BASELINE_VALIDATION_AUDIT_RAW}")

    print(
        "\\nImportant: This module validates readiness controls only. Current "
        "benchmark approval, when present, is for controlled benchmark integration "
        "and merge/context review only. It does not blend official Ukrstat GRP "
        "baseline candidates or expanded Prozorro procurement features into WARIS "
        "risk layers or composite scoring."
    )


if __name__ == "__main__":
    main()
