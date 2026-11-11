from __future__ import annotations

from .utils import official_baseline_observations

import pandas as pd

from .config import BASE_WEIGHTS, RISK_BANDS
from .utils import (
    boolean_field_ok,
    clip_0_100,
    min_max_scale,
    normalize_waris_oblast_name,
    safe_read_csv,
    unique_values_from_tables,
)

try:
    from .config import UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE
except ImportError:
    UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE = None

try:
    from .config import (
        PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE,
        PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE,
        PROZORRO_PROCUREMENT_CURRENT_USE,
        PROZORRO_PROCUREMENT_PROHIBITED_USE,
        PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE,
    )
except ImportError:
    PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE = None
    PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE = None
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
    WARTIME_AML_TYPOLOGY_REGISTER_TABLE = None
    WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE = None
    WARTIME_AML_TYPOLOGY_SUMMARY_TABLE = None
    WARTIME_AML_TYPOLOGY_CURRENT_USE = (
        "literature_support_and_typology_reference_only"
    )
    WARTIME_AML_TYPOLOGY_PROHIBITED_USE = "direct_scoring_without_change_control"
    WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE = "none"
    FIU_OFFICIAL_SOURCE_REGISTER_TABLE = None
    FIU_REPORTING_STATISTICS_CONTEXT_TABLE = None
    FIU_CASE_REFERRAL_CONTEXT_TABLE = None
    FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE = None
    FIU_CONTEXT_SUMMARY_TABLE = None
    FIU_CONTEXT_CURRENT_USE = "official_fiu_context_and_typology_support_only"
    FIU_CONTEXT_PROHIBITED_USE = "direct_scoring_without_change_control"
    FIU_CONTEXT_PRODUCTION_SCORE_CHANGE = "none"

    ANALYST_REVIEW_SUMMARY_TABLE = None
    ANALYST_REVIEW_CURRENT_USE = "analyst_review_workflow_only"
    ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE = "none"

    FALSE_POSITIVE_SUMMARY_TABLE = None
    FALSE_POSITIVE_CONTROLS_CURRENT_USE = "human_review_support_only"
    FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE = "none"

    SOURCE_FRESHNESS_SUMMARY_TABLE = None
    SOURCE_FRESHNESS_CURRENT_USE = "source_freshness_monitoring_only"
    SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE = "none"

    RUN_MANIFEST_SUMMARY_TABLE = None
    RUN_MANIFEST_CURRENT_USE = "run_manifest_documentation"
    RUN_MANIFEST_PRODUCTION_SCORE_CHANGE = "none"


REQUIRED_INPUT_COLUMNS = [
    "prewar_revenue_index_2021",
    "current_revenue_index",
    "conflict_intensity_proxy",
    "trade_dislocation_proxy",
    "sanctions_counterparty_proxy",
    "procurement_awards_proxy",
    "ownership_opacity_proxy",
    "financial_supervision_proxy",
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


def assign_risk_band(score: float) -> str:
    """Assign a WARIS review-priority band from a numeric score."""
    for threshold, label in RISK_BANDS:
        if score >= threshold:
            return label
    return "Baseline / Monitor"


def _normalize_oblast_name(value: object) -> str:
    """Normalize official/source oblast labels to WARIS canonical labels."""
    normalized = normalize_waris_oblast_name(value)
    return UKRSTAT_TO_WARIS_OBLAST.get(normalized, normalized)


def _load_optional_csv(path) -> pd.DataFrame | None:
    """Load an optional CSV artifact with conservative error handling."""
    return safe_read_csv(path)


def _load_official_baseline_candidates() -> pd.DataFrame | None:
    """Load validation-only official Ukrstat baseline candidates if available.

    These candidates are attached to risk-model outputs only as governance and
    validation context. They do not change any risk layer or composite score.
    """
    candidates = _load_optional_csv(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE)

    if candidates is None or "oblast" not in candidates.columns:
        return None

    candidates = official_baseline_observations(candidates)
    if candidates.empty:
        return None

    out = candidates.copy()
    out["oblast"] = out["oblast"].apply(_normalize_oblast_name)

    keep_cols = [
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
            "approved_current_use",
            "prohibited_current_use",
            "production_score_change",
            "official_baseline_used_in_scoring",
            "official_baseline_used_in_monte_carlo",
            "source_separation_note",
            "control_note",
            "context_bridge_note",
        ]
        if col in out.columns
    ]

    out = out[keep_cols].drop_duplicates(subset=["oblast"], keep="first")

    rename_map = {
        "region_code": "official_baseline_region_code",
        "indicator_code": "official_baseline_indicator_code",
        "nace_code": "official_baseline_nace_code",
        "freq_code": "official_baseline_freq_code",
        "latest_period": "official_baseline_latest_period",
        "official_regional_baseline_proxy": "official_baseline_proxy",
        "source_status": "official_baseline_source_status",
        "validation_status": "official_baseline_validation_status",
        "current_use_in_scoring": "official_baseline_current_use_in_scoring",
        "approved_current_use": "official_baseline_approved_current_use",
        "prohibited_current_use": "official_baseline_prohibited_current_use",
        "production_score_change": "official_baseline_production_score_change",
        "official_baseline_used_in_monte_carlo": (
            "official_baseline_used_in_monte_carlo"
        ),
        "source_separation_note": "official_baseline_source_separation_note",
        "control_note": "official_baseline_control_note",
    }

    out = out.rename(columns=rename_map)

    out["official_baseline_candidate_available"] = True

    if "official_baseline_used_in_scoring" not in out.columns:
        out["official_baseline_used_in_scoring"] = False

    if "official_baseline_used_in_monte_carlo" not in out.columns:
        out["official_baseline_used_in_monte_carlo"] = False

    if "official_baseline_approved_current_use" not in out.columns:
        out["official_baseline_approved_current_use"] = (
            "controlled_benchmark_integration_only"
        )

    if "official_baseline_prohibited_current_use" not in out.columns:
        out["official_baseline_prohibited_current_use"] = (
            "risk_layer_calculation_or_composite_scoring"
        )

    if "official_baseline_production_score_change" not in out.columns:
        out["official_baseline_production_score_change"] = "none"

    if "official_baseline_source_separation_note" not in out.columns:
        out["official_baseline_source_separation_note"] = (
            "Official Ukrstat GRP baseline candidates remain separate from expanded "
            "Prozorro, wartime AML/CFT typology, official FIU/SFMS context, "
            "analyst-review, false-positive, source-freshness, and run-manifest layers."
        )

    if "official_baseline_control_note" not in out.columns:
        out["official_baseline_control_note"] = (
            "Official Ukrstat GRP baseline candidate attached for validation context "
            "only; not used in WARIS risk-layer, composite-score, risk-band, "
            "review-rationale, or Monte Carlo calculations."
        )

    return out


