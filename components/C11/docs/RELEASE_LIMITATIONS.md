# Release limitations

This is a reviewable candidate, not a release certification. Resolve the following before treating the complete research product as ready:

1. The owner confirms that the exposed ACLED credentials were rotated. Account-side rotation is not independently checked; the Research-1 local credential file was stale when checked October 13 and was read only for redacted secret checks in this continuation; authentication and post-rotation status were not verified. Configure fresh credentials privately before authenticated validation.
2. The owner confirms code ownership and MIT intent. Provider data and derivative-output rights remain separate; clear each selected research artifact before public inclusion.
3. The stage-7 missing official-GRP failure and false availability/readiness claims are repaired and regression-tested in rc2. Extend adversarial/schema coverage and obtain independent review; do not infer live-source readiness from a successful fallback run.
4. Verify authorized live pipeline execution in a separate environment. Archive source snapshots, exact dependencies, input/output hashes and same-run identities; reproduce a frozen historical run if historical reproducibility is claimed.
5. Review basic live procurement sampling, ACLED zero-fill, NBU availability-based scoring, numeric coercion and calibration assumptions with appropriate subject-matter experts.
6. Run CI on the intended platforms; verify the dashboard visually and full PDF separately. Local headless checks do not establish visual quality or all tabs' behavior.
7. The rc4 candidate passed 17 tests; rc5 passed 26 tests plus three subtests, including reference mismatches, protected context layers, missing sources and stale-readiness handling. Further validation should address uncovered methodological and source-coverage risks. The guide's three unspecified module proposals are deferred suggestions, not established first-release requirements; agree on specifications before implementing them.

Quarterly FIU numerical text checks and indicator-specific World Bank licensing are recorded in rc4. The FIU annual-report claims, quarterly label/denominator caveat, exact Prozorro permission scope, selected-artifact provenance and final report review remain open. See REFERENCE_CHECKS.md and FULL_RESEARCH_ASSEMBLY.md.

Rc8 replaces the incomplete legacy inventory with full eligible data/output hashing, UUID execution identity, pre-run source/environment snapshots, captured scoring/simulation frames and an external final seal. See RUN_PROVENANCE.md for self-exclusions and integrity verification. A file snapshot does not authenticate acquisition or prove all files were consumed/regenerated; source permissions, input custody, wheel hashes and independent methodological validation remain separate. Older rc1-rc7 manifest limitations are retained as historical findings, not assertions about the repaired rc8 mechanism.
