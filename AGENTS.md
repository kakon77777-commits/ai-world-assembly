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

Phase 4 — Dynamic Asset Graph MVP.

Phase 1 contracts, the Phase 2 read-only SEDB adapter, and the Phase 3 deterministic CSC-OCM
resolver are complete. Current work should introduce typed assembly nodes/edges, required
closure, missing-node tasks, validation/hash binding and deterministic graph snapshots.
Do not turn the graph into runtime causality, a second semantic database, or a Presentation
scene graph.

## Frozen Phase 3 composition semantics

- `world-profile.v0.1` preserves the original CSC-OCM Version Profile structure under the
  integration-level World Profile name.
- Required dependencies resolve fail-closed and must be acyclic.
- Optional modules named in a World Profile are selected optional modules, not best-effort
  imports; missing selected modules fail resolution.
- v0.1 permits one installed manifest per module ID and locks that version in the receipt.
- explicit module conflicts and compatibility-class policy violations fail resolution.
- capability requirements resolve against provider-independent capability contracts.
- `requires.semantic_entities` is preserved but is not guessed/validated until later intake.

## SEDB read boundary

The Phase 2 adapter remains constrained:

- SQLite `mode=ro`;
- `PRAGMA query_only=ON`;
- no import of SEDB write services;
- namespace is defined by SEDB fields, not by inventing an entity namespace column;
- only active/converged field cells enter v0.1 game semantic projections.

## Validation before claiming completion

Run:

```bash
python -m pip install -e ".[dev]"
pytest -q
```

Any shared contract change must update both a valid and an invalid fixture and must keep every
schema meta-valid under JSON Schema Draft 2020-12.
