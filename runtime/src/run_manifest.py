from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import (
    BASE_DIR,
    MODEL_VERSION,
    ACQUISITION_POLICY_VERSION,
    OUTPUT_DIR,
    REPORT_DIR,
    TABLE_DIR,
)
from .utils import ensure_dirs, safe_read_csv, safe_write_csv
from .provenance import RunContext, artifact_snapshot, new_run_id, seal_run


RUN_MANIFEST_TABLE = TABLE_DIR / "run_manifest.csv"
RUN_MANIFEST_JSON = REPORT_DIR / "run_manifest.json"
RUN_MANIFEST_SUMMARY_TABLE = TABLE_DIR / "run_manifest_summary.csv"


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


def _utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp for the current run."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_len(path: Path) -> int:
    """Return CSV row count for an optional artifact."""
    df = safe_read_csv(path)
    return 0 if df is None else len(df)


def _artifact_exists(path: Path) -> bool:
    """Return True when an output artifact exists and has content."""
    try:
        return path.exists() and path.stat().st_size > 0
    except Exception:
        return False


def _safe_file_size(path: Path) -> int:
    """Return file size in bytes or zero if unavailable."""
    try:
        if not path.exists():
            return 0
        return int(path.stat().st_size)
    except Exception:
        return 0


def _read_first_value(
    path: Path,
    column: str,
    fallback: str = "not_available",
) -> str:
    """Read the first non-empty value from a CSV column."""
    df = safe_read_csv(path)

    if df is None or df.empty or column not in df.columns:
        return fallback

    values = (
        df[column]
        .dropna()
        .astype(str)
        .map(str.strip)
        .loc[lambda s: s.ne("")]
        .tolist()
    )

    if not values:
        return fallback

    return values[0]


def _unique_values(
    path: Path,
    column: str,
    fallback: str = "not_available",
    max_items: int = 8,
) -> str:
    """Return compact semicolon-separated unique values from a CSV column."""
    df = safe_read_csv(path)

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


def _summary_value_for_area(
    path: Path,
    summary_area: str,
    value_column: str = "value",
    fallback: str = "not_available",
) -> str:
    """Return a value from a standard summary table."""
    df = safe_read_csv(path)

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


