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

Phase 3 — CSC-OCM resolver.

Phase 1 contracts and the Phase 2 read-only SEDB adapter are complete. Current work should
resolve a World Profile into a deterministic Composition Receipt. Do not add SEDB canonical
writes, mutate CompilableWorld state, or begin Presentation adapters during this milestone.

## SEDB read boundary

The Phase 2 adapter is intentionally constrained:

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
