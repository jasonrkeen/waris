# Update guide assessment

The supplied Word guide contains four numbered filenames, numbered 4 through 7:

| Proposed file | Supplied implementation | Candidate disposition |
| --- | --- | --- |
| `prozorro_validation.py` | Absent in both archives | Deferred; existing `prozorro_procurement_features.py` is not an equivalent validation module |
| `confidence_adjusted_priority.py` | Absent in both archives | Deferred; existing `source_confidence.py` documents confidence and does not implement this proposed overlay |
| `MODEL_CARD.md` | Absent in both archives | Added as documentation; no scoring change |
| `executive_brief_generator.py` | Absent in both archives | Deferred; existing `report_generator.py` is a full research report generator |

There are no formulas, acceptance criteria, replacement code, or instructions in the guide. It is source material for this audit and is not authorization to redesign scoring.

A future procurement-validation module should test pagination, coverage, geography and sector mapping, missing buyer/supplier identifiers, duplicates and bid-count semantics against documented fixtures. It must not activate expanded features in scoring. A future confidence overlay needs an approved formula, handling of unavailable/stale sources, separation from core scores and sensitivity review. A brief generator must label synthetic/mixed data, carry source boundaries, use same-run identity and avoid presenting source availability as evidence of crime. None of these future implementations is claimed complete.
