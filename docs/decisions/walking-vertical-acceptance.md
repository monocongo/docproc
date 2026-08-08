# Accelerated walking-vertical acceptance

The first implementation target is one complete walking vertical within **seven elapsed days of implementation authorization**. This is a scope-control target, not a deadline or authorization to implement on this branch. The existing fourteen-day sequence remains illustrative and must be reordered around the vertical rather than treated as a promise that end-to-end work waits until its eleventh day.

This decision resolves [issue #9](https://github.com/monocongo/docproc/issues/9). It assumes issue #11 later authorizes a Phase 0 outcome compatible with local VLM extraction; a cut or incompatible adjustment must revise this contract before implementation begins.

## Accepted inputs

This contract reconciles the protected blueprint with the accepted decision map rather than revising the blueprint now:

- [Current PR #2 blueprint at `ca4ea1b`](https://github.com/monocongo/docproc/blob/ca4ea1ba2e1ffb4178aa52ac86a9f6d3a6100636/docs/planning/pdf-processing-pipeline-plan.md)
- [NAF public-accuracy/FUNSD decision at `4c1714d`](https://github.com/monocongo/docproc/blob/4c1714d372a89d2ee99373a2bccbd33c6cd66e9c/docs/adr/0001-public-evaluation-corpus.md)
- [Phase 0 VLM serving contract at `cabf749`](https://github.com/monocongo/docproc/blob/cabf7490a7a66fd8b4cf6f00ea6207c78dd50f5c/docs/decisions/phase-0-vlm-serving-contract.md)
- [Parser candidate and gate research at `0e4fbf3`](https://github.com/monocongo/docproc/blob/0e4fbf3f87989ed0002ca5e24add68b6fda0a055/docs/research/parser-spike-candidates.md)
- [Artifact and licensing gates at `a6a0ce8`](https://github.com/monocongo/docproc/blob/a6a0ce8014391d7956801154a39b8061fa8940f8/docs/research/dependency-artifact-licensing-gates.md)

This commit-backed contract carries forward issue #17's accepted outcome: the walking vertical uses only Docling; Marker and direct Surya are absent, and a Docling hard-gate failure stops for a new replacement decision.

## Clock and scope rule

- **T0** is the `createdAt` of a newly created, unedited issue #13 resolution comment that links the already-pushed final-blueprint commit and explicitly approves it and authorizes implementation. The authorization comment must have `lastEditedAt = null`; editing it invalidates that authorization and requires a new comment with a new T0. Without such a comment, implementation is not authorized and the clock has not started.
- The target is acceptance by `T0 + 7 × 24 hours`. Delaying the first implementation commit cannot move T0. Research, decision, and blueprint-editing time before T0 does not consume the interval.
- Missing the target does not waive an acceptance condition or silently extend scope. Record the observed blocker, cut a deferred feature first, and obtain an explicit adjustment if an agreed vertical stage cannot fit.
- MinIO, SQLite, Docling, the selected host-Ollama model, OpenSearch, and Streamlit are all vertical stages. None may be replaced by an in-memory fake, skipped, or deferred in the walking-vertical acceptance run.
- The one-PDF path takes priority over extra document classes, batch behavior, UI polish, broad failure handling, performance tuning, and the public accuracy benchmark.

## Seven-day critical path

The sequence is a capacity budget, not seven independent deadlines. Basic correctness tests are written with each slice rather than postponed:

| Elapsed window | Critical-path outcome |
|---|---|
| T0–24h | Freeze locks/contracts, explicitly acquire and verify NAF outside Git, freeze the six-page `vlm-smoke-v1` and scoring manifests, complete the smoke scorer/report harness required by Gate R, generate the walking document, and start the minimal local services/test harness. |
| 24–48h | Execute the bounded Docling conformance and complete VLM selection gates, including the smoke evaluated report; stop on adjust/cut rather than coding around a failed gate. |
| 48–72h | Complete MinIO discovery, content identity, SQLite registration of the Source object, Document, and Processing run, plus deterministic state tests. |
| 72–96h | Complete inspection, Docling normalization, typed internal representation, immutable artifacts, and provenance tests. |
| 96–120h | Integrate the selected model and already-complete scoring contract into the walking path; complete schema/repair transitions, synthetic-fixture scoring, persistence, and their basic correctness tests. |
| 120–144h | Complete the minimal OpenSearch projection and Streamlit inspection path. |
| 144–168h | Complete cached Processing run behavior, process restart/readback, the actual walking-vertical acceptance run, and its record. |

A Phase 0 adjustment that invalidates this budget stops the clocked plan for an explicit scope decision; it does not justify skipping a vertical stage.

## Fixed walking document

Walking-vertical acceptance uses one committed, project-authored, deterministic, single-page image-only form PDF with a committed source definition and ground truth. It contains at least three generic linked form fields, including one repeated label, with exact label/value text and source regions. Its generator inputs, generator version, seed, PDF bytes, page-render bytes, ground truth, and SHA-256 values are frozen.

The fixture is deliberately simple. It proves scanned-page intake, OCR/parser normalization, linked-field extraction plumbing, evidence display, and deterministic scoring mechanics without claiming extraction correctness or pretending to represent NAF or broad real documents. The walking document itself requires no downloaded corpus; the separate Phase 0 VLM gate still uses the explicitly acquired NAF training smoke population.

## Observable acceptance scenario

From a clean clone whose explicitly acquired packages, model/OCR artifacts, host Ollama, and service images already pass the Phase 0 lock and licensing gates, a maintainer can use documented commands to perform this scenario with external network access denied:

1. Start pinned localhost-only MinIO and OpenSearch, initialize the SQLite registry, verify host Ollama and the selected model, and start the worker and Streamlit inspector.
2. Generate or verify the exact walking PDF and upload it through MinIO, the only intake path.
3. Discover the Source object, stream its SHA-256, and register one Source object, one content-identified Document, and one Processing run under the frozen processing definition. Record its compatibility fingerprint: the digest of parser, OCR, renderer, model, prompt, schema, and every relevant configuration identity.
4. Inspect the PDF under fixed page/size bounds and record that it is a one-page image-only form.
5. Parse it with the Phase 0 Docling configuration and normalize the result into the typed internal document representation with page, region, parser, configuration, and artifact provenance.
6. Send exactly one page through the selected host-Ollama serving contract, preserve the first and any repair attempt, produce a non-empty schema-valid extraction, and retain checkable visible evidence for every emitted field.
7. Validate and persist the accepted extraction, raw attempts, stage timings, failures/warnings, and content-addressed artifact references. No stage may be reported successful if an admitted page or required artifact is missing.
8. Upsert the successful producer Processing run and linked fields into OpenSearch without making it the system of record.
9. Find the Document through OpenSearch and inspect in Streamlit the original synthetic page, parsed blocks, extracted fields, schema-valid status, evidence regions, raw/repair attempts, stage status, timings, and complete artifact/configuration provenance.
10. Score the accepted extraction against the synthetic ground truth and display schema-valid, evidence-grounded, and evaluated accuracy separately. The walking-vertical acceptance run must emit pair precision, recall, and F1, but no F1 threshold determines acceptance.
11. Upload the same bytes under a second MinIO key. Observe a second Source object linked to the same Document, plus a new `CACHED` Processing run with its own run ID, `cache_hit=true`, the identical compatibility fingerprint, a producing-run reference, and references to the producer's immutable artifacts. No parser or model call occurs for the cached Processing run, and UI provenance distinguishes both Source objects and both Processing runs.
12. Record application process identities, stop them, start fresh processes, and confirm SQLite still supplies authoritative Processing run state, MinIO still supplies immutable source/artifact bytes, OpenSearch still finds both Processing runs, and Streamlit still renders the same persisted producer and cache-reuse result with zero new parser or model calls.

Acceptance requires one non-empty schema-valid, inspectable extraction result; an explicit model/page failure is correct accounting but does not complete this walking vertical. Evaluated accuracy may be low and must remain visible. A schema-valid response and visible evidence cannot be presented as correctness.

## Basic correctness tests that ship with the vertical

Ordinary CI runs these deterministic tests offline, with no NAF/model/OCI acquisition and no live Ollama inference:

1. **Fixture determinism:** the source definition regenerates the expected PDF, page render, ground truth, and digests; every fixture input is project-authored or separately cleared.
2. **Content identity:** identical fixture bytes under different object keys map to one Document and distinct Source objects; distinct fixture bytes produce distinct digests and Document identities.
3. **Processing run identity and reuse:** the same Document plus compatibility fingerprint creates a new `CACHED` Processing run that identifies its Source object and producer Processing run and reuses immutable artifact references; any parser, OCR, renderer, model, prompt, schema, or relevant configuration digest change creates a new producer Processing run and forbids stale reuse.
4. **State transitions:** only allowed stage transitions occur; incomplete pages/artifacts and a schema-invalid final response cannot become `SUCCEEDED`; rerunning a completed transition is idempotent.
5. **Typed boundaries:** representative valid internal-document, extraction, evidence, error, and run-manifest records validate; invalid page numbers, missing artifact digests, invented block references, and inconsistent field/evidence pages are rejected.
6. **Repair semantics:** a schema-valid first response is accepted without repair; a schema-invalid first response followed by a schema-valid repair becomes the accepted extraction; and a schema-invalid repair becomes explicit failure. Exactly one repair attempt is preserved whenever the first response is schema-invalid.
7. **Provenance closure:** every accepted field resolves to the source object version, document digest, page render, parser artifact, model attempt, prompt/schema/configuration identities, and visible source region.
8. **Persistence contracts:** SQLite uniqueness/transaction tests enforce Source object, Document, producer Processing run, and cached Processing run identities. MinIO tests require write-if-absent, reject a conflicting write at an occupied immutable key, return and retain the created object version, then perform version-pinned readback with digest verification. OpenSearch mapping/upsert tests prove idempotent projection from an authoritative Processing run artifact.
9. **Scoring mechanics:** hand-computed linked-pair cases cover exact matches, misses, extra predictions, repeated labels, deterministic ties, and zero-prediction/zero-ground-truth denominators while keeping schema-valid, evidence-grounded, and evaluated accuracy results separate.
10. **Walking-path integration:** a deterministic test double exercises the complete orchestration path and failure accounting in ordinary CI; the walking-vertical acceptance run repeats the same scenario manually against the actual pinned local components.
11. **Fresh-process readback:** after persisted producer and cached Processing runs are written, terminate the application instance, open the state from a fresh instance, rebuild the same views, and assert through an inference-call spy that no parser or model request occurred.

A test double may prove orchestration in ordinary CI but never satisfies the walking-vertical acceptance run.

## Required acceptance record

The walking-vertical acceptance run produces a content-addressed record containing:

- issue #13 resolution-comment permalink and database ID, author, immutable `createdAt`, `lastEditedAt = null`, captured full body and SHA-256, linked final-blueprint commit, issue `closedAt`, computed T0/deadline, and walking-vertical acceptance-run absolute start/end timestamps;
- repository commit and clean/dirty state;
- fixture, both Source object/version identities, the Document identity, producer and cached Processing run IDs/statuses, `cache_hit`, compatibility fingerprint, producing-run link, and artifact references;
- dependency, interpreter, host-tool, model/OCR, Ollama, and OCI lock digests;
- parser, renderer, image policy, prompt, schema, scoring, and configuration digests;
- actual hardware/OS, service health, network-denied evidence, stage timings, and resource observations;
- first/repair model attempts, schema-valid and evidence-grounded results, evaluated accuracy metrics, warnings, failures, and exclusions;
- first-upload, duplicate-upload, and fresh-process-restart observations, including pre/post process identities and proof that no parser or model request occurred for the cached Processing run or post-restart readback; and
- commands used plus links or keys for every inspectable artifact.

The record reports what ran; it does not claim production readiness or public-corpus accuracy.

## Intentionally afterward

The following are not conditions for the seven-day walking vertical:

- the full `NAF-linked-v3` test-set public accuracy benchmark, public benchmark reporting, annotation-noise analysis, or contamination analysis beyond the required six-page training smoke selection;
- additional synthetic fixtures, native-text PDFs, multi-page ordering, rotation, tables, long reports, modern invoices, malformed/encrypted/oversized inputs, or broad document-type support;
- concurrent workers, queues, batch scheduling, near-duplicate detection, cache eviction, throughput/load testing, or distributed execution;
- automatic retry/backoff, lease recovery, parser-process termination, service-outage recovery, OpenSearch rebuild drills, backup/restore, or chaos testing;
- authentication, multi-tenancy, hostile-input isolation, malware scanning, secrets hardening, public deployment, or an offline distribution bundle;
- Streamlit styling, advanced filters, annotation/edit workflows, dashboards, embeddings, confidence routing, or model fine-tuning;
- broad operational benchmarks, full notices/SBOM release packaging, polished diagrams/blog/retrospective, and release tagging.

These items remain planned only where the final blueprint retains them. Reliability and public evaluation begin after the walking vertical; distributed infrastructure remains future-only.

## Cut order before weakening acceptance

If the seven-day target is threatened, cut UI styling, extra views/filters, extra fixtures, optional diagnostics, generalized abstractions, and packaging prose first. Do not cut typed stage boundaries, content identity, one-page Docling parsing, selected local VLM extraction, schema validation, visible evidence, immutable artifact/provenance records, SQLite authority, MinIO intake/artifacts, OpenSearch projection, Streamlit inspection, duplicate reuse, or the basic correctness tests above.
