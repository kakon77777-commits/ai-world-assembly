from __future__ import annotations

import json
import struct
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from awa_asset_graph.graph import sha256_json

from .common import sha_bytes, validate


class CandidateProducer(Protocol):
    producer_id: str

    def produce(self, *, attempt: int, task: dict, diagnostics: list[str]) -> bytes: ...


@runtime_checkable
class ProviderEvidencedProducer(Protocol):
    def invocation_receipt(self, *, attempt: int) -> dict: ...


def provider_invocation_for(producer: CandidateProducer, *, attempt: int) -> dict | None:
    if not isinstance(producer, ProviderEvidencedProducer):
        return None
    return producer.invocation_receipt(attempt=attempt)


def _pcm_wav(samples: list[int], *, sample_rate: int = 22050) -> bytes:
    channels = 1
    sample_width = 2
    byte_rate = sample_rate * channels * sample_width
    block_align = channels * sample_width
    pcm = b"".join(struct.pack("<h", max(-32768, min(32767, int(value)))) for value in samples)
    fmt = struct.pack("<HHIIHH", 1, channels, sample_rate, byte_rate, block_align, sample_width * 8)
    riff_size = 4 + (8 + len(fmt)) + (8 + len(pcm))
    return b"RIFF" + struct.pack("<I", riff_size) + b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(pcm)) + pcm


