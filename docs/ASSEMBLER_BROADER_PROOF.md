# Phase 9 — Broader Assembler Proof

Phase 8 proved a bounded generate/validate/repair loop on binary audio. Phase 9 deliberately changes both modality and repair class instead of adding a second renderer prematurely.

## Selected target

A dedicated Three.js presentation Asset Graph root requires `artifact.presentation.threejs.mutation_effect_recipe`, which is absent from the canonical registry. The graph therefore emits one deterministic `generation-task.v0.1` in the `presentation` layer.

The assembler task wraps that observed task and targets a JSON `presentation-effect-recipe.v0.1`.

## RED → repair

The deterministic reference producer emits a first candidate that is valid JSON but intentionally violates the presentation recipe boundary in two ways:

- it contains `runtime_action`, which a presentation recipe may never carry;
- `effect.duration_ms` is outside the bounded contract range.

The contract/semantic validators reject that exact SHA-256 and return diagnostics. Attempt 2 removes the forbidden authority-shaped field and repairs the duration. Validation evidence is rebound to the new exact bytes.

## Presentation-only contract

The recipe may describe only a bounded visual effect for `alien_lineage.creature_mutated`:

- target: `creature_visual`;
- scale peak;
- duration;
- emissive boost.

It cannot issue ActionIR, StateDelta, EntityRegistry writes or Runtime state mutation. The Three.js effect host consumes the recipe only after the Runtime has already emitted the matching EventIR.

$$
EventIR\rightarrow PresentationRecipe\rightarrow VisualEffect
$$

not

$$
PresentationRecipe\rightarrow RuntimeMutation
$$

## Candidate overlay

A passing candidate is copied only into a temporary built Three.js `dist/candidate/` overlay for browser evidence. It is not written into canonical `presentation/threejs/src`, the presentation Asset Graph registry, SEDB or CompilableWorld. Browser smoke must prove that the candidate recipe is loaded and applied after the mutation EventIR while the existing Runtime authority gates remain green.

## Promotion boundary

Phase 9 retains the Phase 8 promotion rule:

$$
RawCandidate\rightarrow ValidatedCandidate
$$

with `canonical_write=false`. Canonical adoption remains a separate authority decision.
