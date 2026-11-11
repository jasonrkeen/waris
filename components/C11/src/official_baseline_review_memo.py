"""Official baseline benchmark review memo for WARIS.

This module creates an analyst-facing memo from the official baseline validation,
merge-planning, and merge-review artifacts.

It does not alter WARIS scoring.

Purpose:
    Explain what the official Ukrstat GRP benchmark comparison shows in plain
    language and document why the current posture remains benchmark_only.

Current expected posture:
    recommended_current_posture = benchmark_only

Approved current use:
    controlled_benchmark_integration_only

Prohibited current use:
    risk_layer_calculation_or_composite_scoring

Output:
    outputs/reports/official_baseline_benchmark_review_memo.md

The memo also summarizes the controlled official-baseline-to-Prozorro,
official-baseline-to-wartime-AML-typology, official-baseline-to-FIU/SFMS, and
official-baseline-to-operational-controls context bridge and context-review
artifacts when they are available. Expanded Prozorro procurement features,
wartime AML/CFT typology artifacts, official FIU/SFMS context artifacts,
analyst-review outputs, false-positive controls, source-freshness outputs, and
run-manifest artifacts remain review/source-support/documentation artifacts and
are not approved for scoring.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .config import REPORT_DIR, TABLE_DIR
from .utils import ensure_dirs


OFFICIAL_BASELINE_READINESS_DECISION_TABLE = (
    TABLE_DIR / "official_baseline_readiness_decision.csv"
)
OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE = (
    TABLE_DIR / "official_baseline_unit_evidence_summary.csv"
)

OFFICIAL_BASELINE_MERGE_PLAN_TABLE = (
    TABLE_DIR / "official_baseline_merge_plan.csv"
)
OFFICIAL_BASELINE_BENCHMARK_COMPARISON_TABLE = (
    TABLE_DIR / "official_baseline_benchmark_comparison.csv"
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

MEMO_OUTPUT_PATH = REPORT_DIR / "official_baseline_benchmark_review_memo.md"

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

EXPECTED_DECISION = "GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION"
EXPECTED_APPROVED_USE = "controlled_benchmark_integration_only"
EXPECTED_PROHIBITED_USE = "risk_layer_calculation_or_composite_scoring"
EXPECTED_POSTURE = "benchmark_only"


def _safe_read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV if available; otherwise return an empty dataframe."""
    try:
        if not path.exists():
            return pd.DataFrame()

        df = pd.read_csv(path)

        if df.empty:
            return pd.DataFrame()

        return df
    except Exception:
        return pd.DataFrame()


def _first_value(
    df: pd.DataFrame,
    column: str,
    default: str = "not_available",
) -> str:
    """Return the first dataframe value as text."""
    if df.empty or column not in df.columns:
        return default

    value = df.iloc[0].get(column, default)

    if pd.isna(value):
        return default

    return str(value)


def _format_number(value: Any, digits: int = 2) -> str:
    """Format numeric values safely."""
    try:
        numeric = float(value)

        if pd.isna(numeric):
            return "not_available"

        return f"{numeric:,.{digits}f}"
    except Exception:
        return str(value) if value not in [None, ""] else "not_available"


def _markdown_table(
    df: pd.DataFrame,
    columns: list[str],
    max_rows: int = 10,
) -> str:
    """Create a compact markdown table from selected columns."""
    if df.empty:
        return "_No rows available._"

    available_columns = [col for col in columns if col in df.columns]

    if not available_columns:
        return "_No displayable columns available._"

    shown = df[available_columns].head(max_rows).copy()

    for col in shown.columns:
        shown[col] = shown[col].fillna("").astype(str)

    header = "| " + " | ".join(available_columns) + " |"
    separator = "| " + " | ".join(["---"] * len(available_columns)) + " |"

    rows = []
    for _, row in shown.iterrows():
        values = [
            str(row[col])
            .replace("\n", " ")
            .replace("|", "/")
            .strip()
            for col in available_columns
        ]
        rows.append("| " + " | ".join(values) + " |")

    return "\n".join([header, separator] + rows)


def _readiness_context() -> dict[str, str]:
    """Load official baseline readiness decision context."""
    readiness = _safe_read_csv(OFFICIAL_BASELINE_READINESS_DECISION_TABLE)

    return {
        "decision": _first_value(readiness, "decision"),
        "approved_current_use": _first_value(readiness, "approved_current_use"),
        "prohibited_current_use": _first_value(readiness, "prohibited_current_use"),
        "rationale": _first_value(readiness, "rationale"),
        "next_decision_point": _first_value(readiness, "next_decision_point"),
    }


def _unit_context() -> dict[str, str]:
    """Load unit/scale evidence context."""
    unit = _safe_read_csv(OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE)

    return {
        "unit_interpretation": _first_value(unit, "unit_interpretation"),
        "validation_status": _first_value(unit, "validation_status"),
        "indicator_name": _first_value(unit, "indicator_name"),
        "nace_name": _first_value(unit, "nace_name"),
        "freq_name": _first_value(unit, "freq_name"),
        "period_min": _first_value(unit, "period_min"),
        "period_max": _first_value(unit, "period_max"),
        "row_count": _first_value(unit, "row_count"),
        "waris_region_count": _first_value(unit, "waris_region_count"),
        "source_file": _first_value(unit, "source_file"),
    }


