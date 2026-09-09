# Architecture Decisions

## ADR-001 — Existing authorities remain separate

**Decision:** SEDB and CompilableWorld remain independent systems. AI World Assembly integrates them through adapters/contracts.

## ADR-002 — Contract-first bootstrap

**Decision:** Establish versioned exchange contracts and conformance tests before autonomy or game-content scale.

## ADR-003 — One integration repository for v0.1

**Decision:** Keep contracts, reference adapters, graph prototype and assembler reference code in this repository initially. Split only when scale justifies it.

## ADR-004 — SEDB read-first

**Decision:** The first SEDB adapter is read-only. No direct canonical mutation from this repo during the bootstrap.

## ADR-005 — CompilableWorld adapter-first

**Decision:** Generate existing CompilableWorld authoring inputs before considering Kernel changes.

## ADR-006 — Three.js first

**Decision:** The first presentation proof uses Three.js because the target is browser-native, agent-observable and already demonstrated by the Alien Lineage prototype.

## ADR-007 — Godot later, only if justified

**Decision:** Add Godot after the first end-to-end contracts are stable, or sooner only if product requirements demand physics/animation/native tooling.

## ADR-008 — Alien Lineage first vertical slice

**Decision:** Use a deliberately small Alien Lineage-like slice rather than a Living World RPG to reduce debugging dimensions.

## ADR-009 — Candidate before canon

**Decision:** AI generation defaults to candidate/proposal scope. Canonicalization requires a separate authority boundary.

## ADR-010 — No presentation world authority

**Decision:** Presentation input maps to semantic intent/ActionIR; presentation effects do not silently mutate persistent world semantics.

## ADR-011 — SEDB adapter enforces read-only at the database boundary

**Decision:** AWA opens the SEDB SQLite source using URI `mode=ro` plus `PRAGMA query_only=ON` and does not import SEDB write services. This makes the Phase 2 read-only claim executable rather than conventional.

## ADR-012 — Namespace projection follows field ownership

**Decision:** SEDB namespaces live on fields, not entities. AWA namespace projections therefore select an entity's active/converged field cells in the requested namespace. Proposed, merged, split and deprecated field definitions are excluded from v0.1 game semantic projections.

## ADR-013 — Namespace snapshot envelope remains adapter-local in Phase 2

**Decision:** `sedb-namespace-snapshot.v0.1` is emitted and tested by the adapter but is not promoted into the shared contract inventory until another system consumes it. This avoids adding a shared schema before a real cross-system boundary requires one.

## ADR-014 — World Profile specializes the original CSC-OCM Version Profile for integration

**Decision:** `world-profile.v0.1` keeps the original CSC-OCM profile structure (`core_version`, required/optional/disabled modules, capability profile and compatibility policy) while using a world-level name because AWA composes executable worlds rather than only historical release versions.

## ADR-015 — Optional modules listed in a World Profile are selected and fail closed

**Decision:** In resolver v0.1, `modules.optional` means modules selected for this profile but optional relative to the common core. A listed optional module must resolve; the resolver never silently drops a missing selected module. Omit or disable it explicitly instead.

## ADR-016 — Resolver v0.1 allows one installed manifest per module ID

**Decision:** Until a version-selection/range contract exists, the module registry rejects duplicate module IDs even if versions differ. The selected manifest version is locked into the Composition Receipt.

## ADR-017 — Provider identity is structurally excluded from composition semantics

**Decision:** World Profile, Module Manifest and Capability Contract schemas remain provider-independent and fail closed on undeclared provider fields. Phase 3 resolves capabilities but does not route them to a model/vendor.

## ADR-018 — Semantic entity requirements are preserved but not guessed in Phase 3

**Decision:** `requires.semantic_entities` remains part of Module Manifest, but the Phase 3 resolver does not claim those references are satisfied without an explicit SEDB snapshot/intake boundary. Cross-layer satisfaction is deferred rather than inferred.

## ADR-019 — Dynamic Asset Graph is assembly topology, not runtime causality

**Decision:** Phase 4 graph edges describe build/content dependencies and evidence relationships. Runtime causal state transitions remain CompilableWorld authority, and Presentation scene hierarchy remains Presentation-local.

## ADR-020 — Only the required dependency subgraph must be acyclic

**Decision:** `requires` edges with `required=true` define the closure/cycle-check graph. Optional and non-dependency relations may form cycles without being rejected as build cycles.

