"""BinaryReceptor desktop application."""
from __future__ import annotations

import csv
import ctypes
import queue
import re
import socket
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from threading import Event, Thread

from .config import Config, ConfigManager, VERSION
from .dedupe import Deduplicator
from .transport import start_http
from .typing_win import type_template, type_token

def set_app_id() -> None:
    if hasattr(ctypes, "windll"):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ouncommono.BinaryReceptor.3.0.0")

class App:
    def __init__(self) -> None:
        set_app_id()
        self.configs = ConfigManager()
        self.config = self.configs.current
        self.root = tk.Tk()
        self.root.title(f"BinaryReceptor {VERSION}")
        self.root.geometry("900x680")
        self.root.minsize(760, 580)
        self.root.configure(bg="#101827")
        icon = Path(__file__).resolve().parent.parent / "res" / "icon.ico"
        if icon.exists():
            try: self.root.iconbitmap(str(icon))
            except tk.TclError: pass
        self.server = None
        self.dedup = Deduplicator(self.config.dedup_window_ms)
        self.events: queue.Queue[tuple[str, dict[str, str], str]] = queue.Queue()
        self.ui_actions: queue.Queue[tuple[str, object, Event | None]] = queue.Queue()
        self.count = 0
        self.mode = tk.StringVar(value=self.config.mode)
        self.lang = tk.StringVar(value=self.config.language)
        self.port = tk.StringVar(value=str(self.config.port))
        self.host = tk.StringVar(value=self.config.host)
        self.dedup_ms = tk.StringVar(value=str(self.config.dedup_window_ms))
        self.prefix = tk.StringVar(value=self.config.prefix)
        self.suffix = tk.StringVar(value=self.config.suffix)
        self.output = tk.StringVar(value=self.config.output_mode)
        self.transform = tk.StringVar(value=self.config.transform)
        self.status = tk.StringVar(value="Stopped")
        self.endpoint = tk.StringVar(value=self.endpoints())
        self.last_scan = ""
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(150, self._poll_events)
        self.root.after(1000, self._poll_config)
        if self.config.auto_start: self.start()

    def _build(self) -> None:
        style = ttk.Style(self.root)
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("TFrame", background="#101827")
        style.configure("Card.TFrame", background="#192538")
        style.configure("TLabel", background="#101827", foreground="#e6edf7", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#192538", foreground="#e6edf7")
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground="#ffffff")
        style.configure("Muted.TLabel", foreground="#9aabc2")
        style.configure("TButton", padding=(12, 7))
        outer = ttk.Frame(self.root, padding=20); outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer); header.pack(fill="x", pady=(0, 15))
        ttk.Label(header, text="BinaryReceptor", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text=f"v{VERSION}", style="Muted.TLabel").pack(side="left", padx=10, pady=(8, 0))
        ttk.Label(header, textvariable=self.status).pack(side="right", padx=12)
        ttk.Combobox(header, textvariable=self.lang, values=("en", "fa"), state="readonly", width=5).pack(side="right")
        summary = ttk.Frame(outer, style="Card.TFrame", padding=16); summary.pack(fill="x", pady=(0, 14))
        ttk.Label(summary, text="BINARYEYE CONNECTION", style="Card.TLabel").pack(anchor="w")
        ttk.Entry(summary, textvariable=self.endpoint, state="readonly", font=("Consolas", 11)).pack(fill="x", pady=9)
        controls = ttk.Frame(summary, style="Card.TFrame"); controls.pack(fill="x")
        ttk.Button(controls, text="Copy URL", command=self.copy_url).pack(side="left")
        ttk.Button(controls, text="Start service", command=self.start).pack(side="left", padx=8)
        ttk.Button(controls, text="Stop service", command=self.stop).pack(side="left")
        ttk.Button(controls, text="Reload settings.ini", command=self.reload_settings).pack(side="right")
        self.tabs = ttk.Notebook(outer); self.tabs.pack(fill="both", expand=True)
        dash = ttk.Frame(self.tabs, padding=16); typing = ttk.Frame(self.tabs, padding=16); network = ttk.Frame(self.tabs, padding=16); log = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(dash, text="Dashboard"); self.tabs.add(typing, text="Prefix / Suffix"); self.tabs.add(network, text="Network & Settings"); self.tabs.add(log, text="Live Scan Log")
        ttk.Label(dash, text="Ready to receive scans", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 6))
        ttk.Label(dash, text="Select HTTP forwarding in BinaryEye, then use the URL above. BinaryEye also supports HTTPS callbacks, while this receiver currently serves HTTP only.", style="Muted.TLabel", wraplength=760).pack(anchor="w")
        self.qr_label = ttk.Label(dash); self.qr_label.pack(anchor="center", pady=18)
        self._make_qr()
        self.scan_count = tk.StringVar(value="Scans received: 0")
        ttk.Label(dash, textvariable=self.scan_count, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(dash, text="Bluetooth RFCOMM service registration is not present in this Python port. HTTP is supported; hybrid mode currently keeps HTTP available.", style="Muted.TLabel", wraplength=760).pack(anchor="w", pady=(12, 0))
        ttk.Label(typing, text="Choose common key actions or edit a template. Tokens such as {ENTER}, {TAB}, {SPACE}, {ESC}, and {DELAY:100} are translated to native key events.", wraplength=760).pack(anchor="w", pady=(0, 14))
        self._field(typing, "Prefix template", self.prefix)
        ttk.Label(typing, text="Insert token:").pack(anchor="w", pady=(10, 4))
        chips = ttk.Frame(typing); chips.pack(anchor="w")
        for token in ("{ENTER}", "{TAB}", "{SPACE}", "{BACKSPACE}", "{ESC}", "{DELAY:100}"):
            ttk.Button(chips, text=f"+ {token}", command=lambda value=token: self._insert_token(self.prefix, value)).pack(side="left", padx=(0, 6))
        self._field(typing, "Suffix template", self.suffix)
        ttk.Label(typing, text="Output mode").pack(anchor="w", pady=(10, 3))
        ttk.Combobox(typing, textvariable=self.output, values=("type", "paste", "copy", "log"), state="readonly", width=24).pack(anchor="w")
        ttk.Button(typing, text="Save typing settings", command=self.save_settings).pack(anchor="w", pady=16)
        self._field(network, "Mode: http / bluetooth / both", self.mode)
        ttk.Combobox(network, textvariable=self.mode, values=("http", "bluetooth", "both"), state="readonly", width=24).pack(anchor="w", pady=(0, 8))
        self._field(network, "Bind address (0.0.0.0 = all interfaces)", self.host)
        self._field(network, "Port (1024–65535)", self.port)
        self._field(network, "Deduplication window in ms (0–10000)", self.dedup_ms)
        ttk.Label(network, text="LAN HTTP is the default. BinaryEye's current callback uses JSON POST. WebSocket support is not documented by BinaryEye.", style="Muted.TLabel", wraplength=760).pack(anchor="w", pady=8)
        ttk.Button(network, text="Save settings", command=self.save_settings).pack(anchor="w", pady=8)
        ttk.Button(network, text="Reset to defaults", command=self.reset_defaults).pack(anchor="w")
        columns = ("time", "value", "format", "source", "status")
        self.history = ttk.Treeview(log, columns=columns, show="headings", height=16)
        for key, label, width in (("time", "Timestamp", 150), ("value", "Barcode value", 340), ("format", "Format", 120), ("source", "Source", 90), ("status", "Status", 150)):
            self.history.heading(key, text=label); self.history.column(key, width=width, anchor="w")
        self.history.pack(fill="both", expand=True)
        actions = ttk.Frame(log); actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Copy selected", command=self.copy_selected).pack(side="left")
        ttk.Button(actions, text="Re-type selected", command=self.retype_selected).pack(side="left", padx=8)
        ttk.Button(actions, text="Clear log", command=lambda: self.history.delete(*self.history.get_children())).pack(side="right")

    def _field(self, parent: ttk.Frame, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).pack(anchor="w", pady=(4, 2))
        ttk.Entry(parent, textvariable=var, width=48).pack(anchor="w", pady=(0, 6))

    @staticmethod
    def _insert_token(var: tk.StringVar, token: str) -> None:
        var.set(var.get() + token)

    def endpoints(self) -> str:
        ips: list[str] = []
        try:
            for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ip = item[4][0]
                if not ip.startswith("127.") and not ip.startswith("169.254.") and ip not in ips: ips.append(ip)
        except OSError: pass
        if self.config.host not in ("0.0.0.0", ""):
            return f"http://{self.config.host}:{self.config.port}/"
        return "\n".join(f"http://{ip}:{self.config.port}/" for ip in ips) or f"http://<computer-ip>:{self.config.port}/"

    def _make_qr(self) -> None:
        try:
            import qrcode
            from PIL import ImageTk
            address = self.endpoint.get().splitlines()[0]
            image = qrcode.make(address).resize((164, 164))
            self.qr_image = ImageTk.PhotoImage(image)
            self.qr_label.configure(image=self.qr_image)
        except (ImportError, OSError, ValueError, tk.TclError):
            self.qr_label.configure(text="Install qrcode[pil] to display the connection QR code")

    def copy_url(self) -> None:
        self.root.clipboard_clear(); self.root.clipboard_append(self.endpoint.get().splitlines()[0]); self.root.update_idletasks()

    def save_settings(self) -> None:
        try:
            old_network = (self.config.host, self.config.port, self.config.mode)
            was_running = self.server is not None
            self.config = self.configs.save(mode=self.mode.get(), host=self.host.get(), port=int(self.port.get()), language=self.lang.get(), dedup_window_ms=int(self.dedup_ms.get()), prefix=self.prefix.get(), suffix=self.suffix.get(), output_mode=self.output.get(), transform=self.transform.get())
            self.dedup = Deduplicator(self.config.dedup_window_ms)
            self.endpoint.set(self.endpoints()); self._make_qr()
            if was_running and old_network != (self.config.host, self.config.port, self.config.mode):
                self.stop(); self.start()
            messagebox.showinfo("Settings", "Settings saved.")
        except (ValueError, OSError) as exc: messagebox.showerror("Settings", str(exc))

    def reload_settings(self) -> None:
        old_network = (self.config.host, self.config.port, self.config.mode)
        was_running = self.server is not None
        self.config = self.configs.reload()
        self.mode.set(self.config.mode); self.host.set(self.config.host); self.port.set(str(self.config.port)); self.lang.set(self.config.language)
        self.dedup_ms.set(str(self.config.dedup_window_ms)); self.prefix.set(self.config.prefix); self.suffix.set(self.config.suffix); self.output.set(self.config.output_mode)
        self.dedup = Deduplicator(self.config.dedup_window_ms); self.endpoint.set(self.endpoints()); self._make_qr()
        if was_running and old_network != (self.config.host, self.config.port, self.config.mode):
            self.stop(); self.start()

    def _poll_config(self) -> None:
        updated = self.configs.reload_if_changed()
        if updated != self.config:
            was_running = self.server is not None
            old_network = (self.config.host, self.config.port, self.config.mode)
            self.config = updated
            self.mode.set(updated.mode); self.port.set(str(updated.port)); self.host.set(updated.host); self.lang.set(updated.language)
            self.dedup_ms.set(str(updated.dedup_window_ms)); self.prefix.set(updated.prefix); self.suffix.set(updated.suffix); self.output.set(updated.output_mode)
            self.dedup = Deduplicator(updated.dedup_window_ms); self.endpoint.set(self.endpoints()); self._make_qr()
            if was_running and old_network != (updated.host, updated.port, updated.mode):
                self.stop(); self.start()
        self.root.after(1000, self._poll_config)

    def reset_defaults(self) -> None:
        self.configs.path.unlink(missing_ok=True); self.configs = ConfigManager(self.configs.path); self.config = self.configs.current
        self.reload_settings()

    def start(self) -> None:
        if self.server: return
        if self.mode.get() == "bluetooth":
            messagebox.showerror("Bluetooth unavailable", "RFCOMM/SDP service registration is not implemented in this Python port.")
            return
        try:
            port = int(self.port.get())
            if not 1024 <= port <= 65535: raise ValueError("Port must be between 1024 and 65535")
            self.server = start_http(self.host.get() or "0.0.0.0", port, lambda value, meta, source: self.events.put((value, meta, source)))
            self.status.set(f"Running · HTTP :{port}")
        except (ValueError, OSError) as exc:
            self.server = None; self.status.set("Error"); messagebox.showerror("HTTP listener", str(exc))

    def stop(self) -> None:
        server, self.server = self.server, None
        if server:
            def shutdown() -> None:
                server.shutdown()
                server.server_close()
            Thread(target=shutdown, name="binaryreceptor-stop", daemon=True).start()
        self.status.set("Stopped")

    def scan(self, content: str, meta: dict[str, str], source: str) -> None:
        self.events.put((content, meta, source))

    def _poll_events(self) -> None:
        try:
            while True:
                content, meta, source = self.events.get_nowait()
                self._handle_scan(content, meta, source)
        except queue.Empty: pass
        try:
            while True:
                action, value, completed = self.ui_actions.get_nowait()
                if action == "clipboard":
                    self._copy(str(value))
                    if completed: completed.set()
                elif action == "error":
                    messagebox.showerror("Keyboard output", str(value))
        except queue.Empty: pass
        self.root.after(80, self._poll_events)

    def _handle_scan(self, content: str, meta: dict[str, str], source: str) -> None:
        if not self.dedup.accept(content):
            self._add_history(content, meta, source, "Duplicate Suppressed"); return
        fmt = meta.get("format", meta.get("symbology", ""))
        accepted = self.config.symbology.lower() == "all" or fmt.lower() == self.config.symbology.lower()
        if not accepted:
            self._add_history(content, meta, source, "Filtered"); return
        if self.config.trim_whitespace: content = content.strip()
        if self.config.transform == "upper": content = content.upper()
        elif self.config.transform == "lower": content = content.lower()
        if self.config.replace_pattern:
            try: content = re.sub(self.config.replace_pattern, self.config.replace_with, content)
            except re.error: pass
        self.last_scan = content
        Thread(target=self._output_scan, args=(content, self.config), name="binaryreceptor-output", daemon=True).start()
        self.count += 1; self.scan_count.set(f"Scans received: {self.count}")
        self._add_history(content, meta, source, {"type": "Typed", "paste": "Pasted", "copy": "Copied", "log": "Logged"}.get(self.config.output_mode, "Typed"))
        if self.config.log_file:
            Thread(target=self._write_log, args=(self.config.log_file, content, fmt, source), daemon=True).start()

    @staticmethod
    def _write_log(path: str, content: str, fmt: str, source: str) -> None:
        try:
            with Path(path).open("a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([datetime.now().isoformat(timespec="seconds"), content, fmt, source])
        except OSError: pass

    def _output_scan(self, content: str, config: Config) -> None:
        try:
            if config.initial_delay_ms: import time; time.sleep(config.initial_delay_ms / 1000)
            if config.output_mode == "type":
                type_template(config.prefix); type_template(content, config.typing_delay_ms); type_template(config.suffix)
            elif config.output_mode == "paste":
                type_template(config.prefix)
                completed = Event()
                self.ui_actions.put(("clipboard", content, completed))
                if not completed.wait(5): raise RuntimeError("Clipboard update timed out")
                type_token("ctrl+v")
                type_template(config.suffix)
            elif config.output_mode == "copy": self.ui_actions.put(("clipboard", content, None))
        except Exception as exc:
            self.ui_actions.put(("error", str(exc), None))

    def _copy(self, value: str) -> None:
        self.root.clipboard_clear(); self.root.clipboard_append(value)

    def _add_history(self, content: str, meta: dict[str, str], source: str, status: str) -> None:
        self.history.insert("", 0, values=(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), content, meta.get("format", ""), source, status))

    def copy_selected(self) -> None:
        selected = self.history.selection()
        if selected: self._copy(str(self.history.item(selected[0], "values")[1]))

    def retype_selected(self) -> None:
        selected = self.history.selection()
        if selected: Thread(target=type_template, args=(str(self.history.item(selected[0], "values")[1]),), daemon=True).start()

    def _close(self) -> None:
        self.stop(); self.root.destroy()

    def run(self) -> None: self.root.mainloop()

if __name__ == "__main__": App().run()
