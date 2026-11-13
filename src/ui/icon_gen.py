"""Multi-resolution icon generator and manager for BinaryReceptor v3.0.0.

Generates high-DPI multi-resolution Windows .ico files (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
featuring a modern cybernetic barcode / optical scanner motif with status beacons.
"""
from __future__ import annotations

import io
from pathlib import Path
from PIL import Image, ImageDraw

ICON_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def render_app_icon(size: int = 256, status_badge: str | None = None) -> Image.Image:
    """Render a crisp vector-style scanner icon at the requested pixel resolution."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = int(size * 0.08)
    corner = int(size * 0.20)
    w = size - 2 * pad
    h = size - 2 * pad

    # 1. Rounded container card (Dark slate blue with border)
    # Background card
    draw.rounded_rectangle(
        [pad, pad, pad + w, pad + h],
        radius=corner,
        fill=(15, 23, 42, 255),       # Slate 900
        outline=(59, 130, 246, 255),  # Vibrant Blue 500
        width=max(1, int(size * 0.035)),
    )

    # 2. Barcode vertical bars
    bar_top = int(size * 0.28)
    bar_bottom = int(size * 0.72)
    left_x = int(size * 0.22)
    right_x = int(size * 0.78)
    total_w = right_x - left_x

    # Proportional bar widths: narrow (1 unit), wide (2.2 units)
    bar_defs = [
        (0.00, 0.08, (241, 245, 249)),
        (0.13, 0.05, (203, 213, 225)),
        (0.23, 0.12, (241, 245, 249)),
        (0.40, 0.06, (203, 213, 225)),
        (0.51, 0.14, (241, 245, 249)),
        (0.70, 0.06, (203, 213, 225)),
        (0.81, 0.11, (241, 245, 249)),
        (0.96, 0.04, (241, 245, 249)),
    ]

    for rel_x, rel_w, color in bar_defs:
        bx1 = left_x + int(rel_x * total_w)
        bx2 = bx1 + max(1, int(rel_w * total_w))
        draw.rectangle([bx1, bar_top, bx2, bar_bottom], fill=color)

    # 3. Horizontal laser scan beam (Emerald green glow line across center)
    beam_y = int(size * 0.50)
    beam_h = max(2, int(size * 0.04))
    draw.line(
        [(pad + int(size * 0.06), beam_y), (pad + w - int(size * 0.06), beam_y)],
        fill=(16, 185, 129, 255),  # Emerald 500
        width=beam_h,
    )

    # 4. Optional status beacon badge in bottom-right corner
    if status_badge in ("running", "active", "green"):
        badge_r = int(size * 0.16)
        bx = size - pad - int(badge_r * 0.7)
        by = size - pad - int(badge_r * 0.7)
        # Glow
        draw.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=(16, 185, 129, 255), outline=(255, 255, 255, 255), width=max(1, int(size * 0.02)))
    elif status_badge in ("stopped", "standby", "amber"):
        badge_r = int(size * 0.16)
        bx = size - pad - int(badge_r * 0.7)
        by = size - pad - int(badge_r * 0.7)
        draw.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=(245, 158, 11, 255), outline=(255, 255, 255, 255), width=max(1, int(size * 0.02)))

    return img


def generate_ico_file(output_path: Path, status_badge: str | None = None) -> Path:
    """Generate and save a multi-resolution .ico containing all standard Windows sizes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    images = [render_app_icon(s[0], status_badge=status_badge) for s in ICON_SIZES]
    images[0].save(
        output_path,
        format="ICO",
        sizes=ICON_SIZES,
        append_images=images[1:],
    )
    return output_path


def ensure_icons_exist() -> tuple[Path, Path]:
    """Ensure standard assets/icon.ico and res/icon.ico exist on disk."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    assets_ico = base_dir / "assets" / "icon.ico"
    res_ico = base_dir / "res" / "icon.ico"

    if not assets_ico.exists():
        generate_ico_file(assets_ico)
    if not res_ico.exists():
        generate_ico_file(res_ico)

    return assets_ico, res_ico
