# Contracts

The bootstrap contract set is intentionally small and versioned. Every schema uses JSON Schema Draft 2020-12, has a stable `$id`, a fixed top-level `contract` discriminator, rejects unknown top-level fields unless explicitly open, and has valid/invalid conformance evidence.

Current contracts include the bootstrap semantic/module/asset/build/binding contracts plus `world-profile.v0.1`, `artifact-validation.v0.1`, `asset-graph-snapshot.v0.1`, `sedb-namespace-snapshot.v0.1`, the CompilableWorld intake contracts, the bounded Alien Lineage runtime contracts, and `runtime-projection.v0.1`.

These schemas define exchange structure only. They do not transfer semantic/runtime authority to this repository.

- `runtime-projection.v0.1` — allowlisted Phase 7 Runtime-to-Presentation projection with generation-bound bindings.
- `assembler-task.v0.1` — bounded Phase 8 generate/repair task over an existing `generation-task.v0.1`, with proposal-only authority and canonical writes structurally disabled.
- `assembler-run-receipt.v0.1` — deterministic Phase 8 evidence receipt for attempts, exact-byte validation, graph preview and validated-candidate promotion.

- `presentation-effect-recipe.v0.1` — declarative Phase 9 Three.js effect candidate contract; bounded visual fields only, with no Runtime action/state authority.

- `alien-lineage-spawn-profile.v0.1` — reviewed bounded parent/egg/child Runtime spawn facts plus required entity transaction capability.
- `alien-lineage-spawn-receipt.v0.1` — Phase 10 deterministic authoring evidence pinned to the CompilableWorld entity-transaction commit.
- `alien-lineage-spawn-assertions.v0.1` — sidecar evidence for dynamic Runtime Entity existence/type/state after ScenarioIR execution.
- `relay-station-runtime-slice.v0.1` — bounded Relay Station runtime module/config declaration for the second world.
- `relay-station-runtime-receipt.v0.1` — deterministic Relay Station authoring evidence pinned to the shared CompilableWorld compatibility target.
- `relay-station-runtime-assertions.v0.1` — Relay Station domain/entity assertion sidecar for the restore-link proof.
- `relay-runtime-projection.v0.1` — allowlisted Relay Station Runtime-to-Presentation projection contract.
- `presentation-effect-recipe.v0.2` — presentation-only effect recipe generalized to bounded `creature_visual` or `relay_visual` targets without Runtime authority.

