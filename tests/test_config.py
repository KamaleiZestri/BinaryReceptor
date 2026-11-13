"""Tests for settings.ini path resolution, parsing, legacy compatibility, and hot-reload."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

from src.config import ConfigManager, get_settings_path, canonicalize_token, DEFAULT_SETTINGS_INI


def test_settings_path_resolution(monkeypatch):
    """Verify deterministic path resolution: alongside exe when frozen, project root in dev."""
    # Development mode (not frozen)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    dev_path = get_settings_path()
    assert dev_path.name == "settings.ini"
    assert dev_path.parent == Path(__file__).resolve().parent.parent

    # Frozen mode (PyInstaller)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    fake_exe = Path("C:/Program Files/BinaryReceptor/BinaryReceptor.exe")
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    frozen_path = get_settings_path()
    assert frozen_path == Path("C:/Program Files/BinaryReceptor/settings.ini")


def test_auto_generate_default_ini(tmp_path):
    """If settings.ini does not exist, it should be auto-generated with defaults."""
    ini_file = tmp_path / "settings.ini"
    assert not ini_file.exists()

    mgr = ConfigManager(ini_file)
    cfg = mgr.current
    mgr.close()

    assert ini_file.exists()
    content = ini_file.read_text(encoding="utf-8")
    assert "BinaryReceptor" in content
    assert "mode = both" in content
    assert cfg.mode == "both"
    assert cfg.http_port == 24234


def test_legacy_key_parsing(tmp_path):
    """Test 100% backward compatibility with legacy settings (preType, postType, mode=bluetooth, port=5050)."""
    ini_file = tmp_path / "settings.ini"
    legacy_content = """; Legacy BinaryReceptor settings
mode=bluetooth
preType={TAB}
postType=\\n
port=5050
"""
    ini_file.write_text(legacy_content, encoding="utf-8")

    mgr = ConfigManager(ini_file)
    cfg = mgr.current
    mgr.close()

    assert cfg.mode == "bluetooth"
    assert cfg.prefix == "{TAB}"
    assert cfg.suffix == "{ENTER}"
    assert cfg.http_port == 5050


def test_utf8_bom_and_inline_comments(tmp_path):
    """Verify UTF-8 with BOM and inline comments (# and ;) are parsed without error."""
    ini_file = tmp_path / "settings.ini"
    bom_content = "\ufeff[general]\nmode = http # inline comment\nlanguage = fa ; persian\n[network]\nhttp_port = 25000 # port\n"
    ini_file.write_bytes(bom_content.encode("utf-8-sig"))

    mgr = ConfigManager(ini_file)
    cfg = mgr.current
    mgr.close()

    assert cfg.mode == "http"
    assert cfg.language == "fa"
    assert cfg.http_port == 25000


def test_atomic_save_and_persistence(tmp_path):
    """Test that saving settings updates disk and in-memory config atomically."""
    ini_file = tmp_path / "settings.ini"
    mgr = ConfigManager(ini_file)

    mgr.save(mode="http", http_port=30000, prefix="{TAB}", suffix="{ENTER}{ENTER}")
    cfg = mgr.current
    mgr.close()

    assert cfg.mode == "http"
    assert cfg.http_port == 30000
    assert cfg.prefix == "{TAB}"
    assert cfg.suffix == "{ENTER}{ENTER}"

    # Verify disk content
    disk_text = ini_file.read_text(encoding="utf-8")
    assert "mode = http" in disk_text
    assert "http_port = 30000" in disk_text


def test_external_file_watcher_hot_reload(tmp_path):
    """Test that externally modifying settings.ini automatically triggers hot-reload."""
    ini_file = tmp_path / "settings.ini"
    mgr = ConfigManager(ini_file)

    reloaded_configs = []
    mgr.add_listener(lambda c: reloaded_configs.append(c))

    # Simulate user editing the file in Notepad after 1.1s
    time.sleep(1.1)
    new_text = ini_file.read_text(encoding="utf-8").replace("mode = both", "mode = http")
    ini_file.write_text(new_text, encoding="utf-8")

    # Wait for file watcher to poll (checks every 1.0s)
    deadline = time.time() + 3.0
    while time.time() < deadline:
        if reloaded_configs and mgr.current.mode == "http":
            break
        time.sleep(0.2)

    mgr.close()
    assert mgr.current.mode == "http"
