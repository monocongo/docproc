# Phase 0 go-adjust-cut gate

Phase 0 must produce one auditable **Overall Phase 0 outcome** before durable walking-vertical application code begins. A Go requires every retained path to satisfy every applicable Selection gate; there is no majority vote, conditional Go, or undocumented waiver. This resolves [issue #11](https://github.com/monocongo/docproc/issues/11).

This branch is documentation only. It does not authorize acquisition, locks, spike harnesses, services, parser/model execution, scoring, pipeline code, or infrastructure.

## Accepted inputs

This gate incorporates these commit-pinned decisions and evidence by reference:

- [Public accuracy benchmark and FUNSD role at `4c1714d`](https://github.com/monocongo/docproc/blob/4c1714d372a89d2ee99373a2bccbd33c6cd66e9c/docs/adr/0001-public-evaluation-corpus.md)
- [Phase 0 VLM/serving contract at `cabf749`](https://github.com/monocongo/docproc/blob/cabf7490a7a66fd8b4cf6f00ea6207c78dd50f5c/docs/decisions/phase-0-vlm-serving-contract.md)
- [Walking-vertical acceptance at `a5e4205`](https://github.com/monocongo/docproc/blob/a5e4205b597b70f15c2ce73421d361a0f0e2b799/docs/decisions/walking-vertical-acceptance.md)
- [Parser candidate and hard-gate research at `0e4fbf3`](https://github.com/monocongo/docproc/blob/0e4fbf3f87989ed0002ca5e24add68b6fda0a055/docs/research/parser-spike-candidates.md)
- [Artifact and licensing gates at `a6a0ce8`](https://github.com/monocongo/docproc/blob/a6a0ce8014391d7956801154a39b8061fa8940f8/docs/research/dependency-artifact-licensing-gates.md)
- [Open-form corpus profile at `532b1fb`](https://github.com/monocongo/docproc/blob/532b1fb1f9b948510e4296dad4c9fe3092d2681e/docs/research/open-real-form-evaluation-corpus.md)

The Docling-only rule recorded by issue #17 and carried into the commit-pinned walking-vertical contract governs parser measurement: no Marker, direct Surya, or preemptive challenger is downloaded or run.

## Phase boundary

The sole Implementation authorization is the new, unedited issue #13 comment defined by the walking-vertical contract. It starts T0, permits the bounded Phase 0 evidence work below immediately, and conditionally permits durable Walking-vertical work only after Overall Phase 0 Go. Overall Go satisfies that condition; it is not a second authorization event:

- freeze environment, component, artifact, corpus, prompt/schema, scoring, and measurement contracts;
- explicitly acquire approved exact artifacts outside Git;
- create locks, inventories, notices, SBOMs, deterministic synthetic fixtures, and fixed corpus manifests;
- create only the minimal conformance/spike, scorer/report, health-probe, and fake-response harnesses needed to resolve these gates; and
- start the pinned MinIO/OpenSearch/host-Ollama processes needed for target-machine coexistence measurements.

Before overall Go, do not implement durable MinIO discovery, SQLite application persistence/orchestration, production Docling/VLM stages, immutable pipeline Artifact storage, OpenSearch indexing, Streamlit application views, queues, distributed infrastructure, or AWS/Kubernetes work. A spike adapter or record may be reused later only after Go; reuse does not make it an accepted application selection before measurement.

## Freeze order and valid measurements

Before the first measured parser or VLM request, content-address and retain:

1. reference-machine/OS record and monotonic/UTC clock source;
2. source commit plus clean/dirty state;
3. package/interpreter/host-tool/OCI/model/OCR/data locks and exact license/notice evidence;
4. `NAF-linked-v3`, `vlm-smoke-v1`, `parser-conformance-v1`, synthetic-fixture, and exclusion manifests;
5. parser/VLM request, timeout, resource, health, normalization, schema, evidence, and scoring contracts; and
6. report schema, gate version, expected checks, and allowed outcome routes.

Classify failure in this total order before assigning an outcome:

1. **Artifact admission first.** Artifact/tag/layer/license mismatch and unexpected component network attempts are classified by Gate LIC and #18 Gate A; they are never invalid measurements. A lock transcription error may be corrected only before execution with an audited record.
2. **Harness preflight second.** Before interpreting candidate behavior, prove the frozen request bytes/schema, endpoint/probe definitions, network-denial control, telemetry recorder, clocks, service baseline, and admitted-input manifest. A defect here is invalid, not Go/Adjust/Cut. Preserve and clean up, correct only that defect without changing a frozen candidate/input/rule, recompute affected harness digests, and restart the entire owning-gate measurement. A contract change is Adjust.
3. **Owning contract last.** After preflight passes, apply the owning contract's classifier exactly. For #18: explicit capability rejection is its Gate C; timeout/transport/non-capability 5xx is its Gate L; other 3xx/4xx and non-contract-valid 2xx envelopes are invalid as #18 specifies; contract-valid 2xx follows schema/repair/Gates S/E/R. For PARSER, timeout, missing outcome, invalid typed output, synthesized coordinates, failed table assertion, or hidden network is its hard-gate evidence. Required-service health/resource observations use Gate MACHINE. No broader phrase such as “candidate response failure” overrides these classifiers.

Changing a candidate, population, exclusion, threshold, timeout, request, artifact, or required observation is Adjust and requires an approved contract revision before remeasurement.

No convenient document drop, post-test threshold, silent artifact/tag update, mixed candidate aggregate, or unpublished failure is allowed.

## Gate LIC — licensing, artifacts, and offline reproducibility

Gate LIC applies to every byte actually acquired or executed: direct/transitive packages and native contents, interpreter, host tools, Docling layout/table/OCR files, Ollama server/model layers, NAF Data/license, MinIO/OpenSearch platform images and layers, and development/SBOM tooling.

### Go

- The admitted graph is exactly Docling-only with approved named Heron/TableFormer/RapidOCR/ONNX artifacts, optional macOS Vision diagnostic, host Ollama and only the currently admitted #18 candidate, unmodified direct-pull MinIO/OpenSearch, NAF, and no Marker/Surya/FUNSD/hosted inference.
- Every resolved artifact has authoritative origin/revision, final URL, size, digest, exact license-text hash or documented evidence class, copyright/notice data, distribution mode, and allow or explicitly approved review disposition.
- Locks include all arm64 wheels/native libraries, actual interpreter distributor/archive, qpdf/SQLite/Docker/Compose/Ollama/macOS records, every model/OCR file, and OCI index/platform manifest/config/layers. No unexpected download or `NOASSERTION` remains.
- Metadata-only model evidence and the Ollama conversion-lineage gap are retained as explicit reviewed exceptions; they are not described as verified provenance. CDLA/AGPL/MPL/LGPL/platform obligations use the distribution boundaries in the pinned licensing decision.
- SBOMs and generated notices reconcile to the resolved artifacts. The repository remains MIT. No model/OCR/data/OCI/binary payload forbidden by the licensing decision is committed, bundled, or mirrored.
- Prefetch under observation records every request; the exact parser/VLM measurement then completes with external network denied and no unlisted request.

### Candidate admission and final reconciliation

Gate LIC first pre-admits the base graph and primary 9B candidate. The 4B and Qwen3-VL fallback identifiers are retained as approved routes but their bytes are not initial downloads. When Gate VLM observes an exact named fallback trigger, it pauses before fallback acquisition/execution and re-enters Gate LIC for that candidate: review authoritative evidence, explicitly acquire under observation, inventory/lock every file/layer/license, and assign Go/Adjust/Cut. Only candidate-level LIC Go permits Gate VLM to resume. Candidate-level LIC Cut is #18 Gate A Cut; no other fallback is substituted.

After Gate VLM selects or cuts a candidate, Gate LIC performs final reconciliation over every byte acquired/executed, including abandoned candidates, and records one final LIC outcome. This nested admission is part of the already-approved fallback route, not Overall Adjust; changing the fallback identity or evidence policy is Adjust.

### Adjust

Stop dependent work and revise the artifact contract when an optional dependency can be removed, an over-broad downloader can be narrowed, an actual transitive/file differs from research, a reviewed distribution mode must become direct-pull-only, or an approved exact replacement can preserve the walking vertical. Rebuild all affected locks/SBOMs/notices and rerun every dependent measurement.

### Cut

Cut the artifact/component from the current initial implementation on unknown/denied terms, output-use conflict, unresolved required notice/source duty, forbidden surprise download, digest mismatch that is not merely a lock transcription error, or distribution mode that cannot satisfy obligations. If the cut item is required by the non-cuttable walking vertical and no separately approved replacement exists, the Overall Phase 0 outcome is Cut.

## Gate CORPUS — corpus and scoring viability

Gate CORPUS uses NAF only; FUNSD has no acquisition, smoke, comparison, fallback, or evaluator path.

### Go

- Explicit acquisition outside Git reproduces every `NAF-linked-v3` revision, asset identity, size/digest, license, split, image-manifest, count, and eligibility-ledger check from the pinned evidence. Any derived PDF uses one frozen lossless conversion recipe and is treated as Enhanced Data.
- The complete 77-page test split remains untouched by parser/VLM selection. Training supplies `vlm-smoke-v1` and the real-form portion of `parser-conformance-v1`; validation is reserved for pre-test design/threshold decisions.
- `vlm-smoke-v1` freezes exactly six training pages, source/converted hashes, eligible ground truth, exclusions, and selection rationale before model requests.
- The scoring contract freezes normalization, eligible-edge conversion, endpoint matching, repeated-label handling, ignored-edge behavior, thresholds, tie-breakers, exact/character metrics, and micro aggregation. Hand-computed tests pass.
- The full profile eligibility conversion reproduces 683 eligible pairs on 56 of 77 test pages and the pinned eligibility-ledger digest. This verifies corpus/scorer viability; no candidate output is evaluated on the test split in Phase 0.
- Corpus material, converted PDFs, local ledgers, and content-bearing outputs stay outside Git; clean-clone/ordinary CI remains synthetic-only and offline. Attribution and residual source-rights caveats are retained.

### Adjust

Stop on upstream disappearance, any identifier/hash/count/ledger/license mismatch, conversion drift, scorer ambiguity, or evidence that the fixed six-page smoke population was selected after observing candidate output. Do not substitute a mirror or another corpus silently; open a corpus/artifact decision, then rebuild and rerun affected gates.

### Cut

Cut NAF from the current blueprint if its grant/task fit is withdrawn or contradicted, required source/output use cannot be accepted, or the exact profile cannot be reproduced. Public evaluated accuracy remains non-cuttable, so cutting NAF makes the Overall Phase 0 outcome Cut until a separately qualified public benchmark and revised blueprint are approved.

## Gate PARSER — Docling parser conformance

`parser-conformance-v1` is frozen before execution and contains five fixed NAF training forms spanning handwriting, dense fields, checkboxes, weak image quality, and rotation, plus project-authored synthetic two-column, table, and embedded-image PDFs. It records every source/render/ground-truth digest and exclusion.

Run exact locked Docling standard PDF pipeline with full-page OCR for image-only forms and explicit RapidOCR/ONNX; disable automatic OCR selection. A small paired macOS Vision run is diagnostic only and cannot become the portable default. Prefetch only approved artifacts, then run with external network denied. Use a 300-second parser timeout per document and record cold/warm measurements separately.

### Go

Gate PARSER owns commit-pinned parser hard gates 1–6 and 8. It collects, but does not classify, the telemetry for original hard gate 7; Gate MACHINE exclusively resolves parser resource/coexistence after Gate VLM selects a candidate. Gate PARSER Go requires:

1. reproducible Python 3.12 arm64 macOS installation;
2. candidate-level Gate LIC Go for every code, dependency, model, and OCR artifact;
3. local measured execution after explicit prefetch with no hidden network or hosted path;
4. completion within 300 seconds and explicit outcome for every admitted page/document;
5. valid typed internal-document output with stable page numbering, text blocks, reading order, source references, and upstream coordinates that are never synthesized;
6. every required synthetic-table row, column, text, and span assertion; and
8. complete package/model/OCR/configuration identities sufficient for a parse fingerprint.

The run must also retain complete parser RSS, memory-pressure, swap, timing, and local-service-health telemetry for Gate MACHINE. PARSER neither marks that resource evidence Go nor routes a resource fallback.

The full scorecard reports word recall/CER, coverage, coordinate coverage, reading order, synthetic assertions, cold/warm latency, RSS/memory, output/download size, failures, nondeterminism, and normalization/provenance loss. No parser word-recall threshold is invented for the Docling-only conformance spike.

### Adjust

Any valid-measurement Docling-owned hard-gate failure is Adjust, exactly as issue #17 decided. Stop durable implementation and open a focused parser-replacement decision; Marker/Surya is not automatically reconsidered, and no replacement is downloaded or run before fresh technical/licensing approval. A revised parser must rerun Gates LIC, PARSER, MACHINE, and every dependent VLM context measurement.

### Cut

Cut Docling immediately on a Gate LIC Cut or evidence that its required artifacts/outputs cannot be used. If a focused replacement decision finds no parser that passes the same non-cuttable scanned-form/typed-provenance contract, cut the current initial PDF-processing implementation rather than weakening that contract.

## Gate VLM — local VLM serving and extraction

Gate VLM incorporates the exact #18 candidate artifacts, population/scoring contract, request transitions, timeout/cleanup rules, coexistence health policy, fixed cold/warm matrix, measurements, Gates A/M/L/C/S/E/R, and ordered fallback table without reinterpretation.

### Go

Go with exactly one candidate only after it passes every applicable #18 gate:

- start with `qwen3.5:9b-q4_K_M` through exact host Ollama `v0.32.6`, one page/request, concurrency one, non-thinking, complete schema constraint, temperature zero, seed 42, explicit 16K context, 4096 output cap, and deterministic one-repair transition;
- verify all manifest/config/model/license/parameter layers, server asset/version, quantization, vision capability, upstream evidence, and the explicit unverified-conversion-lineage state before inference;
- complete the six-page NAF-training image-only and image-plus-Docling-context matrices under the frozen scorer, preserving every request/response/repair/failure and selected context variant;
- pass the exact memory/coexistence and 90-second warm total-page rules, the per-repetition five-of-six final schema-valid rule, admitted-page/evidence rules, and complete evaluated report; and
- select image-plus-parser-context only under #18's strict dominance rule; otherwise use image-only.

Schema-valid, evidence-grounded, and evaluated accuracy are reported separately. There is deliberately no Phase 0 F1 threshold; measured misses and extra predictions remain visible and do not become a hidden model-selection threshold.

### Named fallback routing inside Gate VLM

- A 9B memory/latency failure tests exact `qwen3.5:4b-q4_K_M` under the identical contract.
- A Qwen3.5 structured-serving compatibility failure tests exact `qwen3-vl:8b-instruct-q4_K_M` under the identical contract.
- Gate A failure cuts that artifact. Qwen3-VL failure or non-compatibility S/E/R failure follows #18's Cut rows. No fallback is authorized for low evaluated accuracy, evidence failure, preference, context regression, or an unmeasured concern.

Testing a named fallback is not an Overall Adjust when it follows the already-approved frozen #18 table; the final Gate VLM result records only the selected candidate's Go or the terminal result.

### Adjust

Any change outside the named table—candidate, Ollama release, context, timeout, population, schema, prompt contract, health/resource rule, fallback reason, or hosted/remote route—is Adjust and requires a new serving-contract decision plus reruns of Gates LIC, VLM, MACHINE, and affected parser-context/scoring evidence.

### Cut

Cut local VLM extraction exactly when #18's ordered table says Cut. Hosted inference and an unlisted model are not substitutes. Because selected local VLM extraction is non-cuttable in the walking vertical, a terminal Gate VLM Cut makes the Overall Phase 0 outcome Cut unless an explicitly revised project scope is approved.

## Gate MACHINE — reference-machine resources and local coexistence

Gate MACHINE uses the Apple M5, 32 GB unified memory, recorded macOS build, host Ollama, pinned MinIO/OpenSearch, and the exact parser/VLM contracts. Sample memory once per second and execute frozen two-second/no-retry service probes before, during, and after measured work.

### Go

- Docling completes `parser-conformance-v1` sequentially within its per-document timeout while MinIO/OpenSearch health remains accepted.
- The selected VLM candidate passes #18's exact warm-up/page deadlines, cleanup/unload checks, `/api/version`, `/api/ps`, MinIO, and OpenSearch predicates.
- Across each measured matrix: no OOM, process kill, cleanup failure, red memory-pressure sample, 30 consecutive seconds of yellow pressure, or service-health failure occurs; swap after unload and a 60-second idle is no more than 512 MiB above the corresponding pre-load baseline.
- Parser and selected-VLM RSS/model-memory/context/swap/timing records are complete. Cold and warm values are not mixed, and no estimate substitutes for telemetry.

### Adjust

A parser resource failure is the original Docling hard-gate-7 failure: Gate MACHINE is Adjust and opens the focused parser-replacement decision required by issue #17. If MACHINE exposes the primary 9B's exact #18 memory/latency trigger before 4B has been tried, it may re-enter the already-named 4B route once: pause MACHINE, obtain candidate-level LIC Go, execute the complete 4B Gate VLM matrix from the beginning, then execute the complete MACHINE matrix from the beginning. No primary-candidate VLM/MACHINE result carries forward. A MACHINE failure for 4B or Qwen3-VL is terminal under #18; no re-entry occurs. Context reduction, service removal, timeout change, or pressure/swap threshold change is Adjust and requires the owning contract decision plus complete affected reruns.

### Cut

Cut a candidate on its owning gate's terminal resource rule. If no approved Docling path and no approved VLM candidate can coexist with the required local services on the reference M5, the Overall Phase 0 outcome is Cut; do not remove MinIO/OpenSearch from the evidence run or replace local inference with hosted inference.

## Gate WALK — walking-vertical compatibility

### Go

- Gates LIC, CORPUS, PARSER, VLM, and MACHINE retain exact MinIO, SQLite, Docling, selected host Ollama, OpenSearch, Streamlit, synthetic walking document, and basic correctness scope required by the commit-pinned walking-vertical contract.
- The selected parser/model/context fits the unchanged critical-path stages without deleting a non-cuttable stage or test.
- The Implementation authorization/T0 record remains the sole new, unedited #13 comment linked to the final blueprint. The Phase 0 decision record is complete no later than `T0 + 48 hours`, leaving the pinned acceptance deadline at `T0 + 168 hours`.

### Adjust

If a gate outcome changes the walking contract or the Phase 0 decision record is not complete by `T0 + 48 hours`, stop measurements and clean up. Assign `adjust` with reason `phase0-window-expired-before-resolution` to every gate/criterion still lacking a final outcome, assign Gate WALK `adjust` unless it is already Cut, and compute Overall Adjust unless an existing Cut takes precedence. Revise the blueprint/acceptance contract and create a new, unedited Implementation authorization that links and explicitly supersedes the prior authorization; the prior conditional permission is revoked, and the replacement comment becomes the sole active authorization and new T0. Do not edit the prior comment or pretend the original seven-day target still applies.

### Cut

If an outcome requires removing a non-cuttable walking stage, typed boundary, local VLM, content identity/reuse, schema/evidence/provenance, SQLite authority, MinIO Artifacts, OpenSearch Projection, Streamlit inspection, or basic correctness tests, Gate WALK and the Overall Phase 0 outcome are Cut.

## Overall decision algorithm

Evaluate in this order: base/primary candidate-level LIC admission → CORPUS → PARSER-owned conformance → VLM (including nested fallback LIC admission) → MACHINE → final LIC reconciliation → WALK. The only bounded re-entry is MACHINE 9B resource failure → 4B LIC admission → complete 4B VLM rerun → complete MACHINE rerun; it occurs at most once and carries no prior-candidate measurements forward. Then record one final Go, Adjust, or Cut for each of the six gates. A named Gate VLM fallback and its candidate-level LIC admission are internal routes, not extra outcomes.

1. Any Cut makes the Overall Phase 0 outcome Cut.
2. Otherwise, any Adjust makes the overall outcome Adjust.
3. Only six Go results make the overall outcome Go.

An overall Adjust stops dependent work, opens named decision/issues, revises affected contracts/blueprint evidence, and requires all affected/downstream gates to rerun. An overall Cut stops the current initial implementation; it neither authorizes a reduced unreviewed pipeline nor closes the issue as success. Overall Go satisfies the condition on the Walking vertical scope already authorized by the sole Implementation authorization; later reliability, full NAF test benchmark, hardening, and distribution remain outside it.

## Required decision record

Produce machine-readable JSON plus Markdown with:

- gate-contract version and exact source decision/evidence commit links;
- authorization/T0 evidence and Phase 0 start/end UTC/monotonic intervals;
- reference hardware/OS and every environment/lock/manifest/report digest;
- every gate criterion with `go | adjust | cut`, evidence references, observed value, and rationale;
- invalid measurements and corrections, named fallback routes, excluded inputs with predeclared reasons, and all failures;
- selected parser/OCR/model/context and explicit unresolved provenance/license caveats;
- schema-valid, evidence-grounded, evaluated-accuracy, latency, memory, and resource results under their exact denominators;
- per-gate outcome, precedence calculation, Overall Phase 0 outcome, approver, and immutable timestamp; and
- content-safety classification for every retained/published record.

The approver publishes an unedited, explicitly **non-authorizing** issue comment linking the exact decision-record commit; it cannot serve as T0 or replace the active Implementation authorization. No gate is Go merely because the Markdown summary says so; every criterion must resolve to retained Gate evidence.
