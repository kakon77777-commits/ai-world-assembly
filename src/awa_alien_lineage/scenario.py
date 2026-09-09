from __future__ import annotations

from typing import Any

from .runtime import install_alien_lineage_runtime


class AlienLineageScenarioError(ValueError):
    pass


def _resolve_ref(value: str | None, actor_id: str) -> str | None:
    return actor_id if value == "$actor" else value


def _scenario(package: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    source = package.get("scenarios", {})
    entries = source.get("scenarios", []) if isinstance(source, dict) else []
    for entry in entries:
        if isinstance(entry, dict) and entry.get("scenario_id") == scenario_id:
            return entry
    raise AlienLineageScenarioError(f"ScenarioIR not found: {scenario_id}")


def run_alien_lineage_scenario(
    package: dict[str, Any], scenario_id: str, *, actor_id: str | None = None,
    domain_assertions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run existing CompilableWorld ScenarioIR semantics with the external lineage module installed.

    This is intentionally a thin compatibility runner pinned by CI to the current CompilableWorld
    ScenarioIR contract. It does not modify the Kernel or compiled package.
    """
    from compilableworld.kernel import WorldRuntime
    from compilableworld.models import ActionIR

    scenario = _scenario(package, scenario_id)
    runtime = WorldRuntime(package)
    install_alien_lineage_runtime(runtime)
    chosen_actor = actor_id or scenario.get("actor_id") or package.get("world", {}).get("default_player_entity")
    if not isinstance(chosen_actor, str) or not runtime.registry.contains(chosen_actor):
        raise AlienLineageScenarioError(f"Scenario actor does not exist: {chosen_actor}")

    for assertion in scenario.get("given", []):
        owner = _resolve_ref(assertion["owner"], chosen_actor)
        runtime.state.seed(owner, assertion["namespace"], assertion["key"], assertion["equals"])

    start_event_count = len(runtime.event_log.events)
    action_results: list[dict[str, Any]] = []
    expected_status = scenario.get("expect", {}).get("status", "completed")
    for index, raw in enumerate(scenario.get("when", [])):
        action_actor = _resolve_ref(raw.get("actor", "$actor"), chosen_actor)
        if not action_actor:
            raise AlienLineageScenarioError(f"Scenario action[{index}] missing actor")
        action = ActionIR(
            actor_id=action_actor,
            verb=raw["verb"],
            target_id=raw.get("target_id"),
            args=dict(raw.get("args", {})),
            authority="scenario",
        )
        receipt = runtime.submit(action, delay=int(raw.get("delay", 0)))
        receipts = [receipt]
        if receipt.status.value == "scheduled":
            receipts = runtime.advance(int(raw.get("delay", 0)))
        final = receipts[-1] if receipts else receipt
        action_results.append({"index": index, "verb": action.verb, "status": final.status.value, "message": final.message, "event_ids": list(final.event_ids)})

    observed = runtime.event_log.events[start_event_count:]
    event_types = [event.event_type for event in observed]
    assertions: list[dict[str, Any]] = []
    for expected in scenario.get("expect", {}).get("state", []):
        owner = _resolve_ref(expected["owner"], chosen_actor)
        actual = runtime.state.get(owner, expected["namespace"], expected["key"])
        assertions.append({"kind": "state", "owner": owner, "namespace": expected["namespace"], "key": expected["key"], "expected": expected["equals"], "actual": actual, "passed": actual == expected["equals"]})
    for event_type in scenario.get("expect", {}).get("events", []):
        assertions.append({"kind": "event", "expected": event_type, "actual": event_type if event_type in event_types else None, "passed": event_type in event_types})
    if domain_assertions is not None:
        if domain_assertions.get("contract") != "alien-lineage-runtime-assertions.v0.1":
            raise AlienLineageScenarioError("unsupported Alien Lineage assertion contract")
        if domain_assertions.get("scenario_id") != scenario_id:
            raise AlienLineageScenarioError("domain assertion scenario_id does not match")
        raw_state = domain_assertions.get("state")
        if not isinstance(raw_state, list):
            raise AlienLineageScenarioError("domain assertion state must be a list")
        for index, expected in enumerate(raw_state):
            if not isinstance(expected, dict) or set(expected) != {"owner", "namespace", "key", "equals"}:
                raise AlienLineageScenarioError(f"domain assertion state[{index}] is invalid")
            owner = _resolve_ref(expected["owner"], chosen_actor)
            actual = runtime.state.get(owner, expected["namespace"], expected["key"])
            assertions.append({"kind": "domain_state", "owner": owner, "namespace": expected["namespace"], "key": expected["key"], "expected": expected["equals"], "actual": actual, "passed": actual == expected["equals"]})
    statuses = [item["status"] for item in action_results]
    assertions.append({"kind": "action_status", "expected": expected_status, "actual": statuses, "passed": all(status == expected_status for status in statuses)})
    return {
        "scenario_id": scenario_id,
        "title": scenario.get("title", ""),
        "actor_id": chosen_actor,
        "passed": all(item["passed"] for item in assertions),
        "action_results": action_results,
        "observed_event_types": event_types,
        "assertions": assertions,
        "diagnostics": runtime.diagnostics(),
    }
