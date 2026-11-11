> Historical documentation from the supplied publish ZIP. Artifact availability, successful-run and readiness claims below have not been certified for this public candidate. Use the root README for current instructions.

# WARIS - Ukraine Wartime AML Revenue Integrity Scoring Model

WARIS is a prototype public-source review-prioritization model for Ukraine wartime anti-money laundering (AML), financial-supervision, and revenue-integrity analysis. It is inspired by the idea that a multi-layered OSINT architecture used for protective intelligence can be adapted to financial-supervision review workflows.

Current project status: **model version 0.12.0**, with official Ukrstat GRP baseline candidates, official unit/scale evidence, a staged validation gate, controlled benchmark-integration merge-planning artifacts, controlled merge-review artifacts, a plain-language benchmark review memo documenting the current `benchmark_only` posture, expanded Prozorro procurement feature artifacts for review-only procurement-risk analysis, a wartime AML/CFT typology reference layer, official FIU/SFMS source-context artifacts, official-baseline-to-context bridge/review artifacts, analyst-review workflow artifacts, false-positive controls, source-freshness monitoring, run-manifest reproducibility artifacts, and official-baseline-to-operational-controls bridge/review artifacts.

> **Research prototype:** WARIS produces sector/oblast-level signals for human review. It does not identify misconduct, make adverse decisions, or replace professional AML, legal, supervisory, or investigative judgment.

Latest v0.12.0 runs use a stable same-run manifest identity. A current-run manifest is refreshed before bridge/review artifacts are created, then rebuilt before the PDF report so the dashboard, PDF, bridge/review outputs, and final manifest can reference the same run ID and model version.

## Purpose

The model asks:

> Which sectors and oblasts show wartime revenue-integrity patterns that may deserve enhanced AML or supervisory review?

WARIS does **not** accuse specific people, companies, institutions, sectors, or regions of wrongdoing. The model is intentionally **sector/oblast-level** and produces review-prioritization signals for trained human analysts.

The current version uses a **hybrid design**:

1. Synthetic fallback inputs keep the full pipeline runnable.
2. Live/source-backed public data enrichments are blended into selected risk proxies when available.
3. Official Ukrstat SDMX regional-account observations are pulled into **validation-only baseline candidate artifacts**.
4. A formal official-baseline validation module creates a staged readiness decision before any scoring integration.
5. A controlled merge-planning module compares official GRP against synthetic WARIS baselines without changing production scores.
6. A controlled merge-review module ranks official-vs-synthetic baseline gaps and recommends the current `benchmark_only` posture.
7. A benchmark review memo explains the validation, merge-planning, merge-review findings, and scoring prohibition in plain language.
8. Expanded Prozorro procurement features create review-only oblast and oblast-sector procurement feature candidates from public tender data.
9. Wartime AML/CFT typology artifacts convert literature-supported wartime typology themes into reference-only governance and future feature-design artifacts.
10. Official FIU/SFMS context artifacts document national reporting, referral, and typology-support context for source-confidence and governance review.
11. Official baseline context bridges compare benchmark context with Prozorro, wartime typology, FIU/SFMS, and operational-control artifacts for documentation only.
12. Analyst-review workflow artifacts convert WARIS signals into human-review queues, review questions, and disposition templates without creating allegations or automated decisions.
13. False-positive controls document benign explanations, review checks, and analyst safeguards.
14. Source-freshness artifacts monitor artifact availability, row counts, file age, freshness posture, and refresh priorities.
15. Run-manifest artifacts document reproducibility metadata, output inventory, git status, and no-scoring/no-adverse-action controls.
16. Each source connector, fallback condition, official-data transition step, validation gate, benchmark gate, review gate, memo artifact, procurement feature artifact, typology artifact, FIU/SFMS context artifact, operational-control artifact, context bridge, and scoring gate is documented in generated tables, the dashboard, governance artifacts, source-confidence artifacts, source-freshness artifacts, run-manifest artifacts, and the PDF report.

## Current official-data milestone

WARIS now has a working official Ukrstat regional-account transition pipeline.

The current Ukrstat workflow:

1. Discovers the `DF_REGIONAL_ACCOUNTS` SDMX dataflow.
2. Parses relevant DSD, codelist, registry-reference, and metadata artifacts.
3. Uses SDMX availability discovery to identify valid query values.
4. Confirms the official regional-account series pattern:

```text
GRP.<REGION>._Z.A
```

5. Pulls official GRP observation series for oblast-level regions.
6. Creates validation-only official oblast baseline candidates.
7. Validates official unit/scale evidence from Ukrstat Dataset Explorer exports.
8. Runs an official baseline validation gate.
9. Produces a readiness decision.
10. Creates controlled benchmark-integration merge-planning artifacts.
11. Creates controlled merge-review artifacts that summarize official-vs-synthetic gaps and scenario recommendations.
12. Creates a plain-language benchmark review memo.
13. Keeps all official baseline values out of WARIS scoring until transformation logic, SME review, and scoring change control are complete.

Current official baseline control posture:

```text
current_use_in_scoring = not_yet_used
official_baseline_used_in_scoring = False
official_baseline_readiness_decision = GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION
approved_current_use = controlled_benchmark_integration_only
prohibited_current_use = risk_layer_calculation_or_composite_scoring
unit_interpretation = million UAH
merge_review_recommended_current_posture = benchmark_only
benchmark_review_memo = official_baseline_benchmark_review_memo.md
```

Still required before any scoring blend:

- Review and approve transformation logic.
- Decide whether official GRP should remain benchmark-only, rescale synthetic revenue baselines, or replace oblast baselines.
- Resolve sector-allocation logic before any sector-level replacement.
- Obtain AML / banking-supervision / Ukraine economic-security SME review.
- Create scoring change-control approval before official values affect risk layers, risk bands, composite scores, or Monte Carlo simulations.

## Official baseline validation gate

WARIS now includes a formal validation gate for the official Ukrstat GRP oblast baseline candidate layer.

Run it directly with:

```bash
python -m src.official_baseline_validation
```

The current validation result is intentionally conservative:

```text
decision = GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION
approved_current_use = controlled_benchmark_integration_only
prohibited_current_use = risk_layer_calculation_or_composite_scoring
```

