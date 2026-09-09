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
- **Next: Phase 3 — CSC-OCM resolver.**

Phase 2 adds a deterministic SQLite read-only adapter for the current SEDB entity/field/cell
schema. It emits `semantic-game-entity.v0.1` projections and namespace snapshots without
importing or exposing SEDB canonical write services.

## Bootstrap roadmap

1. versioned JSON Schema contracts — **complete**;
2. valid/invalid conformance fixtures — **complete**;
3. deterministic contract validation — **complete**;
4. SEDB read adapter — **complete**;
5. CSC-OCM resolver — **next**;
6. Dynamic Asset Graph MVP;
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
```

See `docs/SEDB_READ_ADAPTER.md` for the Phase 2 projection semantics and read-only guarantee.

## Source backups

Every push to `main` runs the `source-backup` workflow. It builds a `git archive` ZIP from the
exact merged commit, writes a SHA-256 sidecar, and uploads both as a GitHub Actions artifact
for 90 days. This is a convenience backup; Git history remains the canonical source record.

## Non-goals for the bootstrap

- no SEDB kernel rewrite;
- no SEDB canonical write path;
- no CompilableWorld kernel rewrite;
- no multiplayer;
- no cloud marketplace;
- no live C3/C4 module migration;
- no autonomous core promotion;
- no Godot/Unity adapter until the first Three.js proof is stable.

See `DECISIONS.md`, `PROJECT_STATE.json`, and `AGENTS.md`.
