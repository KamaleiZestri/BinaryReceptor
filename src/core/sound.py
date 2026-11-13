"""In-memory 16-bit PCM scanner audio chime synthesizer and asynchronous player for BinaryReceptor."""
from __future__ import annotations

import io
import math
import struct
import threading
import wave

try:
    import winsound
except ImportError:
    winsound = None


def generate_scanner_beep_wav(
    freq1: float = 1800.0,
    dur1_ms: float = 45.0,
    freq2: float = 2400.0,
    dur2_ms: float = 45.0,
    sample_rate: int = 44100,
    volume: float = 0.6,
) -> bytes:
    """Synthesize a dual-tone scanner chime in memory as a standard 16-bit PCM .wav."""
    n1 = int(sample_rate * (dur1_ms / 1000.0))
    n2 = int(sample_rate * (dur2_ms / 1000.0))
    samples: list[int] = []
    max_amp = int(32767 * max(0.0, min(1.0, volume)))

    # Tone 1 with 5ms attack envelope
    attack_samples = int(sample_rate * 0.005)
    for i in range(n1):
        t = i / sample_rate
        val = math.sin(2.0 * math.pi * freq1 * t)
        env = min(1.0, i / max(1, attack_samples))
        samples.append(int(val * env * max_amp))

    # Tone 2 with 5ms decay envelope at the end
    decay_samples = int(sample_rate * 0.005)
    for i in range(n2):
        t = i / sample_rate
        val = math.sin(2.0 * math.pi * freq2 * t)
        rem = n2 - 1 - i
        env = min(1.0, rem / max(1, decay_samples))
        samples.append(int(val * env * max_amp))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        raw_pcm = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(raw_pcm)

    return buf.getvalue()


# Synthesize once at module import
SCANNER_BEEP_WAV: bytes = generate_scanner_beep_wav()


def play_scanner_beep(wav_bytes: bytes | None = None) -> None:
    """Play the synthesized scanner beep asynchronously without blocking or failing on modern Windows."""
    if not winsound:
        return

    data = wav_bytes or SCANNER_BEEP_WAV

    def _worker():
        try:
            # SND_MEMORY plays directly from RAM. Running in daemon thread ensures zero UI/worker delay.
            winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_NODEFAULT)
        except Exception:
            try:
                winsound.Beep(2200, 100)
            except Exception:
                pass

    threading.Thread(target=_worker, name="BinaryReceptor-AudioBeep", daemon=True).start()
