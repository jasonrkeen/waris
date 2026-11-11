# Controlled platform reproducibility policy

26 October 2026. The Windows Python 3.12.14 review build is the retained canonical artifact set. The separate Linux x86_64 Python 3.12.14 (WSL2/glibc 2.39) check found three PNG file encodings differ while their dimensions and decoded RGBA pixels are identical. The nine-page PDF, all three plotted CSVs, source/contract identities, metrics and other manifest metadata are byte-identical. No numerical or visible-chart difference was found.

The initial strict all-file byte check failed on Linux and is retained in the private diagnostic evidence. This is not relabelled as an initial pass. No original output or source value was changed to obtain parity.

The root checker now enforces all of the following:

- Two independent builds on each platform must have byte-identical complete manifests and artifact hashes.
- Every generated artifact must match its own manifest, and the canonical artifacts must match their frozen manifest.
- Source hashes, data contract, metrics and every non-output manifest field must exactly equal the canonical build.
- PDF and plotted CSV bytes must exactly equal the canonical artifacts.
- Windows also requires exact canonical PNG bytes. Qualified Linux x86_64 may differ in PNG encoding only when file type, dimensions, metadata and every decoded RGBA pixel match the canonical PNGs exactly.
- Any missing/extra output, changed PDF/CSV/metadata, false artifact hash or changed pixel fails the check. Other operating systems/architectures are not qualified by this policy.

Nine regression tests enforce strict mode, the explicit encoding allowance, changed-pixel/PDF/CSV/metadata rejection and artifact-hash consistency. This policy does not waive source restrictions, missingness rules, benchmark-only status, excluded FIU claims, live-acquisition gates or final publication approval. Local Linux execution is separate from remote Ubuntu GitHub Actions, which has not run.
