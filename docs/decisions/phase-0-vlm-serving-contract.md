# Phase 0 VLM and serving contract

Phase 0 will measure **`qwen3.5:9b-q4_K_M` through host Ollama** on the Apple M5 with 32 GB unified memory. It is a candidate model, not a selected model: one candidate is selected only after every applicable selection gate below passes. This resolves [issue #18](https://github.com/monocongo/docproc/issues/18) without authorizing model acquisition, serving, extraction, or pipeline implementation.

## Evidence relied on

This decision incorporates the findings and caveats of these commit-pinned artifacts by reference:

- [Local VLM serving on the Apple M5 reference machine](https://github.com/monocongo/docproc/blob/cc144e6239b4d4dff37f8325ad6feb70dc2d77f9/docs/research/local-vlm-serving-m5.md)
- [Dependency and artifact licensing gates](https://github.com/monocongo/docproc/blob/a6a0ce8014391d7956801154a39b8061fa8940f8/docs/research/dependency-artifact-licensing-gates.md)
- [Public accuracy benchmark and FUNSD decision](https://github.com/monocongo/docproc/blob/4c1714d372a89d2ee99373a2bccbd33c6cd66e9c/docs/adr/0001-public-evaluation-corpus.md)

The stale Qwen2.5-VL recommendation is rejected. No VLM ADR is accepted by this planning decision; a durable model-selection ADR waits for measurements from the bounded M5 spike.

## Candidate and artifact contract

The primary candidate is exactly `qwen3.5:9b-q4_K_M`, not `latest`, a bare model name, or a size-only alias. Its research-time evidence is:

- Ollama manifest SHA-256 `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`;
- config-layer SHA-256 `be595b49fe22012bd1f5605ec14c7ffa58331783a88a4fd8c22e5fc8ec42cf9f`;
- model-layer SHA-256 `dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c`, 6,594,462,816 bytes;
- license-layer SHA-256 `7339fa418c9ad3e8e12e74ad0fd26a9cc4be8703f9c110728a992b193be85cb2`, containing Apache-2.0; and
- parameters-layer SHA-256 `9371364b27a52acac9d87f88bd93c9db1174d8d6ec57f6888925cdc1788871ff`.

The server candidate is exact Ollama `v0.32.6`, host-installed and bound only to `127.0.0.1:11434`. The Phase 0 lock must add the publisher's digest for the actual macOS release asset and verify it before the server is admitted. Running Ollama in a container or calling hosted inference is outside this contract.

The lock records the separate upstream revision `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a` and its exact license evidence. The public Ollama layers do not cryptographically prove conversion from that revision, so the accepted provenance state for this bounded spike is **unverified conversion lineage**. Documentation must never claim otherwise. Self-conversion is not added to Phase 0; a later requirement for cryptographic lineage triggers a new artifact decision.

Selection gate **A — artifact identity** fails before inference on any mismatch in server asset/version, installed manifest, layer digest/size, Q4_K_M quantization, model family/parameter metadata, vision capability, embedded license, upstream evidence, or approved provenance state. Pull once under explicit observation, record every artifact, then deny external network access for measured runs. Do not commit or mirror server binaries, model layers, or weights.

## Population and scoring contract

The selection gate uses a six-page, explicitly acquired **`vlm-smoke-v1`** manifest drawn only from the `NAF-linked-v3` training split. Before the first candidate request, that manifest must freeze and digest exactly six image identities, source-image hashes, converted-PDF hashes, eligible linked-field ground truth, exclusion records, and selection rationale. It remains byte-identical across candidate models and request variants. Validation and test pages are forbidden; this smoke measurement is not the public accuracy benchmark.

A versioned scoring contract is frozen and digested at the same time. It identifies the ground-truth manifest and defines text normalization, eligible-edge conversion, repeated-label association, evidence endpoint matching, exact/character-similarity measures, thresholds, deterministic tie-breakers, exclusions, and micro aggregation. Candidate, request-variant, repair, and repetition comparisons all use that one scoring contract. No evaluated-accuracy number is reportable without both digests.

No corpus or scorer is implemented by this decision. Gate A cannot pass later until the two required content-addressed inputs exist.

## Request and state-transition contract

Every primary and fallback measurement uses the same serving contract except for the exact model identity:

- call Ollama's native `POST /api/chat` endpoint through the project adapter;
- send exactly one rendered page per request at concurrency one;
- use the complete canonical extraction JSON Schema both as `format` and in the versioned prompt;
- set `think: false`, `stream: false`, `temperature: 0`, `seed: 42`, `num_ctx: 16384`, `num_predict: 4096`, and warm `keep_alive: "10m"` explicitly;
- bound image dimensions/pixels, rendered bytes, parser context, prompt size, and response size under frozen policies;
- preserve the population, scoring, rendered-image, prompt, schema, renderer, image-policy, parser-context, batching-policy, generation-option, health-policy, and request digests; and
- require every admitted page to produce an accepted extraction or an explicit per-page failure.

Response handling has no operator choice:

1. Classify every first or repair outcome before schema validation, using this precedence: an explicit server rejection of `think`, vision input, or the complete JSON Schema on an otherwise contract-valid request fails Gate C at any HTTP status; a timeout, transport error, or other HTTP 5xx fails Gate L; any other HTTP 3xx/4xx, non-contract-valid HTTP 2xx response envelope, malformed client request, or environment/configuration error makes the measurement invalid rather than failing a candidate. Every such terminal outcome is preserved, followed by deadline-bound unload and matrix abort.
2. Only a contract-valid HTTP 2xx response proceeds to Pydantic validation. Preserve the first raw response and validation result. Accept it when schema-valid.
3. For a schema-invalid first response, issue exactly one repair attempt using the remaining page-time budget. If no budget remains, record a timeout and fail Gate L rather than skipping repair.
4. Apply step 1 to the repair outcome, then preserve every contract-valid HTTP 2xx repair response and validation result. Accept a schema-valid repair; record an explicit page failure for a schema-invalid repair.
5. An invalid measurement authorizes no fallback. Correct and review the defect, recompute affected serving-contract digests, and restart that candidate's complete matrix from step 1.
6. Never retry an individual timeout, transport error, server error, or explicit page failure.

The two request variants run in fixed order: **image-only**, then **image plus the same bounded Docling context**. Image-only is the selection-gate baseline. Retain parser context only if its 18 warm page results pass every gate; have strictly higher linked-field micro F1; introduce no additional explicit page failure; and have per-repetition schema-valid-page counts, an evidence-grounded-field rate, and a maximum warm page time no worse than image-only. The evidence-grounded-field rate is grounded fields divided by all fields in accepted extractions across the 18 results; it is zero if ground truth is non-empty and the candidate emits no fields. Any tie or mixed result selects image-only. A context-variant failure never authorizes a model fallback when image-only passes.

The context allocation is exactly 16,384 tokens. Reducing it, inheriting Ollama's machine-dependent default, multi-page requests, batching, concurrency above one, or speculative decoding changes the serving contract and requires an explicit adjust decision; it is not a silent retry.

## Timeouts and cleanup

- A cold page has a 180-second total wall-clock budget. A warm page has a 90-second total wall-clock budget. A repair attempt receives only the page's remaining budget.
- The client deadline on each HTTP call is the remaining page budget. On expiry, close the response/connection, record a timeout, and do not retry.
- A warm-up request has a 180-second client deadline. Failure to warm up prevents the warm matrix and fails Gate L.
- At every matrix unload/reset point and before every abort—including invalid measurement, capability rejection, health failure, timeout, or transport/server failure—request model unload with `keep_alive: 0` under a separate 30-second cleanup deadline. Cleanup failure fails Gate M; it is never hidden by restarting and continuing.

## Coexistence health policy

Before the first candidate request, freeze and digest these localhost probes. Execute each probe at matrix step 1 after the 60-second wait, at step 3 after the 60-second wait, after every warm page result in step 5, and at step 6 after final unload and its 60-second wait. A probe has a two-second deadline and no retry:

- Ollama version: `GET http://127.0.0.1:11434/api/version` returns HTTP 200 with JSON `version` exactly `0.32.6`.
- Ollama process state: `GET http://127.0.0.1:11434/api/ps` returns HTTP 200. At steps 1, 3, and 6, `models` is empty. After each warm page, `models` contains exactly one entry: its digest equals the locked candidate digest and its `context_length` equals `16384`.
- MinIO: `GET http://127.0.0.1:9000/minio/health/ready` returns HTTP 200.
- OpenSearch: `GET http://127.0.0.1:9200/_cluster/health` returns HTTP 200 with JSON `status` equal to `yellow` or `green` and `timed_out` equal to `false`.

Any failed probe fails Gate M and aborts the current candidate matrix. This policy measures coexistence with the agreed local stack; it does not authorize implementing or starting those services on this branch.

## Fixed run matrix

For each candidate and each request variant, process the six manifest pages in manifest order:

1. **Pre-load baseline:** ensure the model is unloaded, wait 60 seconds, then record memory/swap and all health probes.
2. **Cold pass:** for each page, run one page result with cold `keep_alive: 0` and the 180-second page budget; retain cold failures without substituting another page.
3. **Warm reset:** unload under the cleanup deadline, wait 60 seconds, and record the memory/swap baseline used by Gate M.
4. **Warm-up:** load the candidate with the first manifest page, warm `keep_alive: "10m"`, and the 180-second deadline; retain but do not score the response.
5. **Warm repetitions:** process all six pages three times with warm `keep_alive: "10m"`, preserving manifest order and keeping the model loaded. These 18 page results are the schema, evidence, evaluated-accuracy, compatibility, latency, and steady-state memory population.
6. **Final unload:** request `keep_alive: 0`, wait 60 seconds, then capture final memory/swap and health probes.

A page result comprises its first request and mandatory repair attempt when the first response is schema-invalid. Cold and warm reports remain separate.

## Required measurements

Preserve every request, raw response, parsed response, schema result, repair response, accepted extraction, and explicit failure. Sample memory once per second during each pass and record:

- cold-load, prompt-evaluation, generation, total request, and total page durations, plus prompt/output tokens and generated tokens per second;
- first-response and final schema-valid counts;
- evidence-grounded-field and unsupported-field counts, plus admitted-page coverage;
- normalized linked-field precision, recall, micro F1, exact match, and character similarity under the scoring contract;
- process RSS, `/api/ps` model memory and allocated context, macOS memory pressure and swap, and every coexistence-health result;
- rendered-image dimensions/bytes and all serving-contract identities; and
- timeout, cancellation, unload, non-empty thinking output, explicit capability rejection, server failure, and byte/semantic differences across the three seeded warm repetitions.

## Selection gates

The gates apply to the image-only baseline. The optional context variant can be retained only by the dominance rule above.

- **Gate A — artifact identity:** all artifact, license, server, vision-capability, request, population, scoring, and provenance-state checks pass before inference.
- **Gate M — memory and coexistence:** no OOM, process kill, cleanup failure, or coexistence-health failure occurs; no red memory-pressure sample occurs; yellow pressure never persists for 30 consecutive seconds; and swap after final unload plus the 60-second idle is no more than 512 MiB above the warm-reset baseline.
- **Gate L — latency:** warm-up completes within 180 seconds, and every one of the 18 warm page results returns its final server response within its 90-second total page budget, including repair time. A timeout, transport error, or non-capability HTTP 5xx fails Gate L and aborts the candidate matrix; a completed schema-invalid response is classified by Gate S.
- **Gate C — structured-serving compatibility:** the candidate neither returns non-empty thinking output with `think: false`, explicitly rejects `think`, vision, or the complete JSON Schema on an otherwise contract-valid request at any HTTP status, nor meets the repeated schema-incompatibility criterion below.
- **Gate S — schema:** in each of the three warm repetitions, at least five of the six pages produce an accepted extraction after the deterministic repair transition.
- **Gate E — evidence and coverage:** every admitted page has an accepted extraction or explicit failure record; every field in an accepted extraction cites checkable visible evidence on that page; invented block IDs or alignment are forbidden. Evidence-grounded-field counts and unsupported fields remain separately visible.
- **Gate R — evaluated report:** the complete report includes both request variants, all cold/warm requests, repairs, admitted pages, explicit failures, exclusions, serving-contract identities, frozen population/scoring digests, evaluated-accuracy metrics, and seeded-repeat differences.

The repeated schema-incompatibility criterion for Gate C is exact: the same page remains schema-invalid after its mandatory repair attempt in at least two of three repetitions, for at least two of the six pages. An isolated schema-invalid page, low evaluated accuracy, unsupported evidence, parser-context regression, malformed client request, failed health probe, or unmeasured concern is not a Gate C failure.

There is deliberately no Phase 0 F1 threshold. Schema-valid, evidence-grounded, and evaluated accuracy remain separate; none substitutes for another.

## Fallback and outcome table

Evaluate gates in `A → M → L → C → S → E → R` order and apply exactly one row to the current candidate. One exception is terminal and unambiguous: an explicit capability rejection on an otherwise contract-valid request immediately fails Gate C and authorizes its named compatibility fallback; incomplete M/L measurements are recorded as not run, not pass or fail. Non-terminal Gate C evidence is evaluated only after M and L pass. Stop after one candidate passes all gates.

| Current candidate and first failed gate | Required outcome |
|---|---|
| Any candidate: A | Cut that artifact and local VLM extraction from the current Phase 0. A corrected or replacement artifact requires a new artifact decision before measurement. |
| 9B: M or L | Test `qwen3.5:4b-q4_K_M` under the identical contract. No other 9B failure authorizes 4B. |
| 4B: M or L | Cut local VLM extraction from the initial implementation. |
| 9B or 4B: C | Test `qwen3-vl:8b-instruct-q4_K_M` under the identical contract. |
| Qwen3-VL: M, L, C, S, E, or R | Cut local VLM extraction from the initial implementation. |
| 9B or 4B: S, E, or R | Cut local VLM extraction from the initial implementation. A later adjustment can reopen measurement only through a separately approved serving-contract decision. |
| Any candidate: no failed gate | Go with that candidate as the selected model and stop comparing. |

The 4B fallback's research-time manifest SHA-256 is `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`. The Qwen3-VL fallback's exact tag is `qwen3-vl:8b-instruct-q4_K_M` and its research-time manifest SHA-256 is `0533d74300e4f9bc367d675d4e64ffd073d50ff16a2b4096cc2e8a1cf8c96319`; the bare `qwen3-vl:8b` thinking alias is forbidden. Each fallback must capture and verify its complete layer, upstream, license, server, and provenance evidence before Gate A can pass.

No fallback is authorized for low evaluated accuracy because this milestone has no invented F1 threshold. Do not search additional models, reduce context silently, or substitute a hosted API.

## Consequences

Phase 0 has one current multimodal candidate, two narrowly triggered fallbacks, and a reproducible way to select at most one model. The plan accepts a clearly labeled conversion-lineage gap for the local spike while failing closed on artifact identity and distribution evidence. Evaluated accuracy remains something the spike reports—not a claim inferred from schema conformance, evidence presence, vendor benchmarks, or model size.
