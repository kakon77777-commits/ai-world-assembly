# Phase 13 Architecture Decisions

These decisions continue the repository decision sequence as ADR-061 through ADR-065. They are kept in a Phase-specific record so the existing historical `DECISIONS.md` remains byte-stable during this closure.

## ADR-061 — Phase 13 resolves promotion-time candidate conflict, not Phase 12 generation conflict

**Decision:** Phase 12 keeps blocking duplicate same-world or shared write claims before generation. Phase 13 consumes candidates that were validated independently in separate workflows and only later converge on the same governed promotion slot. No Phase 12 preflight rule is weakened or bypassed.

## ADR-062 — Promotion slots preserve world/shared claim semantics

**Decision:** A world-scoped promotion slot is `world:<world_scope>:<key>` while a shared slot is `shared:<key>`. The same world key may be independently promoted in different worlds; a shared key is globally conflicting.

## ADR-063 — Selection uses explicit reviewed criteria; legitimate ties block

**Decision:** `conflict-evaluation-policy.v0.1` uses ordered numeric criteria carried in explicit policy evidence. Last-writer-wins and implicit tiebreakers are structurally false. Input order, timestamps, candidate hashes and run IDs are not legal hidden tiebreak mechanisms. If the explicit policy produces a tie, Phase 13 returns `blocked_tie`.

## ADR-064 — Promotion readiness is evidence, not authority

**Decision:** `promotion-readiness-receipt.v0.1` records candidate conflict/selection closure and always requires separate promotion authority. A ready receipt cannot perform or authorize a canonical write by itself.

## ADR-065 — Promotion authority binds exact readiness and exact candidate but still does not write

**Decision:** `promotion-authority-grant.v0.1` binds exact readiness evidence, policy hash, governed slot, candidate ID/SHA and a nonce. Verification emits `promotion-authority-receipt.v0.1`, but both contracts structurally keep `canonical_write=false`. Writer-side expiry, signature verification, nonce consumption and single-use semantics are deferred until a real writer/protocol exists rather than being simulated in Phase 13.
