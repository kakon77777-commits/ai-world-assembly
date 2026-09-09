from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from awa_contracts.validator import ContractValidationError, load_json, validation_errors
from awa_sedb_adapter.projection import sha256_json as sedb_sha256_json


class CompilableWorldIntakeError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _schema(root: Path, contract: str) -> dict[str, Any]:
    try:
        return load_json(root / "schemas" / f"{contract}.schema.json")
    except ContractValidationError as exc:
        raise CompilableWorldIntakeError(str(exc)) from exc


def _validate(root: Path, contract: str, document: Any, label: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise CompilableWorldIntakeError(f"{label} must be a JSON object")
    errors = validation_errors(_schema(root, contract), document)
    if errors:
        raise CompilableWorldIntakeError(f"{label} violates {contract}: " + "; ".join(errors))
    return document


def _load_validated(path: str | Path, contract: str, *, root: Path, label: str) -> dict[str, Any]:
    try:
        document = load_json(path)
    except ContractValidationError as exc:
        raise CompilableWorldIntakeError(str(exc)) from exc
    return _validate(root, contract, document, label)


def _verify_semantic_snapshot(root: Path, snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if snapshot["entity_count"] != len(snapshot["entities"]):
        raise CompilableWorldIntakeError("semantic snapshot entity_count does not match entities length")
    basis = {key: value for key, value in snapshot.items() if key != "sha256"}
    if sedb_sha256_json(basis) != snapshot["sha256"]:
        raise CompilableWorldIntakeError("semantic snapshot sha256 mismatch")
    entities: dict[str, dict[str, Any]] = {}
    for entity in snapshot["entities"]:
        _validate(root, "semantic-game-entity.v0.1", entity, "semantic entity")
        entity_id = entity["entity_id"]
        if entity_id in entities:
            raise CompilableWorldIntakeError(f"duplicate semantic entity id: {entity_id}")
        if entity["namespace"] != snapshot["namespace"]:
            raise CompilableWorldIntakeError(f"semantic entity namespace mismatch: {entity_id}")
        entities[entity_id] = entity
    return entities


def _verify_graph_snapshot(snapshot: dict[str, Any]) -> None:
    body = {key: value for key, value in snapshot.items() if key not in {"snapshot_id", "sha256"}}
    digest = sha256_json(body)
    if digest != snapshot["sha256"] or snapshot["snapshot_id"] != f"graph:{digest[:16]}":
        raise CompilableWorldIntakeError("asset graph snapshot identity mismatch")
    if snapshot["missing_required"] or snapshot["generation_task_ids"]:
        raise CompilableWorldIntakeError("asset graph snapshot is not build-complete")
    bad = sorted(
        status["node_id"]
        for status in snapshot["artifact_statuses"]
        if status["effective_status"] != "passed"
    )
    if bad:
        raise CompilableWorldIntakeError(f"asset graph contains non-passed required artifacts: {bad}")


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for value in values:
        if value in seen:
            duplicate.add(value)
        seen.add(value)
    return sorted(duplicate)


def _validate_plan_links(
    plan: dict[str, Any],
    semantic_entities: dict[str, dict[str, Any]],
    composition: dict[str, Any],
    graph: dict[str, Any],
) -> None:
    missing_modules = sorted(set(plan["required_composition_modules"]) - set(composition["resolved_modules"]))
    if missing_modules:
        raise CompilableWorldIntakeError(f"intake plan requires unresolved composition modules: {missing_modules}")
    if sorted(plan["graph_roots"]) != sorted(graph["roots"]):
        raise CompilableWorldIntakeError("intake plan graph_roots must exactly match asset graph snapshot roots in v0.1")

    room_ids = [room["room_id"] for room in plan["rooms"]]
    duplicates = _duplicates(room_ids)
    if duplicates:
        raise CompilableWorldIntakeError(f"duplicate room ids: {duplicates}")
    room_set = set(room_ids)
    if plan["world"]["player_spawn"] not in room_set:
        raise CompilableWorldIntakeError("world.player_spawn is not declared in intake rooms")

    runtime_ids = [entity["runtime_entity_id"] for entity in plan["entities"]]
    duplicates = _duplicates(runtime_ids)
    if duplicates:
        raise CompilableWorldIntakeError(f"duplicate runtime entity ids: {duplicates}")
    if plan["world"]["default_player_entity"] not in set(runtime_ids):
        raise CompilableWorldIntakeError("world.default_player_entity is not declared in intake entities")

    for entity in plan["entities"]:
        if entity["semantic_ref"] not in semantic_entities:
            raise CompilableWorldIntakeError(f"semantic_ref not found in SEDB projection: {entity['semantic_ref']}")
        if entity["room"] not in room_set:
            raise CompilableWorldIntakeError(f"runtime entity references unknown room: {entity['runtime_entity_id']} -> {entity['room']}")
    for item in plan["items"]:
        if item["room"] not in room_set:
            raise CompilableWorldIntakeError(f"item references unknown room: {item['item_id']} -> {item['room']}")
    exit_ids = [edge["exit_id"] for edge in plan["exits"]]
    duplicates = _duplicates(exit_ids)
    if duplicates:
        raise CompilableWorldIntakeError(f"duplicate exit ids: {duplicates}")
    for edge in plan["exits"]:
        if edge["from_room"] not in room_set or edge["to_room"] not in room_set:
            raise CompilableWorldIntakeError(f"exit references unknown room: {edge['exit_id']}")


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


def build_authoring_files(
    semantic_snapshot: dict[str, Any],
    composition_receipt: dict[str, Any],
    asset_graph_snapshot: dict[str, Any],
    intake_plan: dict[str, Any],
    *,
    root: str | Path,
) -> tuple[dict[str, str], dict[str, Any]]:
    root_path = Path(root)
    _validate(root_path, "sedb-namespace-snapshot.v0.1", semantic_snapshot, "SEDB namespace snapshot")
    _validate(root_path, "composition-receipt.v0.1", composition_receipt, "composition receipt")
    _validate(root_path, "asset-graph-snapshot.v0.1", asset_graph_snapshot, "asset graph snapshot")
    _validate(root_path, "compilableworld-intake-plan.v0.1", intake_plan, "CompilableWorld intake plan")
    semantic_entities = _verify_semantic_snapshot(root_path, semantic_snapshot)
    _verify_graph_snapshot(asset_graph_snapshot)
    _validate_plan_links(intake_plan, semantic_entities, composition_receipt, asset_graph_snapshot)

    world_spec = intake_plan["world"]
    files: dict[str, str] = {}
    manifest = {
        "world_id": world_spec["world_id"],
        "world_version": world_spec["world_version"],
        "schema_version": world_spec["schema_version"],
        "namespace": world_spec["namespace"],
        "compiler_version": "0.1.0",
        "targets": ["mssp-python-runtime"],
        "sources": {
            "world": "world.json",
            "rooms": "data/rooms.csv",
            "exits": "data/exits.csv",
            "entities": "data/entities.csv",
            "items": "data/items.csv",
            "quests": "quests.json",
            "scenarios": "scenarios.json"
        },
        "modules": sorted(intake_plan["runtime_modules"]),
        "build": {"strict": True, "fail_on_warning": False}
    }
    files["manifest.json"] = _json_text(manifest)
    files["world.json"] = _json_text({
        "title": world_spec["title"],
        "default_language": world_spec["default_language"],
        "player_spawn": world_spec["player_spawn"],
        "default_player_entity": world_spec["default_player_entity"],
        "provenance": {
            "source_type": "awa_intake",
            "canon_status": "runtime_projection",
            "intake_id": intake_plan["intake_id"]
        }
    })
    room_rows = [
        {"room_id": room["room_id"], "name": room["name"], "description": room["description"], "region": room["region"]}
        for room in sorted(intake_plan["rooms"], key=lambda item: item["room_id"])
    ]
    files["data/rooms.csv"] = _csv_text(["room_id", "name", "description", "region"], room_rows)
    exit_rows = [
        {
            "exit_id": edge["exit_id"],
            "from_room": edge["from_room"],
            "to_room": edge["to_room"],
            "direction": edge["direction"],
            "bidirectional": "true" if edge["bidirectional"] else "false",
            "door_entity": "",
            "open": "true",
            "locked": "false",
            "key_id": ""
        }
        for edge in sorted(intake_plan["exits"], key=lambda item: item["exit_id"])
    ]
    files["data/exits.csv"] = _csv_text(
        ["exit_id", "from_room", "to_room", "direction", "bidirectional", "door_entity", "open", "locked", "key_id"],
        exit_rows,
    )
    entity_rows = []
    for entity in sorted(intake_plan["entities"], key=lambda item: item["runtime_entity_id"]):
        semantic = semantic_entities[entity["semantic_ref"]]
        entity_rows.append({
            "entity_id": entity["runtime_entity_id"],
            "entity_type": entity["entity_type"],
            "name": semantic["label"],
            "room": entity["room"],
            "health": "" if entity["health"] is None else str(entity["health"]),
            "components": "|".join(sorted(entity["components"])),
            "provenance": f"awa:{entity['semantic_ref']}"
        })
    files["data/entities.csv"] = _csv_text(
        ["entity_id", "entity_type", "name", "room", "health", "components", "provenance"],
        entity_rows,
    )
    item_rows = [
        {
            "item_id": item["item_id"],
            "name": item["name"],
            "room": item["room"],
            "portable": "true" if item["portable"] else "false",
            "provenance": item["provenance"]
        }
        for item in sorted(intake_plan["items"], key=lambda item: item["item_id"])
    ]
    files["data/items.csv"] = _csv_text(["item_id", "name", "room", "portable", "provenance"], item_rows)
    files["quests.json"] = _json_text(intake_plan["quests"])
    files["scenarios.json"] = _json_text({"scenarios": sorted(intake_plan["scenarios"], key=lambda item: item.get("scenario_id", ""))})

    output_hashes = {name: sha256_bytes(text.encode("utf-8")) for name, text in sorted(files.items())}
    source_hashes = {
        "semantic_snapshot": sha256_json(semantic_snapshot),
        "composition_receipt": sha256_json(composition_receipt),
        "asset_graph_snapshot": sha256_json(asset_graph_snapshot),
        "intake_plan": sha256_json(intake_plan),
    }
    authoring_sha = sha256_json({"output_hashes": output_hashes})
    receipt_basis = {
        "intake_id": intake_plan["intake_id"],
        "world_id": world_spec["world_id"],
        "source_hashes": source_hashes,
        "authoring_sha256": authoring_sha,
    }
    receipt = {
        "contract": "compilableworld-intake-receipt.v0.1",
        "receipt_id": f"cw-intake:{intake_plan['intake_id'].replace(':', '.') }:{sha256_json(receipt_basis)[:16]}",
        "intake_id": intake_plan["intake_id"],
        "world_id": world_spec["world_id"],
        "target": "compilableworld.authoring/v0.1",
        "files": sorted(files),
        "source_hashes": source_hashes,
        "output_hashes": output_hashes,
        "authoring_sha256": authoring_sha,
    }
    errors = validation_errors(_schema(root_path, "compilableworld-intake-receipt.v0.1"), receipt)
    if errors:
        raise CompilableWorldIntakeError("internal intake receipt violates contract: " + "; ".join(errors))
    return files, receipt


def emit_authoring(
    semantic_snapshot_path: str | Path,
    composition_receipt_path: str | Path,
    asset_graph_snapshot_path: str | Path,
    intake_plan_path: str | Path,
    output_dir: str | Path,
    *,
    root: str | Path,
) -> Path:
    root_path = Path(root)
    semantic_snapshot = _load_validated(semantic_snapshot_path, "sedb-namespace-snapshot.v0.1", root=root_path, label="SEDB namespace snapshot")
    composition_receipt = _load_validated(composition_receipt_path, "composition-receipt.v0.1", root=root_path, label="composition receipt")
    graph_snapshot = _load_validated(asset_graph_snapshot_path, "asset-graph-snapshot.v0.1", root=root_path, label="asset graph snapshot")
    plan = _load_validated(intake_plan_path, "compilableworld-intake-plan.v0.1", root=root_path, label="CompilableWorld intake plan")
    files, receipt = build_authoring_files(semantic_snapshot, composition_receipt, graph_snapshot, plan, root=root_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for relative, text in files.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="")
    receipt_path = destination / "awa-intake-receipt.json"
    receipt_path.write_text(_json_text(receipt), encoding="utf-8", newline="")
    return receipt_path
