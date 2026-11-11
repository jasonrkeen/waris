from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="WARIS Ukraine AML Risk Model",
    layout="wide",
)

st.title("WARIS - Ukraine Wartime AML Revenue Integrity Scoring Model")
st.warning("Research prototype. The public offline demo uses synthetic assumptions, not observed misconduct or operationally validated risk.")
st.caption(
    "Public-source, sector/oblast-level AML supervisory review prioritization. "
    "Not an accusation tool."
)

st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.035);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 0.75rem;
        padding: 0.75rem 0.85rem;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.88rem;
        white-space: normal;
        line-height: 1.15rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


BASE_DIR = Path(__file__).resolve().parent
TABLE_DIR = BASE_DIR / "outputs" / "tables"
RAW_DIR = BASE_DIR / "data" / "raw"
CHART_DIR = BASE_DIR / "outputs" / "charts"
REPORT_DIR = BASE_DIR / "outputs" / "reports"

SCORED_PATH = TABLE_DIR / "waris_scored_oblast_sector.csv"
OBLAST_PATH = TABLE_DIR / "waris_oblast_summary.csv"
SECTOR_PATH = TABLE_DIR / "waris_sector_summary.csv"
MC_PATH = TABLE_DIR / "waris_monte_carlo_results.csv"
LIVE_STATUS_PATH = TABLE_DIR / "live_data_status.csv"
ACLED_CONFLICT_PATH = RAW_DIR / "acled_oblast_conflict_proxy.csv"

# Official Ukrstat baseline transition artifacts.
UKRSTAT_BASELINE_CANDIDATES_PATH = (
    TABLE_DIR / "ukrstat_oblast_baseline_candidates.csv"
)
UKRSTAT_BASELINE_PROBE_PATH = (
    TABLE_DIR / "ukrstat_oblast_baseline_probe_results.csv"
)
UKRSTAT_CONFIRMED_SERIES_PARSED_PATH = (
    TABLE_DIR / "ukrstat_confirmed_series_parsed.csv"
)
UKRSTAT_AVAILABILITY_VALUES_PATH = (
    TABLE_DIR / "ukrstat_availability_value_candidates.csv"
)
UKRSTAT_QUERY_PLAN_PATH = (
    TABLE_DIR / "ukrstat_observation_query_plan.csv"
)

# Official baseline validation gate artifacts.
OFFICIAL_BASELINE_VALIDATION_REGISTER_PATH = (
    TABLE_DIR / "official_baseline_validation_register.csv"
)
OFFICIAL_BASELINE_VALIDATION_SUMMARY_PATH = (
    TABLE_DIR / "official_baseline_validation_summary.csv"
)
OFFICIAL_BASELINE_GEOGRAPHY_CROSSWALK_CHECK_PATH = (
    TABLE_DIR / "official_baseline_geography_crosswalk_check.csv"
)
OFFICIAL_BASELINE_PERIOD_COVERAGE_PATH = (
    TABLE_DIR / "official_baseline_period_coverage.csv"
)
OFFICIAL_BASELINE_READINESS_DECISION_PATH = (
    TABLE_DIR / "official_baseline_readiness_decision.csv"
)
OFFICIAL_BASELINE_UNIT_EVIDENCE_PATH = (
    TABLE_DIR / "official_baseline_unit_evidence.csv"
)
OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_PATH = (
    TABLE_DIR / "official_baseline_unit_evidence_summary.csv"
)

# Official baseline controlled benchmark-integration artifacts.
OFFICIAL_BASELINE_MERGE_PLAN_PATH = (
    TABLE_DIR / "official_baseline_merge_plan.csv"
)
OFFICIAL_BASELINE_BENCHMARK_COMPARISON_PATH = (
    TABLE_DIR / "official_baseline_benchmark_comparison.csv"
)
OFFICIAL_BASELINE_RESCALE_SCENARIO_PATH = (
    TABLE_DIR / "official_baseline_rescale_scenario.csv"
)
OFFICIAL_BASELINE_REPLACE_OBLAST_BASELINE_SCENARIO_PATH = (
    TABLE_DIR / "official_baseline_replace_oblast_baseline_scenario.csv"
)
OFFICIAL_BASELINE_MERGE_READINESS_SUMMARY_PATH = (
    TABLE_DIR / "official_baseline_merge_readiness_summary.csv"
)

# Official baseline controlled merge-review artifacts.
OFFICIAL_BASELINE_GAP_REVIEW_PATH = (
    TABLE_DIR / "official_baseline_gap_review.csv"
)
OFFICIAL_BASELINE_SCENARIO_RECOMMENDATIONS_PATH = (
    TABLE_DIR / "official_baseline_scenario_recommendations.csv"
)
OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_PATH = (
    TABLE_DIR / "official_baseline_merge_review_summary.csv"
)

# Official baseline benchmark review memo artifact.
OFFICIAL_BASELINE_REVIEW_MEMO_PATH = (
    REPORT_DIR / "official_baseline_benchmark_review_memo.md"
)

# Expanded Prozorro procurement feature artifacts.
PROZORRO_EXPANDED_FEATURE_ROWS_PATH = (
    RAW_DIR / "prozorro_expanded_feature_rows_raw.csv"
)
PROZORRO_PROCUREMENT_FEATURES_OBLAST_PATH = (
    TABLE_DIR / "prozorro_procurement_features_oblast.csv"
)
PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_PATH = (
    TABLE_DIR / "prozorro_procurement_features_oblast_sector.csv"
)
PROZORRO_PROCUREMENT_SCORING_CANDIDATES_PATH = (
    TABLE_DIR / "prozorro_procurement_scoring_candidates.csv"
)
PROZORRO_PROCUREMENT_FEATURE_SUMMARY_PATH = (
    TABLE_DIR / "prozorro_procurement_feature_summary.csv"
)

WARTIME_AML_TYPOLOGY_REGISTER_PATH = (
    TABLE_DIR / "waris_wartime_aml_typology_register.csv"
)
WARTIME_AML_TYPOLOGY_LAYER_MAP_PATH = (
    TABLE_DIR / "waris_wartime_aml_typology_layer_map.csv"
)
WARTIME_AML_TYPOLOGY_SUMMARY_PATH = (
    TABLE_DIR / "waris_wartime_aml_typology_summary.csv"
)

FIU_OFFICIAL_SOURCE_REGISTER_PATH = (
    TABLE_DIR / "waris_fiu_official_source_register.csv"
)
FIU_REPORTING_STATISTICS_CONTEXT_PATH = (
    TABLE_DIR / "waris_fiu_reporting_statistics_context.csv"
)
FIU_CASE_REFERRAL_CONTEXT_PATH = (
    TABLE_DIR / "waris_fiu_case_referral_context.csv"
)
FIU_TYPOLOGY_SUPPORT_REGISTER_PATH = (
    TABLE_DIR / "waris_fiu_typology_support_register.csv"
)
FIU_CONTEXT_SUMMARY_PATH = TABLE_DIR / "waris_fiu_context_summary.csv"

OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_PATH = (
    TABLE_DIR / "official_baseline_prozorro_context_bridge.csv"
)
OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_PATH = (
    TABLE_DIR / "official_baseline_prozorro_context_review.csv"
)
OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_PATH = (
    TABLE_DIR / "official_baseline_wartime_typology_context_bridge.csv"
)
OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_PATH = (
    TABLE_DIR / "official_baseline_wartime_typology_context_review.csv"
)
OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_PATH = (
    TABLE_DIR / "official_baseline_fiu_context_bridge.csv"
)
OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_PATH = (
    TABLE_DIR / "official_baseline_fiu_context_review.csv"
)
OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_PATH = (
    TABLE_DIR / "official_baseline_operational_controls_context_bridge.csv"
)
OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_PATH = (
    TABLE_DIR / "official_baseline_operational_controls_context_review.csv"
)

# Operational-control / human-review support artifacts.
ANALYST_REVIEW_QUEUE_PATH = TABLE_DIR / "analyst_review_queue.csv"
ANALYST_REVIEW_QUESTIONS_PATH = TABLE_DIR / "analyst_review_questions.csv"
REVIEW_DISPOSITION_TEMPLATE_PATH = TABLE_DIR / "review_disposition_template.csv"
ANALYST_REVIEW_SUMMARY_PATH = TABLE_DIR / "analyst_review_summary.csv"

