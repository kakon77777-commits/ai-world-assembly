# Phase 14 — Provider-Backed Multi-World Assembly

Phase 14 connects a real provider transport boundary to the existing bounded AI World Assembler without changing world/module semantics or weakening Phase 12/13 governance.

## Core separation

```text
World/Module Semantics
        !=
Provider / Model Identity
        !=
Promotion Authority
        !=
Canonical Write
```

The existing `CandidateProducer` protocol remains the generation boundary. `HTTPProviderProducer` implements that protocol through a provider-agnostic HTTP gateway:

```text
assembler-task.v0.1
  -> provider-generation-request.v0.1
  -> HTTP provider gateway
  -> raw candidate bytes
  -> provider-invocation-receipt.v0.1
  -> exact-byte validators
  -> assembler-run-receipt.v0.2
```

The stable artifact `generator` identity is `provider-backed.http.v0.1`. Vendor/model identity is recorded only in invocation evidence and never becomes a Domain, module, capability, Asset Graph node identity, or Phase 13 selection criterion.

## Provider request authority

`provider-generation-request.v0.1` is proposal-only and structurally fixes `canonical_write=false`. It carries the existing bounded assembler target, capability, validators, attempt number and prior diagnostics. A provider receives enough context to propose bytes, not authority to modify AWA state.

## Exact invocation evidence

Every successful provider invocation produces a locally derived `provider-invocation-receipt.v0.1` binding:

- stable adapter ID;
- provider ID;
- model ID;
- task ID / attempt;
- exact canonical request SHA-256;
- exact raw response SHA-256;
- HTTP status / response content type;
- `canonical_write=false`.

The provider does not self-assert this receipt. AWA derives it from the configured execution binding plus observed request/response bytes.

Provider-backed assembler runs use `assembler-run-receipt.v0.2`. Each attempt binds the provider evidence hash, and the full provider invocation list is included in the assembler evidence hash. Deterministic reference producers continue to emit `assembler-run-receipt.v0.1`, keeping Phase 8–13 evidence stable.

## Execution-only provider bindings

`provider-bindings.v0.1` maps reviewed orchestration task IDs to HTTP provider execution settings. The file is deployment/execution policy, not world semantics. It is intentionally separate from `multi-world-orchestration-plan.v0.1`.

Unbound orchestration tasks still resolve to the deterministic reference producers. Binding an external provider therefore does not alter the Phase 12 plan contract or its world-scoped authority model.

CLI:

```bash
awa-orchestrate run \
  --plan fixtures/orchestration/phase12.multi-world.plan.json \
  --provider-bindings path/to/provider-bindings.json \
  --out build/phase14-provider-orchestration
```

The HTTP endpoint is expected to act as a provider gateway and return raw candidate bytes. Authentication/vendor SDK concerns remain outside world/module semantics and can be implemented behind that gateway.

## Multi-world authority preservation

`MultiWorldOrchestrator` now accepts an injectable producer resolver. Its default resolver is unchanged and still uses the Phase 8–11 deterministic reference producers. Provider-backed children therefore pass through the same Phase 12:

- dependency DAG;
- world scope;
- write-claim preflight;
- bounded attempt budget;
- per-world evidence grouping;
- `canonical_write=false` coordination receipt.

A provider-backed child does not broaden any other child's authority.

## Feeding Phase 13

Phase 12 correctly blocks two same-world/same-slot generation jobs in one orchestration plan before generation. Phase 14 does **not** weaken that rule just to manufacture competing candidates.

Instead, competing provider candidates are produced in independent governed orchestration runs. `candidate_from_orchestration()` projects a validated child into the existing `candidate-conflict-set.v0.1` shape using:

- exact candidate bytes / SHA;
- child task/run identity;
- exact validator identity;
- existing reviewed write claim;
- separately supplied reviewed policy facts.

Provider/model identity is deliberately not copied into Phase 13 comparison input.

The resulting path is:

```text
Independent Provider Run A --\
                            +--> candidate-conflict-set.v0.1
Independent Provider Run B --/          |
                                       v
                          conflict-evaluation-policy.v0.1
                                       |
                              explicit selection / tie block
                                       |
                          promotion-readiness-receipt.v0.1
                                       |
                          separate promotion authority grant
                                       |
                          promotion-authority-receipt.v0.1
                                       |
                              still canonical_write=false
```

Provider success is therefore neither selection nor promotion authority.

## Fail-closed behavior

Phase 14 fails closed when:

- provider endpoint is not HTTP(S);
- provider/model identity is missing;
- transport fails;
- HTTP response is non-2xx;
- response bytes are empty;
- provider binding references an unknown orchestration task;
- duplicate provider bindings claim the same orchestration task;
- candidate validators fail;
- Phase 12 write claims conflict;
- Phase 13 reviewed policy ties.

## Deliberate limits

Phase 14 does not add:

- a vendor-specific SDK into world/module semantics;
- provider-controlled validation or promotion policy;
- a canonical writer;
- writer-side grant signatures / expiry / nonce consumption;
- secret material in provider evidence;
- arbitrary provider-generated executable code.

Provider authentication can live behind a configured gateway or a later execution adapter without changing the semantic contracts proven here.
