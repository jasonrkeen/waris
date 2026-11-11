## Unpublished rc13 methodology review — 2026-10-22

Replace numeric confidence averaging with categorical declarations, recognise Medium-High and keep Unknown separate. Retire the unvalidated ACLED event/fatality proxy and synthetic blend. Add a private sample inspector with exact aliases and explicit absence/missingness. Live acquisition stays gated. Synthetic model formulas, weights, seed and Monte Carlo draws remain unchanged. No full-release approval.

## Unpublished rc12 controlled review — 2026-10-22

Integrated explicit-label GRP parsing, strict non-scoring review flags, format-aware structure monitoring, confidence-label rejection, and rescale-support checks. ACLED acquisition/cache use is gated while provenance and output rights remain unresolved. No scoring-formula, weight, seed, or model-version change. Existing FIU exclusion and GRP benchmark boundaries remain.

# Public candidate continuation

## 0.12.0-rc5 unreleased

Withhold six unchecked annual/mixed FIU typology claims and the ambiguous quarterly metric from report context tables; retain internal records and report withheld counts. Missing or wrong-period/semantic verification fails closed. Correct blank period/interpretation columns and add visible quarterly citations. Record statutory Prozorro open-data reuse basis and individual artifact limitations. Add pytest coverage and pinned development tools; runtime lock, acquisition policy and core scoring are unchanged. Nothing published.

# Public candidate continuation

## 0.12.0-rc4 unreleased reference review candidate

Added official FIU quarterly URLs, page locators and numeric-reference annotations that flag changed/unknown values. Kept annual-report claims unverified and flagged the inherited 99.92 percent label/denominator. Added publisher DOI/license metadata for conceptual typologies, indicator-specific World Bank license records, third party notices and full research assembly guidance. No core score, simulation, weight, acquisition-policy or source-boundary change. Full research release remains blocked.

## Preserved prior history

# Public candidate continuation

## 0.12.0-rc3 unreleased review candidate

NBU acquisition policy `nbu-query-repair-1` corrects the income/expense endpoint to banksincexp and adds period=m for main-indicator and income/expense requests. Query date, scoring formulas, weights and protected source boundaries remain unchanged. The repair changes retrieval availability and therefore can change the legacy NBU-based score input. A controlled fixture showed approximately +0.3333 composite points and two band crossings among 150 synthetic records. This is disclosed for review and is not operational validation or publication approval. Owner confirms MIT intent and account credential rotation; the existing Research-1 local credential file remains stale and was not used. Historical core numerical replay passed separately against frozen enriched inputs; full live/source collection replay remains pending.

## Preserved earlier candidate history

# Public candidate continuation

## 0.12.0-rc2 unreleased

Fixed source-unavailable benchmark handling without changing score formulas or weights. Missing-input notices no longer count as benchmark observations. Official observation consumers reject blank, invalid, nonfinite, nonpositive or undated rows. Readiness fails closed on missing core evidence or incomplete registers, and even an all-pass register cannot authorize scoring in this release. Benchmark memos report current evidence rather than a fixed milestone claim. Current synthetic baselines and readiness precede consumers; final inventory is refreshed after PDF creation. Added missing/malformed-data, valid benchmark, stale-score precedence and full denied-network clean/rerun regression coverage. No publication or provider credentials used.

## Earlier candidate history

# Public candidate audit

## 0.12.0-rc1 unreleased

Packaging candidate retaining model 0.12.0 formulas and weights. Excluded all archived data and generated outputs; added a network-blocked synthetic demo, four regression tests, model card, data policy, guide assessment, limitations, security/contribution documentation and pinned dependency snapshot. Main research pipeline now requires explicit --allow-live; authentication response bodies are omitted; dashboard paths resolve from the project directory. Full research pipeline fallback has a confirmed stage-7 missing-benchmark failure and is not release-certified. Nothing published or pushed.

## Inherited development history

# Changelog

All notable changes to WARIS - Ukraine Wartime AML Revenue Integrity Scoring Model will be documented in this file.

The project follows a research-prototype versioning pattern. Version numbers mark model-development milestones, not operational validation.

## v0.12.0 - Operational controls, source freshness, run manifest, and human-review safeguards

### Added

- Added analyst-review workflow artifacts:
  - `outputs/tables/analyst_review_queue.csv`
  - `outputs/tables/analyst_review_questions.csv`
  - `outputs/tables/review_disposition_template.csv`
  - `outputs/tables/analyst_review_summary.csv`
