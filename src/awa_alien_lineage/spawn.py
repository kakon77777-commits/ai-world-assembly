from __future__ import annotations

from typing import Any

SPAWN_MODULE_ID = "alien_lineage.spawn"
SPAWN_MODULE_VERSION = "0.1.0"
SPAWN_ENTRYPOINT = "awa_alien_lineage.spawn:AlienLineageSpawnModule"
ENTITY_TRANSACTION_CAPABILITY = "entity_transaction/v0.1"


class AlienLineageSpawnModule:
    """Create one reviewed egg slot and one reviewed child slot transactionally."""

    def __init__(self) -> None:
        from compilableworld.models import ModuleContract
        self.contract = ModuleContract(
            SPAWN_MODULE_ID,
            SPAWN_MODULE_VERSION,
            "TMS",
            ["lay_egg", "hatch"],
            ["alien_lineage.egg_laid", "alien_lineage.egg_hatched"],
            ["position.*", "biology.*", "lineage.*"],
            ["position.*", "biology.*", "lineage.*"],
            ["entity", "state", "action", "event", ENTITY_TRANSACTION_CAPABILITY],
        )

    @staticmethod
    def _world_config(runtime: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        world = runtime.package.get("world", {})
        lineage = world.get("alien_lineage_runtime")
        spawn = world.get("alien_lineage_spawn")
        if not isinstance(lineage, dict) or not isinstance(spawn, dict):
            raise ValueError("Alien Lineage spawn configuration is missing")
        return lineage, spawn

    @staticmethod
    def _set(owner: str, namespace: str, key: str, value: Any) -> Any:
        from compilableworld.models import StateDelta
        return StateDelta(owner, namespace, key, "set", value, source_module=SPAWN_MODULE_ID)

    @staticmethod
    def _event(event_type: str, action: Any, payload: dict[str, Any]) -> Any:
        from compilableworld.models import EventIR
        return EventIR(event_type, SPAWN_MODULE_ID, payload, target=action.actor_id)

    @staticmethod
    def _entity_delta(spec: dict[str, Any]) -> Any:
        from compilableworld.models import Entity, EntityDelta
        entity = Entity(
            entity_id=spec["entity_id"],
            entity_type=spec["entity_type"],
            name=spec["name"],
            components=list(spec["components"]),
            metadata=dict(spec.get("metadata", {})),
        )
        return EntityDelta(operation="create", entity=entity, expected_absent=True, source_module=SPAWN_MODULE_ID)

    @staticmethod
    def _result(accepted: bool, *, deltas: list[Any] | None = None, events: list[Any] | None = None, entity_deltas: list[Any] | None = None, message: str = "") -> Any:
        from compilableworld.models import TransitionResult
        return TransitionResult(accepted, deltas or [], events or [], message, entity_deltas or [])

    @staticmethod
    def _bounded_int(value: Any, *, minimum: int = 0) -> int:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("numeric state is invalid")
        result = int(value)
        if result != value or result < minimum:
            raise ValueError("numeric state is out of bounds")
        return result

    def _function(self, runtime: Any, function_id: str, values: dict[str, int]) -> int:
        if not runtime.functions.has(function_id):
            raise ValueError(f"required FunctionIR is missing: {function_id}")
        return self._bounded_int(runtime.functions.evaluate(function_id, values), minimum=0)

    def evaluate(self, action: Any, runtime: Any) -> Any:
        try:
            if action.verb == "lay_egg":
                return self._lay_egg(action, runtime)
            if action.verb == "hatch":
                return self._hatch(action, runtime)
            return self._result(False, message=f"unsupported Alien Lineage spawn action: {action.verb}")
        except (ValueError, KeyError, TypeError) as exc:
            return self._result(False, message=str(exc))

    def _lay_egg(self, action: Any, runtime: Any) -> Any:
        config, spawn = self._world_config(runtime)
        if action.actor_id != spawn["parent_entity_id"]:
            return self._result(False, message="actor is not the reviewed bounded spawn parent")
        stages = list(config["stages"])
        current = runtime.state.get(action.actor_id, "lineage", "stage", stages[0])
        if current != config["adult_stage"]:
            return self._result(False, message="only an adult creature may lay an egg")
        egg = spawn["egg"]
        if runtime.registry.contains(egg["entity_id"]):
            return self._result(False, message="the reviewed egg entity already exists")
        if runtime.state.get(action.actor_id, "lineage", "egg_state", "none") != "none":
            return self._result(False, message="the bounded lineage egg slot is already used")
        room = runtime.state.get(action.actor_id, "position", "room")
        if not isinstance(room, str) or not room:
            return self._result(False, message="parent position is invalid")
        cost = self._function(runtime, "alien_lineage.egg_cost", {"stage_index": stages.index(current)})
        energy = self._bounded_int(runtime.state.get(action.actor_id, "biology", "energy", 0), minimum=0)
        if energy < cost:
            return self._result(False, message="insufficient energy to lay an egg")
        egg_id = egg["entity_id"]
        deltas = [
            self._set(action.actor_id, "biology", "energy", energy - cost),
            self._set(action.actor_id, "lineage", "egg_state", "laid"),
            self._set(action.actor_id, "lineage", "egg_id", egg_id),
            self._set(egg_id, "position", "room", room),
            self._set(egg_id, "lineage", "stage", "egg"),
            self._set(egg_id, "lineage", "species_ref", config["species_ref"]),
            self._set(egg_id, "lineage", "parent_id", action.actor_id),
        ]
        event = self._event("alien_lineage.egg_laid", action, {"parent": action.actor_id, "egg_id": egg_id, "energy_cost": cost, "room_id": room})
        return self._result(True, deltas=deltas, events=[event], entity_deltas=[self._entity_delta(egg)], message=f"Egg entity created: {egg_id}")

    def _hatch(self, action: Any, runtime: Any) -> Any:
        config, spawn = self._world_config(runtime)
        if action.actor_id != spawn["parent_entity_id"]:
            return self._result(False, message="actor is not the reviewed bounded spawn parent")
        egg = spawn["egg"]
        child = spawn["child"]
        egg_id, child_id = egg["entity_id"], child["entity_id"]
        if runtime.state.get(action.actor_id, "lineage", "egg_id") != egg_id or not runtime.registry.contains(egg_id):
            return self._result(False, message="there is no reviewed egg entity to hatch")
        if runtime.state.get(egg_id, "lineage", "stage") != "egg":
            return self._result(False, message="egg entity is not in the hatchable stage")
        if runtime.registry.contains(child_id):
            return self._result(False, message="the reviewed child entity already exists")
        room = runtime.state.get(egg_id, "position", "room")
        if not isinstance(room, str) or not room:
            return self._result(False, message="egg position is invalid")
        stage = config["hatch_stage"]
        species = config["species_ref"]
        deltas = [
            self._set(action.actor_id, "lineage", "egg_state", "hatched"),
            self._set(action.actor_id, "lineage", "child_id", child_id),
            self._set(action.actor_id, "lineage", "child_stage", stage),
            self._set(action.actor_id, "lineage", "child_species", species),
            self._set(egg_id, "lineage", "stage", "hatched"),
            self._set(egg_id, "lineage", "child_id", child_id),
            self._set(child_id, "position", "room", room),
            self._set(child_id, "lineage", "stage", stage),
            self._set(child_id, "lineage", "species_ref", species),
            self._set(child_id, "lineage", "parent_id", action.actor_id),
            self._set(child_id, "lineage", "organs", []),
            self._set(child_id, "biology", "energy", 0),
            self._set(child_id, "biology", "growth_points", 0),
        ]
        event = self._event("alien_lineage.egg_hatched", action, {"egg_id": egg_id, "child_id": child_id, "species_ref": species, "stage": stage, "room_id": room})
        return self._result(True, deltas=deltas, events=[event], entity_deltas=[self._entity_delta(child)], message=f"Child entity created: {child_id}")
