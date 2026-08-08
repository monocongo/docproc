# Processing Coordination

The docproc coordination language separates durable processing facts from replaceable execution and query mechanisms so local operation remains simple without making future distribution invisible or automatic.

## Language

**Source object**:
One occurrence of PDF bytes received from a source.
_Avoid_: Document

**Document**:
The identity shared by Source objects containing exactly the same PDF content.
_Avoid_: Upload, file

**Processing request**:
An idempotent intention to create exactly one Processing run.
_Avoid_: Processing run, notification

**Processing run**:
One attempt to process a Document under one Processing request and processing definition.
_Avoid_: Document, job

**Stage attempt**:
One execution attempt for a named stage of a Processing run.
_Avoid_: Processing run, message

**Work claim**:
Time-bounded authority for one worker to advance one Stage attempt.
_Avoid_: Lock, queue message

**Artifact**:
Immutable stage output whose identity is derived from its kind and content.
_Avoid_: Local file, latest object

**Artifact reference**:
A durable, verifiable description of one exact Artifact occurrence.
_Avoid_: Path, URL

**Processing definition**:
The immutable set of component, model, prompt, schema, and relevant configuration identities governing a Processing run.
_Avoid_: Environment, latest configuration

**Projection**:
A rebuildable view derived from authoritative Processing runs and Artifacts.
_Avoid_: Source of truth
