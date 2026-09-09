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
- **Phase 8 — bounded AI World Assembler loop:** complete.
- **Phase 9 — broader assembler proof with declarative presentation recipe:** complete.
- **Phase 10 — transaction-safe Runtime spawn:** complete.
- **Next: Phase 11 — second world vertical slice.**

Phase 8 adds the first bounded assembler loop over the deliberate Crystal Filterer attack-audio gap. Phase 9 proves the same governance loop on a different modality: a declarative Three.js mutation-effect recipe whose first candidate violates presentation authority/contract bounds and whose repaired candidate is consumed only through a temporary browser overlay. Both proofs stop at `validated_candidate` with `canonical_write=false`. Phase 10 then closes the previously deferred Runtime spawn gap: `alien_lineage.spawn` creates a real reviewed Egg Entity and Child Entity through the pinned CompilableWorld `entity_transaction/v0.1` boundary, never by direct registry mutation from an AWA module.

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
10. bounded AI World Assembler loop — **complete**;
11. second independent presentation/assembler proof — **complete**;
12. transaction-safe Runtime entity spawn — **complete**;
13. second world vertical slice — **next**.

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

# Phase 10 transaction-safe egg/child Runtime entities
awa-alien-lineage spawn-build \
  --semantic-snapshot fixtures/sedb/expected.game.alien_lineage.snapshot.json \
  --composition-receipt fixtures/csc_ocm/expected.alien_lineage.composition-receipt.json \
  --asset-graph-snapshot fixtures/compilableworld_intake/asset-graph.resolved.json \
  --plan fixtures/alien_lineage_runtime/alien_lineage.intake-plan.json \
  --slice fixtures/alien_lineage_runtime/runtime-slice.json \
  --spawn-profile fixtures/alien_lineage_runtime/spawn-profile.json \
  --out build/alien-lineage-phase10

# After compiling Phase 6/10 with the pinned CompilableWorld runtime:
cd presentation/threejs && npm install --no-audit --no-fund --package-lock=false && npm test && npm run build && cd ../..
awa-threejs verify-assets presentation/threejs/dist
awa-threejs serve build/alien-lineage-phase6-runtime/world.package.json \
  --binding fixtures/threejs/alien-lineage.presentation-binding.json \
  --static-dir presentation/threejs/dist

# Bounded Phase 8 assembler proof
awa-assembler run \
  --task fixtures/assembler/alien-lineage.attack-audio.task.json \
  --semantic-snapshot fixtures/sedb/expected.game.alien_lineage.snapshot.json \
  --composition-receipt fixtures/csc_ocm/expected.alien_lineage.composition-receipt.json \
  --presentation-binding fixtures/threejs/alien-lineage.presentation-binding.json \
  --capability-contract fixtures/assembler/audio_generation.capability.json \
  --nodes fixtures/asset_graph/nodes \
  --edges fixtures/asset_graph/edges \
  --artifacts fixtures/asset_graph/artifacts \
  --validations fixtures/asset_graph/validations \
  --out build/phase8-assembler

# Bounded Phase 9 presentation-recipe proof
awa-assembler run \
  --task fixtures/assembler/alien-lineage.mutation-effect-recipe.task.json \
  --semantic-snapshot fixtures/sedb/expected.game.alien_lineage.snapshot.json \
  --composition-receipt fixtures/csc_ocm/expected.alien_lineage.composition-receipt.json \
  --presentation-binding fixtures/threejs/alien-lineage.presentation-binding.json \
  --capability-contract fixtures/assembler/presentation_recipe_generation.capability.json \
  --nodes fixtures/assembler_presentation_graph/nodes \
  --edges fixtures/assembler_presentation_graph/edges \
  --artifacts fixtures/assembler_presentation_graph/artifacts \
  --validations fixtures/assembler_presentation_graph/validations \
  --out build/phase9-assembler
```

See `docs/SEDB_READ_ADAPTER.md`, `docs/CSC_OCM_RESOLVER.md`, `docs/DYNAMIC_ASSET_GRAPH.md`, `docs/COMPILABLEWORLD_INTAKE.md`, `docs/ALIEN_LINEAGE_RUNTIME.md`, `docs/THREEJS_PRESENTATION.md`, and `docs/AI_WORLD_ASSEMBLER.md`. Phase 9 broader-proof details are in `docs/ASSEMBLER_BROADER_PROOF.md`.

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
- no second renderer unless it adds independent architectural evidence beyond the stable Three.js proof.

See `DECISIONS.md`, `PROJECT_STATE.json`, and `AGENTS.md`.