FALSE_POSITIVE_RISK_REGISTER_PATH = TABLE_DIR / "false_positive_risk_register.csv"
FALSE_POSITIVE_CONTROLS_PATH = TABLE_DIR / "false_positive_controls.csv"
FALSE_POSITIVE_REVIEW_CHECKLIST_PATH = TABLE_DIR / "false_positive_review_checklist.csv"
FALSE_POSITIVE_SUMMARY_PATH = TABLE_DIR / "false_positive_summary.csv"

SOURCE_FRESHNESS_INVENTORY_PATH = TABLE_DIR / "source_freshness_inventory.csv"
SOURCE_FRESHNESS_ASSESSMENT_PATH = TABLE_DIR / "source_freshness_assessment.csv"
SOURCE_FRESHNESS_REPLACEMENT_PRIORITIES_PATH = (
    TABLE_DIR / "source_freshness_replacement_priorities.csv"
)
SOURCE_FRESHNESS_SUMMARY_PATH = TABLE_DIR / "source_freshness_summary.csv"

RUN_MANIFEST_PATH = TABLE_DIR / "run_manifest.csv"
RUN_MANIFEST_SUMMARY_PATH = TABLE_DIR / "run_manifest_summary.csv"
RUN_MANIFEST_JSON_PATH = REPORT_DIR / "run_manifest.json"

CHART_PATHS = {
    "Top WARIS review signals": CHART_DIR / "top_waris_risks.png",
    "Risk layer profile": CHART_DIR / "top_layer_profile.png",
    "Oblast summary": CHART_DIR / "oblast_summary.png",
    "Conflict intensity": CHART_DIR / "conflict_intensity_summary.png",
    "Live source status": CHART_DIR / "live_source_status.png",
    "Ukrstat official baseline candidates": (
        CHART_DIR / "ukrstat_official_baseline_candidates.png"
    ),
    "Ukrstat official baseline validation status": (
        CHART_DIR / "ukrstat_official_baseline_validation_status.png"
    ),
    "Source-context artifact coverage": (
        CHART_DIR / "source_context_artifact_coverage.png"
    ),
    "Wartime AML typology family distribution": (
        CHART_DIR / "wartime_aml_typology_family_distribution.png"
    ),
    "FIU/SFMS context artifact coverage": (
        CHART_DIR / "fiu_context_artifact_coverage.png"
    ),
    "Official baseline context-review coverage": (
        CHART_DIR / "official_baseline_context_review_coverage.png"
    ),
    "Operational controls artifact coverage": (
        CHART_DIR / "operational_controls_artifact_coverage.png"
    ),
}


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame | None:
    from src.utils import read_optional_dashboard_csv

    return read_optional_dashboard_csv(path)


def safe_load_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return load_csv(path)


@st.cache_data
def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def safe_load_text(path: Path) -> str | None:
    if not path.exists():
        return None

    try:
        text = load_text(path)
    except Exception:
        return None

    return text if text.strip() else None


def extract_markdown_section(
    markdown_text: str | None,
    heading: str,
    fallback: str = "N/A",
) -> str:
    if markdown_text is None:
        return fallback

    lines = markdown_text.splitlines()
    in_section = False
    collected: list[str] = []

    for line in lines:
        if line.strip() == f"## {heading}":
            in_section = True
            continue

        if in_section and line.startswith("## "):
            break

        if in_section:
            collected.append(line)

    section = "\n".join(collected).strip()
    return section if section else fallback


def coerce_numeric(df: pd.DataFrame, cols: list[str], preserve_missing: bool = False) -> pd.DataFrame:
    out = df.copy()

    for col in cols:
        if col in out.columns:
            numeric = pd.to_numeric(out[col], errors="coerce")
            out[col] = numeric if preserve_missing else numeric.fillna(0)

    return out


def bool_count(df: pd.DataFrame | None, col: str) -> int:
    if df is None or df.empty or col not in df.columns:
        return 0

    return int(
        df[col]
        .fillna(False)
        .astype(str)
        .str.lower()
        .isin(["true", "1", "yes", "y", "pass", "created", "fresh", "available"])
        .sum()
    )


def unique_text(df: pd.DataFrame | None, col: str, fallback: str = "N/A") -> str:
    if df is None or df.empty or col not in df.columns:
        return fallback

    values = (
        df[col]
        .dropna()
        .astype(str)
        .map(str.strip)
        .loc[lambda s: s.ne("")]
        .drop_duplicates()
        .head(3)
        .tolist()
    )

    if not values:
        return fallback

    return "; ".join(values)


def first_value(df: pd.DataFrame | None, col: str, fallback: str = "N/A") -> str:
    if df is None or df.empty or col not in df.columns:
        return fallback

    value = df.iloc[0].get(col, fallback)

    if pd.isna(value):
        return fallback

    text = str(value).strip()

    return text if text else fallback


def count_status(df: pd.DataFrame | None, status_value: str) -> int:
    if df is None or df.empty or "status" not in df.columns:
        return 0

    return int(
        df["status"]
        .fillna("")
        .astype(str)
        .str.lower()
        .eq(status_value.lower())
        .sum()
    )


def short_label(value: object, max_chars: int = 24, fallback: str = "N/A") -> str:
    """Return a compact readable label for dashboard metrics."""
    if value is None or pd.isna(value):
        return fallback

    text = str(value).strip()
    if not text:
        return fallback

    replacements = {
        "GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION": "Controlled benchmark",
        "controlled_benchmark_integration_only": "Benchmark only",
        "risk_layer_calculation_or_composite_scoring": "Scoring blocked",
        "benchmark_only": "Benchmark only",
        "review_artifact_only": "Review only",
        "literature_support_and_typology_reference_only": "Typology reference",
        "official_fiu_context_and_typology_support_only": "FIU context only",
        "analyst_review_workflow_only": "Analyst review",
        "human_review_support_only": "Human review",
        "source_freshness_monitoring_only": "Freshness monitor",
        "run_manifest_documentation": "Run manifest",
        "current_for_documented_use": "Current",
        "control_active": "Active",
        "computed": "Computed",
    }

    if text in replacements:
        return replacements[text]

    text = text.replace("_", " ").strip()
    text = " ".join(word.capitalize() for word in text.split())

    if len(text) <= max_chars:
        return text

    return text[: max_chars - 1].rstrip() + "…"


def summary_lookup(
    df: pd.DataFrame | None,
    summary_area: str,
    column: str = "value",
    fallback: str = "N/A",
) -> str:
    """Read a compact value from a standard WARIS summary table."""
    if df is None or df.empty or "summary_area" not in df.columns:
        return fallback

    rows = df[df["summary_area"].fillna("").astype(str).eq(summary_area)]

    if rows.empty or column not in rows.columns:
        return fallback

    value = rows.iloc[0].get(column, fallback)

    if pd.isna(value):
        return fallback

    text = str(value).strip()
    return text if text else fallback


required_paths = [
    SCORED_PATH,
    OBLAST_PATH,
    SECTOR_PATH,
    MC_PATH,
]

missing = [str(path) for path in required_paths if not path.exists()]

if missing:
    st.error("Run `python main.py` first to generate output tables.")
    st.code("\n".join(missing))
    st.stop()


scored = load_csv(SCORED_PATH)
oblast = load_csv(OBLAST_PATH)
sector = load_csv(SECTOR_PATH)
mc = load_csv(MC_PATH)

live_status = safe_load_csv(LIVE_STATUS_PATH)
acled_conflict = safe_load_csv(ACLED_CONFLICT_PATH)

ukrstat_baseline_candidates = safe_load_csv(UKRSTAT_BASELINE_CANDIDATES_PATH)
ukrstat_baseline_probe = safe_load_csv(UKRSTAT_BASELINE_PROBE_PATH)
ukrstat_confirmed_series = safe_load_csv(UKRSTAT_CONFIRMED_SERIES_PARSED_PATH)
ukrstat_availability_values = safe_load_csv(UKRSTAT_AVAILABILITY_VALUES_PATH)
ukrstat_query_plan = safe_load_csv(UKRSTAT_QUERY_PLAN_PATH)

