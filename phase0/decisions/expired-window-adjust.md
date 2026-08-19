# Expired Phase 0 window — Adjust candidate

> **Pending human, explicitly non-authorizing approval.** This AI-prepared record is not approval, does not establish T0, and authorizes no acquisition or measurement.

- Evidence ID: `EVID-PHASE0-DECISION-001`
- Machine record: [`expired-window-adjust.json`](./expired-window-adjust.json)
- Prior T0: `2026-08-08T17:54:45Z`
- Prior deadline: `2026-08-10T17:54:45Z`
- Frozen reason: `phase0-window-expired-before-resolution`
- Overall result: **Adjust**
- Precedence: no Cut; six Adjust; therefore Overall Adjust

## Result

The old Phase 0 window expired without retained final evidence for LIC, CORPUS, PARSER, VLM, MACHINE, or WALK. Every unresolved gate and criterion is Adjust with the frozen expiry reason. Gate WALK is Adjust. No durable walking-vertical work is authorized.

No accepted exact-byte closure, SBOM/notices reconciliation, NAF corpus verification, parser/VLM conformance, M5 coexistence result, independent acquisition receipt, or descendant/container-covering no-egress preflight exists.

## Tracker reconciliation

Issue #20 was closed despite its [explicit “not resolved” comment](https://github.com/monocongo/docproc/issues/20#issuecomment-5229146843). It was [reopened as a tracker correction](https://github.com/monocongo/docproc/issues/20#issuecomment-5343953722) and remains the hard prerequisite for #21.

PR #26 and merged PR #27 (`7046d540c5ffbe2181f67f1fc3a8a2616add7265`, merge `81d554ad5d153fff2b36753bca5e0da9ed0ff531`) are fail-closed harness cleanup only. They are not artifact admission or Gate LIC evidence. PR #27's PF wrapper refuses every measured command rather than claim incomplete egress denial.

## Gate outcomes

| Gate | Outcome | Basis |
|---|---|---|
| LIC | Adjust | Exact closure, rights review, SBOM/notices, independent acquisition receipt, and no-egress evidence are not demonstrated. |
| CORPUS | Adjust | NAF acquisition/profile/scorer/ledger evidence is not demonstrated. |
| PARSER | Adjust | No valid Docling conformance measurement exists. |
| VLM | Adjust | No valid host-Ollama/Qwen conformance measurement exists. |
| MACHINE | Adjust | No valid M5 coexistence/resource measurement exists. |
| WALK | Adjust | The decision deadline expired and prerequisite gate evidence is missing. |

The machine record enumerates every frozen criterion and its `adjust` outcome.

## Required revision

The proposed [`phase-0-recovery-contract.md`](../../docs/decisions/phase-0-recovery-contract.md):

1. separates #20's non-content-bearing NAF source/terms admission from #21's content acquisition and observation;
2. replaces the inadequate PF-anchor approach with a hardware-isolated no-uplink boundary covering host processes, descendants, and Docker containers; and
3. requires a new human superseding Implementation authorization/new T0 after this Adjust record receives a separate non-authorizing human approval.

## Required human action

A human approver must review the exact committed JSON/Markdown pair and post one new, unedited #25 comment that:

- links the exact commit;
- says the expired-window result is approved as Overall Adjust;
- says the approval is explicitly non-authorizing;
- says it does not establish T0 and permits no acquisition or measurement; and
- identifies the approver and immutable GitHub timestamp.

After the revised contract/blueprint is accepted, a human—not an agent—must post the new #13 Implementation authorization that links and explicitly supersedes [comment `5227376778`](https://github.com/monocongo/docproc/issues/13#issuecomment-5227376778). Its `createdAt` becomes the new T0.

Until both human steps exist, stop.

## Publication safety

This summary and its JSON pair are metadata-only and publication-safe. They contain no local path, secret, host fingerprint, NAF content, transcription, ledger, model/OCR weight, OCI archive, third-party binary, or content-bearing output.
