# Procurement observation and sparse-group policy

Unreleased rc11, 18 October 2026. This policy concerns expanded review artifacts only. It changes their interpretation and candidate availability; it does not change core WARIS scoring or the basic live procurement connector.

## Missing observations

An unavailable bid list is null, not zero. A visible empty array counts zero visible objects, without proving zero economic participation or a completed procurement process. Malformed lists also produce unknown counts. Award suppliers are counted only when all visible award records provide usable supplier lists/identities; missing/incomplete records produce null. The supplier scope covers all visible award records, including possible qualifications/disqualifications, and does not identify winning suppliers. Legacy identifier/name fallback remains a limitation; entity resolution is not certified.

The combined flag uses three-valued OR: one observed positive suffices; a negative needs both counts; other cases are unknown. Its rate uses the number of known combined flags, explicitly reported beside total unique tenders and unavailable counts. Separate single-visible-bid and single-visible-award-supplier rates use their own observed denominators. These are visible-field descriptions, not verified competitive participation or AML indicators. Reporting/negotiation and other procedures may expose different fields; an unavailable field is not assigned a causal explanation or inferred applicability.

## Conservative internal support screen

The configured `PROZORRO_MIN_REVIEW_GROUP_TENDERS = 5` is an engineering screen, not a validated statistical cutoff, legal anonymity threshold or release approval. A candidate is withheld when fewer than five unique tenders support the group, or when any member has unavailable bid/supplier observations. Duplicate or missing record identities fail rather than inflate support. Candidate projections also require the new observation metadata, preventing legacy tables from silently restoring withheld priorities. Single-bid/supplier scaling uses supported observed groups only. Other component scores remain internal descriptive heuristics.

Missing candidates remain null in CSVs, unavailable in context bands/actions, and missing in the dashboard. PDF numeric cells distinguish missing values from observed zero; this formatting repair applies to all PDF numeric tables. Summary top-candidate rows select only an available candidate. Unsupported groups do not receive an artificial low-priority label.

All regional/sector feature, candidate and bridge tables remain private review artifacts with an explicit held publication status. Nulling a candidate is not disclosure control for the remaining counts/prices. No new regional/sector public view is approved or bundled.

## Sparse-group disclosure review

Review both grains together. An oblast total and its sector children can reveal a withheld child through subtraction; filtering individual rows at five alone does not resolve complementary disclosure. This candidate therefore does not release either numeric hierarchy. Publicly scoped material remains whole-sample field-availability metadata and first-party policy definitions, reviewed separately. Internal support diagnostics retain their private classification. High-support rows are not automatically anonymous or publication eligible.

Before approving a later numerical public extract, define its exact fields and linked tables, inspect direct and indirect entity linkage, set an appropriate suppression/coarsening scheme, test complementary disclosure and retain sample/temporal/source qualifications. No source entitlement is granted by this policy. Official GRP remains benchmark-only, FIU national context-only and literature reference-only; unverified FIU annual claims remain excluded.
