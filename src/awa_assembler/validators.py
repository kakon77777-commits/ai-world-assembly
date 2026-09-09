from __future__ import annotations

import io
import json
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from awa_contracts.validator import validation_errors

from .common import schema


@dataclass(frozen=True)
class CheckResult:
    validator: str
    passed: bool
    diagnostics: list[str]


Validator = Callable[[bytes, Path, dict[str, Any]], CheckResult]


def _decode_wav(payload: bytes) -> tuple[wave.Wave_read, bytes]:
    handle = wave.open(io.BytesIO(payload), "rb")
    frames = handle.readframes(handle.getnframes())
    return handle, frames


def validate_decode(payload: bytes, root: Path, task: dict[str, Any]) -> CheckResult:
    del root, task
    validator = "validator.wav.decode"
    try:
        handle, frames = _decode_wav(payload)
        if handle.getcomptype() != "NONE":
            return CheckResult(validator, False, [f"{validator}: compressed WAV is not allowed"])
        if handle.getnchannels() != 1 or handle.getsampwidth() != 2:
            return CheckResult(validator, False, [f"{validator}: expected mono 16-bit PCM"])
        if not frames:
            return CheckResult(validator, False, [f"{validator}: WAV contains no PCM frames"])
    except (wave.Error, EOFError, struct.error) as exc:
        return CheckResult(validator, False, [f"{validator}: cannot decode WAV ({exc})"])
    return CheckResult(validator, True, [])


def validate_duration(payload: bytes, root: Path, task: dict[str, Any]) -> CheckResult:
    del root, task
    validator = "validator.audio.duration"
    try:
        handle, _ = _decode_wav(payload)
        rate = handle.getframerate()
        frames = handle.getnframes()
        if rate <= 0:
            return CheckResult(validator, False, [f"{validator}: invalid sample rate"])
        duration_ms = frames * 1000 // rate
    except (wave.Error, EOFError, struct.error) as exc:
        return CheckResult(validator, False, [f"{validator}: cannot inspect WAV ({exc})"])
    if not 50 <= duration_ms <= 500:
        return CheckResult(validator, False, [f"{validator}: duration_ms={duration_ms} outside 50..500"])
    return CheckResult(validator, True, [])


def validate_non_silent(payload: bytes, root: Path, task: dict[str, Any]) -> CheckResult:
    del root, task
    validator = "validator.audio.non_silent"
    try:
        handle, frames = _decode_wav(payload)
        if handle.getsampwidth() != 2:
            return CheckResult(validator, False, [f"{validator}: expected 16-bit PCM"])
        if len(frames) % 2:
            return CheckResult(validator, False, [f"{validator}: malformed PCM byte length"])
        samples = struct.unpack(f"<{len(frames) // 2}h", frames)
        peak = max((abs(value) for value in samples), default=0)
    except (wave.Error, EOFError, struct.error) as exc:
        return CheckResult(validator, False, [f"{validator}: cannot inspect PCM ({exc})"])
    if peak < 1000:
        return CheckResult(validator, False, [f"{validator}: peak amplitude {peak} below 1000"])
    return CheckResult(validator, True, [])


def _decode_json(payload: bytes) -> tuple[Any | None, str | None]:
    try:
        return json.loads(payload.decode("utf-8")), None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, str(exc)


def validate_json_decode(payload: bytes, root: Path, task: dict[str, Any]) -> CheckResult:
    del root, task
    validator = "validator.json.decode"
    document, error = _decode_json(payload)
    if error is not None:
        return CheckResult(validator, False, [f"{validator}: cannot decode UTF-8 JSON ({error})"])
    if not isinstance(document, dict):
        return CheckResult(validator, False, [f"{validator}: top-level JSON value must be an object"])
    return CheckResult(validator, True, [])


def validate_effect_recipe_contract(payload: bytes, root: Path, task: dict[str, Any]) -> CheckResult:
    del task
    validator = "validator.presentation.effect_recipe_contract"
    document, error = _decode_json(payload)
    if error is not None or not isinstance(document, dict):
        return CheckResult(validator, False, [f"{validator}: cannot inspect invalid JSON"])
    contract = document.get("contract")
    name = "presentation-effect-recipe.v0.2" if contract == "presentation-effect-recipe.v0.2" else "presentation-effect-recipe.v0.1"
    errors = validation_errors(schema(root, name), document)
    if errors:
        return CheckResult(validator, False, [f"{validator}: {item}" for item in errors])
    return CheckResult(validator, True, [])


def validate_effect_recipe_semantics(payload: bytes, root: Path, task: dict[str, Any]) -> CheckResult:
    del root
    validator = "validator.presentation.effect_recipe_semantics"
    document, error = _decode_json(payload)
    if error is not None or not isinstance(document, dict):
        return CheckResult(validator, False, [f"{validator}: recipe is not inspectable JSON"])
    if task["target"]["layer"] != "presentation":
        return CheckResult(validator, False, [f"{validator}: target layer must be presentation"])
    forbidden = sorted(set(document) & {"runtime_action", "state_delta", "entity_registry", "world_state"})
    if forbidden:
        return CheckResult(validator, False, [f"{validator}: presentation recipe contains forbidden authority fields: {forbidden}"])
    effect = document.get("effect")
    kind = task["target"]["kind"]
    if kind == "relay_presentation_recipe":
        if document.get("contract") != "presentation-effect-recipe.v0.2" or document.get("event_type") != "relay_station.relay_activated":
            return CheckResult(validator, False, [f"{validator}: relay_effect_recipe must bind relay_station.relay_activated using v0.2"])
        if not isinstance(effect, dict) or effect.get("target") != "relay_visual":
            return CheckResult(validator, False, [f"{validator}: relay_effect_recipe may target relay_visual only"])
        return CheckResult(validator, True, [])
    if document.get("event_type") != "alien_lineage.creature_mutated":
        return CheckResult(validator, False, [f"{validator}: recipe must bind alien_lineage.creature_mutated"])
    if not isinstance(effect, dict) or effect.get("target") != "creature_visual":
        return CheckResult(validator, False, [f"{validator}: recipe may target creature_visual only"])
    return CheckResult(validator, True, [])


VALIDATORS: dict[str, Validator] = {
    "validator.wav.decode": validate_decode,
    "validator.audio.duration": validate_duration,
    "validator.audio.non_silent": validate_non_silent,
    "validator.json.decode": validate_json_decode,
    "validator.presentation.effect_recipe_contract": validate_effect_recipe_contract,
    "validator.presentation.effect_recipe_semantics": validate_effect_recipe_semantics,
}
