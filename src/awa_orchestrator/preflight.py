from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from awa_contracts.validator import load_json
from awa_assembler.common import validate


class OrchestrationError(ValueError):
    pass


def resolve_ref(root: Path, value: str, *, expect_dir: bool = False) -> Path:
    raw = Path(value)
    if raw.is_absolute():
        raise OrchestrationError(f"orchestration references must be repository-relative: {value}")
    target = (root / raw).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise OrchestrationError(f"reference escapes repository root: {value}") from exc
    if expect_dir:
        if not target.is_dir():
            raise OrchestrationError(f"required directory does not exist: {value}")
    elif not target.is_file():
        raise OrchestrationError(f"required file does not exist: {value}")
    return target


def detect_claim_conflicts(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    claims: dict[tuple[str, ...], list[tuple[str, str, dict[str, str]]]] = defaultdict(list)
    for job in jobs:
        for claim in job["write_claims"]:
            identity = (
                ("shared", claim["key"])
                if claim["scope"] == "shared"
                else ("world", job["world_scope"], claim["key"])
            )
            claims[identity].append((job["orchestration_task_id"], job["world_scope"], claim))
    conflicts: list[dict[str, Any]] = []
    for identity, owners in sorted(claims.items()):
        unique_tasks = sorted({item[0] for item in owners})
        if len(unique_tasks) < 2:
            continue
        claim = owners[0][2]
        worlds = sorted({item[1] for item in owners})
        scope_text = "shared" if claim["scope"] == "shared" else f"world {worlds[0]}"
        conflicts.append({
            "claim": {"scope": claim["scope"], "key": claim["key"]},
            "task_ids": unique_tasks,
            "world_scopes": worlds,
            "reason": f"multiple orchestration tasks claim write authority for {scope_text} resource {claim['key']}",
        })
    return conflicts


def execution_batches(tasks: list[dict[str, Any]], max_parallel: int) -> list[list[str]]:
    by_id = {item["orchestration_task_id"]: item for item in tasks}
    if len(by_id) != len(tasks):
        raise OrchestrationError("duplicate orchestration task id")
    for item in tasks:
        task_id = item["orchestration_task_id"]
        for dep in item["depends_on"]:
            if dep == task_id:
                raise OrchestrationError(f"dependency cycle includes {task_id}")
            if dep not in by_id:
                raise OrchestrationError(f"unknown dependency {dep} for {task_id}")

    remaining = set(by_id)
    completed: set[str] = set()
    batches: list[list[str]] = []
    while remaining:
        ready = sorted(
            task_id for task_id in remaining
            if set(by_id[task_id]["depends_on"]).issubset(completed)
        )
        if not ready:
            raise OrchestrationError("dependency cycle prevents orchestration scheduling")
        for offset in range(0, len(ready), max_parallel):
            batch = ready[offset: offset + max_parallel]
            batches.append(batch)
            completed.update(batch)
            remaining.difference_update(batch)
    return batches


def prepare_jobs(root: Path, plan: dict[str, Any]) -> tuple[list[dict[str, Any]], list[list[str]]]:
    validate(root, "multi-world-orchestration-plan.v0.1", plan, "multi-world orchestration plan")
    policy = plan["execution_policy"]
    tasks = plan["tasks"]
    if len(tasks) > policy["max_tasks"]:
        raise OrchestrationError("task count exceeds orchestration max_tasks budget")

    jobs: list[dict[str, Any]] = []
    reserved_attempts = 0
    for item in tasks:
        task_path = resolve_ref(root, item["task_ref"])
        task = validate(root, "assembler-task.v0.1", load_json(task_path), f"child task {item['orchestration_task_id']}")
        semantic_path = resolve_ref(root, item["context"]["semantic_snapshot"])
        semantic = validate(root, "sedb-namespace-snapshot.v0.1", load_json(semantic_path), "child semantic snapshot")
        if semantic["namespace"] != item["world_scope"]:
            raise OrchestrationError(
                f"semantic namespace {semantic['namespace']} does not match world scope {item['world_scope']}"
            )
        required_target_claim = {"scope": "world", "key": task["target"]["node_id"]}
        if required_target_claim not in item["write_claims"]:
            raise OrchestrationError(
                f"task {item['orchestration_task_id']} must claim its world-scoped target {task['target']['node_id']}"
            )
        context = {
            "semantic_snapshot": semantic_path,
            "composition_receipt": resolve_ref(root, item["context"]["composition_receipt"]),
            "presentation_binding": resolve_ref(root, item["context"]["presentation_binding"]),
            "capability_contract": resolve_ref(root, item["context"]["capability_contract"]),
            "nodes": resolve_ref(root, item["context"]["nodes"], expect_dir=True),
            "edges": resolve_ref(root, item["context"]["edges"], expect_dir=True),
            "artifacts": resolve_ref(root, item["context"]["artifacts"], expect_dir=True),
            "validations": resolve_ref(root, item["context"]["validations"], expect_dir=True),
        }
        reserved_attempts += task["repair_policy"]["max_attempts"]
        jobs.append({**item, "task": task, "context_paths": context})

    if reserved_attempts > policy["max_total_attempts"]:
        raise OrchestrationError(
            f"declared child attempt budget {reserved_attempts} exceeds orchestration attempt budget {policy['max_total_attempts']}"
        )
    return jobs, execution_batches(tasks, policy["max_parallel"])