def _gap_review_context(gap_review: pd.DataFrame) -> dict[str, object]:
    """Summarize official-vs-synthetic gap review."""
    if gap_review.empty:
        return {
            "row_count": 0,
            "largest_gap_oblast": "not_available",
            "largest_gap_value": "not_available",
            "average_absolute_gap": "not_available",
            "gap_distribution": {},
            "very_large_or_large_count": 0,
            "moderate_count": 0,
            "small_or_minimal_count": 0,
        }

    working = gap_review.copy()

    if "absolute_index_gap" in working.columns:
        working["absolute_index_gap"] = pd.to_numeric(
            working["absolute_index_gap"],
            errors="coerce",
        )
        average_gap = working["absolute_index_gap"].mean()
        working = working.sort_values("absolute_index_gap", ascending=False)
    else:
        average_gap = pd.NA

    if "official_vs_synthetic_index_gap" in working.columns:
        working["official_vs_synthetic_index_gap"] = pd.to_numeric(
            working["official_vs_synthetic_index_gap"],
            errors="coerce",
        )

    largest_gap_oblast = "not_available"
    largest_gap_value = "not_available"

    if not working.empty:
        largest_gap_oblast = str(working.iloc[0].get("waris_oblast", "not_available"))
        largest_gap_value = str(
            working.iloc[0].get(
                "official_vs_synthetic_index_gap",
                "not_available",
            )
        )

    if "gap_band" in working.columns:
        gap_distribution = (
            working["gap_band"]
            .fillna("missing_gap")
            .astype(str)
            .value_counts()
            .to_dict()
        )
    else:
        gap_distribution = {}

    very_large_or_large_count = int(
        gap_distribution.get("very_large_gap", 0)
        + gap_distribution.get("large_gap", 0)
    )
    moderate_count = int(gap_distribution.get("moderate_gap", 0))
    small_or_minimal_count = int(
        gap_distribution.get("small_gap", 0)
        + gap_distribution.get("minimal_gap", 0)
    )

    return {
        "row_count": len(working),
        "largest_gap_oblast": largest_gap_oblast,
        "largest_gap_value": largest_gap_value,
        "average_absolute_gap": (
            f"{float(average_gap):.2f}" if pd.notna(average_gap) else "not_available"
        ),
        "gap_distribution": gap_distribution,
        "very_large_or_large_count": very_large_or_large_count,
        "moderate_count": moderate_count,
        "small_or_minimal_count": small_or_minimal_count,
    }


def _scenario_context(scenario_recommendations: pd.DataFrame) -> dict[str, str]:
    """Summarize scenario recommendations."""
    if scenario_recommendations.empty:
        return {
            "recommended_current_posture": "not_available",
            "rescale_recommendation": "not_available",
            "replace_recommendation": "not_available",
            "prozorro_context_recommendation": "not_available",
            "wartime_typology_context_recommendation": "not_available",
            "fiu_context_recommendation": "not_available",
            "operational_controls_context_recommendation": "not_available",
        }

    recommended_current_posture = "not_available"
    rescale_recommendation = "not_available"
    replace_recommendation = "not_available"
    prozorro_context_recommendation = "not_available"
    wartime_typology_context_recommendation = "not_available"
    fiu_context_recommendation = "not_available"
    operational_controls_context_recommendation = "not_available"

    if {"scenario_name", "current_recommendation"}.issubset(
        scenario_recommendations.columns
    ):
        current = scenario_recommendations[
            scenario_recommendations["current_recommendation"]
            .fillna("")
            .astype(str)
            .eq("recommended_current_posture")
        ]

        if not current.empty:
            recommended_current_posture = str(
                current.iloc[0].get("scenario_name", "not_available")
            )

        rescale = scenario_recommendations[
            scenario_recommendations["scenario_name"]
            .fillna("")
            .astype(str)
            .eq("rescale_revenue_baseline")
        ]

        if not rescale.empty:
            rescale_recommendation = str(
                rescale.iloc[0].get("current_recommendation", "not_available")
            )

        replace = scenario_recommendations[
            scenario_recommendations["scenario_name"]
            .fillna("")
            .astype(str)
            .eq("replace_oblast_baseline")
        ]

        if not replace.empty:
            replace_recommendation = str(
                replace.iloc[0].get("current_recommendation", "not_available")
            )

        prozorro_context = scenario_recommendations[
            scenario_recommendations["scenario_name"]
            .fillna("")
            .astype(str)
            .eq("official_baseline_to_prozorro_context_bridge")
        ]

        if not prozorro_context.empty:
            prozorro_context_recommendation = str(
                prozorro_context.iloc[0].get(
                    "current_recommendation",
                    "not_available",
                )
            )

        wartime_typology_context = scenario_recommendations[
            scenario_recommendations["scenario_name"]
            .fillna("")
            .astype(str)
            .eq("official_baseline_to_wartime_typology_context_bridge")
        ]
        if not wartime_typology_context.empty:
            wartime_typology_context_recommendation = str(
                wartime_typology_context.iloc[0].get(
                    "current_recommendation",
                    "not_available",
                )
            )

        fiu_context = scenario_recommendations[
            scenario_recommendations["scenario_name"]
            .fillna("")
            .astype(str)
            .eq("official_baseline_to_fiu_context_bridge")
        ]
        if not fiu_context.empty:
            fiu_context_recommendation = str(
                fiu_context.iloc[0].get("current_recommendation", "not_available")
            )

        operational_controls_context = scenario_recommendations[
            scenario_recommendations["scenario_name"]
            .fillna("")
            .astype(str)
            .eq("official_baseline_to_operational_controls_context_bridge")
        ]
        if not operational_controls_context.empty:
            operational_controls_context_recommendation = str(
                operational_controls_context.iloc[0].get(
                    "current_recommendation",
                    "not_available",
                )
            )

    return {
        "recommended_current_posture": recommended_current_posture,
        "rescale_recommendation": rescale_recommendation,
        "replace_recommendation": replace_recommendation,
        "prozorro_context_recommendation": prozorro_context_recommendation,
        "wartime_typology_context_recommendation": (
            wartime_typology_context_recommendation
        ),
        "fiu_context_recommendation": fiu_context_recommendation,
        "operational_controls_context_recommendation": (
            operational_controls_context_recommendation
        ),
    }


