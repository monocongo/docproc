# Parser-spike candidates and decision rule research

- **Resolves:** [Validate the parser-spike candidates and decision rule](https://github.com/monocongo/docproc/issues/6)
- **Researched:** 2026-08-08
- **Reference machine:** Apple M5, 32 GB unified memory
- **Legal status:** Engineering research, not legal advice

## Conclusion

Docling remains the defensible provisional production parser. Its current standard pipeline exposes layout, reading order, table structure, OCR, bounding boxes, lossless JSON, and a typed `DoclingDocument`; it supports macOS arm64 and explicit CPU/MPS execution. That shape fits the proposed typed internal document representation and keeps parser-specific types behind one adapter.

The planned Docling-versus-Marker spike needs revision. Marker 2 is now technically credible and its **code is Apache-2.0**, so the blueprint's expected GPL-3.0 statement is stale. However, Marker's scanned-document path depends on Surya model weights under a modified OpenRAIL-M license with commercial, competitive-use, attribution, and output share-alike restrictions. Those restrictions are a poor fit for a permissively licensed public project that explicitly wants a later AWS/EKS path. Marker should not be a required production candidate unless the cross-cutting license decision explicitly accepts those terms.

Surya should not be treated as a third parser. It is the OCR/layout/table subsystem used by Marker. A direct Surya run is useful only as a diagnostic when a Marker result needs attribution; otherwise it duplicates the Marker spike and should be cut.

Phase 0 should first run a Docling conformance spike against predeclared acceptance criteria. It should add a comparative parser only if focused follow-up research finds a technically suitable candidate with permissive code **and model-weight** terms. A comparison is not valuable merely for having two columns.

## Current upstream facts

| Component | Current release | Code license | Relevant model terms | Role |
|---|---|---|---|---|
| Docling | `v2.118.1` | MIT | Selected model artifacts must be checked individually; the core Docling model repository advertises CDLA-Permissive-2.0 and Apache-2.0 | Provisional production parser |
| Marker | `v2.0.0` | Apache-2.0 | Modified OpenRAIL-M through Surya | Conditional challenger only |
| Surya | `v0.22.1` | Apache-2.0 | Modified OpenRAIL-M | Marker subsystem; diagnostic, not parser candidate |

Sources:

- [Docling release](https://github.com/docling-project/docling/releases/tag/v2.118.1) and [source revision](https://github.com/docling-project/docling/tree/72bb55bc765afcc01f60391b1f23978583e08fa4)
- [Marker release](https://github.com/datalab-to/marker/releases/tag/v2.0.0) and [source revision](https://github.com/datalab-to/marker/tree/e1a6226adfaab4cd573cfa96e12d60905ee38036)
- [Surya release](https://github.com/datalab-to/surya/releases/tag/v0.22.1) and [source revision](https://github.com/datalab-to/surya/tree/f2c45daaf67be28dfe09c602eb62a0df99a022a8)
- [Docling model repository metadata](https://huggingface.co/docling-project/docling-models/tree/2199320848bb9a8a519d22e4b528185a4f9a6f64)

These are research-time snapshots, not permission to use floating versions. Phase 0 must lock exact packages, source/model revisions, artifact digests, and configuration.

## Docling assessment

Docling's authoritative documentation states that it provides:

- advanced PDF layout, reading order, and table structure;
- a unified `DoclingDocument` representation;
- lossless JSON plus Markdown and HTML exports;
- OCR support for scanned PDFs and images; and
- macOS, Linux, Windows, x86_64, and arm64 support.

Its current model catalog exposes labeled layout boxes, TableFormer cell structure, and OCR backends including RapidOCR, Tesseract, EasyOCR, macOS Vision, and SuryaOCR. Accelerator configuration explicitly supports CPU and Apple MPS. TableFormer currently runs on CPU rather than MPS, which must be reflected in target-machine timings.

For this project, configure the standard PDF pipeline explicitly rather than relying on auto-selection:

1. Use full-page OCR for image-only forms.
2. Test **RapidOCR with ONNX Runtime** as the portable default candidate for later Linux deployment.
3. Test **macOS Vision (`ocrmac`)** on a small paired subset as a target-machine baseline, not as the portable production default.
4. Try EasyOCR only if those candidates fail an acceptance criterion; do not compare OCR engines indefinitely.
5. Pin layout, OCR, and table model artifacts and prefetch them before the measured/offline rerun.

The current Docling auto-selection chooses macOS Vision first on Darwin when installed, then RapidOCR/ONNX, then EasyOCR. Relying on that order would make cache fingerprints and Linux reproduction environment-dependent.

Sources:

- [Docling README and capability summary](https://github.com/docling-project/docling/blob/72bb55bc765afcc01f60391b1f23978583e08fa4/README.md)
- [Docling OCR engines](https://github.com/docling-project/docling/blob/72bb55bc765afcc01f60391b1f23978583e08fa4/docs/concepts/OCR.md)
- [Docling model catalog](https://github.com/docling-project/docling/blob/72bb55bc765afcc01f60391b1f23978583e08fa4/docs/usage/model_catalog.md)
- [Docling accelerator options](https://github.com/docling-project/docling/blob/72bb55bc765afcc01f60391b1f23978583e08fa4/docling/datamodel/accelerator_options.py)
- [Docling automatic OCR selection](https://github.com/docling-project/docling/blob/72bb55bc765afcc01f60391b1f23978583e08fa4/docling/models/stages/ocr/auto_ocr_model.py)

## Marker and Surya assessment

Marker 2 converts PDFs to Markdown, JSON, chunks, or HTML and exposes document/page/block trees with block types and polygons. It supports CPU, GPU, and MPS. Its default Apple/CPU `fast` mode uses lightweight layout and invokes the Surya VLM for scanned or damaged pages; `balanced` is GPU-oriented. Marker also states that complex layouts and forms may not render well, making an actual form-focused spike necessary rather than relying on its published general-document benchmark.

The comparison must disable Marker's optional hosted/third-party LLM refinement. `--use_llm` defaults to Gemini unless reconfigured and would violate the local-only requirement while confounding parser quality with a second generative model. For image-only forms, `--disable_ocr` is not a valid alternative because it skips scanned content.

Marker and Surya code are Apache-2.0, but their repositories distinguish code from model weights. The modified model license:

- restricts commercial use above stated funding/revenue thresholds;
- prohibits use competing with the licensor's products or services;
- requires attribution with output;
- applies share-alike terms to model output; and
- requires downstream users to receive and observe restrictions.

This is materially different from the blueprint's earlier GPL concern: isolated packaging does not remove model-use or output obligations. The cross-cutting licensing gate must decide whether even spike outputs may be published.

Surya 2 itself emits OCR/layout/table results and supports Apple Silicon through `llama.cpp`. Marker depends on it directly, so running Surya separately provides correlated evidence, not an independent parser comparison.

Sources:

- [Marker README, architecture, JSON output, limitations, and platform support](https://github.com/datalab-to/marker/blob/e1a6226adfaab4cd573cfa96e12d60905ee38036/README.md)
- [Marker model license](https://github.com/datalab-to/marker/blob/e1a6226adfaab4cd573cfa96e12d60905ee38036/MODEL_LICENSE)
- [Marker dependency on Surya](https://github.com/datalab-to/marker/blob/e1a6226adfaab4cd573cfa96e12d60905ee38036/pyproject.toml)
- [Surya README and Apple Silicon path](https://github.com/datalab-to/surya/blob/f2c45daaf67be28dfe09c602eb62a0df99a022a8/README.md)
- [Surya model license](https://github.com/datalab-to/surya/blob/f2c45daaf67be28dfe09c602eb62a0df99a022a8/MODEL_LICENSE)
- [Pinned Surya OCR model metadata](https://huggingface.co/datalab-to/surya-ocr-2/tree/3b3d4cdf88d6928b0acdc75181b13206ea67c4a3)

## Revised spike design

Use a fixed manifest after the corpus decision is complete:

- four scanned forms spanning handwriting, dense fields, checkboxes, and weak image quality;
- one rotated scanned form;
- one synthetic two-column digital PDF;
- one synthetic table PDF with expected cells and spans; and
- one synthetic PDF containing embedded raster/vector images.

Run every candidate from an isolated locked environment. Prefetch all artifacts, record their digests and licenses, disable network access and hosted-model paths for the measured rerun, and normalize outputs through the same internal-document adapter before scoring.

### Hard gates

A production candidate must:

1. install reproducibly under Python 3.12 on arm64 macOS;
2. have acceptable code, dependency, and model-artifact terms for the intended project;
3. run locally after an explicit prefetch, with no hidden network or hosted inference;
4. terminate within the configured timeout and produce an explicit outcome for every admitted page;
5. normalize into a valid internal document with stable page numbering, text blocks, reading order, source references, and real—not synthesized—coordinates where upstream provides them;
6. preserve the synthetic table's required row, column, text, and span assertions;
7. fit alongside the required local services on the 32 GB reference machine without memory-pressure failure; and
8. expose enough version/configuration information to build a complete parse fingerprint.

Malformed, encrypted, and limit-exceeding fixtures are expected input failures and should not count as parser failures.

### Measured scorecard

Record per document and aggregate:

- normalized word recall and character error rate against available ground truth;
- page and block coverage;
- fraction of text blocks with valid coordinates;
- reading-order rubric on fixed examples;
- exact semantic assertions for synthetic table cells and images;
- cold start, warm latency, peak RSS, model-server memory, output size, and artifact download size;
- warnings, crashes, timeouts, and nondeterministic output changes; and
- adapter complexity and loss of provenance during normalization.

Do not use vendor-published benchmark scores as the decision. They target different corpora, hardware, modes, and output formats.

### Selection rule

Keep Docling when it passes every hard gate and no challenger demonstrates a material extraction-relevant advantage on the same manifest.

Switch only when either:

- Docling fails a hard gate that the challenger passes; or
- the challenger improves normalized word recall by at least ten percentage points **and** does not regress coordinate coverage, reading order, required table assertions, licensing, reproducibility, or target-machine viability.

Treat differences below five percentage points as a tie and prefer Docling's typed integration and permissive expected stack. For a five-to-ten-point difference, inspect paired errors and keep Docling unless the errors demonstrably affect linked-field extraction. Record the evidence in the later parser ADR; do not continue parser comparison after the gate.

## Required blueprint changes

1. Keep Docling as a provisional default, not an accepted selection.
2. Replace stale claims that Marker is GPL-3.0 with the current code/model license distinction.
3. Make Marker conditional on the cross-cutting model-license decision; do not add it to production dependencies by default.
4. Remove the unconditional direct Surya run; retain it only as a diagnostic if Marker is actually tested.
5. Replace the vague EasyOCR comparison with RapidOCR/ONNX as the portable candidate and macOS Vision as a small M5 baseline.
6. Define the hard gates and common scorecard before running candidates.
7. Require a prefetched, network-disabled measured rerun.
8. Avoid parser claims based on a restricted corpus until the corpus decision is resolved.
9. Record exact release, source, model, OCR-backend, and configuration fingerprints.
10. Create the parser ADR only after measured Phase 0 evidence exists.

## Decision surfaced

The blueprint needs a decision on whether a Docling conformance spike is sufficient or whether Phase 0 should include a different, permissively licensed parser challenger. That choice should follow focused research into current alternatives; Marker/Surya should not silently remain the challenger merely because an older plan named them.