The validation module checks:

- Candidate artifact availability
- Expected 25-region coverage
- Ukrstat-to-WARIS geography mapping
- Scoring gate status
- Validation status
- Unit validation status
- Indicator code
- `NACE = _Z`
- Annual frequency
- Latest-period consistency
- Numeric/positive value sanity
- Endpoint evidence
- Confirmed-series parser evidence

Current expected validation posture:

Current validation checks include official baseline, Prozorro, wartime typology, FIU/SFMS, and operational-control no-scoring gates.

```text
latest expected checks = OBV-001 through OBV-022
operational_controls_context_bridge_check = OBV-021
operational_controls_scoring_gate_check = OBV-022
remaining blocker = transformation logic and SME review before scoring integration
overall readiness = ready_for_controlled_benchmark_integration
recommended integration decision = GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION
```

The validation gate creates a controlled separation between:

```text
official data exists
```

and:

```text
official data is approved for scoring
```

At the current project stage, official GRP values may support controlled benchmark integration, source-lineage review, and merge-review analysis only. The current review recommendation is `benchmark_only`.

## Official baseline controlled merge-planning layer

WARIS now includes a controlled, non-production merge-planning module:

```bash
python -m src.official_baseline_merge_plan
```

This module creates benchmark artifacts only. It does **not** alter production scoring tables, risk layers, risk bands, review rationales, or Monte Carlo score simulations.

The merge plan compares three scenarios:

```text
benchmark_only
rescale_revenue_baseline
replace_oblast_baseline
```

Generated artifacts:

- `outputs/tables/official_baseline_merge_plan.csv`
- `outputs/tables/official_baseline_benchmark_comparison.csv`
- `outputs/tables/official_baseline_rescale_scenario.csv`
- `outputs/tables/official_baseline_replace_oblast_baseline_scenario.csv`
- `outputs/tables/official_baseline_merge_readiness_summary.csv`

Current merge posture:

```text
approved_current_use = controlled_benchmark_integration_only
prohibited_current_use = risk_layer_calculation_or_composite_scoring
production_score_change = none
```

This creates a defensible bridge between "official data exists" and "official data is approved for scoring." At the current stage, official GRP may be compared against synthetic WARIS baselines, but it must not change any production score.

## Official baseline controlled merge-review layer

WARIS now includes a controlled, non-production merge-review module:

```bash
python -m src.official_baseline_merge_review
```

This module reviews the benchmark outputs created by the merge-planning layer. It does **not** alter production scoring tables, risk layers, risk bands, review rationales, or Monte Carlo score simulations.

Generated artifacts:

- `outputs/tables/official_baseline_gap_review.csv`
- `outputs/tables/official_baseline_scenario_recommendations.csv`
- `outputs/tables/official_baseline_merge_review_summary.csv`

The merge-review layer:

- Ranks oblasts by absolute official-vs-synthetic baseline gap.
- Classifies gaps as minimal, small, moderate, large, or very large.
- Identifies whether official GRP share is higher or lower than the synthetic baseline share.
- Summarizes scenario recommendations.
- Maintains `production_score_change = none`.

Current review posture:

```text
recommended_current_posture = benchmark_only
approved_current_use = controlled_benchmark_integration_only
prohibited_current_use = risk_layer_calculation_or_composite_scoring
production_score_change = none
```

This layer moves the project from “official data can be benchmarked” to “the benchmark has been reviewed and the current recommendation is to remain benchmark-only.”

## Official baseline benchmark review memo

WARIS now includes a plain-language benchmark review memo:

```bash
python -m src.official_baseline_review_memo
```

This memo is an analyst-facing documentation artifact. It summarizes the validation gate, merge-planning scenarios, merge-review findings, and current `benchmark_only` posture in plain language.

Generated artifact:

- `outputs/reports/official_baseline_benchmark_review_memo.md`

The memo documents:

- Current readiness decision
- Approved and prohibited current use
- Official unit and scale evidence
- Official-vs-synthetic benchmark gap findings
- Scenario recommendations
- Why official GRP is not scoring-ready
- Current recommendation
- Recommended next actions
- Governance note

Current memo posture:

```text
recommended_current_posture = benchmark_only
approved_current_use = controlled_benchmark_integration_only
prohibited_current_use = risk_layer_calculation_or_composite_scoring
production_score_change = none
```

The memo does **not** approve scoring integration. It is a review artifact for SME discussion, model change-control planning, GitHub/practitioner explanation, and future validation work.

## Expanded Prozorro procurement feature layer

WARIS now includes an expanded Prozorro procurement feature module:

```bash
python -m src.prozorro_procurement_features
```

This module pulls recent public Prozorro tender data and creates review-only procurement feature artifacts at the oblast and oblast-sector level.

Generated artifacts:

- `data/raw/prozorro_expanded_tenders_raw.csv`
- `data/raw/prozorro_expanded_tender_details_raw.csv`
- `data/raw/prozorro_expanded_feature_rows_raw.csv`
- `outputs/tables/prozorro_procurement_features_oblast.csv`
- `outputs/tables/prozorro_procurement_features_oblast_sector.csv`
- `outputs/tables/prozorro_procurement_scoring_candidates.csv`
- `outputs/tables/prozorro_procurement_feature_summary.csv`

The expanded procurement layer creates candidate features such as:

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

Current procurement feature posture:

```text
current_use = review_artifact_only
prohibited_use = direct_scoring_without_change_control
production_score_change = none
```

The expanded Prozorro layer does **not** accuse any buyer, supplier, oblast, or sector of misconduct. It is a review-support artifact intended to help compare source-backed procurement signals against the existing WARIS `procurement_awards_proxy` before any future governed scoring branch is considered.

Before the expanded Prozorro features can affect WARIS scoring, the project requires:

- Larger historical coverage review
- Buyer/address/oblast mapping validation
- Sector-mapping validation
- Bidder/supplier field validation
- Procurement and AML SME review
- False-positive controls
- Scoring change-control approval

## Wartime AML/CFT typology reference layer

WARIS now includes a wartime AML/CFT typology register:

```bash
python -m src.wartime_aml_typology_register
```

