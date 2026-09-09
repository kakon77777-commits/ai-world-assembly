# Transaction-Safe Runtime Spawn — Phase 10

Phase 10 closes the deliberate gap left by ADR-030. The previous `lay_egg` / `hatch` implementation could change lineage state but could not create an EntityRegistry entry inside the same rollback boundary.

The pinned CompilableWorld compatibility target is:

```text
cf37f539e0807499e8b337f80a5f152324c087f2
```

It adds `entity_transaction/v0.1`: create-only EntityDelta plus `EntityTransactionRuntime`. AWA does not modify or monkey-patch that commit.

Phase 10 packages declare two external modules:

```text
alien_lineage.runtime  -> feed / mutate / grow / enter_rift
alien_lineage.spawn    -> lay_egg / hatch
```

The spawn module returns StateDelta, EntityDelta(create), and EventIR. It never calls EntityRegistry mutation APIs directly. One reviewed egg ID and one reviewed child ID come from `alien-lineage-spawn-profile.v0.1`; position is derived from committed Runtime state at the action boundary.

The bounded lifecycle is now:

```text
ParentEntity
  -> lay_egg
  -> EggEntity(stage=egg)
  -> hatch
  -> EggEntity(stage=hatched) + ChildEntity(stage=hatchling)
```

Duplicate create and durable EventLog failure are fail-closed and restore StateStore, EntityRegistry, and dynamic-entity bookkeeping. Removal/despawn and dynamic ID allocation remain explicitly deferred.
