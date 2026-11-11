from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import REPORT_DIR, TABLE_DIR
from .utils import ensure_dirs, safe_read_csv, safe_write_csv

try:
    from .config import (
        ANALYST_REVIEW_CURRENT_USE,
        ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
        FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
        FALSE_POSITIVE_CONTROLS_TABLE,
        FALSE_POSITIVE_REVIEW_CHECKLIST_TABLE,
        FALSE_POSITIVE_RISK_REGISTER_TABLE,
        FALSE_POSITIVE_SUMMARY_TABLE,
        SOURCE_FRESHNESS_CURRENT_USE,
        SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
    )
except ImportError:
    ANALYST_REVIEW_CURRENT_USE = "analyst_review_workflow_only"
    ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE = "none"
    FALSE_POSITIVE_CONTROLS_CURRENT_USE = "human_review_support_only"
    FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE = "none"
    FALSE_POSITIVE_RISK_REGISTER_TABLE = TABLE_DIR / "false_positive_risk_register.csv"
    FALSE_POSITIVE_CONTROLS_TABLE = TABLE_DIR / "false_positive_controls.csv"
    FALSE_POSITIVE_REVIEW_CHECKLIST_TABLE = TABLE_DIR / "false_positive_review_checklist.csv"
    FALSE_POSITIVE_SUMMARY_TABLE = TABLE_DIR / "false_positive_summary.csv"
    SOURCE_FRESHNESS_CURRENT_USE = "source_freshness_monitoring_only"
    SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE = "none"


LAYER_FALSE_POSITIVE_PATTERNS = [
    {
        "risk_layer": "revenue_anomaly_risk",
        "false_positive_risk": "Legitimate wartime revenue disruption",
        "why_it_matters": (
            "Revenue anomalies can reflect displacement, infrastructure damage, "
            "temporary reporting disruption, emergency production shifts, or macroeconomic volatility."
        ),
        "analyst_control": (
            "Compare against sector peers, official baseline context, conflict exposure, "
            "and reporting-period limitations before treating the signal as stronger."
        ),
        "required_evidence_before_escalation": (
            "Source-backed revenue baseline, period comparability, sector comparison, "
            "and documented explanation for non-illicit wartime effects."
        ),
    },
    {
        "risk_layer": "procurement_integrity_risk",
        "false_positive_risk": "Legitimate emergency or reconstruction procurement",
        "why_it_matters": (
            "High procurement value, emergency keywords, or concentrated buying can be "
            "normal during urgent reconstruction, defense support, medical procurement, or infrastructure repair."
        ),
        "analyst_control": (
            "Review buyer concentration, procurement method, repeated awards, single-bid indicators, "
            "and whether urgency is consistent with the oblast/sector context."
        ),
        "required_evidence_before_escalation": (
            "Validated procurement mapping, historical coverage, tender detail review, "
            "false-positive rationale, and procurement/AML SME review."
        ),
    },
    {
        "risk_layer": "conflict_plausibility_gap",
        "false_positive_risk": "Conflict effects explain activity patterns",
        "why_it_matters": (
            "Conflict intensity can explain unusual logistics, procurement, revenue movement, "
            "humanitarian demand, population displacement, and infrastructure repair patterns."
        ),
        "analyst_control": (
            "Compare conflict-event context with sector activity and avoid interpreting conflict-driven disruption "
            "as an AML concern without corroborating indicators."
        ),
        "required_evidence_before_escalation": (
            "Conflict-event source context, sector-specific explanation, and independent corroborating risk indicators."
        ),
    },
    {
        "risk_layer": "sanctions_exposure_risk",
        "false_positive_risk": "Broad regional or sector exposure without specific counterparty support",
        "why_it_matters": (
            "Sanctions proxies may indicate broad exposure rather than a specific sanctioned entity, transaction, "
            "counterparty, or beneficial owner."
        ),
        "analyst_control": (
            "Treat sanctions exposure as contextual unless entity-level sanctions-screening evidence is validated "
            "and legally/compliantly usable."
        ),
        "required_evidence_before_escalation": (
            "Current sanctions-list match logic, entity-resolution controls, false-positive review, "
            "and legal/compliance review before operational use."
        ),
    },
    {
        "risk_layer": "ownership_opacity_risk",
        "false_positive_risk": "Registry gaps or unavailable ownership data",
        "why_it_matters": (
            "Ownership opacity may reflect data limitations, registry access issues, privacy constraints, "
            "or incomplete public-source coverage rather than concealment."
        ),
        "analyst_control": (
            "Document whether the ownership signal is source-backed or synthetic fallback and identify what registry "
            "or beneficial-ownership fields would be needed for stronger review."
        ),
        "required_evidence_before_escalation": (
            "Validated registry source, beneficial ownership fields, entity-resolution method, "
            "and false-positive review."
        ),
    },
    {
        "risk_layer": "tbml_risk",
        "false_positive_risk": "Legitimate trade disruption or logistics rerouting",
        "why_it_matters": (
            "Trade-based exposure can rise because of wartime supply-chain disruption, route changes, "
            "import substitution, export interruption, or humanitarian logistics."
        ),
        "analyst_control": (
            "Compare trade proxy signals against macro trade context, sector demand, logistics disruption, "
            "and source-confidence limits."
        ),
        "required_evidence_before_escalation": (
            "Validated trade indicators, sector-specific baseline, route/counterparty context, "
            "and non-illicit explanation review."
        ),
    },
    {
        "risk_layer": "financial_supervision_exposure",
        "false_positive_risk": "National-level context applied too strongly to oblast/sector records",
        "why_it_matters": (
            "FIU/SFMS and NBU context may be national-level and not directly attributable to an oblast, sector, "
            "entity, or transaction."
        ),
        "analyst_control": (
            "Keep national FIU/SFMS and NBU context as source-support only unless measurable oblast/sector indicators "
            "are validated."
        ),
        "required_evidence_before_escalation": (
            "Measurable oblast/sector indicator design, source validation, SME review, and model change control."
        ),
    },
]


