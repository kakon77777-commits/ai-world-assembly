# Phase 8 — Bounded AI World Assembler Loop

Phase 8 proves one bounded generate/validate/repair/promotion loop over the already-proven AWA authority stack. The proof target is the deliberate Phase 4 missing required dependency `artifact.audio.crystal_filterer.attack`.

## Authority flow

```text
PROJECT_STATE + SEDB snapshot + Composition Receipt + Asset Graph + Presentation Binding
    -> observe exact context
    -> existing generation-task.v0.1
    -> candidate producer (proposal authority only)
    -> exact-byte validators
    -> failed candidate evidence
    -> diagnostic-driven repair attempt
    -> exact-byte validators
    -> candidate Asset Graph overlay + graph preview
    -> validated candidate receipt
```

`validated_candidate` is not canonicalization. Phase 8 never writes SEDB, never mutates CompilableWorld state, never updates the canonical Asset Graph registries, and never changes Presentation bindings automatically. `assembler-task.v0.1` requires `authority=proposal` and `promotion_policy.canonical_write=false`; `assembler-run-receipt.v0.1` repeats that closure in evidence.

## Reference proof producer

CI uses `ReferenceAudioProducer`, a deterministic proof producer rather than an external AI model. Attempt 1 intentionally emits a valid but silent WAV; `validator.audio.non_silent` rejects it. Attempt 2 receives that diagnostic and emits a deterministic non-silent waveform. This isolates assembler orchestration and repair correctness from provider/model quality. Real AI producers can implement the same `CandidateProducer` protocol later without changing semantic/module contracts.

The candidate validator chain is:

- `validator.wav.decode` — mono 16-bit PCM WAV must decode;
- `validator.audio.duration` — bounded to 50–500 ms;
- `validator.audio.non_silent` — peak PCM amplitude must exceed the minimum threshold.

Every `artifact-validation.v0.1` is bound to the exact candidate SHA-256. A new candidate therefore cannot reuse old evidence.

## Promotion semantics

When all validators pass, AWA creates an in-memory/output-bundle Asset Graph overlay containing:

- the missing artifact node with `status=candidate`;
- the exact candidate `artifact-reference.v0.1`;
- one validation node/evidence record per validator;
- `validated_by` edges;
- a root-scoped graph snapshot preview.

Promotion succeeds only when the preview has no missing required dependencies, no new generation tasks, and the target artifact effective status is `passed`. The result is `validated_candidate`; canonical registries remain unchanged.

## Reproducible CLI proof

```bash
awa-assembler run \
  --task fixtures/assembler/alien-lineage.attack-audio.task.json \
  --semantic-snapshot fixtures/sedb/expected.game.alien_lineage.snapshot.json \
  --composition-receipt fixtures/csc_ocm/expected.alien_lineage.composition-receipt.json \
  --presentation-binding fixtures/threejs/alien-lineage.presentation-binding.json \
  --capability-contract fixtures/assembler/audio_generation.capability.json \
  --nodes fixtures/asset_graph/nodes \
  --edges fixtures/asset_graph/edges \
  --artifacts fixtures/asset_graph/artifacts \
  --validations fixtures/asset_graph/validations \
  --out build/phase8-assembler
```

The output includes both attempt artifacts/evidence, the selected candidate bundle, `graph-snapshot.preview.json`, and `assembler-run-receipt.json`.

## Phase 9 generalization

Phase 9 proves that the bounded loop is not audio-specific. Artifact identity and validation identity are now derived from the task target, while the producer/validator registry remains modality-specific. The same loop therefore handles both the Phase 8 WAV target and the Phase 9 declarative presentation recipe without changing promotion semantics.

The second proof intentionally exercises contract/authority repair rather than signal-quality repair. A passing candidate may be consumed by a downstream validation overlay, but that consumption does not grant canonical authority.