def _attach_official_baseline_context(scored: pd.DataFrame) -> pd.DataFrame:
    """Attach official-baseline governance fields without changing scores."""
    if scored.empty or "oblast" not in scored.columns:
        return scored

    candidates = _load_official_baseline_candidates()

    out = scored.copy()

    if candidates is None or candidates.empty:
        out["official_baseline_candidate_available"] = False
        out["official_baseline_used_in_scoring"] = False
        out["official_baseline_current_use_in_scoring"] = "not_available"
        out["official_baseline_validation_status"] = "not_available"
        out["official_baseline_control_note"] = (
            "No official Ukrstat baseline candidate artifact was available for this run."
        )
        return out

    out = out.merge(candidates, on="oblast", how="left")

    out["official_baseline_candidate_available"] = out[
        "official_baseline_candidate_available"
    ].fillna(False)

    out["official_baseline_used_in_scoring"] = out[
        "official_baseline_used_in_scoring"
    ].fillna(False)

    for col, fallback in [
        ("official_baseline_region_code", ""),
        ("official_baseline_indicator_code", ""),
        ("official_baseline_nace_code", ""),
        ("official_baseline_freq_code", ""),
        ("official_baseline_latest_period", ""),
        ("official_baseline_proxy", ""),
        ("official_baseline_source_status", "not_available"),
        ("official_baseline_validation_status", "not_available"),
        ("official_baseline_current_use_in_scoring", "not_available"),
        ("official_baseline_approved_current_use", "controlled_benchmark_integration_only"),
        (
            "official_baseline_prohibited_current_use",
            "risk_layer_calculation_or_composite_scoring",
        ),
        ("official_baseline_production_score_change", "none"),
        (
            "official_baseline_source_separation_note",
            "Official baseline remains separate from Prozorro, typology, FIU/SFMS, "
            "analyst-review, false-positive, source-freshness, and run-manifest layers.",
        ),
        (
            "official_baseline_control_note",
            "No official baseline candidate matched this oblast.",
        ),
    ]:
        if col in out.columns:
            out[col] = out[col].fillna(fallback)

    return out


