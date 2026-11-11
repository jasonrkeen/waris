"""Official baseline merge-planning artifacts for WARIS.

This module creates controlled, non-production benchmark-integration artifacts
for official Ukrstat GRP oblast baseline candidates.

It does not change WARIS production scoring.

Purpose:
    Compare the synthetic WARIS revenue baseline against official Ukrstat GRP
    candidates and document possible future integration options.

Current approved use expected from official_baseline_validation.py:
    GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION

Current prohibited use:
    risk_layer_calculation_or_composite_scoring

Outputs:
    outputs/tables/official_baseline_merge_plan.csv
    outputs/tables/official_baseline_benchmark_comparison.csv
    outputs/tables/official_baseline_rescale_scenario.csv
    outputs/tables/official_baseline_replace_oblast_baseline_scenario.csv
    outputs/tables/official_baseline_merge_readiness_summary.csv
    outputs/tables/official_baseline_prozorro_context_bridge.csv
    outputs/tables/official_baseline_wartime_typology_context_bridge.csv
    outputs/tables/official_baseline_fiu_context_bridge.csv
    outputs/tables/official_baseline_operational_controls_context_bridge.csv

Expanded Prozorro procurement features, wartime AML/CFT typology artifacts,
official FIU/SFMS context artifacts, analyst-review outputs, false-positive
controls, source-freshness outputs, and run-manifest artifacts remain
review/support/documentation artifacts and are not merged into official baseline
scoring scenarios. This module only adds controlled context bridges so analysts
can compare official baseline scale with review-only source-support and
operational-control layers before any future change-control discussion.
"""

from __future__ import annotations

from .controlled_guards import rescale as strict_rescale

from .utils import official_baseline_observations

from pathlib import Path

import pandas as pd

from .config import RAW_DIR, TABLE_DIR
from .utils import ensure_dirs, min_max_scale

try:
    from .config import PROCESSED_DIR
except ImportError:
    PROCESSED_DIR = RAW_DIR.parent / "processed"

try:
    from .config import (
        PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE,
        PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE,
        PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE,
        PROZORRO_PROCUREMENT_CURRENT_USE,
        PROZORRO_PROCUREMENT_PROHIBITED_USE,
        PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE,
    )
except ImportError:
    PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE = (
        TABLE_DIR / "prozorro_procurement_features_oblast.csv"
    )
    PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE = (
        TABLE_DIR / "prozorro_procurement_features_oblast_sector.csv"
    )
    PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE = (
        TABLE_DIR / "prozorro_procurement_scoring_candidates.csv"
    )
    PROZORRO_PROCUREMENT_CURRENT_USE = "review_artifact_only"
    PROZORRO_PROCUREMENT_PROHIBITED_USE = "direct_scoring_without_change_control"
    PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE = "none"

try:
    from .config import (
        WARTIME_AML_TYPOLOGY_REGISTER_TABLE,
        WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE,
        WARTIME_AML_TYPOLOGY_SUMMARY_TABLE,
        WARTIME_AML_TYPOLOGY_CURRENT_USE,
        WARTIME_AML_TYPOLOGY_PROHIBITED_USE,
        WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE,
        FIU_OFFICIAL_SOURCE_REGISTER_TABLE,
        FIU_REPORTING_STATISTICS_CONTEXT_TABLE,
        FIU_CASE_REFERRAL_CONTEXT_TABLE,
        FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE,
        FIU_CONTEXT_SUMMARY_TABLE,
        FIU_CONTEXT_CURRENT_USE,
        FIU_CONTEXT_PROHIBITED_USE,
        FIU_CONTEXT_PRODUCTION_SCORE_CHANGE,
    )
except ImportError:
    WARTIME_AML_TYPOLOGY_REGISTER_TABLE = (
        TABLE_DIR / "waris_wartime_aml_typology_register.csv"
    )
    WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE = (
        TABLE_DIR / "waris_wartime_aml_typology_layer_map.csv"
    )
    WARTIME_AML_TYPOLOGY_SUMMARY_TABLE = (
        TABLE_DIR / "waris_wartime_aml_typology_summary.csv"
    )
    WARTIME_AML_TYPOLOGY_CURRENT_USE = (
        "literature_support_and_typology_reference_only"
    )
    WARTIME_AML_TYPOLOGY_PROHIBITED_USE = "direct_scoring_without_change_control"
    WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE = "none"

    FIU_OFFICIAL_SOURCE_REGISTER_TABLE = (
        TABLE_DIR / "waris_fiu_official_source_register.csv"
    )
    FIU_REPORTING_STATISTICS_CONTEXT_TABLE = (
        TABLE_DIR / "waris_fiu_reporting_statistics_context.csv"
    )
    FIU_CASE_REFERRAL_CONTEXT_TABLE = (
        TABLE_DIR / "waris_fiu_case_referral_context.csv"
    )
    FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE = (
        TABLE_DIR / "waris_fiu_typology_support_register.csv"
    )
    FIU_CONTEXT_SUMMARY_TABLE = TABLE_DIR / "waris_fiu_context_summary.csv"
    FIU_CONTEXT_CURRENT_USE = "official_fiu_context_and_typology_support_only"
    FIU_CONTEXT_PROHIBITED_USE = "direct_scoring_without_change_control"
    FIU_CONTEXT_PRODUCTION_SCORE_CHANGE = "none"


try:
    from .config import (
        ANALYST_REVIEW_SUMMARY_TABLE,
        ANALYST_REVIEW_CURRENT_USE,
        ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
        FALSE_POSITIVE_SUMMARY_TABLE,
        FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
        SOURCE_FRESHNESS_SUMMARY_TABLE,
        SOURCE_FRESHNESS_CURRENT_USE,
        SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
        RUN_MANIFEST_SUMMARY_TABLE,
        RUN_MANIFEST_CURRENT_USE,
        RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
    )
except ImportError:
    ANALYST_REVIEW_SUMMARY_TABLE = TABLE_DIR / "analyst_review_summary.csv"
    ANALYST_REVIEW_CURRENT_USE = "analyst_review_workflow_only"
    ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE = "none"

    FALSE_POSITIVE_SUMMARY_TABLE = TABLE_DIR / "false_positive_summary.csv"
    FALSE_POSITIVE_CONTROLS_CURRENT_USE = "human_review_support_only"
    FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE = "none"

    SOURCE_FRESHNESS_SUMMARY_TABLE = TABLE_DIR / "source_freshness_summary.csv"
    SOURCE_FRESHNESS_CURRENT_USE = "source_freshness_monitoring_only"
    SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE = "none"

    RUN_MANIFEST_SUMMARY_TABLE = TABLE_DIR / "run_manifest_summary.csv"
    RUN_MANIFEST_CURRENT_USE = "run_manifest_documentation"
    RUN_MANIFEST_PRODUCTION_SCORE_CHANGE = "none"


UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE = (
    TABLE_DIR / "ukrstat_oblast_baseline_candidates.csv"
)
OFFICIAL_BASELINE_READINESS_DECISION_TABLE = (
    TABLE_DIR / "official_baseline_readiness_decision.csv"
)
OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE = (
    TABLE_DIR / "official_baseline_unit_evidence_summary.csv"
)

SCORED_TABLE = TABLE_DIR / "waris_scored_oblast_sector.csv"
SYNTHETIC_INPUTS_RAW = RAW_DIR / "synthetic_oblast_sector_inputs.csv"

MERGE_PLAN_TABLE = TABLE_DIR / "official_baseline_merge_plan.csv"
BENCHMARK_COMPARISON_TABLE = (
    TABLE_DIR / "official_baseline_benchmark_comparison.csv"
)
RESCALE_SCENARIO_TABLE = (
    TABLE_DIR / "official_baseline_rescale_scenario.csv"
)
REPLACE_OBLAST_BASELINE_SCENARIO_TABLE = (
    TABLE_DIR / "official_baseline_replace_oblast_baseline_scenario.csv"
)
MERGE_READINESS_SUMMARY_TABLE = (
    TABLE_DIR / "official_baseline_merge_readiness_summary.csv"
)
OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE = (
    TABLE_DIR / "official_baseline_prozorro_context_bridge.csv"
)
OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_TABLE = (
    TABLE_DIR / "official_baseline_wartime_typology_context_bridge.csv"
)
OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_TABLE = (
    TABLE_DIR / "official_baseline_fiu_context_bridge.csv"
)
OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_TABLE = (
    TABLE_DIR / "official_baseline_operational_controls_context_bridge.csv"
)

DECISION_GO_BENCHMARK = "GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION"
PROHIBITED_SCORING_USE = "risk_layer_calculation_or_composite_scoring"


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


def _safe_read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV if available, otherwise return an empty dataframe."""
    try:
        if not path.exists():
            return pd.DataFrame()

        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _normalize_oblast(value: object) -> str:
    """Map Ukrstat oblast labels to WARIS canonical oblast labels."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""

    text = str(value).strip()

    if not text:
        return ""

    return UKRSTAT_TO_WARIS_OBLAST.get(text, text)


def _load_readiness_decision() -> pd.DataFrame:
    """Load official baseline readiness decision artifact."""
    return _safe_read_csv(OFFICIAL_BASELINE_READINESS_DECISION_TABLE)


def _readiness_status() -> dict[str, str]:
    """Return compact readiness decision metadata."""
    readiness = _load_readiness_decision()

    if readiness.empty:
        return {
            "decision": "missing",
            "approved_current_use": "missing",
            "prohibited_current_use": "missing",
            "rationale": "official_baseline_readiness_decision.csv was not found.",
            "next_decision_point": (
                "Run python -m src.official_baseline_validation before merge planning."
            ),
        }

    row = readiness.iloc[0]

    return {
        "decision": str(row.get("decision", "")),
        "approved_current_use": str(row.get("approved_current_use", "")),
        "prohibited_current_use": str(row.get("prohibited_current_use", "")),
        "rationale": str(row.get("rationale", "")),
        "next_decision_point": str(row.get("next_decision_point", "")),
    }


def _load_unit_evidence() -> dict[str, str]:
    """Load official baseline unit-evidence summary."""
    unit = _safe_read_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE)

    if unit.empty:
        return {
            "unit_interpretation": "missing",
            "validation_status": "missing",
            "source_file": "missing",
            "period_min": "",
            "period_max": "",
        }

    row = unit.iloc[0]

    return {
        "unit_interpretation": str(row.get("unit_interpretation", "")),
        "validation_status": str(row.get("validation_status", "")),
        "source_file": str(row.get("source_file", "")),
        "period_min": str(row.get("period_min", "")),
        "period_max": str(row.get("period_max", "")),
    }


def _load_official_baseline_candidates() -> pd.DataFrame:
    """Load and normalize official Ukrstat GRP baseline candidates."""
    candidates = _safe_read_csv(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE)
    candidates = official_baseline_observations(candidates)

    if candidates.empty:
        return pd.DataFrame()

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
        "validation_status",
        "current_use_in_scoring",
    ]:
        if col not in out.columns:
            out[col] = ""

    out["waris_oblast"] = out["oblast"].apply(_normalize_oblast)
    out["official_grp_million_uah"] = pd.to_numeric(
        out["official_regional_baseline_proxy"],
        errors="coerce",
    )

    out["official_grp_share_of_waris_total"] = (
        out["official_grp_million_uah"]
        / out["official_grp_million_uah"].sum()
    )

    out["official_grp_index_0_100"] = min_max_scale(
        out["official_grp_million_uah"]
    )

    return out


def _load_model_baseline() -> pd.DataFrame:
    """Load WARIS scored or raw synthetic baseline table."""
    raw = _safe_read_csv(SYNTHETIC_INPUTS_RAW)
    if not raw.empty:
        return raw
    # Standalone review may use scored inputs when no synthetic snapshot exists.
    scored = _safe_read_csv(SCORED_TABLE)
    if not scored.empty:
        return scored

    return pd.DataFrame()


