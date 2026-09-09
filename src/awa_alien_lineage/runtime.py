from __future__ import annotations

from typing import Any

MODULE_ID = "alien_lineage.runtime"
MODULE_VERSION = "0.1.0"
ENTRYPOINT = "awa_alien_lineage.runtime:AlienLineageModule"


class AlienLineageModule:
    """Bounded domain module loaded outside CompilableWorld's builtin registry.

    The module mutates only StateStore paths through StateDelta and emits EventIR.
    It deliberately does not add/remove EntityRegistry entries in Phase 6.
    """

    def __init__(self) -> None:
        from compilableworld.models import ModuleContract

        self.contract = ModuleContract(
            MODULE_ID,
            MODULE_VERSION,
            "TMS",
            ["feed", "mutate", "grow", "lay_egg", "hatch", "enter_rift"],
            [
                "alien_lineage.creature_fed",
                "alien_lineage.creature_mutated",
                "alien_lineage.creature_grew",
                "alien_lineage.egg_laid",
                "alien_lineage.egg_hatched",
                "alien_lineage.rift_entered",
            ],
            ["position.*", "resource.*", "biology.*", "lineage.*", "world.*"],
            ["resource.*", "biology.*", "lineage.*", "world.*"],
            ["entity", "state", "action", "event"],
        )

    @staticmethod
    def _config(runtime: Any) -> dict[str, Any]:
        config = runtime.package.get("world", {}).get("alien_lineage_runtime")
        if not isinstance(config, dict):
            raise ValueError("Alien Lineage runtime config is missing")
        return config

    @staticmethod
    def _event(event_type: str, action: Any, payload: dict[str, Any]) -> Any:
        from compilableworld.models import EventIR
        return EventIR(event_type, MODULE_ID, payload, target=action.actor_id)

    @staticmethod
    def _set(owner: str, namespace: str, key: str, value: Any) -> Any:
        from compilableworld.models import StateDelta
        return StateDelta(owner, namespace, key, "set", value, source_module=MODULE_ID)

    @staticmethod
    def _append(owner: str, namespace: str, key: str, value: Any) -> Any:
        from compilableworld.models import StateDelta
        return StateDelta(owner, namespace, key, "append", value, source_module=MODULE_ID)

    @staticmethod
    def _result(accepted: bool, deltas: list[Any] | None = None, events: list[Any] | None = None, message: str = "") -> Any:
        from compilableworld.models import TransitionResult
        return TransitionResult(accepted, deltas or [], events or [], message)

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
        result = runtime.functions.evaluate(function_id, values)
        return self._bounded_int(result, minimum=0)

    def evaluate(self, action: Any, runtime: Any) -> Any:
        try:
            if action.verb == "feed":
                return self._feed(action, runtime)
            if action.verb == "mutate":
                return self._mutate(action, runtime)
            if action.verb == "grow":
                return self._grow(action, runtime)
            if action.verb == "lay_egg":
                return self._lay_egg(action, runtime)
            if action.verb == "hatch":
                return self._hatch(action, runtime)
            if action.verb == "enter_rift":
                return self._enter_rift(action, runtime)
            return self._result(False, message=f"unsupported Alien Lineage action: {action.verb}")
        except (ValueError, KeyError, TypeError) as exc:
            return self._result(False, message=str(exc))

    def _feed(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        target = action.target_id
        defaults = config.get("resource_defaults", {})
        if not target or target not in defaults or not runtime.registry.contains(target):
            return self._result(False, message="feed target is not an authored Alien Lineage resource")
        if runtime.registry.get(target).entity_type != "item":
            return self._result(False, message="feed target is not a resource item")
        actor_room = runtime.state.get(action.actor_id, "position", "room")
        target_room = runtime.state.get(target, "position", "room")
        if actor_room != target_room:
            return self._result(False, message="feed target is not in the current room")
        units = action.args.get("units", 1)
        if units != 1:
            return self._result(False, message="Phase 6 feed supports exactly one resource unit per action")
        current = self._bounded_int(runtime.state.get(target, "resource", "amount", defaults[target]), minimum=0)
        if current < 1:
            return self._result(False, message="resource is depleted")
        gain = self._function(runtime, "alien_lineage.feed_gain", {"units": 1})
        energy = self._bounded_int(runtime.state.get(action.actor_id, "biology", "energy", 0), minimum=0)
        growth = self._bounded_int(runtime.state.get(action.actor_id, "biology", "growth_points", 0), minimum=0)
        deltas = [
            self._set(target, "resource", "amount", current - 1),
            self._set(action.actor_id, "biology", "energy", energy + gain),
            self._set(action.actor_id, "biology", "growth_points", growth + gain),
        ]
        event = self._event("alien_lineage.creature_fed", action, {"resource": target, "units": 1, "gain": gain, "remaining": current - 1})
        return self._result(True, deltas, [event], "The creature filters one unit of mineral bloom.")

    def _mutate(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        organ_id = action.args.get("organ_id")
        catalog = {entry["organ_id"]: entry for entry in config.get("organs", []) if isinstance(entry, dict)}
        if not isinstance(organ_id, str) or organ_id not in catalog:
            return self._result(False, message="unknown or unauthorized organ mutation")
        organs = runtime.state.get(action.actor_id, "lineage", "organs", [])
        if not isinstance(organs, list):
            return self._result(False, message="lineage.organs state is invalid")
        if organ_id in organs:
            return self._result(False, message="organ is already present")
        cost = self._function(runtime, "alien_lineage.mutation_cost", {"tier": int(catalog[organ_id]["tier"])})
        growth = self._bounded_int(runtime.state.get(action.actor_id, "biology", "growth_points", 0), minimum=0)
        if growth < cost:
            return self._result(False, message="insufficient growth points for mutation")
        deltas = [
            self._set(action.actor_id, "biology", "growth_points", growth - cost),
            self._append(action.actor_id, "lineage", "organs", organ_id),
        ]
        event = self._event("alien_lineage.creature_mutated", action, {"organ_id": organ_id, "cost": cost})
        return self._result(True, deltas, [event], f"Mutation accepted: {organ_id}")

    def _grow(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        stages = list(config.get("stages", []))
        if len(stages) < 2:
            return self._result(False, message="runtime stage configuration is invalid")
        current = runtime.state.get(action.actor_id, "lineage", "stage", stages[0])
        if current not in stages:
            return self._result(False, message="current lineage stage is invalid")
        index = stages.index(current)
        if index >= len(stages) - 1:
            return self._result(False, message="creature is already at the final bounded stage")
        threshold = self._function(runtime, "alien_lineage.growth_threshold", {"stage_index": index})
        growth = self._bounded_int(runtime.state.get(action.actor_id, "biology", "growth_points", 0), minimum=0)
        if growth < threshold:
            return self._result(False, message="insufficient growth points")
        target = stages[index + 1]
        deltas = [
            self._set(action.actor_id, "biology", "growth_points", growth - threshold),
            self._set(action.actor_id, "lineage", "stage", target),
        ]
        event = self._event("alien_lineage.creature_grew", action, {"from": current, "to": target, "threshold": threshold})
        return self._result(True, deltas, [event], f"Growth stage advanced to {target}.")

    def _lay_egg(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        stages = list(config["stages"])
        current = runtime.state.get(action.actor_id, "lineage", "stage", stages[0])
        if current != config["adult_stage"]:
            return self._result(False, message="only an adult creature may lay an egg")
        egg_state = runtime.state.get(action.actor_id, "lineage", "egg_state", "none")
        if egg_state != "none":
            return self._result(False, message="the bounded lineage egg slot is already used")
        stage_index = stages.index(current)
        cost = self._function(runtime, "alien_lineage.egg_cost", {"stage_index": stage_index})
        energy = self._bounded_int(runtime.state.get(action.actor_id, "biology", "energy", 0), minimum=0)
        if energy < cost:
            return self._result(False, message="insufficient energy to lay an egg")
        deltas = [
            self._set(action.actor_id, "biology", "energy", energy - cost),
            self._set(action.actor_id, "lineage", "egg_state", "laid"),
            self._set(action.actor_id, "lineage", "egg_parent", action.actor_id),
        ]
        event = self._event("alien_lineage.egg_laid", action, {"parent": action.actor_id, "energy_cost": cost})
        return self._result(True, deltas, [event], "A bounded lineage egg has been laid.")

    def _hatch(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        if runtime.state.get(action.actor_id, "lineage", "egg_state", "none") != "laid":
            return self._result(False, message="there is no laid egg to hatch")
        deltas = [
            self._set(action.actor_id, "lineage", "egg_state", "hatched"),
            self._set(action.actor_id, "lineage", "child_stage", config["hatch_stage"]),
            self._set(action.actor_id, "lineage", "child_species", config["species_ref"]),
        ]
        event = self._event("alien_lineage.egg_hatched", action, {"species_ref": config["species_ref"], "stage": config["hatch_stage"]})
        return self._result(True, deltas, [event], "The bounded lineage egg has hatched.")

    def _enter_rift(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        stages = list(config["stages"])
        current = runtime.state.get(action.actor_id, "lineage", "stage", stages[0])
        if current != config["adult_stage"]:
            return self._result(False, message="only an adult creature may enter a rift")
        rift_id = action.args.get("rift_id")
        rifts = config.get("rifts", {})
        if not isinstance(rift_id, str) or rift_id not in rifts:
            return self._result(False, message="unknown rift")
        worldline = rifts[rift_id]
        deltas = [
            self._set(action.actor_id, "world", "worldline", worldline),
            self._set(action.actor_id, "lineage", "last_rift", rift_id),
        ]
        event = self._event("alien_lineage.rift_entered", action, {"rift_id": rift_id, "worldline": worldline})
        return self._result(True, deltas, [event], f"Entered rift {rift_id} -> {worldline}.")


def install_alien_lineage_runtime(runtime: Any) -> None:
    from compilableworld.modules import install_builtin_modules

    install_builtin_modules(runtime)
    extensions = runtime.package.get("world", {}).get("runtime_extensions", [])
    expected = {"module_id": MODULE_ID, "version": MODULE_VERSION, "entrypoint": ENTRYPOINT}
    if expected not in extensions:
        raise ValueError("compiled world does not declare the expected Alien Lineage runtime extension")
    runtime.register_module(AlienLineageModule())
