from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Protocol


class CandidateProducer(Protocol):
    producer_id: str

    def produce(self, *, attempt: int, task: dict, diagnostics: list[str]) -> bytes: ...


def _pcm_wav(samples: list[int], *, sample_rate: int = 22050) -> bytes:
    channels = 1
    sample_width = 2
    byte_rate = sample_rate * channels * sample_width
    block_align = channels * sample_width
    pcm = b"".join(struct.pack("<h", max(-32768, min(32767, int(value)))) for value in samples)
    fmt = struct.pack("<HHIIHH", 1, channels, sample_rate, byte_rate, block_align, sample_width * 8)
    riff_size = 4 + (8 + len(fmt)) + (8 + len(pcm))
    return b"RIFF" + struct.pack("<I", riff_size) + b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(pcm)) + pcm


@dataclass(frozen=True)
class ReferenceAudioProducer:
    """Deterministic proof producer for the assembler loop.

    Attempt 1 intentionally emits silence so the non-silent validator produces
    a real RED witness. A repair attempt emits a deterministic decaying triangle
    waveform. This proves orchestration/repair without making CI depend on an
    external model provider. Real AI providers can implement CandidateProducer.
    """

    producer_id: str = "reference.audio.repair.v0.1"

    def produce(self, *, attempt: int, task: dict, diagnostics: list[str]) -> bytes:
        if task["target"]["kind"] != "audio" or task["target"]["mime_type"] != "audio/wav":
            raise ValueError("reference audio producer only supports audio/wav")
        sample_rate = 22050
        frames = sample_rate // 4
        if attempt == 1:
            return _pcm_wav([0] * frames, sample_rate=sample_rate)

        # Repair is diagnostic-driven: the reference producer only changes the
        # signal after the first candidate was rejected as silent.
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
            sample = centered * envelope // frames
            samples.append(sample)
        return _pcm_wav(samples, sample_rate=sample_rate)
