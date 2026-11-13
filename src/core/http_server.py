"""Universal fault-tolerant HTTP companion server for BinaryEye in BinaryReceptor v3.0.0.

Accepts requests on ANY path (/*) and ANY HTTP method (GET, POST, PUT, OPTIONS).
Guarantees sub-millisecond HTTP 200 OK responses to respect BinaryEye's strict timeouts,
dispatching payload extraction to a thread-safe worker queue.

Supports all 5 BinaryEye forwarding cases:
  - Case A: JSON POST (JSON Forwarding & Continuous Scan Callbacks)
  - Case B: Query Parameter Key-Value pairs (?content=... / ?result=... / ?q=...)
  - Case C: Raw Query String (/?ScannedBarcodeText)
  - Case D: Raw URL Path (/ScannedBarcodeText or /scan/ScannedBarcodeText)
  - Case E: Form-Urlencoded & Raw UTF-8 POST Body
  - Health/Status Endpoint (/ and /health with no payload)
"""
from __future__ import annotations

import json
import logging
import queue
import socket
import urllib.parse
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread
from typing import Callable, Any

from src.version import __version__, APP_NAME

logger = logging.getLogger("BinaryReceptor.HTTP")

CONTENT_PARAM_KEYS = {
    "content",
    "result",
    "text",
    "data",
    "code",
    "barcode",
    "q",
    "msg",
    "payload",
    "val",
    "value",
}

FORMAT_PARAM_KEYS = {"format", "symbology", "type"}
RAW_PARAM_KEYS = {"raw", "result_bytes", "bytes"}
SCAN_ID_KEYS = {"scanid", "scan_id", "id", "uuid"}


@dataclass
class ScanPayload:
    content: str
    format: str = ""
    raw: str = ""
    scan_id: str | None = None
    source: str = "HTTP"
    client_address: str = ""
    headers: dict[str, str] = field(default_factory=dict)


