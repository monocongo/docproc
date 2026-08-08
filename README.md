# docproc
Document processing pipelines

## Architectural Justification: The Modern Local-First PDF Pipeline

This repository implements a highly disciplined, spec-driven execution of a modern document processing pipeline. While legacy document pipelines rely on flat text extraction and external cloud dependencies, `docproc` compresses modern paradigms—vision-native parsing, LLM-driven structured extraction, and semantic indexing—into a fiercely governed, local-only "walking vertical."

This architecture prioritizes absolute data sovereignty, offline determinism, and exact evidence over premature scaling.

### Legacy vs. Modern Architecture

| Feature | Legacy Pipeline Approach | Modern `docproc` Approach |
| :--- | :--- | :--- |
| **Pipeline Flow** | Ingest ➔ OCR ➔ Inference ➔ ES-Index ➔ UI | MinIO ➔ Worker ➔ Docling ➔ Local Ollama ➔ SQLite/OpenSearch ➔ Streamlit |
| **Parsing Strategy** | Dumb OCR (flattens layouts, destroys tables). | Vision-native parsing (preserves reading order, tables, and visual hierarchy). |
| **State Management** | Search index acts as the primary database, risking split-brain state drift. | SQLite is authoritative; OpenSearch is strictly a rebuildable Projection. |
| **Inference & Privacy** | Cloud APIs (GPT-4, Claude) requiring data egress and creating privacy risks. | 100% local host Ollama quantized models with a strict, frozen fallback routing matrix. |
| **Execution Boundaries** | Prematurely distributed (Kafka, Celery, Kubernetes) complicating debugging. | Single polling worker enforcing deterministic, end-to-end data contracts. |
| **Testing & Evaluation** | Evaluated on real "anonymized" data, risking PII leakage into Git. | Synthetic-only CI fixtures isolated from the public accuracy benchmark. |

### Core Advantages of the `docproc` Blueprint

#### 1. The Projection Pattern (State Management)

Pumping extracted JSON directly into a search index often leads to corruption or schema drift that is impossible to cleanly recover from. This architecture mandates SQLite as the authoritative state registry and treats OpenSearch purely as a rebuildable projection. If the search cluster corrupts, the index can be deterministically reconstructed from the SQLite and MinIO sources of truth.

#### 2. Absolute Data Sovereignty

By explicitly locking the runtime to local quantized models (e.g., `qwen3.5:9b-q4_K_M`), the pipeline guarantees absolute data privacy and offline capability. To account for the limitations of smaller local models, the pipeline utilizes a strict, mathematically sound fallback routing matrix (e.g., degrading to `4b` or vision-enabled `qwen3-vl` only on specific gate failures) rather than silently dropping data or reaching out to cloud APIs.

#### 3. Vision-Native Enforcement

Legacy OCR produces unpredictable text blobs that cause downstream AI to hallucinate. This pipeline enforces Docling with full-page RapidOCR/ONNX while explicitly banning automatic/heuristic OCR fallbacks. By establishing strict timeout limits and hard gates, it ensures the downstream LLM relies on perfectly predictable, structurally intact Markdown/JSON tables every single time.

#### 4. Bounded Execution

Rather than building a distributed system on day one, this blueprint enforces a "walking vertical." A single polling worker validates the data contracts (ingest ➔ parse ➔ extract ➔ project) end-to-end while preserving these identity invariants:

- **Source Object:** One received occurrence, identified from its storage namespace, bucket, object key, and immutable object version. Its locator and version never change; a different key or version creates a new Source Object, and each Source Object links to exactly one Document.
- **Document:** Immutable content identity, identified by the SHA-256 digest of the exact PDF bytes. Source Objects with identical bytes share one Document; changed bytes create a new Document.
- **Processing Run:** One attempt with a new UUIDv4 for each Processing Request, including cache hits, with immutable references to exactly one Source Object, its Document, and one processing-definition digest. Replaying a request returns its existing run; reprocessing requires a new request and child run rather than overwriting history.
- **Evidence Record:** A content-addressed, immutable envelope and payload that link the observed Processing Run and its exact version-pinned artifacts to their inputs, environment, outcome, and specification references. Corrections or redactions create new linked records or artifacts; they never mutate prior evidence.

Kubernetes, AWS, and other distributed scaling remain deferred until the walking vertical demonstrates these invariants and lifecycle relationships.
