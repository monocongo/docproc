# Phase 0 Decisions

The docproc Phase 0 language separates a valid evidence result from a scope decision and keeps response shape, source traceability, and measured correctness distinct.

## Language

**Implementation authorization**:
The new, unedited issue #13 resolution comment that approves one commit-pinned final blueprint and conditionally permits its Phase 0 and Walking vertical work.
_Avoid_: Gate result, plan approval

**T0**:
The immutable creation time of the Implementation authorization, used as the seven-day target's sole clock origin.
_Avoid_: First implementation commit, Phase 0 completion time

**Walking vertical**:
One project-authored synthetic PDF traversing every agreed local stage into an inspectable extraction result.
_Avoid_: Prototype, full benchmark, production pipeline

**Selection gate**:
A frozen, observable condition that a candidate or project path must satisfy before selection.
_Avoid_: Preference, recommendation

**Gate evidence**:
The complete, content-addressed inputs, observations, outputs, and deviations used to resolve one Selection gate.
_Avoid_: Notes, impression

**Valid measurement**:
A measurement that followed its frozen contract with every admitted input and required observation accounted for.
_Avoid_: Successful result

**Go**:
The gate outcome serialized as `go` that retains the measured candidate or path without changing its frozen contract.
_Avoid_: Good enough, pass with caveats

**Adjust**:
The gate outcome serialized as `adjust` that stops dependent work until a named contract, candidate, or scope decision is approved and remeasured.
_Avoid_: Retry, tune later

**Cut**:
The gate outcome serialized as `cut` that removes the candidate or path from the current initial implementation rather than substituting an unapproved alternative.
_Avoid_: Adjust, fallback

**Overall Phase 0 outcome**:
The single Go, Adjust, or Cut result obtained by reconciling every Selection gate.
_Avoid_: Majority result, partial go

**Schema-valid**:
Conforming to the fixed extraction schema; this makes no claim that extracted content is correct or traceable.
_Avoid_: Successful, accurate

**Evidence-grounded**:
Citing page evidence that can be checked against the source document; this makes no claim that the cited label/value pair is correct.
_Avoid_: Accurate, validated

**Evaluated accuracy**:
Correctness measured against eligible ground truth under a frozen scoring contract.
_Avoid_: Quality, schema validity, evidence grounding
