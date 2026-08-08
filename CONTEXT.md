# Blueprint Conformance

The docproc blueprint language connects stable specification statements to acceptance and retained evidence without recording implementation chronology.

## Language

**Normative requirement**:
An atomic, stable statement of behavior or constraint that later work must satisfy.
_Avoid_: Task, note, aspiration

**Acceptance criterion**:
An observable condition that decides whether one or more Normative requirements are satisfied.
_Avoid_: Implementation step, test name

**Planned test**:
A specified verification method expected to exercise an Acceptance criterion.
_Avoid_: Acceptance criterion, evidence

**Decision evidence**:
A commit-pinned research or decision artifact that explains why a Normative requirement exists.
_Avoid_: Conformance evidence

**Conformance evidence**:
An immutable observation produced later to demonstrate whether an implemented result satisfies a Normative requirement.
_Avoid_: Decision evidence, claim

**Evidence record**:
A content-addressed envelope that identifies a Conformance-evidence observation, its inputs, producer, environment, outcome, and specification references.
_Avoid_: Log line, screenshot alone

**Trace link**:
An explicit relationship among a Normative requirement, its Decision evidence, Acceptance criteria, Planned tests, and expected Evidence records.
_Avoid_: Prose implication

**Trace matrix**:
The blueprint index containing every Trace link exactly once.
_Avoid_: Checklist, status board

**Development diary**:
Chronological implementation narration, temporary status, session history, or commit-by-commit progress that does not belong in the blueprint.
_Avoid_: Trace matrix, evidence index
