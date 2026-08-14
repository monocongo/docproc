from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

MODULE = Path(__file__).parents[1] / "phase0" / "lock" / "phase0_lock.py"
spec = importlib.util.spec_from_file_location("phase0_lock", MODULE)
phase0_lock = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(phase0_lock)


class Phase0LockTests(unittest.TestCase):
    def write_private_json(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")
        path.chmod(0o600)

    def write_private_bytes(self, path, value):
        path.write_bytes(value)
        path.chmod(0o600)

    def policy(self):
        body = b"admitted byte\n"
        return {
            "policy_version": "phase0-exact-byte-v1",
            "scope": "base-and-primary-candidate-admission",
            "source_decisions": [{"id": "SRC-LICENSE", "commit": "a" * 40}],
            "artifacts": [{
                "id": "approved-byte",
                "component_id": "approved-component",
                "kind": "test-byte",
                "required": True,
                "admission_status": "approved-for-acquisition",
                "origin": {
                    "authority": "test authority",
                    "revision": "rev-1",
                    "immutable_reference": "sha256:" + "c" * 64,
                },
                "acquisition": {
                    "url": "https://example.invalid/admitted-byte",
                    "expected": {"sha256": hashlib.sha256(body).hexdigest(), "byte_length": len(body)},
                    "descriptor": {"media_type": "application/octet-stream", "content_encoding": "identity"},
                },
                "license": {"evidence_class": "exact-license-text", "review_status": "reviewed"},
                "distribution_mode": "direct-upstream-pull",
                "publication_disposition": "do-not-publish",
            }],
        }

    def test_policy_rejects_an_unreviewed_approved_artifact(self):
        policy = self.policy()
        policy["artifacts"][0]["license"]["review_status"] = "pending-human-review"
        with self.assertRaisesRegex(phase0_lock.LockError, "pending license review"):
            phase0_lock.validate_policy(policy)

    def test_policy_rejects_noassertion(self):
        policy = self.policy()
        policy["artifacts"][0]["license"]["evidence_class"] = "NOASSERTION"
        with self.assertRaisesRegex(phase0_lock.LockError, "NOASSERTION"):
            phase0_lock.validate_policy(policy)

    def test_policy_rejects_non_string_digest_and_commit(self):
        policy = self.policy()
        policy["source_decisions"][0]["commit"] = 123
        with self.assertRaisesRegex(phase0_lock.LockError, "full lowercase commit"):
            phase0_lock.validate_policy(policy)
        policy = self.policy()
        policy["artifacts"][0]["acquisition"]["expected"]["sha256"] = 123
        with self.assertRaisesRegex(phase0_lock.LockError, "expected SHA-256"):
            phase0_lock.validate_policy(policy)

    def test_policy_rejects_ignored_top_level_members(self):
        policy = self.policy()
        policy["ignored_graph"] = {"artifact": "not enforced"}
        with self.assertRaisesRegex(phase0_lock.LockError, "unexpected members: ignored_graph"):
            phase0_lock.validate_policy(policy)

    def test_prefetch_refuses_pending_graph_without_request(self):
        policy = self.policy()
        policy["artifacts"][0]["admission_status"] = "pending-human-review"
        policy["artifacts"][0]["acquisition"] = {"url": None}
        policy["artifacts"][0]["license"]["review_status"] = "pending-human-review"
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            phase0_lock.urllib.request, "build_opener"
        ) as build_opener:
            with self.assertRaisesRegex(phase0_lock.LockError, "until every required artifact is approved"):
                phase0_lock.prefetch(phase0_lock.validate_policy(policy), Path(temporary))
        build_opener.assert_not_called()

    def test_prefetch_refuses_denied_graph_without_request(self):
        policy = self.policy()
        denied = copy.deepcopy(policy["artifacts"][0])
        denied["id"] = "denied-byte"
        denied["required"] = False
        denied["admission_status"] = "denied"
        denied["acquisition"] = {"url": None}
        policy["artifacts"].append(denied)
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            phase0_lock.urllib.request, "build_opener"
        ) as build_opener:
            with self.assertRaisesRegex(phase0_lock.LockError, "denied artifacts in graph"):
                phase0_lock.prefetch(phase0_lock.validate_policy(policy), Path(temporary))
        build_opener.assert_not_called()

    def test_exact_download_disables_ambient_proxies(self):
        item = self.policy()["artifacts"][0]
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            phase0_lock.urllib.request, "build_opener", side_effect=RuntimeError("stop before request")
        ) as build_opener:
            with self.assertRaisesRegex(RuntimeError, "stop before request"):
                phase0_lock.download_exact(item, Path(temporary))
        proxy_handler, redirect_handler = build_opener.call_args.args
        self.assertIsInstance(proxy_handler, phase0_lock.urllib.request.ProxyHandler)
        self.assertEqual(proxy_handler.proxies, {})
        self.assertIs(redirect_handler, phase0_lock.NoRedirect)

    def test_exact_download_keeps_the_secure_temporary_descriptor(self):
        item = self.policy()["artifacts"][0]
        body = b"admitted byte\n"

        class Response:
            status = 200
            headers = {
                "Content-Length": str(len(body)),
                "Content-Encoding": "identity",
                "Content-Type": "application/octet-stream",
            }

            def __init__(self):
                self.remaining = body

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                return None

            def geturl(self):
                return item["acquisition"]["url"]

            def read(self, unused_size):
                chunk, self.remaining = self.remaining, b""
                return chunk

        opener = mock.Mock()
        opener.open.return_value = Response()
        original_open = Path.open

        def reject_temporary_path_reopen(path, *args, **kwargs):
            if path.name.startswith("prefetch-"):
                raise AssertionError("secure temporary file reopened by path")
            return original_open(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            phase0_lock.urllib.request, "build_opener", return_value=opener
        ), mock.patch.object(Path, "open", new=reject_temporary_path_reopen):
            observation = phase0_lock.download_exact(item, Path(temporary))

        self.assertEqual(observation["content_digest"], "sha256:" + hashlib.sha256(body).hexdigest())

    def test_artifact_install_never_replaces_an_existing_address(self):
        first = b"first immutable body"
        conflicting = b"conflicting body"
        observed = hashlib.sha256(conflicting).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            artifacts.mkdir(mode=0o700)
            artifact_path = artifacts / ("sha256-" + observed)
            self.write_private_bytes(artifact_path, first)
            candidate = root / "candidate"
            self.write_private_bytes(candidate, conflicting)

            with candidate.open("rb") as source:
                with self.assertRaisesRegex(phase0_lock.LockError, "content-addressed artifact collision"):
                    phase0_lock.install_artifact_once(
                        root, candidate, source.fileno(), artifact_path,
                        "approved-byte", observed, len(conflicting)
                    )

            self.assertEqual(artifact_path.read_bytes(), first)
            self.assertEqual(candidate.read_bytes(), conflicting)

    def test_artifact_install_rejects_a_swapped_temporary_path(self):
        body = b"verified body"
        replacement = b"replacement body"
        observed = hashlib.sha256(body).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            artifacts.mkdir(mode=0o700)
            artifact_path = artifacts / ("sha256-" + observed)
            candidate = root / "candidate"
            self.write_private_bytes(candidate, body)
            original_link = os.link

            def swap_before_link(source, target):
                source.unlink()
                self.write_private_bytes(source, replacement)
                original_link(source, target)

            with candidate.open("rb") as source, mock.patch.object(
                phase0_lock.os, "link", side_effect=swap_before_link
            ):
                with self.assertRaisesRegex(phase0_lock.LockError, "temporary artifact changed"):
                    phase0_lock.install_artifact_once(
                        root, candidate, source.fileno(), artifact_path,
                        "approved-byte", observed, len(body)
                    )

    def test_schema_byte_read_failures_are_bounded(self):
        schema = Path(__file__).parents[1] / "schemas" / "phase0-lock-inventory-v1.json"
        with mock.patch.object(Path, "read_bytes", side_effect=PermissionError("/private/schema")):
            with self.assertRaisesRegex(phase0_lock.LockError, "cannot read schema bytes: PermissionError"):
                phase0_lock.read_schema_bytes(schema)

    def test_optional_records_are_bound_to_the_reviewed_policy(self):
        policy = phase0_lock.validate_policy(self.policy())
        unknown = {"artifact_id": "outside-policy"}
        with self.assertRaisesRegex(phase0_lock.LockError, "not bound to an artifact"):
            phase0_lock.validate_optional_policy_records([unknown], "failures", policy)
        with self.assertRaisesRegex(phase0_lock.LockError, "conflicts with an approved acquisition"):
            phase0_lock.validate_optional_policy_records(
                [{"artifact_id": "approved-byte"}], "exclusions", policy
            )

        pending = copy.deepcopy(policy["artifacts"][0])
        pending["id"] = "pending-byte"
        pending["required"] = False
        pending["admission_status"] = "pending-human-review"
        pending["acquisition"] = {"url": None}
        pending["license"]["review_status"] = "pending-human-review"
        policy["artifacts"].append(pending)
        with self.assertRaisesRegex(phase0_lock.LockError, "not bound to an approved acquisition"):
            phase0_lock.validate_optional_policy_records(
                [{"artifact_id": "pending-byte"}], "failures", policy
            )

    def test_failure_records_require_content_addressed_filenames(self):
        failure = {
            "failure_version": "phase0-acquisition-failure-v1",
            "artifact_id": "approved-byte",
            "occurred_at_utc": "2026-08-14T00:00:00Z",
            "stage": "prefetch",
            "message": "admitted request did not complete byte verification",
            "content_classification": "metadata-only",
            "publication_disposition": "private-only",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            failures = root / "failures"
            failures.mkdir(mode=0o700)
            self.write_private_json(failures / "manual.json", failure)
            with self.assertRaisesRegex(phase0_lock.LockError, "content-addressed filename"):
                phase0_lock.load_optional_records(root, "failures")

    def test_closure_rejects_an_unapproved_component(self):
        catalog = self.policy()
        catalog["policy_version"] = "phase0-base-primary-v1"
        catalog["artifacts"][0].pop("component_id")
        exact = self.policy()
        exact["artifacts"][0]["component_id"] = "surprise-model"
        with self.assertRaisesRegex(phase0_lock.LockError, "unapproved component"):
            phase0_lock.validate_closure(
                phase0_lock.validate_policy(catalog), phase0_lock.validate_policy(exact)
            )

    def test_closure_preserves_catalog_source_decisions(self):
        catalog = self.policy()
        catalog["policy_version"] = "phase0-base-primary-v1"
        catalog["artifacts"][0].pop("component_id")
        catalog["artifacts"][0]["id"] = "approved-component"
        exact = self.policy()
        exact["source_decisions"][0]["commit"] = "b" * 40
        with self.assertRaisesRegex(phase0_lock.LockError, "preserve catalog source decisions"):
            phase0_lock.validate_closure(
                phase0_lock.validate_policy(catalog), phase0_lock.validate_policy(exact)
            )

    def test_seal_and_verify_are_content_addressed(self):
        policy = self.policy()
        exception = copy.deepcopy(policy["artifacts"][0])
        exception["id"] = "exception-byte"
        exception["acquisition"]["url"] = "https://example.invalid/exception-byte"
        exception["license"]["review_status"] = "reviewed-exception"
        policy["artifacts"].append(exception)
        policy = phase0_lock.validate_policy(policy)
        body = b"admitted byte\n"
        digest = hashlib.sha256(body).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "artifacts" / ("sha256-" + digest)
            artifact.parent.mkdir(mode=0o700)
            self.write_private_bytes(artifact, body)
            observation = {
                "observation_version": "phase0-acquisition-observation-v1",
                "artifact_id": "approved-byte",
                "requested_url": "https://example.invalid/admitted-byte",
                "final_url": "https://example.invalid/admitted-byte",
                "method": "GET",
                "status": 200,
                "content_digest": "sha256:" + digest,
                "byte_length": len(body),
                "content_type": "application/octet-stream",
                "observed_started_at_utc": "2026-08-09T00:00:00Z",
                "observed_completed_at_utc": "2026-08-09T00:00:01Z",
                "redirects": [],
                "network_result": "admitted-request-completed",
            }
            observations = root / "observations"
            observations.mkdir(mode=0o700)
            observation_path = observations / "approved-byte.json"
            self.write_private_json(observation_path, [])
            schema = Path(__file__).parents[1] / "schemas" / "phase0-lock-inventory-v1.json"
            with self.assertRaisesRegex(phase0_lock.LockError, "observation must be an object"):
                phase0_lock.seal(policy, root, schema, "b" * 40)
            self.write_private_json(observation_path, observation)
            exception_observation = copy.deepcopy(observation)
            exception_observation["artifact_id"] = "exception-byte"
            exception_observation["requested_url"] = "https://example.invalid/exception-byte"
            exception_observation["final_url"] = "https://example.invalid/exception-byte"
            self.write_private_json(observations / "exception-byte.json", exception_observation)
            phase0_lock.record_prefetch_failure(root, "approved-byte")
            evidence_address = phase0_lock.seal(policy, root, schema, "b" * 40)
            self.assertTrue(evidence_address.startswith("evr1:sha256:"))
            phase0_lock.verify(root, evidence_address, schema, policy)
            self.write_private_bytes(artifact, b"tampered")
            with self.assertRaisesRegex(phase0_lock.LockError, "does not match sealed inventory"):
                phase0_lock.verify(root, evidence_address, schema, policy)
            self.write_private_bytes(artifact, body)
            with self.assertRaisesRegex(phase0_lock.LockError, "invalid evidence address"):
                phase0_lock.verify(root, "not-an-evidence-address", schema, policy)

            record = root / "records" / evidence_address.replace(":", "_")
            envelope_path = record / "envelope.json"
            original_envelope = envelope_path.read_text(encoding="utf-8")
            envelope_path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "evidence envelope is invalid"):
                phase0_lock.verify(root, evidence_address, schema, policy)
            envelope_path.write_text(original_envelope, encoding="utf-8")
            envelope = json.loads(original_envelope)
            envelope["input_ids"].append("tampered")
            envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "does not bind"):
                phase0_lock.verify(root, evidence_address, schema, policy)
            envelope_path.write_text(original_envelope, encoding="utf-8")

            payload_path = record / "payload.json"
            original_payload = payload_path.read_text(encoding="utf-8")
            payload = json.loads(original_payload)
            self.assertEqual(payload["failures"][0]["message"], "admitted request did not complete byte verification")
            self.assertEqual(
                payload["reviewed_exceptions"],
                [{"artifact_id": "exception-byte", "license": exception["license"]}],
            )
            forged_payload = copy.deepcopy(payload)
            forged_payload["inventory"][0]["artifact_id"] = "forged-byte"
            forged_payload["inventory"][0]["license"] = {
                "evidence_class": "forged-license",
                "review_status": "reviewed",
            }
            forged_envelope = json.loads(original_envelope)
            forged_envelope["input_ids"][0] = "forged-byte"
            forged_envelope["payload_address"] = "evp1:sha256:" + phase0_lock.sha256_bytes(
                b"docproc:evidence-payload:v1\x00" + phase0_lock.jcs_bytes(forged_payload)
            )
            forged_unsigned = {
                key: value for key, value in forged_envelope.items() if key != "evidence_address"
            }
            forged_address = "evr1:sha256:" + phase0_lock.sha256_bytes(
                b"docproc:evidence-envelope:v1\x00" + phase0_lock.jcs_bytes(forged_unsigned)
            )
            forged_envelope["evidence_address"] = forged_address
            forged_record = root / "records" / forged_address.replace(":", "_")
            forged_record.mkdir(mode=0o700)
            self.write_private_json(forged_record / "payload.json", forged_payload)
            self.write_private_json(forged_record / "envelope.json", forged_envelope)
            with self.assertRaisesRegex(phase0_lock.LockError, "inventory does not match the reviewed policy"):
                phase0_lock.verify(root, forged_address, schema, policy)
            payload["inventory"][0]["observation"]["redirects"] = ["https://example.invalid/redirect"]
            payload_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "maxItems"):
                phase0_lock.verify(root, evidence_address, schema, policy)
            payload_path.write_text(original_payload, encoding="utf-8")
            payload = json.loads(original_payload)
            payload["inventory"][0]["artifact_descriptor"]["address"] = "art1:sha256:" + "0" * 64
            payload_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "artifact descriptor address mismatch"):
                phase0_lock.verify(root, evidence_address, schema, policy)
            payload_path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "missing schema members"):
                phase0_lock.verify(root, evidence_address, schema, policy)

    def test_verify_rejects_forged_redirect_observation(self):
        policy = phase0_lock.validate_policy(self.policy())
        body = b"admitted byte\n"
        digest = hashlib.sha256(body).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            artifacts.mkdir(mode=0o700)
            self.write_private_bytes(artifacts / ("sha256-" + digest), body)
            observations = root / "observations"
            observations.mkdir(mode=0o700)
            self.write_private_json(observations / "approved-byte.json", {
                "observation_version": "phase0-acquisition-observation-v1",
                "artifact_id": "approved-byte",
                "requested_url": "https://example.invalid/admitted-byte",
                "final_url": "https://example.invalid/admitted-byte",
                "method": "GET",
                "status": 200,
                "content_digest": "sha256:" + digest,
                "byte_length": len(body),
                "content_type": "application/octet-stream",
                "observed_started_at_utc": "2026-08-09T00:00:00Z",
                "observed_completed_at_utc": "2026-08-09T00:00:01Z",
                "redirects": [],
                "network_result": "admitted-request-completed",
            })
            schema = Path(__file__).parents[1] / "schemas" / "phase0-lock-inventory-v1.json"
            evidence_address = phase0_lock.seal(policy, root, schema, "b" * 40)
            record = root / "records" / evidence_address.replace(":", "_")
            payload = json.loads((record / "payload.json").read_text(encoding="utf-8"))
            envelope = json.loads((record / "envelope.json").read_text(encoding="utf-8"))
            payload["inventory"][0]["observation"]["redirects"] = [{"status": 302}]
            payload_address = "evp1:sha256:" + phase0_lock.sha256_bytes(
                b"docproc:evidence-payload:v1\x00" + phase0_lock.jcs_bytes(payload)
            )
            envelope["payload_address"] = payload_address
            unsigned = {key: value for key, value in envelope.items() if key != "evidence_address"}
            forged_address = "evr1:sha256:" + phase0_lock.sha256_bytes(
                b"docproc:evidence-envelope:v1\x00" + phase0_lock.jcs_bytes(unsigned)
            )
            envelope["evidence_address"] = forged_address
            forged = root / "records" / forged_address.replace(":", "_")
            forged.mkdir(mode=0o700)
            self.write_private_json(forged / "payload.json", payload)
            self.write_private_json(forged / "envelope.json", envelope)
            with self.assertRaisesRegex(phase0_lock.LockError, "maxItems"):
                phase0_lock.verify(root, forged_address, schema, policy)

    def test_seal_rejects_artifact_symlink_outside_private_root(self):
        policy = phase0_lock.validate_policy(self.policy())
        body = b"admitted byte\n"
        digest = hashlib.sha256(body).hexdigest()
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as external:
            root = Path(temporary)
            artifacts = root / "artifacts"
            artifacts.mkdir(mode=0o700)
            outside = Path(external) / "artifact"
            self.write_private_bytes(outside, body)
            try:
                (artifacts / ("sha256-" + digest)).symlink_to(outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest("symlinks unavailable: %s" % type(exc).__name__)
            observations = root / "observations"
            observations.mkdir(mode=0o700)
            self.write_private_json(observations / "approved-byte.json", {
                "observation_version": "phase0-acquisition-observation-v1",
                "artifact_id": "approved-byte",
                "requested_url": "https://example.invalid/admitted-byte",
                "final_url": "https://example.invalid/admitted-byte",
                "method": "GET",
                "status": 200,
                "content_digest": "sha256:" + digest,
                "byte_length": len(body),
                "content_type": "application/octet-stream",
                "observed_started_at_utc": "2026-08-09T00:00:00Z",
                "observed_completed_at_utc": "2026-08-09T00:00:01Z",
                "redirects": [],
                "network_result": "admitted-request-completed",
            })
            schema = Path(__file__).parents[1] / "schemas" / "phase0-lock-inventory-v1.json"
            with self.assertRaisesRegex(phase0_lock.LockError, "regular private file"):
                phase0_lock.seal(policy, root, schema, "b" * 40)

    def test_closure_requires_approved_required_records_for_each_required_component(self):
        catalog = self.policy()
        catalog["policy_version"] = "phase0-base-primary-v1"
        catalog["artifacts"][0].pop("component_id")
        catalog["artifacts"][0]["id"] = "approved-component"
        second_catalog_item = copy.deepcopy(catalog["artifacts"][0])
        second_catalog_item["id"] = "second-component"
        catalog["artifacts"].append(second_catalog_item)

        exact = self.policy()
        pending = copy.deepcopy(exact["artifacts"][0])
        pending["id"] = "second-byte"
        pending["component_id"] = "second-component"
        pending["required"] = False
        pending["admission_status"] = "pending-human-review"
        pending["acquisition"] = {"url": None}
        pending["license"]["review_status"] = "pending-human-review"
        exact["artifacts"].append(pending)

        with self.assertRaisesRegex(phase0_lock.LockError, "required approved exact-byte record"):
            phase0_lock.validate_closure(
                phase0_lock.validate_policy(catalog), phase0_lock.validate_policy(exact)
            )

    def test_policy_rejects_noncanonical_values_query_urls_and_boolean_lengths_before_prefetch(self):
        policy = self.policy()
        policy["source_decisions"][0]["commit"] = 0.5
        with self.assertRaisesRegex(phase0_lock.LockError, "floating-point"):
            phase0_lock.validate_policy(policy)

        policy = self.policy()
        policy["artifacts"][0]["acquisition"]["url"] += "?"
        with self.assertRaisesRegex(phase0_lock.LockError, "without query"):
            phase0_lock.validate_policy(policy)

        policy = self.policy()
        policy["artifacts"][0]["acquisition"]["expected"]["sha256"] += "\n"
        with self.assertRaisesRegex(phase0_lock.LockError, "expected SHA-256"):
            phase0_lock.validate_policy(policy)

        policy = self.policy()
        policy["artifacts"][0]["acquisition"]["expected"]["byte_length"] = True
        with self.assertRaisesRegex(phase0_lock.LockError, "expected byte_length"):
            phase0_lock.validate_policy(policy)

        policy = self.policy()
        policy["artifacts"][0]["acquisition"]["descriptor"]["media_type"] = "application/json"
        with self.assertRaisesRegex(phase0_lock.LockError, "requires a charset"):
            phase0_lock.validate_policy(policy)

        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            phase0_lock, "download_exact", side_effect=OSError("private/path")
        ):
            root = Path(temporary)
            with self.assertRaisesRegex(phase0_lock.LockError, "prefetch failed"):
                phase0_lock.prefetch(self.policy(), root)
            failures = list((root / "failures").glob("*.json"))
            self.assertEqual(len(failures), 1)
            self.assertNotIn("private/path", failures[0].read_text(encoding="utf-8"))

    def test_pf_wrapper_refuses_to_claim_unmanaged_host_egress_denial(self):
        wrapper = Path(__file__).parents[1] / "phase0" / "lock" / "network-deny-pf.sh"
        with tempfile.TemporaryDirectory() as temporary:
            bin_dir = Path(temporary) / "bin"
            bin_dir.mkdir()
            uname = bin_dir / "uname"
            uname.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            uname.chmod(0o755)
            marker = Path(temporary) / "target-ran"
            target = bin_dir / "target"
            target.write_text("#!/bin/sh\n/usr/bin/touch \"$1\"\n", encoding="utf-8")
            target.chmod(0o755)
            environment = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"]}
            result = subprocess.run(
                ["sh", str(wrapper), "--", str(target), str(marker)], text=True, capture_output=True, env=environment
            )
            self.assertEqual(result.returncode, 2)
            self.assertTrue("refusing run" in result.stderr or "macOS PF is required" in result.stderr)
            self.assertFalse(marker.exists())

    def test_safe_root_uses_the_harness_checkout_and_private_permissions(self):
        inside_checkout = MODULE.parents[2] / "phase0" / "private-evidence"
        with tempfile.TemporaryDirectory() as temporary:
            subprocess.run(["git", "init", "-q", temporary], check=True)
            original_cwd = Path.cwd()
            try:
                os.chdir(temporary)
                with self.assertRaisesRegex(phase0_lock.LockError, "outside the Git worktree"):
                    phase0_lock.safe_root(str(inside_checkout))
            finally:
                os.chdir(original_cwd)

            root = phase0_lock.safe_root(str(Path(temporary) / "private"))
            phase0_lock.write_json_once(root, root / "nested" / "record.json", {"record": "private"})
            self.assertEqual((root.stat().st_mode & 0o777), 0o700)
            self.assertEqual(((root / "nested").stat().st_mode & 0o777), 0o700)
            self.assertEqual(((root / "nested" / "record.json").stat().st_mode & 0o777), 0o600)

    def test_repository_root_does_not_execute_ambient_git(self):
        with mock.patch.object(
            phase0_lock.subprocess, "run", side_effect=AssertionError("ambient process executed")
        ) as run:
            self.assertEqual(phase0_lock.repository_root(), MODULE.parents[2])
        run.assert_not_called()

    def test_platform_command_output_is_redacted_and_bounded(self):
        completed = subprocess.CompletedProcess(
            args=["/usr/bin/sw_vers"], returncode=0, stdout="reading /private/token", stderr=""
        )
        with mock.patch.object(phase0_lock.subprocess, "run", return_value=completed):
            observation = phase0_lock.platform_command_observation("sw_vers")
        self.assertEqual(observation["output"], "<redacted-local-path-output>")

        completed = subprocess.CompletedProcess(
            args=["/usr/bin/sw_vers"],
            returncode=0,
            stdout="release https://example.test/releases/v1",
            stderr="",
        )
        with mock.patch.object(phase0_lock.subprocess, "run", return_value=completed):
            observation = phase0_lock.platform_command_observation("sw_vers")
        self.assertEqual(observation["output"], "release https://example.test/releases/v1")

        long_output = "x" * 5000
        completed = subprocess.CompletedProcess(
            args=["/usr/bin/sw_vers"], returncode=0, stdout=long_output, stderr=""
        )
        with mock.patch.object(phase0_lock.subprocess, "run", return_value=completed):
            observation = phase0_lock.platform_command_observation("sw_vers")
        self.assertEqual(observation["output"], long_output[:4096])

    def test_host_record_hashes_tools_without_executing_them(self):
        with mock.patch.object(phase0_lock.shutil, "which", return_value="/private/tool") as which, mock.patch.object(
            phase0_lock, "sha256_file", return_value=("a" * 64, 12)
        ), mock.patch.object(phase0_lock, "platform_command_observation", return_value={"status": "observed"}) as platform_probe:
            record = phase0_lock.host_record()
        self.assertEqual(record["executables"][0], {
            "name": "uv", "sha256": "sha256:" + "a" * 64, "byte_length": 12
        })
        self.assertEqual(which.call_count, 5)
        self.assertEqual(platform_probe.call_count, 3)

    def test_host_record_string_encodes_out_of_range_monotonic_clock(self):
        out_of_range_clock = 9007199254740992
        with mock.patch.object(phase0_lock.shutil, "which", return_value=None), mock.patch.object(
            phase0_lock, "platform_command_observation", return_value={"status": "observed"}
        ), mock.patch.object(phase0_lock.time, "monotonic_ns", return_value=out_of_range_clock):
            record = phase0_lock.host_record()
        self.assertEqual(record["monotonic_ns"], str(out_of_range_clock))
        phase0_lock.jcs_bytes(record)

    def test_host_record_bounds_unreadable_tool_failures(self):
        with mock.patch.object(phase0_lock.shutil, "which", return_value="/private/tool"), mock.patch.object(
            phase0_lock, "sha256_file", side_effect=PermissionError("/private/tool")
        ), mock.patch.object(
            phase0_lock, "platform_command_observation", return_value={"status": "observed"}
        ):
            record = phase0_lock.host_record()
        self.assertEqual(
            record["executables"][0],
            {"name": "uv", "status": "unavailable", "detail": "PermissionError"},
        )
        self.assertNotIn("/private/tool", json.dumps(record))

    def test_json_duplicate_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text('{"x": 1, "x": 2}', encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "duplicate JSON object member"):
                phase0_lock.load_json(path)

    def test_non_integral_numbers_are_not_silently_canonicalized(self):
        with self.assertRaisesRegex(phase0_lock.LockError, "floating-point"):
            phase0_lock.jcs_bytes({"value": 0.5})

    def test_schema_charset_condition_is_enforced_and_authoring_errors_propagate(self):
        schema_path = Path(__file__).parents[1] / "schemas" / "phase0-lock-inventory-v1.json"
        schema = phase0_lock.load_json(schema_path)
        descriptor = {
            "descriptor_version": "docproc-artifact-descriptor-v1",
            "content_digest": "sha256:" + "a" * 64,
            "byte_length": 1,
            "media_type": "text/plain",
            "content_encoding": "identity",
        }
        with self.assertRaisesRegex(phase0_lock.LockError, "missing schema members: charset"):
            phase0_lock.validate_schema_value(descriptor, schema["$defs"]["descriptor"], schema, "$")

        malformed_condition = {
            "if": {"$ref": "#/$defs/missing"},
            "then": {"const": "unreachable"},
        }
        with self.assertRaisesRegex(phase0_lock.LockError, "unknown definition"):
            phase0_lock.validate_schema_value("value", malformed_condition, {"$defs": {}}, "$")

    def test_evidence_root_inside_worktree_is_rejected(self):
        inside = str(Path(__file__).parents[1] / "phase0" / "private-evidence")
        with self.assertRaisesRegex(phase0_lock.LockError, "outside the Git worktree"):
            phase0_lock.safe_root(inside)


if __name__ == "__main__":
    unittest.main()
