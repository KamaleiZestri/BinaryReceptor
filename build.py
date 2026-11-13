"""Build the portable Windows one-file distribution."""
from __future__ import annotations
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"

def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("The standalone BinaryReceptor executable must be built on Windows.")
    command = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--noconsole",
        "--name", "BinaryReceptor", "--icon", str(ROOT / "res" / "icon.ico"),
        "--version-file", str(ROOT / "res" / "version.txt"),
        "--add-data", f"{ROOT / 'res' / 'icon.ico'};res",
        "--hidden-import", "PIL._tkinter_finder", "--hidden-import", "qrcode.image.pil",
        str(ROOT / "run.py"),
    ]
    subprocess.check_call(command, cwd=ROOT)
    shutil.copy2(ROOT / "settings.ini", DIST / "settings.ini")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
