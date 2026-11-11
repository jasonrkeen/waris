from __future__ import annotations

from .utils import official_baseline_observations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import BASE_WEIGHTS, MONTE_CARLO_RUNS, RANDOM_SEED

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


def _normalize_oblast_name(value: object) -> str:
    """Normalize official/source oblast labels to WARIS canonical labels."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""

    text = str(value).strip()

    if not text:
        return ""

    return UKRSTAT_TO_WARIS_OBLAST.get(text, text)


def _load_optional_csv(path) -> pd.DataFrame | None:
    """Load an optional CSV artifact with conservative error handling."""
    try:
        if path is None:
            return None

        path = Path(path)

        if not path.exists():
            return None

        df = pd.read_csv(path)

        if df.empty:
            return None

        return df
    except Exception:
        return None


def _unique_values_from_tables(
    tables: list[pd.DataFrame | None],
    column: str,
) -> list[str]:
    """Return sorted unique non-empty values from optional tables."""
    values: set[str] = set()

    for table in tables:
        if table is None or table.empty or column not in table.columns:
            continue

        for value in table[column].dropna().astype(str):
            cleaned = value.strip()
            if cleaned:
                values.add(cleaned)

    return sorted(values)


def _boolean_field_ok(
    tables: list[pd.DataFrame | None],
    column: str,
    expected: bool = False,
) -> bool:
    """Return True when all present boolean-like values match expected."""
    found_any = False

    for table in tables:
        if table is None or table.empty or column not in table.columns:
            continue

        found_any = True

        for value in table[column].fillna(expected):
            if isinstance(value, str):
                value_bool = value.strip().lower() in {"true", "1", "yes"}
            else:
                value_bool = bool(value)

            if value_bool != expected:
                return False

    return found_any


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


def _load_operational_review_controls() -> dict[str, object]:
    """Load operational review/control artifacts for Monte Carlo context.

    These controls are attached as run-level governance context only. Analyst
    review, false-positive, source-freshness, and run-manifest artifacts are not
    used as Monte Carlo inputs and do not change simulated scores.
    """
    analyst_summary = _load_optional_csv(ANALYST_REVIEW_SUMMARY_TABLE)
    false_positive_summary = _load_optional_csv(FALSE_POSITIVE_SUMMARY_TABLE)
    source_freshness_summary = _load_optional_csv(SOURCE_FRESHNESS_SUMMARY_TABLE)
    run_manifest_summary = _load_optional_csv(RUN_MANIFEST_SUMMARY_TABLE)

    analyst_queue_records = _summary_value_for_area(
        analyst_summary,
        "Review queue records",
    )
    review_questions = _summary_value_for_area(
        analyst_summary,
        "Review questions",
    )
    false_positive_control_counts = _summary_value_for_area(
        false_positive_summary,
        "Control status counts",
    )
    false_positive_checklist_rows = _summary_value_for_area(
        false_positive_summary,
        "False-positive review checklist",
    )
    source_freshness_posture = _summary_value_for_area(
        source_freshness_summary,
        "Overall freshness posture",
        value_column="status",
    )
    source_freshness_counts = _summary_value_for_area(
        source_freshness_summary,
        "Freshness status counts",
    )

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
        "analyst_queue_records": analyst_queue_records,
        "review_questions": review_questions,
        "analyst_review_current_use": ANALYST_REVIEW_CURRENT_USE,
        "analyst_review_production_score_change": ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
        "false_positive_controls_available": false_positive_summary is not None
        and not false_positive_summary.empty,
        "false_positive_control_counts": false_positive_control_counts,
        "false_positive_checklist_rows": false_positive_checklist_rows,
        "false_positive_current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        "false_positive_production_score_change": (
            FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE
        ),
        "source_freshness_available": source_freshness_summary is not None
        and not source_freshness_summary.empty,
        "source_freshness_posture": source_freshness_posture,
        "source_freshness_counts": source_freshness_counts,
        "source_freshness_current_use": SOURCE_FRESHNESS_CURRENT_USE,
        "source_freshness_production_score_change": (
            SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE
        ),
        "run_manifest_available": run_manifest_summary is not None
        and not run_manifest_summary.empty,
        "run_manifest_run_id": run_id,
        "run_manifest_model_version": model_version,
        "run_manifest_production_score_change": manifest_score_change,
        "run_manifest_current_use": RUN_MANIFEST_CURRENT_USE,
        "all_operational_controls_score_change_ok": all(
            value == "none"
            for value in [
                ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
                FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
                SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
                RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
            ]
        ),
    }


def _add_operational_review_controls(out: pd.DataFrame) -> pd.DataFrame:
    """Attach operational review/control flags to Monte Carlo output."""
    if out.empty:
        return out

    working = out.copy()
    controls = _load_operational_review_controls()

    working["analyst_review_available"] = bool(
        controls["analyst_review_available"]
    )
    working["analyst_review_used_in_monte_carlo"] = False
    working["analyst_review_current_use"] = str(
        controls["analyst_review_current_use"]
    )
    working["analyst_review_production_score_change"] = str(
        controls["analyst_review_production_score_change"]
    )
    working["analyst_review_queue_records"] = str(
        controls["analyst_queue_records"]
    )
    working["analyst_review_questions"] = str(controls["review_questions"])

    working["false_positive_controls_available"] = bool(
        controls["false_positive_controls_available"]
    )
    working["false_positive_controls_used_in_monte_carlo"] = False
    working["false_positive_controls_current_use"] = str(
        controls["false_positive_current_use"]
    )
    working["false_positive_controls_production_score_change"] = str(
        controls["false_positive_production_score_change"]
    )
    working["false_positive_control_counts"] = str(
        controls["false_positive_control_counts"]
    )
    working["false_positive_checklist_rows"] = str(
        controls["false_positive_checklist_rows"]
    )

    working["source_freshness_available"] = bool(
        controls["source_freshness_available"]
    )
    working["source_freshness_used_in_monte_carlo"] = False
    working["source_freshness_current_use"] = str(
        controls["source_freshness_current_use"]
    )
    working["source_freshness_production_score_change"] = str(
        controls["source_freshness_production_score_change"]
    )
    working["source_freshness_posture"] = str(
        controls["source_freshness_posture"]
    )
    working["source_freshness_counts"] = str(
        controls["source_freshness_counts"]
    )

    working["run_manifest_available"] = bool(controls["run_manifest_available"])
    working["run_manifest_used_in_monte_carlo"] = False
    working["run_manifest_current_use"] = str(controls["run_manifest_current_use"])
    working["run_manifest_run_id"] = str(controls["run_manifest_run_id"])
    working["run_manifest_model_version"] = str(
        controls["run_manifest_model_version"]
    )
    working["run_manifest_production_score_change"] = str(
        controls["run_manifest_production_score_change"]
    )

    working["operational_controls_used_in_monte_carlo"] = False
    working["operational_controls_score_change_ok"] = bool(
        controls["all_operational_controls_score_change_ok"]
    )
    working["operational_controls_note"] = (
        "Analyst review, false-positive controls, source freshness, and run "
        "manifest artifacts attached for governance context only; not used in "
        "Monte Carlo score simulation."
    )

    return working


def _load_wartime_typology_controls() -> dict[str, object]:
    """Load wartime AML/CFT typology controls for Monte Carlo context.

    These controls are attached as run-level governance context only. Typology
    artifacts are not used as Monte Carlo inputs and do not change simulated scores.
    """
    register = _load_optional_csv(WARTIME_AML_TYPOLOGY_REGISTER_TABLE)
    layer_map = _load_optional_csv(WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE)
    summary = _load_optional_csv(WARTIME_AML_TYPOLOGY_SUMMARY_TABLE)

    tables = [register, layer_map, summary]

    current_use_values = _unique_values_from_tables(tables, "current_use")
    prohibited_use_values = _unique_values_from_tables(tables, "prohibited_use")
    production_score_change_values = _unique_values_from_tables(
        tables,
        "production_score_change",
    )

    typology_family_count = 0
    if register is not None and not register.empty and "typology_family" in register.columns:
        typology_family_count = int(register["typology_family"].nunique(dropna=True))

    return {
        "available": register is not None and not register.empty,
        "register_rows": 0 if register is None else len(register),
        "layer_map_rows": 0 if layer_map is None else len(layer_map),
        "summary_rows": 0 if summary is None else len(summary),
        "typology_family_count": typology_family_count,
        "current_use_values": current_use_values,
        "prohibited_use_values": prohibited_use_values,
        "production_score_change_values": production_score_change_values,
        "current_use_ok": (
            WARTIME_AML_TYPOLOGY_CURRENT_USE in current_use_values
            if current_use_values
            else False
        ),
        "prohibited_use_ok": (
            WARTIME_AML_TYPOLOGY_PROHIBITED_USE in prohibited_use_values
            if prohibited_use_values
            else False
        ),
        "score_change_ok": (
            WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE
            in production_score_change_values
            if production_score_change_values
            else False
        ),
    }


def _load_fiu_context_controls() -> dict[str, object]:
    """Load official FIU/SFMS context controls for Monte Carlo context.

    These controls are attached as run-level governance context only. FIU/SFMS
    artifacts are not used as Monte Carlo inputs and do not change simulated scores.
    """
    source_register = _load_optional_csv(FIU_OFFICIAL_SOURCE_REGISTER_TABLE)
    reporting_stats = _load_optional_csv(FIU_REPORTING_STATISTICS_CONTEXT_TABLE)
    case_referrals = _load_optional_csv(FIU_CASE_REFERRAL_CONTEXT_TABLE)
    typology_support = _load_optional_csv(FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE)
    summary = _load_optional_csv(FIU_CONTEXT_SUMMARY_TABLE)

    tables = [source_register, reporting_stats, case_referrals, typology_support, summary]

    current_use_values = _unique_values_from_tables(tables, "current_use")
    prohibited_use_values = _unique_values_from_tables(tables, "prohibited_use")
    production_score_change_values = _unique_values_from_tables(
        tables,
        "production_score_change",
    )

    used_in_scoring_ok = _boolean_field_ok(tables, "used_in_waris_scoring", False)
    used_in_monte_carlo_ok = _boolean_field_ok(tables, "used_in_monte_carlo", False)

    q1_2025_reports = "not_available"
    suspicious_share = "not_available"
    if reporting_stats is not None and not reporting_stats.empty:
        if {"metric_name", "metric_value"}.issubset(reporting_stats.columns):
            reports = reporting_stats[
                reporting_stats["metric_name"]
                .fillna("")
                .astype(str)
                .eq("financial_transaction_reports_received_and_processed")
            ]
            if not reports.empty:
                q1_2025_reports = str(reports.iloc[0].get("metric_value", "not_available"))

            suspicious = reporting_stats[
                reporting_stats["metric_name"]
                .fillna("")
                .astype(str)
                .eq("suspicious_transaction_activity_report_share")
            ]
            if not suspicious.empty:
                suspicious_share = str(suspicious.iloc[0].get("metric_value", "not_available"))

    q1_2026_referrals = "not_available"
    q1_2026_funds_uah_mln = "not_available"
    if case_referrals is not None and not case_referrals.empty:
        if {"person_category", "case_referrals_and_additional_referrals"}.issubset(
            case_referrals.columns
        ):
            total = case_referrals[
                case_referrals["person_category"].fillna("").astype(str).eq("total")
            ]
            if not total.empty:
                q1_2026_referrals = str(
                    total.iloc[0].get(
                        "case_referrals_and_additional_referrals",
                        "not_available",
                    )
                )
                q1_2026_funds_uah_mln = str(
                    total.iloc[0].get(
                        "funds_related_to_crime_uah_mln",
                        "not_available",
                    )
                )

    return {
        "available": source_register is not None and not source_register.empty,
        "source_register_rows": 0 if source_register is None else len(source_register),
        "reporting_stat_rows": 0 if reporting_stats is None else len(reporting_stats),
        "case_referral_rows": 0 if case_referrals is None else len(case_referrals),
        "typology_support_rows": 0 if typology_support is None else len(typology_support),
        "summary_rows": 0 if summary is None else len(summary),
        "q1_2025_reports": q1_2025_reports,
        "suspicious_share": suspicious_share,
        "q1_2026_referrals": q1_2026_referrals,
        "q1_2026_funds_uah_mln": q1_2026_funds_uah_mln,
        "current_use_values": current_use_values,
        "prohibited_use_values": prohibited_use_values,
        "production_score_change_values": production_score_change_values,
        "current_use_ok": (
            FIU_CONTEXT_CURRENT_USE in current_use_values
            if current_use_values
            else False
        ),
        "prohibited_use_ok": (
            FIU_CONTEXT_PROHIBITED_USE in prohibited_use_values
            if prohibited_use_values
            else False
        ),
        "score_change_ok": (
            FIU_CONTEXT_PRODUCTION_SCORE_CHANGE in production_score_change_values
            if production_score_change_values
            else False
        ),
        "used_in_scoring_ok": used_in_scoring_ok,
        "used_in_monte_carlo_ok": used_in_monte_carlo_ok,
    }


def _add_wartime_typology_and_fiu_controls(out: pd.DataFrame) -> pd.DataFrame:
    """Attach typology and FIU/SFMS governance flags to Monte Carlo output."""
    if out.empty:
        return out

    working = out.copy()

    typology = _load_wartime_typology_controls()
    fiu = _load_fiu_context_controls()

    working["wartime_aml_typology_available"] = bool(typology["available"])
    working["wartime_aml_typology_used_in_monte_carlo"] = False
    working["wartime_aml_typology_current_use"] = (
        "; ".join(typology["current_use_values"]) or "not_available"
    )
    working["wartime_aml_typology_expected_current_use"] = (
        WARTIME_AML_TYPOLOGY_CURRENT_USE
    )
    working["wartime_aml_typology_prohibited_use"] = (
        "; ".join(typology["prohibited_use_values"]) or "not_available"
    )
    working["wartime_aml_typology_expected_prohibited_use"] = (
        WARTIME_AML_TYPOLOGY_PROHIBITED_USE
    )
    working["wartime_aml_typology_production_score_change"] = (
        "; ".join(typology["production_score_change_values"]) or "not_available"
    )
    working["wartime_aml_typology_expected_production_score_change"] = (
        WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE
    )
    working["wartime_aml_typology_current_use_ok"] = bool(typology["current_use_ok"])
    working["wartime_aml_typology_prohibited_use_ok"] = bool(
        typology["prohibited_use_ok"]
    )
    working["wartime_aml_typology_score_change_ok"] = bool(typology["score_change_ok"])
    working["wartime_aml_typology_register_rows"] = int(typology["register_rows"])
    working["wartime_aml_typology_layer_map_rows"] = int(typology["layer_map_rows"])
    working["wartime_aml_typology_family_count"] = int(
        typology["typology_family_count"]
    )
    working["wartime_aml_typology_control_note"] = (
        "Wartime AML/CFT typology artifacts attached for governance context only; "
        "not used in Monte Carlo score simulation."
        if typology["available"]
        else "Wartime AML/CFT typology artifacts were not available for this run."
    )

    working["fiu_context_available"] = bool(fiu["available"])
    working["fiu_context_used_in_monte_carlo"] = False
    working["fiu_context_current_use"] = (
        "; ".join(fiu["current_use_values"]) or "not_available"
    )
    working["fiu_context_expected_current_use"] = FIU_CONTEXT_CURRENT_USE
    working["fiu_context_prohibited_use"] = (
        "; ".join(fiu["prohibited_use_values"]) or "not_available"
    )
    working["fiu_context_expected_prohibited_use"] = FIU_CONTEXT_PROHIBITED_USE
    working["fiu_context_production_score_change"] = (
        "; ".join(fiu["production_score_change_values"]) or "not_available"
    )
    working["fiu_context_expected_production_score_change"] = (
        FIU_CONTEXT_PRODUCTION_SCORE_CHANGE
    )
    working["fiu_context_current_use_ok"] = bool(fiu["current_use_ok"])
    working["fiu_context_prohibited_use_ok"] = bool(fiu["prohibited_use_ok"])
    working["fiu_context_score_change_ok"] = bool(fiu["score_change_ok"])
    working["fiu_context_used_in_scoring_ok"] = bool(fiu["used_in_scoring_ok"])
    working["fiu_context_used_in_monte_carlo_ok"] = bool(
        fiu["used_in_monte_carlo_ok"]
    )
    working["fiu_context_source_register_rows"] = int(fiu["source_register_rows"])
    working["fiu_context_reporting_stat_rows"] = int(fiu["reporting_stat_rows"])
    working["fiu_context_case_referral_rows"] = int(fiu["case_referral_rows"])
    working["fiu_context_typology_support_rows"] = int(fiu["typology_support_rows"])
    working["fiu_context_q1_2025_reports"] = str(fiu["q1_2025_reports"])
    working["fiu_context_suspicious_share"] = str(fiu["suspicious_share"])
    working["fiu_context_q1_2026_referrals"] = str(fiu["q1_2026_referrals"])
    working["fiu_context_q1_2026_funds_uah_mln"] = str(
        fiu["q1_2026_funds_uah_mln"]
    )
    working["fiu_context_control_note"] = (
        "Official FIU/SFMS context artifacts attached for governance context only; "
        "not used in Monte Carlo score simulation."
        if fiu["available"]
        else "Official FIU/SFMS context artifacts were not available for this run."
    )

    return working


def _load_official_baseline_controls() -> pd.DataFrame | None:
    """Load official Ukrstat baseline candidate controls when available.

    The official baseline candidate layer is validation-only. This function only
    attaches governance/control fields to Monte Carlo output. It does not use
    official GRP values in score simulation.
    """
    df = _load_optional_csv(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE)

    if df is None or "oblast" not in df.columns:
        return None

    df = official_baseline_observations(df)
    if df.empty:
        return None

    working = df.copy()
    working["oblast"] = working["oblast"].apply(_normalize_oblast_name)

    keep_cols = [
        col
        for col in [
            "oblast",
            "latest_period",
            "official_regional_baseline_proxy",
            "source_status",
            "validation_status",
            "current_use_in_scoring",
        ]
        if col in working.columns
    ]

    if "oblast" not in keep_cols:
        return None

    working = working[keep_cols].drop_duplicates(subset=["oblast"], keep="first")

    rename_map = {
        "latest_period": "official_baseline_latest_period",
        "official_regional_baseline_proxy": "official_baseline_proxy",
        "source_status": "official_baseline_source_status",
        "validation_status": "official_baseline_validation_status",
        "current_use_in_scoring": "official_baseline_current_use_in_scoring",
    }

    working = working.rename(columns=rename_map)

    working["official_baseline_candidate_available"] = True
    working["official_baseline_used_in_monte_carlo"] = False
    working["official_baseline_control_note"] = (
        "Official Ukrstat baseline candidate attached for governance context only; "
        "not used in Monte Carlo score simulation."
    )

    return working


def _add_official_baseline_controls(out: pd.DataFrame) -> pd.DataFrame:
    """Attach official baseline governance flags to Monte Carlo output."""
    if out.empty or "oblast" not in out.columns:
        return out

    controls = _load_official_baseline_controls()

    if controls is None or controls.empty:
        out = out.copy()
        out["official_baseline_candidate_available"] = False
        out["official_baseline_used_in_monte_carlo"] = False
        out["official_baseline_current_use_in_scoring"] = "not_available"
        out["official_baseline_validation_status"] = "not_available"
        out["official_baseline_control_note"] = (
            "No official Ukrstat baseline candidate artifact was available for this run."
        )
        return out

    merged = out.merge(controls, on="oblast", how="left")

    merged["official_baseline_candidate_available"] = merged[
        "official_baseline_candidate_available"
    ].fillna(False)

    merged["official_baseline_used_in_monte_carlo"] = merged[
        "official_baseline_used_in_monte_carlo"
    ].fillna(False)

    for col, fallback in [
        ("official_baseline_current_use_in_scoring", "not_available"),
        ("official_baseline_validation_status", "not_available"),
        ("official_baseline_source_status", "not_available"),
        ("official_baseline_latest_period", ""),
        ("official_baseline_proxy", ""),
        (
            "official_baseline_control_note",
            "No official baseline candidate matched this oblast.",
        ),
    ]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(fallback)

    return merged


def _load_prozorro_procurement_controls() -> pd.DataFrame | None:
    """Load expanded Prozorro procurement controls when available.

    The expanded Prozorro layer is a review-only procurement feature layer. This
    function attaches governance/context fields to Monte Carlo output. It does
    not use expanded Prozorro values in score simulation.
    """
    features = _load_optional_csv(PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE)

    if features is None:
        return None

    if not {"oblast", "sector"}.issubset(features.columns):
        return None

    working = features.copy()

    for col in [
        "procurement_review_priority_candidate",
        "procurement_intensity_score",
        "procurement_value_score",
        "single_bid_supplier_score",
        "reconstruction_emergency_score",
        "buyer_concentration_score",
    ]:
        if col in working.columns:
            working[col] = pd.to_numeric(working[col], errors="coerce")

    keep_cols = [
        col
        for col in [
            "oblast",
            "sector",
            "procurement_review_priority_candidate",
            "procurement_intensity_score",
            "procurement_value_score",
            "single_bid_supplier_score",
            "reconstruction_emergency_score",
            "buyer_concentration_score",
            "current_use",
            "prohibited_use",
        ]
        if col in working.columns
    ]

    working = working[keep_cols].drop_duplicates(
        subset=["oblast", "sector"],
        keep="first",
    )

    rename_map = {
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
    }

    working = working.rename(columns=rename_map)

    scoring_candidates = _load_optional_csv(PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE)

    score_change_map = None
    if (
        scoring_candidates is not None
        and {"oblast", "sector", "production_score_change"}.issubset(
            scoring_candidates.columns
        )
    ):
        score_change_map = scoring_candidates[
            ["oblast", "sector", "production_score_change"]
        ].drop_duplicates(subset=["oblast", "sector"], keep="first")
        score_change_map = score_change_map.rename(
            columns={
                "production_score_change": (
                    "expanded_prozorro_production_score_change"
                )
            }
        )

    if score_change_map is not None:
        working = working.merge(score_change_map, on=["oblast", "sector"], how="left")
    else:
        working["expanded_prozorro_production_score_change"] = (
            PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
        )

    working["expanded_prozorro_feature_candidate_available"] = True
    working["expanded_prozorro_used_in_monte_carlo"] = False

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

    working["expanded_prozorro_control_note"] = (
        "Expanded Prozorro procurement candidate attached for governance context only; "
        "not used in Monte Carlo score simulation."
    )

    return working


def _add_prozorro_procurement_controls(out: pd.DataFrame) -> pd.DataFrame:
    """Attach expanded Prozorro governance flags to Monte Carlo output."""
    if out.empty or not {"oblast", "sector"}.issubset(out.columns):
        return out

    controls = _load_prozorro_procurement_controls()

    if controls is None or controls.empty:
        out = out.copy()
        out["expanded_prozorro_feature_candidate_available"] = False
        out["expanded_prozorro_used_in_monte_carlo"] = False
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

    merged = out.merge(controls, on=["oblast", "sector"], how="left")

    merged["expanded_prozorro_feature_candidate_available"] = merged[
        "expanded_prozorro_feature_candidate_available"
    ].fillna(False)

    merged["expanded_prozorro_used_in_monte_carlo"] = merged[
        "expanded_prozorro_used_in_monte_carlo"
    ].fillna(False)

    fill_values = {
        "expanded_prozorro_current_use": "not_available",
        "expanded_prozorro_prohibited_use": "not_available",
        "expanded_prozorro_production_score_change": "not_available",
        "expanded_prozorro_expected_current_use": PROZORRO_PROCUREMENT_CURRENT_USE,
        "expanded_prozorro_expected_prohibited_use": PROZORRO_PROCUREMENT_PROHIBITED_USE,
        "expanded_prozorro_expected_production_score_change": (
            PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
        ),
        "expanded_prozorro_current_use_ok": False,
        "expanded_prozorro_prohibited_use_ok": False,
        "expanded_prozorro_score_change_ok": False,
        "expanded_prozorro_control_note": (
            "No expanded Prozorro procurement candidate matched this oblast/sector."
        ),
    }

    for col, fallback in fill_values.items():
        if col in merged.columns:
            merged[col] = merged[col].fillna(fallback)

    numeric_cols = [
        "expanded_prozorro_procurement_review_priority_candidate",
        "expanded_prozorro_procurement_intensity_score",
        "expanded_prozorro_procurement_value_score",
        "expanded_prozorro_single_bid_supplier_score",
        "expanded_prozorro_reconstruction_emergency_score",
        "expanded_prozorro_buyer_concentration_score",
    ]

    for col in numeric_cols:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce")

    return merged


def run_monte_carlo(
    scored: pd.DataFrame,
    runs: int = MONTE_CARLO_RUNS,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Run Monte Carlo robustness testing for WARIS scores.

    The simulation perturbs both:
    - model weights, using a Dirichlet distribution around BASE_WEIGHTS
    - layer values, using small normally distributed noise

    Outputs estimate whether elevated/high review signals remain stable under
    reasonable model uncertainty.

    Official Ukrstat GRP baseline candidates, when present, are attached only as
    validation/governance context. They are not used as Monte Carlo inputs and
    do not change simulated scores.

    Expanded Prozorro procurement candidates, when present, are attached only as
    review/governance context. They are not used as Monte Carlo inputs and do
    not change simulated scores.

    Wartime AML/CFT typology, official FIU/SFMS context, analyst-review,
    false-positive, source-freshness, and run-manifest artifacts, when present,
    are attached only as governance/source/control context. They are not used as
    Monte Carlo inputs and do not change simulated scores.
    """
    rng = np.random.default_rng(seed)

    layer_cols = [col for col in BASE_WEIGHTS.keys() if col in scored.columns]

    if not layer_cols:
        raise ValueError("No BASE_WEIGHTS layer columns were found in scored dataframe.")

    base_w = np.array([BASE_WEIGHTS[col] for col in layer_cols], dtype=float)
    base_w = base_w / base_w.sum()

    # Higher concentration = less weight volatility.
    # 120 keeps weights close to the base model while still testing uncertainty.
    concentration = 120
    alpha = base_w * concentration

    matrix = (
        scored[layer_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .clip(0, 100)
        .to_numpy(dtype=float)
    )

    all_scores = np.empty((len(scored), runs), dtype=float)

    for i in range(runs):
        weights = rng.dirichlet(alpha)

        # Layer-level uncertainty. Four points is intentionally modest because
        # WARIS is a prioritization model, not a precision estimator.
        noise = rng.normal(0, 4, size=matrix.shape)

        noisy_layers = np.clip(matrix + noise, 0, 100)
        all_scores[:, i] = noisy_layers @ weights

    out_cols = [
        col
        for col in ["oblast", "sector", "waris_aml_review_score", "risk_band"]
        if col in scored.columns
    ]

    out = scored[out_cols].copy()

    out["mc_mean_score"] = all_scores.mean(axis=1)
    out["mc_p05_score"] = np.percentile(all_scores, 5, axis=1)
    out["mc_p95_score"] = np.percentile(all_scores, 95, axis=1)
    out["mc_uncertainty_width"] = out["mc_p95_score"] - out["mc_p05_score"]

    if "waris_aml_review_score" in out.columns:
        out["mc_mean_delta_from_base"] = (
            out["mc_mean_score"] - pd.to_numeric(
                out["waris_aml_review_score"],
                errors="coerce",
            )
        )
    else:
        out["mc_mean_delta_from_base"] = np.nan

    out["prob_elevated_or_high"] = (all_scores >= 65).mean(axis=1)
    out["prob_high"] = (all_scores >= 80).mean(axis=1)

    out["robustness_band"] = pd.cut(
        out["prob_elevated_or_high"],
        bins=[-0.01, 0.25, 0.50, 0.75, 1.01],
        labels=[
            "Low robustness",
            "Mixed robustness",
            "Moderate robustness",
            "High robustness",
        ],
    ).astype(str)

    out["uncertainty_band"] = pd.cut(
        out["mc_uncertainty_width"],
        bins=[-0.01, 8, 14, 22, np.inf],
        labels=[
            "Narrow uncertainty",
            "Moderate uncertainty",
            "Wide uncertainty",
            "Very wide uncertainty",
        ],
    ).astype(str)

    out["signal_stability_flag"] = np.select(
        [
            out["prob_elevated_or_high"] >= 0.75,
            out["prob_elevated_or_high"].between(0.25, 0.75, inclusive="left"),
            out["prob_elevated_or_high"] < 0.25,
        ],
        [
            "Stable elevated/high signal under uncertainty",
            "Mixed signal under uncertainty",
            "Not stable as elevated/high under uncertainty",
        ],
        default="Review required",
    )

    out = _add_official_baseline_controls(out)
    out = _add_prozorro_procurement_controls(out)
    out = _add_wartime_typology_and_fiu_controls(out)
    out = _add_operational_review_controls(out)

    for flag_col in [
        "official_baseline_used_in_monte_carlo",
        "expanded_prozorro_used_in_monte_carlo",
        "wartime_aml_typology_used_in_monte_carlo",
        "fiu_context_used_in_monte_carlo",
        "analyst_review_used_in_monte_carlo",
        "false_positive_controls_used_in_monte_carlo",
        "source_freshness_used_in_monte_carlo",
        "run_manifest_used_in_monte_carlo",
        "operational_controls_used_in_monte_carlo",
    ]:
        if flag_col in out.columns:
            out[flag_col] = out[flag_col].fillna(False).astype(bool)

    return (
        out.sort_values(
            ["prob_elevated_or_high", "mc_mean_score"],
            ascending=[False, False],
        )
        .reset_index(drop=True)
    )
