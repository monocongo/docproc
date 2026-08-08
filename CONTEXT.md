# Document Processing Evaluation

The docproc evaluation language separates output shape, source traceability, and measured correctness so that a successful run cannot be mistaken for an accurate one.

## Language

**Linked form field**:
A document label and its associated response, represented without assuming a fixed business-field ontology.
_Avoid_: Named field, fixed field

**Synthetic fixture**:
A project-authored or separately cleared document with deterministic expected behavior, suitable for repository distribution and offline checks.
_Avoid_: Public benchmark, real-form benchmark

**Clean-clone acceptance**:
The checks that run from a source checkout using only committed synthetic fixtures and no externally acquired corpus.
_Avoid_: Benchmark run

**Public accuracy benchmark**:
A reproducible real-form evaluation whose aggregate results may be published, but whose source data is explicitly acquired outside the repository.
_Avoid_: Default test corpus, CI corpus

**Evidence profile**:
A fixed set of source revisions, artifact identities, integrity records, license evidence, split membership, and ground-truth eligibility rules that identifies one reproducible benchmark input.
_Avoid_: Dataset version

**Schema-valid**:
Conforming to the fixed extraction schema; this makes no claim that extracted content is correct or traceable.
_Avoid_: Valid, successful

**Evidence-grounded**:
Citing page evidence that can be checked against the source document; this makes no claim that the cited label/value pair is correct.
_Avoid_: Accurate, validated

**Evaluated accuracy**:
Correctness measured against eligible ground truth under a frozen matching contract.
_Avoid_: Quality, schema validity, evidence grounding

**Ignored ground truth**:
An annotated linked-form-field edge excluded from accuracy denominators for a recorded reason while remaining visible to the evaluator so corresponding predictions are handled deterministically.
_Avoid_: Deleted annotation, ignored page
