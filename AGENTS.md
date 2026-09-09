# AGENTS.md

## Mission

Build the AI World Assembly integration layer without collapsing existing authority boundaries.

## Frozen bootstrap invariants

1. Do not modify SEDB or CompilableWorld kernels from this repository.
2. SEDB integration starts read-only.
3. Generated content is candidate-first; generation is not canonicalization.
4. Runtime semantic mutation must eventually flow through CompilableWorld ActionIR / StateDelta / EventIR.
5. Presentation must not contain hidden world rules.
6. Module contracts describe capabilities, not provider identities.
7. Search/reuse before generating a new fragment or module.
8. Unknown data is legal; do not invent canonical values.
9. Every shared contract is versioned and fail-closed on unknown/invalid structure.
10. Keep repair scope local to the failing layer.

## Current milestone

Phase 8 — bounded AI World Assembler loop.

Phases 1–7 are complete. The Alien Lineage Runtime is projected through a live Three.js sidecar
without moving semantic/runtime authority into Presentation. Current work should add one bounded
AI World Assembler loop over the existing authority stack, with candidate-first generation, explicit
validation evidence, local repair scope and promotion only after the canonical gates pass.

## Frozen Phase 7 presentation semantics

- Three.js receives an allowlisted `runtime-projection.v0.1`, never an unrestricted StateStore dump.
- Browser input is a presentation intent; the Python sidecar converts it to CompilableWorld ActionIR.
- Presentation never constructs StateDelta or mutates EntityRegistry/StateStore directly.
- EventIR maps only to Presentation effects such as rebuild/VFX/UI; it does not execute world rules.
- Runtime bindings are generation-bound. Reload changes Presentation instance identity while preserving World Entity identity.
- Stale generation/instance intents fail closed.
- Three.js is pinned to `0.180.0`; built target artifacts are SHA-256 verified before the browser gate.
- The live sidecar remains localhost/reference-MVP scope; WebSocket, multiplayer and dynamic spawn are not Phase 7 features.

## Frozen Phase 6 runtime semantics

- `alien_lineage.runtime` is an external AWA Runtime Module, not a CompilableWorld builtin.
- Runtime actions are exactly `feed`, `mutate`, `grow`, `lay_egg`, `hatch`, and `enter_rift`.
- Lineage side effects commit only through StateDelta/EventIR.
- Feed gain, mutation cost, growth threshold, and egg cost are pure FunctionIR.
- Phase 6 never calls `EntityRegistry.add()` from Module evaluation; dynamic child spawning is deferred.
- `world.runtime_extensions` must declare the exact external module/version/entrypoint before installation.
- CI pins the CompilableWorld compatibility target and runs the full lineage ScenarioIR.
- Portable ScenarioIR assertions remain inside the upstream read whitelist; domain-state/list assertions use the versioned AWA sidecar.

## Frozen Phase 5 intake semantics

- Upstream semantic/composition/asset data does not uniquely determine Runtime authoring facts.
- Unknown Runtime facts must be stated in a reviewed `compilableworld-intake-plan.v0.1`; never guessed.
- Intake requires the referenced Composition modules to be resolved.
- Intake requires the Asset Graph snapshot roots to match and required build state to be complete.
- Every required artifact entering intake must have effective validation state `passed`.
- Runtime entity names are grounded in SEDB semantic labels; Runtime IDs/components/rooms come from the reviewed plan.
- The adapter emits existing CompilableWorld files; it does not define a second Runtime Package format.
- Compatibility proof is pinned to CompilableWorld master `70141f364220697fe037cd0047604c608ad4c074`.

## Frozen Dynamic Asset Graph semantics

- The graph is assembly topology, not runtime causality or a Presentation scene graph.
- Only `requires` + `required=true` edges form the required closure and cycle-check subgraph.
- Missing required dependencies emit deterministic `generation-task.v0.1` proposals.
- Missing optional dependencies are legal and do not auto-generate work.
- Validation evidence binds to an exact artifact SHA-256; mismatched evidence is stale.
- Required-build snapshots are root-scoped and ignore unrelated optional edges.
- Phase 4 supports null or exact `vN.N` edge version constraints only.

## Frozen Phase 3 composition semantics

- Required dependencies resolve fail-closed and must be acyclic.
- Optional modules named in a World Profile are selected optional modules, not best-effort imports.
- v0.1 permits one installed manifest per module ID and locks that version in the receipt.
- explicit module conflicts and compatibility-class policy violations fail resolution.
- capability requirements resolve against provider-independent capability contracts.
- `requires.semantic_entities` is preserved but is not guessed/validated until intake.

## SEDB read boundary

The Phase 2 adapter remains constrained:

- SQLite `mode=ro`;
- `PRAGMA query_only=ON`;
- no import of SEDB write services;
- namespace is defined by SEDB fields;
- only active/converged field cells enter v0.1 game semantic projections.

## Validation before claiming completion

Run:

```bash
python -m pip install -e ".[dev]"
pytest -q
```

Any shared contract change must update both a valid and an invalid fixture and must keep every
schema meta-valid under JSON Schema Draft 2020-12.
