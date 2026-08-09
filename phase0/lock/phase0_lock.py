#!/usr/bin/env python3
"""Fail-closed acquisition and evidence sealing for the Phase 0 LIC gate.

This program deliberately has no third-party dependencies: it is used before the
Python environment it records has been admitted.  It never chooses a dependency,
accepts a redirect, or treats a download as admitted.  A human-reviewed policy
must name the precise bytes before ``prefetch`` will make a network request.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, NoReturn, Tuple

ADDRESS_RE = re.compile(r"^(?:evp1|art1|evr1):sha256:[0-9a-f]{64}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX_COMMIT_RE = re.compile(r"^[0-9a-f]{40,64}$")


class LockError(RuntimeError):
    """An invalid policy, observation, or evidence record."""


def die(message: str) -> NoReturn:
    raise LockError(message)


def no_duplicate_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            die("duplicate JSON object member: %s" % key)
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_object)
    except (OSError, json.JSONDecodeError) as exc:
        die("cannot read JSON %s: %s" % (path, exc))


def assert_json_domain(value: Any, path: str = "$") -> None:
    """Restrict records to the JCS subset this zero-dependency implementation emits.

    All Phase 0 values are strings, booleans, nulls, arrays, objects, or integral
    byte/count values.  Rejecting floats and non-ASCII keys prevents Python's JSON
    encoder from becoming an accidental, incomplete implementation of ECMAScript
    number or UTF-16 key ordering rules.
    """
    if value is None or isinstance(value, bool) or isinstance(value, str):
        return
    if isinstance(value, int):
        if abs(value) > 9007199254740991:
            die("integer outside JCS interoperable range at %s" % path)
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            die("non-finite number at %s" % path)
        die("floating-point numbers are forbidden at %s; use an integer or string" % path)
    if isinstance(value, list):
        for index, item in enumerate(value):
            assert_json_domain(item, "%s[%d]" % (path, index))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not key.isascii():
                die("object keys must be ASCII strings at %s" % path)
            assert_json_domain(item, "%s.%s" % (path, key))
        return
    die("unsupported JSON value at %s" % path)


def jcs_bytes(value: Any) -> bytes:
    """Canonical bytes for the deliberately restricted Phase 0 evidence domain."""
    assert_json_domain(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> Tuple[str, int]:
    digest = hashlib.sha256()
    length = 0
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
            length += len(block)
    return digest.hexdigest(), length


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_once(path: Path, data: bytes) -> None:
    """Create content once, or prove an existing path is exactly the same."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(data)
    except FileExistsError:
        if path.read_bytes() != data:
            die("immutable path already contains different bytes: %s" % path)


def write_json_once(path: Path, value: Any) -> None:
    write_once(path, jcs_bytes(value) + b"\n")


