"""Wartime AML/CFT typology register for WARIS.

This module converts literature-supported wartime AML/CFT risk themes into a
transparent typology register for model governance, source support, and future
feature design.

It does not change WARIS production scoring.

This module is intentionally separate from the official FIU/SFMS context module,
expanded Prozorro procurement feature module, official Ukrstat baseline module,
analyst-review workflow, false-positive controls, source-freshness monitoring,
and run-manifest documentation. Downstream bridge/review modules may compare
these artifacts, but this register remains literature-support context only.

Current use:
    literature_support_and_typology_reference_only

Prohibited use:
    direct_scoring_without_change_control

Production score change:
    none

Primary source basis:
    Utenkova, K. (2026). Anti-money laundering as an instrument of economic
    security: Wartime adaptation of AML/CFT frameworks in Ukraine.

Outputs:
    outputs/tables/waris_wartime_aml_typology_register.csv
    outputs/tables/waris_wartime_aml_typology_layer_map.csv
    outputs/tables/waris_wartime_aml_typology_summary.csv

Operational-control posture:
    Analyst-review, false-positive, source-freshness, and run-manifest artifacts
    are downstream documentation controls only. They are not consumed by this
    module and do not approve typology-based scoring.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import TABLE_DIR
from .utils import add_constant_control_fields, ensure_dirs, safe_write_csv


try:
    from .config import (
        WARTIME_AML_TYPOLOGY_REGISTER_TABLE,
        WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE,
        WARTIME_AML_TYPOLOGY_SUMMARY_TABLE,
        WARTIME_AML_TYPOLOGY_CURRENT_USE,
        WARTIME_AML_TYPOLOGY_PROHIBITED_USE,
        WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE,
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
    WARTIME_AML_TYPOLOGY_REGISTER_TABLE = (
        TABLE_DIR / "waris_wartime_aml_typology_register.csv"
    )
    WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE = (
        TABLE_DIR / "waris_wartime_aml_typology_layer_map.csv"
    )
    WARTIME_AML_TYPOLOGY_SUMMARY_TABLE = (
        TABLE_DIR / "waris_wartime_aml_typology_summary.csv"
    )
    WARTIME_AML_TYPOLOGY_CURRENT_USE = (
        "literature_support_and_typology_reference_only"
    )
    WARTIME_AML_TYPOLOGY_PROHIBITED_USE = "direct_scoring_without_change_control"
    WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE = "none"
    ANALYST_REVIEW_CURRENT_USE = "analyst_review_workflow_only"
    ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE = "none"
    FALSE_POSITIVE_CONTROLS_CURRENT_USE = "human_review_support_only"
    FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE = "none"
    SOURCE_FRESHNESS_CURRENT_USE = "source_freshness_monitoring_only"
    SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE = "none"
    RUN_MANIFEST_CURRENT_USE = "run_manifest_documentation"
    RUN_MANIFEST_PRODUCTION_SCORE_CHANGE = "none"


TYPOLOGY_REGISTER_TABLE = WARTIME_AML_TYPOLOGY_REGISTER_TABLE
TYPOLOGY_LAYER_MAP_TABLE = WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE
TYPOLOGY_SUMMARY_TABLE = WARTIME_AML_TYPOLOGY_SUMMARY_TABLE

CURRENT_USE = WARTIME_AML_TYPOLOGY_CURRENT_USE
PROHIBITED_USE = WARTIME_AML_TYPOLOGY_PROHIBITED_USE
PRODUCTION_SCORE_CHANGE = WARTIME_AML_TYPOLOGY_PRODUCTION_SCORE_CHANGE

CONTROL_FIELDS = {
    "current_use": CURRENT_USE,
    "prohibited_use": PROHIBITED_USE,
    "production_score_change": PRODUCTION_SCORE_CHANGE,
    "used_in_waris_scoring": False,
    "used_in_monte_carlo": False,
    "approved_current_use": "literature_support_and_typology_reference_only",
}

OPERATIONAL_CONTROL_FIELDS = {
    "analyst_review_current_use": ANALYST_REVIEW_CURRENT_USE,
    "analyst_review_production_score_change": ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
    "false_positive_controls_current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
    "false_positive_controls_production_score_change": (
        FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE
    ),
    "source_freshness_current_use": SOURCE_FRESHNESS_CURRENT_USE,
    "source_freshness_production_score_change": SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE,
    "run_manifest_current_use": RUN_MANIFEST_CURRENT_USE,
    "run_manifest_production_score_change": RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
    "operational_controls_used_in_typology_scoring": False,
}

PRIMARY_SOURCE = (
    "Utenkova, K. (2026). Anti-money laundering as an instrument of economic "
    "security: Wartime adaptation of AML/CFT frameworks in Ukraine."
)


def _add_typology_control_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Attach no-scoring typology control fields to typology artifacts."""
    if df is None or df.empty:
        return df

    out = add_constant_control_fields(df, CONTROL_FIELDS)
    out = add_constant_control_fields(out, OPERATIONAL_CONTROL_FIELDS)
    out["control_note"] = (
        "Wartime AML/CFT typology reference only. Literature-support context; "
        "not an allegation, not a measured oblast/sector indicator, and not used "
        "in WARIS scoring or Monte Carlo without SME review, false-positive "
        "controls, measurable indicator design, and model change control."
    )
    out["operational_control_note"] = (
        "Analyst-review, false-positive, source-freshness, and run-manifest "
        "artifacts are downstream operational controls only. They do not alter "
        "typology-register content, approve typology-based scoring, or change "
        "WARIS production scores."
    )
    out["source_separation_note"] = (
        "This typology register does not consume official Ukrstat GRP baseline "
        "values, expanded Prozorro procurement features, official FIU/SFMS "
        "context artifacts, analyst-review workflow artifacts, false-positive "
        "controls, source-freshness monitoring, or run-manifest outputs. "
        "Downstream bridge/review modules may compare these sources for "
        "documentation only."
    )
    return out


