"""Optional live/public-source data connectors for WARIS.

These connectors are deliberately conservative. They collect public data where
available, save raw extracts, and convert them into sector/oblast-level proxies.

If a source is unavailable, blocked, rate-limited, or requires credentials, the
pipeline keeps using the synthetic fallback fields. Existing official Ukrstat
baseline candidates are reported as controlled benchmark-integration artifacts
when the official validation gate supports that posture, but they are not blended
into scoring here. Expanded Prozorro procurement features are reported as
review-only candidate artifacts using centralized config posture constants and
are not blended into scoring here. Wartime AML/CFT typology and official
FIU/SFMS context artifacts are also reported as source-support context only and
are not blended into scoring here. Analyst review, false-positive controls,
source-freshness, and run-manifest artifacts are surfaced as operational
documentation/status records only and are not blended into scoring here.

Important:
- This module does not accuse specific people, firms, or institutions.
- Source-backed values are used as risk-prioritization proxies only.
- Outputs remain sector/oblast-level for human AML/supervisory review.
"""

from __future__ import annotations

from .utils import official_baseline_observations

import json
import os
import re
from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import requests

from .config import RAW_DIR

try:
    from .config import (
        ACLED_API_BASE_URL,
        ACLED_API_FIELDS,
        ACLED_API_LIMIT,
        ACLED_EVENT_TYPES,
        ACLED_OAUTH_URL,
        ACLED_RAW_FILE,
        ENRICHED_INPUTS_RAW,
        LIVE_DATA_STATUS_RAW,
        NBU_API_BASE_URL,
        NBU_DEFAULT_REPORT_DATE,
        NBU_ENDPOINTS,
        OFFICIAL_INDICATOR_CATALOG_RAW,
        OFFICIAL_INDICATOR_CATALOG_TABLE,
        UKRSTAT_BASELINE_CURRENT_USE_IN_SCORING,
        UKRSTAT_BASELINE_VALIDATION_STATUS,
        UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE,
        UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE,
        UKRSTAT_SDMX_DATAFLOW_URL,
        OFFICIAL_BASELINE_READINESS_DECISION_TABLE,
        OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE,
        OFFICIAL_BASELINE_MERGE_READINESS_SUMMARY_TABLE,
        PROZORRO_API_BASE_URL,
        PROZORRO_PAGE_LIMIT,
        PROZORRO_MAX_DETAIL_RECORDS,
        PROZORRO_TIMEOUT_SECONDS,
        PROZORRO_EXPANDED_FEATURE_ROWS_RAW,
        PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE,
        PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE,
        PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE,
        PROZORRO_PROCUREMENT_FEATURE_SUMMARY_TABLE,
        PROZORRO_PROCUREMENT_CURRENT_USE,
        PROZORRO_PROCUREMENT_PROHIBITED_USE,
        PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE,
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
    ACLED_API_BASE_URL = "https://acleddata.com/api/acled/read"
    ACLED_OAUTH_URL = "https://acleddata.com/oauth/token"
    ACLED_API_LIMIT = 5000
    ACLED_API_FIELDS = [
        "event_id_cnty",
        "event_date",
        "year",
        "event_type",
        "sub_event_type",
        "country",
        "admin1",
        "admin2",
        "location",
        "latitude",
        "longitude",
        "fatalities",
    ]
    ACLED_EVENT_TYPES = [
        "Battles",
        "Explosions/Remote violence",
        "Violence against civilians",
        "Riots",
        "Protests",
        "Strategic developments",
    ]
    ACLED_RAW_FILE = RAW_DIR / "acled_ukraine_events_raw.csv"

    NBU_API_BASE_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory"
    NBU_DEFAULT_REPORT_DATE = "20240101"
    NBU_ENDPOINTS = {
        "bank_key_indicators": "basindbank",
        "bank_income_expenses": "banksincexp",
        "loans": "loan",
    }

    UKRSTAT_SDMX_DATAFLOW_URL = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/3.0/structure/dataflow/*/*/*?detail=allstubs&references=none"
    )

    LIVE_DATA_STATUS_RAW = RAW_DIR / "live_data_status.csv"
    ENRICHED_INPUTS_RAW = RAW_DIR / "oblast_sector_inputs_enriched.csv"
    OFFICIAL_INDICATOR_CATALOG_RAW = RAW_DIR / "official_indicator_catalog.csv"
    OFFICIAL_INDICATOR_CATALOG_TABLE = RAW_DIR / "official_indicator_catalog.csv"

    UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "ukrstat_oblast_baseline_probe_results.csv"
    )
    UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "ukrstat_oblast_baseline_candidates.csv"
    )
    UKRSTAT_BASELINE_CURRENT_USE_IN_SCORING = "not_yet_used"
    UKRSTAT_BASELINE_VALIDATION_STATUS = "pending_unit_and_mapping_validation"

    OFFICIAL_BASELINE_READINESS_DECISION_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "official_baseline_readiness_decision.csv"
    )
    OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "official_baseline_unit_evidence_summary.csv"
    )
    OFFICIAL_BASELINE_MERGE_READINESS_SUMMARY_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "official_baseline_merge_readiness_summary.csv"
    )

    PROZORRO_API_BASE_URL = "https://public.api.openprocurement.org/api/2.5/tenders"
    PROZORRO_PAGE_LIMIT = 100
    PROZORRO_MAX_DETAIL_RECORDS = 150
    PROZORRO_TIMEOUT_SECONDS = 30
    PROZORRO_EXPANDED_FEATURE_ROWS_RAW = (
        RAW_DIR / "prozorro_expanded_feature_rows_raw.csv"
    )
    PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "prozorro_procurement_features_oblast.csv"
    )
    PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE = (
        RAW_DIR.parent
        / "outputs"
        / "tables"
        / "prozorro_procurement_features_oblast_sector.csv"
    )
    PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "prozorro_procurement_scoring_candidates.csv"
    )
    PROZORRO_PROCUREMENT_FEATURE_SUMMARY_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "prozorro_procurement_feature_summary.csv"
    )
    PROZORRO_PROCUREMENT_CURRENT_USE = "review_artifact_only"
    PROZORRO_PROCUREMENT_PROHIBITED_USE = "direct_scoring_without_change_control"
    PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE = "none"

    WARTIME_AML_TYPOLOGY_REGISTER_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "waris_wartime_aml_typology_register.csv"
    )
    WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "waris_wartime_aml_typology_layer_map.csv"
    )
    WARTIME_AML_TYPOLOGY_SUMMARY_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "waris_wartime_aml_typology_summary.csv"
    )
    WARTIME_AML_TYPOLOGY_CURRENT_USE = (
        "literature_support_and_typology_reference_only"
    )
    WARTIME_AML_TYPOLOGY_PROHIBITED_USE = "direct_scoring_without_change_control"
    WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE = "none"

    FIU_OFFICIAL_SOURCE_REGISTER_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "waris_fiu_official_source_register.csv"
    )
    FIU_REPORTING_STATISTICS_CONTEXT_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "waris_fiu_reporting_statistics_context.csv"
    )
    FIU_CASE_REFERRAL_CONTEXT_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "waris_fiu_case_referral_context.csv"
    )
    FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "waris_fiu_typology_support_register.csv"
    )
    FIU_CONTEXT_SUMMARY_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "waris_fiu_context_summary.csv"
    )
    FIU_CONTEXT_CURRENT_USE = "official_fiu_context_and_typology_support_only"
    FIU_CONTEXT_PROHIBITED_USE = "direct_scoring_without_change_control"
    FIU_CONTEXT_PRODUCTION_SCORE_CHANGE = "none"

    ANALYST_REVIEW_SUMMARY_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "analyst_review_summary.csv"
    )
    ANALYST_REVIEW_CURRENT_USE = "analyst_review_workflow_only"
    ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE = "none"

    FALSE_POSITIVE_SUMMARY_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "false_positive_summary.csv"
    )
    FALSE_POSITIVE_CONTROLS_CURRENT_USE = "human_review_support_only"
    FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE = "none"

    SOURCE_FRESHNESS_SUMMARY_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "source_freshness_summary.csv"
    )
    SOURCE_FRESHNESS_CURRENT_USE = "source_freshness_monitoring_only"
    SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE = "none"

    RUN_MANIFEST_SUMMARY_TABLE = (
        RAW_DIR.parent / "outputs" / "tables" / "run_manifest_summary.csv"
    )
    RUN_MANIFEST_CURRENT_USE = "run_manifest_documentation"
    RUN_MANIFEST_PRODUCTION_SCORE_CHANGE = "none"

from .utils import ensure_dirs, min_max_scale


@dataclass
class SourceStatus:
    source_name: str
    status: str
    rows: int = 0
    note: str = ""


def _safe_get_json(
    url: str,
    params: Optional[dict] = None,
    timeout: int = 30,
) -> Optional[dict | list]:
    """Fetch JSON from a public endpoint with conservative error handling."""
    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={"User-Agent": "WARIS research prototype"},
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"[WARN] fetch failed for {url}: {exc}")
        return None


