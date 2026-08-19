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
import secrets
import shutil
import sqlite3
import stat
import subprocess
import sys
import time
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
LICENSE_EVIDENCE_ROLES = {"license-text", "copyright", "notice", "metadata", "review-record"}
COPYRIGHT_NOTICE_STATUSES = {"present", "reviewed-not-present"}
SCRIPT_DIRECTORY = Path(__file__).resolve().parent


class LockError(RuntimeError):
    """An invalid policy, observation, or evidence record."""


class SchemaValueMismatch(LockError):
    """A candidate value did not satisfy a valid schema constraint."""


class ReviewedControls:
    """Independently retained identities for every admission-review control."""

    def __init__(
        self, catalog_digest: str, policy_file_digest: str, schema_digest: str,
        host_baseline_digest: str, producer_commit: str,
    ):
        digests = {
            "catalog_digest": catalog_digest,
            "policy_file_digest": policy_file_digest,
            "schema_digest": schema_digest,
            "host_baseline_digest": host_baseline_digest,
        }
        for name, digest in digests.items():
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                die("reviewed control %s is not an exact SHA-256" % name)
        if not isinstance(producer_commit, str) or not HEX_COMMIT_RE.fullmatch(producer_commit):
            die("reviewed producer commit must be a full lowercase SHA")
        self.catalog_digest = catalog_digest
        self.policy_file_digest = policy_file_digest
        self.schema_digest = schema_digest
        self.host_baseline_digest = host_baseline_digest
        self.producer_commit = producer_commit

    def record(self) -> Dict[str, str]:
        return {
            "catalog_digest": self.catalog_digest,
            "policy_file_digest": self.policy_file_digest,
            "schema_digest": self.schema_digest,
            "host_baseline_digest": self.host_baseline_digest,
            "producer_commit": self.producer_commit,
        }


class PrivateRoot:
    """One private evidence root pinned by an open directory descriptor."""

    def __init__(self, path: Path, descriptor: int):
        self.path = path
        self.descriptor = descriptor

    def __truediv__(self, child: str) -> Path:
        return self.path / child

    def stat(self) -> os.stat_result:
        return os.fstat(self.descriptor)

    def close(self) -> None:
        if self.descriptor >= 0:
            os.close(self.descriptor)
            self.descriptor = -1

    def __enter__(self) -> "PrivateRoot":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except OSError:
            pass


def die(message: str) -> NoReturn:
    raise LockError(message)


def schema_mismatch(message: str) -> NoReturn:
    raise SchemaValueMismatch(message)


def no_duplicate_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            die("duplicate JSON object member: %s" % key)
        result[key] = value
    return result


