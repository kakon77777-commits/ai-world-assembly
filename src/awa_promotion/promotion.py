from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from awa_asset_graph.graph import sha256_json
from awa_assembler.common import validate, write_json, sha_bytes
from awa_contracts.validator import load_json


class PromotionError(ValueError):
    pass


_FORBIDDEN_SELECTION_FIELDS = {
    "input_order", "candidate_order", "candidate_sha256", "sha256", "hash",
    "timestamp", "created_at", "updated_at", "run_id", "sequence",
}


def _safe_ref(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PromotionError(f"candidate artifact_ref escapes repository: {ref}") from exc
    if not path.is_file():
        raise PromotionError(f"candidate artifact does not exist: {ref}")
    return path


def validation_evidence_hash(candidate: dict[str, Any]) -> str:
    evidence = candidate["validation_evidence"]
    basis = {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate["candidate_sha256"],
        "artifact_contract": candidate["artifact_contract"],
        "status": evidence["status"],
        "validators": evidence["validators"],
    }
    return sha256_json(basis)


def policy_evidence_hash(candidate: dict[str, Any]) -> str:
    evidence = candidate["policy_evidence"]
    basis = {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate["candidate_sha256"],
        "facts": evidence["facts"],
        "source": evidence["source"],
    }
    return sha256_json(basis)


def normalized_conflict_set_hash(conflict_set: dict[str, Any]) -> str:
    normalized = copy.deepcopy(conflict_set)
    normalized["candidates"] = sorted(normalized["candidates"], key=lambda item: item["candidate_id"])
    return sha256_json(normalized)


def _verify_receipt_hash(document: dict[str, Any], label: str) -> None:
    body = {key: value for key, value in document.items() if key != "evidence_hash"}
    expected = sha256_json(body)
    if document.get("evidence_hash") != expected:
        raise PromotionError(f"{label} evidence hash mismatch")


def _slot_id(candidate: dict[str, Any]) -> str:
    claim = candidate["write_claim"]
    if claim["scope"] == "shared":
        return f"shared:{claim['key']}"
    return f"world:{candidate['world_scope']}:{claim['key']}"


def _candidate_ref(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "world_scope": candidate["world_scope"],
        "candidate_sha256": candidate["candidate_sha256"],
    }


class PromotionEvaluator:
    def __init__(self, *, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def _verify_policy(self, policy: dict[str, Any]) -> dict[str, Any]:
        policy = validate(self.root, "conflict-evaluation-policy.v0.1", policy, "conflict evaluation policy")
        fields = [item["field"] for item in policy["criteria"]]
        if len(fields) != len(set(fields)):
            raise PromotionError("conflict policy criteria fields must be unique")
        forbidden = [field for field in fields if field.lower() in _FORBIDDEN_SELECTION_FIELDS]
        if forbidden:
            raise PromotionError(f"forbidden hidden/LWW selection field: {forbidden[0]}")
        return policy

    def _verify_candidate(self, candidate: dict[str, Any]) -> None:
        artifact_path = _safe_ref(self.root, candidate["artifact_ref"])
        actual_sha = sha_bytes(artifact_path.read_bytes())
        if actual_sha != candidate["candidate_sha256"]:
            raise PromotionError(f"candidate sha mismatch for {candidate['candidate_id']}")
        artifact = load_json(artifact_path)
        if not isinstance(artifact, dict):
            raise PromotionError(f"candidate artifact must be an object: {candidate['candidate_id']}")
        validate(self.root, candidate["artifact_contract"], artifact, f"candidate artifact {candidate['candidate_id']}")
        if candidate["validation_evidence"]["evidence_hash"] != validation_evidence_hash(candidate):
            raise PromotionError(f"validation evidence hash mismatch for {candidate['candidate_id']}")
        if candidate["policy_evidence"]["evidence_hash"] != policy_evidence_hash(candidate):
            raise PromotionError(f"policy evidence hash mismatch for {candidate['candidate_id']}")

    def _decision(self, group: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
        ordered = sorted(group, key=lambda item: item["candidate_id"])
        claim = ordered[0]["write_claim"]
        slot_id = _slot_id(ordered[0])
        ranking: list[dict[str, Any]] = []
        scored: list[tuple[tuple[int, ...], dict[str, Any]]] = []
        for candidate in ordered:
            facts = candidate["policy_evidence"]["facts"]
            values: list[int] = []
            comparable: list[int] = []
            for criterion in policy["criteria"]:
                field = criterion["field"]
                if field not in facts:
                    raise PromotionError(f"candidate {candidate['candidate_id']} missing policy fact: {field}")
                value = facts[field]
                values.append(value)
                comparable.append(value if criterion["direction"] == "max" else -value)
            ranking.append({"candidate_id": candidate["candidate_id"], "values": values})
            scored.append((tuple(comparable), candidate))

        if len(ordered) == 1:
            selected = ordered[0]
            decision = "uncontested"
            reason = "one independently validated candidate claims this governed slot"
        else:
            best_score = max(score for score, _ in scored)
            winners = [candidate for score, candidate in scored if score == best_score]
            if len(winners) != 1:
                selected = None
                decision = "blocked_tie"
                reason = "explicit policy criteria produced a tie; policy forbids hidden, hash, input-order, or last-writer-wins tiebreaking"
            else:
                selected = winners[0]
                decision = "selected"
                reason = "explicit reviewed numeric policy uniquely selected one validated candidate"

        return {
            "slot_id": slot_id,
            "claim": claim,
            "world_scopes": sorted({item["world_scope"] for item in ordered}),
            "candidate_ids": [item["candidate_id"] for item in ordered],
            "conflict": len(ordered) > 1,
            "decision": decision,
            "selected_candidate": _candidate_ref(selected) if selected is not None else None,
            "ranking": ranking,
            "reason": reason,
        }

    def evaluate(self, *, conflict_set: dict[str, Any], policy: dict[str, Any], out: str | Path | None = None) -> dict[str, Any]:
        conflict_set = validate(self.root, "candidate-conflict-set.v0.1", conflict_set, "candidate conflict set")
        policy = self._verify_policy(policy)
        candidates = conflict_set["candidates"]
        ids = [item["candidate_id"] for item in candidates]
        if len(ids) != len(set(ids)):
            raise PromotionError("candidate ids must be unique")
        for candidate in candidates:
            self._verify_candidate(candidate)

        grouped: dict[str, list[dict[str, Any]]] = {}
        for candidate in candidates:
            grouped.setdefault(_slot_id(candidate), []).append(candidate)
        decisions = [self._decision(grouped[slot], policy) for slot in sorted(grouped)]
        blocked = any(item["decision"] == "blocked_tie" for item in decisions)
        ready_candidates = [item["selected_candidate"] for item in decisions if item["selected_candidate"] is not None]
        basis = {
            "conflict_set_id": conflict_set["conflict_set_id"],
            "policy_id": policy["policy_id"],
            "status": "blocked" if blocked else "ready",
            "authority": "readiness_evaluation",
            "source_hashes": {
                "conflict_set": normalized_conflict_set_hash(conflict_set),
                "policy": sha256_json(policy),
            },
            "decisions": decisions,
            "ready_candidates": ready_candidates,
            "promotion_authority_required": True,
            "canonical_write": False,
        }
        body = {
            "contract": "promotion-readiness-receipt.v0.1",
            "readiness_id": f"promotion-readiness:{sha256_json(basis)[:16]}",
            **basis,
        }
        receipt = {**body, "evidence_hash": sha256_json(body)}
        receipt = validate(self.root, "promotion-readiness-receipt.v0.1", receipt, "promotion readiness receipt")
        if out is not None:
            output = Path(out)
            output.mkdir(parents=True, exist_ok=True)
            write_json(output / "promotion-readiness-receipt.json", receipt)
        return receipt

    def authorize(self, *, readiness: dict[str, Any], grant: dict[str, Any], out: str | Path | None = None) -> dict[str, Any]:
        readiness = validate(self.root, "promotion-readiness-receipt.v0.1", readiness, "promotion readiness receipt")
        if readiness["status"] != "ready":
            raise PromotionError("readiness is blocked")
        _verify_receipt_hash(readiness, "readiness")
        grant = validate(self.root, "promotion-authority-grant.v0.1", grant, "promotion authority grant")
        if grant["readiness_evidence_hash"] != readiness["evidence_hash"]:
            raise PromotionError("grant readiness evidence hash mismatch")
        if grant["policy_id"] != readiness["policy_id"]:
            raise PromotionError("grant policy id mismatch")
        if grant["policy_sha256"] != readiness["source_hashes"]["policy"]:
            raise PromotionError("grant policy sha mismatch")
        decision = next((item for item in readiness["decisions"] if item["slot_id"] == grant["slot_id"]), None)
        if decision is None:
            raise PromotionError("grant slot is not present in readiness")
        selected = decision["selected_candidate"]
        if selected is None:
            raise PromotionError("grant slot has no selected candidate")
        if grant["candidate_id"] != selected["candidate_id"]:
            raise PromotionError("grant candidate id mismatch")
        if grant["candidate_sha256"] != selected["candidate_sha256"]:
            raise PromotionError("grant candidate sha mismatch")

        basis = {
            "status": "promotion_authorized",
            "authority": "promotion_verification",
            "readiness_evidence_hash": readiness["evidence_hash"],
            "grant_hash": sha256_json(grant),
            "policy_id": readiness["policy_id"],
            "policy_sha256": readiness["source_hashes"]["policy"],
            "slot_id": grant["slot_id"],
            "candidate_id": grant["candidate_id"],
            "candidate_sha256": grant["candidate_sha256"],
            "canonical_write": False,
            "reason": "exact promotion grant verified against an explicit ready selection; Phase 13 performs no canonical write",
        }
        body = {
            "contract": "promotion-authority-receipt.v0.1",
            "authorization_id": f"promotion-authorization:{sha256_json(basis)[:16]}",
            **basis,
        }
        receipt = {**body, "evidence_hash": sha256_json(body)}
        receipt = validate(self.root, "promotion-authority-receipt.v0.1", receipt, "promotion authority receipt")
        if out is not None:
            output = Path(out)
            output.mkdir(parents=True, exist_ok=True)
            write_json(output / "promotion-authority-receipt.json", receipt)
        return receipt