official_validation_register = safe_load_csv(OFFICIAL_BASELINE_VALIDATION_REGISTER_PATH)
official_validation_summary = safe_load_csv(OFFICIAL_BASELINE_VALIDATION_SUMMARY_PATH)
official_geography_check = safe_load_csv(OFFICIAL_BASELINE_GEOGRAPHY_CROSSWALK_CHECK_PATH)
official_period_coverage = safe_load_csv(OFFICIAL_BASELINE_PERIOD_COVERAGE_PATH)
official_readiness_decision = safe_load_csv(OFFICIAL_BASELINE_READINESS_DECISION_PATH)
official_unit_evidence = safe_load_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_PATH)
official_unit_evidence_summary = safe_load_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_PATH)

official_merge_plan = safe_load_csv(OFFICIAL_BASELINE_MERGE_PLAN_PATH)
official_benchmark_comparison = safe_load_csv(OFFICIAL_BASELINE_BENCHMARK_COMPARISON_PATH)
official_rescale_scenario = safe_load_csv(OFFICIAL_BASELINE_RESCALE_SCENARIO_PATH)
official_replace_oblast_baseline = safe_load_csv(
    OFFICIAL_BASELINE_REPLACE_OBLAST_BASELINE_SCENARIO_PATH
)
official_merge_readiness_summary = safe_load_csv(
    OFFICIAL_BASELINE_MERGE_READINESS_SUMMARY_PATH
)

official_gap_review = safe_load_csv(OFFICIAL_BASELINE_GAP_REVIEW_PATH)
official_scenario_recommendations = safe_load_csv(
    OFFICIAL_BASELINE_SCENARIO_RECOMMENDATIONS_PATH
)
official_merge_review_summary = safe_load_csv(
    OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_PATH
)

official_review_memo_text = safe_load_text(OFFICIAL_BASELINE_REVIEW_MEMO_PATH)

prozorro_expanded_feature_rows = safe_load_csv(PROZORRO_EXPANDED_FEATURE_ROWS_PATH)
prozorro_procurement_oblast = safe_load_csv(PROZORRO_PROCUREMENT_FEATURES_OBLAST_PATH)
prozorro_procurement_oblast_sector = safe_load_csv(
    PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_PATH
)
prozorro_procurement_scoring_candidates = safe_load_csv(
    PROZORRO_PROCUREMENT_SCORING_CANDIDATES_PATH
)
prozorro_procurement_feature_summary = safe_load_csv(
    PROZORRO_PROCUREMENT_FEATURE_SUMMARY_PATH
)

wartime_typology_register = safe_load_csv(WARTIME_AML_TYPOLOGY_REGISTER_PATH)
wartime_typology_layer_map = safe_load_csv(WARTIME_AML_TYPOLOGY_LAYER_MAP_PATH)
wartime_typology_summary = safe_load_csv(WARTIME_AML_TYPOLOGY_SUMMARY_PATH)

fiu_official_source_register = safe_load_csv(FIU_OFFICIAL_SOURCE_REGISTER_PATH)
fiu_reporting_statistics_context = safe_load_csv(FIU_REPORTING_STATISTICS_CONTEXT_PATH)
fiu_case_referral_context = safe_load_csv(FIU_CASE_REFERRAL_CONTEXT_PATH)
fiu_typology_support_register = safe_load_csv(FIU_TYPOLOGY_SUPPORT_REGISTER_PATH)
fiu_context_summary = safe_load_csv(FIU_CONTEXT_SUMMARY_PATH)

official_prozorro_context_bridge = safe_load_csv(
    OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_PATH
)
official_prozorro_context_review = safe_load_csv(
    OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_PATH
)
official_wartime_typology_context_bridge = safe_load_csv(
    OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_PATH
)
official_wartime_typology_context_review = safe_load_csv(
    OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_PATH
)
official_fiu_context_bridge = safe_load_csv(OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_PATH)
official_fiu_context_review = safe_load_csv(OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_PATH)
official_operational_controls_context_bridge = safe_load_csv(
    OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_PATH
)
official_operational_controls_context_review = safe_load_csv(
    OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_PATH
)

analyst_review_queue = safe_load_csv(ANALYST_REVIEW_QUEUE_PATH)
analyst_review_questions = safe_load_csv(ANALYST_REVIEW_QUESTIONS_PATH)
review_disposition_template = safe_load_csv(REVIEW_DISPOSITION_TEMPLATE_PATH)
analyst_review_summary = safe_load_csv(ANALYST_REVIEW_SUMMARY_PATH)

false_positive_risk_register = safe_load_csv(FALSE_POSITIVE_RISK_REGISTER_PATH)
false_positive_controls = safe_load_csv(FALSE_POSITIVE_CONTROLS_PATH)
false_positive_review_checklist = safe_load_csv(FALSE_POSITIVE_REVIEW_CHECKLIST_PATH)
false_positive_summary = safe_load_csv(FALSE_POSITIVE_SUMMARY_PATH)

source_freshness_inventory = safe_load_csv(SOURCE_FRESHNESS_INVENTORY_PATH)
source_freshness_assessment = safe_load_csv(SOURCE_FRESHNESS_ASSESSMENT_PATH)
source_freshness_replacement_priorities = safe_load_csv(
    SOURCE_FRESHNESS_REPLACEMENT_PRIORITIES_PATH
)
source_freshness_summary = safe_load_csv(SOURCE_FRESHNESS_SUMMARY_PATH)

run_manifest = safe_load_csv(RUN_MANIFEST_PATH)
run_manifest_summary = safe_load_csv(RUN_MANIFEST_SUMMARY_PATH)


score_col = "waris_aml_review_score"

scored = coerce_numeric(
    scored,
    [
        score_col,
        "revenue_anomaly_risk",
        "sanctions_exposure_risk",
        "procurement_integrity_risk",
        "ownership_opacity_risk",
        "tbml_risk",
        "conflict_plausibility_gap",
        "financial_supervision_exposure",
        "official_baseline_proxy",
    ],
)

oblast = coerce_numeric(
    oblast,
    [
        score_col,
        "max_sector_score",
        "official_baseline_proxy",
    ],
)

sector = coerce_numeric(
    sector,
    [
        score_col,
        "max_oblast_score",
    ],
)

mc = coerce_numeric(
    mc,
    [
        score_col,
        "mc_mean_score",
        "mc_p05_score",
        "mc_p95_score",
        "mc_uncertainty_width",
        "mc_mean_delta_from_base",
        "prob_elevated_or_high",
        "prob_high",
        "official_baseline_proxy",
    ],
)

if ukrstat_baseline_candidates is not None:
    ukrstat_baseline_candidates = coerce_numeric(
        ukrstat_baseline_candidates,
        ["official_regional_baseline_proxy"],
    )

if ukrstat_baseline_probe is not None:
    ukrstat_baseline_probe = coerce_numeric(
        ukrstat_baseline_probe,
        ["observation_value_count"],
    )

if official_benchmark_comparison is not None:
    official_benchmark_comparison = coerce_numeric(
        official_benchmark_comparison,
        [
            "official_grp_million_uah",
            "official_grp_share_of_waris_total",
            "official_grp_index_0_100",
            "synthetic_prewar_revenue_index_mean",
            "synthetic_prewar_revenue_index_sum",
            "synthetic_prewar_share_of_total",
            "synthetic_prewar_index_0_100",
            "official_to_synthetic_share_ratio",
            "official_vs_synthetic_index_gap",
            "sector_count",
        ],
    )

if official_rescale_scenario is not None:
    official_rescale_scenario = coerce_numeric(
        official_rescale_scenario,
        [
            "official_grp_million_uah",
            "official_oblast_scale_index",
            "sector_share_within_oblast",
            "prewar_revenue_index_2021",
            "scenario_prewar_revenue_index_2021",
            "current_revenue_index",
            "scenario_current_revenue_index",
            "original_revenue_change_pct",
        ],
    )

if official_replace_oblast_baseline is not None:
    official_replace_oblast_baseline = coerce_numeric(
        official_replace_oblast_baseline,
        [
            "scenario_oblast_baseline_value",
            "official_grp_share_of_waris_total",
            "official_grp_index_0_100",
            "synthetic_prewar_revenue_index_sum",
            "synthetic_prewar_share_of_total",
            "current_waris_score_mean",
        ],
    )

