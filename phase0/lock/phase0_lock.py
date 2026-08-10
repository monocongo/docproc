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
import stat
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
IMMUTABLE_REFERENCE_RE = re.compile(r"^(?:git:[0-9a-f]{40,64}|sha256:[0-9a-f]{64})$")
MEDIA_TYPE_RE = re.compile(r"^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$")
IANA_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9!#$&^_.+-]*$")
TEXTUAL_MEDIA_TYPE_RE = re.compile(r"^(?:text/|application/(?:json|xml|javascript|sql|graphql)$|application/.+\+(?:json|xml)$)")
SCRIPT_DIRECTORY = Path(__file__).resolve().parent


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
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            die("string is not a Unicode scalar sequence at %s" % path)
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


def ensure_private_directory(directory: Path) -> None:
    """Require an owner-only, non-symlink directory for private evidence."""
    try:
        info = directory.lstat()
    except FileNotFoundError:
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        info = directory.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        die("private evidence path is not a directory")
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        die("private evidence directory must be owned and accessible only by this user")


def ensure_private_tree(root: Path, directory: Path) -> None:
    """Create and check evidence directories without inheriting the umask."""
    try:
        relative = directory.relative_to(root)
    except ValueError:
        die("private evidence path escapes its root")
    ensure_private_directory(root)
    current = root
    for part in relative.parts:
        current /= part
        ensure_private_directory(current)


def write_once(root: Path, path: Path, data: bytes) -> None:
    """Create private content once, or prove an existing file has identical bytes."""
    ensure_private_tree(root, path.parent)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            info = path.lstat()
        except OSError as exc:
            die("cannot inspect immutable private evidence: %s" % type(exc).__name__)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            die("immutable private evidence is not a regular file")
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            die("immutable private evidence must be owned and accessible only by this user")
        if path.read_bytes() != data:
            die("immutable path already contains different bytes: %s" % path)
    else:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)


def write_json_once(root: Path, path: Path, value: Any) -> None:
    write_once(root, path, jcs_bytes(value) + b"\n")


