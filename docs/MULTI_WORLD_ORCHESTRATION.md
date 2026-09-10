# Phase 12 — Multi-World / Multi-Target Assembler Orchestration

Phase 12 coordinates already-governed assembler tasks across multiple worlds. It does **not** merge semantic, runtime, presentation, evidence, or promotion authority.

## Authority model

The orchestration layer has one authority only:

```text
coordination
```

It may decide which reviewed task is ready, which independent tasks may run in the same bounded batch, and whether declared write claims conflict. It cannot:

- write SEDB canonical state;
- construct CompilableWorld `StateDelta` or mutate `EntityRegistry`;
- change child `assembler-task.v0.1` proposal authority;
- promote a validated candidate into a canonical Asset Graph or Presentation registry.

Therefore:

```text
OrchestrationSuccess != CanonicalPromotion
```

and every Phase 12 receipt keeps `canonical_write=false`.

## Canonical Phase 12 plan

`fixtures/orchestration/phase12.multi-world.plan.json` coordinates three existing tasks:

1. `alien-audio` — Alien Lineage attack-audio repair;
2. `relay-activation-recipe` — Relay Station activation presentation recipe repair;
3. `alien-mutation-recipe` — Alien Lineage mutation presentation recipe repair.

The first two are independent and fit in one `max_parallel=2` batch. The mutation recipe is explicitly gated behind the Alien Lineage base audio closure for the Phase 12 release plan.

Expected schedule:

```text
Batch 1: alien-audio | relay-activation-recipe
Batch 2: alien-mutation-recipe
```

The implementation uses a bounded thread pool for tasks in the same batch, then sorts child evidence back into the reviewed schedule order. Completion timing therefore cannot change the orchestration receipt identity.

## World-scoped evidence

Each child is still a normal `BoundedAssembler` run and emits its own `assembler-run-receipt.v0.1`. The orchestration receipt records those child `evidence_hash` values per `world_scope` instead of inventing one cross-world semantic receipt.

```text
game.alien_lineage -> child evidence set A
game.relay_station -> child evidence set B
```

The aggregate evidence hash proves coordination over those child receipts; it does not replace them.

## Write claims and conflicts

Every task must claim its own target node as a `world` write claim. World claims are namespaced by `world_scope`, so the same key in two independent worlds is legal.

A `shared` write claim is intentionally global. If two tasks claim the same shared resource, Phase 12 blocks **before creating the child `tasks/` output directory**. This gives a concrete pre-generation conflict witness rather than resolving conflicts by last-writer-wins.

Examples:

```text
world(game.a, artifact.same) + world(game.b, artifact.same) -> legal
shared(presentation.shared.effect-registry) x 2 -> blocked
```

## Budget closure

The plan declares:

- maximum parallel tasks;
- maximum task count;
- maximum total child repair attempts;
- fail-fast behavior.

Preflight reserves each child task's declared repair-attempt ceiling. A plan whose theoretical child attempt total exceeds the orchestration budget fails closed before generation.

The Phase 12 reference plan reserves and uses six attempts: all three deterministic reference producers fail once and repair once.

## Non-goals

Phase 12 does not implement:

- autonomous task discovery from all repository graphs;
- dynamic provider selection;
- canonical promotion;
- conflict resolution or winner selection;
- distributed workers / queues;
- cross-world Runtime causality;
- shared mutable world state.

Those require stronger policy and promotion contracts. Phase 13 is reserved for governed multi-candidate conflict and promotion closure.
