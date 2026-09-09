from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from awa_contracts.validator import ContractValidationError, load_json, validation_errors
from awa_cw_intake.intake import (
    CompilableWorldIntakeError,
    build_authoring_files,
    canonical_json,
    sha256_bytes,
    sha256_json,
)


class AlienLineageBuildError(ValueError):
    pass


def _schema(root: Path, contract: str) -> dict[str, Any]:
    try:
        return load_json(root / "schemas" / f"{contract}.schema.json")
    except ContractValidationError as exc:
        raise AlienLineageBuildError(str(exc)) from exc


def _validate(root: Path, contract: str, document: Any, label: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise AlienLineageBuildError(f"{label} must be a JSON object")
    errors = validation_errors(_schema(root, contract), document)
    if errors:
        raise AlienLineageBuildError(f"{label} violates {contract}: " + "; ".join(errors))
    return document


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _verify_slice_links(slice_doc: dict[str, Any], semantic_snapshot: dict[str, Any], intake_plan: dict[str, Any]) -> None:
    species_ref = slice_doc["runtime_config"]["species_ref"]
    semantic_ids = {entity["entity_id"] for entity in semantic_snapshot["entities"]}
    if species_ref not in semantic_ids:
        raise AlienLineageBuildError(f"runtime slice species_ref is not present in semantic snapshot: {species_ref}")
    if not any(entity["semantic_ref"] == species_ref for entity in intake_plan["entities"]):
        raise AlienLineageBuildError("runtime slice species_ref is not mapped into the intake plan")
    stages = slice_doc["runtime_config"]["stages"]
    if slice_doc["runtime_config"]["adult_stage"] not in stages:
        raise AlienLineageBuildError("adult_stage must be one of runtime_config.stages")
    organ_ids = [organ["organ_id"] for organ in slice_doc["runtime_config"]["organs"]]
    if len(organ_ids) != len(set(organ_ids)):
        raise AlienLineageBuildError("runtime_config.organs contains duplicate organ_id")
    function_ids = [item.get("function_id") for item in slice_doc["functions"]["functions"] if isinstance(item, dict)]
    required = {
        "alien_lineage.feed_gain",
        "alien_lineage.mutation_cost",
        "alien_lineage.growth_threshold",
        "alien_lineage.egg_cost",
    }
    if set(function_ids) != required:
        raise AlienLineageBuildError(f"runtime slice must declare exactly the bounded FunctionIR set: {sorted(required)}")


def build_runtime_authoring_files(
    semantic_snapshot: dict[str, Any],
    composition_receipt: dict[str, Any],
    asset_graph_snapshot: dict[str, Any],
    intake_plan: dict[str, Any],
    runtime_slice: dict[str, Any],
    *,
    root: str | Path,
) -> tuple[dict[str, str], dict[str, Any]]:
    root_path = Path(root)
    _validate(root_path, "alien-lineage-runtime-slice.v0.1", runtime_slice, "Alien Lineage runtime slice")
    _verify_slice_links(runtime_slice, semantic_snapshot, intake_plan)
    try:
        files, base_receipt = build_authoring_files(
            semantic_snapshot,
            composition_receipt,
            asset_graph_snapshot,
            intake_plan,
            root=root_path,
        )
    except CompilableWorldIntakeError as exc:
        raise AlienLineageBuildError(str(exc)) from exc

    manifest = json.loads(files["manifest.json"])
    manifest["sources"]["functions"] = "functions.json"
    files["manifest.json"] = _json_text(manifest)

    world = json.loads(files["world.json"])
    world["alien_lineage_runtime"] = runtime_slice["runtime_config"]
    world["runtime_extensions"] = [runtime_slice["runtime_module"]]
    files["world.json"] = _json_text(world)
    files["functions.json"] = _json_text(runtime_slice["functions"])

    output_hashes = {name: sha256_bytes(text.encode("utf-8")) for name, text in sorted(files.items())}
    source_hashes = {
        "semantic_snapshot": sha256_json(semantic_snapshot),
        "composition_receipt": sha256_json(composition_receipt),
        "asset_graph_snapshot": sha256_json(asset_graph_snapshot),
        "intake_plan": sha256_json(intake_plan),
        "runtime_slice": sha256_json(runtime_slice),
        "base_intake_receipt": sha256_json(base_receipt),
    }
    authoring_sha = sha256_json({"output_hashes": output_hashes})
    basis = {
        "slice_id": runtime_slice["slice_id"],
        "base_intake_receipt_id": base_receipt["receipt_id"],
        "runtime_module": runtime_slice["runtime_module"],
        "source_hashes": source_hashes,
        "authoring_sha256": authoring_sha,
    }
    receipt = {
        "contract": "alien-lineage-runtime-receipt.v0.1",
        "receipt_id": f"alien-runtime:{runtime_slice['slice_id'].replace(':', '.') }:{sha256_json(basis)[:16]}",
        "slice_id": runtime_slice["slice_id"],
        "base_intake_receipt_id": base_receipt["receipt_id"],
        "runtime_module": runtime_slice["runtime_module"],
        "source_hashes": source_hashes,
        "output_hashes": output_hashes,
        "authoring_sha256": authoring_sha,
    }
    errors = validation_errors(_schema(root_path, "alien-lineage-runtime-receipt.v0.1"), receipt)
    if errors:
        raise AlienLineageBuildError("internal runtime receipt violates contract: " + "; ".join(errors))
    return files, receipt


def emit_runtime_authoring(
    semantic_snapshot_path: str | Path,
    composition_receipt_path: str | Path,
    asset_graph_snapshot_path: str | Path,
    intake_plan_path: str | Path,
    runtime_slice_path: str | Path,
    output_dir: str | Path,
    *,
    root: str | Path,
) -> Path:
    root_path = Path(root)
    try:
        semantic = load_json(semantic_snapshot_path)
        composition = load_json(composition_receipt_path)
        graph = load_json(asset_graph_snapshot_path)
        plan = load_json(intake_plan_path)
        slice_doc = load_json(runtime_slice_path)
    except ContractValidationError as exc:
        raise AlienLineageBuildError(str(exc)) from exc
    files, receipt = build_runtime_authoring_files(semantic, composition, graph, plan, slice_doc, root=root_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for relative, text in files.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="")
    receipt_path = destination / "awa-alien-lineage-runtime-receipt.json"
    receipt_path.write_text(_json_text(receipt), encoding="utf-8", newline="")
    return receipt_path
