"""World-class bilingual (Persian RTL & English LTR) dashboard for BinaryReceptor v3.0.0."""
from __future__ import annotations

import csv
import io
import os
import queue
import re
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal, QObject, Slot
from PySide6.QtGui import QIcon, QPixmap, QFont, QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QGroupBox,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QMessageBox,
    QFileDialog,
    QFrame,
    QScrollArea,
    QSplitter,
)

from src.config import (
    AppConfig,
    ConfigManager,
    canonicalize_token,
    parse_tokens,
    format_token_preview,
)
from src.core.bt_server import BluetoothServerController, get_local_bt_address
from src.core.deduplicator import DeduplicationEngine
from src.core.http_server import HttpServerController, ScanPayload
from src.core.key_injector import KeyInjector
from src.core.qr_helper import (
    BINARYEYE_FORMATS,
    build_continuous_scan_url,
    build_encode_url,
    build_forwarding_url,
    generate_qr_png_bytes,
    get_active_lan_ips,
    get_primary_lan_ip,
)
from src.ui.i18n import tr
from src.ui.icon_gen import ensure_icons_exist, render_app_icon
from src.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from src.ui.tray import SystemTrayController
from src.version import __version__, APP_NAME

try:
    import winsound
except ImportError:
    winsound = None

try:
    import winreg
except ImportError:
    winreg = None


def set_autostart_registry(enabled: bool) -> bool:
    """Configure Windows Run key for autostart."""
    if not winreg or os.name != "nt":
        return False
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        if getattr(sys, "frozen", False):
            cmd = f'"{sys.executable}"'
        else:
            entry = Path(__file__).resolve().parent.parent / "main.py"
            cmd = f'"{sys.executable}" "{entry}"'

        if enabled:
            winreg.SetValueEx(key, "BinaryReceptor", 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, "BinaryReceptor")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


class MainWindowSignals(QObject):
    scan_received = Signal(object, str, str)  # payload, processed_status, detail
    bt_status_changed = Signal(str)
    stats_updated = Signal()
    config_reloaded = Signal(object)