def _prozorro_context_review_context(
    context_review: pd.DataFrame,
) -> dict[str, object]:
    """Summarize official-baseline-to-Prozorro context review."""
    if context_review.empty:
        return {
            "row_count": 0,
            "top_oblast": "not_available",
            "top_score": "not_available",
            "band_distribution": {},
            "current_use_values": [],
            "prohibited_use_values": [],
            "production_score_change_values": [],
            "used_in_scoring_values": [],
            "used_in_monte_carlo_values": [],
        }

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

    top_oblast = "not_available"
    top_score = "not_available"

    if not working.empty:
        top_oblast = str(working.iloc[0].get("waris_oblast", "not_available"))
        top_score = str(
            working.iloc[0].get(
                "procurement_review_priority_candidate",
                "not_available",
            )
        )

    if "procurement_candidate_band" in working.columns:
        band_distribution = (
            working["procurement_candidate_band"]
            .fillna("missing_band")
            .astype(str)
            .value_counts()
            .to_dict()
        )
    else:
        band_distribution = {}

    def _unique_values(column: str) -> list[str]:
        if column not in working.columns:
            return []
        return (
            working[column]
            .fillna("")
            .astype(str)
            .loc[lambda s: s.ne("")]
            .drop_duplicates()
            .tolist()
        )

    return {
        "row_count": len(working),
        "top_oblast": top_oblast,
        "top_score": top_score,
        "band_distribution": band_distribution,
        "current_use_values": _unique_values("current_use"),
        "prohibited_use_values": _unique_values("prohibited_use"),
        "production_score_change_values": _unique_values("production_score_change"),
        "used_in_scoring_values": _unique_values("used_in_scoring"),
        "used_in_monte_carlo_values": _unique_values("used_in_monte_carlo"),
    }


def _prozorro_control_assessment(
    context: dict[str, object],
) -> str:
    """Return plain-language control assessment for Prozorro context review."""
    current_use_ok = (
        PROZORRO_PROCUREMENT_CURRENT_USE in context["current_use_values"]
        if context["current_use_values"]
        else False
    )
    prohibited_use_ok = (
        PROZORRO_PROCUREMENT_PROHIBITED_USE in context["prohibited_use_values"]
        if context["prohibited_use_values"]
        else False
    )
    score_change_ok = (
        PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
        in context["production_score_change_values"]
        if context["production_score_change_values"]
        else False
    )

    scoring_ok = (
        "False" in context["used_in_scoring_values"]
        or "false" in context["used_in_scoring_values"]
    )
    monte_carlo_ok = (
        "False" in context["used_in_monte_carlo_values"]
        or "false" in context["used_in_monte_carlo_values"]
    )

    if (
        context["row_count"] > 0
        and current_use_ok
        and prohibited_use_ok
        and score_change_ok
        and scoring_ok
        and monte_carlo_ok
    ):
        return (
            "The expanded Prozorro context-review posture is coherent. The context "
            "bridge is marked review_artifact_only, direct scoring remains prohibited, "
            "production_score_change is none, and the bridge is not used in scoring or "
            "Monte Carlo."
        )

    if context["row_count"] == 0:
        return (
            "No official-baseline-to-Prozorro context review artifact was available. "
            "Run the merge-plan and merge-review modules after generating expanded "
            "Prozorro procurement features."
        )

    return (
        "The expanded Prozorro context-review posture requires review. At least one "
        "current-use, prohibited-use, production-score-change, scoring-use, or "
        "Monte Carlo-use value does not match the expected review-only control state."
    )



def _source_context_review_context(context_review: pd.DataFrame) -> dict[str, object]:
    """Summarize non-scoring source-support context review artifacts."""
    if context_review.empty:
        return {
            "row_count": 0,
            "family_distribution": {},
            "current_use_values": [],
            "prohibited_use_values": [],
            "production_score_change_values": [],
            "used_in_scoring_values": [],
            "used_in_monte_carlo_values": [],
            "top_typology_name": "not_available",
            "top_typology_family": "not_available",
        }

    working = context_review.copy()

    def _unique_values(column: str) -> list[str]:
        if column not in working.columns:
            return []
        return (
            working[column]
            .fillna("")
            .astype(str)
            .loc[lambda s: s.ne("")]
            .drop_duplicates()
            .tolist()
        )

    family_distribution = (
        working["typology_family"]
        .fillna("missing_family")
        .astype(str)
        .value_counts()
        .to_dict()
        if "typology_family" in working.columns
        else {}
    )

    top_typology_name = "not_available"
    top_typology_family = "not_available"
    if not working.empty:
        top_typology_name = str(working.iloc[0].get("typology_name", "not_available"))
        top_typology_family = str(
            working.iloc[0].get("typology_family", "not_available")
        )

    return {
        "row_count": len(working),
        "family_distribution": family_distribution,
        "current_use_values": _unique_values("current_use"),
        "prohibited_use_values": _unique_values("prohibited_use"),
        "production_score_change_values": _unique_values("production_score_change"),
        "used_in_scoring_values": _unique_values("used_in_scoring"),
        "used_in_monte_carlo_values": _unique_values("used_in_monte_carlo"),
        "top_typology_name": top_typology_name,
        "top_typology_family": top_typology_family,
    }


def _source_context_control_assessment(
    context: dict[str, object],
    label: str,
    expected_current_use: str,
    expected_prohibited_use: str,
    expected_production_score_change: str,
) -> str:
    """Return plain-language source-context control assessment."""
    current_use_ok = (
        expected_current_use in context["current_use_values"]
        if context["current_use_values"]
        else False
    )
    prohibited_use_ok = (
        expected_prohibited_use in context["prohibited_use_values"]
        if context["prohibited_use_values"]
        else False
    )
    score_change_ok = (
        expected_production_score_change in context["production_score_change_values"]
        if context["production_score_change_values"]
        else False
    )
    scoring_ok = (
        "False" in context["used_in_scoring_values"]
        or "false" in context["used_in_scoring_values"]
    )
    monte_carlo_ok = (
        "False" in context["used_in_monte_carlo_values"]
        or "false" in context["used_in_monte_carlo_values"]
    )

    if (
        context["row_count"] > 0
        and current_use_ok
        and prohibited_use_ok
        and score_change_ok
        and scoring_ok
        and monte_carlo_ok
    ):
        return (
            f"The {label} context-review posture is coherent. The context bridge "
            "is marked for source-support review only, direct scoring remains "
            "prohibited, production_score_change is none, and the bridge is not "
            "used in scoring or Monte Carlo."
        )

    if context["row_count"] == 0:
        return (
            f"No {label} context-review artifact was available. Run the typology/FIU "
            "context module, then rerun the merge-plan and merge-review modules."
        )

    return (
        f"The {label} context-review posture requires review. At least one current-use, "
        "prohibited-use, production-score-change, scoring-use, or Monte Carlo-use "
        "value does not match the expected source-support control state."
    )