def policy_items(policy: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    items = policy.get("artifacts")
    if not isinstance(items, list) or not items:
        die("policy.artifacts must be a non-empty array")
    return items


def validate_url(url: str, context: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or "?" in url
        or "#" in url
    ):
        die("%s must be an absolute credential-free HTTPS URL without query or fragment" % context)


def validate_descriptor_metadata(value: Any, artifact_id: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        die("approved artifact %s requires descriptor metadata" % artifact_id)
    required = {"media_type", "content_encoding"}
    if required - set(value):
        die("approved artifact %s descriptor metadata is incomplete" % artifact_id)
    allowed = required | {"charset", "format_schema"}
    if set(value) - allowed:
        die("approved artifact %s descriptor metadata has unexpected members" % artifact_id)
    media_type = value["media_type"]
    content_encoding = value["content_encoding"]
    if not isinstance(media_type, str) or not MEDIA_TYPE_RE.fullmatch(media_type):
        die("approved artifact %s requires a lowercase IANA media type" % artifact_id)
    if not isinstance(content_encoding, str) or content_encoding != "identity" and not IANA_TOKEN_RE.fullmatch(content_encoding):
        die("approved artifact %s requires a lowercase IANA content encoding" % artifact_id)
    charset = value.get("charset")
    if TEXTUAL_MEDIA_TYPE_RE.match(media_type) and charset is None:
        die("approved textual artifact %s requires a charset" % artifact_id)
    if charset is not None and (not isinstance(charset, str) or not IANA_TOKEN_RE.fullmatch(charset)):
        die("approved artifact %s requires a lowercase IANA charset" % artifact_id)
    format_schema = value.get("format_schema")
    if format_schema is not None:
        if not isinstance(format_schema, dict) or set(format_schema) != {"id", "version", "digest"}:
            die("approved artifact %s has invalid format schema metadata" % artifact_id)
        if not all(isinstance(format_schema[key], str) and format_schema[key] for key in ("id", "version")):
            die("approved artifact %s has incomplete format schema metadata" % artifact_id)
        if not isinstance(format_schema["digest"], str) or not SHA256_RE.fullmatch(format_schema["digest"]):
            die("approved artifact %s has invalid format schema digest" % artifact_id)
    return value


def validate_policy(policy: Any) -> Dict[str, Any]:
    if not isinstance(policy, dict):
        die("policy root must be an object")
    assert_json_domain(policy)
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
    source_ids = set()
    for source in policy["source_decisions"]:
        if not isinstance(source, dict) or set(source) != {"id", "commit"}:
            die("each source decision must contain only id and commit")
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            die("each source decision must carry a stable identifier")
        if source_id in source_ids:
            die("duplicate source decision id: %s" % source_id)
        source_ids.add(source_id)
        commit = source.get("commit")
        if not isinstance(commit, str) or not HEX_COMMIT_RE.fullmatch(commit):
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
        allowed_fields = fields | ({"component_id"} if policy["policy_version"] == "phase0-exact-byte-v1" else set())
        if set(item) - allowed_fields:
            die("artifact has unexpected members: %s" % ", ".join(sorted(set(item) - allowed_fields)))
        identifier = item["id"]
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]+", identifier):
            die("artifact id is invalid: %r" % identifier)
        if identifier in seen:
            die("duplicate artifact id: %s" % identifier)
        seen.add(identifier)
        if policy["policy_version"] == "phase0-exact-byte-v1":
            component_id = item.get("component_id")
            if not isinstance(component_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]+", component_id):
                die("exact-byte artifact %s requires a valid component_id" % identifier)
        if not isinstance(item["required"], bool):
            die("artifact %s required must be a boolean" % identifier)
        if item["admission_status"] not in {"pending-human-review", "approved-for-acquisition", "denied"}:
            die("artifact %s has unknown admission_status" % identifier)
        origin = item["origin"]
        if not isinstance(origin, dict) or set(origin) - {"authority", "revision", "immutable_reference"}:
            die("artifact %s has invalid origin metadata" % identifier)
        if not isinstance(origin.get("authority"), str) or not origin.get("authority"):
            die("artifact %s has no authoritative origin" % identifier)
        if not isinstance(origin.get("revision"), str) or not origin.get("revision"):
            die("artifact %s has no immutable origin revision" % identifier)
        if item["admission_status"] == "approved-for-acquisition":
            immutable_reference = origin.get("immutable_reference")
            if not isinstance(immutable_reference, str) or not IMMUTABLE_REFERENCE_RE.fullmatch(immutable_reference):
                die("approved artifact %s requires an immutable origin reference" % identifier)
        acquisition = item["acquisition"]
        if not isinstance(acquisition, dict):
            die("artifact %s acquisition must be an object" % identifier)
        allowed_acquisition_fields = {"url", "expected", "descriptor"} if item["admission_status"] == "approved-for-acquisition" else {"url"}
        if set(acquisition) - allowed_acquisition_fields:
            die("artifact %s acquisition has unexpected members" % identifier)
        url = acquisition.get("url")
        if item["admission_status"] == "approved-for-acquisition":
            if not isinstance(url, str):
                die("approved artifact %s requires an exact acquisition URL" % identifier)
            validate_url(url, "artifact %s acquisition.url" % identifier)
            expected = acquisition.get("expected")
            if not isinstance(expected, dict):
                die("approved artifact %s requires an expected byte record" % identifier)
            if set(expected) != {"sha256", "byte_length"}:
                die("approved artifact %s expected byte record has unexpected members" % identifier)
            expected_sha256 = expected.get("sha256")
            if not isinstance(expected_sha256, str) or not DIGEST_RE.fullmatch(expected_sha256):
                die("approved artifact %s requires an expected SHA-256" % identifier)
            if type(expected.get("byte_length")) is not int or expected["byte_length"] < 0:
                die("approved artifact %s requires an expected byte_length" % identifier)
            validate_descriptor_metadata(acquisition.get("descriptor"), identifier)
        elif url is not None:
            if not isinstance(url, str):
                die("artifact %s acquisition.url must be a string or null" % identifier)
            validate_url(url, "artifact %s acquisition.url" % identifier)
        license_info = item["license"]
        if not isinstance(license_info, dict) or set(license_info) != {"evidence_class", "review_status"}:
            die("artifact %s license must contain evidence_class and review_status" % identifier)
        evidence_class = license_info.get("evidence_class")
        if not isinstance(evidence_class, str) or not evidence_class or evidence_class == "NOASSERTION":
            die("artifact %s requires a reviewed license evidence class other than NOASSERTION" % identifier)
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
    """Resolve the checkout that contains this harness, never the caller's CWD."""
    result = subprocess.run(
        ["git", "-C", str(SCRIPT_DIRECTORY), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        die("phase0-lock must be stored in a Git worktree")
    return Path(result.stdout.strip()).resolve()


def safe_root(raw_root: str) -> Path:
    root = Path(raw_root).expanduser().resolve()
    checkout = repository_root()
    if root == checkout or checkout in root.parents:
        die("evidence root must be outside the Git worktree: %s" % checkout)
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    ensure_private_directory(root)
    return root


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def download_exact(item: Dict[str, Any], root: Path) -> Dict[str, Any]:
    """Download one already-admitted URL, forbidding redirect and byte surprises."""
    acquisition = item["acquisition"]
    expected = acquisition["expected"]
    descriptor_metadata = acquisition["descriptor"]
    url = acquisition["url"]
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": "docproc-phase0-lock/1"})
    started = utc_now()
    try:
        response = opener.open(request, timeout=60)
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            die("redirect rejected for %s" % item["id"])
        die("download failed for %s: HTTP %d" % (item["id"], exc.code))
    except urllib.error.URLError:
        die("download failed for %s: network error" % item["id"])
    with response:
        final_url = response.geturl()
        if final_url != url:
            die("redirect/final URL mismatch rejected for %s" % item["id"])
        if response.status != 200:
            die("download failed for %s: HTTP %d" % (item["id"], response.status))
        content_length = response.headers.get("Content-Length")
        if content_length is not None and content_length != str(expected["byte_length"]):
            die("Content-Length mismatch for %s" % item["id"])
        response_encoding = response.headers.get("Content-Encoding", "identity").lower()
        if response_encoding != descriptor_metadata["content_encoding"]:
            die("Content-Encoding mismatch for %s" % item["id"])
        ensure_private_directory(root)
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
            ensure_private_tree(root, artifact_path.parent)
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
    write_json_once(root, root / "observations" / (item["id"] + ".json"), observation)
    return observation


def validate_closure(catalog: Dict[str, Any], exact_policy: Dict[str, Any]) -> None:
    if catalog["policy_version"] != "phase0-base-primary-v1":
        die("closure catalog must use phase0-base-primary-v1")
    if exact_policy["policy_version"] != "phase0-exact-byte-v1":
        die("closure input must use phase0-exact-byte-v1")
    catalog_by_id = {item["id"]: item for item in policy_items(catalog)}
    covered = set()
    for item in policy_items(exact_policy):
        component_id = item["component_id"]
        catalog_item = catalog_by_id.get(component_id)
        if catalog_item is None:
            die("exact-byte artifact %s belongs to unapproved component %s" % (item["id"], component_id))
        if catalog_item["required"] and (
            not item["required"] or item["admission_status"] != "approved-for-acquisition"
        ):
            die("required catalog component %s must have a required approved exact-byte record" % component_id)
        covered.add(component_id)
    missing = {item["id"] for item in policy_items(catalog) if item["required"]} - covered
    if missing:
        die("exact-byte policy does not cover required catalog components: %s" % ", ".join(sorted(missing)))


def record_prefetch_failure(root: Path, artifact_id: str) -> None:
    """Retain a failed admitted request without retaining credential or local-path data."""
    failure = {
        "failure_version": "phase0-acquisition-failure-v1",
        "artifact_id": artifact_id,
        "occurred_at_utc": utc_now(),
        "stage": "prefetch",
        "message": "admitted request did not complete byte verification",
        "content_classification": "metadata-only",
        "publication_disposition": "private-only",
    }
    event_name = "sha256-" + sha256_bytes(jcs_bytes(failure)) + ".json"
    write_json_once(root, root / "failures" / event_name, failure)


def prefetch(policy: Dict[str, Any], root: Path) -> None:
    policy = validate_policy(policy)
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
            except (LockError, OSError, UnicodeError) as exc:
                record_prefetch_failure(root, item["id"])
                if isinstance(exc, LockError):
                    raise
                die("prefetch failed for %s: %s" % (item["id"], type(exc).__name__))


def artifact_descriptor(content_digest: str, byte_length: int, metadata: Dict[str, Any]) -> Dict[str, Any]:
    descriptor = {
        "descriptor_version": "docproc-artifact-descriptor-v1",
        "content_digest": content_digest,
        "byte_length": byte_length,
        **metadata,
    }
    address = "art1:sha256:" + sha256_bytes(b"docproc:artifact-descriptor:v1\x00" + jcs_bytes(descriptor))
    return {"address": address, "descriptor": descriptor}


def load_observations(root: Path, policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Load every acquired record and prove it matches its approved policy row."""
    observations: List[Dict[str, Any]] = []
    for item in policy_items(policy):
        if item["required"] and item["admission_status"] != "approved-for-acquisition":
            die("required artifact is not approved for sealing: %s" % item["id"])
        if item["admission_status"] != "approved-for-acquisition":
            continue
        path = root / "observations" / (item["id"] + ".json")
        if not path.is_file():
            die("missing approved acquisition observation: %s" % item["id"])
        observed = load_json(path)
        if not isinstance(observed, dict):
            die("acquisition observation must be an object for %s" % item["id"])
        expected = item["acquisition"]["expected"]
        if (
            observed.get("observation_version") != "phase0-acquisition-observation-v1"
            or observed.get("artifact_id") != item["id"]
            or observed.get("requested_url") != item["acquisition"]["url"]
            or observed.get("final_url") != item["acquisition"]["url"]
            or observed.get("method") != "GET"
            or observed.get("status") != 200
            or observed.get("redirects") != []
            or observed.get("network_result") != "admitted-request-completed"
            or observed.get("content_digest") != "sha256:" + expected["sha256"]
            or observed.get("byte_length") != expected["byte_length"]
        ):
            die("observation does not match approved policy for %s" % item["id"])
        if not isinstance(observed.get("content_type"), str):
            die("observation content_type is invalid for %s" % item["id"])
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


def resolve_schema(schema: Any, root_schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        die("lock-inventory schema constraint must be an object")
    reference = schema.get("$ref")
    if reference is None:
        return schema
    if not isinstance(reference, str) or not reference.startswith("#/$defs/"):
        die("lock-inventory schema has an unsupported reference")
    definition = root_schema.get("$defs", {}).get(reference.removeprefix("#/$defs/"))
    if not isinstance(definition, dict):
        die("lock-inventory schema references an unknown definition")
    return definition


def validate_schema_value(value: Any, schema: Any, root_schema: Dict[str, Any], path: str) -> None:
    """Apply the closed JSON Schema subset used by this pre-dependency harness."""
    constraints = resolve_schema(schema, root_schema)
    all_of = constraints.get("allOf", [])
    if not isinstance(all_of, list):
        die("lock-inventory schema has invalid allOf")
    for item_schema in all_of:
        validate_schema_value(value, item_schema, root_schema, path)
    condition = constraints.get("if")
    if condition is not None:
        try:
            validate_schema_value(value, condition, root_schema, path)
        except LockError:
            pass
        else:
            then_schema = constraints.get("then")
            if then_schema is not None:
                validate_schema_value(value, then_schema, root_schema, path)
    expected_type = constraints.get("type")
    expected_types = {
        "string": lambda candidate: isinstance(candidate, str),
        "array": lambda candidate: isinstance(candidate, list),
        "object": lambda candidate: isinstance(candidate, dict),
        "integer": lambda candidate: type(candidate) is int,
        "boolean": lambda candidate: type(candidate) is bool,
    }
    if expected_type is not None:
        checker = expected_types.get(expected_type)
        if checker is None or not checker(value):
            die("payload member %s does not satisfy schema type" % path)
    if "const" in constraints and value != constraints["const"]:
        die("payload member %s does not satisfy schema const" % path)
    pattern = constraints.get("pattern")
    if pattern is not None:
        if not isinstance(pattern, str) or not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            die("payload member %s does not satisfy schema pattern" % path)
    min_length = constraints.get("minLength")
    if min_length is not None and (type(min_length) is not int or not isinstance(value, str) or len(value) < min_length):
        die("payload member %s does not satisfy schema minLength" % path)
    minimum = constraints.get("minimum")
    if minimum is not None and (type(minimum) is not int or type(value) is not int or value < minimum):
        die("payload member %s does not satisfy schema minimum" % path)
    if isinstance(value, list):
        min_items = constraints.get("minItems")
        if min_items is not None and (type(min_items) is not int or len(value) < min_items):
            die("payload member %s does not satisfy schema minItems" % path)
        item_schema = constraints.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                validate_schema_value(item, item_schema, root_schema, "%s[%d]" % (path, index))
    if isinstance(value, dict):
        properties = constraints.get("properties", {})
        required = constraints.get("required", [])
        if not isinstance(properties, dict) or not isinstance(required, list) or not all(isinstance(name, str) for name in required):
            die("lock-inventory schema has invalid object constraints")
        missing = set(required) - set(value)
        unexpected = set(value) - set(properties)
        if missing:
            die("payload member %s is missing schema members: %s" % (path, ", ".join(sorted(missing))))
        if constraints.get("additionalProperties") is False and unexpected:
            die("payload member %s has unexpected schema members: %s" % (path, ", ".join(sorted(unexpected))))
        for name, member in value.items():
            if name in properties:
                validate_schema_value(member, properties[name], root_schema, "%s.%s" % (path, name))


def validate_lock_inventory_payload(payload: Dict[str, Any], schema: Any) -> None:
    if not isinstance(schema, dict) or schema.get("$id") != "docproc:phase0-lock-inventory-v1":
        die("schema is not phase0-lock-inventory-v1")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        die("lock-inventory schema must be a closed object")
    validate_schema_value(payload, schema, schema, "$")


def seal(policy: Dict[str, Any], root: Path, schema: Path, source_commit: str) -> str:
    policy = validate_policy(policy)
    if policy["policy_version"] != "phase0-exact-byte-v1":
        die("sealing requires a reviewed phase0-exact-byte-v1 policy")
    if not HEX_COMMIT_RE.fullmatch(source_commit):
        die("source commit must be a full lowercase SHA")
    ensure_private_directory(root)
    schema_definition = load_json(schema)
    schema_bytes = schema.read_bytes()
    observations = load_observations(root, policy)
    inventory = []
    for observation in observations:
        item = next(item for item in policy_items(policy) if item["id"] == observation["artifact_id"])
        descriptor = artifact_descriptor(
            observation["content_digest"], observation["byte_length"], item["acquisition"]["descriptor"]
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
    source_decisions = sorted(policy["source_decisions"], key=lambda source: source["id"])
    exceptions = sorted(
        ({"artifact_id": item["id"], "license": item["license"]}
         for item in policy_items(policy)
         if item["license"]["review_status"] == "reviewed-exception"),
        key=lambda row: row["artifact_id"],
    )
    payload = {
        "payload_version": "docproc-evidence-payload-v1",
        "payload_schema_digest": "sha256:" + sha256_bytes(schema_bytes),
        "evidence_id": "EVID-LOCK-INVENTORY-001",
        "kind": "lock-inventory",
        "source_commit": source_commit,
        "policy_digest": "sha256:" + sha256_bytes(jcs_bytes(policy)),
        "source_decisions": source_decisions,
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
        "envelope_version": "docproc:evidence-envelope-v1",
        "evidence_profile": "phase0-admission",
        "payload_address": payload_address,
        "admission_scope": "base-and-primary-candidate-admission",
        "policy_digest": payload["policy_digest"],
        "input_ids": [row["artifact_id"] for row in inventory],
        "environment": {"kind": "phase0-admission", "policy_digest": payload["policy_digest"]},
        "outcome": "go-candidate-pending-human-approval",
        "specification_refs": sorted(source["commit"] for source in source_decisions),
        "artifact_bindings": [{"role": "admitted-artifact", "artifact_address": row["artifact_descriptor"]["address"]} for row in inventory],
        "content_classification": "metadata-only",
        "publication_disposition": "private-only",
    }
    envelope["artifact_bindings"].sort(key=lambda row: (row["role"], row["artifact_address"]))
    evidence_address = "evr1:sha256:" + sha256_bytes(b"docproc:evidence-envelope:v1\x00" + jcs_bytes(envelope))
    envelope["evidence_address"] = evidence_address
    record = root / "records" / evidence_address.replace(":", "_")
    write_json_once(root, record / "payload.json", payload)
    write_json_once(root, record / "envelope.json", envelope)
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
    write_once(root, record / "summary.md", summary)
    print(evidence_address)
    return evidence_address


def validate_phase0_envelope(envelope: Any, payload: Dict[str, Any], expected_bindings: List[Dict[str, str]]) -> None:
    if not isinstance(envelope, dict):
        die("evidence envelope is invalid")
    required = {
        "envelope_version", "evidence_profile", "payload_address", "admission_scope", "policy_digest",
        "input_ids", "environment", "outcome", "specification_refs", "artifact_bindings",
        "content_classification", "publication_disposition", "evidence_address",
    }
    if set(envelope) != required:
        die("evidence envelope has an invalid member set")
    if (
        envelope["envelope_version"] != "docproc:evidence-envelope-v1"
        or envelope["evidence_profile"] != "phase0-admission"
        or envelope["admission_scope"] != "base-and-primary-candidate-admission"
        or envelope["policy_digest"] != payload["policy_digest"]
        or envelope["outcome"] != "go-candidate-pending-human-approval"
        or envelope["content_classification"] != "metadata-only"
        or envelope["publication_disposition"] != "private-only"
        or envelope["environment"] != {"kind": "phase0-admission", "policy_digest": payload["policy_digest"]}
    ):
        die("evidence envelope violates the Phase 0 admission profile")
    expected_ids = [row["artifact_id"] for row in payload["inventory"]]
    expected_refs = sorted(source["commit"] for source in payload["source_decisions"])
    if envelope["input_ids"] != expected_ids or envelope["specification_refs"] != expected_refs:
        die("evidence envelope does not bind the sealed payload inputs")
    if envelope["artifact_bindings"] != expected_bindings:
        die("evidence envelope does not bind the sealed artifact descriptors")


def verify(root: Path, evidence_address: str, schema: Path) -> None:
    if not ADDRESS_RE.fullmatch(evidence_address) or not evidence_address.startswith("evr1:"):
        die("invalid evidence address")
    schema_definition = load_json(schema)
    schema_bytes = schema.read_bytes()
    record = root / "records" / evidence_address.replace(":", "_")
    payload = load_json(record / "payload.json")
    envelope = load_json(record / "envelope.json")
    if not isinstance(payload, dict):
        die("payload is invalid")
    if not isinstance(envelope, dict):
        die("evidence envelope is invalid")
    validate_lock_inventory_payload(payload, schema_definition)
    if payload["payload_schema_digest"] != "sha256:" + sha256_bytes(schema_bytes):
        die("payload schema digest mismatch")
    expected_bindings = []
    inventory = payload["inventory"]
    artifact_ids = [row["artifact_id"] for row in inventory]
    if artifact_ids != sorted(artifact_ids) or len(set(artifact_ids)) != len(artifact_ids):
        die("payload inventory is not sorted by unique artifact id")
    for row in inventory:
        observation = row["observation"]
        descriptor_record = row["artifact_descriptor"]
        descriptor = descriptor_record["descriptor"]
        metadata = {key: value for key, value in descriptor.items() if key not in {
            "descriptor_version", "content_digest", "byte_length"
        }}
        if (
            descriptor["descriptor_version"] != "docproc-artifact-descriptor-v1"
            or descriptor["content_digest"] != observation["content_digest"]
            or descriptor["byte_length"] != observation["byte_length"]
        ):
            die("artifact descriptor does not match its observation")
        validate_descriptor_metadata(metadata, row["artifact_id"])
        calculated_descriptor = artifact_descriptor(
            descriptor["content_digest"], descriptor["byte_length"], metadata
        )
        if descriptor_record["address"] != calculated_descriptor["address"]:
            die("artifact descriptor address mismatch")
        expected_bindings.append({"role": "admitted-artifact", "artifact_address": calculated_descriptor["address"]})
        artifact = root / "artifacts" / ("sha256-" + observation["content_digest"].removeprefix("sha256:"))
        if not artifact.is_file():
            die("missing content-addressed artifact for %s" % row["artifact_id"])
        try:
            digest, length = sha256_file(artifact)
        except OSError as exc:
            die("cannot read content-addressed artifact for %s: %s" % (row["artifact_id"], type(exc).__name__))
        if "sha256:" + digest != observation["content_digest"] or length != observation["byte_length"]:
            die("content-addressed artifact does not match sealed inventory for %s" % row["artifact_id"])
    expected_bindings.sort(key=lambda row: (row["role"], row["artifact_address"]))
    payload_address = "evp1:sha256:" + sha256_bytes(b"docproc:evidence-payload:v1\x00" + jcs_bytes(payload))
    if payload_address != envelope.get("payload_address"):
        die("payload address mismatch")
    validate_phase0_envelope(envelope, payload, expected_bindings)
    supplied = envelope["evidence_address"]
    unsigned_envelope = {key: value for key, value in envelope.items() if key != "evidence_address"}
    calculated = "evr1:sha256:" + sha256_bytes(b"docproc:evidence-envelope:v1\x00" + jcs_bytes(unsigned_envelope))
    if supplied != calculated or supplied != evidence_address:
        die("evidence address mismatch")


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
    verify_cmd.add_argument("--schema", type=Path, required=True)
    verify_cmd.add_argument("--evidence-address", required=True)
    host_cmd = sub.add_parser("capture-host-baseline")
    host_cmd.add_argument("--root", required=True, help="private evidence root outside this Git worktree")
    args = parser.parse_args(argv)
    try:
        if args.command == "capture-host-baseline":
            root = safe_root(args.root)
            write_json_once(root, root / "host-baseline.json", host_record())
        elif args.command == "verify":
            verify(safe_root(args.root), args.evidence_address, args.schema)
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
