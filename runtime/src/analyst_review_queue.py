from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import REPORT_DIR, TABLE_DIR
from .utils import ensure_dirs, safe_read_csv, safe_write_csv


ANALYST_REVIEW_QUEUE_TABLE = TABLE_DIR / "analyst_review_queue.csv"
ANALYST_REVIEW_QUESTIONS_TABLE = TABLE_DIR / "analyst_review_questions.csv"
REVIEW_DISPOSITION_TEMPLATE_TABLE = TABLE_DIR / "review_disposition_template.csv"
ANALYST_REVIEW_SUMMARY_TABLE = TABLE_DIR / "analyst_review_summary.csv"


LAYER_DISPLAY_NAMES = {
    "revenue_anomaly_risk": "revenue anomaly",
    "sanctions_exposure_risk": "sanctions exposure",
    "procurement_integrity_risk": "procurement integrity",
    "ownership_opacity_risk": "ownership opacity",
    "tbml_risk": "trade-based money laundering exposure",
    "conflict_plausibility_gap": "conflict plausibility gap",
    "financial_supervision_exposure": "financial-supervision exposure",
}


LAYER_REVIEW_QUESTIONS = {
    "revenue_anomaly_risk": [
        "Could the revenue signal reflect legitimate wartime reporting disruption, displacement, reconstruction activity, or macroeconomic volatility?",
        "Does the oblast/sector pattern differ materially from comparable oblasts or sectors after considering source quality and baseline assumptions?",
    ],
    "sanctions_exposure_risk": [
        "Is the sanctions signal supported by current public-source sanctions data, or is it a broad contextual proxy requiring additional validation?",
        "Would future sanctions-screening integration require entity-level data, false-positive controls, and legal/compliance review before operational use?",
    ],
    "procurement_integrity_risk": [
        "Are public procurement patterns unusually concentrated, emergency-oriented, reconstruction-related, or single-bid/supplier-heavy in the available review artifacts?",
        "Could the procurement signal reflect legitimate urgent wartime procurement needs rather than integrity risk?",
    ],
    "ownership_opacity_risk": [
        "Is the ownership-opacity signal based on source-backed information or synthetic fallback assumptions?",
        "What public-source beneficial ownership or registry indicators would be needed before treating this as a stronger review signal?",
    ],
    "tbml_risk": [
        "Could trade exposure reflect legitimate wartime supply-chain disruption, import substitution, logistics constraints, or export-market changes?",
        "Are additional trade, customs, sector, or counterparty indicators needed before escalating this signal?",
    ],
    "conflict_plausibility_gap": [
        "Does conflict exposure plausibly explain disruption, displacement, infrastructure repair, or emergency procurement patterns?",
        "Is the signal supported by live conflict-event data, fallback assumptions, or a blend of both?",
    ],
    "financial_supervision_exposure": [
        "Is the financial-supervision signal national-context only, or does it have measurable oblast/sector support?",
        "What NBU/FIU/SFMS measurable indicators would be required before using this signal in a stronger model layer?",
    ],
}


