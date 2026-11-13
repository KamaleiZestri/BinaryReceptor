"""Tests for Universal BinaryEye HTTP protocol compatibility across all 5 forwarding structures."""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.parse
import pytest

from src.core.http_server import (
    parse_binaryeye_request,
    HttpServerController,
    ScanPayload,
)


# ------------------------------------------------------------------------------
# Unit tests for parse_binaryeye_request
# ------------------------------------------------------------------------------

def test_case_a_json_post():
    """Case A: BinaryEye JSON Forwarding and Continuous Scan callback payload."""
    payload_json = json.dumps({
        "content": "HELLO-BINARYEYE-2026",
        "format": "QR_CODE",
        "raw": "SEVMTE8tQklOQVJZRVRFLTIwMjY=",
        "scanId": "scan-uuid-42",
    }).encode("utf-8")

    headers = {"content-type": "application/json"}
    payload, is_health = parse_binaryeye_request("POST", "/scan", headers, payload_json)

    assert not is_health
    assert payload is not None
    assert payload.content == "HELLO-BINARYEYE-2026"
    assert payload.format == "QR_CODE"
    assert payload.scan_id == "scan-uuid-42"
    assert payload.raw == "SEVMTE8tQklOQVJZRVRFLTIwMjY="


def test_case_b_query_parameters_get():
    """Case B: Query parameters (?content=... / ?result=... / ?q=...)."""
    headers = {}
    payload, is_health = parse_binaryeye_request(
        "GET",
        "/?content=EAN13-9780123456789&format=EAN_13&scanId=101",
        headers,
        b"",
    )

    assert not is_health
    assert payload is not None
    assert payload.content == "EAN13-9780123456789"
    assert payload.format == "EAN_13"
    assert payload.scan_id == "101"


def test_case_b_query_parameters_result_alias():
    """Case B with 'result' alias."""
    headers = {}
    payload, is_health = parse_binaryeye_request("GET", "/scan?result=ABC-XYZ-99", headers, b"")

    assert not is_health
    assert payload is not None
    assert payload.content == "ABC-XYZ-99"


def test_case_c_raw_query_string():
    """Case C: Raw query string with no key-value separator (GET /?ScannedBarcode)."""
    headers = {}
    payload, is_health = parse_binaryeye_request("GET", "/?MY_RAW_BARCODE_TEXT%20123", headers, b"")

    assert not is_health
    assert payload is not None
    assert payload.content == "MY_RAW_BARCODE_TEXT 123"


def test_case_d_raw_url_path():
    """Case D: Raw URL Path (BinaryEye 'GET and simply add content' mode)."""
    headers = {}
    payload1, is_health1 = parse_binaryeye_request("GET", "/123456789012", headers, b"")
    assert not is_health1
    assert payload1 is not None
    assert payload1.content == "123456789012"

    payload2, is_health2 = parse_binaryeye_request("GET", "/scan/BARCODE-PREFIX-88", headers, b"")
    assert not is_health2
    assert payload2 is not None
    assert payload2.content == "BARCODE-PREFIX-88"


def test_case_e_form_urlencoded_post():
    """Case E: Form-Urlencoded POST body."""
    body = b"content=FORM_BARCODE_DATA&format=CODE_128"
    headers = {"content-type": "application/x-www-form-urlencoded"}
    payload, is_health = parse_binaryeye_request("POST", "/", headers, body)

    assert not is_health
    assert payload is not None
    assert payload.content == "FORM_BARCODE_DATA"
    assert payload.format == "CODE_128"


def test_case_e_raw_utf8_post_body():
    """Case E: Raw plain text body POST."""
    body = "Direct raw barcode text over HTTP POST".encode("utf-8")
    headers = {"content-type": "text/plain"}
    payload, is_health = parse_binaryeye_request("POST", "/", headers, body)

    assert not is_health
    assert payload is not None
    assert payload.content == "Direct raw barcode text over HTTP POST"


def test_health_check_endpoint():
    """Health check endpoints return is_health=True and no barcode payload."""
    payload1, is_health1 = parse_binaryeye_request("GET", "/", {}, b"")
    assert is_health1
    assert payload1 is None

    payload2, is_health2 = parse_binaryeye_request("GET", "/health", {}, b"")
    assert is_health2
    assert payload2 is None


# ------------------------------------------------------------------------------
# End-to-end integration test with live server
# ------------------------------------------------------------------------------

def test_live_http_server_dispatch_and_latency():
    """Test actual live HTTP server returning 200 OK in <50ms and dispatching payload."""
    received_scans: list[ScanPayload] = []

    server = HttpServerController(
        host="127.0.0.1",
        port=24299,  # Test port
        on_scan=lambda p: received_scans.append(p),
    )

    started, msg = server.start()
    assert started, msg

    try:
        # Give server a moment to bind
        time.sleep(0.15)

        # 1. Health check GET
        req_health = urllib.request.Request("http://127.0.0.1:24299/health")
        with urllib.request.urlopen(req_health, timeout=2.0) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert data["mode"] == "ready"

        # 2. Case A JSON POST
        json_data = json.dumps({"content": "LIVE-TEST-123", "format": "QR_CODE", "scanId": "s-1"}).encode("utf-8")
        req_post = urllib.request.Request(
            "http://127.0.0.1:24299/scan",
            data=json_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        t0 = time.perf_counter()
        with urllib.request.urlopen(req_post, timeout=2.0) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert data["scanId"] == "s-1"
            assert elapsed_ms < 50.0  # Fast sub-50ms response

        # Wait briefly for worker callback
        time.sleep(0.1)
        assert len(received_scans) == 1
        assert received_scans[0].content == "LIVE-TEST-123"
        assert received_scans[0].scan_id == "s-1"

    finally:
        server.stop()
