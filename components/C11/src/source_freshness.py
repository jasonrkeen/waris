from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import RAW_DIR, REPORT_DIR, TABLE_DIR
from .utils import ensure_dirs, safe_read_csv, safe_write_csv


SOURCE_FRESHNESS_INVENTORY_TABLE = TABLE_DIR / "source_freshness_inventory.csv"
SOURCE_FRESHNESS_ASSESSMENT_TABLE = TABLE_DIR / "source_freshness_assessment.csv"
SOURCE_FRESHNESS_REPLACEMENT_PRIORITIES_TABLE = TABLE_DIR / "source_freshness_replacement_priorities.csv"
SOURCE_FRESHNESS_SUMMARY_TABLE = TABLE_DIR / "source_freshness_summary.csv"


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


EXPECTED_SOURCE_ARTIFACTS = [
    {
        "source_family": "waris_scoring_outputs",
        "artifact_name": "WARIS scored oblast-sector table",
        "path": TABLE_DIR / "waris_scored_oblast_sector.csv",
        "expected_use": "risk_layer_output",
        "current_use": "scoring_output",
        "scoring_dependency": True,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "monte_carlo",
        "artifact_name": "WARIS Monte Carlo robustness results",
        "path": TABLE_DIR / "waris_monte_carlo_results.csv",
        "expected_use": "robustness_output",
        "current_use": "uncertainty_output",
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "analyst_review",
        "artifact_name": "Analyst review queue",
        "path": TABLE_DIR / "analyst_review_queue.csv",
        "expected_use": "human_review_workflow",
        "current_use": ANALYST_REVIEW_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "false_positive_controls",
        "artifact_name": "False-positive controls",
        "path": TABLE_DIR / "false_positive_controls.csv",
        "expected_use": "human_review_control",
        "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 90,
    },
    {
        "source_family": "analyst_review",
        "artifact_name": "Analyst review questions",
        "path": TABLE_DIR / "analyst_review_questions.csv",
        "expected_use": "human_review_workflow",
        "current_use": ANALYST_REVIEW_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "analyst_review",
        "artifact_name": "Review disposition template",
        "path": TABLE_DIR / "review_disposition_template.csv",
        "expected_use": "human_review_workflow",
        "current_use": ANALYST_REVIEW_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "analyst_review",
        "artifact_name": "Analyst review summary",
        "path": TABLE_DIR / "analyst_review_summary.csv",
        "expected_use": "human_review_workflow_summary",
        "current_use": ANALYST_REVIEW_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "false_positive_controls",
        "artifact_name": "False-positive risk register",
        "path": TABLE_DIR / "false_positive_risk_register.csv",
        "expected_use": "human_review_control",
        "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 90,
    },
    {
        "source_family": "false_positive_controls",
        "artifact_name": "False-positive review checklist",
        "path": TABLE_DIR / "false_positive_review_checklist.csv",
        "expected_use": "human_review_control",
        "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 90,
    },
    {
        "source_family": "false_positive_controls",
        "artifact_name": "False-positive summary",
        "path": TABLE_DIR / "false_positive_summary.csv",
        "expected_use": "human_review_control_summary",
        "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 90,
    },
    {
        "source_family": "official_baseline_operational_controls",
        "artifact_name": "Official baseline to operational controls context bridge",
        "path": TABLE_DIR / "official_baseline_operational_controls_context_bridge.csv",
        "expected_use": "operational_control_context_bridge",
        "current_use": "context_review_only",
        "scoring_dependency": False,
        "freshness_expectation_days": 90,
    },
    {
        "source_family": "official_baseline_operational_controls",
        "artifact_name": "Official baseline to operational controls context review",
        "path": TABLE_DIR / "official_baseline_operational_controls_context_review.csv",
        "expected_use": "operational_control_context_review",
        "current_use": "context_review_only",
        "scoring_dependency": False,
        "freshness_expectation_days": 90,
    },
    {
        "source_family": "live_status",
        "artifact_name": "Live/source status table",
        "path": TABLE_DIR / "live_data_status.csv",
        "expected_use": "source_status_monitoring",
        "current_use": "source_status_documentation",
        "scoring_dependency": False,
        "freshness_expectation_days": 7,
    },
    {
        "source_family": "prozorro",
        "artifact_name": "Prozorro expanded tender list",
        "path": RAW_DIR / "prozorro_expanded_tenders_raw.csv",
        "expected_use": "procurement_context",
        "current_use": "review_artifact_only",
        "scoring_dependency": False,
        "freshness_expectation_days": 14,
    },
    {
        "source_family": "prozorro",
        "artifact_name": "Prozorro procurement scoring candidates",
        "path": TABLE_DIR / "prozorro_procurement_scoring_candidates.csv",
        "expected_use": "procurement_review_candidates",
        "current_use": "review_artifact_only",
        "scoring_dependency": False,
        "freshness_expectation_days": 14,
    },
    {
        "source_family": "ukrstat_official_baseline",
        "artifact_name": "Ukrstat all-oblast baseline candidates",
        "path": TABLE_DIR / "ukrstat_oblast_baseline_candidates.csv",
        "expected_use": "official_benchmark_candidate",
        "current_use": "controlled_benchmark_integration_only",
        "scoring_dependency": False,
        "freshness_expectation_days": 365,
    },
    {
        "source_family": "official_baseline_validation",
        "artifact_name": "Official baseline readiness decision",
        "path": TABLE_DIR / "official_baseline_readiness_decision.csv",
        "expected_use": "validation_gate",
        "current_use": "controlled_benchmark_integration_only",
        "scoring_dependency": False,
        "freshness_expectation_days": 90,
    },
    {
        "source_family": "official_baseline_review",
        "artifact_name": "Official baseline merge-review summary",
        "path": TABLE_DIR / "official_baseline_merge_review_summary.csv",
        "expected_use": "benchmark_review",
        "current_use": "benchmark_only",
        "scoring_dependency": False,
        "freshness_expectation_days": 90,
    },
    {
        "source_family": "wartime_aml_typology",
        "artifact_name": "Wartime AML/CFT typology register",
        "path": TABLE_DIR / "waris_wartime_aml_typology_register.csv",
        "expected_use": "literature_support",
        "current_use": "literature_support_and_typology_reference_only",
        "scoring_dependency": False,
        "freshness_expectation_days": 180,
    },
    {
        "source_family": "fiu_sfms_context",
        "artifact_name": "FIU/SFMS context summary",
        "path": TABLE_DIR / "waris_fiu_context_summary.csv",
        "expected_use": "official_source_context",
        "current_use": "official_fiu_context_and_typology_support_only",
        "scoring_dependency": False,
        "freshness_expectation_days": 180,
    },
    {
        "source_family": "source_confidence",
        "artifact_name": "Source confidence summary",
        "path": TABLE_DIR / "source_confidence_summary.csv",
        "expected_use": "field_lineage_and_confidence",
        "current_use": "source_confidence_documentation",
        "scoring_dependency": False,
        "freshness_expectation_days": 90,
    },
    {
        "source_family": "model_governance",
        "artifact_name": "Model governance summary",
        "path": TABLE_DIR / "model_governance_summary.csv",
        "expected_use": "governance_documentation",
        "current_use": "model_governance_documentation",
        "scoring_dependency": False,
        "freshness_expectation_days": 90,
    },
    {
        "source_family": "source_freshness",
        "artifact_name": "Source freshness inventory",
        "path": SOURCE_FRESHNESS_INVENTORY_TABLE,
        "expected_use": "source_freshness_inventory",
        "current_use": SOURCE_FRESHNESS_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "source_freshness",
        "artifact_name": "Source freshness assessment",
        "path": SOURCE_FRESHNESS_ASSESSMENT_TABLE,
        "expected_use": "source_freshness_assessment",
        "current_use": SOURCE_FRESHNESS_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "source_freshness",
        "artifact_name": "Source freshness replacement priorities",
        "path": SOURCE_FRESHNESS_REPLACEMENT_PRIORITIES_TABLE,
        "expected_use": "source_freshness_replacement_priorities",
        "current_use": SOURCE_FRESHNESS_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "run_manifest",
        "artifact_name": "Run manifest summary",
        "path": TABLE_DIR / "run_manifest_summary.csv",
        "expected_use": "reproducibility_metadata",
        "current_use": RUN_MANIFEST_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "run_manifest",
        "artifact_name": "Run manifest inventory",
        "path": TABLE_DIR / "run_manifest.csv",
        "expected_use": "reproducibility_inventory",
        "current_use": RUN_MANIFEST_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
    {
        "source_family": "run_manifest",
        "artifact_name": "Run manifest JSON",
        "path": REPORT_DIR / "run_manifest.json",
        "expected_use": "reproducibility_metadata",
        "current_use": RUN_MANIFEST_CURRENT_USE,
        "scoring_dependency": False,
        "freshness_expectation_days": 30,
    },
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().replace(microsecond=0).isoformat()


def _safe_read(path: Path) -> pd.DataFrame | None:
    return safe_read_csv(path)


def _row_count(path: Path) -> int:
    df = _safe_read(path)
    if df is None:
        return 0
    return int(len(df))


def _modified_at(path: Path) -> datetime | None:
    if not path.exists():
        return None

    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _age_days(path: Path) -> float | None:
    modified = _modified_at(path)
    if modified is None:
        return None

    delta = _utc_now() - modified
    return round(delta.total_seconds() / 86400, 4)


def _freshness_status(
    exists: bool,
    row_count: int,
    age_days: float | None,
    expectation_days: int,
) -> str:
    if not exists:
        return "missing"

    if row_count <= 0:
        return "empty"

    if age_days is None:
        return "unknown"

    if age_days <= expectation_days:
        return "fresh"

    if age_days <= expectation_days * 2:
        return "aging"

    return "stale"


def _refresh_priority(
    status: str,
    source_family: str,
    scoring_dependency: bool,
    current_use: str,
) -> str:
    if status in {"missing", "empty"} and scoring_dependency:
        return "priority_1_required_for_pipeline"

    if status in {"missing", "empty"}:
        return "priority_2_restore_context_artifact"

    if status == "stale" and scoring_dependency:
        return "priority_1_refresh_scoring_dependency"

    if status == "stale":
        return "priority_3_refresh_source_context"

    if status == "aging":
        return "priority_4_monitor_refresh_window"

    if (
        "review_artifact_only" in current_use
        or "context" in current_use
        or "workflow" in current_use
        or "support" in current_use
        or "freshness" in current_use
        or "manifest" in current_use
    ):
        return "priority_5_context_current"

    return "priority_6_no_action_current"


def _recommended_action(
    status: str,
    artifact_name: str,
    current_use: str,
    scoring_dependency: bool,
) -> str:
    if status == "missing":
        return f"Regenerate {artifact_name}; keep current_use={current_use} and production_score_change=none."
    if status == "empty":
        return f"Inspect source collection and regenerate {artifact_name}; do not infer risk from empty artifacts."
    if status == "stale":
        return f"Refresh {artifact_name} before relying on it for current reporting or review prioritization."
    if status == "aging":
        return f"Monitor {artifact_name}; refresh soon if preparing a published report or external review."
    if scoring_dependency:
        return f"{artifact_name} is available for the current prototype run; continue documenting source and fallback limitations."
    return f"{artifact_name} is current for its documented non-scoring use."


def _build_inventory() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for item in EXPECTED_SOURCE_ARTIFACTS:
        path = Path(item["path"])
        exists = path.exists()
        modified = _modified_at(path)
        rows.append(
            {
                "source_family": item["source_family"],
                "artifact_name": item["artifact_name"],
                "artifact_path": str(path),
                "artifact_exists": exists,
                "row_count": _row_count(path) if exists else 0,
                "modified_at_utc": "" if modified is None else modified.replace(microsecond=0).isoformat(),
                "age_days": _age_days(path),
                "freshness_expectation_days": item["freshness_expectation_days"],
                "expected_use": item["expected_use"],
                "current_use": item["current_use"],
                "scoring_dependency": item["scoring_dependency"],
                "production_score_change": (
                    ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE
                    if item["source_family"] == "analyst_review"
                    else FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE
                    if item["source_family"] == "false_positive_controls"
                    else SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE
                    if item["source_family"] == "source_freshness"
                    else RUN_MANIFEST_PRODUCTION_SCORE_CHANGE
                    if item["source_family"] == "run_manifest"
                    else "none"
                ),
                "generated_at_utc": _utc_now_iso(),
            }
        )

    return pd.DataFrame(rows)


def _build_assessment(inventory: pd.DataFrame) -> pd.DataFrame:
    assessment = inventory.copy()

    assessment["freshness_status"] = assessment.apply(
        lambda row: _freshness_status(
            exists=bool(row.get("artifact_exists", False)),
            row_count=int(row.get("row_count", 0)),
            age_days=row.get("age_days"),
            expectation_days=int(row.get("freshness_expectation_days", 30)),
        ),
        axis=1,
    )

    assessment["refresh_priority"] = assessment.apply(
        lambda row: _refresh_priority(
            status=str(row.get("freshness_status", "unknown")),
            source_family=str(row.get("source_family", "")),
            scoring_dependency=bool(row.get("scoring_dependency", False)),
            current_use=str(row.get("current_use", "")),
        ),
        axis=1,
    )

    assessment["recommended_action"] = assessment.apply(
        lambda row: _recommended_action(
            status=str(row.get("freshness_status", "unknown")),
            artifact_name=str(row.get("artifact_name", "")),
            current_use=str(row.get("current_use", "")),
            scoring_dependency=bool(row.get("scoring_dependency", False)),
        ),
        axis=1,
    )

    assessment["human_review_required"] = True
    assessment["automated_adverse_action_allowed"] = False
    assessment["entity_level_findings_allowed"] = False
    assessment["current_use_control"] = "source_freshness_monitoring_only"

    return assessment


def _build_replacement_priorities(assessment: pd.DataFrame) -> pd.DataFrame:
    if assessment.empty:
        return pd.DataFrame(
            [
                {
                    "priority_rank": 1,
                    "source_family": "not_available",
                    "artifact_name": "not_available",
                    "refresh_priority": "not_available",
                    "recommended_action": "Run the pipeline before source-freshness assessment.",
                    "production_score_change": "none",
                }
            ]
        )

    priority_order = {
        "priority_1_required_for_pipeline": 1,
        "priority_1_refresh_scoring_dependency": 1,
        "priority_2_restore_context_artifact": 2,
        "priority_3_refresh_source_context": 3,
        "priority_4_monitor_refresh_window": 4,
        "priority_5_context_current": 5,
        "priority_6_no_action_current": 6,
    }

    priorities = assessment.copy()
    priorities["priority_sort"] = priorities["refresh_priority"].map(priority_order).fillna(99)
    priorities = priorities.sort_values(
        ["priority_sort", "source_family", "artifact_name"],
        ascending=[True, True, True],
    ).copy()
    priorities["priority_rank"] = range(1, len(priorities) + 1)

    keep_cols = [
        "priority_rank",
        "source_family",
        "artifact_name",
        "freshness_status",
        "refresh_priority",
        "artifact_exists",
        "row_count",
        "age_days",
        "freshness_expectation_days",
        "current_use",
        "scoring_dependency",
        "recommended_action",
        "production_score_change",
        "human_review_required",
        "automated_adverse_action_allowed",
        "entity_level_findings_allowed",
    ]

    return priorities[keep_cols].copy()


def _build_summary(inventory: pd.DataFrame, assessment: pd.DataFrame) -> pd.DataFrame:
    status_counts = (
        assessment["freshness_status"].value_counts().to_dict()
        if "freshness_status" in assessment.columns
        else {}
    )
    priority_counts = (
        assessment["refresh_priority"].value_counts().to_dict()
        if "refresh_priority" in assessment.columns
        else {}
    )

    missing_count = int((assessment.get("freshness_status") == "missing").sum()) if not assessment.empty else 0
    stale_count = int((assessment.get("freshness_status") == "stale").sum()) if not assessment.empty else 0
    empty_count = int((assessment.get("freshness_status") == "empty").sum()) if not assessment.empty else 0

    if missing_count or stale_count or empty_count:
        overall_status = "review_required"
        next_action = "Review missing, empty, or stale artifacts before external reporting or model-change discussion."
    else:
        overall_status = "current_for_documented_use"
        next_action = "Continue routine refresh monitoring and preserve non-scoring controls."

    rows = [
        {
            "summary_area": "Source freshness inventory",
            "status": "created",
            "value": len(inventory),
            "recommended_next_action": "Use inventory to document artifact availability, row counts, and age.",
        },
        {
            "summary_area": "Freshness status counts",
            "status": "computed",
            "value": status_counts,
            "recommended_next_action": "Investigate missing, empty, aging, or stale source families.",
        },
        {
            "summary_area": "Refresh priority counts",
            "status": "computed",
            "value": priority_counts,
            "recommended_next_action": "Use replacement priorities to plan source refresh or collection improvements.",
        },
        {
            "summary_area": "Overall freshness posture",
            "status": overall_status,
            "value": {
                "missing": missing_count,
                "empty": empty_count,
                "stale": stale_count,
            },
            "recommended_next_action": next_action,
        },
        {
            "summary_area": "Production score change control",
            "status": "control_active",
            "value": "none",
            "recommended_next_action": "Source-freshness monitoring does not alter WARIS scores, risk bands, or Monte Carlo outputs.",
        },
        {
            "summary_area": "Use limitation",
            "status": "control_active",
            "value": SOURCE_FRESHNESS_CURRENT_USE,
            "recommended_next_action": "Use freshness outputs for documentation, refresh planning, and source-confidence review only.",
        },
        {
            "summary_area": "Operational control coverage",
            "status": "computed",
            "value": {
                "analyst_review": int((assessment["source_family"] == "analyst_review").sum())
                if "source_family" in assessment.columns
                else 0,
                "false_positive_controls": int((assessment["source_family"] == "false_positive_controls").sum())
                if "source_family" in assessment.columns
                else 0,
                "source_freshness": int((assessment["source_family"] == "source_freshness").sum())
                if "source_family" in assessment.columns
                else 0,
                "run_manifest": int((assessment["source_family"] == "run_manifest").sum())
                if "source_family" in assessment.columns
                else 0,
                "operational_controls_bridge_review": int((assessment["source_family"] == "official_baseline_operational_controls").sum())
                if "source_family" in assessment.columns
                else 0,
            },
            "recommended_next_action": (
                "Confirm analyst-review, false-positive, source-freshness, run-manifest, "
                "and operational-controls bridge/review artifacts remain documentation "
                "and human-review support only."
            ),
        },
        {
            "summary_area": "Operational controls production score change",
            "status": "control_active",
            "value": {
                "analyst_review": ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
                "false_positive_controls": FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
                "source_freshness": SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
                "run_manifest": RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
            },
            "recommended_next_action": (
                "Maintain production_score_change=none for all operational-control "
                "artifacts unless a formal governed model-change record is approved."
            ),
        },
    ]

    return pd.DataFrame(rows)


def build_source_freshness_artifacts() -> dict[str, Any]:
    """Build source freshness and refresh-priority artifacts.

    These artifacts document whether major WARIS input/output/context and
    operational-control artifacts are present, populated, and recent enough for
    their documented use. They do
    not alter risk-layer calculations, composite scores, risk bands, analyst
    disposition fields, or Monte Carlo outputs.
    """
    ensure_dirs([TABLE_DIR, REPORT_DIR, RAW_DIR])

    inventory = _build_inventory()
    assessment = _build_assessment(inventory)
    priorities = _build_replacement_priorities(assessment)
    summary = _build_summary(inventory, assessment)

    safe_write_csv(inventory, SOURCE_FRESHNESS_INVENTORY_TABLE)
    safe_write_csv(assessment, SOURCE_FRESHNESS_ASSESSMENT_TABLE)
    safe_write_csv(priorities, SOURCE_FRESHNESS_REPLACEMENT_PRIORITIES_TABLE)
    safe_write_csv(summary, SOURCE_FRESHNESS_SUMMARY_TABLE)

    return {
        "source_freshness_inventory": inventory,
        "source_freshness_assessment": assessment,
        "source_freshness_replacement_priorities": priorities,
        "source_freshness_summary": summary,
        "source_freshness_inventory_path": SOURCE_FRESHNESS_INVENTORY_TABLE,
        "source_freshness_assessment_path": SOURCE_FRESHNESS_ASSESSMENT_TABLE,
        "source_freshness_replacement_priorities_path": SOURCE_FRESHNESS_REPLACEMENT_PRIORITIES_TABLE,
        "source_freshness_summary_path": SOURCE_FRESHNESS_SUMMARY_TABLE,
    }


def main() -> None:
    artifacts = build_source_freshness_artifacts()

    print("WARIS source freshness artifacts created:")
    print(f"- Source freshness inventory: {artifacts['source_freshness_inventory_path']}")
    print(f"- Source freshness assessment: {artifacts['source_freshness_assessment_path']}")
    print(f"- Source freshness replacement priorities: {artifacts['source_freshness_replacement_priorities_path']}")
    print(f"- Source freshness summary: {artifacts['source_freshness_summary_path']}")


if __name__ == "__main__":
    main()
