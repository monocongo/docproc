# Local Document Processing

The docproc delivery language distinguishes one complete, inspectable path from broader benchmark, reliability, and production-readiness work.

## Language

**Source object**:
One occurrence of PDF bytes received from a source.
_Avoid_: Document

**Document**:
The identity shared by source objects containing exactly the same PDF content.
_Avoid_: Upload, file

**Processing run**:
One attempt to process a Document under one processing definition.
_Avoid_: Document, job

**Walking vertical**:
One project-authored synthetic PDF traversing every agreed local stage into an inspectable extraction result.
_Avoid_: Prototype, full benchmark, production pipeline

**Walking-vertical acceptance run**:
The manual, network-denied execution of the walking vertical against the actual pinned local components.
_Avoid_: Ordinary CI, public accuracy benchmark

**Basic correctness test**:
A deterministic offline check of project-owned behavior that ships with the Walking vertical.
_Avoid_: Hardening test, benchmark

**Schema-valid**:
Conforming to the fixed extraction schema; this makes no claim that extracted content is correct or traceable.
_Avoid_: Successful, accurate

**Evidence-grounded**:
Citing page evidence that can be checked against the source document; this makes no claim that the cited label/value pair is correct.
_Avoid_: Accurate, validated

**Evaluated accuracy**:
Correctness measured against eligible ground truth under a frozen scoring contract.
_Avoid_: Quality, schema validity, evidence grounding

**Later hardening**:
Reliability, breadth, performance, security, and packaging work intentionally performed after walking-vertical acceptance.
_Avoid_: Walking vertical
