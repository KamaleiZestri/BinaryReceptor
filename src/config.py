"""Configuration manager for BinaryReceptor v3.0.0.

Provides deterministic settings.ini path resolution (alongside the executable),
automatic default generation with comprehensive comments, live file-watcher hot-reload,
case-insensitive INI parsing with inline comment and UTF-8 BOM tolerance, legacy key
compatibility, and the intuitive visual Prefix/Suffix token compiler.
"""
from __future__ import annotations

import configparser
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Any

from src.version import (
    __version__,
    DEFAULT_HTTP_HOST,
    DEFAULT_HTTP_PORT,
    DEFAULT_BT_UUID,
    DEFAULT_BT_NAME,
    DEFAULT_DEDUP_WINDOW_MS,
)


def get_settings_path() -> Path:
    """Deterministic path resolver for settings.ini.

    In frozen executables (PyInstaller/Nuitka), always resolves to the directory
    containing BinaryReceptor.exe. During development, resolves to the project root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "settings.ini"
    return Path(__file__).resolve().parent.parent / "settings.ini"


DEFAULT_SETTINGS_INI = f"""# ==============================================================================
# BinaryReceptor v{__version__} - Desktop Companion Server for BinaryEye
# https://github.com/ouncommono/BinaryReceptor
# ==============================================================================
# This configuration file is read from and written to the directory alongside
# BinaryReceptor.exe. You can modify these settings directly while the app is
# running; changes will hot-reload automatically within 1 second.
# ==============================================================================

[general]
# Operating Mode:
#   both      - Runs both Bluetooth RFCOMM and HTTP servers simultaneously (Recommended)
#   http      - HTTP server only (Wi-Fi / LAN forwarding)
#   bluetooth - Bluetooth RFCOMM server only
mode = both

# UI Language: en (English - LTR) or fa (Persian / فارسی - RTL)
language = en

# UI Theme: dark, light, or system
theme = dark

# Automatically start listeners when application launches
auto_start = true

# Start application minimized directly to system tray
start_minimized = false

# Minimize window to system tray when the 'X' close button is clicked
minimize_to_tray = true

# Start BinaryReceptor automatically with Windows user login
start_with_windows = false

# Beep sound effect when a scan is successfully received and processed
audio_feedback = true
beep_frequency = 2450
beep_duration_ms = 85

# Show Windows System Tray / Toast notifications on scan reception
tray_notifications = true

[network]
# Local network interface to bind HTTP listener (0.0.0.0 binds to all LAN adapters)
http_host = {DEFAULT_HTTP_HOST}

# HTTP port for BinaryEye Webhook / Forwarding requests (Default: {DEFAULT_HTTP_PORT})
http_port = {DEFAULT_HTTP_PORT}

[bluetooth]
# Enable native Windows Bluetooth RFCOMM listener
bt_enabled = true

# BinaryEye standard Bluetooth Service SDP UUID
service_uuid = {DEFAULT_BT_UUID}

# Bluetooth SDP Service Name advertised to paired Android devices
service_name = {DEFAULT_BT_NAME}

[wedge]
# Keystroke Output Mode:
#   type      - Simulated Win32 keystrokes using SendInput Unicode
#   paste     - Instant clipboard paste using Ctrl+V (ideal for large 2D QR codes)
#   copy_only - Copy scanned text to clipboard without injecting keystrokes
output_mode = type

# Prefix typed before barcode content.
# Supports tokens: {{ENTER}}, {{TAB}}, {{SPACE}}, {{BACKSPACE}}, {{ESC}}, {{DOWN}}, {{UP}}, {{DATE}}, {{TIME}}
prefix = 

# Suffix typed after barcode content. (Default: {{ENTER}})
suffix = {{ENTER}}

# Inter-key typing delay in milliseconds (0 to 100ms)
inter_key_delay_ms = 0

# Delay in milliseconds before typing begins after scan is received (0 to 5000ms)
pre_typing_delay_ms = 0

# Restore previous clipboard contents after Ctrl+V paste mode completes
restore_clipboard = true

[deduplication]
# Suppress duplicate scans arriving via both Bluetooth & HTTP simultaneously
deduplication_enabled = true

# Deduplication sliding time window in milliseconds (100 to 10000ms)
deduplication_window_ms = {DEFAULT_DEDUP_WINDOW_MS}

[filters]
# Strip leading and trailing whitespace from scanned content
trim_whitespace = true

# Replace internal newlines: none, tab, or space
replace_newlines = none

