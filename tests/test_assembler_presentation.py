from __future__ import annotations

import json
from pathlib import Path

from awa_assembler.loop import BoundedAssembler
from awa_assembler.provider import ReferencePresentationRecipeProducer

ROOT = Path(__file__).resolve().parents[1]


def j(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "project_state": ROOT / "PROJECT_STATE.json",
        "semantic_snapshot": ROOT / "fixtures/sedb/expected.game.alien_lineage.snapshot.json",
        "composition_receipt": ROOT / "fixtures/csc_ocm/expected.alien_lineage.composition-receipt.json",
        "presentation_binding": ROOT / "fixtures/threejs/alien-lineage.presentation-binding.json",
        "capability_contract": ROOT / "fixtures/assembler/presentation_recipe_generation.capability.json",
        "nodes": ROOT / "fixtures/assembler_presentation_graph/nodes",
        "edges": ROOT / "fixtures/assembler_presentation_graph/edges",
        "artifacts": ROOT / "fixtures/assembler_presentation_graph/artifacts",
        "validations": ROOT / "fixtures/assembler_presentation_graph/validations",
        "out": tmp_path / "assembler-presentation",
    }


def build(tmp_path: Path):
    task = j("fixtures/assembler/alien-lineage.mutation-effect-recipe.task.json")
    return BoundedAssembler(root=ROOT, producer=ReferencePresentationRecipeProducer()).run(task=task, **paths(tmp_path))


def test_presentation_recipe_repairs_contract_and_authority_failure(tmp_path: Path) -> None:
    receipt = build(tmp_path)
    assert receipt["status"] == "validated_candidate"
    assert [item["validation_status"] for item in receipt["attempts"]] == ["failed", "passed"]
    first = "\n".join(receipt["attempts"][0]["diagnostics"])
    assert "runtime_action" in first
    assert "duration_ms" in first
    assert receipt["promotion"]["canonical_write"] is False
    assert receipt["attempts"][0]["artifact_sha256"] == "c1b753e2c8f7150566a146f0e517a323bf4d6ea7d47257aadc23379ad27fdd99"
    assert receipt["attempts"][1]["artifact_sha256"] == "c26cd3b1af92ca515ca81680f2982bb296237ff38f4fe95ca930f2eb83bcaeb5"


def test_selected_recipe_is_declarative_presentation_only(tmp_path: Path) -> None:
    receipt = build(tmp_path)
    candidate = json.loads((paths(tmp_path)["out"] / "candidate" / "mutation_effect_recipe.json").read_text())
    assert candidate["contract"] == "presentation-effect-recipe.v0.1"
    assert candidate["event_type"] == "alien_lineage.creature_mutated"
    assert candidate["effect"]["target"] == "creature_visual"
    assert "runtime_action" not in candidate
    assert receipt["selected_candidate"]["mime_type"] == "application/json"


def test_presentation_candidate_closes_its_own_graph_without_canonical_promotion(tmp_path: Path) -> None:
    before = j("fixtures/assembler_presentation_graph/expected.graph-snapshot.json")
    receipt = build(tmp_path)
    preview = json.loads((paths(tmp_path)["out"] / "candidate" / "graph-snapshot.preview.json").read_text())
    assert len(before["missing_required"]) == 1
    assert before["missing_required"][0]["to"] == "artifact.presentation.threejs.mutation_effect_recipe"
    assert preview["missing_required"] == []
    assert preview["generation_task_ids"] == []
    target = next(item for item in preview["artifact_statuses"] if item["node_id"] == "artifact.presentation.threejs.mutation_effect_recipe")
    assert target["effective_status"] == "passed"
    assert receipt["promotion"]["status"] == "validated_candidate"
    assert not (ROOT / "fixtures/assembler_presentation_graph/nodes/artifact.presentation.threejs.mutation_effect_recipe.json").exists()


def test_presentation_recipe_evidence_is_deterministic(tmp_path: Path) -> None:
    first = build(tmp_path / "a")
    second = build(tmp_path / "b")
    assert first["selected_candidate"]["sha256"] == second["selected_candidate"]["sha256"]
    assert first["evidence_hash"] == second["evidence_hash"]


def test_threejs_effect_host_contains_no_runtime_write_primitives() -> None:
    source = (ROOT / "presentation/threejs/src/effect-recipe.js").read_text(encoding="utf-8")
    for token in ["/api/action", "StateDelta", "EntityRegistry", "runtime.state", "registry.add("]:
        assert token not in source