- Added false-positive control artifacts:
  - `outputs/tables/false_positive_risk_register.csv`
  - `outputs/tables/false_positive_controls.csv`
  - `outputs/tables/false_positive_review_checklist.csv`
  - `outputs/tables/false_positive_summary.csv`
- Added source-freshness monitoring artifacts:
  - `outputs/tables/source_freshness_inventory.csv`
  - `outputs/tables/source_freshness_assessment.csv`
  - `outputs/tables/source_freshness_replacement_priorities.csv`
  - `outputs/tables/source_freshness_summary.csv`
- Added run-manifest and reproducibility artifacts:
  - `outputs/tables/run_manifest.csv`
  - `outputs/tables/run_manifest_summary.csv`
  - `outputs/reports/run_manifest.json`
- Added operational-review artifact crosswalk:
  - `data/raw/operational_review_artifact_crosswalk.csv`
  - `outputs/tables/operational_review_artifact_crosswalk.csv`
- Added official-baseline-to-operational-controls bridge and review artifacts:
  - `outputs/tables/official_baseline_operational_controls_context_bridge.csv`
  - `outputs/tables/official_baseline_operational_controls_context_review.csv`
- Added operational-control validation checks:
  - `OBV-021` Operational controls context bridge
  - `OBV-022` Operational controls scoring gate
- Added operational-control context fields to scored outputs, oblast summaries, sector summaries, Monte Carlo outputs, source-confidence outputs, source-freshness outputs, run-manifest outputs, report artifacts, and Streamlit dashboard views.
- Added operational-control chart:
  - `outputs/charts/operational_controls_artifact_coverage.png`
- Added operational-controls appendix to the PDF report.
- Added `Operational controls` tab to the Streamlit dashboard.
- Added operational-control coverage to `visualization.py`, `report_generator.py`, `main.py`, and `app.py`.
- Added shared utility helpers for artifact checks, standard summary-table lookups, non-scoring controls, compact counts, status normalization, and standard no-scoring notes.

### Updated

- Updated `config.py` to define shared current-use and production-score-change constants for analyst review, false-positive controls, source freshness, and run manifest artifacts.
- Updated `data_collection.py` to build an operational artifact crosswalk.
- Updated `risk_model.py` to attach operational-control context fields without changing WARIS score calculations.
- Updated `monte_carlo.py` to carry operational-control context without changing Monte Carlo calculations.
- Updated `live_data.py` to report operational-review/control artifact status.
- Updated `model_governance.py` to include analyst-review, false-positive, source-freshness, and run-manifest governance rows.
- Updated `source_confidence.py` to include operational-control lineage.
- Updated `source_freshness.py` to monitor operational-control, source-context, run-manifest, and bridge/review artifacts.
- Updated `run_manifest.py` to inventory operational-control artifacts and summarize their availability.
- Updated `official_baseline_merge_plan.py` to create the official-baseline-to-operational-controls context bridge.
- Updated `official_baseline_merge_review.py` to review the operational-controls context bridge.
- Updated `official_baseline_validation.py` to validate operational-control bridge availability and no-scoring gates.
- Updated `official_baseline_review_memo.py` to include operational-controls bridge/review findings and no-scoring interpretation.
- Updated `prozorro_procurement_features.py`, `ukrstat_observations.py`, and `wartime_aml_typology_register.py` to explicitly state separation from operational-control artifacts.
- Updated `visualization.py` to shorten the live/artifact coverage chart title and add operational-control coverage charting.
- Updated `report_generator.py` to include a dedicated operational-controls appendix and related how-to-read guidance.
- Updated `app.py` to show operational-control metrics, tables, charts, and bridge/review outputs.
- Updated `main.py` to run and report the operational-control chart and final output paths.

### Current posture

```text
analyst_review_current_use = analyst_review_workflow_only
analyst_review_production_score_change = none

false_positive_controls_current_use = human_review_support_only
false_positive_controls_production_score_change = none

source_freshness_current_use = source_freshness_monitoring_only
source_freshness_production_score_change = none

run_manifest_current_use = run_manifest_documentation
run_manifest_production_score_change = none

official_baseline_operational_controls_context_bridge_current_use = context_review_only
official_baseline_operational_controls_context_review_current_use = context_review_only

used_in_waris_scoring = False
used_in_monte_carlo = False
human_review_required = True
automated_adverse_action_allowed = False
entity_level_findings_allowed = False
```

### Notes

The analyst-review workflow converts WARIS outputs into human-review queues, review questions, and disposition templates. It does not create allegations, enforcement recommendations, entity-level findings, or automated adverse-action decisions.