def policy_items(policy: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    items = policy.get("artifacts")
    if not isinstance(items, list) or not items:
        die("policy.artifacts must be a non-empty array")
    return items


def validate_url(url: str, context: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.fragment:
        die("%s must be an absolute credential-free HTTPS URL" % context)


def validate_policy(policy: Any) -> Dict[str, Any]:
    if not isinstance(policy, dict):
        die("policy root must be an object")
    required = {
        "policy_version",
        "scope",
        "source_decisions",
        "artifacts",
    }
    missing = required - set(policy)
    if missing:
        die("policy is missing: %s" % ", ".join(sorted(missing)))
    if policy["policy_version"] not in {"phase0-base-primary-v1", "phase0-exact-byte-v1"}:
        die("unsupported policy_version")
    if policy["scope"] != "base-and-primary-candidate-admission":
        die("policy scope is not base-and-primary-candidate-admission")
    if not isinstance(policy["source_decisions"], list) or not policy["source_decisions"]:
        die("policy.source_decisions must be a non-empty list")
    for source in policy["source_decisions"]:
        if not isinstance(source, dict):
            die("each source decision must be an object")
        commit = source.get("commit")
        if not isinstance(commit, str) or not HEX_COMMIT_RE.match(commit):
            die("each source decision must carry a full lowercase commit")
    seen = set()
    for item in policy_items(policy):
        if not isinstance(item, dict):
            die("artifact must be an object")
        fields = {
            "id", "kind", "required", "admission_status", "origin", "acquisition",
            "license", "distribution_mode", "publication_disposition",
        }
        absent = fields - set(item)
        if absent:
            die("artifact is missing %s" % ", ".join(sorted(absent)))
        identifier = item["id"]
        if not isinstance(identifier, str) or not re.match(r"^[a-z0-9][a-z0-9.-]+$", identifier):
            die("artifact id is invalid: %r" % identifier)
        if identifier in seen:
            die("duplicate artifact id: %s" % identifier)
        seen.add(identifier)
        if policy["policy_version"] == "phase0-exact-byte-v1":
            component_id = item.get("component_id")
            if not isinstance(component_id, str) or not re.match(r"^[a-z0-9][a-z0-9.-]+$", component_id):
                die("exact-byte artifact %s requires a valid component_id" % identifier)
        if not isinstance(item["required"], bool):
            die("artifact %s required must be a boolean" % identifier)
        if item["admission_status"] not in {"pending-human-review", "approved-for-acquisition", "denied"}:
            die("artifact %s has unknown admission_status" % identifier)
        origin = item["origin"]
        if not isinstance(origin, dict) or not isinstance(origin.get("authority"), str) or not origin.get("authority"):
            die("artifact %s has no authoritative origin" % identifier)
        if not isinstance(origin.get("revision"), str) or not origin.get("revision"):
            die("artifact %s has no immutable origin revision" % identifier)
        acquisition = item["acquisition"]
        if not isinstance(acquisition, dict):
            die("artifact %s acquisition must be an object" % identifier)
        url = acquisition.get("url")
        if item["admission_status"] == "approved-for-acquisition":
            if not isinstance(url, str):
                die("approved artifact %s requires an exact acquisition URL" % identifier)
            validate_url(url, "artifact %s acquisition.url" % identifier)
            expected = acquisition.get("expected")
            if not isinstance(expected, dict):
                die("approved artifact %s requires an expected byte record" % identifier)
            expected_sha256 = expected.get("sha256")
            if not isinstance(expected_sha256, str) or not DIGEST_RE.match(expected_sha256):
                die("approved artifact %s requires an expected SHA-256" % identifier)
            if not isinstance(expected.get("byte_length"), int) or expected["byte_length"] < 0:
                die("approved artifact %s requires an expected byte_length" % identifier)
        elif url is not None:
            if not isinstance(url, str):
                die("artifact %s acquisition.url must be a string or null" % identifier)
            validate_url(url, "artifact %s acquisition.url" % identifier)
        license_info = item["license"]
        if not isinstance(license_info, dict):
            die("artifact %s license must be an object" % identifier)
        if license_info.get("evidence_class") == "NOASSERTION":
            die("artifact %s may not use NOASSERTION" % identifier)
        if license_info.get("review_status") not in {"pending-human-review", "reviewed", "reviewed-exception"}:
            die("artifact %s has no valid license review status" % identifier)
        if item["admission_status"] == "approved-for-acquisition" and license_info["review_status"] == "pending-human-review":
            die("approved artifact %s still has pending license review" % identifier)
        if item["distribution_mode"] not in {"source-only", "direct-upstream-pull", "host-installed", "manual-data-acquisition"}:
            die("artifact %s has an unapproved distribution mode" % identifier)
        if item["publication_disposition"] not in {"metadata-only", "do-not-publish", "private-only"}:
            die("artifact %s has an invalid publication disposition" % identifier)
    return policy


def repository_root() -> Path:
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True)
    if result.returncode:
        die("must run from a Git worktree")
    return Path(result.stdout.strip()).resolve()


def safe_root(raw_root: str) -> Path:
    root = Path(raw_root).expanduser().resolve()
    checkout = repository_root()
    if root == checkout or checkout in root.parents:
        die("evidence root must be outside the Git worktree: %s" % checkout)
    return root


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def download_exact(item: Dict[str, Any], root: Path) -> Dict[str, Any]:
    """Download one already-admitted URL, forbidding redirect and byte surprises."""
    acquisition = item["acquisition"]
    expected = acquisition["expected"]
    url = acquisition["url"]
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": "docproc-phase0-lock/1"})
    started = utc_now()
    try:
        response = opener.open(request, timeout=60)
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            die("redirect rejected for %s: %s" % (item["id"], exc.headers.get("Location", "missing Location")))
        die("download failed for %s: HTTP %d" % (item["id"], exc.code))
    except urllib.error.URLError as exc:
        die("download failed for %s: %s" % (item["id"], exc.reason))
    with response:
        final_url = response.geturl()
        if final_url != url:
            die("redirect/final URL mismatch rejected for %s" % item["id"])
        if response.status != 200:
            die("download failed for %s: HTTP %d" % (item["id"], response.status))
        content_length = response.headers.get("Content-Length")
        if content_length is not None and content_length != str(expected["byte_length"]):
            die("Content-Length mismatch for %s" % item["id"])
        root.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(prefix="prefetch-", dir=str(root))
        os.close(file_descriptor)
        temporary = Path(temporary_name)
        try:
            digest = hashlib.sha256()
            length = 0
            with temporary.open("wb") as destination:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    length += len(chunk)
                    if length > expected["byte_length"]:
                        die("response exceeds approved byte_length for %s" % item["id"])
                    destination.write(chunk)
                    digest.update(chunk)
            observed = digest.hexdigest()
            if observed != expected["sha256"] or length != expected["byte_length"]:
                die("byte identity mismatch for %s (got %s / %d)" % (item["id"], observed, length))
            artifact_path = root / "artifacts" / ("sha256-%s" % observed)
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            if artifact_path.exists():
                try:
                    existing_digest, existing_length = sha256_file(artifact_path)
                except OSError as exc:
                    die("cannot read existing content-addressed artifact for %s: %s" % (item["id"], type(exc).__name__))
                if existing_digest != observed or existing_length != length:
                    die("content-addressed artifact collision for %s at sha256-%s" % (item["id"], observed))
                temporary.unlink()
            else:
                os.replace(str(temporary), str(artifact_path))
        finally:
            if temporary.exists():
                temporary.unlink()
    observation = {
        "observation_version": "phase0-acquisition-observation-v1",
        "artifact_id": item["id"],
        "requested_url": url,
        "final_url": final_url,
        "method": "GET",
        "status": 200,
        "content_digest": "sha256:" + expected["sha256"],
        "byte_length": expected["byte_length"],
        "content_type": response.headers.get("Content-Type", "").split(";", 1)[0].lower(),
        "observed_started_at_utc": started,
        "observed_completed_at_utc": utc_now(),
        "redirects": [],
        "network_result": "admitted-request-completed",
    }
    write_json_once(root / "observations" / (item["id"] + ".json"), observation)
    return observation


def validate_closure(catalog: Dict[str, Any], exact_policy: Dict[str, Any]) -> None:
    if catalog["policy_version"] != "phase0-base-primary-v1":
        die("closure catalog must use phase0-base-primary-v1")
    if exact_policy["policy_version"] != "phase0-exact-byte-v1":
        die("closure input must use phase0-exact-byte-v1")
    catalog_ids = {item["id"] for item in policy_items(catalog)}
    covered = set()
    for item in policy_items(exact_policy):
        component_id = item["component_id"]
        if component_id not in catalog_ids:
            die("exact-byte artifact %s belongs to unapproved component %s" % (item["id"], component_id))
        covered.add(component_id)
    missing = {item["id"] for item in policy_items(catalog) if item["required"]} - covered
    if missing:
        die("exact-byte policy does not cover required catalog components: %s" % ", ".join(sorted(missing)))


def record_prefetch_failure(root: Path, artifact_id: str, message: str) -> None:
    """Retain a failed admitted request without retaining credential or local-path data."""
    failure = {
        "failure_version": "phase0-acquisition-failure-v1",
        "artifact_id": artifact_id,
        "occurred_at_utc": utc_now(),
        "stage": "prefetch",
        "message": message,
        "content_classification": "metadata-only",
        "publication_disposition": "private-only",
    }
    event_name = "sha256-" + sha256_bytes(jcs_bytes(failure)) + ".json"
    write_json_once(root / "failures" / event_name, failure)


def prefetch(policy: Dict[str, Any], root: Path) -> None:
    if policy["policy_version"] != "phase0-exact-byte-v1":
        die("prefetch requires a reviewed phase0-exact-byte-v1 policy")
    pending = [item["id"] for item in policy_items(policy) if item["required"] and item["admission_status"] != "approved-for-acquisition"]
    if pending:
        die("refusing network acquisition until every required artifact is approved: %s" % ", ".join(pending))
    denied = [item["id"] for item in policy_items(policy) if item["admission_status"] == "denied"]
    if denied:
        die("refusing network acquisition with denied artifacts in graph: %s" % ", ".join(denied))
    for item in policy_items(policy):
        if item["admission_status"] == "approved-for-acquisition":
            try:
                download_exact(item, root)
            except LockError as exc:
                record_prefetch_failure(root, item["id"], str(exc))
                raise


def artifact_descriptor(content_digest: str, byte_length: int, media_type: str, content_encoding: str = "identity") -> Dict[str, Any]:
    descriptor = {
        "descriptor_version": "docproc-artifact-descriptor-v1",
        "content_digest": content_digest,
        "byte_length": byte_length,
        "media_type": media_type,
        "content_encoding": content_encoding,
    }
    address = "art1:sha256:" + sha256_bytes(b"docproc:artifact-descriptor:v1\x00" + jcs_bytes(descriptor))
    return {"address": address, "descriptor": descriptor}


def load_observations(root: Path, policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    observations: List[Dict[str, Any]] = []
    for item in policy_items(policy):
        if not item["required"]:
            continue
        path = root / "observations" / (item["id"] + ".json")
        if not path.exists():
            die("missing required acquisition observation: %s" % item["id"])
        observed = load_json(path)
        expected = item["acquisition"]["expected"]
        if observed.get("artifact_id") != item["id"] or observed.get("content_digest") != "sha256:" + expected["sha256"] or observed.get("byte_length") != expected["byte_length"]:
            die("observation does not match policy for %s" % item["id"])
        artifact = root / "artifacts" / ("sha256-" + expected["sha256"])
        if not artifact.is_file():
            die("missing content-addressed artifact for %s" % item["id"])
        try:
            digest, length = sha256_file(artifact)
        except OSError as exc:
            die("cannot read content-addressed artifact for %s: %s" % (item["id"], type(exc).__name__))
        if digest != expected["sha256"] or length != expected["byte_length"]:
            die("content-addressed file does not match observation for %s" % item["id"])
        observations.append(observed)
    return observations


def load_optional_records(root: Path, directory: str) -> List[Dict[str, Any]]:
    records_path = root / directory
    if not records_path.exists():
        return []
    if not records_path.is_dir():
        die("%s must be a directory when present" % records_path)
    records = []
    for path in sorted(records_path.glob("*.json")):
        record = load_json(path)
        if not isinstance(record, dict):
            die("%s must contain JSON objects" % path)
        records.append(record)
    return records


def validate_lock_inventory_payload(payload: Dict[str, Any], schema: Any) -> None:
    """Apply the intentionally small JSON Schema subset used by this payload."""
    if not isinstance(schema, dict) or schema.get("$id") != "docproc:phase0-lock-inventory-v1":
        die("schema is not phase0-lock-inventory-v1")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        die("lock-inventory schema must be a closed object")
    required = schema.get("required")
    properties = schema.get("properties")
    if not isinstance(required, list) or not all(isinstance(name, str) for name in required) or not isinstance(properties, dict):
        die("lock-inventory schema has invalid required/properties declarations")
    missing = set(required) - set(payload)
    unexpected = set(payload) - set(properties)
    if missing:
        die("payload is missing schema members: %s" % ", ".join(sorted(missing)))
    if unexpected:
        die("payload has unexpected schema members: %s" % ", ".join(sorted(unexpected)))
    expected_types = {"string": str, "array": list, "object": dict}
    for name, constraints in properties.items():
        if name not in payload:
            continue
        if not isinstance(constraints, dict):
            die("schema constraints for %s must be an object" % name)
        value = payload[name]
        expected_type = constraints.get("type")
        if expected_type is not None:
            python_type = expected_types.get(expected_type)
            if python_type is None or not isinstance(value, python_type):
                die("payload member %s does not satisfy schema type" % name)
        if "const" in constraints and value != constraints["const"]:
            die("payload member %s does not satisfy schema const" % name)
        pattern = constraints.get("pattern")
        if pattern is not None:
            if not isinstance(pattern, str) or not isinstance(value, str) or re.fullmatch(pattern, value) is None:
                die("payload member %s does not satisfy schema pattern" % name)
        min_items = constraints.get("minItems")
        if min_items is not None:
            if not isinstance(min_items, int) or not isinstance(value, list) or len(value) < min_items:
                die("payload member %s does not satisfy schema minItems" % name)


def seal(policy: Dict[str, Any], root: Path, schema: Path, source_commit: str) -> str:
    if policy["policy_version"] != "phase0-exact-byte-v1":
        die("sealing requires a reviewed phase0-exact-byte-v1 policy")
    if not HEX_COMMIT_RE.match(source_commit):
        die("source commit must be a full lowercase SHA")
    schema_definition = load_json(schema)
    schema_bytes = schema.read_bytes()
    observations = load_observations(root, policy)
    inventory = []
    for observation in observations:
        item = next(item for item in policy_items(policy) if item["id"] == observation["artifact_id"])
        descriptor = artifact_descriptor(
            observation["content_digest"], observation["byte_length"], observation["content_type"] or "application/octet-stream"
        )
        inventory.append({
            "artifact_id": observation["artifact_id"],
            "origin": item["origin"],
            "license": item["license"],
            "distribution_mode": item["distribution_mode"],
            "publication_disposition": item["publication_disposition"],
            "observation": observation,
            "artifact_descriptor": descriptor,
        })
    inventory.sort(key=lambda row: row["artifact_id"])
    exceptions = [
        {"artifact_id": item["id"], "license": item["license"]}
        for item in policy_items(policy)
        if item["license"]["review_status"] == "reviewed-exception"
    ]
    payload = {
        "payload_version": "docproc-evidence-payload-v1",
        "payload_schema_digest": "sha256:" + sha256_bytes(schema_bytes),
        "evidence_id": "EVID-LOCK-INVENTORY-001",
        "kind": "lock-inventory",
        "source_commit": source_commit,
        "policy_digest": "sha256:" + sha256_bytes(jcs_bytes(policy)),
        "source_decisions": policy["source_decisions"],
        "inventory": inventory,
        "failures": load_optional_records(root, "failures"),
        "exclusions": load_optional_records(root, "exclusions"),
        "reviewed_exceptions": exceptions,
        "content_classification": "metadata-only",
        "publication_disposition": "private-only",
    }
    validate_lock_inventory_payload(payload, schema_definition)
    payload_address = "evp1:sha256:" + sha256_bytes(b"docproc:evidence-payload:v1\x00" + jcs_bytes(payload))
    envelope = {
        "envelope_version": "docproc-evidence-envelope-v1",
        "payload_address": payload_address,
        "run_id": "phase0-lic-admission",
        "source_object_id": "not-applicable",
        "document_digest": "not-applicable",
        "processing_definition_digest": "not-applicable",
        "input_ids": [row["artifact_id"] for row in inventory],
        "environment": {"kind": "phase0-admission", "policy_digest": payload["policy_digest"]},
        "outcome": "go-candidate-pending-human-approval",
        "specification_refs": [source["commit"] for source in policy["source_decisions"]],
        "artifact_bindings": [{"role": "admitted-artifact", "artifact_address": row["artifact_descriptor"]["address"]} for row in inventory],
        "content_classification": "metadata-only",
        "publication_disposition": "private-only",
    }
    envelope["artifact_bindings"].sort(key=lambda row: (row["role"], row["artifact_address"]))
    evidence_address = "evr1:sha256:" + sha256_bytes(b"docproc:evidence-envelope:v1\x00" + jcs_bytes(envelope))
    envelope["evidence_address"] = evidence_address
    record = root / "records" / evidence_address.replace(":", "_")
    write_json_once(record / "payload.json", payload)
    write_json_once(record / "envelope.json", envelope)
    summary = "\n".join([
        "# EVID-LOCK-INVENTORY-001",
        "",
        "- Evidence address: `%s`" % evidence_address,
        "- Payload address: `%s`" % payload_address,
        "- Scope: base and primary-candidate admission only; not final Gate LIC.",
        "- Content classification: metadata-only.",
        "- Publication disposition: private-only.",
        "- Artifacts: %s." % ", ".join(row["artifact_id"] for row in inventory),
        "",
        "This generated summary does not itself approve an artifact or authorize execution.",
        "",
    ]).encode("utf-8")
    write_once(record / "summary.md", summary)
    print(evidence_address)
    return evidence_address


def verify(root: Path, evidence_address: str) -> None:
    if not ADDRESS_RE.match(evidence_address) or not evidence_address.startswith("evr1:"):
        die("invalid evidence address")
    record = root / "records" / evidence_address.replace(":", "_")
    payload = load_json(record / "payload.json")
    envelope = load_json(record / "envelope.json")
    payload_address = "evp1:sha256:" + sha256_bytes(b"docproc:evidence-payload:v1\x00" + jcs_bytes(payload))
    if payload_address != envelope.get("payload_address"):
        die("payload address mismatch")
    supplied = envelope.pop("evidence_address", None)
    calculated = "evr1:sha256:" + sha256_bytes(b"docproc:evidence-envelope:v1\x00" + jcs_bytes(envelope))
    if supplied != calculated or supplied != evidence_address:
        die("evidence address mismatch")
    inventory = payload.get("inventory")
    if not isinstance(inventory, list):
        die("payload inventory is invalid")
    for row in inventory:
        if not isinstance(row, dict) or not isinstance(row.get("observation"), dict):
            die("payload inventory entry is invalid")
        observation = row["observation"]
        content_digest = observation.get("content_digest")
        byte_length = observation.get("byte_length")
        artifact_id = observation.get("artifact_id")
        if not isinstance(content_digest, str) or not SHA256_RE.match(content_digest) or not isinstance(byte_length, int) or byte_length < 0 or not isinstance(artifact_id, str):
            die("payload inventory observation is invalid")
        artifact = root / "artifacts" / ("sha256-" + content_digest.removeprefix("sha256:"))
        if not artifact.is_file():
            die("missing content-addressed artifact for %s" % artifact_id)
        try:
            digest, length = sha256_file(artifact)
        except OSError as exc:
            die("cannot read content-addressed artifact for %s: %s" % (artifact_id, type(exc).__name__))
        if "sha256:" + digest != content_digest or length != byte_length:
            die("content-addressed artifact does not match sealed inventory for %s" % artifact_id)


def platform_command_observation(command_id: str) -> Dict[str, Any]:
    """Capture a bounded macOS platform fact from a fixed, non-user command.

    Do not execute an unadmitted host tool merely to learn its version. Tool
    versions are admitted through the exact-byte policy; this helper runs only
    the three fixed operating-system probes required for a platform baseline.
    """
    try:
        if command_id == "sw_vers":
            result = subprocess.run(["/usr/bin/sw_vers"], text=True, capture_output=True, timeout=15)
        elif command_id == "cpu_brand":
            result = subprocess.run(["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"], text=True, capture_output=True, timeout=15)
        elif command_id == "memory_bytes":
            result = subprocess.run(["/usr/sbin/sysctl", "-n", "hw.memsize"], text=True, capture_output=True, timeout=15)
        else:
            die("unapproved platform command: %s" % command_id)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "unavailable", "detail": type(exc).__name__}
    output = (result.stdout + result.stderr).strip()
    # Version probes have no legitimate need to emit a local filesystem path.
    # Remove the entire response rather than trying to partially rewrite an
    # arbitrary token and accidentally disclose a local path.
    if re.search(r"(?:^|[\s=])(?:/|file:///|unix:///)", output):
        output = "<redacted-local-path-output>"
    return {
        "status": "observed" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "output": output[:4096],
    }


def host_record() -> Dict[str, Any]:
    executable_names = ["uv", "docker", "docker-compose", "qpdf", "ollama"]
    executables = []
    for name in executable_names:
        location = shutil.which(name)
        if location:
            digest, length = sha256_file(Path(location))
            executables.append({"name": name, "sha256": "sha256:" + digest, "byte_length": length})
        else:
            executables.append({"name": name, "status": "not-present"})
    platform_records = {
        "sw_vers": platform_command_observation("sw_vers"),
        "cpu_brand": platform_command_observation("cpu_brand"),
        "memory_bytes": platform_command_observation("memory_bytes"),
    }
    return {
        "record_version": "phase0-host-baseline-v1",
        "recorded_at_utc": utc_now(),
        "monotonic_ns": str(time.monotonic_ns()),
        "clock_source": "Python datetime.now(timezone.utc) and time.monotonic_ns",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "platform_records": platform_records,
        "python": {"version": sys.version, "sqlite_runtime": sqlite3.sqlite_version},
        "executables": executables,
        "publication_disposition": "private-only",
    }


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    policy_cmd = sub.add_parser("validate-policy")
    policy_cmd.add_argument("--policy", type=Path, required=True)
    closure_cmd = sub.add_parser("validate-closure")
    closure_cmd.add_argument("--catalog", type=Path, required=True)
    closure_cmd.add_argument("--policy", type=Path, required=True)
    prefetch_cmd = sub.add_parser("prefetch")
    prefetch_cmd.add_argument("--catalog", type=Path, required=True)
    prefetch_cmd.add_argument("--policy", type=Path, required=True)
    prefetch_cmd.add_argument("--root", required=True, help="private evidence root outside this Git worktree")
    seal_cmd = sub.add_parser("seal")
    seal_cmd.add_argument("--catalog", type=Path, required=True)
    seal_cmd.add_argument("--policy", type=Path, required=True)
    seal_cmd.add_argument("--root", required=True)
    seal_cmd.add_argument("--schema", type=Path, required=True)
    seal_cmd.add_argument("--source-commit", required=True)
    verify_cmd = sub.add_parser("verify")
    verify_cmd.add_argument("--root", required=True)
    verify_cmd.add_argument("--evidence-address", required=True)
    host_cmd = sub.add_parser("capture-host-baseline")
    host_cmd.add_argument("--root", required=True, help="private evidence root outside this Git worktree")
    args = parser.parse_args(argv)
    try:
        if args.command == "capture-host-baseline":
            write_json_once(safe_root(args.root) / "host-baseline.json", host_record())
        elif args.command == "verify":
            verify(safe_root(args.root), args.evidence_address)
        else:
            policy = validate_policy(load_json(args.policy))
            if args.command == "validate-policy":
                print("policy valid; no network request made")
            elif args.command == "validate-closure":
                catalog = validate_policy(load_json(args.catalog))
                validate_closure(catalog, policy)
                print("exact-byte policy covers only the base/primary catalog; no network request made")
            elif args.command == "prefetch":
                validate_closure(validate_policy(load_json(args.catalog)), policy)
                prefetch(policy, safe_root(args.root))
            elif args.command == "seal":
                validate_closure(validate_policy(load_json(args.catalog)), policy)
                seal(policy, safe_root(args.root), args.schema, args.source_commit)
        return 0
    except LockError as exc:
        print("phase0-lock: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
