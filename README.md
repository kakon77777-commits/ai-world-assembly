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
- **Next: Phase 5 — CompilableWorld intake adapter.**

Phase 4 adds a deterministic typed assembly graph. It resolves only required-dependency closure,
permits non-required cycles, emits Generation Task proposals for missing required nodes, binds
validation evidence to exact artifact SHA-256 values, marks old evidence stale after artifact
changes, and emits reproducible root-scoped graph snapshots.

## Bootstrap roadmap

1. versioned JSON Schema contracts — **complete**;
2. valid/invalid conformance fixtures — **complete**;
3. deterministic contract validation — **complete**;
4. SEDB read adapter — **complete**;
5. CSC-OCM resolver — **complete**;
6. Dynamic Asset Graph MVP — **complete**;
7. CompilableWorld intake adapter — **next**;
8. Alien Lineage vertical slice;
9. Three.js first presentation target;
10. bounded AI World Assembler loop.

## Quick start

```bash
python -m pip install -e ".[dev]"
pytest -q

awa-contracts validate schemas/semantic-game-entity.v0.1.schema.json path/to/entity.json

awa-sedb-export check path/to/sedb.db
awa-sedb-export entity path/to/sedb.db species.crystal_filterer --namespace game.alien_lineage
awa-sedb-export namespace path/to/sedb.db game.alien_lineage -o snapshot.json

awa-compose fixtures/csc_ocm/alien_lineage.profile.json \
  --modules fixtures/csc_ocm/modules \
  --capabilities fixtures/csc_ocm/capabilities \
  -o composition-receipt.json

awa-asset-graph \
  --nodes fixtures/asset_graph/nodes \
  --edges fixtures/asset_graph/edges \
  --artifacts fixtures/asset_graph/artifacts \
  --validations fixtures/asset_graph/validations \
  --root-dir . \
  snapshot species.crystal_filterer \
  -o graph-snapshot.json \
  --tasks-output generation-tasks.json
```

See `docs/SEDB_READ_ADAPTER.md`, `docs/CSC_OCM_RESOLVER.md`, and
`docs/DYNAMIC_ASSET_GRAPH.md` for implemented boundaries.

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
