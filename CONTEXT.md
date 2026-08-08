# Local Document Extraction

The docproc extraction language distinguishes a model proposed for measurement from one selected by measured evidence, and separates response shape, source traceability, and correctness.

## Language

**Candidate model**:
A pinned model artifact proposed for bounded measurement; it is not yet an architectural selection.
_Avoid_: Selected model, production model

**Selected model**:
A candidate model retained on measured evidence rather than proposal alone.
_Avoid_: Default model, candidate

**Serving contract**:
The complete frozen set of model artifact, local server, request, generation, context, batching, validation, and telemetry constraints used for a measured extraction.
_Avoid_: API call, model configuration

**Selection gate**:
A frozen, observable condition that a candidate model must satisfy before selection.
_Avoid_: Preference, recommendation

**Hard failure**:
An observed violation of a selection gate.
_Avoid_: Poor result, concern

**Scoring contract**:
The frozen ground-truth, normalization, matching, exclusion, metric, threshold, tie-breaker, and aggregation rules for one evaluation.
_Avoid_: Metric list

**Schema-valid**:
Conforming to the fixed extraction schema; this makes no claim that extracted content is correct or traceable.
_Avoid_: Successful extraction

**Evidence-grounded**:
Citing page evidence that can be checked against the source document; this makes no claim that the cited label/value pair is correct.
_Avoid_: Accurate

**Evaluated accuracy**:
Correctness measured against eligible ground truth under a scoring contract.
_Avoid_: Quality

**Admitted page**:
A page included in the population of a measured run.
_Avoid_: Attempted page

**Accepted extraction**:
The schema-valid response retained as a page's extraction outcome; acceptance does not imply evidence grounding or evaluated accuracy.
_Avoid_: Successful extraction

**Repair attempt**:
A follow-up request intended to turn a schema-invalid first response into a schema-valid response.
_Avoid_: Retry
