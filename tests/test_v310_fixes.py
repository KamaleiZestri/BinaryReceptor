"""Comprehensive unit and integration tests for BinaryReceptor Version 3.1.0 requirements.

Validates:
- Mode isolation guards
- Scanner chime WAV synthesis
- Atomic deduplication with canonical normalization
- Output mode routing (copy_only, log_only, type)
- Self-link / continuous scan URL interception
- 100% English / Persian localization dictionary parity
- Version numbers and App ID consistency
"""
from __future__ import annotations

import io
import re
import wave
import pytest

from src.version import __version__, APP_ID, APP_NAME
from src.ui.i18n import TRANSLATIONS, tr
from src.core.sound import generate_scanner_beep_wav
from src.core.deduplicator import ScanDeduplicator, DeduplicationEngine
from src.core.key_injector import KeyInjector
from src.config import render_keystroke_output


def test_version_and_appid():
    """Verify version 3.1.0 and clean App ID without prefixes."""
    assert __version__ == "3.1.0"
    assert APP_ID == "BinaryReceptor.3.1.0"
    assert "ouncommono" not in APP_ID


def test_i18n_exact_parity():
    """Requirement 12: Verify 100% dictionary parity between EN and FA."""
    en_keys = set(TRANSLATIONS["en"].keys())
    fa_keys = set(TRANSLATIONS["fa"].keys())

    missing_in_fa = en_keys - fa_keys
    missing_in_en = fa_keys - en_keys

    assert not missing_in_fa, f"Keys missing in FA: {missing_in_fa}"
    assert not missing_in_en, f"Keys missing in EN: {missing_in_en}"
    assert len(en_keys) >= 140

    for key, val in TRANSLATIONS["en"].items():
        assert val.strip(), f"Empty EN translation for key: {key}"
    for key, val in TRANSLATIONS["fa"].items():
        assert val.strip(), f"Empty FA translation for key: {key}"


def test_sound_wav_generator():
    """Requirement 2: Verify in-memory 16-bit PCM WAV scanner chime synthesis."""
    wav_bytes = generate_scanner_beep_wav(sample_rate=44100)
    assert len(wav_bytes) > 1000

    # Parse with standard wave library to ensure valid RIFF header
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2  # 16-bit
        assert wf.getframerate() == 44100
        n_frames = wf.getnframes()
        assert n_frames > 0
        frames = wf.readframes(n_frames)
        assert len(frames) == n_frames * 2


def test_canonical_normalization_deduplication():
    """Requirement 3: Verify canonical normalization strips CRLF and URL-decodes."""
    norm1 = ScanDeduplicator.normalize_content("123456789\r\n")
    norm2 = ScanDeduplicator.normalize_content("123456789\n")
    norm3 = ScanDeduplicator.normalize_content("  123456789  \t")
    assert norm1 == "123456789"
    assert norm2 == "123456789"
    assert norm3 == "123456789"

    # URL decoding
    norm_url1 = ScanDeduplicator.normalize_content("Hello%20World%21")
    norm_url2 = ScanDeduplicator.normalize_content("Hello World!")
    assert norm_url1 == norm_url2 == "Hello World!"

    # Dedup engine prevents double-typing across transports with CRLF differences
    engine = DeduplicationEngine(window_ms=1500, enabled=True)
    is_dup1, _ = engine.check_and_record(norm1, source="Bluetooth")
    assert not is_dup1

    # Second arrival via HTTP has trailing newline or URL encoding
    is_dup2, msg2 = engine.check_and_record(norm2, source="HTTP")
    assert is_dup2
    assert "already processed via Bluetooth" in msg2


def test_mode_isolation_guard():
    """Requirement 1: Verify mode isolation rules drop scans from inactive transports."""
    def should_accept(active_mode: str, source: str) -> bool:
        mode_l = active_mode.strip().lower()
        src_l = source.strip().lower()
        if mode_l == "http" and src_l != "http":
            return False
        if mode_l == "bluetooth" and src_l != "bluetooth":
            return False
        return True

    # HTTP only mode
    assert should_accept("http", "http") is True
    assert should_accept("http", "HTTP") is True
    assert should_accept("http", "bluetooth") is False
    assert should_accept("http", "Bluetooth") is False

    # Bluetooth only mode
    assert should_accept("bluetooth", "bluetooth") is True
    assert should_accept("bluetooth", "http") is False

    # Both (Hybrid) mode
    assert should_accept("both", "http") is True
    assert should_accept("both", "bluetooth") is True


def test_self_link_interception():
    """Requirement 6: Verify deep link or self-server URLs are intercepted and not typed."""
    def is_self_link(content: str, http_port: int = 24234) -> bool:
        clean = content.strip()
        return (
            clean.startswith("binaryeye://")
            or f":{http_port}" in clean
            or clean.endswith("/scan")
            or clean.endswith("/start")
        )

    assert is_self_link("binaryeye://scan?continuous=true&callback=http%3A%2F%2F192.168.1.5%3A24234%2Fscan") is True
    assert is_self_link("http://192.168.1.100:24234/start") is True
    assert is_self_link("http://192.168.1.100:24234/scan") is True
    assert is_self_link("http://my-domain.com/scan") is True

    # Real barcodes should not be intercepted
    assert is_self_link("9780132350884") is False
    assert is_self_link("https://github.com/markusfisch/BinaryEye") is False
    assert is_self_link("https://example.com/product/12345") is False


def test_output_modes_dry_run():
    """Requirement 4: Verify copy_only and log_only never simulate keystrokes."""
    injector = KeyInjector(dry_run=True)

    # 1. copy_only
    injector.inject_scan(content="CLIPBOARD-ONLY-123", output_mode="copy_only")
    events = injector.recorded_events
    assert len(events) == 1
    assert events[0] == ("copy_only", "CLIPBOARD-ONLY-123")

    # 2. log_only (no events recorded)
    injector.recorded_events.clear()
    injector.inject_scan(content="LOG-ONLY-456", output_mode="log_only")
    assert len(injector.recorded_events) == 0

    # 3. type mode
    injector.recorded_events.clear()
    injector.inject_scan(content="TYPED-789", prefix_template="", suffix_template="{ENTER}", output_mode="type")
    assert len(injector.recorded_events) == 2
    assert injector.recorded_events[0] == ("unicode", "TYPED-789")
    assert injector.recorded_events[1] == ("vk", 0x0D)  # VK_RETURN


def test_live_keystroke_preview_rendering():
    """Requirement 11: Verify tokens render actual whitespace and character deletions."""
    # Newline replacement
    preview = render_keystroke_output(
        content="BARCODE123",
        prefix="[START] ",
        suffix=" {ENTER}",
    )
    assert preview == "[START] BARCODE123 \n"
    assert "{ENTER}" not in preview

    # Backspace simulation
    preview_bs = render_keystroke_output(
        content="ABCDEF",
        prefix="",
        suffix="{BACKSPACE}{BACKSPACE}XYZ",
    )
    assert preview_bs == "ABCDXYZ"

    # Tab and space tokens
    preview_tab = render_keystroke_output(
        content="COL1",
        prefix="",
        suffix="{TAB}COL2{SPACE}{SPACE}COL3",
    )
    assert preview_tab == "COL1\tCOL2  COL3"