def _model_oblast_baseline(model_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize current WARIS synthetic/prototype baseline by oblast."""
    if model_df.empty:
        return pd.DataFrame()

    required = {"oblast", "prewar_revenue_index_2021"}

    if not required.issubset(set(model_df.columns)):
        return pd.DataFrame()

    working = model_df.copy()

    working["prewar_revenue_index_2021"] = pd.to_numeric(
        working["prewar_revenue_index_2021"],
        errors="coerce",
    )

    if "current_revenue_index" in working.columns:
        working["current_revenue_index"] = pd.to_numeric(
            working["current_revenue_index"],
            errors="coerce",
        )
    else:
        working["current_revenue_index"] = pd.NA

    if "waris_aml_review_score" in working.columns:
        working["waris_aml_review_score"] = pd.to_numeric(
            working["waris_aml_review_score"],
            errors="coerce",
        )
    else:
        working["waris_aml_review_score"] = pd.NA

    summary = (
        working.groupby("oblast", as_index=False)
        .agg(
            synthetic_prewar_revenue_index_mean=(
                "prewar_revenue_index_2021",
                "mean",
            ),
            synthetic_prewar_revenue_index_sum=(
                "prewar_revenue_index_2021",
                "sum",
            ),
            current_revenue_index_mean=("current_revenue_index", "mean"),
            current_waris_score_mean=("waris_aml_review_score", "mean"),
            sector_count=("sector", "nunique") if "sector" in working.columns else ("oblast", "size"),
        )
    )

    summary["synthetic_prewar_share_of_total"] = (
        summary["synthetic_prewar_revenue_index_sum"]
        / summary["synthetic_prewar_revenue_index_sum"].sum()
    )

    summary["synthetic_prewar_index_0_100"] = min_max_scale(
        summary["synthetic_prewar_revenue_index_sum"]
    )

    return summary


def build_benchmark_comparison(
    official: pd.DataFrame,
    model_baseline: pd.DataFrame,
) -> pd.DataFrame:
    """Compare official GRP baseline to WARIS current synthetic baseline."""
    if official.empty or model_baseline.empty:
        out = pd.DataFrame(
            [
                {
                    "waris_oblast": "",
                    "benchmark_status": "missing_required_inputs",
                    "notes": (
                        "Official candidates or WARIS model baseline table was missing."
                    ),
                    "current_use_in_scoring": "not_yet_used",
                }
            ]
        )
        # A missing-input notice is not an observation or reviewed region.
        out = out.iloc[:0].copy()
        out.to_csv(BENCHMARK_COMPARISON_TABLE, index=False)
        return out

    merged = official.merge(
        model_baseline,
        left_on="waris_oblast",
        right_on="oblast",
        how="left",
        suffixes=("_official", "_model"),
    )

    merged["official_to_synthetic_share_ratio"] = (
        merged["official_grp_share_of_waris_total"]
        / merged["synthetic_prewar_share_of_total"].replace(0, pd.NA)
    )

    merged["official_vs_synthetic_index_gap"] = (
        merged["official_grp_index_0_100"]
        - merged["synthetic_prewar_index_0_100"]
    )

    merged["benchmark_status"] = "controlled_benchmark_only"
    merged["current_use_in_scoring"] = "not_yet_used"
    merged["approved_current_use"] = "controlled_benchmark_integration_only"
    merged["prohibited_current_use"] = PROHIBITED_SCORING_USE
    merged["notes"] = (
        "Compares official GRP scale with current synthetic prewar revenue "
        "baseline. Does not alter WARIS scoring."
    )

    cols = [
        "waris_oblast",
        "region_code",
        "indicator_code",
        "indicator_name",
        "nace_code",
        "freq_code",
        "latest_period",
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
        "benchmark_status",
        "current_use_in_scoring",
        "approved_current_use",
        "prohibited_current_use",
        "notes",
    ]

    cols = [col for col in cols if col in merged.columns]

    out = merged[cols].sort_values(
        "official_grp_million_uah",
        ascending=False,
    )

    out.to_csv(BENCHMARK_COMPARISON_TABLE, index=False)

    return out


def build_rescale_scenario(model_df: pd.DataFrame, official: pd.DataFrame) -> pd.DataFrame:
    """Strict 25-region/six-sector index illustration; never production allocation."""
    columns=['oblast','sector','official_grp_million_uah','official_oblast_scale_index','sector_share_within_oblast','prewar_revenue_index_2021','scenario_prewar_revenue_index_2021','current_revenue_index','scenario_current_revenue_index','original_revenue_change_pct','scenario_name','scenario_status','current_use_in_scoring','approved_current_use','prohibited_current_use','notes']
    if model_df.empty or official.empty:
        out=pd.DataFrame(columns=columns)
    else:
        records=strict_rescale(official.to_dict('records'),model_df.to_dict('records'))
        out=pd.DataFrame(records)
        out['scenario_name']='rescale_revenue_baseline'
        out['scenario_status']='non_production_benchmark_scenario'
        out['current_use_in_scoring']='not_yet_used'
        out['approved_current_use']='controlled_benchmark_integration_only'
        out['prohibited_current_use']=PROHIBITED_SCORING_USE
        out['notes']='Synthetic-index mathematical illustration only; not observed sector revenue or allocated official sector GRP. No empirical allocation/scoring approval.'
        out=out[columns].sort_values(['official_grp_million_uah','oblast','sector'],ascending=[False,True,True])
    out.to_csv(RESCALE_SCENARIO_TABLE,index=False)
    return out


def build_replace_oblast_baseline_scenario(
    model_df: pd.DataFrame,
    official: pd.DataFrame,
) -> pd.DataFrame:
    """Create a non-production scenario replacing oblast baseline with official GRP.

    This creates an oblast-level replacement scenario only. Sector allocation
    remains unsupported unless official sector-by-oblast data is later validated.
    """
    if model_df.empty or official.empty:
        out = pd.DataFrame(
            [
                {
                    "waris_oblast": "",
                    "scenario_name": "replace_oblast_baseline",
                    "scenario_status": "missing_required_inputs",
                    "current_use_in_scoring": "not_yet_used",
                    "notes": "Required input tables were missing.",
                }
            ]
        )
        # A missing-input notice is not an observation or reviewed region.
        out = out.iloc[:0].copy()
        out.to_csv(REPLACE_OBLAST_BASELINE_SCENARIO_TABLE, index=False)
        return out

    model_oblast = _model_oblast_baseline(model_df)

    scenario = official.merge(
        model_oblast,
        left_on="waris_oblast",
        right_on="oblast",
        how="left",
    )

    scenario["scenario_oblast_baseline_value"] = scenario["official_grp_million_uah"]
    scenario["scenario_oblast_baseline_unit"] = "million UAH"
    scenario["scenario_name"] = "replace_oblast_baseline"
    scenario["scenario_status"] = (
        "non_production_oblast_level_replacement_scenario"
    )
    scenario["sector_allocation_status"] = (
        "not_supported_without_validated_sector_oblast_official_data"
    )
    scenario["current_use_in_scoring"] = "not_yet_used"
    scenario["approved_current_use"] = "controlled_benchmark_integration_only"
    scenario["prohibited_current_use"] = PROHIBITED_SCORING_USE
    scenario["notes"] = (
        "Scenario only. Official GRP can replace the oblast-level baseline in "
        "a benchmark table, but cannot allocate values across WARIS sectors "
        "without additional validated official sector data."
    )

    cols = [
        "waris_oblast",
        "region_code",
        "latest_period",
        "scenario_oblast_baseline_value",
        "scenario_oblast_baseline_unit",
        "official_grp_share_of_waris_total",
        "official_grp_index_0_100",
        "synthetic_prewar_revenue_index_sum",
        "synthetic_prewar_share_of_total",
        "current_waris_score_mean",
        "scenario_name",
        "scenario_status",
        "sector_allocation_status",
        "current_use_in_scoring",
        "approved_current_use",
        "prohibited_current_use",
        "notes",
    ]

    cols = [col for col in cols if col in scenario.columns]

    out = scenario[cols].sort_values(
        "scenario_oblast_baseline_value",
        ascending=False,
    )

    out.to_csv(REPLACE_OBLAST_BASELINE_SCENARIO_TABLE, index=False)

    return out


def _load_prozorro_oblast_features() -> pd.DataFrame:
    """Load expanded Prozorro oblast-level review-only feature artifacts."""
    features = _safe_read_csv(PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE)

    if features.empty:
        return pd.DataFrame()

    out = features.copy()

    if "oblast" not in out.columns:
        return pd.DataFrame()

    for col in [
        "tender_count",
        "total_expected_value",
        "mean_expected_value",
        "single_bid_or_supplier_proxy_rate",
        "reconstruction_emergency_tender_count",
        "reconstruction_emergency_share",
        "top_buyer_tender_share",
        "procurement_review_priority_candidate",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "current_use" not in out.columns:
        out["current_use"] = PROZORRO_PROCUREMENT_CURRENT_USE

    if "prohibited_use" not in out.columns:
        out["prohibited_use"] = PROZORRO_PROCUREMENT_PROHIBITED_USE

    if "production_score_change" not in out.columns:
        out["production_score_change"] = PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE

    return out


def _load_prozorro_scoring_candidate_summary() -> pd.DataFrame:
    """Load expanded Prozorro scoring-candidate controls by oblast."""
    candidates = _safe_read_csv(PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE)

    if candidates.empty or "oblast" not in candidates.columns:
        return pd.DataFrame()

    working = candidates.copy()

    if "procurement_review_priority_candidate" in working.columns:
        working["procurement_review_priority_candidate"] = pd.to_numeric(
            working["procurement_review_priority_candidate"],
            errors="coerce",
        )

    agg_dict = {}

    if "sector" in working.columns:
        agg_dict["candidate_sector_count"] = ("sector", "nunique")

    if "procurement_review_priority_candidate" in working.columns:
        agg_dict["max_procurement_review_priority_candidate"] = (
            "procurement_review_priority_candidate",
            "max",
        )
        agg_dict["mean_procurement_review_priority_candidate"] = (
            "procurement_review_priority_candidate",
            "mean",
        )

    if not agg_dict:
        return pd.DataFrame()

    summary = working.groupby("oblast", as_index=False).agg(**agg_dict)

    if "current_use" in working.columns:
        current_use = (
            working.groupby("oblast")["current_use"]
            .apply(lambda s: "; ".join(sorted(set(s.dropna().astype(str)))))
            .reset_index(name="prozorro_candidate_current_use_values")
        )
        summary = summary.merge(current_use, on="oblast", how="left")

    if "prohibited_use" in working.columns:
        prohibited_use = (
            working.groupby("oblast")["prohibited_use"]
            .apply(lambda s: "; ".join(sorted(set(s.dropna().astype(str)))))
            .reset_index(name="prozorro_candidate_prohibited_use_values")
        )
        summary = summary.merge(prohibited_use, on="oblast", how="left")

    if "production_score_change" in working.columns:
        score_change = (
            working.groupby("oblast")["production_score_change"]
            .apply(lambda s: "; ".join(sorted(set(s.dropna().astype(str)))))
            .reset_index(name="prozorro_candidate_score_change_values")
        )
        summary = summary.merge(score_change, on="oblast", how="left")

    return summary


def _summary_value_for_area(
    table: pd.DataFrame,
    summary_area: str,
    value_column: str = "value",
    default: str = "not_available",
) -> str:
    """Return a value from a standard summary table."""
    if table.empty or "summary_area" not in table.columns:
        return default

    rows = table[
        table["summary_area"]
        .fillna("")
        .astype(str)
        .eq(summary_area)
    ]

    if rows.empty:
        return default

    value = rows.iloc[0].get(value_column, default)

    if pd.isna(value):
        return default

    return str(value)


def _load_operational_control_context_rows(
    gap_context: dict[str, object],
) -> list[dict[str, object]]:
    """Build documentation-only operational-control bridge rows."""
    analyst_summary = _safe_read_csv(ANALYST_REVIEW_SUMMARY_TABLE)
    false_positive_summary = _safe_read_csv(FALSE_POSITIVE_SUMMARY_TABLE)
    source_freshness_summary = _safe_read_csv(SOURCE_FRESHNESS_SUMMARY_TABLE)
    run_manifest_summary = _safe_read_csv(RUN_MANIFEST_SUMMARY_TABLE)

    run_id = "not_available"
    model_version = "not_available"
    manifest_score_change = "not_available"

    if not run_manifest_summary.empty:
        first = run_manifest_summary.iloc[0]
        run_id = str(first.get("run_id", "not_available"))
        model_version = str(first.get("model_version", "not_available"))
        manifest_score_change = str(
            first.get("production_score_change", "not_available")
        )

    return [
        {
            "operational_artifact_family": "analyst_review_workflow",
            "artifact_status": "available" if not analyst_summary.empty else "not_available",
            "artifact_summary": (
                f"queue records={_summary_value_for_area(analyst_summary, 'Review queue records')}; "
                f"questions={_summary_value_for_area(analyst_summary, 'Review questions')}"
            ),
            "current_use": ANALYST_REVIEW_CURRENT_USE,
            "production_score_change": ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
        },
        {
            "operational_artifact_family": "false_positive_controls",
            "artifact_status": (
                "available" if not false_positive_summary.empty else "not_available"
            ),
            "artifact_summary": (
                f"control counts={_summary_value_for_area(false_positive_summary, 'Control status counts')}; "
                f"checklist rows={_summary_value_for_area(false_positive_summary, 'False-positive review checklist')}"
            ),
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
            "production_score_change": FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
        },
        {
            "operational_artifact_family": "source_freshness",
            "artifact_status": (
                "available" if not source_freshness_summary.empty else "not_available"
            ),
            "artifact_summary": (
                f"posture={_summary_value_for_area(source_freshness_summary, 'Overall freshness posture', value_column='status')}; "
                f"freshness counts={_summary_value_for_area(source_freshness_summary, 'Freshness status counts')}; "
                f"priority counts={_summary_value_for_area(source_freshness_summary, 'Refresh priority counts')}"
            ),
            "current_use": SOURCE_FRESHNESS_CURRENT_USE,
            "production_score_change": SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
        },
        {
            "operational_artifact_family": "run_manifest",
            "artifact_status": "available" if not run_manifest_summary.empty else "not_available",
            "artifact_summary": (
                f"run_id={run_id}; model_version={model_version}; "
                f"manifest_score_change={manifest_score_change}"
            ),
            "current_use": RUN_MANIFEST_CURRENT_USE,
            "production_score_change": RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
        },
    ]


def build_official_baseline_operational_controls_context_bridge(
    benchmark: pd.DataFrame,
) -> pd.DataFrame:
    """Create an official-baseline-to-operational-controls context bridge.

    This is a documentation-only bridge. It lets analysts see whether the official
    baseline benchmark artifacts are accompanied by analyst-review,
    false-positive, source-freshness, and run-manifest controls. It does not
    alter scoring or official baseline scenarios.
    """
    gap_context = _benchmark_gap_context(benchmark)
    rows = []

    for row in _load_operational_control_context_rows(gap_context):
        rows.append(
            {
                "bridge_name": "official_baseline_to_operational_controls_context",
                "bridge_status": "documentation_only_context_bridge",
                "benchmark_rows": gap_context["benchmark_rows"],
                "largest_gap_oblast": gap_context["largest_gap_oblast"],
                "largest_gap_value": gap_context["largest_gap_value"],
                "average_abs_gap": gap_context["average_abs_gap"],
                "approved_current_use": "context_review_only",
                "prohibited_use": PROHIBITED_SCORING_USE,
                "used_in_scoring": False,
                "used_in_monte_carlo": False,
                "notes": (
                    "Operational-control bridge only. Analyst-review, false-positive, "
                    "source-freshness, and run-manifest artifacts remain documentation "
                    "and human-review support. They do not alter official baseline "
                    "scenarios or WARIS scoring."
                ),
                **row,
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_TABLE, index=False)
    return out


def build_official_baseline_prozorro_context_bridge(
    benchmark: pd.DataFrame,
) -> pd.DataFrame:
    """Create a controlled official-baseline-to-Prozorro context bridge.

    This is a non-production review artifact. It lets analysts compare official
    GRP benchmark scale against expanded Prozorro procurement candidate features
    at the oblast level without changing risk layers, composite scores, risk
    bands, or Monte Carlo simulations.
    """
    prozorro_oblast = _load_prozorro_oblast_features()
    prozorro_candidates = _load_prozorro_scoring_candidate_summary()

    if benchmark.empty or prozorro_oblast.empty:
        out = pd.DataFrame(
            [
                {
                    "waris_oblast": "",
                    "bridge_status": "missing_required_inputs",
                    "current_use": "review_artifact_only",
                    "prohibited_use": PROZORRO_PROCUREMENT_PROHIBITED_USE,
                    "production_score_change": PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE,
                    "notes": (
                        "Official baseline benchmark comparison or expanded Prozorro "
                        "oblast feature table was missing."
                    ),
                }
            ]
        )
        # A missing-input notice is not an observation or reviewed region.
        out = out.iloc[:0].copy()
        out.to_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE, index=False)
        return out

    benchmark_cols = [
        col
        for col in [
            "waris_oblast",
            "official_grp_million_uah",
            "official_grp_share_of_waris_total",
            "synthetic_prewar_share_of_total",
            "official_to_synthetic_share_ratio",
            "official_vs_synthetic_index_gap",
            "benchmark_status",
            "current_use_in_scoring",
            "approved_current_use",
            "prohibited_current_use",
        ]
        if col in benchmark.columns
    ]

    bridge = benchmark[benchmark_cols].merge(
        prozorro_oblast,
        left_on="waris_oblast",
        right_on="oblast",
        how="left",
        suffixes=("_official", "_prozorro"),
    )

    if not prozorro_candidates.empty:
        bridge = bridge.merge(
            prozorro_candidates,
            left_on="waris_oblast",
            right_on="oblast",
            how="left",
            suffixes=("", "_candidate_summary"),
        )

    bridge["bridge_name"] = "official_baseline_to_prozorro_procurement_context"
    bridge["bridge_status"] = "review_only_context_bridge"
    bridge["current_use"] = PROZORRO_PROCUREMENT_CURRENT_USE
    bridge["approved_current_use"] = "context_review_only"
    bridge["prohibited_use"] = PROZORRO_PROCUREMENT_PROHIBITED_USE
    bridge["production_score_change"] = PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
    bridge["used_in_scoring"] = False
    bridge["used_in_monte_carlo"] = False
    bridge["notes"] = (
        "Compares official baseline benchmark context with expanded Prozorro "
        "procurement candidate features. Does not alter WARIS scoring."
    )

    sort_col = (
        "procurement_review_priority_candidate"
        if "procurement_review_priority_candidate" in bridge.columns
        else "official_grp_million_uah"
    )

    if sort_col in bridge.columns:
        bridge[sort_col] = pd.to_numeric(bridge[sort_col], errors="coerce")
        bridge = bridge.sort_values(sort_col, ascending=False)

    drop_cols = [
        col
        for col in ["oblast", "oblast_candidate_summary"]
        if col in bridge.columns
    ]
    if drop_cols:
        bridge = bridge.drop(columns=drop_cols)

    bridge.to_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE, index=False)

    return bridge


def _benchmark_gap_context(benchmark: pd.DataFrame) -> dict[str, object]:
    """Return compact official-vs-synthetic benchmark context."""
    if benchmark.empty or "official_vs_synthetic_index_gap" not in benchmark.columns:
        return {
            "benchmark_rows": 0,
            "largest_gap_oblast": "not_available",
            "largest_gap_value": "not_available",
            "average_abs_gap": "not_available",
        }

    working = benchmark.copy()
    working["absolute_index_gap"] = pd.to_numeric(
        working["official_vs_synthetic_index_gap"],
        errors="coerce",
    ).abs()
    average_gap = working["absolute_index_gap"].mean()
    working = working.sort_values("absolute_index_gap", ascending=False)

    if working.empty:
        return {
            "benchmark_rows": 0,
            "largest_gap_oblast": "not_available",
            "largest_gap_value": "not_available",
            "average_abs_gap": "not_available",
        }

    return {
        "benchmark_rows": len(working),
        "largest_gap_oblast": str(working.iloc[0].get("waris_oblast", "not_available")),
        "largest_gap_value": str(
            working.iloc[0].get("official_vs_synthetic_index_gap", "not_available")
        ),
        "average_abs_gap": (
            "not_available" if pd.isna(average_gap) else f"{average_gap:.2f}"
        ),
    }


def _add_context_bridge_controls(
    df: pd.DataFrame,
    current_use: str,
    prohibited_use: str,
    production_score_change: str,
) -> pd.DataFrame:
    """Apply common no-scoring context-bridge controls."""
    out = df.copy()
    out["approved_current_use"] = "context_review_only"
    out["current_use"] = current_use
    out["prohibited_use"] = prohibited_use
    out["production_score_change"] = production_score_change
    out["used_in_scoring"] = False
    out["used_in_monte_carlo"] = False
    return out


def build_official_baseline_wartime_typology_context_bridge(
    benchmark: pd.DataFrame,
) -> pd.DataFrame:
    """Create an official-baseline-to-wartime-AML-typology context bridge."""
    typology = _safe_read_csv(WARTIME_AML_TYPOLOGY_REGISTER_TABLE)
    gap_context = _benchmark_gap_context(benchmark)

    if typology.empty:
        out = pd.DataFrame(
            [
                {
                    "bridge_name": "official_baseline_to_wartime_aml_typology_context",
                    "bridge_status": "missing_typology_artifacts",
                    "typology_id": "",
                    "typology_name": "",
                    "typology_family": "",
                    "waris_layer_candidates": "",
                    "benchmark_rows": gap_context["benchmark_rows"],
                    "largest_gap_oblast": gap_context["largest_gap_oblast"],
                    "largest_gap_value": gap_context["largest_gap_value"],
                    "average_abs_gap": gap_context["average_abs_gap"],
                    "notes": (
                        "Wartime AML/CFT typology register was not available. Run "
                        "python -m src.wartime_aml_typology_register."
                    ),
                }
            ]
        )
    else:
        working = typology.copy()
        for col in [
            "typology_id",
            "typology_name",
            "typology_family",
            "waris_layer_candidates",
        ]:
            if col not in working.columns:
                working[col] = ""

        rows = []
        for _, row in working.iterrows():
            rows.append(
                {
                    "bridge_name": "official_baseline_to_wartime_aml_typology_context",
                    "bridge_status": "review_only_context_bridge",
                    "typology_id": row.get("typology_id", ""),
                    "typology_name": row.get("typology_name", ""),
                    "typology_family": row.get("typology_family", ""),
                    "waris_layer_candidates": row.get("waris_layer_candidates", ""),
                    "benchmark_rows": gap_context["benchmark_rows"],
                    "largest_gap_oblast": gap_context["largest_gap_oblast"],
                    "largest_gap_value": gap_context["largest_gap_value"],
                    "average_abs_gap": gap_context["average_abs_gap"],
                    "notes": (
                        "Context bridge only. Typology themes remain literature-supported "
                        "references and do not alter official baseline scenarios or scoring."
                    ),
                }
            )
        out = pd.DataFrame(rows)

    out = _add_context_bridge_controls(
        out,
        current_use=WARTIME_AML_TYPOLOGY_CURRENT_USE,
        prohibited_use=WARTIME_AML_TYPOLOGY_PROHIBITED_USE,
        production_score_change=WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE,
    )
    out.to_csv(OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_TABLE, index=False)
    return out


def build_official_baseline_fiu_context_bridge(
    benchmark: pd.DataFrame,
) -> pd.DataFrame:
    """Create an official-baseline-to-FIU/SFMS context bridge."""
    fiu_typology = _safe_read_csv(FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE)
    gap_context = _benchmark_gap_context(benchmark)

    if fiu_typology.empty:
        out = pd.DataFrame(
            [
                {
                    "bridge_name": "official_baseline_to_fiu_context",
                    "bridge_status": "missing_fiu_context_artifacts",
                    "typology_support_id": "",
                    "typology_name": "",
                    "typology_family": "",
                    "waris_layer_candidates": "",
                    "benchmark_rows": gap_context["benchmark_rows"],
                    "largest_gap_oblast": gap_context["largest_gap_oblast"],
                    "largest_gap_value": gap_context["largest_gap_value"],
                    "average_abs_gap": gap_context["average_abs_gap"],
                    "notes": (
                        "Official FIU/SFMS typology-support register was not available. "
                        "Run python -m src.fiu_official_context."
                    ),
                }
            ]
        )
    else:
        working = fiu_typology.copy()
        for col in [
            "typology_support_id",
            "typology_name",
            "typology_family",
            "waris_layer_candidates",
        ]:
            if col not in working.columns:
                working[col] = ""

        rows = []
        for _, row in working.iterrows():
            rows.append(
                {
                    "bridge_name": "official_baseline_to_fiu_context",
                    "bridge_status": "review_only_context_bridge",
                    "typology_support_id": row.get("typology_support_id", ""),
                    "typology_name": row.get("typology_name", ""),
                    "typology_family": row.get("typology_family", ""),
                    "waris_layer_candidates": row.get("waris_layer_candidates", ""),
                    "benchmark_rows": gap_context["benchmark_rows"],
                    "largest_gap_oblast": gap_context["largest_gap_oblast"],
                    "largest_gap_value": gap_context["largest_gap_value"],
                    "average_abs_gap": gap_context["average_abs_gap"],
                    "notes": (
                        "Context bridge only. Official FIU/SFMS context remains national "
                        "source support and does not alter official baseline scenarios or scoring."
                    ),
                }
            )
        out = pd.DataFrame(rows)

    out = _add_context_bridge_controls(
        out,
        current_use=FIU_CONTEXT_CURRENT_USE,
        prohibited_use=FIU_CONTEXT_PROHIBITED_USE,
        production_score_change=FIU_CONTEXT_PRODUCTION_SCORE_CHANGE,
    )
    out.to_csv(OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_TABLE, index=False)
    return out


def build_merge_plan(
    readiness: dict[str, str],
    unit_evidence: dict[str, str],
) -> pd.DataFrame:
    """Build a scenario-by-scenario merge plan."""
    decision = readiness["decision"]
    benchmark_ready = decision in {
        DECISION_GO_BENCHMARK,
        "GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION",
    }

    rows = [
        {
            "scenario_name": "benchmark_only",
            "scenario_description": (
                "Compare official GRP million-UAH oblast baseline against current "
                "WARIS synthetic prewar revenue baseline."
            ),
            "approved_now": benchmark_ready,
            "approved_current_use": (
                "controlled_benchmark_integration_only"
                if benchmark_ready
                else "validation_reporting_benchmarking_context_only"
            ),
            "prohibited_current_use": PROHIBITED_SCORING_USE,
            "production_score_change": "none",
            "required_before_scoring": (
                "Document transformation logic, SME review, and change control."
            ),
            "output_table": str(BENCHMARK_COMPARISON_TABLE),
            "notes": (
                "Recommended current scenario. Safe because it does not change "
                "risk layers, composite scores, risk bands, or Monte Carlo outputs."
            ),
        },
        {
            "scenario_name": "rescale_revenue_baseline",
            "scenario_description": (
                "Use official GRP distribution to rescale the WARIS synthetic "
                "prewar revenue baseline while preserving sector-level prototype "
                "variation."
            ),
            "approved_now": benchmark_ready,
            "approved_current_use": "scenario_analysis_only",
            "prohibited_current_use": PROHIBITED_SCORING_USE,
            "production_score_change": "none",
            "required_before_scoring": (
                "Validate transformation formula, sector allocation logic, sensitivity "
                "effects, and SME approval."
            ),
            "output_table": str(RESCALE_SCENARIO_TABLE),
            "notes": (
                "Useful for sensitivity review but should not replace production "
                "revenue fields yet."
            ),
        },
        {
            "scenario_name": "replace_oblast_baseline",
            "scenario_description": (
                "Replace oblast-level baseline with official GRP million UAH in a "
                "non-production benchmark table."
            ),
            "approved_now": benchmark_ready,
            "approved_current_use": "oblast_level_benchmark_scenario_only",
            "prohibited_current_use": PROHIBITED_SCORING_USE,
            "production_score_change": "none",
            "required_before_scoring": (
                "Find and validate official sector-by-oblast data or formally approve "
                "a sector allocation method."
            ),
            "output_table": str(REPLACE_OBLAST_BASELINE_SCENARIO_TABLE),
            "notes": (
                "Cannot allocate to WARIS sectors without additional official data "
                "or an approved allocation method."
            ),
        },
        {
            "scenario_name": "official_baseline_to_prozorro_context_bridge",
            "scenario_description": (
                "Compare official GRP benchmark context with expanded Prozorro "
                "procurement review-priority candidates at the oblast level."
            ),
            "approved_now": benchmark_ready,
            "approved_current_use": "context_review_only",
            "prohibited_current_use": PROZORRO_PROCUREMENT_PROHIBITED_USE,
            "production_score_change": PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE,
            "required_before_scoring": (
                "Validate procurement coverage, buyer/address/oblast mapping, sector "
                "mapping, bidder/supplier fields, false-positive controls, SME review, "
                "and formal scoring change control."
            ),
            "output_table": str(OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE),
            "notes": (
                "Review-only context bridge. Does not alter official baseline scenarios, "
                "risk layers, composite scores, risk bands, or Monte Carlo outputs."
            ),
        },
        {
            "scenario_name": "official_baseline_to_wartime_typology_context_bridge",
            "scenario_description": (
                "Compare official GRP benchmark context with literature-supported "
                "wartime AML/CFT typology themes."
            ),
            "approved_now": benchmark_ready,
            "approved_current_use": "context_review_only",
            "prohibited_current_use": WARTIME_AML_TYPOLOGY_PROHIBITED_USE,
            "production_score_change": WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE,
            "required_before_scoring": (
                "Validate measurable public-source indicators, SME review, "
                "false-positive controls, and formal scoring change control before "
                "any typology theme becomes a scoring feature."
            ),
            "output_table": str(OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_TABLE),
            "notes": (
                "Review-only context bridge. Does not alter official baseline scenarios, "
                "risk layers, composite scores, risk bands, or Monte Carlo outputs."
            ),
        },
        {
            "scenario_name": "official_baseline_to_fiu_context_bridge",
            "scenario_description": (
                "Compare official GRP benchmark context with official FIU/SFMS "
                "national typology-support themes."
            ),
            "approved_now": benchmark_ready,
            "approved_current_use": "context_review_only",
            "prohibited_current_use": FIU_CONTEXT_PROHIBITED_USE,
            "production_score_change": FIU_CONTEXT_PRODUCTION_SCORE_CHANGE,
            "required_before_scoring": (
                "Validate measurable oblast/sector indicators, SME review, "
                "false-positive controls, and formal scoring change control before "
                "any FIU/SFMS context theme becomes a scoring feature."
            ),
            "output_table": str(OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_TABLE),
            "notes": (
                "Review-only context bridge. Official FIU/SFMS context remains "
                "source support and does not alter official baseline scenarios, "
                "risk layers, composite scores, risk bands, or Monte Carlo outputs."
            ),
        },
        {
            "scenario_name": "official_baseline_to_operational_controls_context_bridge",
            "scenario_description": (
                "Compare official GRP benchmark context with analyst-review, "
                "false-positive, source-freshness, and run-manifest control availability."
            ),
            "approved_now": benchmark_ready,
            "approved_current_use": "context_review_only",
            "prohibited_current_use": PROHIBITED_SCORING_USE,
            "production_score_change": "none",
            "required_before_scoring": (
                "Operational-control artifacts are documentation and human-review "
                "support only. They do not authorize official baseline scoring use."
            ),
            "output_table": str(OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_TABLE),
            "notes": (
                "Documentation-only context bridge. Does not alter official baseline "
                "scenarios, risk layers, composite scores, risk bands, or Monte Carlo outputs."
            ),
        },
    ]

    out = pd.DataFrame(rows)

    out["readiness_decision"] = decision
    out["readiness_rationale"] = readiness["rationale"]
    out["unit_interpretation"] = unit_evidence["unit_interpretation"]
    out["unit_evidence_status"] = unit_evidence["validation_status"]

    out.to_csv(MERGE_PLAN_TABLE, index=False)

    return out


def build_merge_readiness_summary(
    readiness: dict[str, str],
    unit_evidence: dict[str, str],
    merge_plan: pd.DataFrame,
    benchmark: pd.DataFrame,
    prozorro_bridge: pd.DataFrame,
    typology_bridge: pd.DataFrame,
    fiu_bridge: pd.DataFrame,
    operational_bridge: pd.DataFrame,
) -> pd.DataFrame:
    """Build a compact merge-readiness summary."""
    benchmark_ready = readiness["decision"] == DECISION_GO_BENCHMARK

    top_benchmark_note = "not_available"

    if not benchmark.empty and "official_vs_synthetic_index_gap" in benchmark.columns:
        valid = benchmark.copy()
        valid["absolute_index_gap"] = pd.to_numeric(
            valid["official_vs_synthetic_index_gap"],
            errors="coerce",
        ).abs()
        valid = valid.sort_values("absolute_index_gap", ascending=False)

        if not valid.empty:
            row = valid.iloc[0]
            top_benchmark_note = (
                f"Largest official-vs-synthetic index gap: "
                f"{row.get('waris_oblast', '')} "
                f"({row.get('official_vs_synthetic_index_gap', '')})."
            )

    rows = [
        {
            "summary_area": "Readiness decision",
            "status": readiness["decision"],
            "summary": readiness["rationale"],
        },
        {
            "summary_area": "Approved current use",
            "status": readiness["approved_current_use"],
            "summary": (
                "Official GRP candidates may be used in controlled benchmark "
                "artifacts if the readiness decision is GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION."
            ),
        },
        {
            "summary_area": "Prohibited current use",
            "status": readiness["prohibited_current_use"],
            "summary": (
                "Official GRP candidates must not alter risk layers, composite scores, "
                "risk bands, or Monte Carlo score simulations."
            ),
        },
        {
            "summary_area": "Unit evidence",
            "status": unit_evidence["validation_status"],
            "summary": (
                f"Unit interpretation: {unit_evidence['unit_interpretation']}; "
                f"source: {unit_evidence['source_file']}."
            ),
        },
        {
            "summary_area": "Scenario count",
            "status": "created",
            "summary": f"{len(merge_plan)} merge scenarios documented.",
        },
        {
            "summary_area": "Benchmark comparison",
            "status": "created" if not benchmark.empty else "missing",
            "summary": top_benchmark_note,
        },
        {
            "summary_area": "Official baseline to Prozorro context bridge",
            "status": "created" if not prozorro_bridge.empty else "missing",
            "summary": (
                f"{len(prozorro_bridge)} bridge rows created. "
                "Expanded Prozorro procurement features remain review-only with "
                "production_score_change=none and are not scoring inputs."
            ),
        },
        {
            "summary_area": "Official baseline to wartime AML typology context bridge",
            "status": "created" if not typology_bridge.empty else "missing",
            "summary": (
                f"{len(typology_bridge)} bridge rows created. "
                "Wartime AML/CFT typology artifacts remain literature-support "
                "references with production_score_change=none and are not scoring inputs."
            ),
        },
        {
            "summary_area": "Official baseline to FIU/SFMS context bridge",
            "status": "created" if not fiu_bridge.empty else "missing",
            "summary": (
                f"{len(fiu_bridge)} bridge rows created. "
                "Official FIU/SFMS context artifacts remain source-support context "
                "with production_score_change=none and are not scoring inputs."
            ),
        },
        {
            "summary_area": "Official baseline to operational controls context bridge",
            "status": "created" if not operational_bridge.empty else "missing",
            "summary": (
                f"{len(operational_bridge)} bridge rows created. "
                "Analyst-review, false-positive, source-freshness, and run-manifest "
                "artifacts remain documentation and human-review support with "
                "production_score_change=none and are not scoring inputs."
            ),
        },
        {
            "summary_area": "Recommended next action",
            "status": "build_merge_review",
            "summary": (
                "Review benchmark-only, rescale, replace-oblast-baseline, "
                "official-baseline-to-Prozorro, official-baseline-to-wartime-typology, "
                "official-baseline-to-FIU, and official-baseline-to-operational-controls context bridge tables. Do not update "
                "production scoring until transformation logic, source coverage "
                "validation, SME review, and change control are documented."
            ),
        },
    ]

    out = pd.DataFrame(rows)
    out.to_csv(MERGE_READINESS_SUMMARY_TABLE, index=False)

    return out


def build_official_baseline_merge_plan_artifacts() -> dict[str, pd.DataFrame]:
    """Build all official baseline merge-planning artifacts."""
    ensure_dirs([TABLE_DIR])

    readiness = _readiness_status()
    unit_evidence = _load_unit_evidence()
    official = _load_official_baseline_candidates()
    model_df = _load_model_baseline()
    model_baseline = _model_oblast_baseline(model_df)

    merge_plan = build_merge_plan(readiness, unit_evidence)
    benchmark = build_benchmark_comparison(official, model_baseline)
    rescale = build_rescale_scenario(model_df, official)
    replace = build_replace_oblast_baseline_scenario(model_df, official)
    prozorro_bridge = build_official_baseline_prozorro_context_bridge(benchmark)
    typology_bridge = build_official_baseline_wartime_typology_context_bridge(benchmark)
    fiu_bridge = build_official_baseline_fiu_context_bridge(benchmark)
    operational_bridge = build_official_baseline_operational_controls_context_bridge(
        benchmark
    )
    summary = build_merge_readiness_summary(
        readiness=readiness,
        unit_evidence=unit_evidence,
        merge_plan=merge_plan,
        benchmark=benchmark,
        prozorro_bridge=prozorro_bridge,
        typology_bridge=typology_bridge,
        fiu_bridge=fiu_bridge,
        operational_bridge=operational_bridge,
    )

    return {
        "merge_plan": merge_plan,
        "benchmark_comparison": benchmark,
        "rescale_scenario": rescale,
        "replace_oblast_baseline_scenario": replace,
        "prozorro_context_bridge": prozorro_bridge,
        "wartime_typology_context_bridge": typology_bridge,
        "fiu_context_bridge": fiu_bridge,
        "operational_controls_context_bridge": operational_bridge,
        "merge_readiness_summary": summary,
    }


def main() -> None:
    """CLI entry point."""
    artifacts = build_official_baseline_merge_plan_artifacts()

    readiness = _readiness_status()

    print("\nOfficial baseline merge-planning artifacts created.")
    print(f"- Readiness decision: {readiness['decision']}")
    print(f"- Approved current use: {readiness['approved_current_use']}")
    print(f"- Prohibited current use: {readiness['prohibited_current_use']}")

    print(f"- Merge plan rows: {len(artifacts['merge_plan'])}")
    print(f"- Benchmark comparison rows: {len(artifacts['benchmark_comparison'])}")
    print(f"- Rescale scenario rows: {len(artifacts['rescale_scenario'])}")
    print(
        "- Replace-oblast-baseline scenario rows: "
        f"{len(artifacts['replace_oblast_baseline_scenario'])}"
    )
    print(
        "- Official baseline to Prozorro context bridge rows: "
        f"{len(artifacts['prozorro_context_bridge'])}"
    )
    print(
        "- Official baseline to wartime AML typology context bridge rows: "
        f"{len(artifacts['wartime_typology_context_bridge'])}"
    )
    print(
        "- Official baseline to FIU/SFMS context bridge rows: "
        f"{len(artifacts['fiu_context_bridge'])}"
    )
    print(
        "- Official baseline to operational controls context bridge rows: "
        f"{len(artifacts['operational_controls_context_bridge'])}"
    )
    print(f"- Merge-readiness summary rows: {len(artifacts['merge_readiness_summary'])}")

    print(f"- Merge plan: {MERGE_PLAN_TABLE}")
    print(f"- Benchmark comparison: {BENCHMARK_COMPARISON_TABLE}")
    print(f"- Rescale scenario: {RESCALE_SCENARIO_TABLE}")
    print(f"- Replace-oblast-baseline scenario: {REPLACE_OBLAST_BASELINE_SCENARIO_TABLE}")
    print(
        "- Official baseline to Prozorro context bridge: "
        f"{OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE}"
    )
    print(
        "- Official baseline to wartime AML typology context bridge: "
        f"{OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_TABLE}"
    )
    print(
        "- Official baseline to FIU/SFMS context bridge: "
        f"{OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_TABLE}"
    )
    print(
        "- Official baseline to operational controls context bridge: "
        f"{OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_TABLE}"
    )
    print(f"- Merge-readiness summary: {MERGE_READINESS_SUMMARY_TABLE}")

    print(
        "\nImportant: These are controlled benchmark-integration artifacts only. "
        "They do not alter WARIS risk layers, composite scores, risk bands, or "
        "Monte Carlo score simulations. Operational-control bridges are documentation only."
    )


if __name__ == "__main__":
    main()
