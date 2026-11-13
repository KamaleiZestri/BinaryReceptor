"""Bounded, threaded HTTP receiver compatible with BinaryEye forwarding."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Callable
from urllib.parse import parse_qs, unquote, urlsplit

BLUETOOTH_SERVICE_UUID = "8a847f2e-c9c6-451f-9973-8f56085d8e3c"
MAX_BODY_BYTES = 1_000_000

def extract(request_path: str, body: bytes, content_type: str) -> tuple[str, dict[str, str]]:
    parsed = urlsplit(request_path)
    params = parse_qs(parsed.query, keep_blank_values=True)
    meta: dict[str, str] = {}
    content = ""
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type == "application/json" or media_type.endswith("+json"):
        try:
            obj = json.loads(body.decode("utf-8-sig")) if body else {}
            if isinstance(obj, dict):
                content = str(obj.get("content", ""))
                meta = {str(k): str(v) for k, v in obj.items() if k != "content"}
                if not content and obj.get("raw"):
                    try: content = bytes.fromhex(str(obj["raw"])).decode("utf-8", "replace")
                    except ValueError: pass
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    elif media_type == "application/x-www-form-urlencoded":
        params.update(parse_qs(body.decode("utf-8", "replace"), keep_blank_values=True))
    elif body:
        content = body.decode("utf-8", "replace")
    if not content:
        for key in ("content", "code", "result"):
            if params.get(key): content = params[key][0]; break
    for key, values in params.items():
        if key not in {"content", "code", "result"} and values:
            meta.setdefault(key, values[0])
    if not content and parsed.path.strip("/") not in ("", "scan"):
        content = unquote(parsed.path.strip("/").split("/", 1)[0])
    if not content and parsed.query and "=" not in parsed.query:
        content = unquote(parsed.query)
    return content, meta

class ScanServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 32

def start_http(host: str, port: int, on_scan: Callable[[str, dict[str, str], str], None]) -> ScanServer:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        def do_GET(self) -> None: self.receive()
        def do_POST(self) -> None: self.receive()
        def receive(self) -> None:
            try: length = int(self.headers.get("Content-Length", "0"))
            except ValueError: length = -1
            if length < 0 or length > MAX_BODY_BYTES:
                self.send_response(413); self.send_header("Content-Length", "0"); self.end_headers(); return
            body = self.rfile.read(length) if length else b""
            content, meta = extract(self.path, body, self.headers.get("Content-Type", ""))
            if not content:
                self.send_response(400); self.send_header("Content-Length", "0"); self.end_headers(); return
            try:
                on_scan(content, meta, "HTTP")
            except Exception:
                self.send_response(500); self.send_header("Content-Length", "0"); self.end_headers(); return
            self.send_response(204); self.send_header("Content-Length", "0"); self.end_headers()
        def log_message(self, *_: object) -> None: pass
    server = ScanServer((host, port), Handler)
    Thread(target=server.serve_forever, name="binaryreceptor-http", daemon=True).start()
    return server
