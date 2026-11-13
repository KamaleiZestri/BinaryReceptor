"""Entry point for BinaryReceptor v3.0.0.

Provides:
  - Early Win32 AppUserModelID registration for taskbar/tray icon synchronization.
  - High-DPI process awareness.
  - Single-instance kernel named mutex.
  - Backward-compatible CLI argument parsing.
  - Headless console daemon mode and PySide6 GUI bootstrap.
"""
from __future__ import annotations

import argparse
import ctypes
import os
import signal
import sys
import time
from pathlib import Path

# Add project root to sys.path so imports work seamlessly during development and frozen runs
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ConfigManager
from src.ui.icon_gen import ensure_icons_exist
from src.version import __version__, APP_NAME, APP_ID


def setup_win32_environment() -> None:
    """Register explicit AppUserModelID and High-DPI awareness on Windows."""
    if os.name == "nt":
        # 1. Register AppUserModelID before ANY window creation
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:
            pass

        # 2. Enable Per-Monitor High-DPI scaling
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


class SingleInstanceMutex:
    """Windows kernel named mutex ensuring only one instance runs at a time."""

    ERROR_ALREADY_EXISTS = 183

    def __init__(self, mutex_name: str = "Global\\BinaryReceptor_3_0_0_Mutex") -> None:
        self.mutex_name = mutex_name
        self.handle = None
        self.already_running = False

        if os.name == "nt":
            try:
                self.handle = ctypes.windll.kernel32.CreateMutexW(None, False, self.mutex_name)
                self.already_running = (ctypes.windll.kernel32.GetLastError() == self.ERROR_ALREADY_EXISTS)
            except Exception:
                pass

    def release(self) -> None:
        if self.handle and os.name == "nt":
            try:
                ctypes.windll.kernel32.CloseHandle(self.handle)
            except Exception:
                pass
            self.handle = None


def run_headless(config_mgr: ConfigManager, mode: str, port: int) -> None:
    """Run servers in non-GUI console daemon mode for server or automation deployments."""
    from src.core.bt_server import BluetoothServerController
    from src.core.deduplicator import DeduplicationEngine
    from src.core.http_server import HttpServerController
    from src.core.key_injector import KeyInjector

    config = config_mgr.current
    print(f"[BinaryReceptor v{__version__}] Starting Headless Mode (mode={mode}, port={port})...")

    dedup = DeduplicationEngine(window_ms=config.deduplication_window_ms, enabled=config.deduplication_enabled)
    injector = KeyInjector()

    def _on_scan(payload):
        is_dup, msg = dedup.check_and_record(payload.content, source=payload.source, scan_id=payload.scan_id)
        if is_dup:
            print(f"[DEDUP] {msg}")
            return
        print(f"[{payload.source}] Scanned: {payload.content}")
        injector.inject_scan(
            content=payload.content,
            prefix_template=config.prefix,
            suffix_template=config.suffix,
            output_mode=config.output_mode,
            inter_key_delay_ms=config.inter_key_delay_ms,
            pre_typing_delay_ms=config.pre_typing_delay_ms,
        )

    http_srv = None
    bt_srv = None

    if mode in ("both", "http"):
        http_srv = HttpServerController(host=config.http_host, port=port, on_scan=_on_scan)
        ok, msg = http_srv.start()
        print(f"[HTTP] {msg}")

    if mode in ("both", "bluetooth"):
        bt_srv = BluetoothServerController(
            service_uuid=config.service_uuid,
            service_name=config.service_name,
            on_scan=_on_scan,
        )
        ok, msg = bt_srv.start()
        print(f"[Bluetooth] {msg}")

    print(f"[BinaryReceptor] Ready. Press Ctrl+C to terminate.")

    stop_event = False

    def _sig_handler(sig, frame):
        nonlocal stop_event
        stop_event = True

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    try:
        while not stop_event:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        print("[BinaryReceptor] Shutting down...")
        if http_srv:
            http_srv.stop()
        if bt_srv:
            bt_srv.stop()
        config_mgr.close()


def main() -> None:
    # 1. Windows AppUserModelID & High-DPI setup
    setup_win32_environment()

    # 2. Parse command-line arguments (retains backward compatibility with CLI scripts)
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} v{__version__} - Companion Server for BinaryEye Barcode Scanner"
    )
    parser.add_argument(
        "pos_mode",
        nargs="?",
        choices=["bluetooth", "http", "both"],
        help="Operating mode (positional argument for backward compatibility)",
    )
    parser.add_argument(
        "pos_port",
        nargs="?",
        type=int,
        help="HTTP port number (positional argument for backward compatibility)",
    )
    parser.add_argument("--mode", choices=["bluetooth", "http", "both"], help="Operating mode")
    parser.add_argument("--port", type=int, help="HTTP port (1024-65535)")
    parser.add_argument("--minimized", action="store_true", help="Start minimized to system tray")
    parser.add_argument("--headless", action="store_true", help="Run without graphical user interface")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")

    args = parser.parse_args()

    # 3. Check Single-Instance Mutex
    mutex = SingleInstanceMutex()
    if mutex.already_running:
        print(f"[{APP_NAME}] Another instance is already running.")
        # If user opened again from desktop/start menu, try bringing the existing window to front
        if os.name == "nt":
            hwnd = ctypes.windll.user32.FindWindowW(None, f"BinaryReceptor v{__version__}")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        sys.exit(0)

    # 4. Initialize Configuration Manager
    config_mgr = ConfigManager()
    cfg = config_mgr.current

    # CLI argument overrides
    selected_mode = args.mode or args.pos_mode or cfg.mode
    selected_port = args.port or args.pos_port or cfg.http_port

    if selected_mode != cfg.mode or selected_port != cfg.http_port:
        config_mgr.save(mode=selected_mode, http_port=selected_port)

    # 5. Headless Mode
    if args.headless:
        run_headless(config_mgr, selected_mode, selected_port)
        mutex.release()
        return

    # 6. PySide6 GUI Bootstrap
    from PySide6.QtWidgets import QApplication
    from src.ui.main_window import MainWindow

    # Set High-DPI attributes
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setQuitOnLastWindowClosed(False)

    ensure_icons_exist()

    window = MainWindow(config_mgr)

    start_minimized = args.minimized or cfg.start_minimized
    if not start_minimized:
        window.show()
    else:
        window.hide()

    exit_code = app.exec()
    mutex.release()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