def _load_expanded_prozorro_context() -> pd.DataFrame | None:
    """Load expanded Prozorro procurement candidates when available.

    These features are attached to risk-model outputs only as review/governance
    context. They do not change procurement_integrity_risk, any risk layer, the
    composite score, risk band, or review rationale.
    """
    features = _load_optional_csv(PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE)

    if features is None or not {"oblast", "sector"}.issubset(features.columns):
        return None

    working = features.copy()

    numeric_cols = [
        "procurement_review_priority_candidate",
        "procurement_intensity_score",
        "procurement_value_score",
        "single_bid_supplier_score",
        "reconstruction_emergency_score",
        "buyer_concentration_score",
        "tender_count",
        "total_expected_value",
        "single_bid_or_supplier_proxy_rate",
        "reconstruction_emergency_share",
        "top_buyer_tender_share",
    ]

    for col in numeric_cols:
        if col in working.columns:
            working[col] = pd.to_numeric(working[col], errors="coerce")

    keep_cols = [
        col
        for col in [
            "oblast",
            "sector",
            "tender_count",
            "total_expected_value",
            "single_bid_or_supplier_proxy_rate",
            "reconstruction_emergency_share",
            "top_buyer_tender_share",
            "procurement_review_priority_candidate",
            "procurement_intensity_score",
            "procurement_value_score",
            "single_bid_supplier_score",
            "reconstruction_emergency_score",
            "buyer_concentration_score",
            "current_use",
            "prohibited_use",
            "production_score_change",
            "used_in_waris_scoring",
            "used_in_monte_carlo",
            "control_note",
        ]
        if col in working.columns
    ]

    working = working[keep_cols].drop_duplicates(
        subset=["oblast", "sector"],
        keep="first",
    )

    rename_map = {
        "tender_count": "expanded_prozorro_tender_count",
        "total_expected_value": "expanded_prozorro_total_expected_value",
        "single_bid_or_supplier_proxy_rate": (
            "expanded_prozorro_single_bid_or_supplier_proxy_rate"
        ),
        "reconstruction_emergency_share": (
            "expanded_prozorro_reconstruction_emergency_share"
        ),
        "top_buyer_tender_share": "expanded_prozorro_top_buyer_tender_share",
        "procurement_review_priority_candidate": (
            "expanded_prozorro_procurement_review_priority_candidate"
        ),
        "procurement_intensity_score": "expanded_prozorro_procurement_intensity_score",
        "procurement_value_score": "expanded_prozorro_procurement_value_score",
        "single_bid_supplier_score": "expanded_prozorro_single_bid_supplier_score",
        "reconstruction_emergency_score": (
            "expanded_prozorro_reconstruction_emergency_score"
        ),
        "buyer_concentration_score": "expanded_prozorro_buyer_concentration_score",
        "current_use": "expanded_prozorro_current_use",
        "prohibited_use": "expanded_prozorro_prohibited_use",
        "production_score_change": "expanded_prozorro_production_score_change",
        "used_in_waris_scoring": "expanded_prozorro_used_in_waris_scoring",
        "used_in_monte_carlo": "expanded_prozorro_used_in_monte_carlo",
        "control_note": "expanded_prozorro_control_note",
        "context_bridge_note": "expanded_prozorro_context_bridge_note",
    }

    working = working.rename(columns=rename_map)

    scoring_candidates = _load_optional_csv(PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE)

    if (
        scoring_candidates is not None
        and {"oblast", "sector", "production_score_change"}.issubset(
            scoring_candidates.columns
        )
    ):
        candidate_controls = scoring_candidates[
            ["oblast", "sector", "production_score_change"]
        ].drop_duplicates(subset=["oblast", "sector"], keep="first")
        candidate_controls = candidate_controls.rename(
            columns={
                "production_score_change": (
                    "expanded_prozorro_candidate_production_score_change"
                )
            }
        )
        working = working.merge(candidate_controls, on=["oblast", "sector"], how="left")
    else:
        working["expanded_prozorro_candidate_production_score_change"] = (
            PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
        )

    working["expanded_prozorro_feature_candidate_available"] = True
    working["expanded_prozorro_used_in_scoring"] = False

    working["expanded_prozorro_expected_current_use"] = PROZORRO_PROCUREMENT_CURRENT_USE
    working["expanded_prozorro_expected_prohibited_use"] = (
        PROZORRO_PROCUREMENT_PROHIBITED_USE
    )
    working["expanded_prozorro_expected_production_score_change"] = (
        PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
    )

    working["expanded_prozorro_current_use_ok"] = (
        working.get("expanded_prozorro_current_use", "")
        .fillna("")
        .astype(str)
        .eq(PROZORRO_PROCUREMENT_CURRENT_USE)
    )
    working["expanded_prozorro_prohibited_use_ok"] = (
        working.get("expanded_prozorro_prohibited_use", "")
        .fillna("")
        .astype(str)
        .eq(PROZORRO_PROCUREMENT_PROHIBITED_USE)
    )
    working["expanded_prozorro_score_change_ok"] = (
        working.get("expanded_prozorro_production_score_change", "")
        .fillna("")
        .astype(str)
        .eq(PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE)
    )

    if "expanded_prozorro_used_in_waris_scoring" not in working.columns:
        working["expanded_prozorro_used_in_waris_scoring"] = False

    if "expanded_prozorro_used_in_monte_carlo" not in working.columns:
        working["expanded_prozorro_used_in_monte_carlo"] = False

    working["expanded_prozorro_control_note"] = working[
        "expanded_prozorro_control_note"
    ].fillna(
        "Expanded Prozorro procurement candidate attached for review context only; "
        "not used in WARIS risk-layer or composite-score calculations."
    )

    return working


def _attach_expanded_prozorro_context(scored: pd.DataFrame) -> pd.DataFrame:
    """Attach expanded Prozorro context without changing scores."""
    if scored.empty or not {"oblast", "sector"}.issubset(scored.columns):
        return scored

    controls = _load_expanded_prozorro_context()

    out = scored.copy()

    if controls is None or controls.empty:
        out["expanded_prozorro_feature_candidate_available"] = False
        out["expanded_prozorro_used_in_scoring"] = False
        out["expanded_prozorro_current_use"] = "not_available"
        out["expanded_prozorro_prohibited_use"] = "not_available"
        out["expanded_prozorro_production_score_change"] = "not_available"
        out["expanded_prozorro_current_use_ok"] = False
        out["expanded_prozorro_prohibited_use_ok"] = False
        out["expanded_prozorro_score_change_ok"] = False
        out["expanded_prozorro_control_note"] = (
            "No expanded Prozorro procurement feature artifact was available for this run."
        )
        return out

    out = out.merge(controls, on=["oblast", "sector"], how="left")

    out["expanded_prozorro_feature_candidate_available"] = out[
        "expanded_prozorro_feature_candidate_available"
    ].fillna(False)

    out["expanded_prozorro_used_in_scoring"] = out[
        "expanded_prozorro_used_in_scoring"
    ].fillna(False)

    fill_values = {
        "expanded_prozorro_current_use": "not_available",
        "expanded_prozorro_prohibited_use": "not_available",
        "expanded_prozorro_production_score_change": "not_available",
        "expanded_prozorro_candidate_production_score_change": "not_available",
        "expanded_prozorro_expected_current_use": PROZORRO_PROCUREMENT_CURRENT_USE,
        "expanded_prozorro_expected_prohibited_use": PROZORRO_PROCUREMENT_PROHIBITED_USE,
        "expanded_prozorro_expected_production_score_change": (
            PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
        ),
        "expanded_prozorro_used_in_waris_scoring": False,
        "expanded_prozorro_used_in_monte_carlo": False,
        "expanded_prozorro_current_use_ok": False,
        "expanded_prozorro_prohibited_use_ok": False,
        "expanded_prozorro_score_change_ok": False,
        "expanded_prozorro_control_note": (
            "No expanded Prozorro procurement candidate matched this oblast/sector."
        ),
        "expanded_prozorro_context_bridge_note": (
            "Expanded Prozorro features remain review-only source context and are "
            "separate from official baseline, wartime typology, FIU/SFMS, "
            "analyst-review, false-positive, source-freshness, and run-manifest artifacts."
        ),
    }

    for col, fallback in fill_values.items():
        if col in out.columns:
            out[col] = out[col].fillna(fallback)

    return out


