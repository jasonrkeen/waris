"""Recorded human reference review; no network access or scoring integration.

Values were compared with official PDF text on 2026-10-13. Source PDF bytes
were not retained through the direct local session (HTTP 403). These records
do not authenticate the user's historical PDFs or complete annual-report QA.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal
import pandas as pd
from .config import FIU_PUBLIC_REFERENCE_STATUSES, FIU_PUBLIC_REFERENCE_PERIODS

REVIEW_DATE = "2026-10-13"
NABU_URL = "https://fiu.gov.ua/assets/userfiles/440/2026/ENG_I%20quarter_NABU.pdf"
STATS_URL = "https://fiu.gov.ua/assets/userfiles/200/Statistics/2025/ENG_Statistic%20I%20quarter%202025.pdf"
ANNUAL_URL = "https://fiu.gov.ua/assets/userfiles/200/Activity%20reports/Report_2023_ENG.pdf"
NUMERIC_CHECKED = "value_checked_against_official_pdf_text"
UNVERIFIED = "full_text_claims_not_verified"
SOURCE_METADATA = {
    "FIU-SRC-001": (NABU_URL, "1", "quarterly_numeric_text_checked"),
    "FIU-SRC-002": (STATS_URL, "1-2", "quarterly_numeric_text_checked_semantic_caveat"),
    "FIU-SRC-003": (ANNUAL_URL, "not_verified", UNVERIFIED),
}
STATISTICS = {
    "FIU-STAT-001": (448075, "1"), "FIU-STAT-002": (18.35, "1"),
    "FIU-STAT-003": (99.49, "1"), "FIU-STAT-004": (0.51, "1 chart"),
    "FIU-STAT-005": (0.08, "1"), "FIU-STAT-006": (99.92, "2"),
    "FIU-STAT-007": (77.81, "2"), "FIU-STAT-008": (22.03, "2"),
    "FIU-STAT-009": (0.04, "2"), "FIU-STAT-010": (0.12, "2"),
    "FIU-STAT-011": (445093, "2 table"), "FIU-STAT-012": (2108, "2 table"),
    "FIU-STAT-013": (155, "2 table"),
}
REFERRALS = {
    "FIU-NABU-001": (13, 0), "FIU-NABU-002": (5, 41.28),
    "FIU-NABU-003": (4, 0), "FIU-NABU-004": (7, 27117.94),
    "FIU-NABU-005": (2, 0), "FIU-NABU-006": (17, 16.57),
    "FIU-NABU-007": (7, 63.08), "FIU-NABU-008": (1, 2.24),
    "FIU-NABU-009": (14, 0), "FIU-NABU-010": (70, 27241.11),
}


def _equal(actual, expected):
    try:
        return math.isclose(float(actual), expected, rel_tol=0, abs_tol=1e-8)
    except (ValueError, TypeError):
        return False


def annotate_fiu_sources(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for idx, row in out.iterrows():
        url, pages, status = SOURCE_METADATA.get(str(row.source_id), ("not_verified", "not_verified", UNVERIFIED))
        out.loc[idx, "source_url_or_file"] = url
        out.loc[idx, "source_pages"] = pages
        out.loc[idx, "reference_verification_status"] = status
        out.loc[idx, "reference_review_date"] = REVIEW_DATE
        out.loc[idx, "source_license_basis"] = "SFMS site default CC BY 4.0 unless otherwise specified"
        out.loc[idx, "source_mode"] = "inherited_reference_unverified_full_text" if status == UNVERIFIED else "official_pdf_text_review_no_local_pdf_snapshot"
    return out


def annotate_fiu_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["source_id"] = "FIU-SRC-002"
    out["source_url"] = STATS_URL
    out["reference_review_date"] = REVIEW_DATE
    for idx, row in out.iterrows():
        record = STATISTICS.get(str(row.metric_id))
        out.loc[idx, "reference_verification_status"] = UNVERIFIED if record is None else NUMERIC_CHECKED if _equal(row.metric_value, record[0]) else "value_mismatch_requires_review"
        out.loc[idx, "source_pages"] = record[1] if record else "not_verified"
        out.loc[idx, "semantic_review_status"] = "label_and_denominator_require_review" if row.metric_id == "FIU-STAT-006" else "national_context_only"
    return out


def annotate_fiu_referrals(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["source_id"] = "FIU-SRC-001"
    out["source_url"] = NABU_URL
    out["source_pages"] = "1"
    out["reference_review_date"] = REVIEW_DATE
    for idx, row in out.iterrows():
        record = REFERRALS.get(str(row.referral_context_id))
        matches = record and _equal(row.case_referrals_and_additional_referrals, record[0]) and _equal(row.funds_related_to_crime_uah_mln, record[1])
        out.loc[idx, "reference_verification_status"] = UNVERIFIED if record is None else NUMERIC_CHECKED if matches else "value_mismatch_requires_review"
        out.loc[idx, "source_table_row"] = "total" if row.referral_context_id == "FIU-NABU-010" else str(row.referral_context_id).rsplit("-", 1)[-1].lstrip("0")
    return out


def annotate_fiu_typologies(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["reference_review_date"] = REVIEW_DATE
    out["reference_verification_status"] = UNVERIFIED
    out["reference_support_scope"] = "Inherited annual-report claims require page-level verification; WARIS feature directions are project interpretations."
    out.loc[out.typology_support_id == "FIU-TYP-002", "reference_verification_status"] = "quarterly_statistics_checked_annual_typology_claim_unverified"
    out.loc[out.typology_support_id == "FIU-TYP-006", "reference_verification_status"] = "quarterly_statistics_checked_national_context_only"
    return out


@dataclass(frozen=True)
class FiuPublicContextSelection:
    """Presentation selection, not provider-rights or model-validation clearance."""

    frame: pd.DataFrame | None
    withheld_rows: int


def select_fiu_public_context(
    frame: pd.DataFrame | None,
    kind: Literal["statistics", "referrals", "typologies"],
) -> FiuPublicContextSelection:
    """Withhold unsupported/ambiguous context; retain the original internal table.

    This checks recorded row annotations, not live source authenticity. Missing
    annotations fail closed. Reference dates remain the original review dates.
    """
    if kind not in FIU_PUBLIC_REFERENCE_STATUSES:
        raise ValueError("Unknown FIU context family")
    if frame is None or frame.empty:
        return FiuPublicContextSelection(frame, 0)
    if "reference_verification_status" not in frame:
        return FiuPublicContextSelection(frame.iloc[0:0].copy(), len(frame))
    eligible = frame["reference_verification_status"].eq(FIU_PUBLIC_REFERENCE_STATUSES[kind])
    if kind in FIU_PUBLIC_REFERENCE_PERIODS:
        if "reporting_period" not in frame:
            eligible &= False
        else:
            eligible &= frame["reporting_period"].eq(FIU_PUBLIC_REFERENCE_PERIODS[kind])
    if kind == "statistics":
        if "semantic_review_status" not in frame:
            eligible &= False
        else:
            eligible &= frame["semantic_review_status"].eq("national_context_only")
    if kind == "typologies":
        if "typology_support_id" not in frame:
            eligible &= False
        else:
            eligible &= frame["typology_support_id"].eq("FIU-TYP-006")
    eligible = eligible.fillna(False).astype(bool)
    return FiuPublicContextSelection(frame.loc[eligible].copy(), int((~eligible).sum()))