The false-positive control layer documents plausible benign explanations, review controls, and checklist items so analysts can avoid over-interpreting wartime disruption, procurement urgency, source gaps, national-level context, or other non-suspicious explanations.

The source-freshness layer monitors artifact availability, row counts, file age, freshness status, and replacement priorities. Freshness monitoring supports source maintenance and documentation only. It does not validate analytical quality or approve scoring.

The run manifest records reproducibility metadata, output inventory, artifact status, git state, validation posture, and no-scoring/no-adverse-action controls for each run. It does not validate model accuracy or change model outputs.

The official-baseline-to-operational-controls bridge and review artifacts document whether operational safeguards exist alongside the official baseline benchmark package. They do not approve official baseline scoring integration.

This version strengthens governance, transparency, auditability, and human-review discipline while preserving the core WARIS boundary: production scoring remains unchanged and all operational-control artifacts remain outside scoring and Monte Carlo.


## v0.11.0 - Official FIU/SFMS context and wartime AML/CFT typology support

### Added

- Added `src.wartime_aml_typology_register`.
- Added literature-supported wartime AML/CFT typology artifacts:
  - `outputs/tables/waris_wartime_aml_typology_register.csv`
  - `outputs/tables/waris_wartime_aml_typology_layer_map.csv`
  - `outputs/tables/waris_wartime_aml_typology_summary.csv`
- Added `src.fiu_official_context`.
- Added official FIU/SFMS context artifacts:
  - `outputs/tables/waris_fiu_official_source_register.csv`
  - `outputs/tables/waris_fiu_reporting_statistics_context.csv`
  - `outputs/tables/waris_fiu_case_referral_context.csv`
  - `outputs/tables/waris_fiu_typology_support_register.csv`
  - `outputs/tables/waris_fiu_context_summary.csv`
- Added official-baseline-to-context bridge artifacts:
  - `outputs/tables/official_baseline_prozorro_context_bridge.csv`
  - `outputs/tables/official_baseline_wartime_typology_context_bridge.csv`
  - `outputs/tables/official_baseline_fiu_context_bridge.csv`
- Added official-baseline-to-context review artifacts:
  - `outputs/tables/official_baseline_prozorro_context_review.csv`
  - `outputs/tables/official_baseline_wartime_typology_context_review.csv`
  - `outputs/tables/official_baseline_fiu_context_review.csv`
- Added official baseline validation checks for wartime typology and FIU/SFMS context gates:
  - `OBV-017` Wartime AML typology context bridge
  - `OBV-018` Wartime AML typology scoring gate
  - `OBV-019` Official FIU/SFMS context bridge
  - `OBV-020` Official FIU/SFMS scoring gate
- Added FIU/SFMS and wartime typology context fields to scored outputs and summary outputs as governance/source-context fields only.
- Added FIU/SFMS and wartime typology controls to Monte Carlo, governance, source-confidence, validation, memo, PDF report, and Streamlit dashboard artifacts.
- Added new visualization outputs:
  - `outputs/charts/source_context_artifact_coverage.png`
  - `outputs/charts/wartime_aml_typology_family_distribution.png`
  - `outputs/charts/fiu_context_artifact_coverage.png`
  - `outputs/charts/official_baseline_context_review_coverage.png`
- Added new Streamlit dashboard tabs:
  - `Wartime AML typology`
  - `Official FIU/SFMS context`
  - `Context bridges`
- Added PDF report appendices for:
  - Wartime AML/CFT typology reference artifacts
  - Official FIU/SFMS context artifacts
  - Official baseline source-context bridge/review artifacts
- Updated `main.py` pipeline order so Prozorro, wartime typology, and FIU/SFMS artifacts are built before official baseline merge-plan, merge-review, validation, memo, reporting, and dashboard outputs.

### Current posture

```text
wartime_aml_typology_current_use = literature_support_and_typology_reference_only
wartime_aml_typology_prohibited_use = direct_scoring_without_change_control
wartime_aml_typology_production_score_change = none

fiu_context_current_use = official_fiu_context_and_typology_support_only
fiu_context_prohibited_use = direct_scoring_without_change_control
fiu_context_production_score_change = none

official_baseline_context_bridges_current_use = review_context_only
production_score_change = none
used_in_waris_scoring = False
used_in_monte_carlo = False
```

### Notes

