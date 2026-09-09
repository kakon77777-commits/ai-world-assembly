# Conformance

Shared JSON Schema contracts are tested with versioned valid/invalid fixture registries under `fixtures/conformance*.json`. `tests/test_contracts.py` merges registries fail-closed, rejects duplicate contract fixture names, and requires exactly one valid and one invalid fixture for every shared schema.

Phase 4 added artifact validation/graph snapshot fixtures; Phase 5 added SEDB snapshot and CompilableWorld intake fixtures; Phase 6 added bounded Alien Lineage runtime fixtures; Phase 7 adds `runtime-projection.v0.1` fixtures for the live Three.js presentation boundary.
