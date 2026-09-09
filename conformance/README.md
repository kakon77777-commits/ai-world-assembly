# Conformance

Shared JSON Schema contracts are tested with versioned valid/invalid fixture registries under
`fixtures/conformance*.json`.

The bootstrap fixture set remains `fixtures/conformance.v0.1.json`. Later phases append small
phase-scoped fixture files rather than rewriting the bootstrap registry. `tests/test_contracts.py`
merges the registries fail-closed and rejects duplicate contract fixture names.

Every shared schema must have exactly one valid and one invalid fixture across the merged registry.
