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

Phase 5 — CompilableWorld intake adapter.

Phases 1–4 are complete. Current work should translate SEDB semantic projections, CSC-OCM
Composition Receipts and Dynamic Asset Graph build closure into the **existing CompilableWorld
authoring/runtime-package pipeline**. Adapter-first remains mandatory: do not modify the
CompilableWorld Kernel unless a concrete contract gap is proven by tests.

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
