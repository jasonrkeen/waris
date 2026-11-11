# WARIS selected Ukrstat preparation supplement — 20 October 2026

Local, unpublished preparation. Four historical CSVs are individually eligible only with this dated companion documentation. A new typed DSD projection and independent arithmetic reconstruction are separate artifacts, not retroactive replacements for frozen originals.

The two metadata tables preserve historical discovery wording. Seven clues and twelve registry references match official agency/id/version/title facts at their exact versions. Registry paths also match the retained historical JSON. Current retrieval does not authenticate original HTTP requests, access dates, query execution or observation availability. Receipts identify selected public official responses; raw responses and bulk imported codelists are not distributed.

The historical benchmark comparison matches 250 numerical cells independently rebuilt from 25 previously cleared official 2021 GRP observations and 150 newly generated first-party synthetic prewar indices (seed 42). Two network-denied replays agreed. The comparison contains no current WARIS score or live conflict/procurement inputs. Synthetic prewar indices are arbitrary model inputs, not measured revenue. Their sums, normalized shares, ratios and min-max gaps are illustrative diagnostics, not estimates of economic error or AML predictive validity. The independent CSV contains only the reviewed numeric projection.

Coverage is 25 selected WARIS regions in 2021 (24 oblasts plus Kyiv City). It does not establish all-territory coverage, current economic conditions, sector representativeness, or boundary equivalence across vintages. GRP remains benchmark-only; sector allocation and production scoring are not approved. Historical approved_current_use wording means controlled benchmark review only.

The typed DSD6 projection separates four series dimensions, one time dimension, fifteen attributes and one measure. The descriptor container is not a dimension. Supplied concept URNs are preserved verbatim, including version selectors. Codelist enumeration links are not inferred from names. Component presence does not approve an observation query.

Public methods checks: from tools, run `python -m pytest test_clearance.py -q` with pytest available. These tests validate method boundaries; they do not recreate remote acquisition or authenticate historical execution. Full seed replay additionally requires the unchanged rc11 source candidate, its pinned dependencies and the previously cleared GRP supplement. Private run_review.py receipts describe that replay; raw provider snapshots and private audit ledgers are not public inputs.

Use this supplement with ATTRIBUTION_AND_RIGHTS.md and its file manifest. The source candidate remains v0.12.0-rc11. No runtime dependencies or scoring formulas changed. Unverified FIU claims remain excluded. Full research release remains blocked by source-specific artifact holds; this ZIP is not permission to publish the private audit or any other outputs.

Offline benchmark replay from the extracted tools directory (use new output folders):

```text
python replay_benchmark.py --source <extracted-rc11-root> --grp <cleared-GRP-CSV> --output <new-private-replay-folder>
```

The replay checks the rc11 file fingerprints and exact previously cleared GRP hash before generating any inputs. It writes only to the supplied new folder. The resulting independent_benchmark_reconstruction.csv must match the bundled file byte-for-byte. Use the pinned rc11 Python environment. New synthetic work files are explicitly synthetic and do not fetch provider data. These engineering checks establish computational reproducibility for this scoped comparison; they do not resolve historical acquisition provenance or validate the model.