def _summary_value_for_area(
    table: pd.DataFrame | None,
    summary_area: str,
    value_column: str = "value",
    default: str = "not_available",
) -> str:
    """Return a value from a standard summary table."""
    if table is None or table.empty or "summary_area" not in table.columns:
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


def _load_operational_review_context() -> dict[str, object]:
    """Load operational review/control context as non-scoring governance metadata."""
    analyst_summary = _load_optional_csv(ANALYST_REVIEW_SUMMARY_TABLE)
    false_positive_summary = _load_optional_csv(FALSE_POSITIVE_SUMMARY_TABLE)
    source_freshness_summary = _load_optional_csv(SOURCE_FRESHNESS_SUMMARY_TABLE)
    run_manifest_summary = _load_optional_csv(RUN_MANIFEST_SUMMARY_TABLE)

    run_id = "not_available"
    model_version = "not_available"
    manifest_score_change = "not_available"

    if run_manifest_summary is not None and not run_manifest_summary.empty:
        first = run_manifest_summary.iloc[0]
        run_id = str(first.get("run_id", "not_available"))
        model_version = str(first.get("model_version", "not_available"))
        manifest_score_change = str(
            first.get("production_score_change", "not_available")
        )

    return {
        "analyst_review_available": analyst_summary is not None
        and not analyst_summary.empty,
        "analyst_review_current_use": ANALYST_REVIEW_CURRENT_USE,
        "analyst_review_production_score_change": ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
        "analyst_review_queue_records": _summary_value_for_area(
            analyst_summary,
            "Review queue records",
        ),
        "analyst_review_questions": _summary_value_for_area(
            analyst_summary,
            "Review questions",
        ),
        "false_positive_controls_available": false_positive_summary is not None
        and not false_positive_summary.empty,
        "false_positive_current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        "false_positive_production_score_change": (
            FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE
        ),
        "false_positive_control_counts": _summary_value_for_area(
            false_positive_summary,
            "Control status counts",
        ),
        "false_positive_checklist_rows": _summary_value_for_area(
            false_positive_summary,
            "False-positive review checklist",
        ),
        "source_freshness_available": source_freshness_summary is not None
        and not source_freshness_summary.empty,
        "source_freshness_current_use": SOURCE_FRESHNESS_CURRENT_USE,
        "source_freshness_production_score_change": (
            SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE
        ),
        "source_freshness_posture": _summary_value_for_area(
            source_freshness_summary,
            "Overall freshness posture",
            value_column="status",
        ),
        "source_freshness_counts": _summary_value_for_area(
            source_freshness_summary,
            "Freshness status counts",
        ),
        "run_manifest_available": run_manifest_summary is not None
        and not run_manifest_summary.empty,
        "run_manifest_current_use": RUN_MANIFEST_CURRENT_USE,
        "run_manifest_run_id": run_id,
        "run_manifest_model_version": model_version,
        "run_manifest_production_score_change": manifest_score_change,
        "all_operational_production_score_change_ok": all(
            value == "none"
            for value in [
                ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
                FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
                SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
                RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
            ]
        ),
    }


