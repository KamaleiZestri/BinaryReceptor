"""System Tray controller for BinaryReceptor v3.0.0 using native PySide6 QSystemTrayIcon."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Callable, Any

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QIcon, QPixmap, QAction, QActionGroup
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QWidget

from src.ui.i18n import tr
from src.ui.icon_gen import render_app_icon


def create_tray_pixmap(status: str = "running") -> QPixmap:
    """Render a dynamic tray icon with live running/stopped badge."""
    badge = "running" if status == "running" else "stopped"
    img = render_app_icon(size=64, status_badge=badge)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    pixmap = QPixmap()
    pixmap.loadFromData(buf.getvalue())
    return pixmap


class SystemTrayController(QObject):
    """Manages the Windows System Tray icon, localized menu, and scan notifications."""

    request_show_window = Signal()
    request_show_qr = Signal()
    request_toggle_server = Signal()
    request_set_mode = Signal(str)
    request_exit = Signal()

    def __init__(self, parent_widget: QWidget | None = None) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.lang = "en"
        self.is_running = False
        self.current_mode = "both"

        self.icon_running = QIcon(create_tray_pixmap("running"))
        self.icon_stopped = QIcon(create_tray_pixmap("stopped"))

        self.tray = QSystemTrayIcon(self.icon_stopped, parent_widget)
        self.tray.setToolTip("BinaryReceptor v3.0.0")

        self.menu = QMenu(parent_widget)
        self.tray.setContextMenu(self.menu)

        self.tray.activated.connect(self._on_tray_activated)
        self.rebuild_menu()
        self.tray.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self.request_show_window.emit()

    def update_state(self, is_running: bool, mode: str, lang: str) -> None:
        """Update live tray icon and context menu."""
        self.is_running = is_running
        self.current_mode = mode
        self.lang = lang

        # Update tray icon
        self.tray.setIcon(self.icon_running if is_running else self.icon_stopped)
        self.rebuild_menu()

    def rebuild_menu(self) -> None:
        """Reconstruct the localized context menu."""
        self.menu.clear()

        # Header item (non-clickable status display)
        mode_label = {
            "both": tr("opt_mode_both", self.lang),
            "http": tr("opt_mode_http", self.lang),
            "bluetooth": tr("opt_mode_bt", self.lang),
        }.get(self.current_mode, self.current_mode)

        status_text = tr("status_running", self.lang) if self.is_running else tr("status_stopped", self.lang)
        header_text = f"BinaryReceptor v3.0.0 · {status_text} [{mode_label}]"
        header_action = self.menu.addAction(header_text)
        header_action.setEnabled(False)

        self.menu.addSeparator()

        # Start / Stop toggle
        toggle_text = tr("tray_stop", self.lang) if self.is_running else tr("tray_start", self.lang)
        act_toggle = self.menu.addAction(toggle_text)
        act_toggle.triggered.connect(lambda: self.request_toggle_server.emit())

        # Mode submenu
        mode_menu = self.menu.addMenu("Mode / حالت سرور")
        mode_group = QActionGroup(self)
        mode_group.setExclusive(True)

        for m_id, label_key in [
            ("both", "tray_mode_both"),
            ("http", "tray_mode_http"),
            ("bluetooth", "tray_mode_bt"),
        ]:
            act = mode_menu.addAction(tr(label_key, self.lang))
            act.setCheckable(True)
            act.setChecked(self.current_mode == m_id)
            mode_group.addAction(act)
            act.triggered.connect(lambda checked=False, m=m_id: self.request_set_mode.emit(m))

        self.menu.addSeparator()

        # Show QR / Connection Info
        act_qr = self.menu.addAction(tr("tray_show_qr", self.lang))
        act_qr.triggered.connect(lambda: self.request_show_qr.emit())

        # Open Main Window
        act_open = self.menu.addAction(tr("tray_show_window", self.lang))
        act_open.triggered.connect(lambda: self.request_show_window.emit())

        self.menu.addSeparator()

        # Exit Completely
        act_exit = self.menu.addAction(tr("tray_exit", self.lang))
        act_exit.triggered.connect(lambda: self.request_exit.emit())

    def show_notification(self, title: str, message: str, msec: int = 2500) -> None:
        """Show native Windows balloon / toast notification."""
        if self.tray.isVisible():
            self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, msec)
