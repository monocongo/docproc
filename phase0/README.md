# Phase 0 evidence workspace

**Status: not admitted; no Phase 0 artifact has been acquired or executed by this workspace.**

This directory contains only the minimal, non-durable admission harness authorized before Overall Phase 0 Go. It is not a PDF-processing application, a downloader default, a model runner, or a substitute for legal review. Its purpose is to produce the private machine record `EVID-LOCK-INVENTORY-001` after every exact byte has been reviewed and observed.

The control implements the Phase 0 boundary from the approved blueprint (`367454a103c55a5d5a363b5be26cc43033cc2623`), Gate LIC (`d5e0f3dfca08f6bc11ad02a6ee275aef0e43b2f9`), the artifact/licensing research (`a6a0ce8014391d7956801154a39b8061fa8940f8`), and the VLM contract (`cabf7490a7a66fd8b4cf6f00ea6207c78dd50f5c`).

## What is frozen now

- `lock/base-primary-policy.json` is an admission **catalog**, not an approval. It names only the base graph and the primary `qwen3.5:9b-q4_K_M` candidate. It does not name either fallback as an initial acquisition.
- Every catalog item is `pending-human-review`. The tool refuses to issue any network request while that is true. In particular, it preserves the metadata-only Heron/TableFormer/RapidOCR evidence and the Ollama conversion-lineage gap as exceptions requiring review; it does not call either verified provenance.
- The catalog also makes the unselected SBOM/license tool an explicit unresolved input. A scanner must be separately selected, version-pinned, acquired, and reviewed; this harness must not quietly install one.
- `lock/phase0_lock.py` rejects credential- or query-bearing URLs, redirects, unreviewed licenses, `NOASSERTION`, non-canonical JSON, graph entries not explicitly approved for acquisition, byte/size or encoding mismatches, and any evidence root inside the checkout that contains this harness. An approved exact-byte row also requires a `git:<commit>` or `sha256:<digest>` immutable origin reference and reviewed artifact-descriptor metadata.
- `schemas/phase0-lock-inventory-v1.json` fixes the complete nested payload shape. The tool produces content-addressed payload (`evp1`), artifact-descriptor (`art1`), and envelope (`evr1`) addresses using the domain-separated SHA-256 preimages defined in `lock/phase0_lock.py`, verifies the schema and descriptor bindings on read, and creates owner-only private evidence directories/files. It limits records to the integer/string JSON subset that it can canonicalize correctly without introducing an unadmitted dependency.
- `lock/network-deny-pf.sh` is deliberately disabled. An anchor in an arbitrary macOS PF ruleset cannot attest complete egress denial because earlier anchors, stateful inbound traffic, and escaped descendants can bypass it. The script performs no PF mutation and refuses every measured command; a separately reviewed isolated guest or container-network boundary is required before any parser/VLM rerun. It does not claim that Docker Desktop VM traffic is covered.
- Host-baseline capture hashes listed host tools but does not execute them merely to learn a version. Exact tool versions are an admission-policy input; only the fixed macOS platform probes are executed for the baseline.

## Human review required before acquisition

This checkout has no admitted Phase 0 environment. Host hardware, operating-system, installed-tool, and service observations are private-only baseline evidence; they are intentionally not recorded in this repository or this document.

A human reviewer must make and retain each of these decisions before changing an artifact to `approved-for-acquisition` in an exact-byte prefetch policy:

1. Select the Python 3.12 arm64 distributor/archive and the SBOM/license tool; record their final publisher URLs, byte lengths, SHA-256 values, exact license/notice text hashes, and distribution dispositions.
2. Approve or reject the actual arm64 wheel closure produced for the Docling/RapidOCR/ONNX path, including native contents and downloader collateral. The prefetch policy must expand each actual wheel, native library, Heron/TableFormer/RapidOCR file, and its license/notice evidence into a distinct byte record.
3. Review the metadata-only model evidence, CDLA TableFormer terms, MinIO AGPL/UBI boundary, Docker Desktop terms, and the Ollama metadata-only conversion lineage. A reviewed exception must state its scope and direct-pull/no-publish boundary.
4. Approve the actual host tool records (macOS build, Python, `uv`, qpdf, SQLite, Docker/Compose, Ollama release asset) and the complete arm64 OCI index/manifest/config/layer closures. MinIO and OpenSearch remain direct upstream pulls; no image layer may be mirrored, committed, or bundled.
5. Hand #21 the NAF source/terms review. NAF bytes, converted PDFs, ledgers, and image-bearing output remain outside Git and private.
6. Record the authorization/T0 source and select a private evidence root outside this checkout. The root must not be synced, published, or committed.

