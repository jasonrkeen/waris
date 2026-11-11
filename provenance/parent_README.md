# WARIS rc13 assembled review candidate

Prepared locally on 25 October 2026. **Assembled for controlled review; full public-release readiness remains blocked.** No publishing, pushing, provider contact or new acquisition occurred. Source/model baseline is rc13 / 0.12.0; assembly ID is WARIS-v0.12.0-rc13-assembled-review-1.

This package materialises the frozen 23 October inclusion plan: 11 separate components, 317 selected direct members, a six-theme reader literature crosswalk and an unchanged runnable copy of the current rc13 source. Original packages and bytes are preserved. The omitted ten-theme reader crosswalk is not copied into C04. Frozen source/audit definitions in runtime are not approved reader exports. Do not copy their old cached or unfiltered content into reports.

## Start here

- runtime/ is the current unchanged rc13 source. Install runtime/requirements-dev.txt in a fresh Python 3.12 environment. It carries the pinned dependencies; this assembly introduces no new runtime dependency or scoring change.
- components/C01/ holds the 20-file historical appendix (23 original entries, three aliases) and mandatory companions. components/C02–C10/ hold separately reviewed procurement, context, literature and correction components. Keep their attribution, typed notes, dates, scope and relative helper paths together.
- components/C11/ is archival rc11 replay source only. It is not an alternative current runtime and must not be used for live collection, old blend/confidence behavior or cached public exports.
- reader/literature/ supplies the six permitted reader-facing page-crosswalk rows and attribution. The current literature register/maps in C04 also contain only the six permitted themes.
- plan/ preserves exact frozen planning material. Its predecessor manifests are dated provenance, not inventories of this assembled tree. ASSEMBLY_MANIFEST.json is the current byte inventory; the delivery checksum binds the complete ZIP.

## Offline checks and reproduction

From this extracted folder, with the pinned environment active:

```text
python tools/validate_assembly.py
python reproduce.py --output-dir <new-empty-output-path>
python tools/check_dashboard.py --result <new-result-json-path>
```

Reproduction refuses an existing output directory and denies provider network connections in child processes. It runs the current synthetic demonstration in a temporary source copy, the selected public benchmark/gap/rescale arithmetic, and supplied-data consistency checks. It never executes provider capture or the archived main pipeline. Outputs are simulated/model-assumption illustrations or scoped arithmetic replays, not a newly acquired empirical wartime study or reconstruction of historical HTTP requests. Details and limitations are written to REPLAY_RESULT.json. Dashboard checks are headless AppTest behavior checks in an isolated synthetic copy, not browser/PDF visual certification.

For interactive synthetic dashboard use, run runtime/offline_demo.py locally, then `python -m streamlit run runtime/app.py`. Optional research tabs may be empty because selected context is intentionally outside runtime cache paths. The historical main.py --allow-live gate stays active before credentials/provider work; do not bypass it. This assembly is not an integrated live/research pipeline or full regenerated research PDF.

## Source boundaries and readiness

GRP remains benchmark-only: no production scores, Monte Carlo integration or approved sector-economic allocation. Expanded procurement is review-only and finite-frame descriptive output, not national prevalence, firm counts or misconduct. Literature is six-theme conceptual reference only. Selected FIU/SFMS facts remain attributed national context; text-only quarterly verification does not establish local PDF custody/visual layout or verify the missing annual report. Unverified FIU annual/mixed claims remain excluded. Confidence remains categorical declarations; the old ACLED scoring/blend is retired and acquisition gated.

Master README/SOURCE_BOUNDARIES take precedence, then the frozen plan/current rc13 policy, component scope notes, and dated component text. Old pass/GO/latest/fresh/run labels do not become current validation or authorise scoring. MIT applies to owned code/methods, not source-provider material. Preserve every applicable source notice and territorial/missingness note.

The full research target is unchanged. This candidate closes physical assembly and the supported offline checks actually reported in the audit; it cannot authenticate missing historical acquisitions or claim full empirical replay. Final integrated run design, actual dashboard/PDF/figure QA, fresh final security/advisory/platform checks and explicit later publication instruction remain separate gates. No private provider records or old mixed scores are included. The source code contains historical/audit definitions whose approved export boundaries must stay enforced.