def _normalize_text(value: object) -> str:
    """Normalize text-like fields for matching."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).lower()


def _extract_nested(record: dict, path: Iterable[str], default=None):
    """Safely extract a nested dictionary value."""
    cur = record
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


OBLAST_ALIASES = {
    "cherkasy": "Cherkasy",
    "cherkaska": "Cherkasy",
    "chernihiv": "Chernihiv",
    "chernihivska": "Chernihiv",
    "chernivtsi": "Chernivtsi",
    "chernivetska": "Chernivtsi",
    "dnipropetrovsk": "Dnipropetrovsk",
    "dnipropetrovska": "Dnipropetrovsk",
    "donetsk": "Donetsk",
    "donetska": "Donetsk",
    "ivano-frankivsk": "Ivano-Frankivsk",
    "ivano frankivsk": "Ivano-Frankivsk",
    "ivano-frankivska": "Ivano-Frankivsk",
    "ivano frankivska": "Ivano-Frankivsk",
    "kharkiv": "Kharkiv",
    "kharkivska": "Kharkiv",
    "kherson": "Kherson",
    "khersonska": "Kherson",
    "khmelnytskyi": "Khmelnytskyi",
    "khmelnytska": "Khmelnytskyi",
    "kirovohrad": "Kirovohrad",
    "kirovohradska": "Kirovohrad",
    "kyiv city": "Kyiv City",
    "city of kyiv": "Kyiv City",
    "kyivska": "Kyiv",
    "kyiv oblast": "Kyiv",
    "kyiv": "Kyiv",
    "kiev": "Kyiv",
    "luhansk": "Luhansk",
    "luhanska": "Luhansk",
    "lviv": "Lviv",
    "lvivska": "Lviv",
    "mykolaiv": "Mykolaiv",
    "mykolaivska": "Mykolaiv",
    "odesa": "Odesa",
    "odeska": "Odesa",
    "odessa": "Odesa",
    "poltava": "Poltava",
    "poltavska": "Poltava",
    "rivne": "Rivne",
    "rivnenska": "Rivne",
    "sumy": "Sumy",
    "sumska": "Sumy",
    "ternopil": "Ternopil",
    "ternopilska": "Ternopil",
    "vinnytsia": "Vinnytsia",
    "vinnytska": "Vinnytsia",
    "volyn": "Volyn",
    "volynska": "Volyn",
    "zakarpattia": "Zakarpattia",
    "zakarpatska": "Zakarpattia",
    "zaporizhzhia": "Zaporizhzhia",
    "zaporizhia": "Zaporizhzhia",
    "zaporizka": "Zaporizhzhia",
    "zhytomyr": "Zhytomyr",
    "zhytomyrska": "Zhytomyr",
}


def standardize_oblast(value: object) -> Optional[str]:
    """Map source-specific region text into the model's canonical oblast names."""
    text = _normalize_text(value)
    text = text.replace("'", "").replace("’", "").strip()

    if not text:
        return None

    # Handle Kyiv City before removing generic words like "city".
    if text in {"kyiv city", "city of kyiv", "misto kyiv", "m. kyiv"}:
        return "Kyiv City"

    if text in OBLAST_ALIASES:
        return OBLAST_ALIASES[text]

    cleaned = re.sub(r"\b(oblast|region|oblast\'|city|misto|m\.)\b", "", text).strip()

    if cleaned in OBLAST_ALIASES:
        return OBLAST_ALIASES[cleaned]

    for key, oblast in OBLAST_ALIASES.items():
        if key in cleaned:
            return oblast

    return None


def classify_sector(text: object) -> str:
    """Classify procurement/source text into the model's sector taxonomy."""
    t = _normalize_text(text)

    if any(
        k in t
        for k in [
            "grain",
            "wheat",
            "corn",
            "barley",
            "oilseed",
            "agric",
            "food",
            "fertiliz",
        ]
    ):
        return "Agriculture and grain trade"

    if any(
        k in t
        for k in [
            "construct",
            "repair",
            "reconstruction",
            "road",
            "bridge",
            "building",
            "infrastructure",
        ]
    ):
        return "Construction and reconstruction"

    if any(
        k in t
        for k in [
            "fuel",
            "diesel",
            "gasoline",
            "logistic",
            "transport",
            "vehicle",
            "freight",
            "rail",
        ]
    ):
        return "Fuel and logistics"

    if any(
        k in t
        for k in [
            "bank",
            "payment",
            "financial",
            "insurance",
            "software",
            "digital",
            "it service",
        ]
    ):
        return "Financial and payment services"

    if any(
        k in t
        for k in [
            "defense",
            "armored",
            "military",
            "drone",
            "munition",
            "security",
            "uniform",
            "protective",
        ]
    ):
        return "Defense-adjacent manufacturing"

    return "Retail and consumer goods"


def fetch_prozorro_tenders(
    limit: int = min(50, PROZORRO_PAGE_LIMIT),
    detail_limit: int = min(50, PROZORRO_MAX_DETAIL_RECORDS),
) -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Fetch recent Prozorro tender records and return flattened tender details."""
    ensure_dirs([RAW_DIR])

    list_url = PROZORRO_API_BASE_URL
    payload = _safe_get_json(
        list_url,
        params={"mode": "_all_", "limit": limit},
        timeout=PROZORRO_TIMEOUT_SECONDS,
    )

    if not isinstance(payload, dict) or "data" not in payload:
        return None, SourceStatus(
            "Prozorro recent tenders",
            "fallback",
            0,
            "List endpoint unavailable",
        )

    base = pd.DataFrame(payload.get("data", []))

    if base.empty:
        return None, SourceStatus(
            "Prozorro recent tenders",
            "fallback",
            0,
            "No list rows returned",
        )

    base.to_csv(RAW_DIR / "prozorro_tender_list_raw.csv", index=False)

    rows = []

    for tender_id in base.get("id", pd.Series(dtype=str)).dropna().head(detail_limit):
        detail_url = f"{list_url}/{tender_id}"
        detail = _safe_get_json(detail_url, timeout=PROZORRO_TIMEOUT_SECONDS)
        data = detail.get("data") if isinstance(detail, dict) else None

        if not isinstance(data, dict):
            continue

        title = data.get("title", "")
        description = data.get("description", "")

        items = data.get("items") or []
        item_desc = " ".join(
            str(item.get("description", ""))
            for item in items
            if isinstance(item, dict)
        )
        cpv_desc = " ".join(
            str(_extract_nested(item, ["classification", "description"], ""))
            for item in items
            if isinstance(item, dict)
        )

        text_for_sector = " ".join([title, description, item_desc, cpv_desc])
        procuring_region = _extract_nested(
            data,
            ["procuringEntity", "address", "region"],
            "",
        )
        value_amount = _extract_nested(data, ["value", "amount"], np.nan)

        rows.append(
            {
                "tender_id": tender_id,
                "date_modified": data.get("dateModified"),
                "status": data.get("status"),
                "title": title,
                "procuring_region": procuring_region,
                "oblast": standardize_oblast(procuring_region),
                "sector": classify_sector(text_for_sector),
                "value_amount": pd.to_numeric(value_amount, errors="coerce"),
                "procurement_method_type": data.get("procurementMethodType"),
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return None, SourceStatus(
            "Prozorro recent tenders",
            "fallback",
            0,
            "Tender details unavailable",
        )

    df.to_csv(RAW_DIR / "prozorro_tender_details_raw.csv", index=False)

    return df, SourceStatus(
        "Prozorro recent tenders",
        "live",
        len(df),
        "Recent public tender details fetched",
    )


def build_procurement_proxy(
    prozorro_df: Optional[pd.DataFrame],
) -> Optional[pd.DataFrame]:
    """Convert recent Prozorro records into oblast/sector procurement proxies."""
    if prozorro_df is None or prozorro_df.empty or "oblast" not in prozorro_df.columns:
        return None

    df = prozorro_df.dropna(subset=["oblast", "sector"]).copy()

    if df.empty:
        return None

    grouped = df.groupby(["oblast", "sector"], as_index=False).agg(
        live_tender_count=("tender_id", "count"),
        live_tender_value=("value_amount", "sum"),
    )

    grouped["procurement_awards_proxy_live"] = min_max_scale(
        (0.65 * grouped["live_tender_count"])
        + (0.35 * min_max_scale(grouped["live_tender_value"].fillna(0)))
    )

    return grouped


def load_prozorro_expanded_procurement_feature_status() -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Load expanded Prozorro procurement features if present.

    The expanded feature artifacts are generated by src.prozorro_procurement_features.
    This function only records their presence in live_data_status.csv and keeps
    the current scoring boundary intact.
    """
    features = _load_optional_table(PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE)

    if features is None or features.empty:
        return None, SourceStatus(
            "Prozorro expanded procurement features",
            "fallback",
            0,
            _prozorro_expanded_feature_note(),
        )

    return features, SourceStatus(
        "Prozorro expanded procurement features",
        "live",
        len(features),
        _prozorro_expanded_feature_note(),
    )


