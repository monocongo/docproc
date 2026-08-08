# docproc
Document processing pipelines

## Architectural Justification: The Modern Local-First PDF Pipeline

This repository implements a highly disciplined, spec-driven execution of a modern document processing pipeline. While legacy document pipelines rely on flat text extraction and external cloud dependencies, `docproc` compresses modern paradigms—vision-native parsing, LLM-driven structured extraction, and semantic indexing—into a fiercely governed, local-only "walking vertical."

This architecture prioritizes local data control, offline-capable operation, and exact evidence over premature scaling.

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

Pumping extracted JSON directly into a search index often leads to corruption or schema drift that is impossible to cleanly recover from. This architecture uses MinIO as the immutable source-document object store, mandates SQLite as the authoritative processing-state registry, and treats OpenSearch purely as a rebuildable projection. If the search cluster corrupts, its index can be rebuilt from SQLite's processing records and the exact immutable MinIO objects those records reference.

#### 2. Local Data Sovereignty

Running quantized models locally (e.g., `qwen3.5:9b-q4_K_M`) supports data privacy and offline operation by avoiding cloud inference; it does not by itself enforce network isolation, disable telemetry, or control storage. The frozen conformance matrix routes a 9B memory or latency failure to `qwen3.5:4b-q4_K_M` and a 9B/4B structured-serving compatibility failure to `qwen3-vl:8b-instruct-q4_K_M`; no other failure triggers a fallback, and no route uses a cloud API.

#### 3. Vision-Native Enforcement

Legacy OCR produces unpredictable text blobs that cause downstream AI to hallucinate. This pipeline enforces Docling with full-page RapidOCR/ONNX while explicitly banning automatic/heuristic OCR fallbacks. Parser output advances only after passing the configured structural gates within the 300-second document limit; a hard-gate failure is retained as an Adjust outcome and stops dependent work without an automatic retry or parser/OCR fallback. Individual inference timeouts are recorded without retry, and only eligible gate failures follow the named model routes above.

#### 4. Bounded Execution

Rather than building a distributed system on day one, this blueprint enforces a "walking vertical." A single polling worker validates the data contracts (ingest ➔ parse ➔ extract ➔ project) end-to-end while preserving these identity invariants:

- **Source Object:** One received occurrence, identified from its storage namespace, bucket, object key, and immutable object version. Its locator and version never change; a different key or version creates a new Source Object, and each Source Object links to exactly one Document.
- **Document:** Immutable content identity, identified by the SHA-256 digest of the exact PDF bytes. Source Objects with identical bytes share one Document; changed bytes create a new Document.
- **Processing Run:** One attempt with a new UUIDv4 for each Processing Request, including cache hits, with immutable references to exactly one Source Object, its Document, and one processing-definition digest. Replaying a request returns its existing run; reprocessing requires a new request and child run rather than overwriting history.
- **Evidence Record:** A content-addressed, immutable envelope and payload that link the observed Processing Run and its exact version-pinned artifacts to their inputs, environment, outcome, and specification references. Corrections or redactions create new linked records or artifacts; they never mutate prior evidence.

Kubernetes, AWS, and other distributed scaling remain deferred until the walking vertical demonstrates these invariants and lifecycle relationships.