This module converts literature-supported wartime AML/CFT risk themes into transparent reference artifacts for model governance, source support, and future feature design.

Generated artifacts:

- `outputs/tables/waris_wartime_aml_typology_register.csv`
- `outputs/tables/waris_wartime_aml_typology_layer_map.csv`
- `outputs/tables/waris_wartime_aml_typology_summary.csv`

Current typology posture:

```text
current_use = literature_support_and_typology_reference_only
prohibited_use = direct_scoring_without_change_control
production_score_change = none
used_in_waris_scoring = False
used_in_monte_carlo = False
```

The typology register includes reference themes such as sanctions evasion, beneficial ownership opacity, reconstruction/emergency procurement misuse, humanitarian-flow misuse, digital asset finance, temporarily occupied territory exposure, IT-sector payment/cash-withdrawal typologies, individual entrepreneur account misuse, cash placement through intermediaries, and cross-border intelligence/sanctions-data integration gaps.

These typologies are **not measured risk indicators**. They do not accuse any person, company, sector, or oblast of misconduct. They do not alter WARIS risk layers, composite scores, risk bands, review rationales, or Monte Carlo simulations.

Before any typology can influence scoring, the project requires measurable indicator design, validated public-source data, SME review, false-positive controls, and model change-control approval.

## Official FIU/SFMS source-context layer

WARIS now includes an official FIU/SFMS context module:

```bash
python -m src.fiu_official_context
```

This module creates official source-support context artifacts from Ukrainian FIU/SFMS reporting, referral, and typology-support sources. The artifacts are national context for governance and source-confidence review. They are not direct oblast/sector scoring inputs.

Generated artifacts:

- `outputs/tables/waris_fiu_official_source_register.csv`
- `outputs/tables/waris_fiu_reporting_statistics_context.csv`
- `outputs/tables/waris_fiu_case_referral_context.csv`
- `outputs/tables/waris_fiu_typology_support_register.csv`
- `outputs/tables/waris_fiu_context_summary.csv`

Current FIU/SFMS posture:

```text
current_use = official_fiu_context_and_typology_support_only
prohibited_use = direct_scoring_without_change_control
production_score_change = none
used_in_waris_scoring = False
used_in_monte_carlo = False
```

The official FIU/SFMS context layer supports source documentation, typology comparison, and governance review. It does not create oblast, sector, entity, or person-level findings and does not alter WARIS risk layers, composite scores, risk bands, review rationales, or Monte Carlo simulations.

Before any FIU/SFMS context can affect scoring, WARIS would require measurable oblast/sector indicator design, source-validation logic, SME review, false-positive controls, and model change-control approval.

## Official baseline source-context bridge layer

WARIS now includes official-baseline-to-context bridge and review artifacts. These compare official baseline benchmark context with expanded Prozorro, wartime AML/CFT typology, official FIU/SFMS context, and operational-control artifacts for documentation and SME review only.

Generated bridge artifacts:

- `outputs/tables/official_baseline_prozorro_context_bridge.csv`
- `outputs/tables/official_baseline_wartime_typology_context_bridge.csv`
- `outputs/tables/official_baseline_fiu_context_bridge.csv`
- `outputs/tables/official_baseline_operational_controls_context_bridge.csv`

Generated review artifacts:

- `outputs/tables/official_baseline_prozorro_context_review.csv`
- `outputs/tables/official_baseline_wartime_typology_context_review.csv`
- `outputs/tables/official_baseline_fiu_context_review.csv`
- `outputs/tables/official_baseline_operational_controls_context_review.csv`

Current context-bridge posture:

```text
current_use = review_context_only
production_score_change = none
used_in_scoring = False
used_in_monte_carlo = False
```

Context bridges do not approve scoring integration. They are review artifacts that help explain how official baseline benchmark context may be compared with other source-context and operational-control layers while preserving source separation.

## Operational-control and human-review safeguards

WARIS now includes operational-control artifacts designed to make the prototype more auditable, safer to interpret, and easier to review.

These controls do **not** change WARIS scoring. They do **not** validate the model for operational use. They do **not** create entity-level findings or automated adverse-action recommendations.

### Analyst-review workflow

Run directly with:

```bash
python -m src.analyst_review_queue
```

Generated artifacts:

- `outputs/tables/analyst_review_queue.csv`
- `outputs/tables/analyst_review_questions.csv`
- `outputs/tables/review_disposition_template.csv`
- `outputs/tables/analyst_review_summary.csv`

Current posture:

```text
current_use = analyst_review_workflow_only
production_score_change = none
used_in_waris_scoring = False
used_in_monte_carlo = False
human_review_required = True
automated_adverse_action_allowed = False
entity_level_findings_allowed = False
```

### False-positive controls

Run directly with:

```bash
python -m src.false_positive_controls
```

Generated artifacts:

- `outputs/tables/false_positive_risk_register.csv`
- `outputs/tables/false_positive_controls.csv`
- `outputs/tables/false_positive_review_checklist.csv`
- `outputs/tables/false_positive_summary.csv`

Current posture:

```text
current_use = human_review_support_only
production_score_change = none
used_in_waris_scoring = False
used_in_monte_carlo = False
```

### Source-freshness monitoring

Run directly with:

```bash
python -m src.source_freshness
```

Generated artifacts:

- `outputs/tables/source_freshness_inventory.csv`
- `outputs/tables/source_freshness_assessment.csv`
- `outputs/tables/source_freshness_replacement_priorities.csv`
- `outputs/tables/source_freshness_summary.csv`

Current posture:

```text
current_use = source_freshness_monitoring_only
production_score_change = none
used_in_waris_scoring = False
used_in_monte_carlo = False
```

### Run manifest and reproducibility

Run directly with:

```bash
python -m src.run_manifest
```

Generated artifacts:

- `outputs/tables/run_manifest.csv`
- `outputs/tables/run_manifest_summary.csv` - should show `model_version = 0.12.0` and `manifest_phase = final`
- `outputs/reports/run_manifest.json`

Current posture:

```text
current_use = run_manifest_documentation
production_score_change = none
used_in_waris_scoring = False
used_in_monte_carlo = False
```

The run manifest records generated artifacts, row counts, file sizes, git status, source/artifact status, validation posture, and no-scoring/no-adverse-action controls for each run.

