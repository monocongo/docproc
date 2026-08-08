# Open real-form evaluation corpus research

- **Resolves:** [Identify an openly reusable real-form evaluation corpus](https://github.com/monocongo/docproc/issues/14)
- **Researched:** 2026-08-08
- **Scope:** A revision-pinned public benchmark candidate for generic linked field extraction; research only, not an acquisition or evaluation implementation
- **Legal status:** Engineering research, not legal advice

## Outcome

The **National Archives Forms (NAF) Dataset** is the qualified engineering candidate under a clearly open publisher grant. Its publisher supplies the form images and annotations under CDLA-Permissive-1.0, which expressly covers gathered images and text and grants worldwide rights to use and publish the data. Its annotations contain polygons, transcriptions, typed label and response regions, and explicit relationship edges. Those facts support a field-name-agnostic `label → value` benchmark without deriving links from a fixed business ontology. Qualification relies on the publisher's rights representation; it is not independent image-by-image chain-of-title verification.

Use the proposed **`NAF-linked-v3` evidence profile** below if issue [#15](https://github.com/monocongo/docproc/issues/15) selects NAF as the primary public benchmark. Keep FUNSD restricted and optional unless #15 omits it entirely. This research identifies a qualified corpus; it does not make #15's final corpus-role decision, implement acquisition/conversion/evaluation, or broaden Phase 0 beyond single-page scanned forms.

CORD v2 is openly licensed but lacks authoritative generic label/value edges. XFUND has the closest modern annotation shape but is non-commercial/share-alike. DocILE and FUNSD impose non-commercial and distribution restrictions. VRDU and Kleister publish useful data without a dataset license at the inspected revisions. None displaces NAF for this specific public benchmark.

## Why NAF qualifies

### The data license covers the published images and annotations

The exact NAF [`LICENSE` at `92df0e0`](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/LICENSE) is CDLA-Permissive-1.0. It:

- defines Data to include copyrightable images or text whether created or gathered by the provider;
- grants worldwide rights to Use and Publish Data;
- imposes no CDLA obligations or restrictions on use or publication of output that meets the agreement's Results definition—output containing no more than a de minimis portion of Data—without clearing unrelated rights;
- conditions publication of Data on giving every recipient the agreement text, name, or a reasonably available copy/link and preserving all existing provider credit or attribution, including legal notices/metadata, provider identification, and practical source hyperlinks;
- requires prominent change notices on files containing Enhanced Data; and
- represents that the provider exercised reasonable care to obtain gathered Data with the right to publish it under the agreement.

Those points come directly from [definitions §§1.3 and 1.10](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/LICENSE#L13-L27), [the Use/Publish grant](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/LICENSE#L35-L41), [publication conditions and Results treatment](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/LICENSE#L43-L57), and [the provider representation](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/LICENSE#L59-L61). The same license blob is present at the image release's exact [`v1.0` commit `a468796`](https://github.com/herobd/NAF_dataset/blob/a468796d08db20d23382821abc16f29437100c03/LICENSE).

The publisher says the dataset was created from images supplied by the United States National Archives and FamilySearch and expressly releases the labeled images with the project. That is [dataset-specific provenance and publication evidence](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/README.md#L12-L20), not an inference that every government-hosted record is public domain. NARA itself warns that [not all records in its holdings are public domain](https://www.archives.gov/research/still-pictures/permissions). The engineering disposition therefore rests on NAF's artifact-level CDLA grant and reasonable-care representation. A provider can grant only rights it holds; this research did not independently trace rights for every image, and downstream users retain the agreement's applicable-law responsibility. Mirroring, commercial distribution, or image-bearing publication should retain that residual risk for review rather than present chain of title as proven.

### The annotations directly represent generic linked fields

The publisher states that NAF captures relationships between text and handwriting entities and groups images by estimated form type. Its schema supplies:

- polygonal `textBBs` and `fieldBBs` with stable IDs;
- a `text` type for a pre-printed label and a `field` type for a written, typed, or stamped response;
- `pairs` of related text and field IDs;
- transcriptions for annotated regions; and
- explicit blank, signature, checkbox, prose, table, and uncertainty signals that can be excluded rather than silently scored.

Sources: [purpose and grouping](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/README.md#L47-L59), [annotation fields](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/README.md#L64-L84), [type semantics](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/README.md#L88-L102), and [transcription markers](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/README.md#L104-L108).

A concrete exact-revision annotation links `t11` (`text`: `ENLISTMENT DATE`) to `f5` (`field`: `26 May 1944`) and gives both polygons. See [`groups/1/007182398_00026.json`](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/groups/1/007182398_00026.json). The document's own printed label—not a dataset ontology name—therefore becomes the generic key, while the linked response becomes the value and both source polygons remain evidence.

## Proposed `NAF-linked-v3` evidence profile

This is a project profile over two publisher artifacts, not a new NAF release:

| Component | Pinned selection and observed integrity |
|---|---|
| Annotation, schema, and license snapshot | [`92df0e0b314e8cff98b4b7805b7323b980f7d6ae`](https://github.com/herobd/NAF_dataset/commit/92df0e0b314e8cff98b4b7805b7323b980f7d6ae), tree `97ee13e821a7d92b601672c744d61c6875ab8255` |
| Image-release commit | [`v1.0` commit `a468796d08db20d23382821abc16f29437100c03`](https://github.com/herobd/NAF_dataset/tree/a468796d08db20d23382821abc16f29437100c03) |
| Image asset | [`labeled_images.tar.gz`, release asset ID `14770049`](https://api.github.com/repos/herobd/NAF_dataset/releases/assets/14770049), stable browser URL `https://github.com/herobd/NAF_dataset/releases/download/v1.0/labeled_images.tar.gz`, 790,561,702 bytes, observed SHA-256 `2024233c25669e76d2398544dd154709831e612a1f49713f64f6984d09132c8d` |
| Image manifest | 865 unique JPEGs and 798,843,699 uncompressed bytes. SHA-256 `7d470960df217d52ad5b2da3f5e2605c0c77469acf169b5d2ea496c7bcb388af` for the LF-terminated, filename-sorted manifest lines `<file-sha256>  <basename>` |
| Dataset license | SHA-256 `52aa39b7c72a3712b1e1ab0b2d6b9d790f443f985407672b9df8edab9eb64712`; byte-identical at the two commits above |
| Canonical split declaration | [`train_valid_test_split.json`](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/train_valid_test_split.json), SHA-256 `506e00d2f25532f67bf37d6acc02463ee408abce37b4127f79b757f72a1ee3b2` |

The publisher's [setup instructions identify the `v1.0` image asset](https://github.com/herobd/NAF_dataset/blob/92df0e0b314e8cff98b4b7805b7323b980f7d6ae/README.md#L31-L43). Observed on 2026-08-08, GitHub's [release metadata](https://api.github.com/repos/herobd/NAF_dataset/releases/19789282) recorded the asset ID and size but no publisher digest, and marked the release non-immutable. The Git commit pins repository content; only the observed size, archive hash, and aggregate per-image manifest hash content-address the separately attached archive. They are fail-closed research evidence, not a claim that GitHub attests the bytes. If the upstream bytes change or disappear, stop and review; do not substitute a mirror silently.

Direct inspection of the pinned annotations and archive found one matching non-template JSON per image. Applying the publisher's split declaration to those 865 released images yields 710 training, 78 validation, and 77 test pages. The README's older distribution counts are explicitly version-specific and cautioned as stale; the profile must use observed pinned-artifact counts rather than copy the graphic.

These are derived research observations, not publisher-attested counts. The exact test inspection classified all 2,598 declared `pairs` edges as 683 eligible, 1,569 other-type, 239 missing-transcription, 55 marked-transcription, 44 blank-or-signature, and 8 empty-transcription rows. Sorting LF-terminated compact JSON rows by `(file, edge, reason)` produced eligibility-ledger SHA-256 `3cd50f369d4331daf981824f8718b5d6f27d0079309d1ba8a640c1c289949222`. The later evaluator must reproduce that digest before using the profile; the ledger itself remains local because its transcriptions and IDs derive from the dataset.

<details>
<summary>Inspection reproducer (research audit, not pipeline implementation)</summary>

```python
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import tarfile

root = Path("NAF_dataset")  # exact 92df0e0 commit
archive = Path("labeled_images.tar.gz")
splits = json.loads((root / "train_valid_test_split.json").read_text())
which = {
    filename: split
    for split, groups in splits.items()
    for filenames in groups.values()
    for filename in filenames
}

archive_hash = sha256()
with archive.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        archive_hash.update(chunk)
assert archive.stat().st_size == 790_561_702
assert archive_hash.hexdigest() == "2024233c25669e76d2398544dd154709831e612a1f49713f64f6984d09132c8d"
assert sha256((root / "LICENSE").read_bytes()).hexdigest() == "52aa39b7c72a3712b1e1ab0b2d6b9d790f443f985407672b9df8edab9eb64712"
assert sha256((root / "train_valid_test_split.json").read_bytes()).hexdigest() == "506e00d2f25532f67bf37d6acc02463ee408abce37b4127f79b757f72a1ee3b2"

with tarfile.open(archive, "r:gz") as tar:
    image_rows = []
    for member in tar.getmembers():
        if member.isfile() and member.name.lower().endswith(".jpg"):
            data = tar.extractfile(member).read()
            image_rows.append((Path(member.name).name, len(data), sha256(data).hexdigest()))
images = {name for name, _, _ in image_rows}
manifest = "".join(
    f"{digest}  {name}\n" for name, _, digest in sorted(image_rows)
)
assert len(images) == 865
assert sha256(manifest.encode()).hexdigest() == "7d470960df217d52ad5b2da3f5e2605c0c77469acf169b5d2ea496c7bcb388af"

annotations = {}
for path in (root / "groups").glob("*/*.json"):
    if not path.name.startswith("template"):
        data = json.loads(path.read_text())
        annotations[data["imageFilename"]] = data
assert images == set(annotations)
assert Counter(which[name] for name in images) == Counter(train=710, valid=78, test=77)

counts = Counter()
eligible_pages = set()
ledger = []
for filename in sorted(name for name in images if which[name] == "test"):
    data = annotations[filename]
    objects = {obj["id"]: obj for obj in data["textBBs"] + data["fieldBBs"]}
    text = data.get("transcriptions", {})
    seen = set()
    for edge in data.get("pairs", []):
        canonical = list(edge)
        if len(edge) != 2 or any(endpoint not in objects for endpoint in edge):
            reason = "bad_endpoint"
        else:
            label, value = edge
            label_obj, value_obj = objects[label], objects[value]
            if label_obj.get("type") == "field" and value_obj.get("type") == "text":
                label, value = value, label
                label_obj, value_obj = value_obj, label_obj
            canonical = [label, value]
            if (label, value) in seen:
                reason = "duplicate"
            elif label_obj.get("type") != "text" or value_obj.get("type") != "field":
                reason = "other_type"
            elif label not in text or value not in text:
                reason = "missing_transcription"
            elif not text[label].strip() or not text[value].strip():
                reason = "empty_transcription"
            elif value_obj.get("isBlank") not in {0, 1, 2}:
                reason = "blank_or_signature"
            elif any(mark in text[label] or mark in text[value] for mark in "¿§«»"):
                reason = "marked_transcription"
            else:
                reason = "eligible"
                eligible_pages.add(filename)
            seen.add((label, value))
        counts[reason] += 1
        ledger.append({"edge": canonical, "file": filename, "reason": reason})

ledger_text = "".join(
    json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
    for row in sorted(ledger, key=lambda row: (row["file"], row["edge"], row["reason"]))
)
assert counts == Counter(
    eligible=683,
    other_type=1569,
    missing_transcription=239,
    marked_transcription=55,
    blank_or_signature=44,
    empty_transcription=8,
)
assert len(eligible_pages) == 56
assert sha256(ledger_text.encode()).hexdigest() == "3cd50f369d4331daf981824f8718b5d6f27d0079309d1ba8a640c1c289949222"
```

</details>

### Strict primary ground truth

Evaluate all 77 canonical test pages. An eligible linked pair must satisfy all of these rules:

1. Canonicalize a two-ID `pairs` edge to label then value; reject missing endpoints.
2. Require the label object type to be exactly `text` and the value object type to be exactly `field`.
3. Require present, non-empty transcriptions for both endpoints.
4. Require the field's `isBlank` value to be `0`, `1`, or `2`; exclude blank (`3`) and signature (`4`) fields.
5. Exclude either endpoint containing the publisher's uncertain, illegible, or struck-through markers `¿`, `§`, `«`, or `»`.
6. Deduplicate by image filename and endpoint IDs; retain both polygons and original transcriptions in the evaluation record.
7. Retain every excluded edge/region in an ignore ledger with its reason. A prediction corresponding to ignored ground truth must not be silently counted as either a true positive or false positive; #15 or the later evaluator specification must define deterministic overlap/matching semantics.

That deterministic rule produced **683 eligible label/value pairs on 56 of the 77 test pages**. All 77 pages stay in evaluation, including pages with no eligible pair, so false positives away from ignored regions remain measurable. Checkboxes, signatures, prose/fill-in regions, table rows/columns, `samePairs`, and uncertain transcriptions may become separately named diagnostic slices later; they are not silently folded into primary linked-field accuracy.

## What the benchmark can and cannot establish

- **Schema-valid** means the output conforms to the fixed generic linked-field schema. It says nothing about whether a pair is correct.
- **Evidence-grounded** means each predicted label and value cites traceable page evidence. NAF's source polygons make this independently testable, but overlap alone does not prove correctness.
- **Evaluated accuracy** compares canonicalized predicted pairs with eligible NAF edges under a separately specified matching rule. Neither valid JSON nor present evidence substitutes for measured pair accuracy.

NAF tests historical, noisy, single-page scanned forms with print, handwriting, and stamps. Wrapping each JPEG as an image-only one-page PDF exercises PDF intake and scanned-page parsing, but not native PDF text, multi-page ordering, broad reports, modern invoices, or rich table extraction. Its form groups are an author-estimated template boundary, not a guarantee against every visual near-duplicate. Public release since 2019 also means foundation-model pretraining contamination cannot be ruled out. Claims must stay limited to the pinned NAF profile.

The exact README says validation/test printed transcriptions were hand-corrected while training printed text remains noisy and partial. Use training pages only for smoke work, validation for design decisions, and preserve the canonical test set for final reporting. Annotation noise remains a measured-data limitation rather than a parser or VLM failure by definition.

## Candidate disposition

| Candidate | Revision-specific evidence | Disposition |
|---|---|---|
| **NAF** | Publisher commit and CDLA license above; exact image asset; polygons, transcriptions, typed regions, and explicit `pairs`. | **Qualified engineering candidate under the publisher grant.** Best direct fit for generic linked fields within form scope, with the residual source-rights caveat above. |
| **CORD v2** | The publisher's exact README applies [CC BY 4.0](https://github.com/clovaai/cord/blob/327310ce58c1623255821d062b3a759ff3789e3c/README.md#L1-L10) and documents [receipt categories, grouping, rows, and `is_key`](https://github.com/clovaai/cord/blob/327310ce58c1623255821d062b3a759ff3789e3c/README.md#L33-L121); the official Hugging Face dataset is ungated at [`7f0115a`](https://huggingface.co/datasets/naver-clova-ix/cord-v2/tree/7f0115a4b758a71d6473b8d085751692da2fef98). | Open and reproducible, but not primary-task fit. Its authoritative schema has no generic printed-label/value relationship edge; deriving keys from the fixed receipt ontology would test a different task and expand scope. |
| **XFUND v1.0** | Exact [`926b5c5` README](https://github.com/doc-analysis/XFUND/blob/926b5c5e2531f63a5f7438d058871ade26a96255/README.md#L1-L9) describes human-labeled multilingual forms with key/value pairs; its [license is CC BY-NC-SA 4.0](https://github.com/doc-analysis/XFUND/blob/926b5c5e2531f63a5f7438d058871ade26a96255/README.md#L96-L100). | Excellent technical fit, but the non-commercial restriction fails the intended unrestricted public-portfolio gate; share-alike adds redistribution duties but is not by itself the rejection reason. |
| **DocILE** | Exact [`9b7b925` code README](https://github.com/rossumai/docile/blob/9b7b92564f2920258033e482e6f57a82dfe3ee04/README.md#L28-L42) requires a secret token. The publisher's mutable [access terms](https://docs.google.com/forms/d/e/1FAIpQLSeYaPkF_BOeD2GwBGueVbprESD7Mys-hMAiUj8oVKBmBGnJUw/viewform), observed 2026-08-08 as 119,202-byte HTML with SHA-256 `45af852ca16754b3a74309a5d6c0221a0bdcbec8adcb7756774495248afb9a02`, limit data to non-commercial research, prohibit third-party access/distribution, and require deletion when permission ends. Its repository MIT file covers the tooling tree, not those separately gated dataset bytes. | Fails the engineering reuse gate for this public benchmark; its fixed invoice field types also do not supply generic document-label/value links. |
| **VRDU Registration/Ad-buy** | The exact [`04a4df7` publisher tree](https://github.com/google-research-datasets/vrdu/tree/04a4df7ac5cc694e51c48115c03fe428f0e240cc) includes source PDFs, OCR, human boxes, fixed entity values, and template splits, but no license or terms file was found in that inspected tree. Public DOJ/FCC origins are provenance, not a redistribution grant over source documents plus annotations. | Reject pending an artifact-level dataset license. Fixed entity names and value boxes are useful structured extraction evidence but not explicit printed-label/value links. |
| **Kleister Charity/NDA** | No dataset license was found in the exact publisher trees [`2309f48`](https://github.com/applicaai/kleister-charity/tree/2309f4861cc49864ac653a7fa108efc2144400b3) and [`c2c7bf0`](https://github.com/applicaai/kleister-nda/tree/c2c7bf069b919bfb618b268fda2a2c079c0db316). Charity uses external git-annex PDF storage; both tasks provide normalized expected values rather than authoritative source-region/link ground truth. | Reject for unresolved data/annotation redistribution rights and task fit. Long reports and contracts would also broaden the initial form-focused scope. |
| **FUNSD** | Existing commit-pinned [corpus research](https://github.com/monocongo/docproc/blob/093a663bdd6fa419ac2931c88ad1b9e5cda0da78/docs/research/funsd-corpus-assumptions.md) and the [official pinned terms](https://github.com/guillaumejaume/FUNSD/blob/8905aca92b3181853307e2880e3d6f71dee8e9f3/work.html) verify direct question/answer links but restrictive non-commercial terms and copyrighted source scans. | Keep only as an optional restricted comparison if #15 retains it; never the clean-clone or primary public path. |

A repository or tooling SPDX label does not clear separately distributed dataset bytes. Public source hosting and citation requests likewise do not establish redistribution rights. CORD is the only rejected candidate above with a sufficiently clear open data grant; it is rejected on task/scope fit, not license.

## Acquisition, redistribution, and reporting boundary

If #15 selects the NAF profile, the blueprint should require:

1. **Clean clone:** keep only project-authored synthetic fixtures in Git and default CI. Do not download NAF or FUNSD during setup, tests, demos, screenshots, or ordinary CI.
2. **Explicit acquisition:** fetch NAF outside Git from the pinned Git revisions and observed publisher asset URL, retain the exact CDLA text and citation, and verify commit, asset ID, observation record, archive size/hash, license hash, split hash, image count, aggregate file-manifest hash, and eligibility-ledger hash before use.
3. **No silent replacement:** fail if any upstream identifier, byte count, hash, manifest, license, or terms evidence differs. A mirror can be considered only through a separate distribution review despite NAF's permission to publish.
4. **Local conversion:** use a separately pinned lossless JPEG-to-one-page-PDF recipe. Treat published converted PDFs conservatively as Enhanced Data: preserve the CDLA agreement/provider attribution and mark the conversion. Do not publish them by default.
5. **Default public outputs:** publish aggregate metrics, exclusion counts, configuration/provenance records, and synthetic screenshots. Image/text excerpts remain Data; when model or report output meets CDLA's de-minimis Results definition, it is not subject to CDLA's data-sharing conditions, but unrelated rights and review still apply.
6. **Evaluation discipline:** use the complete split membership, strict eligibility rule, and an exclusion ledger. Keep schema validity, evidence grounding, and pair accuracy as separate reported measures; do not generalize NAF results to native or multi-page PDFs.
7. **Offline measured runs:** after explicit acquisition, run the measured parser/VLM path with external network denied. Dataset availability must not become a hosted runtime dependency.

These boundaries are intentionally stricter than NAF's redistribution permission. They keep the portfolio reproducible and auditable without bloating a clean clone or creating a casual dataset mirror.

## Handoff to the corpus-role decision

No further corpus search is required before issue #15. It should decide whether to adopt `NAF-linked-v3` as the primary public real-form benchmark and either retain FUNSD as an explicitly accepted, non-redistributed restricted comparison or omit FUNSD. That decision should preserve synthetic clean-clone acceptance and leave acquisition/conversion/evaluator implementation to the later implementation phase.
