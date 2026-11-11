# WARIS rc13 selected historical appendix — local review 1

This package settles the proposed inclusion role and mandatory companions for the 23 conditionally eligible historical inventory entries. It contains **20 unique unchanged historical CSVs**, with three byte-identical aliases mapped rather than duplicated. This is a historical methods/benchmark appendix, separate from active pipeline data. It is not the full research release or a publication approval. Nothing was published or pushed.

Local unpublished preparation, 23 October 2026. Selected only for the historical appendix; not an active runtime input. GRP remains benchmark-only; sector-economic allocation, scoring and Monte Carlo integration are unapproved. Expanded procurement remains review-only; unverified FIU claims are excluded. Historical status/latest/pass/fresh labels are recorded text, not current verification, operational effectiveness or release approval. These scope labels describe WARIS use and impose no additional restriction on CC-licensed content.

## Selected files and mandatory reading

Read [attribution and scope](ATTRIBUTION_AND_SCOPE.md), each table's linked companion and all mandatory files named by that companion. [INCLUSION_PLAN.json](INCLUSION_PLAN.json) is the machine-readable selection/companion authority, [INCLUSION_LIST.csv](INCLUSION_LIST.csv) maps all 23 original locations, and [the exclusion list](EXCLUDED_HISTORICAL_FILES.csv) retains all 152 historical exclusions. File identity, typed correction, provenance evidence, and methodological validity are separate questions. None of these entries is a current source-freshness or operational-performance result.

| ID | Historical CSV | Actual rows | Mandatory companion |
| --- | --- | ---: | --- |
| A01 | [oblast_name_crosswalk.csv](artifacts/methods/oblast_name_crosswalk.csv) | 25 | [methods](companions/A01.md) |
| A02 | [operational_review_artifact_crosswalk.csv](artifacts/methods/operational_review_artifact_crosswalk.csv) | 15 | [methods](companions/A02.md) |
| A03 | [prozorro_procurement_crosswalk.csv](artifacts/methods/prozorro_procurement_crosswalk.csv) | 101 | [methods](companions/A03.md) |
| A04 | [synthetic_oblast_sector_inputs.csv](artifacts/synthetic/synthetic_oblast_sector_inputs.csv) | 150 | [synthetic](companions/A04.md) |
| A05 | [analyst_review_summary.csv](artifacts/workflow/analyst_review_summary.csv) | 7 | [workflow](companions/A05.md) |
| A06 | [false_positive_controls.csv](artifacts/workflow/false_positive_controls.csv) | 7 | [workflow](companions/A06.md) |
| A07 | [false_positive_risk_register.csv](artifacts/methods/false_positive_risk_register.csv) | 7 | [methods](companions/A07.md) |
| A08 | [false_positive_summary.csv](artifacts/workflow/false_positive_summary.csv) | 8 | [workflow](companions/A08.md) |
| A09 | [model_monitoring_plan.csv](artifacts/methods/model_monitoring_plan.csv) | 22 | [methods](companions/A09.md) |
| A10 | [official_baseline_benchmark_comparison.csv](artifacts/benchmark/official_baseline_benchmark_comparison.csv) | 25 | [benchmark](companions/A10.md) |
| A11 | [official_baseline_geography_crosswalk_check.csv](artifacts/geography/official_baseline_geography_crosswalk_check.csv) | 25 | [geography](companions/A11.md) |
| A12 | [official_baseline_operational_controls_context_bridge.csv](artifacts/operational/official_baseline_operational_controls_context_bridge.csv) | 4 | [operational](companions/A12.md) |
| A13 | [official_baseline_period_coverage.csv](artifacts/benchmark/official_baseline_period_coverage.csv) | 1 | [benchmark](companions/A13.md) |
| A14 | [official_baseline_rescale_scenario.csv](artifacts/illustrative_scenario/official_baseline_rescale_scenario.csv) | 150 | [illustrative_scenario](companions/A14.md) |
| A15 | [ukrstat_confirmed_oblast_baseline_candidates.csv](artifacts/historical_extraction/ukrstat_confirmed_oblast_baseline_candidates.csv) | 1 | [historical_extraction](companions/A15.md) |
| A16 | [ukrstat_confirmed_series_parsed.csv](artifacts/historical_extraction/ukrstat_confirmed_series_parsed.csv) | 18 | [historical_extraction](companions/A16.md) |
| A17 | [ukrstat_oblast_baseline_candidates.csv](artifacts/historical_extraction/ukrstat_oblast_baseline_candidates.csv) | 25 | [historical_extraction](companions/A17.md) |
| A18 | [ukrstat_observation_query_candidates.csv](artifacts/metadata/ukrstat_observation_query_candidates.csv) | 67 | [metadata](companions/A18.md) |
| A19 | [ukrstat_regional_accounts_metadata_clues.csv](artifacts/metadata/ukrstat_regional_accounts_metadata_clues.csv) | 7 | [metadata](companions/A19.md) |
| A20 | [ukrstat_registry_references.csv](artifacts/metadata/ukrstat_registry_references.csv) | 12 | [metadata](companions/A20.md) |

The original data/raw crosswalk copies and outputs/tables copies share hashes. Their three aliases map to one file each. The original synthetic input file is clearly under artifacts/synthetic with a mandatory synthetic companion; every numeric field is simulated. The coverage CSV is one summary row counting 25 regions, not 25 rows. The non-production rescale scenario is an arbitrary-index arithmetic example, not validated sector allocation or GRP scoring. Original blank metadata, pending labels, source locators, dates, control flags and recommendations remain historical text.

## Companion closure and reproduction limits

Every release-required public companion is bundled, including the exact unchanged rc13 source/configuration ZIP, selected typed unit/period/source-note tables, dated government attribution, selected acquisition/metadata receipts and workflow recounts. Sources and transformations are bound in [SOURCE_COMPONENTS.json](SOURCE_COMPONENTS.json). Companion tables are supporting material with separate identities; they do not change the 175-row historical inventory or approve unselected replacement files. The embedded source ZIP has model version 0.12.0 and rc13 code baseline; this appendix is a separate packaging revision with no runtime change. Its retained older history documents do not override current rc13 gates.

The bundle allows public byte-integrity, alias/companion closure and selected arithmetic checks. It does not reproduce the original HTTP acquisition or full research run: authorised private raw snapshots, missing historical request receipts, final source/methodology decisions and complete research execution remain separate gates. Public source URLs are references, not an instruction or permission to reacquire data. No new source retrieval or terms review was performed here.

Run the standard-library integrity/closure check from this extracted folder: `python tools/validate_selection.py`. It checks the manifest and declared files; it does not authenticate providers, validate the model or grant rights. Tests of this checker run with `python -m unittest discover -s tools -p test_selection.py`.

## Still outside the settled subset

This selection covers the 23 historical entries only. Fresh reviewed procurement study outputs, other typed corrections, selected literature, national context projections and final charts/PDF each retain separate inclusion decisions. Do not import excluded old score tables, ranked queues, images, unverified FIU claims or provider caches. Full-release work still needs an exact overall component list, remaining source/methodology gates, a qualifying frozen run/replay, final output QA, refreshed dependency/security checks and intended-platform evidence. Publication needs a later instruction.
