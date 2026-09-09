from __future__ import annotations

from pathlib import Path
from typing import Any

from awa_asset_graph.graph import AssetGraph, sha256_json
from awa_contracts.validator import load_json

from .common import AssemblerError, validate
from .validators import VALIDATORS


def load_context(*, root: Path, task: dict[str, Any], project_state: Path,
                 semantic_snapshot: Path, composition_receipt: Path,
                 presentation_binding: Path, capability_contract: Path,
                 nodes: Path, edges: Path, artifacts: Path, validations: Path):
    validate(root, "assembler-task.v0.1", task, "assembler task")
    generation = validate(root, "generation-task.v0.1", task["generation_task"], "generation task")
    semantic = validate(root, "sedb-namespace-snapshot.v0.1", load_json(semantic_snapshot), "semantic snapshot")
    composition = validate(root, "composition-receipt.v0.1", load_json(composition_receipt), "composition receipt")
    presentation = validate(root, "presentation-binding.v0.1", load_json(presentation_binding), "presentation binding")
    capability = validate(root, "capability-contract.v0.1", load_json(capability_contract), "capability contract")
    state = load_json(project_state)
    if not isinstance(state, dict):
        raise AssemblerError("project state must be a JSON object")

    graph = AssetGraph.from_directories(nodes=nodes, edges=edges, artifacts=artifacts,
                                        validations=validations, root=root)
    before = graph.analyze([generation["target"]["node_ref"]])
    if len(before.generation_tasks) != 1 or before.generation_tasks[0] != generation:
        raise AssemblerError("generation task does not match the observed missing required target")

    refs = task["context_refs"]
    checks = [
        (semantic["sha256"] == refs["semantic_snapshot_sha256"], "semantic snapshot context mismatch"),
        (composition["receipt_id"] == refs["composition_receipt_id"], "composition receipt context mismatch"),
        (before.snapshot["snapshot_id"] == refs["graph_snapshot_id"], "asset graph context mismatch"),
        (presentation["binding_id"] == refs["presentation_binding_id"], "presentation binding context mismatch"),
        (capability["capability"]["id"] == task["capability_id"], "capability contract context mismatch"),
        (capability["capability"]["authority"] == "proposal", "assembler generation capability must remain proposal authority"),
        (generation["authority"] == task["authority"] == "proposal", "assembler task must remain proposal authority"),
        (task["target"]["node_id"] == generation["target"]["missing_role"], "generation target mismatch"),
        (task["target"]["layer"] in generation["allowed_layers"], "target layer is outside generation task authority"),
        (task["repair_policy"]["max_attempts"] <= generation["budget"]["max_attempts"], "repair policy exceeds generation task attempt budget"),
        (task["repair_policy"]["max_attempts"] <= capability["capability"]["budget"]["max_calls"], "repair policy exceeds capability call budget"),
    ]
    for ok, message in checks:
        if not ok:
            raise AssemblerError(message)
    unknown = sorted(set(task["validators"]) - set(VALIDATORS))
    if unknown:
        raise AssemblerError(f"unknown validators: {unknown}")

    source_hashes = {
        "project_state": sha256_json(state),
        "semantic_snapshot": sha256_json(semantic),
        "composition_receipt": sha256_json(composition),
        "graph_snapshot_before": sha256_json(before.snapshot),
        "presentation_binding": sha256_json(presentation),
        "capability_contract": sha256_json(capability),
    }
    return {"graph_before": before.snapshot}, source_hashes, graph, generation