GENERAL_CONTROLS = [
    {
        "control_id": "FPC-001",
        "control_name": "Human review requirement",
        "control_type": "governance",
        "control_description": "Every queue record requires trained human review before interpretation or follow-up.",
        "control_test": "Confirm human_review_required=True in analyst_review_queue.csv.",
        "pass_condition": "All review queue rows show human_review_required=True.",
    },
    {
        "control_id": "FPC-002",
        "control_name": "No automated adverse action",
        "control_type": "governance",
        "control_description": "WARIS outputs must not trigger automated adverse action.",
        "control_test": "Confirm automated_adverse_action_allowed=False in review workflow outputs.",
        "pass_condition": "All workflow rows show automated_adverse_action_allowed=False.",
    },
    {
        "control_id": "FPC-003",
        "control_name": "No entity-level findings",
        "control_type": "scope",
        "control_description": "WARIS remains oblast/sector-level review support and does not make entity-level findings.",
        "control_test": "Confirm entity_level_findings_allowed=False and no entity identifiers are required for queue outputs.",
        "pass_condition": "All workflow rows show entity_level_findings_allowed=False.",
    },
    {
        "control_id": "FPC-004",
        "control_name": "Production score unchanged",
        "control_type": "model_change_control",
        "control_description": "False-positive controls document interpretation risk but do not change scores.",
        "control_test": "Confirm production_score_change=none.",
        "pass_condition": "All false-positive artifacts show production_score_change=none.",
    },
    {
        "control_id": "FPC-005",
        "control_name": "Source-context separation",
        "control_type": "source_governance",
        "control_description": "Official baseline, Prozorro, typology, FIU/SFMS, source-freshness, analyst-review, and run-manifest artifacts remain separate from scoring unless change control is approved.",
        "control_test": "Confirm current-use labels remain benchmark-only, review-only, literature-support-only, source-context-only, monitoring-only, or documentation-only.",
        "pass_condition": "No false-positive control artifact authorizes direct scoring integration.",
    },
    {
        "control_id": "FPC-006",
        "control_name": "Source freshness context available",
        "control_type": "source_monitoring",
        "control_description": "Analysts should know whether source-freshness artifacts are available before relying on source-context flags.",
        "control_test": "Confirm source_freshness_summary.csv is available or mark the control for review.",
        "pass_condition": "Source-freshness summary is available and can be reviewed before disposition.",
    },
    {
        "control_id": "FPC-007",
        "control_name": "Operational artifact crosswalk available",
        "control_type": "workflow_documentation",
        "control_description": "The operational artifact crosswalk documents analyst review, false-positive, source-freshness, and run-manifest artifacts as non-scoring workflow support.",
        "control_test": "Confirm operational_review_artifact_crosswalk.csv is available or mark the control for review.",
        "pass_condition": "Operational artifact crosswalk is available and does not authorize scoring use.",
    },
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_table(filename: str) -> pd.DataFrame | None:
    return safe_read_csv(TABLE_DIR / filename)


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def _check_bool_column(df: pd.DataFrame | None, column: str, expected: bool) -> str:
    if df is None or df.empty:
        return "not_available"

    if column not in df.columns:
        return "missing_column"

    values = df[column].fillna(False).astype(bool)
    return "pass" if bool(values.eq(expected).all()) else "review_required"


def _check_text_column(df: pd.DataFrame | None, column: str, expected: str) -> str:
    if df is None or df.empty:
        return "not_available"

    if column not in df.columns:
        return "missing_column"

    values = df[column].dropna().astype(str).str.strip().str.lower()
    if values.empty:
        return "not_available"

    return "pass" if bool(values.eq(expected.lower()).all()) else "review_required"


def _source_context_controls_status() -> str:
    summary = _load_table("analyst_review_summary.csv")
    manifest = _load_table("run_manifest_summary.csv")

    if summary is None and manifest is None:
        return "not_available"

    return "pass"


def _source_freshness_controls_status() -> str:
    summary = _load_table("source_freshness_summary.csv")

    if summary is None or summary.empty:
        return "not_available"

    if "summary_area" not in summary.columns:
        return "missing_column"

    posture = summary[
        summary["summary_area"]
        .fillna("")
        .astype(str)
        .eq("Overall freshness posture")
    ]

    if posture.empty:
        return "review_required"

    status = str(posture.iloc[0].get("status", "")).lower()
    if status in {"current_for_documented_use", "created", "control_active"}:
        return "pass"

    return "review_required"


def _operational_artifact_crosswalk_status() -> str:
    crosswalk = _load_table("operational_review_artifact_crosswalk.csv")

    if crosswalk is None or crosswalk.empty:
        return "not_available"

    required_columns = {
        "artifact_family",
        "artifact_output",
        "current_use",
        "production_score_change",
        "automated_adverse_action_allowed",
        "entity_level_findings_allowed",
        "current_use_in_scoring",
    }

    missing = required_columns - set(crosswalk.columns)
    if missing:
        return "missing_column"

    scoring_ok = crosswalk["current_use_in_scoring"].fillna("").astype(str).eq(
        "not_a_scoring_field"
    ).all()
    production_ok = crosswalk["production_score_change"].fillna("").astype(str).eq(
        "none"
    ).all()
    adverse_action_ok = (
        crosswalk["automated_adverse_action_allowed"].fillna(False).astype(bool).eq(False).all()
    )
    entity_finding_ok = (
        crosswalk["entity_level_findings_allowed"].fillna(False).astype(bool).eq(False).all()
    )

    if scoring_ok and production_ok and adverse_action_ok and entity_finding_ok:
        return "pass"

    return "review_required"


def _build_layer_register() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for idx, item in enumerate(LAYER_FALSE_POSITIVE_PATTERNS, start=1):
        row = {
            "false_positive_id": f"FPR-{idx:03d}",
            "risk_layer": item["risk_layer"],
            "false_positive_risk": item["false_positive_risk"],
            "why_it_matters": item["why_it_matters"],
            "analyst_control": item["analyst_control"],
            "required_evidence_before_escalation": item[
                "required_evidence_before_escalation"
            ],
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
            "production_score_change": FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
            "human_review_required": True,
            "automated_adverse_action_allowed": False,
            "entity_level_findings_allowed": False,
        }
        rows.append(row)

    return pd.DataFrame(rows)


def _build_controls_table() -> pd.DataFrame:
    queue = _load_table("analyst_review_queue.csv")

    test_status_map = {
        "FPC-001": _check_bool_column(queue, "human_review_required", True),
        "FPC-002": _check_bool_column(queue, "automated_adverse_action_allowed", False),
        "FPC-003": _check_bool_column(queue, "entity_level_findings_allowed", False),
        "FPC-004": _check_text_column(queue, "production_score_change", "none"),
        "FPC-005": _source_context_controls_status(),
        "FPC-006": _source_freshness_controls_status(),
        "FPC-007": _operational_artifact_crosswalk_status(),
    }

    rows: list[dict[str, Any]] = []

    for control in GENERAL_CONTROLS:
        control_id = control["control_id"]
        rows.append(
            {
                **control,
                "test_status": test_status_map.get(control_id, "not_available"),
                "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
                "production_score_change": FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
                "generated_at_utc": _utc_now_iso(),
            }
        )

    return pd.DataFrame(rows)


def _build_review_checklist() -> pd.DataFrame:
    queue = _load_table("analyst_review_queue.csv")

    if queue is None or queue.empty:
        return pd.DataFrame(
            [
                {
                    "review_id": "not_available",
                    "checklist_item": "Run analyst_review_queue.py before building record-level false-positive checklist.",
                    "checklist_status": "not_started",
                    "production_score_change": "none",
                }
            ]
        )

    rows: list[dict[str, Any]] = []

    checklist_items = [
        "Document the most likely legitimate explanation for each primary driver.",
        "Check whether the signal is supported by live/source-backed data or synthetic fallback fields.",
        "Review source-context flags before assigning disposition.",
        "Review source-freshness posture before relying on source-context flags.",
        "Confirm that false-positive controls were considered before assigning disposition.",
        "Confirm that no entity-level finding is being made from oblast/sector-level signals.",
        "Document whether follow-up is needed, not needed, or requires SME review.",
        "Mark false_positive_flag when a plausible benign explanation is stronger than the review signal.",
    ]

    for _, record in queue.iterrows():
        for idx, item in enumerate(checklist_items, start=1):
            rows.append(
                {
                    "review_id": record.get("review_id"),
                    "review_priority_rank": record.get("review_priority_rank"),
                    "oblast": record.get("oblast"),
                    "sector": record.get("sector"),
                    "checklist_number": idx,
                    "checklist_item": item,
                    "checklist_status": "not_started",
                    "analyst_notes": "",
                    "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
                    "production_score_change": FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
                }
            )

    return pd.DataFrame(rows)


def _build_summary(
    register: pd.DataFrame,
    controls: pd.DataFrame,
    checklist: pd.DataFrame,
) -> pd.DataFrame:
    status_counts = (
        controls["test_status"].value_counts().to_dict()
        if controls is not None and not controls.empty and "test_status" in controls.columns
        else {}
    )

    rows = [
        {
            "summary_area": "False-positive risk register",
            "status": "created",
            "value": len(register),
            "recommended_next_action": "Use risk-layer false-positive patterns to frame analyst review and report limitations.",
        },
        {
            "summary_area": "False-positive controls",
            "status": "created",
            "value": len(controls),
            "recommended_next_action": "Review any control with status other than pass.",
        },
        {
            "summary_area": "False-positive review checklist",
            "status": "created",
            "value": len(checklist),
            "recommended_next_action": "Use checklist rows when completing analyst disposition fields.",
        },
        {
            "summary_area": "Source freshness integration",
            "status": _source_freshness_controls_status(),
            "value": SOURCE_FRESHNESS_CURRENT_USE,
            "recommended_next_action": "Review source-freshness posture before relying on source-context flags.",
        },
        {
            "summary_area": "Operational artifact crosswalk",
            "status": _operational_artifact_crosswalk_status(),
            "value": "operational_review_artifact_crosswalk.csv",
            "recommended_next_action": "Use the crosswalk to confirm review-support artifacts remain outside scoring.",
        },
        {
            "summary_area": "Control status counts",
            "status": "computed",
            "value": status_counts,
            "recommended_next_action": "Investigate review_required, missing_column, or not_available statuses.",
        },
        {
            "summary_area": "Production score change control",
            "status": "control_active",
            "value": FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
            "recommended_next_action": "False-positive controls do not alter WARIS scores, risk bands, or Monte Carlo outputs.",
        },
        {
            "summary_area": "Use limitation",
            "status": "control_active",
            "value": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
            "recommended_next_action": "Do not treat false-positive controls as allegations, clearances, or automated decisions.",
        },
    ]

    return pd.DataFrame(rows)


def build_false_positive_control_artifacts() -> dict[str, Any]:
    """Build false-positive risk and control artifacts.

    These artifacts document ways WARIS signals can be misinterpreted and define
    review controls. They also check source-freshness and operational-artifact
    crosswalk availability when those newer modules have been generated. They do
    not alter risk-layer calculations, composite scores, risk bands, review
    rationales, analyst dispositions, or Monte Carlo outputs.
    """
    ensure_dirs([TABLE_DIR, REPORT_DIR])

    register = _build_layer_register()
    controls = _build_controls_table()
    checklist = _build_review_checklist()
    summary = _build_summary(register, controls, checklist)

    safe_write_csv(register, FALSE_POSITIVE_RISK_REGISTER_TABLE)
    safe_write_csv(controls, FALSE_POSITIVE_CONTROLS_TABLE)
    safe_write_csv(checklist, FALSE_POSITIVE_REVIEW_CHECKLIST_TABLE)
    safe_write_csv(summary, FALSE_POSITIVE_SUMMARY_TABLE)

    return {
        "false_positive_risk_register": register,
        "false_positive_controls": controls,
        "false_positive_review_checklist": checklist,
        "false_positive_summary": summary,
        "false_positive_risk_register_path": FALSE_POSITIVE_RISK_REGISTER_TABLE,
        "false_positive_controls_path": FALSE_POSITIVE_CONTROLS_TABLE,
        "false_positive_review_checklist_path": FALSE_POSITIVE_REVIEW_CHECKLIST_TABLE,
        "false_positive_summary_path": FALSE_POSITIVE_SUMMARY_TABLE,
    }


def main() -> None:
    artifacts = build_false_positive_control_artifacts()

    print("WARIS false-positive control artifacts created:")
    print(f"- False-positive risk register: {artifacts['false_positive_risk_register_path']}")
    print(f"- False-positive controls: {artifacts['false_positive_controls_path']}")
    print(f"- False-positive review checklist: {artifacts['false_positive_review_checklist_path']}")
    print(f"- False-positive summary: {artifacts['false_positive_summary_path']}")


if __name__ == "__main__":
    main()