def _attach_operational_review_context(scored: pd.DataFrame) -> pd.DataFrame:
    """Attach operational review/control context without changing scores."""
    if scored.empty:
        return scored

    out = scored.copy()
    controls = _load_operational_review_context()

    out["analyst_review_available"] = bool(controls["analyst_review_available"])
    out["analyst_review_used_in_scoring"] = False
    out["analyst_review_used_in_monte_carlo"] = False
    out["analyst_review_current_use"] = str(controls["analyst_review_current_use"])
    out["analyst_review_production_score_change"] = str(
        controls["analyst_review_production_score_change"]
    )
    out["analyst_review_queue_records"] = str(
        controls["analyst_review_queue_records"]
    )
    out["analyst_review_questions"] = str(controls["analyst_review_questions"])

    out["false_positive_controls_available"] = bool(
        controls["false_positive_controls_available"]
    )
    out["false_positive_controls_used_in_scoring"] = False
    out["false_positive_controls_used_in_monte_carlo"] = False
    out["false_positive_controls_current_use"] = str(
        controls["false_positive_current_use"]
    )
    out["false_positive_controls_production_score_change"] = str(
        controls["false_positive_production_score_change"]
    )
    out["false_positive_control_counts"] = str(
        controls["false_positive_control_counts"]
    )
    out["false_positive_checklist_rows"] = str(
        controls["false_positive_checklist_rows"]
    )

    out["source_freshness_available"] = bool(controls["source_freshness_available"])
    out["source_freshness_used_in_scoring"] = False
    out["source_freshness_used_in_monte_carlo"] = False
    out["source_freshness_current_use"] = str(
        controls["source_freshness_current_use"]
    )
    out["source_freshness_production_score_change"] = str(
        controls["source_freshness_production_score_change"]
    )
    out["source_freshness_posture"] = str(controls["source_freshness_posture"])
    out["source_freshness_counts"] = str(controls["source_freshness_counts"])

    out["run_manifest_available"] = bool(controls["run_manifest_available"])
    out["run_manifest_used_in_scoring"] = False
    out["run_manifest_used_in_monte_carlo"] = False
    out["run_manifest_current_use"] = str(controls["run_manifest_current_use"])
    out["run_manifest_run_id"] = str(controls["run_manifest_run_id"])
    out["run_manifest_model_version"] = str(controls["run_manifest_model_version"])
    out["run_manifest_production_score_change"] = str(
        controls["run_manifest_production_score_change"]
    )

    out["operational_controls_used_in_scoring"] = False
    out["operational_controls_used_in_monte_carlo"] = False
    out["operational_controls_score_change_ok"] = bool(
        controls["all_operational_production_score_change_ok"]
    )
    out["operational_controls_note"] = (
        "Analyst-review, false-positive, source-freshness, and run-manifest "
        "artifacts are attached for governance context only. They are not used in "
        "WARIS risk-layer, composite-score, risk-band, review-rationale, or Monte "
        "Carlo calculations."
    )

    return out


def _load_wartime_typology_context() -> dict[str, object]:
    """Load wartime AML/CFT typology context as non-scoring governance metadata."""
    register = _load_optional_csv(WARTIME_AML_TYPOLOGY_REGISTER_TABLE)
    layer_map = _load_optional_csv(WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE)
    summary = _load_optional_csv(WARTIME_AML_TYPOLOGY_SUMMARY_TABLE)

    tables = [register, layer_map, summary]

    return {
        "available": register is not None and not register.empty,
        "register_rows": 0 if register is None else len(register),
        "layer_map_rows": 0 if layer_map is None else len(layer_map),
        "summary_rows": 0 if summary is None else len(summary),
        "current_use": ";".join(unique_values_from_tables(tables, "current_use")) or "not_available",
        "prohibited_use": ";".join(unique_values_from_tables(tables, "prohibited_use")) or "not_available",
        "production_score_change": ";".join(
            unique_values_from_tables(tables, "production_score_change")
        )
        or "not_available",
        "used_in_scoring_ok": boolean_field_ok(tables, "used_in_waris_scoring", False),
        "used_in_monte_carlo_ok": boolean_field_ok(tables, "used_in_monte_carlo", False),
    }


def _load_fiu_context() -> dict[str, object]:
    """Load official FIU/SFMS context as non-scoring governance metadata."""
    source_register = _load_optional_csv(FIU_OFFICIAL_SOURCE_REGISTER_TABLE)
    reporting_stats = _load_optional_csv(FIU_REPORTING_STATISTICS_CONTEXT_TABLE)
    case_referrals = _load_optional_csv(FIU_CASE_REFERRAL_CONTEXT_TABLE)
    typology_support = _load_optional_csv(FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE)
    summary = _load_optional_csv(FIU_CONTEXT_SUMMARY_TABLE)

    tables = [
        source_register,
        reporting_stats,
        case_referrals,
        typology_support,
        summary,
    ]

    return {
        "available": source_register is not None and not source_register.empty,
        "source_register_rows": 0 if source_register is None else len(source_register),
        "reporting_stat_rows": 0 if reporting_stats is None else len(reporting_stats),
        "case_referral_rows": 0 if case_referrals is None else len(case_referrals),
        "typology_support_rows": 0 if typology_support is None else len(typology_support),
        "summary_rows": 0 if summary is None else len(summary),
        "current_use": ";".join(unique_values_from_tables(tables, "current_use")) or "not_available",
        "prohibited_use": ";".join(unique_values_from_tables(tables, "prohibited_use")) or "not_available",
        "production_score_change": ";".join(
            unique_values_from_tables(tables, "production_score_change")
        )
        or "not_available",
        "used_in_scoring_ok": boolean_field_ok(tables, "used_in_waris_scoring", False),
        "used_in_monte_carlo_ok": boolean_field_ok(tables, "used_in_monte_carlo", False),
    }


