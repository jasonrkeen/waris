# Run manifest and provenance contract - rc8

The research pipeline creates a UUID-based execution identity before stage 1 and keeps it across pre-context, pre-report and final manifests. Separate processes no longer share an ID merely because they start within the same second. Do not run two processes against the same output directory; use independent directories for independent executions.

The final manifest is written after the PDF. It inventories every eligible file under data/ and outputs/ with a project-relative path, exact size and SHA-256. It excludes five named self-metadata files to avoid stale sizes and recursive hashing:

- outputs/tables/run_manifest.csv
- outputs/tables/run_manifest_summary.csv
- outputs/reports/run_manifest.json
- outputs/reports/run_provenance.json
- outputs/reports/run_provenance.sha256

The seal, run_provenance.json, hashes the completed first three files and records the complete final data/output inventory separately. run_provenance.sha256 hashes the completed seal. Keep that checksum outside the run directory as an independent integrity anchor. These are ordinary hashes, not signed authentication; someone able to replace both files can rewrite them.

Before pipeline stages, the context records eligible project source/configuration, existing data/artifact hashes and installed Python/package/platform metadata. It captures an ordered CSV serialization of the exact dataframe passed to risk-layer calculation and of the scored dataframe passed to Monte Carlo. These snapshots are private generated data, not automatically cleared research datasets. Source drift or modification of either captured input before finalization refuses sealing. File observation does not prove every artifact was read or freshly regenerated; preexisting unchanged content is labelled explicitly. The manifest does not silently turn old files into new execution evidence.

Credential files and cache paths are excluded. No environment variable values or authentication payloads are recorded. Source scope covers root code/document/configuration files and src/, tests/, docs/ and .github/; the release source manifest is included. Installed distribution metadata is recorded, not wheel hashes or a claim that the environment is immutable. Input snapshots preserve the declared pandas UTF-8/LF CSV serialization, not native in-memory bit patterns. Initial file hashes do not retain overwritten initial bytes; archive authorized inputs separately if reconstruction of an initial snapshot is required.

After finalization:

```text
python -m src.provenance --verify
```

Verification rejects changed/missing/additional data/output artifacts, changed source, changed completed manifests, mismatched identities and a missing/damaged seal. Standalone run_manifest generation is labelled file observation, not pipeline execution. Intermediate manifests are not final seals. The PDF consumes pre-report metadata; it does not embed a final hash of itself. Retain the final seal beside it.

Hashes, relative filenames, installed-package inventories and generated snapshots may reveal research details. Review them separately before public inclusion. This mechanism does not authenticate a provider download, prove source permissions or complete historical provenance, and does not validate model accuracy. A successful network-denied fallback remains a fallback. Unverified FIU annual claims remain excluded. Official GRP remains benchmark-only; expanded Prozorro review-only; FIU national context-only; wartime typologies literature/reference-only.

## rc11 capture-tool source coverage

The eligible source tree now includes tools/ alongside src/, tests/, docs/ and .github/. The new capture utility is therefore included in pre-run and final source inventories; changing its code invalidates source-integrity verification. The capture receipt separately retains its before-request script hash. Credential/example exclusions and self-referential metadata exclusions remain explicit.
