"""Official baseline merge-review artifacts for WARIS.

This module reviews controlled benchmark-integration outputs created by:

    python -m src.official_baseline_merge_plan

It does not change WARIS production scoring.

Purpose:
    Turn the benchmark-only, rescale, and replace-oblast-baseline scenario tables
    into concise review artifacts that help analysts decide what official Ukrstat
    GRP is telling us about the synthetic WARIS baseline.

Current approved use expected:
    controlled_benchmark_integration_only

Current prohibited use:
    risk_layer_calculation_or_composite_scoring

Outputs:
    outputs/tables/official_baseline_gap_review.csv
    outputs/tables/official_baseline_scenario_recommendations.csv
    outputs/tables/official_baseline_prozorro_context_review.csv
    outputs/tables/official_baseline_wartime_typology_context_review.csv
    outputs/tables/official_baseline_fiu_context_review.csv
    outputs/tables/official_baseline_operational_controls_context_review.csv
    outputs/tables/official_baseline_merge_review_summary.csv

Expanded Prozorro procurement features, wartime AML/CFT typology artifacts,
official FIU/SFMS context artifacts, analyst-review outputs, false-positive
controls, source-freshness outputs, and run-manifest artifacts remain
review-only/source-support/documentation artifacts. This module can review the
official-baseline-to-context bridges created by official_baseline_merge_plan.py,
but it does not approve scoring integration or alter WARIS production scoring.
"""

from __future__ import annotations

from .controlled_guards import assert_context_flags

from pathlib import Path

import numpy as np
import pandas as pd

from .config import RAW_DIR, TABLE_DIR
from .utils import ensure_dirs


OFFICIAL_BASELINE_READINESS_DECISION_TABLE = (
    TABLE_DIR / "official_baseline_readiness_decision.csv"
)
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

OFFICIAL_BASELINE_GAP_REVIEW_TABLE = (
    TABLE_DIR / "official_baseline_gap_review.csv"
)
OFFICIAL_BASELINE_SCENARIO_RECOMMENDATIONS_TABLE = (
    TABLE_DIR / "official_baseline_scenario_recommendations.csv"
)
OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE = (
    TABLE_DIR / "official_baseline_prozorro_context_review.csv"
)
OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE = (
    TABLE_DIR / "official_baseline_wartime_typology_context_review.csv"
)
OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE = (
    TABLE_DIR / "official_baseline_fiu_context_review.csv"
)
OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE = (
    TABLE_DIR / "official_baseline_operational_controls_context_review.csv"
)
OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_TABLE = (
    TABLE_DIR / "official_baseline_merge_review_summary.csv"
)

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

DECISION_GO_BENCHMARK = "GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION"
APPROVED_BENCHMARK_USE = "controlled_benchmark_integration_only"
PROHIBITED_SCORING_USE = "risk_layer_calculation_or_composite_scoring"