def _get_acled_credentials() -> tuple[str, str]:
    """Load ACLED OAuth credentials from environment variables."""
    username = os.getenv("ACLED_USERNAME")
    password = os.getenv("ACLED_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Missing ACLED credentials. Add ACLED_USERNAME and ACLED_PASSWORD to .env."
        )

    return username, password


def _request_acled_token(username: str, password: str) -> str:
    """Request an ACLED OAuth bearer token."""
    payload = {
        "username": username,
        "password": password,
        "grant_type": "password",
        "client_id": "acled",
        "scope": "authenticated",
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(
        ACLED_OAUTH_URL,
        data=payload,
        headers=headers,
        timeout=45,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "ACLED authentication failed. "
            f"Status code: {response.status_code}. "
            "Provider response body omitted to protect authentication details."
        )

    token_payload = response.json()
    access_token = token_payload.get("access_token")

    if not access_token:
        raise RuntimeError(
            "ACLED authentication response did not include an access_token."
        )

    return access_token


def fetch_acled_ukraine(
    limit: int = ACLED_API_LIMIT,
) -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Fetch credentialed ACLED Ukraine events using OAuth username/password."""
    ensure_dirs([RAW_DIR])

    if ACLED_RAW_FILE.exists():
        try:
            existing = pd.read_csv(ACLED_RAW_FILE, low_memory=False)
            if not existing.empty:
                return existing, SourceStatus(
                    "ACLED Ukraine events",
                    "live",
                    len(existing),
                    "Using existing credentialed OAuth Ukraine event file",
                )
        except Exception:
            pass

    try:
        username, password = _get_acled_credentials()
        access_token = _request_acled_token(username=username, password=password)

        headers = {"Authorization": f"Bearer {access_token}"}

        params = {
            "country": "Ukraine",
            "event_type": "|".join(ACLED_EVENT_TYPES),
            "fields": "|".join(ACLED_API_FIELDS),
            "limit": limit,
            "page": 1,
            "with_total": "true",
        }

        response = requests.get(
            ACLED_API_BASE_URL,
            headers=headers,
            params=params,
            timeout=90,
        )

        if response.status_code != 200:
            return None, SourceStatus(
                "ACLED Ukraine events",
                "fallback",
                0,
                f"ACLED data request failed: {response.status_code} - {response.text[:300]}",
            )

        payload = response.json()
        records = payload.get("data", [])

        if not isinstance(records, list) or not records:
            return None, SourceStatus(
                "ACLED Ukraine events",
                "fallback",
                0,
                "ACLED returned no Ukraine event rows",
            )

        df = pd.DataFrame(records)

        for col in ["fatalities", "year", "latitude", "longitude"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "fatalities" in df.columns:
            df["fatalities"] = df["fatalities"].fillna(0)

        if "event_date" in df.columns:
            df["event_date"] = pd.to_datetime(
                df["event_date"],
                errors="coerce",
            ).dt.strftime("%Y-%m-%d")

        if "event_id_cnty" in df.columns:
            df = df.drop_duplicates(subset=["event_id_cnty"], keep="first")
        else:
            df = df.drop_duplicates()

        df = df.reset_index(drop=True)
        df.to_csv(ACLED_RAW_FILE, index=False)

        return df, SourceStatus(
            "ACLED Ukraine events",
            "live",
            len(df),
            "Credentialed OAuth Ukraine event sample fetched",
        )

    except Exception as exc:
        return None, SourceStatus(
            "ACLED Ukraine events",
            "fallback",
            0,
            f"ACLED OAuth fetch failed: {exc}",
        )


def build_conflict_proxy(acled_df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Convert ACLED records into a more stable oblast-level conflict proxy.

    Improvements:
    - Handles missing/unknown oblast values.
    - Uses log1p transforms so Donetsk/Luhansk do not overwhelm all other oblasts.
    - Blends event count and fatalities.
    - Fills missing proxy values with 0.
    - Saves an audit table for report/dashboard review.
    """
    if acled_df is None or acled_df.empty:
        return None

    df = acled_df.copy()

    admin_col = "admin1" if "admin1" in df.columns else None

    if not admin_col:
        return None

    df["oblast"] = df[admin_col].apply(standardize_oblast)
    df = df.dropna(subset=["oblast"]).copy()

    if df.empty:
        return None

    df["fatalities"] = pd.to_numeric(
        df.get("fatalities", 0),
        errors="coerce",
    ).fillna(0)

    grouped = (
        df.groupby("oblast", as_index=False)
        .agg(
            live_event_count=(admin_col, "count"),
            live_fatalities=("fatalities", "sum"),
        )
    )

    grouped["log_event_count"] = np.log1p(grouped["live_event_count"])
    grouped["log_fatalities"] = np.log1p(grouped["live_fatalities"])

    grouped["event_count_scaled"] = min_max_scale(
        grouped["log_event_count"]
    ).fillna(0)

    grouped["fatalities_scaled"] = min_max_scale(
        grouped["log_fatalities"]
    ).fillna(0)

    grouped["conflict_intensity_proxy_live"] = (
        0.70 * grouped["event_count_scaled"]
        + 0.30 * grouped["fatalities_scaled"]
    ).clip(0, 100)

    grouped["conflict_intensity_proxy_live"] = grouped[
        "conflict_intensity_proxy_live"
    ].fillna(0)

    grouped = grouped.sort_values(
        "conflict_intensity_proxy_live",
        ascending=False,
    )

    grouped.to_csv(RAW_DIR / "acled_oblast_conflict_proxy.csv", index=False)

    return grouped


def fetch_world_bank_ukraine_context() -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Fetch national fiscal/economic context for Ukraine from World Bank WDI."""
    indicators = {
        "NY.GDP.MKTP.CD": "GDP current US$",
        "GC.TAX.TOTL.GD.ZS": "Tax revenue % GDP",
        "NE.EXP.GNFS.CD": "Exports goods/services current US$",
        "NE.IMP.GNFS.CD": "Imports goods/services current US$",
    }

    rows = []

    for code, name in indicators.items():
        url = f"https://api.worldbank.org/v2/country/UKR/indicator/{code}"

        payload = _safe_get_json(
            url,
            params={"format": "json", "per_page": 100},
        )

        if isinstance(payload, list) and len(payload) > 1:
            for item in payload[1]:
                if item.get("value") is not None:
                    rows.append(
                        {
                            "indicator_code": code,
                            "indicator_name": name,
                            "year": item.get("date"),
                            "value": item.get("value"),
                        }
                    )

    df = pd.DataFrame(rows)

    if df.empty:
        return None, SourceStatus(
            "World Bank Ukraine fiscal context",
            "fallback",
            0,
            "World Bank API unavailable or no rows",
        )

    df.to_csv(RAW_DIR / "world_bank_ukraine_context_raw.csv", index=False)

    return df, SourceStatus(
        "World Bank Ukraine fiscal context",
        "live",
        len(df),
        "National fiscal context fetched",
    )


def fetch_nbu_financial_context() -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Fetch optional NBU financial-sector context.

    This connector stores raw NBU API responses and reports source availability.
    These fields are national financial-sector context, not direct entity-level
    AML signals.
    """
    ensure_dirs([RAW_DIR])

    report_date = os.getenv("NBU_REPORT_DATE", NBU_DEFAULT_REPORT_DATE)
    rows = []

    for label, endpoint in NBU_ENDPOINTS.items():
        url = f"{NBU_API_BASE_URL}/{endpoint}"
        params = {"date": report_date, "json": ""}
        # These monthly NBU series require an explicit period parameter.
        # Loan statistics use the existing date-only contract.
        if endpoint in {"basindbank", "banksincexp"}:
            params["period"] = "m"

        try:
            response = requests.get(
                url,
                params=params,
                timeout=45,
                headers={"User-Agent": "WARIS research prototype"},
            )

            if response.status_code != 200:
                rows.append(
                    {
                        "dataset": label,
                        "endpoint": endpoint,
                        "status": "fallback",
                        "rows": 0,
                        "note": f"HTTP {response.status_code}",
                    }
                )
                continue

            payload = response.json()

            if isinstance(payload, list):
                df = pd.DataFrame(payload)
            elif isinstance(payload, dict):
                df = pd.DataFrame(payload.get("data", []))
            else:
                df = pd.DataFrame()

            if df.empty:
                rows.append(
                    {
                        "dataset": label,
                        "endpoint": endpoint,
                        "status": "fallback",
                        "rows": 0,
                        "note": "No rows returned",
                    }
                )
                continue

            raw_path = RAW_DIR / f"nbu_{label}_raw.csv"
            df.to_csv(raw_path, index=False)

            rows.append(
                {
                    "dataset": label,
                    "endpoint": endpoint,
                    "status": "live",
                    "rows": len(df),
                    "note": f"Saved {raw_path.name}",
                }
            )

        except Exception as exc:
            rows.append(
                {
                    "dataset": label,
                    "endpoint": endpoint,
                    "status": "fallback",
                    "rows": 0,
                    "note": str(exc)[:250],
                }
            )

    status_df = pd.DataFrame(rows)
    status_df.to_csv(RAW_DIR / "nbu_financial_context_status.csv", index=False)

    live_rows = int(status_df.loc[status_df["status"] == "live", "rows"].sum())

    if live_rows == 0:
        return None, SourceStatus(
            "NBU financial-sector context",
            "fallback",
            0,
            "NBU endpoints unavailable for configured report date",
        )

    return status_df, SourceStatus(
        "NBU financial-sector context",
        "live",
        live_rows,
        f"NBU financial context fetched for report date {report_date}",
    )


def build_nbu_financial_proxy(nbu_status_df: Optional[pd.DataFrame]) -> Optional[float]:
    """Build a simple national financial-context proxy from NBU availability.

    This creates a small national context adjustment only when NBU financial-sector
    datasets are available.
    """
    if nbu_status_df is None or nbu_status_df.empty:
        return None

    if "status" not in nbu_status_df.columns:
        return None

    live_count = int((nbu_status_df["status"] == "live").sum())
    total_count = len(nbu_status_df)

    if total_count == 0:
        return None

    return float(np.clip((live_count / total_count) * 100, 0, 100))



def _load_optional_table(path) -> Optional[pd.DataFrame]:
    """Load an optional CSV artifact with conservative error handling."""
    try:
        if path is None or not path.exists():
            return None

        df = pd.read_csv(path)

        if df.empty:
            return None

        return df
    except Exception:
        return None


def _first_table_value(
    df: Optional[pd.DataFrame],
    column: str,
    default: str = "not_available",
) -> str:
    """Return first table value as text, with a safe default."""
    if df is None or df.empty or column not in df.columns:
        return default

    value = df.iloc[0].get(column, default)

    if pd.isna(value):
        return default

    return str(value)


def _unique_values_from_tables(
    tables: Iterable[Optional[pd.DataFrame]],
    column: str,
) -> list[str]:
    """Return sorted unique non-empty values from a column across optional tables."""
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
    tables: Iterable[Optional[pd.DataFrame]],
    column: str,
    expected: bool = False,
) -> bool:
    """Return True if all present boolean-like values match expected."""
    found_any = False

    for table in tables:
        if table is None or table.empty or column not in table.columns:
            continue

        found_any = True
        values = table[column].fillna(expected)

        for value in values:
            if isinstance(value, str):
                value_bool = value.strip().lower() in {"true", "1", "yes"}
            else:
                value_bool = bool(value)

            if value_bool != expected:
                return False

    return found_any


