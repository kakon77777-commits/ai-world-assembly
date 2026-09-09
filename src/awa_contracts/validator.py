from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class ContractValidationError(ValueError):
    pass


def load_json(path: str | Path) -> Any:
    target = Path(path)
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"cannot load JSON: {target}") from exc


def validate_schema(schema: dict[str, Any]) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise ContractValidationError(f"invalid Draft 2020-12 schema: {exc}") from exc


def validation_errors(schema: dict[str, Any], document: Any) -> list[str]:
    validate_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def validate_files(schema_path: str | Path, document_path: str | Path) -> None:
    schema = load_json(schema_path)
    document = load_json(document_path)
    errors = validation_errors(schema, document)
    if errors:
        raise ContractValidationError("\n".join(errors))