@dataclass(frozen=True)
class WartimeAmlTypology:
    typology_id: str
    typology_name: str
    typology_family: str
    description: str
    wartime_relevance: str
    waris_layer_candidates: str
    possible_public_source_indicators: str
    current_use: str
    prohibited_use: str
    production_score_change: str
    confidence_level: str
    source_basis: str
    notes: str


def _typologies() -> list[WartimeAmlTypology]:
    """Return literature-supported wartime AML/CFT typologies."""
    return [
        WartimeAmlTypology(
            typology_id="WAML-001",
            typology_name="Sanctions evasion and aggressor-state exposure",
            typology_family="sanctions_enforcement",
            description=(
                "Use of financial, corporate, trade, or payment channels to evade "
                "wartime sanctions or move value connected to sanctioned or "
                "aggressor-state-linked actors."
            ),
            wartime_relevance=(
                "The report frames sanctions enforcement as increasingly integrated "
                "with AML/CFT and geopolitical security objectives."
            ),
            waris_layer_candidates="sanctions_exposure_risk; tbml_risk; ownership_opacity_risk",
            possible_public_source_indicators=(
                "sanctions-list exposure counts; OpenSanctions/OFAC/NSDC matches; "
                "cross-border trade anomaly indicators; high-risk jurisdiction flags"
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            confidence_level="high_conceptual_relevance",
            source_basis=PRIMARY_SOURCE,
            notes=(
                "Use only as source-support and model-design rationale until a "
                "validated sanctions data pipeline and false-positive controls are approved."
            ),
        ),
        WartimeAmlTypology(
            typology_id="WAML-002",
            typology_name="Beneficial ownership opacity in high-risk sectors",
            typology_family="beneficial_ownership_transparency",
            description=(
                "Opacity around the natural persons who ultimately own or control "
                "assets, companies, suppliers, or counterparties in wartime-sensitive sectors."
            ),
            wartime_relevance=(
                "The report emphasizes beneficial ownership transparency as a "
                "structural safeguard, especially in reconstruction, procurement, "
                "humanitarian finance, and crisis conditions."
            ),
            waris_layer_candidates="ownership_opacity_risk; procurement_integrity_risk; sanctions_exposure_risk",
            possible_public_source_indicators=(
                "company registry gaps; missing ownership records; foreign ownership "
                "flags; PEP-related disclosure indicators; beneficial-owner verification status"
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            confidence_level="high_conceptual_relevance",
            source_basis=PRIMARY_SOURCE,
            notes=(
                "This does not identify or accuse any owner or company; it supports "
                "future aggregate ownership-transparency feature design."
            ),
        ),
        WartimeAmlTypology(
            typology_id="WAML-003",
            typology_name="Reconstruction and emergency procurement misuse",
            typology_family="procurement_and_reconstruction",
            description=(
                "Misuse or exploitation of emergency procurement, reconstruction "
                "funding, infrastructure repair, or public contracting flows."
            ),
            wartime_relevance=(
                "The report repeatedly identifies reconstruction, public procurement, "
                "and emergency finance as sectors where wartime conditions can magnify "
                "corruption and laundering risks."
            ),
            waris_layer_candidates="procurement_integrity_risk; ownership_opacity_risk; revenue_anomaly_risk",
            possible_public_source_indicators=(
                "Prozorro tender counts; emergency/reconstruction keywords; single-bid "
                "or single-supplier proxy; buyer concentration; expected value concentration"
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            confidence_level="high_model_alignment",
            source_basis=PRIMARY_SOURCE,
            notes=(
                "Supports the current expanded Prozorro feature layer as review-only "
                "context. It does not approve direct scoring use."
            ),
        ),
        WartimeAmlTypology(
            typology_id="WAML-004",
            typology_name="Humanitarian-flow diversion and misuse",
            typology_family="humanitarian_finance",
            description=(
                "Diversion, misuse, or laundering through humanitarian aid flows, "
                "relief logistics, emergency assistance, or cross-border support channels."
            ),
            wartime_relevance=(
                "The report identifies misuse of humanitarian flows and humanitarian "
                "finance as intensified wartime AML/CFT risks."
            ),
            waris_layer_candidates="tbml_risk; procurement_integrity_risk; financial_supervision_exposure",
            possible_public_source_indicators=(
                "humanitarian procurement keywords; aid/logistics sector exposure; "
                "border-region logistics indicators; NGO/aid-sector typology references"
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            confidence_level="medium_high_conceptual_relevance",
            source_basis=PRIMARY_SOURCE,
            notes=(
                "Requires careful safeguards to avoid chilling legitimate humanitarian "
                "activity or implying wrongdoing."
            ),
        ),
        WartimeAmlTypology(
            typology_id="WAML-005",
            typology_name="Digital asset and cryptocurrency-enabled finance",
            typology_family="digital_assets",
            description=(
                "Use of crypto wallets, digital platforms, or virtual-asset rails to "
                "move value connected to recruitment, sanctions evasion, crowdfunding, "
                "or conflict-linked finance."
            ),
            wartime_relevance=(
                "The report highlights digital asset transactions and crypto-wallet "
                "use as emerging wartime AML/CFT risk typologies."
            ),
            waris_layer_candidates="financial_supervision_exposure; sanctions_exposure_risk; tbml_risk",
            possible_public_source_indicators=(
                "virtual-asset typology references; official warnings; sanctioned "
                "wallet datasets where legally available; crypto-related public alerts"
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            confidence_level="medium_high_conceptual_relevance",
            source_basis=PRIMARY_SOURCE,
            notes=(
                "Do not add wallet-level or entity-level claims without legal review, "
                "high-quality source validation, and strict false-positive controls."
            ),
        ),
        WartimeAmlTypology(
            typology_id="WAML-006",
            typology_name="Temporarily occupied territory account exposure",
            typology_family="occupation_related_finance",
            description=(
                "Use of accounts or financial activity connected to temporarily "
                "occupied territories, occupation-linked intermediaries, or disrupted "
                "supervisory environments."
            ),
            wartime_relevance=(
                "The report identifies exploitation of accounts registered in "
                "temporarily occupied territories as a wartime risk mechanism."
            ),
            waris_layer_candidates="conflict_plausibility_gap; sanctions_exposure_risk; financial_supervision_exposure",
            possible_public_source_indicators=(
                "oblast conflict intensity; occupation/frontline status indicators; "
                "official risk advisories; sanctions or supervisory alerts"
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            confidence_level="medium_conceptual_relevance",
            source_basis=PRIMARY_SOURCE,
            notes=(
                "Should remain aggregate and region-level. Do not infer account-level "
                "wrongdoing from territorial exposure alone."
            ),
        ),
        WartimeAmlTypology(
            typology_id="WAML-007",
            typology_name="IT-sector payment and cash-withdrawal typologies",
            typology_family="sector_payment_typologies",
            description=(
                "Use of IT-sector payments, service payments, or digital-service "
                "channels followed by cash withdrawal or value movement."
            ),
            wartime_relevance=(
                "The report lists covert financing through IT-sector payments and "
                "subsequent cash withdrawals as a wartime typology."
            ),
            waris_layer_candidates="financial_supervision_exposure; revenue_anomaly_risk; tbml_risk",
            possible_public_source_indicators=(
                "sector revenue anomaly indicators; financial-sector exposure context; "
                "official typology references; cash-intensity proxies if available"
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            confidence_level="medium_conceptual_relevance",
            source_basis=PRIMARY_SOURCE,
            notes=(
                "Requires additional official typology support before any measurable "
                "feature is proposed."
            ),
        ),
        WartimeAmlTypology(
            typology_id="WAML-008",
            typology_name="Individual entrepreneur account misuse",
            typology_family="small_business_and_intermediary_accounts",
            description=(
                "Misuse of individual entrepreneur or small-business accounts for "
                "unverified transactions, intermediary payments, or value placement."
            ),
            wartime_relevance=(
                "The report identifies misuse of individual entrepreneur accounts "
                "for unverified transactions as a contemporary wartime typology."
            ),
            waris_layer_candidates="ownership_opacity_risk; financial_supervision_exposure; revenue_anomaly_risk",
            possible_public_source_indicators=(
                "official typology references; sector-level small-business density; "
                "supervisory alerts; anomalous revenue growth proxies"
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            confidence_level="medium_conceptual_relevance",
            source_basis=PRIMARY_SOURCE,
            notes=(
                "Do not treat small-business activity as suspicious by itself. This "
                "is a typology reference only."
            ),
        ),
        WartimeAmlTypology(
            typology_id="WAML-009",
            typology_name="Cash placement through intermediaries",
            typology_family="intermediary_and_cash_typologies",
            description=(
                "Placement of cash obtained via intermediaries into accounts controlled "
                "by, or connected to, aggressor-state-linked entities or networks."
            ),
            wartime_relevance=(
                "The report identifies cash placement through intermediaries into "
                "aggressor-affiliated accounts as a wartime mechanism."
            ),
            waris_layer_candidates="sanctions_exposure_risk; ownership_opacity_risk; financial_supervision_exposure",
            possible_public_source_indicators=(
                "official FIU typology references; sanctions exposure context; "
                "financial-supervision proxy context; ownership opacity indicators"
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            confidence_level="medium_conceptual_relevance",
            source_basis=PRIMARY_SOURCE,
            notes=(
                "Entity-level use would require lawful investigative process and "
                "validated data. WARIS should keep this at typology/reference level."
            ),
        ),
        WartimeAmlTypology(
            typology_id="WAML-010",
            typology_name="Cross-border intelligence and sanctions-data integration gaps",
            typology_family="institutional_capacity",
            description=(
                "Weak integration among AML, sanctions, beneficial ownership, and "
                "cross-border intelligence systems that can reduce wartime monitoring effectiveness."
            ),
            wartime_relevance=(
                "The report concludes that cross-border intelligence exchange, "
                "integrated sanctions/AML data systems, and digital verification "
                "mechanisms are key priorities."
            ),
            waris_layer_candidates="financial_supervision_exposure; sanctions_exposure_risk; ownership_opacity_risk",
            possible_public_source_indicators=(
                "MONEYVAL/FATF follow-up findings; FIU typology publications; "
                "beneficial-ownership verification status; sanctions-screening integration references"
            ),
            current_use=CURRENT_USE,
            prohibited_use=PROHIBITED_USE,
            production_score_change=PRODUCTION_SCORE_CHANGE,
            confidence_level="high_governance_relevance",
            source_basis=PRIMARY_SOURCE,
            notes=(
                "Supports model governance and future data-integration roadmap rather "
                "than immediate scoring."
            ),
        ),
    ]


def build_wartime_aml_typology_register() -> pd.DataFrame:
    """Build the wartime AML/CFT typology register."""
    ensure_dirs([TABLE_DIR])

    rows = [typology.__dict__ for typology in _typologies()]
    out = pd.DataFrame(rows)
    from .config import WARTIME_PUBLIC_TYPOLOGY_IDS
    out = out.loc[out.typology_id.isin(WARTIME_PUBLIC_TYPOLOGY_IDS)].copy()
    # Public conceptual wording must not inherit the unverified SFMS recruitment example.
    out.loc[out.typology_id.eq("WAML-005"), "description"] = (
        "Potential misuse of virtual assets or digital payment channels in wartime finance; "
        "a general literature theme, without attributing a particular transaction or scheme."
    )
    out = _add_typology_control_fields(out)
    out["reference_review_date"] = "2026-10-18"
    out["source_doi"] = "10.65237/2336-3630-2026-3(1)-4"
    out["source_url"] = "https://phes.com.ua/ojs/index.php/www/en/article/view/112"
    out["source_license"] = "CC BY 4.0"
    out["reference_support_scope"] = "Conceptual literature only; WARIS indicator and layer assignments are project interpretations."
    out["reference_page_crosswalk"] = "docs/typology_conceptual_page_crosswalk.csv"

    safe_write_csv(out, TYPOLOGY_REGISTER_TABLE)
    return out


def build_wartime_aml_typology_layer_map(register: pd.DataFrame) -> pd.DataFrame:
    """Explode typology-to-WARIS-layer candidates into a mapping table."""
    ensure_dirs([TABLE_DIR])

    from .config import WARTIME_PUBLIC_TYPOLOGY_IDS
    register = register.loc[register.typology_id.isin(WARTIME_PUBLIC_TYPOLOGY_IDS)].copy() if "typology_id" in register else register.iloc[0:0].copy()
    if register.empty:
        out = pd.DataFrame()
        safe_write_csv(out, TYPOLOGY_LAYER_MAP_TABLE)
        return out

    rows = []

    for _, row in register.iterrows():
        layer_text = str(row.get("waris_layer_candidates", ""))
        layers = [layer.strip() for layer in layer_text.split(";") if layer.strip()]

        for layer in layers:
            rows.append(
                {
                    "typology_id": row.get("typology_id", ""),
                    "typology_name": row.get("typology_name", ""),
                    "typology_family": row.get("typology_family", ""),
                    "waris_layer_candidate": layer,
                    "current_use": CURRENT_USE,
                    "prohibited_use": PROHIBITED_USE,
                    "production_score_change": PRODUCTION_SCORE_CHANGE,
                    "used_in_waris_scoring": False,
                    "used_in_monte_carlo": False,
                    "approved_current_use": "literature_support_and_typology_reference_only",
                    "analyst_review_current_use": ANALYST_REVIEW_CURRENT_USE,
                    "analyst_review_production_score_change": ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE,
                    "false_positive_controls_current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
                    "false_positive_controls_production_score_change": (
                        FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE
                    ),
                    "source_freshness_current_use": SOURCE_FRESHNESS_CURRENT_USE,
                    "source_freshness_production_score_change": (
                        SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE
                    ),
                    "run_manifest_current_use": RUN_MANIFEST_CURRENT_USE,
                    "run_manifest_production_score_change": RUN_MANIFEST_PRODUCTION_SCORE_CHANGE,
                    "operational_controls_used_in_typology_scoring": False,
                    "source_basis": row.get("source_basis", PRIMARY_SOURCE),
                    "source_url": row.get("source_url", "https://phes.com.ua/ojs/index.php/www/en/article/view/112"),
                    "source_doi": "10.65237/2336-3630-2026-3(1)-4",
                    "source_license": "CC BY 4.0",
                    "reference_support_scope": "Conceptual literature only; detailed unverified SFMS examples excluded; layer assignments are WARIS interpretations.",
                    "notes": (
                        "Layer mapping is conceptual and does not change score weights, "
                        "risk-layer values, composite scores, risk bands, review "
                        "rationales, or Monte Carlo simulations."
                    ),
                    "control_note": (
                        "Conceptual layer mapping only. Requires measurable indicators, "
                        "SME review, false-positive controls, and change control before "
                        "any scoring use."
                    ),
                }
            )

    out = pd.DataFrame(rows)
    out = _add_typology_control_fields(out)
    safe_write_csv(out, TYPOLOGY_LAYER_MAP_TABLE)
    return out


def build_wartime_aml_typology_summary(
    register: pd.DataFrame,
    layer_map: pd.DataFrame,
) -> pd.DataFrame:
    """Build a compact summary of the typology register."""
    ensure_dirs([TABLE_DIR])
    from .config import WARTIME_PUBLIC_TYPOLOGY_IDS
    register = register.loc[register.typology_id.isin(WARTIME_PUBLIC_TYPOLOGY_IDS)].copy() if "typology_id" in register else register.iloc[0:0].copy()
    layer_map = layer_map.loc[layer_map.typology_id.isin(WARTIME_PUBLIC_TYPOLOGY_IDS)].copy() if "typology_id" in layer_map else layer_map.iloc[0:0].copy()

    family_counts = (
        register["typology_family"].value_counts().to_dict()
        if not register.empty and "typology_family" in register.columns
        else {}
    )

    layer_counts = (
        layer_map["waris_layer_candidate"].value_counts().to_dict()
        if not layer_map.empty and "waris_layer_candidate" in layer_map.columns
        else {}
    )

    rows = [
        {
            "summary_area": "Typology register",
            "status": "created" if not register.empty else "missing_or_empty",
            "value": len(register),
            "recommended_next_action": (
                "Use as literature-supported source context and model-design rationale only."
            ),
        },
        {
            "summary_area": "Typology families",
            "status": "created" if family_counts else "missing_or_empty",
            "value": str(family_counts),
            "recommended_next_action": (
                "Review whether additional official FIU/FATF/MONEYVAL typology sources "
                "should be added."
            ),
        },
        {
            "summary_area": "WARIS layer mapping",
            "status": "created" if not layer_map.empty else "missing_or_empty",
            "value": str(layer_counts),
            "recommended_next_action": (
                "Use layer mappings for documentation and future feature planning, not scoring."
            ),
        },
        {
            "summary_area": "Current use control",
            "status": "control_active",
            "value": CURRENT_USE,
            "recommended_next_action": (
                "Keep typologies as reference artifacts unless a future governed model branch "
                "approves measurable indicators."
            ),
        },
        {
            "summary_area": "Prohibited use control",
            "status": "control_active",
            "value": PROHIBITED_USE,
            "recommended_next_action": (
                "Do not map typology references directly into scores without data validation, "
                "SME review, false-positive controls, and change control."
            ),
        },
        {
            "summary_area": "Production score change control",
            "status": "control_active",
            "value": PRODUCTION_SCORE_CHANGE,
            "recommended_next_action": "Maintain production_score_change=none.",
        },
        {
            "summary_area": "Scoring and Monte Carlo control",
            "status": "control_active",
            "value": "used_in_waris_scoring=False; used_in_monte_carlo=False",
            "recommended_next_action": (
                "Keep typology artifacts outside risk-layer calculation, composite "
                "scoring, risk-band assignment, review-rationale generation, and "
                "Monte Carlo score simulation."
            ),
        },
        {
            "summary_area": "Source separation control",
            "status": "control_active",
            "value": (
                "separate_from_ukrstat_baseline; separate_from_prozorro_features; "
                "separate_from_fiu_context; separate_from_operational_controls"
            ),
            "recommended_next_action": (
                "Use downstream bridge/review artifacts for documentation only. Do "
                "not merge typology references directly into scoring pipelines."
            ),
        },
        {
            "summary_area": "Operational control separation",
            "status": "control_active",
            "value": (
                f"analyst_review={ANALYST_REVIEW_CURRENT_USE}; "
                f"false_positive_controls={FALSE_POSITIVE_CONTROLS_CURRENT_USE}; "
                f"source_freshness={SOURCE_FRESHNESS_CURRENT_USE}; "
                f"run_manifest={RUN_MANIFEST_CURRENT_USE}"
            ),
            "recommended_next_action": (
                "Keep operational-control artifacts downstream from typology-register "
                "generation. They support documentation and human review only."
            ),
        },
        {
            "summary_area": "Operational controls production score change",
            "status": "control_active",
            "value": (
                f"analyst_review={ANALYST_REVIEW_PRODUCTION_SCORE_CHANGE}; "
                f"false_positive_controls={FALSE_POSITIVE_CONTROLS_PRODUCTION_SCORE_CHANGE}; "
                f"source_freshness={SOURCE_FRESHNESS_PRODUCTION_SCORE_CHANGE}; "
                f"run_manifest={RUN_MANIFEST_PRODUCTION_SCORE_CHANGE}"
            ),
            "recommended_next_action": (
                "Maintain production_score_change=none for typology and downstream "
                "operational-control artifacts unless formal model change control is approved."
            ),
        },
    ]

    out = pd.DataFrame(rows)
    out = _add_typology_control_fields(out)
    safe_write_csv(out, TYPOLOGY_SUMMARY_TABLE)
    return out


def build_wartime_aml_typology_artifacts() -> dict[str, pd.DataFrame]:
    """Build all wartime AML/CFT typology artifacts."""
    register = build_wartime_aml_typology_register()
    layer_map = build_wartime_aml_typology_layer_map(register)
    summary = build_wartime_aml_typology_summary(register, layer_map)

    return {
        "typology_register": register,
        "typology_layer_map": layer_map,
        "typology_summary": summary,
    }


def main() -> None:
    """CLI entry point."""
    artifacts = build_wartime_aml_typology_artifacts()

    print("\nWartime AML/CFT typology artifacts created.")
    print(f"- Typology register rows: {len(artifacts['typology_register'])}")
    print(f"- Typology layer-map rows: {len(artifacts['typology_layer_map'])}")
    print(f"- Typology summary rows: {len(artifacts['typology_summary'])}")
    print(f"- Typology register: {TYPOLOGY_REGISTER_TABLE}")
    print(f"- Typology layer map: {TYPOLOGY_LAYER_MAP_TABLE}")
    print(f"- Typology summary: {TYPOLOGY_SUMMARY_TABLE}")

    print(
        "\nImportant: These are literature-support and typology-reference artifacts only. "
        f"current_use={CURRENT_USE}; prohibited_use={PROHIBITED_USE}; "
        f"production_score_change={PRODUCTION_SCORE_CHANGE}. They do not alter WARIS "
        "risk layers, composite scores, risk bands, review rationales, or Monte Carlo. "
        "They remain separate from official Ukrstat baseline, expanded Prozorro, "
        "official FIU/SFMS context, analyst-review, false-positive, source-freshness, "
        "and run-manifest artifacts unless a future governed scoring-integration "
        "change is explicitly approved."
    )


if __name__ == "__main__":
    main()