def _wartime_aml_typology_status() -> dict[str, object]:
    """Summarize wartime AML/CFT typology support artifacts."""
    register = _load_optional_table(WARTIME_AML_TYPOLOGY_REGISTER_TABLE)
    layer_map = _load_optional_table(WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE)
    summary = _load_optional_table(WARTIME_AML_TYPOLOGY_SUMMARY_TABLE)

    tables = [register, layer_map, summary]

    current_use_values = _unique_values_from_tables(tables, "current_use")
    prohibited_use_values = _unique_values_from_tables(tables, "prohibited_use")
    production_score_change_values = _unique_values_from_tables(
        tables,
        "production_score_change",
    )

    top_family = "not_available"
    if register is not None and not register.empty and "typology_family" in register.columns:
        family_counts = register["typology_family"].fillna("").astype(str).value_counts()
        if not family_counts.empty:
            top_family = str(family_counts.index[0])

    return {
        "has_typology_register": register is not None and not register.empty,
        "register_rows": 0 if register is None else len(register),
        "layer_map_rows": 0 if layer_map is None else len(layer_map),
        "summary_rows": 0 if summary is None else len(summary),
        "top_typology_family": top_family,
        "current_use_values": current_use_values,
        "prohibited_use_values": prohibited_use_values,
        "production_score_change_values": production_score_change_values,
        "posture_current_use_ok": (
            WARTIME_AML_TYPOLOGY_CURRENT_USE in current_use_values
            if current_use_values
            else False
        ),
        "posture_prohibited_use_ok": (
            WARTIME_AML_TYPOLOGY_PROHIBITED_USE in prohibited_use_values
            if prohibited_use_values
            else False
        ),
        "posture_score_change_ok": (
            WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE
            in production_score_change_values
            if production_score_change_values
            else False
        ),
    }


def _wartime_aml_typology_note() -> str:
    """Return compact live-status note for wartime AML/CFT typology artifacts."""
    status = _wartime_aml_typology_status()

    if not status["has_typology_register"]:
        return (
            "Wartime AML/CFT typology artifacts were not found. Run "
            "python -m src.wartime_aml_typology_register to generate "
            "literature-supported typology reference artifacts."
        )

    return (
        f"Wartime AML/CFT typology artifacts loaded. "
        f"Register rows: {status['register_rows']}; "
        f"layer-map rows: {status['layer_map_rows']}; "
        f"summary rows: {status['summary_rows']}; "
        f"top typology family: {status['top_typology_family']}. "
        f"Current use: {status['current_use_values']} "
        f"(expected {WARTIME_AML_TYPOLOGY_CURRENT_USE}; "
        f"ok={status['posture_current_use_ok']}). "
        f"Prohibited use: {status['prohibited_use_values']} "
        f"(expected {WARTIME_AML_TYPOLOGY_PROHIBITED_USE}; "
        f"ok={status['posture_prohibited_use_ok']}). "
        f"Production score change: {status['production_score_change_values']} "
        f"(expected {WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE}; "
        f"ok={status['posture_score_change_ok']})."
    )


def load_wartime_aml_typology_status() -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Load wartime AML/CFT typology artifacts if present.

    These artifacts are generated by src.wartime_aml_typology_register and are
    source-support/reference artifacts only. They are not blended into scoring.
    """
    typology_register = _load_optional_table(WARTIME_AML_TYPOLOGY_REGISTER_TABLE)

    if typology_register is None or typology_register.empty:
        return None, SourceStatus(
            "Wartime AML/CFT typology register",
            "fallback",
            0,
            _wartime_aml_typology_note(),
        )

    return typology_register, SourceStatus(
        "Wartime AML/CFT typology register",
        "live",
        len(typology_register),
        _wartime_aml_typology_note(),
    )


def _fiu_official_context_status() -> dict[str, object]:
    """Summarize official FIU/SFMS context artifacts."""
    source_register = _load_optional_table(FIU_OFFICIAL_SOURCE_REGISTER_TABLE)
    reporting_stats = _load_optional_table(FIU_REPORTING_STATISTICS_CONTEXT_TABLE)
    case_referrals = _load_optional_table(FIU_CASE_REFERRAL_CONTEXT_TABLE)
    typology_support = _load_optional_table(FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE)
    summary = _load_optional_table(FIU_CONTEXT_SUMMARY_TABLE)

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
                reporting_stats["metric_name"].astype(str).eq(
                    "financial_transaction_reports_received_and_processed"
                )
            ]
            if not reports.empty:
                q1_2025_reports = str(reports.iloc[0].get("metric_value", "not_available"))

            suspicious = reporting_stats[
                reporting_stats["metric_name"].astype(str).eq(
                    "suspicious_transaction_activity_report_share"
                )
            ]
            if not suspicious.empty:
                suspicious_share = str(
                    suspicious.iloc[0].get("metric_value", "not_available")
                )

    q1_2026_referrals = "not_available"
    q1_2026_funds = "not_available"
    if case_referrals is not None and not case_referrals.empty:
        if {"person_category", "case_referrals_and_additional_referrals"}.issubset(
            case_referrals.columns
        ):
            total = case_referrals[case_referrals["person_category"].astype(str).eq("total")]
            if not total.empty:
                q1_2026_referrals = str(
                    total.iloc[0].get(
                        "case_referrals_and_additional_referrals",
                        "not_available",
                    )
                )
                q1_2026_funds = str(
                    total.iloc[0].get(
                        "funds_related_to_crime_uah_mln",
                        "not_available",
                    )
                )

    return {
        "has_fiu_context": (
            source_register is not None
            and not source_register.empty
            and reporting_stats is not None
            and not reporting_stats.empty
            and case_referrals is not None
            and not case_referrals.empty
            and typology_support is not None
            and not typology_support.empty
        ),
        "source_register_rows": 0 if source_register is None else len(source_register),
        "reporting_stat_rows": 0 if reporting_stats is None else len(reporting_stats),
        "case_referral_rows": 0 if case_referrals is None else len(case_referrals),
        "typology_support_rows": 0 if typology_support is None else len(typology_support),
        "summary_rows": 0 if summary is None else len(summary),
        "q1_2025_reports": q1_2025_reports,
        "suspicious_share": suspicious_share,
        "q1_2026_referrals": q1_2026_referrals,
        "q1_2026_funds_uah_mln": q1_2026_funds,
        "current_use_values": current_use_values,
        "prohibited_use_values": prohibited_use_values,
        "production_score_change_values": production_score_change_values,
        "used_in_scoring_ok": used_in_scoring_ok,
        "used_in_monte_carlo_ok": used_in_monte_carlo_ok,
        "posture_current_use_ok": (
            FIU_CONTEXT_CURRENT_USE in current_use_values
            if current_use_values
            else False
        ),
        "posture_prohibited_use_ok": (
            FIU_CONTEXT_PROHIBITED_USE in prohibited_use_values
            if prohibited_use_values
            else False
        ),
        "posture_score_change_ok": (
            FIU_CONTEXT_PRODUCTION_SCORE_CHANGE in production_score_change_values
            if production_score_change_values
            else False
        ),
    }


def _fiu_official_context_note() -> str:
    """Return compact live-status note for official FIU/SFMS context artifacts."""
    status = _fiu_official_context_status()

    if not status["has_fiu_context"]:
        return (
            "Official FIU/SFMS context artifacts were not found or are incomplete. "
            "Run python -m src.fiu_official_context to generate official-source "
            "context and typology-support artifacts."
        )

    return (
        f"Official FIU/SFMS context artifacts loaded. "
        f"Source rows: {status['source_register_rows']}; "
        f"reporting-stat rows: {status['reporting_stat_rows']}; "
        f"case-referral rows: {status['case_referral_rows']}; "
        f"typology-support rows: {status['typology_support_rows']}; "
        f"summary rows: {status['summary_rows']}. "
        f"Q1 2025 reports: {status['q1_2025_reports']}; "
        f"suspicious activity share: {status['suspicious_share']}%; "
        f"Q1 2026 NABU referrals: {status['q1_2026_referrals']}; "
        f"funds context: UAH {status['q1_2026_funds_uah_mln']} mln. "
        f"Current use: {status['current_use_values']} "
        f"(expected {FIU_CONTEXT_CURRENT_USE}; ok={status['posture_current_use_ok']}). "
        f"Prohibited use: {status['prohibited_use_values']} "
        f"(expected {FIU_CONTEXT_PROHIBITED_USE}; ok={status['posture_prohibited_use_ok']}). "
        f"Production score change: {status['production_score_change_values']} "
        f"(expected {FIU_CONTEXT_PRODUCTION_SCORE_CHANGE}; "
        f"ok={status['posture_score_change_ok']}). "
        f"Scoring flag ok={status['used_in_scoring_ok']}; "
        f"Monte Carlo flag ok={status['used_in_monte_carlo_ok']}."
    )


def load_fiu_official_context_status() -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Load official FIU/SFMS context artifacts if present.

    These artifacts are generated by src.fiu_official_context and are official
    source-context artifacts only. They are not blended into scoring.
    """
    source_register = _load_optional_table(FIU_OFFICIAL_SOURCE_REGISTER_TABLE)

    if source_register is None or source_register.empty:
        return None, SourceStatus(
            "Official FIU/SFMS context artifacts",
            "fallback",
            0,
            _fiu_official_context_note(),
        )

    return source_register, SourceStatus(
        "Official FIU/SFMS context artifacts",
        "live",
        len(source_register),
        _fiu_official_context_note(),
    )


