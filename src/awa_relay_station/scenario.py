from __future__ import annotations

from typing import Any

from .runtime import install_relay_station_runtime


class RelayStationScenarioError(ValueError):
    pass


def _scenario(package: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    source = package.get("scenarios", {})
    entries = source.get("scenarios", []) if isinstance(source, dict) else []
    for entry in entries:
        if isinstance(entry, dict) and entry.get("scenario_id") == scenario_id:
            return entry
    raise RelayStationScenarioError(f"ScenarioIR not found: {scenario_id}")


def _ref(value: str | None, actor: str) -> str | None:
    return actor if value == "$actor" else value


def run_relay_station_scenario(package: dict[str, Any], scenario_id: str, *, actor_id: str | None = None, domain_assertions: dict[str, Any] | None = None) -> dict[str, Any]:
    from compilableworld.entity_transaction import EntityTransactionRuntime
    from compilableworld.models import ActionIR
    scenario = _scenario(package, scenario_id)
    runtime = EntityTransactionRuntime(package)
    install_relay_station_runtime(runtime)
    actor = actor_id or scenario.get("actor_id") or package.get("world", {}).get("default_player_entity")
    if not isinstance(actor, str) or not runtime.registry.contains(actor):
        raise RelayStationScenarioError(f"Scenario actor does not exist: {actor}")
    for item in scenario.get("given", []):
        runtime.state.seed(_ref(item["owner"], actor), item["namespace"], item["key"], item["equals"])
    start = len(runtime.event_log.events); actions=[]
    for i, raw in enumerate(scenario.get("when", [])):
        receipt = runtime.submit(ActionIR(_ref(raw.get("actor", "$actor"), actor), raw["verb"], target_id=raw.get("target_id"), args=dict(raw.get("args", {})), authority="scenario"), delay=int(raw.get("delay", 0)))
        final = receipt
        if receipt.status.value == "scheduled":
            advanced = runtime.advance(int(raw.get("delay", 0))); final = advanced[-1] if advanced else receipt
        actions.append({"index":i,"verb":raw["verb"],"status":final.status.value,"message":final.message,"event_ids":list(final.event_ids),"changed_entities":list(getattr(final,"changed_entities",[]))})
    observed = runtime.event_log.events[start:]; types=[e.event_type for e in observed]; assertions=[]
    for expected in scenario.get("expect", {}).get("state", []):
        owner=_ref(expected["owner"],actor); actual=runtime.state.get(owner,expected["namespace"],expected["key"]); assertions.append({"kind":"state","owner":owner,"namespace":expected["namespace"],"key":expected["key"],"expected":expected["equals"],"actual":actual,"passed":actual==expected["equals"]})
    for event_type in scenario.get("expect", {}).get("events", []):
        assertions.append({"kind":"event","expected":event_type,"actual":event_type if event_type in types else None,"passed":event_type in types})
    if domain_assertions is not None:
        if domain_assertions.get("contract") != "relay-station-runtime-assertions.v0.1" or domain_assertions.get("scenario_id") != scenario_id:
            raise RelayStationScenarioError("invalid Relay Station domain assertions")
        for expected in domain_assertions.get("state", []):
            owner=_ref(expected["owner"],actor); actual=runtime.state.get(owner,expected["namespace"],expected["key"]); assertions.append({"kind":"domain_state","owner":owner,"namespace":expected["namespace"],"key":expected["key"],"expected":expected["equals"],"actual":actual,"passed":actual==expected["equals"]})
        for expected in domain_assertions.get("entities", []):
            eid=expected["entity_id"]; exists=runtime.registry.contains(eid); actual_type=runtime.registry.get(eid).entity_type if exists else None; assertions.append({"kind":"entity","entity_id":eid,"expected":expected["entity_type"],"actual":actual_type,"passed":exists and actual_type==expected["entity_type"]})
            for item in expected.get("state", []):
                actual=runtime.state.get(eid,item["namespace"],item["key"]); assertions.append({"kind":"entity_state","entity_id":eid,"namespace":item["namespace"],"key":item["key"],"expected":item["equals"],"actual":actual,"passed":exists and actual==item["equals"]})
    expected_status=scenario.get("expect",{}).get("status","completed"); statuses=[x["status"] for x in actions]; assertions.append({"kind":"action_status","expected":expected_status,"actual":statuses,"passed":all(x==expected_status for x in statuses)})
    return {"scenario_id":scenario_id,"title":scenario.get("title",""),"actor_id":actor,"passed":all(x["passed"] for x in assertions),"action_results":actions,"observed_event_types":types,"assertions":assertions,"diagnostics":runtime.diagnostics()}
