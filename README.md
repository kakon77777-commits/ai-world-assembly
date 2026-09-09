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

## Bootstrap scope

v0.1 starts with a contract-first integration layer:

1. versioned JSON Schema contracts;
2. valid/invalid conformance fixtures;
3. deterministic local validation;
4. SEDB read adapter next;
5. CSC-OCM resolver;
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
```

## Non-goals for the bootstrap

- no SEDB kernel rewrite;
- no CompilableWorld kernel rewrite;
- no multiplayer;
- no cloud marketplace;
- no live C3/C4 module migration;
- no autonomous core promotion;
- no Godot/Unity adapter until the first Three.js proof is stable.

See `DECISIONS.md`, `PROJECT_STATE.json`, and `AGENTS.md`.