# Regular expression search pattern to transform barcodes (leave empty to disable)
regex_pattern = 

# Replacement string for regex matches
regex_replacement = 

# Filter allowed barcode formats (e.g. 'all' or comma-separated 'QR_CODE,EAN_13,CODE_128')
allowed_formats = all

# Automatically open scanned content in default web browser if it is a valid URL
auto_open_urls = false

# Always copy scanned text to clipboard in addition to keystroke typing
copy_to_clipboard = false
"""

# Virtual key code mappings for tokens
TOKEN_VK_MAP: dict[str, int] = {
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "TAB": 0x09,
    "SPACE": 0x20,
    "BACKSPACE": 0x08,
    "BKSP": 0x08,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "DELETE": 0x2E,
    "DEL": 0x2E,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
    "HOME": 0x24,
    "END": 0x23,
    "F1": 0x70,
    "F2": 0x71,
    "F3": 0x72,
    "F4": 0x73,
    "F5": 0x74,
    "F6": 0x75,
    "F7": 0x76,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F11": 0x7A,
    "F12": 0x7B,
}


def canonicalize_token(token_str: str) -> str:
    """Normalize user input or legacy alias into canonical {TOKEN} form."""
    if not token_str:
        return ""
    cleaned = token_str.strip()
    upper = cleaned.upper()

    # Plain text escape sequence normalization
    if cleaned in ("\\n", "\\r\\n", "\n", "\r\n") or upper in ("ENTER", "{ENTER}", "RETURN", "{RETURN}"):
        return "{ENTER}"
    if cleaned in ("\\t", "\t") or upper in ("TAB", "{TAB}"):
        return "{TAB}"
    if cleaned == " " or upper in ("SPACE", "{SPACE}"):
        return "{SPACE}"
    if upper in ("BACKSPACE", "{BACKSPACE}", "BKSP", "{BKSP}"):
        return "{BACKSPACE}"
    if upper in ("ESC", "{ESC}", "ESCAPE", "{ESCAPE}"):
        return "{ESC}"
    if upper in ("DOWN", "{DOWN}"):
        return "{DOWN}"
    if upper in ("UP", "{UP}"):
        return "{UP}"
    if upper in ("LEFT", "{LEFT}"):
        return "{LEFT}"
    if upper in ("RIGHT", "{RIGHT}"):
        return "{RIGHT}"
    if upper in ("NONE", "{NONE}", "EMPTY"):
        return ""
    return token_str


def parse_tokens(template: str) -> list[tuple[str, Any]]:
    """Parse a tokenized template string into a list of executable actions.

    Actions returned:
      - ('text', string_to_type)
      - ('vk', virtual_key_code)
      - ('delay', milliseconds)
    """
    if not template:
        return []

    # Replace escape sequences if written literally as \n, \t, etc.
    raw = template.replace("\\r\\n", "{ENTER}").replace("\\n", "{ENTER}").replace("\\t", "{TAB}")

    # Regex to split on {TOKEN} markers
    pattern = re.compile(r"(\{([A-Za-z0-9_]+)\})")
    actions: list[tuple[str, Any]] = []
    last_idx = 0

    for match in pattern.finditer(raw):
        start, end = match.span()
        if start > last_idx:
            literal = raw[last_idx:start]
            if literal:
                actions.append(("text", literal))

        token_name = match.group(2).upper()
        if token_name in TOKEN_VK_MAP:
            actions.append(("vk", TOKEN_VK_MAP[token_name]))
        elif token_name == "DATE":
            actions.append(("text", datetime.now().strftime("%Y-%m-%d")))
        elif token_name == "TIME":
            actions.append(("text", datetime.now().strftime("%H:%M:%S")))
        elif token_name == "TIMESTAMP":
            actions.append(("text", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        elif token_name.startswith("DELAY_"):
            try:
                ms = int(token_name.split("_")[1])
                actions.append(("delay", ms))
            except ValueError:
                actions.append(("text", match.group(1)))
        else:
            # Unrecognized token, treat as literal text
            actions.append(("text", match.group(1)))

        last_idx = end

    if last_idx < len(raw):
        remainder = raw[last_idx:]
        if remainder:
            actions.append(("text", remainder))

    return actions


def format_token_preview(prefix: str, content: str, suffix: str) -> str:
    """Generate a clean visual preview of the combined scan output."""
    def _display(text: str) -> str:
        s = text or ""
        s = s.replace("{ENTER}", "↵ [Enter] ")
        s = s.replace("{TAB}", "⇥ [Tab] ")
        s = s.replace("{SPACE}", "␣ [Space] ")
        s = s.replace("{BACKSPACE}", "⌫ [Bksp] ")
        s = s.replace("{ESC}", "⎋ [Esc] ")
        s = s.replace("{DOWN}", "↓ [Down] ")
        return s

    p = _display(prefix)
    s = _display(suffix)
    return f"{p}{content}{s}"


@dataclass
class AppConfig:
    # General
    mode: str = "both"  # "bluetooth", "http", "both"
    language: str = "en"  # "en", "fa"
    theme: str = "dark"  # "dark", "light", "system"
    auto_start: bool = True
    start_minimized: bool = False
    minimize_to_tray: bool = True
    start_with_windows: bool = False
    audio_feedback: bool = True
    beep_frequency: int = 2450
    beep_duration_ms: int = 85
    tray_notifications: bool = True

    # Network / HTTP
    http_host: str = DEFAULT_HTTP_HOST
    http_port: int = DEFAULT_HTTP_PORT

    # Bluetooth
    bt_enabled: bool = True
    service_uuid: str = DEFAULT_BT_UUID
    service_name: str = DEFAULT_BT_NAME

    # Keystroke / Wedge
    output_mode: str = "type"  # "type", "paste", "copy_only"
    prefix: str = ""
    suffix: str = "{ENTER}"
    inter_key_delay_ms: int = 0
    pre_typing_delay_ms: int = 0
    restore_clipboard: bool = True

    # Deduplication
    deduplication_enabled: bool = True
    deduplication_window_ms: int = DEFAULT_DEDUP_WINDOW_MS

    # Filters & Transformation
    trim_whitespace: bool = True
    replace_newlines: str = "none"  # "none", "tab", "space"
    regex_pattern: str = ""
    regex_replacement: str = ""
    allowed_formats: str = "all"
    auto_open_urls: bool = False
    copy_to_clipboard: bool = False

    def copy(self) -> AppConfig:
        """Create a shallow copy of config."""
        c = AppConfig()
        for k, v in self.__dict__.items():
            setattr(c, k, v)
        return c


class ConfigManager:
    """Thread-safe, disk-backed settings manager with live hot-reload."""

    def __init__(self, ini_path: Path | None = None) -> None:
        self.path = ini_path or get_settings_path()
        self._lock = threading.RLock()
        self._listeners: list[Callable[[AppConfig], None]] = []
        self._last_mtime: float | None = None
        self._ignore_watcher_until: float = 0.0
        self._stop_event = threading.Event()
        self._watcher_thread: threading.Thread | None = None

        # Load initial configuration and start background file watcher
        self._config = self._load_from_disk()
        self._start_watcher()

    @property
    def current(self) -> AppConfig:
        with self._lock:
            return self._config.copy()

    def add_listener(self, callback: Callable[[AppConfig], None]) -> None:
        """Register a callback to be notified when config is reloaded or changed."""
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[AppConfig], None]) -> None:
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def _notify_listeners(self, config: AppConfig) -> None:
        listeners = []
        with self._lock:
            listeners = list(self._listeners)
        for cb in listeners:
            try:
                cb(config)
            except Exception:
                pass

    def _load_from_disk(self) -> AppConfig:
        """Read settings.ini from disk with fallback, legacy key support, and auto-creation."""
        cfg = AppConfig()

        if not self.path.exists():
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(DEFAULT_SETTINGS_INI, encoding="utf-8")
                self._last_mtime = self.path.stat().st_mtime
            except OSError:
                pass
            return cfg

        parser = configparser.ConfigParser(
            interpolation=None,
            comment_prefixes=("#", ";"),
            inline_comment_prefixes=("#", ";"),
        )

        try:
            # Read with UTF-8 BOM tolerance and handle sectionless legacy files
            raw_text = self.path.read_text(encoding="utf-8-sig", errors="replace")
            raw_text = raw_text.lstrip("\ufeff")
            if not any(line.strip().startswith("[") for line in raw_text.splitlines() if line.strip()):
                raw_text = "[general]\n" + raw_text

            parser.read_string(raw_text)
            self._last_mtime = self.path.stat().st_mtime
        except Exception:
            # File might be partially written, retain current or return defaults
            return cfg

        # Helper to find a key across sections or fallback
        flat_map: dict[str, str] = {}
        for section in parser.sections():
            for k, v in parser.items(section):
                flat_map[k.lower()] = v.strip()

        # Also support legacy section-less or [app] INI files
        if parser.defaults():
            for k, v in parser.defaults().items():
                flat_map[k.lower()] = v.strip()

        def _get_str(key: str, default: str, *aliases: str) -> str:
            all_keys = [key.lower()] + [a.lower() for a in aliases]
            for ak in all_keys:
                if ak in flat_map and flat_map[ak] != "":
                    return flat_map[ak]
            return default

        def _get_bool(key: str, default: bool, *aliases: str) -> bool:
            val = _get_str(key, "", *aliases).lower()
            if not val:
                return default
            return val in ("true", "1", "yes", "on", "enabled")

        def _get_int(key: str, default: int, min_val: int, max_val: int, *aliases: str) -> int:
            val_str = _get_str(key, "", *aliases)
            if not val_str:
                return default
            try:
                val = int(val_str)
                return max(min_val, min(max_val, val))
            except ValueError:
                return default

        # Parse general
        mode_str = _get_str("mode", "both").lower()
        if mode_str in ("both", "http", "bluetooth"):
            cfg.mode = mode_str
        elif mode_str in ("wifi", "lan", "network"):
            cfg.mode = "http"
        elif mode_str in ("bt", "serial"):
            cfg.mode = "bluetooth"
        else:
            cfg.mode = "both"

        lang_str = _get_str("language", "en", "lang").lower()
        cfg.language = "fa" if lang_str in ("fa", "persian", "farsi") else "en"

        theme_str = _get_str("theme", "dark").lower()
        cfg.theme = theme_str if theme_str in ("dark", "light", "system") else "dark"

        cfg.auto_start = _get_bool("auto_start", True, "master_power_on_launch")
        cfg.start_minimized = _get_bool("start_minimized", False)
        cfg.minimize_to_tray = _get_bool("minimize_to_tray", True)
        cfg.start_with_windows = _get_bool("start_with_windows", False, "autostart")
        cfg.audio_feedback = _get_bool("audio_feedback", True, "beep_enabled")
        cfg.beep_frequency = _get_int("beep_frequency", 2450, 100, 10000, "beep_freq")
        cfg.beep_duration_ms = _get_int("beep_duration_ms", 85, 10, 2000, "beep_dur")
        cfg.tray_notifications = _get_bool("tray_notifications", True)

        # Network / HTTP
        cfg.http_host = _get_str("http_host", DEFAULT_HTTP_HOST, "host")
        cfg.http_port = _get_int("http_port", DEFAULT_HTTP_PORT, 1024, 65535, "port")

        # Bluetooth
        cfg.bt_enabled = _get_bool("bt_enabled", True, "bluetooth_enabled")
        cfg.service_uuid = _get_str("service_uuid", DEFAULT_BT_UUID, "uuid", "bt_uuid")
        cfg.service_name = _get_str("service_name", DEFAULT_BT_NAME, "bt_name")

        # Keystroke / Wedge
        out_mode = _get_str("output_mode", "type", "wedge_mode").lower()
        cfg.output_mode = out_mode if out_mode in ("type", "paste", "copy_only") else "type"

        # Legacy preType / postType compatibility
        raw_prefix = _get_str("prefix", "", "pretype")
        raw_suffix = _get_str("suffix", "{ENTER}", "posttype")
        cfg.prefix = canonicalize_token(raw_prefix)
        cfg.suffix = canonicalize_token(raw_suffix)

        cfg.inter_key_delay_ms = _get_int("inter_key_delay_ms", 0, 0, 500, "typing_delay_ms")
        cfg.pre_typing_delay_ms = _get_int("pre_typing_delay_ms", 0, 0, 5000, "initial_delay_ms")
        cfg.restore_clipboard = _get_bool("restore_clipboard", True)

        # Deduplication
        cfg.deduplication_enabled = _get_bool("deduplication_enabled", True, "dedup_enabled")
        cfg.deduplication_window_ms = _get_int(
            "deduplication_window_ms", DEFAULT_DEDUP_WINDOW_MS, 100, 10000, "dedup_window_ms", "debounce_ms"
        )

        # Filters & Transformation
        cfg.trim_whitespace = _get_bool("trim_whitespace", True)
        cfg.replace_newlines = _get_str("replace_newlines", "none").lower()
        if cfg.replace_newlines not in ("none", "tab", "space"):
            cfg.replace_newlines = "none"

        cfg.regex_pattern = _get_str("regex_pattern", "", "replace_pattern")
        cfg.regex_replacement = _get_str("regex_replacement", "", "replace_with")
        cfg.allowed_formats = _get_str("allowed_formats", "all", "symbology")
        cfg.auto_open_urls = _get_bool("auto_open_urls", False)
        cfg.copy_to_clipboard = _get_bool("copy_to_clipboard", False)

        return cfg

    def reload(self) -> AppConfig:
        """Manually trigger reload from disk and notify listeners."""
        with self._lock:
            self._config = self._load_from_disk()
            cfg_copy = self._config.copy()
        self._notify_listeners(cfg_copy)
        return cfg_copy

    def save(self, **updates: Any) -> AppConfig:
        """Atomically persist configuration changes to settings.ini."""
        with self._lock:
            # Apply updates to in-memory config
            for k, v in updates.items():
                if hasattr(self._config, k):
                    setattr(self._config, k, v)

            cfg = self._config

            parser = configparser.ConfigParser(interpolation=None)
            parser["general"] = {
                "mode": str(cfg.mode),
                "language": str(cfg.language),
                "theme": str(cfg.theme),
                "auto_start": "true" if cfg.auto_start else "false",
                "start_minimized": "true" if cfg.start_minimized else "false",
                "minimize_to_tray": "true" if cfg.minimize_to_tray else "false",
                "start_with_windows": "true" if cfg.start_with_windows else "false",
                "audio_feedback": "true" if cfg.audio_feedback else "false",
                "beep_frequency": str(cfg.beep_frequency),
                "beep_duration_ms": str(cfg.beep_duration_ms),
                "tray_notifications": "true" if cfg.tray_notifications else "false",
            }
            parser["network"] = {
                "http_host": str(cfg.http_host),
                "http_port": str(cfg.http_port),
            }
            parser["bluetooth"] = {
                "bt_enabled": "true" if cfg.bt_enabled else "false",
                "service_uuid": str(cfg.service_uuid),
                "service_name": str(cfg.service_name),
            }
            parser["wedge"] = {
                "output_mode": str(cfg.output_mode),
                "prefix": str(cfg.prefix),
                "suffix": str(cfg.suffix),
                "inter_key_delay_ms": str(cfg.inter_key_delay_ms),
                "pre_typing_delay_ms": str(cfg.pre_typing_delay_ms),
                "restore_clipboard": "true" if cfg.restore_clipboard else "false",
            }
            parser["deduplication"] = {
                "deduplication_enabled": "true" if cfg.deduplication_enabled else "false",
                "deduplication_window_ms": str(cfg.deduplication_window_ms),
            }
            parser["filters"] = {
                "trim_whitespace": "true" if cfg.trim_whitespace else "false",
                "replace_newlines": str(cfg.replace_newlines),
                "regex_pattern": str(cfg.regex_pattern),
                "regex_replacement": str(cfg.regex_replacement),
                "allowed_formats": str(cfg.allowed_formats),
                "auto_open_urls": "true" if cfg.auto_open_urls else "false",
                "copy_to_clipboard": "true" if cfg.copy_to_clipboard else "false",
            }

            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                tmp_path = self.path.with_suffix(".tmp")
                with tmp_path.open("w", encoding="utf-8") as f:
                    f.write(f"# BinaryReceptor v{__version__} Settings File\n")
                    f.write(f"# Saved at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    parser.write(f)

                # Avoid triggering watcher reload from our own write
                self._ignore_watcher_until = time.time() + 1.5
                os.replace(tmp_path, self.path)
                self._last_mtime = self.path.stat().st_mtime
            except OSError:
                pass

            cfg_copy = self._config.copy()

        self._notify_listeners(cfg_copy)
        return cfg_copy

    def _start_watcher(self) -> None:
        """Background thread polling file mtime every 1.0s for hot-reload."""
        def _watch_loop():
            while not self._stop_event.is_set():
                time.sleep(1.0)
                if time.time() < self._ignore_watcher_until:
                    continue

                try:
                    if self.path.exists():
                        mtime = self.path.stat().st_mtime
                        if self._last_mtime is not None and mtime > (self._last_mtime + 0.05):
                            # File changed externally!
                            with self._lock:
                                self._config = self._load_from_disk()
                                cfg_copy = self._config.copy()
                            self._notify_listeners(cfg_copy)
                except OSError:
                    pass

        self._watcher_thread = threading.Thread(
            target=_watch_loop, name="BinaryReceptor-ConfigWatcher", daemon=True
        )
        self._watcher_thread.start()

    def close(self) -> None:
        """Stop background file watcher."""
        self._stop_event.set()
        if self._watcher_thread and self._watcher_thread.is_alive():
            self._watcher_thread.join(timeout=1.0)
