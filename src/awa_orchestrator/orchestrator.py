from __future__ import annotations

import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from awa_asset_graph.graph import sha256_json
from awa_contracts.validator import load_json
from awa_assembler.common import validate, write_json
from awa_assembler.loop import BoundedAssembler
from awa_assembler.provider import CandidateProducer, reference_producer_for

from .preflight import OrchestrationError, detect_claim_conflicts, prepare_jobs, resolve_ref


def _safe_output(root: Path, out: str | Path) -> Path:
    target = Path(out).resolve()
    repo = root.resolve()
    if target == repo:
        raise OrchestrationError("orchestration output cannot be repository root")
    try:
        rel = target.relative_to(repo)
    except ValueError:
        return target
    if not rel.parts or rel.parts[0] != "build":
        raise OrchestrationError("repository-local orchestration output must be under build/")
    return target


def _task_result(job: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    selected = receipt["selected_candidate"]
    graph = receipt["graph_preview"]
    return {
        "orchestration_task_id": job["orchestration_task_id"],
        "world_scope": job["world_scope"],
        "task_id": receipt["task_id"],
        "target_node_id": job["task"]["target"]["node_id"],
        "status": receipt["status"],
        "attempts": len(receipt["attempts"]),
        "run_id": receipt["run_id"],
        "evidence_hash": receipt["evidence_hash"],
        "selected_candidate_sha256": selected["sha256"] if selected else None,
        "graph_snapshot_id": graph["snapshot_id"] if graph else None,
        "canonical_write": receipt["promotion"]["canonical_write"],
    }


def _world_evidence(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(result["world_scope"], []).append(result)
    evidence: list[dict[str, Any]] = []
    for world_scope in sorted(grouped):
        items = sorted(grouped[world_scope], key=lambda item: item["orchestration_task_id"])
        basis = {
            "world_scope": world_scope,
            "orchestration_task_ids": [item["orchestration_task_id"] for item in items],
            "child_evidence_hashes": [item["evidence_hash"] for item in items],
        }
        evidence.append({**basis, "evidence_hash": sha256_json(basis)})
    return evidence


class MultiWorldOrchestrator:
    def __init__(self, *, root: str | Path,
                 producer_resolver: Callable[[dict[str, Any]], CandidateProducer] | None = None) -> None:
        self.root = Path(root).resolve()
        self.producer_resolver = producer_resolver or (lambda job: reference_producer_for(job["task"]))

    def _receipt(self, *, plan: dict[str, Any], project_state: dict[str, Any],
                 batches: list[list[str]], results: list[dict[str, Any]],
                 conflicts: list[dict[str, Any]]) -> dict[str, Any]:
        policy = plan["execution_policy"]
        status = "blocked" if conflicts or any(item["status"] != "validated_candidate" for item in results) else "completed"
        promotion = {
            "status": "blocked" if status == "blocked" else "coordination_complete",
            "canonical_write": False,
            "reason": (
                "orchestration was blocked before canonical promotion; child authority remains isolated"
                if status == "blocked"
                else "all scheduled child tasks produced independently validated candidates; orchestration grants no canonical write authority"
            ),
        }
        budget = {
            "max_parallel": policy["max_parallel"],
            "max_tasks": policy["max_tasks"],
            "max_total_attempts": policy["max_total_attempts"],
            "used_tasks": len(results),
            "used_attempts": sum(item["attempts"] for item in results),
        }
        basis = {
            "plan_id": plan["plan_id"],
            "status": status,
            "authority": "coordination",
            "source_hashes": {
                "plan": sha256_json(plan),
                "project_state": sha256_json(project_state),
            },
            "execution_batches": batches,
            "task_results": results,
            "world_evidence": _world_evidence(results),
            "conflicts": conflicts,
            "budget": budget,
            "promotion": promotion,
        }
        body = {
            "contract": "multi-world-orchestration-receipt.v0.1",
            "orchestration_id": f"orchestration-run:{sha256_json(basis)[:16]}",
            **basis,
        }
        receipt = {**body, "evidence_hash": sha256_json(body)}
        return validate(self.root, "multi-world-orchestration-receipt.v0.1", receipt, "multi-world orchestration receipt")

    def run(self, *, plan: dict[str, Any], out: str | Path) -> dict[str, Any]:
        jobs, batches = prepare_jobs(self.root, plan)
        project_state_path = resolve_ref(self.root, plan["project_state_ref"])
        project_state = load_json(project_state_path)
        if not isinstance(project_state, dict):
            raise OrchestrationError("project state must be an object")
        conflicts = detect_claim_conflicts(jobs)
        output = _safe_output(self.root, out)
        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True, exist_ok=True)
        write_json(output / "orchestration-plan.observed.json", plan)

        if conflicts:
            receipt = self._receipt(
                plan=plan, project_state=project_state, batches=[],
                results=[], conflicts=conflicts,
            )
            write_json(output / "multi-world-orchestration-receipt.json", receipt)
            return receipt

        by_id = {job["orchestration_task_id"]: job for job in jobs}
        results_by_id: dict[str, dict[str, Any]] = {}
        executed_batches: list[list[str]] = []
        stop = False
        for batch in batches:
            if stop:
                break
            executed_batches.append(list(batch))
            workers = min(plan["execution_policy"]["max_parallel"], len(batch))
            futures = {}
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for task_id in batch:
                    job = by_id[task_id]
                    child_out = output / "tasks" / task_id
                    assembler = BoundedAssembler(root=self.root, producer=self.producer_resolver(job))
                    future = pool.submit(
                        assembler.run,
                        task=job["task"],
                        project_state=project_state_path,
                        semantic_snapshot=job["context_paths"]["semantic_snapshot"],
                        composition_receipt=job["context_paths"]["composition_receipt"],
                        presentation_binding=job["context_paths"]["presentation_binding"],
                        capability_contract=job["context_paths"]["capability_contract"],
                        nodes=job["context_paths"]["nodes"],
                        edges=job["context_paths"]["edges"],
                        artifacts=job["context_paths"]["artifacts"],
                        validations=job["context_paths"]["validations"],
                        out=child_out,
                    )
                    futures[future] = task_id
                for future in as_completed(futures):
                    task_id = futures[future]
                    child_receipt = future.result()
                    results_by_id[task_id] = _task_result(by_id[task_id], child_receipt)
            if plan["execution_policy"]["fail_fast"] and any(
                results_by_id[item]["status"] != "validated_candidate" for item in batch
            ):
                stop = True

        ordered_ids = [task_id for batch in batches for task_id in batch if task_id in results_by_id]
        results = [results_by_id[task_id] for task_id in ordered_ids]
        receipt = self._receipt(
            plan=plan, project_state=project_state, batches=executed_batches,
            results=results, conflicts=[],
        )
        write_json(output / "multi-world-orchestration-receipt.json", receipt)
        return receipt
