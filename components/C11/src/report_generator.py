from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
    CondPageBreak,
)

from .config import BASE_WEIGHTS, PROJECT_NAME, RAW_DIR, REPORT_DIR, TABLE_DIR
from .utils import ensure_dirs, safe_read_csv
from .reference_evidence import select_fiu_public_context, NABU_URL, STATS_URL


# ReportLab does not automatically shrink wide tables to the page frame.
# Keep one centralized width budget so every table builder can scale columns
# before the PDF is generated. This prevents clipped appendix tables.
REPORT_PAGE_SIZE = landscape(LETTER)
REPORT_LEFT_MARGIN = 0.55 * inch
REPORT_RIGHT_MARGIN = 0.55 * inch
REPORT_TOP_MARGIN = 0.55 * inch
REPORT_BOTTOM_MARGIN = 0.55 * inch
REPORT_CONTENT_WIDTH = REPORT_PAGE_SIZE[0] - REPORT_LEFT_MARGIN - REPORT_RIGHT_MARGIN


SOURCE_LAYER_MAP = {
    "Prozorro recent tenders": {
        "model_layer_supported": "Procurement integrity risk",
        "current_use": "Recent tender count/value proxy blended into procurement exposure.",
        "future_use": "Award concentration, buyer/supplier concentration, emergency procurement, repeat awards.",
    },
    "Prozorro expanded procurement features": {
        "model_layer_supported": "Procurement integrity expanded features",
        "current_use": (
            "Review-only oblast/sector procurement feature candidates generated "
            "from expanded Prozorro tender details. These artifacts are not blended "
            "into production scoring."
        ),
        "future_use": (
            "After coverage validation, sector/oblast mapping review, procurement/AML "
            "SME review, and scoring change-control approval, compare against or "
            "replace the existing procurement_awards_proxy layer."
        ),
    },
    "ACLED Ukraine events": {
        "model_layer_supported": "Conflict plausibility gap",
        "current_use": "Oblast-level conflict intensity proxy blended into conflict plausibility scoring.",
        "future_use": "Event-type weighting, recency weighting, fatalities, infrastructure disruption, spatial smoothing.",
    },
    "World Bank Ukraine fiscal context": {
        "model_layer_supported": "Macroeconomic/fiscal context",
        "current_use": "National fiscal, GDP, import, and export context retained for source-backed framing.",
        "future_use": "Trade dislocation baselines, macro stress controls, fiscal revenue comparison.",
    },
    "NBU financial-sector context": {
        "model_layer_supported": "Financial supervision exposure",
        "current_use": "National financial-sector context adjustment for supervision exposure proxy.",
        "future_use": "Banking activity, deposits, lending, payment-system indicators, sector stress measures.",
    },
    "Ukrstat SDMX dataflow discovery": {
        "model_layer_supported": "Official economic baseline discovery",
        "current_use": (
            "Official SDMX metadata, availability, and regional-account observation "
            "probes now produce validation-only oblast baseline candidates."
        ),
        "future_use": (
            "After unit, geography, NACE, indicator, and period validation, replace "
            "synthetic regional baseline fields with official oblast-level statistics."
        ),
    },
    "Official indicator alignment catalog": {
        "model_layer_supported": "Official indicator-to-layer mapping",
        "current_use": "Maps NBU and Ukrstat candidate indicators to WARIS model layers before replacing synthetic assumptions.",
        "future_use": "Use selected official indicators to replace synthetic revenue, trade, and supervisory-exposure fields.",
    },
    "Ukrstat regional accounts official baseline candidates": {
        "model_layer_supported": "Official regional baseline validation",
        "current_use": (
            "Official GRP oblast baseline candidates are available as validation-only "
            "artifacts and remain excluded from scoring."
        ),
        "future_use": (
            "After validation and SME review, decide whether official GRP should "
            "replace, benchmark, or rescale synthetic revenue baseline fields."
        ),
    },
    "Official baseline merge-planning artifacts": {
        "model_layer_supported": "Controlled benchmark integration",
        "current_use": (
            "Documents benchmark_only, rescale_revenue_baseline, and "
            "replace_oblast_baseline scenarios without changing production WARIS scores."
        ),
        "future_use": (
            "After transformation logic and SME review, decide whether any scenario "
            "should move into controlled scoring-integration change management."
        ),
    },
    "Official baseline merge-review artifacts": {
        "model_layer_supported": "Controlled benchmark review",
        "current_use": (
            "Reviews official-vs-synthetic baseline gaps and recommends the current "
            "benchmark_only posture without changing production WARIS scores."
        ),
        "future_use": (
            "Use gap review and scenario recommendations to support SME review and "
            "future scoring-integration change-control discussion."
        ),
    },
    "Official baseline benchmark review memo": {
        "model_layer_supported": "Controlled benchmark review documentation",
        "current_use": (
            "Plain-language analyst memo summarizing official baseline validation, "
            "merge-planning, merge-review findings, and the benchmark_only posture."
        ),
        "future_use": (
            "Use as a review artifact for SME discussion, model change-control "
            "planning, and GitHub/practitioner explanation."
        ),
    },
    "Wartime AML/CFT typology register": {
        "model_layer_supported": "Literature-supported AML/CFT typology context",
        "current_use": (
            "Reference-only typology register and WARIS layer map. These artifacts "
            "support documentation and future feature design, but are not scoring inputs."
        ),
        "future_use": (
            "After measurable indicator design, SME review, false-positive controls, "
            "and model change-control approval, selected typologies may inform future "
            "validated feature design."
        ),
    },
    "Official FIU/SFMS context artifacts": {
        "model_layer_supported": "Official FIU/SFMS source context and typology support",
        "current_use": (
            "Official national source-support context from SFMS/FIU reporting, "
            "case-referral, and typology-support artifacts. These artifacts are not "
            "oblast/sector scoring inputs."
        ),
        "future_use": (
            "Use for source-confidence review, governance, reporting context, and "
            "future measurable indicator design after SME review and change control."
        ),
    },
    "Official baseline context bridges and reviews": {
        "model_layer_supported": "Controlled source-context bridge review",
        "current_use": (
            "Review-only official-baseline-to-Prozorro, official-baseline-to-typology, "
            "official-baseline-to-FIU/SFMS, and official-baseline-to-operational-controls "
            "bridge/review artifacts."
        ),
        "future_use": (
            "Use bridge/review artifacts to support documentation and SME discussion. "
            "Do not use as scoring inputs without governed change approval."
        ),
    },
    "WARIS operational review/control artifacts": {
        "model_layer_supported": "Operational-control and human-review support",
        "current_use": (
            "Analyst-review, false-positive, source-freshness, run-manifest, and "
            "operational-controls bridge/review artifacts. These support governance, "
            "reproducibility, source maintenance, and human review only."
        ),
        "future_use": (
            "Use these controls to improve review discipline, false-positive handling, "
            "source refresh planning, reproducibility, and external presentation readiness. "
            "Do not treat them as scoring approval or validation."
        ),
    },
    "OpenSanctions Ukraine NSDC": {
        "model_layer_supported": "Sanctions exposure risk",
        "current_use": "Machine-readable Ukraine NSDC sanctions source availability and sample coverage.",
        "future_use": "Sector/jurisdiction exposure mapping, multi-list sanctions overlap, Russia/Belarus exposure.",
    },
}


