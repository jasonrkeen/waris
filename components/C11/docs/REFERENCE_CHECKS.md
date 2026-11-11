# Reference checks for the full research release

Review date: October 13, 2026. Two quarterly FIU references now have verified official URLs and text-level numerical reconciliation. This is separate from recovery of the exact historical user-supplied PDFs.

| Source | Check and boundary |
| --- | --- |
| [Q1 2025 transaction reports](https://fiu.gov.ua/assets/userfiles/200/Statistics/2025/ENG_Statistic%20I%20quarter%202025.pdf) | All 13 recorded values match the two-page PDF text, including the non-bank share in the page-1 chart and channel counts in the page-2 table. FIU-STAT-006's 99.92% is present, but the denominator and inherited successful-submission label require semantic review. The registered-channel counts are a different measure from received/processed reports; do not force the two totals to agree. |
| [Q1 2026 NABU referrals](https://fiu.gov.ua/assets/userfiles/440/2026/ENG_I%20quarter_NABU.pdf) | Ten records, including the total, match page 1 for both count and funds: 20 numeric cells. Two separate source rows use the same executive-authority category; retain row identity and legal-clause context rather than deduplicating by label. Aggregates are national referral context, not regional findings. |
| [2023 annual report](https://fiu.gov.ua/assets/userfiles/200/Activity%20reports/Report_2023_ENG.pdf) | Official locator identified. Full text was not available for verification: web reader rejected the 49,258,511-byte document; direct local retrieval returned HTTP 403. Claimed section/page support for FIU-TYP-001 through 005 and 007 remains open. FIU-TYP-002 has checked quarterly statistics but an unverified annual typology claim. |
| [Utenkova article](https://phes.com.ua/ojs/index.php/www/en/article/view/112) | Publisher identity, title, DOI and CC BY 4.0 verified. See typology_conceptual_page_crosswalk.csv for previously checked printed pages. This is conceptual literature support and does not validate proxy formulas, sector allocations or regional conclusions. |
| World Bank historical extract | 132 of 136 observations match a new official snapshot at relative tolerance 1e-10 and absolute tolerance 1e-8. All four differences are 2024 observations, one per indicator. Preserve the archived snapshot; record differences as revision/snapshot differences, not evidence of transcription error without historical retrieval records. |

The official FIU navigation has inconsistent year/title labels. The Q1 2026 referral page is under a navigation entry labeled 2025, while its heading and PDF state January-March 2026. The Q1 2025 statistics landing heading says 2025, while the linked PDF specifies the first quarter. Use the PDF reporting period, not a misleading navigation label.

Review method: official PDF text through the web reader, compared with the archived tables. Direct local requests returned HTTP 403; no source PDF bytes/hash were retained. Screenshot calls did not deliver inspectable pixels through this tool connection. Final source-file retention and visual table review remain open; no visual certification or historical-byte authentication is claimed.

The generated reference annotations report the recorded check and detect changed/unknown numeric values. They are not a live source verification service. Annual claims remain visibly unverified even when their context tables are created successfully. No reference is approved for scoring or Monte Carlo use.

## October 18 continuation

The user cannot locate a local annual-report copy. Further direct and normal-browser attempts failed; the exact annual pages remain unverified. One indexed official-report excerpt suggests section 4.3.5 corresponds to the inherited fraud theme, but this is not accepted as full-text/page verification. No substitute year, translation or reconstructed report was used.

rc5 now withholds six unverified annual/mixed typology rows and FIU-STAT-006 from the report's context tables while preserving internal records. Rows lacking qualifying verification, semantics or reporting-period annotations are also withheld. Reporting-period and notes columns replace nonexistent report column names. Applicable quarterly source links and license context are visible in the appendix. This is presentation control, not source verification or a scoring change. The isolated three-page appendix was visually inspected; full research PDF QA remains open.
