# Dynamic Asset Graph MVP — Phase 4

Phase 4 implements the first executable form of the Dynamic Asset Graph described by the
internal architecture series. It is an **assembly topology**, not a scene graph, runtime event
graph, or second semantic database.

## Inputs

The graph consumes four versioned registries:

- `asset-graph-node.v0.1`
- `asset-graph-edge.v0.1`
- `artifact-reference.v0.1`
- `artifact-validation.v0.1`

Nodes remain typed as semantic, fragment, artifact, module, validation or task. Artifact nodes
must reference an `artifact-reference.v0.1` document through `metadata.artifact_ref`.
Validation nodes must reference an `artifact-validation.v0.1` document through
`metadata.validation_ref`.

## Required closure

`requires` edges with `required=true` form the authoritative required-dependency subgraph.
Only that subgraph is required to be acyclic. Optional or other relation cycles remain legal.
The resolver emits dependency-first closure order and rejects unknown roots.

A missing target on a required or optional dependency edge is a legal graph state. A missing
target on `validated_by`, `binds`, `uses`, `derived_from`, etc. is rejected because those
relations claim an existing object.

Phase 4 v0.1 supports `version_constraint = null` or one exact `vN.N` node version. Range
semantics are intentionally deferred rather than silently approximated.

## Missing required nodes

If a required edge points to an absent node, analysis emits a deterministic
`generation-task.v0.1` proposal. Missing optional nodes do not generate work automatically.
Generation is still proposal scope; the graph does not canonicalize content.

## Artifact validation binding

`artifact-validation.v0.1` binds validation evidence to:

- an artifact ID;
- the exact artifact SHA-256;
- validator identity/version;
- passed/failed status;
- diagnostics and evidence reference.

A `validated_by` graph edge must connect an artifact node to a validation node whose validation
document targets the artifact referenced by the source node.

Effective artifact status is derived, not trusted from a filename or stale flag:

- any fresh failed evidence -> `failed`;
- otherwise any fresh passed evidence -> `passed`;
- otherwise stale evidence exists -> `stale`;
- otherwise -> `unvalidated`.

Changing artifact bytes/hash automatically makes prior validation evidence stale.

## Deterministic graph snapshot

`asset-graph-snapshot.v0.1` is root-scoped and captures:

- sorted roots;
- dependency-first required closure;
- missing required dependencies;
- deterministic Generation Task IDs;
- effective artifact validation states;
- canonical JSON source hashes for selected nodes, required/validation edges, artifacts and validation evidence;
- a final snapshot SHA-256 and derived snapshot ID.

Unrelated optional edges are deliberately excluded from the required-build snapshot identity.
This means a decorative/optional relation outside the required closure cannot perturb a build
that does not consume it.

## CLI

```bash
awa-asset-graph \
  --nodes fixtures/asset_graph/nodes \
  --edges fixtures/asset_graph/edges \
  --artifacts fixtures/asset_graph/artifacts \
  --validations fixtures/asset_graph/validations \
  --root-dir . \
  check

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

## Explicit non-goals

Phase 4 does not:

- mutate SEDB canon;
- resolve runtime causality;
- load mesh/audio bytes;
- choose an AI/provider for a Generation Task;
- perform Presentation scene instantiation;
- implement semantic version ranges;
- make optional missing nodes mandatory work.

The next boundary is Phase 5: turn SEDB/composition/graph outputs into **existing
CompilableWorld authoring inputs** without changing the CompilableWorld Kernel first.
