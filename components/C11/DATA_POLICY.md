# Data and redistribution policy

The public candidate contains source code and documentation only. All supplied `data/` and `outputs/` files are excluded, including derived proxies and historical reports. This conservative exclusion is a packaging decision, not a finding that every provider prohibits redistribution.

ACLED events and derived conflict proxies require review against the user's access agreement and applicable [EULA](https://acleddata.com/eula), [content usage](https://acleddata.com/contentusage), and attribution requirements. Removing event rows alone does not settle derivative-output rights. The owner attests that the exposed credentials were rotated. Account-side rotation has not been independently checked, and the Research-1 local credential file was stale at the October 13 check. On October 18 it was read only for redacted package secret checks; authentication and post-rotation status were not verified.

OpenSanctions samples contain entity-level data. The source-code MIT license cannot override [OpenSanctions licensing](https://www.opensanctions.org/licensing/) or [non-commercial-use conditions](https://www.opensanctions.org/docs/commercial/exemption/). No assertion is made that all redistribution is prohibited; the exact dataset, license, attribution and intended use must be recorded before inclusion.

Ukrstat, Prozorro, NBU, World Bank and FIU/SFMS materials also need per-artifact provenance: original URL, access date, coverage, transformation, provider terms/version, attribution, personal-data review and redistribution decision. No institutional-library or privileged-access provenance is implied. Public accessibility is not blanket relicensing permission.

Before including any extract or derivative report, document the decision in a data register and scan the full output dependency chain. Keep credentials and provider downloads local; all runtime artifacts are ignored by Git. The offline demo creates only clearly labeled synthetic files and records hashes. It reads no supplied raw or processed inputs.

## Rights and reference preparation

See [Third party notices](THIRD_PARTY_NOTICES.md), [Reference checks](docs/REFERENCE_CHECKS.md), and [Full research assembly](docs/FULL_RESEARCH_ASSEMBLY.md). A provider permission basis is separate from verification of a particular saved extract. Current provider pages cannot supply missing historical retrieval dates. No reviewed provider dataset is relicensed under MIT.

Full research distribution can include verified methods, approved aggregate results and instructions for authorized users to acquire restricted inputs. It does not require public redistribution of restricted raw data. The full release remains blocked until its exact included artifacts, provenance, rights, citations and reproducibility are cleared.

Generated run provenance, integrity receipts and captured input snapshots remain private until artifact clearance. Hashing does not grant redistribution rights or authenticate provider collection.