class MainWindow(QMainWindow):
    """Bilingual desktop companion server GUI for BinaryEye."""

    def __init__(self, config_manager: ConfigManager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.config = self.config_manager.current

        self.signals = MainWindowSignals()
        self.signals.scan_received.connect(self._on_scan_received_ui)
        self.signals.bt_status_changed.connect(self._on_bt_status_changed_ui)
        self.signals.stats_updated.connect(self._update_kpi_cards)
        self.signals.config_reloaded.connect(self._on_config_reloaded_from_disk)

        # Core Engines
        self.dedup = DeduplicationEngine(
            window_ms=self.config.deduplication_window_ms,
            enabled=self.config.deduplication_enabled,
        )
        self.injector = KeyInjector()

        # Metrics Counters
        self.cnt_total = 0
        self.cnt_bt = 0
        self.cnt_http = 0
        self.cnt_dedup = 0

        # Scan worker queue
        self.scan_queue: queue.Queue[ScanPayload] = queue.Queue()
        self._worker_thread: threading.Thread | None = None
        self._worker_stop = threading.Event()

        # Controllers
        self.http_server: HttpServerController | None = None
        self.bt_server: BluetoothServerController | None = None
        self.is_server_active = False

        # Set Window Properties
        self.setWindowTitle(f"BinaryReceptor v{__version__}")
        self.resize(1000, 720)
        self.setMinimumSize(850, 600)

        # Multi-resolution Icon
        assets_ico, res_ico = ensure_icons_exist()
        if assets_ico.exists():
            self.setWindowIcon(QIcon(str(assets_ico)))

        # Build UI Components
        self._init_ui()

        # System Tray Integration
        self.tray = SystemTrayController(self)
        self.tray.request_show_window.connect(self.show_and_activate)
        self.tray.request_show_qr.connect(self._show_qr_tab)
        self.tray.request_toggle_server.connect(self.toggle_server)
        self.tray.request_set_mode.connect(self._change_mode_from_tray)
        self.tray.request_exit.connect(self.exit_application)

        # Apply Initial Language and Theme
        self.apply_language(self.config.language)
        self.apply_theme(self.config.theme)

        # Start Background Queue Worker
        self._start_worker_thread()

        # Listen for hot-reloads from disk
        self.config_manager.add_listener(lambda cfg: self.signals.config_reloaded.emit(cfg))

        # Auto-start server if enabled
        if self.config.auto_start:
            QTimer.singleShot(400, self.start_server)

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # 1. Header Card (Title, Master Power Button, Theme/Lang Switchers)
        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(14, 10, 14, 10)

        title_box = QVBoxLayout()
        self.lbl_app_title = QLabel("BinaryReceptor v3.0.0")
        self.lbl_app_title.setObjectName("AppTitle")
        self.lbl_app_subtitle = QLabel("Desktop Companion Server for BinaryEye")
        self.lbl_app_subtitle.setObjectName("AppSubtitle")
        title_box.addWidget(self.lbl_app_title)
        title_box.addWidget(self.lbl_app_subtitle)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Master Power Button
        self.btn_master_power = QPushButton()
        self.btn_master_power.setObjectName("MasterPowerBtnStopped")
        self.btn_master_power.clicked.connect(self.toggle_server)
        header_layout.addWidget(self.btn_master_power)

        # Theme Switcher Button
        self.btn_theme_toggle = QPushButton()
        self.btn_theme_toggle.setObjectName("SecondaryBtn")
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.btn_theme_toggle)

        # Language Switcher Button
        self.btn_lang_toggle = QPushButton()
        self.btn_lang_toggle.setObjectName("SecondaryBtn")
        self.btn_lang_toggle.clicked.connect(self.toggle_language)
        header_layout.addWidget(self.btn_lang_toggle)

        main_layout.addWidget(header_card)

        # 2. KPI Metrics Bar
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)

        self.kpi_cards: dict[str, tuple[QLabel, QLabel]] = {}
        for key in ["kpi_total_scans", "kpi_bt_scans", "kpi_http_scans", "kpi_dedup_blocked"]:
            card = QFrame()
            card.setProperty("class", "KPICard")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(10, 8, 10, 8)
            lbl = QLabel(key)
            lbl.setProperty("class", "KPICardLabel")
            val = QLabel("0")
            val.setProperty("class", "KPICardValue")
            cl.addWidget(lbl)
            cl.addWidget(val)
            kpi_layout.addWidget(card)
            self.kpi_cards[key] = (lbl, val)

        # Channel Status Badges
        self.badge_bt = QLabel("Bluetooth: Standby")
        self.badge_bt.setProperty("class", "StatusBadge")
        self.badge_http = QLabel("HTTP: Standby")
        self.badge_http.setProperty("class", "StatusBadge")
        kpi_layout.addWidget(self.badge_bt)
        kpi_layout.addWidget(self.badge_http)

        main_layout.addLayout(kpi_layout)

        # 3. Tabs Navigation
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, stretch=1)

        # Build individual tabs
        self._build_dashboard_tab()
        self._build_wedge_tab()
        self._build_connection_tab()
        self._build_settings_tab()

    # ==========================================================================
    # TAB 1: Live Activity Log
    # ==========================================================================
    def _build_dashboard_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)

        # Table
        self.table_history = QTableWidget(0, 5)
        self.table_history.setHorizontalHeaderLabels([
            tr("col_time", self.config.language),
            tr("col_channel", self.config.language),
            tr("col_format", self.config.language),
            tr("col_content", self.config.language),
            tr("col_status", self.config.language),
        ])
        header = self.table_history.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table_history)

        # Action Buttons Toolbar
        btn_bar = QHBoxLayout()
        self.btn_retype = QPushButton(tr("btn_retype", self.config.language))
        self.btn_retype.clicked.connect(self._retype_selected_scan)
        btn_bar.addWidget(self.btn_retype)

        self.btn_copy_content = QPushButton(tr("btn_copy", self.config.language))
        self.btn_copy_content.setObjectName("SecondaryBtn")
        self.btn_copy_content.clicked.connect(self._copy_selected_scan)
        btn_bar.addWidget(self.btn_copy_content)

        btn_bar.addStretch()

        self.btn_export_csv = QPushButton(tr("btn_export_csv", self.config.language))
        self.btn_export_csv.setObjectName("SecondaryBtn")
        self.btn_export_csv.clicked.connect(self._export_csv)
        btn_bar.addWidget(self.btn_export_csv)

        self.btn_clear_log = QPushButton(tr("btn_clear_log", self.config.language))
        self.btn_clear_log.setObjectName("SecondaryBtn")
        self.btn_clear_log.clicked.connect(self._clear_history_log)
        btn_bar.addWidget(self.btn_clear_log)

        layout.addLayout(btn_bar)
        self.tabs.addTab(tab, tr("tab_dashboard", self.config.language))

    # ==========================================================================
    # TAB 2: Visual Prefix & Suffix Builder
    # ==========================================================================
    def _build_wedge_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)

        self.lbl_wedge_title = QLabel(tr("wedge_title", self.config.language))
        self.lbl_wedge_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(self.lbl_wedge_title)

        self.lbl_wedge_desc = QLabel(tr("wedge_desc", self.config.language))
        self.lbl_wedge_desc.setWordWrap(True)
        self.lbl_wedge_desc.setStyleSheet("color: #94a3b8; margin-bottom: 8px;")
        layout.addWidget(self.lbl_wedge_desc)

        # Prefix Builder Card
        prefix_group = QGroupBox("Prefix (قبل از بارکد)")
        self.grp_prefix = prefix_group
        pl = QVBoxLayout(prefix_group)

        p_row1 = QHBoxLayout()
        self.combo_prefix_preset = QComboBox()
        self._populate_token_presets(self.combo_prefix_preset)
        self.combo_prefix_preset.currentIndexChanged.connect(self._on_prefix_preset_changed)
        p_row1.addWidget(self.combo_prefix_preset)

        self.txt_prefix = QLineEdit(self.config.prefix)
        self.txt_prefix.textChanged.connect(self._on_wedge_text_changed)
        p_row1.addWidget(self.txt_prefix, stretch=1)

        btn_clear_p = QPushButton("✕")
        btn_clear_p.setObjectName("SecondaryBtn")
        btn_clear_p.clicked.connect(lambda: self.txt_prefix.clear())
        p_row1.addWidget(btn_clear_p)
        pl.addLayout(p_row1)

        # Interactive Token Chips for Prefix
        p_chips = QHBoxLayout()
        for token, label in [
            ("{ENTER}", "+ Enter"),
            ("{TAB}", "+ Tab"),
            ("{SPACE}", "+ Space"),
            ("{BACKSPACE}", "+ Bksp"),
            ("{ESC}", "+ Esc"),
            ("{DOWN}", "+ Down"),
            ("{DATE}", "+ Date"),
            ("{TIME}", "+ Time"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("ChipBtn")
            btn.clicked.connect(lambda checked=False, t=token: self._append_token(self.txt_prefix, t))
            p_chips.addWidget(btn)
        p_chips.addStretch()
        pl.addLayout(p_chips)
        layout.addWidget(prefix_group)

        # Suffix Builder Card
        suffix_group = QGroupBox("Suffix (بعد از بارکد)")
        self.grp_suffix = suffix_group
        sl = QVBoxLayout(suffix_group)

        s_row1 = QHBoxLayout()
        self.combo_suffix_preset = QComboBox()
        self._populate_token_presets(self.combo_suffix_preset)
        self.combo_suffix_preset.currentIndexChanged.connect(self._on_suffix_preset_changed)
        s_row1.addWidget(self.combo_suffix_preset)

        self.txt_suffix = QLineEdit(self.config.suffix)
        self.txt_suffix.textChanged.connect(self._on_wedge_text_changed)
        s_row1.addWidget(self.txt_suffix, stretch=1)

        btn_clear_s = QPushButton("✕")
        btn_clear_s.setObjectName("SecondaryBtn")
        btn_clear_s.clicked.connect(lambda: self.txt_suffix.clear())
        s_row1.addWidget(btn_clear_s)
        sl.addLayout(s_row1)

        # Interactive Token Chips for Suffix
        s_chips = QHBoxLayout()
        for token, label in [
            ("{ENTER}", "+ Enter"),
            ("{TAB}", "+ Tab"),
            ("{SPACE}", "+ Space"),
            ("{BACKSPACE}", "+ Bksp"),
            ("{ESC}", "+ Esc"),
            ("{DOWN}", "+ Down"),
            ("{DATE}", "+ Date"),
            ("{TIME}", "+ Time"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("ChipBtn")
            btn.clicked.connect(lambda checked=False, t=token: self._append_token(self.txt_suffix, t))
            s_chips.addWidget(btn)
        s_chips.addStretch()
        sl.addLayout(s_chips)
        layout.addWidget(suffix_group)

        # Live Keystroke Preview Box
        preview_group = QGroupBox(tr("lbl_preview", self.config.language))
        self.grp_preview = preview_group
        pr_layout = QVBoxLayout(preview_group)
        self.lbl_preview_text = QLabel()
        self.lbl_preview_text.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 15px; color: #38bdf8; padding: 10px;"
        )
        pr_layout.addWidget(self.lbl_preview_text)
        layout.addWidget(preview_group)

        layout.addStretch()
        self._update_wedge_preview()
        self.tabs.addTab(tab, tr("tab_wedge", self.config.language))

    def _populate_token_presets(self, combo: QComboBox) -> None:
        combo.clear()
        combo.addItem("Custom / دستی", "CUSTOM")
        combo.addItem("None / هیچکدام", "")
        combo.addItem("Enter / خط بعد", "{ENTER}")
        combo.addItem("Tab / پرش به فیلد بعد", "{TAB}")
        combo.addItem("Space / فاصله", "{SPACE}")
        combo.addItem("Double Enter / دو خط بعد", "{ENTER}{ENTER}")
        combo.addItem("Tab + Enter", "{TAB}{ENTER}")
        combo.addItem("Backspace / پاک کردن", "{BACKSPACE}")
        combo.addItem("Escape / خروج", "{ESC}")
        combo.addItem("Down Arrow / فلش پایین", "{DOWN}")

    def _append_token(self, line_edit: QLineEdit, token: str) -> None:
        line_edit.setText(line_edit.text() + token)

    def _on_prefix_preset_changed(self, idx: int) -> None:
        val = self.combo_prefix_preset.currentData()
        if val != "CUSTOM":
            self.txt_prefix.setText(val)

    def _on_suffix_preset_changed(self, idx: int) -> None:
        val = self.combo_suffix_preset.currentData()
        if val != "CUSTOM":
            self.txt_suffix.setText(val)

    def _on_wedge_text_changed(self) -> None:
        self._update_wedge_preview()
        # Persist immediately to config
        self.config_manager.save(
            prefix=self.txt_prefix.text(),
            suffix=self.txt_suffix.text(),
        )

    def _update_wedge_preview(self) -> None:
        sample = "987654321012"
        p = self.txt_prefix.text()
        s = self.txt_suffix.text()
        preview = format_token_preview(p, sample, s)
        self.lbl_preview_text.setText(f"Typing sequence:  {preview}")

    # ==========================================================================
    # TAB 3: Connection Assistant & Dynamic QR Code Generator
    # ==========================================================================
    def _build_connection_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)

        # Top Network Configuration Bar
        top_bar = QHBoxLayout()
        self.lbl_lan_ip_header = QLabel(tr("lbl_lan_ip", self.config.language))
        top_bar.addWidget(self.lbl_lan_ip_header)

        self.combo_interfaces = QComboBox()
        self.detected_ips = get_active_lan_ips()
        for iface in self.detected_ips:
            label = f"{iface['ip']} ({iface['interface']})"
            self.combo_interfaces.addItem(label, iface["ip"])
        self.combo_interfaces.currentIndexChanged.connect(self._on_lan_interface_changed)
        top_bar.addWidget(self.combo_interfaces, stretch=1)

        self.btn_refresh_net = QPushButton("⟳")
        self.btn_refresh_net.setObjectName("SecondaryBtn")
        self.btn_refresh_net.clicked.connect(self._refresh_network_interfaces)
        top_bar.addWidget(self.btn_refresh_net)

        self.btn_copy_active_url = QPushButton(tr("btn_copy_url", self.config.language))
        self.btn_copy_active_url.clicked.connect(self._copy_http_forwarding_url)
        top_bar.addWidget(self.btn_copy_active_url)

        layout.addLayout(top_bar)

        # Sub-Notebook for 3 QR Code Modes
        self.qr_subtabs = QTabWidget()
        layout.addWidget(self.qr_subtabs, stretch=1)

        # Subtab 1: Standard Forwarding URL QR
        sub1 = QWidget()
        l1 = QHBoxLayout(sub1)
        self.lbl_qr_url_img = QLabel()
        self.lbl_qr_url_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l1.addWidget(self.lbl_qr_url_img)

        info1 = QVBoxLayout()
        self.lbl_desc_qr_url = QLabel(tr("desc_qr_url", self.config.language))
        self.lbl_desc_qr_url.setWordWrap(True)
        info1.addWidget(self.lbl_desc_qr_url)
        self.txt_url_display = QLineEdit()
        self.txt_url_display.setReadOnly(True)
        info1.addWidget(self.txt_url_display)
        info1.addStretch()
        l1.addLayout(info1, stretch=1)
        self.qr_subtabs.addTab(sub1, tr("subtab_qr_url", self.config.language))

        # Subtab 2: 1-Scan Continuous Mode Deep Link QR
        sub2 = QWidget()
        l2 = QHBoxLayout(sub2)
        self.lbl_qr_direct_img = QLabel()
        self.lbl_qr_direct_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l2.addWidget(self.lbl_qr_direct_img)

        info2 = QVBoxLayout()
        self.lbl_desc_qr_direct = QLabel(tr("desc_qr_direct", self.config.language))
        self.lbl_desc_qr_direct.setWordWrap(True)
        self.lbl_desc_qr_direct.setStyleSheet("font-size: 14px; font-weight: bold; color: #10b981;")
        info2.addWidget(self.lbl_desc_qr_direct)
        self.txt_direct_display = QLineEdit()
        self.txt_direct_display.setReadOnly(True)
        info2.addWidget(self.txt_direct_display)
        info2.addStretch()
        l2.addLayout(info2, stretch=1)
        self.qr_subtabs.addTab(sub2, tr("subtab_qr_direct", self.config.language))

        # Subtab 3: Send Barcode to Phone (binaryeye://encode)
        sub3 = QWidget()
        l3 = QHBoxLayout(sub3)
        self.lbl_qr_encode_img = QLabel()
        self.lbl_qr_encode_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l3.addWidget(self.lbl_qr_encode_img)

        form3 = QVBoxLayout()
        self.lbl_desc_qr_encode = QLabel(tr("desc_qr_encode", self.config.language))
        self.lbl_desc_qr_encode.setWordWrap(True)
        form3.addWidget(self.lbl_desc_qr_encode)

        self.lbl_encode_txt_hdr = QLabel(tr("lbl_encode_text", self.config.language))
        form3.addWidget(self.lbl_encode_txt_hdr)
        self.txt_encode_content = QLineEdit("https://github.com/ouncommono/BinaryReceptor")
        self.txt_encode_content.textChanged.connect(self._render_encode_qr)
        form3.addWidget(self.txt_encode_content)

        self.lbl_encode_fmt_hdr = QLabel(tr("lbl_encode_format", self.config.language))
        form3.addWidget(self.lbl_encode_fmt_hdr)
        self.combo_encode_format = QComboBox()
        self.combo_encode_format.addItems(BINARYEYE_FORMATS)
        self.combo_encode_format.currentIndexChanged.connect(self._render_encode_qr)
        form3.addWidget(self.combo_encode_format)

        form3.addStretch()
        l3.addLayout(form3, stretch=1)
        self.qr_subtabs.addTab(sub3, tr("subtab_qr_encode", self.config.language))

        self.tabs.addTab(tab, tr("tab_connection", self.config.language))
        self._refresh_all_qrs()

    def _on_lan_interface_changed(self) -> None:
        self._refresh_all_qrs()

    def _refresh_network_interfaces(self) -> None:
        self.combo_interfaces.clear()
        self.detected_ips = get_active_lan_ips()
        for iface in self.detected_ips:
            label = f"{iface['ip']} ({iface['interface']})"
            self.combo_interfaces.addItem(label, iface["ip"])
        self._refresh_all_qrs()

    def _get_selected_ip(self) -> str:
        ip = self.combo_interfaces.currentData()
        return str(ip) if ip else get_primary_lan_ip()

    def _refresh_all_qrs(self) -> None:
        ip = self._get_selected_ip()
        port = self.config.http_port

        # 1. Standard URL
        url = build_forwarding_url(ip, port)
        self.txt_url_display.setText(url)
        png1 = generate_qr_png_bytes(url, box_size=5, border=1)
        pm1 = QPixmap()
        pm1.loadFromData(png1)
        self.lbl_qr_url_img.setPixmap(pm1.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))

        # 2. Continuous Scan Deep Link
        deep_link = build_continuous_scan_url(ip, port)
        self.txt_direct_display.setText(deep_link)
        png2 = generate_qr_png_bytes(deep_link, box_size=5, border=1)
        pm2 = QPixmap()
        pm2.loadFromData(png2)
        self.lbl_qr_direct_img.setPixmap(pm2.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))

        # 3. Encode Barcode
        self._render_encode_qr()

    def _render_encode_qr(self) -> None:
        content = self.txt_encode_content.text() or "BinaryReceptor"
        fmt = self.combo_encode_format.currentText()
        encode_url = build_encode_url(content, fmt)
        png = generate_qr_png_bytes(encode_url, box_size=5, border=1)
        pm = QPixmap()
        pm.loadFromData(png)
        self.lbl_qr_encode_img.setPixmap(pm.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))

    def _copy_http_forwarding_url(self) -> None:
        url = self.txt_url_display.text()
        QApplication.clipboard().setText(url)
        QMessageBox.information(self, tr("app_title", self.config.language), tr("url_copied", self.config.language))

    # ==========================================================================
    # TAB 4: Settings & Hardware Configuration
    # ==========================================================================
    def _build_settings_tab(self) -> None:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(14, 14, 14, 14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(14)

        # 1. General & Operation Mode
        grp_gen = QGroupBox(tr("sec_general", self.config.language))
        self.grp_gen = grp_gen
        gl = QGridLayout(grp_gen)

        self.lbl_mode_setting = QLabel(tr("lbl_mode", self.config.language))
        gl.addWidget(self.lbl_mode_setting, 0, 0)
        self.combo_mode = QComboBox()
        self.combo_mode.addItem(tr("opt_mode_both", self.config.language), "both")
        self.combo_mode.addItem(tr("opt_mode_http", self.config.language), "http")
        self.combo_mode.addItem(tr("opt_mode_bt", self.config.language), "bluetooth")
        idx = self.combo_mode.findData(self.config.mode)
        if idx >= 0:
            self.combo_mode.setCurrentIndex(idx)
        gl.addWidget(self.combo_mode, 0, 1)

        self.chk_auto_start_srv = QCheckBox(tr("chk_auto_start", self.config.language))
        self.chk_auto_start_srv.setChecked(self.config.auto_start)
        gl.addWidget(self.chk_auto_start_srv, 1, 0, 1, 2)

        self.chk_start_windows = QCheckBox(tr("chk_start_windows", self.config.language))
        self.chk_start_windows.setChecked(self.config.start_with_windows)
        gl.addWidget(self.chk_start_windows, 2, 0, 1, 2)

        self.chk_min_tray = QCheckBox(tr("chk_min_tray", self.config.language))
        self.chk_min_tray.setChecked(self.config.minimize_to_tray)
        gl.addWidget(self.chk_min_tray, 3, 0, 1, 2)

        self.chk_beep = QCheckBox(tr("chk_beep", self.config.language))
        self.chk_beep.setChecked(self.config.audio_feedback)
        gl.addWidget(self.chk_beep, 4, 0, 1, 2)

        layout.addWidget(grp_gen)

        # 2. Network / HTTP
        grp_net = QGroupBox(tr("sec_network", self.config.language))
        self.grp_net = grp_net
        nl = QGridLayout(grp_net)

        self.lbl_host_setting = QLabel(tr("lbl_host", self.config.language))
        nl.addWidget(self.lbl_host_setting, 0, 0)
        self.txt_host = QLineEdit(self.config.http_host)
        nl.addWidget(self.txt_host, 0, 1)

        self.lbl_port_setting = QLabel(tr("lbl_port", self.config.language))
        nl.addWidget(self.lbl_port_setting, 1, 0)
        self.spin_port = QSpinBox()
        self.spin_port.setRange(1024, 65535)
        self.spin_port.setValue(self.config.http_port)
        nl.addWidget(self.spin_port, 1, 1)

        layout.addWidget(grp_net)

        # 3. Deduplication Engine
        grp_dedup = QGroupBox(tr("sec_dedup", self.config.language))
        self.grp_dedup = grp_dedup
        dl = QGridLayout(grp_dedup)

        self.chk_dedup = QCheckBox(tr("chk_dedup_enabled", self.config.language))
        self.chk_dedup.setChecked(self.config.deduplication_enabled)
        dl.addWidget(self.chk_dedup, 0, 0, 1, 2)

        self.lbl_dedup_win = QLabel(tr("lbl_dedup_window", self.config.language))
        dl.addWidget(self.lbl_dedup_win, 1, 0)
        self.spin_dedup_win = QSpinBox()
        self.spin_dedup_win.setRange(100, 10000)
        self.spin_dedup_win.setSingleStep(250)
        self.spin_dedup_win.setValue(self.config.deduplication_window_ms)
        dl.addWidget(self.spin_dedup_win, 1, 1)

        layout.addWidget(grp_dedup)

        # 4. Keystroke Output & Wedging
        grp_wedge = QGroupBox(tr("sec_wedge", self.config.language))
        self.grp_wedge = grp_wedge
        wl = QGridLayout(grp_wedge)

        self.lbl_out_mode = QLabel(tr("lbl_out_mode", self.config.language))
        wl.addWidget(self.lbl_out_mode, 0, 0)
        self.combo_out_mode = QComboBox()
        self.combo_out_mode.addItem(tr("opt_out_type", self.config.language), "type")
        self.combo_out_mode.addItem(tr("opt_out_paste", self.config.language), "paste")
        self.combo_out_mode.addItem(tr("opt_out_copy", self.config.language), "copy_only")
        idx_m = self.combo_out_mode.findData(self.config.output_mode)
        if idx_m >= 0:
            self.combo_out_mode.setCurrentIndex(idx_m)
        wl.addWidget(self.combo_out_mode, 0, 1)

        self.lbl_inter_key = QLabel(tr("lbl_inter_key", self.config.language))
        wl.addWidget(self.lbl_inter_key, 1, 0)
        self.spin_inter_key = QSpinBox()
        self.spin_inter_key.setRange(0, 100)
        self.spin_inter_key.setValue(self.config.inter_key_delay_ms)
        wl.addWidget(self.spin_inter_key, 1, 1)

        self.lbl_pre_delay = QLabel(tr("lbl_pre_delay", self.config.language))
        wl.addWidget(self.lbl_pre_delay, 2, 0)
        self.spin_pre_delay = QSpinBox()
        self.spin_pre_delay.setRange(0, 5000)
        self.spin_pre_delay.setSingleStep(100)
        self.spin_pre_delay.setValue(self.config.pre_typing_delay_ms)
        wl.addWidget(self.spin_pre_delay, 2, 1)

        self.chk_restore_clip = QCheckBox(tr("chk_restore_clip", self.config.language))
        self.chk_restore_clip.setChecked(self.config.restore_clipboard)
        wl.addWidget(self.chk_restore_clip, 3, 0, 1, 2)

        layout.addWidget(grp_wedge)

        # 5. Filters & Transforms
        grp_filt = QGroupBox(tr("sec_filters", self.config.language))
        self.grp_filt = grp_filt
        fl = QGridLayout(grp_filt)

        self.chk_trim_space = QCheckBox(tr("chk_trim_space", self.config.language))
        self.chk_trim_space.setChecked(self.config.trim_whitespace)
        fl.addWidget(self.chk_trim_space, 0, 0, 1, 2)

        self.lbl_replace_nl = QLabel(tr("lbl_replace_newlines", self.config.language))
        fl.addWidget(self.lbl_replace_nl, 1, 0)
        self.combo_nl = QComboBox()
        self.combo_nl.addItem(tr("opt_nl_none", self.config.language), "none")
        self.combo_nl.addItem(tr("opt_nl_tab", self.config.language), "tab")
        self.combo_nl.addItem(tr("opt_nl_space", self.config.language), "space")
        idx_nl = self.combo_nl.findData(self.config.replace_newlines)
        if idx_nl >= 0:
            self.combo_nl.setCurrentIndex(idx_nl)
        fl.addWidget(self.combo_nl, 1, 1)

        self.lbl_regex_pat = QLabel(tr("lbl_regex_pat", self.config.language))
        fl.addWidget(self.lbl_regex_pat, 2, 0)
        self.txt_regex_pat = QLineEdit(self.config.regex_pattern)
        fl.addWidget(self.txt_regex_pat, 2, 1)

        self.lbl_regex_rep = QLabel(tr("lbl_regex_rep", self.config.language))
        fl.addWidget(self.lbl_regex_rep, 3, 0)
        self.txt_regex_rep = QLineEdit(self.config.regex_replacement)
        fl.addWidget(self.txt_regex_rep, 3, 1)

        self.chk_auto_url = QCheckBox(tr("chk_auto_url", self.config.language))
        self.chk_auto_url.setChecked(self.config.auto_open_urls)
        fl.addWidget(self.chk_auto_url, 4, 0, 1, 2)

        self.chk_copy_always = QCheckBox(tr("chk_copy_always", self.config.language))
        self.chk_copy_always.setChecked(self.config.copy_to_clipboard)
        fl.addWidget(self.chk_copy_always, 5, 0, 1, 2)

        layout.addWidget(grp_filt)

        # Save Button
        self.btn_save_settings = QPushButton(tr("btn_save_settings", self.config.language))
        self.btn_save_settings.clicked.connect(self._save_settings_from_ui)
        layout.addWidget(self.btn_save_settings)

        scroll.setWidget(content)
        tab_layout.addWidget(scroll)
        self.tabs.addTab(tab, tr("tab_settings", self.config.language))

    def _save_settings_from_ui(self) -> None:
        old_mode = self.config.mode
        old_port = self.config.http_port
        old_host = self.config.http_host

        new_mode = self.combo_mode.currentData()
        new_port = self.spin_port.value()
        new_host = self.txt_host.text().strip() or "0.0.0.0"

        # Apply Windows Run autostart if changed
        if self.chk_start_windows.isChecked() != self.config.start_with_windows:
            set_autostart_registry(self.chk_start_windows.isChecked())

        self.config = self.config_manager.save(
            mode=new_mode,
            http_host=new_host,
            http_port=new_port,
            auto_start=self.chk_auto_start_srv.isChecked(),
            start_with_windows=self.chk_start_windows.isChecked(),
            minimize_to_tray=self.chk_min_tray.isChecked(),
            audio_feedback=self.chk_beep.isChecked(),
            deduplication_enabled=self.chk_dedup.isChecked(),
            deduplication_window_ms=self.spin_dedup_win.value(),
            output_mode=self.combo_out_mode.currentData(),
            inter_key_delay_ms=self.spin_inter_key.value(),
            pre_typing_delay_ms=self.spin_pre_delay.value(),
            restore_clipboard=self.chk_restore_clip.isChecked(),
            trim_whitespace=self.chk_trim_space.isChecked(),
            replace_newlines=self.combo_nl.currentData(),
            regex_pattern=self.txt_regex_pat.text(),
            regex_replacement=self.txt_regex_rep.text(),
            auto_open_urls=self.chk_auto_url.isChecked(),
            copy_to_clipboard=self.chk_copy_always.isChecked(),
        )

        self.dedup.update_settings(
            window_ms=self.config.deduplication_window_ms,
            enabled=self.config.deduplication_enabled,
        )

        # Restart servers if mode/port/host changed while active
        if self.is_server_active and (new_mode != old_mode or new_port != old_port or new_host != old_host):
            self.stop_server()
            self.start_server()

        self._refresh_all_qrs()
        QMessageBox.information(
            self,
            tr("app_title", self.config.language),
            tr("settings_saved", self.config.language),
        )

    # ==========================================================================
    # SERVER LIFECYCLE & CORE ORCHESTRATION
    # ==========================================================================
    def toggle_server(self) -> None:
        if self.is_server_active:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self) -> None:
        if self.is_server_active:
            return

        mode = self.config.mode
        bt_ok = False
        http_ok = False

        # 1. Start Bluetooth if mode is both or bluetooth
        if mode in ("both", "bluetooth"):
            self.bt_server = BluetoothServerController(
                service_uuid=self.config.service_uuid,
                service_name=self.config.service_name,
                on_scan=self.enqueue_scan,
                on_status_change=lambda s: self.signals.bt_status_changed.emit(s),
            )
            bt_ok, bt_msg = self.bt_server.start()
            if not bt_ok:
                self.badge_bt.setText(f"Bluetooth: {self.bt_server.status}")
                self.badge_bt.setProperty("class", "StatusBadgeInactive")
            else:
                self.badge_bt.setText(f"Bluetooth: {self.bt_server.status}")
                self.badge_bt.setProperty("class", "StatusBadgeActive")
        else:
            self.badge_bt.setText("Bluetooth: Standby")
            self.badge_bt.setProperty("class", "StatusBadgeInactive")

        # 2. Start HTTP if mode is both or http
        if mode in ("both", "http"):
            self.http_server = HttpServerController(
                host=self.config.http_host,
                port=self.config.http_port,
                on_scan=self.enqueue_scan,
            )
            http_ok, http_msg = self.http_server.start()
            if not http_ok:
                self.badge_http.setText(f"HTTP: Error ({self.config.http_port})")
                self.badge_http.setProperty("class", "StatusBadgeInactive")
                QMessageBox.warning(self, "HTTP Server", http_msg)
            else:
                self.badge_http.setText(f"HTTP: :{self.config.http_port}")
                self.badge_http.setProperty("class", "StatusBadgeActive")
        else:
            self.badge_http.setText("HTTP: Standby")
            self.badge_http.setProperty("class", "StatusBadgeInactive")

        self.is_server_active = bt_ok or http_ok
        self._update_power_button()
        self.tray.update_state(self.is_server_active, self.config.mode, self.config.language)

    def stop_server(self) -> None:
        if self.http_server:
            self.http_server.stop()
            self.http_server = None

        if self.bt_server:
            self.bt_server.stop()
            self.bt_server = None

        self.is_server_active = False
        self.badge_bt.setText("Bluetooth: Standby")
        self.badge_bt.setProperty("class", "StatusBadgeInactive")
        self.badge_http.setText("HTTP: Standby")
        self.badge_http.setProperty("class", "StatusBadgeInactive")

        self._update_power_button()
        self.tray.update_state(False, self.config.mode, self.config.language)

    def _update_power_button(self) -> None:
        if self.is_server_active:
            self.btn_master_power.setObjectName("MasterPowerBtnRunning")
            self.btn_master_power.setText(f"● {tr('btn_stop', self.config.language)}")
        else:
            self.btn_master_power.setObjectName("MasterPowerBtnStopped")
            self.btn_master_power.setText(f"▶ {tr('btn_start', self.config.language)}")
        self.btn_master_power.setStyle(self.btn_master_power.style())

    @Slot(str)
    def _on_bt_status_changed_ui(self, status: str) -> None:
        self.badge_bt.setText(f"Bluetooth: {status}")
        if "Connected" in status or "Listening" in status:
            self.badge_bt.setProperty("class", "StatusBadgeActive")
        else:
            self.badge_bt.setProperty("class", "StatusBadgeInactive")
        self.badge_bt.setStyle(self.badge_bt.style())

    # ==========================================================================
    # BACKGROUND QUEUE WORKER & SCAN PROCESSING
    # ==========================================================================
    def _start_worker_thread(self) -> None:
        def _worker_loop():
            while not self._worker_stop.is_set():
                try:
                    payload = self.scan_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                self._process_scan_payload(payload)
                self.scan_queue.task_done()

        self._worker_thread = threading.Thread(
            target=_worker_loop, name="BinaryReceptor-Worker", daemon=True
        )
        self._worker_thread.start()

    def enqueue_scan(self, payload: ScanPayload) -> None:
        """Called by HTTP or Bluetooth threads to enqueue incoming scan."""
        self.scan_queue.put(payload)

    def _process_scan_payload(self, payload: ScanPayload) -> None:
        content = payload.content

        # 1. Format Filter Check
        if self.config.allowed_formats.lower() != "all" and payload.format:
            allowed = [f.strip().lower() for f in self.config.allowed_formats.split(",")]
            if payload.format.lower() not in allowed:
                self.signals.scan_received.emit(payload, tr("status_filtered", self.config.language), "Format filtered")
                return

        # 2. Content Transformations
        if self.config.trim_whitespace:
            content = content.strip()

        if self.config.replace_newlines == "tab":
            content = content.replace("\r\n", "\t").replace("\n", "\t")
        elif self.config.replace_newlines == "space":
            content = content.replace("\r\n", " ").replace("\n", " ")

        if self.config.regex_pattern:
            try:
                content = re.sub(self.config.regex_pattern, self.config.regex_replacement, content)
            except re.error:
                pass

        payload.content = content

        # 3. Intelligent Deduplication Engine
        is_dup, dedup_msg = self.dedup.check_and_record(
            content=content,
            source=payload.source,
            scan_id=payload.scan_id,
        )

        if is_dup:
            self.cnt_dedup += 1
            self.signals.stats_updated.emit()
            self.signals.scan_received.emit(payload, tr("status_dedup", self.config.language), dedup_msg)
            return

        # 4. Inject Keystrokes
        try:
            self.injector.inject_scan(
                content=content,
                prefix_template=self.config.prefix,
                suffix_template=self.config.suffix,
                output_mode=self.config.output_mode,
                inter_key_delay_ms=self.config.inter_key_delay_ms,
                pre_typing_delay_ms=self.config.pre_typing_delay_ms,
                restore_clipboard=self.config.restore_clipboard,
                copy_to_clipboard=self.config.copy_to_clipboard,
            )
            status_text = {
                "type": tr("status_typed", self.config.language),
                "paste": tr("status_pasted", self.config.language),
                "copy_only": tr("status_copied", self.config.language),
            }.get(self.config.output_mode, tr("status_typed", self.config.language))
        except Exception as e:
            status_text = f"Error: {e}"

        # 5. Audio Beep Feedback
        if self.config.audio_feedback and winsound:
            try:
                winsound.Beep(self.config.beep_frequency, self.config.beep_duration_ms)
            except Exception:
                pass

        # 6. Auto-Open URLs
        if self.config.auto_open_urls and (content.startswith("http://") or content.startswith("https://")):
            try:
                webbrowser.open(content)
            except Exception:
                pass

        # 7. Update Counters & Emit UI Signals
        self.cnt_total += 1
        if payload.source == "Bluetooth":
            self.cnt_bt += 1
        else:
            self.cnt_http += 1

        self.signals.stats_updated.emit()
        self.signals.scan_received.emit(payload, status_text, "Processed successfully")

    @Slot(object, str, str)
    def _on_scan_received_ui(self, payload: ScanPayload, status_text: str, detail: str) -> None:
        """Insert row into history table on UI thread."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.table_history.insertRow(0)
        self.table_history.setItem(0, 0, QTableWidgetItem(now_str))
        self.table_history.setItem(0, 1, QTableWidgetItem(payload.source))
        self.table_history.setItem(0, 2, QTableWidgetItem(payload.format or "Auto"))
        self.table_history.setItem(0, 3, QTableWidgetItem(payload.content))
        self.table_history.setItem(0, 4, QTableWidgetItem(status_text))

        # Show Tray Toast if enabled
        if self.config.tray_notifications and not self.isVisible():
            title = tr("toast_scan_title", self.config.language, source=payload.source)
            self.tray.show_notification(title, f"{payload.content[:60]}... ({status_text})")

    @Slot()
    def _update_kpi_cards(self) -> None:
        self.kpi_cards["kpi_total_scans"][1].setText(str(self.cnt_total))
        self.kpi_cards["kpi_bt_scans"][1].setText(str(self.cnt_bt))
        self.kpi_cards["kpi_http_scans"][1].setText(str(self.cnt_http))
        self.kpi_cards["kpi_dedup_blocked"][1].setText(str(self.cnt_dedup))

    # ==========================================================================
    # HISTORY TABLE ACTIONS
    # ==========================================================================
    def _retype_selected_scan(self) -> None:
        row = self.table_history.currentRow()
        if row >= 0:
            content_item = self.table_history.item(row, 3)
            if content_item:
                content = content_item.text()
                threading.Thread(
                    target=lambda: self.injector.inject_scan(
                        content=content,
                        prefix_template=self.config.prefix,
                        suffix_template=self.config.suffix,
                        output_mode=self.config.output_mode,
                    ),
                    daemon=True,
                ).start()

    def _copy_selected_scan(self) -> None:
        row = self.table_history.currentRow()
        if row >= 0:
            item = self.table_history.item(row, 3)
            if item:
                QApplication.clipboard().setText(item.text())

    def _clear_history_log(self) -> None:
        res = QMessageBox.question(
            self,
            tr("app_title", self.config.language),
            tr("confirm_clear_log", self.config.language),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if res == QMessageBox.StandardButton.Yes:
            self.table_history.setRowCount(0)
            self.cnt_total = 0
            self.cnt_bt = 0
            self.cnt_http = 0
            self.cnt_dedup = 0
            self.dedup.reset_stats()
            self._update_kpi_cards()

    def _export_csv(self) -> None:
        row_count = self.table_history.rowCount()
        if row_count == 0:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("btn_export_csv", self.config.language),
            f"BinaryReceptor_scans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Channel", "Format", "Content", "Status"])
                for r in range(row_count):
                    writer.writerow([
                        self.table_history.item(r, c).text() if self.table_history.item(r, c) else ""
                        for c in range(5)
                    ])
            QMessageBox.information(
                self,
                tr("app_title", self.config.language),
                tr("export_success", self.config.language, count=row_count, path=file_path),
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    # ==========================================================================
    # LANGUAGE & THEME SWITCHING
    # ==========================================================================
    def toggle_language(self) -> None:
        new_lang = "fa" if self.config.language == "en" else "en"
        self.apply_language(new_lang)
        self.config_manager.save(language=new_lang)

    def apply_language(self, lang: str) -> None:
        self.config.language = lang

        # Flip layout direction for RTL Persian
        if lang == "fa":
            QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            QApplication.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        # Header
        self.lbl_app_title.setText(tr("app_title", lang))
        self.lbl_app_subtitle.setText(tr("app_subtitle", lang))
        self.btn_lang_toggle.setText(tr("lang_switch", lang))
        self._update_power_button()

        # Tab titles
        self.tabs.setTabText(0, tr("tab_dashboard", lang))
        self.tabs.setTabText(1, tr("tab_wedge", lang))
        self.tabs.setTabText(2, tr("tab_connection", lang))
        self.tabs.setTabText(3, tr("tab_settings", lang))

        # KPI labels
        for key in ["kpi_total_scans", "kpi_bt_scans", "kpi_http_scans", "kpi_dedup_blocked"]:
            self.kpi_cards[key][0].setText(tr(key, lang))

        # Dashboard table headers
        self.table_history.setHorizontalHeaderLabels([
            tr("col_time", lang),
            tr("col_channel", lang),
            tr("col_format", lang),
            tr("col_content", lang),
            tr("col_status", lang),
        ])
        self.btn_retype.setText(tr("btn_retype", lang))
        self.btn_copy_content.setText(tr("btn_copy", lang))
        self.btn_export_csv.setText(tr("btn_export_csv", lang))
        self.btn_clear_log.setText(tr("btn_clear_log", lang))

        # Wedge tab
        self.lbl_wedge_title.setText(tr("wedge_title", lang))
        self.lbl_wedge_desc.setText(tr("wedge_desc", lang))
        self.grp_preview.setTitle(tr("lbl_preview", lang))

        # Connection tab
        self.lbl_lan_ip_header.setText(tr("lbl_lan_ip", lang))
        self.btn_copy_active_url.setText(tr("btn_copy_url", lang))
        self.qr_subtabs.setTabText(0, tr("subtab_qr_url", lang))
        self.qr_subtabs.setTabText(1, tr("subtab_qr_direct", lang))
        self.qr_subtabs.setTabText(2, tr("subtab_qr_encode", lang))
        self.lbl_desc_qr_url.setText(tr("desc_qr_url", lang))
        self.lbl_desc_qr_direct.setText(tr("desc_qr_direct", lang))
        self.lbl_desc_qr_encode.setText(tr("desc_qr_encode", lang))
        self.lbl_encode_txt_hdr.setText(tr("lbl_encode_text", lang))
        self.lbl_encode_fmt_hdr.setText(tr("lbl_encode_format", lang))

        # Settings tab
        self.grp_gen.setTitle(tr("sec_general", lang))
        self.lbl_mode_setting.setText(tr("lbl_mode", lang))
        self.chk_auto_start_srv.setText(tr("chk_auto_start", lang))
        self.chk_start_windows.setText(tr("chk_start_windows", lang))
        self.chk_min_tray.setText(tr("chk_min_tray", lang))
        self.chk_beep.setText(tr("chk_beep", lang))

        self.grp_net.setTitle(tr("sec_network", lang))
        self.lbl_host_setting.setText(tr("lbl_host", lang))
        self.lbl_port_setting.setText(tr("lbl_port", lang))

        self.grp_dedup.setTitle(tr("sec_dedup", lang))
        self.chk_dedup.setText(tr("chk_dedup_enabled", lang))
        self.lbl_dedup_win.setText(tr("lbl_dedup_window", lang))

        self.grp_wedge.setTitle(tr("sec_wedge", lang))
        self.lbl_out_mode.setText(tr("lbl_out_mode", lang))
        self.lbl_inter_key.setText(tr("lbl_inter_key", lang))
        self.lbl_pre_delay.setText(tr("lbl_pre_delay", lang))
        self.chk_restore_clip.setText(tr("chk_restore_clip", lang))

        self.grp_filt.setTitle(tr("sec_filters", lang))
        self.chk_trim_space.setText(tr("chk_trim_space", lang))
        self.lbl_replace_nl.setText(tr("lbl_replace_newlines", lang))
        self.lbl_regex_pat.setText(tr("lbl_regex_pat", lang))
        self.lbl_regex_rep.setText(tr("lbl_regex_rep", lang))
        self.chk_auto_url.setText(tr("chk_auto_url", lang))
        self.chk_copy_always.setText(tr("chk_copy_always", lang))
        self.btn_save_settings.setText(tr("btn_save_settings", lang))

        # Update Tray
        self.tray.update_state(self.is_server_active, self.config.mode, lang)

    def toggle_theme(self) -> None:
        new_theme = "light" if self.config.theme == "dark" else "dark"
        self.apply_theme(new_theme)
        self.config_manager.save(theme=new_theme)

    def apply_theme(self, theme: str) -> None:
        self.config.theme = theme
        if theme == "light":
            QApplication.instance().setStyleSheet(LIGHT_STYLESHEET)
            self.btn_theme_toggle.setText("🌙 Dark")
        else:
            QApplication.instance().setStyleSheet(DARK_STYLESHEET)
            self.btn_theme_toggle.setText("☀️ Light")

    # ==========================================================================
    # TRAY & WINDOW MANAGEMENT
    # ==========================================================================
    def show_and_activate(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _show_qr_tab(self) -> None:
        self.show_and_activate()
        self.tabs.setCurrentIndex(2)

    def _change_mode_from_tray(self, mode: str) -> None:
        self.config_manager.save(mode=mode)
        if self.is_server_active:
            self.stop_server()
            self.start_server()

    @Slot(object)
    def _on_config_reloaded_from_disk(self, new_config: AppConfig) -> None:
        """Called when settings.ini is modified externally on disk."""
        old_mode = self.config.mode
        old_port = self.config.http_port
        old_host = self.config.http_host
        self.config = new_config

        self.txt_prefix.setText(new_config.prefix)
        self.txt_suffix.setText(new_config.suffix)
        self.spin_port.setValue(new_config.http_port)
        self.txt_host.setText(new_config.http_host)
        self.spin_dedup_win.setValue(new_config.deduplication_window_ms)
        self.chk_dedup.setChecked(new_config.deduplication_enabled)

        self.dedup.update_settings(
            window_ms=new_config.deduplication_window_ms,
            enabled=new_config.deduplication_enabled,
        )

        if self.is_server_active and (
            new_config.mode != old_mode
            or new_config.http_port != old_port
            or new_config.http_host != old_host
        ):
            self.stop_server()
            self.start_server()

        self._refresh_all_qrs()

    def closeEvent(self, event) -> None:
        if self.config.minimize_to_tray:
            event.ignore()
            self.hide()
            if self.config.tray_notifications:
                self.tray.show_notification(
                    tr("app_title", self.config.language),
                    "BinaryReceptor is minimized to system tray.",
                    msec=2000,
                )
        else:
            self.exit_application()

    def exit_application(self) -> None:
        self.stop_server()
        self._worker_stop.set()
        self.config_manager.close()
        QApplication.quit()
