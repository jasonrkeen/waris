# WARIS reviewed research supplements

Prepared 18 October 2026. Unpublished local release preparation. These small, separately reviewed supplements do not approve the full WARIS research package or the 175 historical artifacts as a group. No restricted raw source dump, historical ranked risk output, ACLED event record, procurement record or full WARIS PDF is included.

## Included components and source credit

### World Bank national context

`world_bank/world_bank_national_context_2026-10-18.csv`: Ukraine, four indicators, 1991–2024, 136 country/indicator/year slots; 128 reported observations and eight missing values. Each of the four indicator pages identified CC BY 4.0 on the review date. Credit the World Bank indicator service and the underlying providers below. No blanket license for unrelated World Bank datasets is asserted.

- `GC.TAX.TOTL.GD.ZS`: Government Finance Statistics Yearbook and data files, International Monetary Fund (IMF). [Indicator/source and CC BY 4.0 notice](https://data.worldbank.org/indicator/GC.TAX.TOTL.GD.ZS).
- `NE.EXP.GNFS.CD`: Country official statistics, National Statistical Offices (NSOs); National Accounts data files, Central Banks; Staff estimates, World Bank (WB). [Indicator/source and CC BY 4.0 notice](https://data.worldbank.org/indicator/NE.EXP.GNFS.CD).
- `NE.IMP.GNFS.CD`: Country official statistics, National Statistical Offices (NSOs); National Accounts data files, Central Banks; Staff estimates, World Bank (WB). [Indicator/source and CC BY 4.0 notice](https://data.worldbank.org/indicator/NE.IMP.GNFS.CD).
- `NY.GDP.MKTP.CD`: Country official statistics, National Statistical Organizations and/or Central Banks; National Accounts data files, Organisation for Economic Co-operation and Development (OECD); Staff estimates, World Bank (WB). [Indicator/source and CC BY 4.0 notice](https://data.worldbank.org/indicator/NY.GDP.MKTP.CD).

Changes: select country and years; normalize fields and units; retain missing values as blank, without interpolation or imputation. Monetary series are current USD, not millions of USD; tax revenue is percent of GDP. National context only; no WARIS scoring integration. Fresh source vintage differs from the retained historical snapshot in four 2024 cells; neither file replaces the other. Source update dates, acquisition times, original response hashes, exact API URLs and credits are in `acquisition_receipt.json`.

### Official GRP benchmark

`grp/ukrstat_GRP_2021_benchmark_2026-10-18.csv`: State Statistics Service of Ukraine (Ukrstat), regional accounts, GRP, annual, 2021, 25 selected regions. [Official dataset explorer](https://stat.gov.ua/uk/explorer?urn=SSSU%3ADF_REGIONAL_ACCOUNTS%28~%29); [official portal and copyright/default CC BY notice](https://stat.gov.ua/uk). The current portal default is CC BY 4.0 unless otherwise specified. The selected public responses supplied no contrary notes, flags or license annotations; this finding does not clear all historical Ukrstat material. Each row retains its exact official SDMX URL, response hash and acquisition timestamp.

Changes: extract one reviewed year and selected series, normalize columns, preserve reported values. Values are **millions of UAH**, with source unit code 1090 and scale code 6. This is a prewar reference benchmark, not a current wartime economic estimate. Geography labels, code-to-unit interpretation and territorial notes are explicitly identified as originating in the hashed retained export, whose original retrieval date was not recovered. Preserve those provenance qualifications. Coverage and territorial exclusions differ across periods; an empty observation-note field is not evidence of complete territorial coverage. Do not allocate these oblast values to sectors or treat them as current productive capacity. These role labels describe WARIS validation status; they do not impose extra restrictions on the CC license. The production pipeline remains unchanged and its offline readiness gate remains NO_GO.

### Conceptual literature and WARIS interpretation

Four CSVs in `literature/`: six broad themes, an 18-row layer map, a summary and an 18-row alignment crosswalk. Source: Karina Utenkova (2026), *Anti-money laundering as an instrument of economic security: Wartime adaptation of AML/CFT frameworks in Ukraine*, pp. 78–91, DOI [10.65237/2336-3630-2026-3(1)-4](https://doi.org/10.65237/2336-3630-2026-3(1)-4). [Publisher source and license](https://phes.com.ua/ojs/index.php/www/en/article/view/112). Copyright © 2026 CENTRAL EUROPEAN JOURNAL OF SCIENCE AND RESEARCH; publisher identifies CC BY 4.0.

Changes: English conceptual paraphrases, reduced theme selection and WARIS-specific proposed indicators, confidence labels and layer assignments. Those assignments are project interpretations, not author endorsement or validated measurements. The four detailed themes relying on independently unverified SFMS examples are withheld; the digital-asset description also omits the recruitment example. The 14-page paper was checked locally, including printed pages 87–88, but it cannot independently verify its underlying FIU claims. No unverified annual FIU claims are cleared here. See `docs/LITERATURE_REFERENCE_SCOPE.md` and the conceptual page crosswalk. Nothing in these tables identifies wrongdoing or enters WARIS scores or Monte Carlo.

### First-party methods

Six project catalogs/control documents in `first_party_methods/` are definitions and proposed controls, not provider observations, independent validation or evidence of operational effectiveness. The corrected limitations register is a new version; historical artifacts retain their own disposition. Owner-confirmed MIT intent applies to WARIS code and first-party methods, as stated in the included MIT license; it does not relicense provider data.

## License and reuse

For the source-derived portions identified above, retain the relevant source/creator/copyright credit, links, changes and [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/); [legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en). No endorsement is implied. No additional restrictions are imposed on CC-licensed material. Privacy, third-party rights and source-specific exceptions are separate questions; the review is limited to these selected files. CC BY licensing is not model validation. The review-only, context-only and benchmark-only labels record how WARIS currently uses the material.

## Reproduction and integrity

Each World Bank and GRP folder includes a receipt and a small offline rebuilding helper. The raw response bodies are retained privately and **not** bundled, following the owner's raw-data policy. The helpers require the exact recorded, hashed snapshots; they do not download or reconstruct missing historical evidence. Use `python replay_world_bank_context.py --help` or `python replay_grp_benchmark.py --help`. New public downloads are a new vintage if their hashes differ and require a new receipt/review. Receipt metadata supports the labelled geography/notes transformations; those source qualifications must remain attached.

The literature exports can be regenerated with the rc9 source candidate. Their content is deterministic; the complete fallback pipeline also produces run-specific identities, paths, times and hashes. The full package is not byte-identical between runs. `FILE_MANIFEST.json` records this supplement's file hashes. Keep a copy of the outer SHA-256 checksum separately; ordinary hashes are not digital signatures or proof of provider authorization.
