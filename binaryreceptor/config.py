"""Thread-safe, disk-backed application configuration."""
from __future__ import annotations

import configparser
import os
import sys
from dataclasses import dataclass, fields
from pathlib import Path
from threading import RLock

VERSION = "3.0.0"
DEFAULTS: dict[str, str] = {
    "version": VERSION, "mode": "http", "host": "0.0.0.0", "port": "24234",
    "language": "en", "dedup_window_ms": "1500", "prefix": "none", "suffix": "enter",
    "output_mode": "type", "typing_delay_ms": "0", "initial_delay_ms": "0",
    "trim_whitespace": "false", "transform": "none", "symbology": "all",
    "replace_pattern": "", "replace_with": "", "log_file": "", "minimize_to_tray": "false",
    "auto_start": "false", "theme": "system",
}

def config_path() -> Path:
    """Return settings.ini beside the executable, or at the source project root."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "settings.ini"
    return Path(__file__).resolve().parent.parent / "settings.ini"

@dataclass(frozen=True, slots=True)
class Config:
    path: Path
    mode: str = "http"
    host: str = "0.0.0.0"
    port: int = 24234
    language: str = "en"
    dedup_window_ms: int = 1500
    prefix: str = "none"
    suffix: str = "enter"
    output_mode: str = "type"
    typing_delay_ms: int = 0
    initial_delay_ms: int = 0
    trim_whitespace: bool = False
    transform: str = "none"
    symbology: str = "all"
    replace_pattern: str = ""
    replace_with: str = ""
    log_file: str = ""
    minimize_to_tray: bool = False
    auto_start: bool = False
    theme: str = "system"

class ConfigManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_path()
        self._lock = RLock()
        self._mtime_ns: int | None = None
        self._config = self.reload()

    @property
    def current(self) -> Config:
        with self._lock:
            return self._config

    def reload_if_changed(self) -> Config:
        try:
            mtime = self.path.stat().st_mtime_ns
        except OSError:
            mtime = None
        with self._lock:
            if mtime != self._mtime_ns:
                self._config = self.reload()
            return self._config

    def reload(self) -> Config:
        with self._lock:
            parser = configparser.ConfigParser(interpolation=None)
            existed = self.path.exists()
            if existed:
                parser.read(self.path, encoding="utf-8-sig")
            if not parser.has_section("app"):
                parser.add_section("app")
            # ConfigParser's initial defaults fill a new file. Existing files are
            # migrated by adding only keys that the user has not set.
            migrated = False
            for key, value in DEFAULTS.items():
                if key not in parser["app"]:
                    parser["app"][key] = value
                    migrated = True
            if not existed or migrated:
                try:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    tmp = self.path.with_suffix(self.path.suffix + ".tmp")
                    with tmp.open("w", encoding="utf-8", newline="\n") as stream: parser.write(stream)
                    os.replace(tmp, self.path)
                except OSError:
                    # Keep read-only portable folders usable with in-memory defaults.
                    pass
            raw = parser["app"]
            values: dict[str, object] = {"path": self.path}
            def choice(key: str, options: set[str], default: str) -> str:
                value = raw.get(key, default).strip().lower()
                return value if value in options else default
            def integer(key: str, low: int, high: int, default: int) -> int:
                try:
                    value = int(raw.get(key, str(default)))
                    return value if low <= value <= high else default
                except (ValueError, TypeError):
                    return default
            def boolean(key: str, default: bool) -> bool:
                try: return raw.getboolean(key)
                except ValueError: return default
            values.update(
                mode=choice("mode", {"http", "bluetooth", "both"}, "http"),
                host=raw.get("host", "0.0.0.0").strip() or "0.0.0.0",
                port=integer("port", 1024, 65535, 24234), language=choice("language", {"en", "fa"}, "en"),
                dedup_window_ms=integer("dedup_window_ms", 0, 10000, 1500),
                prefix=raw.get("prefix", "none"), suffix=raw.get("suffix", "enter"),
                output_mode=choice("output_mode", {"type", "paste", "copy", "log"}, "type"),
                typing_delay_ms=integer("typing_delay_ms", 0, 100, 0),
                initial_delay_ms=integer("initial_delay_ms", 0, 10000, 0),
                trim_whitespace=boolean("trim_whitespace", False),
                transform=choice("transform", {"none", "upper", "lower"}, "none"),
                symbology=raw.get("symbology", "all").strip() or "all",
                replace_pattern=raw.get("replace_pattern", ""), replace_with=raw.get("replace_with", ""),
                log_file=raw.get("log_file", "").strip(), minimize_to_tray=boolean("minimize_to_tray", False),
                auto_start=boolean("auto_start", False), theme=choice("theme", {"system", "light", "dark"}, "system"),
            )
            self._config = Config(**values)
            self._mtime_ns = self.path.stat().st_mtime_ns if self.path.exists() else None
            return self._config

    def save(self, **updates: object) -> Config:
        """Atomically persist known settings, retaining unknown future keys."""
        allowed = {field.name for field in fields(Config)} - {"path"}
        with self._lock:
            parser = configparser.ConfigParser(interpolation=None)
            parser.read_dict({"app": DEFAULTS})
            if self.path.exists(): parser.read(self.path, encoding="utf-8-sig")
            for key, value in updates.items():
                if key in allowed: parser["app"][key] = str(value).lower() if isinstance(value, bool) else str(value)
            parser["app"]["version"] = VERSION
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8", newline="\n") as stream: parser.write(stream)
            os.replace(tmp, self.path)
            self._mtime_ns = None
            return self.reload()

def load_config(path: Path | None = None) -> Config:
    return ConfigManager(path).current