if official_gap_review is not None:
    official_gap_review = coerce_numeric(
        official_gap_review,
        [
            "official_grp_million_uah",
            "official_grp_share_of_waris_total",
            "synthetic_prewar_share_of_total",
            "official_grp_index_0_100",
            "synthetic_prewar_index_0_100",
            "official_vs_synthetic_index_gap",
            "absolute_index_gap",
            "official_to_synthetic_share_ratio",
        ],
    )

prozorro_numeric_cols = [
    "tender_count",
    "total_expected_value",
    "mean_expected_value",
    "single_bid_or_supplier_proxy_rate",
    "reconstruction_emergency_tender_count",
    "reconstruction_emergency_share",
    "unique_buyer_count",
    "procurement_method_count",
    "top_buyer_tender_share",
    "procurement_intensity_score",
    "procurement_value_score",
    "single_bid_supplier_score",
    "reconstruction_emergency_score",
    "buyer_concentration_score",
    "procurement_review_priority_candidate",
]

if prozorro_procurement_oblast is not None:
    prozorro_procurement_oblast = coerce_numeric(
        prozorro_procurement_oblast,
        prozorro_numeric_cols,
        preserve_missing=True,
    )

if prozorro_procurement_oblast_sector is not None:
    prozorro_procurement_oblast_sector = coerce_numeric(
        prozorro_procurement_oblast_sector,
        prozorro_numeric_cols,
        preserve_missing=True,
    )

if prozorro_procurement_scoring_candidates is not None:
    prozorro_procurement_scoring_candidates = coerce_numeric(
        prozorro_procurement_scoring_candidates,
        [
            "procurement_review_priority_candidate",
            "procurement_intensity_score",
            "procurement_value_score",
            "single_bid_supplier_score",
            "reconstruction_emergency_score",
            "buyer_concentration_score",
        ],
        preserve_missing=True,
    )

if prozorro_expanded_feature_rows is not None:
    prozorro_expanded_feature_rows = coerce_numeric(
        prozorro_expanded_feature_rows,
        [
            "value_amount",
            "bids_count",
            "supplier_count",
            "single_bid_or_supplier_proxy",
            "reconstruction_emergency_flag",
            "search_text_length",
            "mapped_to_waris_oblast",
            "mapped_to_waris_sector",
        ],
        preserve_missing=True,
    )

if analyst_review_queue is not None:
    analyst_review_queue = coerce_numeric(
        analyst_review_queue,
        [
            "waris_aml_review_score",
            "review_priority_score",
            "source_confidence_adjustment",
        ],
    )

if false_positive_review_checklist is not None:
    false_positive_review_checklist = coerce_numeric(
        false_positive_review_checklist,
        ["waris_aml_review_score"],
    )

if source_freshness_assessment is not None:
    source_freshness_assessment = coerce_numeric(
        source_freshness_assessment,
        ["row_count", "file_size_bytes", "age_days", "freshness_expectation_days"],
    )

if source_freshness_replacement_priorities is not None:
    source_freshness_replacement_priorities = coerce_numeric(
        source_freshness_replacement_priorities,
        ["priority_rank", "row_count", "age_days", "file_size_bytes"],
    )

if run_manifest is not None:
    run_manifest = coerce_numeric(
        run_manifest,
        ["row_count", "file_size_bytes"],
    )


with st.sidebar:
    st.header("Filters")

    selected_oblasts = st.multiselect(
        "Oblast",
        sorted(scored["oblast"].dropna().unique()),
    )

    selected_sectors = st.multiselect(
        "Sector",
        sorted(scored["sector"].dropna().unique()),
    )

    min_score = st.slider(
        "Minimum WARIS score",
        0,
        100,
        50,
    )

    st.divider()

    st.caption("Official baseline benchmark gate")
    st.write(
        "Ukrstat GRP candidates are approved for controlled benchmark integration only. "
        "They are not used in scoring."
    )

    st.divider()

    st.caption("Run refresh")
    st.code("python main.py", language="powershell")
    st.code("python -m src.ukrstat_observations", language="powershell")
    st.code("python -m src.official_baseline_validation", language="powershell")
    st.code("python -m src.official_baseline_merge_plan", language="powershell")
    st.code("python -m src.official_baseline_merge_review", language="powershell")
    st.code("python -m src.official_baseline_review_memo", language="powershell")
    st.code("python -m src.prozorro_procurement_features", language="powershell")
    st.code("python -m src.wartime_aml_typology_register", language="powershell")
    st.code("python -m src.fiu_official_context", language="powershell")
    st.code("python -m src.analyst_review_queue", language="powershell")
    st.code("python -m src.false_positive_controls", language="powershell")
    st.code("python -m src.source_freshness", language="powershell")
    st.code("python -m src.run_manifest", language="powershell")


filtered = scored.copy()

if selected_oblasts:
    filtered = filtered[filtered["oblast"].isin(selected_oblasts)]

if selected_sectors:
    filtered = filtered[filtered["sector"].isin(selected_sectors)]

filtered = filtered[filtered[score_col] >= min_score]


st.subheader("Model status")

status_row_1 = st.columns(4)
status_row_1[0].metric("Rows shown", len(filtered))
status_row_1[1].metric(
    "Average WARIS score",
    f"{filtered[score_col].mean():.1f}" if len(filtered) else "N/A",
)
status_row_1[2].metric(
    "High priority rows",
    int((filtered["risk_band"] == "High AML Review Priority").sum())
    if "risk_band" in filtered.columns
    else 0,
)
status_row_1[3].metric(
    "Elevated priority rows",
    int((filtered["risk_band"] == "Elevated AML Review Priority").sum())
    if "risk_band" in filtered.columns
    else 0,
)

status_row_2 = st.columns(4)
status_row_2[0].metric(
    "Live sources",
    int((live_status["status"] == "live").sum())
    if live_status is not None and not live_status.empty and "status" in live_status.columns
    else "N/A",
)
status_row_2[1].metric(
    "Ukrstat baseline candidates",
    len(ukrstat_baseline_candidates)
    if ukrstat_baseline_candidates is not None and not ukrstat_baseline_candidates.empty
    else "N/A",
)
status_row_2[2].metric(
    "Baseline decision",
    short_label(first_value(official_readiness_decision, "decision", "N/A")),
    help=first_value(official_readiness_decision, "decision", "N/A"),
)
status_row_2[3].metric(
    "Review posture",
    short_label(first_value(official_scenario_recommendations, "scenario_name", "N/A")),
    help=first_value(official_scenario_recommendations, "scenario_name", "N/A"),
)

status_row_3 = st.columns(4)
status_row_3[0].metric(
    "Prozorro feature rows",
    len(prozorro_procurement_oblast_sector)
    if prozorro_procurement_oblast_sector is not None
    and not prozorro_procurement_oblast_sector.empty
    else "N/A",
)
status_row_3[1].metric(
    "Typology references",
    len(wartime_typology_register)
    if wartime_typology_register is not None and not wartime_typology_register.empty
    else "N/A",
)
status_row_3[2].metric(
    "FIU/SFMS context rows",
    len(fiu_typology_support_register)
    if fiu_typology_support_register is not None
    and not fiu_typology_support_register.empty
    else "N/A",
)
status_row_3[3].metric(
    "Benchmark memo",
    "Available" if official_review_memo_text else "N/A",
)

status_row_4 = st.columns(4)
status_row_4[0].metric(
    "Analyst queue rows",
    len(analyst_review_queue)
    if analyst_review_queue is not None and not analyst_review_queue.empty
    else "N/A",
)
status_row_4[1].metric(
    "False-positive controls",
    len(false_positive_controls)
    if false_positive_controls is not None and not false_positive_controls.empty
    else "N/A",
)
status_row_4[2].metric(
    "Freshness posture",
    short_label(
        summary_lookup(
            source_freshness_summary,
            "Overall freshness posture",
            column="status",
            fallback=first_value(source_freshness_summary, "status", "N/A"),
        )
    ),
    help=summary_lookup(
        source_freshness_summary,
        "Overall freshness posture",
        column="value",
        fallback=first_value(source_freshness_summary, "status", "N/A"),
    ),
)
status_row_4[3].metric(
    "Run manifest version",
    short_label(first_value(run_manifest_summary, "model_version", "N/A")),
)



