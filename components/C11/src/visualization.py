from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from .config import CHART_DIR
from .utils import (
    ensure_dirs,
    normalize_waris_oblast_name,
    safe_read_csv,
)

try:
    from .config import UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE
except ImportError:
    UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE = None

try:
    from .config import (
        PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE,
        PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE,
        PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE,
    )
except ImportError:
    PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE = None
    PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE = None
    PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE = None

try:
    from .config import (
        OFFICIAL_BASELINE_READINESS_DECISION_TABLE,
        OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_TABLE,
    )
except ImportError:
    OFFICIAL_BASELINE_READINESS_DECISION_TABLE = None
    OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_TABLE = None

try:
    from .config import (
        WARTIME_AML_TYPOLOGY_REGISTER_TABLE,
        WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE,
        WARTIME_AML_TYPOLOGY_SUMMARY_TABLE,
        FIU_OFFICIAL_SOURCE_REGISTER_TABLE,
        FIU_REPORTING_STATISTICS_CONTEXT_TABLE,
        FIU_CASE_REFERRAL_CONTEXT_TABLE,
        FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE,
        FIU_CONTEXT_SUMMARY_TABLE,
        WARTIME_AML_TYPOLOGY_CURRENT_USE,
        FIU_CONTEXT_CURRENT_USE,
    )
except ImportError:
    WARTIME_AML_TYPOLOGY_REGISTER_TABLE = None
    WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE = None
    WARTIME_AML_TYPOLOGY_SUMMARY_TABLE = None
    FIU_OFFICIAL_SOURCE_REGISTER_TABLE = None
    FIU_REPORTING_STATISTICS_CONTEXT_TABLE = None
    FIU_CASE_REFERRAL_CONTEXT_TABLE = None
    FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE = None
    FIU_CONTEXT_SUMMARY_TABLE = None
    WARTIME_AML_TYPOLOGY_CURRENT_USE = (
        "literature_support_and_typology_reference_only"
    )
    FIU_CONTEXT_CURRENT_USE = "official_fiu_context_and_typology_support_only"

try:
    from .config import (
        OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE,
        OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE,
        OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE,
        OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE,
    )
except ImportError:
    OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE = None
    OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE = None
    OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE = None
    OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE = None

try:
    from .config import (
        ANALYST_REVIEW_QUEUE_TABLE,
        ANALYST_REVIEW_QUESTIONS_TABLE,
        ANALYST_REVIEW_SUMMARY_TABLE,
        FALSE_POSITIVE_CONTROLS_TABLE,
        FALSE_POSITIVE_REVIEW_CHECKLIST_TABLE,
        FALSE_POSITIVE_SUMMARY_TABLE,
        SOURCE_FRESHNESS_INVENTORY_TABLE,
        SOURCE_FRESHNESS_ASSESSMENT_TABLE,
        SOURCE_FRESHNESS_SUMMARY_TABLE,
        RUN_MANIFEST_TABLE,
        RUN_MANIFEST_SUMMARY_TABLE,
        ANALYST_REVIEW_CURRENT_USE,
        FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        SOURCE_FRESHNESS_CURRENT_USE,
        RUN_MANIFEST_CURRENT_USE,
    )
except ImportError:
    ANALYST_REVIEW_QUEUE_TABLE = None
    ANALYST_REVIEW_QUESTIONS_TABLE = None
    ANALYST_REVIEW_SUMMARY_TABLE = None
    FALSE_POSITIVE_CONTROLS_TABLE = None
    FALSE_POSITIVE_REVIEW_CHECKLIST_TABLE = None
    FALSE_POSITIVE_SUMMARY_TABLE = None
    SOURCE_FRESHNESS_INVENTORY_TABLE = None
    SOURCE_FRESHNESS_ASSESSMENT_TABLE = None
    SOURCE_FRESHNESS_SUMMARY_TABLE = None
    RUN_MANIFEST_TABLE = None
    RUN_MANIFEST_SUMMARY_TABLE = None
    ANALYST_REVIEW_CURRENT_USE = "analyst_review_workflow_only"
    FALSE_POSITIVE_CONTROLS_CURRENT_USE = "human_review_support_only"
    SOURCE_FRESHNESS_CURRENT_USE = "source_freshness_monitoring_only"
    RUN_MANIFEST_CURRENT_USE = "run_manifest_documentation"


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
    normalized = normalize_waris_oblast_name(value)
    return UKRSTAT_TO_WARIS_OBLAST.get(normalized, normalized)


