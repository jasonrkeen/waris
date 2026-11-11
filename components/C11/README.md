# WARIS

Ukraine Wartime AML Revenue Integrity Scoring Model. **Unreleased public research candidate 0.12.0-rc11**, retaining model version 0.12.0.

WARIS demonstrates transparent sector/oblast review prioritization. It is a research prototype with synthetic assumptions and optional source-backed enrichments. Scores are not probabilities of money laundering, evidence of misconduct, operational validation, or grounds for adverse action.

## Run the public demonstration

Use Python 3.12 from this directory. Create and activate a virtual environment, then:

```text
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python offline_demo.py
python -m pytest -q
python -m streamlit run app.py
```

The demo runs without keys or network access. It builds synthetic inputs in an isolated temporary directory and writes five CSVs under `outputs/tables`, plus `outputs/reports/synthetic_demo_manifest.json`. Each CSV is marked `synthetic_only`. The manifest records seed, simulation count, runtime versions and output hashes. No historical data or historical PDF is bundled. Missing optional dashboard tabs indicate unavailable research artifacts, not validated controls. The demo does not build the full research PDF or all 22 research stages.

Only Windows Python 3.12 has been exercised locally. The supplied workflow is a proposed check for Windows and Linux; remote CI has not run. The dependency snapshot is pinned but does not include wheel hashes. Revalidate after dependency updates.

## Source boundaries

| Layer | Current permitted use |
| --- | --- |
| Official Ukrstat GRP | Benchmark context only; never risk-layer/composite-score or Monte Carlo input |
| Expanded Prozorro features | Review artifacts only |
| Wartime AML/CFT typologies | Literature/reference support only |
| FIU/SFMS | National source context only |
| Analyst workflow, false-positive, freshness, manifest artifacts | Human review/documentation only |

The historical `GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION` decision is not scoring approval and is not asserted for a new demo run. No sector allocation of official GRP is approved.

## Legacy research pipeline

`python main.py --allow-live` explicitly opts into provider requests and mixed-input research scoring. Obtain applicable provider permissions first. Configure credentials locally using `.env.example`; never commit `.env`, downloaded data, or generated outputs.

The legacy pipeline remains **not certified for a full public research release**. Its complete source-unavailable fallback now runs under tests with all provider access denied, including a rerun seeded with a stale scoring approval. Missing official evidence yields NO_GO, zero benchmark observations and no score changes. Successful authorized live execution and historical-output reproduction remain unverified. Basic Prozorro samples can blend into procurement scoring; ACLED can blend into conflict scoring; NBU endpoint availability can blend into financial-supervision scoring. These legacy behaviors are separate from the protected reference layers above and require methodological review. Synthetic fallback can create region/sector patterns by construction.

## Release status and documentation

Read [MODEL_CARD.md](MODEL_CARD.md), [DATA_POLICY.md](DATA_POLICY.md), [release limitations](docs/RELEASE_LIMITATIONS.md), and the [update-guide assessment](docs/UPDATE_GUIDE_ASSESSMENT.md). The archived [legacy README](docs/LEGACY_README.md) is historical documentation; its run-success and artifact-availability claims do not certify this candidate.

This candidate excludes all supplied raw data, processed data, charts, PDFs and generated tables pending provenance and redistribution clearance. MIT applies to the source code under the inherited [LICENSE](LICENSE); it does not license provider data. Nothing has been published, pushed, or tagged.


## NBU query repair under review

rc3 uses the documented `banksincexp` endpoint and monthly `period=m` for main-indicator and income/expense requests. The report date remains January 1, 2024. Research manifests identify acquisition policy `nbu-query-repair-1`. This is a score-affecting retrieval repair: under the legacy availability-based NBU heuristic, three working endpoints can raise composite scores by about 0.3333 compared with one working endpoint. Two records crossed review bands in the controlled synthetic sensitivity fixture. The heuristic itself is not substantively validated. rc2 and frozen historical inputs remain unchanged; use them for the verified historical numerical replay. Full authenticated live execution, provider rights and release approval remain pending.

## Full research release preparation

rc4 records official quarterly FIU source URLs and value checks, exposes annual-report verification gaps and the FIU-STAT-006 interpretation caveat, and adds conceptual literature source metadata. It does not alter core formulas, weights or acquisition policy. See [third party notices](THIRD_PARTY_NOTICES.md), [reference checks](docs/REFERENCE_CHECKS.md) and [full research assembly](docs/FULL_RESEARCH_ASSEMBLY.md). The full research release remains on hold pending the documented evidence, rights, live-run, replay and report-review gates.

## rc5 reference and permission continuation

The FIU report tables now withhold unsupported annual claims and the ambiguous quarterly metric while retaining internal evidence records. Missing qualifying reference annotations fail closed. The report's period/notes columns and quarterly citations are corrected. Core scoring, simulations, weights and acquisition policy are unchanged. The updated Prozorro permission basis and per-file holds are documented in docs/PROZORRO_PERMISSION_SCOPE.md. The full research release remains on hold. Tests use the pinned requirements-dev.txt snapshot and pytest; runtime requirements.lock.txt is unchanged.

Rc6 withholds unsupported FIU claims before context export, including indirect summaries and memo text. Regenerate all outputs in a fresh directory; historical outputs are not repaired by updating source. See [artifact clearance and replay](docs/ARTIFACT_CLEARANCE_AND_REPLAY.md).

Rc8 repairs execution identity, complete file hashing, captured scoring/simulation inputs and final provenance seals. See [run provenance](docs/RUN_PROVENANCE.md). Verify a completed research run with `python -m src.provenance --verify`; this checks integrity, not permissions or model validity.

Rc9 literature curation withholds four detailed examples dependent on unverified SFMS evidence before public context export. Six general conceptual themes remain. See docs/LITERATURE_REFERENCE_SCOPE.md for attribution, adaptations and exclusions. Model formulas and source boundaries remain unchanged.

Rc9 also repairs the missing Zaporizhia geographic alias in the shared source normalizer. Acquisition policy is nbu-query-repair-1+oblast-alias-repair-1. This can change future live-source scores through existing input transformations; it does not change formulas/weights or historical frozen inputs. See docs/GEOGRAPHY_ALIAS_REPAIR.md.

## Procurement cache replay repair

rc10 restores nested JSON or legacy literal CSV fields before expanded procurement extraction, rejects invalid cells without evaluating code, and normalizes missing text consistently. See [the replay review](docs/PROCUREMENT_CACHE_REPLAY.md). This repairs review-artifact reproducibility; historical acquisition dates, sample completeness, missing-bid semantics and individual publication decisions remain separate. Core WARIS scoring and the protected FIU/GRP boundaries are unchanged.

## Procurement observation and acquisition controls

rc11 preserves unavailable bid/award counts and rates, records visible-observation denominators, and withholds internal review candidates below five unique tenders or with incomplete bid/supplier observations. All regional/sector tables still require individual public-release review. The dashboard and PDF retain missing values. A separate bounded public API capture tool records its plan and every attempted response in a new private directory. See [procurement observation policy](docs/PROCUREMENT_OBSERVATION_POLICY.md) and [capture protocol](docs/PROCUREMENT_CAPTURE_PROTOCOL.md). Core scoring and protected FIU/GRP boundaries remain unchanged.
