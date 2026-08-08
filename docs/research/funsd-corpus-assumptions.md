# FUNSD corpus and extraction-task research

- **Resolves:** [Validate the corpus and extraction-task assumptions](https://github.com/monocongo/docproc/issues/5)
- **Researched:** 2026-08-08
- **Scope:** Technical suitability, reproducibility, and license constraints for the proposed public `docproc` portfolio project
- **Legal status:** Engineering research, not legal advice

## Conclusion

FUNSD is technically suitable for a bounded benchmark of generic linked question/answer field extraction, but it is **not an openly licensed CC BY 4.0 corpus**. Its authoritative terms restrict use to non-commercial research and education, impose an age condition, identify the scans as copyrighted images originating in RVL-CDIP, and place responsibility for additional image clearances on the user. The current blueprint must remove the CC BY claim.

Retain FUNSD only as a download-on-demand, non-redistributed, optional benchmark behind explicit acceptance of its authoritative terms. Do not make it the only clean-clone acceptance path or commit scans, converted PDFs, page crops, or image-bearing benchmark artifacts. A deterministic synthetic corpus should remain the committed baseline, and the project should investigate an openly reusable real-form corpus before confirming FUNSD as the primary public benchmark.

## Authoritative findings

### Dataset contents support linked field extraction

The official project describes FUNSD as 199 fully annotated forms with 31,485 words, 9,707 semantic entities, and 5,304 relations. Its paper describes 199 real scanned forms intended for text detection, OCR, spatial layout analysis, entity labeling, and entity linking.

The official annotation example contains entity text, boxes, labels (`question`, `answer`, `header`, `other`), word boxes, entity IDs, and linking edges. That is sufficient to derive deterministic question/answer pair ground truth without inventing fixed field names.

Inspection of the authoritative archive found:

| Split | Images | Annotation files | Entities | Unique links | Question/answer links |
|---|---:|---:|---:|---:|---:|
| Training | 149 | 149 | 7,411 | 4,230 | 3,129 |
| Test | 50 | 50 | 2,332 | 1,064 | 837 |

All inspected link endpoints referenced entities in the same annotation file. The conversion must canonicalize edge direction, deduplicate edges repeated on both entities, and admit only edges whose endpoint labels are exactly `question` and `answer`. Unlinked or empty questions cannot automatically become blank-field ground truth.

Sources:

- [Official FUNSD overview at the repository revision](https://github.com/guillaumejaume/FUNSD/blob/8905aca92b3181853307e2880e3d6f71dee8e9f3/index.html)
- [Official annotation-format example](https://github.com/guillaumejaume/FUNSD/blob/8905aca92b3181853307e2880e3d6f71dee8e9f3/description.html)
- [FUNSD paper and abstract](https://arxiv.org/abs/1905.13538)
- [Authoritative dataset archive at the repository revision](https://raw.githubusercontent.com/guillaumejaume/FUNSD/8905aca92b3181853307e2880e3d6f71dee8e9f3/dataset.zip)

### Acquisition can be pinned, but availability is not guaranteed

The authoritative GitHub repository has not changed since commit `8905aca92b3181853307e2880e3d6f71dee8e9f3` dated 2019-07-05. At research time its `dataset.zip` was 16,838,830 bytes with:

```text
SHA-256 c31735649e4f441bcbb4fd0f379574f7520b42286e80b01d80b445649d54761f
Git blob  514c5d3766eefb21c74607f9424fee66901dae11
```

A reproducible acquisition command can therefore pin both the repository revision and archive digest. It must fail closed on a mismatch. The official terms nevertheless say the dataset or its terms may change or become unavailable without notice, so the project cannot promise perpetual reproducibility from a clean clone.

A Hugging Face mirror is not an authoritative substitute: its dataset card has blank license, citation, and homepage fields, and its exposed schema contains BIO entity tags but does not expose the official relation links required by this extraction benchmark.

Sources:

- [Authoritative repository revision](https://github.com/guillaumejaume/FUNSD/commit/8905aca92b3181853307e2880e3d6f71dee8e9f3)
- [Official download page](https://github.com/guillaumejaume/FUNSD/blob/8905aca92b3181853307e2880e3d6f71dee8e9f3/download.html)
- [Non-authoritative Hugging Face mirror metadata](https://huggingface.co/datasets/nielsr/funsd/blob/main/README.md)

### The license is restrictive and is not CC BY 4.0

The authoritative FUNSD terms state that:

- access is unavailable to anyone under 18;
- the dataset is for non-commercial research and educational purposes only;
- the images are copyrighted and originate in RVL-CDIP;
- the user is responsible for determining whether additional licenses, clearances, consents, or releases are required;
- use is at the user's risk; and
- EPFL-LTS5 may change the dataset or terms, discontinue availability, or prevent it from becoming generally available.

The repository's `LICENSE.md` applies to the website template, not the dataset. Neither that file nor the authoritative dataset terms grants CC BY 4.0 rights. The plan's current statement that FUNSD is “commonly described as CC BY 4.0” is unsupported by the authoritative source and should be deleted rather than softened.

Source: [Official FUNSD license and terms of use](https://github.com/guillaumejaume/FUNSD/blob/8905aca92b3181853307e2880e3d6f71dee8e9f3/work.html).

## Benchmark limitations the blueprint must state

1. FUNSD consists of single scanned page images, not native PDFs. Wrapping each image in a one-page PDF tests intake and image-only parsing, but not embedded text, native PDF structure, multi-page ordering, or PDF table extraction.
2. It evaluates forms and linked semantic entities, not arbitrary reports, invoices, filings, or rich tables.
3. The 50 official test forms are useful as a fixed held-out evaluation set, but too narrow to support broad document-understanding claims.
4. Converted PDFs remain image-bearing derivatives; conversion does not remove the source-image restrictions.
5. Exact question/answer-pair scoring measures extraction accuracy. Schema validity and evidence alignment remain separate metrics.

## Required blueprint changes

1. Mark FUNSD as a **provisional, restricted, download-on-demand benchmark**, not an openly licensed primary corpus.
2. Remove every CC BY 4.0 assertion and cite the authoritative terms instead.
3. Require explicit acceptance of the FUNSD terms before acquisition; do not silently download it during general setup or tests.
4. Pin the upstream commit, archive SHA-256, expected file manifest, and deterministic image-to-PDF conversion tool/version.
5. Never commit or redistribute source images, converted PDFs, page crops, image-bearing reports, or model artifacts that reproduce substantial source content.
6. Use committed synthetic forms for default tests, screenshots, demos, and clean-clone acceptance.
7. Keep the official 50-document test split untouched. Use fixed training documents for spikes and smoke checks.
8. Define ground-truth conversion exactly: canonicalize and deduplicate links; accept only question/answer edges; preserve original entity IDs, boxes, and text; record exclusions.
9. State that availability and mutable terms are reproducibility risks despite the pinned digest.
10. Add a decision gate for selecting either an openly reusable real-form corpus or restricted FUNSD use before publishing the benchmark.

## Proposed Phase 0 gate

**Go with FUNSD** only if all are true:

- the maintainer explicitly accepts the authoritative non-commercial research/education terms;
- the planned repository and benchmark use fit those terms after license review;
- acquisition from the pinned revision matches the recorded digest and manifest;
- no source or image-bearing derivative is committed or redistributed;
- the annotation converter reproduces expected split and relation counts; and
- public documentation clearly limits claims to scanned forms and linked question/answer extraction.

**Adjust** by making FUNSD optional and using an openly reusable real-form corpus as the public benchmark if one is suitable.

**Cut FUNSD** if the project's intended use, redistribution, automated setup, or later commercial/AWS context conflicts with the authoritative terms or cannot be cleared confidently.

## Decision surfaced

The blueprint now needs an explicit corpus decision: keep FUNSD only as a restricted optional benchmark, or replace/complement it with an openly reusable corpus. That decision should follow focused research into available alternatives rather than assuming FUNSD is permissively licensed.