def _operational_controls_context_review_context(
    context_review: pd.DataFrame,
) -> dict[str, object]:
    """Summarize official-baseline-to-operational-controls context review."""
    if context_review.empty:
        return {
            "row_count": 0,
            "artifact_status_distribution": {},
            "artifact_family_distribution": {},
            "current_use_values": [],
            "production_score_change_values": [],
            "used_in_scoring_values": [],
            "used_in_monte_carlo_values": [],
            "top_artifact_family": "not_available",
            "top_artifact_status": "not_available",
        }

    working = context_review.copy()

    def _unique_values(column: str) -> list[str]:
        if column not in working.columns:
            return []
        return (
            working[column]
            .fillna("")
            .astype(str)
            .loc[lambda s: s.ne("")]
            .drop_duplicates()
            .tolist()
        )

    artifact_status_distribution = (
        working["artifact_status"]
        .fillna("missing_status")
        .astype(str)
        .value_counts()
        .to_dict()
        if "artifact_status" in working.columns
        else {}
    )

    artifact_family_distribution = (
        working["operational_artifact_family"]
        .fillna("missing_family")
        .astype(str)
        .value_counts()
        .to_dict()
        if "operational_artifact_family" in working.columns
        else {}
    )

    top_artifact_family = "not_available"
    top_artifact_status = "not_available"
    if not working.empty:
        top_artifact_family = str(
            working.iloc[0].get("operational_artifact_family", "not_available")
        )
        top_artifact_status = str(
            working.iloc[0].get("artifact_status", "not_available")
        )

    return {
        "row_count": len(working),
        "artifact_status_distribution": artifact_status_distribution,
        "artifact_family_distribution": artifact_family_distribution,
        "current_use_values": _unique_values("current_use"),
        "production_score_change_values": _unique_values("production_score_change"),
        "used_in_scoring_values": _unique_values("used_in_scoring"),
        "used_in_monte_carlo_values": _unique_values("used_in_monte_carlo"),
        "top_artifact_family": top_artifact_family,
        "top_artifact_status": top_artifact_status,
    }


def _operational_controls_control_assessment(
    context: dict[str, object],
) -> str:
    """Return plain-language operational-controls context assessment."""
    score_change_ok = (
        "none" in context["production_score_change_values"]
        if context["production_score_change_values"]
        else False
    )
    scoring_ok = (
        "False" in context["used_in_scoring_values"]
        or "false" in context["used_in_scoring_values"]
    )
    monte_carlo_ok = (
        "False" in context["used_in_monte_carlo_values"]
        or "false" in context["used_in_monte_carlo_values"]
    )

    if context["row_count"] > 0 and score_change_ok and scoring_ok and monte_carlo_ok:
        return (
            "The operational-controls context-review posture is coherent. Analyst-review, "
            "false-positive, source-freshness, and run-manifest artifacts are documented "
            "as review/control support, production_score_change is none, and the bridge "
            "is not used in scoring or Monte Carlo."
        )

    if context["row_count"] == 0:
        return (
            "No official-baseline-to-operational-controls context review artifact was "
            "available. Run the analyst-review, false-positive, source-freshness, "
            "run-manifest, merge-plan, and merge-review modules."
        )

    return (
        "The operational-controls context-review posture requires review. At least one "
        "production-score-change, scoring-use, or Monte Carlo-use value does not match "
        "the expected documentation-only control state."
    )


def _risk_control_assessment(
    readiness: dict[str, str],
    scenario: dict[str, str],
) -> str:
    """Return a plain-language risk-control assessment."""
    decision = readiness.get("decision", "not_available")
    approved_use = readiness.get("approved_current_use", "not_available")
    prohibited_use = readiness.get("prohibited_current_use", "not_available")
    posture = scenario.get("recommended_current_posture", "not_available")

    controls_ok = (
        decision == EXPECTED_DECISION
        and approved_use == EXPECTED_APPROVED_USE
        and prohibited_use == EXPECTED_PROHIBITED_USE
        and posture == EXPECTED_POSTURE
    )

    if controls_ok:
        return (
            "The control posture is coherent. Official GRP is approved for controlled "
            "benchmark integration only, the merge-review layer recommends "
            "benchmark_only, and official values remain prohibited from risk-layer "
            "calculation or composite scoring."
        )

    return (
        "The control posture requires review. At least one readiness, approved-use, "
        "prohibited-use, or scenario-recommendation value does not match the expected "
        "benchmark_only control state."
    )


