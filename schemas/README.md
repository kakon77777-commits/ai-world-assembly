# Contracts

The bootstrap contract set is intentionally small and versioned.

Every schema:

- uses JSON Schema Draft 2020-12;
- has a stable `$id`;
- has a top-level `contract` discriminator fixed to its contract/version name;
- rejects unknown top-level fields unless the contract explicitly defines an open metadata map;
- has one valid and one invalid conformance fixture in `fixtures/conformance.v0.1.json`.

Current contracts:

1. `semantic-game-entity.v0.1`
2. `fragment-profile.v0.1`
3. `artifact-reference.v0.1`
4. `module-manifest.v0.1`
5. `capability-contract.v0.1`
6. `composition-receipt.v0.1`
7. `asset-graph-node.v0.1`
8. `asset-graph-edge.v0.1`
9. `generation-task.v0.1`
10. `build-manifest.v0.1`
11. `runtime-binding.v0.1`
12. `presentation-binding.v0.1`

These schemas define exchange structure only. They do not transfer semantic/runtime authority to this repository.