if (
    analyst_review_summary is not None
    or false_positive_summary is not None
    or source_freshness_summary is not None
    or run_manifest_summary is not None
):
    st.subheader("Operational controls status")
    st.info(
        "These artifacts support human review, false-positive handling, source "
        "maintenance, and run reproducibility. They do not approve scoring, create "
        "findings, or authorize automated adverse action."
    )

    control_cols = st.columns(4)
    control_cols[0].metric(
        "Review questions",
        len(analyst_review_questions)
        if analyst_review_questions is not None and not analyst_review_questions.empty
        else "N/A",
        help="Generated human-review questions. Not scoring inputs.",
    )
    control_cols[1].metric(
        "False-positive checklist",
        len(false_positive_review_checklist)
        if false_positive_review_checklist is not None
        and not false_positive_review_checklist.empty
        else "N/A",
        help="Checklist rows for benign explanations and review controls.",
    )
    control_cols[2].metric(
        "Freshness artifacts",
        len(source_freshness_assessment)
        if source_freshness_assessment is not None
        and not source_freshness_assessment.empty
        else "N/A",
        help="Artifacts checked for availability, file age, and row counts.",
    )
    control_cols[3].metric(
        "Manifest rows",
        len(run_manifest)
        if run_manifest is not None and not run_manifest.empty
        else "N/A",
        help="Run-manifest inventory rows.",
    )


if ukrstat_baseline_candidates is not None and not ukrstat_baseline_candidates.empty:
    st.subheader("Official Ukrstat baseline benchmark-integration gate")

    gate_cols = st.columns(6)

    gate_cols[0].metric(
        "Candidate rows",
        len(ukrstat_baseline_candidates),
    )

    gate_cols[1].metric(
        "Successful probes",
        bool_count(ukrstat_baseline_probe, "success_status"),
    )

    gate_cols[2].metric(
        "Probes with observations",
        bool_count(ukrstat_baseline_probe, "has_observations"),
    )

    gate_cols[3].metric(
        "Readiness decision",
        short_label(first_value(official_readiness_decision, "decision", "NO_GO")),
        help=first_value(official_readiness_decision, "decision", "NO_GO"),
    )

    gate_cols[4].metric(
        "Checks passed",
        count_status(official_validation_register, "pass"),
    )

    gate_cols[5].metric(
        "Checks needing review",
        count_status(official_validation_register, "review_required")
        + count_status(official_validation_register, "partial"),
    )

    approved_use = first_value(
        official_readiness_decision,
        "approved_current_use",
        "validation_and_reporting_context_only",
    )
    prohibited_use = first_value(
        official_readiness_decision,
        "prohibited_current_use",
        "risk_layer_calculation_or_composite_scoring",
    )

    st.info(
        "**Official baseline posture:** Ukrstat GRP candidates are approved for "
        "controlled benchmark integration only and remain excluded from scoring.\n\n"
        f"- **Readiness decision:** {short_label(first_value(official_readiness_decision, 'decision', 'N/A'))}\n"
        f"- **Approved current use:** {short_label(approved_use)}\n"
        f"- **Prohibited current use:** {short_label(prohibited_use)}"
    )

    validation_cols = [
        col
        for col in [
            "oblast",
            "region_code",
            "indicator_code",
            "nace_code",
            "freq_code",
            "latest_period",
            "official_regional_baseline_proxy",
            "source_status",
            "validation_status",
            "current_use_in_scoring",
        ]
        if col in ukrstat_baseline_candidates.columns
    ]

    with st.expander("View official Ukrstat baseline candidate table"):
        st.dataframe(
            ukrstat_baseline_candidates[validation_cols],
            width="stretch",
            hide_index=True,
        )

    if official_validation_summary is not None and not official_validation_summary.empty:
        with st.expander("View official baseline validation summary", expanded=True):
            st.dataframe(
                official_validation_summary,
                width="stretch",
                hide_index=True,
            )

    if (
        official_merge_readiness_summary is not None
        and not official_merge_readiness_summary.empty
    ):
        with st.expander("View official baseline merge-readiness summary", expanded=True):
            st.dataframe(
                official_merge_readiness_summary,
                width="stretch",
                hide_index=True,
            )

    if (
        official_unit_evidence_summary is not None
        and not official_unit_evidence_summary.empty
    ):
        with st.expander("View official unit and scale evidence"):
            st.dataframe(
                official_unit_evidence_summary,
                width="stretch",
                hide_index=True,
            )

    if (
        official_merge_review_summary is not None
        and not official_merge_review_summary.empty
    ):
        with st.expander("View official baseline merge-review summary", expanded=True):
            st.dataframe(
                official_merge_review_summary,
                width="stretch",
                hide_index=True,
            )

    if official_review_memo_text:
        with st.expander("View official baseline benchmark review memo"):
            st.markdown(official_review_memo_text)


if live_status is not None and not live_status.empty:
    st.subheader("Live/source-backed enrichment status")

    live_status_display = live_status.copy()

    if "rows" in live_status_display.columns:
        live_status_display["rows"] = pd.to_numeric(
            live_status_display["rows"],
            errors="coerce",
        ).fillna(0).astype(int)

    st.dataframe(
        live_status_display,
        width="stretch",
        hide_index=True,
    )


if (
    prozorro_procurement_feature_summary is not None
    and not prozorro_procurement_feature_summary.empty
):
    st.subheader("Expanded Prozorro procurement features")

    st.warning(
        "Expanded Prozorro procurement features are review-only candidate "
        "artifacts. They are not blended into WARIS production scoring. "
        "Current use remains review_artifact_only with production_score_change=none."
    )

    st.dataframe(
        prozorro_procurement_feature_summary,
        width="stretch",
        hide_index=True,
    )


if (
    wartime_typology_summary is not None
    and not wartime_typology_summary.empty
):
    st.subheader("Wartime AML/CFT typology reference layer")
    st.warning(
        "Wartime AML/CFT typology artifacts are literature-support references only. "
        "They are not measured risk indicators and are not used in WARIS scoring "
        "or Monte Carlo simulation."
    )
    st.dataframe(
        wartime_typology_summary,
        width="stretch",
        hide_index=True,
    )

if fiu_context_summary is not None and not fiu_context_summary.empty:
    st.subheader("Official FIU/SFMS context layer")
    st.warning(
        "Official FIU/SFMS artifacts are source-support context only. They do not "
        "create oblast, sector, entity, or person-level findings and are not used "
        "in WARIS scoring or Monte Carlo simulation."
    )
    st.dataframe(
        fiu_context_summary,
        width="stretch",
        hide_index=True,
    )

st.subheader("Top sector/oblast review signals")

display_cols = [
    col
    for col in [
        "oblast",
        "sector",
        "waris_aml_review_score",
        "risk_band",
        "review_rationale",
        "revenue_anomaly_risk",
        "sanctions_exposure_risk",
        "procurement_integrity_risk",
        "ownership_opacity_risk",
        "tbml_risk",
        "conflict_plausibility_gap",
        "financial_supervision_exposure",
        "official_baseline_candidate_available",
        "official_baseline_used_in_scoring",
        "official_baseline_latest_period",
        "official_baseline_proxy",
        "official_baseline_validation_status",
        "official_baseline_current_use_in_scoring",
        "wartime_aml_typology_available",
        "wartime_aml_typology_used_in_scoring",
        "wartime_aml_typology_control_ok",
        "fiu_context_available",
        "fiu_context_used_in_scoring",
        "fiu_context_control_ok",
        "analyst_review_available",
        "analyst_review_used_in_scoring",
        "false_positive_controls_available",
        "false_positive_controls_used_in_scoring",
        "source_freshness_available",
        "source_freshness_used_in_scoring",
        "run_manifest_available",
        "run_manifest_used_in_scoring",
        "operational_controls_used_in_scoring",
        "operational_controls_score_change_ok",
    ]
    if col in filtered.columns
]

