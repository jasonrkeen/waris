"""Data collection and synthetic fallback data for WARIS.

The prototype ships with synthetic oblast/sector observations so it can run
without keys or source availability. The live/source-backed enrichment layer in
src/live_data.py can then blend public-source inputs into these fields.

Important:
- The fields are risk proxies, not claims of misconduct.
- The model operates at sector/oblast level.
- Scores are prioritization signals for human AML/supervisory review only.

Current official-data posture:
- Ukrstat regional-account observations now produce validation-only oblast GRP
  baseline candidates in separate artifacts.
- Those official values are not blended into scoring until unit, geography,
  NACE, indicator meaning, and period coverage are validated.
- Expanded Prozorro procurement features are generated in separate review-only
  artifacts and are not part of the synthetic fallback dataset.
- Wartime AML/CFT typology and FIU/SFMS context artifacts are generated in
  separate reference modules and are not part of the synthetic fallback dataset.
- This module keeps the canonical WARIS oblast names used by the synthetic
  fallback dataset and provides crosswalks for Ukrstat-style oblast names,
  procurement feature validation, typology/FIU layer alignment, and operational
  review controls such as analyst review, false-positive controls, source
  freshness, and run-manifest documentation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import RAW_DIR, RANDOM_SEED, SOURCES, TABLE_DIR
from .utils import ensure_dirs

try:
    from .config import (
        WARTIME_AML_TYPOLOGY_CURRENT_USE,
        WARTIME_AML_TYPOLOGY_PROHIBITED_USE,
        WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE,
        FIU_CONTEXT_CURRENT_USE,
        FIU_CONTEXT_PROHIBITED_USE,
        FIU_CONTEXT_PRODUCTION_SCORE_CHANGE,
        ANALYST_REVIEW_CURRENT_USE,
        ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
        ANALYST_REVIEW_HUMAN_REVIEW_REQUIRED,
        ANALYST_REVIEW_AUTOMATED_ADVERSE_ACTION_ALLOWED,
        ANALYST_REVIEW_ENTITY_LEVEL_FINDINGS_ALLOWED,
        FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
        SOURCE_FRESHNESS_CURRENT_USE,
        SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
        RUN_MANIFEST_CURRENT_USE,
        RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
    )
except ImportError:
    WARTIME_AML_TYPOLOGY_CURRENT_USE = (
        "literature_support_and_typology_reference_only"
    )
    WARTIME_AML_TYPOLOGY_PROHIBITED_USE = "direct_scoring_without_change_control"
    WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE = "none"
    FIU_CONTEXT_CURRENT_USE = "official_fiu_context_and_typology_support_only"
    FIU_CONTEXT_PROHIBITED_USE = "direct_scoring_without_change_control"
    FIU_CONTEXT_PRODUCTION_SCORE_CHANGE = "none"
    ANALYST_REVIEW_CURRENT_USE = "analyst_review_workflow_only"
    ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE = "none"
    ANALYST_REVIEW_HUMAN_REVIEW_REQUIRED = True
    ANALYST_REVIEW_AUTOMATED_ADVERSE_ACTION_ALLOWED = False
    ANALYST_REVIEW_ENTITY_LEVEL_FINDINGS_ALLOWED = False
    FALSE_POSITIVE_CONTROLS_CURRENT_USE = "human_review_support_only"
    FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE = "none"
    SOURCE_FRESHNESS_CURRENT_USE = "source_freshness_monitoring_only"
    SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE = "none"
    RUN_MANIFEST_CURRENT_USE = "run_manifest_documentation"
    RUN_MANIFEST_PRODUCTION_SCORE_CHANGE = "none"


# Canonical model geography.
# Live-source enrichment layers should map back to these names so every
# oblast/sector observation remains aligned across the pipeline.
OBLASTS = [
    "Cherkasy",
    "Chernihiv",
    "Chernivtsi",
    "Dnipropetrovsk",
    "Donetsk",
    "Ivano-Frankivsk",
    "Kharkiv",
    "Kherson",
    "Khmelnytskyi",
    "Kirovohrad",
    "Kyiv",
    "Luhansk",
    "Lviv",
    "Mykolaiv",
    "Odesa",
    "Poltava",
    "Rivne",
    "Sumy",
    "Ternopil",
    "Vinnytsia",
    "Volyn",
    "Zakarpattia",
    "Zaporizhzhia",
    "Zhytomyr",
    "Kyiv City",
]

# Ukrstat/KATOTTG regional-account responses use adjectival oblast names
# such as "Cherkaska" rather than the canonical English names used inside WARIS
# such as "Cherkasy". Keep this mapping explicit so future validation or
# integration modules do not silently mismatch official baseline rows.
UKRSTAT_OBLAST_NAME_TO_WARIS_OBLAST = {
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

WARIS_OBLAST_TO_UKRSTAT_OBLAST_NAME = {
    waris_name: ukrstat_name
    for ukrstat_name, waris_name in UKRSTAT_OBLAST_NAME_TO_WARIS_OBLAST.items()
    if ukrstat_name not in {"Kyiv", "City of Kyiv"}
}

# Add a clearer preferred label for Kyiv City.
WARIS_OBLAST_TO_UKRSTAT_OBLAST_NAME["Kyiv City"] = "Kyiv"

SECTORS = [
    "Agriculture and grain trade",
    "Construction and reconstruction",
    "Fuel and logistics",
    "Retail and consumer goods",
    "Financial and payment services",
    "Defense-adjacent manufacturing",
]

# Conservative procurement-keyword-to-sector mapping used for documentation and
# validation of the expanded Prozorro procurement feature module. The actual
# live feature extraction happens in src.prozorro_procurement_features; this
# mapping documents expected sector logic and keeps the taxonomy auditable.
PROZORRO_SECTOR_KEYWORD_CROSSWALK = {
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
}

PROZORRO_RECONSTRUCTION_EMERGENCY_KEYWORDS = [
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

# Conceptual alignment between official/literature typology themes and WARIS
# risk layers. This is a documentation bridge only. The actual typology and FIU
# artifacts are generated in src.wartime_aml_typology_register and
# src.fiu_official_context.
WARTIME_AML_TYPOLOGY_LAYER_ALIGNMENT = {
    "sanctions_evasion_and_aggressor_state_exposure": [
        "sanctions_exposure_risk",
        "tbml_risk",
        "ownership_opacity_risk",
    ],
    "beneficial_ownership_opacity": [
        "ownership_opacity_risk",
        "procurement_integrity_risk",
        "sanctions_exposure_risk",
    ],
    "reconstruction_and_emergency_procurement_misuse": [
        "procurement_integrity_risk",
        "ownership_opacity_risk",
        "revenue_anomaly_risk",
    ],
    "humanitarian_flow_diversion_and_misuse": [
        "tbml_risk",
        "procurement_integrity_risk",
        "financial_supervision_exposure",
    ],
    "digital_asset_and_crypto_enabled_finance": [
        "financial_supervision_exposure",
        "sanctions_exposure_risk",
        "tbml_risk",
    ],
    "temporarily_occupied_territory_account_exposure": [
        "conflict_plausibility_gap",
        "sanctions_exposure_risk",
        "financial_supervision_exposure",
    ],
    "it_sector_payment_and_cash_withdrawal_typologies": [
        "financial_supervision_exposure",
        "revenue_anomaly_risk",
        "tbml_risk",
    ],
    "individual_entrepreneur_account_misuse": [
        "ownership_opacity_risk",
        "financial_supervision_exposure",
        "revenue_anomaly_risk",
    ],
    "cash_placement_through_intermediaries": [
        "sanctions_exposure_risk",
        "ownership_opacity_risk",
        "financial_supervision_exposure",
    ],
    "cross_border_intelligence_and_sanctions_data_integration_gaps": [
        "financial_supervision_exposure",
        "sanctions_exposure_risk",
        "ownership_opacity_risk",
    ],
}

FIU_CONTEXT_LAYER_ALIGNMENT = {
    "financial_transaction_reporting_statistics": [
        "financial_supervision_exposure",
    ],
    "nabu_case_referral_context": [
        "ownership_opacity_risk",
        "procurement_integrity_risk",
        "financial_supervision_exposure",
    ],
    "war_and_terrorism_financing": [
        "sanctions_exposure_risk",
        "conflict_plausibility_gap",
        "tbml_risk",
    ],
    "corruption_laundering": [
        "ownership_opacity_risk",
        "procurement_integrity_risk",
        "financial_supervision_exposure",
    ],
    "budget_and_state_assets": [
        "procurement_integrity_risk",
        "ownership_opacity_risk",
        "revenue_anomaly_risk",
    ],
    "humanitarian_reconstruction_finance": [
        "procurement_integrity_risk",
        "tbml_risk",
        "financial_supervision_exposure",
    ],
    "international_cooperation_and_fiu_exchange": [
        "financial_supervision_exposure",
        "sanctions_exposure_risk",
    ],
}

# Documentation-only operational artifact alignment. These are not scoring
# inputs. They explain where review-support artifacts sit in the broader WARIS
# workflow so source confidence, report generation, and future README/model-card
# work can stay consistent.
OPERATIONAL_REVIEW_ARTIFACT_ALIGNMENT = {
    "analyst_review_workflow": {
        "artifact_outputs": [
            "analyst_review_queue.csv",
            "analyst_review_questions.csv",
            "review_disposition_template.csv",
            "analyst_review_summary.csv",
        ],
        "workflow_stage": "model_signal_to_human_review",
        "current_use": ANALYST_REVIEW_CURRENT_USE,
        "production_score_change": ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
        "human_review_required": ANALYST_REVIEW_HUMAN_REVIEW_REQUIRED,
        "automated_adverse_action_allowed": ANALYST_REVIEW_AUTOMATED_ADVERSE_ACTION_ALLOWED,
        "entity_level_findings_allowed": ANALYST_REVIEW_ENTITY_LEVEL_FINDINGS_ALLOWED,
    },
    "false_positive_controls": {
        "artifact_outputs": [
            "false_positive_risk_register.csv",
            "false_positive_controls.csv",
            "false_positive_review_checklist.csv",
            "false_positive_summary.csv",
        ],
        "workflow_stage": "human_review_quality_control",
        "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        "production_score_change": FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE,
        "human_review_required": True,
        "automated_adverse_action_allowed": False,
        "entity_level_findings_allowed": False,
    },
    "source_freshness": {
        "artifact_outputs": [
            "source_freshness_inventory.csv",
            "source_freshness_assessment.csv",
            "source_freshness_replacement_priorities.csv",
            "source_freshness_summary.csv",
        ],
        "workflow_stage": "source_monitoring_and_refresh_planning",
        "current_use": SOURCE_FRESHNESS_CURRENT_USE,
        "production_score_change": SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
        "human_review_required": True,
        "automated_adverse_action_allowed": False,
        "entity_level_findings_allowed": False,
    },
    "run_manifest": {
        "artifact_outputs": [
            "run_manifest.csv",
            "run_manifest_summary.csv",
            "run_manifest.json",
        ],
        "workflow_stage": "reproducibility_and_output_inventory",
        "current_use": RUN_MANIFEST_CURRENT_USE,
        "production_score_change": RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
        "human_review_required": True,
        "automated_adverse_action_allowed": False,
        "entity_level_findings_allowed": False,
    },
}


def normalize_oblast_name(name: str) -> str:
    """Normalize live/official source geography names to canonical WARIS names.

    This is intentionally conservative. If a source name is unknown, the original
    stripped value is returned so downstream validation can detect mismatches
    rather than forcing an incorrect mapping.
    """
    if name is None:
        return ""

    cleaned = str(name).strip()

    if cleaned in OBLASTS:
        return cleaned

    return UKRSTAT_OBLAST_NAME_TO_WARIS_OBLAST.get(cleaned, cleaned)


def build_oblast_name_crosswalk() -> pd.DataFrame:
    """Build a crosswalk between WARIS and Ukrstat-style oblast names.

    The crosswalk is useful for future validation and integration steps that
    compare canonical WARIS synthetic/fallback rows against official Ukrstat
    baseline candidates. It does not blend official data into scoring.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    rows = []

    for oblast in OBLASTS:
        ukrstat_name = WARIS_OBLAST_TO_UKRSTAT_OBLAST_NAME.get(oblast, oblast)
        rows.append(
            {
                "waris_oblast": oblast,
                "ukrstat_oblast_name": ukrstat_name,
                "normalization_status": "mapped",
                "current_use_in_scoring": "not_a_scoring_field",
                "notes": (
                    "Name crosswalk only. Supports validation of official Ukrstat "
                    "baseline candidates against canonical WARIS geography."
                ),
            }
        )

    df = pd.DataFrame(rows)

    df.to_csv(RAW_DIR / "oblast_name_crosswalk.csv", index=False)
    df.to_csv(TABLE_DIR / "oblast_name_crosswalk.csv", index=False)

    return df


