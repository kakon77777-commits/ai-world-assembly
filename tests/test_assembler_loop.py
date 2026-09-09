from __future__ import annotations

import json
from pathlib import Path

import pytest

from awa_assembler.loop import AssemblerError, BoundedAssembler
from awa_assembler.provider import ReferenceAudioProducer

ROOT = Path(__file__).resolve().parents[1]


def j(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "project_state": ROOT / "PROJECT_STATE.json",
        "semantic_snapshot": ROOT / "fixtures/sedb/expected.game.alien_lineage.snapshot.json",
        "composition_receipt": ROOT / "fixtures/csc_ocm/expected.alien_lineage.composition-receipt.json",
        "presentation_binding": ROOT / "fixtures/threejs/alien-lineage.presentation-binding.json",
        "capability_contract": ROOT / "fixtures/assembler/audio_generation.capability.json",
        "nodes": ROOT / "fixtures/asset_graph/nodes",
        "edges": ROOT / "fixtures/asset_graph/edges",
        "artifacts": ROOT / "fixtures/asset_graph/artifacts",
        "validations": ROOT / "fixtures/asset_graph/validations",
        "out": tmp_path / "assembler",
    }


def build(tmp_path: Path, *, max_attempts: int | None = None):
    task = j("fixtures/assembler/alien-lineage.attack-audio.task.json")
    if max_attempts is not None:
        task["repair_policy"]["max_attempts"] = max_attempts
    assembler = BoundedAssembler(root=ROOT, producer=ReferenceAudioProducer())
    return assembler.run(task=task, **paths(tmp_path))


def test_reference_loop_repairs_failed_first_candidate(tmp_path: Path) -> None:
    receipt = build(tmp_path)
    assert receipt["status"] == "validated_candidate"
    assert [item["validation_status"] for item in receipt["attempts"]] == ["failed", "passed"]
    assert any("non_silent" in item for item in receipt["attempts"][0]["diagnostics"])
    assert receipt["attempts"][0]["artifact_sha256"] == "23fc92432963f74bd638f38ea9d7ddb475853f022810bdc8b344269bf43d5830"
    assert receipt["attempts"][1]["artifact_sha256"] == "28f03358e57423849a0a88e87221412ad7421c5c1defea70662f8e23191baabf"
    assert receipt["promotion"] == {
        "status": "validated_candidate",
        "target_node_status": "candidate",
        "canonical_write": False,
        "reason": "all validators passed and the candidate graph preview is build-complete; canonical authority was not granted",
    }


def test_validation_evidence_is_bound_to_exact_candidate_sha(tmp_path: Path) -> None:
    receipt = build(tmp_path)
    selected_sha = receipt["selected_candidate"]["sha256"]
    candidate_dir = paths(tmp_path)["out"] / "candidate"
    validations = [json.loads(path.read_text()) for path in sorted(candidate_dir.glob("validation.*.json"))]
    assert len(validations) == 3
    assert {item["artifact_sha256"] for item in validations} == {selected_sha}
    assert {item["status"] for item in validations} == {"passed"}


def test_graph_preview_closes_missing_required_without_canonical_mutation(tmp_path: Path) -> None:
    before = j("fixtures/asset_graph/expected.crystal_filterer.graph-snapshot.json")
    receipt = build(tmp_path)
    preview = json.loads((paths(tmp_path)["out"] / "candidate" / "graph-snapshot.preview.json").read_text())
    assert before["missing_required"]
    assert preview["missing_required"] == []
    assert preview["generation_task_ids"] == []
    target = next(item for item in preview["artifact_statuses"] if item["node_id"] == "artifact.audio.crystal_filterer.attack")
    assert target["effective_status"] == "passed"
    assert receipt["promotion"]["canonical_write"] is False
    assert not (ROOT / "fixtures/asset_graph/nodes/artifact.audio.crystal_filterer.attack.json").exists()


def test_one_attempt_budget_blocks_after_failed_candidate(tmp_path: Path) -> None:
    receipt = build(tmp_path, max_attempts=1)
    assert receipt["status"] == "blocked"
    assert len(receipt["attempts"]) == 1
    assert receipt["attempts"][0]["validation_status"] == "failed"
    assert receipt["selected_candidate"] is None
    assert receipt["graph_preview"] is None
    assert receipt["promotion"]["status"] == "blocked"


def test_context_reference_drift_fails_closed(tmp_path: Path) -> None:
    task = j("fixtures/assembler/alien-lineage.attack-audio.task.json")
    task["context_refs"]["composition_receipt_id"] = "composition:wrong"
    assembler = BoundedAssembler(root=ROOT, producer=ReferenceAudioProducer())
    with pytest.raises(AssemblerError, match="composition receipt context mismatch"):
        assembler.run(task=task, **paths(tmp_path))


def test_proposal_authority_cannot_request_canonical_write(tmp_path: Path) -> None:
    task = j("fixtures/assembler/alien-lineage.attack-audio.task.json")
    task["promotion_policy"]["canonical_write"] = True
    assembler = BoundedAssembler(root=ROOT, producer=ReferenceAudioProducer())
    with pytest.raises(AssemblerError, match="assembler-task.v0.1"):
        assembler.run(task=task, **paths(tmp_path))


def test_wrong_generation_target_fails_closed(tmp_path: Path) -> None:
    task = j("fixtures/assembler/alien-lineage.attack-audio.task.json")
    task["target"]["node_id"] = "artifact.audio.some_other_target"
    assembler = BoundedAssembler(root=ROOT, producer=ReferenceAudioProducer())
    with pytest.raises(AssemblerError, match="generation target mismatch"):
        assembler.run(task=task, **paths(tmp_path))


def test_same_inputs_produce_same_evidence_hash(tmp_path: Path) -> None:
    first = build(tmp_path / "a")
    second = build(tmp_path / "b")
    assert first["evidence_hash"] == second["evidence_hash"]
    assert first["selected_candidate"]["sha256"] == second["selected_candidate"]["sha256"]


def test_assembler_source_has_no_sedb_write_or_runtime_state_delta_authority() -> None:
    sources = "\n".join(path.read_text(encoding="utf-8") for path in sorted((ROOT / "src/awa_assembler").glob("*.py")))
    forbidden = ["EntityService", "StateDelta(", "runtime.state.set", "registry.add("]
    for token in forbidden:
        assert token not in sources
