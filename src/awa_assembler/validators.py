from __future__ import annotations

import io
import struct
import wave
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class CheckResult:
    validator: str
    passed: bool
    diagnostics: list[str]


def _decode_wav(payload: bytes) -> tuple[wave.Wave_read, bytes]:
    handle = wave.open(io.BytesIO(payload), "rb")
    frames = handle.readframes(handle.getnframes())
    return handle, frames


def validate_decode(payload: bytes) -> CheckResult:
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


def validate_duration(payload: bytes) -> CheckResult:
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


def validate_non_silent(payload: bytes) -> CheckResult:
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


VALIDATORS: dict[str, Callable[[bytes], CheckResult]] = {
    "validator.wav.decode": validate_decode,
    "validator.audio.duration": validate_duration,
    "validator.audio.non_silent": validate_non_silent,
}
