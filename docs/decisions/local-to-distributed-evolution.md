# Local-to-distributed evolution constraints

Any later authorized initial implementation is constrained to one local polling worker with SQLite, versioned MinIO, local OpenSearch, Streamlit, Docling, and host Ollama. It will preserve only the contracts needed to move work and durable state later; it will not implement a distributed system, a second backend, or speculative cloud abstractions. This resolves [issue #10](https://github.com/monocongo/docproc/issues/10).

This decision is documentation only. It authorizes no code, configuration, service startup, artifact acquisition, or infrastructure work.

Preserving a distribution seam means the future change is bounded and testable. It does not mean local and distributed deployments are interchangeable, that migration is free, or that Kubernetes/AWS architecture has been selected.

## Accepted inputs

- [Current PR #2 blueprint at `ca4ea1b`](https://github.com/monocongo/docproc/blob/ca4ea1ba2e1ffb4178aa52ac86a9f6d3a6100636/docs/planning/pdf-processing-pipeline-plan.md)
- [Walking-vertical acceptance at `a5e4205`](https://github.com/monocongo/docproc/blob/a5e4205b597b70f15c2ce73421d361a0f0e2b799/docs/decisions/walking-vertical-acceptance.md)
- [Phase 0 VLM serving contract at `cabf749`](https://github.com/monocongo/docproc/blob/cabf7490a7a66fd8b4cf6f00ea6207c78dd50f5c/docs/decisions/phase-0-vlm-serving-contract.md)
- [Artifact and licensing gates at `a6a0ce8`](https://github.com/monocongo/docproc/blob/a6a0ce8014391d7956801154a39b8061fa8940f8/docs/research/dependency-artifact-licensing-gates.md)

## Required initial local topology

- One polling worker owns orchestration and advances at most one claimed Stage attempt at a time.
- SQLite is authoritative for Source objects, Documents, Processing runs, Stage attempts, Work claims, cache metadata, and schema version.
- Versioned MinIO is authoritative for source bytes and immutable Artifacts.
- OpenSearch is only a Projection. Streamlit reads authoritative metadata/Artifacts plus that Projection; it owns no processing state.
- Docling executes behind the parser boundary. Host Ollama executes behind the VLM boundary and stays bound to localhost for the reference Mac.
- MinIO and OpenSearch remain separately operated local services. Distributed infrastructure is absent.

The later authorized local implementation may optimize for one worker, but no correctness rule may depend on process memory, a local filesystem path, SQLite row IDs, an unchecked “latest” object, or OpenSearch being current.

## Stable identity contract

Identity canonicalization is versioned as **`docproc-identity-v1`**:

- Hashes use SHA-256 and lowercase hexadecimal.
- An identity string is UTF-8 encoded exactly as received after schema validation; no Unicode, case, path, or URL normalization is applied.
- A framed value is an unsigned 64-bit big-endian byte length followed by exactly that many bytes.
- Source object hash input is ASCII `docproc:source-object:v1`, one NUL byte, then framed storage namespace, bucket, key, and immutable object-version strings in that order. Its external form is `source:v1:sha256:<hex>`.
- Document hash input is the exact PDF bytes. Its external form is `document:v1:sha256:<hex>`.
- Artifact hash input is ASCII `docproc:artifact:v1`, one NUL byte, then framed registered Artifact-kind UTF-8 bytes and framed exact Artifact bytes. Its external form is `artifact:v1:sha256:<hex>`. Artifact kinds are versioned schema enum values; unknown kinds fail closed.
- Processing definition and cache-key digests hash UTF-8 RFC 8785 JSON Canonicalization Scheme bytes for their versioned typed record. Identity-bearing schemas prohibit ambiguous numeric or untyped values.

Required byte-level test vectors (the NUL byte is `00`, and each frame's eight-byte length is visible in the hash-input hex):

| Identity | Inputs | Exact hash-input hex | Exact expected digest |
|---|---|---|---|
| Source object | namespace `local`, bucket `source`, key `incoming/form.pdf`, version `v1` | `646f6370726f633a736f757263652d6f626a6563743a76310000000000000000056c6f63616c0000000000000006736f757263650000000000000011696e636f6d696e672f666f726d2e70646600000000000000027631` | `20409f62753cfdf3d6969079a9ac011346b11daee31eb58014fe8635ba115a50` |
| Document | bytes hex `5044460a` (`PDF\n`) | `5044460a` | `4223df8e7f52c02d07737c3af675d7eef7803b7a7bd0bc29be05f894860255fa` |
| Artifact | kind `inspection.json`, bytes hex `7b7d` (`{}`) | `646f6370726f633a61727469666163743a763100000000000000000f696e7370656374696f6e2e6a736f6e00000000000000027b7d` | `a4c6329081e774f567410b88a74fa29801ba699f37301d45024908a5f88ff7cf` |

### Processing-definition record v1

The RFC 8785 input object has exactly three required fields and no unknown fields:

- `version`: literal string `processing-definition-v1`;
- `components`: non-empty array of objects with exactly `role`, `implementation`, `version`, `artifact_ids`, and `configuration_digest`; and
- `contracts`: non-empty array of objects with exactly `role` and `digest`.

Roles are unique lowercase ASCII identifiers matching `[a-z][a-z0-9-]*`. Component and contract rows sort by UTF-8 role bytes before canonicalization; `artifact_ids` are unique valid Artifact IDs sorted by UTF-8 bytes. Versions and implementations are non-empty strings. Every digest is `sha256:<64 lowercase hex>`. Every output-affecting participating component, artifact, schema, prompt, renderer/image/context/batching/generation/scoring policy, and contract must have one component or contract row; omission invalidates Gate A rather than creating a partial identity. The external digest form is `processing-definition:v1:sha256:<hex>`.

Canonicalization vector:

```json
{"components":[{"artifact_ids":[],"configuration_digest":"sha256:0000000000000000000000000000000000000000000000000000000000000000","implementation":"docproc.inspector","role":"inspector","version":"1.0.0"}],"contracts":[{"digest":"sha256:1111111111111111111111111111111111111111111111111111111111111111","role":"inspection-schema"}],"version":"processing-definition-v1"}
```

Its UTF-8 bytes have SHA-256 `4513caef7e933876dc31cd83aa28a2becaf1a4d7b03059b7bcff926a1348645e`.

### Stage-cache-key record v1

The RFC 8785 input object has exactly four required fields and no unknown fields:

- `version`: literal string `stage-cache-key-v1`;
- `stage`: object with exactly lowercase ASCII `name` and integer `version >= 1`;
- `processing_definition_id`: one valid processing-definition external ID; and
- `input_artifacts`: non-empty array of objects with exactly lowercase ASCII `role`, integer `ordinal >= 0`, and valid `artifact_id`.

Input rows have unique `(role, ordinal)` and sort by UTF-8 role bytes, then ordinal, then Artifact-ID bytes before canonicalization. The external form is `stage-cache:v1:sha256:<hex>`.

Canonicalization vector:

```json
{"input_artifacts":[{"artifact_id":"artifact:v1:sha256:0000000000000000000000000000000000000000000000000000000000000000","ordinal":0,"role":"source"}],"processing_definition_id":"processing-definition:v1:sha256:1111111111111111111111111111111111111111111111111111111111111111","stage":{"name":"inspect","version":1},"version":"stage-cache-key-v1"}
```

Its UTF-8 bytes have SHA-256 `b04c6d77666cd795c4e70655aba3e5f594d3358e5f11df67c31c4565aee6bded`.

These identities survive a later backend or execution move:

| Concept | Stable identity and rule |
|---|---|
| Source object | `docproc-identity-v1` over storage namespace, bucket, key, and immutable object version. A URL, ETag, filesystem path, or MinIO host name is not its identity. |
| Document | `docproc-identity-v1` over exact source bytes, independent of location or worker. |
| Processing request | Caller-supplied UUIDv4 idempotency key, serialized as lowercase hyphenated text. Replaying one Processing request returns its existing Processing run. The automatic intake request is inserted once under uniqueness over Source object ID, Processing definition digest, and trigger version. |
| Processing run | New UUIDv4, serialized as lowercase hyphenated text, for every new Processing request, including cache hits; references that request, one Document, one Source object, and one Processing definition digest. Persist and migrate it; never derive it from a backend sequence. |
| Stage attempt | New UUIDv4 for every attempt, plus Processing run ID, stable stage name/version, and ordinal. Retry creates a new Stage attempt rather than overwriting history. |
| Work claim | Stage attempt identity plus an opaque persisted claim token, owner identity, acquisition time, and expiry. Only the current token may complete the Stage attempt. |
| Artifact | `docproc-identity-v1` over registered kind and exact bytes. |
| Artifact reference | Storage namespace, bucket/key, immutable object version, content digest, media type, and Artifact identity. Readers verify version and digest; they never resolve “latest.” |
| Cache entry | Versioned canonical record containing stage name/version, exact input Artifact identities, and every Processing definition identity that can affect output. |

Identifiers never embed pod names, host names, process IDs, local temporary paths, SQLite primary-key allocation, queue delivery IDs, regions, accounts, or deployment names. A deployment locator may be recorded as metadata but cannot alter content or Processing run identity. Changing canonicalization requires a new identity version and explicit migration; adapters never reinterpret stored IDs.

## Versioned boundary records

Every cross-stage input and outcome is a versioned typed record that can round-trip through RFC 8785 canonical JSON without parser objects, ORM rows, SDK clients, open file handles, exceptions, or process-local references. It contains only:

- stable Source object, Document, Processing request, Processing run, Stage attempt, and Artifact identities/references;
- the Processing definition and stage-contract versions;
- bounded scalar metadata required by that stage;
- success, explicit failure, or cache-reuse outcome; and
- provenance needed to trace the producing Stage attempt.

Large source, page, parser, request, response, and extraction content travels by exact Artifact reference, not inside a future queue payload. Logs and traces may carry the stable IDs but are not durable state.

Schema evolution is additive while old workers may coexist. Removing/renaming a field, changing identity semantics, changing canonicalization, or changing a stage's output meaning requires a new contract version and migration decision. Unknown required versions fail closed; they are never guessed.

## Coordination and state invariants

The one-worker implementation must honor semantics that remain safe under at-least-once execution:

1. **Claim before work.** A worker atomically claims one ready Stage attempt through the metadata repository and receives an opaque token plus expiry. Claiming through a process mutex or file lock is forbidden as the correctness mechanism.
2. **Fenced completion.** Success, failure, heartbeat, or retry scheduling uses compare-and-set semantics over Stage attempt identity, current state, and claim token. An expired or replaced token cannot commit.
3. **Deterministic replay outcomes.** Re-discovering the same storage namespace/bucket/key/version is a no-op: it creates no Source object, Document, Processing request, Processing run, or Stage attempt. Discovering a different Source object with identical bytes creates that Source object, reuses the Document, and creates exactly one automatic Processing request/Processing run for that intake. Compatibility is exact Stage-cache-key equality. Before stage execution, contenders atomically create or claim the sole cache-key reservation, which records `RESERVED`, the producer Stage-attempt ID, a fence token, and an expiry. Only that fenced producer executes; joiners do not execute and instead reconcile the reservation. The current producer alone may atomically publish `SUCCEEDED` with its Processing-run ID, Artifact-manifest digest, and exact Artifact references. Joiners then become cache hits. If the producer fails or its reservation expires, one joiner may replace it by compare-and-set with a new fence/Stage attempt while all others continue waiting; stale producers cannot publish. A different manifest at the same key fails closed, and failed/partial producers are never reusable. Re-delivering notification for an existing Stage attempt ID only attempts to claim that same Stage attempt; completed work is a no-op and no notification creates a Processing request or Processing run. Replaying a Processing request returns its existing Processing run; an explicit reprocessing action uses a new Processing request ID and creates one new Processing run and may reuse only compatible Artifacts.
4. **Immutable output first.** Write an Artifact with a create-if-absent precondition, retain the returned object version, read that version back, and verify its digest before publishing success metadata.
5. **Metadata second.** Commit the Artifact reference and terminal Stage attempt transition in one metadata transaction after verification. Metadata never points to an absent or unverified Artifact.
6. **Recoverable split point.** A worker crash after Artifact creation but before metadata commit leaves an immutable orphan candidate. A later claimant verifies and adopts the exact expected Artifact or records the conflict; it never overwrites.
7. **Immutable processing definition.** A Processing run never observes mutable component/configuration defaults. A changed parser, OCR, renderer, model, prompt, schema, batching, scoring, or relevant setting creates a new digest and prevents stale reuse.
8. **Complete accounting.** A Processing run cannot be `SUCCEEDED` while an admitted page/stage is absent, unclaimed without terminal accounting, or supported only by an unverified Artifact.
9. **Projection isolation.** Pipeline decisions, claims, retries, cache checks, and UI truth never require an OpenSearch read. Projection lag/outage cannot corrupt authoritative state.
10. **Network denial remains meaningful.** Execution consumes prefetched exact Artifacts and does not make hosted inference, mutable downloads, or cloud control planes runtime dependencies.

The later authorized initial SQLite adapter may serialize claims because there is one worker. Its repository contract still exposes atomic claim/fence/transaction semantics rather than SQLite SQL or locking behavior. A later database adapter must satisfy the same externally observable invariants, not copy SQLite implementation details.

## Replaceable boundaries, not parallel implementations

The application core may depend on narrow interfaces exercised by the local vertical:

| Boundary | Initial adapter | Preserved future substitution |
|---|---|---|
| Source/Artifact storage | Versioned MinIO through S3-compatible operations | Another object store only if immutable-version, conditional-write, digest, and attribution semantics pass the contract. |
| Metadata/coordination repository | SQLite transaction adapter | A concurrent metadata store only if claim fencing, uniqueness, migrations, and authoritative-history semantics pass. |
| Parser | Docling adapter | Another parser only after its own measured/license decision and the same typed output/provenance contract. |
| VLM serving | Host-Ollama adapter | A later Linux service only after model/request/artifact identity and telemetry semantics remain explicit. Hosted inference is not implicitly allowed. |
| Search | Local OpenSearch adapter | Another Projection target rebuildable from authoritative metadata and Artifacts. |
| Inspection | Streamlit over application queries | Another UI using the same query/application records, never infrastructure-native objects. |

Any later authorized initial implementation will implement and test only one local adapter per exercised boundary. There is no transport interface now: the poller queries authoritative metadata and calls the claim operation directly. A future notification may carry an existing Stage attempt ID to that same claim operation, but remains lossy, duplicative, and non-authoritative.

Do not build a PostgreSQL repository, queue publisher/consumer, S3-specific backend, remote VLM server, or Kubernetes runtime “to prove” a seam. This decision itself authorizes none of the local implementation either. A seam is proved later by boundary tests and absence of infrastructure leakage, not by carrying two systems.

## Dependency-direction constraints

- Domain records and state transitions import no MinIO, boto, SQLAlchemy, SQLite, OpenSearch, Ollama, Docling, HTTP, Docker, Kubernetes, or AWS SDK types.
- Orchestration depends on typed application boundaries; infrastructure adapters translate at the edge.
- ORM rows, S3 responses, OpenSearch documents, Ollama payloads, and Docling-native structures do not cross their adapter boundary.
- Stage functions receive versioned records and Artifact references, not a global service container or ambient filesystem.
- Endpoint, credential, storage namespace, and resource names are explicit configuration; localhost and MinIO names are not hard-coded into domain identities.
- Credentials and authorization context never enter Processing definitions, cache keys, Artifacts, logs, or future work-notification records.
- Time and owner identity used for Work claims are injected at the repository boundary and recorded; domain tests do not rely on wall-clock sleeps.

Create interfaces only for boundaries exercised by the local architecture. Do not add generic cloud factories, provider enums, distributed base classes, deployment descriptors, or unused methods for imagined future services.

## Seam acceptance tests

A later authorized initial implementation must prove these constraints without distributed infrastructure:

1. Identity tests reproduce every `docproc-identity-v1` vector byte-for-byte, cover Unicode-normalization-distinct keys, and reject unknown identity versions.
2. Canonical round-trip tests for every versioned stage input/outcome and Artifact reference reject local paths, SDK/native objects, unknown required versions, and missing provenance.
3. Adapter contract tests prove MinIO conditional immutable writes, version-pinned readback/digest verification, and equivalent behavior through an in-memory test double used only by tests.
4. Repository contract tests simulate two owners: only one claim token wins; stale/expired tokens cannot heartbeat or complete; duplicate claims/deliveries do not duplicate producer state. Replaying one Processing request returns its original Processing run, while a new Processing request creates exactly one new producer or cached Processing run. Cache-reservation races prove only the fenced reservation owner executes, joiners wait/reuse, one expired owner can be replaced, and the stale owner cannot publish.
5. Crash-window tests write the expected Artifact without terminal metadata, then prove a fresh claimant verifies/adopts it; mismatched bytes at the immutable key fail closed.
6. Processing definition tests change each relevant identity independently and prove stale cache entries do not match.
7. Projection tests delete/recreate the OpenSearch index and rebuild it from SQLite plus exact MinIO Artifact references without parser/VLM re-execution.
8. Import-architecture tests fail when domain/application modules import forbidden adapter or deployment packages.
9. Configuration tests move endpoint/resource names without changing Document, Processing run, Stage attempt, or Artifact identities.
10. Offline tests prove stage execution makes no unlisted network request after explicit acquisition.

These tests establish semantic portability, not distributed throughput, high availability, or cloud fitness.

## Future migration proof scenarios

A later distribution effort must pass all of these before claiming compatibility:

- Existing local Source objects, Documents, Processing runs, Stage attempts, Artifacts, cache records, and Processing definitions migrate without identity changes.
- Two workers receive the same work notification; exactly one current Work claim can commit, and the loser performs no destructive write.
- A claim expires while its worker still runs; the stale worker's completion is fenced out after another worker claims.
- A worker dies at every boundary between claim, Artifact write/verification, and metadata commit; replay reaches one terminal outcome without overwriting or losing evidence.
- Queue loss is repaired by authoritative-state reconciliation; queue duplication/reordering does not alter Processing run history.
- Projection loss or lag is repaired from authoritative records without inference/parsing reruns.
- Artifact and model acquisition/distribution still satisfies the commit-pinned licensing and provenance gates for the actual deployment mode.

Passing local seam tests is necessary but not sufficient; the future effort must add database/object-store consistency analysis, load/failure measurements, threat modeling, observability, backup/recovery, cost, licensing, and deployment evidence.

## Explicitly absent now

Any later authorized initial implementation must contain no:

- PostgreSQL, RDS, DynamoDB, distributed SQLite, Redis, or second metadata backend;
- SQS, SNS, EventBridge, Kafka, RabbitMQ, Celery, workflow engine, queue table, outbox, or event webhook;
- Kubernetes, EKS, Helm, Kustomize, manifests, operators, ingress, service mesh, autoscaling, or pod scheduling logic;
- Terraform, CloudFormation, CDK, AWS account/region resources, IAM policy, secrets-manager integration, or cloud deployment scripts;
- application/Ollama container for the reference Mac, remote model service, hosted inference API, model gateway, or multi-model router;
- concurrent worker, distributed lease service, leader election, sharding, cross-region replication, or high-availability claim; or
- mirrored OCI images, model/OCR weights, datasets, third-party binaries, or offline appliance.

No particular future queue, database, object store, Kubernetes topology, AWS service, or model-serving route is selected. Those choices require evidence-backed decisions when a concrete distribution need exists.

## Trigger for a future distribution decision

Open a separate distribution initiative only when measured local evidence shows a named need such as concurrent throughput, isolation, team access, availability, data volume, or deployment policy that the one-worker reference system cannot satisfy. That initiative must state workload/SLO/security/distribution requirements first, compare concrete options, and preserve or explicitly migrate every invariant above.

Until then, the correct architecture is the local walking vertical with honest seams—not a dormant distributed platform.