def _load_official_baseline_candidates() -> pd.DataFrame | None:
    """Load validation-only Ukrstat official baseline candidates if available."""
    if UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE is None:
        return None

    df = safe_read_csv(UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE)

    if df is None or df.empty:
        return None

    if "oblast" in df.columns:
        df = df.copy()
        df["oblast"] = df["oblast"].apply(_normalize_oblast_name)

    return df


def _load_optional_table(path) -> pd.DataFrame | None:
    """Load an optional generated artifact if available."""
    return safe_read_csv(path)


def _count_rows(path) -> int:
    """Return row count for an optional CSV artifact."""
    df = _load_optional_table(path)
    return 0 if df is None else len(df)


def _count_rows_across(paths: list[object]) -> int:
    """Return combined row count across optional generated artifact tables."""
    return sum(_count_rows(path) for path in paths)


def _readable_use_label(value: object) -> str:
    """Convert long governance values into compact chart labels."""
    text = "" if value is None else str(value).strip()

    mapping = {
        "literature_support_and_typology_reference_only": "literature support only",
        "official_fiu_context_and_typology_support_only": "FIU/SFMS context only",
        "review_artifact_only": "review artifact only",
        "controlled_benchmark_integration_only": "benchmark artifact only",
        "direct_scoring_without_change_control": "scoring blocked",
        "risk_layer_calculation_or_composite_scoring": "scoring blocked",
        "analyst_review_workflow_only": "analyst review only",
        "human_review_support_only": "human review support only",
        "source_freshness_monitoring_only": "freshness monitoring only",
        "run_manifest_documentation": "run manifest only",
        "context_review_only": "context review only",
    }

    return mapping.get(text, text.replace("_", " "))


def _normalize_live_status_for_chart(live_status: pd.DataFrame) -> pd.DataFrame:
    """Correct generated artifact rows before plotting live/source status.

    The live status table records connector status, while several WARIS layers are
    generated artifacts in the same run. This helper prevents the chart from
    showing those generated artifacts as fallback when their output tables exist.
    """
    if live_status is None or live_status.empty or "source_name" not in live_status.columns:
        return live_status

    out = live_status.copy()

    artifact_specs = {
        "Prozorro expanded procurement features": {
            "paths": [
                PROZORRO_PROCUREMENT_FEATURES_OBLAST_TABLE,
                PROZORRO_PROCUREMENT_FEATURES_OBLAST_SECTOR_TABLE,
                PROZORRO_PROCUREMENT_SCORING_CANDIDATES_TABLE,
            ],
            "status": "artifact",
        },
        "Wartime AML/CFT typology register": {
            "paths": [
                WARTIME_AML_TYPOLOGY_REGISTER_TABLE,
                WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE,
                WARTIME_AML_TYPOLOGY_SUMMARY_TABLE,
            ],
            "status": "artifact",
        },
        "Official FIU/SFMS context artifacts": {
            "paths": [
                FIU_OFFICIAL_SOURCE_REGISTER_TABLE,
                FIU_REPORTING_STATISTICS_CONTEXT_TABLE,
                FIU_CASE_REFERRAL_CONTEXT_TABLE,
                FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE,
                FIU_CONTEXT_SUMMARY_TABLE,
            ],
            "status": "artifact",
        },
        "Ukrstat regional accounts official baseline candidates": {
            "paths": [
                UKRSTAT_OBLAST_BASELINE_CANDIDATES_TABLE,
                OFFICIAL_BASELINE_READINESS_DECISION_TABLE,
                OFFICIAL_BASELINE_MERGE_REVIEW_SUMMARY_TABLE,
            ],
            "status": "benchmark artifact",
        },
        "WARIS operational review/control artifacts": {
            "paths": [
                ANALYST_REVIEW_QUEUE_TABLE,
                ANALYST_REVIEW_QUESTIONS_TABLE,
                ANALYST_REVIEW_SUMMARY_TABLE,
                FALSE_POSITIVE_CONTROLS_TABLE,
                FALSE_POSITIVE_REVIEW_CHECKLIST_TABLE,
                FALSE_POSITIVE_SUMMARY_TABLE,
                SOURCE_FRESHNESS_INVENTORY_TABLE,
                SOURCE_FRESHNESS_ASSESSMENT_TABLE,
                SOURCE_FRESHNESS_SUMMARY_TABLE,
                RUN_MANIFEST_TABLE,
                RUN_MANIFEST_SUMMARY_TABLE,
                OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE,
            ],
            "status": "artifact",
        },
    }

    for source_name, spec in artifact_specs.items():
        mask = out["source_name"].astype(str).eq(source_name)

        if not mask.any():
            continue

        row_count = _count_rows_across(spec["paths"])

        if row_count > 0:
            out.loc[mask, "status"] = spec["status"]
            out.loc[mask, "rows"] = row_count

    return out


