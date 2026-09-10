from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from awa_asset_graph.graph import sha256_json

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_phase13_unique_explicit_rank_selects_without_canonical_write(tmp_path: Path) -> None:
    from awa_promotion import PromotionEvaluator
    conflict_set = load("fixtures/promotion/phase13.selection.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    receipt = PromotionEvaluator(root=ROOT).evaluate(conflict_set=conflict_set, policy=policy, out=tmp_path / "selection")
    assert receipt["status"] == "ready"
    relay = next(item for item in receipt["decisions"] if item["slot_id"].startswith("world:game.relay_station:"))
    assert relay["conflict"] is True
    assert relay["decision"] == "selected"
    assert relay["selected_candidate"]["candidate_id"] == "relay-glow-a"
    assert receipt["promotion_authority_required"] is True
    assert receipt["canonical_write"] is False


def test_valid_policy_tie_blocks_without_hash_or_order_tiebreak(tmp_path: Path) -> None:
    from awa_promotion import PromotionEvaluator, policy_evidence_hash
    conflict_set = load("fixtures/promotion/phase13.selection.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    tied = copy.deepcopy(conflict_set)
    tied["candidates"][1]["policy_evidence"]["facts"]["reviewed_priority"] = 20
    tied["candidates"][1]["policy_evidence"]["evidence_hash"] = policy_evidence_hash(tied["candidates"][1])
    receipt = PromotionEvaluator(root=ROOT).evaluate(conflict_set=tied, policy=policy, out=tmp_path / "tie")
    relay = next(item for item in receipt["decisions"] if item["slot_id"].startswith("world:game.relay_station:"))
    assert receipt["status"] == "blocked"
    assert relay["decision"] == "blocked_tie"
    assert relay["selected_candidate"] is None
    assert "last-writer-wins" in relay["reason"]


def test_candidate_input_order_cannot_change_readiness_identity(tmp_path: Path) -> None:
    from awa_promotion import PromotionEvaluator
    conflict_set = load("fixtures/promotion/phase13.selection.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    evaluator = PromotionEvaluator(root=ROOT)
    first = evaluator.evaluate(conflict_set=conflict_set, policy=policy, out=tmp_path / "a")
    reversed_set = copy.deepcopy(conflict_set)
    reversed_set["candidates"].reverse()
    second = evaluator.evaluate(conflict_set=reversed_set, policy=policy, out=tmp_path / "b")
    assert first == second


def test_world_scoped_same_key_across_worlds_is_not_conflict(tmp_path: Path) -> None:
    from awa_promotion import PromotionEvaluator
    conflict_set = load("fixtures/promotion/phase13.selection.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    receipt = PromotionEvaluator(root=ROOT).evaluate(conflict_set=conflict_set, policy=policy, out=tmp_path / "selection")
    same_key = [item for item in receipt["decisions"] if item["claim"]["key"] == "presentation.effect.primary"]
    assert len(same_key) == 2
    assert {item["slot_id"].split(":", 2)[1] for item in same_key} == {"game.alien_lineage", "game.relay_station"}


def test_shared_same_key_across_worlds_conflicts_and_tie_blocks(tmp_path: Path) -> None:
    from awa_promotion import PromotionEvaluator
    conflict_set = load("fixtures/promotion/phase13.shared-tie.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    receipt = PromotionEvaluator(root=ROOT).evaluate(conflict_set=conflict_set, policy=policy, out=tmp_path / "shared")
    assert receipt["status"] == "blocked"
    assert len(receipt["decisions"]) == 1
    decision = receipt["decisions"][0]
    assert decision["slot_id"] == "shared:presentation.shared.effect-registry"
    assert decision["conflict"] is True
    assert decision["decision"] == "blocked_tie"
    assert decision["selected_candidate"] is None


def test_invalid_candidate_policy_evidence_fails_closed(tmp_path: Path) -> None:
    from awa_promotion import PromotionError, PromotionEvaluator
    conflict_set = load("fixtures/promotion/phase13.selection.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    conflict_set["candidates"][0]["policy_evidence"]["evidence_hash"] = "0" * 64
    with pytest.raises(PromotionError, match="policy evidence hash"):
        PromotionEvaluator(root=ROOT).evaluate(conflict_set=conflict_set, policy=policy, out=tmp_path / "bad")


def test_hidden_or_lww_tiebreak_fields_are_rejected(tmp_path: Path) -> None:
    from awa_promotion import PromotionError, PromotionEvaluator
    conflict_set = load("fixtures/promotion/phase13.selection.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    policy["criteria"] = [{"field": "timestamp", "direction": "max"}]
    for candidate in conflict_set["candidates"]:
        candidate["policy_evidence"]["facts"]["timestamp"] = 1
        basis = {
            "candidate_id": candidate["candidate_id"],
            "candidate_sha256": candidate["candidate_sha256"],
            "facts": candidate["policy_evidence"]["facts"],
            "source": candidate["policy_evidence"]["source"],
        }
        candidate["policy_evidence"]["evidence_hash"] = sha256_json(basis)
    with pytest.raises(PromotionError, match="forbidden hidden/LWW"):
        PromotionEvaluator(root=ROOT).evaluate(conflict_set=conflict_set, policy=policy, out=tmp_path / "bad-policy")


def test_authority_grant_is_separate_and_binds_exact_readiness(tmp_path: Path) -> None:
    from awa_promotion import PromotionEvaluator
    conflict_set = load("fixtures/promotion/phase13.selection.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    evaluator = PromotionEvaluator(root=ROOT)
    readiness = evaluator.evaluate(conflict_set=conflict_set, policy=policy, out=tmp_path / "selection")
    grant = load("fixtures/promotion/phase13.relay-glow-a.authority-grant.json")
    receipt = evaluator.authorize(readiness=readiness, grant=grant, out=tmp_path / "authority")
    assert receipt["status"] == "promotion_authorized"
    assert receipt["candidate_id"] == "relay-glow-a"
    assert receipt["readiness_evidence_hash"] == readiness["evidence_hash"]
    assert receipt["canonical_write"] is False


def test_mismatched_authority_grant_fails_closed(tmp_path: Path) -> None:
    from awa_promotion import PromotionError, PromotionEvaluator
    conflict_set = load("fixtures/promotion/phase13.selection.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    evaluator = PromotionEvaluator(root=ROOT)
    readiness = evaluator.evaluate(conflict_set=conflict_set, policy=policy, out=tmp_path / "selection")
    grant = load("fixtures/promotion/phase13.relay-glow-a.authority-grant.json")
    grant["candidate_sha256"] = "f" * 64
    with pytest.raises(PromotionError, match="candidate sha"):
        evaluator.authorize(readiness=readiness, grant=grant, out=tmp_path / "authority")


def test_blocked_readiness_cannot_be_authorized(tmp_path: Path) -> None:
    from awa_promotion import PromotionError, PromotionEvaluator
    conflict_set = load("fixtures/promotion/phase13.shared-tie.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    evaluator = PromotionEvaluator(root=ROOT)
    readiness = evaluator.evaluate(conflict_set=conflict_set, policy=policy, out=tmp_path / "shared")
    grant = load("fixtures/promotion/phase13.relay-glow-a.authority-grant.json")
    with pytest.raises(PromotionError, match="readiness is blocked"):
        evaluator.authorize(readiness=readiness, grant=grant, out=tmp_path / "authority")


def test_promotion_layer_has_no_canonical_or_runtime_write_authority() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in sorted((ROOT / "src/awa_promotion").glob("*.py")))
    for token in ["StateDelta(", "EntityDelta(", "registry.add(", "canonical_write=True", "canonical_write = True"]:
        assert token not in source


def test_phase13_readiness_and_authority_match_goldens(tmp_path: Path) -> None:
    from awa_promotion import PromotionEvaluator
    conflict_set = load("fixtures/promotion/phase13.selection.conflict-set.json")
    policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
    evaluator = PromotionEvaluator(root=ROOT)
    readiness = evaluator.evaluate(conflict_set=conflict_set, policy=policy, out=tmp_path / "selection")
    assert readiness == load("fixtures/promotion/expected.phase13.selection.readiness.json")
    grant = load("fixtures/promotion/phase13.relay-glow-a.authority-grant.json")
    authority = evaluator.authorize(readiness=readiness, grant=grant, out=tmp_path / "authority")
    assert authority == load("fixtures/promotion/expected.phase13.relay-glow-a.authority.json")
