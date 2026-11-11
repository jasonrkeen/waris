from pathlib import Path
from src.controlled_guards import require_acled_clearance

from dotenv import load_dotenv

from src.config import (
    CHART_DIR,
    MODEL_VERSION,
    OUTPUT_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    REPORT_DIR,
    TABLE_DIR,
)
from src.data_collection import (
    build_oblast_name_crosswalk,
    build_source_register,
    build_synthetic_oblast_sector_data,
)
from src.live_data import enrich_with_optional_live_data
from src.analyst_review_queue import build_analyst_review_artifacts
from src.false_positive_controls import build_false_positive_control_artifacts
from src.model_governance import build_model_governance_artifacts
from src.monte_carlo import run_monte_carlo
from src.official_baseline_validation import (
    build_official_baseline_validation_artifacts,
)
from src.official_baseline_merge_plan import (
    build_official_baseline_merge_plan_artifacts,
)
from src.official_baseline_merge_review import (
    build_official_baseline_merge_review_artifacts,
)
from src.official_baseline_review_memo import (
    build_official_baseline_review_memo_artifacts,
)
from src.prozorro_procurement_features import (
    build_prozorro_procurement_feature_artifacts,
)
from src.wartime_aml_typology_register import (
    build_wartime_aml_typology_artifacts,
)
from src.fiu_official_context import build_fiu_official_context_artifacts
from src.report_generator import build_pdf_report
from src.run_manifest import build_run_manifest_artifacts
from src.provenance import start_run, capture_scoring_input, capture_simulation_input, verify_run
from src.risk_model import calculate_risk_layers, summarize_by_oblast, summarize_by_sector
from src.source_confidence import build_source_confidence_artifacts
from src.source_freshness import build_source_freshness_artifacts
from src.ukrstat_observations import build_ukrstat_regional_accounts_artifacts
from src.utils import ensure_dirs
from src.visualization import (
    plot_conflict_intensity,
    plot_layer_profile,
    plot_live_source_status,
    plot_oblast_summary,
    plot_official_baseline_candidates,
    plot_official_baseline_validation_status,
    plot_source_context_artifact_coverage,
    plot_typology_family_distribution,
    plot_fiu_context_artifact_coverage,
    plot_context_review_coverage,
    plot_operational_controls_coverage,
    plot_top_risks,
)



