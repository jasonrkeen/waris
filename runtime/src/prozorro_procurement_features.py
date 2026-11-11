"""Prozorro procurement feature expansion for WARIS.

This module builds a deeper procurement-risk feature layer from public Prozorro
tender data while preserving the current WARIS control posture.

It is designed as a source-backed enrichment and review artifact. It does not
make entity-level accusations and does not replace the existing WARIS composite
score unless a future model-governance change explicitly approves that.

This module is intentionally separate from the official FIU/SFMS context layer,
wartime AML/CFT typology register, official baseline benchmark layer, analyst
review workflow, false-positive controls, source-freshness monitoring, and run
manifest. Those artifacts can reference Prozorro context through downstream
bridge/review modules, but this module does not consume FIU/SFMS, typology,
official GRP, analyst-review, false-positive, source-freshness, or run-manifest
data and does not change WARIS scoring.

Purpose:
    Expand procurement integrity context beyond simple recent-tender counts by
    producing oblast/sector-level features such as:

    - tender count
    - expected value
    - supplier/bidder counts when available
    - single-bid proxy
    - buyer concentration
    - procurement-method mix
    - reconstruction/emergency keyword exposure
    - CPV/category distribution
    - oblast/sector aggregation
    - WARIS-ready procurement feature candidates

Current use:
    review_artifact_only

Prohibited use:
    Entity-level accusation, automated adverse action, or direct scoring
    integration without SME review and model change-control approval.

Production score change:
    none

Outputs:
    data/raw/prozorro_expanded_tenders_raw.csv
    data/raw/prozorro_expanded_tender_details_raw.csv
    data/raw/prozorro_expanded_feature_rows_raw.csv
    outputs/tables/prozorro_procurement_features_oblast.csv
    outputs/tables/prozorro_procurement_features_oblast_sector.csv
    outputs/tables/prozorro_procurement_feature_summary.csv
    outputs/tables/prozorro_procurement_scoring_candidates.csv
"""

from __future__ import annotations

import ast
import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import requests

from .config import RAW_DIR, TABLE_DIR
from .data_collection import OBLASTS, SECTORS
from .utils import ensure_dirs, min_max_scale

