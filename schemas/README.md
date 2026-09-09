# Contracts

The bootstrap contract set is intentionally small and versioned. Every schema uses JSON Schema Draft 2020-12, has a stable `$id`, a fixed top-level `contract` discriminator, rejects unknown top-level fields unless explicitly open, and has valid/invalid conformance evidence.

Current contracts include the bootstrap semantic/module/asset/build/binding contracts plus `world-profile.v0.1`, `artifact-validation.v0.1`, `asset-graph-snapshot.v0.1`, `sedb-namespace-snapshot.v0.1`, the CompilableWorld intake contracts, the bounded Alien Lineage runtime contracts, and `runtime-projection.v0.1`.

These schemas define exchange structure only. They do not transfer semantic/runtime authority to this repository.

- `runtime-projection.v0.1` — allowlisted Phase 7 Runtime-to-Presentation projection with generation-bound bindings.