def _stable_run_identity_from_manifest(
    manifest_artifacts: dict,
) -> tuple[str | None, str | None]:
    """Extract stable run identity from a run-manifest artifact payload."""
    summary = manifest_artifacts.get("run_manifest_summary")

    if summary is None or summary.empty:
        return None, None

    first = summary.iloc[0]
    run_id = first.get("run_id")
    run_timestamp_utc = first.get("run_timestamp_utc")

    return (
        None if run_id is None else str(run_id),
        None if run_timestamp_utc is None else str(run_timestamp_utc),
    )


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Legacy research pipeline with live downloads")
    parser.add_argument("--allow-live", action="store_true", help="Enable provider downloads and mixed-input research scoring")
    args = parser.parse_args()
    if not args.allow_live:
        parser.error("Use python offline_demo.py for the public synthetic demonstration. Live research requires --allow-live and provider authorization.")

    require_acled_clearance()

    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)

    print("=" * 72)
    print("WARIS - Ukraine Wartime AML Revenue Integrity Scoring Model")
    print(f"Model version: v{MODEL_VERSION}")
    print("=" * 72)

    # Console step labels are intentionally kept at 22 total stages. Several
    # stages build multiple related governance/context artifacts, but they are
    # grouped to keep the run output readable. A current-run manifest identity is
    # refreshed before bridge/review generation, then the final manifest is built
    # before the PDF so the report can consume same-run version and manifest
    # summary data instead of the previous run's manifest.
    ensure_dirs([OUTPUT_DIR, TABLE_DIR, CHART_DIR, REPORT_DIR, PROCESSED_DIR, RAW_DIR])

    execution_context = start_run(Path(__file__).resolve().parent)

    print("[1/22] Building source register and geography crosswalk...")
    raw = build_synthetic_oblast_sector_data()
    sources = build_source_register()
    sources.to_csv(TABLE_DIR / "source_register.csv", index=False)

    oblast_crosswalk = build_oblast_name_crosswalk()

    print("[2/22] Building Ukrstat regional accounts transition artifacts...")
    # Build Ukrstat artifacts before live-data, risk, governance, source-confidence,
    # Monte Carlo, validation, and reporting outputs so all downstream modules can
    # see the latest validation-only official baseline candidate layer in the same run.
    ukrstat_artifacts = build_ukrstat_regional_accounts_artifacts()

    print("[3/22] Building expanded Prozorro procurement feature artifacts...")
    # This creates deeper source-backed procurement review artifacts, including
    # oblast/sector procurement feature candidates. These outputs are review
    # artifacts only and do not alter production WARIS scoring without future
    # governance approval.
    prozorro_procurement_artifacts = build_prozorro_procurement_feature_artifacts()

    print("[4/22] Building wartime AML/CFT typology reference artifacts...")
    # These are literature-support and typology-reference artifacts only. They
    # support governance, source confidence, and future feature design, but do
    # not alter production WARIS scores, risk layers, risk bands, or Monte Carlo.
    wartime_typology_artifacts = build_wartime_aml_typology_artifacts()

    print("[5/22] Building official FIU/SFMS context artifacts...")
    # These are official source-support context artifacts only. They support
    # governance, source confidence, reporting, and typology review, but do not
    # alter production WARIS scores, risk layers, risk bands, or Monte Carlo.
    fiu_official_context_artifacts = build_fiu_official_context_artifacts()

    print("      Refreshing current run identity manifest for bridge/review freshness...")
    # Some downstream bridge/review artifacts read run_manifest_summary.csv while
    # they are being created. Build a lightweight current-run manifest now so
    # those bridge/review artifacts reference this run ID instead of the previous
    # run. The final manifest is rebuilt at step 20 with the same run identity
    # after all artifacts and charts are generated.
    run_manifest_artifacts = build_run_manifest_artifacts(
        context=execution_context,
        manifest_phase="pre_context_bridge"
    )
    stable_run_id, stable_run_timestamp_utc = _stable_run_identity_from_manifest(
        run_manifest_artifacts
    )

    # Refresh evidence-based readiness before consumers can read a previous run.
    build_official_baseline_validation_artifacts()

    print("[6/22] Building official baseline merge-planning and context-bridge artifacts...")
    # This creates controlled benchmark-integration artifacts only. It compares
    # benchmark_only, rescale_revenue_baseline, replace_oblast_baseline, and
    # review-only source-context bridge scenarios without changing production
    # WARIS scores, risk layers, risk bands, or Monte Carlo simulations.
    official_baseline_merge_plan_artifacts = (
        build_official_baseline_merge_plan_artifacts()
    )

    print("[7/22] Building official baseline merge-review artifacts...")
    # This reviews controlled benchmark-integration outputs and context bridges,
    # identifies largest official-vs-synthetic gaps, scenario recommendations,
    # and current benchmark-only posture. It does not change production scoring.
    official_baseline_merge_review_artifacts = (
        build_official_baseline_merge_review_artifacts()
    )

    print("[8/22] Building official baseline validation artifacts...")
    # This is a staged validation gate. It validates candidate readiness and
    # confirms the no-scoring gates for official baseline, Prozorro, wartime
    # typology, FIU/SFMS context, and operational-control artifacts.
    official_baseline_validation_artifacts = (
        build_official_baseline_validation_artifacts()
    )

    # Refresh consumers against the completed current validation decision.
    official_baseline_merge_plan_artifacts = build_official_baseline_merge_plan_artifacts()
    official_baseline_merge_review_artifacts = build_official_baseline_merge_review_artifacts()

    print("[9/22] Building official baseline benchmark review memo...")
    # This creates an analyst-facing markdown memo that explains the controlled
    # benchmark review findings and context-bridge controls in plain language.
    # It does not change scoring.
    official_baseline_review_memo_artifacts = (
        build_official_baseline_review_memo_artifacts()
    )

    print("[10/22] Loading prototype data and optional live/source-backed enrichments...")
    raw, live_status = enrich_with_optional_live_data(raw)
    live_status.to_csv(TABLE_DIR / "live_data_status.csv", index=False)

    print("[11/22] Calculating AML review risk layers...")
    execution_context = capture_scoring_input(execution_context, Path(__file__).resolve().parent, raw)
    scored = calculate_risk_layers(raw)
    scored.to_csv(PROCESSED_DIR / "waris_scored_oblast_sector.csv", index=False)
    scored.to_csv(TABLE_DIR / "waris_scored_oblast_sector.csv", index=False)

    print("[12/22] Building oblast and sector summaries...")
    oblast_summary = summarize_by_oblast(scored)
    sector_summary = summarize_by_sector(scored)

    oblast_summary.to_csv(TABLE_DIR / "waris_oblast_summary.csv", index=False)
    sector_summary.to_csv(TABLE_DIR / "waris_sector_summary.csv", index=False)

    print("[13/22] Running Monte Carlo robustness analysis...")
    execution_context = capture_simulation_input(execution_context, Path(__file__).resolve().parent, scored)
    mc = run_monte_carlo(scored)
    mc.to_csv(TABLE_DIR / "waris_monte_carlo_results.csv", index=False)

    print("[14/22] Building analyst review workflow artifacts...")
    # This converts WARIS signals into human-review queue records, suggested
    # review questions, and a disposition template. It does not alter scoring,
    # risk bands, review rationales, Monte Carlo outputs, or source-context gates.
    analyst_review_artifacts = build_analyst_review_artifacts()

    print("[15/22] Building false-positive control artifacts...")
    # This documents plausible benign explanations, review controls, and
    # checklist items for analyst review. It does not alter scoring, risk bands,
    # review rationales, Monte Carlo outputs, or source-context gates.
    false_positive_artifacts = build_false_positive_control_artifacts()

    print("[16/22] Building model governance artifacts...")
    governance_artifacts = build_model_governance_artifacts()

    print("[17/22] Building source confidence and field lineage artifacts...")
    source_confidence_artifacts = build_source_confidence_artifacts()

    print("[18/22] Building source freshness and refresh-priority artifacts...")
    # This documents artifact availability, row counts, file age, freshness
    # status, and refresh priorities. It does not alter scoring, risk bands,
    # review rationales, analyst dispositions, Monte Carlo outputs, or source-context gates.
    source_freshness_artifacts = build_source_freshness_artifacts()

    print("[19/22] Creating charts...")
    chart_paths = [
        plot_top_risks(scored),
        plot_layer_profile(scored),
        plot_oblast_summary(oblast_summary),
    ]

    optional_chart_paths = [
        plot_conflict_intensity(scored),
        plot_live_source_status(live_status),
        plot_official_baseline_candidates(),
        plot_official_baseline_validation_status(),
        plot_source_context_artifact_coverage(),
        plot_typology_family_distribution(),
        plot_fiu_context_artifact_coverage(),
        plot_context_review_coverage(),
        plot_operational_controls_coverage(),
    ]

    chart_paths.extend([path for path in optional_chart_paths if path is not None])

    print("[20/22] Building run manifest artifacts...")
    # Build the run manifest before the PDF so the report can include the
    # current run's manifest summary, model version, output inventory, and
    # no-scoring/no-adverse-action controls. The manifest is documentation only
    # and does not alter WARIS scores, risk bands, or Monte Carlo outputs.
    run_manifest_artifacts = build_run_manifest_artifacts(
        run_id=stable_run_id,
        run_timestamp_utc=stable_run_timestamp_utc,
        context=execution_context,
        manifest_phase="pre_report",
    )

    print("[21/22] Building PDF report...")
    report_path = build_pdf_report(
        scored=scored,
        oblast_summary=oblast_summary,
        sector_summary=sector_summary,
        mc_results=mc,
        chart_paths=chart_paths,
        source_register=sources,
        live_status=live_status,
    )

    print("[22/22] Writing final run summary...")
    # Final inventory must observe this run's completed PDF, not an older file.
    run_manifest_artifacts = build_run_manifest_artifacts(
        run_id=stable_run_id,
        run_timestamp_utc=stable_run_timestamp_utc,
        context=execution_context,
        manifest_phase="final",
    )


    integrity_errors = verify_run(Path(__file__).resolve().parent)
    if integrity_errors:
        raise RuntimeError("Final provenance verification failed: " + ", ".join(integrity_errors))

    print("\nPipeline complete.")
    print(f"- Scored table: {TABLE_DIR / 'waris_scored_oblast_sector.csv'}")
    print(f"- Oblast summary: {TABLE_DIR / 'waris_oblast_summary.csv'}")
    print(f"- Sector summary: {TABLE_DIR / 'waris_sector_summary.csv'}")
    print(f"- Monte Carlo results: {TABLE_DIR / 'waris_monte_carlo_results.csv'}")
    print(f"- Analyst review queue: {TABLE_DIR / 'analyst_review_queue.csv'}")
    print(f"- Analyst review questions: {TABLE_DIR / 'analyst_review_questions.csv'}")
    print(f"- Review disposition template: {TABLE_DIR / 'review_disposition_template.csv'}")
    print(f"- Analyst review summary: {TABLE_DIR / 'analyst_review_summary.csv'}")
    print(f"- False-positive risk register: {TABLE_DIR / 'false_positive_risk_register.csv'}")
    print(f"- False-positive controls: {TABLE_DIR / 'false_positive_controls.csv'}")
    print(f"- False-positive review checklist: {TABLE_DIR / 'false_positive_review_checklist.csv'}")
    print(f"- False-positive summary: {TABLE_DIR / 'false_positive_summary.csv'}")
    print(f"- PDF report: {report_path}")
    print(f"- Run manifest table: {TABLE_DIR / 'run_manifest.csv'}")
    print(f"- Run manifest summary: {TABLE_DIR / 'run_manifest_summary.csv'}")
    print(f"- Run manifest JSON: {REPORT_DIR / 'run_manifest.json'}")
    print(f"- Live/source status: {TABLE_DIR / 'live_data_status.csv'}")
    print(
        f"- Prozorro expanded tender list: "
        f"{RAW_DIR / 'prozorro_expanded_tenders_raw.csv'}"
    )
    print(
        f"- Prozorro expanded tender details: "
        f"{RAW_DIR / 'prozorro_expanded_tender_details_raw.csv'}"
    )
    print(
        f"- Prozorro expanded feature rows: "
        f"{RAW_DIR / 'prozorro_expanded_feature_rows_raw.csv'}"
    )
    print(
        f"- Prozorro procurement oblast features: "
        f"{TABLE_DIR / 'prozorro_procurement_features_oblast.csv'}"
    )
    print(
        f"- Prozorro procurement oblast-sector features: "
        f"{TABLE_DIR / 'prozorro_procurement_features_oblast_sector.csv'}"
    )
    print(
        f"- Prozorro procurement scoring candidates: "
        f"{TABLE_DIR / 'prozorro_procurement_scoring_candidates.csv'}"
    )
    print(
        f"- Prozorro procurement feature summary: "
        f"{TABLE_DIR / 'prozorro_procurement_feature_summary.csv'}"
    )
    print(
        f"- Wartime AML typology register: "
        f"{TABLE_DIR / 'waris_wartime_aml_typology_register.csv'}"
    )
    print(
        f"- Wartime AML typology layer map: "
        f"{TABLE_DIR / 'waris_wartime_aml_typology_layer_map.csv'}"
    )
    print(
        f"- Wartime AML typology summary: "
        f"{TABLE_DIR / 'waris_wartime_aml_typology_summary.csv'}"
    )
    print(
        f"- FIU/SFMS official source register: "
        f"{TABLE_DIR / 'waris_fiu_official_source_register.csv'}"
    )
    print(
        f"- FIU/SFMS reporting statistics context: "
        f"{TABLE_DIR / 'waris_fiu_reporting_statistics_context.csv'}"
    )
    print(
        f"- FIU/SFMS case referral context: "
        f"{TABLE_DIR / 'waris_fiu_case_referral_context.csv'}"
    )
    print(
        f"- FIU/SFMS typology support register: "
        f"{TABLE_DIR / 'waris_fiu_typology_support_register.csv'}"
    )
    print(
        f"- FIU/SFMS context summary: "
        f"{TABLE_DIR / 'waris_fiu_context_summary.csv'}"
    )
    print(f"- Official indicator catalog: {TABLE_DIR / 'official_indicator_catalog.csv'}")

    print(f"- Oblast name crosswalk: {TABLE_DIR / 'oblast_name_crosswalk.csv'}")

    print(f"- Model inventory: {TABLE_DIR / 'model_inventory.csv'}")
    print(f"- Model limitations: {TABLE_DIR / 'model_limitations_register.csv'}")
    print(f"- Validation checklist: {TABLE_DIR / 'model_validation_checklist.csv'}")
    print(f"- Monitoring plan: {TABLE_DIR / 'model_monitoring_plan.csv'}")
    print(f"- Governance summary: {TABLE_DIR / 'model_governance_summary.csv'}")

    print(f"- Field source register: {TABLE_DIR / 'field_source_register.csv'}")
    print(f"- Source confidence assessment: {TABLE_DIR / 'source_confidence_assessment.csv'}")
    print(f"- Source confidence summary: {TABLE_DIR / 'source_confidence_summary.csv'}")
    print(f"- Source freshness inventory: {TABLE_DIR / 'source_freshness_inventory.csv'}")
    print(f"- Source freshness assessment: {TABLE_DIR / 'source_freshness_assessment.csv'}")
    print(
        f"- Source freshness replacement priorities: "
        f"{TABLE_DIR / 'source_freshness_replacement_priorities.csv'}"
    )
    print(f"- Source freshness summary: {TABLE_DIR / 'source_freshness_summary.csv'}")

    print(
        f"- Official baseline validation register: "
        f"{TABLE_DIR / 'official_baseline_validation_register.csv'}"
    )
    print(
        f"- Official baseline validation summary: "
        f"{TABLE_DIR / 'official_baseline_validation_summary.csv'}"
    )
    print(
        f"- Official baseline geography crosswalk check: "
        f"{TABLE_DIR / 'official_baseline_geography_crosswalk_check.csv'}"
    )
    print(
        f"- Official baseline period coverage: "
        f"{TABLE_DIR / 'official_baseline_period_coverage.csv'}"
    )
    print(
        f"- Official baseline readiness decision: "
        f"{TABLE_DIR / 'official_baseline_readiness_decision.csv'}"
    )
    print(
        f"- Official baseline validation audit: "
        f"{RAW_DIR / 'official_baseline_validation_audit.csv'}"
    )
    print(
        f"- Official baseline merge plan: "
        f"{TABLE_DIR / 'official_baseline_merge_plan.csv'}"
    )
    print(
        f"- Official baseline benchmark comparison: "
        f"{TABLE_DIR / 'official_baseline_benchmark_comparison.csv'}"
    )
    print(
        f"- Official baseline rescale scenario: "
        f"{TABLE_DIR / 'official_baseline_rescale_scenario.csv'}"
    )
    print(
        f"- Official baseline replace-oblast-baseline scenario: "
        f"{TABLE_DIR / 'official_baseline_replace_oblast_baseline_scenario.csv'}"
    )
    print(
        f"- Official baseline merge-readiness summary: "
        f"{TABLE_DIR / 'official_baseline_merge_readiness_summary.csv'}"
    )
    print(
        f"- Official baseline to Prozorro context bridge: "
        f"{TABLE_DIR / 'official_baseline_prozorro_context_bridge.csv'}"
    )
    print(
        f"- Official baseline to wartime typology context bridge: "
        f"{TABLE_DIR / 'official_baseline_wartime_typology_context_bridge.csv'}"
    )
    print(
        f"- Official baseline to FIU/SFMS context bridge: "
        f"{TABLE_DIR / 'official_baseline_fiu_context_bridge.csv'}"
    )
    print(
        f"- Official baseline to operational controls context bridge: "
        f"{TABLE_DIR / 'official_baseline_operational_controls_context_bridge.csv'}"
    )
    print(
        f"- Official baseline gap review: "
        f"{TABLE_DIR / 'official_baseline_gap_review.csv'}"
    )
    print(
        f"- Official baseline scenario recommendations: "
        f"{TABLE_DIR / 'official_baseline_scenario_recommendations.csv'}"
    )
    print(
        f"- Official baseline merge-review summary: "
        f"{TABLE_DIR / 'official_baseline_merge_review_summary.csv'}"
    )
    print(
        f"- Official baseline to Prozorro context review: "
        f"{TABLE_DIR / 'official_baseline_prozorro_context_review.csv'}"
    )
    print(
        f"- Official baseline to wartime typology context review: "
        f"{TABLE_DIR / 'official_baseline_wartime_typology_context_review.csv'}"
    )
    print(
        f"- Official baseline to FIU/SFMS context review: "
        f"{TABLE_DIR / 'official_baseline_fiu_context_review.csv'}"
    )
    print(
        f"- Official baseline to operational controls context review: "
        f"{TABLE_DIR / 'official_baseline_operational_controls_context_review.csv'}"
    )
    print(
        f"- Official baseline benchmark review memo: "
        f"{REPORT_DIR / 'official_baseline_benchmark_review_memo.md'}"
    )

    print(
        f"- Ukrstat regional accounts discovery: "
        f"{RAW_DIR / 'ukrstat_regional_accounts_discovery_raw.csv'}"
    )
    print(
        f"- Ukrstat structure attempts: "
        f"{RAW_DIR / 'ukrstat_regional_accounts_structure_attempts.csv'}"
    )
    print(
        f"- Ukrstat structure paths: "
        f"{RAW_DIR / 'ukrstat_regional_accounts_structure_paths_raw.csv'}"
    )
    print(
        f"- Ukrstat saved DSD payload: "
        f"{RAW_DIR / 'ukrstat_dsd_regional_accounts_6_raw.json'}"
    )
    print(
        f"- Ukrstat saved DSD references payload: "
        f"{RAW_DIR / 'ukrstat_dsd_regional_accounts_6_references_raw.json'}"
    )
    print(
        f"- Ukrstat regional accounts dimensions: "
        f"{TABLE_DIR / 'ukrstat_regional_accounts_dimensions.csv'}"
    )
    print(
        f"- Ukrstat regional accounts codelists: "
        f"{TABLE_DIR / 'ukrstat_regional_accounts_codelists.csv'}"
    )
    print(
        f"- Ukrstat metadata clues: "
        f"{TABLE_DIR / 'ukrstat_regional_accounts_metadata_clues.csv'}"
    )
    print(
        f"- Ukrstat registry references: "
        f"{TABLE_DIR / 'ukrstat_registry_references.csv'}"
    )
    print(
        f"- Ukrstat DSD dimension candidates: "
        f"{TABLE_DIR / 'ukrstat_dsd_dimension_candidates.csv'}"
    )
    print(
        f"- Ukrstat dimension code candidates: "
        f"{TABLE_DIR / 'ukrstat_dimension_code_candidates.csv'}"
    )
    print(
        f"- Ukrstat observation query candidates: "
        f"{TABLE_DIR / 'ukrstat_observation_query_candidates.csv'}"
    )
    print(
        f"- Ukrstat availability discovery: "
        f"{TABLE_DIR / 'ukrstat_availability_discovery_results.csv'}"
    )
    print(
        f"- Ukrstat availability value candidates: "
        f"{TABLE_DIR / 'ukrstat_availability_value_candidates.csv'}"
    )
    print(
        f"- Ukrstat observation probe results: "
        f"{TABLE_DIR / 'ukrstat_observation_probe_results.csv'}"
    )
    print(
        f"- Ukrstat observation matrix probe results: "
        f"{TABLE_DIR / 'ukrstat_observation_matrix_probe_results.csv'}"
    )
    print(
        f"- Ukrstat confirmed series probe results: "
        f"{TABLE_DIR / 'ukrstat_confirmed_series_probe_results.csv'}"
    )
    print(
        f"- Ukrstat confirmed series parsed: "
        f"{TABLE_DIR / 'ukrstat_confirmed_series_parsed.csv'}"
    )
    print(
        f"- Ukrstat confirmed single-oblast baseline candidates: "
        f"{TABLE_DIR / 'ukrstat_confirmed_oblast_baseline_candidates.csv'}"
    )
    print(
        f"- Ukrstat all-oblast baseline probe results: "
        f"{TABLE_DIR / 'ukrstat_oblast_baseline_probe_results.csv'}"
    )
    print(
        f"- Ukrstat all-oblast baseline candidates: "
        f"{TABLE_DIR / 'ukrstat_oblast_baseline_candidates.csv'}"
    )
    print(
        f"- Ukrstat all-oblast success raw folder: "
        f"{RAW_DIR / 'ukrstat_oblast_baseline_success_responses'}"
    )
    print(
        f"- Ukrstat observation response paths: "
        f"{TABLE_DIR / 'ukrstat_observation_response_paths.csv'}"
    )
    print(
        f"- Ukrstat endpoint probe results: "
        f"{TABLE_DIR / 'ukrstat_endpoint_probe_results.csv'}"
    )
    print(
        f"- Ukrstat DSD endpoint probe results: "
        f"{TABLE_DIR / 'ukrstat_dsd_endpoint_probe_results.csv'}"
    )
    print(
        f"- Ukrstat observation query plan: "
        f"{TABLE_DIR / 'ukrstat_observation_query_plan.csv'}"
    )
    print(f"- Ukrstat placeholder oblast baseline: {TABLE_DIR / 'ukrstat_oblast_baseline.csv'}")

    print(f"- Charts folder: {CHART_DIR}")
    print(
        f"- Official baseline candidate chart: "
        f"{CHART_DIR / 'ukrstat_official_baseline_candidates.png'}"
    )
    print(
        f"- Official baseline validation-status chart: "
        f"{CHART_DIR / 'ukrstat_official_baseline_validation_status.png'}"
    )
    print(
        f"- Source-context artifact coverage chart: "
        f"{CHART_DIR / 'source_context_artifact_coverage.png'}"
    )
    print(
        f"- Wartime AML typology family distribution chart: "
        f"{CHART_DIR / 'wartime_aml_typology_family_distribution.png'}"
    )
    print(
        f"- FIU/SFMS context artifact coverage chart: "
        f"{CHART_DIR / 'fiu_context_artifact_coverage.png'}"
    )
    print(
        f"- Official baseline context-review coverage chart: "
        f"{CHART_DIR / 'official_baseline_context_review_coverage.png'}"
    )
    print(
        f"- Operational controls artifact coverage chart: "
        f"{CHART_DIR / 'operational_controls_artifact_coverage.png'}"
    )

    readiness = official_baseline_validation_artifacts.get("readiness_decision")
    if readiness is not None and not readiness.empty:
        decision = readiness.iloc[0].get("decision", "UNKNOWN")
        approved_use = readiness.iloc[0].get("approved_current_use", "UNKNOWN")
        prohibited_use = readiness.iloc[0].get("prohibited_current_use", "UNKNOWN")

        rationale = readiness.iloc[0].get("rationale", "")
        next_decision_point = readiness.iloc[0].get("next_decision_point", "")

        print("\nOfficial baseline validation gate:")
        print(f"- Decision: {decision}")
        print(f"- Approved current use: {approved_use}")
        print(f"- Prohibited current use: {prohibited_use}")

        if rationale:
            print(f"- Rationale: {rationale}")

        if next_decision_point:
            print(f"- Next decision point: {next_decision_point}")

    merge_summary = official_baseline_merge_plan_artifacts.get("merge_readiness_summary")
    if merge_summary is not None and not merge_summary.empty:
        print("\nOfficial baseline merge-planning gate:")
        for _, row in merge_summary.iterrows():
            summary_area = row.get("summary_area", "")
            status = row.get("status", "")
            summary = row.get("summary", "")
            if summary_area:
                print(f"- {summary_area}: {status} | {summary}")

    merge_review_summary = official_baseline_merge_review_artifacts.get(
        "merge_review_summary"
    )
    if merge_review_summary is not None and not merge_review_summary.empty:
        print("\nOfficial baseline merge-review gate:")
        for _, row in merge_review_summary.iterrows():
            summary_area = row.get("summary_area", "")
            status = row.get("status", "")
            summary = row.get("summary", "")
            recommended_next_action = row.get("recommended_next_action", "")
            if summary_area:
                print(f"- {summary_area}: {status} | {summary}")
                if recommended_next_action:
                    print(f"  Next action: {recommended_next_action}")

    memo_path = official_baseline_review_memo_artifacts.get("memo_path")
    if memo_path:
        print("\nOfficial baseline benchmark review memo:")
        print(f"- Memo: {memo_path}")
        print(
            "- Current posture: benchmark_only within controlled benchmark "
            "integration; production_score_change=none."
        )

    prozorro_summary = prozorro_procurement_artifacts.get("summary")
    if prozorro_summary is not None and not prozorro_summary.empty:
        print("\nProzorro procurement feature expansion:")
        for _, row in prozorro_summary.iterrows():
            summary_area = row.get("summary_area", "")
            status = row.get("status", "")
            value = row.get("value", "")
            recommended_next_action = row.get("recommended_next_action", "")
            if summary_area:
                print(f"- {summary_area}: {status} | {value}")
                if recommended_next_action:
                    print(f"  Next action: {recommended_next_action}")

    typology_summary = wartime_typology_artifacts.get("typology_summary")
    if typology_summary is not None and not typology_summary.empty:
        print("\nWartime AML/CFT typology reference layer:")
        for _, row in typology_summary.iterrows():
            summary_area = row.get("summary_area", "")
            status = row.get("status", "")
            value = row.get("value", "")
            recommended_next_action = row.get("recommended_next_action", "")
            if summary_area:
                print(f"- {summary_area}: {status} | {value}")
                if recommended_next_action:
                    print(f"  Next action: {recommended_next_action}")

    fiu_summary = fiu_official_context_artifacts.get("context_summary")
    if fiu_summary is not None and not fiu_summary.empty:
        print("\nOfficial FIU/SFMS context layer:")
        for _, row in fiu_summary.iterrows():
            summary_area = row.get("summary_area", "")
            status = row.get("status", "")
            value = row.get("value", "")
            recommended_next_action = row.get("recommended_next_action", "")
            if summary_area:
                print(f"- {summary_area}: {status} | {value}")
                if recommended_next_action:
                    print(f"  Next action: {recommended_next_action}")

    analyst_review_summary = analyst_review_artifacts.get("analyst_review_summary")
    if analyst_review_summary is not None and not analyst_review_summary.empty:
        print("\nAnalyst review workflow:")
        for _, row in analyst_review_summary.iterrows():
            summary_area = row.get("summary_area", "")
            status = row.get("status", "")
            value = row.get("value", "")
            recommended_next_action = row.get("recommended_next_action", "")
            if summary_area:
                print(f"- {summary_area}: {status} | {value}")
                if recommended_next_action:
                    print(f"  Next action: {recommended_next_action}")

    false_positive_summary = false_positive_artifacts.get("false_positive_summary")
    if false_positive_summary is not None and not false_positive_summary.empty:
        print("\nFalse-positive controls:")
        for _, row in false_positive_summary.iterrows():
            summary_area = row.get("summary_area", "")
            status = row.get("status", "")
            value = row.get("value", "")
            recommended_next_action = row.get("recommended_next_action", "")
            if summary_area:
                print(f"- {summary_area}: {status} | {value}")
                if recommended_next_action:
                    print(f"  Next action: {recommended_next_action}")

    source_freshness_summary = source_freshness_artifacts.get("source_freshness_summary")
    operational_bridge = official_baseline_merge_plan_artifacts.get(
        "operational_controls_context_bridge"
    )
    if operational_bridge is not None and not operational_bridge.empty:
        print("\nOfficial baseline to operational controls bridge:")
        print(f"- Rows: {len(operational_bridge)}")
        if "artifact_family" in operational_bridge.columns:
            families = (
                operational_bridge["artifact_family"]
                .dropna()
                .astype(str)
                .drop_duplicates()
                .tolist()
            )
            if families:
                print(f"- Artifact families: {'; '.join(families)}")
        print("- Current use: context_review_only; production_score_change=none.")

    operational_review = official_baseline_merge_review_artifacts.get(
        "operational_controls_context_review"
    )
    if operational_review is not None and not operational_review.empty:
        print("\nOfficial baseline to operational controls review:")
        print(f"- Rows: {len(operational_review)}")
        if "artifact_status" in operational_review.columns:
            status_counts = (
                operational_review["artifact_status"]
                .fillna("missing_status")
                .astype(str)
                .value_counts()
                .to_dict()
            )
            print(f"- Artifact status counts: {status_counts}")
        print("- Current use: context_review_only; production_score_change=none.")

    if source_freshness_summary is not None and not source_freshness_summary.empty:
        print("\nSource freshness and refresh priorities:")
        for _, row in source_freshness_summary.iterrows():
            summary_area = row.get("summary_area", "")
            status = row.get("status", "")
            value = row.get("value", "")
            recommended_next_action = row.get("recommended_next_action", "")
            if summary_area:
                print(f"- {summary_area}: {status} | {value}")
                if recommended_next_action:
                    print(f"  Next action: {recommended_next_action}")

    run_manifest_summary = run_manifest_artifacts.get("run_manifest_summary")
    if run_manifest_summary is not None and not run_manifest_summary.empty:
        row = run_manifest_summary.iloc[0]
        manifest_version = str(row.get("model_version", "not_available"))
        print("\nRun manifest:")
        print(f"- Run ID: {row.get('run_id', 'not_available')}")
        print(f"- Config model version: {MODEL_VERSION}")
        print(f"- Manifest model version: {manifest_version}")
        print(f"- Manifest phase: {row.get('manifest_phase', 'not_available')}")
        if manifest_version not in {MODEL_VERSION, f"v{MODEL_VERSION}"}:
            print(
                "- Version alignment warning: run_manifest.py may still be using "
                "a hardcoded model version. Update run_manifest.py to import "
                "MODEL_VERSION from src.config."
            )
        print(f"- Production score change: {row.get('production_score_change', 'not_available')}")
        print(f"- Git status: {row.get('git_working_tree_status', 'not_available')}")
        print(
            "- Output inventory: "
            f"{TABLE_DIR / 'run_manifest.csv'} and {REPORT_DIR / 'run_manifest.json'}"
        )

    print(
        f"\nImportant: WARIS config model version is v{MODEL_VERSION}. WARIS uses "
        "a hybrid design. Synthetic fallback fields keep "
        "the model runnable, while available live/source-backed enrichments are "
        "blended into selected risk proxies and documented in the live-status table. "
        "Governance artifacts document intended use, limitations, validation status, "
        "and monitoring controls. Source-confidence artifacts document field lineage, "
        "confidence levels, and replacement priorities. Ukrstat regional accounts "
        "artifacts now document a full transition from metadata discovery to "
        "validation-only official oblast GRP baseline candidates using the confirmed "
        "GRP.<REGION>._Z.A SDMX pattern. The official baseline validation module "
        "adds a staged readiness gate, the official baseline merge-plan module "
        "adds controlled benchmark-integration scenarios, the merge-review "
        "module summarizes official-vs-synthetic gaps and scenario recommendations, "
        "and the benchmark review memo explains the findings in plain language. "
        "The expanded Prozorro procurement module adds source-backed procurement "
        "feature artifacts and scoring candidates as review-only outputs with "
        "production_score_change=none. The wartime AML/CFT typology register adds "
        "literature-support typology references, and the official FIU/SFMS context "
        "module adds national source-support context and typology-support artifacts; "
        "both remain outside scoring and Monte Carlo. The official baseline "
        "merge-plan and merge-review modules now also create and review controlled "
        "context bridges for Prozorro, wartime typology, FIU/SFMS context, and "
        "operational-control artifacts. "
        "The current expected posture is benchmark-only within controlled benchmark "
        "integration, while risk-layer calculation and composite scoring remain "
        "prohibited until transformation logic, SME review, and scoring change "
        "control are complete. These official baseline candidates remain not_yet_used "
        "in scoring. The analyst review workflow converts model signals into "
        "human-review queue records, suggested review questions, and disposition "
        "templates without creating allegations, entity-level findings, or automated "
        "adverse-action recommendations. The false-positive control layer documents "
        "plausible benign explanations, review controls, and checklist items so analysts "
        "can avoid over-interpreting wartime disruption, procurement urgency, source gaps, "
        "or national-level context. The source freshness layer monitors artifact availability, "
        "row counts, file age, freshness status, and refresh priorities for major WARIS "
        "source, governance, and operational-control outputs. The visualization and PDF "
        "report now include operational-control coverage so analyst-review, false-positive, "
        "source-freshness, run-manifest, and operational bridge/review artifacts can be "
        "audited alongside source-context artifacts. A current-run manifest identity "
        "is refreshed before bridge/review artifacts are created, and the final run "
        "manifest is built before the PDF report so the report can show same-run "
        "version and manifest summary data. The run manifest records reproducibility metadata, source/artifact "
        "status, output inventory, validation posture, and no-adverse-action controls "
        "for each completed run. These controls improve transparency but do not make "
        "the model operationally validated."
    )

    # Keep references available for debuggers or future extension without changing output behavior.
    _ = oblast_crosswalk
    _ = governance_artifacts
    _ = analyst_review_artifacts
    _ = false_positive_artifacts
    _ = source_confidence_artifacts
    _ = source_freshness_artifacts
    _ = ukrstat_artifacts
    _ = official_baseline_validation_artifacts
    _ = official_baseline_merge_plan_artifacts
    _ = official_baseline_merge_review_artifacts
    _ = official_baseline_review_memo_artifacts
    _ = prozorro_procurement_artifacts
    _ = wartime_typology_artifacts
    _ = fiu_official_context_artifacts
    _ = run_manifest_artifacts
    _ = MODEL_VERSION


if __name__ == "__main__":
    main()
