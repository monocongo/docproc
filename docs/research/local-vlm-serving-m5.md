# Local VLM serving on the Apple M5 reference machine

- **Resolves:** [Validate local VLM serving on the reference Mac](https://github.com/monocongo/docproc/issues/7)
- **Researched:** 2026-08-08
- **Reference machine:** Apple M5, 32 GB unified memory, macOS 26.6.1
- **Current environment:** Ollama is not installed; this research specifies the Phase 0 spike rather than claiming measured performance

## Conclusion

Phase 0 should test **Qwen3.5-9B served locally by Ollama**, using the explicit Ollama artifact `qwen3.5:9b-q4_K_M`. The blueprint's Qwen2.5-VL-7B recommendation is now stale. Qwen3.5 is Qwen's current natively multimodal generation, is Apache-2.0, includes document-understanding and OCR evaluation, and is available as a 6.59 GB Q4_K_M Ollama artifact that should fit comfortably enough to justify a measured attempt on the 32 GB M5.

Use Ollama's native `/api/chat` endpoint because it supports images, JSON Schema structured output, explicit non-thinking mode, deterministic generation options, timing counters, model digests, quantization metadata, context allocation, and reported model memory. Run Ollama on the host so Apple Metal remains available; do not containerize it for the reference-Mac implementation.

Do not compare several models preemptively. If the 9B candidate fails a resource or warm-latency hard gate, retry the same request contract with `qwen3.5:4b-q4_K_M`. If Qwen3.5's non-thinking structured-output path itself is incompatible, use `qwen3-vl:8b-instruct-q4_K_M` as the compatibility fallback. Select one model at the Phase 0 gate and stop comparing.

## Why Qwen3.5 replaces Qwen2.5-VL

Qwen's authoritative Qwen3.5 model card describes a unified vision-language foundation, a vision encoder, native 262,144-token context, document-understanding/OCR benchmarks, and Apache-2.0 terms. It states that Qwen3.5 improves on Qwen3-VL across visual understanding and other capabilities. Vendor benchmark claims are not project evidence, but they are sufficient to make the current model—not the older Qwen2.5 generation—the provisional spike candidate.

The 9B model operates in thinking mode by default. Structured extraction does not need a reasoning trace, so every request must set `think: false`; relying on a server or tag default would make latency, output parsing, and cache fingerprints unstable.

Sources:

- [Qwen3.5-9B model card at the researched revision](https://huggingface.co/Qwen/Qwen3.5-9B/tree/c202236235762e1c871ad0ccb60c8ee5ba337b9a)
- [Qwen3.5-4B model card at the researched revision](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a)
- [Qwen3-VL-8B-Instruct compatibility fallback](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/tree/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b)
- [Older Qwen2.5-VL-7B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/tree/cc594898137f460bfe9f0759e9844b3ce807cfb5)

## Explicit Ollama artifacts

Research-time registry inspection found:

| Candidate | Quantization | Model layer | Ollama manifest SHA-256 | Purpose |
|---|---|---:|---|---|
| `qwen3.5:9b-q4_K_M` | Q4_K_M | 6,594,462,816 bytes | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | Primary |
| `qwen3.5:4b-q4_K_M` | Q4_K_M | 3,389,971,840 bytes | `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd` | Resource/latency fallback |
| `qwen3-vl:8b-instruct-q4_K_M` | Q4_K_M | 6,140,392,672 bytes | `0533d74300e4f9bc367d675d4e64ffd073d50ff16a2b4096cc2e8a1cf8c96319` | Structured-output compatibility fallback |

The Qwen3.5 9B manifest declares model type `9.7B`, Q4_K_M, and a minimum Ollama version of `0.17.1`. At research time Ollama's latest release was `v0.32.6`; Ollama code is MIT and supports Apple M-series CPU/GPU on macOS Sonoma or newer.

Never use `latest` or a size-only alias in benchmark configuration. The bare `qwen3-vl:8b` alias currently resolves to a **thinking** variant rather than the required instruct variant, demonstrating why exact tag and digest verification are mandatory.

The lock must record both the upstream Qwen revision and the Ollama manifest/model-layer digests. These are independent provenance claims: the Ollama manifest does not itself cryptographically prove which Hugging Face commit produced its GGUF. If that provenance gap is unacceptable, Phase 0 must build/import a GGUF from the pinned upstream revision and lock the resulting local artifact instead of pretending the public tag supplies the linkage.

Sources:

- [Ollama Qwen3.5 9B Q4_K_M artifact](https://ollama.com/library/qwen3.5:9b-q4_K_M)
- [Ollama Qwen3.5 4B Q4_K_M artifact](https://ollama.com/library/qwen3.5:4b-q4_K_M)
- [Ollama Qwen3-VL 8B Instruct Q4_K_M artifact](https://ollama.com/library/qwen3-vl:8b-instruct-q4_K_M)
- [Ollama `v0.32.6`](https://github.com/ollama/ollama/releases/tag/v0.32.6)
- [Ollama macOS requirements](https://docs.ollama.com/macos)

Registry manifests are mutable remote metadata; the values above are research evidence, not a substitute for capturing and verifying the artifact actually installed during Phase 0.

## Serving contract

Use host Ollama bound to `127.0.0.1:11434` and call `POST /api/chat` through the project's own `httpx` adapter. The request contract should start as:

```json
{
  "model": "qwen3.5:9b-q4_K_M",
  "messages": [
    {
      "role": "user",
      "content": "<versioned extraction prompt plus bounded parser context>",
      "images": ["<one base64-encoded rendered page>"]
    }
  ],
  "format": {"$ref": "<canonical FormExtraction JSON Schema>"},
  "think": false,
  "stream": false,
  "options": {
    "temperature": 0,
    "seed": 42,
    "num_ctx": 16384,
    "num_predict": 4096
  }
}
```

The actual `format` value is the complete canonical JSON Schema, not a `$ref`; the abbreviated object above keeps the example readable. Include the same schema in the prompt as Ollama recommends, then validate `message.content` again with Pydantic. Server-side constrained decoding is not an accuracy guarantee.

Start Phase 0 with one page per request and concurrency one. Three-page batching should not be a default before single-page accuracy, context use, memory, and latency are measured. Bound image dimensions/pixels and parser text deterministically; preserve the exact rendered-image digest and request metadata.

Sources:

- [Ollama vision requests](https://docs.ollama.com/capabilities/vision)
- [Ollama structured outputs, including vision and Pydantic](https://docs.ollama.com/capabilities/structured-outputs)
- [Ollama chat API](https://docs.ollama.com/api/chat)
- [Ollama thinking control](https://docs.ollama.com/capabilities/thinking)

## Reproducibility contract

`models.lock.json` must record and `docproc models verify` must check:

- logical model role;
- exact Ollama tag;
- locally installed manifest digest from `/api/tags`;
- quantization, format, parameter size, model family, and vision capability from `/api/show`;
- model-layer digest and size when captured;
- upstream repository and revision, with the conversion-provenance caveat;
- embedded license text digest;
- exact Ollama version from `/api/version`;
- prompt, schema, renderer, image-policy, batching-policy, and parser-context digests;
- `think`, `temperature`, seed, context, output limit, and all other generation options; and
- reference hardware and operating system.

Verification must fail before inference on any mismatch. Pull once, capture the lock, disable external network access, and rerun the measured smoke spike locally. A floating tag that now resolves to different contents is a new candidate, not the same benchmark.

Ollama's `/api/tags` reports model SHA-256, format, parameter size, and quantization. `/api/show` reports license, capabilities, template, parameters, and model metadata. `/api/ps` reports loaded model digest, memory usage, and allocated context. `/api/version` reports the server version.

Sources:

- [List installed models](https://docs.ollama.com/api/tags)
- [Show model details](https://docs.ollama.com/api-reference/show-model-details)
- [List running models and memory/context data](https://docs.ollama.com/api/ps)
- [Get Ollama version](https://docs.ollama.com/api-reference/get-version)

## Phase 0 measurements

Run the fixed smoke forms twice: image-only and image plus the same bounded Docling context. Preserve every request, raw response, parsed response, validation result, repair response, and accepted extraction.

Record per request:

- cold load, prompt evaluation, generation, and total durations;
- prompt and output token counts and generated tokens/second;
- first-response and final schema validity;
- evidence grounding and unsupported-field count;
- normalized question/answer precision, recall, and micro F1;
- exact match and character similarity;
- process RSS, `/api/ps` model memory, allocated context, and macOS memory pressure;
- rendered-image dimensions and bytes;
- timeout, cancellation, unload, and server-restart behavior; and
- deterministic-output differences across at least three identical seeded requests.

Measure cold requests by unloading with `keep_alive: 0`, then measure warm requests with a documented keep-alive. Do not mix cold and warm latency. The published benchmark must identify which mode it reports.

## Hard gates and outcomes

### Go

Use Qwen3.5 9B only if it:

1. verifies the exact artifact, license, server version, and vision capability before inference;
2. runs the fixed one-page request at 16K context on the M5 without OOM, sustained swap growth, or unhealthy local services;
3. completes warm requests within the provisional 90-second-per-page timeout;
4. produces final schema-valid output for at least five of six fixed smoke forms after no more than one repair;
5. represents every admitted page or records an explicit per-page failure;
6. retains visible evidence for accepted fields rather than inventing alignment; and
7. produces a complete measured accuracy report with all failures and exclusions visible.

Accuracy must be measured, but this initial engineering milestone has no invented F1 pass threshold. Schema validity, evidence grounding, and evaluated accuracy remain distinct.

### Adjust

- If only memory or warm latency fails, test `qwen3.5:4b-q4_K_M` with the identical contract.
- If Qwen3.5 cannot reliably disable thinking or honor the structured vision schema through the pinned Ollama release, test `qwen3-vl:8b-instruct-q4_K_M`.
- If parser context is measurably worse, choose image-only extraction; do not keep context because the architecture expected it.
- If 16K context is excessive, reduce it only after recording image and prompt token use; never inherit Ollama's machine-dependent default.

### Cut

Cut local VLM extraction from the initial implementation if no candidate can fit, finish within the timeout, produce bounded schema-valid evidence-grounded output, or satisfy the license/provenance gate. Do not replace it with a hosted API under this issue.

## Required blueprint changes

1. Replace Qwen2.5-VL-7B/3B with Qwen3.5 9B/4B candidates.
2. Name the explicit Q4_K_M tag and forbid `latest` and size-only aliases.
3. Set `think: false`, temperature zero, fixed seed, explicit context, and bounded output in the request fingerprint.
4. Start with one page per request and concurrency one; make batching a measured later optimization.
5. Separate cold and warm timing and capture Ollama's native token/duration telemetry.
6. Verify installed digest, quantization, vision capability, license, model metadata, and server version before inference.
7. Document the upstream-to-Ollama conversion-provenance gap.
8. Keep the model server on the host for Metal; preserve an adapter seam for a later Linux/EKS serving implementation.
9. Retain one repair attempt, raw-response capture, full page-coverage accounting, and accuracy reporting.
10. Create the VLM ADR only after the M5 spike supplies measured evidence.

## Decision surfaced

The blueprint needs explicit approval of Qwen3.5 9B Q4_K_M through host Ollama as the Phase 0 candidate, with the 4B and Qwen3-VL fallbacks limited to named hard-failure modes. It must not silently preserve the older Qwen2.5 selection merely because that was current when the original draft was written.