def _truncate_label(label: object, max_chars: int = 72) -> str:
    """Keep chart labels readable in PDF output."""
    text = "" if label is None else str(label).strip()

    if len(text) <= max_chars:
        return text

    return text[: max_chars - 1].rstrip() + "…"


def plot_source_context_artifact_coverage() -> str | None:
    """Plot row coverage for source-context and governance artifacts.

    This is a data-coverage chart only. It does not imply scoring use of
    official baseline, Prozorro, wartime typology, or FIU/SFMS artifacts.
    """
    ensure_dirs([CHART_DIR])

    rows = [
        {
            "artifact": "Wartime typology register",
            "rows": _count_rows(WARTIME_AML_TYPOLOGY_REGISTER_TABLE),
            "current_use": WARTIME_AML_TYPOLOGY_CURRENT_USE,
        },
        {
            "artifact": "Wartime typology layer map",
            "rows": _count_rows(WARTIME_AML_TYPOLOGY_LAYER_MAP_TABLE),
            "current_use": WARTIME_AML_TYPOLOGY_CURRENT_USE,
        },
        {
            "artifact": "FIU source register",
            "rows": _count_rows(FIU_OFFICIAL_SOURCE_REGISTER_TABLE),
            "current_use": FIU_CONTEXT_CURRENT_USE,
        },
        {
            "artifact": "FIU reporting stats",
            "rows": _count_rows(FIU_REPORTING_STATISTICS_CONTEXT_TABLE),
            "current_use": FIU_CONTEXT_CURRENT_USE,
        },
        {
            "artifact": "FIU case referrals",
            "rows": _count_rows(FIU_CASE_REFERRAL_CONTEXT_TABLE),
            "current_use": FIU_CONTEXT_CURRENT_USE,
        },
        {
            "artifact": "FIU typology support",
            "rows": _count_rows(FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE),
            "current_use": FIU_CONTEXT_CURRENT_USE,
        },
        {
            "artifact": "Analyst review queue",
            "rows": _count_rows(ANALYST_REVIEW_QUEUE_TABLE),
            "current_use": ANALYST_REVIEW_CURRENT_USE,
        },
        {
            "artifact": "Analyst review questions",
            "rows": _count_rows(ANALYST_REVIEW_QUESTIONS_TABLE),
            "current_use": ANALYST_REVIEW_CURRENT_USE,
        },
        {
            "artifact": "False-positive controls",
            "rows": _count_rows(FALSE_POSITIVE_CONTROLS_TABLE),
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        },
        {
            "artifact": "False-positive checklist",
            "rows": _count_rows(FALSE_POSITIVE_REVIEW_CHECKLIST_TABLE),
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        },
        {
            "artifact": "Source freshness assessment",
            "rows": _count_rows(SOURCE_FRESHNESS_ASSESSMENT_TABLE),
            "current_use": SOURCE_FRESHNESS_CURRENT_USE,
        },
        {
            "artifact": "Run manifest inventory",
            "rows": _count_rows(RUN_MANIFEST_TABLE),
            "current_use": RUN_MANIFEST_CURRENT_USE,
        },
    ]

    coverage = pd.DataFrame(rows)
    coverage = coverage[coverage["rows"] > 0].copy()

    if coverage.empty:
        return None

    coverage = coverage.sort_values("rows", ascending=True)
    coverage["current_use_label"] = coverage["current_use"].apply(_readable_use_label)
    labels = (
        coverage["artifact"].astype(str)
        + " ("
        + coverage["current_use_label"].astype(str)
        + ")"
    ).apply(lambda value: _truncate_label(value, 72))

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(labels, coverage["rows"])
    ax.set_xlabel("Rows available")
    ax.set_title("Source-Context and Control Coverage")

    fig.tight_layout()
    path = CHART_DIR / "source_context_artifact_coverage.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_typology_family_distribution() -> str | None:
    """Plot wartime AML/CFT typology family distribution.

    This chart summarizes literature-support typology references only. It is not
    a risk ranking and does not alter model scoring.
    """
    ensure_dirs([CHART_DIR])

    register = _load_optional_table(WARTIME_AML_TYPOLOGY_REGISTER_TABLE)

    if register is None or register.empty or "typology_family" not in register.columns:
        return None

    working = register.copy()
    working["typology_family"] = (
        working["typology_family"].fillna("missing_family").astype(str)
    )

    counts = (
        working["typology_family"]
        .value_counts()
        .rename_axis("typology_family")
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    counts["typology_family_label"] = (
        counts["typology_family"]
        .astype(str)
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    if counts.empty:
        return None

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    ax.barh(counts["typology_family_label"], counts["count"])
    ax.set_xlabel("Typology count")
    ax.set_title("Wartime AML/CFT Typology Family Distribution")

    fig.tight_layout()
    path = CHART_DIR / "wartime_aml_typology_family_distribution.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_fiu_context_artifact_coverage() -> str | None:
    """Plot official FIU/SFMS context artifact row coverage.

    This chart is official-source coverage context only. It does not imply any
    oblast, sector, entity, or person-level finding.
    """
    ensure_dirs([CHART_DIR])

    rows = [
        {"artifact": "Source register", "rows": _count_rows(FIU_OFFICIAL_SOURCE_REGISTER_TABLE)},
        {"artifact": "Reporting statistics", "rows": _count_rows(FIU_REPORTING_STATISTICS_CONTEXT_TABLE)},
        {"artifact": "Case referral context", "rows": _count_rows(FIU_CASE_REFERRAL_CONTEXT_TABLE)},
        {"artifact": "Typology support", "rows": _count_rows(FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE)},
        {"artifact": "Context summary", "rows": _count_rows(FIU_CONTEXT_SUMMARY_TABLE)},
    ]

    coverage = pd.DataFrame(rows)
    coverage = coverage[coverage["rows"] > 0].copy()

    if coverage.empty:
        return None

    coverage = coverage.sort_values("rows", ascending=True)

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.barh(coverage["artifact"], coverage["rows"])
    ax.set_xlabel("Rows available")
    ax.set_title("Official FIU/SFMS Context Artifact Coverage")

    fig.tight_layout()
    path = CHART_DIR / "fiu_context_artifact_coverage.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_context_review_coverage() -> str | None:
    """Plot row coverage for official-baseline context-review artifacts."""
    ensure_dirs([CHART_DIR])

    rows = [
        {
            "review_artifact": "Baseline-Prozorro review",
            "rows": _count_rows(OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE),
        },
        {
            "review_artifact": "Baseline-typology review",
            "rows": _count_rows(
                OFFICIAL_BASELINE_WARTIME_TYPOLOGY_CONTEXT_REVIEW_TABLE
            ),
        },
        {
            "review_artifact": "Baseline-FIU/SFMS review",
            "rows": _count_rows(OFFICIAL_BASELINE_FIU_CONTEXT_REVIEW_TABLE),
        },
        {
            "review_artifact": "Baseline-controls review",
            "rows": _count_rows(OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE),
        },
    ]

    coverage = pd.DataFrame(rows)
    coverage = coverage[coverage["rows"] > 0].copy()

    if coverage.empty:
        return None

    coverage = coverage.sort_values("rows", ascending=True)

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.barh(coverage["review_artifact"], coverage["rows"])
    ax.set_xlabel("Rows available")
    ax.set_title("Official Baseline Context-Review Coverage")

    fig.tight_layout()
    path = CHART_DIR / "official_baseline_context_review_coverage.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_operational_controls_coverage() -> str | None:
    """Plot row coverage for operational-control artifacts.

    This chart documents governance and human-review support artifacts only. It
    does not imply scoring use or model validation.
    """
    ensure_dirs([CHART_DIR])

    rows = [
        {
            "artifact": "Analyst queue",
            "rows": _count_rows(ANALYST_REVIEW_QUEUE_TABLE),
            "current_use": ANALYST_REVIEW_CURRENT_USE,
        },
        {
            "artifact": "Review questions",
            "rows": _count_rows(ANALYST_REVIEW_QUESTIONS_TABLE),
            "current_use": ANALYST_REVIEW_CURRENT_USE,
        },
        {
            "artifact": "Analyst summary",
            "rows": _count_rows(ANALYST_REVIEW_SUMMARY_TABLE),
            "current_use": ANALYST_REVIEW_CURRENT_USE,
        },
        {
            "artifact": "False-positive controls",
            "rows": _count_rows(FALSE_POSITIVE_CONTROLS_TABLE),
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        },
        {
            "artifact": "False-positive checklist",
            "rows": _count_rows(FALSE_POSITIVE_REVIEW_CHECKLIST_TABLE),
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        },
        {
            "artifact": "False-positive summary",
            "rows": _count_rows(FALSE_POSITIVE_SUMMARY_TABLE),
            "current_use": FALSE_POSITIVE_CONTROLS_CURRENT_USE,
        },
        {
            "artifact": "Freshness inventory",
            "rows": _count_rows(SOURCE_FRESHNESS_INVENTORY_TABLE),
            "current_use": SOURCE_FRESHNESS_CURRENT_USE,
        },
        {
            "artifact": "Freshness assessment",
            "rows": _count_rows(SOURCE_FRESHNESS_ASSESSMENT_TABLE),
            "current_use": SOURCE_FRESHNESS_CURRENT_USE,
        },
        {
            "artifact": "Freshness summary",
            "rows": _count_rows(SOURCE_FRESHNESS_SUMMARY_TABLE),
            "current_use": SOURCE_FRESHNESS_CURRENT_USE,
        },
        {
            "artifact": "Run manifest inventory",
            "rows": _count_rows(RUN_MANIFEST_TABLE),
            "current_use": RUN_MANIFEST_CURRENT_USE,
        },
        {
            "artifact": "Run manifest summary",
            "rows": _count_rows(RUN_MANIFEST_SUMMARY_TABLE),
            "current_use": RUN_MANIFEST_CURRENT_USE,
        },
        {
            "artifact": "Baseline-controls review",
            "rows": _count_rows(OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE),
            "current_use": "context_review_only",
        },
    ]

    coverage = pd.DataFrame(rows)
    coverage = coverage[coverage["rows"] > 0].copy()

    if coverage.empty:
        return None

    coverage = coverage.sort_values("rows", ascending=True)
    coverage["current_use_label"] = coverage["current_use"].apply(_readable_use_label)
    labels = (
        coverage["artifact"].astype(str)
        + " ("
        + coverage["current_use_label"].astype(str)
        + ")"
    ).apply(lambda value: _truncate_label(value, 64))

    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    ax.barh(labels, coverage["rows"])
    ax.set_xlabel("Rows available")
    ax.set_title("Operational-Control Artifact Coverage")

    fig.tight_layout()
    path = CHART_DIR / "operational_controls_artifact_coverage.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_top_risks(scored: pd.DataFrame, top_n: int = 15) -> str:
    """Plot the highest WARIS AML review signals."""
    ensure_dirs([CHART_DIR])

    top = scored.head(top_n).copy()

    top["waris_aml_review_score"] = pd.to_numeric(
        top["waris_aml_review_score"],
        errors="coerce",
    ).fillna(0)

    top["oblast"] = top["oblast"].fillna("Unknown").astype(str)
    top["sector"] = top["sector"].fillna("Unknown").astype(str)

    top = top.sort_values("waris_aml_review_score")
    labels = top["oblast"] + " - " + top["sector"]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(labels, top["waris_aml_review_score"])
    ax.set_xlabel("WARIS AML Review Score")
    ax.set_title("Top Ukraine Wartime Revenue Integrity AML Review Signals")
    ax.set_xlim(0, 100)

    fig.tight_layout()
    path = CHART_DIR / "top_waris_risks.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_layer_profile(scored: pd.DataFrame, top_n: int = 10) -> str:
    """Plot the average risk-layer profile for the highest-scoring records."""
    ensure_dirs([CHART_DIR])

    layer_cols = [
        "revenue_anomaly_risk",
        "sanctions_exposure_risk",
        "procurement_integrity_risk",
        "ownership_opacity_risk",
        "tbml_risk",
        "conflict_plausibility_gap",
        "financial_supervision_exposure",
    ]

    available_cols = [col for col in layer_cols if col in scored.columns]

    if not available_cols:
        raise ValueError("No risk-layer columns available for plotting.")

    profile = (
        scored.head(top_n)[available_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .mean()
        .sort_values()
    )

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh([c.replace("_", " ") for c in profile.index], profile.values)
    ax.set_xlabel("Average Layer Score")
    ax.set_title(f"Average Risk Layer Profile - Top {top_n} Signals")
    ax.set_xlim(0, 100)

    fig.tight_layout()
    path = CHART_DIR / "top_layer_profile.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_oblast_summary(oblast_summary: pd.DataFrame, top_n: int = 12) -> str:
    """Plot average WARIS review score by oblast."""
    ensure_dirs([CHART_DIR])

    top = oblast_summary.head(top_n).copy()

    top["waris_aml_review_score"] = pd.to_numeric(
        top["waris_aml_review_score"],
        errors="coerce",
    ).fillna(0)

    top["oblast"] = top["oblast"].fillna("Unknown").astype(str)

    top = top.sort_values("waris_aml_review_score")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top["oblast"], top["waris_aml_review_score"])
    ax.set_xlabel("Average WARIS Score")
    ax.set_title("Top Oblast-Level AML Review Priorities")
    ax.set_xlim(0, 100)

    fig.tight_layout()
    path = CHART_DIR / "oblast_summary.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_conflict_intensity(scored: pd.DataFrame, top_n: int = 15) -> str | None:
    """Plot oblast-level conflict intensity proxy.

    If ACLED is live, conflict_intensity_proxy_live should be present and is
    preferred. Otherwise this falls back to the synthetic/blended
    conflict_intensity_proxy.
    """
    ensure_dirs([CHART_DIR])

    if scored is None or scored.empty:
        return None

    if "oblast" not in scored.columns:
        return None

    if "conflict_intensity_proxy_live" in scored.columns:
        proxy_col = "conflict_intensity_proxy_live"
        title_suffix = "ACLED Live Proxy"
    elif "conflict_intensity_proxy" in scored.columns:
        proxy_col = "conflict_intensity_proxy"
        title_suffix = "Fallback / Blended Proxy"
    else:
        return None

    working = scored.copy()

    working["oblast"] = working["oblast"].fillna("Unknown").astype(str)
    working[proxy_col] = pd.to_numeric(
        working[proxy_col],
        errors="coerce",
    ).fillna(0)

    conflict = (
        working.groupby("oblast", as_index=False)
        .agg(conflict_intensity=(proxy_col, "mean"))
        .sort_values("conflict_intensity", ascending=False)
        .head(top_n)
        .sort_values("conflict_intensity")
    )

    if conflict.empty:
        return None

    fig, ax = plt.subplots(figsize=(8.5, 6))
    ax.barh(conflict["oblast"], conflict["conflict_intensity"])
    ax.set_xlabel("Conflict Intensity Proxy")
    ax.set_title(f"Top Oblast Conflict Intensity - {title_suffix}")
    ax.set_xlim(0, 100)

    fig.tight_layout()
    path = CHART_DIR / "conflict_intensity_summary.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_live_source_status(live_status: pd.DataFrame) -> str | None:
    """Plot source-backed connector row counts by source."""
    ensure_dirs([CHART_DIR])

    if live_status is None or live_status.empty:
        return None

    required_cols = {"source_name", "status", "rows"}

    if not required_cols.issubset(set(live_status.columns)):
        return None

    status_df = _normalize_live_status_for_chart(live_status)

    status_df["rows"] = pd.to_numeric(
        status_df["rows"],
        errors="coerce",
    ).fillna(0)

    status_df["source_name"] = status_df["source_name"].fillna("Unknown").astype(str)
    status_df["status"] = status_df["status"].fillna("unknown").astype(str)

    status_df = status_df.sort_values("rows", ascending=True)

    labels = (
        status_df["source_name"].astype(str)
        + " ("
        + status_df["status"].astype(str)
        + ")"
    ).apply(lambda value: _truncate_label(value, 72))

    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    ax.barh(labels, status_df["rows"])
    ax.set_xlabel("Rows / records available")
    ax.set_title("Live and Artifact Coverage")

    fig.tight_layout()
    path = CHART_DIR / "live_source_status.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_official_baseline_candidates(top_n: int = 15) -> str | None:
    """Plot validation-only official Ukrstat oblast GRP baseline candidates.

    This chart is a data-coverage and validation artifact. It does not imply
    that official GRP values are used in WARIS scoring.
    """
    ensure_dirs([CHART_DIR])

    candidates = _load_official_baseline_candidates()

    if candidates is None or candidates.empty:
        return None

    required_cols = {
        "oblast",
        "official_regional_baseline_proxy",
        "current_use_in_scoring",
        "validation_status",
    }

    if not required_cols.issubset(set(candidates.columns)):
        return None

    working = candidates.copy()

    working["oblast"] = working["oblast"].fillna("Unknown").astype(str)
    working["official_regional_baseline_proxy"] = pd.to_numeric(
        working["official_regional_baseline_proxy"],
        errors="coerce",
    )

    working = working.dropna(subset=["official_regional_baseline_proxy"]).copy()

    if working.empty:
        return None

    # Keep the visualization readable by showing the largest official baseline
    # candidates. This is not a risk ranking.
    top = (
        working.sort_values("official_regional_baseline_proxy", ascending=False)
        .head(top_n)
        .sort_values("official_regional_baseline_proxy")
    )

    labels = top["oblast"]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(labels, top["official_regional_baseline_proxy"])
    ax.set_xlabel("Official GRP Baseline Candidate")
    ax.set_title("Validation-Only Ukrstat Official Oblast Baseline Candidates")

    fig.tight_layout()
    path = CHART_DIR / "ukrstat_official_baseline_candidates.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)


def plot_official_baseline_validation_status() -> str | None:
    """Plot validation/scoring-control status for official baseline candidates."""
    ensure_dirs([CHART_DIR])

    candidates = _load_official_baseline_candidates()

    if candidates is None or candidates.empty:
        return None

    required_cols = {"validation_status", "current_use_in_scoring"}

    if not required_cols.issubset(set(candidates.columns)):
        return None

    working = candidates.copy()

    working["validation_status"] = (
        working["validation_status"].fillna("unknown").astype(str)
    )
    working["current_use_in_scoring"] = (
        working["current_use_in_scoring"].fillna("unknown").astype(str)
    )

    status_counts = (
        working.groupby(["validation_status", "current_use_in_scoring"], as_index=False)
        .size()
        .rename(columns={"size": "candidate_count"})
        .sort_values("candidate_count", ascending=True)
    )

    if status_counts.empty:
        return None

    labels = (
        status_counts["validation_status"].astype(str).str.replace("_", " ", regex=False)
        + " / "
        + status_counts["current_use_in_scoring"].astype(str).str.replace("_", " ", regex=False)
    ).apply(lambda value: _truncate_label(value, 72))

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(labels, status_counts["candidate_count"])
    ax.set_xlabel("Candidate Count")
    ax.set_title("Official Baseline Validation and Scoring-Control Status")

    fig.tight_layout()
    path = CHART_DIR / "ukrstat_official_baseline_validation_status.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return str(path)