def parse_binaryeye_request(
    method: str,
    path_and_query: str,
    headers: dict[str, str],
    body_bytes: bytes,
    client_ip: str = "",
) -> tuple[ScanPayload | None, bool]:
    """Parse HTTP request according to all 5 BinaryEye transport protocols.

    Returns:
        (scan_payload, is_health_check)
    """
    parsed_url = urllib.parse.urlsplit(path_and_query)
    path = parsed_url.path
    query_str = parsed_url.query

    content: str | None = None
    fmt: str = ""
    raw_bytes_str: str = ""
    scan_id: str | None = None

    content_type = headers.get("content-type", "").lower()

    # --------------------------------------------------------------------------
    # Case A: JSON POST Body (BinaryEye JSON Forwarding & Continuous Callback)
    # --------------------------------------------------------------------------
    if method in ("POST", "PUT") and ("application/json" in content_type or (body_bytes and body_bytes.lstrip().startswith(b"{"))):
        try:
            body_text = body_bytes.decode("utf-8", errors="replace")
            data = json.loads(body_text)
            if isinstance(data, dict):
                # Search for content
                for k, v in data.items():
                    lk = k.lower()
                    if lk in CONTENT_PARAM_KEYS and isinstance(v, (str, int, float)):
                        content = str(v)
                    elif lk in FORMAT_PARAM_KEYS and isinstance(v, str):
                        fmt = v
                    elif lk in RAW_PARAM_KEYS and isinstance(v, str):
                        raw_bytes_str = v
                    elif lk in SCAN_ID_KEYS and isinstance(v, (str, int)):
                        scan_id = str(v)
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Case B: Query Parameters (GET or POST ?content=... / ?result=...)
    # --------------------------------------------------------------------------
    if content is None and query_str and "=" in query_str:
        try:
            qs_dict = urllib.parse.parse_qs(query_str, keep_blank_values=False)
            for k, val_list in qs_dict.items():
                if not val_list:
                    continue
                lk = k.lower()
                val = val_list[0]
                if lk in CONTENT_PARAM_KEYS:
                    content = val
                elif lk in FORMAT_PARAM_KEYS:
                    fmt = val
                elif lk in RAW_PARAM_KEYS:
                    raw_bytes_str = val
                elif lk in SCAN_ID_KEYS:
                    scan_id = val
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Case C: Raw Query String (GET /?ScannedBarcodeText without = key-value)
    # --------------------------------------------------------------------------
    if content is None and query_str and "=" not in query_str:
        unquoted = urllib.parse.unquote_plus(query_str).strip()
        if unquoted:
            content = unquoted

    # --------------------------------------------------------------------------
    # Case E: Form-Urlencoded or Raw Body (POST / PUT)
    # --------------------------------------------------------------------------
    if content is None and method in ("POST", "PUT") and body_bytes:
        body_text = body_bytes.decode("utf-8", errors="replace").strip()
        if "application/x-www-form-urlencoded" in content_type and "=" in body_text:
            try:
                form_dict = urllib.parse.parse_qs(body_text, keep_blank_values=False)
                for k, val_list in form_dict.items():
                    if not val_list:
                        continue
                    lk = k.lower()
                    val = val_list[0]
                    if lk in CONTENT_PARAM_KEYS:
                        content = val
                    elif lk in FORMAT_PARAM_KEYS:
                        fmt = val
                    elif lk in SCAN_ID_KEYS:
                        scan_id = val
            except Exception:
                pass

        # If not parsed as form, treat whole non-empty body as raw text
        if content is None and body_text:
            content = body_text

    # --------------------------------------------------------------------------
    # Case D: Raw URL Path (GET /ScannedContent or GET /scan/ScannedContent)
    # --------------------------------------------------------------------------
    clean_path = path.strip("/")
    if clean_path.lower().startswith("scan/"):
        clean_path = clean_path[5:].strip("/")

    is_health = (clean_path.lower() in ("", "health", "status", "ping", "favicon.ico", "start") and not query_str and not body_bytes)

    if content is None and not is_health and clean_path:
        # BinaryEye "GET and simply append content" mode
        unquoted_path = urllib.parse.unquote(clean_path).strip()
        if unquoted_path and unquoted_path.lower() not in ("health", "status", "ping", "favicon.ico", "start"):
            content = unquoted_path

    if content is not None:
        return (
            ScanPayload(
                content=content,
                format=fmt,
                raw=raw_bytes_str,
                scan_id=scan_id,
                source="HTTP",
                client_address=client_ip,
                headers=headers,
            ),
            False,
        )

    return None, is_health


