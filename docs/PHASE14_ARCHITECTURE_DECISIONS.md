# Phase 14 Architecture Decisions

These decisions continue the repository decision sequence as ADR-066 through ADR-070 while keeping historical `DECISIONS.md` byte-stable.

## ADR-066 — Provider transport implements the existing CandidateProducer boundary

**Decision:** Phase 14 does not create a second assembler. `HTTPProviderProducer` implements the existing `CandidateProducer` protocol and returns raw candidate bytes into the same exact-byte validation/repair loop. The stable artifact generator identity is the adapter (`provider-backed.http.v0.1`), not a vendor/model identity.

## ADR-067 — Provider provenance is exact evidence, not semantic identity

**Decision:** `provider-invocation-receipt.v0.1` is locally derived from the configured provider/model plus exact canonical request and raw response SHA-256. Provider-backed runs use `assembler-run-receipt.v0.2` so each invocation evidence hash is transitively covered by the assembler evidence hash. Reference producers remain on v0.1 to preserve prior evidence.

## ADR-068 — Provider bindings are execution policy outside the world plan

**Decision:** `provider-bindings.v0.1` maps orchestration task IDs to provider execution settings without modifying `multi-world-orchestration-plan.v0.1`. Provider routing therefore cannot become world/module semantics or broaden Phase 12 write claims.

## ADR-069 — Provider-backed children reuse Phase 12 authority boundaries

**Decision:** `MultiWorldOrchestrator` accepts an injectable producer resolver but keeps its existing default reference resolver. Provider-backed children remain independently world-scoped, budgeted and evidence-grouped. Same-world/shared claim conflicts still block before generation.

## ADR-070 — Provider identity is not a Phase 13 selection criterion

**Decision:** Competing provider candidates are produced in independent governed runs and projected into the existing Phase 13 comparison contract without provider/model fields. Explicit reviewed policy evidence alone selects a unique winner; legitimate ties remain `blocked_tie`. Provider success, readiness, promotion authority and canonical write remain separate states.
