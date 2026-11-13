from __future__ import annotations

import tempfile
import time
import unittest
from threading import Event
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen

from binaryreceptor.config import ConfigManager
from binaryreceptor.dedupe import Deduplicator
from binaryreceptor.transport import extract
from binaryreceptor.typing_win import type_template

class ConfigTests(unittest.TestCase):
    def test_external_settings_override_defaults_and_reload(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.ini"
            path.write_text("[app]\nmode = http\nport = 8080\n", encoding="utf-8")
            manager = ConfigManager(path)
            self.assertEqual((manager.current.mode, manager.current.port), ("http", 8080))
            self.assertIn("dedup_window_ms = 1500", path.read_text(encoding="utf-8"))
            time.sleep(0.02)
            path.write_text("[app]\nmode = both\nport = 8181\n", encoding="utf-8")
            self.assertEqual((manager.reload_if_changed().mode, manager.current.port), ("both", 8181))

class DedupeTests(unittest.TestCase):
    def test_suppresses_same_payload_within_window(self) -> None:
        dedupe = Deduplicator(1500)
        self.assertTrue(dedupe.accept("  12345 "))
        self.assertFalse(dedupe.accept("12345"))
        self.assertTrue(Deduplicator(0).accept("12345"))

class TransportTests(unittest.TestCase):
    def test_get_form_json_raw_and_root_path(self) -> None:
        self.assertEqual(extract("/?content=abc&format=QRCode", b"", "")[0], "abc")
        content, meta = extract("/scan", b"content=hello+world&format=EAN13", "application/x-www-form-urlencoded")
        self.assertEqual((content, meta.get("format")), ("hello world", "EAN13"))
        content, meta = extract("/", b'{"content":"123","format":"QRCode","raw":"313233"}', "application/json")
        self.assertEqual((content, meta["format"], meta["raw"]), ("123", "QRCode", "313233"))
        self.assertEqual(extract("/", b'{"raw":"313233"}', "application/json")[0], "123")
        self.assertEqual(extract("/", b"raw scan", "text/plain")[0], "raw scan")

    def test_http_post_accepts_binaryeye_json(self) -> None:
        from binaryreceptor.transport import start_http
        received = Event()
        scans: list[tuple[str, dict[str, str], str]] = []
        server = start_http("127.0.0.1", 0, lambda content, meta, source: (scans.append((content, meta, source)), received.set()))
        try:
            request = Request(f"http://127.0.0.1:{server.server_port}/scan", data=b'{"content":"SKU-17","format":"Code128","scanId":"abc"}', headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=2) as response:
                self.assertEqual(response.status, 204)
            self.assertTrue(received.wait(2))
            self.assertEqual(scans[0], ("SKU-17", {"format": "Code128", "scanId": "abc"}, "HTTP"))
        finally:
            server.shutdown(); server.server_close()

class TokenTests(unittest.TestCase):
    def test_tokens_map_to_native_key_events(self) -> None:
        with patch("binaryreceptor.typing_win._send") as send:
            type_template("A{ENTER}{TAB}{SPACE}{BACKSPACE}{ESC}")
        keys = [call.kwargs.get("vk") for call in send.call_args_list]
        self.assertEqual(keys[2:10], [0x0D, 0x0D, 0x09, 0x09, 0x20, 0x20, 0x08, 0x08])
        self.assertEqual(keys[10:12], [0x1B, 0x1B])

if __name__ == "__main__":
    unittest.main()
