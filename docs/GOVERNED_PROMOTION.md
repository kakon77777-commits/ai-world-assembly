# Phase 13 — Governed Multi-Candidate Conflict and Promotion Closure

## Scope

Phase 13 begins **after** independently validated candidates already exist. It does not weaken Phase 12 pre-generation write-claim conflict blocking and it does not add a canonical writer.

The authority ladder is intentionally separated:

```text
Validation
  != Selection
  != Promotion Readiness
  != Promotion Authority
  != Canonical Write
```

Every Phase 13 contract structurally keeps `canonical_write=false`.

## Promotion slots

Candidates declare the same write-claim shape introduced in Phase 12:

```json
{"scope":"world","key":"presentation.effect.primary"}
```

or:

```json
{"scope":"shared","key":"presentation.shared.effect-registry"}
```

A world-scoped promotion slot is normalized as:

```text
world:<world_scope>:<key>
```

A shared slot is normalized as:

```text
shared:<key>
```

Therefore the same world-scoped key in Alien Lineage and Relay Station is not a conflict, while the same shared key is.

## Exact candidate evidence

`candidate-conflict-set.v0.1` requires each candidate to bind:

- candidate/world/task/run identity;
- `validated_candidate` status;
- repository-relative artifact reference;
- artifact contract;
- exact artifact SHA-256;
- validation evidence hash;
- world/shared write claim;
- explicit policy facts plus policy-evidence hash;
- `canonical_write=false`.

The evaluator re-reads the candidate bytes, verifies the SHA-256, validates the artifact against its declared contract, and recomputes both evidence hashes. A claimed valid candidate with stale bytes or stale evidence fails closed before comparison.

## Explicit selection policy

`conflict-evaluation-policy.v0.1` supports ordered numeric criteria only in Phase 13. Criteria are reviewed and visible in candidate policy evidence. The reference proof uses:

```text
reviewed_priority: max
```

The policy fixes:

```text
tie_behavior = block
last_writer_wins = false
implicit_tiebreakers = false
canonical_write = false
```

Input order, candidate hash, timestamps, run IDs and similar hidden/LWW tiebreak fields are rejected. A legitimate tie remains a tie and produces `blocked_tie`; it is never repaired by hash order or arrival order.

Candidate input order is normalized before conflict-set evidence hashing, so reversing the candidate list cannot change the readiness receipt identity.

## Readiness

`promotion-readiness-receipt.v0.1` records one deterministic decision per normalized slot:

- `uncontested` — one validated candidate;
- `selected` — multiple validated candidates and a unique explicit-policy winner;
- `blocked_tie` — explicit criteria do not produce one winner.

If any slot is tied, overall readiness is `blocked`. A ready receipt still says:

```text
promotion_authority_required = true
canonical_write = false
```

Readiness is evidence, not permission.

## Separate promotion authority

`promotion-authority-grant.v0.1` is an independent input. It binds an issuer and nonce to the exact:

- readiness evidence hash;
- policy ID and policy SHA-256;
- promotion slot;
- selected candidate ID;
- selected candidate SHA-256.

`PromotionEvaluator.authorize()` verifies those bindings and emits `promotion-authority-receipt.v0.1` only for an exact ready selection.

A grant for a different candidate, policy, slot or readiness receipt fails closed. A blocked readiness receipt cannot be authorized.

## No writer in Phase 13

`promotion-authority-receipt.v0.1` means only:

> an explicit promotion grant has been verified against an exact ready candidate selection.

It does **not** write SEDB, Asset Graph registries, Presentation source, CompilableWorld state, or any other canonical target. The promotion package has no StateDelta, EntityDelta, registry mutation or canonical-write path.

Expiry, cryptographic signatures, nonce replay protection and single-use consumption are deliberately deferred until a real canonical writer/protocol exists. Phase 13 does not pretend to enforce writer-side properties without a writer.

## Reference witness

The reference fixture contains three exact `presentation-effect-recipe.v0.2` candidates:

- `alien-glow-c` — uncontested world-scoped Alien Lineage slot;
- `relay-glow-a` — Relay Station candidate with reviewed priority 20;
- `relay-glow-b` — Relay Station candidate with reviewed priority 10.

The two Relay Station candidates conflict at the same world-scoped slot. The explicit reviewed policy selects `relay-glow-a`. A separate exact grant then authorizes that selection for future promotion handling while `canonical_write=false` remains structural.

A second fixture places Relay and Alien candidates on one shared slot with equal explicit rank. Both candidates remain valid; the result is `blocked_tie`.

## Frozen boundary

Phase 13 establishes:

```text
ValidatedCandidates
  -> ExplicitConflictPolicy
  -> SelectedOrBlocked
  -> PromotionReadiness
  -> SeparateAuthorityGrant
  -> PromotionAuthorization
```

It deliberately stops before:

```text
CanonicalWrite
```

Phase 14 may add provider-backed multi-world candidate generation, but it must enter this same governed boundary rather than gaining provider-specific promotion authority.
