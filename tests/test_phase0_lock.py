from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
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

            payload_path = root / "records" / evidence_address.replace(":", "_") / "payload.json"
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["failures"][0]["message"], "simulated rejected retry")
            payload_path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(phase0_lock.LockError, "payload address mismatch"):
                phase0_lock.verify(root, evidence_address)

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
