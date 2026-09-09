# SEDB Read Adapter v0.1

Phase 2 establishes a deliberately narrow SEDB integration boundary.

## Source compatibility

The adapter targets the current SEDB v0.4B-style SQLite read schema used by:

- `entities`
- `fields`
- `cells`

It does not import `EntityService`, `FieldService`, governance services, or autonomy write paths.
The database is opened using SQLite URI `mode=ro`, followed by `PRAGMA query_only=ON`.

## Namespace semantics

SEDB stores `namespace` on **fields**, not entities.

AWA therefore defines a namespace projection as:

> the canonical field cells of an entity whose fields belong to that namespace.

For v0.1, only fields in status `active` or `converged` are projected. Proposed, merged,
split, and deprecated field definitions do not enter the game semantic projection.

A namespace snapshot includes only entities that have at least one projected field in the
requested namespace.

## Entity projection

`export_entity()` emits the existing `semantic-game-entity.v0.1` contract.

The `version` field is the AWA projection version (`v0.1`), because current SEDB entities do
not expose an independent semantic entity revision counter.

`provenance_ref` is a deterministic `sedb://` reference carrying a SHA-256 digest of the
projected entity content. It is a traceable projection identifier, not a replacement for
SEDB's richer source/confidence/governance evidence.

## Namespace snapshot

`export_namespace()` emits a deterministic adapter envelope:

```json
{
  "contract": "sedb-namespace-snapshot.v0.1",
  "source": "SEDB",
  "namespace": "game.alien_lineage",
  "projection_version": "v0.1",
  "entity_count": 2,
  "entities": [],
  "sha256": "..."
}
```

The SHA-256 is computed over canonical JSON of every field except the digest itself.
Entities are ordered by stable SEDB entity ID.

This snapshot envelope is adapter-local in Phase 2; it is not added to the shared bootstrap
contract inventory until a second consumer requires it.

## CLI

```bash
awa-sedb-export check path/to/sedb.db
awa-sedb-export entity path/to/sedb.db species.crystal_filterer --namespace game.alien_lineage
awa-sedb-export namespace path/to/sedb.db game.alien_lineage -o snapshot.json
```

## Non-goals

- no SEDB canonical writes;
- no field proposal/decision operations;
- no SEDB kernel/schema changes;
- no runtime state export;
- no automatic historical sedimentation.