st.dataframe(
    filtered.sort_values(score_col, ascending=False)[display_cols],
    width="stretch",
    hide_index=True,
)


st.subheader("Charts")

available_charts = {
    name: path
    for name, path in CHART_PATHS.items()
    if path.exists()
}

if available_charts:
    selected_chart = st.selectbox(
        "Select chart",
        list(available_charts.keys()),
    )

    st.image(str(available_charts[selected_chart]), width="stretch")
else:
    st.info("No chart images found. Run `python main.py` to generate charts.")


tab_names = [
    "Oblast summary",
    "Sector summary",
    "Monte Carlo robustness",
    "Official validation gate",
    "Official benchmark integration",
    "Official merge review",
    "Official review memo",
    "Prozorro procurement features",
    "Wartime AML typology",
    "Official FIU/SFMS context",
    "Context bridges",
    "Operational controls",
    "Official Ukrstat baseline",
    "ACLED conflict proxy",
]

(
    tab1,
    tab2,
    tab3,
    tab4,
    tab5,
    tab6,
    tab7,
    tab8,
    tab9,
    tab10,
    tab11,
    tab12,
    tab13,
    tab14,
) = st.tabs(tab_names)

with tab1:
    st.dataframe(
        oblast.sort_values(score_col, ascending=False),
        width="stretch",
        hide_index=True,
    )

with tab2:
    st.dataframe(
        sector.sort_values(score_col, ascending=False),
        width="stretch",
        hide_index=True,
    )

with tab3:
    mc_display = mc.copy()

    sort_col = (
        "prob_elevated_or_high"
        if "prob_elevated_or_high" in mc_display.columns
        else score_col
    )

    mc_cols = [
        col
        for col in [
            "oblast",
            "sector",
            "waris_aml_review_score",
            "mc_mean_score",
            "mc_p05_score",
            "mc_p95_score",
            "mc_uncertainty_width",
            "prob_elevated_or_high",
            "prob_high",
            "robustness_band",
            "uncertainty_band",
            "signal_stability_flag",
            "official_baseline_candidate_available",
            "official_baseline_used_in_monte_carlo",
            "official_baseline_latest_period",
            "official_baseline_proxy",
            "official_baseline_validation_status",
            "official_baseline_current_use_in_scoring",
        ]
        if col in mc_display.columns
    ]

    st.dataframe(
        mc_display.sort_values(sort_col, ascending=False)[mc_cols],
        width="stretch",
        hide_index=True,
    )

with tab4:
    st.markdown(
        "The official baseline validation gate documents whether Ukrstat GRP "
        "candidate values are ready for controlled benchmark integration. Current "
        "posture is GO for controlled benchmark integration, while risk-layer "
        "calculation and composite scoring remain prohibited."
    )

    if official_readiness_decision is not None and not official_readiness_decision.empty:
        st.markdown("#### Readiness decision")
        st.dataframe(
            official_readiness_decision,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "No official baseline readiness decision found. Run "
            "`python -m src.official_baseline_validation`."
        )

    if official_validation_summary is not None and not official_validation_summary.empty:
        st.markdown("#### Validation summary")
        st.dataframe(
            official_validation_summary,
            width="stretch",
            hide_index=True,
        )

    if official_validation_register is not None and not official_validation_register.empty:
        st.markdown("#### Validation check register")

        register_display = official_validation_register.copy()

        if {"status", "severity"}.issubset(register_display.columns):
            status_order = {
                "review_required": 0,
                "partial": 1,
                "pass": 2,
            }
            severity_order = {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "info": 3,
            }
            register_display["_status_order"] = (
                register_display["status"].fillna("").astype(str).map(status_order).fillna(9)
            )
            register_display["_severity_order"] = (
                register_display["severity"].fillna("").astype(str).map(severity_order).fillna(9)
            )
            register_display = register_display.sort_values(
                ["_status_order", "_severity_order", "check_id"]
            ).drop(columns=["_status_order", "_severity_order"])

        st.dataframe(
            register_display,
            width="stretch",
            hide_index=True,
        )

    if official_geography_check is not None and not official_geography_check.empty:
        st.markdown("#### Geography crosswalk validation")
        st.dataframe(
            official_geography_check,
            width="stretch",
            hide_index=True,
        )

    if official_period_coverage is not None and not official_period_coverage.empty:
        st.markdown("#### Period coverage validation")
        st.dataframe(
            official_period_coverage,
            width="stretch",
            hide_index=True,
        )

    if (
        official_unit_evidence_summary is not None
        and not official_unit_evidence_summary.empty
    ):
        st.markdown("#### Official unit and scale evidence")
        st.dataframe(
            official_unit_evidence_summary,
            width="stretch",
            hide_index=True,
        )

    if official_unit_evidence is not None and not official_unit_evidence.empty:
        st.markdown("#### Unit evidence sample")
        st.dataframe(
            official_unit_evidence.head(50),
            width="stretch",
            hide_index=True,
        )

with tab5:
    st.markdown(
        "The official baseline merge-plan compares official GRP values against "
        "WARIS synthetic baselines in controlled, non-production benchmark artifacts. "
        "These tables do not alter WARIS scores."
    )

    if (
        official_merge_readiness_summary is not None
        and not official_merge_readiness_summary.empty
    ):
        st.markdown("#### Merge-readiness summary")
        st.dataframe(
            official_merge_readiness_summary,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "No official baseline merge-readiness summary found. Run "
            "`python -m src.official_baseline_merge_plan`."
        )

    if official_merge_plan is not None and not official_merge_plan.empty:
        st.markdown("#### Merge plan scenarios")
        st.dataframe(
            official_merge_plan,
            width="stretch",
            hide_index=True,
        )

    if (
        official_benchmark_comparison is not None
        and not official_benchmark_comparison.empty
    ):
        st.markdown("#### Benchmark-only comparison")

        benchmark_display = official_benchmark_comparison.copy()

        if "official_vs_synthetic_index_gap" in benchmark_display.columns:
            benchmark_display["abs_index_gap"] = pd.to_numeric(
                benchmark_display["official_vs_synthetic_index_gap"],
                errors="coerce",
            ).abs()
            benchmark_display = benchmark_display.sort_values(
                "abs_index_gap",
                ascending=False,
            )

        st.dataframe(
            benchmark_display,
            width="stretch",
            hide_index=True,
        )

    if official_rescale_scenario is not None and not official_rescale_scenario.empty:
        st.markdown("#### Rescale revenue baseline scenario")
        st.dataframe(
            official_rescale_scenario,
            width="stretch",
            hide_index=True,
        )

    if (
        official_replace_oblast_baseline is not None
        and not official_replace_oblast_baseline.empty
    ):
        st.markdown("#### Replace-oblast-baseline scenario")
        st.dataframe(
            official_replace_oblast_baseline,
            width="stretch",
            hide_index=True,
        )

with tab6:
    st.markdown(
        "The official merge-review layer summarizes official-vs-synthetic baseline "
        "gaps and scenario recommendations. Current posture remains benchmark-only "
        "within controlled benchmark integration. These tables do not alter WARIS scores."
    )

    if (
        official_merge_review_summary is not None
        and not official_merge_review_summary.empty
    ):
        st.markdown("#### Merge-review summary")
        st.dataframe(
            official_merge_review_summary,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "No official baseline merge-review summary found. Run "
            "`python -m src.official_baseline_merge_review`."
        )

    if (
        official_scenario_recommendations is not None
        and not official_scenario_recommendations.empty
    ):
        st.markdown("#### Scenario recommendations")
        st.dataframe(
            official_scenario_recommendations,
            width="stretch",
            hide_index=True,
        )

    if official_gap_review is not None and not official_gap_review.empty:
        st.markdown("#### Official-vs-synthetic gap review")

        gap_display = official_gap_review.copy()

        if "absolute_index_gap" in gap_display.columns:
            gap_display = gap_display.sort_values(
                "absolute_index_gap",
                ascending=False,
            )

        st.dataframe(
            gap_display,
            width="stretch",
            hide_index=True,
        )

