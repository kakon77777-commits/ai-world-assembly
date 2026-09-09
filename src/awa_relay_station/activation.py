from __future__ import annotations

from typing import Any

ACTIVATION_MODULE_ID = "relay_station.activation"
ACTIVATION_MODULE_VERSION = "0.1.0"
ACTIVATION_ENTRYPOINT = "awa_relay_station.activation:RelayActivationModule"
ENTITY_TRANSACTION_CAPABILITY = "entity_transaction/v0.1"


class RelayActivationModule:
    def __init__(self) -> None:
        from compilableworld.models import ModuleContract
        self.contract = ModuleContract(
            ACTIVATION_MODULE_ID, ACTIVATION_MODULE_VERSION, "TMS",
            ["activate"],
            ["relay_station.relay_activated", "relay_station.signal_online"],
            ["position.*", "contract.*", "maintenance.*", "signal.*"],
            ["contract.*", "signal.*", "position.*"],
            ["entity", "state", "action", "event", ENTITY_TRANSACTION_CAPABILITY],
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
        return StateDelta(owner, namespace, key, "set", value, source_module=ACTIVATION_MODULE_ID)

    @staticmethod
    def _event(event_type: str, action: Any, payload: dict[str, Any]) -> Any:
        from compilableworld.models import EventIR
        return EventIR(event_type, ACTIVATION_MODULE_ID, payload, target=action.actor_id)

    @staticmethod
    def _entity_delta(spec: dict[str, Any]) -> Any:
        from compilableworld.models import Entity, EntityDelta
        return EntityDelta(
            operation="create",
            entity=Entity(
                entity_id=spec["entity_id"],
                entity_type=spec["entity_type"],
                name=spec["name"],
                components=list(spec["components"]),
                metadata={"semantic_ref": spec["semantic_ref"], "provenance": "awa:relay_station:phase11"},
            ),
            expected_absent=True,
            source_module=ACTIVATION_MODULE_ID,
        )

    @staticmethod
    def _result(accepted: bool, *, deltas: list[Any] | None = None, events: list[Any] | None = None, entity_deltas: list[Any] | None = None, message: str = "") -> Any:
        from compilableworld.models import TransitionResult
        return TransitionResult(accepted, deltas or [], events or [], message, entity_deltas or [])

    def evaluate(self, action: Any, runtime: Any) -> Any:
        try:
            return self._activate(action, runtime) if action.verb == "activate" else self._result(False, message=f"unsupported Relay Station activation action: {action.verb}")
        except (ValueError, KeyError, TypeError) as exc:
            return self._result(False, message=str(exc))

    def _activate(self, action: Any, runtime: Any) -> Any:
        config = self._config(runtime)
        relay = config["relay_entity_id"]
        beacon = config["beacon"]
        if action.target_id != relay:
            return self._result(False, message="activate target must be the storm relay core")
        if runtime.state.get(action.actor_id, "position", "room") != runtime.state.get(relay, "position", "room"):
            return self._result(False, message="storm relay core is not in the actor room")
        if runtime.state.get(relay, "maintenance", "condition", config["condition_default"]) != "repaired":
            return self._result(False, message="relay must be repaired before activation")
        if runtime.state.get(relay, "signal", "active", False) is True:
            return self._result(False, message="relay is already active")
        if runtime.registry.contains(beacon["entity_id"]):
            return self._result(False, message="reviewed relay beacon entity already exists")
        room = runtime.state.get(relay, "position", "room")
        deltas = [
            self._set(relay, "signal", "active", True),
            self._set(action.actor_id, "contract", "status", "activated"),
            self._set(beacon["entity_id"], "position", "room", room),
            self._set(beacon["entity_id"], "signal", "state", "online"),
            self._set(beacon["entity_id"], "signal", "source_relay", relay),
        ]
        events = [
            self._event("relay_station.relay_activated", action, {"relay_id": relay, "beacon_id": beacon["entity_id"], "room_id": room}),
            self._event("relay_station.signal_online", action, {"beacon_id": beacon["entity_id"], "semantic_ref": beacon["semantic_ref"]}),
        ]
        return self._result(True, deltas=deltas, events=events, entity_deltas=[self._entity_delta(beacon)], message=f"Relay link activated: {beacon['entity_id']}")