def build_prozorro_procurement_crosswalk() -> pd.DataFrame:
    """Build a documented sector-keyword crosswalk for Prozorro features.

    This crosswalk supports review of the expanded Prozorro procurement feature
    module. It is documentation and validation support only. It does not create
    procurement scores and does not alter the synthetic fallback dataset.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    rows = []

    for sector, keywords in PROZORRO_SECTOR_KEYWORD_CROSSWALK.items():
        for keyword in keywords:
            rows.append(
                {
                    "crosswalk_type": "sector_keyword",
                    "waris_sector": sector,
                    "keyword": keyword,
                    "current_use_in_scoring": "not_a_scoring_field",
                    "notes": (
                        "Supports review of conservative keyword mapping used by "
                        "expanded Prozorro procurement feature artifacts."
                    ),
                }
            )

    for keyword in PROZORRO_RECONSTRUCTION_EMERGENCY_KEYWORDS:
        rows.append(
            {
                "crosswalk_type": "reconstruction_emergency_keyword",
                "waris_sector": "cross_sector_indicator",
                "keyword": keyword,
                "current_use_in_scoring": "not_a_scoring_field",
                "notes": (
                    "Supports review of reconstruction/emergency keyword exposure "
                    "in expanded Prozorro procurement feature artifacts."
                ),
            }
        )

    df = pd.DataFrame(rows)

    df.to_csv(RAW_DIR / "prozorro_procurement_crosswalk.csv", index=False)
    df.to_csv(TABLE_DIR / "prozorro_procurement_crosswalk.csv", index=False)

    return df



def build_wartime_aml_typology_layer_alignment_crosswalk() -> pd.DataFrame:
    """Build a documentation-only typology-to-WARIS-layer crosswalk.

    This supports review of the wartime AML/CFT typology register. It does not
    create scores and does not alter the synthetic fallback dataset.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    rows = []

    from .config import WARTIME_PUBLIC_ALIGNMENT_THEMES
    for typology_theme, layers in WARTIME_AML_TYPOLOGY_LAYER_ALIGNMENT.items():
        if typology_theme not in WARTIME_PUBLIC_ALIGNMENT_THEMES:
            continue
        for layer in layers:
            rows.append(
                {
                    "crosswalk_type": "wartime_aml_typology_layer_alignment",
                    "reference_theme": typology_theme,
                    "waris_layer_candidate": layer,
                    "current_use": WARTIME_AML_TYPOLOGY_CURRENT_USE,
                    "prohibited_use": WARTIME_AML_TYPOLOGY_PROHIBITED_USE,
                    "production_score_change": WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE,
                    "current_use_in_scoring": "not_a_scoring_field",
                    "notes": (
                        "Conceptual typology-to-layer alignment only. Generated for "
                        "documentation, source-confidence, and future feature planning."
                    ),
                }
            )

    df = pd.DataFrame(rows)

    df.to_csv(RAW_DIR / "wartime_aml_typology_layer_alignment_crosswalk.csv", index=False)
    df.to_csv(
        TABLE_DIR / "wartime_aml_typology_layer_alignment_crosswalk.csv",
        index=False,
    )

    return df