with tab7:
    st.markdown(
        "The benchmark review memo is the plain-language analyst artifact that "
        "explains the official baseline validation, merge-planning, merge-review "
        "findings, and the current benchmark_only posture."
    )

    if official_review_memo_text:
        executive_summary = extract_markdown_section(
            official_review_memo_text,
            "Executive summary",
        )
        control_assessment = extract_markdown_section(
            official_review_memo_text,
            "Control assessment",
        )
        gap_findings = extract_markdown_section(
            official_review_memo_text,
            "Benchmark gap findings",
        )
        typology_context_review_section = extract_markdown_section(
            official_review_memo_text,
            "Official baseline to wartime AML/CFT typology context review",
        )
        fiu_context_review_section = extract_markdown_section(
            official_review_memo_text,
            "Official baseline to FIU/SFMS context review",
        )
        recommendation = extract_markdown_section(
            official_review_memo_text,
            "Current recommendation",
        )
        next_actions = extract_markdown_section(
            official_review_memo_text,
            "Recommended next actions",
        )

        st.markdown("#### Executive summary")
        st.markdown(executive_summary)

        st.markdown("#### Control assessment")
        st.markdown(control_assessment)

        st.markdown("#### Benchmark gap findings")
        st.markdown(gap_findings)

        st.markdown("#### Official baseline to wartime AML/CFT typology context review")
        st.markdown(typology_context_review_section)

        st.markdown("#### Official baseline to FIU/SFMS context review")
        st.markdown(fiu_context_review_section)

        st.markdown("#### Current recommendation")
        st.markdown(recommendation)

        st.markdown("#### Recommended next actions")
        st.markdown(next_actions)

        with st.expander("View full benchmark review memo"):
            st.markdown(official_review_memo_text)
    else:
        st.info(
            "No official baseline benchmark review memo found. Run "
            "`python -m src.official_baseline_review_memo`."
        )

with tab8:
    st.markdown(
        "The expanded Prozorro procurement feature layer adds source-backed "
        "procurement review artifacts such as tender count, expected value, "
        "single-bid/supplier proxy, buyer concentration, and reconstruction/emergency "
        "keyword exposure. These tables are review-only and do not alter WARIS scores."
    )

    if (
        prozorro_procurement_feature_summary is not None
        and not prozorro_procurement_feature_summary.empty
    ):
        st.markdown("#### Procurement feature summary")
        st.dataframe(
            prozorro_procurement_feature_summary,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "No expanded Prozorro procurement feature summary found. Run "
            "`python -m src.prozorro_procurement_features`."
        )

    if (
        prozorro_procurement_oblast is not None
        and not prozorro_procurement_oblast.empty
    ):
        st.markdown("#### Oblast procurement feature candidates")

        oblast_display = prozorro_procurement_oblast.copy()

        if "procurement_review_priority_candidate" in oblast_display.columns:
            oblast_display = oblast_display.sort_values(
                "procurement_review_priority_candidate",
                ascending=False,
            )

        st.dataframe(
            oblast_display,
            width="stretch",
            hide_index=True,
        )

    if (
        prozorro_procurement_oblast_sector is not None
        and not prozorro_procurement_oblast_sector.empty
    ):
        st.markdown("#### Oblast-sector procurement candidates")

        sector_display = prozorro_procurement_oblast_sector.copy()

        if "procurement_review_priority_candidate" in sector_display.columns:
            sector_display = sector_display.sort_values(
                "procurement_review_priority_candidate",
                ascending=False,
            )

        st.dataframe(
            sector_display,
            width="stretch",
            hide_index=True,
        )

    if (
        prozorro_procurement_scoring_candidates is not None
        and not prozorro_procurement_scoring_candidates.empty
    ):
        st.markdown("#### Procurement scoring-candidate control table")
        st.warning(
            "This table documents candidate procurement features for a possible "
            "future governed scoring branch. Current production_score_change remains none."
        )

        scoring_display = prozorro_procurement_scoring_candidates.copy()

        if "procurement_review_priority_candidate" in scoring_display.columns:
            scoring_display = scoring_display.sort_values(
                "procurement_review_priority_candidate",
                ascending=False,
            )

        st.dataframe(
            scoring_display,
            width="stretch",
            hide_index=True,
        )

    if (
        prozorro_expanded_feature_rows is not None
        and not prozorro_expanded_feature_rows.empty
    ):
        with st.expander("View expanded Prozorro raw feature rows"):
            st.dataframe(
                prozorro_expanded_feature_rows,
                width="stretch",
                hide_index=True,
            )

with tab9:
    st.markdown(
        "Wartime AML/CFT typology artifacts are literature-support references. "
        "They support source-confidence review, governance, and future feature "
        "design only. They are not scoring inputs."
    )

    if wartime_typology_summary is not None and not wartime_typology_summary.empty:
        st.markdown("#### Typology summary")
        st.dataframe(
            wartime_typology_summary,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "No wartime AML/CFT typology summary found. Run "
            "`python -m src.wartime_aml_typology_register`."
        )

    if wartime_typology_register is not None and not wartime_typology_register.empty:
        st.markdown("#### Typology register")
        st.dataframe(
            wartime_typology_register,
            width="stretch",
            hide_index=True,
        )

    if wartime_typology_layer_map is not None and not wartime_typology_layer_map.empty:
        st.markdown("#### Typology-to-WARIS layer map")
        st.dataframe(
            wartime_typology_layer_map,
            width="stretch",
            hide_index=True,
        )


with tab10:
    st.markdown(
        "Official FIU/SFMS context artifacts provide national source-support "
        "context for governance and typology review. They are not direct "
        "oblast/sector scoring inputs."
    )

    if fiu_context_summary is not None and not fiu_context_summary.empty:
        st.markdown("#### FIU/SFMS context summary")
        st.dataframe(
            fiu_context_summary,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "No official FIU/SFMS context summary found. Run "
            "`python -m src.fiu_official_context`."
        )

    if (
        fiu_official_source_register is not None
        and not fiu_official_source_register.empty
    ):
        st.markdown("#### Official source register")
        st.dataframe(
            fiu_official_source_register,
            width="stretch",
            hide_index=True,
        )

    if (
        fiu_reporting_statistics_context is not None
        and not fiu_reporting_statistics_context.empty
    ):
        st.markdown("#### Reporting statistics context")
        st.dataframe(
            fiu_reporting_statistics_context,
            width="stretch",
            hide_index=True,
        )

    if fiu_case_referral_context is not None and not fiu_case_referral_context.empty:
        st.markdown("#### Case referral context")
        st.dataframe(
            fiu_case_referral_context,
            width="stretch",
            hide_index=True,
        )

    if (
        fiu_typology_support_register is not None
        and not fiu_typology_support_register.empty
    ):
        st.markdown("#### Typology-support register")
        st.dataframe(
            fiu_typology_support_register,
            width="stretch",
            hide_index=True,
        )


with tab11:
    st.markdown(
        "Official baseline source-context bridges compare official baseline "
        "benchmark context with Prozorro, wartime typology, FIU/SFMS context, "
        "and operational-control artifacts. These are review artifacts only and "
        "do not approve scoring integration."
    )

    context_frames = [
        ("Official baseline to Prozorro context review", official_prozorro_context_review),
        (
            "Official baseline to wartime AML/CFT typology context review",
            official_wartime_typology_context_review,
        ),
        ("Official baseline to FIU/SFMS context review", official_fiu_context_review),
        (
            "Official baseline to operational controls context review",
            official_operational_controls_context_review,
        ),
        ("Official baseline to Prozorro context bridge", official_prozorro_context_bridge),
        (
            "Official baseline to wartime typology context bridge",
            official_wartime_typology_context_bridge,
        ),
        ("Official baseline to FIU/SFMS context bridge", official_fiu_context_bridge),
        (
            "Official baseline to operational controls context bridge",
            official_operational_controls_context_bridge,
        ),
    ]

    any_context_frame = False

    for title, frame in context_frames:
        if frame is not None and not frame.empty:
            any_context_frame = True
            st.markdown(f"#### {title}")
            st.dataframe(frame, width="stretch", hide_index=True)

    if not any_context_frame:
        st.info(
            "No official baseline context bridge/review tables found. Run "
            "`python -m src.official_baseline_merge_plan` and "
            "`python -m src.official_baseline_merge_review`."
        )