GENERAL_REVIEW_QUESTIONS = [
    "Is the signal supported by multiple independent source families, or mainly by synthetic fallback fields?",
    "What false-positive explanations should be ruled out before any follow-up analysis?",
    "Does the record require SME review before any future model-design or scoring-change discussion?",
    "Is the correct current posture review-only, benchmark-only, source-context-only, or no further action?",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def _load_table(filename: str) -> pd.DataFrame | None:
    return safe_read_csv(TABLE_DIR / filename)


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _primary_layer_drivers(row: pd.Series, top_n: int = 3) -> list[str]:
    values: list[tuple[str, float]] = []

    for col, display in LAYER_DISPLAY_NAMES.items():
        if col not in row.index:
            continue

        try:
            value = float(row.get(col, 0))
        except Exception:
            value = 0.0

        values.append((display, value))

    values.sort(key=lambda item: item[1], reverse=True)

    return [name for name, value in values[:top_n] if value > 0]


def _primary_layer_columns(row: pd.Series, top_n: int = 3) -> list[str]:
    values: list[tuple[str, float]] = []

    for col in LAYER_DISPLAY_NAMES:
        if col not in row.index:
            continue

        try:
            value = float(row.get(col, 0))
        except Exception:
            value = 0.0

        values.append((col, value))

    values.sort(key=lambda item: item[1], reverse=True)

    return [col for col, value in values[:top_n] if value > 0]


def _risk_band_priority(risk_band: object) -> int:
    text = "" if risk_band is None else str(risk_band).lower()

    if "high" in text:
        return 1
    if "elevated" in text:
        return 2
    if "moderate" in text:
        return 3
    if "baseline" in text:
        return 4

    return 5


def _score_priority(score: float) -> str:
    if score >= 70:
        return "priority_1_high_review"
    if score >= 60:
        return "priority_2_elevated_review"
    if score >= 50:
        return "priority_3_moderate_review"
    return "priority_4_baseline_monitor"


def _load_monte_carlo_context() -> pd.DataFrame:
    mc = _load_table("waris_monte_carlo_results.csv")

    if mc is None or mc.empty:
        return pd.DataFrame(columns=["oblast", "sector"])

    keep_cols = [
        col
        for col in [
            "oblast",
            "sector",
            "prob_elevated_or_high",
            "robustness_band",
            "mc_p05_score",
            "mc_p95_score",
        ]
        if col in mc.columns
    ]

    if "oblast" not in keep_cols or "sector" not in keep_cols:
        return pd.DataFrame(columns=["oblast", "sector"])

    return mc[keep_cols].copy()


def _load_oblast_context_flags() -> pd.DataFrame:
    """Build oblast-level source-context flags from optional review artifacts."""
    frames: list[pd.DataFrame] = []

    prozorro_review = _load_table("official_baseline_prozorro_context_review.csv")
    if prozorro_review is not None and not prozorro_review.empty and "oblast" in prozorro_review.columns:
        proc_col = _first_existing_column(
            prozorro_review,
            [
                "procurement_review_priority_candidate",
                "procurement_context_candidate",
                "prozorro_context_candidate",
            ],
        )
        tmp = prozorro_review[["oblast"]].copy()
        tmp["prozorro_context_available"] = True
        if proc_col:
            tmp["prozorro_context_score"] = _safe_numeric(prozorro_review[proc_col])
        frames.append(tmp)

    baseline_review = _load_table("official_baseline_gap_review.csv")
    if baseline_review is not None and not baseline_review.empty and "oblast" in baseline_review.columns:
        gap_col = _first_existing_column(
            baseline_review,
            ["absolute_index_gap", "abs_index_gap", "index_gap"],
        )
        tmp = baseline_review[["oblast"]].copy()
        tmp["official_baseline_context_available"] = True
        if gap_col:
            tmp["official_baseline_gap_value"] = _safe_numeric(baseline_review[gap_col])
        frames.append(tmp)

    if not frames:
        return pd.DataFrame(columns=["oblast"])

    context = frames[0]
    for frame in frames[1:]:
        context = context.merge(frame, on="oblast", how="outer")

    bool_cols = [
        "prozorro_context_available",
        "official_baseline_context_available",
    ]

    for col in bool_cols:
        if col in context.columns:
            context[col] = context[col].fillna(False).astype(bool)

    return context


def _global_context_flags() -> dict[str, Any]:
    typology = _load_table("waris_wartime_aml_typology_register.csv")
    fiu = _load_table("waris_fiu_context_summary.csv")
    source_confidence = _load_table("source_confidence_summary.csv")
    source_freshness = _load_table("source_freshness_summary.csv")
    false_positive_controls = _load_table("false_positive_controls.csv")
    false_positive_summary = _load_table("false_positive_summary.csv")
    run_manifest_summary = _load_table("run_manifest_summary.csv")

    freshness_posture = "not_available"
    if source_freshness is not None and not source_freshness.empty:
        if "summary_area" in source_freshness.columns:
            posture_rows = source_freshness[
                source_freshness["summary_area"]
                .fillna("")
                .astype(str)
                .eq("Overall freshness posture")
            ]
            if not posture_rows.empty:
                freshness_posture = str(posture_rows.iloc[0].get("status", "not_available"))

    false_positive_control_status = "not_available"
    if false_positive_summary is not None and not false_positive_summary.empty:
        if "summary_area" in false_positive_summary.columns:
            control_rows = false_positive_summary[
                false_positive_summary["summary_area"]
                .fillna("")
                .astype(str)
                .eq("Control status counts")
            ]
            if not control_rows.empty:
                false_positive_control_status = str(
                    control_rows.iloc[0].get("value", "not_available")
                )

    return {
        "wartime_typology_context_available": typology is not None and not typology.empty,
        "wartime_typology_reference_rows": 0 if typology is None else len(typology),
        "fiu_context_available": fiu is not None and not fiu.empty,
        "fiu_context_rows": 0 if fiu is None else len(fiu),
        "source_confidence_available": source_confidence is not None
        and not source_confidence.empty,
        "source_freshness_available": source_freshness is not None
        and not source_freshness.empty,
        "source_freshness_posture": freshness_posture,
        "false_positive_controls_available": false_positive_controls is not None
        and not false_positive_controls.empty,
        "false_positive_control_status": false_positive_control_status,
        "run_manifest_available": run_manifest_summary is not None
        and not run_manifest_summary.empty,
    }


def _build_source_context_summary(row: pd.Series) -> str:
    flags = []

    if bool(row.get("prozorro_context_available", False)):
        flags.append("Prozorro context available")

    if bool(row.get("official_baseline_context_available", False)):
        flags.append("official baseline benchmark context available")

    if bool(row.get("wartime_typology_context_available", False)):
        flags.append("wartime typology reference available")

    if bool(row.get("fiu_context_available", False)):
        flags.append("FIU/SFMS national context available")

    if bool(row.get("source_confidence_available", False)):
        flags.append("source-confidence artifacts available")

    if bool(row.get("source_freshness_available", False)):
        posture = str(row.get("source_freshness_posture", "not_available"))
        flags.append(f"source-freshness posture: {posture}")

    if bool(row.get("false_positive_controls_available", False)):
        flags.append("false-positive controls available")

    if not flags:
        return "No generated source-context artifacts available for this record."

    return "; ".join(flags)


def _questions_for_row(row: pd.Series) -> list[str]:
    questions: list[str] = []

    for col in _primary_layer_columns(row, top_n=3):
        questions.extend(LAYER_REVIEW_QUESTIONS.get(col, []))

    questions.extend(GENERAL_REVIEW_QUESTIONS)

    # De-duplicate while preserving order.
    seen: set[str] = set()
    deduped: list[str] = []

    for question in questions:
        if question in seen:
            continue
        seen.add(question)
        deduped.append(question)

    return deduped[:8]


def _safe_review_id(rank: int, oblast: object, sector: object) -> str:
    oblast_token = str(oblast).lower().replace(" ", "_").replace("-", "_")
    sector_token = str(sector).lower().replace(" ", "_").replace("-", "_")
    sector_token = "".join(ch for ch in sector_token if ch.isalnum() or ch == "_")[:32]
    oblast_token = "".join(ch for ch in oblast_token if ch.isalnum() or ch == "_")[:24]
    return f"WARIS-REV-{rank:04d}-{oblast_token}-{sector_token}"


def build_analyst_review_artifacts(
    top_n: int = 25,
    minimum_score: float = 45.0,
) -> dict[str, Any]:
    """Build analyst review workflow artifacts.

    These outputs convert WARIS model signals into human-review queue records,
    suggested review questions, source-freshness context, false-positive control
    context, and a disposition template. They are not allegations, entity-level
    findings, enforcement outputs, or automated adverse-action recommendations.
    """
    ensure_dirs([TABLE_DIR, REPORT_DIR])

    scored = _load_table("waris_scored_oblast_sector.csv")

    if scored is None or scored.empty:
        raise FileNotFoundError(
            "waris_scored_oblast_sector.csv is required before building the analyst review queue."
        )

    required_cols = {"oblast", "sector", "waris_aml_review_score"}

    if not required_cols.issubset(scored.columns):
        missing = sorted(required_cols - set(scored.columns))
        raise ValueError(f"Scored table is missing required columns: {missing}")

    working = scored.copy()
    working["waris_aml_review_score"] = _safe_numeric(working["waris_aml_review_score"])

    if "risk_band" not in working.columns:
        working["risk_band"] = working["waris_aml_review_score"].map(_score_priority)

    working["risk_band_priority"] = working["risk_band"].map(_risk_band_priority)
    working = working.sort_values(
        ["risk_band_priority", "waris_aml_review_score"],
        ascending=[True, False],
    ).copy()

    working = working[working["waris_aml_review_score"] >= minimum_score].head(top_n).copy()

    if working.empty:
        working = scored.copy()
        working["waris_aml_review_score"] = _safe_numeric(working["waris_aml_review_score"])
        working = working.sort_values("waris_aml_review_score", ascending=False).head(top_n)

    working["review_priority_rank"] = range(1, len(working) + 1)
    working["review_id"] = working.apply(
        lambda row: _safe_review_id(
            int(row["review_priority_rank"]),
            row["oblast"],
            row["sector"],
        ),
        axis=1,
    )

    mc_context = _load_monte_carlo_context()
    if not mc_context.empty:
        working = working.merge(mc_context, on=["oblast", "sector"], how="left")

    oblast_context = _load_oblast_context_flags()
    if not oblast_context.empty:
        working = working.merge(oblast_context, on="oblast", how="left")

    global_flags = _global_context_flags()
    for key, value in global_flags.items():
        working[key] = value

    bool_cols = [
        "prozorro_context_available",
        "official_baseline_context_available",
        "wartime_typology_context_available",
        "fiu_context_available",
        "source_confidence_available",
        "source_freshness_available",
        "false_positive_controls_available",
        "run_manifest_available",
    ]

    for col in bool_cols:
        if col in working.columns:
            working[col] = working[col].fillna(False).astype(bool)

    for col in ["prob_elevated_or_high", "mc_p05_score", "mc_p95_score"]:
        if col in working.columns:
            working[col] = _safe_numeric(working[col])

    if "robustness_band" not in working.columns:
        working["robustness_band"] = "not_available"
    else:
        working["robustness_band"] = working["robustness_band"].fillna("not_available").astype(str)

    working["primary_risk_drivers"] = working.apply(
        lambda row: "; ".join(_primary_layer_drivers(row, top_n=3)),
        axis=1,
    )
    working["source_context_flags"] = working.apply(_build_source_context_summary, axis=1)
    working["suggested_review_questions"] = working.apply(
        lambda row: " | ".join(_questions_for_row(row)),
        axis=1,
    )
    working["false_positive_control_context"] = working.apply(
        lambda row: (
            "false-positive controls available; review benign explanations before disposition"
            if bool(row.get("false_positive_controls_available", False))
            else "false-positive controls not available for this run"
        ),
        axis=1,
    )
    working["source_freshness_context"] = working.apply(
        lambda row: (
            f"source-freshness posture: {row.get('source_freshness_posture', 'not_available')}"
            if bool(row.get("source_freshness_available", False))
            else "source-freshness summary not available for this run"
        ),
        axis=1,
    )

    working["review_status"] = "not_started"
    working["analyst_disposition"] = ""
    working["analyst_notes"] = ""
    working["false_positive_flag"] = ""
    working["follow_up_required"] = ""
    working["reviewer_initials"] = ""
    working["date_reviewed"] = ""
    working["human_review_required"] = True
    working["automated_adverse_action_allowed"] = False
    working["entity_level_findings_allowed"] = False
    working["production_score_change"] = "none"
    working["current_use"] = "analyst_review_workflow_only"
    working["control_note"] = (
        "This queue supports human review prioritization only. It is not an allegation, "
        "entity-level finding, enforcement recommendation, or automated adverse action."
    )

    queue_columns = [
        "review_id",
        "review_priority_rank",
        "oblast",
        "sector",
        "waris_aml_review_score",
        "risk_band",
        "primary_risk_drivers",
        "prob_elevated_or_high",
        "robustness_band",
        "mc_p05_score",
        "mc_p95_score",
        "source_context_flags",
        "false_positive_control_context",
        "source_freshness_context",
        "suggested_review_questions",
        "review_status",
        "analyst_disposition",
        "analyst_notes",
        "false_positive_flag",
        "follow_up_required",
        "reviewer_initials",
        "date_reviewed",
        "human_review_required",
        "automated_adverse_action_allowed",
        "entity_level_findings_allowed",
        "production_score_change",
        "current_use",
        "control_note",
    ]

    available_queue_columns = [col for col in queue_columns if col in working.columns]
    review_queue = working[available_queue_columns].copy()

    question_rows: list[dict[str, Any]] = []
    for _, row in review_queue.iterrows():
        questions = str(row.get("suggested_review_questions", "")).split(" | ")
        for idx, question in enumerate([q for q in questions if q.strip()], start=1):
            question_rows.append(
                {
                    "review_id": row.get("review_id"),
                    "review_priority_rank": row.get("review_priority_rank"),
                    "oblast": row.get("oblast"),
                    "sector": row.get("sector"),
                    "question_number": idx,
                    "review_question": question,
                    "question_type": "analyst_review_prompt",
                    "current_use": "human_review_only",
                    "production_score_change": "none",
                }
            )

    questions_df = pd.DataFrame(question_rows)

    disposition_template = review_queue[
        [
            "review_id",
            "review_priority_rank",
            "oblast",
            "sector",
            "waris_aml_review_score",
            "risk_band",
            "primary_risk_drivers",
            "false_positive_control_context",
            "source_freshness_context",
            "review_status",
            "analyst_disposition",
            "analyst_notes",
            "false_positive_flag",
            "follow_up_required",
            "reviewer_initials",
            "date_reviewed",
        ]
    ].copy()

    summary_rows = [
        {
            "summary_area": "Review queue records",
            "status": "created",
            "value": len(review_queue),
            "recommended_next_action": "Review top-ranked records and complete analyst disposition fields.",
        },
        {
            "summary_area": "Review questions",
            "status": "created",
            "value": len(questions_df),
            "recommended_next_action": "Use questions to structure non-accusatory human review.",
        },
        {
            "summary_area": "Current use control",
            "status": "control_active",
            "value": "analyst_review_workflow_only",
            "recommended_next_action": "Do not treat queue entries as allegations, findings, or enforcement recommendations.",
        },
        {
            "summary_area": "Production score change control",
            "status": "control_active",
            "value": "none",
            "recommended_next_action": "Review workflow does not alter WARIS scores, risk bands, or Monte Carlo outputs.",
        },
        {
            "summary_area": "Human review control",
            "status": "control_active",
            "value": "human_review_required=True; automated_adverse_action_allowed=False; entity_level_findings_allowed=False",
            "recommended_next_action": "Keep review decisions documented and analyst-led.",
        },
        {
            "summary_area": "False-positive control context",
            "status": "available" if bool(global_flags.get("false_positive_controls_available")) else "not_available",
            "value": global_flags.get("false_positive_control_status", "not_available"),
            "recommended_next_action": "Use false-positive controls before assigning analyst disposition.",
        },
        {
            "summary_area": "Source freshness context",
            "status": "available" if bool(global_flags.get("source_freshness_available")) else "not_available",
            "value": global_flags.get("source_freshness_posture", "not_available"),
            "recommended_next_action": "Check source-freshness posture before relying on source-context flags.",
        },
    ]

    summary_df = pd.DataFrame(summary_rows)

    safe_write_csv(review_queue, ANALYST_REVIEW_QUEUE_TABLE)
    safe_write_csv(questions_df, ANALYST_REVIEW_QUESTIONS_TABLE)
    safe_write_csv(disposition_template, REVIEW_DISPOSITION_TEMPLATE_TABLE)
    safe_write_csv(summary_df, ANALYST_REVIEW_SUMMARY_TABLE)

    return {
        "analyst_review_queue": review_queue,
        "analyst_review_questions": questions_df,
        "review_disposition_template": disposition_template,
        "analyst_review_summary": summary_df,
        "analyst_review_queue_path": ANALYST_REVIEW_QUEUE_TABLE,
        "analyst_review_questions_path": ANALYST_REVIEW_QUESTIONS_TABLE,
        "review_disposition_template_path": REVIEW_DISPOSITION_TEMPLATE_TABLE,
        "analyst_review_summary_path": ANALYST_REVIEW_SUMMARY_TABLE,
    }


def main() -> None:
    artifacts = build_analyst_review_artifacts()

    print("WARIS analyst review workflow artifacts created:")
    print(f"- Analyst review queue: {artifacts['analyst_review_queue_path']}")
    print(f"- Analyst review questions: {artifacts['analyst_review_questions_path']}")
    print(f"- Review disposition template: {artifacts['review_disposition_template_path']}")
    print(f"- Analyst review summary: {artifacts['analyst_review_summary_path']}")


if __name__ == "__main__":
    main()