The catalog deliberately cannot be edited into a runnable prefetch file by changing just a status: an approved byte record requires an exact query-free HTTPS URL, expected SHA-256, expected byte length, authoritative immutable origin reference, reviewed license evidence class, reviewed descriptor metadata (media type and content encoding, plus charset/format schema when applicable), distribution mode, and publication disposition. Every record for a required catalog component must itself be required and approved. Components with several downloaded bytes must expand to several records. This makes an incomplete resolution fail before the first network request.

## Controlled workflow

All commands below are deliberately manual. They must be run only after the review above and must retain their stdout/stderr as an acquisition or preflight observation. `PRIVATE_ROOT` must be a private directory outside the repository.

```sh
PRIVATE_ROOT="$HOME/.local/share/docproc-phase0"
python3 phase0/lock/phase0_lock.py validate-policy \
  --policy phase0/lock/base-primary-policy.json
python3 phase0/lock/phase0_lock.py capture-host-baseline \
  --root "$PRIVATE_ROOT"
```

Create a reviewed **exact-byte** policy outside Git with `policy_version` `phase0-exact-byte-v1`. It uses the same shape as `base-primary-policy.json`, adds a `component_id` naming one catalog row, and gives every required entry `approved-for-acquisition`, an exact publisher URL, and matching digest/length. It must include the complete wheel/native/model/OCI/layer closure—not merely this catalog's component rows. Then:

```sh
python3 phase0/lock/phase0_lock.py validate-closure \
  --catalog phase0/lock/base-primary-policy.json \
  --policy "$PRIVATE_ROOT/reviewed-exact-byte-policy.json"
python3 phase0/lock/phase0_lock.py prefetch \
  --catalog phase0/lock/base-primary-policy.json \
  --policy "$PRIVATE_ROOT/reviewed-exact-byte-policy.json" \
  --root "$PRIVATE_ROOT"
```

`network-deny-pf.sh` currently refuses every command rather than make an unverifiable no-egress claim. Do not run a parser/VLM harness until a separately reviewed isolated guest or container-network boundary is available. That future measured rerun must include a denial probe that fails if an external connection succeeds, for example:

```sh
if curl --connect-timeout 2 --max-time 3 https://example.com; then
  echo "unexpected egress" >&2
  exit 1
fi
```

Only after the selected SBOM/license tool has scanned the resolved closure, notices have been generated, every required observation is present, and the final policy/source commit are fixed, seal the private evidence record:

```sh
python3 phase0/lock/phase0_lock.py seal \
  --catalog phase0/lock/base-primary-policy.json \
  --policy "$PRIVATE_ROOT/reviewed-exact-byte-policy.json" \
  --root "$PRIVATE_ROOT" \
  --schema schemas/phase0-lock-inventory-v1.json \
  --source-commit "$(git rev-parse HEAD)"
python3 phase0/lock/phase0_lock.py verify \
  --root "$PRIVATE_ROOT" \
  --catalog phase0/lock/base-primary-policy.json \
  --policy "$PRIVATE_ROOT/reviewed-exact-byte-policy.json" \
  --schema schemas/phase0-lock-inventory-v1.json \
  --evidence-address 'evr1:sha256:...'
```

`seal` creates the private `EVID-LOCK-INVENTORY-001` envelope and a human summary but intentionally returns `go-candidate-pending-human-approval`, not a Gate LIC Go. Final LIC reconciliation must additionally cover scanner results, notices, SBOMs, all actual OCI/model closures, approved exceptions, and an observed parser/VLM rerun with egress denied. That final outcome belongs in #25.

## Prohibited behavior

Do not run `uv sync`, `pip install`, `ollama pull`, `docker pull`, a generic Docling downloader, or a model/corpus downloader against this catalog. Do not add Marker, Surya, FUNSD, hosted inference, a fallback candidate, a mirror, or a floating tag/revision. Do not publish or commit downloaded payloads, OCI archives, model/OCR weights, NAF material, third-party binaries, local paths, secrets, or content-bearing derived output.