## ADR-021 — Missing required dependencies become Generation Task proposals

**Decision:** A missing target on a required dependency is represented explicitly and produces a deterministic `generation-task.v0.1` proposal. Missing optional targets remain legal without automatic generation; missing targets on non-dependency relations fail closed.

## ADR-022 — Validation evidence is bound to exact artifact bytes

**Decision:** `artifact-validation.v0.1` records the artifact SHA-256 it validated. Evidence whose hash no longer matches the current `artifact-reference.v0.1` is stale and cannot satisfy validation.

## ADR-023 — Required-build snapshots are root-scoped and ignore unrelated optional edges

**Decision:** `asset-graph-snapshot.v0.1` hashes the selected required closure, its required/validation edges, selected artifacts and validation evidence. Unrelated optional relations do not perturb the required build identity.

## ADR-024 — Graph version constraints are exact-only in v0.1

**Decision:** `version_constraint` is either null or an exact `vN.N` node version during Phase 4. Range selection is deferred instead of being silently interpreted.

## ADR-025 — Reviewed CompilableWorld Intake Plan

**Decision:** SEDB semantic projection, Composition Receipt and Asset Graph snapshot do not uniquely
determine Runtime rooms/components/spawn/scenarios. Phase 5 uses an explicit reviewed
`compilableworld-intake-plan.v0.1`; the adapter never guesses missing Runtime authoring facts.

## ADR-026 — Existing CompilableWorld authoring is the integration target

**Decision:** AWA emits the current CompilableWorld `manifest.json`, `world.json`, CSV data and
ScenarioIR files. Do not introduce a parallel Runtime Package format or modify the Kernel first.

## ADR-027 — Pin the first external compiler compatibility proof

**Decision:** Phase 5 CI proves compatibility against `compilableworld-runtime-mvp` master commit
`70141f364220697fe037cd0047604c608ad4c074`. Future upgrades must deliberately advance this pin.

## ADR-028 — Intake requires a build-complete asset snapshot

**Decision:** Phase 5 Runtime intake rejects missing required graph nodes and any required artifact
whose effective validation state is not `passed`. A separate future profile may relax this for
prototype/placeholder builds; v0.1 does not.

## ADR-029 — Alien Lineage domain behavior remains an external Runtime Module

**Decision:** Phase 6 implements `alien_lineage.runtime` in AWA and registers it after CompilableWorld built-ins. The CompilableWorld Kernel and builtin module registry remain unchanged. The compiled `world.json` declares the exact external module/version/entrypoint so the extension is not hidden.

## ADR-030 — Phase 6 does not mutate EntityRegistry from a Module action

**Decision:** `lay_egg` and `hatch` commit bounded lineage state and EventIR only. They do not call `registry.add()` from `evaluate()`, because EntityRegistry mutation currently lacks the same StateDelta/EventIR transaction and rollback boundary. A formal runtime spawn contract is deferred.

## ADR-031 — Bounded lineage costs and thresholds are FunctionIR

**Decision:** feed gain, mutation cost, growth threshold and egg cost are declared as pure CompilableWorld FunctionIR. Runtime Modules own side effects; numeric policy remains inspectable, deterministic and separately testable.

## ADR-032 — Scenario extension compatibility is pinned, not assumed

**Decision:** AWA supplies a thin ScenarioIR-compatible runner that installs the external lineage module and otherwise follows the current CompilableWorld ActionIR/StateStore/EventIR assertion model. CI pins the real CompilableWorld source commit and runs the full lineage scenario on every change.

## ADR-033 — Domain state assertions remain outside portable CompilableWorld ScenarioIR

**Decision:** The pinned CompilableWorld ScenarioIR contract permits only its current StateStore read whitelist and scalar expected values. Phase 6 therefore keeps the full action/event sequence and portable `position` assertion in native ScenarioIR, while lineage/world/list-valued checks live in versioned `alien-lineage-runtime-assertions.v0.1` sidecar evidence consumed by the AWA extension runner. Do not widen the upstream compiler from AWA.

## ADR-034 — Runtime-to-Presentation projection is allowlisted

**Decision:** Phase 7 exposes `runtime-projection.v0.1` instead of handing Three.js unrestricted StateStore/EntityRegistry access. Presentation receives only the bounded state required to render and formulate intents.

## ADR-035 — Presentation identity is generation-bound and disposable

**Decision:** `world_entity_id` remains stable Runtime identity while scene hydration/reload creates a new `presentation_instance_id` and increments generation. Stale presentation intents fail before ActionIR creation.