def _summary_value_for_area(
    table: Optional[pd.DataFrame],
    summary_area: str,
    value_column: str = "value",
    default: str = "not_available",
) -> str:
    """Return a summary-table value for a named summary area."""
    if table is None or table.empty:
        return default

    if "summary_area" not in table.columns:
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


def _summary_status_for_area(
    table: Optional[pd.DataFrame],
    summary_area: str,
    default: str = "not_available",
) -> str:
    """Return a summary-table status for a named summary area."""
    return _summary_value_for_area(
        table,
        summary_area=summary_area,
        value_column="status",
        default=default,
    )


def _operational_review_artifacts_status() -> dict[str, object]:
    """Summarize operational documentation/control artifacts."""
    analyst_summary = _load_optional_table(ANALYST_REVIEW_SUMMARY_TABLE)
    false_positive_summary = _load_optional_table(FALSE_POSITIVE_SUMMARY_TABLE)
    source_freshness_summary = _load_optional_table(SOURCE_FRESHNESS_SUMMARY_TABLE)
    run_manifest_summary = _load_optional_table(RUN_MANIFEST_SUMMARY_TABLE)

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
    source_freshness_posture = _summary_status_for_area(
        source_freshness_summary,
        "Overall freshness posture",
    )
    source_freshness_counts = _summary_value_for_area(
        source_freshness_summary,
        "Freshness status counts",
    )

    run_id = "not_available"
    model_version = "not_available"
    manifest_score_change = "not_available"
    if run_manifest_summary is not None and not run_manifest_summary.empty:
        run_id = str(run_manifest_summary.iloc[0].get("run_id", "not_available"))
        model_version = str(
            run_manifest_summary.iloc[0].get("model_version", "not_available")
        )
        manifest_score_change = str(
            run_manifest_summary.iloc[0].get(
                "production_score_change",
                "not_available",
            )
        )

    return {
        "has_analyst_review": analyst_summary is not None and not analyst_summary.empty,
        "has_false_positive_controls": false_positive_summary is not None
        and not false_positive_summary.empty,
        "has_source_freshness": source_freshness_summary is not None
        and not source_freshness_summary.empty,
        "has_run_manifest": run_manifest_summary is not None
        and not run_manifest_summary.empty,
        "analyst_queue_records": analyst_queue_records,
        "review_questions": review_questions,
        "false_positive_control_counts": false_positive_control_counts,
        "false_positive_checklist_rows": false_positive_checklist_rows,
        "source_freshness_posture": source_freshness_posture,
        "source_freshness_counts": source_freshness_counts,
        "run_id": run_id,
        "model_version": model_version,
        "manifest_score_change": manifest_score_change,
    }


def _operational_review_artifacts_note() -> str:
    """Return compact live-status note for operational review artifacts."""
    status = _operational_review_artifacts_status()

    if not any(
        [
            status["has_analyst_review"],
            status["has_false_positive_controls"],
            status["has_source_freshness"],
            status["has_run_manifest"],
        ]
    ):
        return (
            "Operational review artifacts were not found. Run main.py or generate "
            "analyst review, false-positive, source-freshness, and run-manifest "
            "modules before external reporting."
        )

    return (
        "Operational review artifacts loaded. "
        f"Analyst review available={status['has_analyst_review']} "
        f"(queue records={status['analyst_queue_records']}; "
        f"questions={status['review_questions']}; "
        f"current_use={ANALYST_REVIEW_CURRENT_USE}; "
        f"production_score_change={ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE}). "
        f"False-positive controls available={status['has_false_positive_controls']} "
        f"(controls={status['false_positive_control_counts']}; "
        f"checklist rows={status['false_positive_checklist_rows']}; "
        f"current_use={FALSE_POSITIVE_CONTROLS_CURRENT_USE}; "
        f"production_score_change={FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE}). "
        f"Source freshness available={status['has_source_freshness']} "
        f"(posture={status['source_freshness_posture']}; "
        f"counts={status['source_freshness_counts']}; "
        f"current_use={SOURCE_FRESHNESS_CURRENT_USE}; "
        f"production_score_change={SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE}). "
        f"Run manifest available={status['has_run_manifest']} "
        f"(run_id={status['run_id']}; model_version={status['model_version']}; "
        f"manifest_score_change={status['manifest_score_change']}; "
        f"current_use={RUN_MANIFEST_CURRENT_USE})."
    )


