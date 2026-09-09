# Conformance

Shared JSON Schema contracts are tested with versioned valid/invalid fixture registries under
`fixtures/conformance*.json`.

The bootstrap fixture set remains `fixtures/conformance.v0.1.json`. Later phases append small
phase-scoped fixture files rather than rewriting prior registries. `tests/test_contracts.py`
merges the registries fail-closed and rejects duplicate contract fixture names.

Every shared schema must have exactly one valid and one invalid fixture across the merged registry.
Phase 4 adds `artifact-validation.v0.1` and `asset-graph-snapshot.v0.1` fixtures without changing
older contract fixtures.

Phase 5 adds SEDB namespace snapshot, CompilableWorld Intake Plan and Intake Receipt conformance fixtures.

Phase 6 adds conformance fixtures for the bounded Alien Lineage runtime-slice, runtime-receipt and domain-assertion contracts.