The wartime AML/CFT typology register is a literature-support reference layer only. It is intended to support documentation, source-confidence review, feature planning, and SME discussion. It does not create measured oblast/sector indicators and does not alter WARIS risk layers, composite scores, risk bands, review rationales, or Monte Carlo simulations.

The official FIU/SFMS context layer is an official source-support context layer only. It documents national reporting, referral, and typology-support context. It does not create oblast, sector, entity, or person-level findings and does not alter WARIS risk layers, composite scores, risk bands, review rationales, or Monte Carlo simulations.

The official-baseline-to-context bridges are review artifacts only. They may help analysts compare official baseline benchmark context with expanded Prozorro, wartime typology, and FIU/SFMS context, but they do not approve scoring integration.

Before any wartime typology or FIU/SFMS context is allowed to affect scoring, the project requires measurable indicator design, source-validation logic, SME review, false-positive controls, model change-control approval, and updated governance/source-confidence documentation.


## v0.10.0 - Expanded Prozorro procurement feature layer

### Added

- Added `src.prozorro_procurement_features`.
- Added expanded Prozorro procurement feature artifacts:
  - `data/raw/prozorro_expanded_tenders_raw.csv`
  - `data/raw/prozorro_expanded_tender_details_raw.csv`
  - `data/raw/prozorro_expanded_feature_rows_raw.csv`
  - `outputs/tables/prozorro_procurement_features_oblast.csv`
  - `outputs/tables/prozorro_procurement_features_oblast_sector.csv`
  - `outputs/tables/prozorro_procurement_scoring_candidates.csv`
  - `outputs/tables/prozorro_procurement_feature_summary.csv`
- Added expanded Prozorro feature integration into the standard `python main.py` pipeline.
- Added expanded Prozorro feature status tracking in `live_data.py`.
- Added expanded Prozorro source-lineage tracking in `source_confidence.py`.
- Added expanded Prozorro procurement appendix coverage to the PDF report.
- Added a `Prozorro procurement features` tab to the Streamlit dashboard.
- Updated README documentation to include the expanded procurement feature layer.

### New candidate features

- Tender count
- Total expected value
- Mean expected value
- Single-bid or single-supplier proxy
- Buyer concentration
- Procurement method count
- Reconstruction/emergency keyword exposure
- CPV/category context where available
- Oblast mapping
- Sector mapping
- Oblast-sector procurement review-priority candidate score

### Current posture

```text
current_use = review_artifact_only
prohibited_use = direct_scoring_without_change_control
production_score_change = none
```

### Notes

The expanded Prozorro procurement layer is a source-backed review artifact only. It does not alter WARIS risk layers, composite scores, risk bands, review rationales, or Monte Carlo simulations.

The expanded procurement features do not accuse any buyer, supplier, oblast, or sector of misconduct. They are intended to support review-prioritization, source-lineage analysis, and future procurement-layer validation.

Before any scoring integration, the project requires broader coverage review, buyer/address/oblast mapping validation, sector-mapping validation, bidder/supplier field validation, procurement and AML SME review, false-positive controls, and model change-control approval.


## v0.9.0 - Official baseline benchmark review memo

### Added

- Added `src.official_baseline_review_memo`.
- Added the plain-language benchmark review memo artifact:
  - `outputs/reports/official_baseline_benchmark_review_memo.md`
- Added memo integration into the standard `python main.py` pipeline.
- Added memo coverage to the PDF report.
- Added memo display in the Streamlit dashboard.
- Added memo governance checks in `model_governance.py`.
- Added memo source-lineage tracking in `source_confidence.py`.
- Updated README documentation to include the benchmark review memo layer.

### Current posture

```text
recommended_current_posture = benchmark_only
approved_current_use = controlled_benchmark_integration_only
prohibited_current_use = risk_layer_calculation_or_composite_scoring
production_score_change = none
```

### Notes

The benchmark review memo is a controlled review artifact only. It does not approve scoring integration, operational use, automated adverse action, or entity-level conclusions.

## v0.8.0 - Controlled official baseline merge-review layer

### Added

- Added `src.official_baseline_merge_review`.
- Added controlled merge-review outputs:
  - `outputs/tables/official_baseline_gap_review.csv`
  - `outputs/tables/official_baseline_scenario_recommendations.csv`
  - `outputs/tables/official_baseline_merge_review_summary.csv`
- Added official-vs-synthetic baseline gap classification.
- Added scenario recommendations:
  - `benchmark_only`
  - `rescale_revenue_baseline`
  - `replace_oblast_baseline`
