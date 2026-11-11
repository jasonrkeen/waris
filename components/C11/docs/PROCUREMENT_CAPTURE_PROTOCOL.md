# Bounded public procurement capture protocol

Unreleased rc11, 18 October 2026. The old June procurement acquisition history was not recovered from the scoped retained extraction and Research-1 working project. A legacy run timestamp, source modification date, matching file hash or reconstructed default is not an authenticated historical HTTP request record.

Use the separate first-party capture tool for a clearly dated new sample:

```text
python tools/capture_prozorro_sample.py --private-output data/raw/UNIQUE_CAPTURE_DIRECTORY --details 50
```

This reads the public unauthenticated Prozorro API only. It does not run ACLED, fetch attachments, invoke the complete WARIS pipeline or publish anything. The fixed endpoint and bound are declared in a frozen dataclass plan: one descending-request feed page, at most 100 rows, default first 50 returned distinct IDs. No lifecycle/date filter or national completeness is implied. Nonunique IDs and unexpected counts fail. Extra pages are recorded but not followed. A failure stops the sample without replacement. A new output directory is mandatory.

Before requesting data, the tool records the plan and script hash. It journals every attempt before sending it, retains response bytes and hashes, requested/final URLs, UTC request/receipt times, status and only Date, ETag, Last-Modified and Content-Type headers when supplied. Redirects are disabled; an unexpected status/URL or mismatched detail identity fails. A partial/failed capture remains visibly partial. Authorization is explicitly excluded from provider requests, including implicit netrc credentials; environment proxy/CA configuration is preserved. Cookies/authorization headers are not logged. Source bodies and record-linkable receipt URLs are PRIVATE, not licensed for publication by this tool.

Only a complete, hash-verified acquisition may feed its corresponding review; retain raw snapshots privately where authorized. Exact replay uses frozen responses rather than current mutable API records. Recorded client times and optional server headers support traceability, not a digital signature or independent clock certification. The new before-request plan is not a preregistration of research hypotheses or evidence that the original acquisition was recovered. Provider rights, missing-field meaning, source representativeness, methodological validation and selected-output clearance remain separate.

Choose a new directory under the ignored data/raw tree or a private location outside the checkout. Keep source bodies and record-linkable receipts out of Git and public archives.
