"""Official FIU/SFMS context layer for WARIS.

This module converts official State Financial Monitoring Service of Ukraine
(SFMS/FIU) public documents into transparent source-support artifacts for WARIS.

It does not change WARIS production scoring.

Current use:
    official_fiu_context_and_typology_support_only

Prohibited use:
    direct_scoring_without_change_control

Production score change:
    none

Primary source basis:
    - SFMS information on NABU case referrals, 01.01.2026 to 31.03.2026
    - SFMS statistics on financial transaction reports, 1st quarter of 2025
    - Annual 2023 definitions below are unverified audit material, excluded from exports

Outputs:
    outputs/tables/waris_fiu_official_source_register.csv
    outputs/tables/waris_fiu_reporting_statistics_context.csv
    outputs/tables/waris_fiu_case_referral_context.csv
    outputs/tables/waris_fiu_typology_support_register.csv
    outputs/tables/waris_fiu_context_summary.csv

Downstream controls:
    - false_positive_controls.py documents benign explanations and analyst controls.
    - source_freshness.py monitors whether FIU/SFMS artifacts are present and current.
    - run_manifest.py records FIU/SFMS outputs in the reproducibility inventory.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .reference_evidence import annotate_fiu_sources, annotate_fiu_statistics, annotate_fiu_referrals, annotate_fiu_typologies
from .reference_evidence import select_fiu_public_context
from .config import TABLE_DIR, FIU_PUBLIC_SOURCE_IDS
from .utils import ensure_dirs

try:
    from .config import (
        FIU_OFFICIAL_SOURCE_REGISTER_TABLE,
        FIU_REPORTING_STATISTICS_CONTEXT_TABLE,
        FIU_CASE_REFERRAL_CONTEXT_TABLE,
        FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE,
        FIU_CONTEXT_SUMMARY_TABLE,
        FIU_CONTEXT_CURRENT_USE,
        FIU_CONTEXT_PROHIBITED_USE,
        FIU_CONTEXT_PRODUCTION_SCORE_CHANGE,
        FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
        SOURCE_FRESHNESS_CURRENT_USE,
        SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
        RUN_MANIFEST_CURRENT_USE,
        RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
    )
except ImportError:
    FIU_OFFICIAL_SOURCE_REGISTER_TABLE = (
        TABLE_DIR / "waris_fiu_official_source_register.csv"
    )
    FIU_REPORTING_STATISTICS_CONTEXT_TABLE = (
        TABLE_DIR / "waris_fiu_reporting_statistics_context.csv"
    )
    FIU_CASE_REFERRAL_CONTEXT_TABLE = TABLE_DIR / "waris_fiu_case_referral_context.csv"
    FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE = (
        TABLE_DIR / "waris_fiu_typology_support_register.csv"
    )
    FIU_CONTEXT_SUMMARY_TABLE = TABLE_DIR / "waris_fiu_context_summary.csv"
    FIU_CONTEXT_CURRENT_USE = "official_fiu_context_and_typology_support_only"
    FIU_CONTEXT_PROHIBITED_USE = "direct_scoring_without_change_control"
    FIU_CONTEXT_PRODUCTION_SCORE_CHANGE = "none"
    FALSE_POSITIVE_CONTROLS_CURRENT_USE = "human_review_support_only"
    FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE = "none"
    SOURCE_FRESHNESS_CURRENT_USE = "source_freshness_monitoring_only"
    SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE = "none"
    RUN_MANIFEST_CURRENT_USE = "run_manifest_documentation"
    RUN_MANIFEST_PRODUCTION_SCORE_CHANGE = "none"

FIU_SOURCE_REGISTER_TABLE = FIU_OFFICIAL_SOURCE_REGISTER_TABLE

CURRENT_USE = FIU_CONTEXT_CURRENT_USE
PROHIBITED_USE = FIU_CONTEXT_PROHIBITED_USE
PRODUCTION_SCORE_CHANGE = FIU_CONTEXT_PRODUCTION_SCORE_CHANGE

SFMS_WEBSITE_URL = "https://fiu.gov.ua/en/"
SFMS_DOCUMENT_SOURCE_MODE = "user_provided_official_sfms_documents"
CONTROL_NOTE = (
    "Official FIU/SFMS context artifact only. Not an allegation, not an "
    "entity-level finding, and not used in WARIS scoring without change control."
)


@dataclass(frozen=True)
class FiuOfficialSource:
    source_id: str
    source_name: str
    source_type: str
    reporting_period: str
    source_url_or_file: str
    source_mode: str
    document_scope: str
    waris_relevance: str
    current_use: str
    prohibited_use: str
    production_score_change: str
    used_in_waris_scoring: bool
    used_in_monte_carlo: bool
    control_note: str
    notes: str


@dataclass(frozen=True)
class FiuReportingStatistic:
    metric_id: str
    reporting_period: str
    metric_name: str
    metric_value: float
    metric_unit: str
    context_category: str
    waris_layer_candidates: str
    current_use: str
    prohibited_use: str
    production_score_change: str
    used_in_waris_scoring: bool
    used_in_monte_carlo: bool
    source_basis: str
    control_note: str
    notes: str


@dataclass(frozen=True)
class FiuCaseReferralContext:
    referral_context_id: str
    reporting_period: str
    institution_or_investigation_context: str
    person_category: str
    case_referrals_and_additional_referrals: int
    funds_related_to_crime_uah_mln: float
    waris_context_category: str
    waris_layer_candidates: str
    current_use: str
    prohibited_use: str
    production_score_change: str
    used_in_waris_scoring: bool
    used_in_monte_carlo: bool
    source_basis: str
    control_note: str
    notes: str


@dataclass(frozen=True)
class FiuTypologySupport:
    typology_support_id: str
    typology_name: str
    typology_family: str
    official_source_support: str
    waris_layer_candidates: str
    possible_future_indicator_direction: str
    current_use: str
    prohibited_use: str
    production_score_change: str
    used_in_waris_scoring: bool
    used_in_monte_carlo: bool
    source_basis: str
    control_note: str
    notes: str


def _control_kwargs() -> dict[str, object]:
    """Return common no-scoring control kwargs for dataclass rows."""
    return {
        "used_in_waris_scoring": False,
        "used_in_monte_carlo": False,
        "control_note": CONTROL_NOTE,
    }


def _add_control_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure standard FIU context control fields are present."""
    if df.empty:
        return df

    out = df.copy()
    out["current_use"] = CURRENT_USE
    out["prohibited_use"] = PROHIBITED_USE
    out["production_score_change"] = PRODUCTION_SCORE_CHANGE

    if "used_in_waris_scoring" not in out.columns:
        out["used_in_waris_scoring"] = False

    if "used_in_monte_carlo" not in out.columns:
        out["used_in_monte_carlo"] = False

    if "control_note" not in out.columns:
        out["control_note"] = CONTROL_NOTE

    return out