class BinaryReceptorHTTPHandler(BaseHTTPRequestHandler):
    """Zero-latency request handler returning immediate 200 OK to BinaryEye."""

    server: "BinaryReceptorHTTPServer"

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stderr HTTP request logging for quiet operation."""
        pass

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Connection", "close")

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests immediately."""
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")

    def _handle_any_request(self) -> None:
        # Check for /start landing page
        parsed_url = urllib.parse.urlsplit(self.path)
        clean_path = parsed_url.path.strip("/")
        if self.command == "GET" and clean_path.lower() == "start":
            host_header = self.headers.get("host") or f"{self.server.server_address[0]}:{self.server.server_address[1]}"
            deep_link = f"binaryeye://scan?continuous=true&callback=http%3A%2F%2F{urllib.parse.quote(host_header, safe='')}%2Fscan"
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BinaryReceptor - BinaryEye Launch</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; text-align: center; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 32px 24px; max-width: 440px; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
    h1 {{ font-size: 24px; margin-bottom: 8px; color: #38bdf8; }}
    p {{ font-size: 15px; color: #94a3b8; line-height: 1.5; margin-bottom: 24px; }}
    .btn {{ display: inline-block; background: #10b981; color: #ffffff; text-decoration: none; font-size: 18px; font-weight: bold; padding: 14px 28px; border-radius: 12px; transition: background 0.2s; box-shadow: 0 4px 12px rgba(16,185,129,0.4); }}
    .btn:hover {{ background: #059669; }}
    .info {{ margin-top: 24px; font-size: 12px; color: #64748b; word-break: break-all; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>BinaryReceptor v{__version__}</h1>
    <p>Tap the button below to launch <strong>BinaryEye</strong> on your phone in continuous scan forwarding mode.</p>
    <a href="{deep_link}" class="btn">🚀 Start Continuous Scan</a>
    <div class="info">Target: http://{host_header}/scan</div>
  </div>
</body>
</html>"""
            html_bytes = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                self.wfile.write(html_bytes)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        # 1. Read request body if present
        body_bytes = b""
        try:
            content_length = int(self.headers.get("content-length", 0))
            if content_length > 0:
                body_bytes = self.rfile.read(min(content_length, 2 * 1024 * 1024))  # 2MB limit
        except Exception:
            body_bytes = b""

        # 2. Extract header map
        header_map = {k.lower(): v for k, v in self.headers.items()}
        client_ip = self.client_address[0] if self.client_address else "unknown"

        # 3. Parse payload
        payload, is_health = parse_binaryeye_request(
            method=self.command,
            path_and_query=self.path,
            headers=header_map,
            body_bytes=body_bytes,
            client_ip=client_ip,
        )

        # 4. Dispatch scan to worker queue without waiting for typing
        if payload is not None:
            self.server.dispatch_scan(payload)

        # 5. Build clean, instant HTTP 200 OK response with exact Content-Length
        status_data = {
            "status": "ok",
            "app": APP_NAME,
            "version": __version__,
            "mode": "ready",
        }
        if payload is not None and payload.scan_id:
            status_data["scanId"] = payload.scan_id
        response_bytes = (json.dumps(status_data) + "\n").encode("utf-8")
        content_type = "application/json; charset=utf-8"

        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(response_bytes)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self) -> None:
        self._handle_any_request()

    def do_POST(self) -> None:
        self._handle_any_request()

    def do_PUT(self) -> None:
        self._handle_any_request()

    def do_HEAD(self) -> None:
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()


class BinaryReceptorHTTPServer(ThreadingHTTPServer):
    """Threaded HTTP Server designed for high-concurrency BinaryEye webhook traffic."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        on_scan: Callable[[ScanPayload], None],
    ) -> None:
        self.on_scan = on_scan
        super().__init__(server_address, BinaryReceptorHTTPHandler)

    def dispatch_scan(self, payload: ScanPayload) -> None:
        try:
            self.on_scan(payload)
        except Exception:
            logger.exception("Error in HTTP on_scan callback")


class HttpServerController:
    """Manages the background execution, lifecycle, and health of the HTTP server."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 24234,
        on_scan: Callable[[ScanPayload], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.on_scan = on_scan or (lambda p: None)

        self._server: BinaryReceptorHTTPServer | None = None
        self._thread: Thread | None = None
        self._is_running = Event()
        self._last_error: str | None = None

    @property
    def is_running(self) -> bool:
        return self._is_running.is_set()

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def start(self) -> tuple[bool, str]:
        """Start the threaded HTTP server in the background."""
        if self.is_running:
            return True, f"HTTP server already running on {self.host}:{self.port}"

        self._last_error = None
        try:
            self._server = BinaryReceptorHTTPServer(
                (self.host, self.port),
                on_scan=self.on_scan,
            )
        except OSError as e:
            self._last_error = f"Cannot bind to {self.host}:{self.port} - {e}"
            return False, self._last_error

        def _serve():
            self._is_running.set()
            try:
                self._server.serve_forever()
            except Exception:
                pass
            finally:
                self._is_running.clear()

        self._thread = Thread(target=_serve, name="BinaryReceptor-HTTP", daemon=True)
        self._thread.start()
        return True, f"HTTP server active on {self.host}:{self.port}"

    def stop(self) -> None:
        """Gracefully shut down the HTTP server."""
        if not self.is_running or not self._server:
            return

        srv = self._server
        self._server = None

        def _shutdown():
            try:
                srv.shutdown()
                srv.server_close()
            except Exception:
                pass

        shutdown_thread = Thread(target=_shutdown, name="BinaryReceptor-HTTP-Stop", daemon=True)
        shutdown_thread.start()
        shutdown_thread.join(timeout=2.0)
        self._is_running.clear()
