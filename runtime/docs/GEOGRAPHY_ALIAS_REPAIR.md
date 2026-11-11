# Geographic alias acquisition repair

Rc9 adds `zaporizhia -> Zaporizhzhia` to the shared geographic normalizer. Existing entries and the 25-oblast project scope remain unchanged. Crimea remains outside that scope; this is not a new territorial allocation or scoring feature. Acquisition policy is `nbu-query-repair-1+oblast-alias-repair-1`; model formulas/weights remain at 0.12.0.

A cached-source lineage review identified the missing spelling. The repair can alter normalized conflict proxies and future live-source scores under the existing transformations. Min-max normalization can transmit a changed input beyond the directly affected region. The normalizer is shared with procurement connectors, so future sample effects require review. No provider events or sample-specific aggregates/score statistics are included in this code candidate; sensitivity results remain in the private audit package pending rights review.

Frozen historical source inputs/results remain unchanged. Historical core numerical replay is separate from the repaired acquisition policy. Applicable account/use entitlement, derivative rights, sample coverage, zero-fill assumptions and methodological review remain open. A mapping fix is not source completeness, scoring approval or operational validation.

Official GRP is benchmark-only, expanded procurement review-only, FIU national context-only, and wartime typologies literature/reference-only. Neither literature curation nor separately acquired research supplements changes these boundaries.
