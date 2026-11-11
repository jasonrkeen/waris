# WARIS full research release inclusion plan — rc13, review 1

23 October 2026. **Selection plan only; the integrated full research release remains blocked.** No publication, push, tag, provider contact or new acquisition. All previous packages stay frozen.

This plan settles the remaining known procurement, literature, context and replacement-component choices alongside the already selected 23 historical entries. It does not redefine the full research target as merely a synthetic demo. It distinguishes planned content from actual execution, rights scope, method validation and final readiness.

## Selected component set

| ID | Planned role | Required dependencies | Mandatory companion |
| --- | --- | --- | --- |
| C01 | current source and historical appendix | — | [scope](companions/C01.md) |
| C02 | recorded procurement frame methods | — | [scope](companions/C02.md) |
| C03 | procurement descriptive projection and metadata | C02 | [scope](companions/C03.md) |
| C04 | curated literature GRP World Bank methods | C01 | [scope](companions/C04.md) |
| C05 | typed DSD and benchmark reconstruction | C01, C04, C11 | [scope](companions/C05.md) |
| C06 | curated historical GRP units and validation scope | C04, C11 | [scope](companions/C06.md) |
| C07 | corrected probe gap merge narratives | C04, C05 | [scope](companions/C07.md) |
| C08 | typed annual candidates and query limits | C04, C06 | [scope](companions/C08.md) |
| C09 | operational declarations and index illustrations | C01, C04, C05, C11 | [scope](companions/C09.md) |
| C10 | historical metadata and selected SFMS national context | C01 | [scope](companions/C10.md) |
| C11 | archival replay dependency only | — | [scope](companions/C11.md) |

The current rc13 source is embedded in C01. C11 is solely a frozen archival rc11 reconstruction dependency because older helpers bind exact source fingerprints. It is never a second active runtime. Keep component directories separate and retain relative helper paths; do not merge identically named methods.py, manifests, READMEs or study inputs across components. Current source/policy precedence is this master plan and SOURCE_BOUNDARIES.json, current rc13 documentation, component scope notes, then dated historical text. Older ACLED, confidence, live-run or readiness statements remain historical and are superseded.

## File selection, aliases and transformations

[COMPONENT_DECISIONS.csv](COMPONENT_DECISIONS.csv) assigns every known predecessor ZIP an inclusion, covered, superseded-development or private/history omission. [MEMBER_INCLUSION_LIST.csv](MEMBER_INCLUSION_LIST.csv) binds every direct file member of selected predecessor packages to its exact bytes and intended component path. ZIP hashes also bind nested contents; C01 carries the previously checked embedded rc13 source and 20-file historical appendix. Its 23 original inventory rows, three aliases, mandatory companions and 152 historical exclusions are unchanged.

Original manifests remain provenance records of predecessor ZIPs, not the current selection/assembly authority. Repeated data/method files are mapped by hash in DUPLICATE_CONTENT_MAP.json; retain duplicate physical copies only where frozen relative-path replay or companion context requires them. Copies are not independent evidence. C01 already covers the separate geography-control package and active rc13 source; those ZIPs are not redundantly selected as new outcomes.

N01 is a separately hashed **six-row reader-facing literature page crosswalk**, filtered from the original ten-row source without changing selected row text. The six permitted IDs are WAML-001 through 005 and WAML-010. The old ten-row file's original hash stays recorded; it is omitted as the reader crosswalk. Its four withheld concepts must not be restored through older caches, maps, memos or auto-exports. Internal source/audit definitions in frozen code are not approved factual exports. Keep the dated literature attribution, adaptations, page scope and no-endorsement/validation notice attached.

## Required source boundaries

- **GRP is benchmark-only.** Neither scenario indices nor regional facts approve sector-economic allocation, production scores or Monte Carlo use. Preserve UAH/scale/year typing, territory/series notes, missing versus unavailable states and nonadditive national aggregates. Arbitrary synthetic-index gaps are not actual revenue discrepancies.
- **Procurement is descriptive/review-only.** Select the recorded-frame design plus individually reviewed observed/weighted projections, not pooled results from earlier development samples. Preserve lifecycle/lot/unknown-bid handling and procedure domains. Weights expand only within the recorded finite frame, not Ukraine. Objects are not firms, convictions or wrongdoing. Private selection/raw responses and record identifiers stay outside release.
- **National context stays national.** World Bank source years/missingness/underlying credits stay attached. SFMS Q1 facts are referrals/associated amounts, not people, convictions or losses. Preserve source row positions, duplicate labels and published total. Its dated verification is text-only: local PDF custody/visual layout and historical acquisition were not established. Unverified FIU annual/mixed claims stay excluded.
- **Literature is conceptual reference.** Project indicators, confidence declarations and layer mappings are interpretations, not validation by the article. No scoring or Monte Carlo.
- **Controls are declarations/methods.** File presence, pass/fresh flags, matched run IDs and synthetic parity are not current provider freshness, completed analyst reviews, calibrated confidence or operational effectiveness. rc13 categorical confidence and retired ACLED scoring/blend remain in force.

All source-specific attribution, CC/MIT separation and dated rights receipts travel with selected files. This pass does not retrieve current terms or grant new permissions. Selecting an already reviewed component does not close missing historical HTTP provenance or authorise a new empirical use. Public arithmetic/source integrity replay is distinct from access to private raw snapshots.

## Assembly and remaining gates

This delivery contains the plan, decisions, projection N01, guard/tests and verification receipts—not an integrated research build or all predecessor archives. Existing exact predecessor ZIPs are available in the local outputs folder. `python tools/validate_plan.py --components-dir <that-folder>` checks the selection, dependencies, policy, projection and locally available source bytes. It does not execute captures, import scoring changes or confer rights. Without --components-dir it checks the plan's internal integrity only.

The composition choices are settled for the known component inventory. Future final dashboard, PDF, figures and run receipt are **not selected as existing completed artifacts**. A controlled assembly must implement these paths/reader filters, preserve component contexts, emit a fresh exact inclusion manifest and run identity, complete qualifying full replay, and validate every final output. Final dependency/security/advisory/platform checks and actual report/dashboard QA remain outstanding. Missing historical inputs/receipts must remain explicit; no reconstructed or newly fetched substitute may authenticate them.

RELEASE_GATES.csv separates these unfinished execution/readiness gates from settled selection. Nothing is ready for automatic public upload. Publication needs a later explicit user instruction.