def build_benchmark_review_memo() -> str:
    """Build and save the official baseline benchmark review memo."""
    ensure_dirs([REPORT_DIR])

    readiness = _readiness_context()
    unit = _unit_context()

    gap_review = _safe_read_csv(OFFICIAL_BASELINE_GAP_REVIEW_TABLE)
    scenario_recommendations = _safe_read_csv(
        OFFICIAL_BASELINE_SCENARIO_RECOMMENDATIONS_TABLE
    )
    merge_review_summary = _safe_read_csv(OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_TABLE)
    merge_plan = _safe_read_csv(OFFICIAL_BASELINE_MERGE_PLAN_TABLE)
    benchmark_comparison = _safe_read_csv(OFFICIAL_BASELINE_BENCHMARK_COMPARISON_TABLE)
    prozorro_context_bridge = _safe_read_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE)
    prozorro_context_review = _safe_read_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE)
    wartime_typology_context_bridge = _safe_read_csv(
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_BRIDGE_TABLE
    )
    wartime_typology_context_review = _safe_read_csv(
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE
    )
    fiu_context_bridge = _safe_read_csv(OFFICIAL_BASELINE_FIU_CONTEXT_BRIDGE_TABLE)
    fiu_context_review = _safe_read_csv(OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE)
    operational_controls_context_bridge = _safe_read_csv(
        OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_BRIDGE_TABLE
    )
    operational_controls_context_review = _safe_read_csv(
        OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE
    )

    gap_context = _gap_review_context(gap_review)
    scenario_context = _scenario_context(scenario_recommendations)
    prozorro_context = _prozorro_context_review_context(prozorro_context_review)
    wartime_typology_context = _source_context_review_context(
        wartime_typology_context_review
    )
    fiu_context = _source_context_review_context(fiu_context_review)
    operational_controls_context = _operational_controls_context_review_context(
        operational_controls_context_review
    )
    prozorro_control_assessment = _prozorro_control_assessment(prozorro_context)
    wartime_typology_control_assessment = _source_context_control_assessment(
        context=wartime_typology_context,
        label="wartime AML/CFT typology",
        expected_current_use=WARTIME_AML_TYPOLOGY_CURRENT_USE,
        expected_prohibited_use=WARTIME_AML_TYPOLOGY_PROHIBITED_USE,
        expected_production_score_change=WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE,
    )
    fiu_control_assessment = _source_context_control_assessment(
        context=fiu_context,
        label="official FIU/SFMS",
        expected_current_use=FIU_CONTEXT_CURRENT_USE,
        expected_prohibited_use=FIU_CONTEXT_PROHIBITED_USE,
        expected_production_score_change=FIU_CONTEXT_PRODUCTION_SCORE_CHANGE,
    )
    operational_controls_assessment = _operational_controls_control_assessment(
        operational_controls_context
    )
    control_assessment = _risk_control_assessment(
        readiness=readiness,
        scenario=scenario_context,
    )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    top_gap_table = "_No gap-review table available._"
    if not gap_review.empty:
        gap_display = gap_review.copy()

        if "absolute_index_gap" in gap_display.columns:
            gap_display["absolute_index_gap"] = pd.to_numeric(
                gap_display["absolute_index_gap"],
                errors="coerce",
            )
            gap_display = gap_display.sort_values("absolute_index_gap", ascending=False)

        top_gap_table = _markdown_table(
            gap_display,
            [
                "waris_oblast",
                "official_grp_million_uah",
                "official_grp_share_of_waris_total",
                "synthetic_prewar_share_of_total",
                "official_vs_synthetic_index_gap",
                "absolute_index_gap",
                "official_to_synthetic_share_ratio",
                "gap_band",
                "ratio_band",
                "recommended_action",
                "production_score_change",
            ],
            max_rows=10,
        )

    scenario_table = _markdown_table(
        scenario_recommendations,
        [
            "scenario_name",
            "current_recommendation",
            "rationale",
            "evidence",
            "approved_current_use",
            "prohibited_current_use",
            "production_score_change",
            "required_before_scoring",
        ],
        max_rows=6,
    )

    merge_summary_table = _markdown_table(
        merge_review_summary,
        [
            "summary_area",
            "status",
            "summary",
            "recommended_next_action",
        ],
        max_rows=8,
    )

    merge_plan_table = _markdown_table(
        merge_plan,
        [
            "scenario_name",
            "approved_now",
            "approved_current_use",
            "prohibited_current_use",
            "production_score_change",
            "required_before_scoring",
            "notes",
        ],
        max_rows=6,
    )

    benchmark_snapshot = _markdown_table(
        benchmark_comparison,
        [
            "waris_oblast",
            "official_grp_million_uah",
            "official_grp_share_of_waris_total",
            "synthetic_prewar_share_of_total",
            "official_to_synthetic_share_ratio",
            "official_vs_synthetic_index_gap",
            "benchmark_status",
            "current_use_in_scoring",
        ],
        max_rows=10,
    )

    prozorro_context_review_table = _markdown_table(
        prozorro_context_review,
        [
            "waris_oblast",
            "official_vs_synthetic_index_gap",
            "baseline_gap_band",
            "tender_count",
            "total_expected_value",
            "procurement_review_priority_candidate",
            "procurement_candidate_band",
            "current_use",
            "prohibited_use",
            "production_score_change",
            "used_in_scoring",
            "used_in_monte_carlo",
            "recommended_action",
        ],
        max_rows=10,
    )

    prozorro_context_bridge_snapshot = _markdown_table(
        prozorro_context_bridge,
        [
            "waris_oblast",
            "official_grp_million_uah",
            "official_vs_synthetic_index_gap",
            "tender_count",
            "total_expected_value",
            "procurement_review_priority_candidate",
            "current_use",
            "prohibited_use",
            "production_score_change",
            "used_in_scoring",
            "used_in_monte_carlo",
        ],
        max_rows=10,
    )

    wartime_typology_context_review_table = _markdown_table(
        wartime_typology_context_review,
        [
            "typology_id",
            "typology_name",
            "typology_family",
            "waris_layer_candidates",
            "largest_gap_oblast",
            "largest_gap_value",
            "average_abs_gap",
            "current_use",
            "prohibited_use",
            "production_score_change",
            "used_in_scoring",
            "used_in_monte_carlo",
            "recommended_action",
        ],
        max_rows=10,
    )

    wartime_typology_context_bridge_snapshot = _markdown_table(
        wartime_typology_context_bridge,
        [
            "typology_id",
            "typology_name",
            "typology_family",
            "waris_layer_candidates",
            "largest_gap_oblast",
            "largest_gap_value",
            "average_abs_gap",
            "current_use",
            "prohibited_use",
            "production_score_change",
            "used_in_scoring",
            "used_in_monte_carlo",
        ],
        max_rows=10,
    )

    fiu_context_review_table = _markdown_table(
        fiu_context_review,
        [
            "typology_support_id",
            "typology_name",
            "typology_family",
            "waris_layer_candidates",
            "largest_gap_oblast",
            "largest_gap_value",
            "average_abs_gap",
            "current_use",
            "prohibited_use",
            "production_score_change",
            "used_in_scoring",
            "used_in_monte_carlo",
            "recommended_action",
        ],
        max_rows=10,
    )

    fiu_context_bridge_snapshot = _markdown_table(
        fiu_context_bridge,
        [
            "typology_support_id",
            "typology_name",
            "typology_family",
            "waris_layer_candidates",
            "largest_gap_oblast",
            "largest_gap_value",
            "average_abs_gap",
            "current_use",
            "prohibited_use",
            "production_score_change",
            "used_in_scoring",
            "used_in_monte_carlo",
        ],
        max_rows=10,
    )

    operational_controls_context_review_table = _markdown_table(
        operational_controls_context_review,
        [
            "operational_artifact_family",
            "artifact_status",
            "artifact_summary",
            "largest_gap_oblast",
            "largest_gap_value",
            "average_abs_gap",
            "current_use",
            "prohibited_use",
            "production_score_change",
            "used_in_scoring",
            "used_in_monte_carlo",
            "recommended_action",
        ],
        max_rows=10,
    )

    operational_controls_context_bridge_snapshot = _markdown_table(
        operational_controls_context_bridge,
        [
            "operational_artifact_family",
            "artifact_status",
            "artifact_summary",
            "largest_gap_oblast",
            "largest_gap_value",
            "average_abs_gap",
            "current_use",
            "prohibited_use",
            "production_score_change",
            "used_in_scoring",
            "used_in_monte_carlo",
        ],
        max_rows=10,
    )

    memo_lines = [
        "# WARIS Official Baseline Benchmark Review Memo",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Executive summary",
        "",
        "This memo records the current official-baseline evidence and readiness decision.",
        "Unavailable observations or unit evidence do not establish benchmark readiness.",
        "Official GRP remains **not approved for WARIS scoring**.",
        "",
        "Current readiness decision:",
        "",
        "```text",
        f"decision = {readiness['decision']}",
        f"approved_current_use = {readiness['approved_current_use']}",
        f"prohibited_current_use = {readiness['prohibited_current_use']}",
        f"recommended_current_posture = {scenario_context['recommended_current_posture']}",
        "```",
        "",
        "Current conclusion:",
        "",
        "```text",
        "Maintain benchmark_only posture.",
        "Do not use official GRP values in risk-layer calculation, composite scoring,",
        "risk-band assignment, review rationale generation, or Monte Carlo score simulation.",
        "Do not use expanded Prozorro procurement candidates in scoring without change control.",
        "Do not use analyst-review, false-positive, source-freshness, or run-manifest",
        "artifacts as scoring approval.",
        "```",
        "",
        "## Control assessment",
        "",
        control_assessment,
        "",
        "Expanded Prozorro context-review control assessment:",
        "",
        prozorro_control_assessment,
        "",
        "Wartime AML/CFT typology context-review control assessment:",
        "",
        wartime_typology_control_assessment,
        "",
        "Official FIU/SFMS context-review control assessment:",
        "",
        fiu_control_assessment,
        "",
        "Operational-controls context-review control assessment:",
        "",
        operational_controls_assessment,
        "",
        "## Official unit and scale evidence",
        "",
        "The current unit-evidence status is reported below. Missing evidence does not",
        "establish the unit interpretation or benchmark readiness.",
        "",
        "```text",
        f"indicator_name = {unit['indicator_name']}",
        f"nace_name = {unit['nace_name']}",
        f"frequency = {unit['freq_name']}",
        f"unit_interpretation = {unit['unit_interpretation']}",
        f"validation_status = {unit['validation_status']}",
        f"period_range = {unit['period_min']} to {unit['period_max']}",
        f"waris_region_count = {unit['waris_region_count']}",
        "```",
        "",
        "Source file:",
        "",
        "```text",
        unit["source_file"],
        "```",
        "",
        "## Benchmark gap findings",
        "",
        "The merge-review layer compared official Ukrstat GRP distribution against the",
        "current WARIS synthetic prewar revenue baseline.",
        "",
        "```text",
        f"oblasts_reviewed = {gap_context['row_count']}",
        f"average_absolute_index_gap = {gap_context['average_absolute_gap']}",
        f"largest_gap_oblast = {gap_context['largest_gap_oblast']}",
        f"largest_gap_value = {gap_context['largest_gap_value']}",
        f"very_large_or_large_gap_count = {gap_context['very_large_or_large_count']}",
        f"moderate_gap_count = {gap_context['moderate_count']}",
        f"small_or_minimal_gap_count = {gap_context['small_or_minimal_count']}",
        f"gap_distribution = {gap_context['gap_distribution']}",
        "```",
        "",
        "Interpretation:",
        "",
        "- Large gaps do **not** mean the official values should be inserted into scoring.",
        "- Large gaps indicate where the synthetic baseline may be least aligned with",
        "  official GRP scale.",
        "- These gaps should guide review, sensitivity testing, and SME discussion.",
        "- The current recommended posture remains `benchmark_only`.",
        "",
        "## Top official-vs-synthetic gaps",
        "",
        top_gap_table,
        "",
        "## Scenario recommendations",
        "",
        "The merge-review layer compares three controlled official-baseline scenarios",
        "and three review-only context bridges:",
        "",
        "```text",
        "benchmark_only",
        "rescale_revenue_baseline",
        "replace_oblast_baseline",
        "official_baseline_to_prozorro_context_bridge",
        "official_baseline_to_wartime_typology_context_bridge",
        "official_baseline_to_fiu_context_bridge",
        "official_baseline_to_operational_controls_context_bridge",
        "```",
        "",
        "Current scenario interpretation:",
        "",
        "```text",
        "benchmark_only = recommended current posture",
        f"rescale_revenue_baseline = {scenario_context['rescale_recommendation']}",
        f"replace_oblast_baseline = {scenario_context['replace_recommendation']}",
        f"official_baseline_to_prozorro_context_bridge = {scenario_context['prozorro_context_recommendation']}",
        f"official_baseline_to_wartime_typology_context_bridge = {scenario_context['wartime_typology_context_recommendation']}",
        f"official_baseline_to_fiu_context_bridge = {scenario_context['fiu_context_recommendation']}",
        f"official_baseline_to_operational_controls_context_bridge = {scenario_context['operational_controls_context_recommendation']}",
        "```",
        "",
        scenario_table,
        "",
        "## Merge-review summary",
        "",
        merge_summary_table,
        "",
        "## Merge-plan snapshot",
        "",
        merge_plan_table,
        "",
        "## Benchmark comparison snapshot",
        "",
        benchmark_snapshot,
        "",
        "## Official baseline to Prozorro context review",
        "",
        "The expanded Prozorro procurement context bridge compares official baseline",
        "benchmark context with review-only procurement feature candidates. It is not",
        "a scoring scenario and does not approve procurement scoring.",
        "",
        "```text",
        f"context_review_rows = {prozorro_context['row_count']}",
        f"top_procurement_context_oblast = {prozorro_context['top_oblast']}",
        f"top_procurement_context_score = {prozorro_context['top_score']}",
        f"procurement_context_band_distribution = {prozorro_context['band_distribution']}",
        f"current_use_values = {prozorro_context['current_use_values']}",
        f"prohibited_use_values = {prozorro_context['prohibited_use_values']}",
        f"production_score_change_values = {prozorro_context['production_score_change_values']}",
        f"used_in_scoring_values = {prozorro_context['used_in_scoring_values']}",
        f"used_in_monte_carlo_values = {prozorro_context['used_in_monte_carlo_values']}",
        "```",
        "",
        "Interpretation:",
        "",
        "- Expanded Prozorro procurement candidates are **not allegations**.",
        "- They do **not** approve buyer, supplier, oblast, or sector conclusions.",
        "- They are not used in risk-layer calculation, composite scoring, risk-band",
        "  assignment, review rationale generation, or Monte Carlo score simulation.",
        "- They can support source-lineage review, mapping review, and future SME",
        "  discussion before any governed scoring branch is considered.",
        "",
        "### Top official-baseline-to-Prozorro context-review rows",
        "",
        prozorro_context_review_table,
        "",
        "### Official-baseline-to-Prozorro context bridge snapshot",
        "",
        prozorro_context_bridge_snapshot,
        "",
        "## Official baseline to wartime AML/CFT typology context review",
        "",
        "The wartime AML/CFT typology context bridge compares official baseline",
        "benchmark context with literature-supported wartime AML/CFT typology themes.",
        "It is not a scoring scenario and does not approve typology scoring.",
        "",
        "```text",
        f"context_review_rows = {wartime_typology_context['row_count']}",
        f"top_typology_name = {wartime_typology_context['top_typology_name']}",
        f"top_typology_family = {wartime_typology_context['top_typology_family']}",
        f"typology_family_distribution = {wartime_typology_context['family_distribution']}",
        f"current_use_values = {wartime_typology_context['current_use_values']}",
        f"prohibited_use_values = {wartime_typology_context['prohibited_use_values']}",
        f"production_score_change_values = {wartime_typology_context['production_score_change_values']}",
        f"used_in_scoring_values = {wartime_typology_context['used_in_scoring_values']}",
        f"used_in_monte_carlo_values = {wartime_typology_context['used_in_monte_carlo_values']}",
        "```",
        "",
        "### Top official-baseline-to-wartime-typology context-review rows",
        "",
        wartime_typology_context_review_table,
        "",
        "### Official-baseline-to-wartime-typology context bridge snapshot",
        "",
        wartime_typology_context_bridge_snapshot,
        "",
        "## Official baseline to FIU/SFMS context review",
        "",
        "The official FIU/SFMS context bridge compares official baseline benchmark",
        "context with official national FIU/SFMS typology-support themes. It is not",
        "a scoring scenario and does not approve FIU-context scoring.",
        "",
        "```text",
        f"context_review_rows = {fiu_context['row_count']}",
        f"top_typology_name = {fiu_context['top_typology_name']}",
        f"top_typology_family = {fiu_context['top_typology_family']}",
        f"typology_family_distribution = {fiu_context['family_distribution']}",
        f"current_use_values = {fiu_context['current_use_values']}",
        f"prohibited_use_values = {fiu_context['prohibited_use_values']}",
        f"production_score_change_values = {fiu_context['production_score_change_values']}",
        f"used_in_scoring_values = {fiu_context['used_in_scoring_values']}",
        f"used_in_monte_carlo_values = {fiu_context['used_in_monte_carlo_values']}",
        "```",
        "",
        "### Top official-baseline-to-FIU/SFMS context-review rows",
        "",
        fiu_context_review_table,
        "",
        "### Official-baseline-to-FIU/SFMS context bridge snapshot",
        "",
        fiu_context_bridge_snapshot,
        "",
        "## Official baseline to operational controls context review",
        "",
        "The operational-controls context bridge checks whether the official baseline",
        "benchmark package is accompanied by analyst-review, false-positive,",
        "source-freshness, and run-manifest controls. It is not a scoring scenario",
        "and does not approve official-baseline scoring.",
        "",
        "```text",
        f"context_review_rows = {operational_controls_context['row_count']}",
        f"artifact_status_distribution = {operational_controls_context['artifact_status_distribution']}",
        f"artifact_family_distribution = {operational_controls_context['artifact_family_distribution']}",
        f"current_use_values = {operational_controls_context['current_use_values']}",
        f"production_score_change_values = {operational_controls_context['production_score_change_values']}",
        f"used_in_scoring_values = {operational_controls_context['used_in_scoring_values']}",
        f"used_in_monte_carlo_values = {operational_controls_context['used_in_monte_carlo_values']}",
        "```",
        "",
        "### Official-baseline-to-operational-controls context-review rows",
        "",
        operational_controls_context_review_table,
        "",
        "### Official-baseline-to-operational-controls context bridge snapshot",
        "",
        operational_controls_context_bridge_snapshot,
        "",
        "## Why official GRP, expanded Prozorro, wartime typology, FIU/SFMS context, and operational controls are not scoring-ready",
        "",
        "Official GRP is suitable for controlled benchmark integration, but several",
        "model-risk controls still block scoring integration:",
        "",
        "1. Transformation logic has not been approved.",
        "2. SME review has not been documented.",
        "3. Sector allocation logic is unresolved for sector/oblast scoring.",
        "4. Rescale effects have not been validated through sensitivity testing.",
        "5. Replace-oblast-baseline logic is not ready because official GRP is oblast-level,",
        "   while WARIS operates at sector/oblast level.",
        "6. Scoring change-control approval has not been created.",
        "7. Official GRP must not affect Monte Carlo score simulations until scoring use is",
        "   formally approved.",
        "8. Expanded Prozorro procurement features require broader coverage review,",
        "   buyer/address/oblast mapping validation, sector-mapping validation, supplier/",
        "   bid field validation, procurement/AML SME review, false-positive controls,",
        "   and model change-control approval before any scoring use.",
        "9. Operational-control artifacts document review safeguards, but they do not",
        "   approve scoring integration or validate model outputs.",
        "",
        "## Current recommendation",
        "",
        "Maintain the following posture:",
        "",
        "```text",
        "recommended_current_posture = benchmark_only",
        "approved_current_use = controlled_benchmark_integration_only",
        "prohibited_current_use = risk_layer_calculation_or_composite_scoring",
        "production_score_change = none",
        "expanded_prozorro_current_use = review_artifact_only",
        "expanded_prozorro_prohibited_use = direct_scoring_without_change_control",
        "expanded_prozorro_production_score_change = none",
        "wartime_aml_typology_current_use = literature_support_and_typology_reference_only",
        "wartime_aml_typology_prohibited_use = direct_scoring_without_change_control",
        "wartime_aml_typology_production_score_change = none",
        "fiu_context_current_use = official_fiu_context_and_typology_support_only",
        "fiu_context_prohibited_use = direct_scoring_without_change_control",
        "fiu_context_production_score_change = none",
        "analyst_review_current_use = analyst_review_workflow_only",
        "analyst_review_production_score_change = none",
        "false_positive_controls_current_use = human_review_support_only",
        "false_positive_controls_production_score_change = none",
        "source_freshness_current_use = source_freshness_monitoring_only",
        "source_freshness_production_score_change = none",
        "run_manifest_current_use = run_manifest_documentation",
        "run_manifest_production_score_change = none",
        "```",
        "",
        "## Recommended next actions",
        "",
        "1. Review the very_large_gap and large_gap oblasts in",
        "   `official_baseline_gap_review.csv`.",
        "2. Document whether each large gap reflects a synthetic-baseline issue, an official",
        "   data interpretation issue, or a harmless scaling difference.",
        "3. Keep `rescale_revenue_baseline` limited to sensitivity review.",
        "4. Keep `replace_oblast_baseline` out of scoring until sector allocation is",
        "   validated.",
        "5. Obtain AML / banking-supervision / Ukraine economic-security SME review.",
        "6. Create a model change-control record before any official GRP scoring branch.",
        "7. Continue reporting official GRP as benchmark context only.",
        "8. Review `official_baseline_prozorro_context_review.csv` for procurement",
        "   coverage, mapping quality, and false-positive controls.",
        "9. Keep expanded Prozorro procurement features as review-only candidates until",
        "   SME review and model change-control approval are documented.",
        "10. Review `official_baseline_operational_controls_context_review.csv` to",
        "    confirm analyst-review, false-positive, source-freshness, and run-manifest",
        "    safeguards are available before external presentation.",
        "",
        "## Governance note",
        "",
        "This memo is a controlled review artifact. It does not accuse any person,",
        "company, institution, sector, or region of misconduct. It does not change WARIS",
        "risk layers, composite scores, risk bands, review rationales, or Monte Carlo",
        "simulation outputs. Expanded Prozorro procurement candidates, wartime AML/CFT",
        "typology themes, official FIU/SFMS context artifacts, analyst-review outputs,",
        "false-positive controls, source-freshness outputs, and run-manifest artifacts",
        "are review/source-support/documentation artifacts and are not allegations or",
        "scoring inputs.",
        "",
        "WARIS remains a research prototype for AML/supervisory review prioritization and",
        "requires further validation before operational use.",
        "",
    ]

    memo = "\n".join(memo_lines)

    MEMO_OUTPUT_PATH.write_text(memo, encoding="utf-8")
    return memo


