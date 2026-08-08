# Blueprint traceability and evidence requirements

The final blueprint must be a stable specification, not a Development diary. It will state each Normative requirement once, connect it to commit-pinned Decision evidence, define observable Acceptance criteria and Planned tests, and name the Conformance evidence later work must retain. This resolves [issue #12](https://github.com/monocongo/docproc/issues/12) without revising PR #2 or implementing evidence tooling.

## Accepted decision sources

Issue #13 must use full-SHA links to this closed set; branch names, mutable “latest” pages, short-SHA-only links, and issue-comment text are not substitutes:

| Source ID | Commit-pinned source | What it governs |
|---|---|---|
| `SRC-PLAN` | [Protected PR #2 blueprint at `ca4ea1b`](https://github.com/monocongo/docproc/blob/ca4ea1ba2e1ffb4178aa52ac86a9f6d3a6100636/docs/planning/pdf-processing-pipeline-plan.md) | Candidate architecture and material to reconcile, not accepted evidence by itself. |
| `SRC-CORPUS` | [Public benchmark/FUNSD decision at `4c1714d`](https://github.com/monocongo/docproc/blob/4c1714d372a89d2ee99373a2bccbd33c6cd66e9c/docs/adr/0001-public-evaluation-corpus.md) | NAF role, synthetic clean clone, FUNSD omission, acquisition/redistribution/ignored-ground-truth/reporting boundaries. |
| `SRC-VLM` | [Phase 0 VLM/serving contract at `cabf749`](https://github.com/monocongo/docproc/blob/cabf7490a7a66fd8b4cf6f00ea6207c78dd50f5c/docs/decisions/phase-0-vlm-serving-contract.md) | Candidate artifacts, request/matrix, resource/schema/evidence/accuracy gates, and named fallback routing. |
| `SRC-WALK` | [Walking-vertical acceptance at `a5e4205`](https://github.com/monocongo/docproc/blob/a5e4205b597b70f15c2ce73421d361a0f0e2b799/docs/decisions/walking-vertical-acceptance.md) | T0/seven-day target, one-PDF observable path, cached Processing run, basic tests, and later hardening boundary. |
| `SRC-EVOLVE` | [Local/distributed evolution at `2006944`](https://github.com/monocongo/docproc/blob/2006944aec59b5052e00192bc5844f986a55b5f7/docs/decisions/local-to-distributed-evolution.md) | Identity/canonicalization, claims/fencing/cache reservation, typed records, adapter boundaries, and explicit distributed absences. |
| `SRC-P0` | [Phase 0 go-adjust-cut gate at `d5e0f3d`](https://github.com/monocongo/docproc/blob/d5e0f3dfca08f6bc11ad02a6ee275aef0e43b2f9/docs/decisions/phase-0-go-adjust-cut-gate.md) | LIC/CORPUS/PARSER/VLM/MACHINE/WALK evidence, outcomes, invalid measurements, authorization, and precedence. |
| `SRC-LICENSE` | [Artifact/licensing gates at `a6a0ce8`](https://github.com/monocongo/docproc/blob/a6a0ce8014391d7956801154a39b8061fa8940f8/docs/research/dependency-artifact-licensing-gates.md) | Exact lock/inventory/SBOM/notices/distribution/network requirements and current MIT repository license. |
| `SRC-NAF` | [Open-form corpus research at `532b1fb`](https://github.com/monocongo/docproc/blob/532b1fb1f9b948510e4296dad4c9fe3092d2681e/docs/research/open-real-form-evaluation-corpus.md) | `NAF-linked-v3` source/integrity/license/profile facts and scope limits. |
| `SRC-FUNSD` | [FUNSD research at `093a663`](https://github.com/monocongo/docproc/blob/093a663bdd6fa419ac2931c88ad1b9e5cda0da78/docs/research/funsd-corpus-assumptions.md) | Historical rationale for omission and correction of the stale CC BY claim. |
| `SRC-PARSER` | [Parser research at `0e4fbf3`](https://github.com/monocongo/docproc/blob/0e4fbf3f87989ed0002ca5e24add68b6fda0a055/docs/research/parser-spike-candidates.md) | Docling hard gates/scorecard and Marker/Surya code/model distinction. |
| `SRC-VLM-RESEARCH` | [M5 VLM research at `cc144e6`](https://github.com/monocongo/docproc/blob/cc144e6239b4d4dff37f8325ad6feb70dc2d77f9/docs/research/local-vlm-serving-m5.md) | Research-time candidate artifacts, M5 serving facts, and measured-evidence gap. |
| `SRC-TRACE` | [Blueprint traceability decision at `30fa592`](https://github.com/monocongo/docproc/blob/30fa592efcde4d45c0f6053518ac5937ae843578/docs/decisions/blueprint-traceability-evidence.md) | Stable traceability, evidence, ID, and publication-boundary contract for the final blueprint. |

The commit-pinned `SRC-WALK` artifact carries the accepted issue #17 Docling-only outcome, so the final blueprint need not rely on a mutable issue comment. Research supports a decision but does not override the later decision artifact.

## Blueprint vocabulary that must be explicit

The blueprint must use these terms consistently and define them in a concise domain-language section. It may link detailed canonicalization/state rules to a Normative requirement, but it cannot silently use one term for another.

### Processing identity and coordination

- **Source object** — one occurrence of PDF bytes received from a source; distinct from a Document.
- **Document** — content identity shared by Source objects with exactly the same PDF bytes.
- **Processing request** — idempotent intention to create exactly one Processing run.
- **Processing run** — one attempt under one Processing request and Processing definition; cache hits receive their own ID/status.
- **Stage attempt** — one execution attempt for a named stage of a Processing run.
- **Work claim** — time-bounded, fenced authority for one worker to advance a Stage attempt.
- **Artifact / Artifact reference** — immutable content/kind identity and an exact version-pinned verifiable occurrence.
- **Processing definition** — immutable component/model/prompt/schema/configuration identities governing output and reuse.
- **Projection** — rebuildable view, specifically OpenSearch, never authoritative processing state.

### Evaluation and delivery

- **Synthetic fixture**, **clean-clone acceptance**, **public accuracy benchmark**, and **evidence profile** remain distinct.
- **Schema-valid**, **evidence-grounded**, and **evaluated accuracy** are three separate results; “quality” cannot replace them.
- **Candidate model** and **selected model** remain distinct until measured gates resolve.
- **Walking vertical** and **walking-vertical acceptance run** remain distinct from ordinary CI and the public accuracy benchmark.
- **Selection gate**, **valid measurement**, **Go**, **Adjust**, **Cut**, **Overall Phase 0 outcome**, **Implementation authorization**, and **T0** use the exact meanings in `SRC-P0`/`SRC-WALK`. Actual-component Phase 0 and walking execution are future Conformance work, not evidence produced by this decision or by issue #13. T0 starts only when the separately authorized, exact Implementation-authorization form in `SRC-P0`/`SRC-WALK` is issued; a review, approval request, or ordinary issue/PR comment does not start it.
- **Later hardening** is not part of walking-vertical acceptance.

## Normative requirement form

Every blueprint statement containing an implementation obligation or prohibition must be an atomic Normative requirement with a stable ID and one observable subject. Use `MUST`, `MUST NOT`, or `SHOULD` deliberately; descriptive context and rationale remain non-normative.

ID families are fixed:

| Prefix | Requirement family |
|---|---|
| `REQ-SCOPE-*` | Local-only scope, timing, current repository license, and explicit non-goals. |
| `REQ-DOMAIN-*` | Domain identities, state ownership, terminology, and canonical records. |
| `REQ-ART-*` | Immutable Artifact writes/references, locks, acquisition, notices, and offline execution. |
| `REQ-CORPUS-*` | Synthetic clean clone, NAF profile/splits/scoring, FUNSD omission, and publication boundaries. |
| `REQ-PARSER-*` | Docling-only conformance contract, OCR/artifacts, hard gates, and scorecard. |
| `REQ-VLM-*` | Candidate/request/matrix, artifact/provenance, fallback, schema/evidence/accuracy, and M5 resource contract. |
| `REQ-RUN-*` | Intake, Source object/Document/Processing request/run identity, state transitions, reuse, and page coverage. |
| `REQ-STORE-*` | MinIO/SQLite authority, transactions/claims/cache reservation, and OpenSearch Projection rebuildability. |
| `REQ-BOUNDARY-*` | Typed parser/VLM/storage/repository/search/UI boundaries and infrastructure dependency direction. |
| `REQ-P0-*` | Phase 0 evidence-only boundary, six gates, invalid measurements, outcomes, timing, and precedence. |
| `REQ-WALK-*` | One-PDF actual-component scenario, duplicate/cached run, restart/readback, basic tests, and acceptance record. |
| `REQ-EVIDENCE-*` | Evidence envelope, content safety, trace completeness, reports, and approval records. |
| `REQ-LATER-*` | Reliability/public benchmark/hardening work after the walking vertical and future distribution trigger. |

Requirement IDs follow `REQ-<FAMILY>-<NNN>`, where `<FAMILY>` is exactly one of the table's family tokens and `<NNN>` is a zero-padded decimal number; for example, `REQ-SCOPE-001`. IDs are stable once the final blueprint is approved. Do not renumber them to match section order; supersede a changed requirement explicitly. One requirement cannot combine independently failing conditions merely to shrink the Trace matrix.

## Mandatory invariant catalog

Issue #13 must encode and trace at least these invariants; detailed subcriteria may receive additional IDs:

| Required family | Minimum invariant content | Decision evidence |
|---|---|---|
| `REQ-SCOPE` | Entirely local runtime; no hosted inference/cloud critical path; one worker; MinIO, SQLite, OpenSearch, Streamlit, Docling, host Ollama retained; fourteen-day sequence illustrative; T0+168h walking target. | `SRC-WALK`, `SRC-EVOLVE`, `SRC-P0` |
| `REQ-DOMAIN` | `docproc-identity-v1` framing/vectors; distinct Source object/Document/Processing request/Processing run/Stage attempt/Work claim; versioned canonical records; Processing definition immutability. | `SRC-EVOLVE` |
| `REQ-ART` | Create-if-absent, version-pinned readback and digest verification before metadata success; exact external acquisition/locks; network-denied measured reruns; current MIT license. | `SRC-EVOLVE`, `SRC-LICENSE` |
| `REQ-CORPUS` | Synthetic-only repository/ordinary CI; NAF as sole public accuracy benchmark under `NAF-linked-v3`; FUNSD absent; exact split/eligibility/ignore/publication boundaries. | `SRC-CORPUS`, `SRC-NAF`, `SRC-FUNSD` |
| `REQ-PARSER` | Docling-only, explicit full-page RapidOCR/ONNX, no automatic OCR/Marker/Surya; exact artifacts; 300-second/document conformance and all owned hard gates; no invented word-recall threshold. | `SRC-P0`, `SRC-PARSER`, `SRC-LICENSE` |
| `REQ-VLM` | Exact 9B/Ollama primary, request/state/matrix, 16K/90-second/resource/schema/evidence/report gates, candidate-level licensing, only named 4B/Qwen3-VL routes, no F1 threshold. | `SRC-VLM`, `SRC-P0`, `SRC-VLM-RESEARCH` |
| `REQ-RUN` | Full admitted-page accounting; schema-invalid final output cannot succeed; deterministic repair; distinct producer/cached Processing runs; exact compatibility fingerprint; no stale reuse. | `SRC-WALK`, `SRC-EVOLVE`, `SRC-VLM` |
| `REQ-STORE` | SQLite/MinIO authoritative roles, Artifact-before-metadata transaction order, fenced Work claims/cache reservation, deterministic replay outcomes, OpenSearch as rebuildable Projection. | `SRC-EVOLVE`, `SRC-WALK` |
| `REQ-BOUNDARY` | Infrastructure types do not escape adapters; typed/versioned cross-stage records use Artifact references; no local path/process/backend identity leakage; no speculative transport/backend. | `SRC-EVOLVE` |
| `REQ-P0` | Only bounded evidence work before overall Go; LIC/CORPUS/PARSER/VLM/MACHINE/WALK exact outcomes; Cut > Adjust > Go; T0+48h expiry; sole/superseding authorization semantics. | `SRC-P0`, `SRC-WALK` |
| `REQ-WALK` | Exact committed one-page synthetic fixture; all actual local stages; non-empty schema-valid result/evidence/metrics; duplicate cached run; fresh-process readback; basic offline tests; immutable acceptance record. | `SRC-WALK` |
| `REQ-EVIDENCE` | Machine-readable/human evidence pair, exact inputs/environment/outcomes/failures/exclusions, Decision-evidence links, specification references, content classification, and immutable approval link. | `SRC-P0`, `SRC-TRACE` |
| `REQ-LATER` | Full 77-page NAF test benchmark, broader reliability/security/performance/packaging after walking acceptance; no queues/PostgreSQL/Kubernetes/EKS/AWS until a measured future initiative. | `SRC-CORPUS`, `SRC-WALK`, `SRC-EVOLVE` |

“No implementation” is a requirement when it protects scope. Explicit absences need negative Acceptance criteria where a repository scan, import rule, lock inventory, or payload scan can observe them.

## Acceptance and Planned-test form

- Acceptance-criterion IDs follow `AC-<FAMILY>-<NNN>`, where `<FAMILY>` exactly matches the family token of every cited requirement (for example, `AC-SCOPE-001` cites `REQ-SCOPE-001`); an AC spanning families uses its own explicit, documented `AC-CROSS-<NNN>` ID.
- Planned-test IDs follow `TEST-<KIND>-<NNN>`, where `<KIND>` is exactly `UNIT`, `SCHEMA`, `CONTRACT`, `INTEGRATION`, `GOLDEN`, `E2E`, `BENCH`, or `MANUAL`, and `<NNN>` is a zero-padded decimal number. Each Planned test cites exact `AC-*` and/or `REQ-*` IDs, never an ID-family placeholder.
- Evidence-record IDs follow `EVID-<KIND>-<NNN>`, where `<KIND>` is a documented evidence kind from this decision and `<NNN>` is a zero-padded decimal number. Requirement, Acceptance-criterion, Planned-test, and Evidence-record IDs are unique and directly parseable; every cross-reference uses the complete exact ID.
- A Planned test states fixture/population, preconditions, action, observable oracle, network/service mode, and expected Evidence-record kind. “Add tests” is not a Planned test.
- Manual acceptance is allowed only when automation cannot establish the observation; it needs a fixed rubric, named evidence, and rationale. Screenshots alone are never sufficient evidence.
- Ordinary CI tests remain deterministic, synthetic-only, and offline. Expensive parser/VLM/NAF/service checks are explicitly authorized jobs/runs with no unsafe artifact publication.
- Test doubles can establish orchestration/contract behavior but cannot satisfy actual-component Phase 0 or walking-vertical Acceptance criteria.

The blueprint must trace, without duplicating their full prose:

1. all six Phase 0 gate contracts and decision-record acceptance;
2. the twelve-step walking-vertical scenario and eleven basic correctness test groups in `SRC-WALK`;
3. identity/canonicalization vectors, claim/cache races, crash windows, Projection rebuild, dependency-import, configuration relocation, and offline checks in `SRC-EVOLVE`;
4. hand-computed scorer cases and complete NAF eligibility-ledger reproduction before public scoring;
5. later NAF 77-page benchmark/report acceptance; and
6. deferred reliability/security/performance/distribution outcomes as later requirements, not accidental walking prerequisites.

## Evidence-record contract

Every expected Conformance-evidence item has a stable `EVID-<KIND>-<NNN>` ID and a documented kind. Its machine-readable envelope contains at least:

```text
evidence_schema_version
evidence_id
kind
spec_refs[]             # REQ/AC/TEST IDs
source_commit
producer_identity
produced_at_utc
inputs[]                 # exact Artifact/data/test refs and digests
environment_ref          # lock/SBOM/hardware/OS/service digests
contract_refs[]          # prompt/schema/config/scoring/gate versions
outcome                  # observed result, never inferred from file presence
failures[]
exclusions[]
artifact_refs[]
content_classification   # synthetic, third-party-data, aggregate, restricted
publication_disposition
```

The envelope and payload are immutable/content-addressed. References use full commit SHAs or exact Artifact version+digest; never branch names, `latest`, size-only aliases, mutable object resolution, local absolute paths, or a screenshot as the only locator. The human Markdown summary links the machine record and explains scope/limitations without changing its outcome.

Evidence must preserve failures, invalid measurements, repairs, retries, excluded inputs, fallback routes, cold/warm distinction, actual denominators, and unresolved provenance/license caveats. Absence of evidence is “not demonstrated,” never Go or success.

### Required evidence kinds

| Kind | Minimum future use |
|---|---|
| `lock-inventory` | Packages/native wheels, interpreter/tools, model/OCR files, data, OCI layers, licenses/notices/SBOM, distribution disposition. |
| `corpus-verification` | `NAF-linked-v3` acquisition/profile/split/image/eligibility/scorer checks and local content classification. |
| `parser-conformance` | Fixed manifest, every hard-gate observation, scorecard, outputs/failures, resource telemetry, selected OCR/configuration. |
| `vlm-conformance` | Exact candidate/request/matrix, raw/repair/schema/evidence/accuracy results, fallback path, memory/latency/health telemetry. |
| `phase0-decision` | Per-criterion/gate outcome, invalid runs, Cut/Adjust/Go precedence, approver, authorization/T0 and deadline evidence. |
| `walking-vertical` | Actual-component twelve-step observations, producer/cached run, duplicate source, fresh-process readback, separate metrics, no-reexecution proof. |
| `test-report` | Exact suite/selection, requirement refs, environment, pass/fail/skip/xfail with reasons, coverage only as supporting context. |
| `public-benchmark` | Full NAF profile, complete 77-page accounting, strict ignored-edge behavior, configuration, metrics/failures/exclusions, scope caveats. |
| `distribution-review` | Only for a later initiative: workload/SLO/security/licensing decision and migration/failure evidence. |

## Content and publication boundary

- Git may contain project-authored/cleared synthetic fixtures, schemas, non-content-bearing manifests, aggregate reports, and safe Evidence records.
- NAF Data/Enhanced Data, local ledgers/transcriptions, converted PDFs, image-bearing output, model/OCR weights, OCI archives, and third-party binaries remain outside Git under their decision-specific controls.
- FUNSD content is absent entirely.
- Every Evidence record declares content classification before publication. Aggregate/de-minimis output still receives source/output-rights review and retains the NAF residual-rights caveat.
- Redaction creates a new derived Artifact with its own digest and provenance; it never mutates evidence or silently changes the observed outcome.

## Trace-matrix columns and completeness

The final blueprint has one canonical Trace matrix with these columns:

```text
Requirement ID
Normative requirement (or exact section anchor)
Decision-evidence Source IDs
Acceptance-criterion IDs
Planned-test IDs
Expected Evidence IDs/kinds
Delivery phase (Phase 0, walking, later hardening, future distribution)
```

Do not add implementation status, assignee, completion date, commit chronology, session notes, or mutable evidence URLs. Those belong in issues/PRs and future evidence indexes.

Before #13 can be approved, demonstrate:

1. every Normative requirement ID is unique and appears in exactly one normative definition;
2. every Normative requirement has Decision evidence, at least one Acceptance criterion, and expected Evidence kind;
3. every Acceptance criterion traces back to requirements and forward to a Planned test or justified manual rubric;
4. every Planned test traces to an Acceptance criterion and names an oracle/evidence kind;
5. every accepted map decision appears in at least one trace row, and every Decision-evidence link uses a full commit SHA;
6. every non-goal/deferred item is assigned to scope or a later requirement instead of disappearing;
7. no row claims future Conformance evidence already exists;
8. schema-valid, evidence-grounded, and evaluated accuracy are never merged into one result;
9. protected scope—synthetic clean clone, actual-component walking vertical, full later NAF benchmark, local/distributed boundary—is internally consistent; and
10. all Markdown/internal/external links resolve, `git diff --check` passes, and the final multi-review has no unresolved feasible P0–P4 finding.

This completeness check may be manual for the documentation-only blueprint revision. Issue #12 does not authorize a linter or evidence system.

## Keep the blueprint out of diary mode

The blueprint records current approved specification and rationale links. It does not record:

- session/agent names, branch/worktree locations, claim comments, handoff history, or review conversation;
- a commit-by-commit changelog, actual daily progress, transient blockers, assignees, or task status checkboxes;
- raw experiment logs, benchmark rows, generated SBOM/notices, or duplicated research findings;
- accepted parser/model ADRs before measured Phase 0 evidence exists; or
- multiple alternative implementation plans after a decision is resolved.

Later evidence lives in versioned reports/Artifact records and later durable selections in concise ADRs. The blueprint links them through stable IDs rather than absorbing their chronology.

## #13 approval handoff

Issue #13 must:

1. revise only `docs/planning/pdf-processing-pipeline-plan.md` on the existing PR #2 branch; it does not authorize incidental planning-README or other PR-file edits;
2. replace stale FUNSD/Qwen2.5/Marker/Apache-license and comparative-spike assertions with the accepted map;
3. consolidate repeated prose into one normative source plus Trace links;
4. include the domain language, requirement catalog, Acceptance criteria, Planned tests, expected evidence, trace matrix, Phase 0 boundary/gates, seven-day walking target, illustrative later sequence, and exact implementation stop points;
5. label post-walking reliability/public evaluation/hardening and future distribution explicitly;
6. list ADR candidates and their required future evidence without declaring measured selections accepted;
7. run `multi-review`, apply every feasible P0–P4 documentation fix, and re-run completeness/link/diff checks;
8. commit and push only the reviewed blueprint documentation to the existing PR branch; and
9. request human approval with the full final blueprint commit link, concise review evidence, and an explicit statement that the comment is not yet an Implementation authorization unless the maintainer intentionally uses the separate exact authorization form required by `SRC-WALK`/`SRC-P0`.