def build_fiu_context_layer_alignment_crosswalk() -> pd.DataFrame:
    """Build a documentation-only FIU-context-to-WARIS-layer crosswalk.

    This supports review of official FIU/SFMS context artifacts. It does not
    create scores and does not alter the synthetic fallback dataset.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    rows = []

    from .config import FIU_PUBLIC_ALIGNMENT_THEMES

    for fiu_context_theme, layers in FIU_CONTEXT_LAYER_ALIGNMENT.items():
        if fiu_context_theme not in FIU_PUBLIC_ALIGNMENT_THEMES:
            continue
        for layer in layers:
            rows.append(
                {
                    "crosswalk_type": "fiu_context_layer_alignment",
                    "reference_theme": fiu_context_theme,
                    "waris_layer_candidate": layer,
                    "current_use": FIU_CONTEXT_CURRENT_USE,
                    "prohibited_use": FIU_CONTEXT_PROHIBITED_USE,
                    "production_score_change": FIU_CONTEXT_PRODUCTION_SCORE_CHANGE,
                    "current_use_in_scoring": "not_a_scoring_field",
                    "notes": (
                        "Official FIU/SFMS context-to-layer alignment only. Generated "
                        "for documentation, source-confidence, and future feature planning."
                    ),
                }
            )

    df = pd.DataFrame(rows)

    df.to_csv(RAW_DIR / "fiu_context_layer_alignment_crosswalk.csv", index=False)
    df.to_csv(TABLE_DIR / "fiu_context_layer_alignment_crosswalk.csv", index=False)

    return df


def build_operational_review_artifact_crosswalk() -> pd.DataFrame:
    """Build a documentation-only operational artifact crosswalk.

    This crosswalk documents analyst-review, false-positive, source-freshness,
    and run-manifest artifacts. It does not create scores and does not alter the
    synthetic fallback dataset.
    """
    ensure_dirs([RAW_DIR, TABLE_DIR])

    rows = []

    for artifact_family, spec in OPERATIONAL_REVIEW_ARTIFACT_ALIGNMENT.items():
        for output_name in spec["artifact_outputs"]:
            rows.append(
                {
                    "crosswalk_type": "operational_review_artifact_alignment",
                    "artifact_family": artifact_family,
                    "artifact_output": output_name,
                    "workflow_stage": spec["workflow_stage"],
                    "current_use": spec["current_use"],
                    "production_score_change": spec["production_score_change"],
                    "human_review_required": spec["human_review_required"],
                    "automated_adverse_action_allowed": spec[
                        "automated_adverse_action_allowed"
                    ],
                    "entity_level_findings_allowed": spec[
                        "entity_level_findings_allowed"
                    ],
                    "current_use_in_scoring": "not_a_scoring_field",
                    "notes": (
                        "Operational documentation and human-review support only. "
                        "This artifact does not change WARIS scores, risk bands, "
                        "review rationales, or Monte Carlo outputs."
                    ),
                }
            )

    df = pd.DataFrame(rows)

    df.to_csv(RAW_DIR / "operational_review_artifact_crosswalk.csv", index=False)
    df.to_csv(TABLE_DIR / "operational_review_artifact_crosswalk.csv", index=False)

    return df


def build_source_register() -> pd.DataFrame:
    """Build the model source register from config.SOURCES."""
    ensure_dirs([RAW_DIR, TABLE_DIR])
    df = pd.DataFrame(SOURCES)
    df.to_csv(RAW_DIR / "source_register.csv", index=False)
    df.to_csv(TABLE_DIR / "source_register.csv", index=False)
    return df


def build_synthetic_oblast_sector_data(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Create a transparent synthetic fallback dataset for prototype scoring.

    The model expects oblast/sector observations with proxy fields for:

    - revenue anomaly
    - sanctions exposure
    - procurement exposure
    - ownership opacity
    - trade dislocation / TBML exposure
    - conflict intensity
    - financial supervision exposure

    These values are intentionally synthetic. They are designed to preserve the
    shape of the model and allow the full pipeline to run even when live sources
    are unavailable.
    """
    rng = np.random.default_rng(seed)
    rows = []

    frontline_oblasts = {
        "Donetsk",
        "Luhansk",
        "Kharkiv",
        "Kherson",
        "Zaporizhzhia",
        "Mykolaiv",
        "Sumy",
        "Chernihiv",
        "Dnipropetrovsk",
        "Odesa",
    }

    highest_conflict_oblasts = {
        "Donetsk",
        "Luhansk",
        "Kherson",
        "Zaporizhzhia",
        "Kharkiv",
    }

    western_lower_conflict_oblasts = {
        "Lviv",
        "Zakarpattia",
        "Volyn",
        "Ivano-Frankivsk",
        "Chernivtsi",
    }

    logistics_hubs = {
        "Odesa",
        "Lviv",
        "Kyiv",
        "Kyiv City",
        "Dnipropetrovsk",
        "Zakarpattia",
        "Volyn",
    }

    reconstruction_focus_oblasts = {
        "Kyiv",
        "Kyiv City",
        "Kharkiv",
        "Chernihiv",
        "Sumy",
        "Mykolaiv",
        "Kherson",
        "Zaporizhzhia",
    }

    sector_growth_assumptions = {
        "Agriculture and grain trade": (2, 12),
        "Construction and reconstruction": (15, 18),
        "Fuel and logistics": (18, 20),
        "Retail and consumer goods": (-5, 10),
        "Financial and payment services": (10, 14),
        "Defense-adjacent manufacturing": (22, 24),
    }

    procurement_sensitive_sectors = {
        "Construction and reconstruction",
        "Defense-adjacent manufacturing",
        "Fuel and logistics",
    }

    sanctions_sensitive_sectors = {
        "Fuel and logistics",
        "Defense-adjacent manufacturing",
        "Agriculture and grain trade",
    }

    ownership_opacity_sensitive_sectors = {
        "Financial and payment services",
        "Fuel and logistics",
        "Agriculture and grain trade",
    }

    trade_dislocation_sensitive_sectors = {
        "Agriculture and grain trade",
        "Fuel and logistics",
    }

    financial_centers = {
        "Kyiv City",
        "Kyiv",
        "Lviv",
        "Odesa",
        "Dnipropetrovsk",
        "Kharkiv",
    }

    for oblast in OBLASTS:
        base_conflict = 65 if oblast in frontline_oblasts else 25

        if oblast in highest_conflict_oblasts:
            base_conflict += 20

        if oblast in western_lower_conflict_oblasts:
            base_conflict -= 10

        for sector in SECTORS:
            prewar_revenue_index = rng.normal(100, 12)

            growth_mean, growth_sd = sector_growth_assumptions[sector]
            sector_growth = rng.normal(growth_mean, growth_sd)

            conflict_penalty = base_conflict * rng.uniform(0.05, 0.25)

            current_revenue_index = (
                prewar_revenue_index
                + sector_growth
                - conflict_penalty
                + rng.normal(0, 10)
            )

            procurement = rng.normal(35, 18)
            if sector in procurement_sensitive_sectors:
                procurement += 25
            if oblast in reconstruction_focus_oblasts:
                procurement += 15

            sanctions_exposure = rng.normal(20, 13)
            if sector in sanctions_sensitive_sectors:
                sanctions_exposure += 18
            if oblast in logistics_hubs:
                sanctions_exposure += 8

            ownership_opacity = rng.normal(35, 15)
            if sector in ownership_opacity_sensitive_sectors:
                ownership_opacity += 10

            trade_dislocation = rng.normal(25, 15)
            if sector in trade_dislocation_sensitive_sectors:
                trade_dislocation += 25
            if oblast in frontline_oblasts or oblast in logistics_hubs:
                trade_dislocation += 10

            financial_supervision_exposure = rng.normal(30, 12)
            if sector == "Financial and payment services":
                financial_supervision_exposure += 45
            if oblast in financial_centers:
                financial_supervision_exposure += 10

            rows.append(
                {
                    "oblast": oblast,
                    "sector": sector,
                    "prewar_revenue_index_2021": max(prewar_revenue_index, 20),
                    "current_revenue_index": max(current_revenue_index, 1),
                    "conflict_intensity_proxy": np.clip(
                        base_conflict + rng.normal(0, 12), 0, 100
                    ),
                    "procurement_awards_proxy": np.clip(procurement, 0, 100),
                    "sanctions_counterparty_proxy": np.clip(
                        sanctions_exposure, 0, 100
                    ),
                    "ownership_opacity_proxy": np.clip(ownership_opacity, 0, 100),
                    "trade_dislocation_proxy": np.clip(trade_dislocation, 0, 100),
                    "financial_supervision_proxy": np.clip(
                        financial_supervision_exposure, 0, 100
                    ),
                }
            )

    df = pd.DataFrame(rows)

    ensure_dirs([RAW_DIR])
    df.to_csv(RAW_DIR / "synthetic_oblast_sector_inputs.csv", index=False)

    # Build crosswalks alongside the synthetic data so the project has stable
    # validation bridges ready for official baseline, expanded procurement,
    # wartime AML typology, and official FIU/SFMS context review.
    build_oblast_name_crosswalk()
    build_prozorro_procurement_crosswalk()
    build_wartime_aml_typology_layer_alignment_crosswalk()
    build_fiu_context_layer_alignment_crosswalk()
    build_operational_review_artifact_crosswalk()

    return df
