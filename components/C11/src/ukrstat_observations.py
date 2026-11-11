"""Ukrstat observation discovery and official baseline preparation for WARIS.

This module is intentionally conservative.

Goal:
- Move WARIS from metadata-only official indicator discovery toward official
  Ukrstat observation integration.
- Start with DF_REGIONAL_ACCOUNTS because it is currently the cleanest candidate
  for an official regional baseline layer.

Current stage:
- Discover DF_REGIONAL_ACCOUNTS.
- Inspect available SDMX structure metadata.
- Save candidate dimensions, codelists, metadata clues, registry references,
  DSD dimension candidates, dimension code candidates, observation-query candidates with stricter oblast-level REGION filtering,
  official SDMX v3 observation/availability probes, official data endpoint route discovery probes,
  parsed observation-response artifacts, raw response path inventory, observation-matrix probes, availability-discovery probes, availability value candidates, availability-derived observation probes, confirmed-series probes, confirmed oblast baseline candidates, all-oblast baseline probes, endpoint probes, DSD-specific endpoint probes, and query-plan artifacts.
- Fetch and save the best available DSD_REGIONAL_ACCOUNTS payload for dimension
  parsing.
- Fetch and save a codelist-rich DSD_REGIONAL_ACCOUNTS payload for code
  candidate parsing.
- Create an oblast-level placeholder baseline table.

This version does not yet blend Ukrstat observations into scoring.

Current source-separation posture:
- Ukrstat GRP observations are official baseline benchmark candidates only.
- Expanded Prozorro features remain review-only procurement context.
- Wartime AML/CFT typology artifacts remain literature-support references only.
- Official FIU/SFMS artifacts remain national source-support context only.
- Analyst-review, false-positive, source-freshness, and run-manifest artifacts
  remain downstream operational-control/documentation artifacts only.
- Official baseline, Prozorro, typology, FIU/SFMS, and operational-control
  bridge/review artifacts are created downstream by merge-plan, merge-review,
  validation, memo, source-confidence, and governance modules. This module does
  not consume those downstream artifacts and does not change WARIS scoring.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import requests

from .config import RAW_DIR, TABLE_DIR
from .data_collection import OBLASTS
from .utils import ensure_dirs


UKRSTAT_METADATA_JSON = RAW_DIR / "ukrstat_sdmx_dataflows_raw.json"
UKRSTAT_METADATA_CSV = RAW_DIR / "ukrstat_sdmx_dataflows_raw.csv"

UKRSTAT_REGIONAL_ACCOUNTS_DISCOVERY_RAW = (
    RAW_DIR / "ukrstat_regional_accounts_discovery_raw.csv"
)

UKRSTAT_REGIONAL_ACCOUNTS_STRUCTURE_RAW = (
    RAW_DIR / "ukrstat_regional_accounts_structure_raw.json"
)

UKRSTAT_REGIONAL_ACCOUNTS_STRUCTURE_PATHS_RAW = (
    RAW_DIR / "ukrstat_regional_accounts_structure_paths_raw.csv"
)

UKRSTAT_REGIONAL_ACCOUNTS_STRUCTURE_ATTEMPTS_RAW = (
    RAW_DIR / "ukrstat_regional_accounts_structure_attempts.csv"
)

UKRSTAT_DSD_STRUCTURE_RAW = (
    RAW_DIR / "ukrstat_dsd_regional_accounts_6_raw.json"
)

UKRSTAT_DSD_STRUCTURE_PATHS_RAW = (
    RAW_DIR / "ukrstat_dsd_regional_accounts_6_paths_raw.csv"
)

UKRSTAT_DSD_REFERENCES_STRUCTURE_RAW = (
    RAW_DIR / "ukrstat_dsd_regional_accounts_6_references_raw.json"
)

UKRSTAT_DSD_REFERENCES_STRUCTURE_PATHS_RAW = (
    RAW_DIR / "ukrstat_dsd_regional_accounts_6_references_paths_raw.csv"
)

UKRSTAT_REGIONAL_ACCOUNTS_DIMENSIONS_TABLE = (
    TABLE_DIR / "ukrstat_regional_accounts_dimensions.csv"
)

UKRSTAT_REGIONAL_ACCOUNTS_CODELISTS_TABLE = (
    TABLE_DIR / "ukrstat_regional_accounts_codelists.csv"
)

UKRSTAT_REGIONAL_ACCOUNTS_METADATA_CLUES_TABLE = (
    TABLE_DIR / "ukrstat_regional_accounts_metadata_clues.csv"
)

UKRSTAT_REGISTRY_REFERENCES_TABLE = (
    TABLE_DIR / "ukrstat_registry_references.csv"
)

UKRSTAT_DSD_DIMENSION_CANDIDATES_TABLE = (
    TABLE_DIR / "ukrstat_dsd_dimension_candidates.csv"
)

UKRSTAT_DIMENSION_CODE_CANDIDATES_TABLE = (
    TABLE_DIR / "ukrstat_dimension_code_candidates.csv"
)

UKRSTAT_OBSERVATION_QUERY_CANDIDATES_TABLE = (
    TABLE_DIR / "ukrstat_observation_query_candidates.csv"
)

UKRSTAT_OBSERVATION_PROBE_TABLE = (
    TABLE_DIR / "ukrstat_observation_probe_results.csv"
)

UKRSTAT_OBSERVATION_PROBE_RAW = (
    RAW_DIR / "ukrstat_observation_probe_response_raw.txt"
)

UKRSTAT_OBSERVATION_DATA_RESPONSE_RAW = (
    RAW_DIR / "ukrstat_observation_data_response_raw.json"
)

UKRSTAT_OBSERVATION_PARSED_TABLE = (
    TABLE_DIR / "ukrstat_observation_probe_parsed.csv"
)

UKRSTAT_OBSERVATION_RESPONSE_PATHS_TABLE = (
    TABLE_DIR / "ukrstat_observation_response_paths.csv"
)

UKRSTAT_OBSERVATION_MATRIX_PROBE_TABLE = (
    TABLE_DIR / "ukrstat_observation_matrix_probe_results.csv"
)

UKRSTAT_OBSERVATION_MATRIX_SUCCESS_RAW = (
    RAW_DIR / "ukrstat_observation_matrix_success_raw.json"
)

UKRSTAT_CONFIRMED_SERIES_PROBE_TABLE = (
    TABLE_DIR / "ukrstat_confirmed_series_probe_results.csv"
)

UKRSTAT_CONFIRMED_SERIES_RAW = (
    RAW_DIR / "ukrstat_confirmed_series_response_raw.json"
)

UKRSTAT_CONFIRMED_SERIES_PARSED_TABLE = (
    TABLE_DIR / "ukrstat_confirmed_series_parsed.csv"
)

UKRSTAT_CONFIRMED_OBLAST_BASELINE_CANDIDATES_TABLE = (
    TABLE_DIR / "ukrstat_confirmed_oblast_baseline_candidates.csv"
)

UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE = (
    TABLE_DIR / "ukrstat_oblast_baseline_probe_results.csv"
)

UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE = (
    TABLE_DIR / "ukrstat_oblast_baseline_candidates.csv"
)

UKRSTAT_OBLAST_BASELINE_SUCCESS_DIR = (
    RAW_DIR / "ukrstat_oblast_baseline_success_responses"
)

UKRSTAT_AVAILABILITY_DISCOVERY_TABLE = (
    TABLE_DIR / "ukrstat_availability_discovery_results.csv"
)

UKRSTAT_AVAILABILITY_DISCOVERY_RAW = (
    RAW_DIR / "ukrstat_availability_discovery_response_raw.json"
)

UKRSTAT_AVAILABILITY_VALUE_CANDIDATES_TABLE = (
    TABLE_DIR / "ukrstat_availability_value_candidates.csv"
)

UKRSTAT_DATA_ENDPOINT_DISCOVERY_TABLE = (
    TABLE_DIR / "ukrstat_data_endpoint_discovery_results.csv"
)

UKRSTAT_DATA_ENDPOINT_DISCOVERY_RAW = (
    RAW_DIR / "ukrstat_data_endpoint_discovery_response_raw.txt"
)

UKRSTAT_ENDPOINT_PROBE_TABLE = (
    TABLE_DIR / "ukrstat_endpoint_probe_results.csv"
)

UKRSTAT_DSD_ENDPOINT_PROBE_TABLE = (
    TABLE_DIR / "ukrstat_dsd_endpoint_probe_results.csv"
)

UKRSTAT_OBSERVATION_QUERY_PLAN_TABLE = (
    TABLE_DIR / "ukrstat_observation_query_plan.csv"
)

UKRSTAT_OBLAST_BASELINE_TABLE = TABLE_DIR / "ukrstat_oblast_baseline.csv"

OFFICIAL_BASELINE_CURRENT_USE = "controlled_benchmark_integration_only"
OFFICIAL_BASELINE_PROHIBITED_USE = "risk_layer_calculation_or_composite_scoring"
OFFICIAL_BASELINE_PRODUCTION_SCORE_CHANGE = "none"
OFFICIAL_BASELINE_USED_IN_SCORING = False
OFFICIAL_BASELINE_USED_IN_MONTE_CARLO = False

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

SOURCE_SEPARATION_NOTE = (
    "Ukrstat official baseline artifacts are benchmark candidates only. "
    "Expanded Prozorro, wartime AML/CFT typology, official FIU/SFMS context, "
    "analyst-review, false-positive, source-freshness, and run-manifest layers "
    "remain separate downstream source-support or operational-control artifacts "
    "and are not consumed by this module."
)

DATAFLOW_ID = "DF_REGIONAL_ACCOUNTS"
DSD_ID = "DSD_REGIONAL_ACCOUNTS"

UKRSTAT_SDMX_STRUCTURE_BASE = (
    "https://stat.gov.ua/sdmx/workspaces/default:integration/"
    "registry/sdmx/3.0/structure"
)


def _safe_get_json(url: str, params: dict | None = None, timeout: int = 45) -> Any | None:
    """Fetch JSON safely."""
    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={
                "User-Agent": "WARIS research prototype",
                "Accept": (
                    "application/vnd.sdmx.structure+json;version=2.0.0, "
                    "application/json"
                ),
            },
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"[WARN] Ukrstat fetch failed: {url} | {exc}")
        return None


def _write_json(path, payload: Any) -> None:
    """Write JSON payload to disk."""
    ensure_dirs([path.parent])
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _add_official_baseline_control_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Attach standard no-scoring official-baseline control fields."""
    if df is None or df.empty:
        return df

    out = df.copy()
    out["approved_current_use"] = OFFICIAL_BASELINE_CURRENT_USE
    out["prohibited_current_use"] = OFFICIAL_BASELINE_PROHIBITED_USE
    out["production_score_change"] = OFFICIAL_BASELINE_PRODUCTION_SCORE_CHANGE
    out["official_baseline_used_in_scoring"] = OFFICIAL_BASELINE_USED_IN_SCORING
    out["official_baseline_used_in_monte_carlo"] = OFFICIAL_BASELINE_USED_IN_MONTE_CARLO
    out["source_separation_note"] = SOURCE_SEPARATION_NOTE
    out["operational_control_separation_note"] = (
        "Analyst-review, false-positive, source-freshness, and run-manifest "
        "artifacts are downstream operational controls only. This Ukrstat module "
        "does not consume those artifacts and they do not authorize official "
        "baseline scoring integration."
    )
    out["analyst_review_current_use"] = ANALYST_REVIEW_CURRENT_USE
    out["analyst_review_production_score_change"] = ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE
    out["false_positive_controls_current_use"] = FALSE_POSITIVE_CONTROLS_CURRENT_USE
    out["false_positive_controls_production_score_change"] = (
        FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE
    )
    out["source_freshness_current_use"] = SOURCE_FRESHNESS_CURRENT_USE
    out["source_freshness_production_score_change"] = (
        SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE
    )
    out["run_manifest_current_use"] = RUN_MANIFEST_CURRENT_USE
    out["run_manifest_production_score_change"] = RUN_MANIFEST_PRODUCTION_SCORE_CHANGE
    out["operational_controls_used_in_official_baseline_scoring"] = False
    out["control_note"] = (
        "Official Ukrstat regional-account observation candidate only. Approved for "
        "controlled benchmark integration/review only; not used in WARIS risk-layer "
        "calculation, composite scoring, risk-band assignment, review-rationale "
        "generation, or Monte Carlo score simulation. Operational-control artifacts "
        "remain downstream documentation and human-review support only."
    )
    return out


