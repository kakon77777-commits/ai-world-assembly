from __future__ import annotations

from typing import Any

MODULE_ID = "relay_station.runtime"
MODULE_VERSION = "0.1.0"
ENTRYPOINT = "awa_relay_station.runtime:RelayStationModule"


class RelayStationModule:
    def __init__(self) -> None:
        from compilableworld.models import ModuleContract
        self.contract = ModuleContract(
            MODULE_ID, MODULE_VERSION, "TMS",
            ["inspect", "pick_up", "deliver", "repair"],
            [
                "relay_station.inspected",
                "relay_station.coupler_picked",
                "relay_station.coupler_delivered",
                "relay_station.relay_repaired",
            ],
            ["position.*", "cargo.*", "contract.*", "inventory.*", "maintenance.*", "signal.*"],
            ["position.*", "cargo.*", "contract.*", "inventory.*", "maintenance.*"],
            ["state", "action", "event"],
        )

    @staticmethod
    def _config(runtime: Any) -> dict[str, Any]:
        config = runtime.package.get("world", {}).get("relay_station_runtime")
        if not isinstance(config, dict):
            raise ValueError("Relay Station runtime configuration is missing")
        return config

    @staticmethod
    def _set(owner: str, namespace: str, key: str, value: Any) -> Any:
        from compilableworld.models import StateDelta
        return StateDelta(owner, namespace, key, "set", value, source_module=MODULE_ID)

    @staticmethod
    def _event(event_type: str, action: Any, payload: dict[str, Any]) -> Any:
        from compilableworld.models import EventIR
        return EventIR(event_type, MODULE_ID, payload, target=action.actor_id)

    @staticmethod
    def _result(accepted: bool, deltas: list[Any] | None = None, events: list[Any] | None = None, message: str = "") -> Any:
        from compilableworld.models import TransitionResult
        return TransitionResult(accepted, deltas or [], events or [], message)

    @staticmethod
    def _same_room(runtime: Any, left: str, right: str) -> bool:
        return runtime.state.get(left, "position", "room") == runtime.state.get(right, "position", "room")

    def evaluate(self, action: Any, runtime: Any) -> Any:
        try:
            if action.verb == "inspect":
                return self._inspect(action, runtime)
            if action.verb == "pick_up":
                return self._pick_up(action, runtime)
            if action.verb == "deliver":
                return self._deliver(action, runtime)
            if action.verb == "repair":
                return self._repair(action, runtime)
            return self._result(False, message=f"unsupported Relay Station action: {action.verb}")
        except (ValueError, KeyError, TypeError) as exc:
            return self._result(False, message=str(exc))

    def _inspect(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        target = action.target_id
        allowed = {config["relay_entity_id"], config["coupler_item_id"]}
        if target not in allowed or not runtime.registry.contains(target):
            return self._result(False, message="inspect target is not part of the bounded Relay Station slice")
        if not self._same_room(runtime, action.actor_id, target):
            return self._result(False, message="inspect target is not in the actor room")
        if target == config["relay_entity_id"]:
            condition = runtime.state.get(target, "maintenance", "condition", config["condition_default"])
            payload = {"target_id": target, "kind": "relay", "condition": condition}
        else:
            payload = {"target_id": target, "kind": "coupler", "portable": True}
        return self._result(True, events=[self._event("relay_station.inspected", action, payload)], message=f"Inspected {target}.")

    def _pick_up(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        item = config["coupler_item_id"]
        if action.target_id != item or not runtime.registry.contains(item):
            return self._result(False, message="pick_up requires the reviewed phase coupler")
        if runtime.state.get(action.actor_id, "cargo", "current") not in {None, ""}:
            return self._result(False, message="cargo slot is already occupied")
        if runtime.state.get(item, "inventory", "carrier") not in {None, ""}:
            return self._result(False, message="phase coupler is already carried")
        if not self._same_room(runtime, action.actor_id, item):
            return self._result(False, message="phase coupler is not in the actor room")
        deltas = [
            self._set(action.actor_id, "cargo", "current", item),
            self._set(action.actor_id, "contract", "status", "coupler_picked"),
            self._set(item, "inventory", "carrier", action.actor_id),
            self._set(item, "position", "room", None),
        ]
        event = self._event("relay_station.coupler_picked", action, {"item_id": item})
        return self._result(True, deltas, [event], "Phase coupler secured.")

    def _deliver(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        relay = config["relay_entity_id"]
        item = config["coupler_item_id"]
        if action.target_id != relay:
            return self._result(False, message="deliver target must be the storm relay core")
        if runtime.state.get(action.actor_id, "cargo", "current") != item:
            return self._result(False, message="phase coupler is not in the actor cargo slot")
        if not self._same_room(runtime, action.actor_id, relay):
            return self._result(False, message="storm relay core is not in the actor room")
        room = runtime.state.get(relay, "position", "room")
        deltas = [
            self._set(action.actor_id, "cargo", "current", None),
            self._set(action.actor_id, "contract", "status", "coupler_delivered"),
            self._set(item, "inventory", "carrier", None),
            self._set(item, "position", "room", room),
            self._set(relay, "maintenance", "coupler_delivered", True),
        ]
        event = self._event("relay_station.coupler_delivered", action, {"item_id": item, "relay_id": relay})
        return self._result(True, deltas, [event], "Phase coupler delivered to the relay core.")

    def _repair(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        relay = config["relay_entity_id"]
        if action.target_id != relay or not self._same_room(runtime, action.actor_id, relay):
            return self._result(False, message="repair requires the local storm relay core")
        if runtime.state.get(relay, "maintenance", "coupler_delivered", False) is not True:
            return self._result(False, message="relay cannot be repaired before coupler delivery")
        condition = runtime.state.get(relay, "maintenance", "condition", config["condition_default"])
        if condition != "damaged":
            return self._result(False, message="relay is not in the damaged state")
        deltas = [
            self._set(relay, "maintenance", "condition", "repaired"),
            self._set(action.actor_id, "contract", "status", "repaired"),
        ]
        event = self._event("relay_station.relay_repaired", action, {"relay_id": relay})
        return self._result(True, deltas, [event], "Storm relay repaired.")


def install_relay_station_runtime(runtime: Any) -> None:
    from compilableworld.modules import install_builtin_modules
    install_builtin_modules(runtime)
    extensions = runtime.package.get("world", {}).get("runtime_extensions", [])
    expected = {"module_id": MODULE_ID, "version": MODULE_VERSION, "entrypoint": ENTRYPOINT}
    if expected not in extensions:
        raise ValueError("compiled world does not declare relay_station.runtime")
    runtime.register_module(RelayStationModule())
    from .activation import ACTIVATION_ENTRYPOINT, ACTIVATION_MODULE_ID, ACTIVATION_MODULE_VERSION, RelayActivationModule
    activation_expected = {
        "module_id": ACTIVATION_MODULE_ID,
        "version": ACTIVATION_MODULE_VERSION,
        "entrypoint": ACTIVATION_ENTRYPOINT,
    }
    if activation_expected in extensions:
        from compilableworld.entity_transaction import EntityTransactionRuntime
        if not isinstance(runtime, EntityTransactionRuntime):
            raise ValueError("relay_station.activation requires EntityTransactionRuntime")
        runtime.register_module(RelayActivationModule())
