# AI World Assembly

Internal integration workspace for the AI-Native Game / World Assembly architecture.

This repository is an **integration layer**, not a replacement for SEDB or CompilableWorld.

## Authority boundaries

- **SEDB** — semantic/content truth, provenance, candidate/canonical governance.
- **CSC-OCM** — module/capability composition and compatibility.
- **Dynamic Asset Graph** — assembly topology, dependencies, missing-node tasks.
- **CompilableWorld** — committed runtime state/action/event authority.
- **Presentation** — rendering, input, audio, UI, target-local physical state.
- **AI World Assembler** — proposal, planning, generation, validation and repair across those boundaries.

## Current status

- **Phase 1 — Contracts:** complete.
- **Phase 2 — SEDB read adapter:** complete.
- **Phase 3 — CSC-OCM resolver:** complete.
- **Next: Phase 4 — Dynamic Asset Graph MVP.**

Phase 3 adds a deterministic CSC-OCM resolver from `world-profile.v0.1` to
`composition-receipt.v0.1`. It expands selected module dependency closure, locks the exact
module versions used, validates explicit conflicts/core compatibility/capability availability,
and keeps provider identity outside semantic module contracts.

## Bootstrap roadmap

1. versioned JSON Schema contracts — **complete**;
2. valid/invalid conformance fixtures — **complete**;
3. deterministic contract validation — **complete**;
4. SEDB read adapter — **complete**;
5. CSC-OCM resolver — **complete**;
6. Dynamic Asset Graph MVP — **next**;
7. CompilableWorld intake adapter;
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
```

See `docs/SEDB_READ_ADAPTER.md` and `docs/CSC_OCM_RESOLVER.md` for the implemented
boundaries and deterministic semantics.

## Non-goals for the bootstrap

- no SEDB kernel rewrite;
- no SEDB canonical write path;
- no CompilableWorld kernel rewrite;
- no provider routing inside module semantics;
- no live C3/C4 module migration;
- no multiplayer;
- no cloud marketplace;
- no autonomous core promotion;
- no Godot/Unity adapter until the first Three.js proof is stable.

See `DECISIONS.md`, `PROJECT_STATE.json`, and `AGENTS.md`.
