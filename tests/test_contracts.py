from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
FIXTURE_DIR = ROOT / "fixtures"


def contract_name(schema_path: Path) -> str:
    suffix = ".schema.json"
    assert schema_path.name.endswith(suffix)
    return schema_path.name[: -len(suffix)]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fixtures():
    merged = {}
    for path in sorted(FIXTURE_DIR.glob("conformance*.json")):
        document = load(path)
        for name, cases in document["fixtures"].items():
            assert name not in merged, f"duplicate conformance fixture: {name}"
            merged[name] = cases
    return merged


def test_every_schema_has_valid_and_invalid_fixture() -> None:
    schema_names = {contract_name(path) for path in SCHEMA_DIR.glob("*.schema.json")}
    fixture_names = set(fixtures())
    assert schema_names
    assert schema_names == fixture_names
    for item in fixtures().values():
        assert set(item) == {"valid", "invalid"}


def test_schemas_are_meta_valid_and_ids_unique() -> None:
    seen_ids: set[str] = set()
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = load(path)
        Draft202012Validator.check_schema(schema)
        schema_id = schema["$id"]
        assert schema_id not in seen_ids
        seen_ids.add(schema_id)
        name = contract_name(path)
        assert schema["properties"]["contract"]["const"] == name


def test_valid_fixtures_pass() -> None:
    cases = fixtures()
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        name = contract_name(path)
        schema = load(path)
        errors = list(Draft202012Validator(schema).iter_errors(cases[name]["valid"]))
        assert errors == [], f"{name}: {[error.message for error in errors]}"


def test_invalid_fixtures_fail() -> None:
    cases = fixtures()
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        name = contract_name(path)
        schema = load(path)
        errors = list(Draft202012Validator(schema).iter_errors(cases[name]["invalid"]))
        assert errors, f"{name}: invalid fixture unexpectedly passed"