def _safe_read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV if available; otherwise return an empty dataframe."""
    try:
        if not path.exists():
            return pd.DataFrame()

        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _first_value(
    df: pd.DataFrame,
    column: str,
    default: str = "not_available",
) -> str:
    """Return the first value in a dataframe column as text."""
    if df.empty or column not in df.columns:
        return default

    value = df.iloc[0].get(column, default)

    if pd.isna(value):
        return default

    return str(value)


def _readiness_context() -> dict[str, str]:
    """Load official baseline readiness context."""
    readiness = _safe_read_csv(OFFICIAL_BASELINE_READINESS_DECISION_TABLE)

    return {
        "decision": _first_value(readiness, "decision"),
        "approved_current_use": _first_value(readiness, "approved_current_use"),
        "prohibited_current_use": _first_value(readiness, "prohibited_current_use"),
        "rationale": _first_value(readiness, "rationale"),
        "next_decision_point": _first_value(readiness, "next_decision_point"),
    }


def _merge_plan_context() -> dict[str, str | int]:
    """Load merge-plan scenario context."""
    merge_plan = _safe_read_csv(OFFICIAL_BASELINE_MERGE_PLAN_TABLE)

    if merge_plan.empty:
        return {
            "scenario_count": 0,
            "approved_scenario_count": 0,
            "scenario_names": "",
        }

    approved_scenario_count = 0

    if "approved_now" in merge_plan.columns:
        approved_scenario_count = int(
            merge_plan["approved_now"]
            .fillna(False)
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
            .sum()
        )

    scenario_names = ""

    if "scenario_name" in merge_plan.columns:
        scenario_names = "; ".join(
            merge_plan["scenario_name"]
            .fillna("")
            .astype(str)
            .loc[lambda s: s.ne("")]
            .drop_duplicates()
            .tolist()
        )

    return {
        "scenario_count": len(merge_plan),
        "approved_scenario_count": approved_scenario_count,
        "scenario_names": scenario_names,
    }


def _gap_band(abs_gap: float) -> str:
    """Classify absolute official-vs-synthetic index gap."""
    if pd.isna(abs_gap):
        return "missing_gap"
    if abs_gap >= 75:
        return "very_large_gap"
    if abs_gap >= 50:
        return "large_gap"
    if abs_gap >= 25:
        return "moderate_gap"
    if abs_gap >= 10:
        return "small_gap"
    return "minimal_gap"


def _ratio_band(ratio: float) -> str:
    """Classify official-to-synthetic share ratio."""
    if pd.isna(ratio):
        return "missing_ratio"
    if ratio >= 2.0:
        return "official_share_much_higher"
    if ratio >= 1.25:
        return "official_share_higher"
    if ratio <= 0.50:
        return "official_share_much_lower"
    if ratio <= 0.80:
        return "official_share_lower"
    return "roughly_aligned"


def _recommended_action(gap_band: str, ratio_band: str) -> str:
    """Create analyst-facing recommendation for each oblast gap."""
    if gap_band in {"very_large_gap", "large_gap"}:
        if ratio_band in {"official_share_much_lower", "official_share_lower"}:
            return (
                "Review whether the synthetic baseline materially overstates this "
                "oblast's relative economic scale. Keep benchmark-only until "
                "transformation logic is approved."
            )

        if ratio_band in {"official_share_much_higher", "official_share_higher"}:
            return (
                "Review whether the synthetic baseline materially understates this "
                "oblast's relative economic scale. Consider rescale scenario for "
                "sensitivity review only."
            )

        return (
            "Large index gap detected. Review benchmark comparison and rescale "
            "scenario before any scoring-integration discussion."
        )

    if gap_band == "moderate_gap":
        return (
            "Moderate official-vs-synthetic difference. Use for benchmark review "
            "and monitor whether gap materially changes risk-layer interpretation."
        )

    return (
        "Official and synthetic baseline appear reasonably aligned. Keep in "
        "benchmark-only status unless broader transformation review recommends change."
    )


def build_gap_review() -> pd.DataFrame:
    """Build official-vs-synthetic gap review table."""
    ensure_dirs([TABLE_DIR])

    benchmark = _safe_read_csv(OFFICIAL_BASELINE_BENCHMARK_COMPARISON_TABLE)

    required = {
        "waris_oblast", "official_grp_million_uah",
        "official_vs_synthetic_index_gap", "official_to_synthetic_share_ratio",
    }
    # Missing-input status rows are not observations. Preserve an empty typed
    # review table so downstream summaries cannot count them as reviewed oblasts.
    if benchmark.empty or not required.issubset(benchmark.columns):
        out = pd.DataFrame(columns=[
            "waris_oblast", "official_grp_million_uah",
            "official_grp_share_of_waris_total", "synthetic_prewar_share_of_total",
            "official_grp_index_0_100", "synthetic_prewar_index_0_100",
            "official_vs_synthetic_index_gap", "absolute_index_gap",
            "official_to_synthetic_share_ratio", "gap_band", "ratio_band",
            "recommended_action", "review_status", "approved_current_use",
            "prohibited_current_use", "production_score_change", "notes",
        ])
        out.to_csv(OFFICIAL_BASELINE_GAP_REVIEW_TABLE, index=False)
        return out

    working = benchmark.copy()

    numeric_cols = [
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
    ]

    for col in numeric_cols:
        if col in working.columns:
            working[col] = pd.to_numeric(working[col], errors="coerce")

    if "official_vs_synthetic_index_gap" not in working.columns:
        working["official_vs_synthetic_index_gap"] = np.nan

    if "official_to_synthetic_share_ratio" not in working.columns:
        working["official_to_synthetic_share_ratio"] = np.nan

    valid = working["waris_oblast"].fillna("").astype(str).str.strip().ne("")
    for col in ["official_grp_million_uah", "official_vs_synthetic_index_gap", "official_to_synthetic_share_ratio"]:
        valid &= np.isfinite(pd.to_numeric(working[col], errors="coerce")).fillna(False)
    valid &= working["official_grp_million_uah"].gt(0)
    working = working.loc[valid].copy()

    working["absolute_index_gap"] = working["official_vs_synthetic_index_gap"].abs()
    working["gap_band"] = working["absolute_index_gap"].apply(_gap_band)
    working["ratio_band"] = working["official_to_synthetic_share_ratio"].apply(
        _ratio_band
    )
    working["recommended_action"] = [
        _recommended_action(gap_band, ratio_band)
        for gap_band, ratio_band in zip(working["gap_band"], working["ratio_band"])
    ]

    working["review_status"] = "controlled_benchmark_review_only"
    working["approved_current_use"] = APPROVED_BENCHMARK_USE
    working["prohibited_current_use"] = PROHIBITED_SCORING_USE
    working["production_score_change"] = "none"
    working["notes"] = (
        "Official GRP benchmark comparison only. This table does not alter WARIS "
        "risk layers, composite scores, risk bands, or Monte Carlo simulations."
    )

    cols = [
        "waris_oblast",
        "official_grp_million_uah",
        "official_grp_share_of_waris_total",
        "synthetic_prewar_share_of_total",
        "official_grp_index_0_100",
        "synthetic_prewar_index_0_100",
        "official_vs_synthetic_index_gap",
        "absolute_index_gap",
        "official_to_synthetic_share_ratio",
        "gap_band",
        "ratio_band",
        "recommended_action",
        "review_status",
        "approved_current_use",
        "prohibited_current_use",
        "production_score_change",
        "notes",
    ]

    cols = [col for col in cols if col in working.columns]

    out = working[cols].sort_values(
        ["absolute_index_gap", "official_grp_million_uah"],
        ascending=[False, False],
    )

    out.to_csv(OFFICIAL_BASELINE_GAP_REVIEW_TABLE, index=False)
    return out


def _prozorro_bridge_action(row: pd.Series) -> str:
    """Create analyst-facing action for bridge rows without implying wrongdoing."""
    priority = pd.to_numeric(
        row.get("procurement_review_priority_candidate", np.nan),
        errors="coerce",
    )
    gap = pd.to_numeric(
        row.get("official_vs_synthetic_index_gap", np.nan),
        errors="coerce",
    )

    if pd.isna(priority):
        return "Procurement candidate unavailable or withheld. Review missing observations, sample support and source coverage before assigning a priority."

    if pd.notna(priority) and priority >= 75:
        return (
            "High procurement review-priority candidate in context bridge. Review "
            "coverage, mapping quality, buyer concentration, tender details, and "
            "sector assignment. Do not treat as allegation or scoring input."
        )

    if pd.notna(priority) and priority >= 50:
        return (
            "Moderate procurement review-priority candidate. Compare with official "
            "baseline gap and existing WARIS procurement proxy for sensitivity review only."
        )

    if pd.notna(gap) and abs(gap) >= 50:
        return (
            "Large official-vs-synthetic economic baseline gap. Review whether "
            "procurement interpretation is sensitive to oblast scale before any "
            "future scoring change discussion."
        )

    return (
        "Use as low-priority context for analyst review. Keep expanded Prozorro "
        "features outside scoring until validation and change control are complete."
    )


def build_prozorro_context_review() -> pd.DataFrame:
    """Review the official-baseline-to-Prozorro context bridge.

    This is a review artifact only. It does not approve scoring integration,
    procurement-risk changes, or entity-level conclusions.
    """
    ensure_dirs([TABLE_DIR])

    bridge = _safe_read_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE)

    if bridge.empty:
        out = pd.DataFrame(
            [
                {
                    "waris_oblast": "",
                    "review_status": "missing_context_bridge",
                    "current_use": PROZORRO_PROCUREMENT_CURRENT_USE,
                    "prohibited_use": PROZORRO_PROCUREMENT_PROHIBITED_USE,
                    "production_score_change": PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE,
                    "used_in_scoring": False,
                    "used_in_monte_carlo": False,
                    "recommended_action": (
                        "Run python -m src.official_baseline_merge_plan after "
                        "generating expanded Prozorro procurement features."
                    ),
                    "notes": "No official_baseline_prozorro_context_bridge.csv table was available.",
                }
            ]
        )
        # A missing-input notice is not an observation or reviewed region.
        out = out.iloc[:0].copy()
        out.to_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE, index=False)
        return out

    assert_context_flags(bridge)

    working = bridge.copy()

    numeric_cols = [
        "official_grp_million_uah",
        "official_grp_share_of_waris_total",
        "synthetic_prewar_share_of_total",
        "official_to_synthetic_share_ratio",
        "official_vs_synthetic_index_gap",
        "tender_count",
        "total_expected_value",
        "single_bid_or_supplier_proxy_rate",
        "reconstruction_emergency_share",
        "top_buyer_tender_share",
        "procurement_review_priority_candidate",
        "max_procurement_review_priority_candidate",
        "mean_procurement_review_priority_candidate",
        "candidate_sector_count",
    ]

    for col in numeric_cols:
        if col in working.columns:
            working[col] = pd.to_numeric(working[col], errors="coerce")

    if "procurement_review_priority_candidate" not in working.columns:
        if "max_procurement_review_priority_candidate" in working.columns:
            working["procurement_review_priority_candidate"] = working[
                "max_procurement_review_priority_candidate"
            ]
        else:
            working["procurement_review_priority_candidate"] = np.nan

    working["absolute_official_baseline_gap"] = pd.to_numeric(
        working.get("official_vs_synthetic_index_gap", np.nan),
        errors="coerce",
    ).abs()

    working["procurement_candidate_band"] = pd.cut(
        working["procurement_review_priority_candidate"],
        bins=[-0.01, 25, 50, 75, np.inf],
        labels=[
            "low_procurement_context",
            "moderate_procurement_context",
            "elevated_procurement_context",
            "high_procurement_context",
        ],
    ).astype("string").fillna("not_available")

    working["baseline_gap_band"] = working["absolute_official_baseline_gap"].apply(
        _gap_band
    )

    working["review_status"] = "review_only_context_bridge"
    working["current_use"] = PROZORRO_PROCUREMENT_CURRENT_USE
    working["approved_current_use"] = "context_review_only"
    working["prohibited_use"] = PROZORRO_PROCUREMENT_PROHIBITED_USE
    working["production_score_change"] = PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
    working["used_in_scoring"] = False
    working["used_in_monte_carlo"] = False
    working["recommended_action"] = working.apply(_prozorro_bridge_action, axis=1)
    working["notes"] = (
        "Official baseline to expanded Prozorro context review only. This table "
        "does not alter risk layers, composite scores, risk bands, review "
        "rationales, or Monte Carlo simulations."
    )

    cols = [
        "waris_oblast",
        "official_grp_million_uah",
        "official_vs_synthetic_index_gap",
        "absolute_official_baseline_gap",
        "baseline_gap_band",
        "tender_count",
        "total_expected_value",
        "single_bid_or_supplier_proxy_rate",
        "reconstruction_emergency_share",
        "top_buyer_tender_share",
        "candidate_sector_count",
        "procurement_review_priority_candidate",
        "procurement_candidate_band",
        "candidate_support_status",
        "bids_observed_tender_count",
        "bids_unavailable_tender_count",
        "supplier_observed_tender_count",
        "supplier_unavailable_tender_count",
        "publication_status",
        "review_status",
        "current_use",
        "approved_current_use",
        "prohibited_use",
        "production_score_change",
        "used_in_scoring",
        "used_in_monte_carlo",
        "recommended_action",
        "notes",
    ]

    cols = [col for col in cols if col in working.columns]

    out = working[cols].sort_values(
        ["procurement_review_priority_candidate", "absolute_official_baseline_gap"],
        ascending=[False, False],
    )

    out.to_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE, index=False)
    return out


def _source_context_bridge_action(row: pd.Series, source_family: str) -> str:
    """Create analyst-facing action for non-scoring source-support bridge rows."""
    gap = pd.to_numeric(
        row.get("largest_gap_value", np.nan),
        errors="coerce",
    )

    family = str(row.get("typology_family", "")).replace("_", " ").strip()
    layers = str(row.get("waris_layer_candidates", "")).strip()

    if pd.notna(gap) and abs(gap) >= 50:
        return (
            f"Review this {source_family} source-support theme alongside the large "
            "official-vs-synthetic baseline gap. Use for documentation and feature "
            "planning only; do not treat as a scoring input."
        )

    if layers:
        return (
            f"Use this {source_family} theme as source-support context for candidate "
            f"WARIS layers ({layers}). Keep review-only until measurable indicators, "
            "SME review, false-positive controls, and change control are documented."
        )

    if family:
        return (
            f"Use this {source_family} {family} theme as broad context only. It does "
            "not approve scoring integration or imply any oblast/sector finding."
        )

    return (
        f"Use this {source_family} bridge row as low-priority source context only. "
        "No scoring integration is approved."
    )


def _build_source_context_review(
    bridge_path: Path,
    output_path: Path,
    source_family: str,
    current_use: str,
    prohibited_use: str,
    production_score_change: str,
    missing_status: str,
    missing_note: str,
) -> pd.DataFrame:
    """Build a standard review table for non-scoring source-support bridges."""
    ensure_dirs([TABLE_DIR])

    bridge = _safe_read_csv(bridge_path)

    if bridge.empty:
        out = pd.DataFrame(
            [
                {
                    "bridge_name": "",
                    "review_status": missing_status,
                    "source_family": source_family,
                    "typology_id": "",
                    "typology_support_id": "",
                    "typology_name": "",
                    "typology_family": "",
                    "waris_layer_candidates": "",
                    "current_use": current_use,
                    "approved_current_use": "context_review_only",
                    "prohibited_use": prohibited_use,
                    "production_score_change": production_score_change,
                    "used_in_scoring": False,
                    "used_in_monte_carlo": False,
                    "recommended_action": missing_note,
                    "notes": "No context bridge table was available.",
                }
            ]
        )
        out.to_csv(output_path, index=False)
        return out

    assert_context_flags(bridge)

    working = bridge.copy()

    for col in [
        "bridge_name",
        "typology_id",
        "typology_support_id",
        "typology_name",
        "typology_family",
        "waris_layer_candidates",
        "benchmark_rows",
        "largest_gap_oblast",
        "largest_gap_value",
        "average_abs_gap",
    ]:
        if col not in working.columns:
            working[col] = ""

    working["review_status"] = "review_only_context_bridge"
    working["source_family"] = source_family
    working["current_use"] = current_use
    working["approved_current_use"] = "context_review_only"
    working["prohibited_use"] = prohibited_use
    working["production_score_change"] = production_score_change
    working["used_in_scoring"] = False
    working["used_in_monte_carlo"] = False
    working["recommended_action"] = working.apply(
        lambda row: _source_context_bridge_action(row, source_family),
        axis=1,
    )
    working["notes"] = (
        f"Official baseline to {source_family} context review only. This table "
        "does not alter risk layers, composite scores, risk bands, review "
        "rationales, or Monte Carlo simulations."
    )

    cols = [
        "bridge_name",
        "source_family",
        "typology_id",
        "typology_support_id",
        "typology_name",
        "typology_family",
        "waris_layer_candidates",
        "benchmark_rows",
        "largest_gap_oblast",
        "largest_gap_value",
        "average_abs_gap",
        "review_status",
        "current_use",
        "approved_current_use",
        "prohibited_use",
        "production_score_change",
        "used_in_scoring",
        "used_in_monte_carlo",
        "recommended_action",
        "notes",
    ]

    cols = [col for col in cols if col in working.columns]
    out = working[cols].copy()

    if "largest_gap_value" in out.columns:
        out["_sort_gap"] = pd.to_numeric(out["largest_gap_value"], errors="coerce").abs()
        out = out.sort_values(["_sort_gap", "typology_family"], ascending=[False, True])
        out = out.drop(columns=["_sort_gap"])

    out.to_csv(output_path, index=False)
    return out


def build_wartime_typology_context_review() -> pd.DataFrame:
    """Review the official-baseline-to-wartime-typology context bridge."""
    return _build_source_context_review(
        bridge_path=OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_TABLE,
        output_path=OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE,
        source_family="wartime AML/CFT typology",
        current_use=WARTIME_AML_TYPOLOGY_CURRENT_USE,
        prohibited_use=WARTIME_AML_TYPOLOGY_PROHIBITED_USE,
        production_score_change=WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE,
        missing_status="missing_wartime_typology_context_bridge",
        missing_note=(
            "Run python -m src.official_baseline_merge_plan after generating "
            "wartime AML/CFT typology artifacts."
        ),
    )


def build_fiu_context_review() -> pd.DataFrame:
    """Review the official-baseline-to-FIU/SFMS context bridge."""
    return _build_source_context_review(
        bridge_path=OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_TABLE,
        output_path=OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE,
        source_family="official FIU/SFMS context",
        current_use=FIU_CONTEXT_CURRENT_USE,
        prohibited_use=FIU_CONTEXT_PROHIBITED_USE,
        production_score_change=FIU_CONTEXT_PRODUCTION_SCORE_CHANGE,
        missing_status="missing_fiu_context_bridge",
        missing_note=(
            "Run python -m src.official_baseline_merge_plan after generating "
            "official FIU/SFMS context artifacts."
        ),
    )


def _operational_context_bridge_action(row: pd.Series) -> str:
    """Create analyst-facing action for operational-control bridge rows."""
    family = str(row.get("operational_artifact_family", "")).replace("_", " ").strip()
    status = str(row.get("artifact_status", "")).strip().lower()
    score_change = str(row.get("production_score_change", "")).strip().lower()

    if status != "available":
        return (
            f"Operational-control artifact family '{family}' was not available. "
            "Regenerate the relevant module before relying on the full governance "
            "package for external presentation."
        )

    if score_change != "none":
        return (
            f"Review operational-control artifact family '{family}' immediately. "
            "Production score change is not marked as none."
        )

    return (
        f"Operational-control artifact family '{family}' is available for "
        "documentation and human-review support. It does not approve official "
        "baseline scoring integration or alter WARIS production scoring."
    )


def build_operational_controls_context_review() -> pd.DataFrame:
    """Review the official-baseline-to-operational-controls context bridge."""
    ensure_dirs([TABLE_DIR])

    bridge = _safe_read_csv(OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_TABLE)

    if bridge.empty:
        out = pd.DataFrame(
            [
                {
                    "bridge_name": "",
                    "review_status": "missing_operational_controls_context_bridge",
                    "operational_artifact_family": "",
                    "artifact_status": "not_available",
                    "artifact_summary": "",
                    "current_use": "context_review_only",
                    "approved_current_use": "context_review_only",
                    "prohibited_use": PROHIBITED_SCORING_USE,
                    "production_score_change": "none",
                    "used_in_scoring": False,
                    "used_in_monte_carlo": False,
                    "recommended_action": (
                        "Run python -m src.official_baseline_merge_plan after "
                        "generating analyst-review, false-positive, source-freshness, "
                        "and run-manifest artifacts."
                    ),
                    "notes": "No official_baseline_operational_controls_context_bridge.csv table was available.",
                }
            ]
        )
        # A missing-input notice is not an observation or reviewed region.
        out = out.iloc[:0].copy()
        out.to_csv(OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE, index=False)
        return out

    assert_context_flags(bridge)

    working = bridge.copy()

    for col in [
        "bridge_name",
        "operational_artifact_family",
        "artifact_status",
        "artifact_summary",
        "benchmark_rows",
        "largest_gap_oblast",
        "largest_gap_value",
        "average_abs_gap",
        "current_use",
        "approved_current_use",
        "prohibited_use",
        "production_score_change",
        "used_in_scoring",
        "used_in_monte_carlo",
    ]:
        if col not in working.columns:
            working[col] = ""

    working["review_status"] = "documentation_only_context_bridge"
    working["approved_current_use"] = "context_review_only"
    working["prohibited_use"] = PROHIBITED_SCORING_USE
    working["used_in_scoring"] = False
    working["used_in_monte_carlo"] = False
    working["recommended_action"] = working.apply(
        _operational_context_bridge_action,
        axis=1,
    )
    working["notes"] = (
        "Official baseline to operational-controls context review only. This table "
        "documents whether analyst-review, false-positive, source-freshness, and "
        "run-manifest controls are available. It does not alter risk layers, "
        "composite scores, risk bands, review rationales, or Monte Carlo simulations."
    )

    cols = [
        "bridge_name",
        "operational_artifact_family",
        "artifact_status",
        "artifact_summary",
        "benchmark_rows",
        "largest_gap_oblast",
        "largest_gap_value",
        "average_abs_gap",
        "review_status",
        "current_use",
        "approved_current_use",
        "prohibited_use",
        "production_score_change",
        "used_in_scoring",
        "used_in_monte_carlo",
        "recommended_action",
        "notes",
    ]

    cols = [col for col in cols if col in working.columns]
    out = working[cols].copy()

    if "operational_artifact_family" in out.columns:
        out = out.sort_values("operational_artifact_family", ascending=True)

    out.to_csv(OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE, index=False)
    return out


def build_scenario_recommendations(gap_review: pd.DataFrame) -> pd.DataFrame:
    """Build scenario-level recommendations from gap review."""
    ensure_dirs([TABLE_DIR])

    readiness = _readiness_context()
    merge_plan = _safe_read_csv(OFFICIAL_BASELINE_MERGE_PLAN_TABLE)
    rescale = _safe_read_csv(OFFICIAL_BASELINE_RESCALE_SCENARIO_TABLE)
    replace = _safe_read_csv(OFFICIAL_BASELINE_REPLACE_OBLAST_BASELINE_SCENARIO_TABLE)
    prozorro_context_review = _safe_read_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE)
    typology_context_review = _safe_read_csv(
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE
    )
    fiu_context_review = _safe_read_csv(OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE)
    operational_context_review = _safe_read_csv(
        OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE
    )

    if gap_review.empty:
        gap_counts = {}
        largest_gap_oblast = "not_available"
        largest_gap_value = "not_available"
    else:
        gap_counts = gap_review.get(
            "gap_band",
            pd.Series(dtype=str),
        ).value_counts().to_dict()

        if "absolute_index_gap" in gap_review.columns:
            top = gap_review.sort_values("absolute_index_gap", ascending=False).head(1)
            largest_gap_oblast = str(top.iloc[0].get("waris_oblast", "not_available"))
            largest_gap_value = str(
                top.iloc[0].get("official_vs_synthetic_index_gap", "not_available")
            )
        else:
            largest_gap_oblast = "not_available"
            largest_gap_value = "not_available"

    large_gap_count = int(
        gap_counts.get("very_large_gap", 0)
        + gap_counts.get("large_gap", 0)
    )
    moderate_gap_count = int(gap_counts.get("moderate_gap", 0))
    small_or_minimal_gap_count = int(
        gap_counts.get("small_gap", 0)
        + gap_counts.get("minimal_gap", 0)
    )

    scenario_rows = [
        {
            "scenario_name": "benchmark_only",
            "current_recommendation": "recommended_current_posture",
            "rationale": (
                ("Official GRP comparison rows are available for benchmark review; "
                 "readiness must be assessed separately. " if not gap_review.empty else
                 "No complete official-vs-synthetic comparison is available. "
                 "Benchmark evidence remains unavailable; retrieve and validate inputs. ")
                + "Official values remain prohibited from scoring."
            ),
            "evidence": (
                f"{len(gap_review)} oblast benchmark rows reviewed; "
                f"{large_gap_count} large or very large gaps; "
                f"{moderate_gap_count} moderate gaps; "
                f"largest gap: {largest_gap_oblast} ({largest_gap_value})."
            ),
            "approved_current_use": APPROVED_BENCHMARK_USE,
            "prohibited_current_use": PROHIBITED_SCORING_USE,
            "production_score_change": "none",
            "required_before_scoring": (
                "Transformation logic, SME review, sector-allocation review if needed, "
                "and scoring change-control approval."
            ),
        },
        {
            "scenario_name": "rescale_revenue_baseline",
            "current_recommendation": (
                "candidate_for_sensitivity_review"
                if large_gap_count > 0 or moderate_gap_count >= 5
                else "optional_sensitivity_review"
            ),
            "rationale": (
                "Rescale scenario may help test whether oblast-level economic scale "
                "changes the interpretation of revenue anomaly patterns. It remains "
                "non-production and should not affect scores."
            ),
            "evidence": (
                f"{len(rescale)} rescale rows available. Gap distribution: {gap_counts}."
            ),
            "approved_current_use": "scenario_analysis_only",
            "prohibited_current_use": PROHIBITED_SCORING_USE,
            "production_score_change": "none",
            "required_before_scoring": (
                "Document rescale formula, compare before/after layer behavior, "
                "perform sensitivity testing, and obtain SME approval."
            ),
        },
        {
            "scenario_name": "replace_oblast_baseline",
            "current_recommendation": "not_recommended_for_scoring_now",
            "rationale": (
                "When available and validated, official GRP supports oblast-level benchmarking; WARIS scores are "
                "sector/oblast-level. Replacement cannot be used for sector-level scoring "
                "without validated sector allocation or sector-by-oblast official data."
            ),
            "evidence": (
                f"{len(replace)} replace-oblast-baseline rows available; sector allocation "
                "remains unsupported unless separately validated."
            ),
            "approved_current_use": "oblast_level_benchmark_scenario_only",
            "prohibited_current_use": PROHIBITED_SCORING_USE,
            "production_score_change": "none",
            "required_before_scoring": (
                "Find official sector-by-oblast data or approve a defensible sector "
                "allocation method through SME and model-governance review."
            ),
        },
        {
            "scenario_name": "official_baseline_to_prozorro_context_bridge",
            "current_recommendation": "review_context_only",
            "rationale": (
                "The context bridge can help compare official economic scale with "
                "expanded procurement review-priority candidates, but it is not a "
                "scoring scenario and does not approve procurement scoring."
            ),
            "evidence": (
                f"{len(prozorro_context_review)} context-review rows available. "
                "Expanded Prozorro features remain review-only candidate artifacts."
            ),
            "approved_current_use": "context_review_only",
            "prohibited_current_use": PROZORRO_PROCUREMENT_PROHIBITED_USE,
            "production_score_change": PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE,
            "required_before_scoring": (
                "Validate procurement coverage, buyer/address/oblast mapping, sector "
                "mapping, bidder/supplier fields, false-positive controls, procurement/"
                "AML SME review, and formal model change control."
            ),
        },
        {
            "scenario_name": "official_baseline_to_wartime_typology_context_bridge",
            "current_recommendation": "review_context_only",
            "rationale": (
                "The context bridge can help compare official economic baseline gaps "
                "with literature-supported wartime AML/CFT typology themes, but it "
                "is not a scoring scenario and does not approve typology scoring."
            ),
            "evidence": (
                f"{len(typology_context_review)} context-review rows available. "
                "Wartime AML/CFT typology artifacts remain literature-support references."
            ),
            "approved_current_use": "context_review_only",
            "prohibited_current_use": WARTIME_AML_TYPOLOGY_PROHIBITED_USE,
            "production_score_change": WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE,
            "required_before_scoring": (
                "Validate measurable public-source indicators, SME review, "
                "false-positive controls, and formal model change control."
            ),
        },
        {
            "scenario_name": "official_baseline_to_fiu_context_bridge",
            "current_recommendation": "review_context_only",
            "rationale": (
                "The context bridge can help compare official economic baseline gaps "
                "with official FIU/SFMS typology-support themes, but it is not a "
                "scoring scenario and does not approve FIU-context scoring."
            ),
            "evidence": (
                f"{len(fiu_context_review)} context-review rows available. "
                "Official FIU/SFMS artifacts remain source-support context."
            ),
            "approved_current_use": "context_review_only",
            "prohibited_current_use": FIU_CONTEXT_PROHIBITED_USE,
            "production_score_change": FIU_CONTEXT_PRODUCTION_SCORE_CHANGE,
            "required_before_scoring": (
                "Validate measurable oblast/sector indicators, SME review, "
                "false-positive controls, and formal model change control."
            ),
        },
        {
            "scenario_name": "official_baseline_to_operational_controls_context_bridge",
            "current_recommendation": "documentation_context_only",
            "rationale": (
                "The context bridge documents analyst-review, false-positive, "
                "source-freshness, and run-manifest control availability. It is not "
                "a scoring scenario and does not approve official-baseline scoring."
            ),
            "evidence": (
                f"{len(operational_context_review)} context-review rows available. "
                "Operational-control artifacts remain documentation and human-review support."
            ),
            "approved_current_use": "context_review_only",
            "prohibited_current_use": PROHIBITED_SCORING_USE,
            "production_score_change": "none",
            "required_before_scoring": (
                "Operational-control artifacts do not authorize scoring use. "
                "Transformation logic, SME review, validation, and model change "
                "control are still required."
            ),
        },
    ]

    out = pd.DataFrame(scenario_rows)

    out["readiness_decision"] = readiness["decision"]
    out["readiness_approved_current_use"] = readiness["approved_current_use"]
    out["readiness_prohibited_current_use"] = readiness["prohibited_current_use"]

    if not merge_plan.empty and "scenario_name" in merge_plan.columns:
        out = out.merge(
            merge_plan[
                [
                    col
                    for col in [
                        "scenario_name",
                        "approved_now",
                        "output_table",
                    ]
                    if col in merge_plan.columns
                ]
            ],
            on="scenario_name",
            how="left",
        )

    out.to_csv(OFFICIAL_BASELINE_SCENARIO_RECOMMENDATIONS_TABLE, index=False)
    return out


def build_merge_review_summary(
    gap_review: pd.DataFrame,
    scenario_recommendations: pd.DataFrame,
    prozorro_context_review: pd.DataFrame,
    typology_context_review: pd.DataFrame,
    fiu_context_review: pd.DataFrame,
    operational_context_review: pd.DataFrame,
) -> pd.DataFrame:
    """Build concise merge-review summary."""
    ensure_dirs([TABLE_DIR])

    readiness = _readiness_context()
    merge_context = _merge_plan_context()

    if gap_review.empty:
        largest_gap_oblast = "not_available"
        largest_gap_value = "not_available"
        gap_counts = {}
        average_abs_gap = "not_available"
    else:
        working = gap_review.copy()
        working["absolute_index_gap"] = pd.to_numeric(
            working.get("absolute_index_gap", np.nan),
            errors="coerce",
        )

        top = working.sort_values("absolute_index_gap", ascending=False).head(1)
        largest_gap_oblast = str(top.iloc[0].get("waris_oblast", "not_available"))
        largest_gap_value = str(
            top.iloc[0].get("official_vs_synthetic_index_gap", "not_available")
        )
        gap_counts = working["gap_band"].value_counts().to_dict()
        average_abs_gap = f"{working['absolute_index_gap'].mean():.2f}"

    recommended_current_posture = "benchmark_only"

    if not scenario_recommendations.empty:
        recommended = scenario_recommendations[
            scenario_recommendations["current_recommendation"].eq(
                "recommended_current_posture"
            )
        ]
        if not recommended.empty:
            recommended_current_posture = str(
                recommended.iloc[0].get("scenario_name", "benchmark_only")
            )

    if prozorro_context_review.empty:
        prozorro_review_count = 0
        top_prozorro_oblast = "not_available"
        top_prozorro_score = "not_available"
        prozorro_band_counts = {}
    else:
        prozorro_working = prozorro_context_review.copy()
        if "procurement_review_priority_candidate" in prozorro_working.columns:
            prozorro_working["procurement_review_priority_candidate"] = pd.to_numeric(
                prozorro_working["procurement_review_priority_candidate"],
                errors="coerce",
            )
            top_prozorro = prozorro_working.sort_values(
                "procurement_review_priority_candidate",
                ascending=False,
            ).head(1)
            top_prozorro_oblast = str(
                top_prozorro.iloc[0].get("waris_oblast", "not_available")
            )
            top_prozorro_score = str(
                top_prozorro.iloc[0].get(
                    "procurement_review_priority_candidate",
                    "not_available",
                )
            )
        else:
            top_prozorro_oblast = "not_available"
            top_prozorro_score = "not_available"

        prozorro_review_count = len(prozorro_context_review)
        if "procurement_candidate_band" in prozorro_context_review.columns:
            prozorro_band_counts = (
                prozorro_context_review["procurement_candidate_band"]
                .fillna("missing_band")
                .astype(str)
                .value_counts()
                .to_dict()
            )
        else:
            prozorro_band_counts = {}

    typology_review_count = 0 if typology_context_review.empty else len(typology_context_review)
    fiu_review_count = 0 if fiu_context_review.empty else len(fiu_context_review)
    operational_review_count = (
        0 if operational_context_review.empty else len(operational_context_review)
    )

    operational_status_counts = (
        operational_context_review["artifact_status"]
        .fillna("missing_status")
        .astype(str)
        .value_counts()
        .to_dict()
        if not operational_context_review.empty
        and "artifact_status" in operational_context_review.columns
        else {}
    )

    typology_family_counts = (
        typology_context_review["typology_family"]
        .fillna("missing_family")
        .astype(str)
        .value_counts()
        .to_dict()
        if not typology_context_review.empty
        and "typology_family" in typology_context_review.columns
        else {}
    )

    fiu_family_counts = (
        fiu_context_review["typology_family"]
        .fillna("missing_family")
        .astype(str)
        .value_counts()
        .to_dict()
        if not fiu_context_review.empty and "typology_family" in fiu_context_review.columns
        else {}
    )

    rows = [
        {
            "summary_area": "Readiness decision",
            "status": readiness["decision"],
            "summary": readiness["rationale"],
            "recommended_next_action": readiness["next_decision_point"],
        },
        {
            "summary_area": "Approved current use",
            "status": readiness["approved_current_use"],
            "summary": (
                "Current readiness is reported in the status field. Missing official "
                "evidence does not approve benchmark use; scoring remains prohibited."
            ),
            "recommended_next_action": (
                "Keep official GRP excluded from scoring until transformation logic "
                "and SME review are complete."
            ),
        },
        {
            "summary_area": "Prohibited current use",
            "status": readiness["prohibited_current_use"],
            "summary": (
                "Official GRP must not alter WARIS risk layers, composite scores, "
                "risk bands, or Monte Carlo simulations."
            ),
            "recommended_next_action": (
                "Block any production scoring change until a formal scoring-integration "
                "change-control branch is approved."
            ),
        },
        {
            "summary_area": "Benchmark gap review",
            "status": "created" if not gap_review.empty else "missing",
            "summary": (
                f"{len(gap_review)} oblasts reviewed. Average absolute index gap: "
                f"{average_abs_gap}. Largest gap: {largest_gap_oblast} "
                f"({largest_gap_value}). Gap distribution: {gap_counts}."
            ),
            "recommended_next_action": (
                "Review large-gap oblasts before choosing any transformation path."
            ),
        },
        {
            "summary_area": "Scenario recommendation",
            "status": recommended_current_posture,
            "summary": (
                "Benchmark-only remains the recommended current posture. Rescale can "
                "be used for sensitivity review. Replace-oblast-baseline is not "
                "recommended for scoring until sector allocation is validated."
            ),
            "recommended_next_action": (
                "Document a benchmark review memo before any scoring integration work."
            ),
        },
        {
            "summary_area": "Merge-plan coverage",
            "status": "available" if merge_context["scenario_count"] else "missing",
            "summary": (
                f"{merge_context['scenario_count']} scenarios documented; "
                f"{merge_context['approved_scenario_count']} approved for current use. "
                f"Scenarios: {merge_context['scenario_names']}."
            ),
            "recommended_next_action": (
                "Keep scenario outputs labeled as non-production benchmark artifacts."
            ),
        },
        {
            "summary_area": "Official baseline to Prozorro context review",
            "status": "created" if prozorro_review_count else "missing",
            "summary": (
                f"{prozorro_review_count} context-review rows. Top procurement "
                f"context candidate: {top_prozorro_oblast} ({top_prozorro_score}). "
                f"Procurement context band distribution: {prozorro_band_counts}. "
                "Expanded Prozorro features remain review-only with "
                "production_score_change=none."
            ),
            "recommended_next_action": (
                "Review procurement coverage, mapping quality, false-positive controls, "
                "and SME feedback before any future procurement scoring discussion."
            ),
        },
        {
            "summary_area": "Official baseline to wartime AML typology context review",
            "status": "created" if typology_review_count else "missing",
            "summary": (
                f"{typology_review_count} context-review rows. "
                f"Typology family distribution: {typology_family_counts}. "
                "Wartime AML/CFT typology artifacts remain literature-support "
                "references with production_score_change=none."
            ),
            "recommended_next_action": (
                "Use typology context for documentation and feature planning only. "
                "Require measurable indicators, SME review, and change control before "
                "any future typology scoring discussion."
            ),
        },
        {
            "summary_area": "Official baseline to FIU/SFMS context review",
            "status": "created" if fiu_review_count else "missing",
            "summary": (
                f"{fiu_review_count} context-review rows. "
                f"FIU/SFMS typology family distribution: {fiu_family_counts}. "
                "Official FIU/SFMS context artifacts remain source-support context "
                "with production_score_change=none."
            ),
            "recommended_next_action": (
                "Use FIU/SFMS context for source confidence, reporting, and governance "
                "only. Require measurable oblast/sector indicators, SME review, and "
                "change control before any future FIU-context scoring discussion."
            ),
        },
        {
            "summary_area": "Official baseline to operational controls context review",
            "status": "created" if operational_review_count else "missing",
            "summary": (
                f"{operational_review_count} context-review rows. "
                f"Operational artifact status distribution: {operational_status_counts}. "
                "Analyst-review, false-positive, source-freshness, and run-manifest "
                "artifacts remain documentation and human-review support with "
                "production_score_change=none."
            ),
            "recommended_next_action": (
                "Use operational-control context to confirm review-support safeguards "
                "are available before external presentation. Do not treat operational "
                "controls as scoring approval."
            ),
        },
    ]

    out = pd.DataFrame(rows)
    out.to_csv(OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_TABLE, index=False)
    return out


def build_official_baseline_merge_review_artifacts() -> dict[str, pd.DataFrame]:
    """Build all controlled merge-review artifacts."""
    ensure_dirs([TABLE_DIR])

    gap_review = build_gap_review()
    prozorro_context_review = build_prozorro_context_review()
    typology_context_review = build_wartime_typology_context_review()
    fiu_context_review = build_fiu_context_review()
    operational_context_review = build_operational_controls_context_review()
    scenario_recommendations = build_scenario_recommendations(gap_review)
    summary = build_merge_review_summary(
        gap_review=gap_review,
        scenario_recommendations=scenario_recommendations,
        prozorro_context_review=prozorro_context_review,
        typology_context_review=typology_context_review,
        fiu_context_review=fiu_context_review,
        operational_context_review=operational_context_review,
    )

    return {
        "gap_review": gap_review,
        "scenario_recommendations": scenario_recommendations,
        "prozorro_context_review": prozorro_context_review,
        "wartime_typology_context_review": typology_context_review,
        "fiu_context_review": fiu_context_review,
        "operational_controls_context_review": operational_context_review,
        "merge_review_summary": summary,
    }


def main() -> None:
    """CLI entry point."""
    artifacts = build_official_baseline_merge_review_artifacts()
    readiness = _readiness_context()

    print("\nOfficial baseline merge-review artifacts created.")
    print(f"- Readiness decision: {readiness['decision']}")
    print(f"- Approved current use: {readiness['approved_current_use']}")
    print(f"- Prohibited current use: {readiness['prohibited_current_use']}")

    print(f"- Gap review rows: {len(artifacts['gap_review'])}")
    print(
        "- Scenario recommendation rows: "
        f"{len(artifacts['scenario_recommendations'])}"
    )
    print(
        "- Official baseline to Prozorro context-review rows: "
        f"{len(artifacts['prozorro_context_review'])}"
    )
    print(
        "- Official baseline to wartime AML typology context-review rows: "
        f"{len(artifacts['wartime_typology_context_review'])}"
    )
    print(
        "- Official baseline to FIU/SFMS context-review rows: "
        f"{len(artifacts['fiu_context_review'])}"
    )
    print(
        "- Official baseline to operational controls context-review rows: "
        f"{len(artifacts['operational_controls_context_review'])}"
    )
    print(f"- Merge-review summary rows: {len(artifacts['merge_review_summary'])}")

    if not artifacts["gap_review"].empty and "absolute_index_gap" in artifacts["gap_review"].columns:
        top = artifacts["gap_review"].head(1).iloc[0]
        print(
            "- Largest official-vs-synthetic gap: "
            f"{top.get('waris_oblast', 'not_available')} "
            f"({top.get('official_vs_synthetic_index_gap', 'not_available')})"
        )

    if not artifacts["scenario_recommendations"].empty:
        current = artifacts["scenario_recommendations"][
            artifacts["scenario_recommendations"]["current_recommendation"].eq(
                "recommended_current_posture"
            )
        ]

        if not current.empty:
            print(
                "- Recommended current posture: "
                f"{current.iloc[0].get('scenario_name', 'benchmark_only')}"
            )

    print(f"- Gap review: {OFFICIAL_BASELINE_GAP_REVIEW_TABLE}")
    print(
        "- Scenario recommendations: "
        f"{OFFICIAL_BASELINE_SCENARIO_RECOMMENDATIONS_TABLE}"
    )
    print(
        "- Official baseline to Prozorro context review: "
        f"{OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE}"
    )
    print(
        "- Official baseline to wartime AML typology context review: "
        f"{OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE}"
    )
    print(
        "- Official baseline to FIU/SFMS context review: "
        f"{OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE}"
    )
    print(
        "- Official baseline to operational controls context review: "
        f"{OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE}"
    )
    print(f"- Merge-review summary: {OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_TABLE}")

    print(
        "\nImportant: These are review artifacts only. They do not alter WARIS "
        "risk layers, composite scores, risk bands, or Monte Carlo simulations."
    )


if __name__ == "__main__":
    main()
