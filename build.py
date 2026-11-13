"""Automated build script for BinaryReceptor v3.1.0.

Compiles the application into a standalone Windows .exe using PyInstaller:
  - --noconsole (windowed GUI mode)
  - --onefile (single binary executable)
  - --name BinaryReceptor
  - --icon assets/icon.ico (multi-resolution 16-256px icon)
  - --version-file res/version.txt (Windows PE metadata)
  - Copies default settings.ini alongside BinaryReceptor.exe in dist/
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
ASSETS_DIR = ROOT_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icon.ico"
VERSION_FILE = ROOT_DIR / "res" / "version.txt"
SETTINGS_SRC = ROOT_DIR / "settings.ini"


def clean():
    print("[1/5] Cleaning prior build artifacts...")
    for folder in [DIST_DIR, BUILD_DIR]:
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
    for spec in ROOT_DIR.glob("*.spec"):
        try:
            spec.unlink()
        except OSError:
            pass


def ensure_icon():
    print("[2/5] Verifying multi-resolution application icons...")
    sys.path.insert(0, str(ROOT_DIR))
    from src.ui.icon_gen import ensure_icons_exist
    ensure_icons_exist()


def run_pyinstaller():
    print("[3/5] Running PyInstaller build...")
    entry_point = ROOT_DIR / "src" / "main.py"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name",
        "BinaryReceptor",
        f"--icon={ICON_PATH}",
        f"--add-data={ASSETS_DIR}{os.pathsep}assets",
        f"--version-file={VERSION_FILE}" if VERSION_FILE.exists() else "",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=qrcode",
        "--hidden-import=PIL",
        "--hidden-import=psutil",
        "--hidden-import=pyperclip",
        str(entry_point),
    ]
    cmd = [arg for arg in cmd if arg]

    print("Command:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if proc.returncode != 0:
        print("[ERROR] PyInstaller compilation failed.")
        sys.exit(proc.returncode)


def finalize_release_bundle():
    print("[4/5] Preparing distribution bundle...")
    exe_path = DIST_DIR / "BinaryReceptor.exe"
    if not exe_path.exists():
        print("[ERROR] Expected binary not found:", exe_path)
        sys.exit(1)

    # Ensure default settings.ini is copied alongside the exe
    target_ini = DIST_DIR / "settings.ini"
    from src.config import DEFAULT_SETTINGS_INI
    target_ini.write_text(DEFAULT_SETTINGS_INI, encoding="utf-8")

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"[5/5] Build SUCCESSFUL!")
    print(f"      Executable : {exe_path} ({size_mb:.2f} MB)")
    print(f"      Settings   : {target_ini}")


def main():
    clean()
    ensure_icon()
    run_pyinstaller()
    finalize_release_bundle()


if __name__ == "__main__":
    main()
