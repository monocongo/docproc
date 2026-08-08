# Local PDF-processing pipeline blueprint

- **Status:** Proposed; implementation is not authorized by this document.
- **Scope:** One local, single-worker PDF-processing walking vertical and its later hardening boundaries.
- **Decision baseline:** The commit-pinned sources below. This blueprint is the sole implementation specification; it is not a development diary.

## Purpose and non-goals

The target is a locally operated path from one synthetic PDF to retained, inspectable typed extraction results. It uses MinIO, SQLite, Docling, host Ollama, OpenSearch, and Streamlit only if the separately authorized Phase 0 evidence work reaches an Overall Go.

This blueprint does not authorize implementation, corpus/model acquisition, external publication, an Implementation-authorization/T0 comment, or a merge. It does not add queues, PostgreSQL, Kubernetes, EKS, AWS services, hosted inference, a second worker, a second database, or distribution infrastructure. Later hardening and public evaluation are requirements for later phases, not prerequisites silently folded into the walking vertical.

`schema-valid`, `evidence-grounded`, and `evaluated accuracy` are separate results. Neither a valid schema nor cited evidence establishes evaluated accuracy, and no quality aggregate substitutes for them.

## Commit-pinned decision evidence

Each `SRC-*` below is a full-SHA-pinned artifact. `SRC-PLAN` is reconciliation input only, not accepted Decision evidence. A research source supports the later decision that uses it; it cannot override that decision. The Docling-only outcome is carried by `SRC-WALK`, not by a mutable issue comment.

