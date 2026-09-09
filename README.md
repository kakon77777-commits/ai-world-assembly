# AI World Assembly

Internal integration workspace for the AI-Native Game / World Assembly architecture.

This repository is an **integration layer**, not a replacement for SEDB or CompilableWorld.

## Authority boundaries

- **SEDB** — semantic/content truth, provenance, candidate/canonical governance.
- **CSC-OCM** — module/capability composition and compatibility.
- **Dynamic Asset Graph** — assembly topology, dependencies, missing-node tasks and validation/hash binding.
- **CompilableWorld** — committed runtime state/action/event authority.
- **Presentation** — rendering, input, audio, UI, target-local physical state.
- **AI World Assembler** — proposal, planning, generation, validation and repair across those boundaries.

## Current status

- **Phase 1 — Contracts:** complete.
- **Phase 2 — SEDB read adapter:** complete.
- **Phase 3 — CSC-OCM resolver:** complete.
- **Phase 4 — Dynamic Asset Graph MVP:** complete.
- **Phase 5 — CompilableWorld intake adapter:** complete.
- **Phase 6 — Alien Lineage runtime slice:** complete.
- **Phase 7 — Three.js presentation adapter:** complete.
- **Next: Phase 8 — bounded AI World Assembler loop.**

Phase 7 adds a live localhost Three.js presentation sidecar over the Phase 6 Runtime. Browser input becomes ActionIR only inside the Python bridge; EventIR becomes presentation effects, and scene reload changes only presentation identity.

## Bootstrap roadmap

1. versioned JSON Schema contracts — **complete**;
2. valid/invalid conformance fixtures — **complete**;
3. deterministic contract validation — **complete**;
4. SEDB read adapter — **complete**;
5. CSC-OCM resolver — **complete**;
6. Dynamic Asset Graph MVP — **complete**;
7. CompilableWorld intake adapter — **complete**;
8. Alien Lineage runtime slice — **complete**;
9. Three.js first presentation target — **complete**;
10. bounded AI World Assembler loop — **next**.

## Quick start

```bash
python -m pip install -e ".[dev]"
pytest -q

awa-cw-intake emit \
  --semantic-snapshot fixtures/sedb/expected.game.alien_lineage.snapshot.json \
  --composition-receipt fixtures/csc_ocm/expected.alien_lineage.composition-receipt.json \
  --asset-graph-snapshot fixtures/compilableworld_intake/asset-graph.resolved.json \
  --plan fixtures/compilableworld_intake/alien_lineage.intake-plan.json \
  --out build/alien-lineage-cw

awa-alien-lineage build \
  --semantic-snapshot fixtures/sedb/expected.game.alien_lineage.snapshot.json \
  --composition-receipt fixtures/csc_ocm/expected.alien_lineage.composition-receipt.json \
  --asset-graph-snapshot fixtures/compilableworld_intake/asset-graph.resolved.json \
  --plan fixtures/alien_lineage_runtime/alien_lineage.intake-plan.json \
  --slice fixtures/alien_lineage_runtime/runtime-slice.json \
  --out build/alien-lineage-phase6

# After compiling Phase 6 with the pinned CompilableWorld runtime:
cd presentation/threejs && npm install --no-audit --no-fund --package-lock=false && npm test && npm run build && cd ../..
awa-threejs verify-assets presentation/threejs/dist
awa-threejs serve build/alien-lineage-phase6-runtime/world.package.json \
  --binding fixtures/threejs/alien-lineage.presentation-binding.json \
  --static-dir presentation/threejs/dist
```

See `docs/SEDB_READ_ADAPTER.md`, `docs/CSC_OCM_RESOLVER.md`, `docs/DYNAMIC_ASSET_GRAPH.md`, `docs/COMPILABLEWORLD_INTAKE.md`, `docs/ALIEN_LINEAGE_RUNTIME.md`, and `docs/THREEJS_PRESENTATION.md`.

## Non-goals for the bootstrap

- no SEDB kernel rewrite;
- no SEDB canonical write path;
- no CompilableWorld kernel rewrite;
- no provider routing inside module semantics;
- no runtime causality in the Dynamic Asset Graph;
- no live C3/C4 module migration;
- no multiplayer;
- no cloud marketplace;
- no autonomous core promotion;
- no Godot/Unity adapter until the first Three.js proof is stable.

See `DECISIONS.md`, `PROJECT_STATE.json`, and `AGENTS.md`.