- Added merge-review integration into:
  - `main.py`
  - `report_generator.py`
  - `app.py`
  - `model_governance.py`
  - `source_confidence.py`
  - `README.md`

### Current finding

The merge-review layer recommends the current posture remain:

```text
benchmark_only
```

Official GRP values remain excluded from WARIS risk-layer calculation, composite scoring, risk bands, review rationales, and Monte Carlo simulations.

## v0.7.0 - Controlled official baseline merge-planning layer

### Added

- Added `src.official_baseline_merge_plan`.
- Added controlled benchmark-integration planning outputs:
  - `outputs/tables/official_baseline_merge_plan.csv`
  - `outputs/tables/official_baseline_benchmark_comparison.csv`
  - `outputs/tables/official_baseline_rescale_scenario.csv`
  - `outputs/tables/official_baseline_replace_oblast_baseline_scenario.csv`
  - `outputs/tables/official_baseline_merge_readiness_summary.csv`
- Added benchmark-only comparison between official Ukrstat GRP and synthetic WARIS revenue baselines.
- Added non-production rescale and replace-baseline scenarios.
- Preserved `production_score_change = none`.

### Notes

This version created the bridge between “official data exists” and “official data may be compared against synthetic baselines,” while still blocking scoring use.

## v0.6.0 - Official baseline validation gate

### Added

- Added `src.official_baseline_validation`.
- Added official baseline validation-gate outputs:
  - `outputs/tables/official_baseline_validation_register.csv`
  - `outputs/tables/official_baseline_validation_summary.csv`
  - `outputs/tables/official_baseline_geography_crosswalk_check.csv`
  - `outputs/tables/official_baseline_period_coverage.csv`
  - `outputs/tables/official_baseline_readiness_decision.csv`
  - `outputs/tables/official_baseline_unit_evidence.csv`
  - `outputs/tables/official_baseline_unit_evidence_summary.csv`
- Added formal readiness decision:
  - `GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION`
- Added approved/prohibited current-use language:
  - `approved_current_use = controlled_benchmark_integration_only`
  - `prohibited_current_use = risk_layer_calculation_or_composite_scoring`

### Notes

This version created the formal separation between official data being available and official data being approved for scoring.

## v0.5.0 - Ukrstat official GRP baseline candidate pipeline

### Added

- Added official Ukrstat regional-account transition artifacts.
- Confirmed the SDMX regional-account pattern:

```text
DF_REGIONAL_ACCOUNTS
DSD_REGIONAL_ACCOUNTS
GRP.<REGION>._Z.A
dimensionAtObservation=TIME_PERIOD
```

- Added official oblast-level baseline candidate outputs:
  - `outputs/tables/ukrstat_oblast_baseline_candidates.csv`
  - `outputs/tables/ukrstat_oblast_baseline_probe_results.csv`
  - `outputs/tables/ukrstat_confirmed_series_parsed.csv`
- Added official GRP context to scored outputs, summaries, Monte Carlo outputs, dashboard, governance, source-confidence, and report artifacts.

### Notes

Official baseline candidates were added as validation/reporting context only and were not used in scoring.

## v0.4.0 - Model governance and source-confidence artifacts

### Added

- Added model governance artifacts:
  - `outputs/tables/model_inventory.csv`
  - `outputs/tables/model_limitations_register.csv`
  - `outputs/tables/model_validation_checklist.csv`
  - `outputs/tables/model_monitoring_plan.csv`
  - `outputs/tables/model_governance_summary.csv`
- Added source-confidence and field-lineage artifacts:
  - `outputs/tables/field_source_register.csv`
  - `outputs/tables/source_confidence_assessment.csv`
  - `outputs/tables/source_confidence_summary.csv`

### Notes

This version improved transparency around intended use, prohibited use, field lineage, model limitations, and validation gaps.

## v0.3.0 - Monte Carlo robustness analysis

### Added

- Added Monte Carlo robustness testing.
- Added uncertainty outputs:
  - `mc_mean_score`
  - `mc_p05_score`
  - `mc_p95_score`
  - `mc_uncertainty_width`
  - `mc_mean_delta_from_base`
  - `prob_elevated_or_high`
  - `prob_high`
  - `robustness_band`
  - `uncertainty_band`
  - `signal_stability_flag`

### Notes

Monte Carlo outputs support model-review robustness analysis only. They do not convert WARIS into an operational prediction model.

## v0.2.0 - Live/source-backed enrichment layer

### Added

- Added optional live/source-backed enrichments while preserving synthetic fallback inputs.
- Added source status tracking:
  - `outputs/tables/live_data_status.csv`