The full pipeline now uses a stable run identity:

```text
manifest_phase = pre_context_bridge  # early current-run identity refresh
manifest_phase = final               # final manifest before PDF generation
model_version = 0.12.0
production_score_change = none
```

This prevents official-baseline bridge/review artifacts and the PDF report from accidentally referencing a previous run's manifest ID.

## Risk layers

WARIS calculates the following transparent risk layers:

- Revenue anomaly risk
- Sanctions exposure risk
- Procurement integrity risk
- Ownership opacity risk
- Trade-based money laundering risk
- Conflict plausibility gap
- Financial supervision exposure

The composite WARIS AML review score is a weighted score from `0` to `100`.

Official Ukrstat GRP baseline candidates are displayed for governance, validation, and source-lineage review only. They do **not** affect the risk layers, composite score, Monte Carlo simulation, risk band, or review rationale.

## Current public-source anchors

WARIS currently references or attempts to enrich from the following public/source-backed anchors and generated control artifacts:

- National Bank of Ukraine financial monitoring and supervision pages
- National Bank of Ukraine Developer API
- Prozorro procurement/open contracting data
- Ukraine NSDC State Register of Sanctions
- OpenSanctions Ukraine NSDC dataset
- OFAC Ukraine-/Russia-related sanctions references
- State Statistics Service of Ukraine
- State Statistics Service of Ukraine SDMX API and SDMX API v3 documentation
- Ukrstat `DF_REGIONAL_ACCOUNTS` / `DSD_REGIONAL_ACCOUNTS` official regional-account observations
- Ukrainian FIU/SFMS official reporting, referral, and typology context
- Literature-supported wartime AML/CFT typology references
- World Bank Ukraine fiscal, macroeconomic, import, and export indicators
- ACLED Ukraine conflict-event data when credentials are available

## Current live/source-backed enrichment connectors

The pipeline attempts source-backed enrichment while preserving synthetic fallback values when a source is unavailable.

Current connectors include:

| Source | Model layer supported | Current use |
|---|---|---|
| Prozorro recent tenders | Procurement integrity risk | Recent tender count/value proxy blended into procurement exposure |
| Prozorro expanded procurement features | Procurement integrity expanded features | Review-only oblast and oblast-sector procurement feature candidates; not blended into production scoring |
| ACLED Ukraine events | Conflict plausibility gap | Oblast-level conflict intensity proxy blended into conflict plausibility scoring |
| World Bank Ukraine fiscal context | Macroeconomic/fiscal context | National fiscal, GDP, import, and export context retained for source-backed framing |
| NBU financial-sector context | Financial supervision exposure | National financial-sector context adjustment for supervisory exposure proxy |
| Ukrstat SDMX dataflow discovery | Official economic baseline discovery | Official SDMX metadata, availability, and regional-account observation probes now produce validation-only oblast baseline candidates |
| Ukrstat regional accounts official baseline candidates | Official economic baseline candidate layer | 25 oblast-level GRP baseline candidates generated from official SDMX observations; not used in scoring |
| Official baseline validation gate | Official baseline scoring control | Produces GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION readiness decision, validation register, validation summary, geography check, and period coverage artifacts |
| Official baseline merge-planning artifacts | Controlled benchmark integration | Produces benchmark_only, rescale_revenue_baseline, and replace_oblast_baseline scenarios without changing production scores |
| Official baseline merge-review artifacts | Controlled benchmark review | Produces gap review, scenario recommendations, and merge-review summary while recommending benchmark_only as the current posture |
| Official baseline benchmark review memo | Controlled benchmark review documentation | Produces a plain-language memo explaining validation, merge-planning, merge-review findings, context-bridge controls, and scoring prohibition |
| Wartime AML/CFT typology register | Literature-supported typology context | Reference-only typology register and WARIS layer map; not used in production scoring |
| Official FIU/SFMS context artifacts | Official source-support context | National FIU/SFMS reporting, referral, and typology-support context; not used in production scoring |
| Official baseline context bridges and reviews | Controlled source-context bridge review | Review-only bridge artifacts comparing official baseline context with Prozorro, typology, FIU/SFMS, and operational-control context |
| Analyst-review workflow | Human-review support | Review queue, review questions, and disposition templates; not scoring inputs |
| False-positive controls | Human-review support | Benign-explanation and review-control documentation; not scoring inputs |
| Source-freshness monitoring | Source maintenance and refresh planning | Artifact availability, file age, row-count, freshness, and replacement-priority monitoring |
| Run manifest | Reproducibility and output inventory | Same-run manifest identity, run metadata, output inventory, git status, no-scoring/no-adverse-action controls |
| OpenSanctions Ukraine NSDC | Sanctions exposure risk | Machine-readable Ukraine NSDC sanctions source availability and sample coverage |

Generated live-status table:

- `outputs/tables/live_data_status.csv`

Raw source samples and audit files, when available, are saved under:

- `data/raw/prozorro_tender_list_raw.csv`
- `data/raw/prozorro_tender_details_raw.csv`
- `data/raw/prozorro_expanded_tenders_raw.csv`
- `data/raw/prozorro_expanded_tender_details_raw.csv`
- `data/raw/prozorro_expanded_feature_rows_raw.csv`
- `data/raw/acled_ukraine_events_raw.csv` (local connector output; excluded from
  version control under ACLED's data-use terms)
- `data/raw/acled_oblast_conflict_proxy.csv`
- `data/raw/world_bank_ukraine_context_raw.csv`
- `data/raw/nbu_financial_context_status.csv`
- `data/raw/nbu_bank_key_indicators_raw.csv`
- `data/raw/nbu_bank_income_expenses_raw.csv`
- `data/raw/nbu_loans_raw.csv`
- `data/raw/ukrstat_sdmx_dataflows_raw.json`
- `data/raw/ukrstat_sdmx_dataflows_raw.csv`
- `data/raw/ukrstat_oblast_baseline_candidates_audit.csv`
- `data/raw/opensanctions_ua_nsdc_sample_raw.csv`
- `data/raw/opensanctions_ua_nsdc_entities_sample.jsonl`
- `data/raw/oblast_sector_inputs_enriched.csv`
- `data/raw/oblast_name_crosswalk.csv`

## Run

Prerequisites:

- Python 3.11 or newer
- Internet access for live public-source enrichments
- Optional ACLED credentials for live conflict-event enrichment

Clone the repository, create an isolated environment, and install dependencies:

```bash
git clone https://github.com/jasonrkeen/waris-ukraine-aml-risk-model.git
cd waris-ukraine-aml-risk-model
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies and run the full pipeline:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

The pipeline remains runnable without private credentials by using documented
fallback inputs where a live connector is unavailable. Copy `.env.example` to
`.env` only when you want to configure optional live-source credentials or
overrides.

A successful v0.12.0 run should report:

```text
Model version: v0.12.0
Manifest phase: final
Config model version: 0.12.0
Manifest model version: 0.12.0
Production score change: none
```

Optional: regenerate only the Ukrstat official-baseline transition artifacts:

```bash
python -m src.ukrstat_observations
```

Optional: regenerate only the official baseline validation-gate artifacts:

```bash
python -m src.official_baseline_validation
```

Optional: regenerate only the official baseline controlled merge-planning artifacts:

```bash
python -m src.official_baseline_merge_plan
```

Optional: regenerate only the official baseline controlled merge-review artifacts:

```bash
python -m src.official_baseline_merge_review
```

Optional: regenerate only the official baseline benchmark review memo:

```bash
python -m src.official_baseline_review_memo
```

Optional: regenerate only the expanded Prozorro procurement feature artifacts:

```bash
python -m src.prozorro_procurement_features
```

Optional: regenerate only the wartime AML/CFT typology reference artifacts:

```bash
python -m src.wartime_aml_typology_register
```

Optional: regenerate only the official FIU/SFMS context artifacts:

```bash
python -m src.fiu_official_context
```

Optional: regenerate only the analyst-review workflow artifacts:

```bash
python -m src.analyst_review_queue
```

Optional: regenerate only the false-positive control artifacts:

```bash
python -m src.false_positive_controls
```

Optional: regenerate only the source-freshness monitoring artifacts:

```bash
python -m src.source_freshness
```

Optional: regenerate only the run-manifest artifacts:

```bash
python -m src.run_manifest
```

## Dashboard

```bash
streamlit run app.py
```

The dashboard displays:

- Filtered sector/oblast review signals
- Live/source-backed enrichment status
- Official Ukrstat baseline benchmark-integration gate
- Official baseline validation gate
- Official benchmark integration tab
- Official merge review tab
- Official review memo tab
- Prozorro procurement features tab
- Wartime AML typology tab
- Official FIU/SFMS context tab
- Context bridges tab
- Operational controls tab
- Readiness decision
- Validation summary
- Validation check register
- Geography crosswalk validation
- Period coverage validation
- Official unit and scale evidence
- Official baseline merge-readiness summary
- Official baseline merge-plan scenarios
- Official baseline merge-review summary
- Official baseline scenario recommendations
- Official-vs-synthetic gap review
- Official baseline benchmark review memo
- Expanded Prozorro procurement feature summary
- Oblast procurement feature candidates
- Oblast-sector procurement candidates
- Procurement scoring-candidate control table
- Wartime AML/CFT typology register
- Wartime AML/CFT typology layer map
- Official FIU/SFMS source register
- FIU/SFMS reporting statistics context
- FIU/SFMS case-referral context
- FIU/SFMS typology-support register
- Official baseline source-context bridge/review tables
- Official baseline operational-controls bridge/review tables
- Analyst review workflow artifacts
- False-positive controls
- Source-freshness monitoring artifacts
- Run-manifest reproducibility artifacts
- Benchmark-only comparison
- Rescale revenue baseline scenario
- Replace-oblast-baseline scenario
- Official Ukrstat baseline candidate table
- Ukrstat probe results
- Availability-derived value candidates
- Observation query plan
- Top WARIS review signals
- Oblast summary
- Sector summary
- Monte Carlo robustness results
- ACLED conflict proxy audit table when available
- Generated chart images

## Outputs

Core tables:

- `outputs/tables/waris_scored_oblast_sector.csv`
- `outputs/tables/waris_oblast_summary.csv`
- `outputs/tables/waris_sector_summary.csv`
- `outputs/tables/waris_monte_carlo_results.csv`
- `outputs/tables/source_register.csv`
- `outputs/tables/live_data_status.csv`
- `outputs/tables/oblast_name_crosswalk.csv`

Expanded Prozorro procurement feature tables:

- `outputs/tables/prozorro_procurement_features_oblast.csv`
- `outputs/tables/prozorro_procurement_features_oblast_sector.csv`
- `outputs/tables/prozorro_procurement_scoring_candidates.csv`
- `outputs/tables/prozorro_procurement_feature_summary.csv`
- `data/raw/prozorro_expanded_tenders_raw.csv`
- `data/raw/prozorro_expanded_tender_details_raw.csv`
- `data/raw/prozorro_expanded_feature_rows_raw.csv`

Wartime AML/CFT typology reference tables:

- `outputs/tables/waris_wartime_aml_typology_register.csv`
- `outputs/tables/waris_wartime_aml_typology_layer_map.csv`
- `outputs/tables/waris_wartime_aml_typology_summary.csv`

Official FIU/SFMS context tables:

- `outputs/tables/waris_fiu_official_source_register.csv`
- `outputs/tables/waris_fiu_reporting_statistics_context.csv`
- `outputs/tables/waris_fiu_case_referral_context.csv`
- `outputs/tables/waris_fiu_typology_support_register.csv`
- `outputs/tables/waris_fiu_context_summary.csv`

Official baseline source-context and operational-control bridge/review tables:

- `outputs/tables/official_baseline_prozorro_context_bridge.csv`
- `outputs/tables/official_baseline_wartime_typology_context_bridge.csv`
- `outputs/tables/official_baseline_fiu_context_bridge.csv`
- `outputs/tables/official_baseline_operational_controls_context_bridge.csv`
- `outputs/tables/official_baseline_prozorro_context_review.csv`
- `outputs/tables/official_baseline_wartime_typology_context_review.csv`
- `outputs/tables/official_baseline_fiu_context_review.csv`
- `outputs/tables/official_baseline_operational_controls_context_review.csv`

Official baseline validation-gate tables:

- `outputs/tables/official_baseline_validation_register.csv`
- `outputs/tables/official_baseline_validation_summary.csv`
- `outputs/tables/official_baseline_geography_crosswalk_check.csv`
- `outputs/tables/official_baseline_period_coverage.csv`
- `outputs/tables/official_baseline_readiness_decision.csv`
- `outputs/tables/official_baseline_unit_evidence.csv`
- `outputs/tables/official_baseline_unit_evidence_summary.csv`
- `data/raw/official_baseline_validation_audit.csv`

Official baseline controlled merge-planning tables:

- `outputs/tables/official_baseline_merge_plan.csv`
- `outputs/tables/official_baseline_benchmark_comparison.csv`
- `outputs/tables/official_baseline_rescale_scenario.csv`
- `outputs/tables/official_baseline_replace_oblast_baseline_scenario.csv`
- `outputs/tables/official_baseline_merge_readiness_summary.csv`

Official baseline controlled merge-review tables:

- `outputs/tables/official_baseline_gap_review.csv`
- `outputs/tables/official_baseline_scenario_recommendations.csv`
- `outputs/tables/official_baseline_merge_review_summary.csv`

Official baseline benchmark review memo:

- `outputs/reports/official_baseline_benchmark_review_memo.md`

Ukrstat official-baseline transition tables:

- `outputs/tables/ukrstat_regional_accounts_dimensions.csv`
- `outputs/tables/ukrstat_regional_accounts_codelists.csv`
- `outputs/tables/ukrstat_regional_accounts_metadata_clues.csv`
- `outputs/tables/ukrstat_registry_references.csv`
- `outputs/tables/ukrstat_dsd_dimension_candidates.csv`
- `outputs/tables/ukrstat_dimension_code_candidates.csv`
- `outputs/tables/ukrstat_observation_query_candidates.csv`
- `outputs/tables/ukrstat_availability_discovery_results.csv`
- `outputs/tables/ukrstat_availability_value_candidates.csv`
- `outputs/tables/ukrstat_observation_probe_results.csv`
- `outputs/tables/ukrstat_observation_matrix_probe_results.csv`
- `outputs/tables/ukrstat_confirmed_series_probe_results.csv`
- `outputs/tables/ukrstat_confirmed_series_parsed.csv`
- `outputs/tables/ukrstat_confirmed_oblast_baseline_candidates.csv`
- `outputs/tables/ukrstat_oblast_baseline_probe_results.csv`
- `outputs/tables/ukrstat_oblast_baseline_candidates.csv`
- `outputs/tables/ukrstat_observation_query_plan.csv`

Ukrstat raw/audit outputs:

- `data/raw/ukrstat_regional_accounts_discovery_raw.csv`
- `data/raw/ukrstat_regional_accounts_structure_raw.json`
- `data/raw/ukrstat_regional_accounts_structure_paths_raw.csv`
- `data/raw/ukrstat_regional_accounts_structure_attempts.csv`
- `data/raw/ukrstat_dsd_regional_accounts_6_raw.json`
- `data/raw/ukrstat_dsd_regional_accounts_6_paths_raw.csv`
- `data/raw/ukrstat_dsd_regional_accounts_6_references_raw.json`
- `data/raw/ukrstat_dsd_regional_accounts_6_references_paths_raw.csv`
- `data/raw/ukrstat_confirmed_series_response_raw.json`
- `data/raw/ukrstat_oblast_baseline_success_responses/`

Governance and source-confidence tables:

- `outputs/tables/model_inventory.csv` - should show `model_version = 0.12.0`
- `outputs/tables/model_limitations_register.csv`
- `outputs/tables/model_validation_checklist.csv`
- `outputs/tables/model_monitoring_plan.csv`
- `outputs/tables/model_governance_summary.csv`
- `outputs/tables/field_source_register.csv`
- `outputs/tables/source_confidence_assessment.csv`
- `outputs/tables/source_confidence_summary.csv`

The governance and source-confidence artifacts now also summarize the official baseline validation gate, unit/scale evidence, controlled merge-planning artifacts, controlled merge-review artifacts, the benchmark review memo, expanded Prozorro procurement feature artifacts, wartime AML/CFT typology artifacts, official FIU/SFMS context artifacts, official baseline source-context bridge/review artifacts, operational-control artifacts, the `GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION` readiness decision, the `benchmark_only` recommendation, and the approved/prohibited current-use boundaries.

Operational-control, source-freshness, and run-manifest tables:

- `outputs/tables/analyst_review_queue.csv`
- `outputs/tables/analyst_review_questions.csv`
- `outputs/tables/review_disposition_template.csv`
- `outputs/tables/analyst_review_summary.csv`
- `outputs/tables/false_positive_risk_register.csv`
- `outputs/tables/false_positive_controls.csv`
- `outputs/tables/false_positive_review_checklist.csv`
- `outputs/tables/false_positive_summary.csv`
- `data/raw/operational_review_artifact_crosswalk.csv`
- `outputs/tables/operational_review_artifact_crosswalk.csv`
- `outputs/tables/source_freshness_inventory.csv`
- `outputs/tables/source_freshness_assessment.csv`
- `outputs/tables/source_freshness_replacement_priorities.csv`
- `outputs/tables/source_freshness_summary.csv`
- `outputs/tables/run_manifest.csv`
- `outputs/tables/run_manifest_summary.csv`
- `outputs/reports/run_manifest.json`

Charts:

- `outputs/charts/top_waris_risks.png`
- `outputs/charts/top_layer_profile.png`
- `outputs/charts/oblast_summary.png`
- `outputs/charts/conflict_intensity_summary.png`
- `outputs/charts/live_source_status.png`
- `outputs/charts/ukrstat_official_baseline_candidates.png`
- `outputs/charts/ukrstat_official_baseline_validation_status.png`
- `outputs/charts/source_context_artifact_coverage.png`
- `outputs/charts/wartime_aml_typology_family_distribution.png`
- `outputs/charts/fiu_context_artifact_coverage.png`
- `outputs/charts/official_baseline_context_review_coverage.png`
- `outputs/charts/operational_controls_artifact_coverage.png`

Report:

- `outputs/reports/waris_ukraine_aml_risk_report.pdf`
- `outputs/reports/official_baseline_benchmark_review_memo.md`

The PDF report now includes expanded Prozorro procurement, wartime AML/CFT typology, official FIU/SFMS context, official baseline source-context bridge/review, and operational-controls appendices when the artifacts are available.

If the default PDF is open or locked, the report generator may create a timestamped PDF such as:

- `outputs/reports/waris_ukraine_aml_risk_report_YYYYMMDD_HHMMSS.pdf`

## Environment variables

WARIS can run without credentials because synthetic fallback values remain active. Some live enrichment sources require credentials or optional overrides.

### ACLED credentials

ACLED uses OAuth username/password authentication.

Create a `.env` file in the project root:

```env
ACLED_USERNAME=your_myacled_email_here
ACLED_PASSWORD=your_myacled_password_here
```

The simplest setup is to copy `.env.example` to `.env`, then replace only the
values you intend to use. The project explicitly loads `.env` from the same
folder as `main.py`. Never commit `.env`; it is excluded by `.gitignore`.

### NBU report date override

The NBU connector defaults to:

```env
NBU_REPORT_DATE=20240101
```

You may override the date in `.env`:

```env
NBU_REPORT_DATE=20240101
```

Date format:

```text
yyyymmdd
```

### OpenSanctions pinned export URL

If the default OpenSanctions export path changes, set a pinned export URL:

```env
OPENSANCTIONS_UA_NSDC_URL=https://.../entities.ftm.json
```

or, when using a CSV export:

```env
OPENSANCTIONS_UA_NSDC_URL=https://.../entities.csv
```

## Model design notes

### Synthetic fallback layer

The model begins with synthetic oblast/sector observations so the full pipeline can run immediately. These fields are not claims of misconduct. They are placeholders that simulate the structure of expected inputs:

- Prewar revenue index
- Current revenue index
- Conflict intensity proxy
- Procurement awards proxy
- Sanctions counterparty proxy
- Ownership opacity proxy
- Trade dislocation proxy
- Financial supervision proxy

### Live/source-backed enrichment layer

When available, live/source-backed enrichments are blended into selected proxy fields. This design preserves model stability while making the model progressively more source-backed.

Examples:

- Prozorro recent tender data partially adjusts procurement exposure.
- Expanded Prozorro procurement feature artifacts create review-only procurement candidates without changing scoring.
- ACLED data partially adjusts conflict intensity.
- NBU financial-sector availability modestly adjusts financial-supervision exposure.
- World Bank, Ukrstat, and OpenSanctions are retained for source-backed context and future layer expansion.

### Official Ukrstat baseline transition layer

The Ukrstat official baseline transition layer is a validation-only bridge from synthetic regional baseline assumptions toward official regional-account observations.

Current confirmed pattern:

```text
DF_REGIONAL_ACCOUNTS
DSD_REGIONAL_ACCOUNTS
GRP.<REGION>._Z.A
dimensionAtObservation=TIME_PERIOD
```

The current pipeline has produced official oblast-level baseline candidates using Ukrstat SDMX responses. These candidates are attached to scored, summary, Monte Carlo, dashboard, governance, source-confidence, and report artifacts as context only.

The official baseline validation gate currently returns:

```text
decision = GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION
approved_current_use = controlled_benchmark_integration_only
prohibited_current_use = risk_layer_calculation_or_composite_scoring
```

They are not used in scoring because the remaining blocker is scoring integration change control:

- Transformation logic review
- Scenario-selection decision: benchmark-only, rescale, or replace-oblast-baseline
- Sector allocation logic if any sector-level replacement is proposed
- SME review
- Scoring change-control approval

The current validation gate output documents the official baseline, Prozorro, wartime typology, FIU/SFMS, and operational-control no-scoring gates through `OBV-022`.

```text
latest expected checks = OBV-001 through OBV-022
operational_controls_context_bridge_check = OBV-021
operational_controls_scoring_gate_check = OBV-022
remaining blocker = transformation logic and SME review before scoring integration
```

The current merge-review output recommends:

```text
recommended_current_posture = benchmark_only
rescale_revenue_baseline = sensitivity review only
replace_oblast_baseline = not recommended for scoring now
production_score_change = none
```

The benchmark review memo summarizes those findings for analyst and SME review:

```text
memo = outputs/reports/official_baseline_benchmark_review_memo.md
memo_use = controlled review artifact only
scoring_approval = no
```

### Wartime AML/CFT typology reference layer

The wartime AML/CFT typology register is a reference layer. It translates wartime AML/CFT themes into transparent documentation artifacts and future feature-design ideas. It is not a scoring layer.

Current controls:

```text
current_use = literature_support_and_typology_reference_only
prohibited_use = direct_scoring_without_change_control
production_score_change = none
used_in_waris_scoring = False
used_in_monte_carlo = False
```

### Official FIU/SFMS context layer

The FIU/SFMS context layer is an official source-support layer. It documents national reporting, referral, and typology-support context for governance and source-confidence review. It is not an oblast/sector scoring layer.

Current controls:

```text
current_use = official_fiu_context_and_typology_support_only
prohibited_use = direct_scoring_without_change_control
production_score_change = none
used_in_waris_scoring = False
used_in_monte_carlo = False
```

### Official baseline source-context bridge layer

The bridge layer creates review-only comparisons between official baseline benchmark context and other context/control layers such as Prozorro, wartime typology, FIU/SFMS context, and operational controls. It is designed to help analysts understand source relationships without merging the layers into scoring.

Current controls:

```text
production_score_change = none
used_in_scoring = False
used_in_monte_carlo = False
```

### Operational-control layer

The operational-control layer documents human-review and governance safeguards. It includes analyst-review workflow artifacts, false-positive controls, source-freshness monitoring, run-manifest reproducibility artifacts, and an official-baseline-to-operational-controls bridge/review layer.

Current controls:

```text
analyst_review_current_use = analyst_review_workflow_only
false_positive_controls_current_use = human_review_support_only
source_freshness_current_use = source_freshness_monitoring_only
run_manifest_current_use = run_manifest_documentation
production_score_change = none
used_in_waris_scoring = False
used_in_monte_carlo = False
human_review_required = True
automated_adverse_action_allowed = False
entity_level_findings_allowed = False
```

Operational-control artifacts support review discipline, transparency, and reproducibility. They do not validate the model, approve scoring integration, create allegations, or authorize automated adverse action.

### ACLED conflict proxy

The ACLED conflict proxy uses an oblast-level aggregation of event count and fatalities. The current implementation uses `log1p` transformations before scaling so that very high-activity oblasts do not overwhelm every other oblast.

The proxy is saved to:

- `data/raw/acled_oblast_conflict_proxy.csv`

### Monte Carlo robustness

WARIS includes Monte Carlo robustness testing. The simulation perturbs:

- Risk-layer weights using a Dirichlet distribution centered on the base weights
- Risk-layer values using modest normally distributed noise

Generated fields include:

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

Official baseline, wartime typology, and FIU/SFMS fields may appear in Monte Carlo output as governance context, but:

```text
official_baseline_used_in_monte_carlo = False
wartime_aml_typology_used_in_monte_carlo = False
fiu_context_used_in_monte_carlo = False
analyst_review_used_in_monte_carlo = False
false_positive_controls_used_in_monte_carlo = False
source_freshness_used_in_monte_carlo = False
run_manifest_used_in_monte_carlo = False
operational_controls_used_in_monte_carlo = False
```

## Governance warning

This is a research prototype. Do not use it for operational decisions without:

1. Replacing or validating synthetic revenue and proxy fields with official/public-source extracts.
2. Creating and maintaining a source register for each field.
3. Validating Ukrstat official baseline units, `NACE = _Z` meaning, geography mapping, indicator meaning, period coverage, benchmark-review findings, transformation logic, expanded Prozorro coverage/mapping quality, wartime AML/CFT typology measurable-indicator design, FIU/SFMS context source-to-indicator design, and SME approval.
4. Validating weights with AML, banking-supervision, sanctions, procurement, Ukraine economic-security, and conflict-risk subject-matter experts.
5. Documenting false-positive risk, analyst review procedures, and appeal/correction mechanisms.
6. Maintaining source-freshness monitoring and run-manifest reproducibility controls.
7. Keeping operational-control artifacts outside scoring unless a future governed scoring branch explicitly approves a different use.
8. Keeping all outputs at review-prioritization level unless independently verified by lawful investigative processes.
9. Avoiding entity-level accusation or automated adverse action.

## Data-use note

Live/source-backed fields are review-prioritization inputs only. Prozorro samples may be recent-only and incomplete. Expanded Prozorro procurement features are review-only candidate artifacts and are not production scoring inputs. Wartime AML/CFT typology artifacts are literature-support references only. Official FIU/SFMS artifacts are source-support context only. Official baseline context bridges and operational-controls bridge/review artifacts are review artifacts only. Analyst-review, false-positive, source-freshness, and run-manifest artifacts are operational controls only. ACLED requires credentials and may not represent every form of disruption. Sanctions datasets can change over time. NBU, Ukrstat, FIU/SFMS, typology references, and operational-control artifacts require careful mapping and change control before they are used as direct model features.

ACLED is the source of the conflict-event enrichment used by the connector.
The published sample accessed Ukraine data on June 30, 2026 and aggregates it
to an oblast-level conflict proxy. Raw ACLED event exports are intentionally
excluded from this repository; users must obtain their own authorized access
and comply with ACLED's current EULA and attribution policy.

Official Ukrstat GRP baseline candidates are official-source-backed and unit-supported for **controlled benchmark integration only**, but they are **not operationally validated** as scoring inputs. The current readiness decision is **GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION**, the current merge-review recommendation is **benchmark_only**, and the benchmark review memo documents the finding in plain language, while scoring integration remains prohibited. WARIS should present outputs as AML supervisory triage signals for human review, not findings of misconduct.

Source freshness may report `review_required` when an expected artifact is empty, missing, or stale. That posture is a governance signal for review and refresh planning, not a pipeline failure and not a scoring adjustment.

## License

The source code is available under the [MIT License](LICENSE). Public-source
datasets and generated extracts remain subject to their respective providers'
terms, attribution requirements, and redistribution rules.

## Recommended next build steps

- Review the benchmark review memo and controlled merge-review artifacts: official-vs-synthetic gap review, scenario recommendations, and merge-review summary.
- Keep the current recommendation at `benchmark_only` unless SME review and change-control evidence support another path.
- Use the rescale scenario only for sensitivity review unless transformation logic is formally approved.
- Do not use replace-oblast-baseline for scoring until sector-allocation logic is validated.
- Keep official GRP values excluded from scoring until transformation logic, SME review, and scoring change-control approval are documented.
- Add a formal model change log for any future scoring-integration branch.
- Validate expanded Prozorro features by reviewing coverage, buyer/oblast mapping, sector mapping, supplier/bid fields, procurement method fields, emergency/reconstruction exposure, and repeat-award logic.
- Review wartime AML/CFT typology artifacts for possible measurable indicator design while keeping them out of scoring.
- Review official FIU/SFMS context artifacts for source-confidence and typology support while keeping them out of scoring.
- Review official baseline context bridges and operational-controls bridge/review artifacts as documentation-only artifacts, not scoring integration approvals.
- Review analyst-review workflow artifacts to confirm review questions, disposition templates, and queue logic remain human-review support only.
- Review false-positive controls to ensure benign explanations and wartime disruption patterns are documented before any operational use.
- Maintain source-freshness monitoring and run-manifest reproducibility artifacts for each published run.
- Before publishing a release, confirm `run_manifest_summary.csv`, `model_inventory.csv`, the PDF report, dashboard, README, and CHANGELOG all reference `model_version = 0.12.0`.
- Map NBU financial-sector data into a more precise supervisory-exposure layer.
- Add broader sanctions-screening features using Ukraine NSDC, OpenSanctions, OFAC, EU, UK, and UN lists.
- Add analyst review notes and disposition examples.
- Maintain `CHANGELOG.md` for model versioning and change-control documentation.
- Keep operational-control artifacts outside scoring and Monte Carlo unless a future governed model-change branch explicitly approves another use.