def _attach_wartime_typology_and_fiu_context(scored: pd.DataFrame) -> pd.DataFrame:
    """Attach typology/FIU context status without changing scores."""
    if scored.empty:
        return scored

    out = scored.copy()

    typology = _load_wartime_typology_context()
    fiu = _load_fiu_context()

    out["wartime_aml_typology_available"] = bool(typology["available"])
    out["wartime_aml_typology_used_in_scoring"] = False
    out["wartime_aml_typology_used_in_monte_carlo"] = False
    out["wartime_aml_typology_current_use"] = typology["current_use"]
    out["wartime_aml_typology_expected_current_use"] = WARTIME_AML_TYPOLOGY_CURRENT_USE
    out["wartime_aml_typology_prohibited_use"] = typology["prohibited_use"]
    out["wartime_aml_typology_expected_prohibited_use"] = (
        WARTIME_AML_TYPOLOGY_PROHIBITED_USE
    )
    out["wartime_aml_typology_production_score_change"] = (
        typology["production_score_change"]
    )
    out["wartime_aml_typology_expected_production_score_change"] = (
        WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE
    )
    out["wartime_aml_typology_register_rows"] = typology["register_rows"]
    out["wartime_aml_typology_layer_map_rows"] = typology["layer_map_rows"]
    out["wartime_aml_typology_control_ok"] = (
        bool(typology["available"])
        and typology["current_use"] == WARTIME_AML_TYPOLOGY_CURRENT_USE
        and typology["prohibited_use"] == WARTIME_AML_TYPOLOGY_PROHIBITED_USE
        and typology["production_score_change"]
        == WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE
        and bool(typology["used_in_scoring_ok"])
        and bool(typology["used_in_monte_carlo_ok"])
    )
    out["wartime_aml_typology_control_note"] = (
        "Wartime AML/CFT typology artifacts are literature-support context only; "
        "not used in WARIS risk-layer, composite-score, risk-band, review-rationale, "
        "or Monte Carlo calculations."
    )

    out["fiu_context_available"] = bool(fiu["available"])
    out["fiu_context_used_in_scoring"] = False
    out["fiu_context_used_in_monte_carlo"] = False
    out["fiu_context_current_use"] = fiu["current_use"]
    out["fiu_context_expected_current_use"] = FIU_CONTEXT_CURRENT_USE
    out["fiu_context_prohibited_use"] = fiu["prohibited_use"]
    out["fiu_context_expected_prohibited_use"] = FIU_CONTEXT_PROHIBITED_USE
    out["fiu_context_production_score_change"] = fiu["production_score_change"]
    out["fiu_context_expected_production_score_change"] = (
        FIU_CONTEXT_PRODUCTION_SCORE_CHANGE
    )
    out["fiu_context_source_register_rows"] = fiu["source_register_rows"]
    out["fiu_context_reporting_stat_rows"] = fiu["reporting_stat_rows"]
    out["fiu_context_case_referral_rows"] = fiu["case_referral_rows"]
    out["fiu_context_typology_support_rows"] = fiu["typology_support_rows"]
    out["fiu_context_control_ok"] = (
        bool(fiu["available"])
        and fiu["current_use"] == FIU_CONTEXT_CURRENT_USE
        and fiu["prohibited_use"] == FIU_CONTEXT_PROHIBITED_USE
        and fiu["production_score_change"] == FIU_CONTEXT_PRODUCTION_SCORE_CHANGE
        and bool(fiu["used_in_scoring_ok"])
        and bool(fiu["used_in_monte_carlo_ok"])
    )
    out["fiu_context_control_note"] = (
        "Official FIU/SFMS artifacts are official source-support context only; "
        "not used in WARIS risk-layer, composite-score, risk-band, review-rationale, "
        "or Monte Carlo calculations."
    )

    return out


