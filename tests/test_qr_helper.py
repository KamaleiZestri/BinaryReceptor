"""Tests for dynamic QR Code generation and BinaryEye deep-link formatting."""
from __future__ import annotations

import io
from PIL import Image

from src.core.qr_helper import (
    build_forwarding_url,
    build_continuous_scan_url,
    build_encode_url,
    generate_qr_image,
    generate_qr_png_bytes,
    get_active_lan_ips,
    BINARYEYE_FORMATS,
)


def test_build_forwarding_url():
    url = build_forwarding_url("192.168.1.100", 24234)
    assert url == "http://192.168.1.100:24234/"


def test_build_continuous_scan_deep_link():
    """Verify BinaryEye native continuous scan callback deep-link format."""
    deep_link = build_continuous_scan_url("192.168.1.50", 24234)
    expected_prefix = "binaryeye://scan?continuous=true&callback="
    assert deep_link.startswith(expected_prefix)
    assert "http%3A%2F%2F192.168.1.50%3A24234%2Fscan" in deep_link


def test_build_encode_deep_link():
    """Verify BinaryEye encode deep link format across supported symbologies."""
    for fmt in ["QR_CODE", "CODE_128", "EAN_13", "DATA_MATRIX"]:
        assert fmt in BINARYEYE_FORMATS
        url = build_encode_url("MY-SECRET-CODE", fmt)
        assert url.startswith("binaryeye://encode?")
        assert "content=MY-SECRET-CODE" in url
        assert f"format={fmt}" in url
        assert "execute=true" in url


def test_qr_image_generation():
    """Verify QR code PIL image and PNG bytes are valid and decodable."""
    png_bytes = generate_qr_png_bytes("https://github.com/ouncommono/BinaryReceptor")
    assert len(png_bytes) > 100
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    img = Image.open(io.BytesIO(png_bytes))
    assert img.size[0] > 50
    assert img.size[1] > 50


def test_lan_ip_detection():
    """Verify active LAN IP detection returns at least one valid address entry."""
    ips = get_active_lan_ips()
    assert len(ips) >= 1
    assert any(ip["is_primary"] for ip in ips)