def load_operational_review_artifacts_status() -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Load operational review/documentation status artifacts if present.

    These artifacts are generated by analyst_review_queue, false_positive_controls,
    source_freshness, and run_manifest. They document workflow controls and are
    not blended into scoring.
    """
    status = _operational_review_artifacts_status()

    rows = [
        {
            "artifact_family": "analyst_review_workflow",
            "available": status["has_analyst_review"],
            "current_use": ANALYST_REVIEW_CURRENT_USE,
            "production_score_change": ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
            "status_detail": (
                f"queue records={status['analyst_queue_records']}; "
                f"questions={status['review_questions']}"
            ),
        },
        {
            "artifact_family": "false_positive_controls",
            "available": status["has_false_positive_controls"],
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
            "production_score_change": FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
            "status_detail": (
                f"controls={status['false_positive_control_counts']}; "
                f"checklist rows={status['false_positive_checklist_rows']}"
            ),
        },
        {
            "artifact_family": "source_freshness",
            "available": status["has_source_freshness"],
            "current_use": SOURCE_FRESHNESS_CURRENT_USE,
            "production_score_change": SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
            "status_detail": (
                f"posture={status['source_freshness_posture']}; "
                f"counts={status['source_freshness_counts']}"
            ),
        },
        {
            "artifact_family": "run_manifest",
            "available": status["has_run_manifest"],
            "current_use": RUN_MANIFEST_CURRENT_USE,
            "production_score_change": RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
            "status_detail": (
                f"run_id={status['run_id']}; "
                f"model_version={status['model_version']}; "
                f"manifest_score_change={status['manifest_score_change']}"
            ),
        },
    ]

    frame = pd.DataFrame(rows)
    available_count = int(frame["available"].fillna(False).astype(bool).sum())

    if available_count == 0:
        return None, SourceStatus(
            "WARIS operational review/control artifacts",
            "fallback",
            0,
            _operational_review_artifacts_note(),
        )

    return frame, SourceStatus(
        "WARIS operational review/control artifacts",
        "artifact",
        available_count,
        _operational_review_artifacts_note(),
    )


def _prozorro_expanded_feature_status() -> dict[str, object]:
    """Summarize expanded Prozorro procurement feature artifacts."""
    feature_rows = _load_optional_table(PROZORRO_EXPANDED_FEATURE_ROWS_RAW)
    oblast_features = _load_optional_table(PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE)
    oblast_sector_features = _load_optional_table(
        PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE
    )
    scoring_candidates = _load_optional_table(PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE)
    summary = _load_optional_table(PROZORRO_PROCUREMENT_FEATURE_SUMMARY_TABLE)

    top_oblast = "not_available"
    top_oblast_score = "not_available"

    if (
        oblast_features is not None
        and not oblast_features.empty
        and "procurement_review_priority_candidate" in oblast_features.columns
    ):
        working = oblast_features.copy()
        working["procurement_review_priority_candidate"] = pd.to_numeric(
            working["procurement_review_priority_candidate"],
            errors="coerce",
        ).fillna(0)
        working = working.sort_values(
            "procurement_review_priority_candidate",
            ascending=False,
        )

        if not working.empty:
            top_oblast = str(working.iloc[0].get("oblast", "not_available"))
            top_oblast_score = str(
                working.iloc[0].get(
                    "procurement_review_priority_candidate",
                    "not_available",
                )
            )

    top_oblast_sector = "not_available"
    top_oblast_sector_score = "not_available"

    if (
        oblast_sector_features is not None
        and not oblast_sector_features.empty
        and "procurement_review_priority_candidate" in oblast_sector_features.columns
    ):
        working = oblast_sector_features.copy()
        working["procurement_review_priority_candidate"] = pd.to_numeric(
            working["procurement_review_priority_candidate"],
            errors="coerce",
        ).fillna(0)
        working = working.sort_values(
            "procurement_review_priority_candidate",
            ascending=False,
        )

        if not working.empty:
            top_oblast_sector = (
                f"{working.iloc[0].get('oblast', 'not_available')} - "
                f"{working.iloc[0].get('sector', 'not_available')}"
            )
            top_oblast_sector_score = str(
                working.iloc[0].get(
                    "procurement_review_priority_candidate",
                    "not_available",
                )
            )

    current_use_values: list[str] = []
    prohibited_use_values: list[str] = []
    production_score_change_values: list[str] = []

    if scoring_candidates is not None and not scoring_candidates.empty:
        if "current_use" in scoring_candidates.columns:
            current_use_values = (
                scoring_candidates["current_use"]
                .fillna("")
                .astype(str)
                .loc[lambda s: s.ne("")]
                .drop_duplicates()
                .tolist()
            )

        if "prohibited_use" in scoring_candidates.columns:
            prohibited_use_values = (
                scoring_candidates["prohibited_use"]
                .fillna("")
                .astype(str)
                .loc[lambda s: s.ne("")]
                .drop_duplicates()
                .tolist()
            )

        if "production_score_change" in scoring_candidates.columns:
            production_score_change_values = (
                scoring_candidates["production_score_change"]
                .fillna("")
                .astype(str)
                .loc[lambda s: s.ne("")]
                .drop_duplicates()
                .tolist()
            )

    posture_current_use_ok = (
        PROZORRO_PROCUREMENT_CURRENT_USE in current_use_values
        if current_use_values
        else False
    )
    posture_prohibited_use_ok = (
        PROZORRO_PROCUREMENT_PROHIBITED_USE in prohibited_use_values
        if prohibited_use_values
        else False
    )
    posture_score_change_ok = (
        PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE in production_score_change_values
        if production_score_change_values
        else False
    )

    return {
        "has_expanded_features": (
            oblast_sector_features is not None and not oblast_sector_features.empty
        ),
        "feature_rows": 0 if feature_rows is None else len(feature_rows),
        "oblast_rows": 0 if oblast_features is None else len(oblast_features),
        "oblast_sector_rows": (
            0 if oblast_sector_features is None else len(oblast_sector_features)
        ),
        "scoring_candidate_rows": (
            0 if scoring_candidates is None else len(scoring_candidates)
        ),
        "summary_rows": 0 if summary is None else len(summary),
        "top_oblast": top_oblast,
        "top_oblast_score": top_oblast_score,
        "top_oblast_sector": top_oblast_sector,
        "top_oblast_sector_score": top_oblast_sector_score,
        "current_use_values": current_use_values,
        "prohibited_use_values": prohibited_use_values,
        "production_score_change_values": production_score_change_values,
        "posture_current_use_ok": posture_current_use_ok,
        "posture_prohibited_use_ok": posture_prohibited_use_ok,
        "posture_score_change_ok": posture_score_change_ok,
    }


def _prozorro_expanded_feature_note() -> str:
    """Return compact live-status note for expanded Prozorro feature artifacts."""
    status = _prozorro_expanded_feature_status()

    if not status["has_expanded_features"]:
        return (
            "Expanded Prozorro procurement feature artifacts were not found. Run "
            "python -m src.prozorro_procurement_features to generate review-only "
            "procurement feature candidates."
        )

    return (
        f"Expanded Prozorro procurement feature artifacts loaded. "
        f"Feature rows: {status['feature_rows']}; "
        f"oblast rows: {status['oblast_rows']}; "
        f"oblast-sector rows: {status['oblast_sector_rows']}; "
        f"scoring candidate rows: {status['scoring_candidate_rows']}. "
        f"Top oblast candidate: {status['top_oblast']} "
        f"({status['top_oblast_score']}). "
        f"Top oblast-sector candidate: {status['top_oblast_sector']} "
        f"({status['top_oblast_sector_score']}). "
        f"Current use: {status['current_use_values']} "
        f"(expected {PROZORRO_PROCUREMENT_CURRENT_USE}; "
        f"ok={status['posture_current_use_ok']}). "
        f"Prohibited use: {status['prohibited_use_values']} "
        f"(expected {PROZORRO_PROCUREMENT_PROHIBITED_USE}; "
        f"ok={status['posture_prohibited_use_ok']}). "
        f"Production score change: {status['production_score_change_values']} "
        f"(expected {PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE}; "
        f"ok={status['posture_score_change_ok']})."
    )


def _official_baseline_readiness_context() -> dict[str, str]:
    """Summarize official baseline validation and merge-readiness context."""
    readiness = _load_optional_table(OFFICIAL_BASELINE_READINESS_DECISION_TABLE)
    unit_summary = _load_optional_table(OFFICIAL_BASELINE_UNIT_EVIDENCE_SUMMARY_TABLE)
    merge_summary = _load_optional_table(OFFICIAL_BASELINE_MERGE_READINESS_SUMMARY_TABLE)

    decision = _first_table_value(readiness, "decision", "not_available")
    approved_current_use = _first_table_value(
        readiness,
        "approved_current_use",
        "not_available",
    )
    prohibited_current_use = _first_table_value(
        readiness,
        "prohibited_current_use",
        "not_available",
    )
    next_decision_point = _first_table_value(
        readiness,
        "next_decision_point",
        "not_available",
    )

    unit_interpretation = _first_table_value(
        unit_summary,
        "unit_interpretation",
        "not_available",
    )
    unit_validation_status = _first_table_value(
        unit_summary,
        "validation_status",
        "not_available",
    )

    merge_status = "not_available"
    merge_summary_text = "not_available"

    if merge_summary is not None and not merge_summary.empty:
        if {"summary_area", "status", "summary"}.issubset(merge_summary.columns):
            decision_rows = merge_summary[
                merge_summary["summary_area"]
                .fillna("")
                .astype(str)
                .eq("Readiness decision")
            ]

            if not decision_rows.empty:
                merge_status = str(decision_rows.iloc[0].get("status", "not_available"))
                merge_summary_text = str(
                    decision_rows.iloc[0].get("summary", "not_available")
                )
            else:
                merge_status = str(merge_summary.iloc[0].get("status", "not_available"))
                merge_summary_text = str(
                    merge_summary.iloc[0].get("summary", "not_available")
                )

    return {
        "decision": decision,
        "approved_current_use": approved_current_use,
        "prohibited_current_use": prohibited_current_use,
        "next_decision_point": next_decision_point,
        "unit_interpretation": unit_interpretation,
        "unit_validation_status": unit_validation_status,
        "merge_status": merge_status,
        "merge_summary": merge_summary_text,
    }


def _build_ukrstat_baseline_live_status_note(
    candidate_count: int,
    validation_values: list[str],
    scoring_values: list[str],
) -> str:
    """Build a concise live-status note for official baseline candidates."""
    context = _official_baseline_readiness_context()

    decision = context["decision"]
    approved_use = context["approved_current_use"]
    prohibited_use = context["prohibited_current_use"]
    unit_interpretation = context["unit_interpretation"]
    unit_status = context["unit_validation_status"]
    merge_status = context["merge_status"]

    if decision == "GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION":
        return (
            f"Loaded {candidate_count} official GRP baseline candidates. "
            f"Readiness decision: {decision}. "
            f"Approved current use: {approved_use}. "
            f"Prohibited current use: {prohibited_use}. "
            f"Unit evidence: {unit_interpretation} ({unit_status}). "
            f"Merge readiness: {merge_status}. "
            f"Current scoring use: {'; '.join(scoring_values[:3])}."
        )

    if decision != "not_available":
        return (
            f"Loaded {candidate_count} official GRP baseline candidates. "
            f"Readiness decision: {decision}. "
            f"Approved current use: {approved_use}. "
            f"Prohibited current use: {prohibited_use}. "
            f"Candidate validation status: {'; '.join(validation_values[:3])}. "
            f"Current scoring use: {'; '.join(scoring_values[:3])}."
        )

    return (
        f"Loaded {candidate_count} official baseline candidates. "
        f"Candidate validation status: {'; '.join(validation_values[:3])}. "
        f"Current scoring use: {'; '.join(scoring_values[:3])}. "
        "Run python -m src.official_baseline_validation and "
        "python -m src.official_baseline_merge_plan to populate readiness context."
    )


def load_ukrstat_oblast_baseline_candidate_status() -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Load validation-only official Ukrstat oblast baseline candidates if present.

    The official baseline candidate table is generated by src.ukrstat_observations,
    not by this live-data connector. This function records the artifact's presence,
    readiness decision, unit evidence, merge-readiness context, and scoring-use
    prohibition in live_data_status.csv so the PDF/dashboard can show that official
    baseline candidates exist and are controlled benchmark artifacts only.

    It deliberately does not blend official values into scoring.
    """
    ensure_dirs([RAW_DIR])

    if not UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE.exists():
        return None, SourceStatus(
            "Ukrstat regional accounts official baseline candidates",
            "fallback",
            0,
            (
                "Candidate table not found for this run. Run "
                "python -m src.ukrstat_observations to generate validation-only "
                "official oblast baseline candidates."
            ),
        )

    try:
        candidates = pd.read_csv(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE)
    except Exception as exc:
        return None, SourceStatus(
            "Ukrstat regional accounts official baseline candidates",
            "fallback",
            0,
            f"Candidate table could not be read: {exc}",
        )

    candidates = official_baseline_observations(candidates)

    if candidates.empty:
        return None, SourceStatus(
            "Ukrstat regional accounts official baseline candidates",
            "fallback",
            0,
            "Candidate table contains no usable official observations; status notices are not data.",
        )

    candidates = candidates.copy()

    if "oblast" in candidates.columns:
        candidates["waris_oblast"] = candidates["oblast"].apply(standardize_oblast)

    if "current_use_in_scoring" not in candidates.columns:
        candidates["current_use_in_scoring"] = UKRSTAT_BASELINE_CURRENT_USE_IN_SCORING

    if "validation_status" not in candidates.columns:
        candidates["validation_status"] = UKRSTAT_BASELINE_VALIDATION_STATUS

    audit_path = RAW_DIR / "ukrstat_oblast_baseline_candidates_audit.csv"
    candidates.to_csv(audit_path, index=False)

    validation_values = (
        candidates["validation_status"]
        .fillna("")
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    scoring_values = (
        candidates["current_use_in_scoring"]
        .fillna("")
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    note = _build_ukrstat_baseline_live_status_note(
        candidate_count=len(candidates),
        validation_values=validation_values,
        scoring_values=scoring_values,
    )

    return candidates, SourceStatus(
        "Ukrstat regional accounts official baseline candidates",
        "live",
        len(candidates),
        note,
    )

def fetch_ukrstat_sdmx_dataflows() -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Fetch Ukrstat SDMX dataflow metadata for future official baseline mapping.

    This first version does not force a specific statistics dataset into WARIS.
    It verifies SDMX access and saves metadata so we can identify the right
    regional/sector economic dataflows later.
    """
    ensure_dirs([RAW_DIR])

    try:
        response = requests.get(
            UKRSTAT_SDMX_DATAFLOW_URL,
            timeout=45,
            headers={
                "User-Agent": "WARIS research prototype",
                "Accept": "application/vnd.sdmx.structure+json;version=2.0.0, application/json",
            },
        )

        if response.status_code != 200:
            return None, SourceStatus(
                "Ukrstat SDMX dataflow discovery",
                "fallback",
                0,
                f"HTTP {response.status_code}",
            )

        payload = response.json()

        raw_path = RAW_DIR / "ukrstat_sdmx_dataflows_raw.json"
        raw_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        rows = []

        def walk(obj):
            if isinstance(obj, dict):
                if "id" in obj and ("name" in obj or "names" in obj):
                    name_value = obj.get("name", obj.get("names", ""))
                    rows.append(
                        {
                            "id": obj.get("id"),
                            "name": str(name_value)[:500],
                        }
                    )
                for value in obj.values():
                    walk(value)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)

        walk(payload)

        df = pd.DataFrame(rows).drop_duplicates()

        if not df.empty:
            df.to_csv(RAW_DIR / "ukrstat_sdmx_dataflows_raw.csv", index=False)

        return df, SourceStatus(
            "Ukrstat SDMX dataflow discovery",
            "live",
            len(df),
            "Ukrstat SDMX dataflow metadata fetched",
        )

    except Exception as exc:
        return None, SourceStatus(
            "Ukrstat SDMX dataflow discovery",
            "fallback",
            0,
            f"Ukrstat SDMX discovery failed: {exc}",
        )


def infer_waris_layer_from_indicator_text(text: object) -> str:
    """Infer the most relevant WARIS model layer from indicator metadata text."""
    t = _normalize_text(text)

    if any(
        k in t
        for k in [
            "revenue",
            "turnover",
            "sales",
            "output",
            "production",
            "gross regional",
            "gdp",
            "gva",
            "value added",
            "enterprise",
            "business activity",
        ]
    ):
        return "revenue_anomaly_risk"

    if any(
        k in t
        for k in [
            "procurement",
            "contract",
            "construction",
            "reconstruction",
            "capital investment",
            "infrastructure",
            "public works",
        ]
    ):
        return "procurement_integrity_risk"

    if any(
        k in t
        for k in [
            "export",
            "import",
            "trade",
            "transport",
            "freight",
            "logistics",
            "cargo",
            "customs",
        ]
    ):
        return "tbml_risk"

    if any(
        k in t
        for k in [
            "bank",
            "loan",
            "deposit",
            "payment",
            "financial",
            "credit",
            "non-performing",
            "npl",
            "capital adequacy",
            "liquidity",
        ]
    ):
        return "financial_supervision_exposure"

    if any(
        k in t
        for k in [
            "sanction",
            "ownership",
            "beneficial owner",
            "counterparty",
            "legal entity",
            "company",
            "register",
        ]
    ):
        return "sanctions_exposure_risk"

    if any(
        k in t
        for k in [
            "oblast",
            "region",
            "regional",
            "territorial",
            "community",
            "district",
            "raion",
        ]
    ):
        return "official_regional_baseline"

    return "general_context"


def build_nbu_indicator_catalog(
    nbu_status_df: Optional[pd.DataFrame],
) -> Optional[pd.DataFrame]:
    """Build a compact catalog of available NBU datasets and inferred WARIS uses."""
    if nbu_status_df is None or nbu_status_df.empty:
        return None

    rows = []

    for _, row in nbu_status_df.iterrows():
        dataset = str(row.get("dataset", ""))
        endpoint = str(row.get("endpoint", ""))
        status = str(row.get("status", ""))
        note = str(row.get("note", ""))

        text = " ".join([dataset, endpoint, note])

        rows.append(
            {
                "source_family": "NBU",
                "indicator_id": endpoint,
                "indicator_name": dataset.replace("_", " "),
                "source_status": status,
                "waris_layer_candidate": infer_waris_layer_from_indicator_text(text),
                "keyword_hits": "",
                "current_use": (
                    "National financial-sector context; candidate input for a more "
                    "precise financial-supervision exposure layer."
                ),
                "implementation_status": (
                    "available_raw_context"
                    if status == "live"
                    else "not_available_this_run"
                ),
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return None

    return df


def build_ukrstat_indicator_catalog(
    ukrstat_dataflows: Optional[pd.DataFrame],
) -> Optional[pd.DataFrame]:
    """Build a candidate Ukrstat indicator catalog from SDMX dataflow metadata.

    This does not yet pull specific statistical observations. It identifies
    candidate official baseline datasets for future regional/sector integration.
    """
    if ukrstat_dataflows is None or ukrstat_dataflows.empty:
        return None

    rows = []

    priority_keywords = [
        "regional",
        "oblast",
        "gross regional",
        "gdp",
        "gva",
        "value added",
        "enterprise",
        "turnover",
        "sales",
        "production",
        "industry",
        "agriculture",
        "construction",
        "transport",
        "trade",
        "export",
        "import",
        "services",
        "capital investment",
        "employment",
        "wages",
        "prices",
    ]

    for _, row in ukrstat_dataflows.iterrows():
        indicator_id = str(row.get("id", ""))
        indicator_name = str(row.get("name", ""))

        text = " ".join([indicator_id, indicator_name])
        text_norm = _normalize_text(text)

        keyword_hits = [
            keyword for keyword in priority_keywords if keyword in text_norm
        ]

        if not keyword_hits:
            continue

        rows.append(
            {
                "source_family": "Ukrstat SDMX",
                "indicator_id": indicator_id,
                "indicator_name": indicator_name[:500],
                "source_status": "live_metadata",
                "waris_layer_candidate": infer_waris_layer_from_indicator_text(text),
                "keyword_hits": "; ".join(keyword_hits[:8]),
                "current_use": (
                    "Candidate official statistical baseline. DF_REGIONAL_ACCOUNTS "
                    "now has a separate validation-only oblast GRP baseline candidate "
                    "artifact when src.ukrstat_observations is run."
                ),
                "implementation_status": (
                    "candidate_metadata_and_observation_transition"
                    if indicator_id == "DF_REGIONAL_ACCOUNTS"
                    else "candidate_metadata_only"
                ),
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return None

    return (
        df.sort_values(
            ["waris_layer_candidate", "indicator_id"],
            ascending=[True, True],
        )
        .reset_index(drop=True)
    )


def build_official_indicator_catalog(
    nbu_status_df: Optional[pd.DataFrame],
    ukrstat_dataflows: Optional[pd.DataFrame],
) -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Combine NBU and Ukrstat candidate indicators into one alignment catalog."""
    ensure_dirs([RAW_DIR, OFFICIAL_INDICATOR_CATALOG_TABLE.parent])

    catalogs = []

    nbu_catalog = build_nbu_indicator_catalog(nbu_status_df)
    if nbu_catalog is not None and not nbu_catalog.empty:
        catalogs.append(nbu_catalog)

    ukrstat_catalog = build_ukrstat_indicator_catalog(ukrstat_dataflows)
    if ukrstat_catalog is not None and not ukrstat_catalog.empty:
        catalogs.append(ukrstat_catalog)

    if not catalogs:
        return None, SourceStatus(
            "Official indicator alignment catalog",
            "fallback",
            0,
            "No NBU/Ukrstat candidate indicators identified",
        )

    catalog = pd.concat(catalogs, ignore_index=True)

    catalog.to_csv(OFFICIAL_INDICATOR_CATALOG_RAW, index=False)
    catalog.to_csv(OFFICIAL_INDICATOR_CATALOG_TABLE, index=False)

    return catalog, SourceStatus(
        "Official indicator alignment catalog",
        "live",
        len(catalog),
        "NBU/Ukrstat candidate indicators mapped to WARIS model layers",
    )


def fetch_opensanctions_sample() -> tuple[Optional[pd.DataFrame], SourceStatus]:
    """Fetch a sample from OpenSanctions Ukraine NSDC FollowTheMoney JSONL export."""
    ensure_dirs([RAW_DIR])

    url = os.getenv(
        "OPENSANCTIONS_UA_NSDC_URL",
        "https://data.opensanctions.org/datasets/latest/ua_nsdc_sanctions/entities.ftm.json",
    )

    rows = []

    raw_path = RAW_DIR / "opensanctions_ua_nsdc_entities_sample.jsonl"
    csv_path = RAW_DIR / "opensanctions_ua_nsdc_sample_raw.csv"

    try:
        response = requests.get(
            url,
            timeout=45,
            headers={"User-Agent": "WARIS research prototype"},
            stream=True,
        )
        response.raise_for_status()

        if url.lower().endswith(".csv"):
            df = pd.read_csv(url, nrows=5000)

            if df.empty:
                return None, SourceStatus(
                    "OpenSanctions Ukraine NSDC",
                    "fallback",
                    0,
                    "CSV export returned no rows",
                )

            df.to_csv(csv_path, index=False)

            return df, SourceStatus(
                "OpenSanctions Ukraine NSDC",
                "live",
                len(df),
                f"Fetched CSV sample from {url}",
            )

        for i, line in enumerate(response.iter_lines(decode_unicode=True)):
            if i >= 5000:
                break

            if not line:
                continue

            entity = json.loads(line)
            props = entity.get("properties", {}) or {}

            rows.append(
                {
                    "id": entity.get("id"),
                    "schema": entity.get("schema"),
                    "caption": entity.get("caption"),
                    "datasets": "|".join(entity.get("datasets", []) or []),
                    "topics": "|".join(entity.get("topics", []) or []),
                    "countries": "|".join(
                        props.get("country", [])
                        or props.get("jurisdiction", [])
                        or props.get("nationality", [])
                        or []
                    ),
                }
            )

        df = pd.DataFrame(rows)

        if df.empty:
            return None, SourceStatus(
                "OpenSanctions Ukraine NSDC",
                "fallback",
                0,
                "JSONL export returned no parsed rows",
            )

        df.to_json(raw_path, orient="records", lines=True, force_ascii=False)
        df.to_csv(csv_path, index=False)

        return df, SourceStatus(
            "OpenSanctions Ukraine NSDC",
            "live",
            len(df),
            "Parsed entities.ftm.json as JSON Lines",
        )

    except Exception as exc:
        print(f"[WARN] OpenSanctions fetch failed for {url}: {exc}")

        return None, SourceStatus(
            "OpenSanctions Ukraine NSDC",
            "fallback",
            0,
            f"OpenSanctions fetch failed: {exc}",
        )


def enrich_with_optional_live_data(
    base_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Blend available live proxies into the base sector/oblast model inputs.

    Blend design:
    - Existing synthetic values keep the model runnable and structurally stable.
    - Live values override part of the relevant proxy rather than fully replacing
      it because samples may be incomplete, recent-only, or uneven by source.
    """
    ensure_dirs([RAW_DIR])

    out = base_df.copy()
    statuses: list[SourceStatus] = []

    prozorro_df, status = fetch_prozorro_tenders(limit=50, detail_limit=50)
    statuses.append(status)

    procurement_proxy = build_procurement_proxy(prozorro_df)

    if procurement_proxy is not None:
        out = out.merge(
            procurement_proxy[
                [
                    "oblast",
                    "sector",
                    "procurement_awards_proxy_live",
                ]
            ],
            on=["oblast", "sector"],
            how="left",
        )

        mask = out["procurement_awards_proxy_live"].notna()

        out.loc[mask, "procurement_awards_proxy"] = (
            0.60 * out.loc[mask, "procurement_awards_proxy"]
            + 0.40 * out.loc[mask, "procurement_awards_proxy_live"]
        )

    # Expanded Prozorro procurement features are generated separately by
    # src.prozorro_procurement_features and now by main.py before live-data
    # enrichment. They are added to live_data_status.csv as review-only
    # artifacts, but they are not blended into production scoring here.
    _, status = load_prozorro_expanded_procurement_feature_status()
    statuses.append(status)

    # Wartime AML/CFT typology and FIU/SFMS context artifacts are generated
    # separately and surfaced in live_data_status.csv as source-support context.
    # They are not blended into WARIS production scoring here.
    _, status = load_wartime_aml_typology_status()
    statuses.append(status)

    _, status = load_fiu_official_context_status()
    statuses.append(status)

    # Operational review and documentation artifacts are generated separately
    # and surfaced here for report/dashboard status only. They are not blended
    # into WARIS production scoring.
    _, status = load_operational_review_artifacts_status()
    statuses.append(status)

    acled_df, status = fetch_acled_ukraine()
    statuses.append(status)

    conflict_proxy = build_conflict_proxy(acled_df)

    if conflict_proxy is not None:
        out = out.merge(
            conflict_proxy[
                [
                    "oblast",
                    "conflict_intensity_proxy_live",
                ]
            ],
            on="oblast",
            how="left",
        )

        # Any model oblast that does not appear in the ACLED sample receives
        # a zero live-conflict value. The existing synthetic fallback field is
        # still retained through the 50/50 blend below.
        out["conflict_intensity_proxy_live"] = out[
            "conflict_intensity_proxy_live"
        ].fillna(0)

        out["conflict_intensity_proxy"] = (
            0.50 * out["conflict_intensity_proxy"]
            + 0.50 * out["conflict_intensity_proxy_live"]
        )

    _, status = fetch_world_bank_ukraine_context()
    statuses.append(status)

    nbu_status_df, status = fetch_nbu_financial_context()
    statuses.append(status)

    nbu_proxy = build_nbu_financial_proxy(nbu_status_df)

    if nbu_proxy is not None and "financial_supervision_proxy" in out.columns:
        out["financial_supervision_proxy"] = (
            0.90 * out["financial_supervision_proxy"] + 0.10 * nbu_proxy
        )

    ukrstat_dataflows, status = fetch_ukrstat_sdmx_dataflows()
    statuses.append(status)

    _, status = load_ukrstat_oblast_baseline_candidate_status()
    statuses.append(status)

    _, status = build_official_indicator_catalog(
        nbu_status_df=nbu_status_df,
        ukrstat_dataflows=ukrstat_dataflows,
    )
    statuses.append(status)

    _, status = fetch_opensanctions_sample()
    statuses.append(status)

    status_df = pd.DataFrame([s.__dict__ for s in statuses])

    status_df.to_csv(LIVE_DATA_STATUS_RAW, index=False)
    out.to_csv(ENRICHED_INPUTS_RAW, index=False)

    return out, status_df