def _walk_json_for_dataflow_records(obj: Any) -> list[dict]:
    """Recursively walk Ukrstat SDMX metadata and extract dataflow-like records."""
    rows: list[dict] = []

    def walk(value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            record_id = value.get("id")
            name = value.get("name", value.get("names", ""))

            if record_id is not None and name:
                rows.append(
                    {
                        "id": str(record_id),
                        "name": str(name)[:500],
                        "json_path": path,
                    }
                )

            for key, child in value.items():
                walk(child, f"{path}.{key}" if path else str(key))

        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(obj)
    return rows


def _flatten_json_paths(obj: Any) -> pd.DataFrame:
    """Flatten JSON into path/value rows for structure inspection."""
    rows: list[dict] = []

    def walk(value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]"
                walk(child, child_path)
        else:
            rows.append(
                {
                    "json_path": path,
                    "value": "" if value is None else str(value)[:500],
                }
            )

    walk(obj)
    return pd.DataFrame(rows)


def _extract_name(value: Any) -> str:
    """Extract readable SDMX name structures into a string."""
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        for key in ["en", "uk", "ua"]:
            candidate = value.get(key)

            if isinstance(candidate, str):
                return candidate

            if isinstance(candidate, dict) and "value" in candidate:
                return str(candidate.get("value", ""))

        if "value" in value:
            return str(value.get("value", ""))

        return json.dumps(value, ensure_ascii=False)[:300]

    return str(value)


def _recursive_find_records(obj: Any, wanted_keys: set[str]) -> list[dict]:
    """Find dict records that contain at least one wanted key."""
    rows: list[dict] = []

    def walk(value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            if any(key in value for key in wanted_keys):
                row = {
                    "json_path": path,
                    "id": value.get("id", ""),
                    "urn": value.get("urn", ""),
                    "name": _extract_name(value.get("name", value.get("names", ""))),
                    "description": _extract_name(
                        value.get("description", value.get("descriptions", ""))
                    ),
                    "agencyID": value.get("agencyID", ""),
                    "version": value.get("version", ""),
                    "local_representation": str(value.get("localRepresentation", ""))[:500],
                    "concept_identity": str(value.get("conceptIdentity", ""))[:500],
                    "codelist": str(value.get("codelist", ""))[:500],
                    "raw_keys": "; ".join(sorted(map(str, value.keys()))),
                }
                rows.append(row)

            for key, child in value.items():
                walk(child, f"{path}.{key}" if path else str(key))

        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(obj)
    return rows


def load_ukrstat_dataflow_metadata() -> pd.DataFrame:
    """Load available Ukrstat SDMX dataflow metadata from prior live_data run."""
    ensure_dirs([RAW_DIR, TABLE_DIR])

    if UKRSTAT_METADATA_CSV.exists():
        df = pd.read_csv(UKRSTAT_METADATA_CSV)

        if not df.empty:
            return df.drop_duplicates().reset_index(drop=True)

    if UKRSTAT_METADATA_JSON.exists():
        payload = json.loads(UKRSTAT_METADATA_JSON.read_text(encoding="utf-8"))
        rows = _walk_json_for_dataflow_records(payload)
        df = pd.DataFrame(rows).drop_duplicates()

        if not df.empty:
            df.to_csv(UKRSTAT_METADATA_CSV, index=False)

        return df.reset_index(drop=True)

    return pd.DataFrame(columns=["id", "name"])


def discover_regional_accounts_dataflows(
    metadata: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Find Ukrstat dataflows related to regional accounts."""
    ensure_dirs([RAW_DIR, TABLE_DIR])

    if metadata is None:
        metadata = load_ukrstat_dataflow_metadata()

    if metadata.empty:
        discovery = pd.DataFrame(
            columns=[
                "id",
                "name",
                "candidate_role",
                "implementation_status",
                "notes",
            ]
        )
        discovery.to_csv(UKRSTAT_REGIONAL_ACCOUNTS_DISCOVERY_RAW, index=False)
        return discovery

    working = metadata.copy()

    for col in ["id", "name"]:
        if col not in working.columns:
            working[col] = ""

    working["id"] = working["id"].fillna("").astype(str)
    working["name"] = working["name"].fillna("").astype(str)

    mask = (
        working["id"].str.contains("REGIONAL", case=False, na=False)
        | working["name"].str.contains("regional accounts", case=False, na=False)
        | working["name"].str.contains("regional", case=False, na=False)
        | working["name"].str.contains("oblast", case=False, na=False)
    )

    discovery = working.loc[mask, ["id", "name"]].drop_duplicates().copy()

    if discovery.empty:
        discovery = pd.DataFrame(
            [
                {
                    "id": DATAFLOW_ID,
                    "name": "Regional accounts",
                    "candidate_role": "official_regional_baseline",
                    "implementation_status": "metadata_not_found_in_current_cache",
                    "notes": (
                        "Expected candidate from official indicator catalog, but not "
                        "found in current Ukrstat metadata cache."
                    ),
                }
            ]
        )
    else:
        discovery["candidate_role"] = discovery["id"].apply(
            lambda value: (
                "primary_official_regional_baseline"
                if value == DATAFLOW_ID
                else "secondary_regional_candidate"
            )
        )
        discovery["implementation_status"] = "metadata_discovered"
        discovery["notes"] = (
            "Candidate dataflow metadata discovered. Next step is dimension inspection "
            "and SDMX observation query mapping."
        )

    discovery = discovery.sort_values(
        ["candidate_role", "id"],
        ascending=[True, True],
    ).reset_index(drop=True)

    discovery.to_csv(UKRSTAT_REGIONAL_ACCOUNTS_DISCOVERY_RAW, index=False)

    return discovery


def fetch_regional_accounts_structure() -> tuple[Any | None, pd.DataFrame]:
    """Attempt to fetch DF_REGIONAL_ACCOUNTS structure metadata."""
    ensure_dirs([RAW_DIR, TABLE_DIR])

    candidate_urls = [
        (
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/dataflow/*/{DATAFLOW_ID}/*"
            "?detail=allstubs&references=all"
        ),
        (
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/dataflow/*/{DATAFLOW_ID}/*"
            "?detail=full&references=all"
        ),
        (
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/dataflow/*/{DATAFLOW_ID}/*"
            "?references=all"
        ),
        (
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/*/*/*"
            "?detail=full&references=all"
        ),
        (
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/*/*/*/*"
            "?detail=allstubs&references=all"
        ),
    ]

    attempts = []

    for url in candidate_urls:
        payload = _safe_get_json(url)

        attempts.append(
            {
                "url": url,
                "status": "success" if payload is not None else "failed",
                "note": (
                    "Payload fetched"
                    if payload is not None
                    else "No JSON payload returned"
                ),
            }
        )

        if payload is not None:
            _write_json(UKRSTAT_REGIONAL_ACCOUNTS_STRUCTURE_RAW, payload)

            flattened = _flatten_json_paths(payload)
            if not flattened.empty:
                flattened.to_csv(
                    UKRSTAT_REGIONAL_ACCOUNTS_STRUCTURE_PATHS_RAW,
                    index=False,
                )

            attempts_df = pd.DataFrame(attempts)
            attempts_df.to_csv(
                UKRSTAT_REGIONAL_ACCOUNTS_STRUCTURE_ATTEMPTS_RAW,
                index=False,
            )

            return payload, attempts_df

    attempts_df = pd.DataFrame(attempts)
    attempts_df.to_csv(
        UKRSTAT_REGIONAL_ACCOUNTS_STRUCTURE_ATTEMPTS_RAW,
        index=False,
    )

    return None, attempts_df


def build_structure_dimension_tables(payload: Any | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build dimension and codelist candidate tables from structure metadata."""
    ensure_dirs([TABLE_DIR])

    if payload is None:
        dimensions = pd.DataFrame(
            [
                {
                    "dimension_id": "",
                    "dimension_name": "",
                    "json_path": "",
                    "representation_hint": "",
                    "implementation_status": "structure_payload_unavailable",
                    "notes": (
                        "Could not fetch structure payload. Review "
                        "ukrstat_regional_accounts_structure_attempts.csv."
                    ),
                }
            ]
        )

        codelists = pd.DataFrame(
            [
                {
                    "codelist_id": "",
                    "codelist_name": "",
                    "code_id": "",
                    "code_name": "",
                    "json_path": "",
                    "implementation_status": "structure_payload_unavailable",
                }
            ]
        )

        dimensions.to_csv(UKRSTAT_REGIONAL_ACCOUNTS_DIMENSIONS_TABLE, index=False)
        codelists.to_csv(UKRSTAT_REGIONAL_ACCOUNTS_CODELISTS_TABLE, index=False)

        return dimensions, codelists

    dimension_records = _recursive_find_records(
        payload,
        wanted_keys={
            "conceptIdentity",
            "localRepresentation",
            "position",
            "dimensions",
            "dimensionList",
        },
    )

    dimensions_raw = pd.DataFrame(dimension_records)

    if dimensions_raw.empty:
        dimensions = pd.DataFrame(
            [
                {
                    "dimension_id": "",
                    "dimension_name": "",
                    "json_path": "",
                    "representation_hint": "",
                    "implementation_status": "no_dimension_records_detected",
                    "notes": (
                        "Structure payload was fetched, but generic parser did not "
                        "detect clear dimension records. Inspect structure paths CSV."
                    ),
                }
            ]
        )
    else:
        dimensions = dimensions_raw.copy()
        dimensions["dimension_id"] = dimensions["id"]
        dimensions["dimension_name"] = dimensions["name"]
        dimensions["representation_hint"] = (
            dimensions["local_representation"].fillna("").astype(str)
            + " "
            + dimensions["concept_identity"].fillna("").astype(str)
            + " "
            + dimensions["codelist"].fillna("").astype(str)
        ).str.strip()
        dimensions["implementation_status"] = "candidate_dimension_record"
        dimensions["notes"] = (
            "Candidate parsed from SDMX structure metadata. Requires analyst "
            "review before observation query construction."
        )

        dimensions = dimensions[
            [
                "dimension_id",
                "dimension_name",
                "json_path",
                "representation_hint",
                "implementation_status",
                "notes",
            ]
        ].drop_duplicates()

    code_records = _recursive_find_records(
        payload,
        wanted_keys={
            "codes",
            "items",
            "codelists",
            "codelist",
        },
    )

    codes_raw = pd.DataFrame(code_records)

    if codes_raw.empty:
        codelists = pd.DataFrame(
            [
                {
                    "codelist_id": "",
                    "codelist_name": "",
                    "code_id": "",
                    "code_name": "",
                    "json_path": "",
                    "implementation_status": "no_codelist_records_detected",
                }
            ]
        )
    else:
        codelists = codes_raw.copy()
        codelists["codelist_id"] = codelists["id"]
        codelists["codelist_name"] = codelists["name"]
        codelists["code_id"] = codelists["id"]
        codelists["code_name"] = codelists["name"]
        codelists["implementation_status"] = "candidate_codelist_or_code_record"

        codelists = codelists[
            [
                "codelist_id",
                "codelist_name",
                "code_id",
                "code_name",
                "json_path",
                "implementation_status",
            ]
        ].drop_duplicates()

    dimensions.to_csv(UKRSTAT_REGIONAL_ACCOUNTS_DIMENSIONS_TABLE, index=False)
    codelists.to_csv(UKRSTAT_REGIONAL_ACCOUNTS_CODELISTS_TABLE, index=False)

    return dimensions, codelists


def build_metadata_clues_table(payload: Any | None) -> pd.DataFrame:
    """Extract useful codelist and concept-scheme clues from Ukrstat metadata."""
    ensure_dirs([TABLE_DIR])

    if payload is None:
        clues = pd.DataFrame(
            [
                {
                    "metadata_type": "structure_payload",
                    "id": "",
                    "name": "",
                    "agencyID": "",
                    "version": "",
                    "relevance_to_waris": "Unavailable",
                    "notes": "No structure payload available.",
                }
            ]
        )
        clues.to_csv(UKRSTAT_REGIONAL_ACCOUNTS_METADATA_CLUES_TABLE, index=False)
        return clues

    rows: list[dict] = []

    useful_ids = {
        "CL_KATOTTG": "Likely geography / administrative-territorial unit codelist.",
        "CL_REGIONAL_ACCOUNTS_INDICATOR": "Likely regional accounts indicator selector.",
        "CL_UNITS_OF_MEASURE": "Likely unit-of-measure codelist.",
        "CL_FREQ": "Likely observation frequency selector.",
        "CL_NACE_UA": "Likely economic activity classification.",
        "CS_REGIONAL_ACCOUNTS": "Regional accounts concept scheme.",
    }

    data = payload.get("data", {}) if isinstance(payload, dict) else {}

    for codelist in data.get("codelists", []):
        codelist_id = str(codelist.get("id", ""))

        if codelist_id in useful_ids:
            rows.append(
                {
                    "metadata_type": "codelist",
                    "id": codelist_id,
                    "name": _extract_name(codelist.get("name", codelist.get("names", ""))),
                    "agencyID": codelist.get("agencyID", ""),
                    "version": codelist.get("version", ""),
                    "relevance_to_waris": useful_ids[codelist_id],
                    "notes": (
                        "Useful metadata clue discovered. Still requires actual "
                        "dimension order before observation query construction."
                    ),
                }
            )

    for concept_scheme in data.get("conceptSchemes", []):
        concept_id = str(concept_scheme.get("id", ""))

        if concept_id in useful_ids:
            rows.append(
                {
                    "metadata_type": "concept_scheme",
                    "id": concept_id,
                    "name": _extract_name(
                        concept_scheme.get("name", concept_scheme.get("names", ""))
                    ),
                    "agencyID": concept_scheme.get("agencyID", ""),
                    "version": concept_scheme.get("version", ""),
                    "relevance_to_waris": useful_ids[concept_id],
                    "notes": (
                        "Useful concept-scheme clue discovered. Still requires actual "
                        "data structure dimensions before observation query construction."
                    ),
                }
            )

    if not rows:
        rows.append(
            {
                "metadata_type": "metadata_clue",
                "id": "",
                "name": "",
                "agencyID": "",
                "version": "",
                "relevance_to_waris": "No targeted codelist/concept clues found.",
                "notes": "Inspect structure paths manually.",
            }
        )

    clues = pd.DataFrame(rows).drop_duplicates()
    clues.to_csv(UKRSTAT_REGIONAL_ACCOUNTS_METADATA_CLUES_TABLE, index=False)

    return clues


def build_registry_references_table(payload: Any | None) -> pd.DataFrame:
    """Extract key registry references from the working Ukrstat SDMX response."""
    ensure_dirs([TABLE_DIR])

    if payload is None or not isinstance(payload, dict):
        references = pd.DataFrame(
            [
                {
                    "artifact_type": "structure_payload",
                    "artifact_id": "",
                    "name": "",
                    "agencyID": "",
                    "version": "",
                    "json_path": "",
                    "relevance_to_observation_pull": "Unavailable",
                    "notes": "No registry payload available.",
                }
            ]
        )
        references.to_csv(UKRSTAT_REGISTRY_REFERENCES_TABLE, index=False)
        return references

    data = payload.get("data", {})
    rows: list[dict] = []

    artifact_groups = {
        "dataStructures": "Data structure definition candidate. Needed to determine dimension order.",
        "dataflows": "Dataflow candidate. Needed to identify the observation dataset.",
        "codelists": "Codelist candidate. Needed to identify geography, indicator, unit, frequency, or activity codes.",
        "conceptSchemes": "Concept scheme candidate. Helps interpret measures and dimensions.",
        "categorySchemes": "Category scheme candidate. Helps locate thematic classification and publication grouping.",
    }

    targeted_ids = {
        DATAFLOW_ID,
        DSD_ID,
        "CL_KATOTTG",
        "CL_REGIONAL_ACCOUNTS_INDICATOR",
        "CL_UNITS_OF_MEASURE",
        "CL_FREQ",
        "CL_NACE_UA",
        "CS_REGIONAL_ACCOUNTS",
    }

    for group_name, relevance in artifact_groups.items():
        items = data.get(group_name, [])

        if not isinstance(items, list):
            continue

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue

            artifact_id = str(item.get("id", ""))
            artifact_name = _extract_name(item.get("name", item.get("names", "")))
            agency_id = str(item.get("agencyID", ""))
            version = str(item.get("version", ""))

            keep = False

            if artifact_id in targeted_ids:
                keep = True

            if "REGIONAL_ACCOUNTS" in artifact_id.upper():
                keep = True

            if "regional accounts" in artifact_name.lower():
                keep = True

            if keep:
                rows.append(
                    {
                        "artifact_type": group_name,
                        "artifact_id": artifact_id,
                        "name": artifact_name,
                        "agencyID": agency_id,
                        "version": version,
                        "json_path": f"data.{group_name}[{index}]",
                        "relevance_to_observation_pull": relevance,
                        "notes": (
                            "Registry reference extracted from working SDMX structure "
                            "response. Dimension order still requires DSD parsing."
                        ),
                    }
                )

    if not rows:
        rows.append(
            {
                "artifact_type": "registry_reference",
                "artifact_id": "",
                "name": "",
                "agencyID": "",
                "version": "",
                "json_path": "",
                "relevance_to_observation_pull": "No targeted references found.",
                "notes": "Inspect structure paths manually.",
            }
        )

    references = pd.DataFrame(rows).drop_duplicates()
    references = references.sort_values(
        ["artifact_type", "artifact_id", "version"],
        ascending=[True, True, False],
    ).reset_index(drop=True)

    references.to_csv(UKRSTAT_REGISTRY_REFERENCES_TABLE, index=False)

    return references


def build_dsd_dimension_candidates_table(payload: Any | None) -> pd.DataFrame:
    """Extract candidate dimensions from DSD_REGIONAL_ACCOUNTS."""
    ensure_dirs([TABLE_DIR])

    if payload is None or not isinstance(payload, dict):
        candidates = pd.DataFrame(
            [
                {
                    "dsd_id": "",
                    "dsd_version": "",
                    "dimension_id": "",
                    "dimension_name": "",
                    "position": "",
                    "concept_identity": "",
                    "local_representation": "",
                    "codelist_hint": "",
                    "json_path": "",
                    "implementation_status": "structure_payload_unavailable",
                    "notes": "No registry payload available.",
                }
            ]
        )
        candidates.to_csv(UKRSTAT_DSD_DIMENSION_CANDIDATES_TABLE, index=False)
        return candidates

    data = payload.get("data", {})
    data_structures = data.get("dataStructures", [])

    if not isinstance(data_structures, list):
        data_structures = []

    dsd_items: list[tuple[int, dict]] = [
        (index, item)
        for index, item in enumerate(data_structures)
        if isinstance(item, dict)
        and str(item.get("id", "")).upper() == DSD_ID
    ]

    dsd_items = sorted(
        dsd_items,
        key=lambda pair: str(pair[1].get("version", "")),
        reverse=True,
    )

    rows: list[dict] = []

    def walk_for_dimensions(
        value: Any,
        dsd_id: str,
        dsd_version: str,
        path: str = "",
    ) -> None:
        if isinstance(value, dict):
            keys = set(value.keys())

            dimension_like = (
                "conceptIdentity" in keys
                or "localRepresentation" in keys
                or "position" in keys
                or ("id" in keys and "dimension" in path.lower())
            )

            if dimension_like:
                dimension_id = str(value.get("id", ""))
                dimension_name = _extract_name(value.get("name", value.get("names", "")))
                position = str(value.get("position", ""))

                concept_identity = str(value.get("conceptIdentity", ""))
                local_representation = str(value.get("localRepresentation", ""))

                codelist_hint = ""

                if isinstance(value.get("localRepresentation"), dict):
                    local_repr = value.get("localRepresentation", {})

                    enum = local_repr.get("enumeration", "")
                    if enum:
                        codelist_hint = str(enum)

                    enum_format = local_repr.get("enumerationFormat", "")
                    if not codelist_hint and enum_format:
                        codelist_hint = str(enum_format)

                rows.append(
                    {
                        "dsd_id": dsd_id,
                        "dsd_version": dsd_version,
                        "dimension_id": dimension_id,
                        "dimension_name": dimension_name,
                        "position": position,
                        "concept_identity": concept_identity[:500],
                        "local_representation": local_representation[:500],
                        "codelist_hint": codelist_hint[:500],
                        "json_path": path,
                        "implementation_status": "candidate_dimension_from_dsd",
                        "notes": (
                            "Candidate dimension parsed from DSD_REGIONAL_ACCOUNTS. "
                            "Requires analyst review before observation query construction."
                        ),
                    }
                )

            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                walk_for_dimensions(child, dsd_id, dsd_version, child_path)

        elif isinstance(value, list):
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]"
                walk_for_dimensions(child, dsd_id, dsd_version, child_path)

    for original_index, dsd in dsd_items:
        dsd_id = str(dsd.get("id", ""))
        dsd_version = str(dsd.get("version", ""))

        walk_for_dimensions(
            dsd,
            dsd_id=dsd_id,
            dsd_version=dsd_version,
            path=f"data.dataStructures[{original_index}]",
        )

    if not rows:
        rows.append(
            {
                "dsd_id": DSD_ID,
                "dsd_version": "",
                "dimension_id": "",
                "dimension_name": "",
                "position": "",
                "concept_identity": "",
                "local_representation": "",
                "codelist_hint": "",
                "json_path": "",
                "implementation_status": "no_dsd_dimensions_detected",
                "notes": (
                    "DSD_REGIONAL_ACCOUNTS was referenced, but this parser did not "
                    "detect dimension records. Inspect raw structure paths manually."
                ),
            }
        )

    candidates = pd.DataFrame(rows).drop_duplicates()

    if "position" in candidates.columns:
        candidates["_position_numeric"] = pd.to_numeric(
            candidates["position"],
            errors="coerce",
        )
        candidates = candidates.sort_values(
            ["dsd_version", "_position_numeric", "dimension_id"],
            ascending=[False, True, True],
        ).drop(columns=["_position_numeric"])

    candidates.to_csv(UKRSTAT_DSD_DIMENSION_CANDIDATES_TABLE, index=False)

    return candidates


def build_dimension_code_candidates_table(payload: Any | None) -> pd.DataFrame:
    """Extract candidate codelist codes for WARIS Ukrstat observation queries."""
    ensure_dirs([TABLE_DIR])

    target_codelists = {
        "CL_REGIONAL_ACCOUNTS_INDICATOR": "INDICATOR",
        "CL_KATOTTG": "REGION",
        "CL_NACE_UA": "NACE",
        "CL_FREQ": "FREQ",
    }

    if payload is None or not isinstance(payload, dict):
        out = pd.DataFrame(
            [
                {
                    "dimension_id": "",
                    "codelist_id": "",
                    "codelist_version": "",
                    "code_id": "",
                    "code_name": "",
                    "code_description": "",
                    "candidate_role": "",
                    "query_use_status": "payload_unavailable",
                    "notes": "No DSD/codelist payload available.",
                }
            ]
        )
        out.to_csv(UKRSTAT_DIMENSION_CODE_CANDIDATES_TABLE, index=False)
        return out

    data = payload.get("data", {})
    codelists = data.get("codelists", [])

    rows: list[dict] = []

    if not isinstance(codelists, list):
        codelists = []

    for codelist in codelists:
        if not isinstance(codelist, dict):
            continue

        codelist_id = str(codelist.get("id", ""))
        if codelist_id not in target_codelists:
            continue

        dimension_id = target_codelists[codelist_id]
        codelist_version = str(codelist.get("version", ""))
        codes = codelist.get("codes", [])

        if not isinstance(codes, list):
            codes = []

        for code in codes:
            if not isinstance(code, dict):
                continue

            code_id = str(code.get("id", ""))
            code_name = _extract_name(code.get("name", code.get("names", "")))
            code_description = _extract_name(
                code.get("description", code.get("descriptions", ""))
            )

            role = "general_candidate"

            if dimension_id == "FREQ" and code_id.upper() in {"A", "Y", "ANNUAL"}:
                role = "likely_annual_frequency"

            if dimension_id == "REGION":
                name_text = f"{code_id} {code_name}".lower()
                if any(
                    token in name_text
                    for token in [
                        "oblast",
                        "kyiv",
                        "donetsk",
                        "lviv",
                        "kharkiv",
                        "odesa",
                        "dnipropetrovsk",
                    ]
                ):
                    role = "possible_oblast_region_code"

            if dimension_id == "NACE":
                if code_id in {"_T", "TOTAL", "A", "F", "G", "H", "K", "C"}:
                    role = "possible_sector_or_total_code"

            if dimension_id == "INDICATOR":
                name_text = f"{code_id} {code_name} {code_description}".lower()
                if any(
                    token in name_text
                    for token in [
                        "gross regional product",
                        "regional gross",
                        "value added",
                        "output",
                        "income",
                        "revenue",
                        "production",
                    ]
                ):
                    role = "possible_regional_baseline_indicator"

            rows.append(
                {
                    "dimension_id": dimension_id,
                    "codelist_id": codelist_id,
                    "codelist_version": codelist_version,
                    "code_id": code_id,
                    "code_name": code_name,
                    "code_description": code_description,
                    "candidate_role": role,
                    "query_use_status": "candidate_pending_review",
                    "notes": (
                        "Candidate code parsed from DSD codelist payload. Requires "
                        "analyst review before building an official observation query."
                    ),
                }
            )

    if not rows:
        rows.append(
            {
                "dimension_id": "",
                "codelist_id": "",
                "codelist_version": "",
                "code_id": "",
                "code_name": "",
                "code_description": "",
                "candidate_role": "",
                "query_use_status": "no_target_codes_detected",
                "notes": (
                    "Target codelists were not found in the available payload. "
                    "Inspect saved DSD reference paths manually."
                ),
            }
        )

    out = pd.DataFrame(rows).drop_duplicates()

    priority_order = {
        "possible_regional_baseline_indicator": 0,
        "possible_oblast_region_code": 1,
        "possible_sector_or_total_code": 2,
        "likely_annual_frequency": 3,
        "general_candidate": 9,
    }

    out["_priority"] = out["candidate_role"].map(priority_order).fillna(99)
    out = out.sort_values(
        ["dimension_id", "_priority", "code_id"],
        ascending=[True, True, True],
    ).drop(columns=["_priority"])

    out.to_csv(UKRSTAT_DIMENSION_CODE_CANDIDATES_TABLE, index=False)

    return out


def build_observation_query_candidates_table(
    dimension_code_candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Build a small analyst-review shortlist for future observation queries.

    The large dimension-code table can contain thousands of codelist values.
    This artifact narrows those values into a defensible review queue for the
    expected SDMX key order:

    INDICATOR.REGION.NACE.FREQ.TIME_PERIOD

    It does not pull observations and does not blend official values into WARIS
    scoring.
    """
    ensure_dirs([TABLE_DIR])

    required_cols = {
        "dimension_id",
        "codelist_id",
        "codelist_version",
        "code_id",
        "code_name",
        "code_description",
        "candidate_role",
        "query_use_status",
    }

    if (
        dimension_code_candidates is None
        or dimension_code_candidates.empty
        or not required_cols.issubset(set(dimension_code_candidates.columns))
    ):
        out = pd.DataFrame(
            [
                {
                    "query_dimension_order": "INDICATOR.REGION.NACE.FREQ.TIME_PERIOD",
                    "dimension_id": "",
                    "code_id": "",
                    "code_name": "",
                    "code_description": "",
                    "candidate_role": "",
                    "selection_reason": "",
                    "candidate_query_status": "dimension_code_candidates_unavailable",
                    "recommended_time_periods": "2021;2022;2023",
                    "notes": (
                        "Dimension-code candidates were unavailable or missing required "
                        "columns. Do not build an observation query from this artifact."
                    ),
                }
            ]
        )
        out.to_csv(UKRSTAT_OBSERVATION_QUERY_CANDIDATES_TABLE, index=False)
        return out

    candidates = dimension_code_candidates.copy()

    for col in required_cols:
        candidates[col] = candidates[col].fillna("").astype(str)

    candidates = candidates[
        candidates["query_use_status"].str.contains(
            "candidate_pending_review",
            case=False,
            na=False,
        )
    ].copy()

    if candidates.empty:
        out = pd.DataFrame(
            [
                {
                    "query_dimension_order": "INDICATOR.REGION.NACE.FREQ.TIME_PERIOD",
                    "dimension_id": "",
                    "code_id": "",
                    "code_name": "",
                    "code_description": "",
                    "candidate_role": "",
                    "selection_reason": "",
                    "candidate_query_status": "no_reviewable_codes_detected",
                    "recommended_time_periods": "2021;2022;2023",
                    "notes": (
                        "No candidate_pending_review codes were available. Do not "
                        "build an observation query from this artifact."
                    ),
                }
            ]
        )
        out.to_csv(UKRSTAT_OBSERVATION_QUERY_CANDIDATES_TABLE, index=False)
        return out

    rows: list[dict] = []

    def add_rows(
        frame: pd.DataFrame,
        selection_reason: str,
        max_rows: int,
    ) -> None:
        """Append a capped set of candidate-code rows to the shortlist."""
        if frame.empty:
            return

        frame = frame.drop_duplicates(
            subset=["dimension_id", "codelist_id", "code_id"]
        ).head(max_rows)

        for _, row in frame.iterrows():
            rows.append(
                {
                    "query_dimension_order": "INDICATOR.REGION.NACE.FREQ.TIME_PERIOD",
                    "dimension_id": row["dimension_id"],
                    "codelist_id": row["codelist_id"],
                    "codelist_version": row["codelist_version"],
                    "code_id": row["code_id"],
                    "code_name": row["code_name"],
                    "code_description": row["code_description"],
                    "candidate_role": row["candidate_role"],
                    "selection_reason": selection_reason,
                    "candidate_query_status": "shortlist_pending_review",
                    "recommended_time_periods": "2021;2022;2023",
                    "notes": (
                        "Shortlisted code for analyst review before building a live "
                        "Ukrstat observation query. This is not yet an executed "
                        "official observation pull."
                    ),
                }
            )

    # Indicator candidates: prefer explicit regional baseline language.
    indicator = candidates[candidates["dimension_id"] == "INDICATOR"].copy()
    indicator_priority = indicator[
        indicator["candidate_role"].str.contains(
            "possible_regional_baseline_indicator",
            case=False,
            na=False,
        )
    ]

    if indicator_priority.empty:
        name_text = (
            indicator["code_id"]
            + " "
            + indicator["code_name"]
            + " "
            + indicator["code_description"]
        ).str.lower()
        indicator_priority = indicator[
            name_text.str.contains(
                "gross|regional|value added|output|income|production|gdp|grp",
                case=False,
                na=False,
                regex=True,
            )
        ]

    add_rows(
        indicator_priority.sort_values(["candidate_role", "code_id"]),
        "Baseline indicator candidate: prioritize GRP/GVA/output/regional-account measures.",
        25,
    )

    if not any(row.get("dimension_id") == "INDICATOR" for row in rows):
        add_rows(
            indicator.sort_values(["candidate_role", "code_id"]),
            "Fallback indicator candidate: no clear baseline indicator detected; review manually.",
            15,
        )

    # Region candidates: prefer oblast-level KATOTTG geography only.
    #
    # CL_KATOTTG includes oblasts, raions, hromadas, settlements, city districts,
    # and other lower-level administrative records. Earlier keyword filtering
    # caught many false positives such as Kyivskyi, Lviv, Novokyivka, and other
    # lower-level places. For the first official observation-query shortlist, we
    # prefer probable oblast-level codes using two conservative signals:
    #
    # 1. The KATOTTG code has the oblast-level pattern:
    #    UA + 2 regional digits + many zeros + final check/control digits.
    #    Example: UA12000000000090473 = Dnipropetrovska.
    # 2. The English transliterated name ends in oblast-style suffixes such as
    #    -ska, -tska, -zka, -ka, or is Kyiv City / city of Kyiv.
    region = candidates[candidates["dimension_id"] == "REGION"].copy()

    def is_probable_oblast_level_region(code_id: str, code_name: str) -> bool:
        code = str(code_id).strip()
        name = str(code_name).strip().lower()

        if not code.startswith("UA"):
            return False

        # KATOTTG oblast-level examples observed in the codelist:
        # UA12000000000090473, UA14000000000091971, UA32000000000030281,
        # UA46000000000026241. This pattern helps exclude city, district,
        # hromada, and settlement codes that contain non-zero lower-level
        # administrative segments.
        has_oblast_level_zero_block = (
            len(code) >= 17
            and code[2:4].isdigit()
            and code[4:13] == "000000000"
        )

        if not has_oblast_level_zero_block:
            return False

        oblast_name_markers = (
            name.endswith("ska")
            or name.endswith("tska")
            or name.endswith("zka")
            or name.endswith("ka")
            or name in {"kyiv city", "city of kyiv", "kyiv"}
            or "kyiv city" in name
            or "city of kyiv" in name
        )

        return oblast_name_markers

    if not region.empty:
        region["_probable_oblast_level"] = region.apply(
            lambda row: is_probable_oblast_level_region(
                row.get("code_id", ""),
                row.get("code_name", ""),
            ),
            axis=1,
        )
        region_priority = region[region["_probable_oblast_level"]].copy()
    else:
        region_priority = region.copy()

    # Fallback remains available, but only if the stricter oblast-level KATOTTG
    # pattern finds nothing. This keeps the artifact robust while avoiding
    # overconfident lower-level geography selection.
    if region_priority.empty:
        name_text = (region["code_id"] + " " + region["code_name"]).str.lower()
        region_priority = region[
            name_text.str.contains(
                "oblast|kyiv city|city of kyiv|dnipropetrovska|donetska|kyivska|lvivska|kharkivska|odeska|zaporizka|khersonska|luhanska",
                case=False,
                na=False,
                regex=True,
            )
        ]

    if "_probable_oblast_level" in region_priority.columns:
        region_priority = region_priority.drop(columns=["_probable_oblast_level"])

    add_rows(
        region_priority.sort_values(["candidate_role", "code_id"]),
        "Region candidate: probable oblast-level KATOTTG code or Kyiv City administrative code.",
        30,
    )

    if not any(row.get("dimension_id") == "REGION" for row in rows):
        add_rows(
            region.sort_values(["candidate_role", "code_id"]),
            "Fallback region candidate: no clear oblast marker detected; review manually.",
            25,
        )

    # NACE candidates: start with total economy and WARIS-relevant sectors.
    nace = candidates[candidates["dimension_id"] == "NACE"].copy()
    preferred_nace_codes = {
        "_T",
        "TOTAL",
        "A",
        "B",
        "C",
        "F",
        "G",
        "H",
        "K",
        "64",
        "65",
        "66",
        "68",
        "69",
        "70",
        "71",
        "72",
        "80",
        "84",
    }

    nace_priority = nace[
        nace["code_id"].isin(preferred_nace_codes)
        | nace["candidate_role"].str.contains(
            "possible_sector_or_total_code",
            case=False,
            na=False,
        )
    ]

    add_rows(
        nace_priority.sort_values(["candidate_role", "code_id"]),
        (
            "NACE candidate: total economy or WARIS-relevant sector such as finance, "
            "real estate, public administration, security, construction, trade, "
            "transport, or production."
        ),
        40,
    )

    if not any(row.get("dimension_id") == "NACE" for row in rows):
        add_rows(
            nace.sort_values(["candidate_role", "code_id"]),
            "Fallback NACE candidate: no preferred total/sector code detected; review manually.",
            25,
        )

    # Frequency candidates: annual is the safest first query for regional accounts.
    freq = candidates[candidates["dimension_id"] == "FREQ"].copy()
    freq_priority = freq[
        freq["candidate_role"].str.contains(
            "likely_annual_frequency",
            case=False,
            na=False,
        )
        | freq["code_id"].str.upper().isin({"A", "Y", "ANNUAL"})
    ]

    add_rows(
        freq_priority.sort_values(["candidate_role", "code_id"]),
        "Frequency candidate: annual data is the safest first pull for regional accounts.",
        10,
    )

    if not any(row.get("dimension_id") == "FREQ" for row in rows):
        add_rows(
            freq.sort_values(["candidate_role", "code_id"]),
            "Fallback frequency candidate: no clear annual code detected; review manually.",
            10,
        )

    # TIME_PERIOD is a free observation-time selector rather than a codelist in the
    # current artifact, so document the initial safe periods as explicit rows.
    for period in ["2021", "2022", "2023"]:
        rows.append(
            {
                "query_dimension_order": "INDICATOR.REGION.NACE.FREQ.TIME_PERIOD",
                "dimension_id": "TIME_PERIOD",
                "codelist_id": "",
                "codelist_version": "",
                "code_id": period,
                "code_name": period,
                "code_description": "Candidate annual period for first official observation test.",
                "candidate_role": "candidate_time_period",
                "selection_reason": (
                    "Initial time-period candidate. Validate availability before "
                    "blending any observation values into WARIS scoring."
                ),
                "candidate_query_status": "shortlist_pending_review",
                "recommended_time_periods": "2021;2022;2023",
                "notes": (
                    "TIME_PERIOD is included to document the first cautious observation "
                    "pull window. These are not yet confirmed available observations."
                ),
            }
        )

    if not rows:
        rows.append(
            {
                "query_dimension_order": "INDICATOR.REGION.NACE.FREQ.TIME_PERIOD",
                "dimension_id": "",
                "codelist_id": "",
                "codelist_version": "",
                "code_id": "",
                "code_name": "",
                "code_description": "",
                "candidate_role": "",
                "selection_reason": "",
                "candidate_query_status": "no_query_shortlist_created",
                "recommended_time_periods": "2021;2022;2023",
                "notes": (
                    "No shortlist could be created from the available dimension-code "
                    "candidate table."
                ),
            }
        )

    out = pd.DataFrame(rows).drop_duplicates()

    dimension_order = {
        "INDICATOR": 0,
        "REGION": 1,
        "NACE": 2,
        "FREQ": 3,
        "TIME_PERIOD": 4,
    }

    role_priority = {
        "possible_regional_baseline_indicator": 0,
        "possible_oblast_region_code": 1,
        "possible_sector_or_total_code": 2,
        "likely_annual_frequency": 3,
        "candidate_time_period": 4,
        "general_candidate": 9,
    }

    out["_dimension_order"] = out["dimension_id"].map(dimension_order).fillna(99)
    out["_role_order"] = out["candidate_role"].map(role_priority).fillna(50)

    out = out.sort_values(
        ["_dimension_order", "_role_order", "code_id"],
        ascending=[True, True, True],
    ).drop(columns=["_dimension_order", "_role_order"])

    out.to_csv(UKRSTAT_OBSERVATION_QUERY_CANDIDATES_TABLE, index=False)

    return out



def _availability_codes_for_dimension(
    availability_value_candidates: pd.DataFrame | None,
    dimension_id: str,
    preferred_codes: list[str],
    max_values: int = 5,
) -> list[str]:
    """Return availability-derived codes for one SDMX dimension.

    Availability discovery is more reliable than manual defaults because it is
    based on the official SDMX availability response. This helper prioritizes
    preferred values if present and then appends other parsed availability
    candidates. It is used only for probe construction, not scoring.
    """
    if availability_value_candidates is None or availability_value_candidates.empty:
        return []

    required = {"dimension_id", "value_code", "query_use_status"}
    if not required.issubset(set(availability_value_candidates.columns)):
        return []

    working = availability_value_candidates.copy()
    for col in required:
        working[col] = working[col].fillna("").astype(str)

    working = working[
        working["query_use_status"].str.contains(
            "availability_candidate_pending_validation",
            case=False,
            na=False,
        )
        & working["dimension_id"].str.upper().eq(dimension_id.upper())
    ].copy()

    if working.empty:
        return []

    values = [
        str(value).strip()
        for value in working["value_code"].tolist()
        if str(value).strip()
    ]

    ordered: list[str] = []
    for preferred in preferred_codes:
        if preferred in values and preferred not in ordered:
            ordered.append(preferred)

    for value in values:
        if value not in ordered:
            ordered.append(value)

    return ordered[:max_values]


def _availability_first_code(
    availability_value_candidates: pd.DataFrame | None,
    dimension_id: str,
    preferred_codes: list[str],
) -> str:
    """Return the first availability-derived code for a dimension, if any."""
    values = _availability_codes_for_dimension(
        availability_value_candidates=availability_value_candidates,
        dimension_id=dimension_id,
        preferred_codes=preferred_codes,
        max_values=1,
    )
    return values[0] if values else ""

def probe_first_observation_query(
    observation_query_candidates: pd.DataFrame,
    availability_value_candidates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Probe one conservative official Ukrstat SDMX observation query.

    This is a diagnostic artifact, not a scoring input. It uses the shortlisted
    candidate table to select one defensible first test query in the expected
    SDMX key order:

    INDICATOR.REGION.NACE.FREQ.TIME_PERIOD

    This version uses the official Ukrstat SDMX v3 registry data route family:

    /registry/sdmx/3.0/data/dataflow/SSSU/<DATAFLOW>/<VERSION>/<KEY>

    It also probes the SDMX v3 availability route before any future observation
    pull, plus a small SDMX 2.1 fallback set. A successful response is saved for
    manual inspection only. It is not blended into WARIS scoring.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    query_order = "INDICATOR.REGION.NACE.FREQ.TIME_PERIOD"

    required_cols = {
        "dimension_id",
        "code_id",
        "code_name",
        "candidate_query_status",
    }

    if (
        observation_query_candidates is None
        or observation_query_candidates.empty
        or not required_cols.issubset(set(observation_query_candidates.columns))
    ):
        out = pd.DataFrame(
            [
                {
                    "probe_name": "observation_probe_unavailable",
                    "purpose": "Probe one conservative official-observation query.",
                    "query_dimension_order": query_order,
                    "sdmx_key": "",
                    "indicator_code": "",
                    "region_code": "",
                    "nace_code": "",
                    "freq_code": "",
                    "time_period": "",
                    "url": "",
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "response_preview": (
                        "Observation query candidates were unavailable. "
                        "No live observation probe executed."
                    ),
                    "notes": (
                        "Do not use Ukrstat observations in scoring until a valid "
                        "observation response, geography mapping, units, and time "
                        "periods are confirmed."
                    ),
                }
            ]
        )
        out.to_csv(UKRSTAT_OBSERVATION_PROBE_TABLE, index=False)
        return out

    candidates = observation_query_candidates.copy()

    for col in required_cols:
        candidates[col] = candidates[col].fillna("").astype(str)

    candidates = candidates[
        candidates["candidate_query_status"].str.contains(
            "shortlist_pending_review",
            case=False,
            na=False,
        )
    ].copy()

    def choose_code(dimension_id: str, preferred_codes: list[str]) -> tuple[str, str]:
        subset = candidates[candidates["dimension_id"] == dimension_id].copy()

        if subset.empty:
            return "", ""

        for preferred in preferred_codes:
            matched = subset[subset["code_id"].astype(str) == preferred]
            if not matched.empty:
                row = matched.iloc[0]
                return str(row.get("code_id", "")), str(row.get("code_name", ""))

        row = subset.iloc[0]
        return str(row.get("code_id", "")), str(row.get("code_name", ""))

    indicator_code, indicator_name = choose_code(
        "INDICATOR",
        ["GRP", "GVA", "OUTPUT", "GRP_CAP"],
    )
    region_code, region_name = choose_code(
        "REGION",
        [
            "UA12000000000090473",  # Dnipropetrovska
            "UA32000000000030281",  # Kyivska
            "UA80000000000093317",  # Kyiv
        ],
    )
    nace_code, nace_name = choose_code("NACE", ["_T", "TOTAL"])
    freq_code, freq_name = choose_code("FREQ", ["A", "Y", "ANNUAL"])
    time_period, _ = choose_code("TIME_PERIOD", ["2021", "2022", "2023"])

    # Prefer values parsed from the official availability response. The latest
    # successful availability probe showed that GRP regional-account data uses
    # NACE=_Z and full-date annual periods such as 2021-01-01 / 2022-01-01.
    availability_nace = _availability_first_code(
        availability_value_candidates,
        "NACE",
        ["_Z", "_T", "TOTAL"],
    )
    if availability_nace:
        nace_code = availability_nace
        nace_name = "Availability-derived NACE candidate"

    availability_freq = _availability_first_code(
        availability_value_candidates,
        "FREQ",
        ["A", "Y", "ANNUAL"],
    )
    if availability_freq:
        freq_code = availability_freq
        freq_name = "Availability-derived frequency candidate"

    availability_time = _availability_first_code(
        availability_value_candidates,
        "TIME_PERIOD",
        ["2021-01-01", "2022-01-01", "2021", "2022", "2023"],
    )
    if availability_time:
        time_period = availability_time

    if not time_period:
        time_period = "2021"

    if not all([indicator_code, region_code, nace_code, freq_code, time_period]):
        out = pd.DataFrame(
            [
                {
                    "probe_name": "observation_probe_missing_key_parts",
                    "purpose": "Probe one conservative official-observation query.",
                    "query_dimension_order": query_order,
                    "sdmx_key": "",
                    "indicator_code": indicator_code,
                    "region_code": region_code,
                    "nace_code": nace_code,
                    "freq_code": freq_code,
                    "time_period": time_period,
                    "url": "",
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "response_preview": (
                        "One or more required SDMX key parts were missing from the "
                        "observation query candidates table."
                    ),
                    "notes": (
                        "Do not execute or blend official observations until all "
                        "dimension codes are selected and validated."
                    ),
                }
            ]
        )
        out.to_csv(UKRSTAT_OBSERVATION_PROBE_TABLE, index=False)
        return out

    # DSD-derived documented order:
    # INDICATOR.REGION.NACE.FREQ.TIME_PERIOD
    sdmx_key_with_time = ".".join(
        [indicator_code, region_code, nace_code, freq_code, time_period]
    )
    series_key_without_time = ".".join(
        [indicator_code, region_code, nace_code, freq_code]
    )
    series_key_with_time_wildcard = ".".join(
        [indicator_code, region_code, nace_code, freq_code, "*"]
    )
    freq_first_series_key = ".".join(
        [freq_code, indicator_code, region_code, nace_code]
    )
    all_dimension_wildcard_key = "*.*.*.*.*"

    official_sdmx_3_data = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/3.0/data"
    )
    official_sdmx_3_availability = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/3.0/availability"
    )
    official_sdmx_2_data = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/2.1/data"
    )

    candidate_urls = [
        {
            "probe_name": "official_v3_availability_latest_series_exact",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{series_key_without_time}/all?mode=exact&references=all"
            ),
            "purpose": (
                "Probe official SDMX v3 availability endpoint for the selected "
                "series key before requesting observations."
            ),
        },
        {
            "probe_name": "official_v3_availability_v8_series_exact",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/8.0.0"
                f"/{series_key_without_time}/all?mode=exact&references=all"
            ),
            "purpose": (
                "Probe official SDMX v3 availability endpoint using dataflow version 8.0.0."
            ),
        },
        {
            "probe_name": "official_v3_data_latest_series_time_filter",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{series_key_without_time}?c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": (
                "Probe official SDMX v3 data endpoint with TIME_PERIOD passed as a c[] filter."
            ),
        },
        {
            "probe_name": "official_v3_data_v8_series_time_filter",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/8.0.0"
                f"/{series_key_without_time}?c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": (
                "Probe official SDMX v3 data endpoint, version 8.0.0, with TIME_PERIOD as c[] filter."
            ),
        },
        {
            "probe_name": "official_v3_data_latest_series_start_end",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{series_key_without_time}?startPeriod={time_period}"
                f"&endPeriod={time_period}&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": (
                "Probe official SDMX v3 data endpoint with startPeriod/endPeriod filters."
            ),
        },
        {
            "probe_name": "official_v3_data_latest_full_key",
            "sdmx_key": sdmx_key_with_time,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{sdmx_key_with_time}"
            ),
            "purpose": (
                "Probe official SDMX v3 data endpoint with TIME_PERIOD included in the key."
            ),
        },
        {
            "probe_name": "official_v3_data_latest_time_wildcard_key",
            "sdmx_key": series_key_with_time_wildcard,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{series_key_with_time_wildcard}?c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": (
                "Probe official SDMX v3 data endpoint with wildcard TIME_PERIOD in the key."
            ),
        },
        {
            "probe_name": "official_v3_data_latest_all_wildcards",
            "sdmx_key": all_dimension_wildcard_key,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{all_dimension_wildcard_key}?c[INDICATOR]={indicator_code}"
                f"&c[REGION]={region_code}&c[NACE]={nace_code}"
                f"&c[FREQ]={freq_code}&c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": (
                "Probe official SDMX v3 data endpoint with wildcard key and c[] dimension filters."
            ),
        },
        {
            "probe_name": "official_v3_data_latest_all_key",
            "sdmx_key": "*",
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/*?c[INDICATOR]={indicator_code}&c[REGION]={region_code}"
                f"&c[NACE]={nace_code}&c[FREQ]={freq_code}"
                f"&c[TIME_PERIOD]={time_period}&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": (
                "Probe official SDMX v3 data endpoint with fully omitted key and c[] filters."
            ),
        },
        {
            "probe_name": "official_v3_data_v8_freq_first_series",
            "sdmx_key": freq_first_series_key,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/8.0.0"
                f"/{freq_first_series_key}?c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": (
                "Probe official SDMX v3 data endpoint with conservative FREQ-first fallback key."
            ),
        },
        {
            "probe_name": "official_v2_data_series_start_end",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_2_data}/{DATAFLOW_ID}/{series_key_without_time}/SSSU"
                f"?startPeriod={time_period}&endPeriod={time_period}"
            ),
            "purpose": (
                "Probe official SDMX 2.1 data endpoint with series key and period filters."
            ),
        },
        {
            "probe_name": "official_v2_data_full_key",
            "sdmx_key": sdmx_key_with_time,
            "url": (
                f"{official_sdmx_2_data}/{DATAFLOW_ID}/{sdmx_key_with_time}/SSSU"
            ),
            "purpose": "Probe official SDMX 2.1 data endpoint with full key.",
        },
        {
            "probe_name": "official_v2_data_all_wildcards",
            "sdmx_key": all_dimension_wildcard_key,
            "url": (
                f"{official_sdmx_2_data}/{DATAFLOW_ID}/{all_dimension_wildcard_key}/SSSU"
                f"?startPeriod={time_period}&endPeriod={time_period}"
            ),
            "purpose": "Probe official SDMX 2.1 data endpoint with wildcard key.",
        },
    ]

    rows: list[dict] = []
    saved_successful_response = False
    saved_data_response = False

    for candidate in candidate_urls:
        url = candidate["url"]

        try:
            response = requests.get(
                url,
                timeout=45,
                headers={
                    "User-Agent": "WARIS research prototype",
                    "Accept": (
                        "application/vnd.sdmx.data+json;version=2.0.0, "
                        "application/vnd.sdmx.data+json;version=1.0.0, "
                        "application/vnd.sdmx.structure+json;version=2.0.0, "
                        "application/json, text/csv, */*"
                    ),
                },
            )

            content_type = response.headers.get("Content-Type", "")
            text_preview = response.text[:750].replace("\n", " ").replace("\r", " ")

            first_json_keys = ""

            try:
                payload = response.json()
                if isinstance(payload, dict):
                    first_json_keys = "; ".join(list(payload.keys())[:20])
            except Exception:
                first_json_keys = ""

            success_status = 200 <= response.status_code < 300

            is_data_response = (
                success_status
                and "application/vnd.sdmx.data" in content_type.lower()
                and "/data/dataflow/" in url
            )

            if success_status and not saved_successful_response:
                UKRSTAT_OBSERVATION_PROBE_RAW.write_text(
                    response.text,
                    encoding="utf-8",
                    errors="ignore",
                )
                saved_successful_response = True

            if is_data_response and not saved_data_response:
                UKRSTAT_OBSERVATION_DATA_RESPONSE_RAW.write_text(
                    response.text,
                    encoding="utf-8",
                    errors="ignore",
                )
                saved_data_response = True

            rows.append(
                {
                    "probe_name": candidate["probe_name"],
                    "purpose": candidate["purpose"],
                    "query_dimension_order": query_order,
                    "sdmx_key": candidate.get("sdmx_key", ""),
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": region_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "time_period": time_period,
                    "url": url,
                    "http_status": response.status_code,
                    "success_status": success_status,
                    "content_type": content_type,
                    "first_json_keys": first_json_keys,
                    "response_preview": text_preview,
                    "notes": (
                        "Official Ukrstat SDMX observation probe only. Do not blend "
                        "into WARIS scoring until response content, units, geography "
                        "mapping, NACE mapping, and time-period coverage are validated."
                    ),
                }
            )

        except Exception as exc:
            rows.append(
                {
                    "probe_name": candidate["probe_name"],
                    "purpose": candidate["purpose"],
                    "query_dimension_order": query_order,
                    "sdmx_key": candidate.get("sdmx_key", ""),
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": region_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "time_period": time_period,
                    "url": url,
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "response_preview": f"Request failed: {exc}",
                    "notes": (
                        "Official Ukrstat SDMX observation probe only. Do not blend "
                        "into WARIS scoring until response content, units, geography "
                        "mapping, NACE mapping, and time-period coverage are validated."
                    ),
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(UKRSTAT_OBSERVATION_PROBE_TABLE, index=False)

    return out


def probe_data_endpoint_discovery(
    observation_query_candidates: pd.DataFrame,
    availability_value_candidates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Probe official Ukrstat SDMX data and availability route families.

    Earlier route-discovery probes confirmed that metadata, DSD, codelists, and
    query candidates are working, but generic /data route families returned 404.
    This version focuses on the official documented SDMX v3 registry route:

    /registry/sdmx/3.0/data/{context}/{agencyID}/{resourceID}/{version}/{key}

    It also probes the official SDMX v3 availability route and SDMX 2.1 fallback
    route. This does not blend official observations into WARIS scoring.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    query_order = "INDICATOR.REGION.NACE.FREQ.TIME_PERIOD"

    required_cols = {
        "dimension_id",
        "code_id",
        "code_name",
        "candidate_query_status",
    }

    if (
        observation_query_candidates is None
        or observation_query_candidates.empty
        or not required_cols.issubset(set(observation_query_candidates.columns))
    ):
        out = pd.DataFrame(
            [
                {
                    "probe_name": "data_endpoint_discovery_unavailable",
                    "purpose": "Discover correct Ukrstat observation data endpoint route.",
                    "query_dimension_order": query_order,
                    "sdmx_key": "",
                    "series_key_without_time": "",
                    "indicator_code": "",
                    "region_code": "",
                    "nace_code": "",
                    "freq_code": "",
                    "time_period": "",
                    "base_route_family": "",
                    "url": "",
                    "http_status": "",
                    "success_status": False,
                    "non_404_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "response_preview": (
                        "Observation query candidates were unavailable. No data "
                        "endpoint discovery probes executed."
                    ),
                    "notes": (
                        "Do not use Ukrstat observations in scoring until a valid "
                        "observation endpoint route and response are confirmed."
                    ),
                }
            ]
        )
        out.to_csv(UKRSTAT_DATA_ENDPOINT_DISCOVERY_TABLE, index=False)
        return out

    candidates = observation_query_candidates.copy()

    for col in required_cols:
        candidates[col] = candidates[col].fillna("").astype(str)

    candidates = candidates[
        candidates["candidate_query_status"].str.contains(
            "shortlist_pending_review",
            case=False,
            na=False,
        )
    ].copy()

    def choose_code(dimension_id: str, preferred_codes: list[str]) -> tuple[str, str]:
        subset = candidates[candidates["dimension_id"] == dimension_id].copy()

        if subset.empty:
            return "", ""

        for preferred in preferred_codes:
            matched = subset[subset["code_id"].astype(str) == preferred]
            if not matched.empty:
                row = matched.iloc[0]
                return str(row.get("code_id", "")), str(row.get("code_name", ""))

        row = subset.iloc[0]
        return str(row.get("code_id", "")), str(row.get("code_name", ""))

    indicator_code, indicator_name = choose_code(
        "INDICATOR",
        ["GRP", "GVA", "OUTPUT", "GRP_CAP"],
    )
    region_code, region_name = choose_code(
        "REGION",
        [
            "UA12000000000090473",  # Dnipropetrovska
            "UA32000000000030281",  # Kyivska
            "UA80000000000093317",  # Kyiv
        ],
    )
    nace_code, nace_name = choose_code("NACE", ["_T", "TOTAL"])
    freq_code, freq_name = choose_code("FREQ", ["A", "Y", "ANNUAL"])
    time_period, _ = choose_code("TIME_PERIOD", ["2021", "2022", "2023"])

    # Prefer values parsed from the official availability response. The latest
    # successful availability probe showed that GRP regional-account data uses
    # NACE=_Z and full-date annual periods such as 2021-01-01 / 2022-01-01.
    availability_nace = _availability_first_code(
        availability_value_candidates,
        "NACE",
        ["_Z", "_T", "TOTAL"],
    )
    if availability_nace:
        nace_code = availability_nace
        nace_name = "Availability-derived NACE candidate"

    availability_freq = _availability_first_code(
        availability_value_candidates,
        "FREQ",
        ["A", "Y", "ANNUAL"],
    )
    if availability_freq:
        freq_code = availability_freq
        freq_name = "Availability-derived frequency candidate"

    availability_time = _availability_first_code(
        availability_value_candidates,
        "TIME_PERIOD",
        ["2021-01-01", "2022-01-01", "2021", "2022", "2023"],
    )
    if availability_time:
        time_period = availability_time

    if not time_period:
        time_period = "2021"

    if not all([indicator_code, region_code, nace_code, freq_code, time_period]):
        out = pd.DataFrame(
            [
                {
                    "probe_name": "data_endpoint_discovery_missing_key_parts",
                    "purpose": "Discover correct Ukrstat observation data endpoint route.",
                    "query_dimension_order": query_order,
                    "sdmx_key": "",
                    "series_key_without_time": "",
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": region_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "time_period": time_period,
                    "base_route_family": "",
                    "url": "",
                    "http_status": "",
                    "success_status": False,
                    "non_404_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "response_preview": (
                        "One or more required SDMX key parts were missing from the "
                        "observation query candidates table."
                    ),
                    "notes": (
                        "Do not execute or blend official observations until all "
                        "dimension codes are selected and validated."
                    ),
                }
            ]
        )
        out.to_csv(UKRSTAT_DATA_ENDPOINT_DISCOVERY_TABLE, index=False)
        return out

    sdmx_key_with_time = ".".join(
        [indicator_code, region_code, nace_code, freq_code, time_period]
    )
    series_key_without_time = ".".join(
        [indicator_code, region_code, nace_code, freq_code]
    )
    series_key_with_time_wildcard = ".".join(
        [indicator_code, region_code, nace_code, freq_code, "*"]
    )
    freq_first_series_key = ".".join(
        [freq_code, indicator_code, region_code, nace_code]
    )
    all_dimension_wildcard_key = "*.*.*.*.*"

    official_sdmx_3_data = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/3.0/data"
    )
    official_sdmx_3_availability = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/3.0/availability"
    )
    official_sdmx_2_data = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/2.1/data"
    )

    route_patterns = [
        {
            "base_route_family": "official_sdmx_3_availability_latest",
            "probe_name": "availability_latest_series_exact",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{series_key_without_time}/all?mode=exact&references=all"
            ),
            "purpose": "Probe official SDMX v3 availability route with latest stable version.",
        },
        {
            "base_route_family": "official_sdmx_3_availability_latest_plus",
            "probe_name": "availability_plus_series_exact",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/+"
                f"/{series_key_without_time}/all?mode=exact&references=all"
            ),
            "purpose": "Probe official SDMX v3 availability route with latest version token '+'.",
        },
        {
            "base_route_family": "official_sdmx_3_availability_v8",
            "probe_name": "availability_v8_series_exact",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/8.0.0"
                f"/{series_key_without_time}/all?mode=exact&references=all"
            ),
            "purpose": "Probe official SDMX v3 availability route with version 8.0.0.",
        },
        {
            "base_route_family": "official_sdmx_3_data_latest_c_filter",
            "probe_name": "data_latest_series_c_time",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{series_key_without_time}?c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": "Probe official SDMX v3 data route with TIME_PERIOD c[] filter.",
        },
        {
            "base_route_family": "official_sdmx_3_data_latest_plus_c_filter",
            "probe_name": "data_plus_series_c_time",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/+"
                f"/{series_key_without_time}?c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": "Probe official SDMX v3 data route with latest version token '+'.",
        },
        {
            "base_route_family": "official_sdmx_3_data_v8_c_filter",
            "probe_name": "data_v8_series_c_time",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/8.0.0"
                f"/{series_key_without_time}?c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": "Probe official SDMX v3 data route, version 8.0.0, with TIME_PERIOD c[] filter.",
        },
        {
            "base_route_family": "official_sdmx_3_data_latest_start_end",
            "probe_name": "data_latest_series_start_end",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{series_key_without_time}?startPeriod={time_period}"
                f"&endPeriod={time_period}&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": "Probe official SDMX v3 data route with startPeriod/endPeriod.",
        },
        {
            "base_route_family": "official_sdmx_3_data_latest_full_key",
            "probe_name": "data_latest_full_key",
            "sdmx_key": sdmx_key_with_time,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{sdmx_key_with_time}"
            ),
            "purpose": "Probe official SDMX v3 data route with TIME_PERIOD in key.",
        },
        {
            "base_route_family": "official_sdmx_3_data_latest_time_wildcard",
            "probe_name": "data_latest_time_wildcard_key",
            "sdmx_key": series_key_with_time_wildcard,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{series_key_with_time_wildcard}?c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": "Probe official SDMX v3 data route with wildcard TIME_PERIOD in key.",
        },
        {
            "base_route_family": "official_sdmx_3_data_latest_all_wildcards",
            "probe_name": "data_latest_all_wildcards_c_filters",
            "sdmx_key": all_dimension_wildcard_key,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{all_dimension_wildcard_key}?c[INDICATOR]={indicator_code}"
                f"&c[REGION]={region_code}&c[NACE]={nace_code}"
                f"&c[FREQ]={freq_code}&c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": "Probe official SDMX v3 data route with wildcard key and c[] filters.",
        },
        {
            "base_route_family": "official_sdmx_3_data_latest_all_key",
            "probe_name": "data_latest_all_key_c_filters",
            "sdmx_key": "*",
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/*?c[INDICATOR]={indicator_code}&c[REGION]={region_code}"
                f"&c[NACE]={nace_code}&c[FREQ]={freq_code}"
                f"&c[TIME_PERIOD]={time_period}&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": "Probe official SDMX v3 data route with '*' key and c[] filters.",
        },
        {
            "base_route_family": "official_sdmx_3_data_v8_freq_first",
            "probe_name": "data_v8_freq_first_series",
            "sdmx_key": freq_first_series_key,
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/8.0.0"
                f"/{freq_first_series_key}?c[TIME_PERIOD]={time_period}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
            "purpose": "Probe official SDMX v3 data route with FREQ-first fallback key.",
        },
        {
            "base_route_family": "official_sdmx_2_data_series",
            "probe_name": "sdmx_2_series_start_end",
            "sdmx_key": series_key_without_time,
            "url": (
                f"{official_sdmx_2_data}/{DATAFLOW_ID}/{series_key_without_time}/SSSU"
                f"?startPeriod={time_period}&endPeriod={time_period}"
            ),
            "purpose": "Probe official SDMX 2.1 data route with series key and period filters.",
        },
        {
            "base_route_family": "official_sdmx_2_data_full_key",
            "probe_name": "sdmx_2_full_key",
            "sdmx_key": sdmx_key_with_time,
            "url": (
                f"{official_sdmx_2_data}/{DATAFLOW_ID}/{sdmx_key_with_time}/SSSU"
            ),
            "purpose": "Probe official SDMX 2.1 data route with full key.",
        },
        {
            "base_route_family": "official_sdmx_2_data_all_wildcards",
            "probe_name": "sdmx_2_all_wildcards",
            "sdmx_key": all_dimension_wildcard_key,
            "url": (
                f"{official_sdmx_2_data}/{DATAFLOW_ID}/{all_dimension_wildcard_key}/SSSU"
                f"?startPeriod={time_period}&endPeriod={time_period}"
            ),
            "purpose": "Probe official SDMX 2.1 data route with wildcard key.",
        },
    ]

    rows: list[dict] = []
    saved_informative_response = False
    saved_data_response = False

    for pattern in route_patterns:
        url = pattern["url"]

        try:
            response = requests.get(
                url,
                timeout=45,
                headers={
                    "User-Agent": "WARIS research prototype",
                    "Accept": (
                        "application/vnd.sdmx.data+json;version=2.0.0, "
                        "application/vnd.sdmx.data+json;version=1.0.0, "
                        "application/vnd.sdmx.structure+json;version=2.0.0, "
                        "application/json, text/csv, */*"
                    ),
                },
            )

            content_type = response.headers.get("Content-Type", "")
            text_preview = response.text[:750].replace("\n", " ").replace("\r", " ")

            first_json_keys = ""

            try:
                payload = response.json()
                if isinstance(payload, dict):
                    first_json_keys = "; ".join(list(payload.keys())[:20])
            except Exception:
                first_json_keys = ""

            success_status = 200 <= response.status_code < 300
            non_404_status = response.status_code != 404

            if (success_status or non_404_status) and not saved_informative_response:
                UKRSTAT_DATA_ENDPOINT_DISCOVERY_RAW.write_text(
                    response.text,
                    encoding="utf-8",
                    errors="ignore",
                )
                saved_informative_response = True

            rows.append(
                {
                    "probe_name": pattern["probe_name"],
                    "purpose": pattern["purpose"],
                    "query_dimension_order": query_order,
                    "sdmx_key": pattern["sdmx_key"],
                    "series_key_without_time": series_key_without_time,
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": region_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "time_period": time_period,
                    "base_route_family": pattern["base_route_family"],
                    "url": url,
                    "http_status": response.status_code,
                    "success_status": success_status,
                    "non_404_status": non_404_status,
                    "content_type": content_type,
                    "first_json_keys": first_json_keys,
                    "response_preview": text_preview,
                    "notes": (
                        "Official SDMX route-discovery probe only. Do not blend into "
                        "WARIS scoring until route, response content, units, geography "
                        "mapping, NACE mapping, and time-period coverage are validated."
                    ),
                }
            )

        except Exception as exc:
            rows.append(
                {
                    "probe_name": pattern["probe_name"],
                    "purpose": pattern["purpose"],
                    "query_dimension_order": query_order,
                    "sdmx_key": pattern["sdmx_key"],
                    "series_key_without_time": series_key_without_time,
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": region_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "time_period": time_period,
                    "base_route_family": pattern["base_route_family"],
                    "url": url,
                    "http_status": "",
                    "success_status": False,
                    "non_404_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "response_preview": f"Request failed: {exc}",
                    "notes": (
                        "Official SDMX route-discovery probe only. Do not blend into "
                        "WARIS scoring until route, response content, units, geography "
                        "mapping, NACE mapping, and time-period coverage are validated."
                    ),
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(UKRSTAT_DATA_ENDPOINT_DISCOVERY_TABLE, index=False)

    return out


def probe_ukrstat_endpoints() -> pd.DataFrame:
    """Probe likely Ukrstat SDMX endpoints without pulling observations into scoring."""
    ensure_dirs([TABLE_DIR])

    candidate_urls = [
        {
            "probe_name": "dataflow_with_all_references",
            "url": (
                f"{UKRSTAT_SDMX_STRUCTURE_BASE}/dataflow/*/{DATAFLOW_ID}/*"
                "?detail=allstubs&references=all"
            ),
            "purpose": "Confirm dataflow and related registry metadata.",
        },
        {
            "probe_name": "dataflow_full_references",
            "url": (
                f"{UKRSTAT_SDMX_STRUCTURE_BASE}/dataflow/*/{DATAFLOW_ID}/*"
                "?detail=full&references=all"
            ),
            "purpose": "Attempt fuller dataflow metadata response.",
        },
        {
            "probe_name": "all_datastructures_full",
            "url": (
                f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/*/*/*"
                "?detail=full&references=all"
            ),
            "purpose": "Search all available data structures for regional-account DSD references.",
        },
        {
            "probe_name": "all_structures_allstubs",
            "url": (
                f"{UKRSTAT_SDMX_STRUCTURE_BASE}/*/*/*/*"
                "?detail=allstubs&references=all"
            ),
            "purpose": "Broad registry structure probe.",
        },
        {
            "probe_name": "possible_sdmx_data_endpoint_v1",
            "url": (
                "https://stat.gov.ua/sdmx/workspaces/default:integration/"
                f"data/{DATAFLOW_ID}/all/all?startPeriod=2021&endPeriod=2023"
            ),
            "purpose": "Probe possible SDMX data endpoint pattern.",
        },
        {
            "probe_name": "possible_sdmx_data_endpoint_v2",
            "url": (
                "https://stat.gov.ua/sdmx/workspaces/default:integration/"
                f"data/{DATAFLOW_ID}/.?startPeriod=2021&endPeriod=2023"
            ),
            "purpose": "Probe compact SDMX data query pattern.",
        },
        {
            "probe_name": "possible_sdmx_data_endpoint_v3",
            "url": (
                "https://stat.gov.ua/sdmx/workspaces/default:integration/"
                f"data/dataflow/SSSU/{DATAFLOW_ID}/1.0?"
                "startPeriod=2021&endPeriod=2023"
            ),
            "purpose": "Probe dataflow-qualified SDMX data endpoint pattern.",
        },
    ]

    rows: list[dict] = []

    for candidate in candidate_urls:
        url = candidate["url"]

        try:
            response = requests.get(
                url,
                timeout=45,
                headers={
                    "User-Agent": "WARIS research prototype",
                    "Accept": (
                        "application/vnd.sdmx.data+json;version=1.0.0, "
                        "application/vnd.sdmx.structure+json;version=2.0.0, "
                        "application/json, text/csv, */*"
                    ),
                },
            )

            content_type = response.headers.get("Content-Type", "")
            text_preview = response.text[:500].replace("\n", " ").replace("\r", " ")

            first_json_keys = ""

            try:
                payload = response.json()

                if isinstance(payload, dict):
                    first_json_keys = "; ".join(list(payload.keys())[:20])
            except Exception:
                first_json_keys = ""

            rows.append(
                {
                    "probe_name": candidate["probe_name"],
                    "purpose": candidate["purpose"],
                    "url": url,
                    "http_status": response.status_code,
                    "success_status": 200 <= response.status_code < 300,
                    "content_type": content_type,
                    "first_json_keys": first_json_keys,
                    "response_preview": text_preview,
                }
            )

        except Exception as exc:
            rows.append(
                {
                    "probe_name": candidate["probe_name"],
                    "purpose": candidate["purpose"],
                    "url": url,
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "response_preview": f"Request failed: {exc}",
                }
            )

    probe_results = pd.DataFrame(rows)
    probe_results.to_csv(UKRSTAT_ENDPOINT_PROBE_TABLE, index=False)

    return probe_results


def probe_dsd_specific_endpoints() -> pd.DataFrame:
    """Probe DSD-specific Ukrstat SDMX structure endpoints."""
    ensure_dirs([TABLE_DIR])

    candidate_urls = [
        {
            "probe_name": "dsd_6_full_references",
            "url": (
                f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/6.0.0"
                "?detail=full&references=all"
            ),
            "purpose": "Fetch full DSD version 6.0.0 with all references.",
        },
        {
            "probe_name": "dsd_6_allstubs_references",
            "url": (
                f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/6.0.0"
                "?detail=allstubs&references=all"
            ),
            "purpose": "Fetch DSD version 6.0.0 with allstubs references.",
        },
        {
            "probe_name": "dsd_6_full_none",
            "url": (
                f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/6.0.0"
                "?detail=full&references=none"
            ),
            "purpose": "Fetch full DSD version 6.0.0 without referenced artifacts.",
        },
        {
            "probe_name": "dsd_any_version_full",
            "url": (
                f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/*"
                "?detail=full&references=all"
            ),
            "purpose": "Fetch any DSD_REGIONAL_ACCOUNTS version with full references.",
        },
        {
            "probe_name": "dsd_5_full_references",
            "url": (
                f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/5.0.0"
                "?detail=full&references=all"
            ),
            "purpose": "Fetch older DSD version 5.0.0 with all references.",
        },
    ]

    rows: list[dict] = []

    for candidate in candidate_urls:
        url = candidate["url"]

        try:
            response = requests.get(
                url,
                timeout=45,
                headers={
                    "User-Agent": "WARIS research prototype",
                    "Accept": (
                        "application/vnd.sdmx.structure+json;version=2.0.0, "
                        "application/json, */*"
                    ),
                },
            )

            content_type = response.headers.get("Content-Type", "")
            text_preview = response.text[:500].replace("\n", " ").replace("\r", " ")

            first_json_keys = ""

            try:
                payload = response.json()

                if isinstance(payload, dict):
                    first_json_keys = "; ".join(list(payload.keys())[:20])
            except Exception:
                first_json_keys = ""

            rows.append(
                {
                    "probe_name": candidate["probe_name"],
                    "purpose": candidate["purpose"],
                    "url": url,
                    "http_status": response.status_code,
                    "success_status": 200 <= response.status_code < 300,
                    "content_type": content_type,
                    "first_json_keys": first_json_keys,
                    "response_preview": text_preview,
                }
            )

        except Exception as exc:
            rows.append(
                {
                    "probe_name": candidate["probe_name"],
                    "purpose": candidate["purpose"],
                    "url": url,
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "response_preview": f"Request failed: {exc}",
                }
            )

    probe_results = pd.DataFrame(rows)
    probe_results.to_csv(UKRSTAT_DSD_ENDPOINT_PROBE_TABLE, index=False)

    return probe_results


def fetch_best_dsd_structure_payload() -> Any | None:
    """Fetch and save the best DSD_REGIONAL_ACCOUNTS payload for dimension parsing.

    Preference order:
    1. DSD 6.0.0 full, references=none
    2. DSD 6.0.0 full, references=all
    3. Any DSD_REGIONAL_ACCOUNTS version full, references=all
    4. DSD 5.0.0 full, references=all
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    candidate_urls = [
        (
            "dsd_6_full_none",
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/6.0.0"
            "?detail=full&references=none",
        ),
        (
            "dsd_6_full_references",
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/6.0.0"
            "?detail=full&references=all",
        ),
        (
            "dsd_any_version_full",
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/*"
            "?detail=full&references=all",
        ),
        (
            "dsd_5_full_references",
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/5.0.0"
            "?detail=full&references=all",
        ),
    ]

    for label, url in candidate_urls:
        payload = _safe_get_json(url)

        if payload is not None:
            _write_json(UKRSTAT_DSD_STRUCTURE_RAW, payload)

            flattened = _flatten_json_paths(payload)
            if not flattened.empty:
                flattened.to_csv(UKRSTAT_DSD_STRUCTURE_PATHS_RAW, index=False)

            return payload

    return None


def fetch_dsd_codelist_payload() -> Any | None:
    """Fetch and save a codelist-rich DSD payload for dimension-code parsing.

    The references=none DSD payload is best for parsing dimension structure.
    The references=all DSD payload is better for extracting the referenced
    codelists and codes needed to build observation-query candidates.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    candidate_urls = [
        (
            "dsd_6_full_references",
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/6.0.0"
            "?detail=full&references=all",
        ),
        (
            "dsd_any_version_full",
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/*"
            "?detail=full&references=all",
        ),
        (
            "dsd_5_full_references",
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/5.0.0"
            "?detail=full&references=all",
        ),
        (
            "dsd_6_allstubs_references",
            f"{UKRSTAT_SDMX_STRUCTURE_BASE}/datastructure/SSSU/{DSD_ID}/6.0.0"
            "?detail=allstubs&references=all",
        ),
    ]

    for label, url in candidate_urls:
        payload = _safe_get_json(url)

        if payload is not None:
            _write_json(UKRSTAT_DSD_REFERENCES_STRUCTURE_RAW, payload)

            flattened = _flatten_json_paths(payload)
            if not flattened.empty:
                flattened.to_csv(
                    UKRSTAT_DSD_REFERENCES_STRUCTURE_PATHS_RAW,
                    index=False,
                )

            return payload

    return None




def _count_sdmx_observation_values(payload: Any) -> int:
    """Count likely observation values in a compact SDMX JSON response."""
    if not isinstance(payload, dict):
        return 0

    data = payload.get("data", payload)
    if not isinstance(data, dict):
        return 0

    count = 0
    data_sets = data.get("dataSets", [])
    if not isinstance(data_sets, list):
        data_sets = []

    for dataset in data_sets:
        if not isinstance(dataset, dict):
            continue

        observations = dataset.get("observations", {})
        if isinstance(observations, dict):
            for obs_payload in observations.values():
                if isinstance(obs_payload, list) and obs_payload:
                    count += 1
                elif obs_payload not in [None, ""]:
                    count += 1

        series = dataset.get("series", {})
        if isinstance(series, dict):
            for series_payload in series.values():
                if not isinstance(series_payload, dict):
                    continue

                series_observations = series_payload.get("observations", {})
                if isinstance(series_observations, dict):
                    for obs_payload in series_observations.values():
                        if isinstance(obs_payload, list) and obs_payload:
                            count += 1
                        elif obs_payload not in [None, ""]:
                            count += 1

    return count


def probe_observation_matrix(
    observation_query_candidates: pd.DataFrame,
    availability_value_candidates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Probe a small matrix of official Ukrstat observation combinations.

    The first confirmed SDMX data route can return valid structure metadata even
    when a specific indicator-region-year combination has no observations. This
    diagnostic matrix tests a small, conservative set of nearby combinations to
    identify which official series actually return observation values.

    This function is still non-operational: it writes probe metadata and saves
    the first response that appears to contain observations for manual review.
    It does not blend official values into WARIS scoring.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    query_order = "INDICATOR.REGION.NACE.FREQ.TIME_PERIOD"
    required_cols = {"dimension_id", "code_id", "code_name", "candidate_query_status"}

    columns = [
        "probe_name",
        "purpose",
        "query_dimension_order",
        "sdmx_key",
        "indicator_code",
        "indicator_name",
        "region_code",
        "region_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "time_period",
        "url",
        "http_status",
        "success_status",
        "content_type",
        "first_json_keys",
        "observation_value_count",
        "has_observations",
        "response_preview",
        "notes",
    ]

    if (
        observation_query_candidates is None
        or observation_query_candidates.empty
        or not required_cols.issubset(set(observation_query_candidates.columns))
    ):
        out = pd.DataFrame(
            [
                {
                    "probe_name": "observation_matrix_unavailable",
                    "purpose": "Probe a small matrix of official Ukrstat observation combinations.",
                    "query_dimension_order": query_order,
                    "sdmx_key": "",
                    "indicator_code": "",
                    "indicator_name": "",
                    "region_code": "",
                    "region_name": "",
                    "nace_code": "",
                    "nace_name": "",
                    "freq_code": "",
                    "freq_name": "",
                    "time_period": "",
                    "url": "",
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "observation_value_count": 0,
                    "has_observations": False,
                    "response_preview": "Observation query candidates unavailable. Matrix probe not executed.",
                    "notes": "Do not use Ukrstat observations in scoring until a valid observation value is confirmed and validated.",
                }
            ],
            columns=columns,
        )
        out.to_csv(UKRSTAT_OBSERVATION_MATRIX_PROBE_TABLE, index=False)
        return out

    candidates = observation_query_candidates.copy()
    for col in required_cols:
        candidates[col] = candidates[col].fillna("").astype(str)

    candidates = candidates[
        candidates["candidate_query_status"].str.contains(
            "shortlist_pending_review",
            case=False,
            na=False,
        )
    ].copy()

    def code_lookup(dimension_id: str) -> dict[str, str]:
        subset = candidates[candidates["dimension_id"] == dimension_id].copy()
        if subset.empty:
            return {}
        return {
            str(row.get("code_id", "")): str(row.get("code_name", ""))
            for _, row in subset.iterrows()
            if str(row.get("code_id", ""))
        }

    indicator_names = code_lookup("INDICATOR")
    region_names = code_lookup("REGION")
    nace_names = code_lookup("NACE")
    freq_names = code_lookup("FREQ")

    indicator_codes = [
        code for code in ["GRP", "GVA", "OUTPUT", "GRP_CAP"] if code in indicator_names
    ]
    if not indicator_codes:
        indicator_codes = list(indicator_names.keys())[:4]

    region_codes = [
        code
        for code in [
            "UA12000000000090473",  # Dnipropetrovska
            "UA32000000000030281",  # Kyivska
            "UA80000000000093317",  # Kyiv
        ]
        if code in region_names
    ]
    if not region_codes:
        region_codes = list(region_names.keys())[:3]

    availability_nace_codes = _availability_codes_for_dimension(
        availability_value_candidates,
        "NACE",
        ["_Z", "_T", "TOTAL"],
        max_values=3,
    )
    nace_codes = [code for code in availability_nace_codes if code]
    if not nace_codes:
        nace_codes = [code for code in ["_Z", "_T", "TOTAL"] if code in nace_names]
    if not nace_codes:
        nace_codes = list(nace_names.keys())[:1]

    availability_freq_codes = _availability_codes_for_dimension(
        availability_value_candidates,
        "FREQ",
        ["A", "Y", "ANNUAL"],
        max_values=2,
    )
    freq_codes = [code for code in availability_freq_codes if code]
    if not freq_codes:
        freq_codes = [code for code in ["A", "Y", "ANNUAL"] if code in freq_names]
    if not freq_codes:
        freq_codes = list(freq_names.keys())[:1]

    availability_time_periods = _availability_codes_for_dimension(
        availability_value_candidates,
        "TIME_PERIOD",
        ["2021-01-01", "2022-01-01", "2021", "2022", "2023"],
        max_values=5,
    )
    time_periods = availability_time_periods if availability_time_periods else [
        "2021-01-01",
        "2022-01-01",
        "2021",
        "2022",
        "2023",
    ]

    official_sdmx_3_data = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/3.0/data"
    )

    rows: list[dict] = []
    saved_observation_response = False

    for indicator_code in indicator_codes:
        for region_code in region_codes:
            for nace_code in nace_codes[:1]:
                for freq_code in freq_codes[:1]:
                    series_key = ".".join(
                        [indicator_code, region_code, nace_code, freq_code]
                    )
                    for time_period in time_periods:
                        url = (
                            f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                            f"/{series_key}?c[TIME_PERIOD]={time_period}"
                            "&dimensionAtObservation=TIME_PERIOD"
                        )

                        try:
                            response = requests.get(
                                url,
                                timeout=45,
                                headers={
                                    "User-Agent": "WARIS research prototype",
                                    "Accept": (
                                        "application/vnd.sdmx.data+json;version=2.0.0, "
                                        "application/vnd.sdmx.data+json;version=1.0.0, "
                                        "application/json, text/csv, */*"
                                    ),
                                },
                            )

                            content_type = response.headers.get("Content-Type", "")
                            text_preview = response.text[:750].replace("\n", " ").replace("\r", " ")
                            first_json_keys = ""
                            observation_value_count = 0

                            try:
                                payload = response.json()
                                if isinstance(payload, dict):
                                    first_json_keys = "; ".join(list(payload.keys())[:20])
                                    observation_value_count = _count_sdmx_observation_values(payload)
                            except Exception:
                                payload = None

                            success_status = 200 <= response.status_code < 300
                            has_observations = observation_value_count > 0

                            if (
                                success_status
                                and has_observations
                                and not saved_observation_response
                            ):
                                UKRSTAT_OBSERVATION_MATRIX_SUCCESS_RAW.write_text(
                                    response.text,
                                    encoding="utf-8",
                                    errors="ignore",
                                )
                                saved_observation_response = True

                            rows.append(
                                {
                                    "probe_name": "official_v3_observation_matrix_series_time_filter",
                                    "purpose": "Probe nearby official regional-account combinations for actual observation values.",
                                    "query_dimension_order": query_order,
                                    "sdmx_key": series_key,
                                    "indicator_code": indicator_code,
                                    "indicator_name": indicator_names.get(indicator_code, ""),
                                    "region_code": region_code,
                                    "region_name": region_names.get(region_code, ""),
                                    "nace_code": nace_code,
                                    "nace_name": nace_names.get(nace_code, ""),
                                    "freq_code": freq_code,
                                    "freq_name": freq_names.get(freq_code, ""),
                                    "time_period": time_period,
                                    "url": url,
                                    "http_status": response.status_code,
                                    "success_status": success_status,
                                    "content_type": content_type,
                                    "first_json_keys": first_json_keys,
                                    "observation_value_count": observation_value_count,
                                    "has_observations": has_observations,
                                    "response_preview": text_preview,
                                    "notes": (
                                        "Observation-matrix probe only. Do not blend into WARIS scoring until "
                                        "the returned value, units, geography mapping, NACE mapping, and time "
                                        "period are manually validated."
                                    ),
                                }
                            )

                        except Exception as exc:
                            rows.append(
                                {
                                    "probe_name": "official_v3_observation_matrix_series_time_filter",
                                    "purpose": "Probe nearby official regional-account combinations for actual observation values.",
                                    "query_dimension_order": query_order,
                                    "sdmx_key": series_key,
                                    "indicator_code": indicator_code,
                                    "indicator_name": indicator_names.get(indicator_code, ""),
                                    "region_code": region_code,
                                    "region_name": region_names.get(region_code, ""),
                                    "nace_code": nace_code,
                                    "nace_name": nace_names.get(nace_code, ""),
                                    "freq_code": freq_code,
                                    "freq_name": freq_names.get(freq_code, ""),
                                    "time_period": time_period,
                                    "url": url,
                                    "http_status": "",
                                    "success_status": False,
                                    "content_type": "",
                                    "first_json_keys": "",
                                    "observation_value_count": 0,
                                    "has_observations": False,
                                    "response_preview": f"Request failed: {exc}",
                                    "notes": (
                                        "Observation-matrix probe only. Do not blend into WARIS scoring until "
                                        "the returned value, units, geography mapping, NACE mapping, and time "
                                        "period are manually validated."
                                    ),
                                }
                            )

    if not rows:
        rows.append(
            {
                "probe_name": "observation_matrix_no_candidate_combinations",
                "purpose": "Probe a small matrix of official Ukrstat observation combinations.",
                "query_dimension_order": query_order,
                "sdmx_key": "",
                "indicator_code": "",
                "indicator_name": "",
                "region_code": "",
                "region_name": "",
                "nace_code": "",
                "nace_name": "",
                "freq_code": "",
                "freq_name": "",
                "time_period": "",
                "url": "",
                "http_status": "",
                "success_status": False,
                "content_type": "",
                "first_json_keys": "",
                "observation_value_count": 0,
                "has_observations": False,
                "response_preview": "No complete matrix combinations were available from the observation query shortlist.",
                "notes": "Do not use Ukrstat observations in scoring until a valid observation value is confirmed and validated.",
            }
        )

    out = pd.DataFrame(rows, columns=columns)
    out.to_csv(UKRSTAT_OBSERVATION_MATRIX_PROBE_TABLE, index=False)

    return out


def _count_availability_values(payload: Any) -> int:
    """Count likely available dimension values in an SDMX availability response.

    Availability payloads can vary by SDMX implementation. This helper is
    intentionally broad: it counts likely value/code records inside data or
    structure sections without treating the count as a validated observation.
    """
    if not isinstance(payload, dict):
        return 0

    count = 0

    def walk(value: Any, path: str = "") -> None:
        nonlocal count

        if isinstance(value, dict):
            keys = {str(key) for key in value.keys()}
            lower_path = path.lower()

            has_code_identity = bool(
                value.get("id")
                or value.get("code")
                or value.get("value")
                or value.get("name")
                or value.get("names")
            )

            looks_like_availability_value = (
                has_code_identity
                and (
                    "available" in lower_path
                    or "availability" in lower_path
                    or "values" in lower_path
                    or "codelists" in lower_path
                    or "codes" in lower_path
                    or "dimensions" in lower_path
                )
            )

            if looks_like_availability_value:
                count += 1

            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                walk(child, child_path)

        elif isinstance(value, list):
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]"
                walk(child, child_path)

    walk(payload)
    return count


def probe_availability_discovery(
    observation_query_candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Use SDMX v3 availability mode=available to discover valid query values.

    The fixed observation matrix can return HTTP 200 with an empty SDMX data
    shell when a selected full series has no observations. This function steps
    back and asks the official availability endpoint which values are available
    around a smaller set of filters.

    This is still non-operational. It only writes discovery metadata and saves
    the first successful availability payload for manual review. It does not
    blend Ukrstat values into WARIS scoring.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    query_order = "INDICATOR.REGION.NACE.FREQ.TIME_PERIOD"
    required_cols = {"dimension_id", "code_id", "code_name", "candidate_query_status"}

    columns = [
        "probe_name",
        "purpose",
        "availability_mode",
        "query_dimension_order",
        "sdmx_key",
        "indicator_code",
        "indicator_name",
        "region_code",
        "region_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "time_period",
        "dimension_filter_summary",
        "url",
        "http_status",
        "success_status",
        "content_type",
        "first_json_keys",
        "availability_value_count",
        "has_availability_values",
        "response_preview",
        "notes",
    ]

    if (
        observation_query_candidates is None
        or observation_query_candidates.empty
        or not required_cols.issubset(set(observation_query_candidates.columns))
    ):
        out = pd.DataFrame(
            [
                {
                    "probe_name": "availability_discovery_unavailable",
                    "purpose": "Discover valid Ukrstat SDMX values before observation pulls.",
                    "availability_mode": "available",
                    "query_dimension_order": query_order,
                    "sdmx_key": "",
                    "indicator_code": "",
                    "indicator_name": "",
                    "region_code": "",
                    "region_name": "",
                    "nace_code": "",
                    "nace_name": "",
                    "freq_code": "",
                    "freq_name": "",
                    "time_period": "",
                    "dimension_filter_summary": "",
                    "url": "",
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "availability_value_count": 0,
                    "has_availability_values": False,
                    "response_preview": "Observation query candidates unavailable. Availability discovery not executed.",
                    "notes": "Do not use Ukrstat observations in scoring until availability and data responses are validated.",
                }
            ],
            columns=columns,
        )
        out.to_csv(UKRSTAT_AVAILABILITY_DISCOVERY_TABLE, index=False)
        return out

    candidates = observation_query_candidates.copy()
    for col in required_cols:
        candidates[col] = candidates[col].fillna("").astype(str)

    candidates = candidates[
        candidates["candidate_query_status"].str.contains(
            "shortlist_pending_review",
            case=False,
            na=False,
        )
    ].copy()

    def choose_code(dimension_id: str, preferred_codes: list[str]) -> tuple[str, str]:
        subset = candidates[candidates["dimension_id"] == dimension_id].copy()
        if subset.empty:
            return "", ""

        for preferred in preferred_codes:
            matched = subset[subset["code_id"].astype(str) == preferred]
            if not matched.empty:
                row = matched.iloc[0]
                return str(row.get("code_id", "")), str(row.get("code_name", ""))

        row = subset.iloc[0]
        return str(row.get("code_id", "")), str(row.get("code_name", ""))

    indicator_code, indicator_name = choose_code(
        "INDICATOR",
        ["GRP", "GVA", "OUTPUT", "GRP_CAP"],
    )
    region_code, region_name = choose_code(
        "REGION",
        [
            "UA12000000000090473",  # Dnipropetrovska
            "UA32000000000030281",  # Kyivska
            "UA80000000000093317",  # Kyiv
        ],
    )
    nace_code, nace_name = choose_code("NACE", ["_T", "TOTAL", "A", "C", "G", "K"])
    freq_code, freq_name = choose_code("FREQ", ["A", "Y", "ANNUAL"])
    time_period, _ = choose_code("TIME_PERIOD", ["2021", "2022", "2023"])

    if not time_period:
        time_period = "2021"

    official_sdmx_3_availability = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/3.0/availability"
    )

    # Build conservative availability-discovery probes. These intentionally use
    # fewer fixed dimensions than the observation matrix so Ukrstat can report
    # valid future selections in mode=available before we ask for data.
    route_patterns = []

    if indicator_code and freq_code:
        route_patterns.append(
            {
                "probe_name": "availability_available_indicator_freq_wildcard_nace_region",
                "sdmx_key": f"{indicator_code}.*.*.{freq_code}",
                "dimension_filter_summary": f"INDICATOR={indicator_code}; FREQ={freq_code}",
                "url": (
                    f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/~"
                    f"/{indicator_code}.*.*.{freq_code}/all?mode=available&references=all"
                ),
                "purpose": "Discover available REGION/NACE/TIME_PERIOD values for selected indicator and annual frequency.",
            }
        )

    if region_code and freq_code:
        route_patterns.append(
            {
                "probe_name": "availability_available_region_freq_filter",
                "sdmx_key": f"*.*.*.{freq_code}",
                "dimension_filter_summary": f"REGION={region_code}; FREQ={freq_code}",
                "url": (
                    f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/~"
                    f"/*.*.*.{freq_code}/all?mode=available&references=all"
                    f"&c[REGION]={region_code}"
                ),
                "purpose": "Discover available indicators/NACE/time periods for selected region and annual frequency.",
            }
        )

    if time_period and freq_code:
        route_patterns.append(
            {
                "probe_name": "availability_available_time_freq_filter",
                "sdmx_key": f"*.*.*.{freq_code}",
                "dimension_filter_summary": f"TIME_PERIOD={time_period}; FREQ={freq_code}",
                "url": (
                    f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/~"
                    f"/*.*.*.{freq_code}/all?mode=available&references=all"
                    f"&c[TIME_PERIOD]={time_period}"
                ),
                "purpose": "Discover available indicator/region/NACE values for selected time period and annual frequency.",
            }
        )

    if indicator_code and region_code and freq_code:
        route_patterns.append(
            {
                "probe_name": "availability_available_indicator_region_freq_filter",
                "sdmx_key": f"{indicator_code}.{region_code}.*.{freq_code}",
                "dimension_filter_summary": f"INDICATOR={indicator_code}; REGION={region_code}; FREQ={freq_code}",
                "url": (
                    f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/~"
                    f"/{indicator_code}.{region_code}.*.{freq_code}/all?mode=available&references=all"
                ),
                "purpose": "Discover available NACE/time-period values for selected indicator, region, and frequency.",
            }
        )

    if indicator_code and region_code and freq_code and time_period:
        route_patterns.append(
            {
                "probe_name": "availability_available_indicator_region_time_freq_filter",
                "sdmx_key": f"{indicator_code}.{region_code}.*.{freq_code}",
                "dimension_filter_summary": f"INDICATOR={indicator_code}; REGION={region_code}; FREQ={freq_code}; TIME_PERIOD={time_period}",
                "url": (
                    f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/~"
                    f"/{indicator_code}.{region_code}.*.{freq_code}/all?mode=available&references=all"
                    f"&c[TIME_PERIOD]={time_period}"
                ),
                "purpose": "Discover available NACE values when time period is filtered instead of fixed in the key.",
            }
        )

    # Compare with exact mode for the broadest useful key. This documents the
    # difference between discovery mode and direct data-query equivalence.
    if indicator_code and region_code and freq_code:
        route_patterns.append(
            {
                "probe_name": "availability_exact_indicator_region_freq_filter",
                "sdmx_key": f"{indicator_code}.{region_code}.*.{freq_code}",
                "dimension_filter_summary": f"INDICATOR={indicator_code}; REGION={region_code}; FREQ={freq_code}",
                "url": (
                    f"{official_sdmx_3_availability}/dataflow/SSSU/{DATAFLOW_ID}/~"
                    f"/{indicator_code}.{region_code}.*.{freq_code}/all?mode=exact&references=all"
                ),
                "purpose": "Compare exact availability with mode=available for the same broad key.",
            }
        )

    rows: list[dict] = []
    saved_availability_response = False

    for route in route_patterns:
        url = route["url"]
        try:
            response = requests.get(
                url,
                timeout=45,
                headers={
                    "User-Agent": "WARIS research prototype",
                    "Accept": (
                        "application/vnd.sdmx.structure+json;version=2.0.0, "
                        "application/vnd.sdmx.data+json;version=2.0.0, "
                        "application/json, text/csv, */*"
                    ),
                },
            )

            content_type = response.headers.get("Content-Type", "")
            text_preview = response.text[:750].replace("\n", " ").replace("\r", " ")
            first_json_keys = ""
            availability_value_count = 0

            try:
                payload = response.json()
                if isinstance(payload, dict):
                    first_json_keys = "; ".join(list(payload.keys())[:20])
                    availability_value_count = _count_availability_values(payload)
            except Exception:
                payload = None

            success_status = 200 <= response.status_code < 300
            has_availability_values = success_status and availability_value_count > 0

            if success_status and not saved_availability_response:
                UKRSTAT_AVAILABILITY_DISCOVERY_RAW.write_text(
                    response.text,
                    encoding="utf-8",
                    errors="ignore",
                )
                saved_availability_response = True

            rows.append(
                {
                    "probe_name": route["probe_name"],
                    "purpose": route["purpose"],
                    "availability_mode": "available" if "mode=available" in url else "exact",
                    "query_dimension_order": query_order,
                    "sdmx_key": route["sdmx_key"],
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": region_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "time_period": time_period,
                    "dimension_filter_summary": route["dimension_filter_summary"],
                    "url": url,
                    "http_status": response.status_code,
                    "success_status": success_status,
                    "content_type": content_type,
                    "first_json_keys": first_json_keys,
                    "availability_value_count": availability_value_count,
                    "has_availability_values": has_availability_values,
                    "response_preview": text_preview,
                    "notes": (
                        "Availability-discovery probe only. Use results to identify "
                        "valid SDMX values before requesting data. Do not blend into "
                        "WARIS scoring until a data response with observations is "
                        "parsed and validated."
                    ),
                }
            )

        except Exception as exc:
            rows.append(
                {
                    "probe_name": route["probe_name"],
                    "purpose": route["purpose"],
                    "availability_mode": "available" if "mode=available" in url else "exact",
                    "query_dimension_order": query_order,
                    "sdmx_key": route["sdmx_key"],
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": region_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "time_period": time_period,
                    "dimension_filter_summary": route["dimension_filter_summary"],
                    "url": url,
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "availability_value_count": 0,
                    "has_availability_values": False,
                    "response_preview": f"Request failed: {exc}",
                    "notes": (
                        "Availability-discovery probe failed. Do not blend into "
                        "WARIS scoring."
                    ),
                }
            )

    if not rows:
        rows.append(
            {
                "probe_name": "availability_discovery_missing_key_parts",
                "purpose": "Discover valid Ukrstat SDMX values before observation pulls.",
                "availability_mode": "available",
                "query_dimension_order": query_order,
                "sdmx_key": "",
                "indicator_code": indicator_code,
                "indicator_name": indicator_name,
                "region_code": region_code,
                "region_name": region_name,
                "nace_code": nace_code,
                "nace_name": nace_name,
                "freq_code": freq_code,
                "freq_name": freq_name,
                "time_period": time_period,
                "dimension_filter_summary": "Missing one or more required seed values.",
                "url": "",
                "http_status": "",
                "success_status": False,
                "content_type": "",
                "first_json_keys": "",
                "availability_value_count": 0,
                "has_availability_values": False,
                "response_preview": "Not enough seed values to build availability-discovery probes.",
                "notes": "Review observation-query candidates before probing availability.",
            }
        )

    out = pd.DataFrame(rows, columns=columns)
    out.to_csv(UKRSTAT_AVAILABILITY_DISCOVERY_TABLE, index=False)

    return out


def parse_availability_discovery_values(
    availability_discovery_results: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Parse saved SDMX availability response into candidate dimension values.

    The availability-discovery probe can confirm that official series exist
    without returning observation values. This parser turns the saved SDMX
    availability response into an analyst-review table of values found inside
    data constraints, especially NACE and TIME_PERIOD candidates.

    This artifact is not a scoring input. It only helps choose valid SDMX values
    for a later official data pull.
    """
    ensure_dirs([TABLE_DIR])

    columns = [
        "source_probe",
        "availability_mode",
        "dimension_id",
        "value_code",
        "value_name",
        "value_description",
        "include_status",
        "component_path",
        "series_count",
        "time_period_start",
        "time_period_end",
        "candidate_role",
        "query_use_status",
        "current_use_in_scoring",
        "validation_status",
        "notes",
    ]

    if not UKRSTAT_AVAILABILITY_DISCOVERY_RAW.exists():
        out = pd.DataFrame(
            [
                {
                    "source_probe": "",
                    "availability_mode": "",
                    "dimension_id": "",
                    "value_code": "",
                    "value_name": "",
                    "value_description": "",
                    "include_status": "",
                    "component_path": "",
                    "series_count": "",
                    "time_period_start": "",
                    "time_period_end": "",
                    "candidate_role": "",
                    "query_use_status": "availability_response_unavailable",
                    "current_use_in_scoring": "not_yet_used",
                    "validation_status": "not_parsed",
                    "notes": (
                        "No saved availability response was found. Run availability "
                        "discovery before building value candidates."
                    ),
                }
            ],
            columns=columns,
        )
        out.to_csv(UKRSTAT_AVAILABILITY_VALUE_CANDIDATES_TABLE, index=False)
        return out

    try:
        payload = json.loads(
            UKRSTAT_AVAILABILITY_DISCOVERY_RAW.read_text(encoding="utf-8")
        )
    except Exception as exc:
        out = pd.DataFrame(
            [
                {
                    "source_probe": "",
                    "availability_mode": "",
                    "dimension_id": "",
                    "value_code": "",
                    "value_name": "",
                    "value_description": "",
                    "include_status": "",
                    "component_path": "",
                    "series_count": "",
                    "time_period_start": "",
                    "time_period_end": "",
                    "candidate_role": "",
                    "query_use_status": "availability_response_unreadable",
                    "current_use_in_scoring": "not_yet_used",
                    "validation_status": "parse_failed",
                    "notes": f"Could not parse saved availability response JSON: {exc}",
                }
            ],
            columns=columns,
        )
        out.to_csv(UKRSTAT_AVAILABILITY_VALUE_CANDIDATES_TABLE, index=False)
        return out

    source_probe = ""
    availability_mode = ""

    if (
        availability_discovery_results is not None
        and not availability_discovery_results.empty
    ):
        working = availability_discovery_results.copy()

        if "has_availability_values" in working.columns:
            positive = working[
                working["has_availability_values"]
                .astype(str)
                .str.lower()
                .eq("true")
            ].copy()
        else:
            positive = pd.DataFrame()

        if positive.empty:
            positive = working

        if not positive.empty:
            source_probe = str(positive.iloc[0].get("probe_name", ""))
            availability_mode = str(positive.iloc[0].get("availability_mode", ""))

    rows: list[dict] = []

    def annotation_value(annotations: list, annotation_id: str) -> str:
        for annotation in annotations:
            if not isinstance(annotation, dict):
                continue

            if str(annotation.get("id", "")) == annotation_id:
                return str(
                    annotation.get(
                        "title",
                        annotation.get("value", annotation.get("text", "")),
                    )
                )

        return ""

    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    constraints = data.get("dataConstraints", [])

    if not isinstance(constraints, list):
        constraints = []

    def extract_component_values(
        component: dict,
        constraint_index: int,
        cube_index: int,
        component_index: int,
        series_count: str,
        time_period_start: str,
        time_period_end: str,
    ) -> None:
        dimension_id = str(component.get("id", ""))
        include_status = str(component.get("include", ""))

        value_sets: list[tuple[str, Any]] = []
        for key in ["values", "codes", "members"]:
            value = component.get(key)
            if isinstance(value, list):
                value_sets.append((key, value))

        # Some SDMX responses store values under nested member/valueSelection
        # objects. This small recursive pass keeps the parser flexible without
        # assuming one exact Ukrstat serialization.
        def collect_nested_values(value: Any, path: str = "") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    child_path = f"{path}.{key}" if path else str(key)
                    if key in {"values", "codes", "members"} and isinstance(child, list):
                        value_sets.append((child_path, child))
                    collect_nested_values(child, child_path)
            elif isinstance(value, list):
                for idx, child in enumerate(value):
                    collect_nested_values(child, f"{path}[{idx}]")

        collect_nested_values(component)

        seen = set()

        for value_key, values in value_sets:
            for value_index, item in enumerate(values):
                if isinstance(item, dict):
                    value_code = str(
                        item.get(
                            "value",
                            item.get("id", item.get("code", item.get("name", ""))),
                        )
                    )
                    value_name = _extract_name(item.get("name", item.get("names", "")))
                    value_description = _extract_name(
                        item.get("description", item.get("descriptions", ""))
                    )
                else:
                    value_code = str(item)
                    value_name = ""
                    value_description = ""

                dedupe_key = (dimension_id, value_code, value_key, value_index)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                candidate_role = "availability_dimension_value"

                if dimension_id == "NACE":
                    candidate_role = "availability_nace_candidate"
                elif dimension_id == "TIME_PERIOD":
                    candidate_role = "availability_time_period_candidate"
                elif dimension_id == "INDICATOR":
                    candidate_role = "availability_indicator_candidate"
                elif dimension_id == "REGION":
                    candidate_role = "availability_region_candidate"
                elif dimension_id == "FREQ":
                    candidate_role = "availability_frequency_candidate"

                rows.append(
                    {
                        "source_probe": source_probe,
                        "availability_mode": availability_mode,
                        "dimension_id": dimension_id,
                        "value_code": value_code,
                        "value_name": value_name,
                        "value_description": value_description,
                        "include_status": include_status,
                        "component_path": (
                            f"data.dataConstraints[{constraint_index}]."
                            f"cubeRegions[{cube_index}].components[{component_index}]."
                            f"{value_key}[{value_index}]"
                        ),
                        "series_count": series_count,
                        "time_period_start": time_period_start,
                        "time_period_end": time_period_end,
                        "candidate_role": candidate_role,
                        "query_use_status": "availability_candidate_pending_validation",
                        "current_use_in_scoring": "not_yet_used",
                        "validation_status": "parsed_pending_validation",
                        "notes": (
                            "Candidate parsed from official SDMX availability response. "
                            "Use this to choose valid observation-query values. Do not "
                            "blend into WARIS scoring until a data response with "
                            "OBS_VALUE, units, geography, NACE, and time-period mapping "
                            "is validated."
                        ),
                    }
                )

    for constraint_index, constraint in enumerate(constraints):
        if not isinstance(constraint, dict):
            continue

        annotations = constraint.get("annotations", [])
        if not isinstance(annotations, list):
            annotations = []

        series_count = annotation_value(annotations, "series_count")
        time_period_start = annotation_value(annotations, "time_period_start")
        time_period_end = annotation_value(annotations, "time_period_end")

        # Store explicit time range rows even when TIME_PERIOD values are not
        # enumerated as component values. This was the key clue in the latest
        # run: availability identified 2004-01-01 through 2022-01-01.
        for boundary_id, boundary_value in [
            ("TIME_PERIOD_START", time_period_start),
            ("TIME_PERIOD_END", time_period_end),
        ]:
            if boundary_value:
                rows.append(
                    {
                        "source_probe": source_probe,
                        "availability_mode": availability_mode,
                        "dimension_id": "TIME_PERIOD",
                        "value_code": boundary_value,
                        "value_name": boundary_value,
                        "value_description": boundary_id,
                        "include_status": "availability_annotation",
                        "component_path": (
                            f"data.dataConstraints[{constraint_index}]."
                            f"annotations[{boundary_id}]"
                        ),
                        "series_count": series_count,
                        "time_period_start": time_period_start,
                        "time_period_end": time_period_end,
                        "candidate_role": "availability_time_period_boundary",
                        "query_use_status": "availability_candidate_pending_validation",
                        "current_use_in_scoring": "not_yet_used",
                        "validation_status": "parsed_pending_validation",
                        "notes": (
                            "Time-period boundary parsed from official availability "
                            "annotations. Use full-date period formatting in the next "
                            "data-query test before any scoring blend."
                        ),
                    }
                )

        cube_regions = constraint.get("cubeRegions", [])
        if not isinstance(cube_regions, list):
            cube_regions = []

        for cube_index, cube_region in enumerate(cube_regions):
            if not isinstance(cube_region, dict):
                continue

            components = cube_region.get("components", [])
            if not isinstance(components, list):
                components = []

            for component_index, component in enumerate(components):
                if not isinstance(component, dict):
                    continue

                extract_component_values(
                    component=component,
                    constraint_index=constraint_index,
                    cube_index=cube_index,
                    component_index=component_index,
                    series_count=series_count,
                    time_period_start=time_period_start,
                    time_period_end=time_period_end,
                )

    if not rows:
        rows.append(
            {
                "source_probe": source_probe,
                "availability_mode": availability_mode,
                "dimension_id": "",
                "value_code": "",
                "value_name": "",
                "value_description": "",
                "include_status": "",
                "component_path": "",
                "series_count": "",
                "time_period_start": "",
                "time_period_end": "",
                "candidate_role": "",
                "query_use_status": "no_availability_values_detected",
                "current_use_in_scoring": "not_yet_used",
                "validation_status": "parsed_no_values_detected",
                "notes": (
                    "Saved availability response was loaded, but this parser did not "
                    "detect candidate values. Inspect the raw availability JSON manually."
                ),
            }
        )

    out = pd.DataFrame(rows, columns=columns).drop_duplicates()

    dimension_order = {
        "INDICATOR": 0,
        "REGION": 1,
        "NACE": 2,
        "FREQ": 3,
        "TIME_PERIOD": 4,
    }
    role_order = {
        "availability_indicator_candidate": 0,
        "availability_region_candidate": 1,
        "availability_nace_candidate": 2,
        "availability_frequency_candidate": 3,
        "availability_time_period_candidate": 4,
        "availability_time_period_boundary": 5,
        "availability_dimension_value": 9,
    }

    out["_dimension_order"] = out["dimension_id"].map(dimension_order).fillna(99)
    out["_role_order"] = out["candidate_role"].map(role_order).fillna(99)
    out = out.sort_values(
        ["_dimension_order", "_role_order", "value_code"],
        ascending=[True, True, True],
    ).drop(columns=["_dimension_order", "_role_order"])

    out.to_csv(UKRSTAT_AVAILABILITY_VALUE_CANDIDATES_TABLE, index=False)

    return out


def probe_confirmed_series_without_time_filter(
    observation_query_candidates: pd.DataFrame,
    availability_value_candidates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Pull a confirmed available regional-account series without a time filter.

    Availability confirms that the GRP annual regional-account series exists for
    the selected oblast when the series key is INDICATOR.REGION.NACE.FREQ. This
    diagnostic removes the TIME_PERIOD filter and lets Ukrstat return whatever
    observation periods are available. It does not blend values into scoring.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    query_order = "INDICATOR.REGION.NACE.FREQ.TIME_PERIOD"
    required_cols = {"dimension_id", "code_id", "code_name", "candidate_query_status"}

    columns = [
        "probe_name",
        "purpose",
        "query_dimension_order",
        "sdmx_key",
        "indicator_code",
        "indicator_name",
        "region_code",
        "region_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "time_filter_strategy",
        "url",
        "http_status",
        "success_status",
        "content_type",
        "first_json_keys",
        "observation_value_count",
        "has_observations",
        "response_preview",
        "notes",
    ]

    if (
        observation_query_candidates is None
        or observation_query_candidates.empty
        or not required_cols.issubset(set(observation_query_candidates.columns))
    ):
        out = pd.DataFrame(
            [
                {
                    "probe_name": "confirmed_series_probe_unavailable",
                    "purpose": "Pull a confirmed series without TIME_PERIOD filtering.",
                    "query_dimension_order": query_order,
                    "sdmx_key": "",
                    "indicator_code": "",
                    "indicator_name": "",
                    "region_code": "",
                    "region_name": "",
                    "nace_code": "",
                    "nace_name": "",
                    "freq_code": "",
                    "freq_name": "",
                    "time_filter_strategy": "",
                    "url": "",
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "observation_value_count": 0,
                    "has_observations": False,
                    "response_preview": "Observation query candidates unavailable. Confirmed-series probe not executed.",
                    "notes": "Do not use Ukrstat observations in scoring until a valid observation value is confirmed and validated.",
                }
            ],
            columns=columns,
        )
        out.to_csv(UKRSTAT_CONFIRMED_SERIES_PROBE_TABLE, index=False)
        return out

    candidates = observation_query_candidates.copy()
    for col in required_cols:
        candidates[col] = candidates[col].fillna("").astype(str)

    candidates = candidates[
        candidates["candidate_query_status"].str.contains(
            "shortlist_pending_review",
            case=False,
            na=False,
        )
    ].copy()

    def choose_code(dimension_id: str, preferred_codes: list[str]) -> tuple[str, str]:
        subset = candidates[candidates["dimension_id"] == dimension_id].copy()
        if subset.empty:
            return "", ""

        for preferred in preferred_codes:
            matched = subset[subset["code_id"].astype(str) == preferred]
            if not matched.empty:
                row = matched.iloc[0]
                return str(row.get("code_id", "")), str(row.get("code_name", ""))

        row = subset.iloc[0]
        return str(row.get("code_id", "")), str(row.get("code_name", ""))

    indicator_code, indicator_name = choose_code(
        "INDICATOR",
        ["GRP", "GVA", "OUTPUT", "GRP_CAP"],
    )
    region_code, region_name = choose_code(
        "REGION",
        [
            "UA12000000000090473",
            "UA32000000000030281",
            "UA80000000000093317",
        ],
    )
    nace_code, nace_name = choose_code("NACE", ["_T", "TOTAL", "_Z"])
    freq_code, freq_name = choose_code("FREQ", ["A", "Y", "ANNUAL"])

    availability_nace = _availability_first_code(
        availability_value_candidates,
        "NACE",
        ["_Z", "_T", "TOTAL"],
    )
    if availability_nace:
        nace_code = availability_nace
        nace_name = "Availability-derived NACE candidate"

    availability_freq = _availability_first_code(
        availability_value_candidates,
        "FREQ",
        ["A", "Y", "ANNUAL"],
    )
    if availability_freq:
        freq_code = availability_freq
        freq_name = "Availability-derived frequency candidate"

    time_values = _availability_codes_for_dimension(
        availability_value_candidates,
        "TIME_PERIOD",
        ["2004-01-01", "2022-01-01", "2021-01-01"],
        max_values=10,
    )
    time_start = time_values[0] if time_values else ""
    time_end = time_values[-1] if len(time_values) > 1 else ""

    if not all([indicator_code, region_code, nace_code, freq_code]):
        out = pd.DataFrame(
            [
                {
                    "probe_name": "confirmed_series_probe_missing_key_parts",
                    "purpose": "Pull a confirmed series without TIME_PERIOD filtering.",
                    "query_dimension_order": query_order,
                    "sdmx_key": "",
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": region_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "time_filter_strategy": "",
                    "url": "",
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "observation_value_count": 0,
                    "has_observations": False,
                    "response_preview": "One or more required SDMX series-key parts were missing.",
                    "notes": "Do not execute or blend official observations until all series-key parts are selected and validated.",
                }
            ],
            columns=columns,
        )
        out.to_csv(UKRSTAT_CONFIRMED_SERIES_PROBE_TABLE, index=False)
        return out

    series_key = ".".join([indicator_code, region_code, nace_code, freq_code])

    official_sdmx_3_data = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/3.0/data"
    )

    candidate_urls = [
        {
            "probe_name": "confirmed_series_latest_no_time_filter",
            "time_filter_strategy": "no_time_filter",
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/{series_key}?dimensionAtObservation=TIME_PERIOD"
            ),
        },
        {
            "probe_name": "confirmed_series_v8_no_time_filter",
            "time_filter_strategy": "no_time_filter_v8",
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/8.0.0"
                f"/{series_key}?dimensionAtObservation=TIME_PERIOD"
            ),
        },
        {
            "probe_name": "confirmed_series_latest_all_key_no_time_filter",
            "time_filter_strategy": "all_key_no_time_filter",
            "url": (
                f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                f"/*?c[INDICATOR]={indicator_code}&c[REGION]={region_code}"
                f"&c[NACE]={nace_code}&c[FREQ]={freq_code}"
                "&dimensionAtObservation=TIME_PERIOD"
            ),
        },
    ]

    if time_start and time_end:
        candidate_urls.append(
            {
                "probe_name": "confirmed_series_latest_availability_range",
                "time_filter_strategy": "availability_start_end",
                "url": (
                    f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
                    f"/{series_key}?startPeriod={time_start}&endPeriod={time_end}"
                    "&dimensionAtObservation=TIME_PERIOD"
                ),
            }
        )

    rows: list[dict] = []
    saved_response = False

    for candidate in candidate_urls:
        url = candidate["url"]
        try:
            response = requests.get(
                url,
                timeout=45,
                headers={
                    "User-Agent": "WARIS research prototype",
                    "Accept": (
                        "application/vnd.sdmx.data+json;version=2.0.0, "
                        "application/vnd.sdmx.data+json;version=1.0.0, "
                        "application/json, text/csv, */*"
                    ),
                },
            )

            content_type = response.headers.get("Content-Type", "")
            text_preview = response.text[:750].replace("\n", " ").replace("\r", " ")
            first_json_keys = ""
            observation_value_count = 0

            try:
                payload = response.json()
                if isinstance(payload, dict):
                    first_json_keys = "; ".join(list(payload.keys())[:20])
                    observation_value_count = _count_sdmx_observation_values(payload)
            except Exception:
                payload = None

            success_status = 200 <= response.status_code < 300
            has_observations = observation_value_count > 0

            if success_status and not saved_response:
                UKRSTAT_CONFIRMED_SERIES_RAW.write_text(
                    response.text,
                    encoding="utf-8",
                    errors="ignore",
                )
                saved_response = True

            if success_status and has_observations:
                UKRSTAT_CONFIRMED_SERIES_RAW.write_text(
                    response.text,
                    encoding="utf-8",
                    errors="ignore",
                )

            rows.append(
                {
                    "probe_name": candidate["probe_name"],
                    "purpose": "Pull confirmed available series without selecting one TIME_PERIOD.",
                    "query_dimension_order": query_order,
                    "sdmx_key": series_key,
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": region_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "time_filter_strategy": candidate["time_filter_strategy"],
                    "url": url,
                    "http_status": response.status_code,
                    "success_status": success_status,
                    "content_type": content_type,
                    "first_json_keys": first_json_keys,
                    "observation_value_count": observation_value_count,
                    "has_observations": has_observations,
                    "response_preview": text_preview,
                    "notes": (
                        "Confirmed-series probe only. Do not blend into WARIS scoring "
                        "until returned values, units, geography mapping, NACE mapping, "
                        "and time-period coverage are manually validated."
                    ),
                }
            )

        except Exception as exc:
            rows.append(
                {
                    "probe_name": candidate["probe_name"],
                    "purpose": "Pull confirmed available series without selecting one TIME_PERIOD.",
                    "query_dimension_order": query_order,
                    "sdmx_key": series_key,
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": region_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "time_filter_strategy": candidate["time_filter_strategy"],
                    "url": url,
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "first_json_keys": "",
                    "observation_value_count": 0,
                    "has_observations": False,
                    "response_preview": f"Request failed: {exc}",
                    "notes": (
                        "Confirmed-series probe only. Do not blend into WARIS scoring "
                        "until returned values, units, geography mapping, NACE mapping, "
                        "and time-period coverage are manually validated."
                    ),
                }
            )

    out = pd.DataFrame(rows, columns=columns)
    out.to_csv(UKRSTAT_CONFIRMED_SERIES_PROBE_TABLE, index=False)

    return out


def parse_confirmed_series_response(
    confirmed_series_probe_results: pd.DataFrame | None = None,
    availability_value_candidates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Parse the saved confirmed-series response into observation review rows.

    The confirmed-series probe now returns real OBS_VALUE records, but compact
    SDMX JSON can encode TIME_PERIOD labels in several places depending on the
    response shape. This parser first tries to extract TIME_PERIOD values from
    the SDMX structure. If those labels are not explicit, it falls back to the
    official availability boundaries and maps observation indexes to annual
    period labels.

    Parsed values remain validation artifacts only. They are not used in WARIS
    scoring.
    """
    ensure_dirs([TABLE_DIR, RAW_DIR])

    columns = [
        "indicator_code",
        "indicator_name",
        "region_code",
        "region_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "time_period",
        "obs_value",
        "unit",
        "updated",
        "source_url",
        "source_status",
        "validation_status",
        "current_use_in_scoring",
        "notes",
    ]

    source_row = {}
    if confirmed_series_probe_results is not None and not confirmed_series_probe_results.empty:
        working = confirmed_series_probe_results.copy()

        if "has_observations" in working.columns:
            positive = working[
                working["has_observations"].astype(str).str.lower().eq("true")
            ].copy()
        else:
            positive = pd.DataFrame()

        if positive.empty and "success_status" in working.columns:
            positive = working[
                working["success_status"].astype(str).str.lower().eq("true")
            ].copy()

        if positive.empty:
            positive = working

        if not positive.empty:
            source_row = positive.iloc[0].to_dict()

    def fallback_row(status: str, validation_status: str, notes: str) -> pd.DataFrame:
        out = pd.DataFrame(
            [
                {
                    "indicator_code": source_row.get("indicator_code", ""),
                    "indicator_name": source_row.get("indicator_name", ""),
                    "region_code": source_row.get("region_code", ""),
                    "region_name": source_row.get("region_name", ""),
                    "nace_code": source_row.get("nace_code", ""),
                    "nace_name": source_row.get("nace_name", ""),
                    "freq_code": source_row.get("freq_code", ""),
                    "freq_name": source_row.get("freq_name", ""),
                    "time_period": "",
                    "obs_value": "",
                    "unit": "",
                    "updated": "",
                    "source_url": source_row.get("url", ""),
                    "source_status": status,
                    "validation_status": validation_status,
                    "current_use_in_scoring": "not_yet_used",
                    "notes": notes,
                }
            ],
            columns=columns,
        )
        out.to_csv(UKRSTAT_CONFIRMED_SERIES_PARSED_TABLE, index=False)
        return out

    if not UKRSTAT_CONFIRMED_SERIES_RAW.exists():
        return fallback_row(
            "confirmed_series_response_unavailable",
            "not_parsed",
            "No saved confirmed-series response was found.",
        )

    try:
        payload = json.loads(UKRSTAT_CONFIRMED_SERIES_RAW.read_text(encoding="utf-8"))
    except Exception as exc:
        return fallback_row(
            "confirmed_series_response_unreadable",
            "parse_failed",
            f"Could not parse confirmed-series response JSON: {exc}",
        )

    def observation_period_values(p: Any) -> list[str]:
        values: list[str] = []

        def extract_values_from_dimension(dim: dict) -> None:
            dim_id = str(dim.get("id", ""))
            if dim_id and dim_id.upper() != "TIME_PERIOD":
                return

            dim_values = dim.get("values", [])
            if not isinstance(dim_values, list):
                return

            for value in dim_values:
                if isinstance(value, dict):
                    code = str(value.get("id", value.get("name", "")))
                    if code:
                        values.append(code)
                elif value not in [None, ""]:
                    values.append(str(value))

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                if "dimensions" in value and isinstance(value.get("dimensions"), dict):
                    observation_dims = value["dimensions"].get("observation", [])
                    if isinstance(observation_dims, list):
                        for dim in observation_dims:
                            if isinstance(dim, dict):
                                extract_values_from_dimension(dim)

                if str(value.get("id", "")).upper() == "TIME_PERIOD":
                    extract_values_from_dimension(value)

                for child in value.values():
                    walk(child)

            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(p)
        return values

    periods = observation_period_values(payload)

    def availability_period_boundaries() -> tuple[str, str]:
        """Return start/end period boundaries from parsed availability candidates."""
        frame = availability_value_candidates

        if (
            frame is None
            or frame.empty
            or not {"dimension_id", "value_code", "candidate_role"}.issubset(
                set(frame.columns)
            )
        ):
            if UKRSTAT_AVAILABILITY_VALUE_CANDIDATES_TABLE.exists():
                try:
                    frame = pd.read_csv(UKRSTAT_AVAILABILITY_VALUE_CANDIDATES_TABLE)
                except Exception:
                    frame = pd.DataFrame()

        if frame is None or frame.empty:
            return "", ""

        working = frame.copy()
        for col in ["dimension_id", "value_code", "candidate_role", "value_description"]:
            if col not in working.columns:
                working[col] = ""
            working[col] = working[col].fillna("").astype(str)

        time_rows = working[working["dimension_id"].str.upper().eq("TIME_PERIOD")].copy()

        if time_rows.empty:
            return "", ""

        start_candidates = time_rows[
            time_rows["value_description"].str.upper().eq("TIME_PERIOD_START")
            | time_rows["candidate_role"].str.contains("boundary", case=False, na=False)
        ].copy()

        end_candidates = time_rows[
            time_rows["value_description"].str.upper().eq("TIME_PERIOD_END")
            | time_rows["candidate_role"].str.contains("boundary", case=False, na=False)
        ].copy()

        date_like = time_rows[
            time_rows["value_code"].str.match(r"^\d{4}(-\d{2}-\d{2})?$", na=False)
        ].copy()

        start_value = ""
        end_value = ""

        if not start_candidates.empty:
            starts = start_candidates[
                start_candidates["value_description"].str.upper().eq("TIME_PERIOD_START")
            ]
            if not starts.empty:
                start_value = str(starts.iloc[0].get("value_code", ""))
            else:
                start_value = str(start_candidates.iloc[0].get("value_code", ""))

        if not end_candidates.empty:
            ends = end_candidates[
                end_candidates["value_description"].str.upper().eq("TIME_PERIOD_END")
            ]
            if not ends.empty:
                end_value = str(ends.iloc[0].get("value_code", ""))
            else:
                end_value = str(end_candidates.iloc[-1].get("value_code", ""))

        if (not start_value or not end_value) and not date_like.empty:
            sorted_dates = sorted(date_like["value_code"].dropna().astype(str).unique())
            if sorted_dates:
                start_value = start_value or sorted_dates[0]
                end_value = end_value or sorted_dates[-1]

        return start_value, end_value

    def build_annual_periods_from_availability(count: int) -> list[str]:
        """Build annual period labels from official availability boundaries."""
        start_value, end_value = availability_period_boundaries()

        if not start_value:
            return []

        try:
            start_year = int(str(start_value)[:4])
        except Exception:
            return []

        end_year = None
        if end_value:
            try:
                end_year = int(str(end_value)[:4])
            except Exception:
                end_year = None

        generated = [f"{start_year + idx}-01-01" for idx in range(count)]

        # If the generated period count reaches beyond the availability end
        # boundary, keep the count from observed records but do not silently
        # fabricate a final period outside the official range.
        if end_year is not None:
            generated = [
                period
                for period in generated
                if int(period[:4]) <= end_year
            ]

            # If availability end is inclusive but the response has fewer values
            # than the full boundary range, keep the observed count. This preserves
            # the actual SDMX observation count while replacing index labels with
            # readable annual period labels.
            generated = generated[:count]

        return generated

    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    if not isinstance(data, dict):
        data = {}

    data_sets = data.get("dataSets", [])
    if not isinstance(data_sets, list):
        data_sets = []

    rows: list[dict] = []

    def count_observation_records() -> int:
        count = 0

        for dataset in data_sets:
            if not isinstance(dataset, dict):
                continue

            observations = dataset.get("observations", {})
            if isinstance(observations, dict):
                count += len(
                    [
                        obs_payload
                        for obs_payload in observations.values()
                        if value_from_obs_payload(obs_payload)
                    ]
                )

            series = dataset.get("series", {})
            if isinstance(series, dict):
                for series_payload in series.values():
                    if not isinstance(series_payload, dict):
                        continue

                    series_observations = series_payload.get("observations", {})
                    if isinstance(series_observations, dict):
                        count += len(
                            [
                                obs_payload
                                for obs_payload in series_observations.values()
                                if value_from_obs_payload(obs_payload)
                            ]
                        )

        return count

    def period_for_key(obs_key: str) -> str:
        first = str(obs_key).split(":")[0]
        try:
            idx = int(first)
            if 0 <= idx < len(periods):
                return periods[idx]
        except Exception:
            pass

        fallback_periods = build_annual_periods_from_availability(
            count_observation_records()
        )

        try:
            idx = int(first)
            if 0 <= idx < len(fallback_periods):
                return fallback_periods[idx]
        except Exception:
            pass

        return str(obs_key)

    def value_from_obs_payload(obs_payload: Any) -> str:
        if isinstance(obs_payload, list):
            if obs_payload:
                return "" if obs_payload[0] is None else str(obs_payload[0])
            return ""
        if isinstance(obs_payload, dict):
            for key in ["value", "obs_value", "OBS_VALUE"]:
                if key in obs_payload:
                    return "" if obs_payload[key] is None else str(obs_payload[key])
            return json.dumps(obs_payload, ensure_ascii=False)[:300]
        return "" if obs_payload is None else str(obs_payload)

    for dataset in data_sets:
        if not isinstance(dataset, dict):
            continue

        observations = dataset.get("observations", {})
        if isinstance(observations, dict):
            for obs_key, obs_payload in observations.items():
                obs_value = value_from_obs_payload(obs_payload)
                if obs_value:
                    rows.append(
                        {
                            "indicator_code": source_row.get("indicator_code", ""),
                            "indicator_name": source_row.get("indicator_name", ""),
                            "region_code": source_row.get("region_code", ""),
                            "region_name": source_row.get("region_name", ""),
                            "nace_code": source_row.get("nace_code", ""),
                            "nace_name": source_row.get("nace_name", ""),
                            "freq_code": source_row.get("freq_code", ""),
                            "freq_name": source_row.get("freq_name", ""),
                            "time_period": period_for_key(str(obs_key)),
                            "obs_value": obs_value,
                            "unit": "",
                            "updated": "",
                            "source_url": source_row.get("url", ""),
                            "source_status": "official_confirmed_series_response_loaded",
                            "validation_status": "parsed_pending_validation",
                            "current_use_in_scoring": "not_yet_used",
                            "notes": "Observation parsed from confirmed series response. TIME_PERIOD labels are mapped from SDMX structure when available, otherwise from official availability boundaries. Validate period, unit, geography, NACE, and meaning before any scoring blend.",
                        }
                    )

        series = dataset.get("series", {})
        if isinstance(series, dict):
            for series_key, series_payload in series.items():
                if not isinstance(series_payload, dict):
                    continue

                series_observations = series_payload.get("observations", {})
                if not isinstance(series_observations, dict):
                    continue

                for obs_key, obs_payload in series_observations.items():
                    obs_value = value_from_obs_payload(obs_payload)
                    if obs_value:
                        rows.append(
                            {
                                "indicator_code": source_row.get("indicator_code", ""),
                                "indicator_name": source_row.get("indicator_name", ""),
                                "region_code": source_row.get("region_code", ""),
                                "region_name": source_row.get("region_name", ""),
                                "nace_code": source_row.get("nace_code", ""),
                                "nace_name": source_row.get("nace_name", ""),
                                "freq_code": source_row.get("freq_code", ""),
                                "freq_name": source_row.get("freq_name", ""),
                                "time_period": period_for_key(str(obs_key)),
                                "obs_value": obs_value,
                                "unit": "",
                                "updated": "",
                                "source_url": source_row.get("url", ""),
                                "source_status": "official_confirmed_series_response_loaded",
                                "validation_status": "parsed_pending_validation",
                                "current_use_in_scoring": "not_yet_used",
                                "notes": "Observation parsed from confirmed series response. TIME_PERIOD labels are mapped from SDMX structure when available, otherwise from official availability boundaries. Validate period, unit, geography, NACE, and meaning before any scoring blend.",
                            }
                        )

    if not rows:
        return fallback_row(
            "official_confirmed_series_response_loaded",
            "parsed_no_observations_detected",
            "Saved confirmed-series SDMX response was loaded, but this parser did not detect observation values. Inspect the raw response before changing scoring logic.",
        )

    out = pd.DataFrame(rows, columns=columns).drop_duplicates()
    out.to_csv(UKRSTAT_CONFIRMED_SERIES_PARSED_TABLE, index=False)
    return out


def build_confirmed_oblast_baseline_candidates(
    confirmed_series_parsed: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Prepare validation-only official oblast baseline candidates.

    This function turns parsed official Ukrstat observations into a candidate
    replacement artifact for synthetic oblast baseline fields. It selects the
    latest parsed observation for each oblast/indicator/NACE/frequency series,
    but it does not blend the value into WARIS scoring.

    The artifact is intentionally conservative:
    - current_use_in_scoring stays not_yet_used
    - validation_status stays pending_unit_and_mapping_validation
    - source_status documents that the value came from an official SDMX response
    """
    ensure_dirs([TABLE_DIR])

    columns = [
        "oblast",
        "region_code",
        "indicator_code",
        "indicator_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "latest_period",
        "official_regional_baseline_proxy",
        "unit",
        "updated",
        "source_url",
        "source_status",
        "validation_status",
        "current_use_in_scoring",
        "approved_current_use",
        "prohibited_current_use",
        "production_score_change",
        "official_baseline_used_in_scoring",
        "official_baseline_used_in_monte_carlo",
        "source_separation_note",
        "operational_control_separation_note",
        "analyst_review_current_use",
        "analyst_review_production_score_change",
        "false_positive_controls_current_use",
        "false_positive_controls_production_score_change",
        "source_freshness_current_use",
        "source_freshness_production_score_change",
        "run_manifest_current_use",
        "run_manifest_production_score_change",
        "operational_controls_used_in_official_baseline_scoring",
        "control_note",
        "recommended_next_action",
        "notes",
    ]

    if confirmed_series_parsed is None or confirmed_series_parsed.empty:
        out = pd.DataFrame(
            [
                {
                    "oblast": "",
                    "region_code": "",
                    "indicator_code": "",
                    "indicator_name": "",
                    "nace_code": "",
                    "nace_name": "",
                    "freq_code": "",
                    "freq_name": "",
                    "latest_period": "",
                    "official_regional_baseline_proxy": "",
                    "unit": "",
                    "updated": "",
                    "source_url": "",
                    "source_status": "confirmed_series_parsed_unavailable",
                    "validation_status": "not_ready",
                    "current_use_in_scoring": "not_yet_used",
                    "recommended_next_action": (
                        "Parse a confirmed official SDMX observation response before "
                        "creating official baseline candidates."
                    ),
                    "notes": "No confirmed-series parsed observations were available.",
                }
            ],
            columns=columns,
        )
        out = _add_official_baseline_control_fields(out)
        out.to_csv(UKRSTAT_CONFIRMED_OBLAST_BASELINE_CANDIDATES_TABLE, index=False)
        return out

    required_cols = {
        "indicator_code",
        "indicator_name",
        "region_code",
        "region_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "time_period",
        "obs_value",
        "unit",
        "updated",
        "source_url",
        "source_status",
        "validation_status",
        "current_use_in_scoring",
    }

    if not required_cols.issubset(set(confirmed_series_parsed.columns)):
        out = pd.DataFrame(
            [
                {
                    "oblast": "",
                    "region_code": "",
                    "indicator_code": "",
                    "indicator_name": "",
                    "nace_code": "",
                    "nace_name": "",
                    "freq_code": "",
                    "freq_name": "",
                    "latest_period": "",
                    "official_regional_baseline_proxy": "",
                    "unit": "",
                    "updated": "",
                    "source_url": "",
                    "source_status": "confirmed_series_parsed_missing_columns",
                    "validation_status": "not_ready",
                    "current_use_in_scoring": "not_yet_used",
                    "recommended_next_action": (
                        "Review confirmed-series parser output columns before "
                        "creating baseline candidates."
                    ),
                    "notes": "Confirmed-series parsed table did not contain required fields.",
                }
            ],
            columns=columns,
        )
        out = _add_official_baseline_control_fields(out)
        out.to_csv(UKRSTAT_CONFIRMED_OBLAST_BASELINE_CANDIDATES_TABLE, index=False)
        return out

    working = confirmed_series_parsed.copy()

    for col in required_cols:
        working[col] = working[col].fillna("").astype(str)

    working = working[
        working["validation_status"].str.contains(
            "parsed_pending_validation",
            case=False,
            na=False,
        )
        & working["obs_value"].str.strip().ne("")
        & working["region_code"].str.strip().ne("")
    ].copy()

    if working.empty:
        out = pd.DataFrame(
            [
                {
                    "oblast": "",
                    "region_code": "",
                    "indicator_code": "",
                    "indicator_name": "",
                    "nace_code": "",
                    "nace_name": "",
                    "freq_code": "",
                    "freq_name": "",
                    "latest_period": "",
                    "official_regional_baseline_proxy": "",
                    "unit": "",
                    "updated": "",
                    "source_url": "",
                    "source_status": "no_reviewable_confirmed_observations",
                    "validation_status": "not_ready",
                    "current_use_in_scoring": "not_yet_used",
                    "recommended_next_action": (
                        "Confirm that the official observation parser returned "
                        "validated candidate values."
                    ),
                    "notes": (
                        "Confirmed-series observations were not available in a "
                        "reviewable parsed_pending_validation state."
                    ),
                }
            ],
            columns=columns,
        )
        out = _add_official_baseline_control_fields(out)
        out.to_csv(UKRSTAT_CONFIRMED_OBLAST_BASELINE_CANDIDATES_TABLE, index=False)
        return out

    working["time_period_dt"] = pd.to_datetime(
        working["time_period"],
        errors="coerce",
    )
    working["obs_value_numeric"] = pd.to_numeric(
        working["obs_value"],
        errors="coerce",
    )

    working = working.dropna(subset=["time_period_dt", "obs_value_numeric"]).copy()

    if working.empty:
        out = pd.DataFrame(
            [
                {
                    "oblast": "",
                    "region_code": "",
                    "indicator_code": "",
                    "indicator_name": "",
                    "nace_code": "",
                    "nace_name": "",
                    "freq_code": "",
                    "freq_name": "",
                    "latest_period": "",
                    "official_regional_baseline_proxy": "",
                    "unit": "",
                    "updated": "",
                    "source_url": "",
                    "source_status": "no_numeric_confirmed_observations",
                    "validation_status": "not_ready",
                    "current_use_in_scoring": "not_yet_used",
                    "recommended_next_action": (
                        "Review time-period and observation-value parsing before "
                        "creating baseline candidates."
                    ),
                    "notes": (
                        "Confirmed observations existed, but time_period or obs_value "
                        "could not be converted into reviewable values."
                    ),
                }
            ],
            columns=columns,
        )
        out = _add_official_baseline_control_fields(out)
        out.to_csv(UKRSTAT_CONFIRMED_OBLAST_BASELINE_CANDIDATES_TABLE, index=False)
        return out

    sort_cols = [
        "region_code",
        "indicator_code",
        "nace_code",
        "freq_code",
        "time_period_dt",
    ]

    latest = (
        working.sort_values(sort_cols)
        .groupby(
            ["region_code", "indicator_code", "nace_code", "freq_code"],
            as_index=False,
        )
        .tail(1)
        .copy()
    )

    rows: list[dict] = []

    for _, row in latest.iterrows():
        oblast = str(row.get("region_name", "")).strip()
        if not oblast:
            oblast = str(row.get("region_code", "")).strip()

        latest_period = ""
        if pd.notna(row.get("time_period_dt")):
            latest_period = row["time_period_dt"].strftime("%Y-%m-%d")
        else:
            latest_period = str(row.get("time_period", ""))

        rows.append(
            {
                "oblast": oblast,
                "region_code": str(row.get("region_code", "")),
                "indicator_code": str(row.get("indicator_code", "")),
                "indicator_name": str(row.get("indicator_name", "")),
                "nace_code": str(row.get("nace_code", "")),
                "nace_name": str(row.get("nace_name", "")),
                "freq_code": str(row.get("freq_code", "")),
                "freq_name": str(row.get("freq_name", "")),
                "latest_period": latest_period,
                "official_regional_baseline_proxy": row.get("obs_value_numeric", ""),
                "unit": str(row.get("unit", "")),
                "updated": str(row.get("updated", "")),
                "source_url": str(row.get("source_url", "")),
                "source_status": "official_sdmx_observation_parsed",
                "validation_status": "pending_unit_and_mapping_validation",
                "current_use_in_scoring": "not_yet_used",
                "recommended_next_action": (
                    "Validate unit, indicator meaning, NACE mapping, geography mapping, "
                    "and period coverage. After validation, expand to all oblasts before "
                    "considering any scoring blend."
                ),
                "notes": (
                    "Latest available official Ukrstat regional-account observation "
                    "selected as a baseline candidate only. This is a replacement "
                    "candidate for synthetic baseline fields, not a scoring input yet."
                ),
            }
        )

    out = pd.DataFrame(rows, columns=columns).drop_duplicates()
    out = out.sort_values(
        ["oblast", "indicator_code", "nace_code", "freq_code"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)

    out = _add_official_baseline_control_fields(out)

    out.to_csv(UKRSTAT_CONFIRMED_OBLAST_BASELINE_CANDIDATES_TABLE, index=False)

    return out


def _oblast_region_candidates_from_query_table(
    observation_query_candidates: pd.DataFrame | None,
) -> pd.DataFrame:
    """Return probable oblast-level REGION candidates from the query shortlist."""
    columns = ["region_code", "oblast"]

    if observation_query_candidates is None or observation_query_candidates.empty:
        return pd.DataFrame(columns=columns)

    required = {"dimension_id", "code_id", "code_name", "candidate_query_status"}
    if not required.issubset(set(observation_query_candidates.columns)):
        return pd.DataFrame(columns=columns)

    working = observation_query_candidates.copy()
    for col in required:
        working[col] = working[col].fillna("").astype(str)

    regions = working[
        working["dimension_id"].str.upper().eq("REGION")
        & working["candidate_query_status"].str.contains(
            "shortlist_pending_review",
            case=False,
            na=False,
        )
    ].copy()

    if regions.empty:
        return pd.DataFrame(columns=columns)

    def is_oblast_level(code_id: str, code_name: str) -> bool:
        code = str(code_id).strip()
        name = str(code_name).strip().lower()

        if not code.startswith("UA"):
            return False

        has_oblast_level_zero_block = (
            len(code) >= 17
            and code[2:4].isdigit()
            and code[4:13] == "000000000"
        )

        if not has_oblast_level_zero_block:
            return False

        oblast_name_markers = (
            name.endswith("ska")
            or name.endswith("tska")
            or name.endswith("zka")
            or name.endswith("ka")
            or name in {"kyiv city", "city of kyiv", "kyiv"}
            or "kyiv city" in name
            or "city of kyiv" in name
        )

        return oblast_name_markers

    regions["_keep"] = regions.apply(
        lambda row: is_oblast_level(row.get("code_id", ""), row.get("code_name", "")),
        axis=1,
    )

    out = regions[regions["_keep"]].copy()

    if out.empty:
        # Fallback to the shortlisted REGION rows rather than failing silently.
        out = regions.copy()

    out = out.rename(columns={"code_id": "region_code", "code_name": "oblast"})
    out = out[["region_code", "oblast"]].drop_duplicates()

    # Keep the first expansion conservative. The shortlist usually contains the
    # 24 oblasts plus Kyiv City. If more rows appear because of fallback behavior,
    # cap at 30 to avoid accidentally pulling lower-level settlements at scale.
    out = out.sort_values(["oblast", "region_code"]).head(30).reset_index(drop=True)

    return out


def _parse_sdmx_observations_to_rows(
    payload: Any,
    source_row: dict,
    availability_value_candidates: pd.DataFrame | None = None,
) -> list[dict]:
    """Parse compact SDMX data JSON observations into validation rows.

    This shared helper is intentionally narrow and conservative. It supports the
    layouts already observed from Ukrstat:
    - data.dataSets[].observations
    - data.dataSets[].series[].observations

    It maps observation indexes to TIME_PERIOD labels from the response when
    available, or from availability boundaries when the compact payload omits
    explicit labels.
    """
    def observation_period_values(p: Any) -> list[str]:
        values: list[str] = []

        def extract_values_from_dimension(dim: dict) -> None:
            dim_id = str(dim.get("id", ""))
            if dim_id and dim_id.upper() != "TIME_PERIOD":
                return

            dim_values = dim.get("values", [])
            if not isinstance(dim_values, list):
                return

            for value in dim_values:
                if isinstance(value, dict):
                    code = str(value.get("id", value.get("name", "")))
                    if code:
                        values.append(code)
                elif value not in [None, ""]:
                    values.append(str(value))

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                if "dimensions" in value and isinstance(value.get("dimensions"), dict):
                    observation_dims = value["dimensions"].get("observation", [])
                    if isinstance(observation_dims, list):
                        for dim in observation_dims:
                            if isinstance(dim, dict):
                                extract_values_from_dimension(dim)

                if str(value.get("id", "")).upper() == "TIME_PERIOD":
                    extract_values_from_dimension(value)

                for child in value.values():
                    walk(child)

            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(p)
        return values

    def availability_period_boundaries() -> tuple[str, str]:
        frame = availability_value_candidates

        if (
            frame is None
            or frame.empty
            or not {"dimension_id", "value_code", "candidate_role"}.issubset(
                set(frame.columns)
            )
        ):
            if UKRSTAT_AVAILABILITY_VALUE_CANDIDATES_TABLE.exists():
                try:
                    frame = pd.read_csv(UKRSTAT_AVAILABILITY_VALUE_CANDIDATES_TABLE)
                except Exception:
                    frame = pd.DataFrame()

        if frame is None or frame.empty:
            return "", ""

        working = frame.copy()
        for col in ["dimension_id", "value_code", "candidate_role", "value_description"]:
            if col not in working.columns:
                working[col] = ""
            working[col] = working[col].fillna("").astype(str)

        time_rows = working[working["dimension_id"].str.upper().eq("TIME_PERIOD")].copy()

        if time_rows.empty:
            return "", ""

        starts = time_rows[time_rows["value_description"].str.upper().eq("TIME_PERIOD_START")]
        ends = time_rows[time_rows["value_description"].str.upper().eq("TIME_PERIOD_END")]

        start_value = str(starts.iloc[0].get("value_code", "")) if not starts.empty else ""
        end_value = str(ends.iloc[0].get("value_code", "")) if not ends.empty else ""

        if not start_value or not end_value:
            date_like = time_rows[
                time_rows["value_code"].str.match(r"^\d{4}(-\d{2}-\d{2})?$", na=False)
            ].copy()
            if not date_like.empty:
                sorted_dates = sorted(date_like["value_code"].dropna().astype(str).unique())
                start_value = start_value or sorted_dates[0]
                end_value = end_value or sorted_dates[-1]

        return start_value, end_value

    def value_from_obs_payload(obs_payload: Any) -> str:
        if isinstance(obs_payload, list):
            if obs_payload:
                return "" if obs_payload[0] is None else str(obs_payload[0])
            return ""

        if isinstance(obs_payload, dict):
            for key in ["value", "obs_value", "OBS_VALUE"]:
                if key in obs_payload:
                    return "" if obs_payload[key] is None else str(obs_payload[key])
            return json.dumps(obs_payload, ensure_ascii=False)[:300]

        return "" if obs_payload is None else str(obs_payload)

    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    if not isinstance(data, dict):
        data = {}

    data_sets = data.get("dataSets", [])
    if not isinstance(data_sets, list):
        data_sets = []

    periods = observation_period_values(payload)

    def count_observation_records() -> int:
        count = 0

        for dataset in data_sets:
            if not isinstance(dataset, dict):
                continue

            observations = dataset.get("observations", {})
            if isinstance(observations, dict):
                count += len(
                    [
                        obs_payload
                        for obs_payload in observations.values()
                        if value_from_obs_payload(obs_payload)
                    ]
                )

            series = dataset.get("series", {})
            if isinstance(series, dict):
                for series_payload in series.values():
                    if not isinstance(series_payload, dict):
                        continue

                    series_observations = series_payload.get("observations", {})
                    if isinstance(series_observations, dict):
                        count += len(
                            [
                                obs_payload
                                for obs_payload in series_observations.values()
                                if value_from_obs_payload(obs_payload)
                            ]
                        )

        return count

    def build_annual_periods_from_availability(count: int) -> list[str]:
        start_value, end_value = availability_period_boundaries()

        if not start_value:
            return []

        try:
            start_year = int(str(start_value)[:4])
        except Exception:
            return []

        end_year = None
        if end_value:
            try:
                end_year = int(str(end_value)[:4])
            except Exception:
                end_year = None

        generated = [f"{start_year + idx}-01-01" for idx in range(count)]

        if end_year is not None:
            generated = [
                period
                for period in generated
                if int(period[:4]) <= end_year
            ][:count]

        return generated

    fallback_periods = build_annual_periods_from_availability(count_observation_records())

    def period_for_key(obs_key: str) -> str:
        first = str(obs_key).split(":")[0]

        try:
            idx = int(first)
            if 0 <= idx < len(periods):
                return periods[idx]
        except Exception:
            pass

        try:
            idx = int(first)
            if 0 <= idx < len(fallback_periods):
                return fallback_periods[idx]
        except Exception:
            pass

        return str(obs_key)

    rows: list[dict] = []

    def append_obs(obs_key: str, obs_payload: Any) -> None:
        obs_value = value_from_obs_payload(obs_payload)
        if not obs_value:
            return

        rows.append(
            {
                "indicator_code": source_row.get("indicator_code", ""),
                "indicator_name": source_row.get("indicator_name", ""),
                "region_code": source_row.get("region_code", ""),
                "region_name": source_row.get("region_name", ""),
                "nace_code": source_row.get("nace_code", ""),
                "nace_name": source_row.get("nace_name", ""),
                "freq_code": source_row.get("freq_code", ""),
                "freq_name": source_row.get("freq_name", ""),
                "time_period": period_for_key(str(obs_key)),
                "obs_value": obs_value,
                "unit": "",
                "updated": "",
                "source_url": source_row.get("url", ""),
                "source_status": "official_sdmx_observation_parsed",
                "validation_status": "parsed_pending_validation",
                "current_use_in_scoring": "not_yet_used",
                "notes": (
                    "Observation parsed from official Ukrstat SDMX response. Validate "
                    "period, unit, geography, NACE, and meaning before any scoring blend."
                ),
            }
        )

    for dataset in data_sets:
        if not isinstance(dataset, dict):
            continue

        observations = dataset.get("observations", {})
        if isinstance(observations, dict):
            for obs_key, obs_payload in observations.items():
                append_obs(str(obs_key), obs_payload)

        series = dataset.get("series", {})
        if isinstance(series, dict):
            for series_payload in series.values():
                if not isinstance(series_payload, dict):
                    continue

                series_observations = series_payload.get("observations", {})
                if isinstance(series_observations, dict):
                    for obs_key, obs_payload in series_observations.items():
                        append_obs(str(obs_key), obs_payload)

    return rows


def probe_all_oblast_baseline_series(
    observation_query_candidates: pd.DataFrame,
    availability_value_candidates: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Expand the confirmed GRP._Z.A pattern across oblast-level regions.

    This creates two validation-only artifacts:
    - ukrstat_oblast_baseline_probe_results.csv
    - ukrstat_oblast_baseline_candidates.csv

    It does not blend official values into WARIS scoring. Output control fields
    explicitly preserve production_score_change=none and scoring/Monte Carlo
    use flags as False.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR, UKRSTAT_OBLAST_BASELINE_SUCCESS_DIR])

    probe_columns = [
        "oblast",
        "region_code",
        "sdmx_key",
        "indicator_code",
        "indicator_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "url",
        "http_status",
        "success_status",
        "content_type",
        "observation_value_count",
        "has_observations",
        "raw_response_path",
        "response_preview",
        "notes",
    ]

    candidate_columns = [
        "oblast",
        "region_code",
        "indicator_code",
        "indicator_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "latest_period",
        "official_regional_baseline_proxy",
        "unit",
        "updated",
        "source_url",
        "source_status",
        "validation_status",
        "current_use_in_scoring",
        "recommended_next_action",
        "notes",
    ]

    region_candidates = _oblast_region_candidates_from_query_table(
        observation_query_candidates
    )

    if region_candidates.empty:
        probe_out = pd.DataFrame(
            [
                {
                    "oblast": "",
                    "region_code": "",
                    "sdmx_key": "",
                    "indicator_code": "GRP",
                    "indicator_name": "Gross regional product",
                    "nace_code": "_Z",
                    "nace_name": "Availability-derived NACE candidate",
                    "freq_code": "A",
                    "freq_name": "Annual",
                    "url": "",
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "observation_value_count": 0,
                    "has_observations": False,
                    "raw_response_path": "",
                    "response_preview": "No oblast-level REGION candidates were available.",
                    "notes": (
                        "No all-oblast baseline probe was executed. Review "
                        "observation-query candidates."
                    ),
                }
            ],
            columns=probe_columns,
        )
        candidate_out = pd.DataFrame(
            [
                {
                    "oblast": "",
                    "region_code": "",
                    "indicator_code": "GRP",
                    "indicator_name": "Gross regional product",
                    "nace_code": "_Z",
                    "nace_name": "Availability-derived NACE candidate",
                    "freq_code": "A",
                    "freq_name": "Annual",
                    "latest_period": "",
                    "official_regional_baseline_proxy": "",
                    "unit": "",
                    "updated": "",
                    "source_url": "",
                    "source_status": "oblast_region_candidates_unavailable",
                    "validation_status": "not_ready",
                    "current_use_in_scoring": "not_yet_used",
                    "recommended_next_action": "Review REGION shortlist before oblast expansion.",
                    "notes": "No all-oblast baseline candidate could be created.",
                }
            ],
            columns=candidate_columns,
        )
        probe_out.to_csv(UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE, index=False)
        candidate_out = _add_official_baseline_control_fields(candidate_out)
        candidate_out.to_csv(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE, index=False)
        return probe_out, candidate_out

    indicator_code = "GRP"
    indicator_name = "Gross regional product"
    nace_code = "_Z"
    nace_name = "Availability-derived NACE candidate"
    freq_code = "A"
    freq_name = "Annual"

    availability_nace = _availability_first_code(
        availability_value_candidates,
        "NACE",
        ["_Z", "_T", "TOTAL"],
    )
    if availability_nace:
        nace_code = availability_nace

    availability_freq = _availability_first_code(
        availability_value_candidates,
        "FREQ",
        ["A", "Y", "ANNUAL"],
    )
    if availability_freq:
        freq_code = availability_freq

    official_sdmx_3_data = (
        "https://stat.gov.ua/sdmx/workspaces/default:integration/"
        "registry/sdmx/3.0/data"
    )

    probe_rows: list[dict] = []
    parsed_rows: list[dict] = []

    for _, region in region_candidates.iterrows():
        region_code = str(region.get("region_code", "")).strip()
        oblast = str(region.get("oblast", "")).strip()

        if not region_code:
            continue

        sdmx_key = ".".join([indicator_code, region_code, nace_code, freq_code])
        url = (
            f"{official_sdmx_3_data}/dataflow/SSSU/{DATAFLOW_ID}/~"
            f"/{sdmx_key}?dimensionAtObservation=TIME_PERIOD"
        )

        raw_response_path = (
            UKRSTAT_OBLAST_BASELINE_SUCCESS_DIR
            / f"{region_code}_{indicator_code}_{nace_code}_{freq_code}.json"
        )

        try:
            response = requests.get(
                url,
                timeout=45,
                headers={
                    "User-Agent": "WARIS research prototype",
                    "Accept": (
                        "application/vnd.sdmx.data+json;version=2.0.0, "
                        "application/vnd.sdmx.data+json;version=1.0.0, "
                        "application/json, text/csv, */*"
                    ),
                },
            )

            content_type = response.headers.get("Content-Type", "")
            success_status = 200 <= response.status_code < 300
            response_preview = response.text[:750].replace("\n", " ").replace("\r", " ")

            observation_value_count = 0
            payload = None

            try:
                payload = response.json()
                if isinstance(payload, dict):
                    observation_value_count = _count_sdmx_observation_values(payload)
            except Exception:
                payload = None

            has_observations = observation_value_count > 0

            if success_status and has_observations and isinstance(payload, dict):
                raw_response_path.write_text(
                    response.text,
                    encoding="utf-8",
                    errors="ignore",
                )

                source_row = {
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "region_code": region_code,
                    "region_name": oblast,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "url": url,
                }

                parsed_rows.extend(
                    _parse_sdmx_observations_to_rows(
                        payload=payload,
                        source_row=source_row,
                        availability_value_candidates=availability_value_candidates,
                    )
                )

            probe_rows.append(
                {
                    "oblast": oblast,
                    "region_code": region_code,
                    "sdmx_key": sdmx_key,
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "url": url,
                    "http_status": response.status_code,
                    "success_status": success_status,
                    "content_type": content_type,
                    "observation_value_count": observation_value_count,
                    "has_observations": has_observations,
                    "raw_response_path": (
                        str(raw_response_path) if raw_response_path.exists() else ""
                    ),
                    "response_preview": response_preview,
                    "notes": (
                        "All-oblast official baseline probe. Do not blend into WARIS "
                        "scoring until unit, period, geography, NACE, and measure "
                        "meaning are validated."
                    ),
                }
            )

        except Exception as exc:
            probe_rows.append(
                {
                    "oblast": oblast,
                    "region_code": region_code,
                    "sdmx_key": sdmx_key,
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "url": url,
                    "http_status": "",
                    "success_status": False,
                    "content_type": "",
                    "observation_value_count": 0,
                    "has_observations": False,
                    "raw_response_path": "",
                    "response_preview": f"Request failed: {exc}",
                    "notes": (
                        "All-oblast official baseline probe failed. Do not blend into "
                        "WARIS scoring from this response."
                    ),
                }
            )

    probe_out = pd.DataFrame(probe_rows, columns=probe_columns).drop_duplicates()
    probe_out.to_csv(UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE, index=False)

    parsed = pd.DataFrame(parsed_rows)

    if parsed.empty:
        candidate_out = pd.DataFrame(
            [
                {
                    "oblast": "",
                    "region_code": "",
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "latest_period": "",
                    "official_regional_baseline_proxy": "",
                    "unit": "",
                    "updated": "",
                    "source_url": "",
                    "source_status": "no_oblast_observations_parsed",
                    "validation_status": "not_ready",
                    "current_use_in_scoring": "not_yet_used",
                    "recommended_next_action": (
                        "Review all-oblast probe results and raw responses before "
                        "attempting scoring integration."
                    ),
                    "notes": (
                        "No all-oblast baseline candidates were created because no "
                        "official observations were parsed."
                    ),
                }
            ],
            columns=candidate_columns,
        )
        candidate_out = _add_official_baseline_control_fields(candidate_out)
        candidate_out.to_csv(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE, index=False)
        return probe_out, candidate_out

    parsed["time_period_dt"] = pd.to_datetime(parsed["time_period"], errors="coerce")
    parsed["obs_value_numeric"] = pd.to_numeric(parsed["obs_value"], errors="coerce")
    parsed = parsed.dropna(subset=["time_period_dt", "obs_value_numeric"]).copy()

    if parsed.empty:
        candidate_out = pd.DataFrame(
            [
                {
                    "oblast": "",
                    "region_code": "",
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "nace_code": nace_code,
                    "nace_name": nace_name,
                    "freq_code": freq_code,
                    "freq_name": freq_name,
                    "latest_period": "",
                    "official_regional_baseline_proxy": "",
                    "unit": "",
                    "updated": "",
                    "source_url": "",
                    "source_status": "oblast_observations_not_numeric",
                    "validation_status": "not_ready",
                    "current_use_in_scoring": "not_yet_used",
                    "recommended_next_action": (
                        "Review all-oblast time-period and observation parsing."
                    ),
                    "notes": (
                        "Official observations were parsed but could not be converted "
                        "to numeric baseline candidates."
                    ),
                }
            ],
            columns=candidate_columns,
        )
        candidate_out = _add_official_baseline_control_fields(candidate_out)
        candidate_out.to_csv(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE, index=False)
        return probe_out, candidate_out

    latest = (
        parsed.sort_values(
            ["region_code", "indicator_code", "nace_code", "freq_code", "time_period_dt"]
        )
        .groupby(["region_code", "indicator_code", "nace_code", "freq_code"], as_index=False)
        .tail(1)
        .copy()
    )

    candidate_rows: list[dict] = []
    for _, row in latest.iterrows():
        latest_period = row["time_period_dt"].strftime("%Y-%m-%d")
        candidate_rows.append(
            {
                "oblast": str(row.get("region_name", "")),
                "region_code": str(row.get("region_code", "")),
                "indicator_code": str(row.get("indicator_code", "")),
                "indicator_name": str(row.get("indicator_name", "")),
                "nace_code": str(row.get("nace_code", "")),
                "nace_name": str(row.get("nace_name", "")),
                "freq_code": str(row.get("freq_code", "")),
                "freq_name": str(row.get("freq_name", "")),
                "latest_period": latest_period,
                "official_regional_baseline_proxy": row.get("obs_value_numeric", ""),
                "unit": str(row.get("unit", "")),
                "updated": str(row.get("updated", "")),
                "source_url": str(row.get("source_url", "")),
                "source_status": "official_sdmx_observation_parsed",
                "validation_status": "pending_unit_and_mapping_validation",
                "current_use_in_scoring": "not_yet_used",
                "recommended_next_action": (
                    "Validate unit, indicator meaning, NACE mapping, geography mapping, "
                    "and latest-period coverage before any scoring blend."
                ),
                "notes": (
                    "Latest available official Ukrstat regional-account observation "
                    "selected as an oblast baseline candidate only. This is not a "
                    "scoring input, not a Monte Carlo input, and not connected to "
                    "Prozorro, wartime typology, or FIU/SFMS source-support layers."
                ),
            }
        )

    candidate_out = pd.DataFrame(candidate_rows, columns=candidate_columns).drop_duplicates()
    candidate_out = candidate_out.sort_values(["oblast", "region_code"]).reset_index(drop=True)
    candidate_out = _add_official_baseline_control_fields(candidate_out)
    candidate_out.to_csv(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE, index=False)

    return probe_out, candidate_out

def parse_observation_probe_response(
    observation_query_candidates: pd.DataFrame,
    observation_probe_results: pd.DataFrame,
    data_endpoint_discovery_results: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Parse the saved Ukrstat SDMX data response into flat review artifacts.

    This parser is intentionally conservative. It reads the saved official SDMX
    data response produced by the observation probes and attempts to normalize
    observation values into a review table. It also writes a raw JSON path
    inventory so the exact response shape can be inspected before any scoring
    use.

    Outputs:
    - outputs/tables/ukrstat_observation_response_paths.csv
    - outputs/tables/ukrstat_observation_probe_parsed.csv

    The function supports common SDMX JSON 2.0 layouts where observations may be
    stored under either:
    - data.dataSets[].series[].observations
    - data.dataSets[].observations

    If the response shape differs, the function writes diagnostic rows instead
    of guessing. Parsed values remain not_yet_used in WARIS scoring.
    """
    ensure_dirs([TABLE_DIR, RAW_DIR])

    columns = [
        "indicator_code",
        "indicator_name",
        "region_code",
        "region_name",
        "nace_code",
        "nace_name",
        "freq_code",
        "freq_name",
        "time_period",
        "obs_value",
        "unit",
        "updated",
        "source_url",
        "source_status",
        "validation_status",
        "current_use_in_scoring",
        "notes",
    ]

    def write_response_path_inventory(payload: Any | None, status: str, notes: str) -> pd.DataFrame:
        """Write JSON path inventory for the saved SDMX observation response."""
        if payload is None:
            paths = pd.DataFrame(
                [
                    {
                        "json_path": "",
                        "value_preview": "",
                        "path_role": "payload_unavailable",
                        "source_status": status,
                        "notes": notes,
                    }
                ]
            )
            paths.to_csv(UKRSTAT_OBSERVATION_RESPONSE_PATHS_TABLE, index=False)
            return paths

        flattened = _flatten_json_paths(payload)

        if flattened.empty:
            paths = pd.DataFrame(
                [
                    {
                        "json_path": "",
                        "value_preview": "",
                        "path_role": "no_scalar_paths_detected",
                        "source_status": status,
                        "notes": notes,
                    }
                ]
            )
            paths.to_csv(UKRSTAT_OBSERVATION_RESPONSE_PATHS_TABLE, index=False)
            return paths

        paths = flattened.rename(columns={"value": "value_preview"}).copy()

        def classify_path(path: str) -> str:
            p = str(path).lower()
            if "observations" in p:
                return "observation_value_or_attribute_path"
            if "series" in p:
                return "series_path"
            if "dimensions" in p:
                return "dimension_metadata_path"
            if "attributes" in p:
                return "attribute_metadata_or_value_path"
            if "structures" in p or "structure" in p:
                return "structure_metadata_path"
            if "dataset" in p or "dataSets" in path:
                return "dataset_path"
            return "other_response_path"

        paths["path_role"] = paths["json_path"].apply(classify_path)
        paths["source_status"] = status
        paths["notes"] = notes

        paths = paths[
            ["json_path", "value_preview", "path_role", "source_status", "notes"]
        ]
        paths.to_csv(UKRSTAT_OBSERVATION_RESPONSE_PATHS_TABLE, index=False)
        return paths

    def diagnostic_row(status: str, validation_status: str, notes: str) -> pd.DataFrame:
        out = pd.DataFrame(
            [
                {
                    "indicator_code": "",
                    "indicator_name": "",
                    "region_code": "",
                    "region_name": "",
                    "nace_code": "",
                    "nace_name": "",
                    "freq_code": "",
                    "freq_name": "",
                    "time_period": "",
                    "obs_value": pd.NA,
                    "unit": "",
                    "updated": "",
                    "source_url": "",
                    "source_status": status,
                    "validation_status": validation_status,
                    "current_use_in_scoring": "not_yet_used",
                    "notes": notes,
                }
            ],
            columns=columns,
        )
        out.to_csv(UKRSTAT_OBSERVATION_PARSED_TABLE, index=False)
        return out

    def choose_default_code(dimension_id: str, preferred_codes: list[str]) -> tuple[str, str]:
        if (
            observation_query_candidates is None
            or observation_query_candidates.empty
            or "dimension_id" not in observation_query_candidates.columns
            or "code_id" not in observation_query_candidates.columns
        ):
            return "", ""

        subset = observation_query_candidates[
            observation_query_candidates["dimension_id"].fillna("").astype(str)
            == dimension_id
        ].copy()

        if subset.empty:
            return "", ""

        for preferred in preferred_codes:
            matched = subset[subset["code_id"].fillna("").astype(str) == preferred]
            if not matched.empty:
                row = matched.iloc[0]
                return str(row.get("code_id", "")), str(row.get("code_name", ""))

        row = subset.iloc[0]
        return str(row.get("code_id", "")), str(row.get("code_name", ""))

    def first_successful_data_url() -> str:
        frames = [observation_probe_results, data_endpoint_discovery_results]

        for frame in frames:
            if frame is None or frame.empty:
                continue

            required = {"success_status", "content_type", "url"}
            if not required.issubset(set(frame.columns)):
                continue

            working = frame.copy()
            success = working["success_status"].astype(str).str.lower().eq("true")
            data_type = working["content_type"].fillna("").astype(str).str.lower().str.contains(
                "application/vnd.sdmx.data|json",
                regex=True,
                na=False,
            )
            data_route = working["url"].fillna("").astype(str).str.contains(
                "/data/dataflow/",
                regex=False,
                na=False,
            )

            matched = working[success & data_type & data_route]
            if not matched.empty:
                return str(matched.iloc[0].get("url", ""))

        return ""

    if not UKRSTAT_OBSERVATION_DATA_RESPONSE_RAW.exists():
        write_response_path_inventory(
            None,
            "data_response_raw_missing",
            "No saved SDMX data response was found.",
        )
        return diagnostic_row(
            "data_response_raw_missing",
            "not_parsed",
            (
                "No saved SDMX data response was found. Re-run the observation "
                "probe after the official SDMX v3 route has been confirmed."
            ),
        )

    try:
        payload = json.loads(
            UKRSTAT_OBSERVATION_DATA_RESPONSE_RAW.read_text(encoding="utf-8")
        )
    except Exception as exc:
        write_response_path_inventory(
            None,
            "data_response_raw_unreadable",
            f"Could not parse saved SDMX data response as JSON: {exc}",
        )
        return diagnostic_row(
            "data_response_raw_unreadable",
            "not_parsed",
            f"Could not parse saved SDMX data response as JSON: {exc}",
        )

    response_paths = write_response_path_inventory(
        payload,
        "official_sdmx_data_response_loaded",
        (
            "Flattened JSON path inventory for official Ukrstat SDMX data "
            "response. Use this to validate where observations, dimensions, "
            "and attributes are located before any scoring blend."
        ),
    )

    indicator_default, indicator_name_default = choose_default_code(
        "INDICATOR",
        ["GRP", "GVA", "OUTPUT", "GRP_CAP"],
    )
    region_default, region_name_default = choose_default_code(
        "REGION",
        [
            "UA12000000000090473",
            "UA32000000000030281",
            "UA80000000000093317",
        ],
    )
    nace_default, nace_name_default = choose_default_code("NACE", ["_T", "TOTAL"])
    freq_default, freq_name_default = choose_default_code("FREQ", ["A", "Y", "ANNUAL"])
    time_default, _ = choose_default_code("TIME_PERIOD", ["2021", "2022", "2023"])

    source_url = first_successful_data_url()

    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    data_sets = data.get("dataSets", []) if isinstance(data, dict) else []

    if not isinstance(data_sets, list) or not data_sets:
        return diagnostic_row(
            "data_response_has_no_datasets",
            "not_parsed",
            (
                "The saved SDMX data response did not contain data.dataSets. "
                "Inspect ukrstat_observation_response_paths.csv before using values."
            ),
        )

    def pick_structure() -> dict:
        """Return the first available SDMX structure object from common layouts."""
        if not isinstance(data, dict):
            return {}

        structures = data.get("structures", [])
        if isinstance(structures, list) and structures:
            first = structures[0]
            if isinstance(first, dict):
                return first

        structure = data.get("structure", {})
        if isinstance(structure, dict):
            return structure
        if isinstance(structure, list) and structure and isinstance(structure[0], dict):
            return structure[0]

        payload_structure = payload.get("structure", {}) if isinstance(payload, dict) else {}
        if isinstance(payload_structure, dict):
            return payload_structure

        return {}

    structure = pick_structure()
    dimensions = structure.get("dimensions", {}) if isinstance(structure, dict) else {}
    attributes = structure.get("attributes", {}) if isinstance(structure, dict) else {}

    series_dimensions = dimensions.get("series", []) if isinstance(dimensions, dict) else []
    observation_dimensions = (
        dimensions.get("observation", []) if isinstance(dimensions, dict) else []
    )
    data_set_attributes = attributes.get("dataSet", []) if isinstance(attributes, dict) else []
    series_attributes = attributes.get("series", []) if isinstance(attributes, dict) else []
    observation_attributes = (
        attributes.get("observation", []) if isinstance(attributes, dict) else []
    )

    def value_from_dimension(dimension: dict, index_value: str) -> tuple[str, str]:
        values = dimension.get("values", []) if isinstance(dimension, dict) else []

        try:
            idx = int(index_value)
        except Exception:
            return str(index_value), ""

        if isinstance(values, list) and 0 <= idx < len(values):
            item = values[idx]
            code = str(item.get("id", index_value)) if isinstance(item, dict) else str(index_value)
            name = _extract_name(item.get("name", item.get("names", ""))) if isinstance(item, dict) else ""
            return code, name

        return str(index_value), ""

    def map_dimensions(dim_list: list, key: str) -> dict[str, dict[str, str]]:
        out: dict[str, dict[str, str]] = {}
        indexes = str(key).split(":") if key != "" else []

        for position, dimension in enumerate(dim_list):
            if not isinstance(dimension, dict):
                continue

            dim_id = str(dimension.get("id", ""))
            if position < len(indexes):
                code, name = value_from_dimension(dimension, indexes[position])
            else:
                code, name = "", ""

            out[dim_id] = {"code": code, "name": name}

        return out

    def attr_value(attribute_list: list, attr_values: Any, target_ids: set[str]) -> str:
        if not isinstance(attribute_list, list) or attr_values is None:
            return ""

        if not isinstance(attr_values, list):
            return ""

        for pos, attr in enumerate(attribute_list):
            if not isinstance(attr, dict):
                continue

            attr_id = str(attr.get("id", ""))
            if attr_id not in target_ids:
                continue

            if pos >= len(attr_values):
                continue

            raw_value = attr_values[pos]

            if raw_value is None:
                continue

            if isinstance(raw_value, list) and raw_value:
                first = raw_value[0]
                if isinstance(first, dict):
                    return _extract_name(first.get("name", first.get("names", first)))
                return str(first)

            if isinstance(raw_value, dict):
                return _extract_name(raw_value.get("name", raw_value.get("names", raw_value)))

            return str(raw_value)

        return ""

    def append_observation_row(
        rows: list[dict],
        series_dim_map: dict[str, dict[str, str]],
        obs_dim_map: dict[str, dict[str, str]],
        obs_payload: Any,
        dataset_unit: str,
        dataset_updated: str,
        series_unit: str = "",
        series_updated: str = "",
    ) -> None:
        obs_value = pd.NA
        obs_attrs: Any = []

        if isinstance(obs_payload, list):
            if obs_payload:
                obs_value = obs_payload[0]
            if len(obs_payload) > 1:
                obs_attrs = obs_payload[1:]
        elif isinstance(obs_payload, dict):
            obs_value = obs_payload.get("value", obs_payload.get("obs_value", pd.NA))
            obs_attrs = obs_payload.get("attributes", [])
        else:
            obs_value = obs_payload

        obs_unit = attr_value(
            observation_attributes,
            obs_attrs,
            {"UNIT_MEASURE", "UNIT", "UNITS_OF_MEASURE"},
        )
        obs_updated = attr_value(observation_attributes, obs_attrs, {"UPDATED"})

        indicator_code = (
            series_dim_map.get("INDICATOR", {}).get("code")
            or obs_dim_map.get("INDICATOR", {}).get("code")
            or indicator_default
        )
        indicator_name = (
            series_dim_map.get("INDICATOR", {}).get("name")
            or obs_dim_map.get("INDICATOR", {}).get("name")
            or indicator_name_default
        )
        region_code = (
            series_dim_map.get("REGION", {}).get("code")
            or obs_dim_map.get("REGION", {}).get("code")
            or region_default
        )
        region_name = (
            series_dim_map.get("REGION", {}).get("name")
            or obs_dim_map.get("REGION", {}).get("name")
            or region_name_default
        )
        nace_code = (
            series_dim_map.get("NACE", {}).get("code")
            or obs_dim_map.get("NACE", {}).get("code")
            or nace_default
        )
        nace_name = (
            series_dim_map.get("NACE", {}).get("name")
            or obs_dim_map.get("NACE", {}).get("name")
            or nace_name_default
        )
        freq_code = (
            series_dim_map.get("FREQ", {}).get("code")
            or obs_dim_map.get("FREQ", {}).get("code")
            or freq_default
        )
        freq_name = (
            series_dim_map.get("FREQ", {}).get("name")
            or obs_dim_map.get("FREQ", {}).get("name")
            or freq_name_default
        )
        time_period = (
            obs_dim_map.get("TIME_PERIOD", {}).get("code")
            or series_dim_map.get("TIME_PERIOD", {}).get("code")
            or time_default
        )

        rows.append(
            {
                "indicator_code": indicator_code,
                "indicator_name": indicator_name,
                "region_code": region_code,
                "region_name": region_name,
                "nace_code": nace_code,
                "nace_name": nace_name,
                "freq_code": freq_code,
                "freq_name": freq_name,
                "time_period": time_period,
                "obs_value": obs_value,
                "unit": obs_unit or series_unit or dataset_unit,
                "updated": obs_updated or series_updated or dataset_updated,
                "source_url": source_url,
                "source_status": "official_sdmx_data_response_parsed",
                "validation_status": "parsed_pending_validation",
                "current_use_in_scoring": "not_yet_used",
                "notes": (
                    "Parsed from saved Ukrstat SDMX data response. Validate value, "
                    "units, geography mapping, NACE mapping, and time-period coverage "
                    "before any WARIS scoring blend."
                ),
            }
        )

    rows: list[dict] = []

    for dataset in data_sets:
        if not isinstance(dataset, dict):
            continue

        dataset_attrs = dataset.get("attributes", [])
        dataset_unit = attr_value(
            data_set_attributes,
            dataset_attrs,
            {"UNIT_MEASURE", "UNIT", "UNITS_OF_MEASURE"},
        )
        dataset_updated = attr_value(
            data_set_attributes,
            dataset_attrs,
            {"UPDATED", "TIME_FORMAT"},
        )

        # SDMX JSON may store observations directly at dataset level when the
        # series key is supplied in the URL and TIME_PERIOD is the observation
        # dimension. This is the likely layout for the first WARIS probe.
        dataset_observations = dataset.get("observations", {})
        if isinstance(dataset_observations, dict) and dataset_observations:
            for obs_key, obs_payload in dataset_observations.items():
                obs_dim_map = map_dimensions(observation_dimensions, str(obs_key))
                append_observation_row(
                    rows=rows,
                    series_dim_map={},
                    obs_dim_map=obs_dim_map,
                    obs_payload=obs_payload,
                    dataset_unit=dataset_unit,
                    dataset_updated=dataset_updated,
                )

        # Some SDMX JSON responses store observations under series keys.
        series = dataset.get("series", {})
        if isinstance(series, dict) and series:
            for series_key, series_payload in series.items():
                if not isinstance(series_payload, dict):
                    continue

                series_dim_map = map_dimensions(series_dimensions, str(series_key))
                series_attrs = series_payload.get("attributes", [])
                series_unit = attr_value(
                    series_attributes,
                    series_attrs,
                    {"UNIT_MEASURE", "UNIT", "UNITS_OF_MEASURE"},
                )
                series_updated = attr_value(series_attributes, series_attrs, {"UPDATED"})

                observations = series_payload.get("observations", {})

                if not isinstance(observations, dict):
                    continue

                for obs_key, obs_payload in observations.items():
                    obs_dim_map = map_dimensions(observation_dimensions, str(obs_key))
                    append_observation_row(
                        rows=rows,
                        series_dim_map=series_dim_map,
                        obs_dim_map=obs_dim_map,
                        obs_payload=obs_payload,
                        dataset_unit=dataset_unit,
                        dataset_updated=dataset_updated,
                        series_unit=series_unit,
                        series_updated=series_updated,
                    )

    if not rows:
        interesting = response_paths[
            response_paths["path_role"].astype(str).str.contains(
                "observation|series|dimension|attribute",
                case=False,
                na=False,
            )
        ]
        path_hint = ""
        if not interesting.empty:
            path_hint = "; sample paths: " + " | ".join(
                interesting["json_path"].astype(str).head(5).tolist()
            )

        out = pd.DataFrame(
            [
                {
                    "indicator_code": indicator_default,
                    "indicator_name": indicator_name_default,
                    "region_code": region_default,
                    "region_name": region_name_default,
                    "nace_code": nace_default,
                    "nace_name": nace_name_default,
                    "freq_code": freq_default,
                    "freq_name": freq_name_default,
                    "time_period": time_default,
                    "obs_value": pd.NA,
                    "unit": "",
                    "updated": "",
                    "source_url": source_url,
                    "source_status": "official_sdmx_data_response_loaded",
                    "validation_status": "parsed_no_observations_detected",
                    "current_use_in_scoring": "not_yet_used",
                    "notes": (
                        "A saved SDMX data response was loaded, but this parser did not "
                        "detect series or dataset-level observations. Inspect "
                        "ukrstat_observation_response_paths.csv manually." + path_hint
                    ),
                }
            ],
            columns=columns,
        )
    else:
        out = pd.DataFrame(rows, columns=columns).drop_duplicates()

    out.to_csv(UKRSTAT_OBSERVATION_PARSED_TABLE, index=False)

    return out

def build_observation_query_plan(
    discovery: pd.DataFrame,
    dimensions: pd.DataFrame,
    codelists: pd.DataFrame,
    metadata_clues: pd.DataFrame,
    registry_references: pd.DataFrame,
    dsd_dimension_candidates: pd.DataFrame,
    dimension_code_candidates: pd.DataFrame,
    observation_query_candidates: pd.DataFrame,
    observation_probe_results: pd.DataFrame,
    data_endpoint_discovery_results: pd.DataFrame,
    observation_matrix_probe_results: pd.DataFrame | None = None,
    availability_discovery_results: pd.DataFrame | None = None,
    availability_value_candidates: pd.DataFrame | None = None,
    parsed_observations: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create an audit-ready SDMX observation query plan."""
    ensure_dirs([TABLE_DIR])

    regional_found = False

    if discovery is not None and not discovery.empty and "id" in discovery.columns:
        regional_found = bool((discovery["id"] == DATAFLOW_ID).any())

    dimension_records_available = (
        dimensions is not None
        and not dimensions.empty
        and "implementation_status" in dimensions.columns
        and dimensions["implementation_status"]
        .astype(str)
        .str.contains("candidate_dimension_record", case=False, na=False)
        .any()
    )

    codelist_records_available = (
        codelists is not None
        and not codelists.empty
        and "implementation_status" in codelists.columns
        and codelists["implementation_status"]
        .astype(str)
        .str.contains("candidate_codelist_or_code_record", case=False, na=False)
        .any()
    )

    metadata_clues_available = (
        metadata_clues is not None
        and not metadata_clues.empty
        and "id" in metadata_clues.columns
        and metadata_clues["id"].fillna("").astype(str).str.len().gt(0).any()
    )

    dsd_reference_available = (
        registry_references is not None
        and not registry_references.empty
        and "artifact_id" in registry_references.columns
        and registry_references["artifact_id"]
        .astype(str)
        .str.contains(DSD_ID, case=False, na=False)
        .any()
    )

    dsd_dimensions_available = (
        dsd_dimension_candidates is not None
        and not dsd_dimension_candidates.empty
        and "implementation_status" in dsd_dimension_candidates.columns
        and dsd_dimension_candidates["implementation_status"]
        .astype(str)
        .str.contains("candidate_dimension_from_dsd", case=False, na=False)
        .any()
    )

    dimension_codes_available = (
        dimension_code_candidates is not None
        and not dimension_code_candidates.empty
        and "query_use_status" in dimension_code_candidates.columns
        and dimension_code_candidates["query_use_status"]
        .astype(str)
        .str.contains("candidate_pending_review", case=False, na=False)
        .any()
    )

    observation_query_candidates_available = (
        observation_query_candidates is not None
        and not observation_query_candidates.empty
        and "candidate_query_status" in observation_query_candidates.columns
        and observation_query_candidates["candidate_query_status"]
        .astype(str)
        .str.contains("shortlist_pending_review", case=False, na=False)
        .any()
    )

    observation_probe_available = (
        observation_probe_results is not None
        and not observation_probe_results.empty
        and "probe_name" in observation_probe_results.columns
    )

    observation_probe_success = (
        observation_probe_results is not None
        and not observation_probe_results.empty
        and "success_status" in observation_probe_results.columns
        and observation_probe_results["success_status"].astype(str).str.lower().eq("true").any()
    )

    data_endpoint_discovery_available = (
        data_endpoint_discovery_results is not None
        and not data_endpoint_discovery_results.empty
        and "probe_name" in data_endpoint_discovery_results.columns
    )

    data_endpoint_non_404 = (
        data_endpoint_discovery_results is not None
        and not data_endpoint_discovery_results.empty
        and "non_404_status" in data_endpoint_discovery_results.columns
        and data_endpoint_discovery_results["non_404_status"]
        .astype(str)
        .str.lower()
        .eq("true")
        .any()
    )

    data_endpoint_success = (
        data_endpoint_discovery_results is not None
        and not data_endpoint_discovery_results.empty
        and "success_status" in data_endpoint_discovery_results.columns
        and data_endpoint_discovery_results["success_status"]
        .astype(str)
        .str.lower()
        .eq("true")
        .any()
    )

    observation_matrix_available = (
        observation_matrix_probe_results is not None
        and not observation_matrix_probe_results.empty
        and "probe_name" in observation_matrix_probe_results.columns
    )

    observation_matrix_success = (
        observation_matrix_probe_results is not None
        and not observation_matrix_probe_results.empty
        and "success_status" in observation_matrix_probe_results.columns
        and observation_matrix_probe_results["success_status"]
        .astype(str)
        .str.lower()
        .eq("true")
        .any()
    )

    observation_matrix_has_values = (
        observation_matrix_probe_results is not None
        and not observation_matrix_probe_results.empty
        and "has_observations" in observation_matrix_probe_results.columns
        and observation_matrix_probe_results["has_observations"]
        .astype(str)
        .str.lower()
        .eq("true")
        .any()
    )

    availability_discovery_available = (
        availability_discovery_results is not None
        and not availability_discovery_results.empty
        and "probe_name" in availability_discovery_results.columns
    )

    availability_discovery_success = (
        availability_discovery_results is not None
        and not availability_discovery_results.empty
        and "success_status" in availability_discovery_results.columns
        and availability_discovery_results["success_status"]
        .astype(str)
        .str.lower()
        .eq("true")
        .any()
    )

    availability_discovery_has_values = (
        availability_discovery_results is not None
        and not availability_discovery_results.empty
        and "has_availability_values" in availability_discovery_results.columns
        and availability_discovery_results["has_availability_values"]
        .astype(str)
        .str.lower()
        .eq("true")
        .any()
    )

    availability_value_candidates_available = (
        availability_value_candidates is not None
        and not availability_value_candidates.empty
        and "query_use_status" in availability_value_candidates.columns
    )

    availability_value_candidates_success = (
        availability_value_candidates_available
        and availability_value_candidates["query_use_status"]
        .astype(str)
        .str.contains("availability_candidate_pending_validation", case=False, na=False)
        .any()
    )

    parsed_observations_available = (
        parsed_observations is not None
        and not parsed_observations.empty
        and "validation_status" in parsed_observations.columns
    )

    parsed_observations_success = (
        parsed_observations_available
        and parsed_observations["validation_status"]
        .astype(str)
        .str.contains("parsed_pending_validation", case=False, na=False)
        .any()
    )

    structure_available = (
        dimension_records_available
        or metadata_clues_available
        or dsd_reference_available
        or dsd_dimensions_available
        or dimension_codes_available
        or observation_query_candidates_available
    )

    if dsd_dimensions_available and dimension_codes_available:
        step_3_status = "complete"
        step_3_notes = (
            "Candidate DSD dimensions and dimension-code candidates were parsed. "
            "Analyst review is still required before observation query construction."
        )
    elif dsd_dimensions_available and codelist_records_available:
        step_3_status = "complete"
        step_3_notes = (
            "Candidate DSD dimensions and codelists were parsed. Analyst review "
            "is still required before observation query construction."
        )
    elif dimension_records_available and codelist_records_available:
        step_3_status = "complete"
        step_3_notes = (
            "Candidate dimensions and codelists parsed. Analyst review required."
        )
    elif (
        metadata_clues_available
        or codelist_records_available
        or dsd_reference_available
        or dsd_dimensions_available
        or dimension_codes_available
    ):
        step_3_status = "partial"
        step_3_notes = (
            "Relevant DSD references, codelists, concept schemes, candidate DSD "
            "dimensions, or dimension-code candidates were found, but final "
            "observation query construction still requires review."
        )
    else:
        step_3_status = "open"
        step_3_notes = (
            "Dimensions/codelists not parsed clearly yet. Inspect raw structure paths."
        )

    rows = [
        {
            "step": 1,
            "task": "Confirm regional accounts dataflow",
            "status": "complete" if regional_found else "open",
            "artifact": str(UKRSTAT_REGIONAL_ACCOUNTS_DISCOVERY_RAW),
            "notes": (
                f"{DATAFLOW_ID} discovered."
                if regional_found
                else f"{DATAFLOW_ID} not found in current metadata."
            ),
        },
        {
            "step": 2,
            "task": "Fetch SDMX structure metadata",
            "status": "partial" if structure_available else "open",
            "artifact": str(UKRSTAT_REGIONAL_ACCOUNTS_STRUCTURE_RAW),
            "notes": (
                "Structure metadata fetched and candidate DSD dimension/code records parsed."
                if dsd_dimensions_available or dimension_codes_available or observation_query_candidates_available
                else "Structure payload fetched and DSD/codelist/concept metadata clues found."
                if structure_available
                else "Structure fetch or dimension parsing requires review."
            ),
        },
        {
            "step": 3,
            "task": "Identify dimensions and codelists",
            "status": step_3_status,
            "artifact": (
                f"{UKRSTAT_REGIONAL_ACCOUNTS_DIMENSIONS_TABLE}; "
                f"{UKRSTAT_REGIONAL_ACCOUNTS_CODELISTS_TABLE}; "
                f"{UKRSTAT_REGIONAL_ACCOUNTS_METADATA_CLUES_TABLE}; "
                f"{UKRSTAT_REGISTRY_REFERENCES_TABLE}; "
                f"{UKRSTAT_DSD_DIMENSION_CANDIDATES_TABLE}; "
                f"{UKRSTAT_DIMENSION_CODE_CANDIDATES_TABLE}; "
                f"{UKRSTAT_OBSERVATION_QUERY_CANDIDATES_TABLE}; "
                f"{UKRSTAT_DSD_STRUCTURE_RAW}; "
                f"{UKRSTAT_DSD_REFERENCES_STRUCTURE_RAW}"
            ),
            "notes": step_3_notes,
        },
        {
            "step": 4,
            "task": "Select regional baseline measure",
            "status": "partial" if observation_query_candidates_available else "open",
            "artifact": (
                f"{UKRSTAT_OBSERVATION_QUERY_PLAN_TABLE}; "
                f"{UKRSTAT_OBSERVATION_QUERY_CANDIDATES_TABLE}"
            ),
            "notes": (
                "Observation-query candidates have been shortlisted for analyst review. "
                "Choose the appropriate regional accounts measure, geography code, "
                "NACE code, frequency, period, and units before any observation pull."
                if observation_query_candidates_available
                else (
                    "Choose appropriate regional accounts measure, geography dimension, "
                    "period, NACE, frequency, and units before observation pull."
                )
            ),
        },
        {
            "step": 5,
            "task": "Probe official observations",
            "status": (
                "partial"
                if (
                    observation_probe_success
                    or data_endpoint_success
                    or data_endpoint_non_404
                    or observation_matrix_success
                    or observation_matrix_has_values
                    or availability_discovery_success
                    or availability_discovery_has_values
                    or availability_value_candidates_success
                    or parsed_observations_success
                )
                else "open"
            ),
            "artifact": (
                f"{UKRSTAT_OBSERVATION_PROBE_TABLE}; "
                f"{UKRSTAT_OBSERVATION_PROBE_RAW}; "
                f"{UKRSTAT_DATA_ENDPOINT_DISCOVERY_TABLE}; "
                f"{UKRSTAT_DATA_ENDPOINT_DISCOVERY_RAW}; "
                f"{UKRSTAT_AVAILABILITY_DISCOVERY_TABLE}; "
                f"{UKRSTAT_AVAILABILITY_DISCOVERY_RAW}; "
                f"{UKRSTAT_AVAILABILITY_VALUE_CANDIDATES_TABLE}; "
                f"{UKRSTAT_OBSERVATION_DATA_RESPONSE_RAW}; "
                f"{UKRSTAT_OBSERVATION_RESPONSE_PATHS_TABLE}; "
                f"{UKRSTAT_OBSERVATION_PARSED_TABLE}; "
                f"{UKRSTAT_OBSERVATION_MATRIX_PROBE_TABLE}; "
                f"{UKRSTAT_OBSERVATION_MATRIX_SUCCESS_RAW}"
                if observation_probe_available or data_endpoint_discovery_available or observation_matrix_available or availability_discovery_available or parsed_observations_available
                else "future: data/raw/ukrstat_regional_accounts_observations_raw.csv"
            ),
            "notes": (
                "At least one official-observation endpoint, data-route, or "
                "availability-discovery probe returned a successful response. "
                "Use the parsed availability value candidates to select valid "
                "NACE/time-period values, then manually validate response content, "
                "units, geography mapping, NACE mapping, and time-period coverage "
                "before any scoring blend."
                if (
                    observation_probe_success
                    or data_endpoint_success
                    or observation_matrix_success
                    or availability_discovery_success
                    or parsed_observations_success
                )
                else (
                    "Availability-discovery probes found available SDMX values, and "
                    "availability value candidates were parsed for analyst review. "
                    "Use those candidates to select valid indicator, region, NACE, "
                    "frequency, and time-period combinations before requesting "
                    "official observations. Do not blend into scoring."
                    if availability_discovery_has_values or availability_value_candidates_success
                    else (
                        "At least one observation-matrix probe found a candidate "
                        "response with observation values. Manually validate the saved "
                        "matrix response, units, geography mapping, NACE mapping, and "
                        "time-period coverage before any scoring blend."
                        if observation_matrix_has_values
                        else (
                            "At least one data endpoint discovery probe returned a "
                            "non-404 response. Inspect the route response before testing "
                            "additional SDMX keys. Do not blend into scoring."
                            if data_endpoint_non_404
                            else (
                                "Official-observation endpoint, data-route discovery, "
                                "availability-discovery, and observation-matrix probes "
                                "were executed but did not yet confirm a valid observation "
                                "response. Do not blend into scoring."
                                if (
                                    observation_probe_available
                                    or data_endpoint_discovery_available
                                    or availability_discovery_available
                                    or observation_matrix_available
                                )
                                else (
                                    "Do not blend into scoring until observation values, "
                                    "geography mapping, NACE mapping, units, and time "
                                    "periods are validated."
                                )
                            )
                        )
                    )
                )
            ),
        },
    ]

    plan = pd.DataFrame(rows)
    plan.to_csv(UKRSTAT_OBSERVATION_QUERY_PLAN_TABLE, index=False)

    return plan


def build_ukrstat_oblast_baseline_placeholder(
    discovery: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create a safe oblast-level official baseline placeholder."""
    ensure_dirs([TABLE_DIR])

    if discovery is None:
        discovery = discover_regional_accounts_dataflows()

    primary_available = False

    if discovery is not None and not discovery.empty and "id" in discovery.columns:
        primary_available = bool((discovery["id"] == DATAFLOW_ID).any())

    rows = []

    for oblast in OBLASTS:
        rows.append(
            {
                "oblast": oblast,
                "official_regional_baseline_proxy": pd.NA,
                "source_family": "Ukrstat SDMX",
                "candidate_dataflow": DATAFLOW_ID,
                "source_status": (
                    "metadata_discovered"
                    if primary_available
                    else "metadata_pending"
                ),
                "implementation_status": "placeholder_pending_observation_query",
                "current_use_in_scoring": "not_yet_used",
                "notes": (
                    "Official regional baseline placeholder. Requires SDMX dimension "
                    "inspection and observation pull before blending into WARIS scoring."
                ),
            }
        )

    baseline = pd.DataFrame(rows)
    baseline = _add_official_baseline_control_fields(baseline)
    baseline.to_csv(UKRSTAT_OBLAST_BASELINE_TABLE, index=False)

    return baseline


def build_ukrstat_regional_accounts_artifacts() -> dict[str, pd.DataFrame]:
    """Build Ukrstat regional accounts discovery and transition outputs."""
    metadata = load_ukrstat_dataflow_metadata()
    discovery = discover_regional_accounts_dataflows(metadata)

    structure_payload, structure_attempts = fetch_regional_accounts_structure()
    dimensions, codelists = build_structure_dimension_tables(structure_payload)
    metadata_clues = build_metadata_clues_table(structure_payload)
    registry_references = build_registry_references_table(structure_payload)

    endpoint_probe = probe_ukrstat_endpoints()
    dsd_endpoint_probe = probe_dsd_specific_endpoints()

    dsd_structure_payload = fetch_best_dsd_structure_payload()
    dsd_codelist_payload = fetch_dsd_codelist_payload()

    dimension_payload = (
        dsd_structure_payload if dsd_structure_payload is not None else structure_payload
    )
    code_payload = (
        dsd_codelist_payload
        if dsd_codelist_payload is not None
        else dimension_payload
    )

    dsd_dimension_candidates = build_dsd_dimension_candidates_table(dimension_payload)
    dimension_code_candidates = build_dimension_code_candidates_table(code_payload)
    observation_query_candidates = build_observation_query_candidates_table(
        dimension_code_candidates
    )
    availability_discovery_results = probe_availability_discovery(
        observation_query_candidates
    )
    availability_value_candidates = parse_availability_discovery_values(
        availability_discovery_results
    )
    observation_probe_results = probe_first_observation_query(
        observation_query_candidates,
        availability_value_candidates=availability_value_candidates,
    )
    data_endpoint_discovery_results = probe_data_endpoint_discovery(
        observation_query_candidates,
        availability_value_candidates=availability_value_candidates,
    )
    observation_matrix_probe_results = probe_observation_matrix(
        observation_query_candidates,
        availability_value_candidates=availability_value_candidates,
    )
    confirmed_series_probe_results = probe_confirmed_series_without_time_filter(
        observation_query_candidates,
        availability_value_candidates=availability_value_candidates,
    )
    confirmed_series_parsed = parse_confirmed_series_response(
        confirmed_series_probe_results,
        availability_value_candidates=availability_value_candidates,
    )
    confirmed_oblast_baseline_candidates = build_confirmed_oblast_baseline_candidates(
        confirmed_series_parsed
    )
    (
        oblast_baseline_probe_results,
        oblast_baseline_candidates,
    ) = probe_all_oblast_baseline_series(
        observation_query_candidates,
        availability_value_candidates=availability_value_candidates,
    )
    parsed_observations = parse_observation_probe_response(
        observation_query_candidates=observation_query_candidates,
        observation_probe_results=observation_probe_results,
        data_endpoint_discovery_results=data_endpoint_discovery_results,
    )

    observation_response_paths = (
        pd.read_csv(UKRSTAT_OBSERVATION_RESPONSE_PATHS_TABLE)
        if UKRSTAT_OBSERVATION_RESPONSE_PATHS_TABLE.exists()
        else pd.DataFrame()
    )

    query_plan = build_observation_query_plan(
        discovery=discovery,
        dimensions=dimensions,
        codelists=codelists,
        metadata_clues=metadata_clues,
        registry_references=registry_references,
        dsd_dimension_candidates=dsd_dimension_candidates,
        dimension_code_candidates=dimension_code_candidates,
        observation_query_candidates=observation_query_candidates,
        observation_probe_results=observation_probe_results,
        data_endpoint_discovery_results=data_endpoint_discovery_results,
        observation_matrix_probe_results=observation_matrix_probe_results,
        availability_discovery_results=availability_discovery_results,
        availability_value_candidates=availability_value_candidates,
        parsed_observations=parsed_observations,
    )

    baseline = build_ukrstat_oblast_baseline_placeholder(discovery)

    return {
        "metadata": metadata,
        "regional_accounts_discovery": discovery,
        "structure_attempts": structure_attempts,
        "dimensions": dimensions,
        "codelists": codelists,
        "metadata_clues": metadata_clues,
        "registry_references": registry_references,
        "dsd_dimension_candidates": dsd_dimension_candidates,
        "dimension_code_candidates": dimension_code_candidates,
        "observation_query_candidates": observation_query_candidates,
        "observation_probe_results": observation_probe_results,
        "data_endpoint_discovery_results": data_endpoint_discovery_results,
        "observation_matrix_probe_results": observation_matrix_probe_results,
        "confirmed_series_probe_results": confirmed_series_probe_results,
        "confirmed_series_parsed": confirmed_series_parsed,
        "confirmed_oblast_baseline_candidates": confirmed_oblast_baseline_candidates,
        "oblast_baseline_probe_results": oblast_baseline_probe_results,
        "oblast_baseline_candidates": oblast_baseline_candidates,
        "availability_discovery_results": availability_discovery_results,
        "availability_value_candidates": availability_value_candidates,
        "parsed_observations": parsed_observations,
        "observation_response_paths": observation_response_paths,
        "endpoint_probe": endpoint_probe,
        "dsd_endpoint_probe": dsd_endpoint_probe,
        "query_plan": query_plan,
        "oblast_baseline": baseline,
    }


def main() -> None:
    """Run standalone Ukrstat regional accounts discovery and structure inspection."""
    artifacts = build_ukrstat_regional_accounts_artifacts()

    print("Ukrstat regional accounts artifacts created.")
    print(f"- Metadata rows: {len(artifacts['metadata'])}")
    print(f"- Regional account candidates: {len(artifacts['regional_accounts_discovery'])}")
    print(f"- Structure attempts: {len(artifacts['structure_attempts'])}")
    print(f"- Candidate dimensions: {len(artifacts['dimensions'])}")
    print(f"- Candidate codelists/codes: {len(artifacts['codelists'])}")
    print(f"- Metadata clues: {len(artifacts['metadata_clues'])}")
    print(f"- Registry references: {len(artifacts['registry_references'])}")
    print(f"- DSD dimension candidates: {len(artifacts['dsd_dimension_candidates'])}")
    print(f"- Dimension code candidates: {len(artifacts['dimension_code_candidates'])}")
    print(f"- Observation query candidates: {len(artifacts['observation_query_candidates'])}")
    print(f"- Observation endpoint probes: {len(artifacts['observation_probe_results'])}")
    print(f"- Data endpoint discovery probes: {len(artifacts['data_endpoint_discovery_results'])}")
    print(f"- Observation matrix probes: {len(artifacts['observation_matrix_probe_results'])}")
    print(f"- Confirmed series probes: {len(artifacts['confirmed_series_probe_results'])}")
    print(f"- Confirmed series parsed rows: {len(artifacts['confirmed_series_parsed'])}")
    print(
        f"- Confirmed oblast baseline candidates: "
        f"{len(artifacts['confirmed_oblast_baseline_candidates'])}"
    )
    print(f"- All-oblast baseline probes: {len(artifacts['oblast_baseline_probe_results'])}")
    print(f"- All-oblast baseline candidates: {len(artifacts['oblast_baseline_candidates'])}")
    print(f"- Availability discovery probes: {len(artifacts['availability_discovery_results'])}")
    print(f"- Availability value candidates: {len(artifacts['availability_value_candidates'])}")
    print(f"- Parsed observation rows: {len(artifacts['parsed_observations'])}")
    print(f"- Observation response paths: {len(artifacts['observation_response_paths'])}")
    print(f"- Endpoint probes: {len(artifacts['endpoint_probe'])}")
    print(f"- DSD endpoint probes: {len(artifacts['dsd_endpoint_probe'])}")
    print(f"- Query plan rows: {len(artifacts['query_plan'])}")
    print(f"- Oblast baseline rows: {len(artifacts['oblast_baseline'])}")
    print(f"- Discovery table: {UKRSTAT_REGIONAL_ACCOUNTS_DISCOVERY_RAW}")
    print(f"- Structure attempts: {UKRSTAT_REGIONAL_ACCOUNTS_STRUCTURE_ATTEMPTS_RAW}")
    print(f"- Structure paths: {UKRSTAT_REGIONAL_ACCOUNTS_STRUCTURE_PATHS_RAW}")
    print(f"- Saved best DSD payload: {UKRSTAT_DSD_STRUCTURE_RAW}")
    print(f"- Saved best DSD paths: {UKRSTAT_DSD_STRUCTURE_PATHS_RAW}")
    print(f"- Saved DSD references payload: {UKRSTAT_DSD_REFERENCES_STRUCTURE_RAW}")
    print(f"- Saved DSD references paths: {UKRSTAT_DSD_REFERENCES_STRUCTURE_PATHS_RAW}")
    print(f"- Dimensions table: {UKRSTAT_REGIONAL_ACCOUNTS_DIMENSIONS_TABLE}")
    print(f"- Codelists table: {UKRSTAT_REGIONAL_ACCOUNTS_CODELISTS_TABLE}")
    print(f"- Metadata clues table: {UKRSTAT_REGIONAL_ACCOUNTS_METADATA_CLUES_TABLE}")
    print(f"- Registry references table: {UKRSTAT_REGISTRY_REFERENCES_TABLE}")
    print(f"- DSD dimension candidates table: {UKRSTAT_DSD_DIMENSION_CANDIDATES_TABLE}")
    print(f"- Dimension code candidates table: {UKRSTAT_DIMENSION_CODE_CANDIDATES_TABLE}")
    print(f"- Observation query candidates table: {UKRSTAT_OBSERVATION_QUERY_CANDIDATES_TABLE}")
    print(f"- Observation endpoint probe table: {UKRSTAT_OBSERVATION_PROBE_TABLE}")
    print(f"- Observation endpoint raw response: {UKRSTAT_OBSERVATION_PROBE_RAW}")
    print(f"- Data endpoint discovery table: {UKRSTAT_DATA_ENDPOINT_DISCOVERY_TABLE}")
    print(f"- Data endpoint discovery raw response: {UKRSTAT_DATA_ENDPOINT_DISCOVERY_RAW}")
    print(f"- Observation matrix probe table: {UKRSTAT_OBSERVATION_MATRIX_PROBE_TABLE}")
    print(f"- Observation matrix success raw response: {UKRSTAT_OBSERVATION_MATRIX_SUCCESS_RAW}")
    print(f"- Confirmed series probe table: {UKRSTAT_CONFIRMED_SERIES_PROBE_TABLE}")
    print(f"- Confirmed series raw response: {UKRSTAT_CONFIRMED_SERIES_RAW}")
    print(f"- Confirmed series parsed table: {UKRSTAT_CONFIRMED_SERIES_PARSED_TABLE}")
    print(
        f"- Confirmed oblast baseline candidates: "
        f"{UKRSTAT_CONFIRMED_OBLAST_BASELINE_CANDIDATES_TABLE}; "
                f"{UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE}; "
                f"{UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE}"
    )
    print(f"- All-oblast baseline probe table: {UKRSTAT_OBLAST_BASELINE_PROBE_RESULTS_TABLE}")
    print(f"- All-oblast baseline candidates: {UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE}")
    print(f"- All-oblast success raw folder: {UKRSTAT_OBLAST_BASELINE_SUCCESS_DIR}")
    print(f"- Availability discovery table: {UKRSTAT_AVAILABILITY_DISCOVERY_TABLE}")
    print(f"- Availability discovery raw response: {UKRSTAT_AVAILABILITY_DISCOVERY_RAW}")
    print(f"- Availability value candidates table: {UKRSTAT_AVAILABILITY_VALUE_CANDIDATES_TABLE}")
    print(f"- Observation data raw response: {UKRSTAT_OBSERVATION_DATA_RESPONSE_RAW}")
    print(f"- Observation response paths table: {UKRSTAT_OBSERVATION_RESPONSE_PATHS_TABLE}")
    print(f"- Parsed observation table: {UKRSTAT_OBSERVATION_PARSED_TABLE}")
    print(f"- Endpoint probe table: {UKRSTAT_ENDPOINT_PROBE_TABLE}")
    print(f"- DSD endpoint probe table: {UKRSTAT_DSD_ENDPOINT_PROBE_TABLE}")
    print(f"- Query plan: {UKRSTAT_OBSERVATION_QUERY_PLAN_TABLE}")
    print(f"- Baseline table: {UKRSTAT_OBLAST_BASELINE_TABLE}")


if __name__ == "__main__":
    main()