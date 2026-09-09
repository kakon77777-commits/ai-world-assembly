# CompilableWorld Intake Adapter — Phase 5

## Purpose

Phase 5 translates already-governed AWA inputs into the **existing CompilableWorld Authoring Layer**.
It does not alter the CompilableWorld Kernel.

The boundary is:

```text
SEDB namespace snapshot
+ CSC-OCM Composition Receipt
+ Dynamic Asset Graph snapshot
+ reviewed CompilableWorld Intake Plan
                ↓
          AWA intake adapter
                ↓
CompilableWorld manifest/world/CSV/ScenarioIR authoring
                ↓
existing CompilableWorld validate / compile / scenario-run
```

## Why an Intake Plan exists

The upstream semantic/composition/asset layers do not uniquely determine Runtime authoring facts
such as exact rooms, exits, Runtime entity IDs/components, player spawn or ScenarioIR. The adapter
must not invent these facts. `compilableworld-intake-plan.v0.1` is therefore an explicit reviewed
mapping surface.

## Implemented fail-closed gates

The adapter rejects:

- a tampered SEDB namespace snapshot hash;
- duplicate semantic/runtime/room/exit identity;
- unresolved semantic references;
- required composition modules absent from the Composition Receipt;
- graph-root mismatch;
- incomplete Dynamic Asset Graph snapshots;
- required artifacts whose effective validation state is not `passed`;
- Runtime entities/items/exits referencing undeclared rooms;
- a missing default player or spawn room.

## Deterministic outputs

The adapter emits exactly the existing CompilableWorld source families used by the Phase 5 proof:

- `manifest.json`
- `world.json`
- `data/rooms.csv`
- `data/exits.csv`
- `data/entities.csv`
- `data/items.csv`
- `quests.json`
- `scenarios.json`

`awa-intake-receipt.json` records canonical source hashes, per-output SHA-256 values and one
root `authoring_sha256`.

## Compatibility proof

CI pins the CompilableWorld compatibility target to:

```text
kakon77777-commits/compilableworld-runtime-mvp
master @ 70141f364220697fe037cd0047604c608ad4c074
```

On the generated Alien Lineage intake fixture CI runs the real external commands:

```text
python -m compilableworld validate
python -m compilableworld compile
python -m compilableworld scenario-run ... alien-lineage.move-smoke
```

This is intentionally an external conformance proof rather than copied compiler logic inside AWA.

## Non-goals

- no CompilableWorld Kernel change;
- no automatic derivation of unknown Runtime facts;
- no replacement of CompilableWorld schemas/compiler;
- no claim that CSC-OCM module IDs are already Runtime Module implementations;
- no Presentation adapter yet.
