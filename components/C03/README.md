# WARIS scoped procurement and metadata supplement

Prepared October 20, 2026. Unpublished release candidate. This supplement clears only the exact files listed in FILE_MANIFEST.json, with the qualifications below. It does not clear the full WARIS research package or change any score. Read ATTRIBUTION_AND_RIGHTS.md and METHODS_AND_LIMITS.md with the tables.

## Procurement files

`procurement/procurement_observed_summary.csv` contains two coarse, source-attributed procedure summaries. Counts are observed in the frozen sample. The metric is exactly one visible active linked bid object per eligible unit under the documented rule; it is not a count of unique firms, valid offers, winners or wrongdoing.

`procurement/procurement_frame_weighted_estimates.csv` contains the corresponding finite-frame weights and expanded totals. The fractional total 22.575 is an estimate, not an observed number of tenders, bids or people. The aboveThreshold row is a census only of its domain in this recorded frame. The priceQuotation row samples 40 of 43 frame tenders. The recorded frame is not national procurement or a calendar-period population. Do not pool the procedure/unit-type rows.

Both tables are eligible as descriptive research outputs of the exact frozen study. This is an internal, artifact-specific release assessment, not blanket legal, anonymity or model certification. No record IDs, names, party identifiers, prices, addresses, procurement subjects, geographic breakdowns, sector hierarchies, per-response fingerprints or selected membership are included. Buyer-diversity checks remain private; no buyer or firm conclusions are approved. The numeric results are not approved to alter WARIS risk layers, scores or Monte Carlo simulations.

## Metadata files

`metadata/ukrstat_observation_query_candidates.csv` is the unchanged historical 67-row metadata shortlist. `metadata/metadata_verification.csv` provides the dated source/agency/version check. Sixty-four code/name/description rows exactly matched fresh same-version official code lists; three year rows are first-party proposals, not confirmed available observations. Its planning statuses remain planning statuses. This is not an executed-query record, validation of proposed indicators, approved sector allocation or proof of original acquisition dates.

This shortlist is eligible only with the dated verification and attribution. It does not clear other historical Ukrstat exports or the broad 32,934-row candidate code table. The full code lists and provider response bodies are not bundled.

## Verification and availability

`tools/public_projection.py` accepts only the exact reviewed private result hash and exports the two approved projections to a new directory. Different input bytes require another clearance. `tools/reconcile_metadata.py` contains the selected-metadata reconciliation logic and a local audit recipe; its work-area paths and private provider snapshots are intentionally not distributed. Tests use synthetic inputs and can run from the tools folder in the existing pinned WARIS Python 3.12 environment:

```powershell
python -m pytest test_projection.py test_metadata.py -q
```

The public tables permit arithmetic checks of counts, sampling fractions, weights and ratios. Independently reproducing the acquisition/selection still requires the retained private frozen inputs; they are not distributed here. Public API re-fetches are a new vintage and may differ. No promise of third-party access to private records is made. The preceding recorded-frame source companion documents the frozen sampling design separately.

The release projection was designed after execution for data minimization. It retains both predeclared procedure domains and their predeclared measures; it does not select a favorable subgroup, change the frozen analysis, extend the sample or retrofit a pre-analysis claim. All earlier source and data artifacts remain immutable.

Official GRP remains benchmark-only. Expanded procurement remains review-only. FIU remains national source context; unverified annual claims remain excluded. Literature remains reference-only. The main WARIS rc11 candidate is unchanged. Full research release remains blocked, and nothing has been published or pushed.
