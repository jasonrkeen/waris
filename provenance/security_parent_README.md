# WARIS rc13 controlled report and dashboard candidate

Local unpublished review, 25 October 2026. This separate candidate adds a nine-page controlled research PDF and selected-snapshot Streamlit dashboard to the frozen assembled rc13 parent. Core runtime/model version 0.12.0, weights, seed and live-acquisition gates are unchanged. GRP stays benchmark-only and unverified FIU claims remain excluded.

## Use the controlled presentation

Install runtime/requirements-dev.txt in a fresh Python 3.12 environment, then from this extracted folder:

    python -m streamlit run presentation/dashboard.py

Read presentation/outputs/WARIS_Controlled_Research_Report_rc13.pdf. Both surfaces use the twelve exact inputs in presentation/data_contract.json. A pinned parent inventory, hash checks and source-specific rules fail closed on drift. Scores and assumed-draw intervals are explicitly synthetic; benchmarks, procurement, national context and literature are separate views. Filtered synthetic downloads retain their data-mode label. The report includes each source family's interpretation limits and attribution.

To reproduce the PDF, three charts and their exact plotted CSVs in a NEW directory:

    python presentation/build_report.py --output-dir <new-output-directory>

The builder does not acquire data, invoke the legacy main pipeline or write to existing outputs. PDF metadata is fixed for deterministic byte-level comparison; the dated cover, contract and build receipt record actual build scope/date. Historical source acquisition dates are not inferred from PDF metadata.

## Boundaries and identity

This is WARIS-v0.12.0-rc13-report-dashboard-review-1, presentation build WARIS-rc13-controlled-report-dashboard-1. Its parent assembled ZIP hash is 6df4c8c3ca5dbd19afce8ab1acdd61baeb593f3943ed60e9dfffb6b54f481272. Parent source/model and dated component identities remain distinct. components/C11 is archival replay source only. runtime/app.py is retained frozen legacy UI source, not the controlled presentation entry point. Do not populate it or reports from historical caches. Archived parent README/check-scope/changelog/manifest are under provenance/; ASSEMBLY_MANIFEST.json inventories this candidate.

The nine-page PDF is a controlled selected-snapshot research presentation, not the gated legacy 75-page/full live report. It preserves the full research target while recording what this build supports. No new empirical wartime AML data, provider entitlement, historical HTTP authentication, calibrated outcome validation or control-effectiveness claim is created. Old source/audit definitions and past pass/GO/fresh labels are not approved public factual exports. Current presentation/source boundaries override dated historical instructions.

## Readiness

The adjacent dated presentation audit records exact-ZIP tests, build parity, PDF rendering and dashboard checks actually completed. Full public-release readiness remains subject to applicable final security/advisory/platform and methodological review gates and explicit later publication instruction. The legacy live entry point remains gated. Nothing was published, pushed or tagged. Code licensing does not relicense selected provider material; preserve source-specific attribution, units, dates, missingness, territorial notes and verification limitations.
