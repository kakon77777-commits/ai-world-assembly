# Phase 6 — Bounded Alien Lineage Runtime Slice

Phase 6 turns the proven Phase 5 intake path into an executable domain slice without changing the CompilableWorld Kernel.

## Runtime actions

`alien_lineage.runtime` provides exactly:

- `feed`
- `mutate`
- `grow`
- `lay_egg`
- `hatch`
- `enter_rift`

The module owns only `resource.*`, `biology.*`, `lineage.*` and `world.*` writes. Normal movement remains `movement.core` authority.

## FunctionIR

The slice authors four pure numeric functions:

- `alien_lineage.feed_gain`
- `alien_lineage.mutation_cost`
- `alien_lineage.growth_threshold`
- `alien_lineage.egg_cost`

The Runtime Module evaluates these functions and emits StateDelta/EventIR; FunctionIR itself has no side effects.

## Egg / hatch boundary

Phase 6 intentionally does **not** create child EntityRegistry entries. `lay_egg` and `hatch` persist a bounded lineage record on the parent (`egg_state`, `child_stage`, `child_species`). Direct registry mutation from Module evaluation would bypass the current transaction/rollback contract, so dynamic spawn is deferred until a formal spawn authority exists.

## Runtime extension declaration

CompilableWorld's builtin installer rejects unknown manifest modules. AWA therefore keeps the manifest limited to real CompilableWorld built-ins and writes an explicit `world.runtime_extensions` declaration:

```json
{
  "module_id": "alien_lineage.runtime",
  "version": "0.1.0",
  "entrypoint": "awa_alien_lineage.runtime:AlienLineageModule"
}
```

`awa-alien-lineage scenario-run` verifies this declaration before registering the module.

## Full-cycle ScenarioIR

`alien-lineage.full-cycle` executes:

1. move to feeding shelf;
2. feed three times;
3. mutate `organ.crystal-gill`;
4. grow to `adult`;
5. return to nursery;
6. lay egg;
7. hatch;
8. move to rift;
9. enter `rift.echo`.

Native CompilableWorld ScenarioIR keeps the final `position` assertion and all six expected lineage events. The pinned compiler intentionally restricts portable state assertions to its existing read whitelist and scalar values, so stage/organ/egg/worldline checks live in the versioned AWA `full-cycle.assertions.json` sidecar and are evaluated after the same Runtime execution.

## CI gate

GitHub Actions checks out CompilableWorld commit `70141f364220697fe037cd0047604c608ad4c074`, builds Phase 6 authoring, runs the real compiler, runs the native move smoke ScenarioIR, then runs the full lineage ScenarioIR with the declared AWA extension module.
