# CSC-OCM Resolver v0.1

Phase 3 implements a deterministic, fail-closed resolver from a `world-profile.v0.1`
input to a `composition-receipt.v0.1` output.

The implementation follows the original CSC-OCM framing: a stable semantic core plus a
module set, explicit dependencies, capability contracts, compatibility classes, and
provider-independent routing semantics.

## v0.1 input

A World Profile contains:

- `core_version`;
- `modules.required`;
- `modules.optional`;
- `modules.disabled`;
- `capability_profile.available` / `disabled`;
- `compatibility_policy.max_class`.

### Optional means selected optional

In v0.1, a module named in `modules.optional` is **selected for this profile** and must
resolve successfully. “Optional” means it is optional relative to the shared core and may
be removed by editing the profile; it does **not** mean the resolver silently ignores a
missing manifest. This keeps composition reproducible and fail-closed.

## Module registry rule

The v0.1 registry permits exactly one manifest per module ID. The resolver records that
manifest's version in the composition receipt. Supporting multiple installed versions of
the same module is deliberately deferred until a version-selection contract exists.

## Required dependency closure

`requires.modules` is recursively expanded. The resolver:

1. rejects missing manifests;
2. rejects dependencies that are explicitly disabled;
3. rejects required dependency cycles;
4. emits dependency-first deterministic ordering.

`requires.core` is interpreted as the set of core versions accepted by the module. An
empty set means no explicit core restriction; otherwise the profile core must be present.

## Compatibility

Each active module must be at or below `compatibility_policy.max_class` using the
CSC-OCM C0-C4 ordering. Any active pair named by a module's explicit `conflicts` list is
rejected.

The v0.1 resolver does not yet implement a separate compatibility matrix or conditional
migration. Those belong to a later composition revision.

## Capability contracts and provider independence

`requires.capabilities` is resolved against `capability-contract.v0.1` documents.
A required capability must be:

- listed in the World Profile's `available` set;
- absent from its `disabled` set;
- present in the capability registry.

Provider names are not part of `module-manifest.v0.1`, `capability-contract.v0.1`, or
`world-profile.v0.1`. All three schemas are fail-closed on unknown properties, so a
provider-specific field is structurally rejected rather than becoming module semantics.

The resolver does not choose a model/provider. That remains a future Capability Router
concern.

## Semantic entity requirements

Module manifests preserve `requires.semantic_entities`, but Phase 3 does not yet validate
those references against an SEDB snapshot. The SEDB adapter exists, but cross-layer
semantic-entity satisfaction belongs to the later intake/build integration phase rather
than being guessed here.

## Receipt and reproducibility

The receipt records:

- resolved module order;
- exact module versions;
- required/available/disabled capability policy;
- compatibility result;
- SHA-256 hashes of the profile, selected module manifests, and selected capability
  contracts.

The receipt ID is derived from those canonical source hashes. Irrelevant registry entries
do not affect the receipt; selected source semantics do.

## CLI

```bash
awa-compose fixtures/csc_ocm/alien_lineage.profile.json \
  --modules fixtures/csc_ocm/modules \
  --capabilities fixtures/csc_ocm/capabilities \
  -o composition-receipt.json
```

## Non-goals

- no provider routing;
- no live module activation;
- no C3/C4 migration;
- no multiple installed versions per module ID;
- no SEDB canonical writes;
- no CompilableWorld runtime changes;
- no automatic semantic-entity satisfaction guesses.
