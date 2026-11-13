"""Dynamic QR Code generator and BinaryEye Deep Link helper for BinaryReceptor v3.0.0.

Provides:
  - Local LAN IP address auto-detection prioritizing active Wi-Fi and Ethernet interfaces.
  - Tab 1: Standard HTTP Forwarding URL (http://<LAN_IP>:<PORT>/).
  - Tab 2: 1-Scan Continuous Mode Deep Link (binaryeye://scan?continuous=true&callback=...).
  - Tab 3: Encode Text to Phone Barcode (binaryeye://encode?content=...&format=...&execute=true).
  - High-DPI QPixmap / PIL Image generation.
"""
from __future__ import annotations

import io
import socket
import urllib.parse
from typing import Any

import qrcode
from PIL import Image

try:
    import psutil
except ImportError:
    psutil = None

BINARYEYE_FORMATS = [
    "QR_CODE",
    "DATA_MATRIX",
    "AZTEC",
    "PDF_417",
    "CODE_128",
    "CODE_39",
    "EAN_13",
    "EAN_8",
    "UPC_A",
    "ITF",
    "CODABAR",
]


def get_active_lan_ips() -> list[dict[str, Any]]:
    """Detect and rank all active local IPv4 addresses.

    Prioritizes active Wi-Fi and Ethernet adapters with private LAN ranges
    (192.168.x.x, 10.x.x.x, 172.16-31.x.x) over APIPA (169.254.x.x) or virtual NICs.
    """
    results: list[dict[str, Any]] = []

    if psutil:
        try:
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()

            for iface_name, addr_list in addrs.items():
                is_up = stats.get(iface_name).isup if iface_name in stats else True
                for a in addr_list:
                    if a.family == socket.AF_INET:
                        ip = a.address
                        if ip.startswith("127."):
                            continue

                        # Score interfaces
                        score = 0
                        lower_name = iface_name.lower()
                        if "wi-fi" in lower_name or "wlan" in lower_name or "wireless" in lower_name:
                            score += 50
                        elif "ethernet" in lower_name or "eth" in lower_name or "lan" in lower_name:
                            score += 40

                        if ip.startswith(("192.168.", "10.")):
                            score += 30
                        elif ip.startswith("172."):
                            score += 20
                        elif ip.startswith("169.254."):
                            score -= 50  # APIPA fallback

                        if is_up:
                            score += 10

                        results.append({
                            "interface": iface_name,
                            "ip": ip,
                            "score": score,
                            "is_primary": False,
                        })
        except Exception:
            pass

    # Fallback to standard socket resolution if psutil returned nothing
    if not results:
        try:
            host_name = socket.gethostname()
            _, _, ip_list = socket.gethostbyname_ex(host_name)
            for ip in ip_list:
                if not ip.startswith("127."):
                    score = 20 if not ip.startswith("169.254.") else 0
                    results.append({
                        "interface": "Local Network",
                        "ip": ip,
                        "score": score,
                        "is_primary": False,
                    })
        except Exception:
            pass

    if not results:
        results.append({
            "interface": "Loopback",
            "ip": "127.0.0.1",
            "score": 0,
            "is_primary": True,
        })
    else:
        results.sort(key=lambda x: x["score"], reverse=True)
        results[0]["is_primary"] = True

    return results


def get_primary_lan_ip() -> str:
    """Return the single best LAN IPv4 address for QR encoding."""
    ips = get_active_lan_ips()
    return ips[0]["ip"] if ips else "127.0.0.1"


def build_forwarding_url(ip: str, port: int) -> str:
    """Build standard HTTP Forwarding URL: http://<IP>:<PORT>/."""
    clean_ip = ip.strip() or "127.0.0.1"
    return f"http://{clean_ip}:{port}/"


def build_continuous_scan_url(ip: str, port: int) -> str:
    """Build 1-scan BinaryEye continuous scan callback deep link.

    Format:
      binaryeye://scan?continuous=true&callback=http%3A%2F%2F<IP>%3A<PORT>%2Fscan
    """
    clean_ip = ip.strip() or "127.0.0.1"
    raw_callback = f"http://{clean_ip}:{port}/scan"
    encoded_callback = urllib.parse.quote(raw_callback, safe="")
    return f"binaryeye://scan?continuous=true&callback={encoded_callback}"


def build_encode_url(content: str, format_name: str = "QR_CODE") -> str:
    """Build BinaryEye barcode generation deep link.

    Format:
      binaryeye://encode?content=...&format=...&execute=true
    """
    clean_format = format_name.upper() if format_name.upper() in BINARYEYE_FORMATS else "QR_CODE"
    encoded_content = urllib.parse.quote(content, safe="")
    return f"binaryeye://encode?content={encoded_content}&format={clean_format}&execute=true"


def generate_qr_image(
    data: str,
    box_size: int = 8,
    border: int = 2,
    fill_color: str = "black",
    back_color: str = "white",
) -> Image.Image:
    """Generate PIL Image containing QR Code."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    return img.convert("RGBA")


def generate_qr_png_bytes(data: str, box_size: int = 8, border: int = 2) -> bytes:
    """Generate raw PNG bytes for a QR code."""
    img = generate_qr_image(data, box_size=box_size, border=border)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
