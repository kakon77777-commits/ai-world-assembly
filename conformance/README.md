# Conformance

`tests/test_contracts.py` is the executable contract gate.

A contract passes the bootstrap gate only when:

- the schema itself is valid Draft 2020-12 JSON Schema;
- its valid fixture has zero validation errors;
- its invalid fixture has at least one validation error;
- `$id` values are unique;
- the top-level `contract.const` matches the schema filename.