def _git_commit_hash() -> str:
    """Return current git commit hash when available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except Exception:
        return "not_available"

    if result.returncode != 0:
        return "not_available"

    value = result.stdout.strip()
    return value or "not_available"


def _git_dirty_status() -> str:
    """Return a compact git working-tree status."""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except Exception:
        return "not_available"

    if result.returncode != 0:
        return "not_available"

    return "dirty" if result.stdout.strip() else "clean"


def _load_live_source_counts() -> dict[str, Any]:
    """Summarize live/source status rows if available."""
    live_status_path = TABLE_DIR / "live_data_status.csv"
    live = safe_read_csv(live_status_path)

    if live is None or live.empty:
        return {
            "live_status_rows": 0,
            "live_sources_count": 0,
            "fallback_sources_count": 0,
            "artifact_sources_count": 0,
            "benchmark_artifact_sources_count": 0,
            "source_status_values": "not_available",
        }

    status_col = "status" if "status" in live.columns else None

    if status_col is None:
        return {
            "live_status_rows": len(live),
            "live_sources_count": 0,
            "fallback_sources_count": 0,
            "artifact_sources_count": 0,
            "benchmark_artifact_sources_count": 0,
            "source_status_values": "status_column_missing",
        }

    statuses = live[status_col].fillna("unknown").astype(str).str.lower().str.strip()

    return {
        "live_status_rows": len(live),
        "live_sources_count": int(statuses.eq("live").sum()),
        "fallback_sources_count": int(statuses.eq("fallback").sum()),
        "artifact_sources_count": int(statuses.eq("artifact").sum()),
        "benchmark_artifact_sources_count": int(statuses.eq("benchmark artifact").sum()),
        "source_status_values": "; ".join(sorted(statuses.drop_duplicates().tolist())),
    }


def _legacy_artifact_inventory_rows() -> list[dict[str, Any]]:
    """Build a compact artifact inventory for the run manifest."""
    artifacts = [
        {
            "artifact_group": "Core model outputs",
            "artifact_name": "WARIS scored oblast-sector table",
            "path": TABLE_DIR / "waris_scored_oblast_sector.csv",
            "artifact_type": "table",
            "current_use": "review_prioritization_output",
            "used_in_waris_scoring": True,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Core model outputs",
            "artifact_name": "WARIS oblast summary",
            "path": TABLE_DIR / "waris_oblast_summary.csv",
            "artifact_type": "table",
            "current_use": "summary_output",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Core model outputs",
            "artifact_name": "WARIS sector summary",
            "path": TABLE_DIR / "waris_sector_summary.csv",
            "artifact_type": "table",
            "current_use": "summary_output",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Monte Carlo",
            "artifact_name": "WARIS Monte Carlo results",
            "path": TABLE_DIR / "waris_monte_carlo_results.csv",
            "artifact_type": "table",
            "current_use": "robustness_review",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": True,
        },
        {
            "artifact_group": "Official baseline",
            "artifact_name": "Official baseline readiness decision",
            "path": TABLE_DIR / "official_baseline_readiness_decision.csv",
            "artifact_type": "table",
            "current_use": "controlled_benchmark_integration_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Official baseline",
            "artifact_name": "Official baseline merge-review summary",
            "path": TABLE_DIR / "official_baseline_merge_review_summary.csv",
            "artifact_type": "table",
            "current_use": "benchmark_review_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Prozorro",
            "artifact_name": "Prozorro procurement scoring candidates",
            "path": TABLE_DIR / "prozorro_procurement_scoring_candidates.csv",
            "artifact_type": "table",
            "current_use": "review_artifact_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Wartime typology",
            "artifact_name": "Wartime AML/CFT typology register",
            "path": TABLE_DIR / "waris_wartime_aml_typology_register.csv",
            "artifact_type": "table",
            "current_use": "literature_support_and_typology_reference_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "FIU/SFMS",
            "artifact_name": "FIU/SFMS context summary",
            "path": TABLE_DIR / "waris_fiu_context_summary.csv",
            "artifact_type": "table",
            "current_use": "official_fiu_context_and_typology_support_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Context bridges",
            "artifact_name": "Official baseline to Prozorro context review",
            "path": TABLE_DIR / "official_baseline_prozorro_context_review.csv",
            "artifact_type": "table",
            "current_use": "review_context_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Context bridges",
            "artifact_name": "Official baseline to wartime typology context review",
            "path": TABLE_DIR / "official_baseline_wartime_typology_context_review.csv",
            "artifact_type": "table",
            "current_use": "review_context_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Context bridges",
            "artifact_name": "Official baseline to FIU/SFMS context review",
            "path": TABLE_DIR / "official_baseline_fiu_context_review.csv",
            "artifact_type": "table",
            "current_use": "review_context_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Context bridges",
            "artifact_name": "Official baseline to operational controls context bridge",
            "path": TABLE_DIR / "official_baseline_operational_controls_context_bridge.csv",
            "artifact_type": "table",
            "current_use": "context_review_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Context bridges",
            "artifact_name": "Official baseline to operational controls context review",
            "path": TABLE_DIR / "official_baseline_operational_controls_context_review.csv",
            "artifact_type": "table",
            "current_use": "context_review_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Analyst review",
            "artifact_name": "Analyst review queue",
            "path": TABLE_DIR / "analyst_review_queue.csv",
            "artifact_type": "table",
            "current_use": ANALYST_REVIEW_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Analyst review",
            "artifact_name": "Analyst review questions",
            "path": TABLE_DIR / "analyst_review_questions.csv",
            "artifact_type": "table",
            "current_use": ANALYST_REVIEW_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Analyst review",
            "artifact_name": "Review disposition template",
            "path": TABLE_DIR / "review_disposition_template.csv",
            "artifact_type": "table",
            "current_use": ANALYST_REVIEW_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Analyst review",
            "artifact_name": "Analyst review summary",
            "path": TABLE_DIR / "analyst_review_summary.csv",
            "artifact_type": "table",
            "current_use": ANALYST_REVIEW_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "False-positive controls",
            "artifact_name": "False-positive risk register",
            "path": TABLE_DIR / "false_positive_risk_register.csv",
            "artifact_type": "table",
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "False-positive controls",
            "artifact_name": "False-positive controls",
            "path": TABLE_DIR / "false_positive_controls.csv",
            "artifact_type": "table",
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "False-positive controls",
            "artifact_name": "False-positive review checklist",
            "path": TABLE_DIR / "false_positive_review_checklist.csv",
            "artifact_type": "table",
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "False-positive controls",
            "artifact_name": "False-positive summary",
            "path": TABLE_DIR / "false_positive_summary.csv",
            "artifact_type": "table",
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Operational controls",
            "artifact_name": "Operational review artifact crosswalk",
            "path": TABLE_DIR / "operational_review_artifact_crosswalk.csv",
            "artifact_type": "table",
            "current_use": "operational_control_documentation_only",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Source freshness",
            "artifact_name": "Source freshness inventory",
            "path": TABLE_DIR / "source_freshness_inventory.csv",
            "artifact_type": "table",
            "current_use": SOURCE_FRESHNESS_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Source freshness",
            "artifact_name": "Source freshness assessment",
            "path": TABLE_DIR / "source_freshness_assessment.csv",
            "artifact_type": "table",
            "current_use": SOURCE_FRESHNESS_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Source freshness",
            "artifact_name": "Source freshness replacement priorities",
            "path": TABLE_DIR / "source_freshness_replacement_priorities.csv",
            "artifact_type": "table",
            "current_use": SOURCE_FRESHNESS_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Source freshness",
            "artifact_name": "Source freshness summary",
            "path": TABLE_DIR / "source_freshness_summary.csv",
            "artifact_type": "table",
            "current_use": SOURCE_FRESHNESS_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Governance",
            "artifact_name": "Model governance summary",
            "path": TABLE_DIR / "model_governance_summary.csv",
            "artifact_type": "table",
            "current_use": "governance_documentation",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Source confidence",
            "artifact_name": "Source confidence summary",
            "path": TABLE_DIR / "source_confidence_summary.csv",
            "artifact_type": "table",
            "current_use": "source_lineage_documentation",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Report",
            "artifact_name": "WARIS PDF report",
            "path": REPORT_DIR / "waris_ukraine_aml_risk_report.pdf",
            "artifact_type": "pdf",
            "current_use": "report_output",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Report",
            "artifact_name": "Official baseline benchmark review memo",
            "path": REPORT_DIR / "official_baseline_benchmark_review_memo.md",
            "artifact_type": "markdown",
            "current_use": "benchmark_review_documentation",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Run manifest",
            "artifact_name": "Run manifest summary",
            "path": RUN_MANIFEST_SUMMARY_TABLE,
            "artifact_type": "table",
            "current_use": RUN_MANIFEST_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
        {
            "artifact_group": "Run manifest",
            "artifact_name": "Run manifest JSON",
            "path": RUN_MANIFEST_JSON,
            "artifact_type": "json",
            "current_use": RUN_MANIFEST_CURRENT_USE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
        },
    ]

    rows: list[dict[str, Any]] = []

    for artifact in artifacts:
        path = Path(artifact["path"])
        rows.append(
            {
                "artifact_group": artifact["artifact_group"],
                "artifact_name": artifact["artifact_name"],
                "artifact_type": artifact["artifact_type"],
                "path": str(path),
                "exists": _artifact_exists(path),
                "row_count": _safe_len(path) if artifact["artifact_type"] == "table" else 0,
                "file_size_bytes": _safe_file_size(path),
                "current_use": artifact["current_use"],
                "used_in_waris_scoring": artifact["used_in_waris_scoring"],
                "used_in_monte_carlo": artifact["used_in_monte_carlo"],
                "production_score_change": (
                    RUN_MANIFEST_PRODUCTION_SCORE_CHANGE
                    if artifact["artifact_group"] == "Run manifest"
                    else SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE
                    if artifact["artifact_group"] == "Source freshness"
                    else FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE
                    if artifact["artifact_group"] == "False-positive controls"
                    else ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE
                    if artifact["artifact_group"] == "Analyst review"
                    else "none"
                ),
            }
        )

    return rows


def _artifact_inventory_rows() -> list[dict[str, Any]]:
    """Hash every eligible data/output file, excluding the five metadata files.

    Known catalog labels are retained. Other files have unassessed scoring use;
    observing a file is not evidence that the pipeline consumed or regenerated it.
    """
    known = {Path(r["path"]).resolve(): r for r in _legacy_artifact_inventory_rows()}
    rows = []
    for evidence in artifact_snapshot(BASE_DIR):
        path = BASE_DIR / evidence.path
        row = dict(known.get(path.resolve(), {
            "artifact_group": "Data snapshot" if evidence.path.startswith("data/") else "Additional output",
            "artifact_name": path.name, "artifact_type": path.suffix.lstrip("."),
            "current_use": "file_observation_only", "used_in_waris_scoring": "not_assessed",
            "used_in_monte_carlo": "not_assessed", "production_score_change": "none",
        }))
        row.update(path=evidence.path, exists=True, file_size_bytes=evidence.bytes,
                   sha256=evidence.sha256, row_count=_safe_len(path) if path.suffix==".csv" else 0)
        rows.append(row)
    return rows


def build_run_manifest_artifacts(
    run_id: str | None = None,
    run_timestamp_utc: str | None = None,
    manifest_phase: str = "final",
    context: RunContext | None = None,
) -> dict[str, Any]:
    """Build reproducibility and run-manifest artifacts.

    The manifest is an operational-control artifact. It documents what was
    generated, when it was generated, source/artifact status, validation-gate
    posture, operational-control availability, and the no-scoring/no-Monte-Carlo boundaries for context layers.

    It does not change WARIS risk layers, composite scores, risk bands, review
    rationales, or Monte Carlo simulations.
    """
    ensure_dirs([OUTPUT_DIR, TABLE_DIR, REPORT_DIR])

    if run_timestamp_utc is None:
        run_timestamp_utc = context.started_at_utc if context is not None else _utc_now_iso()

    if run_id is None:
        run_id = context.run_id if context is not None else new_run_id()

    if context is not None and (context.run_id != run_id or context.started_at_utc != run_timestamp_utc):
        raise ValueError("Manifest identity differs from captured execution context")

    live_counts = _load_live_source_counts()

    readiness_path = TABLE_DIR / "official_baseline_readiness_decision.csv"
    merge_summary_path = TABLE_DIR / "official_baseline_merge_review_summary.csv"
    governance_summary_path = TABLE_DIR / "model_governance_summary.csv"
    source_confidence_summary_path = TABLE_DIR / "source_confidence_summary.csv"
    analyst_review_summary_path = TABLE_DIR / "analyst_review_summary.csv"
    false_positive_summary_path = TABLE_DIR / "false_positive_summary.csv"
    source_freshness_summary_path = TABLE_DIR / "source_freshness_summary.csv"
    operational_context_review_path = (
        TABLE_DIR / "official_baseline_operational_controls_context_review.csv"
    )

    manifest_summary = {
        "run_id": run_id,
        "run_timestamp_utc": run_timestamp_utc,
        "manifest_phase": manifest_phase,
        "provenance_schema_version": 1,
        "inventory_scope": "all_eligible_data_and_output_files_excluding_five_self_metadata_files",
        "execution_evidence": "captured_pipeline_context" if context else "standalone_file_observation",
        "model_name": "WARIS - Ukraine Wartime AML Revenue Integrity Scoring Model",
        "model_version": MODEL_VERSION,
        "acquisition_policy_version": ACQUISITION_POLICY_VERSION,
        "model_version_label": f"v{MODEL_VERSION}",
        "python_version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "git_commit_hash": _git_commit_hash(),
        "git_working_tree_status": _git_dirty_status(),
        "production_score_change": "none",
        "official_baseline_decision": _read_first_value(
            readiness_path,
            "decision",
        ),
        "official_baseline_current_posture": _summary_value_for_area(
            merge_summary_path,
            "Scenario recommendation",
            value_column="status",
            fallback="not_available",
        ),
        "approved_current_use": _unique_values(
            readiness_path,
            "approved_current_use",
            fallback="not_available",
        ),
        "prohibited_current_use": _unique_values(
            readiness_path,
            "prohibited_current_use",
            fallback="risk_layer_calculation_or_composite_scoring",
        ),
        "scored_rows": _safe_len(TABLE_DIR / "waris_scored_oblast_sector.csv"),
        "oblast_summary_rows": _safe_len(TABLE_DIR / "waris_oblast_summary.csv"),
        "sector_summary_rows": _safe_len(TABLE_DIR / "waris_sector_summary.csv"),
        "monte_carlo_rows": _safe_len(TABLE_DIR / "waris_monte_carlo_results.csv"),
        "prozorro_candidate_rows": _safe_len(
            TABLE_DIR / "prozorro_procurement_scoring_candidates.csv"
        ),
        "wartime_typology_rows": _safe_len(
            TABLE_DIR / "waris_wartime_aml_typology_register.csv"
        ),
        "fiu_context_rows": _safe_len(TABLE_DIR / "waris_fiu_context_summary.csv"),
        "context_bridge_review_rows": (
            _safe_len(TABLE_DIR / "official_baseline_prozorro_context_review.csv")
            + _safe_len(
                TABLE_DIR / "official_baseline_wartime_typology_context_review.csv"
            )
            + _safe_len(TABLE_DIR / "official_baseline_fiu_context_review.csv")
            + _safe_len(
                TABLE_DIR / "official_baseline_operational_controls_context_review.csv"
            )
        ),
        "operational_controls_context_review_rows": _safe_len(
            operational_context_review_path
        ),
        "analyst_review_queue_rows": _safe_len(TABLE_DIR / "analyst_review_queue.csv"),
        "analyst_review_question_rows": _safe_len(
            TABLE_DIR / "analyst_review_questions.csv"
        ),
        "analyst_review_summary_rows": _safe_len(analyst_review_summary_path),
        "false_positive_control_rows": _safe_len(
            TABLE_DIR / "false_positive_controls.csv"
        ),
        "false_positive_checklist_rows": _safe_len(
            TABLE_DIR / "false_positive_review_checklist.csv"
        ),
        "false_positive_summary_rows": _safe_len(false_positive_summary_path),
        "operational_review_artifact_crosswalk_rows": _safe_len(
            TABLE_DIR / "operational_review_artifact_crosswalk.csv"
        ),
        "source_freshness_inventory_rows": _safe_len(
            TABLE_DIR / "source_freshness_inventory.csv"
        ),
        "source_freshness_summary_rows": _safe_len(source_freshness_summary_path),
        "source_freshness_posture": _summary_value_for_area(
            source_freshness_summary_path,
            "Overall freshness posture",
            value_column="status",
        ),
        "false_positive_control_status": _summary_value_for_area(
            false_positive_summary_path,
            "Control status counts",
        ),
        "governance_summary_rows": _safe_len(governance_summary_path),
        "source_confidence_summary_rows": _safe_len(source_confidence_summary_path),
        "live_status_rows": live_counts["live_status_rows"],
        "live_sources_count": live_counts["live_sources_count"],
        "fallback_sources_count": live_counts["fallback_sources_count"],
        "artifact_sources_count": live_counts["artifact_sources_count"],
        "benchmark_artifact_sources_count": live_counts[
            "benchmark_artifact_sources_count"
        ],
        "source_status_values": live_counts["source_status_values"],
        "pdf_report_exists": _artifact_exists(
            REPORT_DIR / "waris_ukraine_aml_risk_report.pdf"
        ),
        "pdf_report_path": str(REPORT_DIR / "waris_ukraine_aml_risk_report.pdf"),
        "run_manifest_table_path": str(RUN_MANIFEST_TABLE),
        "run_manifest_json_path": str(RUN_MANIFEST_JSON),
        "current_use_note": (
            f"WARIS model version v{MODEL_VERSION}; manifest_phase={manifest_phase}. Official baseline is benchmark-only; expanded Prozorro is review-only; "
            "wartime AML/CFT typology is literature support only; official FIU/SFMS "
            "is source-context only; context bridges are review artifacts only; "
            "analyst review, false-positive controls, source freshness, and run "
            "manifest artifacts are operational controls only."
        ),
        "human_review_required": True,
        "automated_adverse_action_allowed": False,
        "entity_level_findings_allowed": False,
    }

    artifact_rows = _artifact_inventory_rows()

    for row in artifact_rows:
        row["run_id"] = run_id
        row["run_timestamp_utc"] = run_timestamp_utc

    manifest_df = pd.DataFrame(artifact_rows)
    summary_df = pd.DataFrame([manifest_summary])

    safe_write_csv(manifest_df, RUN_MANIFEST_TABLE)
    safe_write_csv(summary_df, RUN_MANIFEST_SUMMARY_TABLE)

    manifest_json = {
        "summary": manifest_summary,
        "artifacts": artifact_rows,
    }

    RUN_MANIFEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    RUN_MANIFEST_JSON.write_text(
        json.dumps(manifest_json, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if manifest_phase in {"final", "standalone"}:
        seal_run(BASE_DIR, context, run_id, manifest_phase)

    return {
        "run_manifest": manifest_df,
        "run_manifest_summary": summary_df,
        "run_manifest_json": manifest_json,
        "run_manifest_table_path": RUN_MANIFEST_TABLE,
        "run_manifest_summary_path": RUN_MANIFEST_SUMMARY_TABLE,
        "run_manifest_json_path": RUN_MANIFEST_JSON,
    }


def main() -> None:
    """CLI entry point for regenerating run manifest artifacts."""
    artifacts = build_run_manifest_artifacts(manifest_phase="standalone")

    print(f"WARIS run manifest artifacts created for model version v{MODEL_VERSION}:")
    print(f"- Run manifest table: {artifacts['run_manifest_table_path']}")
    print(f"- Run manifest summary: {artifacts['run_manifest_summary_path']}")
    print(f"- Run manifest JSON: {artifacts['run_manifest_json_path']}")


if __name__ == "__main__":
    main()
