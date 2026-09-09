from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from awa_asset_graph import AssetGraph, AssetGraphError
from awa_contracts.validator import validation_errors

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures" / "asset_graph"
NODES = FIX / "nodes"
EDGES = FIX / "edges"
ARTIFACTS = FIX / "artifacts"
VALIDATIONS = FIX / "validations"
EXPECTED_SNAPSHOT = FIX / "expected.crystal_filterer.graph-snapshot.json"
EXPECTED_TASKS = FIX / "expected.crystal_filterer.generation-tasks.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _graph() -> AssetGraph:
    return AssetGraph.from_directories(nodes=NODES, edges=EDGES, artifacts=ARTIFACTS, validations=VALIDATIONS, root=ROOT)


def test_golden_snapshot_and_generation_task_are_deterministic() -> None:
    graph = _graph()
    one = graph.analyze(["species.crystal_filterer"])
    two = graph.analyze(["species.crystal_filterer"])
    assert one == two
    assert one.snapshot == _load(EXPECTED_SNAPSHOT)
    assert one.generation_tasks == _load(EXPECTED_TASKS)
    snapshot_schema = _load(ROOT / "schemas" / "asset-graph-snapshot.v0.1.schema.json")
    task_schema = _load(ROOT / "schemas" / "generation-task.v0.1.schema.json")
    assert validation_errors(snapshot_schema, one.snapshot) == []
    assert all(validation_errors(task_schema, task) == [] for task in one.generation_tasks)
    assert one.snapshot["required_closure"] == ["artifact.mesh.crystal_filterer", "behavior.filter_feed", "species.crystal_filterer"]
    assert len(one.snapshot["missing_required"]) == 1
    assert one.snapshot["missing_required"][0]["to"] == "artifact.audio.crystal_filterer.attack"
    assert one.snapshot["artifact_statuses"][0]["effective_status"] == "passed"


def test_only_required_dependency_cycles_are_rejected() -> None:
    graph = _graph()
    assert graph.analyze(["species.crystal_filterer"]).snapshot["required_closure"]
    nodes = copy.deepcopy(graph.nodes)
    edges = copy.deepcopy(graph.edges)
    edges["edge:required-cycle"] = {
        "contract": "asset-graph-edge.v0.1", "edge_id": "edge:required-cycle",
        "from": "behavior.filter_feed", "to": "species.crystal_filterer",
        "type": "requires", "required": True, "version_constraint": "v0.1",
        "scope": "asset", "reason": "test required cycle", "provenance_ref": "prov:test:cycle",
    }
    cyc = AssetGraph(nodes, edges, copy.deepcopy(graph.artifacts), copy.deepcopy(graph.validations), root=ROOT)
    with pytest.raises(AssetGraphError, match="required asset dependency cycle"):
        cyc.analyze(["species.crystal_filterer"])


def test_version_constraints_and_dependency_flags_fail_closed() -> None:
    graph = _graph()
    edges = copy.deepcopy(graph.edges)
    edges["edge:crystal_filterer->mesh"]["version_constraint"] = "v9.9"
    with pytest.raises(AssetGraphError, match="version constraint mismatch"):
        AssetGraph(copy.deepcopy(graph.nodes), edges, copy.deepcopy(graph.artifacts), copy.deepcopy(graph.validations), root=ROOT)
    edges = copy.deepcopy(graph.edges)
    edges["edge:crystal_filterer->mesh"]["required"] = False
    with pytest.raises(AssetGraphError, match="requires edge must set required=true"):
        AssetGraph(copy.deepcopy(graph.nodes), edges, copy.deepcopy(graph.artifacts), copy.deepcopy(graph.validations), root=ROOT)


def test_non_dependency_missing_target_and_bad_validation_binding_fail_closed() -> None:
    graph = _graph()
    edges = copy.deepcopy(graph.edges)
    edges["edge:mesh->validation"]["to"] = "validation.missing"
    with pytest.raises(AssetGraphError, match="edge target node not found"):
        AssetGraph(copy.deepcopy(graph.nodes), edges, copy.deepcopy(graph.artifacts), copy.deepcopy(graph.validations), root=ROOT)
    validations = copy.deepcopy(graph.validations)
    validations["validation.mesh.crystal_filterer.v1"]["artifact_id"] = "artifact.somewhere.else"
    with pytest.raises(AssetGraphError, match="validation artifact mismatch"):
        AssetGraph(copy.deepcopy(graph.nodes), copy.deepcopy(graph.edges), copy.deepcopy(graph.artifacts), validations, root=ROOT)