def _safe_table(filename: str) -> pd.DataFrame | None:
    """Load an optional downstream control table."""
    path = TABLE_DIR / filename

    if not path.exists():
        return None

    try:
        df = pd.read_csv(path)
    except Exception:
        return None

    return df


def _downstream_control_context() -> dict[str, object]:
    """Return status of downstream control layers relevant to FIU/SFMS context."""
    false_positive_summary = _safe_table("false_positive_summary.csv")
    source_freshness_summary = _safe_table("source_freshness_summary.csv")
    run_manifest_summary = _safe_table("run_manifest_summary.csv")
    operational_crosswalk = _safe_table("operational_review_artifact_crosswalk.csv")

    source_freshness_posture = "not_available"
    if source_freshness_summary is not None and not source_freshness_summary.empty:
        if "summary_area" in source_freshness_summary.columns:
            posture = source_freshness_summary[
                source_freshness_summary["summary_area"]
                .fillna("")
                .astype(str)
                .eq("Overall freshness posture")
            ]
            if not posture.empty:
                source_freshness_posture = str(posture.iloc[0].get("status", "not_available"))

    false_positive_status = "not_available"
    if false_positive_summary is not None and not false_positive_summary.empty:
        if "summary_area" in false_positive_summary.columns:
            controls = false_positive_summary[
                false_positive_summary["summary_area"]
                .fillna("")
                .astype(str)
                .eq("Control status counts")
            ]
            if not controls.empty:
                false_positive_status = str(controls.iloc[0].get("value", "not_available"))

    return {
        "false_positive_controls_available": false_positive_summary is not None
        and not false_positive_summary.empty,
        "false_positive_control_status": false_positive_status,
        "source_freshness_available": source_freshness_summary is not None
        and not source_freshness_summary.empty,
        "source_freshness_posture": source_freshness_posture,
        "run_manifest_available": run_manifest_summary is not None
        and not run_manifest_summary.empty,
        "operational_crosswalk_available": operational_crosswalk is not None
        and not operational_crosswalk.empty,
    }