try:
    from .config import (
        PROZORRO_API_BASE_URL,
        PROZORRO_MAX_PAGES,
        PROZORRO_PAGE_LIMIT,
        PROZORRO_MAX_DETAIL_RECORDS,
        PROZORRO_SLEEP_SECONDS,
        PROZORRO_TIMEOUT_SECONDS,
        PROZORRO_EXPANDED_TENDERS_RAW,
        PROZORRO_EXPANDED_TENDER_DETAILS_RAW,
        PROZORRO_EXPANDED_FEATURE_ROWS_RAW,
        PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE,
        PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE,
        PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE,
        PROZORRO_PROCUREMENT_FEATURE_SUMMARY_TABLE,
        PROZORRO_PROCUREMENT_CURRENT_USE,
        PROZORRO_PROCUREMENT_PROHIBITED_USE,
        PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE,
        FIU_CONTEXT_CURRENT_USE,
        WARTIME_AML_TYPOLOGY_CURRENT_USE,
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
    PROZORRO_API_BASE_URL = "https://public.api.openprocurement.org/api/2.5/tenders"
    PROZORRO_MAX_PAGES = 3
    PROZORRO_PAGE_LIMIT = 100
    PROZORRO_MAX_DETAIL_RECORDS = 150
    PROZORRO_SLEEP_SECONDS = 0.25
    PROZORRO_TIMEOUT_SECONDS = 30
    PROZORRO_EXPANDED_TENDERS_RAW = RAW_DIR / "prozorro_expanded_tenders_raw.csv"
    PROZORRO_EXPANDED_TENDER_DETAILS_RAW = (
        RAW_DIR / "prozorro_expanded_tender_details_raw.csv"
    )
    PROZORRO_EXPANDED_FEATURE_ROWS_RAW = (
        RAW_DIR / "prozorro_expanded_feature_rows_raw.csv"
    )
    PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE = (
        TABLE_DIR / "prozorro_procurement_features_oblast.csv"
    )
    PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE = (
        TABLE_DIR / "prozorro_procurement_features_oblast_sector.csv"
    )
    PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE = (
        TABLE_DIR / "prozorro_procurement_scoring_candidates.csv"
    )
    PROZORRO_PROCUREMENT_FEATURE_SUMMARY_TABLE = (
        TABLE_DIR / "prozorro_procurement_feature_summary.csv"
    )
    PROZORRO_PROCUREMENT_CURRENT_USE = "review_artifact_only"
    PROZORRO_PROCUREMENT_PROHIBITED_USE = "direct_scoring_without_change_control"
    PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE = "none"
    FIU_CONTEXT_CURRENT_USE = "official_fiu_context_and_typology_support_only"
    WARTIME_AML_TYPOLOGY_CURRENT_USE = (
        "literature_support_and_typology_reference_only"
    )
    ANALYST_REVIEW_CURRENT_USE = "analyst_review_workflow_only"
    ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE = "none"
    FALSE_POSITIVE_CONTROLS_CURRENT_USE = "human_review_support_only"
    FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE = "none"
    SOURCE_FRESHNESS_CURRENT_USE = "source_freshness_monitoring_only"
    SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE = "none"
    RUN_MANIFEST_CURRENT_USE = "run_manifest_documentation"
    RUN_MANIFEST_PRODUCTION_SCORE_CHANGE = "none"

PROZORRO_FEED_URL = PROZORRO_API_BASE_URL
PROZORRO_TENDER_DETAIL_URL = f"{PROZORRO_API_BASE_URL}/{{tender_id}}"

RAW_TENDER_LIST_TABLE = PROZORRO_EXPANDED_TENDERS_RAW
RAW_TENDER_DETAIL_TABLE = PROZORRO_EXPANDED_TENDER_DETAILS_RAW
RAW_FEATURE_ROWS_TABLE = PROZORRO_EXPANDED_FEATURE_ROWS_RAW
OBLAST_FEATURE_TABLE = PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE
OBLAST_SECTOR_FEATURE_TABLE = PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE
FEATURE_SUMMARY_TABLE = PROZORRO_PROCUREMENT_FEATURE_SUMMARY_TABLE
SCORING_CANDIDATE_TABLE = PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE


# Conservative keyword mapping. These keywords support aggregate categorization
# only; they are not allegations of misconduct.
SECTOR_KEYWORDS = {
    "Construction and reconstruction": [
        "construction",
        "reconstruction",
        "repair",
        "restoration",
        "building",
        "road",
        "bridge",
        "housing",
        "infrastructure",
        "будівниц",
        "ремонт",
        "віднов",
        "реконструк",
        "дорог",
        "міст",
        "житл",
        "інфраструкт",
    ],
    "Fuel and logistics": [
        "fuel",
        "diesel",
        "gasoline",
        "logistics",
        "transport",
        "freight",
        "vehicle",
        "oil",
        "бензин",
        "дизель",
        "палив",
        "логіст",
        "транспорт",
        "перевез",
        "нафт",
    ],
    "Agriculture and grain trade": [
        "grain",
        "wheat",
        "corn",
        "sunflower",
        "agriculture",
        "seed",
        "fertilizer",
        "зерн",
        "пшени",
        "кукуруд",
        "соняш",
        "сільськ",
        "насін",
        "добрив",
    ],
    "Financial and payment services": [
        "bank",
        "payment",
        "financial",
        "insurance",
        "audit",
        "accounting",
        "банк",
        "платіж",
        "фінанс",
        "страх",
        "аудит",
        "бухгалтер",
    ],
    "Defense-adjacent manufacturing": [
        "defense",
        "military",
        "security",
        "uniform",
        "protective",
        "equipment",
        "drone",
        "vehicle repair",
        "оборон",
        "військ",
        "безпек",
        "форма",
        "захис",
        "обладнан",
        "дрон",
    ],
    "Retail and consumer goods": [
        "food",
        "consumer",
        "retail",
        "clothing",
        "medicine",
        "supplies",
        "продукт",
        "спожив",
        "роздріб",
        "одяг",
        "медикамент",
        "постач",
    ],
}

RECONSTRUCTION_EMERGENCY_KEYWORDS = [
    "reconstruction",
    "restoration",
    "repair",
    "recovery",
    "emergency",
    "critical infrastructure",
    "shelter",
    "damage",
    "віднов",
    "реконструк",
    "ремонт",
    "аварі",
    "надзвичай",
    "критич",
    "укрит",
    "пошкод",
]

OBLAST_KEYWORDS = {
    "Cherkasy": ["cherkasy", "черка"],
    "Chernihiv": ["chernihiv", "черніг"],
    "Chernivtsi": ["chernivtsi", "чернів"],
    "Dnipropetrovsk": ["dnipro", "dnipropetrovsk", "дніпро", "дніпроп"],
    "Donetsk": ["donetsk", "донець"],
    "Ivano-Frankivsk": ["ivano", "frankivsk", "івано", "франків"],
    "Kharkiv": ["kharkiv", "харків"],
    "Kherson": ["kherson", "херсон"],
    "Khmelnytskyi": ["khmelnytskyi", "хмельниц"],
    "Kirovohrad": ["kirovohrad", "kropyvnytskyi", "кіровоград", "кропивниц"],
    "Kyiv": ["kyiv oblast", "kyivska", "київська", "київськ"],
    "Luhansk": ["luhansk", "луган"],
    "Lviv": ["lviv", "львів"],
    "Mykolaiv": ["mykolaiv", "микола"],
    "Odesa": ["odesa", "odessa", "одес"],
    "Poltava": ["poltava", "полтав"],
    "Rivne": ["rivne", "рівнен", "рівне"],
    "Sumy": ["sumy", "сум"],
    "Ternopil": ["ternopil", "терноп"],
    "Vinnytsia": ["vinnytsia", "вінниц"],
    "Volyn": ["volyn", "волин"],
    "Zakarpattia": ["zakarpattia", "uzhhorod", "закарпат", "ужгород"],
    "Zaporizhzhia": ["zaporizhzhia", "zaporizhia", "запор"],
    "Zhytomyr": ["zhytomyr", "житом"],
    "Kyiv City": ["kyiv city", "м. київ", "місто київ", "київ "],
}


@dataclass
class ProzorroFetchConfig:
    """Runtime settings for Prozorro fetches."""

    max_pages: int = 3
    page_limit: int = 100
    max_detail_records: int = 150
    sleep_seconds: float = 0.25
    timeout_seconds: int = 30
    opt_fields: str = (
        "id,tenderID,dateModified,title,description,status,"
        "procurementMethodType,value,procuringEntity,items,awards,bids"
    )


def _env_int(name: str, default: int) -> int:
    """Read integer environment variable with fallback."""
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    """Read float environment variable with fallback."""
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def _runtime_config() -> ProzorroFetchConfig:
    """Create fetch config from optional environment overrides."""
    return ProzorroFetchConfig(
        max_pages=_env_int("PROZORRO_MAX_PAGES", PROZORRO_MAX_PAGES),
        page_limit=_env_int("PROZORRO_PAGE_LIMIT", PROZORRO_PAGE_LIMIT),
        max_detail_records=_env_int(
            "PROZORRO_MAX_DETAIL_RECORDS",
            PROZORRO_MAX_DETAIL_RECORDS,
        ),
        sleep_seconds=_env_float("PROZORRO_SLEEP_SECONDS", PROZORRO_SLEEP_SECONDS),
        timeout_seconds=_env_int("PROZORRO_TIMEOUT_SECONDS", PROZORRO_TIMEOUT_SECONDS),
    )


def _safe_get_json(url: str, params: dict[str, Any] | None, timeout: int) -> dict[str, Any]:
    """GET JSON with conservative error handling."""
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
        return {"error": str(exc), "data": []}


def _flatten_text(value: Any) -> str:
    """Flatten common nested tender fields into searchable text."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        return " ".join(_flatten_text(v) for v in value.values())

    if isinstance(value, list):
        return " ".join(_flatten_text(v) for v in value)

    return str(value)


def _contains_any(text: str, keywords: list[str]) -> bool:
    """Return whether lowercase text contains any keyword."""
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in keywords)


def _classify_sector(text: str) -> str:
    """Map tender text to a WARIS sector using conservative keyword rules."""
    scores = {}

    for sector, keywords in SECTOR_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword.lower() in text.lower())
        scores[sector] = score

    best_sector = max(scores, key=scores.get)

    if scores[best_sector] == 0:
        return "Retail and consumer goods"

    return best_sector


def _infer_oblast(text: str) -> str | None:
    """Infer oblast from tender text using keyword rules."""
    lower = text.lower()

    # Handle Kyiv City before Kyiv oblast because it is more specific.
    if any(keyword in lower for keyword in OBLAST_KEYWORDS["Kyiv City"]):
        if "обла" not in lower and "oblast" not in lower:
            return "Kyiv City"

    for oblast, keywords in OBLAST_KEYWORDS.items():
        if oblast == "Kyiv City":
            continue

        if any(keyword.lower() in lower for keyword in keywords):
            return oblast

    return None


def _extract_value_amount(tender: dict[str, Any]) -> float:
    """Extract tender expected value amount."""
    value = tender.get("value") or {}

    if isinstance(value, dict):
        try:
            return float(value.get("amount", 0) or 0)
        except Exception:
            return 0.0

    return 0.0


def _extract_currency(tender: dict[str, Any]) -> str:
    """Extract tender currency."""
    value = tender.get("value") or {}

    if isinstance(value, dict):
        return str(value.get("currency", "not_available"))

    return "not_available"


def _extract_bids_count(tender: dict[str, Any]) -> int | None:
    """Count visible bid objects; an unavailable list is not zero bids."""
    bids = tender.get("bids")
    if not isinstance(bids, list) or any(not isinstance(bid, dict) for bid in bids):
        return None
    return len(bids)


def _extract_award_supplier_count(tender: dict[str, Any]) -> int | None:
    """Count visible suppliers across award records, without inferring winners."""
    awards = tender.get("awards")
    if not isinstance(awards, list):
        return None
    suppliers = set()
    for award in awards:
        if not isinstance(award, dict):
            return None
        visible = award.get("suppliers")
        if not isinstance(visible, list) or not visible:
            return None
        for supplier in visible:
            if not isinstance(supplier, dict):
                return None
            identifier = supplier.get("identifier")
            key = identifier.get("id") if isinstance(identifier, dict) else None
            key = key or supplier.get("name")
            if not key:
                return None
            suppliers.add(str(key))
    return len(suppliers)


def _combined_visible_proxy(bids: int | None, suppliers: int | None) -> int | None:
    """Three-valued OR: a known positive suffices; false needs both observations."""
    if bids == 1 or suppliers == 1:
        return 1
    if bids is None or suppliers is None:
        return None
    return 0


def _extract_buyer_name(tender: dict[str, Any]) -> str:
    """Extract procuring entity name."""
    entity = tender.get("procuringEntity") or {}

    if isinstance(entity, dict):
        return str(entity.get("name", "not_available"))

    return "not_available"


def _extract_cpv_codes(tender: dict[str, Any]) -> str:
    """Extract CPV/classification codes from tender items."""
    codes = []

    items = tender.get("items") or []

    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue

            classification = item.get("classification") or {}

            if isinstance(classification, dict):
                code = classification.get("id")
                if code:
                    codes.append(str(code))

    return ";".join(sorted(set(codes)))


def fetch_recent_prozorro_tenders(config: ProzorroFetchConfig | None = None) -> pd.DataFrame:
    """Fetch recent tender feed rows from Prozorro public API."""
    ensure_dirs([RAW_DIR])

    config = config or _runtime_config()

    records: list[dict[str, Any]] = []
    offset = None

    for page in range(config.max_pages):
        params: dict[str, Any] = {
            "limit": config.page_limit,
            "descending": "1",
            "opt_fields": config.opt_fields,
        }

        if offset:
            params["offset"] = offset

        payload = _safe_get_json(
            PROZORRO_FEED_URL,
            params=params,
            timeout=config.timeout_seconds,
        )

        data = payload.get("data", [])

        if not isinstance(data, list) or not data:
            break

        for row in data:
            if isinstance(row, dict):
                row["_source_page"] = page + 1
                records.append(row)

        next_page = payload.get("next_page") or {}
        uri = next_page.get("uri") if isinstance(next_page, dict) else None
        offset = next_page.get("offset") if isinstance(next_page, dict) else None

        if not offset and uri and "offset=" in uri:
            # Fallback extraction for older API response shapes.
            try:
                offset = uri.split("offset=", 1)[1].split("&", 1)[0]
            except Exception:
                offset = None

        if not offset:
            break

        time.sleep(config.sleep_seconds)

    df = pd.DataFrame(records)

    if df.empty:
        df = pd.DataFrame(
            columns=[
                "id",
                "tenderID",
                "dateModified",
                "title",
                "description",
                "status",
                "procurementMethodType",
            ]
        )

    df.to_csv(RAW_TENDER_LIST_TABLE, index=False)
    return df


def fetch_tender_details(
    tender_feed: pd.DataFrame,
    config: ProzorroFetchConfig | None = None,
) -> pd.DataFrame:
    """Fetch tender detail records for a bounded tender sample."""
    ensure_dirs([RAW_DIR])

    config = config or _runtime_config()

    if tender_feed.empty or "id" not in tender_feed.columns:
        df = pd.DataFrame()
        df.to_csv(RAW_TENDER_DETAIL_TABLE, index=False)
        return df

    tender_ids = (
        tender_feed["id"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .head(config.max_detail_records)
        .tolist()
    )

    records = []

    for i, tender_id in enumerate(tender_ids, start=1):
        url = PROZORRO_TENDER_DETAIL_URL.format(tender_id=tender_id)
        payload = _safe_get_json(url, params=None, timeout=config.timeout_seconds)

        data = payload.get("data", {})

        if isinstance(data, dict):
            data["_detail_fetch_order"] = i
            records.append(data)

        time.sleep(config.sleep_seconds)

    df = pd.DataFrame(records)

    if df.empty:
        df = pd.DataFrame(columns=["id", "tenderID", "dateModified"])

    df.to_csv(RAW_TENDER_DETAIL_TABLE, index=False)
    return df


def _restore_nested_tender_fields(tenders: pd.DataFrame) -> pd.DataFrame:
    """Restore only known nested fields from JSON or legacy literal CSV cells.

    Invalid or oversized cells fail without including source contents in errors.
    This restores serialization, not source acquisition or missing observations.
    """
    expected = {"value": dict, "procuringEntity": dict, "items": list,
                "awards": list, "bids": list}
    out = tenders.copy()
    for field, container in expected.items():
        if field not in out:
            continue

        def restore(value: Any) -> Any:
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return None
            if isinstance(value, str):
                if not value.strip():
                    return None
                if len(value) > 2_000_000:
                    raise ValueError(f"Oversized nested procurement field: {field}")
                try:
                    value = json.loads(value)
                except (ValueError, RecursionError):
                    try:
                        tree = ast.parse(value, mode="eval")
                        if sum(1 for _ in ast.walk(tree)) > 50_000:
                            raise ValueError("Too many nodes")
                        value = ast.literal_eval(tree)
                    except (ValueError, SyntaxError, RecursionError, TypeError):
                        raise ValueError(f"Invalid nested procurement field: {field}") from None
            if value is None:
                return None
            if not isinstance(value, container):
                raise ValueError(f"Wrong container for nested procurement field: {field}")
            return value

        out[field] = out[field].map(restore)
    return out


def _prepare_tender_feature_rows(tenders: pd.DataFrame) -> pd.DataFrame:
    """Convert raw tender/detail rows into normalized feature rows."""
    tenders = _restore_nested_tender_fields(tenders)
    rows = []
    if not tenders.empty and ("id" not in tenders or tenders["id"].isna().any()
                              or tenders["id"].astype(str).str.strip().eq("").any()
                              or tenders["id"].duplicated().any()):
        raise ValueError("Missing or duplicate procurement record identity")

    for _, row in tenders.iterrows():
        tender = row.to_dict()

        searchable_text = " ".join(
            [
                _flatten_text(tender.get("title")),
                _flatten_text(tender.get("description")),
                _flatten_text(tender.get("procuringEntity")),
                _flatten_text(tender.get("items")),
            ]
        )

        oblast = _infer_oblast(searchable_text)
        sector = _classify_sector(searchable_text)

        value_amount = _extract_value_amount(tender)
        bids_count = _extract_bids_count(tender)
        supplier_count = _extract_award_supplier_count(tender)
        buyer_name = _extract_buyer_name(tender)

        reconstruction_emergency_flag = int(
            _contains_any(searchable_text, RECONSTRUCTION_EMERGENCY_KEYWORDS)
        )

        rows.append(
            {
                "tender_id": tender.get("id", ""),
                "tender_public_id": tender.get("tenderID", ""),
                "date_modified": tender.get("dateModified", ""),
                "status": tender.get("status", ""),
                "procurement_method_type": tender.get("procurementMethodType", ""),
                "buyer_name": buyer_name,
                "oblast": oblast if oblast else "Unmapped",
                "sector": sector,
                "value_amount": value_amount,
                "currency": _extract_currency(tender),
                "bids_count": bids_count,
                "supplier_count": supplier_count,
                "bids_observation_status": "visible_list" if bids_count is not None else "unavailable",
                "supplier_observation_status": "visible_award_records" if supplier_count is not None else "unavailable_or_incomplete",
                "supplier_count_scope": "all_visible_award_records_not_winning_supplier_count",
                "single_visible_bid_flag": int(bids_count == 1) if bids_count is not None else None,
                "single_visible_award_supplier_flag": int(supplier_count == 1) if supplier_count is not None else None,
                "single_bid_or_supplier_proxy": _combined_visible_proxy(bids_count, supplier_count),
                "reconstruction_emergency_flag": reconstruction_emergency_flag,
                "cpv_codes": _extract_cpv_codes(tender),
                "search_text_length": len(searchable_text),
                "mapped_to_waris_oblast": int(oblast in OBLASTS if oblast else False),
                "mapped_to_waris_sector": int(sector in SECTORS),
            }
        )

    return pd.DataFrame(rows)


def _concentration_ratio(series: pd.Series) -> float:
    """Return top buyer/share concentration ratio for a grouping."""
    if series.empty:
        return 0.0

    counts = series.fillna("not_available").astype(str).value_counts()

    if counts.empty:
        return 0.0

    return float(counts.iloc[0] / counts.sum())


def _add_procurement_control_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add standard review-only control fields to procurement feature outputs."""
    if df.empty:
        return df

    out = df.copy()
    out["current_use"] = PROZORRO_PROCUREMENT_CURRENT_USE
    out["prohibited_use"] = PROZORRO_PROCUREMENT_PROHIBITED_USE
    out["production_score_change"] = PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
    out["used_in_waris_scoring"] = False
    out["used_in_monte_carlo"] = False
    out["control_note"] = (
        "Expanded Prozorro procurement feature candidate only. Review artifact; "
        "not an allegation, not an entity-level finding, and not used in WARIS "
        "scoring or Monte Carlo without SME review and model change control."
    )
    out["context_bridge_note"] = (
        "Downstream official-baseline-to-Prozorro, wartime typology, FIU/SFMS, "
        "and operational-control context bridges may reference these features for "
        "review only. This module does not consume official GRP, FIU/SFMS, wartime "
        "typology, analyst-review, false-positive, source-freshness, or run-manifest "
        "artifacts."
    )
    out["operational_control_note"] = (
        "Analyst-review, false-positive, source-freshness, and run-manifest artifacts "
        "are downstream documentation controls only. They do not alter Prozorro feature "
        "calculations or authorize scoring integration."
    )
    return out


def _scale_observed(series: pd.Series) -> pd.Series:
    """Scale observed values only, retaining missing values as missing."""
    observed = pd.to_numeric(series, errors="coerce").dropna()
    result = pd.Series(float("nan"), index=series.index, dtype=float)
    if not observed.empty:
        result.loc[observed.index] = min_max_scale(observed)
    return result


def _add_observation_coverage(out: pd.DataFrame, rows: pd.DataFrame, group: list[str]) -> pd.DataFrame:
    from .config import PROZORRO_MIN_REVIEW_GROUP_TENDERS
    if (rows["tender_id"].isna().any() or rows["tender_id"].astype(str).str.strip().eq("").any()
            or rows["tender_id"].duplicated().any()):
        raise ValueError("Missing or duplicate procurement feature identity")
    coverage = rows.groupby(group, as_index=False).agg(
        unique_tender_count=("tender_id", "nunique"),
        bids_observed_tender_count=("bids_count", "count"),
        supplier_observed_tender_count=("supplier_count", "count"),
        combined_proxy_observed_tender_count=("single_bid_or_supplier_proxy", "count"),
    )
    out = out.merge(coverage, on=group, how="left", validate="one_to_one")
    for field, prefix in [("bids", "bids"), ("supplier", "supplier"), ("combined_proxy", "combined_proxy")]:
        observed = out[f"{prefix}_observed_tender_count"]
        out[f"{field}_unavailable_tender_count"] = out.unique_tender_count - observed
        out[f"{field}_observation_coverage"] = observed / out.unique_tender_count
    out["minimum_review_group_tenders"] = PROZORRO_MIN_REVIEW_GROUP_TENDERS
    small = out.unique_tender_count.lt(PROZORRO_MIN_REVIEW_GROUP_TENDERS)
    partial = out.bids_unavailable_tender_count.gt(0) | out.supplier_unavailable_tender_count.gt(0)
    out["candidate_support_status"] = "visible_fields_sufficient_for_internal_heuristic_only"
    out.loc[partial, "candidate_support_status"] = "partial_observations_candidate_withheld"
    out.loc[small, "candidate_support_status"] = "sparse_group_candidate_withheld"
    out["publication_status"] = "held_individual_release_review_required"
    out["observation_note"] = "Visible arrays only; absence is unknown, not zero; supplier counts cover all visible award records, not winners."
    return out


def build_oblast_features(feature_rows: pd.DataFrame) -> pd.DataFrame:
    """Aggregate procurement features by oblast."""
    ensure_dirs([TABLE_DIR])

    if feature_rows.empty:
        out = pd.DataFrame()
        out.to_csv(OBLAST_FEATURE_TABLE, index=False)
        return out

    mapped = feature_rows[feature_rows["oblast"].isin(OBLASTS)].copy()

    if mapped.empty:
        out = pd.DataFrame()
        out.to_csv(OBLAST_FEATURE_TABLE, index=False)
        return out

    out = (
        mapped.groupby("oblast", as_index=False)
        .agg(
            tender_count=("tender_id", "count"),
            total_expected_value=("value_amount", "sum"),
            mean_expected_value=("value_amount", "mean"),
            single_bid_or_supplier_proxy_rate=("single_bid_or_supplier_proxy", "mean"),
            single_visible_bid_rate=("single_visible_bid_flag", "mean"),
            single_visible_award_supplier_rate=("single_visible_award_supplier_flag", "mean"),
            reconstruction_emergency_tender_count=(
                "reconstruction_emergency_flag",
                "sum",
            ),
            reconstruction_emergency_share=(
                "reconstruction_emergency_flag",
                "mean",
            ),
            unique_buyer_count=("buyer_name", "nunique"),
            procurement_method_count=("procurement_method_type", "nunique"),
        )
    )

    buyer_concentration = (
        mapped.groupby("oblast")["buyer_name"]
        .apply(_concentration_ratio)
        .reset_index(name="top_buyer_tender_share")
    )

    out = out.merge(buyer_concentration, on="oblast", how="left")
    out = _add_observation_coverage(out, mapped, ["oblast"])

    for col in [
        "tender_count",
        "total_expected_value",
        "reconstruction_emergency_tender_count",
        "reconstruction_emergency_share",
        "top_buyer_tender_share",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)

    out["procurement_intensity_score"] = min_max_scale(out["tender_count"])
    out["procurement_value_score"] = min_max_scale(out["total_expected_value"])
    out["single_bid_supplier_score"] = _scale_observed(
        out["single_bid_or_supplier_proxy_rate"].where(
            out.candidate_support_status.eq("visible_fields_sufficient_for_internal_heuristic_only"))
    )
    out["reconstruction_emergency_score"] = min_max_scale(
        out["reconstruction_emergency_tender_count"]
    )
    out["buyer_concentration_score"] = min_max_scale(out["top_buyer_tender_share"])

    out["procurement_review_priority_candidate"] = (
        0.25 * out["procurement_intensity_score"]
        + 0.25 * out["procurement_value_score"]
        + 0.20 * out["single_bid_supplier_score"]
        + 0.20 * out["reconstruction_emergency_score"]
        + 0.10 * out["buyer_concentration_score"]
    ).clip(0, 100)

    unsupported = out.candidate_support_status.ne("visible_fields_sufficient_for_internal_heuristic_only")
    out.loc[unsupported, "procurement_review_priority_candidate"] = float("nan")
    out = _add_procurement_control_fields(out)

    out = out.sort_values(
        "procurement_review_priority_candidate",
        ascending=False,
    ).reset_index(drop=True)

    out.to_csv(OBLAST_FEATURE_TABLE, index=False)
    return out


def build_oblast_sector_features(feature_rows: pd.DataFrame) -> pd.DataFrame:
    """Aggregate procurement features by oblast and WARIS sector."""
    ensure_dirs([TABLE_DIR])

    if feature_rows.empty:
        out = pd.DataFrame()
        out.to_csv(OBLAST_SECTOR_FEATURE_TABLE, index=False)
        return out

    mapped = feature_rows[
        feature_rows["oblast"].isin(OBLASTS)
        & feature_rows["sector"].isin(SECTORS)
    ].copy()

    if mapped.empty:
        out = pd.DataFrame()
        out.to_csv(OBLAST_SECTOR_FEATURE_TABLE, index=False)
        return out

    out = (
        mapped.groupby(["oblast", "sector"], as_index=False)
        .agg(
            tender_count=("tender_id", "count"),
            total_expected_value=("value_amount", "sum"),
            mean_expected_value=("value_amount", "mean"),
            single_bid_or_supplier_proxy_rate=("single_bid_or_supplier_proxy", "mean"),
            single_visible_bid_rate=("single_visible_bid_flag", "mean"),
            single_visible_award_supplier_rate=("single_visible_award_supplier_flag", "mean"),
            reconstruction_emergency_tender_count=(
                "reconstruction_emergency_flag",
                "sum",
            ),
            reconstruction_emergency_share=(
                "reconstruction_emergency_flag",
                "mean",
            ),
            unique_buyer_count=("buyer_name", "nunique"),
            procurement_method_count=("procurement_method_type", "nunique"),
        )
    )

    buyer_concentration = (
        mapped.groupby(["oblast", "sector"])["buyer_name"]
        .apply(_concentration_ratio)
        .reset_index(name="top_buyer_tender_share")
    )

    out = out.merge(buyer_concentration, on=["oblast", "sector"], how="left")
    out = _add_observation_coverage(out, mapped, ["oblast", "sector"])

    for col in [
        "tender_count",
        "total_expected_value",
        "reconstruction_emergency_tender_count",
        "reconstruction_emergency_share",
        "top_buyer_tender_share",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)

    out["procurement_intensity_score"] = min_max_scale(out["tender_count"])
    out["procurement_value_score"] = min_max_scale(out["total_expected_value"])
    out["single_bid_supplier_score"] = _scale_observed(
        out["single_bid_or_supplier_proxy_rate"].where(
            out.candidate_support_status.eq("visible_fields_sufficient_for_internal_heuristic_only"))
    )
    out["reconstruction_emergency_score"] = min_max_scale(
        out["reconstruction_emergency_tender_count"]
    )
    out["buyer_concentration_score"] = min_max_scale(out["top_buyer_tender_share"])

    out["procurement_review_priority_candidate"] = (
        0.25 * out["procurement_intensity_score"]
        + 0.25 * out["procurement_value_score"]
        + 0.20 * out["single_bid_supplier_score"]
        + 0.20 * out["reconstruction_emergency_score"]
        + 0.10 * out["buyer_concentration_score"]
    ).clip(0, 100)

    unsupported = out.candidate_support_status.ne("visible_fields_sufficient_for_internal_heuristic_only")
    out.loc[unsupported, "procurement_review_priority_candidate"] = float("nan")
    out = _add_procurement_control_fields(out)

    out = out.sort_values(
        "procurement_review_priority_candidate",
        ascending=False,
    ).reset_index(drop=True)

    out.to_csv(OBLAST_SECTOR_FEATURE_TABLE, index=False)
    return out


def build_scoring_candidate_table(oblast_sector_features: pd.DataFrame) -> pd.DataFrame:
    """Build scoring-candidate table without altering WARIS scoring."""
    ensure_dirs([TABLE_DIR])

    if oblast_sector_features.empty:
        out = pd.DataFrame()
        out.to_csv(SCORING_CANDIDATE_TABLE, index=False)
        return out

    candidate_cols = [
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
        "production_score_change",
        "used_in_waris_scoring",
        "used_in_monte_carlo",
        "control_note",
        "context_bridge_note",
        "operational_control_note",
    ]

    candidate_cols += ["unique_tender_count", "bids_observed_tender_count", "bids_unavailable_tender_count",
                       "supplier_observed_tender_count", "supplier_unavailable_tender_count",
                       "combined_proxy_observed_tender_count", "combined_proxy_unavailable_tender_count",
                       "candidate_support_status", "publication_status", "observation_note"]
    for col in candidate_cols:
        if col not in oblast_sector_features.columns:
            if col in {"used_in_waris_scoring", "used_in_monte_carlo"}:
                oblast_sector_features[col] = False
            elif col == "current_use":
                oblast_sector_features[col] = PROZORRO_PROCUREMENT_CURRENT_USE
            elif col == "prohibited_use":
                oblast_sector_features[col] = PROZORRO_PROCUREMENT_PROHIBITED_USE
            elif col == "production_score_change":
                oblast_sector_features[col] = PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
            elif col == "control_note":
                oblast_sector_features[col] = (
                    "Expanded Prozorro procurement feature candidate only. "
                    "Review artifact; not an allegation or scoring input."
                )
            elif col == "context_bridge_note":
                oblast_sector_features[col] = (
                    "Downstream bridge modules may reference this feature for "
                    "review only."
                )
            elif col == "operational_control_note":
                oblast_sector_features[col] = (
                    "Operational-control artifacts are downstream documentation "
                    "controls only and do not authorize Prozorro scoring use."
                )
            else:
                oblast_sector_features[col] = pd.NA

    out = oblast_sector_features[candidate_cols].copy()
    from .config import PROZORRO_MIN_REVIEW_GROUP_TENDERS
    count = pd.to_numeric(out.unique_tender_count, errors="coerce")
    bid_count = pd.to_numeric(out.bids_observed_tender_count, errors="coerce")
    supplier_count = pd.to_numeric(out.supplier_observed_tender_count, errors="coerce")
    supported = (out.candidate_support_status.eq("visible_fields_sufficient_for_internal_heuristic_only")
                 & count.ge(PROZORRO_MIN_REVIEW_GROUP_TENDERS) & bid_count.eq(count) & supplier_count.eq(count))
    supported = supported.fillna(False)
    out.loc[~supported, "procurement_review_priority_candidate"] = float("nan")
    out["candidate_support_status"] = out.candidate_support_status.fillna("missing_observation_metadata_candidate_withheld")
    out["publication_status"] = "held_individual_release_review_required"

    out["candidate_target_field"] = "procurement_awards_proxy"
    out["recommended_current_action"] = (
        "review_only_compare_against_existing_procurement_layer"
    )
    out["required_before_scoring"] = (
        "Validate mapping, expand historical coverage, confirm bid/supplier fields, "
        "review with procurement/AML SMEs, and approve model change control."
    )
    out["production_score_change"] = PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE
    out["current_use"] = PROZORRO_PROCUREMENT_CURRENT_USE
    out["prohibited_use"] = PROZORRO_PROCUREMENT_PROHIBITED_USE
    out["used_in_waris_scoring"] = False
    out["used_in_monte_carlo"] = False

    out.to_csv(SCORING_CANDIDATE_TABLE, index=False)
    return out


def build_feature_summary(
    feature_rows: pd.DataFrame,
    oblast_features: pd.DataFrame,
    oblast_sector_features: pd.DataFrame,
    scoring_candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Build concise procurement feature summary."""
    ensure_dirs([TABLE_DIR])

    mapped_count = 0
    unmapped_count = 0

    if not feature_rows.empty and "oblast" in feature_rows.columns:
        mapped_count = int(feature_rows["oblast"].isin(OBLASTS).sum())
        unmapped_count = int((~feature_rows["oblast"].isin(OBLASTS)).sum())

    top_oblast = "not_available"
    top_oblast_score = "not_available"

    if not oblast_features.empty and oblast_features.procurement_review_priority_candidate.notna().any():
        top = oblast_features.loc[oblast_features.procurement_review_priority_candidate.notna()].iloc[0]
        top_oblast = str(top.get("oblast", "not_available"))
        top_oblast_score = str(
            top.get("procurement_review_priority_candidate", "not_available")
        )

    top_oblast_sector = "not_available"
    top_oblast_sector_score = "not_available"

    if not oblast_sector_features.empty and oblast_sector_features.procurement_review_priority_candidate.notna().any():
        top = oblast_sector_features.loc[oblast_sector_features.procurement_review_priority_candidate.notna()].iloc[0]
        top_oblast_sector = (
            f"{top.get('oblast', 'not_available')} - "
            f"{top.get('sector', 'not_available')}"
        )
        top_oblast_sector_score = str(
            top.get("procurement_review_priority_candidate", "not_available")
        )

    rows = [
        {
            "summary_area": "Raw tender feature rows",
            "status": "created" if not feature_rows.empty else "missing_or_empty",
            "value": len(feature_rows),
            "recommended_next_action": (
                "Review raw tender coverage, date range, and mapping quality."
            ),
        },
        {
            "summary_area": "Oblast mapping",
            "status": "partial_mapping_expected",
            "value": f"mapped={mapped_count}; unmapped={unmapped_count}",
            "recommended_next_action": (
                "Improve buyer/address/region parsing before scoring use."
            ),
        },
        {
            "summary_area": "Oblast features",
            "status": "created" if not oblast_features.empty else "missing_or_empty",
            "value": len(oblast_features),
            "recommended_next_action": (
                "Review top oblast procurement review-priority candidates."
            ),
        },
        {
            "summary_area": "Oblast-sector features",
            "status": (
                "created" if not oblast_sector_features.empty else "missing_or_empty"
            ),
            "value": len(oblast_sector_features),
            "recommended_next_action": (
                "Compare sector/oblast procurement candidates against existing WARIS "
                "procurement_awards_proxy values."
            ),
        },
        {
            "summary_area": "Top oblast candidate",
            "status": "review_only",
            "value": f"{top_oblast} ({top_oblast_score})",
            "recommended_next_action": "Do not treat as allegation; use for review only.",
        },
        {
            "summary_area": "Top oblast-sector candidate",
            "status": "review_only",
            "value": f"{top_oblast_sector} ({top_oblast_sector_score})",
            "recommended_next_action": "Do not treat as allegation; use for review only.",
        },
        {
            "summary_area": "Scoring candidate table",
            "status": "created" if not scoring_candidates.empty else "missing_or_empty",
            "value": len(scoring_candidates),
            "recommended_next_action": (
                "Keep production_score_change=none until SME review and change control."
            ),
        },
        {
            "summary_area": "Current use control",
            "status": "control_active",
            "value": PROZORRO_PROCUREMENT_CURRENT_USE,
            "recommended_next_action": (
                "Keep expanded procurement features as review artifacts only."
            ),
        },
        {
            "summary_area": "Prohibited use control",
            "status": "control_active",
            "value": PROZORRO_PROCUREMENT_PROHIBITED_USE,
            "recommended_next_action": (
                "Block direct scoring integration until validation and change control."
            ),
        },
        {
            "summary_area": "Production score change control",
            "status": "control_active",
            "value": PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE,
            "recommended_next_action": (
                "Maintain production_score_change=none unless a governed "
                "scoring-integration change is approved."
            ),
        },
        {
            "summary_area": "Scoring and Monte Carlo control",
            "status": "control_active",
            "value": "used_in_waris_scoring=False; used_in_monte_carlo=False",
            "recommended_next_action": (
                "Confirm generated feature tables remain review-only and out of "
                "risk-layer, composite-score, risk-band, and Monte Carlo calculations."
            ),
        },
        {
            "summary_area": "FIU/SFMS context separation",
            "status": "source_separation_active",
            "value": FIU_CONTEXT_CURRENT_USE,
            "recommended_next_action": (
                "Keep official FIU/SFMS context in downstream source-support and "
                "governance artifacts only; do not merge it into Prozorro feature "
                "calculations."
            ),
        },
        {
            "summary_area": "Wartime AML typology context separation",
            "status": "source_separation_active",
            "value": WARTIME_AML_TYPOLOGY_CURRENT_USE,
            "recommended_next_action": (
                "Keep wartime AML/CFT typology artifacts as literature-support "
                "references only; do not merge them into Prozorro feature calculations."
            ),
        },
        {
            "summary_area": "Analyst review workflow separation",
            "status": "operational_control_separation_active",
            "value": (
                f"{ANALYST_REVIEW_CURRENT_USE}; "
                f"production_score_change={ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE}"
            ),
            "recommended_next_action": (
                "Keep analyst-review workflow artifacts downstream from Prozorro feature "
                "generation. They document human review only and do not alter feature "
                "calculations."
            ),
        },
        {
            "summary_area": "False-positive control separation",
            "status": "operational_control_separation_active",
            "value": (
                f"{FALSE_POSITIVE_CONTROLS_CURRENT_USE}; "
                f"production_score_change={FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE}"
            ),
            "recommended_next_action": (
                "Use false-positive controls during downstream review; do not use them "
                "to automatically clear or escalate Prozorro feature candidates."
            ),
        },
        {
            "summary_area": "Source freshness separation",
            "status": "operational_control_separation_active",
            "value": (
                f"{SOURCE_FRESHNESS_CURRENT_USE}; "
                f"production_score_change={SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE}"
            ),
            "recommended_next_action": (
                "Use source-freshness outputs for refresh planning only. Do not treat "
                "freshness as scoring approval for Prozorro procurement features."
            ),
        },
        {
            "summary_area": "Run manifest separation",
            "status": "operational_control_separation_active",
            "value": (
                f"{RUN_MANIFEST_CURRENT_USE}; "
                f"production_score_change={RUN_MANIFEST_PRODUCTION_SCORE_CHANGE}"
            ),
            "recommended_next_action": (
                "Use run-manifest outputs for reproducibility and release traceability "
                "only. Do not treat the manifest as validation or scoring approval."
            ),
        },
    ]

    out = pd.DataFrame(rows)
    out.to_csv(FEATURE_SUMMARY_TABLE, index=False)
    return out


def build_prozorro_procurement_feature_artifacts(
    fetch_live: bool = True,
) -> dict[str, pd.DataFrame]:
    """Build all expanded Prozorro procurement feature artifacts."""
    ensure_dirs([RAW_DIR, TABLE_DIR])

    config = _runtime_config()

    if fetch_live:
        tender_feed = fetch_recent_prozorro_tenders(config=config)
        tender_details = fetch_tender_details(tender_feed, config=config)
    else:
        if RAW_TENDER_DETAIL_TABLE.exists():
            tender_details = pd.read_csv(RAW_TENDER_DETAIL_TABLE)
        elif RAW_TENDER_LIST_TABLE.exists():
            tender_details = pd.read_csv(RAW_TENDER_LIST_TABLE)
        else:
            tender_details = pd.DataFrame()

    feature_rows = _prepare_tender_feature_rows(tender_details)
    feature_rows.to_csv(RAW_FEATURE_ROWS_TABLE, index=False)

    oblast_features = build_oblast_features(feature_rows)
    oblast_sector_features = build_oblast_sector_features(feature_rows)
    scoring_candidates = build_scoring_candidate_table(oblast_sector_features)
    summary = build_feature_summary(
        feature_rows=feature_rows,
        oblast_features=oblast_features,
        oblast_sector_features=oblast_sector_features,
        scoring_candidates=scoring_candidates,
    )

    return {
        "tender_feed": tender_feed if fetch_live else pd.DataFrame(),
        "tender_details": tender_details,
        "feature_rows": feature_rows,
        "oblast_features": oblast_features,
        "oblast_sector_features": oblast_sector_features,
        "scoring_candidates": scoring_candidates,
        "summary": summary,
    }


def main() -> None:
    """CLI entry point."""
    fetch_live = os.getenv("PROZORRO_FETCH_LIVE", "1").strip().lower() not in {
        "0",
        "false",
        "no",
    }

    artifacts = build_prozorro_procurement_feature_artifacts(fetch_live=fetch_live)

    print("\nProzorro procurement feature artifacts created.")
    print(f"- Fetch live: {fetch_live}")
    print(f"- Tender detail rows: {len(artifacts['tender_details'])}")
    print(f"- Feature rows: {len(artifacts['feature_rows'])}")
    print(f"- Oblast feature rows: {len(artifacts['oblast_features'])}")
    print(f"- Oblast-sector feature rows: {len(artifacts['oblast_sector_features'])}")
    print(f"- Scoring candidate rows: {len(artifacts['scoring_candidates'])}")
    print(f"- Summary rows: {len(artifacts['summary'])}")

    print(f"- Raw tender list: {RAW_TENDER_LIST_TABLE}")
    print(f"- Raw tender details: {RAW_TENDER_DETAIL_TABLE}")
    print(f"- Raw feature rows: {RAW_FEATURE_ROWS_TABLE}")
    print(f"- Oblast features: {OBLAST_FEATURE_TABLE}")
    print(f"- Oblast-sector features: {OBLAST_SECTOR_FEATURE_TABLE}")
    print(f"- Scoring candidates: {SCORING_CANDIDATE_TABLE}")
    print(f"- Feature summary: {FEATURE_SUMMARY_TABLE}")

    print(
        "\nImportant: These are procurement review artifacts and candidate features. "
        f"current_use={PROZORRO_PROCUREMENT_CURRENT_USE}; "
        f"prohibited_use={PROZORRO_PROCUREMENT_PROHIBITED_USE}; "
        f"production_score_change={PROZORRO_PROCUREMENT_PRODUCTION_SCORE_CHANGE}. "
        "They do not alter WARIS risk layers, composite scores, risk bands, "
        "review rationales, or Monte Carlo simulations unless a future governed "
        "scoring-integration change is explicitly approved. FIU/SFMS, wartime "
        "typology, analyst-review, false-positive, source-freshness, and run-manifest "
        "context remain separate source-support or operational-control layers."
    )


if __name__ == "__main__":
    main()
