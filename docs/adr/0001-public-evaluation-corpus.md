---
status: accepted
---

# Use NAF as the public accuracy benchmark and omit FUNSD

The blueprint will use the revision- and content-pinned **`NAF-linked-v3` evidence profile** as its sole public accuracy benchmark for linked form fields. Clean-clone acceptance remains synthetic-only, and FUNSD is omitted rather than maintained as a restricted comparison. This resolves [issue #15](https://github.com/monocongo/docproc/issues/15) without authorizing corpus tooling or pipeline implementation.

## Evidence relied on

This decision incorporates the findings and caveats of these commit-pinned artifacts by reference rather than restating their research:

- [NAF corpus qualification and `NAF-linked-v3` profile](https://github.com/monocongo/docproc/blob/532b1fb1f9b948510e4296dad4c9fe3092d2681e/docs/research/open-real-form-evaluation-corpus.md)
- [FUNSD corpus and terms assessment](https://github.com/monocongo/docproc/blob/093a663bdd6fa419ac2931c88ad1b9e5cda0da78/docs/research/funsd-corpus-assumptions.md)
- [Cross-cutting dependency, artifact, data, and output gates](https://github.com/monocongo/docproc/blob/a6a0ce8014391d7956801154a39b8061fa8940f8/docs/research/dependency-artifact-licensing-gates.md)

NAF is selected because its publisher grant and explicit relationship annotations satisfy the public accuracy benchmark's engineering reuse and task-fit gates. The decision relies on the publisher's rights representation, not independent image-by-image chain-of-title verification. FUNSD's similar task fit does not justify a second acquisition, conversion, evaluator, terms-acceptance, and reporting path under its non-commercial restrictions and mutable availability.

## Required boundaries

These boundaries constrain the final blueprint. They do not add acquisition, conversion, evaluation, parser, VLM, or infrastructure work to this decision branch.

### Clean clone and ordinary CI

- The repository, default setup, tests, demos, screenshots, and ordinary CI use only project-authored or separately cleared synthetic fixtures.
- A clean clone neither contains nor downloads NAF or FUNSD scans, annotations, transcriptions, crops, converted PDFs, image-bearing outputs, or derived eligibility ledgers.
- Clean-clone acceptance is not an accuracy claim. The public accuracy benchmark is an explicit, separately authorized run and is never a prerequisite for ordinary CI.
- Ordinary CI and synthetic checks run without external network access.

### NAF acquisition and conversion

- Acquire NAF explicitly outside Git and only from the publisher origins identified by `NAF-linked-v3`; do not silently use a mirror or mutable substitute.
- Before use, fail closed unless every revision, asset identity, size, digest, license record, split record, image manifest, and eligibility-ledger check required by the pinned profile matches. Upstream change, disappearance, or mismatch stops the run for review.
- Preserve outside Git an acquisition record, the exact CDLA agreement, publisher identification, citation, existing notices or metadata, and practical source links.
- External network access is acquisition-only. After verified prefetch, measured parser and VLM runs deny external network access; dataset availability is not a runtime dependency.
- Convert JPEGs locally with a separately frozen, lossless, content-addressed recipe. Treat converted PDFs as Enhanced Data, preserve attribution, and mark the conversion. Conversion does not broaden source rights.

### Redistribution, attribution, and public output

- The project does not commit, mirror, bundle, or publish NAF source Data, annotations, local eligibility ledgers, or converted PDFs by default, even though the publisher grant permits publication subject to conditions.
- Default public accuracy benchmark output is limited to aggregate metrics and exclusion counts, non-content-bearing configuration and provenance records, and synthetic screenshots. It excludes NAF images, crops, transcriptions, document-level text/model responses, and image-bearing reports.
- Any later publication of Data or Enhanced Data requires a separate distribution review. It must make the CDLA agreement, its name, or a practical copy/link available; preserve existing provider attribution, legal notices, metadata, provider identification, and practical source links; and mark changes prominently.
- Output claimed to be de-minimis Results still requires source/output-rights review before publication. The public accuracy benchmark must retain the pinned research's residual source-rights caveat and must not claim independently proven chain of title.

### Evaluation and ignored ground truth

- The primary accuracy run uses all 77 pages in the canonical `NAF-linked-v3` test split, including pages with no eligible linked pair. Training pages are limited to smoke work, validation pages to design and threshold choices, and the test split to final reporting.
- The evaluator must reproduce the profile's strict eligibility rule, expected 683 eligible pairs on 56 pages, exclusion counts, and eligibility-ledger digest before scoring. A mismatch fails closed; it is not repaired by dropping documents or annotations.
- Every excluded edge remains in a local ignore ledger with its reason. Ignored ground truth contributes neither a true positive nor a false negative and is absent from accuracy denominators.
- First match predictions one-to-one against eligible edges under the frozen benchmark matching contract. A remaining prediction is ignored only when both of its evidence endpoints match the corresponding endpoints of the same ignored edge under that contract. Each ignored edge can consume at most one prediction, and deterministic tie-breaking is required.
- A page, one matching endpoint, nearby text, or overlap with an endpoint from a different ignored edge never creates a page-wide or region-wide exemption. Every remaining unmatched prediction is a false positive, including predictions on the 21 test pages with no eligible pair.
- Matching, normalization, overlap thresholds, and tie-breakers must be frozen using validation data before the test run and recorded in the benchmark configuration. This corpus-role decision does not invent those evaluator parameters.
- Report **schema-valid**, **evidence-grounded**, and **evaluated accuracy** separately. None substitutes for another, and no blended “quality” result may obscure them.
- Report annotation exclusions/noise, public-release contamination risk, and the exact profile identity alongside results. Claims are limited to historical, noisy, single-page scanned forms and linked form fields; they do not extend to native PDFs, multi-page ordering, broad reports, modern invoices, or rich tables.

### FUNSD

- FUNSD has no supported role in the blueprint: no acquisition, conversion, evaluator adapter, smoke set, public accuracy benchmark, report, screenshot, CI job, or fallback path is planned.
- Its pinned research remains rationale for this decision, not authorization to use or redistribute the corpus.
- Reintroducing FUNSD requires a new named decision that establishes a necessary comparison goal, explicit acceptance and fit with the then-current authoritative terms, fail-closed acquisition, and the existing non-redistribution boundaries. It is never an automatic substitute for unavailable or changed NAF artifacts.

## Consequences

The project has one public accuracy benchmark and one synthetic clean-clone acceptance path instead of two real-form corpus policies. This reduces legal, reproducibility, evaluator, and reporting surface while preserving a technically aligned benchmark. It also deliberately narrows what public results can establish; broader document classes require separately qualified evidence rather than extrapolation from NAF.
