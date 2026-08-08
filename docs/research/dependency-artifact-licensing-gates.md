# Dependency and artifact licensing gates

- **Resolves:** [Establish the dependency and artifact licensing gates](https://github.com/monocongo/docproc/issues/8)
- **Researched:** 2026-08-08
- **Scope:** The proposed public, local PDF-processing stack; revision snapshots below are research evidence, not final dependency pins
- **Legal status:** Engineering research, not legal advice

## Outcome

The reconciled Phase 0 architecture can remain **Docling-only**, with an explicit RapidOCR/ONNX backend and a small optional macOS Vision diagnostic. That is an architectural selection, not blanket license approval for its model artifacts. Marker and Surya are not dependencies unless Docling first fails a hard gate and a new license review approves their code, weights, and output terms. The VLM candidate remains `qwen3.5:9b-q4_K_M` through host Ollama. FUNSD remains restricted, optional, manual-download-only data.

No blanket license clearance follows from a project-level SPDX label. The repository should distribute source, lock metadata, acquisition code, and notices—not datasets, model/OCR weights, Ollama layers, third-party binaries, or mirrored service images. Exact wheels, native libraries, model files, OCI layers, and interpreter/tool distributions must pass the lock-time gate before implementation may call the environment reproducible or public-release-ready.

The current repository is [MIT-licensed](https://github.com/monocongo/docproc/blob/711af9175605e8ac9bcef1e734a6b83649534d04/LICENSE); the draft blueprint's proposed Apache-2.0 status is not operative. Keep MIT in the blueprint unless the maintainer explicitly changes the repository license.

### Disposition

| Class | Disposition before a lock exists |
|---|---|
| Permissive direct code with an exact license file | May remain proposed; recheck the exact locked wheel/binary and transitives. |
| Model/OCR repositories with only model-card metadata | Provisional spike candidates only; preserve the evidence gap and require explicit review of every downloaded file. |
| MPL, LGPL, CDLA, AGPL service, proprietary platform/EULA, or custom dataset terms | Mandatory review and documented distribution mode. |
| Missing/unknown license, unexpected download, or output-use restriction | Fail closed. Do not download, run, bundle, or publish output until approved. |

## Verified facts

### What the principal licenses say

Most duties below arise when covered copies are conveyed; AGPL §13 separately covers specified remote interaction with a modified program. Use of a dependency is not itself proof that the application is a derivative work.

| License | Verified distribution/network duties from the license text |
|---|---|
| [MIT](https://spdx.org/licenses/MIT.html) | Include its copyright and permission notice in copies or substantial portions. |
| [BSD-3-Clause](https://spdx.org/licenses/BSD-3-Clause.html) | Retain notices/disclaimer in source; reproduce them in binary documentation/materials; do not imply endorsement. |
| [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0.txt) | Supply the license, mark modified files, retain relevant notices, and propagate applicable upstream `NOTICE` attributions; includes a patent grant and termination clause. |
| [CDLA-Permissive-2.0](https://cdla.dev/permissive-2-0/) | When publishing or distributing covered Data, make the agreement available with it and preserve included notices; Results are not subject to the agreement's data-sharing conditions. |
| [MPL-2.0](https://www.mozilla.org/MPL/2.0/) | Keep Covered Software source files and modifications under MPL. Recipients of executable form must be told how to obtain the corresponding covered source. Separate files in a Larger Work may use other terms. |
| [LGPL-3.0](https://www.gnu.org/licenses/lgpl-3.0.html) | Conveyance requires the LGPL/GPL texts and applicable source/relinking or replacement rights for the library/combined work. |
| [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html) | Conveyance invokes GPL-style license and Corresponding Source duties. Section 13 requires a **modified** network version to offer its Corresponding Source prominently to remote users. |
| [PSF-2.0 and bundled CPython terms](https://github.com/python/cpython/blob/3bb231a6a5dc02b95658877318bf61501a7209e9/LICENSE) | Preserve the applicable PSF and bundled-component notices; distributed Python derivatives must summarize changes. |
| [SQLite public-domain dedication](https://www.sqlite.org/copyright.html) | SQLite's deliverable code is dedicated to the public domain; the exact runtime may still bundle other licensed components. |

### Docling, layout, table, and OCR

Docling [`2.118.1` at `72bb55b`](https://github.com/docling-project/docling/tree/72bb55bc765afcc01f60391b1f23978583e08fa4) is MIT. Its `docling` package is a meta-package over `docling-slim[standard]`; RapidOCR requires an additional explicit extra. Its source requests Heron from floating `main`, requests TableFormer tag `v2.3.0`, and its generic downloader enables extra layout-engine, Torch/Chinese OCR, CodeFormulaV2, and picture-classifier downloads unless flags narrow it. Those generic-prefetch artifacts and EasyOCR are **unapproved**: Phase 0 must not request them, and any fallback requires a fresh inventory. These are authoritative runtime facts, not merely model-card descriptions:

- [package and extras](https://github.com/docling-project/docling/blob/72bb55bc765afcc01f60391b1f23978583e08fa4/packages/docling/pyproject.toml#L5-L85)
- [generic downloader defaults](https://github.com/docling-project/docling/blob/72bb55bc765afcc01f60391b1f23978583e08fa4/docling/utils/model_downloader.py#L43-L70)
- [floating Heron revisions and ONNX override](https://github.com/docling-project/docling/blob/72bb55bc765afcc01f60391b1f23978583e08fa4/docling/datamodel/stage_model_specs.py#L990-L1006)
- [TableFormer `v2.3.0` request](https://github.com/docling-project/docling/blob/72bb55bc765afcc01f60391b1f23978583e08fa4/docling/models/stages/table_structure/table_structure_model.py#L99-L109)

The proposed Phase 0 prefetch must name only these candidate artifacts; the metadata-only rows remain subject to the model-artifact gate:

| Artifact | Exact research snapshot and digest | Verified license evidence | Disposition |
|---|---|---|---|
| Heron layout | [`docling-layout-heron@8f39ad3`](https://huggingface.co/docling-project/docling-layout-heron/tree/8f39ad3c0b4c58e9c2d2c84a38465abf757272d8); `model.safetensors` SHA-256 `00333a43451945aaf89db8ca9c0a17e75d1537c17db60fdb91aa95f4c7929e0c` | Exact-revision card metadata says Apache-2.0, but the repository has no license file. | Provisional; override `main`, capture metadata/text evidence, hash every file, and review before execution. |
| TableFormer | [`docling-models@fc0f2d4`](https://huggingface.co/docling-project/docling-models/tree/fc0f2d45e2218ea24bce5045f58a389aed16dc23), the commit behind `v2.3.0` | Exact-revision card metadata says CDLA-Permissive-2.0, but the repository has no license file. | Mandatory CDLA review. Whole-repository download fetches both weights; lock both or narrow acquisition. |
| TableFormer accurate | SHA-256 `2a7d6c924b3cd12fb99a09280ca9c33a89c5d60b93253617d2e088c1a40374d9` | Same repository-level metadata. | Selected runtime weight. |
| TableFormer fast | SHA-256 `3119563aab5a7c96fda4d621119b63fd8806272b86c30936d15507616422f718` | Same repository-level metadata. | Download collateral under the current helper; avoid or lock it. |
| RapidOCR code | [`3.9.2` at `095232a`](https://github.com/RapidAI/RapidOCR/tree/095232a4c94f7f0e6600ba5bba1177010ad696d4) | Exact Apache-2.0 file. | Proposed explicit OCR backend. |
| ONNX Runtime | [`1.28.0` at `da9b5e3`](https://github.com/microsoft/onnxruntime/tree/da9b5e364c465de65c49d91e696cd6485270757f) | Exact MIT file plus [`ThirdPartyNotices.txt`](https://github.com/microsoft/onnxruntime/blob/da9b5e364c465de65c49d91e696cd6485270757f/ThirdPartyNotices.txt). | Inspect the selected arm64 wheel and native contents. |
| RapidOCR detector | `PP-OCRv6_det_small.onnx`, SHA-256 `090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f` | RapidOCR's [exact registry](https://github.com/RapidAI/RapidOCR/blob/095232a4c94f7f0e6600ba5bba1177010ad696d4/python/rapidocr/default_models.yaml#L117-L138) records URL/hash; the [hosting repository metadata](https://www.modelscope.cn/models/RapidAI/RapidOCR) says Apache License 2.0. No checkpoint-specific license file or conversion provenance was found. | Provisional, metadata-only model evidence. |
| RapidOCR orientation classifier | `ch_ppocr_mobile_v2.0_cls_mobile.onnx`, SHA-256 `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` | Same evidence and gap. | Provisional. |
| RapidOCR recognizer | `PP-OCRv6_rec_small.onnx`, SHA-256 `6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884` | Same evidence and gap. | Provisional. |
| macOS diagnostic | [`ocrmac 1.0.1` at `a38d01c`](https://github.com/straussmaximilian/ocrmac/tree/a38d01c653272b30a6bb2d6f8655956ab678cc38), MIT; calls Apple's [Vision API](https://developer.apple.com/documentation/vision/recognizing-text-in-images) | No separately downloaded weight was identified. | Diagnostic only; record macOS build and Apple platform terms; never redistribute Apple components. |

Artifacts that the generic downloader can fetch but Phase 0 must disable include Heron ONNX (`40bde04`, Apache-2.0 metadata only, model SHA-256 `59c81a3a2923042d85034ffc487f8f47e4854117e879aef89b2b9f728fb4922a`), CodeFormulaV2 (`ecedbe1`, CDLA metadata only), and DocumentFigureClassifier v2.5 (`f859dfb`, MIT metadata only). TableFormerV2 [`51559fa`](https://huggingface.co/docling-project/TableFormerV2/tree/51559fad3946873e26a6f9b8e912f948e8745bef) has neither license metadata nor a license file and is denied.

A source-level list does not close Docling's transitive binary surface. The actual lock must inventory `docling-slim`, PyTorch, `docling-parse`, `docling-ibm-models`, `pypdfium2`/PDFium, Pillow, NumPy, and platform-specific wheels. For example, current pypdfium2 [`5.12.1` at `b3e7e67`](https://github.com/pypdfium2-team/pypdfium2/tree/b3e7e67a1e35c9436b52cb043d476b89ec8c38cb) carries a [large build-license inventory](https://github.com/pypdfium2-team/pypdfium2/tree/b3e7e67a1e35c9436b52cb043d476b89ec8c38cb/BUILD_LICENSES); checking only its package classifier would miss PDFium's contents.

### Qwen3.5 and host Ollama

| Artifact | Verified revision-specific facts | Distribution disposition |
|---|---|---|
| Upstream Qwen | [`Qwen/Qwen3.5-9B@c202236`](https://huggingface.co/Qwen/Qwen3.5-9B/tree/c202236235762e1c871ad0ccb60c8ee5ba337b9a) contains an exact [Apache-2.0 license file](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/LICENSE). Its four safetensor SHA-256 values are `db6f444b43d318c92f360a13a25561a6a65b10c0631b8ed305a426dbaa6c380e`, `31c7d7e2dd5d207840b31cc59083c8f4c4718959149e0358c0364052bb9a0330`, `7ec36ba3a4176a44c3c0876ad80c56a2f70c84bf008d82e9501df642f17dadec`, and `b62b0c4cd7e44edee103ee8f4fe225f246d5e768e07bfd5f25b63a8aa1fdd0c6`. | Record as upstream provenance evidence; do not commit or mirror weights. |
| Ollama server | [`v0.32.6` at `c82ebbd`](https://github.com/ollama/ollama/tree/c82ebbd5bfb9ec7d94d3894e9023db0fb224ff50), MIT. The [release](https://github.com/ollama/ollama/releases/tag/v0.32.6) publishes SHA-256 sums for macOS assets. | Host-installed process; if a binary is bundled later, inventory its Go/native dependencies and notices. |
| Ollama model | [`qwen3.5:9b-q4_K_M`](https://ollama.com/library/qwen3.5:9b-q4_K_M); manifest SHA-256 `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`; config `be595b49fe22012bd1f5605ec14c7ffa58331783a88a4fd8c22e5fc8ec42cf9f`; model layer `dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c` (6,594,462,816 bytes); license layer `7339fa418c9ad3e8e12e74ad0fd26a9cc4be8703f9c110728a992b193be85cb2` contains Apache-2.0; parameters layer `9371364b27a52acac9d87f88bd93c9db1174d8d6ec57f6888925cdc1788871ff`. | User-initiated direct pull; lock every manifest/config/layer digest and embedded license text; do not mirror. |

The public Ollama manifest does **not** identify the upstream Hugging Face commit, converter/quantizer revisions, or conversion command. The upstream and GGUF license evidence is compatible, but their lineage is not cryptographically established. The VLM gate must either retain that explicit provenance gap or self-convert the pinned upstream snapshot with a pinned recipe and lock the resulting GGUF.

The 4B and Qwen3-VL fallback artifacts from the [commit-pinned VLM research](https://github.com/monocongo/docproc/blob/cc144e6239b4d4dff37f8325ad6feb70dc2d77f9/docs/research/local-vlm-serving-m5.md) are not initial downloads. They enter the inventory only after their named hard-failure condition, with the same gate.

### Services and OCI images

| Service/image | Exact evidence | Obligations and boundary |
|---|---|---|
| MinIO server | Same-release source tag [`RELEASE.2025-09-07T16-13-09Z` at `07c3a42`](https://github.com/minio/minio/tree/07c3a429bfed433e49018cb0f78a52145d4bedeb), AGPL-3.0 with [`NOTICE`](https://github.com/minio/minio/blob/07c3a429bfed433e49018cb0f78a52145d4bedeb/NOTICE). [Registry metadata](https://hub.docker.com/v2/repositories/minio/minio/tags/RELEASE.2025-09-07T16-13-09Z) gives OCI index `sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`, arm64 manifest `sha256:9966a92a734f9411e32f4f41d7d9d826fcdc0f68c4e20b70295bd4e7c11f8a2f`, and config `sha256:8f08aee614800a237906bd48114d733e5ac5bfac4ccdf731f141b0e880d7a253`. Config labels identify UBI 9 Micro 9.6 and its [Red Hat UBI terms](https://www.redhat.com/en/about/red-hat-end-user-license-agreements#UBI). Current upstream says community edition is [source-only](https://github.com/minio/minio/blob/9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a/README.md#source-only-distribution), so the legacy image is no longer maintained. | Keep it unmodified and separately operated behind S3. Direct upstream pull by digest; no mirror/offline bundle. AGPL §13 applies when a modified version supports remote network interaction; conveying an image invokes AGPL source/license duties. |
| MinIO Python client | [`7.2.20` at `f671ca9`](https://github.com/minio/minio-py/tree/f671ca948b35978c39a3100e4ae0e9b93416b911), Apache-2.0 with [`NOTICE`](https://github.com/minio/minio-py/blob/f671ca948b35978c39a3100e4ae0e9b93416b911/NOTICE). | This imported client is not the AGPL server; preserve license/notice if conveyed. |
| OpenSearch server | [`3.8.0` at `e5a3c56`](https://github.com/opensearch-project/OpenSearch/tree/e5a3c5691be87af6c12dbe3e158c59c04ee72973), Apache-2.0 with [`NOTICE`](https://github.com/opensearch-project/OpenSearch/blob/e5a3c5691be87af6c12dbe3e158c59c04ee72973/NOTICE.txt). [Registry metadata](https://hub.docker.com/v2/repositories/opensearchproject/opensearch/tags/3.8.0) gives OCI index `sha256:bcc1797519726ceb6d651d4a3e60b7c30da91793914a8dfe75fd441d4f641509`, arm64 manifest `sha256:42e9343f4f4f2993c29e1ca6bc1b23e19d05478cc3bada8e136964f8ab702d20`, and config `sha256:0f05e388e343d971eb3a083fa0b19fec6b2f2ac8dc8e04cda88753ffadbdeceb`. Config history identifies Amazon Linux 2023 base `2023.12.20260727.0`; the [release Dockerfile](https://github.com/opensearch-project/opensearch-build/blob/38af40cc53ffaa54d37a851c26652630affc8906/docker/release/dockerfiles/opensearch.al2023.dockerfile) adds OS packages, JDK, plugins, and native libraries. | Direct upstream pull by digest. Mirroring/derivation first requires the [official component manifest](https://github.com/opensearch-project/opensearch-build/blob/38af40cc53ffaa54d37a851c26652630affc8906/manifests/3.8.0/opensearch-3.8.0.yml), final image SBOM, and complete notices. |
| OpenSearch client | [`3.2.0` at `8991792`](https://github.com/opensearch-project/opensearch-py/tree/8991792d3fcdfc221c9aef62d7e82c3d15ff0206), Apache-2.0 with [`NOTICE`](https://github.com/opensearch-project/opensearch-py/blob/8991792d3fcdfc221c9aef62d7e82c3d15ff0206/NOTICE.txt). | Preserve license/notice if conveyed. |
| Ollama / Streamlit | Ollama is the MIT host service above. Streamlit [`1.61.1` at `cc5f10b`](https://github.com/streamlit/streamlit/tree/cc5f10b7c5b2eb6174cb9fd36769b0b788de84a6) is Apache-2.0. | Localhost services; no hosted inference or external runtime API is approved. |

**Risk interpretation:** A separately operated, unmodified MinIO process does not automatically relicense the application's independent client code merely because they communicate over S3. This architectural separation is evidence, not a legal safe harbor. Publishing a Compose reference is also different from mirroring the image bytes. Seek legal review before distributing an offline appliance, modified MinIO build, or hosted MinIO-based product.

No application or Ollama container is proposed on the reference Mac. The source tags, Dockerfiles, component manifest, and registry configs above are separate evidence; none cryptographically attests the complete image build provenance. Top-level project/base-image licenses are not an image SBOM.

External network use is acquisition-only: the package index, Hugging Face, ModelScope, Ollama registry, Docker Hub, the authoritative FUNSD GitHub revision, and the selected host-package distributor. These are not approved hosted inference/runtime dependencies. Acquisition must record the origin, immutable identifier, final URL, response digest, and applicable artifact/data terms; measured reruns must deny external network access.

### PDF, interpreter, and host tools

| Component | Exact license evidence | Gate |
|---|---|---|
| qpdf | [`12.3.2` at `a898bb3`](https://github.com/qpdf/qpdf/tree/a898bb3a7289d1d05789d6d3f0d5dd534943a8da), Apache-2.0 with a multi-component [`NOTICE`](https://github.com/qpdf/qpdf/blob/a898bb3a7289d1d05789d6d3f0d5dd534943a8da/NOTICE.md). | Prefer host package-manager installation. If binary/package copies are distributed, preserve the full notice and inventory package dependencies. |
| pikepdf | [`10.11.0` at `1dd7a24`](https://github.com/pikepdf/pikepdf/tree/1dd7a243fc7c57a15db28809c11a03e05dcbd63c), [MPL-2.0](https://github.com/pikepdf/pikepdf/blob/1dd7a243fc7c57a15db28809c11a03e05dcbd63c/LICENSE.txt). Wheels vendor native qpdf-related content. | Mandatory review of the selected wheel; preserve notices and make MPL-covered source/modifications obtainable. Remove it if qpdf plus Docling make it unnecessary. |
| PyMuPDF | [`1.28.2` at `12786d1`](https://github.com/pymupdf/PyMuPDF/tree/12786d12b2962a1d77fd13b103162eddf749644c), AGPL-3.0 or commercial terms. | Not proposed and denied as a casual pikepdf replacement without commercial licensing or specific review. |
| img2pdf | [`0.6.3` at `62b58e8`](https://gitlab.mister-muffin.de/josch/img2pdf/commit/62b58e81cbb0acf1eb3b3e8883e337e8056e128a), LGPL-3.0. | Dataset-build tool only. Prefer user installation; bundling requires LGPL compliance and review of Pillow/pikepdf transitives. |
| CPython | Research candidate [`3.12.13` at `3bb231a`](https://github.com/python/cpython/tree/3bb231a6a5dc02b95658877318bf61501a7209e9), PSF plus bundled historical licenses. | Lock distributor, platform archive, SHA-256, and bundled licenses. `uv`-managed Python may be an Astral `python-build-standalone` archive rather than python.org. |
| uv | [`0.12.3` at `5072309`](https://github.com/astral-sh/uv/tree/507230998c9541d67814b57463ac00e454ff6991), MIT OR Apache-2.0. | Lock binary digest and selected license expression. `uv.lock` does not pin Python, SQLite, qpdf, models, Ollama, or OCI images. |
| SQLite | Public-domain core. | Record `sqlite3.sqlite_version` and the actual interpreter/OS distribution that supplied it. |
| Docker runtime/Compose | Moby and Compose source are Apache-2.0; [Docker Desktop has separate subscription terms](https://docs.docker.com/subscription/desktop-license/). | Record the actual host runtime and obtain any required Docker Desktop organizational approval; it is not covered by the container images' licenses. |

### Direct Python and development dependency snapshot

There is no `pyproject.toml` or `uv.lock`; these exact current revisions classify every direct package named by the draft, not the unresolved transitive graph. MIT/BSD packages require notice retention on conveyance; Apache packages additionally require Apache/`NOTICE` handling described above.

| License | Exact research snapshots |
|---|---|
| MIT | [Pydantic 2.13.4](https://github.com/pydantic/pydantic/blob/cf67d4b3193c3fe43ede18612ed62785eee11382/LICENSE), [pydantic-settings 2.15.0](https://github.com/pydantic/pydantic-settings/blob/f725ca187bee4212e9ef799eefa3cb25be788462/LICENSE), [SQLAlchemy 2.0.51](https://github.com/sqlalchemy/sqlalchemy/blob/c8e26d5c9ffcde0a82b4b7fa5de27f0c6bc46bec/LICENSE), [Alembic 1.19.0](https://github.com/sqlalchemy/alembic/blob/d2204e4860fc87096a8c8e43b5370a6978f4d470/LICENSE), [Typer 0.27.1](https://github.com/fastapi/typer/blob/fe2aa0e2f9c853de378e60ca24ec3b256144decf/LICENSE), [pytest 9.1.1](https://github.com/pytest-dev/pytest/blob/cf470ec0bf7eb89cd97dd56df4859eae5db46447/LICENSE), [pytest-cov 7.1.0](https://github.com/pytest-dev/pytest-cov/blob/66c8a526b1246b5eb8fb1bc218878131bc628622/LICENSE), and [Ruff 0.16.2](https://github.com/astral-sh/ruff/blob/5b48a040974781ba90b47c8df628f8fd9b6c95dd/LICENSE). |
| MIT OR Apache-2.0 | [structlog 26.1.0](https://github.com/hynek/structlog/blob/8174a86a2f14b5bd295eded733ff5fffc12aa173/pyproject.toml) with [`NOTICE`](https://github.com/hynek/structlog/blob/8174a86a2f14b5bd295eded733ff5fffc12aa173/NOTICE); uv as above. |
| Apache-2.0 | MinIO client and OpenSearch client above; [Streamlit 1.61.1](https://github.com/streamlit/streamlit/blob/cc5f10b7c5b2eb6174cb9fd36769b0b788de84a6/LICENSE); [pytest-asyncio 1.4.0](https://github.com/pytest-dev/pytest-asyncio/blob/6e14cd2af9292dca1fa2b027a06bbc40b0e0e425/LICENSE). |
| BSD-3-Clause | [HTTPX 0.28.1](https://github.com/encode/httpx/blob/26d48e0634e6ee9cdc0533996db289ce4b430177/LICENSE.md), [psutil 7.2.2](https://github.com/giampaolo/psutil/blob/9eea97dd6f1d16ea33f5144c8925f1ce7a0688e1/LICENSE), [Jinja2 3.1.6](https://github.com/pallets/jinja/blob/15206881c006c79667fe5154fe80c01c65410679/LICENSE.txt), [RESPX 0.23.1](https://github.com/lundberg/respx/blob/fc8b43bc74a69d07a6bdccf61522069b12bb8fad/LICENSE.md). |
| Conditional | pikepdf/MPL and img2pdf/LGPL as above. `pytest-asyncio` must not be added unless used. The license-report tool is unselected and cannot enter the lock until separately reviewed. |

Official Pyright [`1.1.411` at `9a9205f`](https://github.com/microsoft/pyright/tree/9a9205fc32a2685767f38f348f5d9232701d4b0b) is MIT. The PyPI package is an unaffiliated [Python wrapper at `392b6ba`](https://github.com/RobertCraigie/pyright-python/tree/392b6ba8e54be6d603e02e9f8d601d27b7a48d12) that can acquire Node and the npm package. Pin and inventory the wrapper, npm integrity, and Node distribution, or use an independently installed official tool.

Lock-time scanning must add transitives such as `pydantic-core`, Greenlet, Mako, Rich, Click, MarkupSafe, Pillow, NumPy, coverage, Streamlit's frontend bundles, and all native wheel contents. Source-repository licenses alone do not establish what a platform wheel conveys.

### Data, fixtures, and outputs

| Data | Verified terms | Distribution boundary |
|---|---|---|
| Project-authored synthetic fixtures | Governed by the repository license only if every font, icon, image, and template input is project-authored or separately cleared. | Default clean-clone tests, CI, demos, screenshots, and public reports. Record all generator inputs. |
| User/public PDFs and derivatives | Rights depend on each input; parser/model licenses do not grant rights in source PDFs. Normalized PDFs, page renders, extracted images/text, parser/VLM outputs, indexes, UI views, and reports may reproduce protected content. | Require lawful input and purpose; keep source/derived artifacts private by default; publish only after input/output review. |
| FUNSD | Authoritative commit [`8905aca`](https://github.com/guillaumejaume/FUNSD/commit/8905aca92b3181853307e2880e3d6f71dee8e9f3); archive SHA-256 `c31735649e4f441bcbb4fd0f379574f7520b42286e80b01d80b445649d54761f`. Its [terms](https://github.com/guillaumejaume/FUNSD/blob/8905aca92b3181853307e2880e3d6f71dee8e9f3/work.html) restrict use to people 18+ for non-commercial research/education, identify RVL-CDIP copyrights, and place clearance responsibility on users. The repository website-template license is not a dataset grant. | Optional manual acquisition after explicit acceptance. Never commit or redistribute scans, converted PDFs, crops, screenshots, or image-bearing reports. Review text/model outputs for reproduced source content. |
| Open real-form corpus | Not selected; issue #14 owns the research. | No corpus may enter the blueprint until its authoritative data license, source provenance, redistribution, attribution, and derivative-output terms pass this same gate. |

Attribution or citation does not cure missing redistribution permission. Conversion does not clear source rights. An SPDX identifier by itself is insufficient evidence for a dataset, model weights, transitive artifact, or container contents.

## Risk interpretation and required mitigation

1. **Docling is not yet a closed artifact set.** It is a defensible code choice, but Heron/TableFormer/RapidOCR weight evidence is metadata-only and current helpers over-download. Phase 0 must use a manifest-driven prefetch, record every response and digest, reject surprises, and rerun offline.
2. **Ollama lineage is incomplete.** The embedded and upstream Apache-2.0 texts show no license conflict, but they do not prove the GGUF came from the pinned upstream revision. Preserve the gap or self-convert.
3. **MinIO's AGPL boundary is acceptable only for the agreed architecture.** Use an unmodified, separately operated service pulled from upstream; do not vendor, derive, or mirror it. Its source-only/current-maintenance status is an operational risk separate from license compatibility.
4. **Top-level licenses do not clear packages or images.** The actual arm64 wheels and OCI platform manifests determine conveyed contents. Build notices/SBOMs from those artifacts, not this research table.
5. **Download-on-demand reduces conveyance; it does not waive use terms.** Acquisition must be explicit, from the authoritative origin, and forbidden in default setup/tests.
6. **No Marker/Surya escape hatch is pre-approved.** Marker [`v2.0.0` at `e1a6226`](https://github.com/datalab-to/marker/tree/e1a6226adfaab4cd573cfa96e12d60905ee38036) and Surya [`v0.22.1` at `f2c45da`](https://github.com/datalab-to/surya/tree/f2c45daaf67be28dfe09c602eb62a0df99a022a8) code is Apache-2.0, but their exact [`MODEL_LICENSE`](https://github.com/datalab-to/surya/blob/f2c45daaf67be28dfe09c602eb62a0df99a022a8/MODEL_LICENSE) and [`surya-ocr-2@3b3d4cd`](https://huggingface.co/datalab-to/surya-ocr-2/tree/3b3d4cdf88d6928b0acdc75181b13206ea67c4a3) impose commercial, competitive-use, attribution, output-share-alike, and downstream restrictions. A Docling failure must stop at a fresh license decision before download or output publication.

No new approval question is required to close this research ticket. The VLM provenance choice belongs in #18; the public-corpus/FUNSD choice belongs in #15 after #14. The blueprint should state the repository's current MIT license rather than inventing a license change.

## Enforceable gates

### Blueprint-time gate

Before the blueprint recommends a component:

1. State the intended distribution mode: source repository only, direct upstream pull, published wheel, derived OCI image, mirror, or offline bundle.
2. Keep the proposed graph explicit: Docling-only; named Heron/TableFormer/RapidOCR files; optional `ocrmac`; host Ollama with `qwen3.5:9b-q4_K_M`; no Marker/Surya or hosted inference.
3. Classify every direct code, model, data, binary, image, base image, and service license as allow, review, or deny. Unknown or metadata-only artifacts remain hard-gated, not silently “Apache expected.”
4. Require immutable source revisions and artifact digests; forbid floating Git branches/tags, OCI tags without digests, Hugging Face `main`, Ollama `latest`, and size-only aliases.
5. Require direct, explicit, terms-aware acquisition. Default clean-clone/CI uses only cleared synthetic fixtures and no heavyweight or restricted downloads.
6. Forbid repository/release bundling of model/OCR weights, FUNSD material, MinIO/OpenSearch images, Ollama binaries/layers, and unreviewed third-party binaries.
7. State current repository license accurately and require a separate maintainer decision for any change.

### Lock-time gate

When Phase 0 creates locks, fail unless it:

1. Freezes all direct/transitive packages and platform wheel hashes; produces SPDX or CycloneDX SBOMs for Python/native wheels, host tools, and each OCI platform image.
2. Records source URL/revision, package/artifact URL, size, SHA-256, license expression, exact license-text hash, copyright, `NOTICE`, evidence class, and approval for every component.
3. Locks interpreter distributor/archive/hash and bundled licenses; `uv`, qpdf/package dependencies, SQLite runtime, Docker/Compose, Ollama release asset, and macOS build.
4. Locks each model repository commit and every downloaded file. The prefetch manifest must include Heron, both actually fetched TableFormer files, and the three exact RapidOCR files—or prove the unused collateral was not fetched.
5. Locks the complete Ollama manifest/config/layer set, embedded license, upstream revision, conversion recipe if available, and explicit provenance-gap status.
6. Locks OCI index plus arm64 manifest/config/layers; inventories base OS, JDK, plugins, RPMs, embedded tools, native libraries, source/notice material, and registry origin.
7. Records FUNSD terms revision/hash, archive/file hashes, acceptance, and non-redistribution policy outside Git; applies equivalent records to the corpus selected by #15.
8. Generates `THIRD_PARTY_NOTICES.md` from the resolved artifacts and records reviewed exceptions for CDLA models, MinIO, pikepdf, img2pdf, Docker Desktop, proprietary Apple APIs, and restricted data.
9. Prefetches once under observation, rejects any unlisted network request/artifact, then proves the measured parser/VLM run succeeds with external network denied.

### CI/release licensing gate

On every dependency, model, data, image, or lock change:

1. Run `uv sync --frozen`; fail on lock drift or unhashed/floating package sources.
2. Run a separately selected and pinned SBOM/license-policy tool over Python, native, model, and OCI inventories; fail on unexpected artifacts, `NOASSERTION`, missing evidence/notices, or baseline drift. Require maintainer review for new components, licenses, extras, model IDs, dataset origins, image layers, or digests.
3. Verify every resolved component maps to retained license/notice text or a documented exception. Rebuild notices from the artifacts that would actually be released.
4. Reject forbidden content: FUNSD scans/derivatives, model-weight formats, OCI archives, third-party binaries, Marker/Surya packages/models/outputs, and active Qwen2.5 configuration.
5. Run ordinary CI offline on synthetic fixtures. Put restricted data and heavyweight model checks in manually authorized jobs with terms acceptance and no artifact publication.
6. Verify model and OCI digests before use; fail before inference/service startup on mismatch. Never silently update a tag.
7. Before publishing any wheel, binary, container, mirror, or offline bundle, scan the final payload and verify source-delivery/source-offer, relinking, notice, attribution, and AGPL network obligations applicable to that distribution mode.

These gates preserve licensing evidence without claiming that an automated scanner or this engineering review supplies legal approval.