with tab12:
    st.markdown(
        "Operational-control artifacts help make WARIS safer and more auditable. "
        "They support analyst review, false-positive handling, source-freshness "
        "monitoring, and run reproducibility. They do not change scoring, validate "
        "model accuracy, create findings, or authorize automated adverse action."
    )

    if analyst_review_summary is not None and not analyst_review_summary.empty:
        st.markdown("#### Analyst review workflow summary")
        st.dataframe(
            analyst_review_summary,
            width="stretch",
            hide_index=True,
        )

    if analyst_review_queue is not None and not analyst_review_queue.empty:
        st.markdown("#### Analyst review queue")
        st.dataframe(
            analyst_review_queue,
            width="stretch",
            hide_index=True,
        )

    if analyst_review_questions is not None and not analyst_review_questions.empty:
        with st.expander("View analyst review questions"):
            st.dataframe(
                analyst_review_questions,
                width="stretch",
                hide_index=True,
            )

    if review_disposition_template is not None and not review_disposition_template.empty:
        with st.expander("View review disposition template"):
            st.dataframe(
                review_disposition_template,
                width="stretch",
                hide_index=True,
            )

    if false_positive_summary is not None and not false_positive_summary.empty:
        st.markdown("#### False-positive controls summary")
        st.dataframe(
            false_positive_summary,
            width="stretch",
            hide_index=True,
        )

    if false_positive_controls is not None and not false_positive_controls.empty:
        st.markdown("#### False-positive controls")
        st.dataframe(
            false_positive_controls,
            width="stretch",
            hide_index=True,
        )

    if false_positive_risk_register is not None and not false_positive_risk_register.empty:
        with st.expander("View false-positive risk register"):
            st.dataframe(
                false_positive_risk_register,
                width="stretch",
                hide_index=True,
            )

    if (
        false_positive_review_checklist is not None
        and not false_positive_review_checklist.empty
    ):
        with st.expander("View false-positive review checklist"):
            st.dataframe(
                false_positive_review_checklist,
                width="stretch",
                hide_index=True,
            )

    if source_freshness_summary is not None and not source_freshness_summary.empty:
        st.markdown("#### Source freshness summary")
        st.dataframe(
            source_freshness_summary,
            width="stretch",
            hide_index=True,
        )

    if (
        source_freshness_replacement_priorities is not None
        and not source_freshness_replacement_priorities.empty
    ):
        st.markdown("#### Source freshness replacement priorities")
        st.dataframe(
            source_freshness_replacement_priorities,
            width="stretch",
            hide_index=True,
        )

    if source_freshness_assessment is not None and not source_freshness_assessment.empty:
        with st.expander("View source freshness assessment"):
            st.dataframe(
                source_freshness_assessment,
                width="stretch",
                hide_index=True,
            )

    if run_manifest_summary is not None and not run_manifest_summary.empty:
        st.markdown("#### Run manifest summary")
        st.dataframe(
            run_manifest_summary,
            width="stretch",
            hide_index=True,
        )

    if run_manifest is not None and not run_manifest.empty:
        st.markdown("#### Run manifest inventory")
        st.dataframe(
            run_manifest,
            width="stretch",
            hide_index=True,
        )

    if (
        official_operational_controls_context_review is not None
        and not official_operational_controls_context_review.empty
    ):
        st.markdown("#### Official baseline to operational controls review")
        st.dataframe(
            official_operational_controls_context_review,
            width="stretch",
            hide_index=True,
        )

    if (
        official_operational_controls_context_bridge is not None
        and not official_operational_controls_context_bridge.empty
    ):
        with st.expander("View official baseline to operational controls bridge"):
            st.dataframe(
                official_operational_controls_context_bridge,
                width="stretch",
                hide_index=True,
            )

    if all(
        df is None or df.empty
        for df in [
            analyst_review_summary,
            analyst_review_queue,
            false_positive_summary,
            false_positive_controls,
            source_freshness_summary,
            run_manifest_summary,
            official_operational_controls_context_review,
        ]
    ):
        st.info(
            "No operational-control artifacts found. Run `python main.py` or the "
            "individual analyst_review_queue, false_positive_controls, "
            "source_freshness, and run_manifest modules."
        )


with tab13:
    st.markdown(
        "Official Ukrstat GRP baseline candidates are shown here for validation, "
        "source-lineage review, and controlled benchmark context only. They are not "
        "scoring inputs."
    )

    if ukrstat_baseline_candidates is not None and not ukrstat_baseline_candidates.empty:
        st.markdown("#### Baseline candidates")

        st.dataframe(
            ukrstat_baseline_candidates,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "No official baseline candidate table found. Run "
            "`python -m src.ukrstat_observations`."
        )

    if ukrstat_baseline_probe is not None and not ukrstat_baseline_probe.empty:
        st.markdown("#### Baseline probe results")

        probe_cols = [
            col
            for col in [
                "oblast",
                "region_code",
                "sdmx_key",
                "http_status",
                "success_status",
                "observation_value_count",
                "has_observations",
                "notes",
            ]
            if col in ukrstat_baseline_probe.columns
        ]

        st.dataframe(
            ukrstat_baseline_probe[probe_cols],
            width="stretch",
            hide_index=True,
        )

    if ukrstat_confirmed_series is not None and not ukrstat_confirmed_series.empty:
        st.markdown("#### Confirmed single-series parsed observations")

        st.dataframe(
            ukrstat_confirmed_series,
            width="stretch",
            hide_index=True,
        )

    if ukrstat_availability_values is not None and not ukrstat_availability_values.empty:
        st.markdown("#### Availability-derived value candidates")

        availability_cols = [
            col
            for col in [
                "dimension_id",
                "value_code",
                "value_name",
                "candidate_role",
                "query_use_status",
                "validation_status",
                "notes",
            ]
            if col in ukrstat_availability_values.columns
        ]

        st.dataframe(
            ukrstat_availability_values[availability_cols],
            width="stretch",
            hide_index=True,
        )

    if ukrstat_query_plan is not None and not ukrstat_query_plan.empty:
        st.markdown("#### Observation query plan")

        st.dataframe(
            ukrstat_query_plan,
            width="stretch",
            hide_index=True,
        )

with tab14:
    if acled_conflict is not None and not acled_conflict.empty:
        conflict_display = acled_conflict.copy()

        numeric_cols = [
            "live_event_count",
            "live_fatalities",
            "conflict_intensity_proxy_live",
            "event_count_scaled",
            "fatalities_scaled",
        ]

        for col in numeric_cols:
            if col in conflict_display.columns:
                conflict_display[col] = pd.to_numeric(
                    conflict_display[col],
                    errors="coerce",
                ).fillna(0)

        if "conflict_intensity_proxy_live" in conflict_display.columns:
            conflict_display = conflict_display.sort_values(
                "conflict_intensity_proxy_live",
                ascending=False,
            )

        st.dataframe(
            conflict_display,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "No ACLED conflict proxy table found. Run `python main.py` after enabling ACLED."
        )


st.divider()

st.info(
    "Model governance note: WARIS is a research prototype for prioritizing human "
    "AML/supervisory review. It does not accuse any person, company, institution, "
    "sector, or region of wrongdoing. Official Ukrstat GRP baseline candidates are "
    "approved for controlled benchmark integration only and are not used in scoring. "
    "The current official baseline readiness decision is "
    "GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION when validation artifacts support it. "
    "Risk-layer calculation and composite scoring remain prohibited until "
    "transformation logic, SME review, and scoring change control are documented. "
    "The current merge-review recommendation is benchmark_only. The benchmark "
    "review memo explains these findings in plain language. Expanded Prozorro "
    "procurement features are review-only candidate artifacts and remain excluded "
    "from production scoring until coverage validation, SME review, and model "
    "change control are complete. Wartime AML/CFT typology artifacts are "
    "literature-support references only, and official FIU/SFMS artifacts are "
    "source-support context only. Official baseline context bridges, including "
    "operational-controls bridge/review artifacts, are review artifacts only and "
    "do not approve scoring integration. Analyst-review, false-positive, "
    "source-freshness, and run-manifest artifacts are operational controls only; "
    "they support human review and reproducibility but do not validate the model "
    "or authorize automated adverse action."
)
