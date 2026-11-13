"""Tests for thread-safe sliding time-window deduplication engine."""
from __future__ import annotations

import concurrent.futures
import time
import pytest

from src.core.deduplicator import DeduplicationEngine


def test_content_hash_deduplication():
    engine = DeduplicationEngine(window_ms=1000, enabled=True)

    # First arrival via Bluetooth
    is_dup1, msg1 = engine.check_and_record("123456789", source="Bluetooth")
    assert not is_dup1
    assert "Accepted" in msg1

    # Immediate second arrival via HTTP
    is_dup2, msg2 = engine.check_and_record("123456789", source="HTTP")
    assert is_dup2
    assert "already processed via Bluetooth" in msg2

    stats = engine.stats
    assert stats["total_received"] == 2
    assert stats["duplicates_blocked"] == 1


def test_scan_id_deduplication():
    engine = DeduplicationEngine(window_ms=1000, enabled=True)

    # Same scanId arrived twice
    is_dup1, _ = engine.check_and_record("PRODUCT-A", source="HTTP", scan_id="scan-xyz-01")
    assert not is_dup1

    is_dup2, msg2 = engine.check_and_record("PRODUCT-A", source="Bluetooth", scan_id="scan-xyz-01")
    assert is_dup2
    assert "Ignored duplicate scanId 'scan-xyz-01'" in msg2


def test_sliding_window_expiration():
    engine = DeduplicationEngine(window_ms=150, enabled=True)

    is_dup1, _ = engine.check_and_record("EXPIRING-BARCODE", source="HTTP")
    assert not is_dup1

    # Within 150ms -> duplicate
    is_dup2, _ = engine.check_and_record("EXPIRING-BARCODE", source="HTTP")
    assert is_dup2

    # Sleep longer than window
    time.sleep(0.22)

    # After window -> accepted again
    is_dup3, _ = engine.check_and_record("EXPIRING-BARCODE", source="HTTP")
    assert not is_dup3


def test_disabled_deduplication():
    engine = DeduplicationEngine(window_ms=1000, enabled=False)

    is_dup1, _ = engine.check_and_record("REPEAT", source="HTTP")
    assert not is_dup1

    is_dup2, _ = engine.check_and_record("REPEAT", source="Bluetooth")
    assert not is_dup2


def test_thread_safety_concurrent_simultaneous_arrival():
    """Simulate simultaneous arrival across 10 concurrent threads."""
    engine = DeduplicationEngine(window_ms=1500, enabled=True)
    barcode = "SIMULTANEOUS-SCAN-999"

    results = []

    def _worker(thread_id: int):
        source = "Bluetooth" if thread_id % 2 == 0 else "HTTP"
        is_dup, msg = engine.check_and_record(barcode, source=source)
        return is_dup

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_worker, i) for i in range(10)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    # Exactly 1 thread must be accepted, 9 threads must be marked duplicate
    accepted = [r for r in results if not r]
    duplicates = [r for r in results if r]
    assert len(accepted) == 1
    assert len(duplicates) == 9
    assert engine.duplicates_blocked == 9
