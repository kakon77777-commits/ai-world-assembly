from __future__ import annotations

import json
from pathlib import Path

import pytest

from awa_contracts.validator import ContractValidationError, validation_errors

ROOT = Path(__file__).resolve().parents[1]


def test_validator_accepts_and_rejects_conformance_pair() -> None:
    name = "semantic-game-entity.v0.1"
    schema = json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    cases = json.loads((ROOT / "fixtures" / "conformance.v0.1.json").read_text(encoding="utf-8"))["fixtures"][name]
    assert validation_errors(schema, cases["valid"]) == []
    assert validation_errors(schema, cases["invalid"])


def test_validation_error_is_raised_by_file_api(tmp_path: Path) -> None:
    from awa_contracts.validator import validate_files
    name = "semantic-game-entity.v0.1"
    schema_path = ROOT / "schemas" / f"{name}.schema.json"
    cases = json.loads((ROOT / "fixtures" / "conformance.v0.1.json").read_text(encoding="utf-8"))["fixtures"][name]
    document = tmp_path / "invalid.json"
    document.write_text(json.dumps(cases["invalid"]), encoding="utf-8")
    with pytest.raises(ContractValidationError):
        validate_files(schema_path, document)
