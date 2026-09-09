from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from awa_contracts.validator import ContractValidationError, load_json, validation_errors
from awa_cw_intake.intake import CompilableWorldIntakeError, build_authoring_files, sha256_bytes, sha256_json

COMPILABLEWORLD_ENTITY_TRANSACTION_COMMIT = "cf37f539e0807499e8b337f80a5f152324c087f2"


class RelayStationBuildError(ValueError):
    pass


def _schema(root: Path, contract: str) -> dict[str, Any]:
    return load_json(root / "schemas" / f"{contract}.schema.json")


def _validate(root: Path, contract: str, document: Any, label: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise RelayStationBuildError(f"{label} must be a JSON object")
    errors = validation_errors(_schema(root, contract), document)
    if errors:
        raise RelayStationBuildError(f"{label} violates {contract}: " + "; ".join(errors))
    return document


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _verify_links(slice_doc: dict[str, Any], semantic: dict[str, Any], plan: dict[str, Any]) -> None:
    config = slice_doc["runtime_config"]
    semantic_ids = {item["entity_id"] for item in semantic["entities"]}
    required_refs = {config["runner_semantic_ref"], config["relay_semantic_ref"], config["beacon"]["semantic_ref"]}
    missing = sorted(required_refs - semantic_ids)
    if missing:
        raise RelayStationBuildError(f"runtime slice semantic refs missing from snapshot: {missing}")
    authored = {item["runtime_entity_id"] for item in plan["entities"]} | {item["item_id"] for item in plan["items"]}
    expected = {config["runner_entity_id"], config["relay_entity_id"], config["coupler_item_id"]}
    if not expected <= authored:
        raise RelayStationBuildError(f"runtime config references unauthored IDs: {sorted(expected-authored)}")
    beacon_id = config["beacon"]["entity_id"]
    if beacon_id in authored:
        raise RelayStationBuildError("reviewed beacon ID must not exist in base authoring")
    modules = {item["module_id"] for item in slice_doc["runtime_modules"]}
    if modules != {"relay_station.runtime", "relay_station.activation"}:
        raise RelayStationBuildError("runtime slice must declare exactly relay_station.runtime and relay_station.activation")


def build_runtime_authoring_files(semantic_snapshot: dict[str, Any], composition_receipt: dict[str, Any], asset_graph_snapshot: dict[str, Any], intake_plan: dict[str, Any], runtime_slice: dict[str, Any], *, root: str | Path) -> tuple[dict[str, str], dict[str, Any]]:
    root_path = Path(root)
    _validate(root_path, "relay-station-runtime-slice.v0.1", runtime_slice, "Relay Station runtime slice")
    _verify_links(runtime_slice, semantic_snapshot, intake_plan)
    try:
        files, base_receipt = build_authoring_files(semantic_snapshot, composition_receipt, asset_graph_snapshot, intake_plan, root=root_path)
    except CompilableWorldIntakeError as exc:
        raise RelayStationBuildError(str(exc)) from exc
    world = json.loads(files["world.json"])
    world["relay_station_runtime"] = runtime_slice["runtime_config"]
    world["runtime_extensions"] = runtime_slice["runtime_modules"]
    files["world.json"] = _json_text(world)
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
    basis = {"slice_id": runtime_slice["slice_id"], "base": base_receipt["receipt_id"], "compatibility_commit": COMPILABLEWORLD_ENTITY_TRANSACTION_COMMIT, "source_hashes": source_hashes, "authoring_sha256": authoring_sha}
    receipt = {
        "contract": "relay-station-runtime-receipt.v0.1",
        "receipt_id": f"relay-runtime:{runtime_slice['slice_id'].replace(':','.') }:{sha256_json(basis)[:16]}",
        "slice_id": runtime_slice["slice_id"],
        "base_intake_receipt_id": base_receipt["receipt_id"],
        "runtime_modules": runtime_slice["runtime_modules"],
        "compatibility_commit": COMPILABLEWORLD_ENTITY_TRANSACTION_COMMIT,
        "source_hashes": source_hashes,
        "output_hashes": output_hashes,
        "authoring_sha256": authoring_sha,
    }
    errors = validation_errors(_schema(root_path, "relay-station-runtime-receipt.v0.1"), receipt)
    if errors:
        raise RelayStationBuildError("internal runtime receipt violates contract: " + "; ".join(errors))
    return files, receipt


def emit_runtime_authoring(semantic_snapshot_path: str | Path, composition_receipt_path: str | Path, asset_graph_snapshot_path: str | Path, intake_plan_path: str | Path, runtime_slice_path: str | Path, output_dir: str | Path, *, root: str | Path) -> Path:
    root_path = Path(root)
    try:
        semantic = load_json(semantic_snapshot_path); composition = load_json(composition_receipt_path); graph = load_json(asset_graph_snapshot_path); plan = load_json(intake_plan_path); slice_doc = load_json(runtime_slice_path)
    except ContractValidationError as exc:
        raise RelayStationBuildError(str(exc)) from exc
    files, receipt = build_runtime_authoring_files(semantic, composition, graph, plan, slice_doc, root=root_path)
    dest = Path(output_dir); dest.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        target = dest / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text, encoding="utf-8", newline="")
    path = dest / "awa-relay-station-runtime-receipt.json"; path.write_text(_json_text(receipt), encoding="utf-8", newline="")
    return path
