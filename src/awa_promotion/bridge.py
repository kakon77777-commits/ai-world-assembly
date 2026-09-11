from __future__ import annotations

from pathlib import Path
from typing import Any

from awa_asset_graph.graph import sha256_json
from awa_contracts.validator import load_json

from .promotion import policy_evidence_hash, validation_evidence_hash


def candidate_from_orchestration(*, root: str | Path, orchestration_out: str | Path,
                                 orchestration_receipt: dict[str, Any], orchestration_task: dict[str, Any],
                                 policy_facts: dict[str, int], policy_source: str) -> dict[str, Any]:
    """Project one validated child candidate into Phase 13 comparison input.

    Provider identity is intentionally not copied. Selection is governed only by reviewed policy
    evidence plus exact candidate/validation evidence already produced by the assembler.
    """
    root_path = Path(root).resolve()
    output = Path(orchestration_out).resolve()
    task_key = orchestration_task["orchestration_task_id"]
    result = next((item for item in orchestration_receipt["task_results"] if item["orchestration_task_id"] == task_key), None)
    if result is None or result["status"] != "validated_candidate":
        raise ValueError(f"orchestration task is not a validated candidate: {task_key}")
    child_dir = output / "tasks" / task_key
    child_receipt = load_json(child_dir / "assembler-run-receipt.json")
    selected = child_receipt.get("selected_candidate")
    if child_receipt.get("status") != "validated_candidate" or not selected:
        raise ValueError(f"child assembler receipt is not a validated candidate: {task_key}")
    task = load_json(root_path / orchestration_task["task_ref"])
    candidate_path = child_dir / "candidate" / task["target"]["filename"]
    try:
        artifact_ref = candidate_path.resolve().relative_to(root_path).as_posix()
    except ValueError as exc:
        raise ValueError("promotion candidate artifact must remain inside repository root") from exc
    artifact = load_json(candidate_path)
    if not isinstance(artifact, dict) or not isinstance(artifact.get("contract"), str):
        raise ValueError("provider candidate must be a contract-bearing JSON object for governed promotion")
    validation_docs = sorted((child_dir / "candidate").glob("validation.*.json"))
    validators = sorted({load_json(path)["validator"] for path in validation_docs})
    if not validators:
        raise ValueError("validated candidate has no validation evidence")
    claim = next((item for item in orchestration_task["write_claims"] if item["key"] == task["target"]["node_id"]), None)
    if claim is None:
        raise ValueError("orchestration task is missing its governed target write claim")
    candidate = {
        "candidate_id": f"phase14:{task_key}:{child_receipt['run_id'].split(':')[-1]}",
        "world_scope": orchestration_task["world_scope"],
        "task_id": child_receipt["task_id"],
        "run_id": child_receipt["run_id"],
        "status": "validated_candidate",
        "artifact_ref": artifact_ref,
        "artifact_contract": artifact["contract"],
        "candidate_sha256": selected["sha256"],
        "validation_evidence": {
            "status": "validated_candidate",
            "validators": validators,
            "evidence_hash": "0" * 64,
        },
        "canonical_write": False,
        "write_claim": claim,
        "policy_evidence": {
            "facts": dict(policy_facts),
            "source": policy_source,
            "evidence_hash": "0" * 64,
        },
    }
    candidate["validation_evidence"]["evidence_hash"] = validation_evidence_hash(candidate)
    candidate["policy_evidence"]["evidence_hash"] = policy_evidence_hash(candidate)
    return candidate