def test_artifact_and_validation_nodes_require_external_refs() -> None:
    graph = _graph()
    nodes = copy.deepcopy(graph.nodes)
    nodes["artifact.mesh.crystal_filterer"]["metadata"] = {}
    with pytest.raises(AssetGraphError, match="metadata.artifact_ref"):
        AssetGraph(nodes, copy.deepcopy(graph.edges), copy.deepcopy(graph.artifacts), copy.deepcopy(graph.validations), root=ROOT)
    nodes = copy.deepcopy(graph.nodes)
    nodes["validation.mesh.crystal_filterer"]["metadata"] = {}
    with pytest.raises(AssetGraphError, match="metadata.validation_ref"):
        AssetGraph(nodes, copy.deepcopy(graph.edges), copy.deepcopy(graph.artifacts), copy.deepcopy(graph.validations), root=ROOT)


def test_validation_evidence_becomes_stale_when_artifact_hash_changes() -> None:
    graph = _graph()
    artifacts = copy.deepcopy(graph.artifacts)
    artifacts["artifact.mesh.crystal_filterer.v1"]["sha256"] = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    changed = AssetGraph(copy.deepcopy(graph.nodes), copy.deepcopy(graph.edges), artifacts, copy.deepcopy(graph.validations), root=ROOT)
    analysis = changed.analyze(["species.crystal_filterer"])
    status = analysis.snapshot["artifact_statuses"][0]
    assert status["effective_status"] == "stale"
    assert status["fresh_validation_ids"] == []
    assert status["stale_validation_ids"] == ["validation.mesh.crystal_filterer.v1"]
    assert analysis.snapshot["sha256"] != _load(EXPECTED_SNAPSHOT)["sha256"]


def test_fresh_failed_validation_dominates_passed_status() -> None:
    graph = _graph()
    validations = copy.deepcopy(graph.validations)
    failed = copy.deepcopy(validations["validation.mesh.crystal_filterer.v1"])
    failed["validation_id"] = "validation.mesh.crystal_filterer.failed"
    failed["status"] = "failed"
    failed["diagnostics"] = ["non-finite vertex"]
    validations[failed["validation_id"]] = failed
    nodes = copy.deepcopy(graph.nodes)
    nodes["validation.mesh.crystal_filterer.failed"] = {
        "contract": "asset-graph-node.v0.1", "node_id": "validation.mesh.crystal_filterer.failed",
        "node_type": "validation", "namespace": "game.alien_lineage", "semantic_ref": "species.crystal_filterer",
        "version": "v0.1", "status": "active", "metadata": {"validation_ref": failed["validation_id"]},
        "provenance_ref": "prov:test:failed-validation",
    }
    edges = copy.deepcopy(graph.edges)
    edges["edge:mesh->failed-validation"] = {
        "contract": "asset-graph-edge.v0.1", "edge_id": "edge:mesh->failed-validation",
        "from": "artifact.mesh.crystal_filterer", "to": "validation.mesh.crystal_filterer.failed",
        "type": "validated_by", "required": False, "version_constraint": None, "scope": "validation",
        "reason": "failing test evidence", "provenance_ref": "prov:test:failed-validation-edge",
    }
    changed = AssetGraph(nodes, edges, copy.deepcopy(graph.artifacts), validations, root=ROOT)
    status = changed.analyze(["species.crystal_filterer"]).snapshot["artifact_statuses"][0]
    assert status["effective_status"] == "failed"
    assert status["fresh_validation_ids"] == ["validation.mesh.crystal_filterer.failed", "validation.mesh.crystal_filterer.v1"]


def test_unrelated_optional_edges_do_not_change_required_snapshot_hash() -> None:
    graph = _graph()
    original = graph.analyze(["species.crystal_filterer"]).snapshot
    edges = copy.deepcopy(graph.edges)
    edges["edge:optional-extra"] = {
        "contract": "asset-graph-edge.v0.1", "edge_id": "edge:optional-extra",
        "from": "species.crystal_filterer", "to": "artifact.optional.not_materialized",
        "type": "optional", "required": False, "version_constraint": None, "scope": "asset",
        "reason": "optional missing asset", "provenance_ref": "prov:test:optional",
    }
    changed = AssetGraph(copy.deepcopy(graph.nodes), edges, copy.deepcopy(graph.artifacts), copy.deepcopy(graph.validations), root=ROOT)
    assert changed.analyze(["species.crystal_filterer"]).snapshot == original


def test_unknown_root_is_rejected() -> None:
    with pytest.raises(AssetGraphError, match="graph root node not found"):
        _graph().analyze(["species.unknown"])


def test_cli_check_and_snapshot_smoke(tmp_path: Path) -> None:
    from awa_asset_graph.__main__ import main
    common = ["--nodes", str(NODES), "--edges", str(EDGES), "--artifacts", str(ARTIFACTS), "--validations", str(VALIDATIONS), "--root-dir", str(ROOT)]
    assert main([*common, "check"]) == 0
    snapshot_path = tmp_path / "snapshot.json"
    tasks_path = tmp_path / "tasks.json"
    assert main([*common, "snapshot", "species.crystal_filterer", "-o", str(snapshot_path), "--tasks-output", str(tasks_path)]) == 0
    assert _load(snapshot_path) == _load(EXPECTED_SNAPSHOT)
    assert _load(tasks_path) == _load(EXPECTED_TASKS)
