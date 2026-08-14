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
            artifact.parent.mkdir()
            artifact.write_bytes(body)
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
            observations.mkdir()
            observation_path = observations / "approved-byte.json"
            observation_path.write_text("[]", encoding="utf-8")
            schema = Path(__file__).parents[1] / "schemas" / "phase0-lock-inventory-v1.json"
            with self.assertRaisesRegex(phase0_lock.LockError, "observation must be an object"):
                phase0_lock.seal(policy, root, schema, "b" * 40)
            observation_path.write_text(json.dumps(observation), encoding="utf-8")
            exception_observation = copy.deepcopy(observation)
            exception_observation["artifact_id"] = "exception-byte"
            exception_observation["requested_url"] = "https://example.invalid/exception-byte"
            exception_observation["final_url"] = "https://example.invalid/exception-byte"
            (observations / "exception-byte.json").write_text(
                json.dumps(exception_observation), encoding="utf-8"
            )
            phase0_lock.record_prefetch_failure(root, "approved-byte")
            evidence_address = phase0_lock.seal(policy, root, schema, "b" * 40)
            self.assertTrue(evidence_address.startswith("evr1:sha256:"))
            phase0_lock.verify(root, evidence_address, schema)
            artifact.write_bytes(b"tampered")
            with self.assertRaisesRegex(phase0_lock.LockError, "does not match sealed inventory"):
                phase0_lock.verify(root, evidence_address, schema)
            artifact.write_bytes(body)
            with self.assertRaisesRegex(phase0_lock.LockError, "invalid evidence address"):
                phase0_lock.verify(root, "not-an-evidence-address", schema)

            record = root / "records" / evidence_address.replace(":", "_")
            envelope_path = record / "envelope.json"
            original_envelope = envelope_path.read_text(encoding="utf-8")
            envelope_path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "evidence envelope is invalid"):
                phase0_lock.verify(root, evidence_address, schema)
            envelope_path.write_text(original_envelope, encoding="utf-8")
            envelope = json.loads(original_envelope)
            envelope["input_ids"].append("tampered")
            envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "does not bind"):
                phase0_lock.verify(root, evidence_address, schema)
            envelope_path.write_text(original_envelope, encoding="utf-8")

            payload_path = record / "payload.json"
            original_payload = payload_path.read_text(encoding="utf-8")
            payload = json.loads(original_payload)
            self.assertEqual(payload["failures"][0]["message"], "admitted request did not complete byte verification")
            self.assertEqual(
                payload["reviewed_exceptions"],
                [{"artifact_id": "exception-byte", "license": exception["license"]}],
            )
            payload["inventory"][0]["artifact_descriptor"]["address"] = "art1:sha256:" + "0" * 64
            payload_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "artifact descriptor address mismatch"):
                phase0_lock.verify(root, evidence_address, schema)
            payload_path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "missing schema members"):
                phase0_lock.verify(root, evidence_address, schema)

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
            uname.write_text("#!/bin/sh\necho Darwin\n", encoding="utf-8")
            uname.chmod(0o755)
            environment = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"]}
            result = subprocess.run(
                ["sh", str(wrapper), "--", "sh", "-c", "exit 0"], text=True, capture_output=True, env=environment
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("refusing run", result.stderr)

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

    def test_json_duplicate_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text('{"x": 1, "x": 2}', encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "duplicate JSON object member"):
                phase0_lock.load_json(path)

    def test_non_integral_numbers_are_not_silently_canonicalized(self):
        with self.assertRaisesRegex(phase0_lock.LockError, "floating-point"):
            phase0_lock.jcs_bytes({"value": 0.5})

    def test_evidence_root_inside_worktree_is_rejected(self):
        inside = str(Path(__file__).parents[1] / "phase0" / "private-evidence")
        with self.assertRaisesRegex(phase0_lock.LockError, "outside the Git worktree"):
            phase0_lock.safe_root(inside)


if __name__ == "__main__":
    unittest.main()