def _source_register_rows() -> list[FiuOfficialSource]:
    """Return official FIU source register rows."""
    return [
        FiuOfficialSource(
            source_id="FIU-SRC-001",
            source_name=(
                "Information on case referrals and additional case referrals "
                "submitted by the SFMS to NABU"
            ),
            source_type="official_fiu_case_referral_statistics",
            reporting_period="2026-Q1",
            source_url_or_file="ENG_I quarter_NABU.pdf",
            source_mode=SFMS_DOCUMENT_SOURCE_MODE,
            document_scope=(
                "NABU-related SFMS case referrals and associated funds by category "
                "of persons."
            ),
            waris_relevance=(
                "Supports corruption, public-sector exposure, state-enterprise, "
                "and high-level public-function typology context."
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            notes=(
                "Official national-level context only. Does not imply misconduct by "
                "any oblast, sector, entity, or person in WARIS."
            ),
        ),
        FiuOfficialSource(
            source_id="FIU-SRC-002",
            source_name=(
                "Statistics on financial transaction reports received by the SFMS "
                "during the 1st quarter of 2025"
            ),
            source_type="official_fiu_reporting_statistics",
            reporting_period="2025-Q1",
            source_url_or_file="ENG_Statistic I quarter 2025.pdf",
            source_mode=SFMS_DOCUMENT_SOURCE_MODE,
            document_scope=(
                "National financial-monitoring reporting volumes, reporting-entity "
                "composition, error rate, and report-type distribution."
            ),
            waris_relevance=(
                "Supports national financial-supervision context and reporting-system "
                "maturity discussion."
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            notes=(
                "National context only. Not oblast-level or sector-level scoring data."
            ),
        ),
        FiuOfficialSource(
            source_id="FIU-SRC-003",
            source_name=(
                "Annual Report of the State Financial Monitoring Service of Ukraine "
                "for 2023"
            ),
            source_type="official_fiu_annual_report",
            reporting_period="2023",
            source_url_or_file="Report_2023_ENG.pdf",
            source_mode=SFMS_DOCUMENT_SOURCE_MODE,
            document_scope=(
                "SFMS role under martial law, analytical activity, financial "
                "investigations, case referrals, interagency cooperation, "
                "international cooperation, and strategic directions."
            ),
            waris_relevance=(
                "Supports wartime AML/CFT typologies, institutional coordination, "
                "sanctions enforcement, FIU-to-FIU exchange, and governance framing."
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            notes=(
                "Official source-support artifact. Does not change WARIS risk layers "
                "or composite scores."
            ),
        ),
    ]


def _reporting_statistics_rows() -> list[FiuReportingStatistic]:
    """Return official SFMS Q1 2025 reporting-statistics context rows."""
    source = (
        "SFMS statistics on financial transaction reports received during "
        "the 1st quarter of 2025"
    )

    return [
        FiuReportingStatistic(
            metric_id="FIU-STAT-001",
            reporting_period="2025-Q1",
            metric_name="financial_transaction_reports_received_and_processed",
            metric_value=448075,
            metric_unit="reports",
            context_category="reporting_volume",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes=(
                "National reporting-volume context only. Indicates reporting-system "
                "load and monitoring activity, not oblast or sector risk."
            ),
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-002",
            reporting_period="2025-Q1",
            metric_name="year_over_year_report_growth",
            metric_value=18.35,
            metric_unit="percent",
            context_category="reporting_volume_change",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes=(
                "Supports national monitoring-intensity context and possible future "
                "time-series monitoring."
            ),
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-003",
            reporting_period="2025-Q1",
            metric_name="bank_share_of_reports",
            metric_value=99.49,
            metric_unit="percent",
            context_category="reporting_entity_composition",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes=(
                "Shows banks dominate the reporting system. This supports governance "
                "context, not scoring."
            ),
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-004",
            reporting_period="2025-Q1",
            metric_name="non_bank_share_of_reports",
            metric_value=0.51,
            metric_unit="percent",
            context_category="reporting_entity_composition",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes="Complements bank-share metric for reporting-entity context.",
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-005",
            reporting_period="2025-Q1",
            metric_name="report_error_share",
            metric_value=0.08,
            metric_unit="percent",
            context_category="data_quality",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes=(
                "Supports official-source quality/context discussion. Not used as a "
                "WARIS score adjustment."
            ),
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-006",
            reporting_period="2025-Q1",
            metric_name="successfully_submitted_report_share",
            metric_value=99.92,
            metric_unit="percent",
            context_category="data_quality",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes=("The source states 99.92 percent submitted reports; its denominator is not explicit. "
                   "The inherited metric label is retained for compatibility and does not validate channel reliability."),
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-007",
            reporting_period="2025-Q1",
            metric_name="threshold_transaction_report_share",
            metric_value=77.81,
            metric_unit="percent",
            context_category="report_type_distribution",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes="National distribution of report types.",
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-008",
            reporting_period="2025-Q1",
            metric_name="suspicious_transaction_activity_report_share",
            metric_value=22.03,
            metric_unit="percent",
            context_category="report_type_distribution",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes=(
                "Useful as national context for suspicious activity reporting share; "
                "not a regional scoring input."
            ),
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-009",
            reporting_period="2025-Q1",
            metric_name="threshold_and_suspicious_report_share",
            metric_value=0.04,
            metric_unit="percent",
            context_category="report_type_distribution",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes="National distribution of report types.",
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-010",
            reporting_period="2025-Q1",
            metric_name="financial_transaction_tracking_monitoring_share",
            metric_value=0.12,
            metric_unit="percent",
            context_category="report_type_distribution",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes="National distribution of report types.",
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-011",
            reporting_period="2025-Q1",
            metric_name="bank_reports_electronic",
            metric_value=445093,
            metric_unit="reports",
            context_category="submission_channel",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes="Banks submitted reports electronically in this official table.",
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-012",
            reporting_period="2025-Q1",
            metric_name="non_bank_reports_electronic",
            metric_value=2108,
            metric_unit="reports",
            context_category="submission_channel",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes="Non-bank electronic-reporting context.",
        ),
        FiuReportingStatistic(
            metric_id="FIU-STAT-013",
            reporting_period="2025-Q1",
            metric_name="non_bank_reports_paper",
            metric_value=155,
            metric_unit="reports",
            context_category="submission_channel",
            waris_layer_candidates="financial_supervision_exposure",
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=source,
            notes="Non-bank paper-reporting context.",
        ),
    ]


def _case_referral_rows() -> list[FiuCaseReferralContext]:
    """Return official SFMS-to-NABU Q1 2026 case-referral context rows."""
    source = (
        "SFMS information on case referrals and additional case referrals prepared "
        "and submitted to NABU from 01.01.2026 to 31.03.2026"
    )

    rows = [
        ("FIU-NABU-001", "members of the Cabinet of Ministers of Ukraine and their deputies", 13, 0.00),
        ("FIU-NABU-002", "members of parliament and deputies of local councils", 5, 41.28),
        ("FIU-NABU-003", "heads of the central executive authorities", 4, 0.00),
        ("FIU-NABU-004", "civil servants", 7, 27117.94),
        ("FIU-NABU-005", "judges", 2, 0.00),
        ("FIU-NABU-006", "senior commanders and the rest of the soldiers", 17, 16.57),
        ("FIU-NABU-007", "heads of state enterprises", 7, 63.08),
        ("FIU-NABU-008", "heads of the central executive authorities", 1, 2.24),
        ("FIU-NABU-009", "other persons", 14, 0.00),
        ("FIU-NABU-010", "total", 70, 27241.11),
    ]

    out = []

    for referral_id, category, count, funds in rows:
        out.append(
            FiuCaseReferralContext(
                referral_context_id=referral_id,
                reporting_period="2026-Q1",
                institution_or_investigation_context="NABU_case_referrals",
                person_category=category,
                case_referrals_and_additional_referrals=int(count),
                funds_related_to_crime_uah_mln=float(funds),
                waris_context_category="public_sector_corruption_and_high_official_exposure",
                waris_layer_candidates=(
                    "ownership_opacity_risk; procurement_integrity_risk; "
                    "financial_supervision_exposure"
                ),
                current_use=CURRENT_USE,
                prohibited_use=PROHIBITED_USE,
                production_score_change=PRODUCTION_SCORE_CHANGE,
                **_control_kwargs(),
                source_basis=source,
                notes=(
                    "Official national-level case-referral context only. It does not "
                    "identify WARIS oblasts or sectors and does not alter scores."
                ),
            )
        )

    return out


def _typology_support_rows() -> list[FiuTypologySupport]:
    """Return official FIU typology-support rows."""
    annual_report = "SFMS Annual Report for 2023"
    q1_stats = "SFMS statistics on financial transaction reports, 2025-Q1"
    nabu = "SFMS-to-NABU case-referral information, 2026-Q1"

    return [
        FiuTypologySupport(
            typology_support_id="FIU-TYP-001",
            typology_name="Countering war and terrorism financing",
            typology_family="war_and_terrorism_financing",
            official_source_support=(
                "Annual report section 4.3.1 and martial-law activity narrative."
            ),
            waris_layer_candidates="sanctions_exposure_risk; conflict_plausibility_gap; tbml_risk",
            possible_future_indicator_direction=(
                "Official typology register links; sanctions and war-financing references; "
                "aggregate FIU case-referral trends."
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=annual_report,
            notes="Supports typology register and governance narrative only.",
        ),
        FiuTypologySupport(
            typology_support_id="FIU-TYP-002",
            typology_name="Money laundering from corruption",
            typology_family="corruption_laundering",
            official_source_support=(
                "Annual report section 4.3.2 and NABU referral statistics."
            ),
            waris_layer_candidates="ownership_opacity_risk; procurement_integrity_risk; financial_supervision_exposure",
            possible_future_indicator_direction=(
                "Public-sector referral context; corruption typology references; "
                "state-enterprise and public-function exposure categories."
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=f"{annual_report}; {nabu}",
            notes=(
                "Do not infer wrongdoing by public categories; use only as official "
                "context for typology support."
            ),
        ),
        FiuTypologySupport(
            typology_support_id="FIU-TYP-003",
            typology_name="Transactions related to budget funds and state assets",
            typology_family="budget_and_state_assets",
            official_source_support="Annual report section 4.3.3.",
            waris_layer_candidates="procurement_integrity_risk; ownership_opacity_risk; revenue_anomaly_risk",
            possible_future_indicator_direction=(
                "Budget-fund typology mapping; public procurement context; state-asset "
                "exposure references."
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=annual_report,
            notes="Relevant to procurement and reconstruction review, not scoring.",
        ),
        FiuTypologySupport(
            typology_support_id="FIU-TYP-004",
            typology_name=(
                "Misuse of funds allocated for humanitarian projects, social projects, "
                "and reconstruction/restoration"
            ),
            typology_family="humanitarian_reconstruction_finance",
            official_source_support="Annual report section 4.3.4.",
            waris_layer_candidates="procurement_integrity_risk; tbml_risk; financial_supervision_exposure",
            possible_future_indicator_direction=(
                "Humanitarian/reconstruction keywords; Prozorro emergency procurement "
                "features; official typology references."
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=annual_report,
            notes=(
                "Strong support for the review-only expanded Prozorro procurement "
                "feature layer."
            ),
        ),
        FiuTypologySupport(
            typology_support_id="FIU-TYP-005",
            typology_name="Fraudulent acquisition of funds from citizens and legal entities",
            typology_family="fraud_proceeds_laundering",
            official_source_support="Annual report section 4.3.5.",
            waris_layer_candidates="financial_supervision_exposure; revenue_anomaly_risk; ownership_opacity_risk",
            possible_future_indicator_direction=(
                "Official fraud typology references; reporting-statistics context; "
                "future public alerts if available."
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=annual_report,
            notes="Typology support only.",
        ),
        FiuTypologySupport(
            typology_support_id="FIU-TYP-006",
            typology_name="Financial monitoring reporting-system intensity",
            typology_family="financial_supervision_context",
            official_source_support=(
                "Q1 2025 reporting statistics: national report volume, suspicious "
                "transaction share, bank/non-bank reporting share, and error rate."
            ),
            waris_layer_candidates="financial_supervision_exposure",
            possible_future_indicator_direction=(
                "National FIU reporting trend monitor; annual/quarterly context layer."
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=q1_stats,
            notes="National-level reporting context only.",
        ),
        FiuTypologySupport(
            typology_support_id="FIU-TYP-007",
            typology_name="International cooperation and FIU-to-FIU exchange",
            typology_family="institutional_coordination",
            official_source_support=(
                "Annual report sections on FATF, Egmont Group, MONEYVAL, EU, UN, "
                "and exchange with foreign FIUs."
            ),
            waris_layer_candidates="financial_supervision_exposure; sanctions_exposure_risk",
            possible_future_indicator_direction=(
                "Institutional coordination source register; governance evidence for "
                "wartime AML/CFT resilience."
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            **_control_kwargs(),
            source_basis=annual_report,
            notes="Supports governance and model-risk documentation.",
        ),
    ]


def build_fiu_official_source_register() -> pd.DataFrame:
    """Build the FIU official source register."""
    ensure_dirs([TABLE_DIR])

    out = pd.DataFrame([row.__dict__ for row in _source_register_rows()])
    out = _add_control_fields(out)
    out = annotate_fiu_sources(out)
    out = out.loc[out.source_id.isin(FIU_PUBLIC_SOURCE_IDS)].copy()
    out.to_csv(FIU_SOURCE_REGISTER_TABLE, index=False)
    return out


def build_fiu_reporting_statistics_context() -> pd.DataFrame:
    """Build the FIU reporting-statistics context table."""
    ensure_dirs([TABLE_DIR])

    out = pd.DataFrame([row.__dict__ for row in _reporting_statistics_rows()])
    out = _add_control_fields(out)
    out = annotate_fiu_statistics(out)
    out = select_fiu_public_context(out, "statistics").frame
    out.to_csv(FIU_REPORTING_STATISTICS_CONTEXT_TABLE, index=False)
    return out


def build_fiu_case_referral_context() -> pd.DataFrame:
    """Build the FIU case-referral context table."""
    ensure_dirs([TABLE_DIR])

    out = pd.DataFrame([row.__dict__ for row in _case_referral_rows()])
    out = _add_control_fields(out)
    out = annotate_fiu_referrals(out)
    out = select_fiu_public_context(out, "referrals").frame
    out.to_csv(FIU_CASE_REFERRAL_CONTEXT_TABLE, index=False)
    return out


def build_fiu_typology_support_register() -> pd.DataFrame:
    """Build the FIU typology-support register."""
    ensure_dirs([TABLE_DIR])

    out = pd.DataFrame([row.__dict__ for row in _typology_support_rows()])
    out = _add_control_fields(out)
    out = annotate_fiu_typologies(out)
    out = select_fiu_public_context(out, "typologies").frame
    out.to_csv(FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE, index=False)
    return out


def build_fiu_context_summary(
    source_register: pd.DataFrame,
    reporting_stats: pd.DataFrame,
    case_referrals: pd.DataFrame,
    typology_support: pd.DataFrame,
    downstream_context: dict[str, object] | None = None,
) -> pd.DataFrame:
    """Build a compact FIU-context summary."""
    ensure_dirs([TABLE_DIR])
    downstream_context = downstream_context or _downstream_control_context()

    total_reports_q1_2025 = "not_available"
    suspicious_share_q1_2025 = "not_available"
    total_referrals_q1_2026 = "not_available"
    total_funds_q1_2026 = "not_available"

    if not reporting_stats.empty:
        total_reports = reporting_stats[
            reporting_stats["metric_name"].eq(
                "financial_transaction_reports_received_and_processed"
            )
        ]
        if not total_reports.empty:
            total_reports_q1_2025 = str(total_reports.iloc[0]["metric_value"])

        suspicious_share = reporting_stats[
            reporting_stats["metric_name"].eq(
                "suspicious_transaction_activity_report_share"
            )
        ]
        if not suspicious_share.empty:
            suspicious_share_q1_2025 = str(suspicious_share.iloc[0]["metric_value"])

    if not case_referrals.empty:
        total_row = case_referrals[case_referrals["person_category"].eq("total")]
        if not total_row.empty:
            total_referrals_q1_2026 = str(
                total_row.iloc[0]["case_referrals_and_additional_referrals"]
            )
            total_funds_q1_2026 = str(
                total_row.iloc[0]["funds_related_to_crime_uah_mln"]
            )

    typology_families = (
        typology_support["typology_family"].value_counts().to_dict()
        if not typology_support.empty and "typology_family" in typology_support.columns
        else {}
    )

    all_context = pd.concat(
        [source_register, reporting_stats, case_referrals, typology_support],
        ignore_index=True,
        sort=False,
    )

    current_use_values = (
        sorted(set(all_context["current_use"].dropna().astype(str)))
        if "current_use" in all_context.columns and not all_context.empty
        else []
    )
    prohibited_use_values = (
        sorted(set(all_context["prohibited_use"].dropna().astype(str)))
        if "prohibited_use" in all_context.columns and not all_context.empty
        else []
    )
    production_score_change_values = (
        sorted(set(all_context["production_score_change"].dropna().astype(str)))
        if "production_score_change" in all_context.columns and not all_context.empty
        else []
    )
    scoring_use_ok = (
        not all_context["used_in_waris_scoring"].fillna(False).astype(bool).any()
        if "used_in_waris_scoring" in all_context.columns
        else True
    )
    monte_carlo_use_ok = (
        not all_context["used_in_monte_carlo"].fillna(False).astype(bool).any()
        if "used_in_monte_carlo" in all_context.columns
        else True
    )

    rows = [
        {
            "summary_area": "Reference verification",
            "status": "partial_reference_check_only",
            "value": "Quarterly numeric text checked; six annual/mixed typology rows and FIU-STAT-006 excluded from exports; annual source excluded. Definitions remain private audit material until verified.",
            "recommended_next_action": "See docs/REFERENCE_CHECKS.md. Table creation and control posture are not source verification or release clearance.",
        },
        {
            "summary_area": "Official FIU source register",
            "status": "created" if not source_register.empty else "missing_or_empty",
            "value": len(source_register),
            "recommended_next_action": (
                "Use as official source-support for README, report appendix, "
                "source confidence, and governance documentation."
            ),
        },
        {
            "summary_area": "Financial transaction reporting statistics",
            "status": "created" if not reporting_stats.empty else "missing_or_empty",
            "value": (
                f"2025-Q1 reports={total_reports_q1_2025}; "
                f"suspicious_share_percent={suspicious_share_q1_2025}"
            ),
            "recommended_next_action": (
                "Keep as national-level financial-supervision context only."
            ),
        },
        {
            "summary_area": "NABU case-referral context",
            "status": "created" if not case_referrals.empty else "missing_or_empty",
            "value": (
                f"2026-Q1 referrals={total_referrals_q1_2026}; "
                f"funds_related_to_crime_uah_mln={total_funds_q1_2026}"
            ),
            "recommended_next_action": (
                "Use for corruption/public-sector typology support only; do not "
                "treat as oblast or sector scoring data."
            ),
        },
        {
            "summary_area": "FIU typology support",
            "status": "created" if not typology_support.empty else "missing_or_empty",
            "value": str(typology_families),
            "recommended_next_action": (
                "Map to WARIS typology register and report appendix as official context."
            ),
        },
        {
            "summary_area": "Current use control",
            "status": "control_active",
            "value": CURRENT_USE,
            "recommended_next_action": (
                "Keep FIU context artifacts out of scoring unless a future change-control "
                "branch approves measurable indicators."
            ),
        },
        {
            "summary_area": "Prohibited use control",
            "status": "control_active",
            "value": PROHIBITED_USE,
            "recommended_next_action": (
                "Do not map FIU context directly into scores without data validation, "
                "false-positive controls, SME review, and model change control."
            ),
        },
        {
            "summary_area": "Production score change control",
            "status": "control_active",
            "value": PRODUCTION_SCORE_CHANGE,
            "recommended_next_action": "Maintain production_score_change=none.",
        },
        {
            "summary_area": "Control posture check",
            "status": "pass"
            if (
                current_use_values == [CURRENT_USE]
                and prohibited_use_values == [PROHIBITED_USE]
                and production_score_change_values == [PRODUCTION_SCORE_CHANGE]
                and scoring_use_ok
                and monte_carlo_use_ok
            )
            else "review_required",
            "value": (
                f"current_use_values={current_use_values}; "
                f"prohibited_use_values={prohibited_use_values}; "
                f"production_score_change_values={production_score_change_values}; "
                f"scoring_use_ok={scoring_use_ok}; "
                f"monte_carlo_use_ok={monte_carlo_use_ok}"
            ),
            "recommended_next_action": (
                "Keep FIU/SFMS context artifacts as source support only. Investigate "
                "immediately if any used_in_waris_scoring or used_in_monte_carlo flag becomes true."
            ),
        },
        {
            "summary_area": "False-positive control linkage",
            "status": "available"
            if downstream_context.get("false_positive_controls_available")
            else "not_available",
            "value": downstream_context.get("false_positive_control_status", "not_available"),
            "recommended_next_action": (
                "Use false-positive controls before interpreting FIU/SFMS national "
                "context as relevant to any oblast or sector."
            ),
        },
        {
            "summary_area": "Source freshness linkage",
            "status": "available"
            if downstream_context.get("source_freshness_available")
            else "not_available",
            "value": downstream_context.get("source_freshness_posture", "not_available"),
            "recommended_next_action": (
                "Review source-freshness posture for FIU/SFMS artifacts before "
                "publication or external review."
            ),
        },
        {
            "summary_area": "Run manifest linkage",
            "status": "available"
            if downstream_context.get("run_manifest_available")
            else "not_available",
            "value": RUN_MANIFEST_CURRENT_USE,
            "recommended_next_action": (
                "Confirm FIU/SFMS outputs appear in the run manifest inventory for "
                "reproducibility and audit traceability."
            ),
        },
        {
            "summary_area": "Operational crosswalk linkage",
            "status": "available"
            if downstream_context.get("operational_crosswalk_available")
            else "not_available",
            "value": "operational_review_artifact_crosswalk.csv",
            "recommended_next_action": (
                "Use the operational crosswalk to confirm FIU/SFMS context remains "
                "source support and not a scoring feature."
            ),
        },
    ]

    out = pd.DataFrame(rows)
    out.to_csv(FIU_CONTEXT_SUMMARY_TABLE, index=False)
    return out


def build_fiu_official_context_artifacts() -> dict[str, pd.DataFrame]:
    """Build all official FIU/SFMS context artifacts."""
    source_register = build_fiu_official_source_register()
    reporting_stats = build_fiu_reporting_statistics_context()
    case_referrals = build_fiu_case_referral_context()
    typology_support = build_fiu_typology_support_register()
    downstream_context = _downstream_control_context()
    summary = build_fiu_context_summary(
        source_register=source_register,
        reporting_stats=reporting_stats,
        case_referrals=case_referrals,
        typology_support=typology_support,
        downstream_context=downstream_context,
    )

    return {
        "source_register": source_register,
        "reporting_statistics_context": reporting_stats,
        "case_referral_context": case_referrals,
        "typology_support_register": typology_support,
        "context_summary": summary,
        "downstream_control_context": downstream_context,
    }


def main() -> None:
    """CLI entry point."""
    artifacts = build_fiu_official_context_artifacts()

    print("\nOfficial FIU/SFMS context artifacts created.")
    print(f"- Source register rows: {len(artifacts['source_register'])}")
    print(
        "- Reporting statistics rows: "
        f"{len(artifacts['reporting_statistics_context'])}"
    )
    print(f"- Case-referral context rows: {len(artifacts['case_referral_context'])}")
    print(
        "- Typology-support rows: "
        f"{len(artifacts['typology_support_register'])}"
    )
    print(f"- Context summary rows: {len(artifacts['context_summary'])}")

    print(f"- Source register: {FIU_SOURCE_REGISTER_TABLE}")
    print(f"- Reporting statistics context: {FIU_REPORTING_STATISTICS_CONTEXT_TABLE}")
    print(f"- Case-referral context: {FIU_CASE_REFERRAL_CONTEXT_TABLE}")
    print(f"- Typology-support register: {FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE}")
    print(f"- Context summary: {FIU_CONTEXT_SUMMARY_TABLE}")

    print(
        "\nImportant: These are official FIU/SFMS source-context artifacts only. "
        f"current_use={CURRENT_USE}; prohibited_use={PROHIBITED_USE}; "
        f"production_score_change={PRODUCTION_SCORE_CHANGE}. They do not alter WARIS "
        "risk layers, composite scores, risk bands, review rationales, or Monte Carlo. "
        "False-positive controls, source-freshness monitoring, and the run manifest "
        "should be used as downstream documentation controls."
    )


if __name__ == "__main__":
    main()
