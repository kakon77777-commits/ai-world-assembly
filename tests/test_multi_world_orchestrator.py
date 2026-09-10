from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_phase12_plan_runs_two_worlds_in_deterministic_batches(tmp_path: Path) -> None:
    from awa_orchestrator import MultiWorldOrchestrator

    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    receipt = MultiWorldOrchestrator(root=ROOT).run(plan=plan, out=tmp_path / "run")

    assert receipt["status"] == "completed"
    assert receipt["execution_batches"] == [
        ["alien-audio", "relay-activation-recipe"],
        ["alien-mutation-recipe"],
    ]
    assert {item["world_scope"] for item in receipt["task_results"]} == {
        "game.alien_lineage",
        "game.relay_station",
    }
    assert [item["status"] for item in receipt["task_results"]] == [
        "validated_candidate",
        "validated_candidate",
        "validated_candidate",
    ]
    assert receipt["budget"]["used_tasks"] == 3
    assert receipt["budget"]["used_attempts"] == 6
    assert receipt["promotion"]["canonical_write"] is False


def test_parallel_completion_order_does_not_change_receipt_identity(tmp_path: Path) -> None:
    from awa_orchestrator import MultiWorldOrchestrator

    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    first = MultiWorldOrchestrator(root=ROOT).run(plan=plan, out=tmp_path / "a")
    second = MultiWorldOrchestrator(root=ROOT).run(plan=plan, out=tmp_path / "b")
    assert first["evidence_hash"] == second["evidence_hash"]
    assert first["orchestration_id"] == second["orchestration_id"]


def test_shared_cross_world_write_claim_conflict_blocks_before_execution(tmp_path: Path) -> None:
    from awa_orchestrator import MultiWorldOrchestrator

    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    conflict = copy.deepcopy(plan)
    shared = {"scope": "shared", "key": "presentation.shared.effect-registry"}
    conflict["tasks"][0]["write_claims"].append(shared)
    conflict["tasks"][1]["write_claims"].append(shared)
    receipt = MultiWorldOrchestrator(root=ROOT).run(plan=conflict, out=tmp_path / "blocked")
    assert receipt["status"] == "blocked"
    assert receipt["task_results"] == []
    assert receipt["execution_batches"] == []
    assert len(receipt["conflicts"]) == 1
    assert receipt["conflicts"][0]["claim"] == shared
    assert receipt["promotion"]["canonical_write"] is False
    assert not (tmp_path / "blocked" / "tasks").exists()


def test_same_world_target_claim_conflict_blocks(tmp_path: Path) -> None:
    from awa_orchestrator import MultiWorldOrchestrator

    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    duplicate = copy.deepcopy(plan["tasks"][0])
    duplicate["orchestration_task_id"] = "alien-audio-duplicate"
    duplicate["depends_on"] = []
    plan["tasks"].append(duplicate)
    plan["execution_policy"]["max_tasks"] = 4
    plan["execution_policy"]["max_total_attempts"] = 8
    receipt = MultiWorldOrchestrator(root=ROOT).run(plan=plan, out=tmp_path / "blocked")
    assert receipt["status"] == "blocked"
    assert any(item["claim"]["scope"] == "world" for item in receipt["conflicts"])


def test_world_scoped_same_claim_key_is_not_cross_world_conflict(tmp_path: Path) -> None:
    from awa_orchestrator.preflight import detect_claim_conflicts

    jobs = [
        {"orchestration_task_id": "a", "world_scope": "game.a", "write_claims": [{"scope": "world", "key": "artifact.same"}]},
        {"orchestration_task_id": "b", "world_scope": "game.b", "write_claims": [{"scope": "world", "key": "artifact.same"}]},
    ]
    assert detect_claim_conflicts(jobs) == []


def test_dependency_cycle_fails_closed(tmp_path: Path) -> None:
    from awa_orchestrator import MultiWorldOrchestrator, OrchestrationError

    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    plan["tasks"][0]["depends_on"] = ["alien-mutation-recipe"]
    with pytest.raises(OrchestrationError, match="dependency cycle"):
        MultiWorldOrchestrator(root=ROOT).run(plan=plan, out=tmp_path / "run")


def test_budget_cannot_underreserve_declared_child_attempts(tmp_path: Path) -> None:
    from awa_orchestrator import MultiWorldOrchestrator, OrchestrationError

    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    plan["execution_policy"]["max_total_attempts"] = 5
    with pytest.raises(OrchestrationError, match="attempt budget"):
        MultiWorldOrchestrator(root=ROOT).run(plan=plan, out=tmp_path / "run")


def test_task_world_scope_must_match_semantic_snapshot(tmp_path: Path) -> None:
    from awa_orchestrator import MultiWorldOrchestrator, OrchestrationError

    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    plan["tasks"][1]["world_scope"] = "game.alien_lineage"
    with pytest.raises(OrchestrationError, match="semantic namespace"):
        MultiWorldOrchestrator(root=ROOT).run(plan=plan, out=tmp_path / "run")


def test_orchestrator_has_no_canonical_or_runtime_write_authority() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "src/awa_orchestrator").glob("*.py"))
    )
    for token in ["EntityService", "StateDelta(", "registry.add(", "canonical_write=True"]:
        assert token not in source


def test_phase12_orchestration_receipt_matches_golden(tmp_path: Path) -> None:
    from awa_orchestrator import MultiWorldOrchestrator

    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    receipt = MultiWorldOrchestrator(root=ROOT).run(plan=plan, out=tmp_path / "run")
    expected = load("fixtures/orchestration/expected.phase12.multi-world.receipt.json")
    assert receipt == expected
