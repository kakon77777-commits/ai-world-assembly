# Phase 14 RED → GREEN Evidence

## Baseline

Exact Phase 13 canonical base:

```text
be0041312110c5f366283b7db3de9d37845248b2
```

Clean baseline regression before Phase 14 work:

```text
102 passed
```

## RED

A new provider-backed test suite was introduced before implementation.

Result:

```text
7 failed, 1 passed
```

The seven failures were all missing-capability failures:

- `HTTPProviderProducer` did not exist;
- `awa_orchestrator.providers` did not exist;
- `awa_promotion.bridge` did not exist.

The only passing test was the source authority scan, because no Phase 14 source existed yet. No pre-existing Phase 12/13 behavior was broken to create RED.

## GREEN

After the minimum implementation:

```text
8 passed
```

The suite proves:

1. provider-backed candidate generation binds exact request/response evidence;
2. non-2xx provider transport fails closed before candidate validation;
3. identical candidate bytes from different providers keep identical artifact semantic identity while run evidence differs;
4. provider-backed children flow through the existing multi-world orchestrator without authority merge;
5. provider bindings remain execution policy outside the world plan;
6. two independent provider-backed orchestration runs feed the existing Phase 13 explicit selection path;
7. equal reviewed policy scores still produce `blocked_tie` and cannot be broken by provider identity;
8. the provider/bridge path contains no Runtime or canonical-write primitive.

Shared contract + regression subset after adding conformance fixtures:

```text
43 passed
```

Full local regression before documentation/project-state closure:

```text
110 passed
```

## Closure condition

Phase 14 is closed only if the final canonical branch preserves:

```text
ProviderGeneration != Validation != Selection != PromotionReadiness != PromotionAuthority != CanonicalWrite
```

and the exact merged source artifact reproduces the test closure.
