from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from awa_assembler.common import validate
from awa_assembler.provider import CandidateProducer, HTTPProviderProducer, reference_producer_for


def producer_resolver_for_plan(*, root: str | Path, plan: dict[str, Any], bindings: dict[str, Any]) -> Callable[[dict[str, Any]], CandidateProducer]:
    root_path = Path(root).resolve()
    bindings = validate(root_path, "provider-bindings.v0.1", bindings, "provider bindings")
    plan_ids = {item["orchestration_task_id"] for item in plan["tasks"]}
    mapping: dict[str, dict[str, Any]] = {}
    for item in bindings["bindings"]:
        task_id = item["orchestration_task_id"]
        if task_id not in plan_ids:
            raise ValueError(f"provider binding references unknown orchestration task: {task_id}")
        if task_id in mapping:
            raise ValueError(f"duplicate provider binding for orchestration task: {task_id}")
        mapping[task_id] = item

    def resolve(job: dict[str, Any]) -> CandidateProducer:
        binding = mapping.get(job["orchestration_task_id"])
        if binding is None:
            return reference_producer_for(job["task"])
        return HTTPProviderProducer(
            root=root_path,
            endpoint=binding["endpoint"],
            provider_id=binding["provider_id"],
            model_id=binding["model_id"],
            timeout_seconds=float(binding["timeout_seconds"]),
        )

    return resolve
