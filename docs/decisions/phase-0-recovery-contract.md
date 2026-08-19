# Phase 0 expired-window recovery contract

- **Status:** Proposed; pending the required human, explicitly non-authorizing approval.
- **Recovery reason:** `phase0-window-expired-before-resolution`
- **Prior authorization:** [issue #13 comment `5227376778`](https://github.com/monocongo/docproc/issues/13#issuecomment-5227376778), created `2026-08-08T17:54:45Z`
- **Expired deadline:** `2026-08-10T17:54:45Z` (`T0 + 48 hours`)
- **Base contract:** [Phase 0 go-adjust-cut gate at `d5e0f3dfca08f6bc11ad02a6ee275aef0e43b2f9`](https://github.com/monocongo/docproc/blob/d5e0f3dfca08f6bc11ad02a6ee275aef0e43b2f9/docs/decisions/phase-0-go-adjust-cut-gate.md)
- **Base blueprint:** [PDF-processing pipeline blueprint at `367454a103c55a5d5a363b5be26cc43033cc2623`](https://github.com/monocongo/docproc/blob/367454a103c55a5d5a363b5be26cc43033cc2623/docs/planning/pdf-processing-pipeline-plan.md)

This recovery contract changes only expired-window authorization, the issue #20/#21 NAF boundary, and the no-egress preflight. Every unmodified rule in the base contract and blueprint remains in force. If this record conflicts with either base document on those three topics, this recovery contract controls after it is approved and merged.

This document is not approval or authorization. No artifact, NAF content, parser/VLM request, or measured service run may occur until the approval and superseding-authorization sequence below is complete.

## Frozen expired-window result

The old Phase 0 window expired before any gate had retained final evidence. No Cut was recorded. Under Gate WALK and `Cut > Adjust > Go`:

- LIC, CORPUS, PARSER, VLM, MACHINE, and WALK are `Adjust` with reason `phase0-window-expired-before-resolution`;
- Overall Phase 0 is `Adjust`;
- the prior conditional permission is no longer usable for acquisition, measurement, or durable walking work; and
- PR #26 and PR #27 are reversible harness work only, not admission evidence or a Gate outcome.

The publication-safe candidate record is `phase0/decisions/expired-window-adjust.json` with paired `phase0/decisions/expired-window-adjust.md`. Human approval of that exact commit must remain explicitly non-authorizing.

## Required approval and reset sequence

The sequence is strict:

1. Merge only publication-safe record/contract changes after review.
2. A human approver posts one new, unedited, explicitly **non-authorizing** #25 comment linking the exact decision-record commit. An AI-generated comment cannot satisfy this step.
3. A human reviews the revised blueprint and this recovery contract at exact full commits.
4. The human posts one new, unedited Implementation-authorization comment in #13 that:
   - links the exact revised blueprint and recovery-contract commits;
   - links comment `5227376778` and explicitly supersedes it;
   - says it is the sole active Implementation authorization;
   - states that its GitHub `createdAt` is the new T0; and
   - retains all gate, scope, publication, and stop conditions.
5. Re-fetch that comment and issue timeline. Calculate `new T0 + 48 hours` before any acquisition or measurement.

Editing the old comment, an AI-authored comment, approving a PR, merging a harness, or approving the expired Adjust record does not establish T0.

## #20 Gate LIC versus #21 NAF boundary

### #20 owns non-content-bearing NAF admission

Issue #20 may close its scoped base/primary admission only after it retains human-reviewed, non-content-bearing NAF evidence sufficient to authorize #21's later acquisition route:

- publisher repository identity and the exact annotation, image-release, and license revisions from `NAF-linked-v3`;
- release asset ID, stable publisher URL, expected archive byte length and SHA-256, expected image-manifest/count/split identities, and expected eligibility-ledger identity as policy values only;
- the exact CDLA license text/hash, publisher identification, required attribution/source links, residual source-rights caveat, distribution/publication disposition, and human terms review;
- an explicit rule that only #21 may request annotation/archive/content bytes; and
- a reviewed #21 acquisition policy digest or immutable policy template that cannot silently substitute a mirror.

#20 may acquire non-content-bearing publisher license/release metadata only when each byte is separately approved and recorded. It must not acquire or seal the NAF annotation tree, image archive, JPEGs, transcriptions, converted PDFs, eligibility ledger, or other content-bearing Data/Enhanced Data. It must not invent observations for those deferred bytes.

`EVID-LOCK-INVENTORY-001` records NAF source/terms admission as a deferred-content route, not as an observed NAF download. #20's publication-safe summary must say `NAF content acquisition: deferred to #21; not observed`.

### #21 owns NAF content acquisition and observation

Only after #20's exact scoped admission is accepted and the new authorization is active may #21:

- fetch the annotation revision and release asset from the admitted publisher origins;
- record observed final URLs, sizes, SHA-256 values, archive/image manifests, and split/ledger checks;
- retain NAF Data, Enhanced Data, transcriptions, ledgers, and content-bearing evidence outside Git; and
- bind those observations into `EVID-CORPUS-VERIFICATION-001`.

Any identity, hash, size, count, license, split, manifest, or ledger mismatch is Adjust and invokes the diagnosis workflow. It never backfills #20 with an invented observation or silently substitutes a mirror.

## Descendant- and container-covering no-egress control

A host PF anchor is not an accepted control. The reference control is a **hardware-isolated, no-uplink measurement network** covering the entire reference Mac and Docker Desktop VM:

1. Connect the reference Mac only to a dedicated wired switch/VLAN with no routed uplink, no default gateway, and firewall/switch policy that drops IPv4 and IPv6 forwarding beyond the isolated segment.
2. Disable and verify every other host uplink or tunnel: Wi-Fi, Bluetooth PAN, additional Ethernet/Thunderbolt interfaces, VPNs, Internet Sharing, and unreviewed virtual adapters. Prevent interface changes for the measured interval.
3. Retain outside Git the reviewed switch/firewall configuration digest, physical-port/VLAN identity, host interface/route snapshots, Docker network inventory, UTC/monotonic clocks, and cleanup record.
4. After online prefetch is complete, activate the boundary before any measured process starts. Do not weaken it until all measured processes, descendants, and containers have exited.
5. Preflight from all applicable execution domains:
   - the exact host harness process and a spawned descendant;
   - one ephemeral probe container attached in turn to every Docker network used by MinIO/OpenSearch or a measured helper; and
   - any separately isolated guest introduced by an approved contract revision.
6. Each domain must fail direct external IPv4, direct external IPv6, DNS, and HTTPS probes. A successful external connection makes preflight invalid and stops work.
7. In the same preflight, required local endpoints must succeed under their frozen predicates: host Ollama via loopback, MinIO/OpenSearch via their reviewed local bindings, and container-internal service health where applicable.
8. Continuously retain host interface/route changes, packet capture or equivalent egress-interface counters, hardware-boundary drop counters, Docker lifecycle/network events, and required local-service probes. Any unreviewed interface, route, network, container, or external packet is a Gate LIC mismatch.
9. Postflight repeats the denial and local-health probes before boundary cleanup. Cleanup is recorded but never erases enforcement evidence.

This boundary covers descendants because it removes every routable host uplink, and covers Docker containers because Docker Desktop's VM/NAT has no physical or routed upstream path. Localhost and container-internal communication remain available. A software rule inside only the measured process, one container, one PF anchor, or one Docker network is insufficient.

A different isolation mechanism requires a separately reviewed contract revision demonstrating equivalent host, descendant, guest, and container coverage before use.

## New-window stop conditions

After a new T0 exists, stop immediately on any of these:

- the new `T0 + 48 hours` expires before the complete decision record;
- any required exact-byte or source/terms review remains pending, denied, mismatched, or `NOASSERTION`;
- the NAF ownership boundary is bypassed;
- the hardware no-egress boundary or any required probe/counter is missing or invalid;
- an observation is only an unauthenticated same-UID assertion without the required independent capture receipt;
- content-bearing/restricted material would enter Git or public evidence;
- any gate is Adjust/Cut; or
- a contract, threshold, candidate, population, service, or evidence requirement is substituted without an approved revision.

No durable walking-vertical implementation may start without six retained Go outcomes under the new window.
