# WARIS recorded procurement frame companion

Separate MIT first-party study code and methods. Main WARIS v0.12.0-rc11 is unchanged. Provider data is not licensed by this code license. Numeric results, tender IDs, selected membership, response bodies and record URLs are excluded from the source companion and remain private pending separate clearance.

The immutable `study_plan.json` and `freeze.json` record a locally frozen design and three code hashes before acquisition. The seed was generated before viewing the frame. Ten consecutive descending feed pages of 100 records define a finite operational recorded frame, with earlier termination only on an empty page. It is not a national or complete-period population. `public_modified` controls API pagination; displayed `dateModified` must not be treated as the cursor's ordering key. Wartime redactions and frame undercoverage remain possible.

Across pages, first-observed metadata wins for repeated IDs and conflicts are counted. The two sampling domains are first-observed complete aboveThreshold and priceQuotation tenders. Independently sample min(40,N) without replacement per domain using the frozen seed on sorted IDs; domains with <=40 are censused. A private selection file with N, n and inclusion probabilities is saved before the first detail request. No replacements, outcome-based page extensions or minimum-success stopping.

Detail records are analyzed with the unchanged prior lot-aware rules. Tenders are sampling clusters, explicit lots are units, and no-explicit-lots tenders form a separate unit type. Sampling domains, exact detail procedures and unit types stay separate. Changed detail statuses remain in the selected sample and contribute only if eligible; method drift does not enter another sampling domain. Missing counts remain unknown and withhold rates. At least five distinct sampled eligible clusters are required per stratum.

Cluster inclusion probabilities are n/N and weights N/n. Weighted totals use a Horvitz-Thompson cluster expansion conditional on this recorded frame and detail-time eligibility. The weighted numerator/denominator ratio is not itself an unbiased estimator. Common weights cancel within each domain; this does not license pooling domains or treating lots as independent sampled tenders. No confidence intervals or national inference are produced. The fixed budget is for feasibility, not a prevalence power calculation.

Use Python 3.12 and the unchanged rc11 pinned requirements. From this directory:

```powershell
python -m pytest test_frame_study.py test_lot_study.py test_geography.py -q
python frame_study.py freeze --study-root data/raw/NEW_FRAME
python frame_study.py capture --study-root data/raw/NEW_FRAME
python frame_study.py analyze --study-root data/raw/NEW_FRAME --output outputs/NEW_PRIVATE_RESULTS
```

Every target must be new. Capture uses public requests without credentials or attachments and retains each attempt/response before validation. It follows only opaque next_page.offset on the fixed endpoint, not arbitrary remote pagination URLs. Analysis checks cursor continuity, exact response inventories, identities, selection reproduction, freeze timestamps and hashes. A failure stays failed_partial, with no inferential output. `verify_local.py` replays the completed private snapshot twice without network access; recipients need its private `frozen_study` folder. New captures are new vintages.

`lot_study.py` and its capture dependency remain byte-identical to the previous frozen source. Its older one-page CLI remains for audit reproducibility; `frame_study.py` is the entry point for this new sampling design. `verify_geography.py` is a separate current-source mapping-control check, not a procurement outcome or scoring input. Its private extraction input is not bundled; the separately scoped geography supplement documents the result and exact official cells.

Primary references: [API feed](https://prozorro-api-docs-uk.readthedocs.io/uk/master/basic-actions/feed.html), [registry coverage/access limitations](https://data.open-contracting.org/en/publication/154), [bid/lotValue schema](https://prozorro-api-docs.readthedocs.io/en/latest/standard/bid.html), [lot schema](https://prozorro-api-docs.readthedocs.io/en/latest/standard/lot.html). The registry provides neither a Ukrainian bulk download nor a stated data license; its site's copyright license does not grant provider-data rights.

GRP stays benchmark-only, expanded procurement review-only, FIU national context-only with unverified annual claims excluded, and literature reference-only. Core scores, weights and seeds are unchanged. No publication or push occurred. The full research release remains blocked pending remaining source-specific evidence.