def _canonical_json_bytes(document: dict) -> bytes:
    return (json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


@dataclass
class HTTPProviderProducer:
    """Provider-agnostic HTTP gateway implementing the existing CandidateProducer boundary.

    The remote endpoint receives a proposal-only, versioned request and returns raw candidate
    bytes. Provider/model identity is recorded only in locally derived invocation evidence; the
    stable artifact generator identity remains this adapter ID so vendor choice cannot become
    world or module semantics.
    """

    root: str | Path
    endpoint: str
    provider_id: str
    model_id: str
    timeout_seconds: float = 30.0
    producer_id: str = "provider-backed.http.v0.1"
    _receipts: dict[int, dict] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root).resolve()
        if not self.endpoint.startswith(("http://", "https://")):
            raise ValueError("provider endpoint must use http or https")
        if not self.provider_id or not self.model_id:
            raise ValueError("provider_id and model_id are required")
        if self.timeout_seconds <= 0:
            raise ValueError("provider timeout must be positive")

    def _request_document(self, *, attempt: int, task: dict, diagnostics: list[str]) -> dict:
        request = {
            "contract": "provider-generation-request.v0.1",
            "authority": "proposal",
            "task_id": task["task_id"],
            "capability_id": task["capability_id"],
            "generation_task": task["generation_task"],
            "target": task["target"],
            "validators": task["validators"],
            "attempt": attempt,
            "diagnostics": list(diagnostics),
            "canonical_write": False,
        }
        return validate(self.root, "provider-generation-request.v0.1", request, "provider generation request")

    def produce(self, *, attempt: int, task: dict, diagnostics: list[str]) -> bytes:
        request_doc = self._request_document(attempt=attempt, task=task, diagnostics=diagnostics)
        request_bytes = _canonical_json_bytes(request_doc)
        request = urllib.request.Request(
            self.endpoint,
            data=request_bytes,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": task["target"]["mime_type"]},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                status = int(response.status)
                payload = response.read()
                content_type = response.headers.get_content_type() or "application/octet-stream"
        except urllib.error.HTTPError as exc:
            raise ValueError(f"provider returned HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise ValueError(f"provider transport failed: {exc.reason}") from exc
        if status < 200 or status >= 300:
            raise ValueError(f"provider returned HTTP {status}")
        if not payload:
            raise ValueError("provider returned empty response")

        basis = {
            "authority": "candidate_generation_evidence",
            "adapter_id": self.producer_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "task_id": task["task_id"],
            "attempt": attempt,
            "request_sha256": sha_bytes(request_bytes),
            "response_sha256": sha_bytes(payload),
            "http_status": status,
            "response_content_type": content_type,
            "canonical_write": False,
        }
        body = {
            "contract": "provider-invocation-receipt.v0.1",
            "invocation_id": f"provider-invocation:{sha256_json(basis)[:16]}",
            **basis,
        }
        receipt = {**body, "evidence_hash": sha256_json(body)}
        self._receipts[attempt] = validate(
            self.root, "provider-invocation-receipt.v0.1", receipt, "provider invocation receipt"
        )
        return payload

    def invocation_receipt(self, *, attempt: int) -> dict:
        try:
            return self._receipts[attempt]
        except KeyError as exc:
            raise ValueError(f"no provider invocation evidence for attempt {attempt}") from exc


@dataclass(frozen=True)
class ReferenceAudioProducer:
    """Deterministic Phase 8 proof producer; real providers can implement CandidateProducer."""

    producer_id: str = "reference.audio.repair.v0.1"

    def produce(self, *, attempt: int, task: dict, diagnostics: list[str]) -> bytes:
        if task["target"]["kind"] != "audio" or task["target"]["mime_type"] != "audio/wav":
            raise ValueError("reference audio producer only supports audio/wav")
        sample_rate = 22050
        frames = sample_rate // 4
        if attempt == 1:
            return _pcm_wav([0] * frames, sample_rate=sample_rate)
        if not any("non_silent" in item for item in diagnostics):
            raise ValueError("repair attempt requires non_silent validator evidence")
        period = 50
        half = period // 2
        samples: list[int] = []
        for index in range(frames):
            phase = index % period
            triangle = phase if phase < half else period - phase
            centered = (triangle * 2 - half) * 900
            envelope = max(1, frames - index)
            samples.append(centered * envelope // frames)
        return _pcm_wav(samples, sample_rate=sample_rate)


@dataclass(frozen=True)
class ReferencePresentationRecipeProducer:
    """Deterministic Phase 9 proof producer for a declarative presentation artifact.

    Attempt 1 deliberately contains a Runtime-authority-shaped field and an out-of-bounds
    duration. Repair removes the forbidden field and returns a schema-valid bounded visual recipe.
    """

    producer_id: str = "reference.presentation-recipe.repair.v0.1"

    def produce(self, *, attempt: int, task: dict, diagnostics: list[str]) -> bytes:
        if task["target"]["kind"] != "presentation_recipe" or task["target"]["mime_type"] != "application/json":
            raise ValueError("reference presentation recipe producer only supports application/json presentation_recipe")
        if attempt == 1:
            return _canonical_json_bytes({
                "contract": "presentation-effect-recipe.v0.1",
                "recipe_id": "effect.mutation-pulse",
                "event_type": "alien_lineage.creature_mutated",
                "effect": {"target": "creature_visual", "scale_peak": 1.16, "duration_ms": 900, "emissive_boost": 0.7},
                "runtime_action": "mutate",
                "version": "v0.1",
            })
        if not any("effect_recipe" in item or "runtime_action" in item or "duration_ms" in item for item in diagnostics):
            raise ValueError("repair attempt requires presentation recipe validator diagnostics")
        return _canonical_json_bytes({
            "contract": "presentation-effect-recipe.v0.1",
            "recipe_id": "effect.mutation-pulse",
            "event_type": "alien_lineage.creature_mutated",
            "effect": {"target": "creature_visual", "scale_peak": 1.16, "duration_ms": 180, "emissive_boost": 0.7},
            "version": "v0.1",
        })


@dataclass(frozen=True)
class ReferenceRelayPresentationRecipeProducer:
    """Deterministic Phase 11 producer for Relay Station activation presentation evidence."""

    producer_id: str = "reference.relay-presentation-recipe.repair.v0.1"

    def produce(self, *, attempt: int, task: dict, diagnostics: list[str]) -> bytes:
        if task["target"]["kind"] != "relay_presentation_recipe" or task["target"]["mime_type"] != "application/json":
            raise ValueError("reference relay presentation recipe producer only supports relay_presentation_recipe")
        if attempt == 1:
            return _canonical_json_bytes({
                "contract": "presentation-effect-recipe.v0.2",
                "recipe_id": "effect.relay-activation-pulse",
                "event_type": "relay_station.relay_activated",
                "effect": {"target": "relay_visual", "scale_peak": 1.14, "duration_ms": 900, "emissive_boost": 0.8},
                "state_delta": {"signal.active": True},
                "version": "v0.2",
            })
        if not any("relay_effect_recipe" in item or "state_delta" in item or "duration_ms" in item for item in diagnostics):
            raise ValueError("repair attempt requires relay presentation validator diagnostics")
        return _canonical_json_bytes({
            "contract": "presentation-effect-recipe.v0.2",
            "recipe_id": "effect.relay-activation-pulse",
            "event_type": "relay_station.relay_activated",
            "effect": {"target": "relay_visual", "scale_peak": 1.14, "duration_ms": 220, "emissive_boost": 0.8},
            "version": "v0.2",
        })


def reference_producer_for(task: dict) -> CandidateProducer:
    kind = task.get("target", {}).get("kind")
    if kind == "audio":
        return ReferenceAudioProducer()
    if kind == "presentation_recipe":
        return ReferencePresentationRecipeProducer()
    if kind == "relay_presentation_recipe":
        return ReferenceRelayPresentationRecipeProducer()
    raise ValueError(f"no deterministic reference producer for target kind: {kind!r}")