def read_regular_bytes(path: Path, context: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            die("%s must be a regular file" % context)
        with os.fdopen(descriptor, "rb") as handle:
            return handle.read()
    except LockError:
        try:
            os.close(descriptor)
        except (NameError, OSError):
            pass
        raise
    except OSError as exc:
        try:
            os.close(descriptor)
        except (NameError, OSError):
            pass
        die("cannot read %s: %s" % (context, type(exc).__name__))


def parse_json_bytes(data: bytes, context: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicate_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        die("cannot decode %s: %s" % (context, type(exc).__name__))


def load_json(path: Path) -> Any:
    return parse_json_bytes(read_regular_bytes(path, "JSON document"), "JSON document")


def load_reviewed_json_document(path: Path, expected_digest: str | None, context: str) -> Tuple[Any, bytes]:
    data = read_regular_bytes(path, "reviewed %s" % context)
    observed_digest = "sha256:" + sha256_bytes(data)
    if expected_digest is not None:
        if not SHA256_RE.fullmatch(expected_digest):
            die("reviewed %s digest must be sha256:<64 lowercase hex>" % context)
        if observed_digest != expected_digest:
            die("reviewed %s digest mismatch" % context)
    return parse_json_bytes(data, "reviewed %s" % context), data


def load_reviewed_json(path: Path, expected_digest: str, context: str) -> Any:
    value, _ = load_reviewed_json_document(path, expected_digest, context)
    return value


def parse_private_json(data: bytes, context: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicate_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        die("cannot decode %s: %s" % (context, type(exc).__name__))


def read_schema_bytes(path: Path) -> bytes:
    """Read schema bytes while keeping local paths out of bounded failures."""
    try:
        return path.read_bytes()
    except OSError as exc:
        die("cannot read schema bytes: %s" % type(exc).__name__)


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


def validate_private_stat(
    info: os.stat_result, context: str, expected_type: str, require_single_link: bool = True
) -> None:
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        die("%s must be owned and accessible only by this user" % context)
    if expected_type == "directory" and not stat.S_ISDIR(info.st_mode):
        die("%s must be a regular private directory" % context)
    if expected_type == "file" and (
        not stat.S_ISREG(info.st_mode) or require_single_link and info.st_nlink != 1
    ):
        die("%s must be a singly linked regular private file" % context)


def private_root_path(root: Path | PrivateRoot) -> Path:
    return root.path if isinstance(root, PrivateRoot) else root


def open_absolute_private_root(path: Path, create: bool) -> int:
    """Open a root once by walking from / without following any path component."""
    path = path.resolve()
    if not path.is_absolute() or any(not hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")):
        die("private evidence root requires absolute no-follow directory access")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    descriptors = []
    try:
        current = os.open("/", flags)
        descriptors.append(current)
        for part in path.parts[1:]:
            try:
                next_descriptor = os.open(part, flags, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, mode=0o700, dir_fd=current)
                except FileExistsError:
                    pass
                next_descriptor = os.open(part, flags, dir_fd=current)
            current = next_descriptor
            descriptors.append(current)
        result = descriptors.pop()
        validate_private_stat(os.fstat(result), "private evidence root", "directory")
        return result
    except LockError:
        raise
    except OSError as exc:
        die("cannot open private evidence root: %s" % type(exc).__name__)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def duplicate_private_root_descriptor(root: Path | PrivateRoot) -> int:
    if isinstance(root, PrivateRoot):
        if root.descriptor < 0:
            die("private evidence root is closed")
        descriptor = os.dup(root.descriptor)
        validate_private_stat(os.fstat(descriptor), "private evidence root", "directory")
        return descriptor
    return open_absolute_private_root(root, create=False)


def open_private_directory_descriptor(
    root: Path | PrivateRoot, directory: Path, context: str, missing_ok: bool = False
) -> int | None:
    """Open one private directory by walking no-follow descriptors from root."""
    try:
        relative = directory.relative_to(private_root_path(root))
    except ValueError:
        die("%s escapes the private evidence root" % context)
    if any(not hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")):
        die("descriptor-bound private access is unavailable on this platform")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    descriptors = []
    try:
        current = duplicate_private_root_descriptor(root)
        descriptors.append(current)
        validate_private_stat(os.fstat(current), context + " root", "directory")
        for part in relative.parts:
            try:
                current = os.open(part, flags, dir_fd=current)
            except FileNotFoundError:
                if missing_ok:
                    return None
                raise
            descriptors.append(current)
            validate_private_stat(os.fstat(current), context, "directory")
        result = descriptors.pop()
        return result
    except LockError:
        raise
    except OSError as exc:
        die("cannot open %s: %s" % (context, type(exc).__name__))
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def open_private_directory_at(
    root_descriptor: int, parts: Tuple[str, ...], context: str, create: bool = False
) -> int:
    """Walk from an already pinned root descriptor, optionally creating parents."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    descriptors = [os.dup(root_descriptor)]
    try:
        validate_private_stat(os.fstat(descriptors[0]), context + " root", "directory")
        current = descriptors[0]
        for part in parts:
            try:
                next_descriptor = os.open(part, flags, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, mode=0o700, dir_fd=current)
                except FileExistsError:
                    pass
                next_descriptor = os.open(part, flags, dir_fd=current)
            current = next_descriptor
            descriptors.append(current)
            validate_private_stat(os.fstat(current), context, "directory")
        result = descriptors.pop()
        return result
    except LockError:
        raise
    except OSError as exc:
        die("cannot open %s: %s" % (context, type(exc).__name__))
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def open_or_create_private_directory_descriptor(
    root: Path | PrivateRoot, directory: Path, context: str
) -> int:
    """Create and open a private directory tree through pinned parent descriptors."""
    try:
        relative = directory.relative_to(private_root_path(root))
    except ValueError:
        die("%s escapes the private evidence root" % context)
    root_descriptor = open_private_directory_descriptor(
        root, private_root_path(root), context + " root"
    )
    assert root_descriptor is not None
    try:
        return open_private_directory_at(root_descriptor, relative.parts, context, create=True)
    finally:
        os.close(root_descriptor)


def open_private_file_descriptor(
    root: Path | PrivateRoot, path: Path, context: str, require_single_link: bool = True
) -> int:
    """Open and validate one private file through no-follow directory descriptors."""
    try:
        relative = path.relative_to(private_root_path(root))
    except ValueError:
        die("%s escapes the private evidence root" % context)
    if not relative.parts:
        die("%s does not name a private file" % context)
    parent = open_private_directory_descriptor(root, path.parent, context + " parent")
    assert parent is not None
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(relative.parts[-1], flags, dir_fd=parent)
        try:
            validate_private_stat(
                os.fstat(descriptor), context, "file", require_single_link=require_single_link
            )
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor
    except LockError:
        raise
    except OSError as exc:
        die("cannot open %s: %s" % (context, type(exc).__name__))
    finally:
        os.close(parent)


def open_private_file_at(
    directory_descriptor: int, name: str, context: str, require_single_link: bool = True
) -> int:
    if not name or "/" in name or name in {".", ".."}:
        die("%s has an invalid private filename" % context)
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=directory_descriptor)
        validate_private_stat(
            os.fstat(descriptor), context, "file", require_single_link=require_single_link
        )
        return descriptor
    except LockError:
        try:
            os.close(descriptor)
        except (NameError, OSError):
            pass
        raise
    except OSError as exc:
        try:
            os.close(descriptor)
        except (NameError, OSError):
            pass
        die("cannot open %s: %s" % (context, type(exc).__name__))


def read_private_file_at(directory_descriptor: int, name: str, context: str) -> bytes:
    descriptor = open_private_file_at(directory_descriptor, name, context)
    try:
        with os.fdopen(descriptor, "rb") as handle:
            return handle.read()
    except OSError as exc:
        die("cannot read %s: %s" % (context, type(exc).__name__))


def sha256_private_file_at(directory_descriptor: int, name: str, context: str) -> Tuple[str, int]:
    descriptor = open_private_file_at(directory_descriptor, name, context)
    digest = hashlib.sha256()
    length = 0
    try:
        with os.fdopen(descriptor, "rb") as handle:
            while True:
                block = handle.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
                length += len(block)
    except OSError as exc:
        die("cannot read %s: %s" % (context, type(exc).__name__))
    return digest.hexdigest(), length


def read_private_bytes(root: Path | PrivateRoot, path: Path, context: str) -> bytes:
    descriptor = open_private_file_descriptor(root, path, context)
    try:
        with os.fdopen(descriptor, "rb") as handle:
            return handle.read()
    except OSError as exc:
        die("cannot read %s: %s" % (context, type(exc).__name__))


def load_private_json(root: Path | PrivateRoot, path: Path, context: str) -> Any:
    return parse_private_json(read_private_bytes(root, path, context), context)


def sha256_private_file(root: Path | PrivateRoot, path: Path, context: str) -> Tuple[str, int]:
    descriptor = open_private_file_descriptor(root, path, context)
    digest = hashlib.sha256()
    length = 0
    try:
        with os.fdopen(descriptor, "rb") as handle:
            while True:
                block = handle.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
                length += len(block)
    except OSError as exc:
        die("cannot read %s: %s" % (context, type(exc).__name__))
    return digest.hexdigest(), length


def write_once(root: Path | PrivateRoot, path: Path, data: bytes) -> None:
    """Create private content once through a pinned parent, or prove equality."""
    try:
        relative = path.relative_to(private_root_path(root))
    except ValueError:
        die("immutable private evidence escapes its root")
    if not relative.parts:
        die("immutable private evidence does not name a file")
    parent = open_or_create_private_directory_descriptor(
        root, path.parent, "immutable private evidence parent"
    )
    flags = (
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        try:
            descriptor = os.open(relative.parts[-1], flags, 0o600, dir_fd=parent)
        except FileExistsError:
            if read_private_file_at(parent, relative.parts[-1], "immutable private evidence") != data:
                die("immutable private evidence already contains different bytes")
        else:
            try:
                validate_private_stat(os.fstat(descriptor), "immutable private evidence", "file")
            except BaseException:
                os.close(descriptor)
                raise
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
    except LockError:
        raise
    except OSError as exc:
        die("cannot write immutable private evidence: %s" % type(exc).__name__)
    finally:
        os.close(parent)


def write_json_once(root: Path | PrivateRoot, path: Path, value: Any) -> None:
    write_once(root, path, jcs_bytes(value) + b"\n")


def validate_host_baseline(record: Any) -> Dict[str, Any]:
    required = {
        "record_version", "recorded_at_utc", "monotonic_ns", "clock_source", "platform",
        "machine", "platform_records", "python", "executables", "publication_disposition",
    }
    if not isinstance(record, dict) or set(record) != required:
        die("host baseline has an invalid member set")
    assert_json_domain(record)
    if record["record_version"] != "phase0-host-baseline-v1":
        die("host baseline has an invalid version")
    if not isinstance(record["recorded_at_utc"], str) or not record["recorded_at_utc"].endswith("Z"):
        die("host baseline has an invalid UTC timestamp")
    if not isinstance(record["monotonic_ns"], str) or not record["monotonic_ns"].isdigit():
        die("host baseline has an invalid monotonic clock observation")
    for field in ("clock_source", "platform", "machine"):
        if not isinstance(record[field], str) or not record[field]:
            die("host baseline has an invalid %s" % field)
    if record["machine"] != "arm64":
        die("host baseline is not the required arm64 machine")
    if not isinstance(record["platform_records"], dict) or set(record["platform_records"]) != {
        "sw_vers", "cpu_brand", "memory_bytes",
    }:
        die("host baseline has invalid platform records")
    for platform_record in record["platform_records"].values():
        if not isinstance(platform_record, dict):
            die("host baseline has invalid platform observations")
        status = platform_record.get("status")
        if status == "unavailable":
            if set(platform_record) != {"status", "detail"} or not isinstance(platform_record["detail"], str):
                die("host baseline has an invalid unavailable platform observation")
        elif status in {"observed", "failed"}:
            if (
                set(platform_record) != {"status", "exit_code", "output"}
                or type(platform_record["exit_code"]) is not int
                or not isinstance(platform_record["output"], str)
            ):
                die("host baseline has an invalid platform command observation")
        else:
            die("host baseline has an unknown platform observation status")
    python_record = record["python"]
    if not isinstance(python_record, dict) or set(python_record) != {"version", "sqlite_runtime"} or not all(
        isinstance(value, str) and value for value in python_record.values()
    ):
        die("host baseline has an invalid Python/SQLite record")
    executable_names = ["uv", "docker", "docker-compose", "qpdf", "ollama"]
    if (
        not isinstance(record["executables"], list)
        or [item.get("name") for item in record["executables"] if isinstance(item, dict)] != executable_names
    ):
        die("host baseline must contain every fixed executable record")
    for executable in record["executables"]:
        if set(executable) == {"name", "sha256", "byte_length"}:
            if (
                not isinstance(executable["sha256"], str)
                or not SHA256_RE.fullmatch(executable["sha256"])
                or type(executable["byte_length"]) is not int
                or executable["byte_length"] < 0
            ):
                die("host baseline has an invalid executable digest record")
        elif executable.get("status") == "not-present" and set(executable) == {"name", "status"}:
            pass
        elif executable.get("status") == "unavailable" and set(executable) == {"name", "status", "detail"}:
            if not isinstance(executable["detail"], str):
                die("host baseline has an invalid unavailable executable record")
        else:
            die("host baseline has an invalid executable record")
    if record["publication_disposition"] != "private-only":
        die("host baseline must remain private-only")
    return record


def load_host_baseline(root: Path | PrivateRoot, expected_digest: str | None = None) -> Dict[str, str]:
    """Bind sealing to the exact private host baseline bytes."""
    path = root / "host-baseline.json"
    data = read_private_bytes(root, path, "host baseline")
    record = validate_host_baseline(parse_private_json(data, "host baseline"))
    if data != jcs_bytes(record) + b"\n":
        die("host baseline must use canonical JSON bytes")
    content_digest = "sha256:" + sha256_bytes(data)
    if expected_digest is not None:
        if not SHA256_RE.fullmatch(expected_digest):
            die("reviewed host baseline digest must be sha256:<64 lowercase hex>")
        if content_digest != expected_digest:
            die("reviewed host baseline digest mismatch")
    return {
        "kind": "phase0-host-baseline-v1",
        "content_digest": content_digest,
    }


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


def validate_license_info(value: Any, artifact_id: str, require_complete: bool) -> Dict[str, Any]:
    base_fields = {"evidence_class", "review_status"}
    complete_fields = base_fields | {
        "license_expression", "copyright_status", "notice_status", "evidence_refs",
    }
    if not isinstance(value, dict) or not base_fields <= set(value) or set(value) - complete_fields:
        die("artifact %s license has an invalid member set" % artifact_id)
    evidence_class = value.get("evidence_class")
    if not isinstance(evidence_class, str) or not evidence_class or evidence_class == "NOASSERTION":
        die("artifact %s requires a reviewed license evidence class other than NOASSERTION" % artifact_id)
    review_status = value.get("review_status")
    if review_status not in {"pending-human-review", "reviewed", "reviewed-exception"}:
        die("artifact %s has no valid license review status" % artifact_id)
    if require_complete and set(value) != complete_fields:
        die("approved artifact %s requires complete license evidence" % artifact_id)
    if set(value) == base_fields:
        return value
    if set(value) != complete_fields:
        die("artifact %s license evidence is incomplete" % artifact_id)
    expression = value["license_expression"]
    if not isinstance(expression, str) or not expression or "NOASSERTION" in expression.upper():
        die("artifact %s requires a reviewed license expression other than NOASSERTION" % artifact_id)
    if value["copyright_status"] not in COPYRIGHT_NOTICE_STATUSES:
        die("artifact %s has no reviewed copyright status" % artifact_id)
    if value["notice_status"] not in COPYRIGHT_NOTICE_STATUSES:
        die("artifact %s has no reviewed notice status" % artifact_id)
    refs = value["evidence_refs"]
    if not isinstance(refs, list) or not refs:
        die("artifact %s requires complete license evidence references" % artifact_id)
    identities = []
    roles = set()
    for ref in refs:
        if not isinstance(ref, dict) or set(ref) != {"role", "artifact_id", "content_digest"}:
            die("artifact %s has an invalid license evidence reference" % artifact_id)
        role = ref.get("role")
        referenced_id = ref.get("artifact_id")
        digest = ref.get("content_digest")
        if role not in LICENSE_EVIDENCE_ROLES:
            die("artifact %s has an unknown license evidence role" % artifact_id)
        if not isinstance(referenced_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]+", referenced_id):
            die("artifact %s has an invalid license evidence artifact id" % artifact_id)
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            die("artifact %s has an invalid license evidence digest" % artifact_id)
        identities.append((role, referenced_id, digest))
        roles.add(role)
    if identities != sorted(set(identities)):
        die("artifact %s license evidence references must be sorted and unique" % artifact_id)
    if review_status == "reviewed" and "license-text" not in roles:
        die("reviewed artifact %s requires exact license-text evidence" % artifact_id)
    if review_status == "reviewed-exception" and (
        "review-record" not in roles or not roles.intersection({"license-text", "metadata"})
    ):
        die("reviewed exception %s requires metadata/license and review-record evidence" % artifact_id)
    if value["copyright_status"] == "present" and "copyright" not in roles:
        die("artifact %s requires copyright evidence" % artifact_id)
    if value["notice_status"] == "present" and "notice" not in roles:
        die("artifact %s requires notice evidence" % artifact_id)
    return value


def validate_origin_references(policy: Dict[str, Any]) -> None:
    """Bind Git revisions to exact, role-typed provenance bytes."""
    items = {item["id"]: item for item in policy_items(policy)}
    for item in items.values():
        if item["admission_status"] != "approved-for-acquisition":
            continue
        reference = item["origin"]["immutable_reference"]
        if not reference.startswith("git:"):
            continue
        provenance = item["origin"]["provenance"]
        target = items.get(provenance["artifact_id"])
        if (
            target is None
            or target["admission_status"] != "approved-for-acquisition"
            or target["component_id"] != item["component_id"]
            or target["kind"] != "origin-provenance"
            or provenance["content_digest"] != "sha256:" + target["acquisition"]["expected"]["sha256"]
        ):
            die("artifact %s Git provenance is not a matching approved exact byte" % item["id"])
        descriptor = target["acquisition"]["descriptor"]
        if descriptor["content_encoding"] != "identity" or not TEXTUAL_MEDIA_TYPE_RE.match(descriptor["media_type"]):
            die("artifact %s Git provenance must be textual identity-encoded evidence" % item["id"])


def validate_license_references(policy: Dict[str, Any]) -> None:
    """Bind every approved license/notice reference to a role-typed exact byte."""
    role_kinds = {
        "license-text": "license-text",
        "copyright": "copyright-evidence",
        "notice": "notice",
        "metadata": "license-metadata",
        "review-record": "license-review-record",
    }
    items = {item["id"]: item for item in policy_items(policy)}
    for item in items.values():
        if item["admission_status"] != "approved-for-acquisition":
            continue
        for ref in item["license"]["evidence_refs"]:
            target = items.get(ref["artifact_id"])
            if target is None or target["admission_status"] != "approved-for-acquisition":
                die("artifact %s license evidence is not an approved exact byte" % item["id"])
            expected = target["acquisition"].get("expected")
            descriptor = target["acquisition"].get("descriptor")
            if (
                target["component_id"] != item["component_id"]
                or target["kind"] != role_kinds[ref["role"]]
                or not isinstance(expected, dict)
                or ref["content_digest"] != "sha256:" + expected.get("sha256", "")
                or not isinstance(descriptor, dict)
                or descriptor.get("content_encoding") != "identity"
                or not TEXTUAL_MEDIA_TYPE_RE.match(descriptor.get("media_type", ""))
            ):
                die("artifact %s license evidence is not a role-compatible textual exact byte" % item["id"])


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
    unexpected = set(policy) - required
    if unexpected:
        die("policy has unexpected members: %s" % ", ".join(sorted(unexpected)))
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
        if not isinstance(origin, dict) or set(origin) - {"authority", "revision", "immutable_reference", "provenance"}:
            die("artifact %s has invalid origin metadata" % identifier)
        if not isinstance(origin.get("authority"), str) or not origin.get("authority"):
            die("artifact %s has no authoritative origin" % identifier)
        if not isinstance(origin.get("revision"), str) or not origin.get("revision"):
            die("artifact %s has no immutable origin revision" % identifier)
        if item["admission_status"] == "approved-for-acquisition":
            immutable_reference = origin.get("immutable_reference")
            if not isinstance(immutable_reference, str) or not IMMUTABLE_REFERENCE_RE.fullmatch(immutable_reference):
                die("approved artifact %s requires an immutable origin reference" % identifier)
            provenance = origin.get("provenance")
            if immutable_reference.startswith("git:"):
                if not isinstance(provenance, dict) or set(provenance) != {"artifact_id", "content_digest"}:
                    die("approved artifact %s Git origin requires provenance evidence" % identifier)
                if (
                    not isinstance(provenance["artifact_id"], str)
                    or not re.fullmatch(r"[a-z0-9][a-z0-9.-]+", provenance["artifact_id"])
                    or not isinstance(provenance["content_digest"], str)
                    or not SHA256_RE.fullmatch(provenance["content_digest"])
                ):
                    die("approved artifact %s has invalid Git provenance evidence" % identifier)
            elif provenance is not None:
                die("approved SHA-256 artifact %s must not carry Git provenance evidence" % identifier)
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
            if origin["immutable_reference"].startswith("sha256:") and origin["immutable_reference"] != "sha256:" + expected_sha256:
                die("approved artifact %s SHA-256 origin reference does not identify the acquired bytes" % identifier)
            validate_descriptor_metadata(acquisition.get("descriptor"), identifier)
        elif url is not None:
            if not isinstance(url, str):
                die("artifact %s acquisition.url must be a string or null" % identifier)
            validate_url(url, "artifact %s acquisition.url" % identifier)
        license_info = validate_license_info(
            item["license"], identifier, item["admission_status"] == "approved-for-acquisition"
        )
        if item["admission_status"] == "approved-for-acquisition" and license_info["review_status"] == "pending-human-review":
            die("approved artifact %s still has pending license review" % identifier)
        if item["distribution_mode"] not in {"source-only", "direct-upstream-pull", "host-installed", "manual-data-acquisition"}:
            die("artifact %s has an unapproved distribution mode" % identifier)
        if item["publication_disposition"] not in {"metadata-only", "do-not-publish", "private-only"}:
            die("artifact %s has an invalid publication disposition" % identifier)
    if policy["policy_version"] == "phase0-exact-byte-v1":
        validate_origin_references(policy)
        validate_license_references(policy)
    return policy


def repository_root() -> Path:
    """Resolve the checkout containing this harness without executing ambient Git."""
    for candidate in (SCRIPT_DIRECTORY, *SCRIPT_DIRECTORY.parents):
        marker = candidate / ".git"
        try:
            info = marker.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            die("cannot inspect harness Git boundary: %s" % type(exc).__name__)
        if stat.S_ISLNK(info.st_mode) or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
            die("harness Git boundary is not a regular directory or gitfile")
        return candidate.resolve()
    die("phase0-lock must be stored in a Git worktree")


def safe_root(raw_root: str) -> PrivateRoot:
    root = Path(raw_root).expanduser().resolve()
    checkout = repository_root()
    if root == checkout or checkout in root.parents:
        die("evidence root must be outside the Git worktree: %s" % checkout)
    descriptor = open_absolute_private_root(root, create=True)
    return PrivateRoot(root, descriptor)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def create_private_temporary_at(root_descriptor: int, prefix: str) -> Tuple[int, str]:
    """Create an owner-only temporary file relative to a pinned evidence root."""
    flags = (
        os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    for _ in range(128):
        name = prefix + secrets.token_hex(16)
        try:
            descriptor = os.open(name, flags, 0o600, dir_fd=root_descriptor)
        except FileExistsError:
            continue
        try:
            validate_private_stat(os.fstat(descriptor), "secure temporary artifact", "file")
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor, name
    die("cannot allocate a unique secure temporary artifact")


def install_artifact_once_at(
    root_descriptor: int, temporary_name: str, source_descriptor: int, artifact_name: str,
    item_id: str, observed: str, length: int
) -> None:
    """Install an artifact using only names relative to one pinned private root."""
    artifacts_descriptor = open_private_directory_at(
        root_descriptor, ("artifacts",), "content-addressed artifact directory", create=True
    )
    try:
        try:
            os.link(
                temporary_name, artifact_name,
                src_dir_fd=root_descriptor, dst_dir_fd=artifacts_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError:
            existing_digest, existing_length = sha256_private_file_at(
                artifacts_descriptor, artifact_name,
                "existing content-addressed artifact for %s" % item_id,
            )
            if existing_digest != observed or existing_length != length:
                die("content-addressed artifact collision for %s at sha256-%s" % (item_id, observed))
            os.unlink(temporary_name, dir_fd=root_descriptor)
            return
        installed_descriptor = open_private_file_at(
            artifacts_descriptor, artifact_name,
            "installed content-addressed artifact for %s" % item_id,
            require_single_link=False,
        )
        try:
            source_info = os.fstat(source_descriptor)
            installed_info = os.fstat(installed_descriptor)
            if (installed_info.st_dev, installed_info.st_ino) != (source_info.st_dev, source_info.st_ino):
                die("secure temporary artifact changed before installation for %s" % item_id)
            os.unlink(temporary_name, dir_fd=root_descriptor)
            if os.fstat(installed_descriptor).st_nlink != 1:
                die("installed content-addressed artifact for %s has unexpected links" % item_id)
        finally:
            os.close(installed_descriptor)
    finally:
        os.close(artifacts_descriptor)


def install_artifact_once(
    root: Path | PrivateRoot, temporary: Path, source_descriptor: int, artifact_path: Path,
    item_id: str, observed: str, length: int
) -> None:
    """Atomically install an immutable artifact without pathname-based parent reuse."""
    try:
        temporary_relative = temporary.relative_to(private_root_path(root))
        artifact_relative = artifact_path.relative_to(private_root_path(root))
    except ValueError:
        die("artifact installation path escapes the private evidence root")
    if len(temporary_relative.parts) != 1 or artifact_relative.parts != (
        "artifacts", "sha256-" + observed,
    ):
        die("artifact installation paths do not match the content-addressed layout")
    root_descriptor = open_private_directory_descriptor(root, root, "artifact installation root")
    assert root_descriptor is not None
    try:
        install_artifact_once_at(
            root_descriptor, temporary_relative.parts[0], source_descriptor,
            artifact_relative.parts[-1], item_id, observed, length,
        )
    finally:
        os.close(root_descriptor)


def download_exact(item: Dict[str, Any], root: Path | PrivateRoot) -> Dict[str, Any]:
    """Download one already-approved candidate URL, forbidding byte surprises."""
    acquisition = item["acquisition"]
    expected = acquisition["expected"]
    descriptor_metadata = acquisition["descriptor"]
    url = acquisition["url"]
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
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
        root_descriptor = open_private_directory_descriptor(root, root, "download evidence root")
        assert root_descriptor is not None
        file_descriptor, temporary_name = create_private_temporary_at(root_descriptor, "prefetch-")
        try:
            digest = hashlib.sha256()
            length = 0
            try:
                destination = os.fdopen(file_descriptor, "wb")
            except OSError:
                os.close(file_descriptor)
                raise
            with destination:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    length += len(chunk)
                    if length > expected["byte_length"]:
                        die("response exceeds approved byte_length for %s" % item["id"])
                    destination.write(chunk)
                    digest.update(chunk)
                destination.flush()
                os.fsync(destination.fileno())
                observed = digest.hexdigest()
                if observed != expected["sha256"] or length != expected["byte_length"]:
                    die("byte identity mismatch for %s (got %s / %d)" % (item["id"], observed, length))
                install_artifact_once_at(
                    root_descriptor, temporary_name, destination.fileno(), "sha256-%s" % observed,
                    item["id"], observed, length,
                )
        finally:
            try:
                os.unlink(temporary_name, dir_fd=root_descriptor)
            except FileNotFoundError:
                pass
            os.close(root_descriptor)
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
        "network_result": "harness-recorded-request-completed-unauthenticated",
    }
    write_json_once(root, root / "observations" / (item["id"] + ".json"), observation)
    return observation


def validate_closure(catalog: Dict[str, Any], exact_policy: Dict[str, Any]) -> None:
    if catalog["policy_version"] != "phase0-base-primary-v1":
        die("closure catalog must use phase0-base-primary-v1")
    if exact_policy["policy_version"] != "phase0-exact-byte-v1":
        die("closure input must use phase0-exact-byte-v1")
    catalog_sources = {source["id"]: source["commit"] for source in catalog["source_decisions"]}
    exact_sources = {source["id"]: source["commit"] for source in exact_policy["source_decisions"]}
    changed_sources = {
        source_id for source_id, commit in catalog_sources.items()
        if exact_sources.get(source_id) != commit
    }
    if changed_sources:
        die("exact-byte policy does not preserve catalog source decisions: %s" % ", ".join(sorted(changed_sources)))
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


def record_prefetch_failure(root: Path | PrivateRoot, artifact_id: str) -> None:
    """Retain a failed candidate request without credential or local-path data."""
    failure = {
        "failure_version": "phase0-acquisition-failure-v1",
        "artifact_id": artifact_id,
        "occurred_at_utc": utc_now(),
        "stage": "prefetch",
        "message": "candidate request did not complete byte verification",
        "content_classification": "metadata-only",
        "publication_disposition": "private-only",
    }
    event_name = "sha256-" + sha256_bytes(jcs_bytes(failure)) + ".json"
    write_json_once(root, root / "failures" / event_name, failure)


def prefetch(policy: Dict[str, Any], root: Path | PrivateRoot) -> None:
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


def load_observations(root: Path | PrivateRoot, policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Load every acquired record and prove it matches its approved policy row."""
    observations: List[Dict[str, Any]] = []
    for item in policy_items(policy):
        if item["required"] and item["admission_status"] != "approved-for-acquisition":
            die("required artifact is not approved for sealing: %s" % item["id"])
        if item["admission_status"] != "approved-for-acquisition":
            continue
        path = root / "observations" / (item["id"] + ".json")
        observed = load_private_json(root, path, "acquisition observation for %s" % item["id"])
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
            or observed.get("network_result") != "harness-recorded-request-completed-unauthenticated"
            or observed.get("content_digest") != "sha256:" + expected["sha256"]
            or observed.get("byte_length") != expected["byte_length"]
        ):
            die("observation does not match approved policy for %s" % item["id"])
        if not isinstance(observed.get("content_type"), str):
            die("observation content_type is invalid for %s" % item["id"])
        artifact = root / "artifacts" / ("sha256-" + expected["sha256"])
        digest, length = sha256_private_file(
            root, artifact, "content-addressed artifact for %s" % item["id"]
        )
        if digest != expected["sha256"] or length != expected["byte_length"]:
            die("content-addressed file does not match observation for %s" % item["id"])
        observations.append(observed)
    return observations


def validate_git_provenance_records(
    policy: Dict[str, Any], root: Path | PrivateRoot
) -> None:
    """Validate exact canonical statements binding Git revisions to acquired bytes."""
    items = {item["id"]: item for item in policy_items(policy)}
    for item in items.values():
        reference = item["origin"].get("immutable_reference", "")
        if item["admission_status"] != "approved-for-acquisition" or not reference.startswith("git:"):
            continue
        provenance = item["origin"]["provenance"]
        target = items[provenance["artifact_id"]]
        target_digest = target["acquisition"]["expected"]["sha256"]
        path = root / "artifacts" / ("sha256-" + target_digest)
        data = read_private_bytes(root, path, "Git origin provenance for %s" % item["id"])
        if len(data) > 65536:
            die("Git origin provenance for %s exceeds the bounded statement size" % item["id"])
        statement = parse_private_json(data, "Git origin provenance for %s" % item["id"])
        expected = {
            "provenance_version": "phase0-git-origin-provenance-v1",
            "subject_artifact_id": item["id"],
            "authority": item["origin"]["authority"],
            "revision": item["origin"]["revision"],
            "commit": reference.removeprefix("git:"),
            "acquired_content_digest": "sha256:" + item["acquisition"]["expected"]["sha256"],
        }
        if statement != expected or data != jcs_bytes(statement) + b"\n":
            die("Git origin provenance for %s does not bind the reviewed commit and acquired digest" % item["id"])


def load_optional_records(root: Path | PrivateRoot, directory: str) -> List[Dict[str, Any]]:
    records_path = root / directory
    descriptor = open_private_directory_descriptor(
        root, records_path, "%s records" % directory, missing_ok=True
    )
    if descriptor is None:
        return []
    try:
        names = sorted(os.listdir(descriptor))
        if any(not name.endswith(".json") for name in names):
            die("%s contains an unexpected non-JSON entry" % directory)
        records = []
        for name in names:
            record = parse_private_json(
                read_private_file_at(descriptor, name, "%s record" % directory),
                "%s record" % directory,
            )
            if not isinstance(record, dict):
                die("%s must contain JSON objects" % directory)
            if directory == "failures":
                expected_name = "sha256-" + sha256_bytes(jcs_bytes(record)) + ".json"
                if name != expected_name:
                    die("failure record does not have its content-addressed filename")
            records.append(record)
        if sorted(os.listdir(descriptor)) != names:
            die("%s records changed while being sealed" % directory)
        return records
    finally:
        os.close(descriptor)


def validate_optional_policy_records(
    records: List[Dict[str, Any]], directory: str, policy: Dict[str, Any]
) -> None:
    """Bind failure and exclusion records to the reviewed policy graph."""
    items = {item["id"]: item for item in policy_items(policy)}
    for record in records:
        artifact_id = record.get("artifact_id")
        if not isinstance(artifact_id, str) or artifact_id not in items:
            die("%s record is not bound to an artifact in the reviewed policy" % directory)
        approved = items[artifact_id]["admission_status"] == "approved-for-acquisition"
        if directory == "failures" and not approved:
            die("failure record is not bound to an approved acquisition")
        if directory == "exclusions" and approved:
            die("exclusion record conflicts with an approved acquisition")


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
        except SchemaValueMismatch:
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
        if checker is None:
            die("lock-inventory schema has an unsupported type")
        if not checker(value):
            schema_mismatch("payload member %s does not satisfy schema type" % path)
    if "const" in constraints and value != constraints["const"]:
        schema_mismatch("payload member %s does not satisfy schema const" % path)
    pattern = constraints.get("pattern")
    if pattern is not None:
        if not isinstance(pattern, str):
            die("lock-inventory schema has an invalid pattern")
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            schema_mismatch("payload member %s does not satisfy schema pattern" % path)
    min_length = constraints.get("minLength")
    if min_length is not None:
        if type(min_length) is not int:
            die("lock-inventory schema has an invalid minLength")
        if not isinstance(value, str) or len(value) < min_length:
            schema_mismatch("payload member %s does not satisfy schema minLength" % path)
    minimum = constraints.get("minimum")
    if minimum is not None:
        if type(minimum) is not int:
            die("lock-inventory schema has an invalid minimum")
        if type(value) is not int or value < minimum:
            schema_mismatch("payload member %s does not satisfy schema minimum" % path)
    if isinstance(value, list):
        min_items = constraints.get("minItems")
        if min_items is not None:
            if type(min_items) is not int:
                die("lock-inventory schema has an invalid minItems")
            if len(value) < min_items:
                schema_mismatch("payload member %s does not satisfy schema minItems" % path)
        max_items = constraints.get("maxItems")
        if max_items is not None:
            if type(max_items) is not int:
                die("lock-inventory schema has an invalid maxItems")
            if len(value) > max_items:
                schema_mismatch("payload member %s does not satisfy schema maxItems" % path)
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
            schema_mismatch("payload member %s is missing schema members: %s" % (path, ", ".join(sorted(missing))))
        if constraints.get("additionalProperties") is False and unexpected:
            schema_mismatch("payload member %s has unexpected schema members: %s" % (path, ", ".join(sorted(unexpected))))
        for name, member in value.items():
            if name in properties:
                validate_schema_value(member, properties[name], root_schema, "%s.%s" % (path, name))


def validate_lock_inventory_payload(payload: Dict[str, Any], schema: Any) -> None:
    if not isinstance(schema, dict) or schema.get("$id") != "docproc:phase0-lock-inventory-v1":
        die("schema is not phase0-lock-inventory-v1")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        die("lock-inventory schema must be a closed object")
    validate_schema_value(payload, schema, schema, "$")


def seal(
    policy: Dict[str, Any], root: Path | PrivateRoot, schema: Path,
    source_commit: str, controls: ReviewedControls,
) -> str:
    policy = validate_policy(policy)
    if policy["policy_version"] != "phase0-exact-byte-v1":
        die("sealing requires a reviewed phase0-exact-byte-v1 policy")
    if source_commit != controls.producer_commit:
        die("source commit does not match the independently reviewed producer commit")
    schema_definition, schema_bytes = load_reviewed_json_document(
        schema, controls.schema_digest, "schema"
    )
    environment_ref = load_host_baseline(root, controls.host_baseline_digest)
    observations = load_observations(root, policy)
    validate_git_provenance_records(policy, root)
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
    failures = load_optional_records(root, "failures")
    exclusions = load_optional_records(root, "exclusions")
    validate_optional_policy_records(failures, "failures", policy)
    validate_optional_policy_records(exclusions, "exclusions", policy)
    payload = {
        "payload_version": "docproc-evidence-payload-v1",
        "payload_schema_digest": "sha256:" + sha256_bytes(schema_bytes),
        "evidence_id": "EVID-LOCK-INVENTORY-001",
        "kind": "lock-inventory",
        "source_commit": source_commit,
        "policy_digest": "sha256:" + sha256_bytes(jcs_bytes(policy)),
        "reviewed_controls": controls.record(),
        "source_decisions": source_decisions,
        "environment_ref": environment_ref,
        "acquisition_attestation": "unauthenticated-harness-observation",
        "inventory": inventory,
        "failures": failures,
        "exclusions": exclusions,
        "reviewed_exceptions": exceptions,
        "content_classification": "metadata-only",
        "publication_disposition": "private-only",
    }
    validate_lock_inventory_payload(payload, schema_definition)
    payload_address = "evp1:sha256:" + sha256_bytes(b"docproc:evidence-payload:v1\x00" + jcs_bytes(payload))
    envelope = {
        "envelope_version": "docproc:evidence-envelope-v1",
        "evidence_profile": "phase0-admission-review-candidate",
        "payload_address": payload_address,
        "review_scope": "base-and-primary-candidate-admission-review",
        "policy_digest": payload["policy_digest"],
        "input_ids": [row["artifact_id"] for row in inventory],
        "environment": {
            "kind": "phase0-admission-review-candidate",
            "policy_digest": payload["policy_digest"],
            "host_baseline_ref": environment_ref,
        },
        "outcome": "pending-human-admission-review",
        "specification_refs": sorted(source["commit"] for source in source_decisions),
        "artifact_bindings": [{"role": "acquired-candidate-byte", "artifact_address": row["artifact_descriptor"]["address"]} for row in inventory],
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
        "- Scope: base and primary-candidate admission review candidate only; no artifact is admitted.",
        "- Outcome: pending-human-admission-review.",
        "- Environment: `%s`." % environment_ref["content_digest"],
        "- Acquisition attestation: unauthenticated harness observation; external capture evidence is still required.",
        "- Content classification: metadata-only.",
        "- Publication disposition: private-only.",
        "- Specification IDs: %s." % ", ".join(source["id"] for source in source_decisions),
        "- Decision commits: %s." % ", ".join(source["commit"] for source in source_decisions),
        "- Artifacts: %s." % ", ".join(row["artifact_id"] for row in inventory),
        "- Failures: %s." % (", ".join(row["artifact_id"] for row in failures) or "none"),
        "- Exclusions: %s." % (", ".join(row["artifact_id"] for row in exclusions) or "none"),
        "",
        "This generated summary admits no artifact, does not authenticate acquisition, and does not authorize execution.",
        "",
    ]).encode("utf-8")
    write_once(root, record / "summary.md", summary)
    print(evidence_address)
    return evidence_address


def validate_phase0_envelope(envelope: Any, payload: Dict[str, Any], expected_bindings: List[Dict[str, str]]) -> None:
    if not isinstance(envelope, dict):
        die("evidence envelope is invalid")
    required = {
        "envelope_version", "evidence_profile", "payload_address", "review_scope", "policy_digest",
        "input_ids", "environment", "outcome", "specification_refs", "artifact_bindings",
        "content_classification", "publication_disposition", "evidence_address",
    }
    if set(envelope) != required:
        die("evidence envelope has an invalid member set")
    if (
        envelope["envelope_version"] != "docproc:evidence-envelope-v1"
        or envelope["evidence_profile"] != "phase0-admission-review-candidate"
        or envelope["review_scope"] != "base-and-primary-candidate-admission-review"
        or envelope["policy_digest"] != payload["policy_digest"]
        or envelope["outcome"] != "pending-human-admission-review"
        or envelope["content_classification"] != "metadata-only"
        or envelope["publication_disposition"] != "private-only"
        or envelope["environment"] != {
            "kind": "phase0-admission-review-candidate",
            "policy_digest": payload["policy_digest"],
            "host_baseline_ref": payload["environment_ref"],
        }
    ):
        die("evidence envelope violates the Phase 0 admission profile")
    expected_ids = [row["artifact_id"] for row in payload["inventory"]]
    expected_refs = sorted(source["commit"] for source in payload["source_decisions"])
    if envelope["input_ids"] != expected_ids or envelope["specification_refs"] != expected_refs:
        die("evidence envelope does not bind the sealed payload inputs")
    if envelope["artifact_bindings"] != expected_bindings:
        die("evidence envelope does not bind the sealed artifact descriptors")


def validate_payload_policy_binding(
    payload: Dict[str, Any], policy: Dict[str, Any], controls: ReviewedControls
) -> Dict[str, Dict[str, Any]]:
    """Bind policy-owned evidence metadata to the reviewed exact-byte policy."""
    policy = validate_policy(policy)
    if policy["policy_version"] != "phase0-exact-byte-v1":
        die("verification requires a reviewed phase0-exact-byte-v1 policy")
    if payload["policy_digest"] != "sha256:" + sha256_bytes(jcs_bytes(policy)):
        die("payload policy digest does not match the reviewed policy")
    if payload["reviewed_controls"] != controls.record():
        die("payload controls do not match the independently reviewed controls")
    expected_sources = sorted(policy["source_decisions"], key=lambda source: source["id"])
    if payload["source_decisions"] != expected_sources:
        die("payload source decisions do not match the reviewed policy")
    expected_exceptions = sorted(
        ({"artifact_id": item["id"], "license": item["license"]}
         for item in policy_items(policy)
         if item["license"]["review_status"] == "reviewed-exception"),
        key=lambda row: row["artifact_id"],
    )
    if payload["reviewed_exceptions"] != expected_exceptions:
        die("payload reviewed exceptions do not match the reviewed policy")
    validate_optional_policy_records(payload["failures"], "failures", policy)
    validate_optional_policy_records(payload["exclusions"], "exclusions", policy)
    expected_items = {
        item["id"]: item
        for item in policy_items(policy)
        if item["admission_status"] == "approved-for-acquisition"
    }
    if [row["artifact_id"] for row in payload["inventory"]] != sorted(expected_items):
        die("payload inventory does not match the reviewed policy")
    return expected_items


def verify(
    root: Path | PrivateRoot, evidence_address: str, schema: Path,
    policy: Dict[str, Any], controls: ReviewedControls,
) -> None:
    if not ADDRESS_RE.fullmatch(evidence_address) or not evidence_address.startswith("evr1:"):
        die("invalid evidence address")
    schema_definition, schema_bytes = load_reviewed_json_document(
        schema, controls.schema_digest, "schema"
    )
    record = root / "records" / evidence_address.replace(":", "_")
    payload = load_private_json(root, record / "payload.json", "sealed payload")
    envelope = load_private_json(root, record / "envelope.json", "sealed envelope")
    if not isinstance(payload, dict):
        die("payload is invalid")
    if not isinstance(envelope, dict):
        die("evidence envelope is invalid")
    validate_lock_inventory_payload(payload, schema_definition)
    if payload["environment_ref"] != load_host_baseline(root, controls.host_baseline_digest):
        die("sealed host baseline does not match the retained machine evidence")
    if payload["payload_schema_digest"] != "sha256:" + sha256_bytes(schema_bytes):
        die("payload schema digest mismatch")
    expected_items = validate_payload_policy_binding(payload, policy, controls)
    validate_git_provenance_records(policy, root)
    expected_bindings = []
    inventory = payload["inventory"]
    artifact_ids = [row["artifact_id"] for row in inventory]
    if artifact_ids != sorted(artifact_ids) or len(set(artifact_ids)) != len(artifact_ids):
        die("payload inventory is not sorted by unique artifact id")
    for row in inventory:
        observation = row["observation"]
        item = expected_items[row["artifact_id"]]
        if (
            observation["artifact_id"] != row["artifact_id"]
            or row["origin"] != item["origin"]
            or row["license"] != item["license"]
            or row["distribution_mode"] != item["distribution_mode"]
            or row["publication_disposition"] != item["publication_disposition"]
            or observation["requested_url"] != item["acquisition"]["url"]
            or observation["final_url"] != item["acquisition"]["url"]
            or observation["content_digest"] != "sha256:" + item["acquisition"]["expected"]["sha256"]
            or observation["byte_length"] != item["acquisition"]["expected"]["byte_length"]
        ):
            die("payload inventory metadata does not match the reviewed policy")
        descriptor_record = row["artifact_descriptor"]
        descriptor = descriptor_record["descriptor"]
        metadata = {key: value for key, value in descriptor.items() if key not in {
            "descriptor_version", "content_digest", "byte_length"
        }}
        if metadata != item["acquisition"]["descriptor"]:
            die("artifact descriptor metadata does not match the reviewed policy")
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
        expected_bindings.append({"role": "acquired-candidate-byte", "artifact_address": calculated_descriptor["address"]})
        artifact = root / "artifacts" / ("sha256-" + observation["content_digest"].removeprefix("sha256:"))
        digest, length = sha256_private_file(
            root, artifact, "content-addressed artifact for %s" % row["artifact_id"]
        )
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
            try:
                digest, length = sha256_file(Path(location))
            except OSError as exc:
                executables.append({"name": name, "status": "unavailable", "detail": type(exc).__name__})
            else:
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
    closure_cmd.add_argument("--catalog-digest", required=True)
    closure_cmd.add_argument("--policy", type=Path, required=True)
    closure_cmd.add_argument("--policy-digest", required=True)
    prefetch_cmd = sub.add_parser("prefetch")
    prefetch_cmd.add_argument("--catalog", type=Path, required=True)
    prefetch_cmd.add_argument("--catalog-digest", required=True)
    prefetch_cmd.add_argument("--policy", type=Path, required=True)
    prefetch_cmd.add_argument("--policy-digest", required=True)
    prefetch_cmd.add_argument("--root", required=True, help="private evidence root outside this Git worktree")
    seal_cmd = sub.add_parser("seal")
    seal_cmd.add_argument("--catalog", type=Path, required=True)
    seal_cmd.add_argument("--catalog-digest", required=True)
    seal_cmd.add_argument("--policy", type=Path, required=True)
    seal_cmd.add_argument("--policy-digest", required=True)
    seal_cmd.add_argument("--root", required=True)
    seal_cmd.add_argument("--schema", type=Path, required=True)
    seal_cmd.add_argument("--schema-digest", required=True)
    seal_cmd.add_argument("--host-baseline-digest", required=True)
    seal_cmd.add_argument("--source-commit", required=True)
    verify_cmd = sub.add_parser("verify")
    verify_cmd.add_argument("--root", required=True)
    verify_cmd.add_argument("--catalog", type=Path, required=True)
    verify_cmd.add_argument("--catalog-digest", required=True)
    verify_cmd.add_argument("--policy", type=Path, required=True)
    verify_cmd.add_argument("--policy-digest", required=True)
    verify_cmd.add_argument("--schema", type=Path, required=True)
    verify_cmd.add_argument("--schema-digest", required=True)
    verify_cmd.add_argument("--host-baseline-digest", required=True)
    verify_cmd.add_argument("--producer-commit", required=True)
    verify_cmd.add_argument("--evidence-address", required=True)
    host_cmd = sub.add_parser("capture-host-baseline")
    host_cmd.add_argument("--root", required=True, help="private evidence root outside this Git worktree")
    args = parser.parse_args(argv)
    try:
        if args.command == "capture-host-baseline":
            with safe_root(args.root) as root:
                record_bytes = jcs_bytes(host_record()) + b"\n"
                write_once(root, root / "host-baseline.json", record_bytes)
                print("sha256:" + sha256_bytes(record_bytes))
        elif args.command == "verify":
            catalog = validate_policy(load_reviewed_json(args.catalog, args.catalog_digest, "catalog"))
            policy = validate_policy(load_reviewed_json(args.policy, args.policy_digest, "policy"))
            validate_closure(catalog, policy)
            controls = ReviewedControls(
                args.catalog_digest, args.policy_digest, args.schema_digest,
                args.host_baseline_digest, args.producer_commit,
            )
            with safe_root(args.root) as root:
                verify(root, args.evidence_address, args.schema, policy, controls)
        elif args.command == "validate-policy":
            validate_policy(load_json(args.policy))
            print("policy valid; no network request made")
        else:
            catalog = validate_policy(load_reviewed_json(args.catalog, args.catalog_digest, "catalog"))
            policy = validate_policy(load_reviewed_json(args.policy, args.policy_digest, "policy"))
            validate_closure(catalog, policy)
            if args.command == "validate-closure":
                print("exact-byte policy covers only the base/primary catalog; no network request made")
            elif args.command == "prefetch":
                with safe_root(args.root) as root:
                    prefetch(policy, root)
            elif args.command == "seal":
                controls = ReviewedControls(
                    args.catalog_digest, args.policy_digest, args.schema_digest,
                    args.host_baseline_digest, args.source_commit,
                )
                with safe_root(args.root) as root:
                    seal(policy, root, args.schema, args.source_commit, controls)
        return 0
    except LockError as exc:
        print("phase0-lock: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