def build_official_baseline_review_memo_artifacts() -> dict[str, str]:
    """Build official baseline benchmark review memo artifacts."""
    memo = build_benchmark_review_memo()

    return {
        "memo_path": str(MEMO_OUTPUT_PATH),
        "memo_text": memo,
    }


def main() -> None:
    """CLI entry point."""
    artifacts = build_official_baseline_review_memo_artifacts()

    readiness = _readiness_context()
    gap_review = _safe_read_csv(OFFICIAL_BASELINE_GAP_REVIEW_TABLE)
    scenario_recommendations = _safe_read_csv(
        OFFICIAL_BASELINE_SCENARIO_RECOMMENDATIONS_TABLE
    )

    prozorro_context_review = _safe_read_csv(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE)
    wartime_typology_context_review = _safe_read_csv(
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE
    )
    fiu_context_review = _safe_read_csv(OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE)
    operational_controls_context_review = _safe_read_csv(
        OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE
    )

    gap_context = _gap_review_context(gap_review)
    scenario_context = _scenario_context(scenario_recommendations)
    prozorro_context = _prozorro_context_review_context(prozorro_context_review)
    wartime_typology_context = _source_context_review_context(
        wartime_typology_context_review
    )
    fiu_context = _source_context_review_context(fiu_context_review)
    operational_controls_context = _operational_controls_context_review_context(
        operational_controls_context_review
    )

    print("\nOfficial baseline benchmark review memo created.")
    print(f"- Memo: {artifacts['memo_path']}")
    print(f"- Readiness decision: {readiness['decision']}")
    print(f"- Approved current use: {readiness['approved_current_use']}")
    print(f"- Prohibited current use: {readiness['prohibited_current_use']}")
    print(
        f"- Recommended current posture: "
        f"{scenario_context['recommended_current_posture']}"
    )
    print(f"- Oblasts reviewed: {gap_context['row_count']}")
    print(f"- Average absolute index gap: {gap_context['average_absolute_gap']}")
    print(
        f"- Largest official-vs-synthetic gap: "
        f"{gap_context['largest_gap_oblast']} "
        f"({gap_context['largest_gap_value']})"
    )
    print(f"- Gap distribution: {gap_context['gap_distribution']}")
    print(f"- Prozorro context-review rows: {prozorro_context['row_count']}")
    print(
        "- Top Prozorro context candidate: "
        f"{prozorro_context['top_oblast']} ({prozorro_context['top_score']})"
    )
    print(
        "- Wartime AML typology context-review rows: "
        f"{wartime_typology_context['row_count']}"
    )
    print(
        "- FIU/SFMS context-review rows: "
        f"{fiu_context['row_count']}"
    )
    print(
        "- Operational-controls context-review rows: "
        f"{operational_controls_context['row_count']}"
    )
    print(
        "\nImportant: This memo is a review artifact only. Expanded Prozorro "
        "procurement features, wartime AML/CFT typology artifacts, official "
        "FIU/SFMS context artifacts, and operational-control artifacts remain "
        "review/source-support/documentation artifacts. This "
        "memo does not alter WARIS risk layers, composite scores, risk bands, or "
        "Monte Carlo simulations."
    )


if __name__ == "__main__":
    main()