def _prepare_numeric_inputs(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce expected model inputs to numeric values and handle missing data."""
    out = df.copy()

    missing_cols = [col for col in REQUIRED_INPUT_COLUMNS if col not in out.columns]
    if missing_cols:
        raise ValueError(f"Missing required risk-model input columns: {missing_cols}")

    for col in REQUIRED_INPUT_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    # Preserve a defensible baseline if a live enrichment creates missing values.
    out["prewar_revenue_index_2021"] = out["prewar_revenue_index_2021"].fillna(100)
    out["current_revenue_index"] = out["current_revenue_index"].fillna(
        out["prewar_revenue_index_2021"]
    )

    proxy_cols = [
        "conflict_intensity_proxy",
        "trade_dislocation_proxy",
        "sanctions_counterparty_proxy",
        "procurement_awards_proxy",
        "ownership_opacity_proxy",
        "financial_supervision_proxy",
    ]

    for col in proxy_cols:
        out[col] = clip_0_100(out[col].fillna(0))

    return out


def calculate_risk_layers(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate WARIS AML review-priority layers and composite scores.

    Scores are review-prioritization signals only. They are not accusations of
    misconduct by any person, company, institution, sector, or region.

    Official Ukrstat GRP baseline candidates may be attached as validation
    context, but they are not blended into any risk layer or composite score.

    Expanded Prozorro procurement candidates may also be attached as review
    context, but they are not blended into procurement_integrity_risk, any risk
    layer, the composite score, risk band, or review rationale.

    Wartime AML/CFT typology, official FIU/SFMS context, analyst-review,
    false-positive, source-freshness, and run-manifest artifacts may be attached
    as governance/source/control context only. They are not scoring inputs and
    do not alter Monte Carlo simulations.
    """
    out = _prepare_numeric_inputs(df)

    revenue_change = (
        (out["current_revenue_index"] - out["prewar_revenue_index_2021"])
        / out["prewar_revenue_index_2021"].replace(0, pd.NA)
    ).fillna(0) * 100

    # A conflict-adjusted plausibility benchmark. High growth in high-conflict or
    # high-dislocation contexts creates a review signal, not an allegation.
    expected_penalty = (
        0.35 * out["conflict_intensity_proxy"]
        + 0.20 * out["trade_dislocation_proxy"]
    )

    plausibility_gap_raw = revenue_change + expected_penalty

    out["revenue_change_pct"] = revenue_change
    out["revenue_anomaly_risk"] = clip_0_100(min_max_scale(plausibility_gap_raw))
    out["sanctions_exposure_risk"] = clip_0_100(out["sanctions_counterparty_proxy"])
    out["procurement_integrity_risk"] = clip_0_100(out["procurement_awards_proxy"])
    out["ownership_opacity_risk"] = clip_0_100(out["ownership_opacity_proxy"])

    out["tbml_risk"] = clip_0_100(
        (0.65 * out["trade_dislocation_proxy"])
        + (0.35 * out["sanctions_counterparty_proxy"])
    )

    out["conflict_plausibility_gap"] = clip_0_100(
        min_max_scale(plausibility_gap_raw + (0.30 * out["conflict_intensity_proxy"]))
    )

    out["financial_supervision_exposure"] = clip_0_100(
        out["financial_supervision_proxy"]
    )

    score = 0
    for col, weight in BASE_WEIGHTS.items():
        if col not in out.columns:
            raise ValueError(f"Missing calculated risk layer: {col}")
        score += out[col].fillna(0) * weight

    out["waris_aml_review_score"] = clip_0_100(score)
    out["risk_band"] = out["waris_aml_review_score"].apply(assign_risk_band)

    flag_cols = [
        "revenue_anomaly_risk",
        "sanctions_exposure_risk",
        "procurement_integrity_risk",
        "ownership_opacity_risk",
        "tbml_risk",
        "conflict_plausibility_gap",
        "financial_supervision_exposure",
    ]

    reasons = []

    for _, row in out.iterrows():
        high = [
            c.replace("_risk", "").replace("_", " ")
            for c in flag_cols
            if row[c] >= 70
        ]

        moderate = [
            c.replace("_risk", "").replace("_", " ")
            for c in flag_cols
            if 55 <= row[c] < 70
        ]

        if high:
            reasons.append("High signal: " + "; ".join(high[:3]))
        elif moderate:
            reasons.append("Moderate signal: " + "; ".join(moderate[:3]))
        else:
            reasons.append("No single dominant signal; monitor composite trend")

    out["review_rationale"] = reasons

    out = _attach_official_baseline_context(out)
    out = _attach_expanded_prozorro_context(out)
    out = _attach_wartime_typology_and_fiu_context(out)
    out = _attach_operational_review_context(out)

    return (
        out.sort_values("waris_aml_review_score", ascending=False)
        .reset_index(drop=True)
    )


def summarize_by_oblast(scored: pd.DataFrame) -> pd.DataFrame:
    """Summarize WARIS scores by oblast.

    This function aggregates by oblast only. Sector-level context joins belong in
    summarize_by_sector() and must not be merged here because the grouped output
    does not contain a sector column.
    """
    agg_dict = {
        "waris_aml_review_score": ("waris_aml_review_score", "mean"),
        "max_sector_score": ("waris_aml_review_score", "max"),
        "high_priority_sectors": (
            "risk_band",
            lambda s: int((s == "High AML Review Priority").sum()),
        ),
        "elevated_priority_sectors": (
            "risk_band",
            lambda s: int((s == "Elevated AML Review Priority").sum()),
        ),
    }

    optional_context_cols = {
        "official_baseline_candidate_available": (
            "official_baseline_candidate_available",
            "max",
        ),
        "official_baseline_used_in_scoring": (
            "official_baseline_used_in_scoring",
            "max",
        ),
        "official_baseline_latest_period": (
            "official_baseline_latest_period",
            "first",
        ),
        "official_baseline_proxy": (
            "official_baseline_proxy",
            "first",
        ),
        "official_baseline_validation_status": (
            "official_baseline_validation_status",
            "first",
        ),
        "official_baseline_current_use_in_scoring": (
            "official_baseline_current_use_in_scoring",
            "first",
        ),
        "expanded_prozorro_feature_candidate_available": (
            "expanded_prozorro_feature_candidate_available",
            "max",
        ),
        "expanded_prozorro_used_in_scoring": (
            "expanded_prozorro_used_in_scoring",
            "max",
        ),
        "max_expanded_prozorro_procurement_review_priority_candidate": (
            "expanded_prozorro_procurement_review_priority_candidate",
            "max",
        ),
        "expanded_prozorro_current_use": (
            "expanded_prozorro_current_use",
            "first",
        ),
        "expanded_prozorro_prohibited_use": (
            "expanded_prozorro_prohibited_use",
            "first",
        ),
        "expanded_prozorro_production_score_change": (
            "expanded_prozorro_production_score_change",
            "first",
        ),
        "wartime_aml_typology_available": (
            "wartime_aml_typology_available",
            "max",
        ),
        "wartime_aml_typology_used_in_scoring": (
            "wartime_aml_typology_used_in_scoring",
            "max",
        ),
        "wartime_aml_typology_current_use": (
            "wartime_aml_typology_current_use",
            "first",
        ),
        "wartime_aml_typology_production_score_change": (
            "wartime_aml_typology_production_score_change",
            "first",
        ),
        "wartime_aml_typology_control_ok": (
            "wartime_aml_typology_control_ok",
            "min",
        ),
        "fiu_context_available": (
            "fiu_context_available",
            "max",
        ),
        "fiu_context_used_in_scoring": (
            "fiu_context_used_in_scoring",
            "max",
        ),
        "fiu_context_current_use": (
            "fiu_context_current_use",
            "first",
        ),
        "fiu_context_production_score_change": (
            "fiu_context_production_score_change",
            "first",
        ),
        "fiu_context_control_ok": (
            "fiu_context_control_ok",
            "min",
        ),
        "analyst_review_available": (
            "analyst_review_available",
            "max",
        ),
        "analyst_review_used_in_scoring": (
            "analyst_review_used_in_scoring",
            "max",
        ),
        "analyst_review_current_use": (
            "analyst_review_current_use",
            "first",
        ),
        "false_positive_controls_available": (
            "false_positive_controls_available",
            "max",
        ),
        "false_positive_controls_used_in_scoring": (
            "false_positive_controls_used_in_scoring",
            "max",
        ),
        "false_positive_controls_current_use": (
            "false_positive_controls_current_use",
            "first",
        ),
        "source_freshness_available": (
            "source_freshness_available",
            "max",
        ),
        "source_freshness_used_in_scoring": (
            "source_freshness_used_in_scoring",
            "max",
        ),
        "source_freshness_posture": (
            "source_freshness_posture",
            "first",
        ),
        "run_manifest_available": (
            "run_manifest_available",
            "max",
        ),
        "run_manifest_used_in_scoring": (
            "run_manifest_used_in_scoring",
            "max",
        ),
        "run_manifest_run_id": (
            "run_manifest_run_id",
            "first",
        ),
        "operational_controls_used_in_scoring": (
            "operational_controls_used_in_scoring",
            "max",
        ),
        "operational_controls_score_change_ok": (
            "operational_controls_score_change_ok",
            "min",
        ),
    }

    for output_col, aggregation in optional_context_cols.items():
        source_col = aggregation[0]
        if source_col in scored.columns:
            agg_dict[output_col] = aggregation

    agg = scored.groupby("oblast", as_index=False).agg(**agg_dict)

    agg["risk_band"] = agg["waris_aml_review_score"].apply(assign_risk_band)

    return (
        agg.sort_values("waris_aml_review_score", ascending=False)
        .reset_index(drop=True)
    )


def summarize_by_sector(scored: pd.DataFrame) -> pd.DataFrame:
    """Summarize WARIS scores by sector."""
    agg = scored.groupby("sector", as_index=False).agg(
        waris_aml_review_score=("waris_aml_review_score", "mean"),
        max_oblast_score=("waris_aml_review_score", "max"),
        elevated_or_high_count=(
            "risk_band",
            lambda s: int(
                s.isin(
                    [
                        "High AML Review Priority",
                        "Elevated AML Review Priority",
                    ]
                ).sum()
            ),
        ),
    )

    if "official_baseline_candidate_available" in scored.columns:
        official_context = scored.groupby("sector", as_index=False).agg(
            oblasts_with_official_baseline_candidates=(
                "official_baseline_candidate_available",
                lambda s: int(pd.Series(s).fillna(False).astype(bool).sum()),
            ),
            official_baseline_used_in_scoring=(
                "official_baseline_used_in_scoring",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
        )

        agg = agg.merge(official_context, on="sector", how="left")

    if "expanded_prozorro_feature_candidate_available" in scored.columns:
        prozorro_context = scored.groupby("sector", as_index=False).agg(
            oblasts_with_expanded_prozorro_candidates=(
                "expanded_prozorro_feature_candidate_available",
                lambda s: int(pd.Series(s).fillna(False).astype(bool).sum()),
            ),
            expanded_prozorro_used_in_scoring=(
                "expanded_prozorro_used_in_scoring",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
        )

        if "expanded_prozorro_procurement_review_priority_candidate" in scored.columns:
            prozorro_max = scored.groupby("sector", as_index=False).agg(
                max_expanded_prozorro_procurement_review_priority_candidate=(
                    "expanded_prozorro_procurement_review_priority_candidate",
                    "max",
                )
            )
            prozorro_context = prozorro_context.merge(
                prozorro_max,
                on="sector",
                how="left",
            )

        agg = agg.merge(prozorro_context, on="sector", how="left")

    if "wartime_aml_typology_available" in scored.columns:
        typology_context = scored.groupby("sector", as_index=False).agg(
            wartime_aml_typology_available=(
                "wartime_aml_typology_available",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
            wartime_aml_typology_used_in_scoring=(
                "wartime_aml_typology_used_in_scoring",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
            wartime_aml_typology_control_ok=(
                "wartime_aml_typology_control_ok",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).all()),
            ),
        )
        agg = agg.merge(typology_context, on="sector", how="left")

    if "fiu_context_available" in scored.columns:
        fiu_context = scored.groupby("sector", as_index=False).agg(
            fiu_context_available=(
                "fiu_context_available",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
            fiu_context_used_in_scoring=(
                "fiu_context_used_in_scoring",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
            fiu_context_control_ok=(
                "fiu_context_control_ok",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).all()),
            ),
        )
        agg = agg.merge(fiu_context, on="sector", how="left")

    if "operational_controls_used_in_scoring" in scored.columns:
        operational_context = scored.groupby("sector", as_index=False).agg(
            analyst_review_available=(
                "analyst_review_available",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
            false_positive_controls_available=(
                "false_positive_controls_available",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
            source_freshness_available=(
                "source_freshness_available",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
            run_manifest_available=(
                "run_manifest_available",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
            operational_controls_used_in_scoring=(
                "operational_controls_used_in_scoring",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).any()),
            ),
            operational_controls_score_change_ok=(
                "operational_controls_score_change_ok",
                lambda s: bool(pd.Series(s).fillna(False).astype(bool).all()),
            ),
        )
        agg = agg.merge(operational_context, on="sector", how="left")

    agg["risk_band"] = agg["waris_aml_review_score"].apply(assign_risk_band)

    return (
        agg.sort_values("waris_aml_review_score", ascending=False)
        .reset_index(drop=True)
    )
