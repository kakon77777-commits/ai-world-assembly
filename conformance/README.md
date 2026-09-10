# Conformance

Shared JSON Schema contracts are tested with versioned valid/invalid fixture registries under `fixtures/conformance*.json`. `tests/test_contracts.py` merges registries fail-closed, rejects duplicate contract fixture names, and requires exactly one valid and one invalid fixture for every shared schema.

Phase 4 added artifact validation/graph snapshot fixtures; Phase 5 added SEDB snapshot and CompilableWorld intake fixtures; Phase 6 added bounded Alien Lineage runtime fixtures; Phase 7 adds `runtime-projection.v0.1` fixtures for the live Three.js presentation boundary.

Phase 8 adds bounded assembler task/run receipt fixtures. Both contracts structurally preserve proposal-only generation and `canonical_write=false`.

Phase 9 adds `presentation-effect-recipe.v0.1` valid/invalid evidence. The invalid case carries a Runtime-authority-shaped field and is rejected fail-closed.

Phase 10 adds valid/invalid evidence for the reviewed spawn profile, spawn receipt and dynamic-entity assertion sidecar.
Phase 11 adds valid/invalid evidence for Relay Station runtime slice/receipt/assertions, the Relay runtime projection, and `presentation-effect-recipe.v0.2`; invalid fixtures fail closed on missing required structure or forbidden/unknown authority-shaped fields.
Phase 12 adds valid/invalid evidence for the reviewed multi-world orchestration plan and receipt. Invalid evidence fails closed on non-coordination authority, invalid budgets, empty plans, or any attempt to grant canonical write permission.