| ID | Source | Governs |
|---|---|---|
| `SRC-PLAN` | [Protected PR #2 candidate](https://github.com/monocongo/docproc/blob/ca4ea1ba2e1ffb4178aa52ac86a9f6d3a6100636/docs/planning/pdf-processing-pipeline-plan.md) | Reconciliation input only. |
| `SRC-CORPUS` | [Public evaluation corpus decision](https://github.com/monocongo/docproc/blob/4c1714d372a89d2ee99373a2bccbd33c6cd66e9c/docs/adr/0001-public-evaluation-corpus.md) | NAF role, synthetic clean clone, FUNSD omission, and reporting/publication limits. |
| `SRC-VLM` | [Phase 0 VLM/serving contract](https://github.com/monocongo/docproc/blob/cabf7490a7a66fd8b4cf6f00ea6207c78dd50f5c/docs/decisions/phase-0-vlm-serving-contract.md) | Candidate/model contract, request matrix, gates, and named fallbacks. |
| `SRC-WALK` | [Walking-vertical acceptance](https://github.com/monocongo/docproc/blob/a5e4205b597b70f15c2ce73421d361a0f0e2b799/docs/decisions/walking-vertical-acceptance.md) | T0, seven-day target, actual-component scenario, basic tests, and later boundary. |
| `SRC-EVOLVE` | [Local-to-distributed evolution](https://github.com/monocongo/docproc/blob/2006944aec59b5052e00192bc5844f986a55b5f7/docs/decisions/local-to-distributed-evolution.md) | Identity, records, claims, cache reservation, adapters, and absent distributed systems. |
| `SRC-P0` | [Phase 0 go-adjust-cut gate](https://github.com/monocongo/docproc/blob/d5e0f3dfca08f6bc11ad02a6ee275aef0e43b2f9/docs/decisions/phase-0-go-adjust-cut-gate.md) | Six gates, validity, precedence, authorization, and decision record. |
| `SRC-LICENSE` | [Artifact and licensing gates](https://github.com/monocongo/docproc/blob/a6a0ce8014391d7956801154a39b8061fa8940f8/docs/research/dependency-artifact-licensing-gates.md) | Lock, inventory, notices, SBOM, offline, and distribution requirements. |
| `SRC-NAF` | [Open-form corpus research](https://github.com/monocongo/docproc/blob/532b1fb1f9b948510e4296dad4c9fe3092d2681e/docs/research/open-real-form-evaluation-corpus.md) | `NAF-linked-v3` facts and limits. |
| `SRC-FUNSD` | [FUNSD research](https://github.com/monocongo/docproc/blob/093a663bdd6fa419ac2931c88ad1b9e5cda0da78/docs/research/funsd-corpus-assumptions.md) | Omission rationale and stale-license correction. |
| `SRC-PARSER` | [Parser research](https://github.com/monocongo/docproc/blob/0e4fbf3f87989ed0002ca5e24add68b6fda0a055/docs/research/parser-spike-candidates.md) | Docling gates and Marker/Surya distinction. |
| `SRC-VLM-RESEARCH` | [M5 VLM research](https://github.com/monocongo/docproc/blob/cc144e6239b4d4dff37f8325ad6feb70dc2d77f9/docs/research/local-vlm-serving-m5.md) | Research-time artifact evidence and measured-evidence gap. |
| `SRC-TRACE` | [Traceability decision](https://github.com/monocongo/docproc/blob/30fa592efcde4d45c0f6053518ac5937ae843578/docs/decisions/blueprint-traceability-evidence.md) | IDs, trace matrix, evidence, and publication boundary. |

## Domain language

- A **Source object** is one occurrence of received PDF bytes. A **Document** is the content identity shared by Source objects with exactly those bytes.
- A **Processing request** is the idempotent intention to create one **Processing run**. A Processing run is one attempt under one Processing request and one immutable **Processing definition**; a cache hit has its own run ID and status.
- A **Stage attempt** is one execution attempt for a named stage. A **Work claim** is time-bounded, fenced authority for a worker to advance it.
- An **Artifact** is immutable content/kind identity. An **Artifact reference** is its exact version-pinned, digest-verifiable occurrence.
- A **Projection** is rebuildable derived state; OpenSearch is a Projection and never authoritative processing state.
- A **synthetic fixture** is project-authored test material. **Clean-clone acceptance** uses only such fixtures. A **public accuracy benchmark** is the later NAF measurement. An **evidence profile** identifies its data and rules.
- A **candidate model** is not a **selected model**. A **walking vertical** is the intended system; a **walking-vertical acceptance run** is its future actual-component observation.
- A **Selection gate** resolves a contract criterion. A **valid measurement** follows the frozen contract. **Go**, **Adjust**, **Cut**, **Overall Phase 0 outcome**, **Implementation authorization**, and **T0** have the meanings in `SRC-P0` and `SRC-WALK`.

Actual-component Phase 0 and walking execution are future Conformance work. They are not evidence produced by this blueprint. T0 begins only with the separately authorized, exact Implementation-authorization form specified by `SRC-P0`/`SRC-WALK`; a review note, approval request, or ordinary issue/PR comment does not start it.

## Required local topology

```text
source PDF → MinIO → one polling worker → Docling → host Ollama
                    ↘ SQLite authoritative state
                    ↘ OpenSearch Projection
Streamlit reads SQLite, MinIO Artifacts, and the OpenSearch Projection
```

MinIO, OpenSearch, Streamlit, and host Ollama bind localhost-only; SQLite is the embedded authoritative registry, and Docling runs through the worker. No listener is a hosted or LAN-facing service.

## Normative requirements

IDs use `REQ-<FAMILY>-<NNN>`. Each requirement has one observable subject; changed requirements are superseded, not renumbered.

| ID | Normative requirement |
|---|---|
| `REQ-SCOPE-001` | The runtime MUST remain entirely local with one polling worker and no hosted inference or cloud critical path. |
| `REQ-SCOPE-002` | The implementation MUST retain MinIO, SQLite, OpenSearch, Streamlit, Docling, and host Ollama in the walking vertical. |
| `REQ-SCOPE-003` | The fourteen-day sequence MUST be treated as illustrative; walking-vertical acceptance MUST target `T0 + 168 hours`. |
| `REQ-SCOPE-004` | The repository license MUST remain MIT unless a maintainer separately changes it. |
| `REQ-SCOPE-005` | Every walking-vertical service MUST bind only to localhost and MUST expose no externally reachable listener. |
| `REQ-DOMAIN-001` | The system MUST use the `docproc-identity-v1` framing and distinguish Source object, Document, Processing request, Processing run, Stage attempt, and Work claim. |
| `REQ-DOMAIN-002` | A Processing definition MUST be immutable and versioned canonical records MUST preserve the identity relationships it governs. |
| `REQ-ART-001` | Artifact writes MUST be create-if-absent and metadata success MUST follow version-pinned readback and digest verification. |
| `REQ-ART-002` | Measured runs MUST use exact acquired artifacts and deny external network access after observed prefetch. |
| `REQ-CORPUS-001` | Ordinary CI and clean-clone acceptance MUST be deterministic, synthetic-only, and offline. |
| `REQ-CORPUS-002` | The only public accuracy benchmark MUST be `NAF-linked-v3` under its pinned profile, split, eligibility, scoring, and publication rules. |
| `REQ-CORPUS-003` | FUNSD MUST be absent from acquisition, CI, evaluation, screenshots, reports, fallback paths, and Git content. |
| `REQ-PARSER-001` | Phase 0 parser conformance MUST use Docling only with full-page RapidOCR/ONNX and no automatic OCR, Marker, or Surya. |
| `REQ-PARSER-002` | Parser conformance MUST enforce its owned hard gates and a 300-second-per-document limit without inventing a word-recall threshold. |
| `REQ-VLM-001` | Phase 0 MUST measure only the exact `qwen3.5:9b-q4_K_M` host-Ollama candidate under the frozen request, matrix, artifact, provenance, resource, schema, evidence, and report contracts. |
| `REQ-VLM-002` | A VLM fallback MUST occur only through the named `qwen3.5:4b-q4_K_M` or `qwen3-vl:8b-instruct-q4_K_M` route and its exact trigger. |
| `REQ-RUN-001` | A successful Processing run MUST account for every admitted page and MUST NOT accept schema-invalid final output. |
| `REQ-RUN-002` | Reuse MUST create a distinct cached Processing run and MUST use an exact compatibility fingerprint that prevents stale reuse. |
| `REQ-STORE-001` | SQLite and MinIO MUST be authoritative for processing state and Artifacts, respectively; Artifact persistence MUST precede metadata success. |
| `REQ-STORE-002` | Work claims and cache reservation MUST be fenced, and OpenSearch MUST remain a rebuildable Projection. |
| `REQ-BOUNDARY-001` | Parser, VLM, storage, repository, search, and UI boundaries MUST exchange typed, versioned records and Artifact references without infrastructure identities escaping adapters. |
| `REQ-P0-001` | Before Overall Phase 0 Go, work MUST be limited to bounded evidence and MUST NOT create durable application implementation. |
| `REQ-P0-002` | Phase 0 MUST resolve LIC, CORPUS, PARSER, VLM, MACHINE, and WALK with `Cut > Adjust > Go` precedence and retain invalid measurements. |
| `REQ-P0-003` | Phase 0 MUST complete its decision record by `T0 + 48 hours`; authorization semantics MUST be sole and superseding as defined by `SRC-P0`. |
| `REQ-WALK-001` | Walking acceptance MUST execute the committed one-page synthetic scenario through every required local component and retain non-empty schema-valid result, evidence, and metrics. |
| `REQ-WALK-002` | Walking acceptance MUST demonstrate duplicate cached processing, fresh-process readback, basic offline tests, and an immutable acceptance record. |
| `REQ-EVIDENCE-001` | Every expected Conformance item MUST have an immutable machine record and human summary containing exact inputs, environment, outcomes, failures, exclusions, decision sources, and specification IDs. |
| `REQ-EVIDENCE-002` | Evidence publication MUST classify content and MUST NOT publish restricted data, derived content, model/OCR weights, OCI archives, third-party binaries, local paths, or secrets. |
| `REQ-LATER-001` | The full 77-page NAF test benchmark and public report MUST occur only after walking acceptance. |
| `REQ-LATER-002` | Reliability, security, performance, packaging, and any distribution initiative MUST remain later work; queues, PostgreSQL, Kubernetes, EKS, and AWS MUST remain absent until a measured future initiative. |

## Acceptance criteria

IDs use `AC-<FAMILY>-<NNN>`; every ID in this table cites exact requirement IDs. `AC-CROSS-*` is used only for a documented cross-family observation.

| ID | Requirement IDs | Observable acceptance criterion |
|---|---|---|
| `AC-SCOPE-001` | `REQ-SCOPE-001`, `REQ-SCOPE-002` | The documented component graph contains the six local components and one worker, and contains no hosted/cloud critical path. |
| `AC-SCOPE-002` | `REQ-SCOPE-003` | The plan labels the 14-day sequence illustrative and the walking target `T0 + 168h`. |
| `AC-SCOPE-003` | `REQ-SCOPE-004` | The repository license file and blueprint both identify MIT with no conflicting operative license assertion. |
| `AC-SCOPE-004` | `REQ-SCOPE-005` | Resolved walking service configuration and listener inspection show localhost-only bindings. |
| `AC-DOMAIN-001` | `REQ-DOMAIN-001`, `REQ-DOMAIN-002` | Canonical records and identity vectors distinguish each defined entity and reject a changed Processing definition as compatible reuse. |
| `AC-ART-001` | `REQ-ART-001` | An Artifact write/readback exposes exact version and digest before metadata success. |
| `AC-ART-002` | `REQ-ART-002` | Observed prefetch rejects every unlisted request/artifact, and locked parser and VLM measured reruns record zero external requests under enforced egress denial. |
| `AC-CORPUS-001` | `REQ-CORPUS-001`, `REQ-CORPUS-003` | The repository/CI content scan finds only cleared synthetic fixtures and no FUNSD material or dependency path. |
| `AC-CORPUS-002` | `REQ-CORPUS-002` | NAF acquisition, eligibility ledger, ignored-edge semantics, hand-computed scorer cases, and 77-page accounting reproduce the frozen profile. |
| `AC-PARSER-001` | `REQ-PARSER-001`, `REQ-PARSER-002` | A fixed Docling manifest records full-page OCR configuration, all hard-gate outcomes, timeout, telemetry, outputs, and failures. |
| `AC-VLM-001` | `REQ-VLM-001` | The frozen candidate matrix preserves request/repair/raw/schema/evidence/accuracy/resource/health results and distinguishes invalid measurements. |
| `AC-VLM-002` | `REQ-VLM-002` | A fallback is observable only after the named trigger and fresh candidate-level artifact admission; any other fallback attempt is rejected. |
| `AC-RUN-001` | `REQ-RUN-001`, `REQ-RUN-002` | Page coverage, deterministic repair, producer/cached runs, and compatibility fingerprint are visible in run records. |
| `AC-STORE-001` | `REQ-STORE-001`, `REQ-STORE-002` | Crash-window, claim-race, cache-reservation, transaction-order, and Projection-rebuild observations preserve the stated authority. |
| `AC-BOUNDARY-001` | `REQ-BOUNDARY-001` | Contract/import tests show typed versioned exchanges and reject backend, process, or local-path leakage. |
| `AC-P0-001` | `REQ-P0-001`, `REQ-P0-002`, `REQ-P0-003` | One Phase 0 record resolves all six gates, invalid runs, precedence, authorization/T0, deadline, and final outcome. |
| `AC-WALK-001` | `REQ-WALK-001`, `REQ-WALK-002` | The twelve-step actual-component scenario and eleven basic correctness groups pass with retained producer/cached/readback evidence. |
| `AC-EVIDENCE-001` | `REQ-EVIDENCE-001`, `REQ-EVIDENCE-002` | Every record validates against the evidence envelope, has exact spec references, and passes content/publication review. |
| `AC-LATER-001` | `REQ-LATER-001`, `REQ-LATER-002` | Later requirements are explicitly phased after walking acceptance and repository scans reject future-distribution infrastructure before a new initiative. |

## Planned tests and manual rubrics

IDs use `TEST-<KIND>-<NNN>`, where `KIND` is `UNIT`, `SCHEMA`, `CONTRACT`, `INTEGRATION`, `GOLDEN`, `E2E`, `BENCH`, or `MANUAL`. Each test states its population, preconditions, action, oracle, mode, and expected evidence kind.

| ID | AC / REQ | Population and action | Oracle / mode / evidence |
|---|---|---|---|
| `TEST-UNIT-001` | `AC-DOMAIN-001` | Identity/canonicalization vectors; construct Source objects, Documents, requests, and changed definitions. | Exact IDs and incompatibility result; offline; `EVID-TEST-REPORT-001`. |
| `TEST-CONTRACT-001` | `AC-ART-001` | Fixed Artifact bytes with forced duplicate and readback. | Create-if-absent, exact version/digest, metadata ordering; offline; `EVID-TEST-REPORT-002`. |
| `TEST-CONTRACT-005` | `AC-SCOPE-001`, `AC-SCOPE-004` | Resolved component configuration plus an authorized local-service run with external network denied. | Exactly one worker and six local components; inspect every network-service listener and require loopback-only binding with no hosted/cloud path; `EVID-TEST-REPORT-003`. |
| `TEST-CONTRACT-006` | `AC-SCOPE-002` | Blueprint schedule text under a fixed review checklist. | Labels 14 days illustrative and walking target exactly `T0 + 168h`; offline; `EVID-TEST-REPORT-004`. |
| `TEST-CONTRACT-007` | `AC-SCOPE-003` | Repository `LICENSE` and operative blueprint license assertions. | Both identify MIT and contain no conflicting operative license; offline; `EVID-TEST-REPORT-005`. |
| `TEST-CONTRACT-008` | `AC-CORPUS-001` | Clean clone, ordinary-CI selection, and repository content/dependency scan. | Only cleared synthetic fixtures are used; FUNSD and restricted corpus material are absent; offline; `EVID-TEST-REPORT-006`. |
| `TEST-CONTRACT-009` | `AC-LATER-001` | Repository configuration, import, and dependency scan before a later initiative. | No queue/PostgreSQL/Kubernetes/EKS/AWS path exists and the full benchmark remains post-walking; offline; `EVID-TEST-REPORT-007`. |
| `TEST-CONTRACT-010` | `AC-ART-002` | Observed prefetch followed by locked parser and VLM measured reruns with egress enforcement. | Every unlisted request/artifact is rejected; both reruns make zero external requests; authorized Phase 0; `EVID-LOCK-INVENTORY-001`. |
| `TEST-CONTRACT-002` | `AC-BOUNDARY-001` | Adapter contracts and import graph. | No infrastructure/local-path/process identity crosses a boundary; offline; `EVID-TEST-REPORT-008`. |
| `TEST-INTEGRATION-001` | `AC-STORE-001` | Claim/cache races and crash windows against actual local stores. | Fencing, deterministic replay, and rebuildable Projection; authorized local service run; `EVID-TEST-REPORT-009`. |
| `TEST-SCHEMA-001` | `AC-RUN-001` | Valid, invalid, and repaired extraction records across admitted pages. | Invalid final output cannot succeed; every page is accounted for; offline; `EVID-TEST-REPORT-010`. |
| `TEST-GOLDEN-001` | `AC-CORPUS-002` | Frozen scorer hand cases and eligibility ledger. | Exact ignored-edge, matching, denominator, and tie-break results; authorized corpus preparation; `EVID-CORPUS-VERIFICATION-001`. |
| `TEST-CONTRACT-003` | `AC-PARSER-001` | `parser-conformance-v1` under locked Docling/RapidOCR/ONNX configuration. | Owned hard gates, 300-second limit, telemetry, and no network; authorized Phase 0; `EVID-PARSER-CONFORMANCE-001`. |
| `TEST-CONTRACT-004` | `AC-VLM-001`, `AC-VLM-002` | Six-page frozen VLM matrix, primary then only named fallback after its candidate-level LIC admission is Go. | Exact request transition, gates, invalid classifications, fallback routing, and rejection of any fallback lacking its linked lock/inventory/admission record; authorized Phase 0; `EVID-VLM-CONFORMANCE-001`. |
| `TEST-INTEGRATION-002` | `AC-P0-001` | Six gate records and invalid-run fixtures. | `Cut > Adjust > Go`, `T0 + 48h`, and required fields; authorized Phase 0; `EVID-PHASE0-DECISION-001`. |
| `TEST-E2E-001` | `AC-WALK-001` | Committed one-page synthetic PDF through all actual local stages. | Twelve-step observation, result/evidence/metrics, and no re-execution for cached run; authorized walking run; `EVID-WALKING-VERTICAL-001`. |
| `TEST-E2E-002` | `AC-WALK-001` | Duplicate source and fresh process after producer run. | Cached run is distinct, readback succeeds, and basic correctness groups pass; authorized walking run; `EVID-WALKING-VERTICAL-001`. |
| `TEST-BENCH-001` | `AC-LATER-001` | Complete NAF 77-page test profile after walking acceptance. | Complete accounting and public-report caveats; separately authorized later run; `EVID-PUBLIC-BENCHMARK-001`. |
| `TEST-MANUAL-001` | `AC-EVIDENCE-001` | Evidence record and proposed publication pair. | Fixed rubric validates envelope/spec references/classification and that screenshots are not sole evidence; produces `EVID-TEST-REPORT-011`. |
| `TEST-MANUAL-002` | `AC-LATER-001` | A proposed future-distribution initiative after walking acceptance. | Fixed rubric verifies workload/SLO/security/licensing/migration evidence and rejects premature infrastructure; separately authorized later review; `EVID-DISTRIBUTION-REVIEW-001`. |

Test doubles establish orchestration and contracts only. They cannot satisfy actual-component Phase 0 or walking acceptance. Ordinary CI remains synthetic-only and offline; heavyweight parser, VLM, NAF, and service checks require their explicitly authorized run and must not publish unsafe artifacts.

## Evidence contract

Evidence IDs use `EVID-<KIND>-<NNN>`; `<KIND>` exactly spells one documented kind token below with its words joined by hyphens, and all cross-references use complete IDs. Independently retained observations use distinct IDs. Each immutable, content-addressed machine envelope contains at least:

```text
evidence_schema_version
evidence_id
kind
spec_refs[]
source_commit
producer_identity
produced_at_utc
inputs[]
environment_ref
contract_refs[]
outcome
failures[]
exclusions[]
artifact_refs[]
content_classification
publication_disposition
```

References are full commit SHAs or exact Artifact version-plus-digest, never branch names, `latest`, size-only aliases, mutable object resolution, local absolute paths, or a screenshot alone. The paired human Markdown summary links the machine record and explains scope without changing its observed outcome. Failures, invalid measurements, retries, repairs, exclusions, fallback route, cold/warm distinction, denominators, and unresolved provenance/license caveats are retained. Missing evidence means **not demonstrated**, never Go or success.

| Expected Evidence ID / kind | Required future use |
|---|---|
| `EVID-LOCK-INVENTORY-001` / `lock-inventory` | Packages/native wheels, tools, model/OCR/data/OCI inventory, licenses, notices, SBOM, and distribution disposition. |
| `EVID-CORPUS-VERIFICATION-001` / `corpus-verification` | NAF profile, acquisition, split/image/eligibility/scorer checks, and local classification. |
| `EVID-PARSER-CONFORMANCE-001` / `parser-conformance` | Fixed manifest, hard gates, scorecard, outputs/failures, telemetry, and OCR/configuration. |
| `EVID-VLM-CONFORMANCE-001` / `vlm-conformance` | Candidate/request/matrix, repairs, schema/evidence/accuracy results, fallbacks, memory, latency, and health. |
| `EVID-PHASE0-DECISION-001` / `phase0-decision` | Gate outcomes, invalid runs, precedence, approver, authorization/T0, and deadline. |
| `EVID-WALKING-VERTICAL-001` / `walking-vertical` | Twelve-step observations, producer/cached runs, duplicate, fresh-process readback, metrics, and no-reexecution proof. |
| `EVID-TEST-REPORT-001` / `test-report` | Identity and Processing-definition vectors. |
| `EVID-TEST-REPORT-002` / `test-report` | Artifact create-if-absent, exact readback, and metadata-ordering check. |
| `EVID-TEST-REPORT-003` / `test-report` | Local topology and listener observation. |
| `EVID-TEST-REPORT-004` / `test-report` | Illustrative-schedule and walking-target check. |
| `EVID-TEST-REPORT-005` / `test-report` | Repository-license consistency check. |
| `EVID-TEST-REPORT-006` / `test-report` | Clean-clone/ordinary-CI synthetic-only and FUNSD-absence check. |
| `EVID-TEST-REPORT-007` / `test-report` | Future-infrastructure absence and later-benchmark boundary check. |
| `EVID-TEST-REPORT-008` / `test-report` | Adapter/import boundary check. |
| `EVID-TEST-REPORT-009` / `test-report` | Claim/cache/crash/Projection integration check. |
| `EVID-TEST-REPORT-010` / `test-report` | Page accounting and final-schema check. |
| `EVID-TEST-REPORT-011` / `test-report` | Evidence-envelope and publication-safety rubric. |
| `EVID-PUBLIC-BENCHMARK-001` / `public-benchmark` | NAF 77-page profile/accounting, strict ignored-edge behavior, configuration, metrics, exclusions, and caveats. |
| `EVID-DISTRIBUTION-REVIEW-001` / `distribution-review` | A later workload/SLO/security/licensing/migration decision and its failure evidence. |

Git may contain project-authored/cleared synthetic fixtures, schemas, non-content-bearing manifests, aggregate reports, and safe evidence records. NAF Data/Enhanced Data, ledgers/transcriptions, converted PDFs, image-bearing output, model/OCR weights, OCI archives, and third-party binaries remain outside Git. FUNSD content is absent. Redaction produces a new derived Artifact with its own digest and provenance; it never mutates a record or silently changes an outcome.

## Phase 0 boundary and stop points

The sole future Implementation authorization is the new, unedited issue #13 comment defined by `SRC-WALK`. It starts T0, permits bounded evidence work immediately, and conditionally permits durable walking work only after Overall Phase 0 Go. This blueprint does not create that authorization.

Before Overall Go, freeze component/artifact/corpus/prompt/schema/scoring/measurement contracts; explicitly acquire approved exact artifacts outside Git; run conformance evidence; and retain the decision record. Do not implement durable MinIO discovery, SQLite orchestration, production Docling/VLM stages, pipeline Artifact storage, OpenSearch indexing, Streamlit views, queues, distributed systems, or AWS/Kubernetes work.

| Gate | Required result and stop point |
|---|---|
| LIC | Admit exact artifacts, lock/inventory/SBOM/notices, and offline reproducibility. Unknown or forbidden terms, mismatches, surprise downloads, or impermissible distribution cut the affected component. |
| CORPUS | Reproduce `NAF-linked-v3`, the eligibility ledger, scorer, and 683 eligible pairs on 56 of 77 test pages without candidate evaluation on the test split. A profile/license/scorer failure is Adjust or Cut as `SRC-P0` defines. |
| PARSER | Run Docling-only `parser-conformance-v1` with full-page RapidOCR/ONNX, offline, within 300 seconds per document. A valid owned hard-gate failure is Adjust; no challenger is automatically downloaded. |
| VLM | Run the exact `SRC-VLM` matrix and gates A/M/L/C/S/E/R. The only fallbacks are the named routes; low accuracy, preference, and unmeasured concern do not authorize a fallback. |
| MACHINE | Measure M5 local coexistence and resource telemetry with the required services. No service removal, context reduction, or threshold change is a silent remedy. |
| WALK | Preserve every non-cuttable walking component/test and complete the decision record by `T0 + 48h`; failure to do so is Adjust unless Cut already prevails. |

Record one final outcome per gate in the fixed `LIC → CORPUS → PARSER → VLM → MACHINE → final LIC reconciliation → WALK` algorithm, including allowed internal fallback routing. Overall Cut stops the current implementation; Overall Adjust stops dependent work, revises the necessary contract, and reruns affected/downstream evidence. Overall Go satisfies the condition for the already-authorized walking scope but does not authorize later hardening, benchmark, or distribution work.

### Frozen VLM fallback routing

Before any fallback request, the candidate-specific LIC admission MUST be Go: its exact server/model/layer/license/provenance lock and inventory are retained, observed acquisition has completed, and the admission record is linked to the VLM matrix. No failed or missing admission may be bypassed.

| Current candidate and first failed gate | Required outcome |
|---|---|
| Any candidate: A | Cut that artifact and local VLM extraction from current Phase 0. |
| 9B: M or L | Admit and test exact `qwen3.5:4b-q4_K_M` under the identical contract. |
| 4B: M or L | Cut local VLM extraction from the initial implementation. |
| 9B or 4B: C | Admit and test exact `qwen3-vl:8b-instruct-q4_K_M` under the identical contract. |
| Qwen3-VL: M, L, C, S, E, or R | Cut local VLM extraction from the initial implementation. |
| 9B or 4B: S, E, or R | Cut local VLM extraction from the initial implementation. |
| Any candidate: no failed gate | Go with that candidate as selected and stop comparing. |

An invalid measurement authorizes no fallback. Low evaluated accuracy, evidence failure, preference, context regression, an unmeasured concern, an unlisted candidate, a hosted route, or a silent contract change authorizes no fallback. A named fallback under this table is an internal Gate VLM route; changing its identity or evidence policy is Adjust.

## Walking vertical and basic correctness

After Overall Go, the acceptance run uses the committed one-page synthetic fixture. It performs and retains observations for: source upload/version capture; streamed content identity; idempotent request/run creation; inspection; exact Artifact write/readback; Docling parse; typed record normalization; exact selected-model request; schema/evidence handling; SQLite state transition; OpenSearch Projection; and Streamlit inspection. A duplicate source must produce a separate cached run; a fresh process must read it back without re-execution.

The eleven basic correctness groups cover identity vectors; input admission; Artifact integrity; processing transitions; page accounting; parser records; VLM request/repair/evidence; cache compatibility; claims/crash recovery; Projection rebuild; and adapter/configuration/offline boundaries. They are not replaced by screenshots or a successful service start.

## Illustrative fourteen-day sequence

The sequence is planning context, not a T0 clock or a commitment to implement features before their authorization. The seven-day walking target is the controlling schedule after authorized T0.

| Illustrative period | Focus after the applicable stop point |
|---|---|
| Days 1–2 | Freeze and execute authorized Phase 0 admission, corpus, parser, VLM, and machine evidence; retain decision record by `T0 + 48h`. |
| Days 3–7 | If Overall Go, complete the one-PDF walking vertical, cached duplicate/readback, basic tests, and immutable acceptance record by `T0 + 168h`. |
| Days 8–11 | Later hardening planning only unless separately authorized: reliability, security, observability, recovery, and packaging requirements. |
| Days 12–14 | Later benchmark/report planning only unless separately authorized: full NAF 77-page evaluation, report, and scoped publication review. |

## Future ADR candidates

No parser/model selection ADR is accepted before measured Phase 0 evidence. If the relevant gates later provide retained evidence, candidates are: selected parser/portable OCR configuration; selected local VLM and request variant; evaluator normalization/matching contract; and any distribution architecture. Each requires its cited evidence record, immutable inputs, scope/rights review, and a new explicit decision. A future distribution ADR additionally requires workload/SLO/security/licensing/migration evidence; it cannot infer approval from this local blueprint.

## Canonical trace matrix

There is one row for each normative requirement. A row names Decision evidence, acceptance, planned tests, expected evidence, and phase; it does not record status, owner, dates, commits, or mutable URLs.

| Requirement ID | Decision evidence | AC IDs | Test IDs | Expected Evidence IDs/kinds | Phase |
|---|---|---|---|---|---|
| `REQ-SCOPE-001` | `SRC-WALK`, `SRC-EVOLVE` | `AC-SCOPE-001` | `TEST-CONTRACT-005` | `EVID-TEST-REPORT-003` / `test-report` | walking |
| `REQ-SCOPE-002` | `SRC-WALK`, `SRC-P0` | `AC-SCOPE-001` | `TEST-CONTRACT-005` | `EVID-TEST-REPORT-003` / `test-report` | walking |
| `REQ-SCOPE-003` | `SRC-WALK`, `SRC-P0` | `AC-SCOPE-002` | `TEST-CONTRACT-006` | `EVID-TEST-REPORT-004` / `test-report` | Phase 0/walking |
| `REQ-SCOPE-004` | `SRC-LICENSE`, `SRC-TRACE` | `AC-SCOPE-003` | `TEST-CONTRACT-007` | `EVID-TEST-REPORT-005` / `test-report` | Phase 0/walking/later |
| `REQ-SCOPE-005` | `SRC-WALK`, `SRC-LICENSE` | `AC-SCOPE-004` | `TEST-CONTRACT-005` | `EVID-TEST-REPORT-003` / `test-report` | walking |
| `REQ-DOMAIN-001` | `SRC-EVOLVE` | `AC-DOMAIN-001` | `TEST-UNIT-001` | `EVID-TEST-REPORT-001` / `test-report` | walking |
| `REQ-DOMAIN-002` | `SRC-EVOLVE` | `AC-DOMAIN-001` | `TEST-UNIT-001` | `EVID-TEST-REPORT-001` / `test-report` | walking |
| `REQ-ART-001` | `SRC-EVOLVE`, `SRC-LICENSE` | `AC-ART-001` | `TEST-CONTRACT-001` | `EVID-TEST-REPORT-002` / `test-report` | Phase 0/walking |
| `REQ-ART-002` | `SRC-LICENSE`, `SRC-P0` | `AC-ART-002` | `TEST-CONTRACT-010` | `EVID-LOCK-INVENTORY-001` / `lock-inventory` | Phase 0 |
| `REQ-CORPUS-001` | `SRC-CORPUS`, `SRC-LICENSE` | `AC-CORPUS-001` | `TEST-CONTRACT-008` | `EVID-TEST-REPORT-006` / `test-report` | walking/later |
| `REQ-CORPUS-002` | `SRC-CORPUS`, `SRC-NAF` | `AC-CORPUS-002` | `TEST-GOLDEN-001`, `TEST-BENCH-001` | `EVID-CORPUS-VERIFICATION-001` / `corpus-verification`; `EVID-PUBLIC-BENCHMARK-001` / `public-benchmark` | Phase 0/later |
| `REQ-CORPUS-003` | `SRC-CORPUS`, `SRC-FUNSD` | `AC-CORPUS-001` | `TEST-CONTRACT-008` | `EVID-TEST-REPORT-006` / `test-report` | walking/later |
| `REQ-PARSER-001` | `SRC-WALK`, `SRC-PARSER`, `SRC-LICENSE` | `AC-PARSER-001` | `TEST-CONTRACT-003` | `EVID-PARSER-CONFORMANCE-001` / `parser-conformance` | Phase 0 |
| `REQ-PARSER-002` | `SRC-P0`, `SRC-PARSER` | `AC-PARSER-001` | `TEST-CONTRACT-003` | `EVID-PARSER-CONFORMANCE-001` / `parser-conformance` | Phase 0 |
| `REQ-VLM-001` | `SRC-VLM`, `SRC-P0`, `SRC-VLM-RESEARCH` | `AC-VLM-001` | `TEST-CONTRACT-004` | `EVID-VLM-CONFORMANCE-001` / `vlm-conformance` | Phase 0 |
| `REQ-VLM-002` | `SRC-VLM`, `SRC-P0` | `AC-VLM-002` | `TEST-CONTRACT-004` | `EVID-VLM-CONFORMANCE-001` / `vlm-conformance` | Phase 0 |
| `REQ-RUN-001` | `SRC-WALK`, `SRC-EVOLVE`, `SRC-VLM` | `AC-RUN-001` | `TEST-SCHEMA-001` | `EVID-TEST-REPORT-010` / `test-report` | walking |
| `REQ-RUN-002` | `SRC-WALK`, `SRC-EVOLVE` | `AC-RUN-001` | `TEST-E2E-002` | `EVID-WALKING-VERTICAL-001` / `walking-vertical` | walking |
| `REQ-STORE-001` | `SRC-EVOLVE`, `SRC-WALK` | `AC-STORE-001` | `TEST-INTEGRATION-001` | `EVID-TEST-REPORT-009` / `test-report` | walking |
| `REQ-STORE-002` | `SRC-EVOLVE` | `AC-STORE-001` | `TEST-INTEGRATION-001` | `EVID-TEST-REPORT-009` / `test-report` | walking |
| `REQ-BOUNDARY-001` | `SRC-EVOLVE` | `AC-BOUNDARY-001` | `TEST-CONTRACT-002` | `EVID-TEST-REPORT-008` / `test-report` | walking |
| `REQ-P0-001` | `SRC-P0`, `SRC-WALK` | `AC-P0-001` | `TEST-INTEGRATION-002` | `EVID-PHASE0-DECISION-001` / `phase0-decision` | Phase 0 |
| `REQ-P0-002` | `SRC-P0` | `AC-P0-001` | `TEST-INTEGRATION-002` | `EVID-PHASE0-DECISION-001` / `phase0-decision` | Phase 0 |
| `REQ-P0-003` | `SRC-P0`, `SRC-WALK` | `AC-P0-001` | `TEST-INTEGRATION-002` | `EVID-PHASE0-DECISION-001` / `phase0-decision` | Phase 0 |
| `REQ-WALK-001` | `SRC-WALK`, `SRC-P0` | `AC-WALK-001` | `TEST-E2E-001` | `EVID-WALKING-VERTICAL-001` / `walking-vertical` | walking |
| `REQ-WALK-002` | `SRC-WALK`, `SRC-EVOLVE` | `AC-WALK-001` | `TEST-E2E-002` | `EVID-WALKING-VERTICAL-001` / `walking-vertical` | walking |
| `REQ-EVIDENCE-001` | `SRC-TRACE`, `SRC-P0` | `AC-EVIDENCE-001` | `TEST-MANUAL-001` | `EVID-TEST-REPORT-011` / `test-report` | Phase 0/walking/later |
| `REQ-EVIDENCE-002` | `SRC-TRACE`, `SRC-CORPUS`, `SRC-LICENSE` | `AC-EVIDENCE-001` | `TEST-MANUAL-001` | `EVID-TEST-REPORT-011` / `test-report` | Phase 0/walking/later |
| `REQ-LATER-001` | `SRC-CORPUS`, `SRC-WALK` | `AC-LATER-001` | `TEST-BENCH-001`, `TEST-CONTRACT-009` | `EVID-PUBLIC-BENCHMARK-001` / `public-benchmark`; `EVID-TEST-REPORT-007` / `test-report` | later hardening |
| `REQ-LATER-002` | `SRC-EVOLVE`, `SRC-WALK` | `AC-LATER-001` | `TEST-MANUAL-002` | `EVID-DISTRIBUTION-REVIEW-001` / `distribution-review` | later/future distribution |

Before approval, manually verify that every requirement occurs once, each has Decision evidence/AC/test/evidence kind, ACs lead to a test or justified manual rubric, every source appears in a row, deferred work is assigned to scope or later phase, no future evidence is claimed, and all full-SHA links and Markdown resolve. The documentation-only review may perform this completeness check manually; it does not authorize a linter or evidence system.
