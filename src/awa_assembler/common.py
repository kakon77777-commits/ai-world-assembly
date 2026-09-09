from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from awa_contracts.validator import ContractValidationError, load_json, validation_errors


class AssemblerError(ValueError):
    pass


def schema(root: Path, contract: str) -> dict[str, Any]:
    try:
        return load_json(root / "schemas" / f"{contract}.schema.json")
    except ContractValidationError as exc:
        raise AssemblerError(str(exc)) from exc


def validate(root: Path, contract: str, document: Any, label: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise AssemblerError(f"{label} must be a JSON object")
    errors = validation_errors(schema(root, contract), document)
    if errors:
        raise AssemblerError(f"{label} violates {contract}: " + "; ".join(errors))
    return document


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def slug(value: str) -> str:
    return value.replace("validator.", "").replace(".", "-")


def candidate_artifact_id(task: dict[str, Any], artifact_sha: str) -> str:
    return f"{task['target']['node_id']}.candidate.{artifact_sha[:16]}"


def validation_id_prefix(task: dict[str, Any]) -> str:
    node_id = task["target"]["node_id"]
    if node_id.startswith("artifact."):
        node_id = node_id[len("artifact.") :]
    return f"validation.{node_id}"
