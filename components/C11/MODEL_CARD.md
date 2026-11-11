# WARIS model card

## Identity and intended use

Model 0.12.0; unreleased package 0.12.0-rc5. A sector/oblast research demonstration for examining review-prioritization architectures, source separation and human-review controls. No institutional endorsement or operational validation is claimed.

## Inputs and scoring

The public demo uses seeded synthetic revenue indices and six proxy fields. The generator assigns different regional and sectoral assumptions; apparent geographic patterns therefore reflect the generator as well as the scoring design. Seven layers combine through fixed configured weights: revenue anomaly, sanctions exposure, procurement integrity, ownership opacity, TBML, conflict plausibility gap and financial-supervision exposure. Revenue and plausibility measures use sample-relative min-max scaling. Scores and rankings can change when the comparison population changes. Thresholds and weights have not been calibrated against verified misconduct labels.

The legacy research mode additionally blends basic procurement samples (60% synthetic / 40% live for matches), conflict proxies (50/50), and NBU availability (90/10). NBU availability is a technical coverage measure, not a demonstrated measure of financial crime. Missing ACLED sample regions receive zero live conflict contribution, which can lower the blended proxy despite incomplete coverage.

## Protected boundaries

Official GRP remains benchmark-only. Expanded Prozorro remains review-only. FIU/SFMS remains national source context. Typologies remain literature references. Operational review controls are documentation only. None of these layers is approved to change scoring or Monte Carlo inputs. Context flags are metadata and should not be mistaken for independent empirical validation.

## Validation and uncertainty

Local synthetic repeatability, score bounds, unique oblast/sector records, required-column rejection and official-GRP score/simulation invariance are tested. The dashboard has a headless smoke check. These checks establish selected software behavior, not predictive validity, false-positive rates, calibration, fairness or fitness for supervision. Monte Carlo perturbs weights and layers under assumed distributions; reported frequencies are sensitivity results, not probabilities of AML violations or empirical confidence intervals.

The full legacy pipeline completes clean and stale-readiness source-unavailable regression runs with all provider access denied. Official readiness remains NO_GO without observation/unit evidence, while core numeric scores and simulations match the synthetic demonstration. Archived output reproduction, live access, full PDF regeneration, comprehensive source-boundary mutation tests and independent SME review remain outstanding. Numeric coercion silently replaces missing proxies with zero and missing revenue with a baseline; invalid numeric values and incomplete source coverage need stronger validation before operational use.

## Prohibited uses and human review

No entity-level accusations, automated adverse action, sanctions determinations, credit denial, law-enforcement targeting, or allocation of official GRP to sectors for scoring. A reviewer must verify source coverage, benign explanations, lawful use and corroborating evidence before any interpretation beyond research. Wartime disruption and missing observations are not evidence of wrongdoing.

## Change control

Changing weights, transformations, live blends, sector allocation, protected-layer use or uncertainty assumptions requires a separately reviewed methodological change, recorded validation evidence and explicit approval. The public candidate preserves the scoring formulas and base weights. Packaging and the synthetic runner do not approve additional scoring inputs.

NBU query repair in rc3 is explicitly identified as acquisition policy nbu-query-repair-1. Corrected availability can affect scores under the inherited heuristic; the heuristic is not validated by successful data retrieval.

Reference review in rc4 is partial: quarterly FIU numeric text checked, annual claims unverified, and FIU-STAT-006 semantics unresolved. Third party licensing remains separate from MIT code. See docs/REFERENCE_CHECKS.md.

rc5 withholds six unchecked annual/mixed FIU support rows and the ambiguous quarterly metric from the report context tables, preserving internal records. This presentation control does not alter scoring or certify source authenticity.

Rc9 acquisition policy nbu-query-repair-1+oblast-alias-repair-1 repairs one geographic spelling alias. Future source-derived scores can change under the existing formula; private cached sensitivity and limitations are in docs/GEOGRAPHY_ALIAS_REPAIR.md. This is not source-rights or operational-model approval.
