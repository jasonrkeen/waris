# WARIS rc13 controlled research release candidate

26 October 2026. **Unpublished local review candidate. Full public-release approval remains pending.** This separate security-integrated child preserves the controlled nine-page research PDF, selected-snapshot dashboard, current rc13 code/model and frozen source boundaries.

## Install and run

Use Python 3.12 in a new virtual environment. From this extracted assembled root:

    python -m venv .venv

Activate .venv using your platform's normal command, then:

    python -m pip install pip==26.2.2
    python -m pip install -r requirements-dev.txt
    python -m pip check
    python -m streamlit run presentation/dashboard.py

The root .streamlit/config.toml binds the dashboard to 127.0.0.1, keeps CORS/XSRF protection, disables static serving and telemetry, and hides detailed errors. This is a local reader; hosted access/authentication has not been reviewed. Keep this root as the working directory so its configuration applies. No provider credentials are required for this controlled presentation.

The supported current installation uses the root requirements files: certifi 2026.10.23, Pillow 13.0.0, Streamlit 1.66.1 and the remaining 47 unchanged application/test pins. Historical runtime/component requirements remain untouched as provenance; do not install those older locks as the current supported environment. Upgrading Pillow alone is incompatible with the historical Streamlit 1.65.0 pin. The bootstrap pip update is separate from application dependencies.

## Reproduce and check

Read presentation/outputs/WARIS_Controlled_Research_Report_rc13.pdf. To reproduce its PDF, three charts and exact plotted CSVs in a NEW directory:

    python presentation/build_report.py --output-dir <new-output-directory-outside-this-candidate>

To run all local suites, dashboard behavior, input/selection integrity and two presentation builds:

    python tools/check_controlled_release.py

The root .github/workflows/controlled-release.yml prepares Python 3.12 Windows/Linux checks. Its presence is not an executed GitHub result. No remote CI, push or publication occurred. CHECK_SCOPE.md and the dated integration audit distinguish actual platform execution from proposed runner coverage. Each platform must reproduce byte-identical independent builds. Windows must match all canonical output bytes. Qualified Linux x86_64 must match PDF/CSV bytes and source/metric metadata exactly; its PNG encoding may differ only if PNG metadata, dimensions and every decoded pixel equal the frozen canonical image. See PLATFORM_REPRODUCIBILITY.md. No source values are rewritten for platform parity. Do not run review tools with Python optimization.

## Identities and source boundaries

Current package: WARIS-v0.12.0-rc13-security-integrated-review-1. Parent report/dashboard ZIP: de224b5a1c54278e4ad588d49a2a8350c9d471a1fbecf1ff6b315dfc77aceab3. Model remains 0.12.0 and code baseline 0.12.0-rc13-methodology-review. Presentation build remains WARIS-rc13-controlled-report-dashboard-1. SECURITY_INTEGRATION_RECEIPT.json identifies this packaging change; the unchanged older assembly/presentation receipts describe their separate builds. Replaced parent reader/inventory files are retained in provenance/security_parent_*.

The twelve allowlisted source inputs, their pinned parent inventory, all 317 selected component members, and all 109 runtime files stay unchanged. Scores and assumed-draw intervals are wholly synthetic. Official GRP is benchmark-only, with no scoring/Monte Carlo use or validated sector-economic allocation. Procurement is separate recorded-frame description; World Bank and selected SFMS facts are national context; six permitted literature themes are conceptual references. Unverified FIU claims and four FIU-dependent themes remain excluded. Missing historical acquisition evidence remains missing. Confidence is categorical, not an adjusted score.

components/C11 is archival replay-only. runtime/app.py is retained legacy source, not the controlled reader entry point. No historical mixed-risk caches or withheld raw provider data are restored. The legacy live pipeline remains gated before credentials/provider work. The controlled report is a selected-snapshot research presentation, not the legacy full live report or empirical AML validation.

## Release limits

The dated audit reports advisory scans, exact-ZIP checks, platform results and preserved hashes actually verified. Updated dependencies and local reproducibility do not establish scientific validity, permission to redistribute every provider-derived artifact, independent control effectiveness or missing historical custody. Preserve source attribution, units, missingness, dates, territorial notes and source-specific limits; MIT covers project code, not blanket source-data rights. No publication, push, tag, provider contact or acquisition is authorized by this package.
