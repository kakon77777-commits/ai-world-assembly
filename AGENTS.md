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

Phase 13 — governed multi-candidate conflict and promotion closure.

Phases 1–12 are complete. Alien Lineage and Relay Station can now be coordinated through one bounded
multi-world orchestration plan while preserving independent child evidence and authority. Current work
must add explicit conflict resolution / promotion policy without turning orchestration success into
canonical write permission.

## Frozen Phase 12 orchestration semantics

- `multi-world-orchestration-plan.v0.1` references existing assembler tasks; it does not create a merged world authority.
- Every child keeps its original `world_scope`, semantic snapshot, Composition Receipt, Asset Graph context, Presentation binding and `assembler-run-receipt.v0.1`.
- Task dependencies form a fail-closed DAG; ready tasks are grouped into deterministic batches bounded by `max_parallel`.
- Concurrent completion timing cannot change receipt identity; results are canonicalized back into reviewed schedule order.
- Every task must claim its target as a world-scoped write claim. Same-key world claims in different worlds are legal; duplicate same-world or shared claims are conflicts.
- Claim conflicts block before child generation. Phase 12 does not choose a winner or silently serialize conflicting writes.
- Orchestration attempt budget must reserve all declared child repair ceilings before execution.
- `multi-world-orchestration-receipt.v0.1` aggregates child evidence hashes per world and structurally keeps `canonical_write=false`.

## Frozen Phase 11 second-world semantics

- Relay Station uses semantic namespace `game.relay_station`; it is a facility/logistics/maintenance world, not an Alien Lineage reskin.
- Bounded domain verbs are `inspect`, `pick_up`, `deliver`, `repair`, and `activate`; built-in `move` remains navigation.
- The same SEDB read adapter, CSC-OCM resolver, Dynamic Asset Graph, CompilableWorld intake/runtime boundary and Three.js target are reused.
- `relay_station.runtime` has StateDelta/EventIR authority only; `relay_station.activation` alone declares `entity_transaction/v0.1`.
- `activate` creates the reviewed Runtime Entity `signal.beacon.001`; dynamic entity allocation remains deferred.
- Three.js dispatches by projection semantic role and contract. Relay Station does not get a second renderer or browser-side world rules.
- Phase 11 adds an independent assembler target `relay_presentation_recipe` using `presentation-effect-recipe.v0.2`; repaired output remains a temporary `validated_candidate` with `canonical_write=false`.
- Alien Lineage Phase 5–10 and assembler Phase 8–9 evidence remain regression gates.

## Frozen Phase 9 broader-proof semantics

- Phase 9 chooses a second assembler modality rather than a second rendering engine because independent repair coverage is the milestone goal.
- The second target is a missing `presentation-effect-recipe.v0.1` artifact required by a dedicated Three.js presentation Asset Graph root.
- Attempt 1 deliberately violates the recipe contract with `runtime_action` and an out-of-bounds duration; attempt 2 repairs only from validator diagnostics.
- The recipe is declarative and presentation-only. It can scale/emissive-pulse a rendered creature after matching EventIR but cannot issue Runtime actions or StateDelta.
- Browser consumption happens through a temporary candidate overlay copied into the built Three.js target after validation; the candidate is not written into canonical presentation source.
- Phase 9 promotion still stops at `validated_candidate` with `canonical_write=false`.
- Existing Phase 5–8 Runtime, Three.js and audio assembler proofs remain regression gates.


## Frozen Phase 10 spawn semantics

- AWA pins CompilableWorld commit `cf37f539e0807499e8b337f80a5f152324c087f2` for `entity_transaction/v0.1`.
- `alien_lineage.spawn` exclusively owns `lay_egg` and `hatch` in Phase 10 packages.
- The module returns create-only EntityDelta; it never calls `EntityRegistry.add()` or `remove()`.
- StateDelta + EntityDelta(create) + EventIR share the upstream transaction rollback boundary.
- One reviewed egg slot and child slot are explicit Runtime facts; no dynamic ID allocator is implied.
- Egg is retained and marked `hatched`; remove/despawn remains out of scope.
- Historical Phase 6 packages remain reproducible through the legacy state-only route.

## Frozen Phase 8 assembler semantics

- `assembler-task.v0.1` wraps one existing `generation-task.v0.1`; it does not invent a target outside the observed Asset Graph gap.
- Generation/capability authority remains `proposal`; `canonical_write` is structurally false.
- The Phase 8 proof target is the deliberate required `artifact.audio.crystal_filterer.attack` gap from Phase 4.
- Candidate bytes are untrusted until validators bind evidence to the exact SHA-256.
- The reference CI producer is deterministic proof infrastructure, not a claim about AI model quality.
- Attempt 1 intentionally fails `validator.audio.non_silent`; attempt 2 repairs from that diagnostic and must pass decode/duration/non-silent checks.
- Promotion means `validated_candidate` only. The canonical Asset Graph registries, SEDB and CompilableWorld state remain unchanged.
- Candidate graph closure is a preview/overlay. It must have no missing required nodes or generation tasks before promotion evidence is emitted.

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