- Added or expanded connectors and source-backed context for:
  - ACLED Ukraine conflict events
  - Prozorro procurement data
  - NBU financial-sector context
  - World Bank Ukraine macro/fiscal context
  - OpenSanctions Ukraine NSDC context
  - Ukrstat SDMX discovery

### Notes

Live/source-backed fields are used for review prioritization and context. Source availability, coverage limits, and fallback behavior are documented per run.

## v0.1.0 - Initial WARIS prototype

### Added

- Added initial sector/oblast-level synthetic fallback dataset.
- Added transparent AML/revenue-integrity risk layers:
  - Revenue anomaly risk
  - Sanctions exposure risk
  - Procurement integrity risk
  - Ownership opacity risk
  - Trade-based money laundering risk
  - Conflict plausibility gap
  - Financial supervision exposure
- Added composite WARIS AML review score.
- Added risk bands.
- Added initial charts and PDF report.

### Notes

The initial prototype was designed to be runnable without credentials or live-source availability. Scores were explicitly framed as review-prioritization signals only.

## Current prohibited uses

WARIS must not be used as:

- An accusation engine
- An enforcement trigger
- An automated adverse-action tool
- An entity-level finding
- A substitute for lawful investigative or supervisory process
- An operationally validated AML model without further review

## Current required controls before any scoring integration

Before official GRP, expanded Prozorro procurement features, wartime AML/CFT typology references, official FIU/SFMS context, operational-control artifacts, or other official/public-source values are allowed to affect WARIS scoring, the following are required:

1. Documented transformation logic.
2. SME review by AML, banking-supervision, sanctions, procurement, Ukraine economic-security, and relevant data experts.
3. Sector-allocation logic if oblast-level data is proposed for sector/oblast scoring.
4. Expanded procurement coverage, buyer/oblast mapping, sector mapping, supplier/bid field validation, and false-positive review.
5. Wartime typology measurable-indicator design and validation before any typology-to-score conversion.
6. Official FIU/SFMS context measurable oblast/sector indicator design before any FIU-context scoring use.
7. Sensitivity review of any rescale scenario.
8. Model change-control approval.
9. Updated governance and source-confidence artifacts.
10. Clear false-positive controls and analyst review procedures.
11. Source-freshness monitoring and run-manifest reproducibility controls.
12. Explicit review confirming operational-control artifacts remain documentation and human-review support only.
13. Continued prohibition on entity-level accusation unless independently verified through lawful processes.

## Unreleased candidate rc8

Repair UUID execution identity, complete eligible file hashes, ordered scoring/simulation input snapshots, post-PDF final sealing and tamper detection. Protected model parameters and scoring functions remain unchanged. Full research release remains on hold; unverified FIU claims remain excluded.

Rc9 literature curation withholds four detailed examples dependent on unverified SFMS evidence before public context export. Six general conceptual themes remain. See docs/LITERATURE_REFERENCE_SCOPE.md for attribution, adaptations and exclusions. Model formulas and source boundaries remain unchanged.

Rc9 also repairs the missing Zaporizhia geographic alias in the shared source normalizer. Acquisition policy is nbu-query-repair-1+oblast-alias-repair-1. This can change future live-source scores through existing input transformations; it does not change formulas/weights or historical frozen inputs. See docs/GEOGRAPHY_ALIAS_REPAIR.md.

## Unreleased 0.12.0-rc10

- Restore known nested procurement fields from cached CSVs with bounded JSON/literal parsing; reject malformed cells without evaluating code or echoing source contents.
- Normalize missing text for live/cache consistency. Historical text-length diagnostics are not reconstructed from lossy CSV missingness.
- Keep the acquisition policy, core scoring and protected source boundaries unchanged; expanded outputs remain review-only.

## Unreleased 0.12.0-rc11

- Preserve unknown bid/award supplier observations and three-valued combined flags; expose separate visible-field rates and coverage counts.
- Withhold internal candidates for sparse or incomplete-observation groups; retain missing candidates in projections, context bands, dashboard and PDF.
- Add a conservative minimum-support parameter (five unique tenders); all research tables retain a held publication status.
- Add a planned public-procurement capture tool with immutable new-directory inputs, per-attempt receipts, response hashes, whitelisted headers and fail-closed identity/redirect handling.
- Preserve core scoring formulas, weights, seed, simulations and protected source boundaries.

- Include tools/ in provenance source snapshots; test that a changed acquisition tool invalidates verification.
