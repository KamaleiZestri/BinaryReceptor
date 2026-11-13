"""Thread-safe sliding time-window deduplication engine for BinaryReceptor v3.1.0."""
from __future__ import annotations

import hashlib
import threading
import time
import urllib.parse
from dataclasses import dataclass


@dataclass
class DedupRecord:
    timestamp: float
    source: str
    scan_id: str | None
    content_hash: str


class ScanDeduplicator:
    """Thread-safe sliding time-window deduplication engine.

    Prevents double-typing when BinaryEye forwards identical barcodes simultaneously
    over Bluetooth and HTTP or re-transmits unacknowledged packets.
    """

    def __init__(self, window_ms: int = 1500, enabled: bool = True) -> None:
        self._lock = threading.Lock()
        self.window_ms = window_ms
        self.enabled = enabled

        # Cache mapping key -> DedupRecord
        self._cache: dict[str, DedupRecord] = {}

        # Running statistics
        self.total_received = 0
        self.duplicates_blocked = 0

    def update_settings(self, window_ms: int, enabled: bool) -> None:
        """Update window duration and toggle state safely."""
        with self._lock:
            self.window_ms = max(50, min(60000, window_ms))
            self.enabled = enabled

    @staticmethod
    def normalize_content(content: str) -> str:
        """Extract canonical normalized barcode text, tolerating URL encoding and CRLF delimiters."""
        if not content:
            return ""
        # Strip trailing/leading CRLF, tabs, spaces
        cleaned = content.strip("\r\n\t ")
        if "%" in cleaned:
            try:
                unquoted = urllib.parse.unquote_plus(cleaned)
                if unquoted:
                    cleaned = unquoted.strip("\r\n\t ")
            except Exception:
                pass
        return cleaned

    @classmethod
    def hash_content(cls, content: str) -> str:
        """Compute SHA-256 digest of normalized barcode text."""
        canonical = cls.normalize_content(content)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def check_and_record(
        self,
        content: str,
        source: str = "HTTP",
        scan_id: str | None = None,
    ) -> tuple[bool, str]:
        """Check if scan is a duplicate within the sliding time window.

        Returns:
            (is_duplicate, detail_message)
            If is_duplicate is True, the scan was already processed and should be suppressed.
            If False, the scan is new and was recorded in the cache.
        """
        now = time.monotonic()
        canonical = self.normalize_content(content)
        content_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        window_sec = self.window_ms / 1000.0

        with self._lock:
            self.total_received += 1

            if not self.enabled:
                return False, "Deduplication disabled"

            # 1. Prune expired entries from cache
            expired_keys = [k for k, rec in self._cache.items() if (now - rec.timestamp) > window_sec]
            for k in expired_keys:
                del self._cache[k]

            # 2. Check by scanId if provided
            if scan_id and scan_id.strip():
                clean_scan_id = scan_id.strip()
                scan_key = f"scanid:{clean_scan_id}"
                if scan_key in self._cache:
                    prev = self._cache[scan_key]
                    delta_ms = int((now - prev.timestamp) * 1000)
                    self.duplicates_blocked += 1
                    msg = (
                        f"[Duplicate Suppressed] Ignored duplicate scanId '{clean_scan_id}' via {source} "
                        f"(already processed via {prev.source} {delta_ms}ms ago)"
                    )
                    return True, msg

            # 3. Check by content hash
            hash_key = f"hash:{content_hash}"
            if hash_key in self._cache:
                prev = self._cache[hash_key]
                delta_ms = int((now - prev.timestamp) * 1000)
                self.duplicates_blocked += 1
                msg = (
                    f"[Duplicate Suppressed] Ignored duplicate scan via {source} "
                    f"(already processed via {prev.source} {delta_ms}ms ago)"
                )
                return True, msg

            # 4. Not duplicate: record in cache atomically
            record = DedupRecord(
                timestamp=now,
                source=source,
                scan_id=scan_id.strip() if scan_id else None,
                content_hash=content_hash,
            )
            self._cache[hash_key] = record
            if scan_id and scan_id.strip():
                self._cache[f"scanid:{scan_id.strip()}"] = record

            return False, f"Accepted from {source}"

    def reset_stats(self) -> None:
        """Reset counters and clear sliding window cache."""
        with self._lock:
            self._cache.clear()
            self.total_received = 0
            self.duplicates_blocked = 0

    @property
    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "total_received": self.total_received,
                "duplicates_blocked": self.duplicates_blocked,
                "active_entries": len(self._cache),
            }


# Backward-compatible alias
DeduplicationEngine = ScanDeduplicator