## ADR-036 — Browser input is never a Runtime write primitive

**Decision:** Three.js emits presentation intents. The Python sidecar is the only Phase 7 adapter that converts them into CompilableWorld ActionIR; browser code never constructs StateDelta or mutates Runtime stores.

## ADR-037 — The first presentation target is pinned and hash-closed

**Decision:** Phase 7 pins Three.js `0.180.0` and emits SHA-256 evidence for every served target file. Browser integration is accepted only after the target closure and headless Chromium smoke both pass.

## ADR-038 — The first assembler loop consumes an existing Generation Task

**Decision:** Phase 8 does not let the assembler invent arbitrary work. `assembler-task.v0.1` must wrap the deterministic `generation-task.v0.1` emitted for the observed required Asset Graph gap.

## ADR-039 — Provider output is untrusted until exact-byte validators pass

**Decision:** Generated candidate bytes receive immutable `artifact-validation.v0.1` evidence bound to their exact SHA-256. New bytes invalidate prior evidence by construction.

## ADR-040 — Repair is diagnostic-driven and budget-bounded

**Decision:** A failed candidate may be retried only within both the Generation Task and capability budgets, and repair input includes validator diagnostics from the previous attempt.

## ADR-041 — Phase 8 promotion stops at validated candidate

**Decision:** Passing validation plus a build-complete candidate graph preview may promote raw output to `validated_candidate`, but never to canonical/active authority. `canonical_write=false` is structural in both task and receipt contracts.

## ADR-042 — CI uses a deterministic reference producer to prove orchestration

**Decision:** The Phase 8 CI producer deliberately emits a silent first WAV and a repaired second WAV. This proves generate/validate/repair/promotion semantics reproducibly without coupling correctness to a vendor/model. Real AI producers may implement the same provider protocol later.


## ADR-043 — Phase 9 broadens modality before adding a second renderer

**Decision:** The second independent proof uses a declarative Three.js presentation effect recipe rather than a Godot/Unity adapter. This gives discriminative evidence for a different artifact/repair class while keeping presentation-engine expansion out of the bootstrap.

## ADR-044 — Generated presentation effects are declarative, not arbitrary executable code

**Decision:** `presentation-effect-recipe.v0.1` contains bounded visual parameters only. Phase 9 does not execute provider-generated JavaScript, which would require a stronger sandbox/security boundary than the current bootstrap provides.

## ADR-045 — Validated presentation candidates are tested through a temporary build overlay

**Decision:** A validated recipe may be copied into `dist/candidate/` for browser evidence after exact-byte validation, but the assembler never writes it into canonical Three.js source or Asset Graph registries. Browser consumption is validation evidence, not canonical promotion.

## ADR-046 — The second repair witness is contract/authority failure, not signal quality

**Decision:** Phase 9 attempt 1 carries forbidden `runtime_action` plus an out-of-bounds duration. Repair must be driven by those diagnostics. This intentionally differs from the Phase 8 non-silent audio quality failure.


## ADR-047 — A proven Runtime contract gap justifies the minimal upstream extension

**Decision:** Phase 10 may advance the CompilableWorld compatibility pin because the pinned Runtime could not represent EntityRegistry mutation inside the existing StateDelta/EventIR rollback boundary. AWA does not monkey-patch the registry or use event subscribers to fake atomicity. The upstream extension is additive and independently tested.

## ADR-048 — Entity transaction v0.1 is create-only and opt-in

**Decision:** `entity_transaction/v0.1` adds create-only `EntityDelta` through `EntityTransactionRuntime`. StateDelta, EntityDelta(create), and EventIR share one rollback boundary. A module must declare the capability explicitly; remove/despawn/replace remain deferred.

## ADR-049 — Runtime spawn IDs are reviewed bounded facts, not generated authority

**Decision:** Phase 10 uses one reviewed egg ID and one reviewed child ID from `alien-lineage-spawn-profile.v0.1`. The Runtime derives position from the committed parent/egg state at action time, but it does not invent entity identity or semantic canon.

## ADR-050 — Historical Phase 6 spawn semantics remain reproducible

**Decision:** Packages declaring only `alien_lineage.runtime` keep the Phase 6 bounded state-only lay/hatch path. Packages that additionally declare `alien_lineage.spawn` route those verbs exclusively to the transaction-safe spawn module under `EntityTransactionRuntime`.
