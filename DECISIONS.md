# Architecture Decisions

## ADR-001 — Existing authorities remain separate

**Decision:** SEDB and CompilableWorld remain independent systems. AI World Assembly integrates them through adapters/contracts.

## ADR-002 — Contract-first bootstrap

**Decision:** Establish versioned exchange contracts and conformance tests before autonomy or game-content scale.

## ADR-003 — One integration repository for v0.1

**Decision:** Keep contracts, reference adapters, graph prototype and assembler reference code in this repository initially. Split only when scale justifies it.

## ADR-004 — SEDB read-first

**Decision:** The first SEDB adapter is read-only. No direct canonical mutation from this repo during the bootstrap.

## ADR-005 — CompilableWorld adapter-first

**Decision:** Generate existing CompilableWorld authoring inputs before considering Kernel changes.

## ADR-006 — Three.js first

**Decision:** The first presentation proof uses Three.js because the target is browser-native, agent-observable and already demonstrated by the Alien Lineage prototype.

## ADR-007 — Godot later, only if justified

**Decision:** Add Godot after the first end-to-end contracts are stable, or sooner only if product requirements demand physics/animation/native tooling.

## ADR-008 — Alien Lineage first vertical slice

**Decision:** Use a deliberately small Alien Lineage-like slice rather than a Living World RPG to reduce debugging dimensions.

## ADR-009 — Candidate before canon

**Decision:** AI generation defaults to candidate/proposal scope. Canonicalization requires a separate authority boundary.

## ADR-010 — No presentation world authority

**Decision:** Presentation input maps to semantic intent/ActionIR; presentation effects do not silently mutate persistent world semantics.

## ADR-011 — SEDB adapter enforces read-only at the database boundary

**Decision:** AWA opens the SEDB SQLite source using URI `mode=ro` plus `PRAGMA query_only=ON` and does not import SEDB write services. This makes the Phase 2 read-only claim executable rather than conventional.

## ADR-012 — Namespace projection follows field ownership

**Decision:** SEDB namespaces live on fields, not entities. AWA namespace projections therefore select an entity's active/converged field cells in the requested namespace. Proposed, merged, split and deprecated field definitions are excluded from v0.1 game semantic projections.

## ADR-013 — Namespace snapshot envelope remains adapter-local in Phase 2

**Decision:** `sedb-namespace-snapshot.v0.1` is emitted and tested by the adapter but is not promoted into the shared contract inventory until another system consumes it. This avoids adding a shared schema before a real cross-system boundary requires one.

## ADR-014 — World Profile specializes the original CSC-OCM Version Profile for integration

**Decision:** `world-profile.v0.1` keeps the original CSC-OCM profile structure (`core_version`, required/optional/disabled modules, capability profile and compatibility policy) while using a world-level name because AWA composes executable worlds rather than only historical release versions.

## ADR-015 — Optional modules listed in a World Profile are selected and fail closed

**Decision:** In resolver v0.1, `modules.optional` means modules selected for this profile but optional relative to the common core. A listed optional module must resolve; the resolver never silently drops a missing selected module. Omit or disable it explicitly instead.

## ADR-016 — Resolver v0.1 allows one installed manifest per module ID

**Decision:** Until a version-selection/range contract exists, the module registry rejects duplicate module IDs even if versions differ. The selected manifest version is locked into the Composition Receipt.

## ADR-017 — Provider identity is structurally excluded from composition semantics

**Decision:** World Profile, Module Manifest and Capability Contract schemas remain provider-independent and fail closed on undeclared provider fields. Phase 3 resolves capabilities but does not route them to a model/vendor.

## ADR-018 — Semantic entity requirements are preserved but not guessed in Phase 3

**Decision:** `requires.semantic_entities` remains part of Module Manifest, but the Phase 3 resolver does not claim those references are satisfied without an explicit SEDB snapshot/intake boundary. Cross-layer satisfaction is deferred rather than inferred.

## ADR-019 — Dynamic Asset Graph is assembly topology, not runtime causality

**Decision:** Phase 4 graph edges describe build/content dependencies and evidence relationships. Runtime causal state transitions remain CompilableWorld authority, and Presentation scene hierarchy remains Presentation-local.

## ADR-020 — Only the required dependency subgraph must be acyclic

**Decision:** `requires` edges with `required=true` define the closure/cycle-check graph. Optional and non-dependency relations may form cycles without being rejected as build cycles.

## ADR-021 — Missing required dependencies become Generation Task proposals

**Decision:** A missing target on a required dependency is represented explicitly and produces a deterministic `generation-task.v0.1` proposal. Missing optional targets remain legal without automatic generation; missing targets on non-dependency relations fail closed.

## ADR-022 — Validation evidence is bound to exact artifact bytes

**Decision:** `artifact-validation.v0.1` records the artifact SHA-256 it validated. Evidence whose hash no longer matches the current `artifact-reference.v0.1` is stale and cannot satisfy validation.

## ADR-023 — Required-build snapshots are root-scoped and ignore unrelated optional edges

**Decision:** `asset-graph-snapshot.v0.1` hashes the selected required closure, its required/validation edges, selected artifacts and validation evidence. Unrelated optional relations do not perturb the required build identity.

## ADR-024 — Graph version constraints are exact-only in v0.1

**Decision:** `version_constraint` is either null or an exact `vN.N` node version during Phase 4. Range selection is deferred instead of being silently interpreted.