def _pretty_table_text(value: object, max_chars: int = 220) -> str:
    """Format table-cell text for readable PDF wrapping."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""

    text = str(value).strip()

    replacements = {
        "direct_scoring_without_change_control": "direct scoring blocked without change control",
        "review_artifact_only": "review artifact only",
        "literature_support_and_typology_reference_only": "literature support / typology reference only",
        "official_fiu_context_and_typology_support_only": "official FIU/SFMS context support only",
        "controlled_benchmark_integration_only": "controlled benchmark integration only",
        "risk_layer_calculation_or_composite_scoring": "risk-layer or composite scoring",
        "production_score_change=none": "production score change = none",
        "production_score_change = none": "production score change = none",
        "used_in_waris_scoring=False": "used in WARIS scoring = False",
        "used_in_monte_carlo=False": "used in Monte Carlo = False",
        "review_only_compare_against_existing_procurement_layer": (
            "review only; compare against existing procurement proxy"
        ),
        "analyst_review_workflow_only": "analyst review workflow only",
        "human_review_support_only": "human review support only",
        "source_freshness_monitoring_only": "source freshness monitoring only",
        "run_manifest_documentation": "run manifest documentation",
        "context_review_only": "context review only",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "..."

    return text


def _normalize_col_widths(
    col_widths: list[float] | None,
    column_count: int,
    max_width: float = REPORT_CONTENT_WIDTH,
) -> list[float]:
    """Return column widths that always fit inside the report frame."""
    if column_count <= 0:
        return []

    if not col_widths:
        return [max_width / column_count for _ in range(column_count)]

    widths = list(col_widths[:column_count])

    if len(widths) < column_count:
        remaining = column_count - len(widths)
        used = sum(widths)
        fallback = max(0.55 * inch, (max_width - used) / max(remaining, 1))
        widths.extend([fallback for _ in range(remaining)])

    total = sum(widths)
    if total <= max_width:
        return widths

    scale = max_width / total
    return [max(0.42 * inch, width * scale) for width in widths]


def _table_cell_max_chars(column_count: int, explicit_max: int | None = None) -> int:
    """Use shorter cell text as tables get wider to preserve readable PDFs."""
    if explicit_max is not None:
        return explicit_max
    if column_count >= 12:
        return 95
    if column_count >= 10:
        return 120
    if column_count >= 8:
        return 150
    return 220


def _table_from_df(
    df: pd.DataFrame,
    columns: list[str],
    max_rows: int = 10,
    col_widths: list[float] | None = None,
    font_size: float = 6.0,
    leading: float | None = None,
    max_chars: int | None = None,
) -> Table:
    """Build a wrapped, page-width-safe ReportLab table from a dataframe."""
    styles = getSampleStyleSheet()

    available_columns = [col for col in columns if col in df.columns]

    if not available_columns:
        available_columns = list(df.columns[:8])

    if not available_columns:
        return Paragraph("No displayable columns available.", styles["BodyText"])

    shown = df[available_columns].head(max_rows).copy()

    column_count = len(available_columns)
    leading = leading if leading is not None else font_size + 1.2
    cell_max_chars = _table_cell_max_chars(column_count, max_chars)

    cell_style = ParagraphStyle(
        name=f"CellWrap_{column_count}_{font_size}",
        parent=styles["BodyText"],
        fontSize=font_size,
        leading=leading,
        wordWrap="CJK",
        splitLongWords=True,
    )

    header_style = ParagraphStyle(
        name=f"HeaderWrap_{column_count}_{font_size}",
        parent=styles["BodyText"],
        fontSize=max(5.6, font_size),
        leading=max(6.8, leading),
        fontName="Helvetica-Bold",
        wordWrap="CJK",
        splitLongWords=True,
    )

    for col in shown.columns:
        if pd.api.types.is_numeric_dtype(shown[col]):
            shown[col] = shown[col].map(lambda x: "not_available" if pd.isna(x) else f"{x:,.2f}")
        else:
            shown[col] = shown[col].fillna("")

    data = [
        [
            Paragraph(
                _pretty_table_text(str(c).replace("_", " "), 80),
                header_style,
            )
            for c in available_columns
        ]
    ]

    for row in shown.astype(str).values.tolist():
        data.append(
            [Paragraph(_pretty_table_text(cell, cell_max_chars), cell_style) for cell in row]
        )

    widths = _normalize_col_widths(col_widths, len(available_columns))
    table = Table(data, repeatRows=1, colWidths=widths)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F7F7F7")],
                ),
            ]
        )
    )

    return table


def _append_table(
    story: list,
    df: pd.DataFrame,
    columns: list[str],
    max_rows: int = 10,
    col_widths: list[float] | None = None,
    font_size: float = 6.0,
    max_chars: int | None = None,
) -> None:
    """Append a page-width-safe table and a small truncation note when useful."""
    if df is None or df.empty:
        return

    story.append(
        _table_from_df(
            df,
            columns,
            max_rows=max_rows,
            col_widths=col_widths,
            font_size=font_size,
            max_chars=max_chars,
        )
    )

    if len(df) > max_rows:
        styles = getSampleStyleSheet()
        if "Tiny" in styles:
            tiny_style = styles["Tiny"]
        else:
            tiny_style = ParagraphStyle(
                name="TinyLocal",
                parent=styles["BodyText"],
                fontSize=7,
                leading=9,
            )
        story.append(
            Paragraph(
                f"Showing first {max_rows:,} of {len(df):,} rows. Review the CSV artifact for the full table.",
                tiny_style,
            )
        )


def _safe_report_path() -> Path:
    """Return the default report path unless it appears locked."""
    ensure_dirs([REPORT_DIR])
    default_path = REPORT_DIR / "waris_ukraine_aml_risk_report.pdf"

    if not default_path.exists():
        return default_path

    try:
        with open(default_path, "ab"):
            pass
        return default_path
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return REPORT_DIR / f"waris_ukraine_aml_risk_report_{timestamp}.pdf"


def _load_table(filename: str) -> pd.DataFrame | None:
    """Load an output table from outputs/tables if it exists."""
    return safe_read_csv(TABLE_DIR / filename)


def _load_raw_table(filename: str) -> pd.DataFrame | None:
    """Load an output table from data/raw if it exists."""
    return safe_read_csv(RAW_DIR / filename)


def _table_row_count(filename: str, table_dir: Path = TABLE_DIR) -> int:
    """Return row count for an optional generated table."""
    df = safe_read_csv(table_dir / filename)
    return 0 if df is None else len(df)


def _normalize_live_status_for_report(status_df: pd.DataFrame) -> pd.DataFrame:
    """Correct source-context artifact rows for the PDF report."""
    if status_df is None or status_df.empty or "source" not in status_df.columns:
        return status_df

    out = status_df.copy()

    artifact_specs = {
        "Prozorro expanded procurement features": {
            "files": [
                "prozorro_procurement_features_oblast.csv",
                "prozorro_procurement_features_oblast_sector.csv",
                "prozorro_procurement_scoring_candidates.csv",
            ],
            "status": "artifact",
            "note": (
                "Generated review-only procurement artifacts available. These are "
                "not production scoring inputs."
            ),
        },
        "Wartime AML/CFT typology register": {
            "files": [
                "waris_wartime_aml_typology_register.csv",
                "waris_wartime_aml_typology_layer_map.csv",
                "waris_wartime_aml_typology_summary.csv",
            ],
            "status": "artifact",
            "note": (
                "Generated literature-support typology reference artifacts available. "
                "These are not scoring or Monte Carlo inputs."
            ),
        },
        "Official FIU/SFMS context artifacts": {
            "files": [
                "waris_fiu_official_source_register.csv",
                "waris_fiu_reporting_statistics_context.csv",
                "waris_fiu_case_referral_context.csv",
                "waris_fiu_typology_support_register.csv",
                "waris_fiu_context_summary.csv",
            ],
            "status": "artifact",
            "note": (
                "Generated official FIU/SFMS source-context artifacts available. "
                "These remain national context only."
            ),
        },
        "Ukrstat regional accounts official baseline candidates": {
            "files": [
                "ukrstat_oblast_baseline_candidates.csv",
                "official_baseline_readiness_decision.csv",
                "official_baseline_merge_review_summary.csv",
            ],
            "status": "benchmark artifact",
            "note": (
                "Official baseline candidate and benchmark-review artifacts available. "
                "Approved for controlled benchmark integration only; not scoring."
            ),
        },
        "WARIS operational review/control artifacts": {
            "files": [
                "analyst_review_queue.csv",
                "analyst_review_questions.csv",
                "analyst_review_summary.csv",
                "false_positive_risk_register.csv",
                "false_positive_controls.csv",
                "false_positive_review_checklist.csv",
                "false_positive_summary.csv",
                "source_freshness_inventory.csv",
                "source_freshness_assessment.csv",
                "source_freshness_summary.csv",
                "run_manifest.csv",
                "run_manifest_summary.csv",
                "official_baseline_operational_controls_context_bridge.csv",
                "official_baseline_operational_controls_context_review.csv",
            ],
            "status": "artifact",
            "note": (
                "Generated analyst-review, false-positive, source-freshness, run-manifest, "
                "and operational-control bridge/review artifacts available. These support "
                "governance and human review only."
            ),
        },
    }

    for source_name, spec in artifact_specs.items():
        mask = out["source"].astype(str).eq(source_name)
        if not mask.any():
            continue

        row_count = sum(_table_row_count(filename) for filename in spec["files"])

        if row_count > 0:
            out.loc[mask, "status"] = spec["status"]
            out.loc[mask, "rows"] = row_count
            out.loc[mask, "note"] = spec["note"]

    return out


def _load_report_text(filename: str) -> str | None:
    """Load a text/markdown report artifact from outputs/reports if it exists."""
    path = REPORT_DIR / filename

    if not path.exists():
        return None

    try:
        memo_text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    if not memo_text.strip():
        return None

    return memo_text


def _extract_memo_sections(
    memo_text: str,
    headings: list[str],
    max_chars_per_section: int = 1500,
) -> dict[str, str]:
    """Extract selected markdown sections from a memo by H2 headings."""
    sections: dict[str, str] = {}
    lines = memo_text.splitlines()

    current_heading: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_heading is None:
            return

        content = "\n".join(current_lines).strip()

        if len(content) > max_chars_per_section:
            content = content[:max_chars_per_section].rstrip() + "..."

        sections[current_heading] = content

    for line in lines:
        if line.startswith("## "):
            flush()
            current_heading = line.replace("## ", "", 1).strip()
            current_lines = []
        else:
            if current_heading is not None:
                current_lines.append(line)

    flush()

    return {heading: sections.get(heading, "") for heading in headings}


def _markdown_section_to_paragraphs(
    story: list,
    styles,
    section_text: str,
    max_lines: int = 18,
) -> None:
    """Render a compact markdown section into ReportLab paragraphs."""
    if not section_text.strip():
        story.append(Paragraph("Section not available.", styles["Small"]))
        return

    lines = section_text.splitlines()
    shown_lines = lines[:max_lines]

    in_code = False
    code_buffer: list[str] = []

    def flush_code() -> None:
        if not code_buffer:
            return

        safe_text = "<br/>".join(
            str(line).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            for line in code_buffer
        )
        story.append(Paragraph(safe_text, styles["Tiny"]))
        code_buffer.clear()

    for line in shown_lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_buffer.append(stripped)
            continue

        if not stripped:
            story.append(Spacer(1, 0.04 * inch))
            continue

        safe_line = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(safe_line, styles["Small"]))

    flush_code()

    if len(lines) > max_lines:
        story.append(
            Paragraph(
                "Memo section truncated in PDF. Review "
                "outputs/reports/official_baseline_benchmark_review_memo.md "
                "for the full text.",
                styles["Tiny"],
            )
        )



HOW_TO_READ_GUIDANCE = {
    "Prototype report - public-source, sector/oblast-level AML decision support": (
        "Start here for the overall purpose of the report. The report is a review-support artifact, "
        "not an allegation, investigation result, or automated decision."
    ),
    "Methodology": (
        "Use this section to understand how the model combines public-source indicators, synthetic fallback fields, "
        "review-only context artifacts, and governance controls. The weights explain structure, not proof."
    ),
    "Top review signals": (
        "Read these rows as the highest-priority records for human review. A high score means 'look here first,' "
        "not that wrongdoing occurred."
    ),
    "Oblast summary": (
        "Use this as a regional comparison. It summarizes patterns by oblast so readers can see where review signals "
        "cluster geographically."
    ),
    "Sector summary": (
        "Use this as a sector comparison. It shows which sectors carry stronger review signals across oblasts."
    ),
    "Monte Carlo robustness": (
        "Use this section to see whether rankings are stable when assumptions are varied. Robustness supports confidence "
        "in prioritization, but it does not validate the model for operational decisions."
    ),
    "Source register": (
        "Use this section to see where the data or artifact came from and whether it is live, fallback, benchmark, or "
        "review-only source context."
    ),
    "Live/source-backed enrichment and artifact status": (
        "Use this table to see which sources were available during the run. Failed live sources do not necessarily break "
        "the model because fallback and artifact tracking preserve transparency."
    ),
    "ACLED / conflict plausibility summary": (
        "Use this section to understand how conflict conditions may explain unusual revenue, procurement, or sector patterns. "
        "Conflict context is often a false-positive explanation."
    ),
    "Expanded Prozorro procurement feature appendix": (
        "Use this appendix to understand procurement review indicators. These are review-only candidate features and should "
        "not be read as findings about buyers, suppliers, sectors, or oblasts."
    ),
    "Procurement feature summary": (
        "Use this as a quick status check for the expanded procurement layer: rows created, mapping quality, top candidates, "
        "and controls."
    ),
    "Oblast procurement feature candidates": (
        "Read these as oblast-level procurement patterns that may deserve review. Scores are not allegations and are not "
        "production WARIS scores."
    ),
    "Oblast-sector procurement candidates": (
        "Read these as sector-and-oblast procurement patterns to compare against existing WARIS procurement proxies before "
        "any future scoring discussion."
    ),
    "Procurement scoring-candidate control table": (
        "This table documents what could be considered in a future governed scoring branch. The current production score "
        "change remains none."
    ),
    "Expanded Prozorro raw feature sample": (
        "Use this sample for audit traceability. It shows tender-level feature rows used to create aggregate review artifacts."
    ),
    "Wartime AML/CFT typology reference appendix": (
        "Use this appendix as background context. Typologies explain possible AML/CFT themes, but they are not measured "
        "indicators and do not change scores."
    ),
    "Typology summary and controls": (
        "Use this table to confirm the typology layer remains literature-support only, outside scoring and Monte Carlo."
    ),
    "Typology register": (
        "Read this as a catalog of typology ideas and source-supported themes that may guide future feature design."
    ),
    "Typology-to-WARIS layer map": (
        "Use this map to see which WARIS risk layers each typology could inform in the future, after measurable indicators "
        "and change control."
    ),
    "Official FIU/SFMS context appendix": (
        "Use this appendix as national-level official context. It supports governance and source confidence, not oblast/sector "
        "scoring."
    ),
    "FIU/SFMS context summary": (
        "Use this as a status table for the official FIU/SFMS context artifacts and their no-scoring controls."
    ),
    "Official source register": (
        "Use this to identify the official source documents or datasets behind the FIU/SFMS context layer."
    ),
    "Q1 2025 reporting statistics context": (
        "Read this as national reporting context. It should not be assigned to a specific oblast, sector, person, or entity."
    ),
    "Q1 2026 SFMS-to-NABU referral context": (
        "Read this as official case-referral context, not as a WARIS finding. It supports typology awareness only."
    ),
    "Official typology-support register": (
        "Use this to see which official FIU/SFMS typology themes support the broader typology appendix."
    ),
    "Official baseline source-context bridge appendix": (
        "Use this appendix to see how official baseline context is compared with Prozorro, typology, and FIU/SFMS artifacts. "
        "Bridge tables are review artifacts only."
    ),
    "Official baseline to Prozorro review": (
        "Use this table to compare official economic baseline scale with procurement context. It does not convert procurement "
        "features into scoring inputs."
    ),
    "Official baseline to wartime AML/CFT typology review": (
        "Use this table to compare official baseline gaps with typology families for documentation and SME discussion only."
    ),
    "Official baseline to FIU/SFMS context review": (
        "Use this table to compare official baseline gaps with FIU/SFMS typology themes for documentation only."
    ),
    "Official NBU / Ukrstat indicator alignment": (
        "Use this section to see which official indicators could eventually replace synthetic assumptions after validation."
    ),
    "Candidate indicators by WARIS layer": (
        "Use this summary to see where official indicators may support future model layers."
    ),
    "Selected candidate official indicators": (
        "Read these as candidates for future validation, not as fields already approved for scoring."
    ),
    "Model governance and validation appendix": (
        "Use this appendix to understand intended use, limitations, validation status, and monitoring controls."
    ),
    "Model inventory": (
        "Use this as the model's identity card: version, status, scope, risk rating, and prohibited uses."
    ),
    "Governance summary": (
        "Use this as a quick view of governance controls and current model-risk posture."
    ),
    "Validation checklist": (
        "Use this to see what has been checked and what remains to be validated before operational use."
    ),
    "Model limitations register": (
        "Use this to understand what the model cannot safely claim and which limitations need mitigation."
    ),
    "Ongoing monitoring plan": (
        "Use this to see what should be watched over time to keep the prototype transparent and controlled."
    ),
    "Source confidence and field lineage appendix": (
        "Use this appendix to understand which fields are source-backed, synthetic, fallback, or candidates for replacement."
    ),
    "Source confidence summary": (
        "Use this as a quick source-quality overview across model areas."
    ),
    "High-priority field replacements": (
        "Use this list to identify the fields that most need stronger official or live-source replacement."
    ),
    "Source confidence assessment by model area": (
        "Use this table to compare source quality across model components."
    ),
    "Field source register": (
        "Use this as field-level lineage documentation for auditability and future validation."
    ),
    "Official baseline validation gate appendix": (
        "Use this appendix to understand whether official Ukrstat GRP candidates are ready for controlled benchmark use. "
        "They are not approved for scoring."
    ),
    "Readiness decision": (
        "Use this as the main decision record for the official baseline gate."
    ),
    "Official unit and scale evidence": (
        "Use this to confirm units, scaling, frequency, and source interpretation before any benchmark comparison."
    ),
    "Unit evidence sample rows": (
        "Use these rows to audit how the official data export supports the unit and scale interpretation."
    ),
    "Validation summary": (
        "Use this as a concise summary of validation checks and next actions."
    ),
    "Validation check register": (
        "Use this as a detailed checklist of pass/review-required controls."
    ),
    "Geography crosswalk validation": (
        "Use this to confirm official region names and codes map cleanly into WARIS oblast names."
    ),
    "Period coverage validation": (
        "Use this to check whether the official data period is usable and comparable."
    ),
    "Official baseline controlled benchmark-integration appendix": (
        "Use this appendix to compare official and synthetic baseline scenarios. These scenarios are non-production benchmarks."
    ),
    "Merge-readiness summary": (
        "Use this table to see whether benchmark comparison artifacts are ready for review."
    ),
    "Controlled merge-plan scenarios": (
        "Use this to compare benchmark-only, rescale, and replacement scenarios without changing production scoring."
    ),
    "Benchmark-only comparison": (
        "Use this table to see official-vs-synthetic gaps. Large gaps should trigger review, not automatic replacement."
    ),
    "Rescale revenue baseline scenario": (
        "Use this as a sensitivity scenario showing what happens if synthetic baselines are rescaled."
    ),
    "Replace-oblast-baseline scenario": (
        "Use this as a non-production scenario showing a stronger replacement option that still needs validation and SME review."
    ),
    "Official baseline controlled merge-review appendix": (
        "Use this appendix to understand the recommended current posture after reviewing benchmark gaps and context bridges."
    ),
    "Merge-review summary": (
        "Use this as the short conclusion of the merge-review process."
    ),
    "Scenario recommendations": (
        "Use this table to understand which scenario is recommended now and what is blocked until validation."
    ),
    "Official-vs-synthetic gap review": (
        "Use this to identify the oblasts where official and synthetic baselines differ most."
    ),
    "Wartime typology context review snapshot": (
        "Use this as a documentation snapshot connecting typology themes to benchmark-review context."
    ),
    "FIU/SFMS context review snapshot": (
        "Use this as a documentation snapshot connecting FIU/SFMS themes to benchmark-review context."
    ),
    "Official baseline benchmark review memo": (
        "Use this memo section as the plain-language explanation of the official baseline review."
    ),
    "Ukrstat official baseline transition appendix": (
        "Use this appendix to trace the path from discovery to official baseline candidate generation."
    ),
    "Official regional baseline transition status": (
        "Use this to understand the status of the transition from placeholder/synthetic baseline to official benchmark artifacts."
    ),
    "All-oblast official baseline candidates": (
        "Use this table to see official candidate values by oblast. These values are benchmark candidates, not scoring inputs."
    ),
    "All-oblast probe results": (
        "Use this for audit evidence showing which official data queries returned usable responses."
    ),
    "Availability-derived query values": (
        "Use this to understand which query values were discovered from availability metadata."
    ),
    "Single-oblast confirmed baseline candidate": (
        "Use this as proof that the confirmed query pattern returned an interpretable oblast candidate."
    ),
    "Regional accounts dataflow discovery": (
        "Use this to see how official Ukrstat regional accounts dataflows were identified."
    ),
    "Regional accounts metadata clues": (
        "Use this to see which metadata supported the official baseline interpretation."
    ),
    "Ukrstat registry references": (
        "Use this to trace official registry references used in the discovery process."
    ),
    "Ukrstat endpoint probe results": (
        "Use this to see which API endpoints worked or failed during discovery."
    ),
    "Ukrstat observation query plan": (
        "Use this to understand the query pattern used to retrieve official observations."
    ),
    "Original placeholder baseline transition table": (
        "Use this to see the previous placeholder baseline and why it is being transitioned into official benchmark artifacts."
    ),
    "Operational controls appendix": (
        "Use this appendix to understand the human-review, false-positive, source-freshness, and run-manifest safeguards. "
        "These controls support review discipline and reproducibility, not scoring approval."
    ),
    "Analyst review workflow": (
        "Use this section to see what records or questions should be reviewed by a human analyst. It does not create findings."
    ),
    "False-positive controls": (
        "Use this section to identify benign explanations and review checks that should be considered before interpreting a signal."
    ),
    "Source freshness monitoring": (
        "Use this section to see which artifacts are fresh, aging, stale, missing, or empty for their documented use."
    ),
    "Run manifest and reproducibility": (
        "Use this section to identify what artifacts were generated in the run and whether score-change controls remained inactive."
    ),
    "Official baseline to operational controls review": (
        "Use this table to confirm operational safeguards are present alongside the official baseline benchmark package. It is not scoring approval."
    ),
    "Data coverage appendix": (
        "Use this appendix to understand which source families support which model layers, and where source gaps remain."
    ),
    "Recommended next build steps": (
        "Use this section as the development roadmap. These are technical next steps, not model findings."
    ),
}


def _append_how_to_read(story: list, styles, section_title: object) -> None:
    """Append a short plain-language reader guide after a section heading."""
    title = "" if section_title is None else str(section_title)
    guidance = HOW_TO_READ_GUIDANCE.get(
        title,
        (
            "This section explains one part of the WARIS review workflow. Focus on what question it answers, "
            "what data or artifact supports it, and whether it is a review aid rather than a scoring or enforcement output."
        ),
    )

    style = styles["HowToRead"] if "HowToRead" in getattr(styles, "byName", {}) else styles["Small"]

    story.append(
        Paragraph(
            f"<b>How to read:</b> {guidance}",
            style,
        )
    )
    story.append(Spacer(1, 0.07 * inch))

def _build_live_status_section(
    story: list,
    styles,
    live_status: pd.DataFrame | None,
) -> None:
    """Add live/source-backed enrichment status table when available."""
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Live/source-backed enrichment and artifact status", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Live/source-backed enrichment and artifact status')

    story.append(
        Paragraph(
            "WARIS uses synthetic fallback fields to keep the prototype runnable, "
            "then blends selected live public-source enrichments into selected risk "
            "proxies. This table also reports generated source-context and operational "
            "control artifacts such as official baseline, Prozorro, wartime typology, "
            "FIU/SFMS context, analyst-review, false-positive, source-freshness, "
            "and run-manifest outputs. Artifact rows are governance/context/control "
            "records, not scoring inputs.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.08 * inch))

    if live_status is None or live_status.empty:
        story.append(
            Paragraph("No live status table was provided for this run.", styles["Small"])
        )
        return

    status_df = live_status.copy()
    status_df = status_df.rename(
        columns={
            "source_name": "source",
            "rows": "rows",
            "status": "status",
            "note": "note",
        }
    )
    status_df = _normalize_live_status_for_report(status_df)

    desired_columns = ["source", "status", "rows", "note"]
    available_columns = [col for col in desired_columns if col in status_df.columns]

    story.append(
        _table_from_df(
            status_df,
            available_columns,
            max_rows=10,
            col_widths=[2.2 * inch, 0.75 * inch, 0.55 * inch, 5.6 * inch],
        )
    )


def _build_acled_conflict_section(
    story: list,
    styles,
    scored: pd.DataFrame,
) -> None:
    """Add an oblast-level ACLED/conflict proxy summary when available."""
    if scored is None or scored.empty or "oblast" not in scored.columns:
        return

    proxy_col = None

    if "conflict_intensity_proxy_live" in scored.columns:
        proxy_col = "conflict_intensity_proxy_live"
    elif "conflict_intensity_proxy" in scored.columns:
        proxy_col = "conflict_intensity_proxy"

    if proxy_col is None:
        return

    agg_dict = {
        "conflict_intensity_proxy": (proxy_col, "mean"),
    }

    if "waris_aml_review_score" in scored.columns:
        agg_dict["max_waris_aml_review_score"] = ("waris_aml_review_score", "max")

    if "conflict_plausibility_gap" in scored.columns:
        agg_dict["avg_conflict_plausibility_gap"] = (
            "conflict_plausibility_gap",
            "mean",
        )

    conflict_summary = (
        scored.groupby("oblast", as_index=False)
        .agg(**agg_dict)
        .sort_values("conflict_intensity_proxy", ascending=False)
    )

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("ACLED / conflict plausibility summary", styles["Heading2"]))
    _append_how_to_read(story, styles, 'ACLED / conflict plausibility summary')

    story.append(
        Paragraph(
            "This table summarizes the oblast-level conflict intensity proxy used "
            "to support the conflict-plausibility layer. When ACLED is live, the "
            "proxy is blended from credentialed conflict-event data. When ACLED is "
            "unavailable, the model uses synthetic fallback conflict fields.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.08 * inch))

    story.append(
        _table_from_df(
            conflict_summary,
            [
                "oblast",
                "conflict_intensity_proxy",
                "avg_conflict_plausibility_gap",
                "max_waris_aml_review_score",
            ],
            max_rows=15,
            col_widths=[1.7 * inch, 1.7 * inch, 1.9 * inch, 2.0 * inch],
        )
    )


def _build_prozorro_procurement_features_section(story: list, styles) -> None:
    """Add expanded Prozorro procurement feature appendix."""
    oblast_features = _load_table("prozorro_procurement_features_oblast.csv")
    oblast_sector_features = _load_table("prozorro_procurement_features_oblast_sector.csv")
    scoring_candidates = _load_table("prozorro_procurement_scoring_candidates.csv")
    feature_summary = _load_table("prozorro_procurement_feature_summary.csv")
    raw_feature_rows = _load_raw_table("prozorro_expanded_feature_rows_raw.csv")

    if all(
        df is None or df.empty
        for df in [
            oblast_features,
            oblast_sector_features,
            scoring_candidates,
            feature_summary,
            raw_feature_rows,
        ]
    ):
        return

    story.append(PageBreak())
    story.append(
        Paragraph(
            "Expanded Prozorro procurement feature appendix",
            styles["Heading2"],
        )
    )
    _append_how_to_read(story, styles, 'Expanded Prozorro procurement feature appendix')

    story.append(
        Paragraph(
            "This appendix documents the expanded Prozorro procurement feature layer. "
            "The module creates source-backed procurement review artifacts such as "
            "tender count, expected value, single-bid or single-supplier proxy, buyer "
            "concentration, procurement-method diversity, reconstruction/emergency "
            "keyword exposure, and oblast-sector review-priority candidates. These "
            "features are review-only candidate artifacts and do not alter WARIS risk "
            "layers, composite scores, risk bands, review rationales, or Monte Carlo "
            "simulations. Missing numeric observations are shown as unavailable. "
            "Sparse or partially observed procurement groups have withheld candidates; "
            "observation denominators and support statuses are retained in the CSV tables. "
            "All regional/sector tables remain private review artifacts pending individual release review.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    if feature_summary is not None and not feature_summary.empty:
        story.append(Paragraph("Procurement feature summary", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Procurement feature summary')
        story.append(
            _table_from_df(
                feature_summary,
                [
                    "summary_area",
                    "status",
                    "value",
                    "recommended_next_action",
                ],
                max_rows=8,
                col_widths=[
                    1.95 * inch,
                    1.2 * inch,
                    2.1 * inch,
                    3.9 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if oblast_features is not None and not oblast_features.empty:
        story.append(Paragraph("Oblast procurement feature candidates", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Oblast procurement feature candidates')
        story.append(
            Paragraph(
                "This table ranks oblast-level procurement review-priority candidates. "
                "The score is a non-production candidate summary derived from expanded "
                "Prozorro features. It is not a finding of misconduct and is not a "
                "production WARIS score.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))

        oblast_display = oblast_features.copy()
        if "procurement_review_priority_candidate" in oblast_display.columns:
            oblast_display["procurement_review_priority_candidate"] = pd.to_numeric(
                oblast_display["procurement_review_priority_candidate"],
                errors="coerce",
            )
            oblast_display = oblast_display.sort_values(
                "procurement_review_priority_candidate",
                ascending=False,
            )

        story.append(
            _table_from_df(
                oblast_display,
                [
                    "oblast",
                    "tender_count",
                    "total_expected_value",
                    "single_bid_or_supplier_proxy_rate",
                    "reconstruction_emergency_tender_count",
                    "reconstruction_emergency_share",
                    "top_buyer_tender_share",
                    "procurement_review_priority_candidate",
                ],
                max_rows=10,
                col_widths=[
                    1.05 * inch,
                    0.75 * inch,
                    1.2 * inch,
                    1.05 * inch,
                    1.1 * inch,
                    1.0 * inch,
                    1.0 * inch,
                    1.15 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if oblast_sector_features is not None and not oblast_sector_features.empty:
        story.append(PageBreak())
        story.append(Paragraph("Oblast-sector procurement candidates", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Oblast-sector procurement candidates')
        story.append(
            Paragraph(
                "This table shows the top oblast-sector procurement feature candidates. "
                "It is intended to help compare the expanded Prozorro layer against the "
                "existing procurement_awards_proxy field before any future scoring "
                "integration discussion.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))

        sector_display = oblast_sector_features.copy()
        if "procurement_review_priority_candidate" in sector_display.columns:
            sector_display["procurement_review_priority_candidate"] = pd.to_numeric(
                sector_display["procurement_review_priority_candidate"],
                errors="coerce",
            )
            sector_display = sector_display.sort_values(
                "procurement_review_priority_candidate",
                ascending=False,
            )

        story.append(
            _table_from_df(
                sector_display,
                [
                    "oblast",
                    "sector",
                    "tender_count",
                    "total_expected_value",
                    "single_bid_or_supplier_proxy_rate",
                    "reconstruction_emergency_tender_count",
                    "procurement_review_priority_candidate",
                ],
                max_rows=12,
                col_widths=[
                    0.95 * inch,
                    1.6 * inch,
                    0.75 * inch,
                    1.25 * inch,
                    1.25 * inch,
                    1.2 * inch,
                    1.15 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if scoring_candidates is not None and not scoring_candidates.empty:
        story.append(Paragraph("Procurement scoring-candidate control table", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Procurement scoring-candidate control table')
        story.append(
            Paragraph(
                "This table documents what the expanded procurement layer could target "
                "in a future governed scoring branch. The current production score "
                "change remains none.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))

        candidate_display = scoring_candidates.copy()
        if "procurement_review_priority_candidate" in candidate_display.columns:
            candidate_display["procurement_review_priority_candidate"] = pd.to_numeric(
                candidate_display["procurement_review_priority_candidate"],
                errors="coerce",
            )
            candidate_display = candidate_display.sort_values(
                "procurement_review_priority_candidate",
                ascending=False,
            )

        story.append(
            _table_from_df(
                candidate_display,
                [
                    "oblast",
                    "sector",
                    "procurement_review_priority_candidate",
                    "production_score_change",
                ],
                max_rows=12,
                col_widths=[
                    1.05 * inch,
                    1.85 * inch,
                    1.4 * inch,
                    1.2 * inch,
                ],
            )
        )
        story.append(
            Paragraph(
                "Required before scoring: expanded historical coverage, buyer/oblast "
                "mapping validation, supplier/bid field validation, procurement/AML SME "
                "review, false-positive controls, and approved model change control.",
                styles["Tiny"],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if raw_feature_rows is not None and not raw_feature_rows.empty:
        story.append(CondPageBreak(2.4 * inch))
        story.append(Paragraph("Expanded Prozorro raw feature sample", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Expanded Prozorro raw feature sample')
        story.append(
            Paragraph(
                "This sample shows the normalized tender-level feature rows used to "
                "build the aggregate procurement artifacts. It is included for audit "
                "traceability and should not be interpreted as an allegation against "
                "any buyer, supplier, oblast, or sector.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))

        story.append(
            _table_from_df(
                raw_feature_rows,
                [
                    "tender_public_id",
                    "date_modified",
                    "status",
                    "procurement_method_type",
                    "oblast",
                    "sector",
                    "value_amount",
                    "single_bid_or_supplier_proxy",
                    "reconstruction_emergency_flag",
                    "mapped_to_waris_oblast",
                    "mapped_to_waris_sector",
                ],
                max_rows=14,
                col_widths=[
                    1.0 * inch,
                    1.0 * inch,
                    0.95 * inch,
                    1.2 * inch,
                    0.95 * inch,
                    1.45 * inch,
                    0.95 * inch,
                    0.85 * inch,
                    0.85 * inch,
                    0.85 * inch,
                    0.85 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Current interpretation: expanded Prozorro procurement features improve "
            "source-backed procurement review context, but they remain review-only. "
            "Before any scoring integration, WARIS needs broader coverage review, "
            "buyer/address/oblast mapping validation, sector-mapping validation, "
            "procurement and AML SME review, false-positive controls, and formal "
            "model change-control approval.",
            styles["Small"],
        )
    )


def _build_wartime_aml_typology_section(story: list, styles) -> None:
    """Add wartime AML/CFT typology register appendix."""
    typology_register = _load_table("waris_wartime_aml_typology_register.csv")
    layer_map = _load_table("waris_wartime_aml_typology_layer_map.csv")
    typology_summary = _load_table("waris_wartime_aml_typology_summary.csv")

    if all(
        df is None or df.empty
        for df in [typology_register, layer_map, typology_summary]
    ):
        return

    story.append(PageBreak())
    story.append(
        Paragraph("Wartime AML/CFT typology reference appendix", styles["Heading2"])
    )
    _append_how_to_read(story, styles, 'Wartime AML/CFT typology reference appendix')

    story.append(
        Paragraph(
            "This appendix summarizes the literature-supported wartime AML/CFT "
            "typology register. The typologies are source-support and model-design "
            "references only. They do not identify wrongdoing, do not make oblast, "
            "sector, entity, or person-level conclusions, and do not alter WARIS "
            "risk layers, composite scores, risk bands, review rationales, or Monte "
            "Carlo simulations.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    if typology_summary is not None and not typology_summary.empty:
        story.append(Paragraph("Typology summary and controls", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Typology summary and controls')
        story.append(
            _table_from_df(
                typology_summary,
                [
                    "summary_area",
                    "status",
                    "value",
                    "recommended_next_action",
                    "current_use",
                    "production_score_change",
                    "used_in_waris_scoring",
                    "used_in_monte_carlo",
                ],
                max_rows=10,
                col_widths=[
                    1.45 * inch,
                    1.0 * inch,
                    1.95 * inch,
                    3.2 * inch,
                    1.25 * inch,
                    0.8 * inch,
                    0.8 * inch,
                    0.8 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if typology_register is not None and not typology_register.empty:
        story.append(Paragraph("Typology register", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Typology register')
        story.append(
            _table_from_df(
                typology_register,
                [
                    "typology_id",
                    "typology_name",
                    "typology_family",
                    "waris_layer_candidates",
                    "confidence_level",
                    "current_use",
                    "production_score_change",
                    "used_in_waris_scoring",
                    "used_in_monte_carlo",
                    "notes",
                ],
                max_rows=12,
                col_widths=[
                    0.65 * inch,
                    1.55 * inch,
                    1.25 * inch,
                    1.55 * inch,
                    1.05 * inch,
                    1.15 * inch,
                    0.8 * inch,
                    0.75 * inch,
                    0.75 * inch,
                    1.55 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if layer_map is not None and not layer_map.empty:
        story.append(Paragraph("Typology-to-WARIS layer map", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Typology-to-WARIS layer map')
        story.append(
            _table_from_df(
                layer_map,
                [
                    "typology_id",
                    "typology_family",
                    "waris_layer_candidate",
                    "current_use",
                    "prohibited_use",
                    "production_score_change",
                    "used_in_waris_scoring",
                    "used_in_monte_carlo",
                    "control_note",
                ],
                max_rows=18,
                col_widths=[
                    0.7 * inch,
                    1.25 * inch,
                    1.65 * inch,
                    1.15 * inch,
                    1.45 * inch,
                    0.9 * inch,
                    0.8 * inch,
                    0.8 * inch,
                    1.85 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Current interpretation: wartime AML/CFT typologies may support source "
            "confidence, model documentation, and future feature planning. They are "
            "not measured indicators and must not be converted into scoring inputs "
            "without measurable indicator design, source validation, SME review, "
            "false-positive controls, and formal change-control approval.",
            styles["Small"],
        )
    )


def _build_fiu_official_context_section(story: list, styles) -> None:
    """Add official FIU/SFMS context appendix."""
    source_register = _load_table("waris_fiu_official_source_register.csv")
    reporting_stats = _load_table("waris_fiu_reporting_statistics_context.csv")
    case_referrals = _load_table("waris_fiu_case_referral_context.csv")
    typology_support = _load_table("waris_fiu_typology_support_register.csv")
    context_summary = _load_table("waris_fiu_context_summary.csv")
    selected_statistics = select_fiu_public_context(reporting_stats, "statistics")
    selected_referrals = select_fiu_public_context(case_referrals, "referrals")
    selected_typologies = select_fiu_public_context(typology_support, "typologies")
    reporting_stats = selected_statistics.frame
    case_referrals = selected_referrals.frame
    typology_support = selected_typologies.frame

    if all(
        df is None or df.empty
        for df in [
            source_register,
            reporting_stats,
            case_referrals,
            typology_support,
            context_summary,
        ]
    ):
        return

    story.append(PageBreak())
    story.append(Paragraph("Official FIU/SFMS context appendix", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Official FIU/SFMS context appendix')

    story.append(
        Paragraph(
            "This appendix summarizes official FIU/SFMS source-context artifacts. "
            "These artifacts provide national reporting, referral, and typology-support "
            "context for governance and source-confidence review. They are not direct "
            "WARIS oblast/sector scoring inputs and do not imply any entity, person, "
            "sector, or oblast finding.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    story.append(
        Paragraph(
            "Reference review is partial. Unverified annual-report claims, ambiguous "
            "metrics and rows without qualifying reference annotations are withheld "
            "from the following context tables; internal records are preserved. "
            f"Withheld rows: statistics={selected_statistics.withheld_rows}, "
            f"referrals={selected_referrals.withheld_rows}, "
            f"typologies={selected_typologies.withheld_rows}. "
            "Recorded checks do not certify source-file authenticity, current "
            "freshness, redistribution rights or operational validity.",
            styles["Small"],
        )
    )

    story.append(
        Paragraph(
            'Source: State Financial Monitoring Service of Ukraine. '
            f'<link href="{STATS_URL}">Q1 2025 reporting statistics, pp. 1-2</link>; '
            f'<link href="{NABU_URL}">Q1 2026 NABU referral statistics, p. 1</link>. '
            'Site default CC BY 4.0 unless otherwise specified. WARIS transcribes '
            'national aggregates and adds review annotations; no scoring use. '
            'Quarterly text review recorded October 13, 2026; source PDF bytes '
            'and historical retrieval dates have not been authenticated.',
            styles["Small"],
        )
    )

    if context_summary is not None and not context_summary.empty:
        story.append(Paragraph("FIU/SFMS context summary", styles["Heading3"]))
        _append_how_to_read(story, styles, 'FIU/SFMS context summary')
        story.append(
            _table_from_df(
                context_summary,
                [
                    "summary_area",
                    "status",
                    "value",
                    "recommended_next_action",
                    "current_use",
                    "production_score_change",
                    "used_in_waris_scoring",
                    "used_in_monte_carlo",
                ],
                max_rows=10,
                col_widths=[
                    1.55 * inch,
                    1.05 * inch,
                    2.0 * inch,
                    3.0 * inch,
                    1.2 * inch,
                    0.8 * inch,
                    0.8 * inch,
                    0.8 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if source_register is not None and not source_register.empty:
        story.append(Paragraph("Official source register", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Official source register')
        story.append(
            _table_from_df(
                source_register,
                [
                    "source_id",
                    "source_name",
                    "source_type",
                    "reporting_period",
                    "source_mode",
                    "current_use",
                    "prohibited_use",
                    "production_score_change",
                    "control_note",
                ],
                max_rows=6,
                col_widths=[
                    0.75 * inch,
                    1.8 * inch,
                    1.0 * inch,
                    0.9 * inch,
                    0.95 * inch,
                    1.2 * inch,
                    1.35 * inch,
                    0.8 * inch,
                    1.5 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if reporting_stats is not None and not reporting_stats.empty:
        story.append(Paragraph("Q1 2025 reporting statistics context", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Q1 2025 reporting statistics context')
        story.append(
            _table_from_df(
                reporting_stats,
                [
                    "metric_name",
                    "metric_value",
                    "metric_unit",
                    "notes",
                    "current_use",
                    "production_score_change",
                ],
                max_rows=14,
                col_widths=[
                    1.7 * inch,
                    0.95 * inch,
                    0.8 * inch,
                    3.1 * inch,
                    1.2 * inch,
                    0.8 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if case_referrals is not None and not case_referrals.empty:
        story.append(PageBreak())
        story.append(Paragraph("Q1 2026 SFMS-to-NABU referral context", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Q1 2026 SFMS-to-NABU referral context')
        story.append(
            _table_from_df(
                case_referrals,
                [
                    "person_category",
                    "case_referrals_and_additional_referrals",
                    "funds_related_to_crime_uah_mln",
                    "notes",
                    "current_use",
                    "production_score_change",
                ],
                max_rows=10,
                col_widths=[
                    1.3 * inch,
                    1.1 * inch,
                    1.1 * inch,
                    3.3 * inch,
                    1.2 * inch,
                    0.8 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if typology_support is not None and not typology_support.empty:
        story.append(Paragraph("Official typology-support register", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Official typology-support register')
        story.append(
            _table_from_df(
                typology_support,
                [
                    "typology_support_id",
                    "typology_name",
                    "typology_family",
                    "waris_layer_candidates",
                    "source_basis",
                    "current_use",
                    "production_score_change",
                    "used_in_waris_scoring",
                    "used_in_monte_carlo",
                ],
                max_rows=12,
                col_widths=[
                    0.85 * inch,
                    1.45 * inch,
                    1.2 * inch,
                    1.5 * inch,
                    1.7 * inch,
                    1.2 * inch,
                    0.8 * inch,
                    0.75 * inch,
                    0.75 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Current interpretation: official FIU/SFMS context strengthens source "
            "documentation and typology support, but it remains national context. "
            "It must not be converted into oblast/sector scoring without measurable "
            "indicator design, source-validation logic, SME review, false-positive "
            "controls, and formal change-control approval.",
            styles["Small"],
        )
    )


def _build_official_baseline_context_bridge_section(story: list, styles) -> None:
    """Add official-baseline-to-context bridge and review appendix."""
    prozorro_bridge = _load_table("official_baseline_prozorro_context_bridge.csv")
    prozorro_review = _load_table("official_baseline_prozorro_context_review.csv")
    typology_bridge = _load_table("official_baseline_wartime_typology_context_bridge.csv")
    typology_review = _load_table("official_baseline_wartime_typology_context_review.csv")
    fiu_bridge = _load_table("official_baseline_fiu_context_bridge.csv")
    fiu_review = _load_table("official_baseline_fiu_context_review.csv")
    operational_bridge = _load_table(
        "official_baseline_operational_controls_context_bridge.csv"
    )
    operational_review = _load_table(
        "official_baseline_operational_controls_context_review.csv"
    )

    if all(
        df is None or df.empty
        for df in [
            prozorro_bridge,
            prozorro_review,
            typology_bridge,
            typology_review,
            fiu_bridge,
            fiu_review,
            operational_bridge,
            operational_review,
        ]
    ):
        return

    story.append(PageBreak())
    story.append(
        Paragraph("Official baseline source-context bridge appendix", styles["Heading2"])
    )
    _append_how_to_read(story, styles, 'Official baseline source-context bridge appendix')

    story.append(
        Paragraph(
            "This appendix documents review-only bridge artifacts comparing official "
            "baseline benchmark context with expanded Prozorro procurement candidates, "
            "wartime AML/CFT typology references, official FIU/SFMS source context, "
            "and operational-control artifacts. These bridge artifacts support "
            "documentation and SME review only. They "
            "do not approve scoring integration and do not alter WARIS outputs.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    bridge_pairs = [
        (
            "Official baseline to Prozorro review",
            prozorro_review,
            [
                "waris_oblast",
                "sector",
                "official_grp_million_uah",
                "official_vs_synthetic_index_gap",
                "procurement_review_priority_candidate",
                "current_use",
                "prohibited_use",
                "production_score_change",
                "used_in_scoring",
                "used_in_monte_carlo",
                "recommended_action",
            ],
        ),
        (
            "Official baseline to wartime AML/CFT typology review",
            typology_review,
            [
                "typology_id",
                "typology_name",
                "typology_family",
                "waris_layer_candidates",
                "largest_gap_oblast",
                "largest_gap_value",
                "average_abs_gap",
                "current_use",
                "prohibited_use",
                "production_score_change",
                "used_in_scoring",
                "used_in_monte_carlo",
                "recommended_action",
            ],
        ),
        (
            "Official baseline to FIU/SFMS context review",
            fiu_review,
            [
                "typology_support_id",
                "typology_name",
                "typology_family",
                "waris_layer_candidates",
                "largest_gap_oblast",
                "largest_gap_value",
                "average_abs_gap",
                "current_use",
                "prohibited_use",
                "production_score_change",
                "used_in_scoring",
                "used_in_monte_carlo",
                "recommended_action",
            ],
        ),
        (
            "Official baseline to operational controls review",
            operational_review,
            [
                "operational_artifact_family",
                "artifact_status",
                "artifact_summary",
                "largest_gap_oblast",
                "largest_gap_value",
                "average_abs_gap",
                "current_use",
                "prohibited_use",
                "production_score_change",
                "used_in_scoring",
                "used_in_monte_carlo",
                "recommended_action",
            ],
        ),
    ]

    for title, frame, columns in bridge_pairs:
        if frame is None or frame.empty:
            continue

        story.append(Paragraph(title, styles["Heading3"]))
        _append_how_to_read(story, styles, title)
        story.append(
            _table_from_df(
                frame,
                columns,
                max_rows=12,
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    bridge_snapshot_pairs = [
        ("Official baseline to wartime typology bridge snapshot", typology_bridge),
        ("Official baseline to FIU/SFMS bridge snapshot", fiu_bridge),
        ("Official baseline to Prozorro bridge snapshot", prozorro_bridge),
        ("Official baseline to operational controls bridge snapshot", operational_bridge),
    ]

    for title, frame in bridge_snapshot_pairs:
        if frame is None or frame.empty:
            continue

        story.append(Paragraph(title, styles["Heading3"]))
        _append_how_to_read(story, styles, title)
        story.append(
            _table_from_df(
                frame,
                list(frame.columns[:10]),
                max_rows=10,
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Current interpretation: context bridges are review artifacts. They may "
            "help an analyst compare official baseline scale with source-context "
            "themes and operational safeguards, but they do not convert procurement, "
            "typology, FIU/SFMS, or operational-control context into WARIS scoring features.",
            styles["Small"],
        )
    )


def _build_operational_controls_section(story: list, styles) -> None:
    """Add analyst-review, false-positive, freshness, and manifest appendix."""
    analyst_queue = _load_table("analyst_review_queue.csv")
    analyst_questions = _load_table("analyst_review_questions.csv")
    disposition_template = _load_table("review_disposition_template.csv")
    analyst_summary = _load_table("analyst_review_summary.csv")

    fp_register = _load_table("false_positive_risk_register.csv")
    fp_controls = _load_table("false_positive_controls.csv")
    fp_checklist = _load_table("false_positive_review_checklist.csv")
    fp_summary = _load_table("false_positive_summary.csv")

    freshness_inventory = _load_table("source_freshness_inventory.csv")
    freshness_assessment = _load_table("source_freshness_assessment.csv")
    freshness_priorities = _load_table("source_freshness_replacement_priorities.csv")
    freshness_summary = _load_table("source_freshness_summary.csv")

    run_manifest = _load_table("run_manifest.csv")
    run_manifest_summary = _load_table("run_manifest_summary.csv")

    operational_bridge = _load_table(
        "official_baseline_operational_controls_context_bridge.csv"
    )
    operational_review = _load_table(
        "official_baseline_operational_controls_context_review.csv"
    )

    if all(
        df is None or df.empty
        for df in [
            analyst_queue,
            analyst_questions,
            disposition_template,
            analyst_summary,
            fp_register,
            fp_controls,
            fp_checklist,
            fp_summary,
            freshness_inventory,
            freshness_assessment,
            freshness_priorities,
            freshness_summary,
            run_manifest,
            run_manifest_summary,
            operational_bridge,
            operational_review,
        ]
    ):
        return

    story.append(PageBreak())
    story.append(Paragraph("Operational controls appendix", styles["Heading2"]))
    _append_how_to_read(story, styles, "Operational controls appendix")

    story.append(
        Paragraph(
            "This appendix documents downstream operational-control artifacts. "
            "These tables support analyst review, false-positive handling, source "
            "freshness monitoring, run reproducibility, and official-baseline review "
            "readiness. They do not validate WARIS accuracy, approve scoring use, "
            "or alter risk layers, composite scores, risk bands, review rationales, "
            "or Monte Carlo simulations.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    if analyst_summary is not None and not analyst_summary.empty:
        story.append(Paragraph("Analyst review workflow", styles["Heading3"]))
        _append_how_to_read(story, styles, "Analyst review workflow")
        _append_table(
            story,
            analyst_summary,
            ["summary_area", "status", "value", "recommended_next_action"],
            max_rows=10,
            col_widths=[1.65 * inch, 1.0 * inch, 2.0 * inch, 4.4 * inch],
        )
        story.append(Spacer(1, 0.12 * inch))

    if analyst_queue is not None and not analyst_queue.empty:
        _append_table(
            story,
            analyst_queue,
            [
                "oblast",
                "sector",
                "waris_aml_review_score",
                "risk_band",
                "review_priority",
                "review_reason",
                "human_review_required",
                "automated_adverse_action_allowed",
            ],
            max_rows=12,
            col_widths=[
                0.9 * inch,
                1.4 * inch,
                0.8 * inch,
                0.9 * inch,
                0.95 * inch,
                3.0 * inch,
                0.8 * inch,
                0.8 * inch,
            ],
            max_chars=115,
        )
        story.append(Spacer(1, 0.15 * inch))

    if fp_summary is not None and not fp_summary.empty:
        story.append(Paragraph("False-positive controls", styles["Heading3"]))
        _append_how_to_read(story, styles, "False-positive controls")
        _append_table(
            story,
            fp_summary,
            ["summary_area", "status", "value", "recommended_next_action"],
            max_rows=10,
            col_widths=[1.65 * inch, 1.0 * inch, 2.0 * inch, 4.4 * inch],
        )
        story.append(Spacer(1, 0.12 * inch))

    if fp_controls is not None and not fp_controls.empty:
        _append_table(
            story,
            fp_controls,
            [
                "control_id",
                "control_name",
                "control_type",
                "test_status",
                "control_description",
                "production_score_change",
            ],
            max_rows=12,
            col_widths=[
                0.75 * inch,
                1.7 * inch,
                1.1 * inch,
                0.85 * inch,
                4.0 * inch,
                0.9 * inch,
            ],
            max_chars=130,
        )
        story.append(Spacer(1, 0.15 * inch))

    if freshness_summary is not None and not freshness_summary.empty:
        story.append(PageBreak())
        story.append(Paragraph("Source freshness monitoring", styles["Heading3"]))
        _append_how_to_read(story, styles, "Source freshness monitoring")
        _append_table(
            story,
            freshness_summary,
            ["summary_area", "status", "value", "recommended_next_action"],
            max_rows=12,
            col_widths=[1.65 * inch, 1.0 * inch, 2.2 * inch, 4.2 * inch],
        )
        story.append(Spacer(1, 0.12 * inch))

    if freshness_priorities is not None and not freshness_priorities.empty:
        _append_table(
            story,
            freshness_priorities,
            [
                "priority_rank",
                "source_family",
                "artifact_name",
                "freshness_status",
                "refresh_priority",
                "row_count",
                "age_days",
                "recommended_action",
            ],
            max_rows=15,
            col_widths=[
                0.55 * inch,
                1.2 * inch,
                1.55 * inch,
                0.85 * inch,
                1.2 * inch,
                0.65 * inch,
                0.65 * inch,
                2.6 * inch,
            ],
            max_chars=115,
        )
        story.append(Spacer(1, 0.15 * inch))

    if run_manifest_summary is not None and not run_manifest_summary.empty:
        story.append(PageBreak())
        story.append(Paragraph("Run manifest and reproducibility", styles["Heading3"]))
        _append_how_to_read(story, styles, "Run manifest and reproducibility")
        _append_table(
            story,
            run_manifest_summary,
            [
                "run_id",
                "model_version",
                "production_score_change",
                "scored_rows",
                "monte_carlo_rows",
                "operational_controls_context_review_rows",
                "source_freshness_posture",
                "git_working_tree_status",
            ],
            max_rows=3,
            col_widths=[
                1.4 * inch,
                0.8 * inch,
                0.9 * inch,
                0.75 * inch,
                0.75 * inch,
                1.0 * inch,
                1.4 * inch,
                1.0 * inch,
            ],
            max_chars=90,
        )
        story.append(Spacer(1, 0.12 * inch))

    if run_manifest is not None and not run_manifest.empty:
        _append_table(
            story,
            run_manifest,
            [
                "artifact_group",
                "artifact_name",
                "artifact_type",
                "exists",
                "row_count",
                "current_use",
                "used_in_waris_scoring",
                "used_in_monte_carlo",
                "production_score_change",
            ],
            max_rows=18,
            col_widths=[
                1.05 * inch,
                1.65 * inch,
                0.7 * inch,
                0.55 * inch,
                0.55 * inch,
                1.5 * inch,
                0.75 * inch,
                0.75 * inch,
                0.8 * inch,
            ],
            max_chars=105,
        )
        story.append(Spacer(1, 0.15 * inch))

    if operational_review is not None and not operational_review.empty:
        story.append(PageBreak())
        story.append(
            Paragraph(
                "Official baseline to operational controls review",
                styles["Heading3"],
            )
        )
        _append_how_to_read(
            story,
            styles,
            "Official baseline to operational controls review",
        )
        _append_table(
            story,
            operational_review,
            [
                "operational_artifact_family",
                "artifact_status",
                "artifact_summary",
                "current_use",
                "prohibited_use",
                "production_score_change",
                "used_in_scoring",
                "used_in_monte_carlo",
                "recommended_action",
            ],
            max_rows=12,
            col_widths=[
                1.25 * inch,
                0.95 * inch,
                2.2 * inch,
                1.1 * inch,
                1.3 * inch,
                0.75 * inch,
                0.6 * inch,
                0.6 * inch,
                1.6 * inch,
            ],
            max_chars=105,
        )
        story.append(Spacer(1, 0.15 * inch))

    if operational_bridge is not None and not operational_bridge.empty:
        _append_table(
            story,
            operational_bridge,
            list(operational_bridge.columns[:10]),
            max_rows=10,
            max_chars=115,
        )
        story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Current interpretation: operational controls are documentation and "
            "human-review support. They make the project safer and more auditable, "
            "but they do not make WARIS operationally validated and do not authorize "
            "automated adverse action or entity-level findings.",
            styles["Small"],
        )
    )


def _build_official_indicator_section(story: list, styles) -> None:
    """Add NBU/Ukrstat official indicator alignment summary to the report."""
    catalog = _load_table("official_indicator_catalog.csv")

    if catalog is None or catalog.empty:
        return

    story.append(PageBreak())
    story.append(
        Paragraph("Official NBU / Ukrstat indicator alignment", styles["Heading2"])
    )
    _append_how_to_read(story, styles, 'Official NBU / Ukrstat indicator alignment')

    story.append(
        Paragraph(
            "This section summarizes candidate official NBU and Ukrstat indicators "
            "that may support future replacement of synthetic WARIS assumptions. "
            "The catalog does not yet claim that these indicators are fully integrated "
            "into scoring. It identifies candidate mappings for analyst review and "
            "future source validation.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.08 * inch))

    if "waris_layer_candidate" in catalog.columns:
        layer_summary = (
            catalog.groupby("waris_layer_candidate", as_index=False)
            .agg(candidate_indicator_count=("indicator_id", "count"))
            .sort_values("candidate_indicator_count", ascending=False)
        )

        story.append(
            Paragraph("Candidate indicators by WARIS layer", styles["Heading3"])
        )
        _append_how_to_read(story, styles, 'Candidate indicators by WARIS layer')
        story.append(
            _table_from_df(
                layer_summary,
                ["waris_layer_candidate", "candidate_indicator_count"],
                max_rows=12,
                col_widths=[3.2 * inch, 1.6 * inch],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    priority_layers = [
        "official_regional_baseline",
        "revenue_anomaly_risk",
        "financial_supervision_exposure",
        "procurement_integrity_risk",
        "tbml_risk",
    ]

    if "waris_layer_candidate" in catalog.columns:
        priority_catalog = catalog[
            catalog["waris_layer_candidate"].isin(priority_layers)
        ].copy()
    else:
        priority_catalog = catalog.copy()

    if priority_catalog.empty:
        priority_catalog = catalog.copy()

    priority_catalog["_priority_order"] = priority_catalog.get(
        "waris_layer_candidate",
        pd.Series(["general_context"] * len(priority_catalog)),
    ).map({layer: idx for idx, layer in enumerate(priority_layers)}).fillna(99)

    priority_catalog = priority_catalog.sort_values(
        ["_priority_order", "source_family", "indicator_id"],
        ascending=[True, True, True],
    )

    story.append(Paragraph("Selected candidate official indicators", styles["Heading3"]))
    _append_how_to_read(story, styles, 'Selected candidate official indicators')
    story.append(
        _table_from_df(
            priority_catalog,
            [
                "source_family",
                "indicator_id",
                "indicator_name",
                "waris_layer_candidate",
                "keyword_hits",
                "implementation_status",
            ],
            max_rows=14,
            col_widths=[
                1.0 * inch,
                1.75 * inch,
                3.0 * inch,
                1.45 * inch,
                1.25 * inch,
                1.35 * inch,
            ],
        )
    )


def _build_model_governance_section(story: list, styles) -> None:
    """Add model governance and validation appendix from generated governance tables."""
    inventory = _load_table("model_inventory.csv")
    limitations = _load_table("model_limitations_register.csv")
    validation = _load_table("model_validation_checklist.csv")
    monitoring = _load_table("model_monitoring_plan.csv")
    summary = _load_table("model_governance_summary.csv")

    if all(
        df is None or df.empty
        for df in [inventory, limitations, validation, monitoring, summary]
    ):
        return

    story.append(PageBreak())
    story.append(Paragraph("Model governance and validation appendix", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Model governance and validation appendix')

    story.append(
        Paragraph(
            "This appendix documents WARIS model-risk controls inspired by supervisory "
            "model risk management principles. These artifacts support transparency, "
            "documentation, intended-use control, limitation tracking, validation planning, "
            "and ongoing monitoring. They do not make WARIS operationally validated.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    if inventory is not None and not inventory.empty:
        story.append(Paragraph("Model inventory", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Model inventory')
        story.append(
            _table_from_df(
                inventory,
                [
                    "model_short_name",
                    "model_version",
                    "model_status",
                    "output_granularity",
                    "model_risk_rating",
                    "materiality_assessment",
                    "prohibited_use",
                ],
                max_rows=1,
                col_widths=[
                    0.75 * inch,
                    0.75 * inch,
                    1.0 * inch,
                    1.15 * inch,
                    1.2 * inch,
                    2.35 * inch,
                    2.5 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if summary is not None and not summary.empty:
        story.append(Paragraph("Governance summary", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Governance summary')
        story.append(
            _table_from_df(
                summary,
                ["governance_area", "status", "summary"],
                max_rows=8,
                col_widths=[1.8 * inch, 1.35 * inch, 6.0 * inch],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if validation is not None and not validation.empty:
        story.append(Paragraph("Validation checklist", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Validation checklist')
        story.append(
            _table_from_df(
                validation,
                [
                    "validation_area",
                    "current_status",
                    "evidence",
                    "next_action",
                ],
                max_rows=10,
                col_widths=[1.7 * inch, 1.25 * inch, 2.6 * inch, 3.4 * inch],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if limitations is not None and not limitations.empty:
        story.append(PageBreak())
        story.append(Paragraph("Model limitations register", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Model limitations register')
        story.append(
            _table_from_df(
                limitations,
                [
                    "limitation_category",
                    "limitation",
                    "potential_impact",
                    "mitigation",
                    "status",
                ],
                max_rows=10,
                col_widths=[
                    1.4 * inch,
                    2.2 * inch,
                    2.0 * inch,
                    2.65 * inch,
                    0.9 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if monitoring is not None and not monitoring.empty:
        story.append(Paragraph("Ongoing monitoring plan", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Ongoing monitoring plan')
        story.append(
            _table_from_df(
                monitoring,
                [
                    "monitoring_item",
                    "monitoring_metric",
                    "frequency",
                    "threshold_or_trigger",
                    "response",
                ],
                max_rows=8,
                col_widths=[
                    1.45 * inch,
                    2.0 * inch,
                    1.0 * inch,
                    2.2 * inch,
                    2.5 * inch,
                ],
            )
        )


def _build_source_confidence_section(story: list, styles) -> None:
    """Add source confidence and field lineage appendix from generated tables."""
    field_register = _load_table("field_source_register.csv")
    confidence_assessment = _load_table("source_confidence_assessment.csv")
    confidence_summary = _load_table("source_confidence_summary.csv")

    if all(
        df is None or df.empty
        for df in [field_register, confidence_assessment, confidence_summary]
    ):
        return

    story.append(PageBreak())
    story.append(
        Paragraph("Source confidence and field lineage appendix", styles["Heading2"])
    )
    _append_how_to_read(story, styles, 'Source confidence and field lineage appendix')

    story.append(
        Paragraph(
            "This appendix documents field-level source lineage, source type, "
            "qualitative confidence, and replacement priority. These ratings are "
            "designed to make WARIS more transparent and easier to validate. They "
            "do not certify data quality and should be reviewed by subject-matter "
            "experts before any operational use.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    if confidence_summary is not None and not confidence_summary.empty:
        story.append(Paragraph("Source confidence summary", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Source confidence summary')
        story.append(
            _table_from_df(
                confidence_summary,
                ["summary_area", "status", "summary"],
                max_rows=12,
                col_widths=[
                    1.8 * inch,
                    1.15 * inch,
                    6.2 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if field_register is not None and not field_register.empty:
        if "replacement_priority" in field_register.columns:
            high_priority = field_register[
                field_register["replacement_priority"] == "High"
            ].copy()
        else:
            high_priority = pd.DataFrame()

        if not high_priority.empty:
            story.append(
                Paragraph("High-priority field replacements", styles["Heading3"])
            )
            _append_how_to_read(story, styles, 'High-priority field replacements')
            story.append(
                _table_from_df(
                    high_priority,
                    [
                        "field_name",
                        "model_area",
                        "current_source_type",
                        "confidence_level",
                        "live_or_official_candidate",
                        "confidence_rationale",
                    ],
                    max_rows=10,
                    col_widths=[
                        1.45 * inch,
                        1.35 * inch,
                        1.55 * inch,
                        0.85 * inch,
                        2.2 * inch,
                        1.95 * inch,
                    ],
                )
            )
            story.append(Spacer(1, 0.15 * inch))

    if confidence_assessment is not None and not confidence_assessment.empty:
        story.append(
            Paragraph("Source confidence assessment by model area", styles["Heading3"])
        )
        _append_how_to_read(story, styles, 'Source confidence assessment by model area')
        story.append(
            _table_from_df(
                confidence_assessment,
                [
                    "model_area",
                    "current_source_type",
                    "field_count",
                    "confidence_interpretation",
                    "replacement_priority_interpretation",
                ],
                max_rows=12,
                col_widths=[
                    1.55 * inch,
                    2.1 * inch,
                    0.8 * inch,
                    1.6 * inch,
                    2.1 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if field_register is not None and not field_register.empty:
        story.append(PageBreak())
        story.append(Paragraph("Field source register", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Field source register')
        story.append(
            _table_from_df(
                field_register,
                [
                    "field_name",
                    "model_area",
                    "current_source_type",
                    "confidence_level",
                    "replacement_priority",
                    "notes",
                ],
                max_rows=16,
                col_widths=[
                    1.55 * inch,
                    1.35 * inch,
                    2.0 * inch,
                    0.9 * inch,
                    0.95 * inch,
                    2.4 * inch,
                ],
            )
        )



def _build_official_baseline_validation_section(story: list, styles) -> None:
    """Add official baseline validation gate appendix."""
    validation_register = _load_table("official_baseline_validation_register.csv")
    validation_summary = _load_table("official_baseline_validation_summary.csv")
    geography_check = _load_table("official_baseline_geography_crosswalk_check.csv")
    period_coverage = _load_table("official_baseline_period_coverage.csv")
    readiness_decision = _load_table("official_baseline_readiness_decision.csv")
    unit_evidence_summary = _load_table("official_baseline_unit_evidence_summary.csv")
    unit_evidence = _load_table("official_baseline_unit_evidence.csv")

    if all(
        df is None or df.empty
        for df in [
            validation_register,
            validation_summary,
            geography_check,
            period_coverage,
            readiness_decision,
            unit_evidence_summary,
            unit_evidence,
        ]
    ):
        return

    story.append(PageBreak())
    story.append(
        Paragraph("Official baseline validation gate appendix", styles["Heading2"])
    )
    _append_how_to_read(story, styles, 'Official baseline validation gate appendix')

    story.append(
        Paragraph(
            "This appendix documents the staged validation gate for official Ukrstat "
            "GRP oblast baseline candidates. The validation module confirms candidate "
            "coverage, geography mapping, period coverage, unit/scale evidence, endpoint "
            "evidence, parser evidence, scoring gate status, and remaining validation "
            "blockers. The current approved use is controlled benchmark integration "
            "only. These artifacts do not approve official values for risk-layer "
            "calculation or composite scoring.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    if readiness_decision is not None and not readiness_decision.empty:
        story.append(Paragraph("Readiness decision", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Readiness decision')
        story.append(
            _table_from_df(
                readiness_decision,
                [
                    "decision_area",
                    "decision",
                    "blocking_item_count",
                    "high_or_critical_blocking_item_count",
                    "approved_current_use",
                    "prohibited_current_use",
                    "next_decision_point",
                ],
                max_rows=3,
                col_widths=[
                    1.65 * inch,
                    0.75 * inch,
                    0.8 * inch,
                    1.15 * inch,
                    1.65 * inch,
                    1.8 * inch,
                    2.3 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

        if "rationale" in readiness_decision.columns:
            rationale = str(readiness_decision.iloc[0].get("rationale", ""))
            if rationale:
                story.append(
                    Paragraph(
                        f"<b>Decision rationale:</b> {rationale}",
                        styles["Small"],
                    )
                )
                story.append(Spacer(1, 0.1 * inch))

    if unit_evidence_summary is not None and not unit_evidence_summary.empty:
        story.append(Paragraph("Official unit and scale evidence", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Official unit and scale evidence')
        story.append(
            _table_from_df(
                unit_evidence_summary,
                [
                    "source_file",
                    "source_export_format",
                    "indicator_code",
                    "indicator_name",
                    "nace_code",
                    "nace_name",
                    "freq_code",
                    "freq_name",
                    "unit_name",
                    "scaling_name",
                    "period_min",
                    "period_max",
                    "unit_interpretation",
                    "validation_status",
                ],
                max_rows=4,
                col_widths=[
                    1.5 * inch,
                    0.95 * inch,
                    0.65 * inch,
                    1.4 * inch,
                    0.55 * inch,
                    1.05 * inch,
                    0.55 * inch,
                    0.8 * inch,
                    0.7 * inch,
                    0.8 * inch,
                    0.65 * inch,
                    0.65 * inch,
                    1.0 * inch,
                    1.65 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if unit_evidence is not None and not unit_evidence.empty:
        story.append(Paragraph("Unit evidence sample rows", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Unit evidence sample rows')

        # Dataset Explorer exports can be saved in long or wide format.
        # Long format has Indicator, Time period, and Observation value columns.
        # Wide format may use year columns. Select existing columns dynamically
        # so PDF generation never fails on a valid but differently-shaped export.
        preferred_unit_evidence_cols = [
            "Indicator",
            "Indicator.1",
            "Region",
            "Region.1",
            "waris_oblast",
            "Economic activity type",
            "Economic activity type.1",
            "Frequency",
            "Frequency.1",
            "Time period",
            "Observation value",
            "Unit of measure",
            "Unit of measure.1",
            "Scaling",
            "Scaling.1",
            "Decimals displayed",
            "Decimals displayed.1",
        ]

        available_unit_evidence_cols = [
            col for col in preferred_unit_evidence_cols if col in unit_evidence.columns
        ]

        if not available_unit_evidence_cols:
            available_unit_evidence_cols = list(unit_evidence.columns[:10])

        if available_unit_evidence_cols:
            dynamic_width = max(
                0.65 * inch,
                min(1.15 * inch, 9.2 * inch / len(available_unit_evidence_cols)),
            )

            story.append(
                _table_from_df(
                    unit_evidence,
                    available_unit_evidence_cols,
                    max_rows=8,
                    col_widths=[dynamic_width for _ in available_unit_evidence_cols],
                )
            )
        else:
            story.append(
                Paragraph(
                    "Unit evidence artifact was present, but no displayable columns "
                    "were found. Review official_baseline_unit_evidence.csv directly.",
                    styles["Small"],
                )
            )

        story.append(Spacer(1, 0.15 * inch))

    if validation_summary is not None and not validation_summary.empty:
        story.append(Paragraph("Validation summary", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Validation summary')
        story.append(
            _table_from_df(
                validation_summary,
                [
                    "summary_area",
                    "status",
                    "value",
                    "recommended_next_action",
                ],
                max_rows=10,
                col_widths=[
                    1.7 * inch,
                    1.35 * inch,
                    2.45 * inch,
                    3.65 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if validation_register is not None and not validation_register.empty:
        story.append(Paragraph("Validation check register", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Validation check register')

        register_display = validation_register.copy()

        # Prioritize review-required and high-severity rows while still showing
        # enough passed controls to document the gate.
        if {"status", "severity"}.issubset(register_display.columns):
            severity_order = {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "info": 3,
            }
            status_order = {
                "review_required": 0,
                "partial": 1,
                "pass": 2,
            }
            register_display["_severity_order"] = (
                register_display["severity"]
                .fillna("")
                .astype(str)
                .map(severity_order)
                .fillna(9)
            )
            register_display["_status_order"] = (
                register_display["status"]
                .fillna("")
                .astype(str)
                .map(status_order)
                .fillna(9)
            )
            register_display = register_display.sort_values(
                ["_status_order", "_severity_order", "check_id"],
                ascending=[True, True, True],
            ).drop(columns=["_severity_order", "_status_order"])

        story.append(
            _table_from_df(
                register_display,
                [
                    "check_id",
                    "validation_area",
                    "status",
                    "severity",
                    "result_value",
                    "expected_value",
                    "recommended_next_action",
                ],
                max_rows=13,
                col_widths=[
                    0.7 * inch,
                    1.4 * inch,
                    0.95 * inch,
                    0.75 * inch,
                    1.7 * inch,
                    1.8 * inch,
                    2.65 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if geography_check is not None and not geography_check.empty:
        story.append(PageBreak())
        story.append(Paragraph("Geography crosswalk validation", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Geography crosswalk validation')
        story.append(
            Paragraph(
                "This table checks whether official Ukrstat oblast labels and region "
                "codes map cleanly into the canonical WARIS geography list. This is "
                "a prerequisite for any future official baseline integration.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))

        story.append(
            _table_from_df(
                geography_check,
                [
                    "waris_oblast",
                    "ukrstat_oblast",
                    "region_code",
                    "mapping_status",
                    "coverage_status",
                    "notes",
                ],
                max_rows=25,
                col_widths=[
                    1.2 * inch,
                    1.35 * inch,
                    1.85 * inch,
                    1.45 * inch,
                    1.25 * inch,
                    2.05 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if period_coverage is not None and not period_coverage.empty:
        story.append(Paragraph("Period coverage validation", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Period coverage validation')
        story.append(
            _table_from_df(
                period_coverage,
                [
                    "latest_period",
                    "candidate_count",
                    "period_parseable_count",
                    "period_coverage_status",
                    "current_use_in_scoring",
                    "notes",
                ],
                max_rows=6,
                col_widths=[
                    1.0 * inch,
                    1.0 * inch,
                    1.2 * inch,
                    1.9 * inch,
                    1.4 * inch,
                    2.65 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Current interpretation: the official baseline validation gate now allows "
            "controlled benchmark integration. Official GRP candidates may be compared "
            "against WARIS synthetic baselines in controlled benchmark artifacts, but "
            "they remain prohibited from risk-layer calculation, composite scoring, "
            "risk-band assignment, or Monte Carlo score simulation until transformation "
            "logic, SME review, and scoring change control are complete.",
            styles["Small"],
        )
    )



def _build_official_baseline_merge_plan_section(story: list, styles) -> None:
    """Add official baseline controlled merge-planning appendix."""
    merge_plan = _load_table("official_baseline_merge_plan.csv")
    benchmark = _load_table("official_baseline_benchmark_comparison.csv")
    rescale = _load_table("official_baseline_rescale_scenario.csv")
    replace = _load_table("official_baseline_replace_oblast_baseline_scenario.csv")
    readiness = _load_table("official_baseline_merge_readiness_summary.csv")

    if all(
        df is None or df.empty
        for df in [merge_plan, benchmark, rescale, replace, readiness]
    ):
        return

    story.append(PageBreak())
    story.append(
        Paragraph(
            "Official baseline controlled benchmark-integration appendix",
            styles["Heading2"],
        )
    )
    _append_how_to_read(story, styles, 'Official baseline controlled benchmark-integration appendix')

    story.append(
        Paragraph(
            "This appendix documents controlled non-production merge-planning "
            "artifacts for official Ukrstat GRP oblast baseline candidates. The "
            "current readiness posture is GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION. "
            "These artifacts are approved for benchmark integration only. They do "
            "not alter WARIS risk layers, composite scores, risk bands, review "
            "rationales, or Monte Carlo score simulations.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    if readiness is not None and not readiness.empty:
        story.append(Paragraph("Merge-readiness summary", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Merge-readiness summary')
        story.append(
            _table_from_df(
                readiness,
                ["summary_area", "status", "summary"],
                max_rows=8,
                col_widths=[1.75 * inch, 1.75 * inch, 5.65 * inch],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if merge_plan is not None and not merge_plan.empty:
        story.append(Paragraph("Controlled merge-plan scenarios", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Controlled merge-plan scenarios')
        story.append(
            _table_from_df(
                merge_plan,
                [
                    "scenario_name",
                    "approved_now",
                    "approved_current_use",
                    "prohibited_current_use",
                    "production_score_change",
                    "required_before_scoring",
                    "notes",
                ],
                max_rows=5,
                col_widths=[
                    1.35 * inch,
                    0.75 * inch,
                    1.45 * inch,
                    1.55 * inch,
                    1.05 * inch,
                    2.0 * inch,
                    2.0 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if benchmark is not None and not benchmark.empty:
        story.append(Paragraph("Benchmark-only comparison", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Benchmark-only comparison')
        story.append(
            Paragraph(
                "This table compares official GRP scale against the current WARIS "
                "synthetic prewar revenue baseline. It is a benchmark artifact only.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))

        benchmark_display = benchmark.copy()
        if "official_vs_synthetic_index_gap" in benchmark_display.columns:
            benchmark_display["abs_gap"] = pd.to_numeric(
                benchmark_display["official_vs_synthetic_index_gap"],
                errors="coerce",
            ).abs()
            benchmark_display = benchmark_display.sort_values(
                "abs_gap",
                ascending=False,
            )

        story.append(
            _table_from_df(
                benchmark_display,
                [
                    "waris_oblast",
                    "official_grp_million_uah",
                    "official_grp_share_of_waris_total",
                    "synthetic_prewar_share_of_total",
                    "official_to_synthetic_share_ratio",
                    "official_vs_synthetic_index_gap",
                    "benchmark_status",
                    "current_use_in_scoring",
                ],
                max_rows=15,
                col_widths=[
                    1.1 * inch,
                    1.15 * inch,
                    1.25 * inch,
                    1.25 * inch,
                    1.25 * inch,
                    1.25 * inch,
                    1.35 * inch,
                    1.1 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if rescale is not None and not rescale.empty:
        story.append(PageBreak())
        story.append(Paragraph("Rescale revenue baseline scenario", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Rescale revenue baseline scenario')
        story.append(
            Paragraph(
                "This non-production scenario uses official GRP distribution to "
                "rescale the synthetic prewar revenue baseline while preserving "
                "sector-level prototype variation. It is not a scoring input.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))

        story.append(
            _table_from_df(
                rescale,
                [
                    "oblast",
                    "sector",
                    "official_grp_million_uah",
                    "official_oblast_scale_index",
                    "prewar_revenue_index_2021",
                    "scenario_prewar_revenue_index_2021",
                    "scenario_status",
                    "current_use_in_scoring",
                ],
                max_rows=15,
                col_widths=[
                    1.0 * inch,
                    1.65 * inch,
                    1.15 * inch,
                    1.05 * inch,
                    1.05 * inch,
                    1.25 * inch,
                    1.5 * inch,
                    1.0 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if replace is not None and not replace.empty:
        story.append(Paragraph("Replace-oblast-baseline scenario", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Replace-oblast-baseline scenario')
        story.append(
            Paragraph(
                "This non-production scenario replaces the oblast-level baseline "
                "with official GRP million UAH in a benchmark table. It cannot "
                "allocate across WARIS sectors without additional validated official "
                "sector-by-oblast data or approved allocation logic.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))

        story.append(
            _table_from_df(
                replace,
                [
                    "waris_oblast",
                    "latest_period",
                    "scenario_oblast_baseline_value",
                    "scenario_oblast_baseline_unit",
                    "official_grp_share_of_waris_total",
                    "sector_allocation_status",
                    "scenario_status",
                    "current_use_in_scoring",
                ],
                max_rows=15,
                col_widths=[
                    1.1 * inch,
                    0.9 * inch,
                    1.3 * inch,
                    1.0 * inch,
                    1.25 * inch,
                    2.0 * inch,
                    1.55 * inch,
                    1.0 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Current interpretation: the official baseline merge-plan permits "
            "controlled benchmark integration only. The benchmark, rescale, and "
            "replace-oblast-baseline scenarios are review artifacts. They must not "
            "be used to alter production WARIS scores until transformation logic, "
            "SME review, and scoring change-control approval are complete.",
            styles["Small"],
        )
    )



def _build_official_baseline_merge_review_section(story: list, styles) -> None:
    """Add official baseline controlled merge-review appendix."""
    gap_review = _load_table("official_baseline_gap_review.csv")
    scenario_recommendations = _load_table("official_baseline_scenario_recommendations.csv")
    review_summary = _load_table("official_baseline_merge_review_summary.csv")
    prozorro_context_review = _load_table("official_baseline_prozorro_context_review.csv")
    typology_context_review = _load_table(
        "official_baseline_wartime_typology_context_review.csv"
    )
    fiu_context_review = _load_table("official_baseline_fiu_context_review.csv")

    if all(
        df is None or df.empty
        for df in [
            gap_review,
            scenario_recommendations,
            review_summary,
            prozorro_context_review,
            typology_context_review,
            fiu_context_review,
        ]
    ):
        return

    story.append(PageBreak())
    story.append(
        Paragraph(
            "Official baseline controlled merge-review appendix",
            styles["Heading2"],
        )
    )
    _append_how_to_read(story, styles, 'Official baseline controlled merge-review appendix')

    story.append(
        Paragraph(
            "This appendix reviews controlled benchmark-integration outputs created "
            "from official Ukrstat GRP oblast baseline candidates. It summarizes "
            "official-vs-synthetic baseline gaps, scenario recommendations, and the "
            "current benchmark_only posture. These review artifacts do not alter "
            "WARIS risk layers, composite scores, risk bands, review rationales, or "
            "Monte Carlo score simulations.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    if review_summary is not None and not review_summary.empty:
        story.append(Paragraph("Merge-review summary", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Merge-review summary')
        story.append(
            _table_from_df(
                review_summary,
                [
                    "summary_area",
                    "status",
                    "summary",
                    "recommended_next_action",
                ],
                max_rows=8,
                col_widths=[
                    1.55 * inch,
                    1.35 * inch,
                    4.05 * inch,
                    2.2 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if scenario_recommendations is not None and not scenario_recommendations.empty:
        story.append(Paragraph("Scenario recommendations", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Scenario recommendations')
        story.append(
            _table_from_df(
                scenario_recommendations,
                [
                    "scenario_name",
                    "current_recommendation",
                    "rationale",
                    "evidence",
                    "approved_current_use",
                    "prohibited_current_use",
                    "production_score_change",
                    "required_before_scoring",
                ],
                max_rows=5,
                col_widths=[
                    1.25 * inch,
                    1.35 * inch,
                    2.0 * inch,
                    1.7 * inch,
                    1.2 * inch,
                    1.35 * inch,
                    0.95 * inch,
                    1.7 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if gap_review is not None and not gap_review.empty:
        story.append(PageBreak())
        story.append(Paragraph("Official-vs-synthetic gap review", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Official-vs-synthetic gap review')
        story.append(
            Paragraph(
                "This table ranks oblasts by the absolute gap between official GRP "
                "scale and the current WARIS synthetic prewar revenue baseline. It is "
                "a benchmark-review artifact only and is not a scoring input.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))

        gap_display = gap_review.copy()

        if "absolute_index_gap" in gap_display.columns:
            gap_display["absolute_index_gap"] = pd.to_numeric(
                gap_display["absolute_index_gap"],
                errors="coerce",
            )
            gap_display = gap_display.sort_values(
                "absolute_index_gap",
                ascending=False,
            )

        story.append(Paragraph("Quantitative gap review", styles["Heading4"]))
        story.append(
            _table_from_df(
                gap_display,
                [
                    "waris_oblast",
                    "official_grp_million_uah",
                    "official_grp_share_of_waris_total",
                    "synthetic_prewar_share_of_total",
                    "official_vs_synthetic_index_gap",
                    "absolute_index_gap",
                    "official_to_synthetic_share_ratio",
                    "gap_band",
                ],
                max_rows=20,
                col_widths=[
                    1.05 * inch,
                    1.2 * inch,
                    1.3 * inch,
                    1.3 * inch,
                    1.35 * inch,
                    1.1 * inch,
                    1.35 * inch,
                    1.05 * inch,
                ],
                max_chars=120,
            )
        )
        story.append(Spacer(1, 0.12 * inch))

        story.append(Paragraph("Governance action review", styles["Heading4"]))
        story.append(
            _table_from_df(
                gap_display,
                [
                    "waris_oblast",
                    "gap_band",
                    "ratio_band",
                    "recommended_action",
                    "production_score_change",
                ],
                max_rows=20,
                col_widths=[
                    1.15 * inch,
                    1.2 * inch,
                    1.25 * inch,
                    4.7 * inch,
                    1.6 * inch,
                ],
                max_chars=260,
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if typology_context_review is not None and not typology_context_review.empty:
        story.append(PageBreak())
        story.append(
            Paragraph("Wartime typology context review snapshot", styles["Heading3"])
        )
        _append_how_to_read(story, styles, 'Wartime typology context review snapshot')
        story.append(
            _table_from_df(
                typology_context_review,
                [
                    "typology_id",
                    "typology_name",
                    "typology_family",
                    "waris_layer_candidates",
                    "largest_gap_oblast",
                    "largest_gap_value",
                    "current_use",
                    "recommended_action",
                ],
                max_rows=10,
                col_widths=[
                    0.7 * inch,
                    1.55 * inch,
                    1.15 * inch,
                    1.45 * inch,
                    1.05 * inch,
                    0.95 * inch,
                    1.25 * inch,
                    1.8 * inch,
                ],
                max_chars=170,
            )
        )
        story.append(
            _table_from_df(
                typology_context_review,
                [
                    "typology_id",
                    "production_score_change",
                    "used_in_scoring",
                    "used_in_monte_carlo",
                ],
                max_rows=10,
                col_widths=[0.9 * inch, 2.0 * inch, 1.5 * inch, 1.5 * inch],
                max_chars=140,
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if fiu_context_review is not None and not fiu_context_review.empty:
        story.append(Paragraph("FIU/SFMS context review snapshot", styles["Heading3"]))
        _append_how_to_read(story, styles, 'FIU/SFMS context review snapshot')
        story.append(
            _table_from_df(
                fiu_context_review,
                [
                    "typology_support_id",
                    "typology_name",
                    "typology_family",
                    "waris_layer_candidates",
                    "largest_gap_oblast",
                    "largest_gap_value",
                    "current_use",
                    "recommended_action",
                ],
                max_rows=10,
                col_widths=[
                    0.9 * inch,
                    1.45 * inch,
                    1.15 * inch,
                    1.45 * inch,
                    1.05 * inch,
                    0.95 * inch,
                    1.25 * inch,
                    1.7 * inch,
                ],
                max_chars=170,
            )
        )
        story.append(
            _table_from_df(
                fiu_context_review,
                [
                    "typology_support_id",
                    "production_score_change",
                    "used_in_scoring",
                    "used_in_monte_carlo",
                ],
                max_rows=10,
                col_widths=[1.1 * inch, 2.0 * inch, 1.5 * inch, 1.5 * inch],
                max_chars=140,
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Current interpretation: the merge-review layer recommends benchmark_only "
            "as the current posture. Rescale remains available for sensitivity review, "
            "and replace-oblast-baseline is not recommended for scoring until sector "
            "allocation logic, SME review, transformation logic, and scoring "
            "change-control approval are complete. Context-review artifacts for "
            "Prozorro, wartime AML/CFT typology, and FIU/SFMS remain review-only "
            "source-support artifacts.",
            styles["Small"],
        )
    )



def _build_official_baseline_review_memo_section(story: list, styles) -> None:
    """Add official baseline benchmark review memo appendix."""
    memo_text = _load_report_text("official_baseline_benchmark_review_memo.md")

    if memo_text is None:
        return

    story.append(PageBreak())
    story.append(
        Paragraph(
            "Official baseline benchmark review memo",
            styles["Heading2"],
        )
    )
    _append_how_to_read(story, styles, 'Official baseline benchmark review memo')

    story.append(
        Paragraph(
            "This appendix summarizes the plain-language benchmark review memo. "
            "The memo explains the official baseline validation, merge-planning, "
            "merge-review findings, and why the current posture remains "
            "benchmark_only. It is a review artifact only and does not alter WARIS "
            "risk layers, composite scores, risk bands, review rationales, or Monte "
            "Carlo simulations.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    selected_sections = _extract_memo_sections(
        memo_text,
        [
            "Executive summary",
            "Control assessment",
            "Benchmark gap findings",
            "Scenario recommendations",
            "Official baseline to wartime AML/CFT typology context review",
            "Official baseline to FIU/SFMS context review",
            "Why official GRP, expanded Prozorro, wartime typology, and FIU/SFMS context are not scoring-ready",
            "Why official GRP is not scoring-ready",
            "Current recommendation",
            "Recommended next actions",
            "Governance note",
        ],
        max_chars_per_section=1800,
    )

    for heading, section_text in selected_sections.items():
        if not section_text:
            continue

        story.append(Paragraph(heading, styles["Heading3"]))
        _append_how_to_read(story, styles, heading)
        _markdown_section_to_paragraphs(
            story,
            styles,
            section_text,
            max_lines=18,
        )
        story.append(Spacer(1, 0.12 * inch))

    story.append(
        Paragraph(
            "Full memo artifact: outputs/reports/"
            "official_baseline_benchmark_review_memo.md",
            styles["Small"],
        )
    )


def _build_ukrstat_baseline_transition_section(story: list, styles) -> None:
    """Add Ukrstat regional accounts transition appendix."""
    discovery = _load_raw_table("ukrstat_regional_accounts_discovery_raw.csv")
    baseline = _load_table("ukrstat_oblast_baseline.csv")
    metadata_clues = _load_table("ukrstat_regional_accounts_metadata_clues.csv")
    registry_references = _load_table("ukrstat_registry_references.csv")
    endpoint_probe = _load_table("ukrstat_endpoint_probe_results.csv")
    query_plan = _load_table("ukrstat_observation_query_plan.csv")

    availability_values = _load_table("ukrstat_availability_value_candidates.csv")
    confirmed_series_probe = _load_table("ukrstat_confirmed_series_probe_results.csv")
    confirmed_series_parsed = _load_table("ukrstat_confirmed_series_parsed.csv")
    confirmed_single_baseline = _load_table(
        "ukrstat_confirmed_oblast_baseline_candidates.csv"
    )
    all_oblast_probe = _load_table("ukrstat_oblast_baseline_probe_results.csv")
    all_oblast_candidates = _load_table("ukrstat_oblast_baseline_candidates.csv")

    if all(
        df is None or df.empty
        for df in [
            discovery,
            baseline,
            metadata_clues,
            registry_references,
            endpoint_probe,
            query_plan,
            availability_values,
            confirmed_series_probe,
            confirmed_series_parsed,
            confirmed_single_baseline,
            all_oblast_probe,
            all_oblast_candidates,
        ]
    ):
        return

    story.append(PageBreak())
    story.append(
        Paragraph("Ukrstat official baseline transition appendix", styles["Heading2"])
    )
    _append_how_to_read(story, styles, 'Ukrstat official baseline transition appendix')

    story.append(
        Paragraph(
            "This appendix documents WARIS's transition from metadata-only official "
            "indicator mapping toward official Ukrstat regional baseline observations. "
            "The current version has moved beyond metadata discovery: it confirms the "
            "DF_REGIONAL_ACCOUNTS dataflow, parses DSD/codelist candidates, uses "
            "SDMX availability to identify valid values, pulls confirmed GRP regional "
            "account series, and creates validation-only official oblast baseline "
            "candidate artifacts. These official values remain blocked from scoring "
            "until unit, geography, NACE, indicator meaning, and period coverage are "
            "validated. This is a controlled transition step, not a completed scoring "
            "replacement.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    # Executive status roll-up for the official baseline transition.
    status_rows = []

    if discovery is not None and not discovery.empty:
        discovered = int(
            discovery.get("id", pd.Series(dtype=str))
            .fillna("")
            .astype(str)
            .eq("DF_REGIONAL_ACCOUNTS")
            .sum()
        )
        status_rows.append(
            {
                "artifact": "DF_REGIONAL_ACCOUNTS discovery",
                "status": "complete" if discovered > 0 else "review_required",
                "count": discovered,
                "interpretation": "Official regional accounts dataflow identified.",
            }
        )

    if availability_values is not None and not availability_values.empty:
        candidate_count = len(availability_values)
        status_rows.append(
            {
                "artifact": "Availability-derived value candidates",
                "status": "parsed_pending_validation",
                "count": candidate_count,
                "interpretation": (
                    "SDMX availability values parsed for analyst review, including "
                    "NACE, frequency, and time-period boundaries."
                ),
            }
        )

    if confirmed_series_probe is not None and not confirmed_series_probe.empty:
        successful = 0
        has_observations = 0

        if "success_status" in confirmed_series_probe.columns:
            successful = int(
                confirmed_series_probe["success_status"]
                .astype(str)
                .str.lower()
                .eq("true")
                .sum()
            )

        if "has_observations" in confirmed_series_probe.columns:
            has_observations = int(
                confirmed_series_probe["has_observations"]
                .astype(str)
                .str.lower()
                .eq("true")
                .sum()
            )

        status_rows.append(
            {
                "artifact": "Confirmed single-series probe",
                "status": "successful_response",
                "count": f"{successful} success / {has_observations} with observations",
                "interpretation": (
                    "Confirmed GRP.<REGION>._Z.A pattern returns official observation "
                    "values for a test oblast."
                ),
            }
        )

    if confirmed_series_parsed is not None and not confirmed_series_parsed.empty:
        parsed_rows = len(confirmed_series_parsed)
        status_rows.append(
            {
                "artifact": "Confirmed series parsed observations",
                "status": "parsed_pending_validation",
                "count": parsed_rows,
                "interpretation": (
                    "Official observations parsed into period/value rows, still not "
                    "used in scoring."
                ),
            }
        )

    if all_oblast_probe is not None and not all_oblast_probe.empty:
        successful = 0
        with_obs = 0

        if "success_status" in all_oblast_probe.columns:
            successful = int(
                all_oblast_probe["success_status"]
                .astype(str)
                .str.lower()
                .eq("true")
                .sum()
            )

        if "has_observations" in all_oblast_probe.columns:
            with_obs = int(
                all_oblast_probe["has_observations"]
                .astype(str)
                .str.lower()
                .eq("true")
                .sum()
            )

        status_rows.append(
            {
                "artifact": "All-oblast official baseline probes",
                "status": "successful_response",
                "count": f"{successful} success / {with_obs} with observations",
                "interpretation": (
                    "Oblast-level GRP series probed across the official regional "
                    "baseline shortlist."
                ),
            }
        )

    if all_oblast_candidates is not None and not all_oblast_candidates.empty:
        candidate_count = len(all_oblast_candidates)
        scoring_use = "not_yet_used"

        if "current_use_in_scoring" in all_oblast_candidates.columns:
            scoring_use_values = (
                all_oblast_candidates["current_use_in_scoring"]
                .fillna("")
                .astype(str)
                .unique()
                .tolist()
            )
            if scoring_use_values:
                scoring_use = "; ".join(scoring_use_values[:3])

        status_rows.append(
            {
                "artifact": "All-oblast official baseline candidates",
                "status": "pending_unit_and_mapping_validation",
                "count": candidate_count,
                "interpretation": (
                    "Official latest available GRP baseline candidates created. "
                    f"Current scoring use: {scoring_use}."
                ),
            }
        )

    if status_rows:
        story.append(Paragraph("Official regional baseline transition status", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Official regional baseline transition status')
        story.append(
            _table_from_df(
                pd.DataFrame(status_rows),
                ["artifact", "status", "count", "interpretation"],
                max_rows=10,
                col_widths=[
                    2.25 * inch,
                    1.45 * inch,
                    1.4 * inch,
                    4.0 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if all_oblast_candidates is not None and not all_oblast_candidates.empty:
        story.append(
            Paragraph("All-oblast official baseline candidates", styles["Heading3"])
        )
        _append_how_to_read(story, styles, 'All-oblast official baseline candidates')
        story.append(
            Paragraph(
                "The table below summarizes the latest available official regional "
                "baseline candidate for each oblast-level region. These values are "
                "candidate replacements for synthetic regional baseline fields only; "
                "they remain excluded from scoring pending validation.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.08 * inch))

        story.append(
            _table_from_df(
                all_oblast_candidates,
                [
                    "oblast",
                    "region_code",
                    "indicator_code",
                    "nace_code",
                    "freq_code",
                    "latest_period",
                    "official_regional_baseline_proxy",
                    "validation_status",
                    "current_use_in_scoring",
                ],
                max_rows=25,
                col_widths=[
                    1.25 * inch,
                    1.65 * inch,
                    0.7 * inch,
                    0.6 * inch,
                    0.55 * inch,
                    0.9 * inch,
                    1.25 * inch,
                    1.35 * inch,
                    1.0 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if all_oblast_probe is not None and not all_oblast_probe.empty:
        story.append(Paragraph("All-oblast probe results", styles["Heading3"]))
        _append_how_to_read(story, styles, 'All-oblast probe results')

        probe_display = all_oblast_probe.copy()

        if "response_preview" in probe_display.columns:
            probe_display["response_preview"] = (
                probe_display["response_preview"]
                .fillna("")
                .astype(str)
                .str.slice(0, 120)
            )

        story.append(
            _table_from_df(
                probe_display,
                [
                    "oblast",
                    "http_status",
                    "success_status",
                    "observation_value_count",
                    "has_observations",
                    "notes",
                ],
                max_rows=15,
                col_widths=[
                    1.35 * inch,
                    0.65 * inch,
                    0.8 * inch,
                    1.05 * inch,
                    0.85 * inch,
                    4.45 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if availability_values is not None and not availability_values.empty:
        story.append(Paragraph("Availability-derived query values", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Availability-derived query values')

        value_display = availability_values.copy()

        if "dimension_id" in value_display.columns:
            preferred_dimensions = ["INDICATOR", "REGION", "NACE", "FREQ", "TIME_PERIOD"]
            value_display["_dimension_order"] = (
                value_display["dimension_id"]
                .fillna("")
                .astype(str)
                .map({value: idx for idx, value in enumerate(preferred_dimensions)})
                .fillna(99)
            )
            value_display = value_display.sort_values(
                ["_dimension_order", "dimension_id", "value_code"],
                ascending=[True, True, True],
            ).drop(columns=["_dimension_order"])

        story.append(
            _table_from_df(
                value_display,
                [
                    "dimension_id",
                    "value_code",
                    "value_name",
                    "candidate_role",
                    "query_use_status",
                    "validation_status",
                ],
                max_rows=14,
                col_widths=[
                    1.0 * inch,
                    1.3 * inch,
                    2.3 * inch,
                    1.6 * inch,
                    1.5 * inch,
                    1.4 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if confirmed_single_baseline is not None and not confirmed_single_baseline.empty:
        story.append(
            Paragraph("Single-oblast confirmed baseline candidate", styles["Heading3"])
        )
        _append_how_to_read(story, styles, 'Single-oblast confirmed baseline candidate')
        story.append(
            _table_from_df(
                confirmed_single_baseline,
                [
                    "oblast",
                    "indicator_code",
                    "nace_code",
                    "freq_code",
                    "latest_period",
                    "official_regional_baseline_proxy",
                    "validation_status",
                    "current_use_in_scoring",
                ],
                max_rows=5,
                col_widths=[
                    1.35 * inch,
                    0.8 * inch,
                    0.65 * inch,
                    0.65 * inch,
                    0.9 * inch,
                    1.4 * inch,
                    1.55 * inch,
                    1.2 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if discovery is not None and not discovery.empty:
        story.append(Paragraph("Regional accounts dataflow discovery", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Regional accounts dataflow discovery')
        story.append(
            _table_from_df(
                discovery,
                [
                    "id",
                    "name",
                    "candidate_role",
                    "implementation_status",
                    "notes",
                ],
                max_rows=8,
                col_widths=[
                    1.7 * inch,
                    1.8 * inch,
                    1.8 * inch,
                    1.8 * inch,
                    2.2 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if metadata_clues is not None and not metadata_clues.empty:
        story.append(Paragraph("Regional accounts metadata clues", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Regional accounts metadata clues')
        story.append(
            _table_from_df(
                metadata_clues,
                [
                    "metadata_type",
                    "id",
                    "name",
                    "agencyID",
                    "version",
                    "relevance_to_waris",
                ],
                max_rows=10,
                col_widths=[
                    1.2 * inch,
                    1.75 * inch,
                    2.3 * inch,
                    0.7 * inch,
                    0.75 * inch,
                    2.4 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if registry_references is not None and not registry_references.empty:
        story.append(Paragraph("Ukrstat registry references", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Ukrstat registry references')
        story.append(
            _table_from_df(
                registry_references,
                [
                    "artifact_type",
                    "artifact_id",
                    "name",
                    "agencyID",
                    "version",
                    "relevance_to_observation_pull",
                ],
                max_rows=14,
                col_widths=[
                    1.15 * inch,
                    1.8 * inch,
                    2.25 * inch,
                    0.7 * inch,
                    0.7 * inch,
                    2.6 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if endpoint_probe is not None and not endpoint_probe.empty:
        story.append(Paragraph("Ukrstat endpoint probe results", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Ukrstat endpoint probe results')

        probe_display = endpoint_probe.copy()

        if "response_preview" in probe_display.columns:
            probe_display["response_preview"] = (
                probe_display["response_preview"]
                .fillna("")
                .astype(str)
                .str.slice(0, 180)
            )

        story.append(
            _table_from_df(
                probe_display,
                [
                    "probe_name",
                    "http_status",
                    "success_status",
                    "content_type",
                    "first_json_keys",
                    "response_preview",
                ],
                max_rows=10,
                col_widths=[
                    1.65 * inch,
                    0.65 * inch,
                    0.8 * inch,
                    1.5 * inch,
                    1.2 * inch,
                    3.25 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if query_plan is not None and not query_plan.empty:
        story.append(Paragraph("Ukrstat observation query plan", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Ukrstat observation query plan')
        story.append(
            _table_from_df(
                query_plan,
                [
                    "step",
                    "task",
                    "status",
                    "notes",
                ],
                max_rows=8,
                col_widths=[
                    0.5 * inch,
                    2.2 * inch,
                    0.85 * inch,
                    5.4 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    if baseline is not None and not baseline.empty:
        story.append(Paragraph("Original placeholder baseline transition table", styles["Heading3"]))
        _append_how_to_read(story, styles, 'Original placeholder baseline transition table')
        story.append(
            _table_from_df(
                baseline,
                [
                    "oblast",
                    "candidate_dataflow",
                    "source_status",
                    "implementation_status",
                    "current_use_in_scoring",
                    "notes",
                ],
                max_rows=15,
                col_widths=[
                    1.25 * inch,
                    1.65 * inch,
                    1.25 * inch,
                    2.0 * inch,
                    1.25 * inch,
                    2.4 * inch,
                ],
            )
        )

def _build_data_coverage_appendix(
    story: list,
    styles,
    live_status: pd.DataFrame | None,
) -> None:
    """Add a source-to-model-layer coverage appendix."""
    if live_status is None or live_status.empty:
        return

    status_df = live_status.copy()
    status_df = status_df.rename(columns={"source": "source_name"})
    status_df = _normalize_live_status_for_report(
        status_df.rename(columns={"source_name": "source"})
    ).rename(columns={"source": "source_name"})

    rows = []
    for _, row in status_df.iterrows():
        source_name = row.get("source_name", "")
        mapped = SOURCE_LAYER_MAP.get(
            source_name,
            {
                "model_layer_supported": "General source context",
                "current_use": "Source availability recorded in live-status table.",
                "future_use": "Future model-layer mapping required.",
            },
        )

        rows.append(
            {
                "source_name": source_name,
                "status": row.get("status", ""),
                "rows": row.get("rows", 0),
                "model_layer_supported": mapped["model_layer_supported"],
                "current_use": mapped["current_use"],
                "future_use": mapped["future_use"],
            }
        )

    coverage_df = pd.DataFrame(rows)

    story.append(PageBreak())
    story.append(Paragraph("Data coverage appendix", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Data coverage appendix')

    story.append(
        Paragraph(
            "This appendix maps each live/source-backed connector to the WARIS model "
            "layer it currently supports. This is intended to make the prototype more "
            "transparent, auditable, and easier to validate before any operational use.",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 0.08 * inch))

    story.append(
        _table_from_df(
            coverage_df,
            [
                "source_name",
                "status",
                "rows",
                "model_layer_supported",
                "current_use",
                "future_use",
            ],
            max_rows=12,
            col_widths=[
                1.65 * inch,
                0.55 * inch,
                0.55 * inch,
                1.45 * inch,
                2.55 * inch,
                2.55 * inch,
            ],
        )
    )


def build_pdf_report(
    scored: pd.DataFrame,
    oblast_summary: pd.DataFrame,
    sector_summary: pd.DataFrame,
    mc_results: pd.DataFrame,
    chart_paths: list[str],
    source_register: pd.DataFrame,
    live_status: pd.DataFrame | None = None,
) -> Path:
    ensure_dirs([REPORT_DIR])

    out_path = _safe_report_path()

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=REPORT_PAGE_SIZE,
        rightMargin=REPORT_RIGHT_MARGIN,
        leftMargin=REPORT_LEFT_MARGIN,
        topMargin=REPORT_TOP_MARGIN,
        bottomMargin=REPORT_BOTTOM_MARGIN,
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Tiny",
            parent=styles["BodyText"],
            fontSize=7,
            leading=9,
        )
    )

    styles.add(
        ParagraphStyle(
            name="HowToRead",
            parent=styles["Small"],
            fontSize=7.6,
            leading=9.2,
            leftIndent=0.08 * inch,
            rightIndent=0.08 * inch,
            spaceBefore=2,
            spaceAfter=4,
            textColor=colors.HexColor("#2F3A4A"),
            backColor=colors.HexColor("#F1F5FA"),
            borderColor=colors.HexColor("#C7D3E5"),
            borderWidth=0.35,
            borderPadding=4,
        )
    )

    story = []

    story.append(Paragraph(PROJECT_NAME, styles["Title"]))
    story.append(
        Paragraph(
            "Prototype report - public-source, sector/oblast-level AML decision support",
            styles["Heading2"],
        )
    )
    _append_how_to_read(story, styles, 'Prototype report - public-source, sector/oblast-level AML decision support')
    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Purpose: identify wartime revenue-integrity and AML review priorities "
            "using transparent public-source risk layers. This model is not an "
            "accusation engine. It produces prioritization signals for trained "
            "human review.",
            styles["BodyText"],
        )
    )

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Methodology", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Methodology')

    methodology = (
        "WARIS combines revenue anomaly, sanctions exposure, procurement integrity, "
        "ownership opacity, trade-based money laundering exposure, conflict "
        "plausibility gap, and financial-supervision exposure. The prototype uses "
        "synthetic fallback inputs so the pipeline runs immediately, then blends "
        "available live or public-source enrichments into selected risk proxies. "
        "Relevant source families include NBU supervisory context, NBU financial-sector "
        "data, Prozorro procurement data, Ukraine sanctions records, OpenSanctions, "
        "OFAC sanctions references, Ukrstat statistics, World Bank indicators, and "
        "ACLED conflict data. A separate official indicator alignment catalog maps "
        "NBU and Ukrstat candidate indicators to WARIS layers before deeper integration. "
        "Model governance artifacts document inventory, limitations, validation status, "
        "and monitoring controls. Source-confidence artifacts document field lineage, "
        "qualitative confidence levels, and replacement priorities. Ukrstat regional "
        "accounts transition artifacts document the path from metadata discovery toward "
        "official regional baseline observations, including current metadata clues, "
        "registry references, endpoint probes, availability-derived values, confirmed "
        "series pulls, validation-only oblast baseline candidates, unit/scale evidence, "
        "expanded Prozorro procurement feature artifacts, wartime AML/CFT typology "
        "reference artifacts, official FIU/SFMS source-context artifacts, controlled "
        "benchmark-integration merge-planning artifacts, source-context bridge/review "
        "artifacts, merge-review artifacts that summarize official-vs-synthetic gaps "
        "and scenario recommendations, and a benchmark review memo that explains the "
        "findings in plain language. Official GRP values are approved for benchmark "
        "integration only and remain prohibited from risk-layer calculation or composite "
        "scoring. Expanded Prozorro, wartime AML/CFT typology, and FIU/SFMS artifacts "
        "remain source-support or review-only layers with production_score_change=none "
        "until measurable indicator design, source validation, SME review, false-positive "
        "controls, and formal change control are complete."
    )

    story.append(Paragraph(methodology, styles["BodyText"]))
    story.append(Spacer(1, 0.1 * inch))

    weights_text = ", ".join(
        [f"{k.replace('_', ' ')}: {v:.0%}" for k, v in BASE_WEIGHTS.items()]
    )
    story.append(Paragraph(f"Base weights: {weights_text}.", styles["Small"]))

    _build_live_status_section(story, styles, live_status)
    _build_acled_conflict_section(story, styles, scored)

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Top review signals", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Top review signals')

    story.append(
        _table_from_df(
            scored,
            [
                "oblast",
                "sector",
                "waris_aml_review_score",
                "risk_band",
                "review_rationale",
            ],
            12,
            [
                0.9 * inch,
                1.65 * inch,
                0.85 * inch,
                1.55 * inch,
                4.35 * inch,
            ],
        )
    )

    for path in chart_paths:
        story.append(Spacer(1, 0.18 * inch))
        story.append(Image(path, width=6.8 * inch, height=4.1 * inch))

    story.append(PageBreak())
    story.append(Paragraph("Oblast summary", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Oblast summary')

    story.append(
        _table_from_df(
            oblast_summary,
            [
                "oblast",
                "waris_aml_review_score",
                "max_sector_score",
                "high_priority_sectors",
                "elevated_priority_sectors",
                "risk_band",
            ],
            15,
            [
                1.2 * inch,
                1.2 * inch,
                1.1 * inch,
                1.15 * inch,
                1.35 * inch,
                2.0 * inch,
            ],
        )
    )

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Sector summary", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Sector summary')

    story.append(
        _table_from_df(
            sector_summary,
            [
                "sector",
                "waris_aml_review_score",
                "max_oblast_score",
                "elevated_or_high_count",
                "risk_band",
            ],
            10,
            [
                2.2 * inch,
                1.2 * inch,
                1.2 * inch,
                1.4 * inch,
                2.0 * inch,
            ],
        )
    )

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Monte Carlo robustness", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Monte Carlo robustness')

    story.append(
        Paragraph(
            "Monte Carlo testing perturbs layer scores and weights to estimate "
            "whether elevated signals remain stable under uncertainty.",
            styles["Small"],
        )
    )

    story.append(
        _table_from_df(
            mc_results,
            [
                "oblast",
                "sector",
                "waris_aml_review_score",
                "mc_p05_score",
                "mc_p95_score",
                "prob_elevated_or_high",
                "robustness_band",
            ],
            12,
            [
                0.9 * inch,
                1.65 * inch,
                1.0 * inch,
                0.85 * inch,
                0.85 * inch,
                1.1 * inch,
                1.65 * inch,
            ],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("Source register", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Source register')

    story.append(
        Paragraph(
            "These are reference sources for institutional framing, model design, "
            "and live/public-source enrichment. The prototype uses synthetic "
            "fallback fields when official extracts or source connectors are "
            "unavailable.",
            styles["Small"],
        )
    )

    story.append(
        _table_from_df(
            source_register,
            ["source_name", "url", "use_in_model"],
            20,
            [
                2.3 * inch,
                3.2 * inch,
                4.0 * inch,
            ],
        )
    )

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Recommended next build steps", styles["Heading2"]))
    _append_how_to_read(story, styles, 'Recommended next build steps')

    next_steps = [
        "Keep official GRP values limited to controlled benchmark integration until transformation logic, SME review, and scoring change-control approval are documented.",
        "Expand Prozorro procurement features by region, buyer, sector, award concentration, and emergency/reconstruction exposure.",
        "Map NBU financial-sector data into a more precise supervisory-exposure layer.",
        "Review official_baseline_benchmark_review_memo.md, official_baseline_gap_review.csv, official_baseline_scenario_recommendations.csv, and official_baseline_merge_review_summary.csv before considering any scoring blend.",
        "Add sanctions-screening features using Ukraine NSDC, OpenSanctions, OFAC, EU, UK, and UN lists.",
        "Keep analyst-review, false-positive, source-freshness, and run-manifest artifacts as operational controls only; they support review and reproducibility but do not approve scoring.",
        "Add source confidence labels, false-positive controls, source-freshness monitoring, run manifests, and SME-reviewed model governance documentation before any operational use.",
    ]

    for step in next_steps:
        story.append(Paragraph(f"- {step}", styles["Small"]))

    _build_prozorro_procurement_features_section(story, styles)
    _build_wartime_aml_typology_section(story, styles)
    _build_fiu_official_context_section(story, styles)
    _build_official_baseline_context_bridge_section(story, styles)
    _build_operational_controls_section(story, styles)
    _build_official_indicator_section(story, styles)
    _build_official_baseline_validation_section(story, styles)
    _build_official_baseline_merge_plan_section(story, styles)
    _build_official_baseline_merge_review_section(story, styles)
    _build_official_baseline_review_memo_section(story, styles)
    _build_model_governance_section(story, styles)
    _build_source_confidence_section(story, styles)
    _build_ukrstat_baseline_transition_section(story, styles)
    _build_data_coverage_appendix(story, styles, live_status)

    doc.build(story)

    return out_path
