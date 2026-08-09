from __future__ import annotations

import copy
import copy
import hashlib
import importlib.util
import json
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
                "origin": {"authority": "test authority", "revision": "rev-1"},
                "acquisition": {
                    "url": "https://example.invalid/admitted-byte",
                    "expected": {"sha256": hashlib.sha256(body).hexdigest(), "byte_length": len(body)},
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

    def test_prefetch_refuses_pending_graph_without_request(self):
        policy = self.policy()
        policy["artifacts"][0]["admission_status"] = "pending-human-review"
        policy["artifacts"][0]["acquisition"] = {"url": None}
        policy["artifacts"][0]["license"]["review_status"] = "pending-human-review"
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(phase0_lock.LockError, "until every required artifact is approved"):
                phase0_lock.prefetch(phase0_lock.validate_policy(policy), Path(temporary))

    def test_prefetch_refuses_denied_graph_without_request(self):
        policy = self.policy()
        denied = copy.deepcopy(policy["artifacts"][0])
        denied["id"] = "denied-byte"
        denied["required"] = False
        denied["admission_status"] = "denied"
        denied["acquisition"] = {"url": None}
        policy["artifacts"].append(denied)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(phase0_lock.LockError, "denied artifacts in graph"):
                phase0_lock.prefetch(phase0_lock.validate_policy(policy), Path(temporary))

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
        policy = phase0_lock.validate_policy(self.policy())
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
            (observations / "approved-byte.json").write_text(json.dumps(observation), encoding="utf-8")
            schema = root / "schema.json"
            schema.write_text("{}\n", encoding="utf-8")
            phase0_lock.record_prefetch_failure(root, "approved-byte", "simulated rejected retry")
            evidence_address = phase0_lock.seal(policy, root, schema, "b" * 40)
            self.assertTrue(evidence_address.startswith("evr1:sha256:"))
            phase0_lock.verify(root, evidence_address)
            with self.assertRaisesRegex(phase0_lock.LockError, "invalid evidence address"):
                phase0_lock.verify(root, "not-an-evidence-address")

            record = root / "records" / evidence_address.replace(":", "_")
            envelope_path = record / "envelope.json"
            original_envelope = envelope_path.read_text(encoding="utf-8")
            envelope = json.loads(original_envelope)
            envelope["input_ids"].append("tampered")
            envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "evidence address mismatch"):
                phase0_lock.verify(root, evidence_address)
            envelope_path.write_text(original_envelope, encoding="utf-8")

            payload_path = record / "payload.json"
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["failures"][0]["message"], "simulated rejected retry")
            payload_path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "payload address mismatch"):
                phase0_lock.verify(root, evidence_address)

    def test_platform_command_output_is_redacted_and_bounded(self):
        completed = subprocess.CompletedProcess(
            args=["/usr/bin/sw_vers"], returncode=0, stdout="reading /private/token", stderr=""
        )
        with mock.patch.object(phase0_lock.subprocess, "run", return_value=completed):
            observation = phase0_lock.platform_command_observation("sw_vers")
        self.assertEqual(observation["output"], "<redacted-local-path-output>")

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

    def test_json_duplicate_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text('{"x": 1, "x": 2}', encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "duplicate JSON object member"):
                phase0_lock.load_json(path)

    def test_non_integral_numbers_are_not_silently_canonicalized(self):
        with self.assertRaisesRegex(phase0_lock.LockError, "floating-point"):
            phase0_lock.jcs_bytes({"value": 0.5})


if __name__ == "__main__":
    unittest.main()
