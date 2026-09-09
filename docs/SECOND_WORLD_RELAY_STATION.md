# Phase 11 — Relay Station Second World Vertical Slice

## Purpose

Relay Station is the first deliberate proof that AI World Assembly is not an Alien-Lineage-specific framework. It changes the semantic domain, module composition, Runtime verbs and world objective while reusing the same governed assembly stack.

$$
SEDB\rightarrow CSC\text{-}OCM\rightarrow DynamicAssetGraph\rightarrow CompilableWorld\rightarrow Three.js\rightarrow AIWorldAssembler
$$

## World

Semantic namespace: `game.relay_station`.

The bounded world is a damaged relay facility. `operator.relay-runner.001` inspects and transports `item.phase-coupler`, moves through the hangar/conduit/core, delivers the coupler, repairs `facility.storm-relay-core.001`, then activates the restored link.

Domain verbs are:

- `inspect`
- `pick_up`
- `deliver`
- `repair`
- `activate`

CompilableWorld built-in `move` remains navigation.

## Authority split

`relay_station.runtime` owns inspect/pick-up/deliver/repair and commits StateDelta + EventIR only.

`relay_station.activation` alone declares `entity_transaction/v0.1`. Successful activation commits:

$$
StateDelta + EntityDelta(create) + EventIR
$$

atomically and creates reviewed Runtime Entity `signal.beacon.001`. Modules do not call EntityRegistry mutation APIs directly. Durable EventLog failure must rollback state, registry membership, dynamic-entity bookkeeping and log append together.

## Reused stack

Phase 11 does not create a second world framework. Relay Station uses:

- the same read-only SEDB projection adapter;
- the same CSC-OCM resolver and Composition Receipt;
- the same Dynamic Asset Graph implementation;
- the same CompilableWorld intake/compiler/runtime compatibility target;
- the same Three.js `0.180.0` presentation target and live sidecar;
- the same bounded AI World Assembler orchestration/evidence model.

The Three.js bridge dispatches by semantic role / projection contract. Relay presentation state is allowlisted in `relay-runtime-projection.v0.1`; the browser does not receive unrestricted Runtime stores or entity-write authority.

## Assembler proof

The Relay presentation graph contains a deliberate missing `artifact.presentation.threejs.relay_activation_recipe`. The assembler target kind is `relay_presentation_recipe`.

Attempt 1 deliberately violates presentation authority/bounds with a forbidden `state_delta` field and an oversized duration. Attempt 2 repairs only from validator diagnostics and produces `presentation-effect-recipe.v0.2` targeting `relay_visual`.

Promotion still ends at:

$$
validated\_candidate,\qquad canonical\_write=false
$$

The validated recipe is copied only into a temporary built-target overlay for Chromium evidence. Canonical source and graph registries remain unchanged.

## Acceptance evidence

Phase 11 closes only when CI proves all of the following on the same compatibility pin:

1. Relay semantic snapshot can be regenerated from the minimal SQLite SEDB fixture through the read-only adapter.
2. Relay composition receipt and base Asset Graph snapshot reproduce deterministically.
3. Real CompilableWorld validate/compile accepts Relay authoring.
4. The restore-link scenario completes and creates true `signal.beacon.001`.
5. Durable EventLog failure during activation rolls back all state/entity changes.
6. The existing Three.js target renders/operates Relay Station and observes the spawned beacon without Runtime write authority.
7. The Relay presentation recipe repair closes its candidate graph and works only as a temporary browser overlay.
8. Alien Lineage and Phase 8–10 regression gates remain green.

## Deferred

- dynamic Runtime entity ID allocation;
- entity remove/despawn transaction semantics;
- second renderer;
- cross-world Runtime migration;
- multi-world task scheduling and promotion conflict resolution.

Those become meaningful only after this second independent vertical proof.
