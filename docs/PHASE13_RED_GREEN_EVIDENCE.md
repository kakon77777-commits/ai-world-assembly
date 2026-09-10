# Phase 13 RED / GREEN / Closure Evidence

## Baseline

Exact Phase 12 base: `024c753fcccfdc0c66330588538ca31c406333bc`.

Clean extracted source backup baseline:

```text
PYTHONPATH=src python -m pytest -q
90 passed
```

## RED

Before `awa_promotion` existed, the new promotion-governance test file failed for the expected missing-capability reason:

```text
8 failed, 1 passed
ModuleNotFoundError: awa_promotion
```

The one passing test was the source-authority scan because the package did not yet exist. Tie coverage was then tightened so the discriminative witness uses two valid candidates with valid evidence and equal reviewed rank; it does not rely on corrupted evidence.

## GREEN

Targeted Phase 13 + shared-contract tests:

```text
16 passed
```

Full repository regression after updating the Phase 12 golden for the new canonical `PROJECT_STATE.json` evidence input:

```text
102 passed
```

The three Phase 12 selected candidate artifact SHA-256 values remain unchanged. The Phase 12 run/evidence identity changes because `PROJECT_STATE.json` is intentionally part of orchestration source evidence.

## Structural closure

- 40 JSON Schemas are Draft 2020-12 meta-valid.
- `python -m compileall -q src tests` passes.
- GitHub Actions workflow YAML parses successfully.
- `awa-promotion evaluate` reproduces the readiness golden semantically.
- `awa-promotion authorize` reproduces the authority golden semantically.
- `src/awa_promotion` contains no `StateDelta(`, `EntityDelta(`, `registry.add(`, or `canonical_write=True` path.

## Discriminative closure

The reference witnesses distinguish the required cases:

1. same world + same governed key + explicit unique rank → `selected`;
2. same world + same governed key + equal valid rank → `blocked_tie`;
3. same world-scoped key in different worlds → separate slots, no cross-world conflict;
4. same shared key in different worlds + equal valid rank → global `blocked_tie`;
5. candidate input reordering → identical readiness receipt identity;
6. stale policy evidence → fail closed;
7. timestamp/LWW-like hidden criterion → rejected;
8. readiness without a separate exact grant → no authorization;
9. mismatched grant candidate SHA → fail closed;
10. blocked readiness → cannot be authorized;
11. verified authority receipt → still `canonical_write=false`.

## Review mode

No independent second live reviewer was available during implementation. Review state is therefore explicitly:

```text
DEGRADED-TWIN
```

This is not represented as independent review evidence.
