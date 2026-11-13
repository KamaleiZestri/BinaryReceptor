"""Modern high-DPI responsive Dark and Light QSS stylesheets for BinaryReceptor v3.1.0.

Engineered with full RTL (Right-to-Left) Persian layout support and beautiful typography
(Vazirmatn, Segoe UI, Tahoma).
"""
from __future__ import annotations

FONT_FAMILY = '"Vazirmatn", "Segoe UI", "Tahoma", -apple-system, sans-serif'

DARK_STYLESHEET = f"""
/* Global Reset and Font */
QWidget {{
    background-color: #0f172a;
    color: #f8fafc;
    font-family: {FONT_FAMILY};
    font-size: 13px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}}

/* Top Header Bar */
#HeaderCard {{
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px;
}}

#AppTitle {{
    font-size: 20px;
    font-weight: bold;
    color: #ffffff;
}}

#AppSubtitle {{
    font-size: 12px;
    color: #94a3b8;
}}

/* Master Power Button */
QPushButton#MasterPowerBtnRunning {{
    background-color: #065f46;
    color: #ecfdf5;
    border: 1px solid #10b981;
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
    padding: 8px 18px;
}}
QPushButton#MasterPowerBtnRunning:hover {{
    background-color: #047857;
}}

QPushButton#MasterPowerBtnStopped {{
    background-color: #7f1d1d;
    color: #fef2f2;
    border: 1px solid #ef4444;
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
    padding: 8px 18px;
}}
QPushButton#MasterPowerBtnStopped:hover {{
    background-color: #991b1b;
}}

/* Dynamic Top Status & KPI Cards */
.KPICard {{
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px;
}}

.KPICardActive {{
    background-color: #0d2822;
    border: 1px solid #10b981;
    border-radius: 8px;
    padding: 10px;
}}

.KPICardInactive {{
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px;
}}

.KPICardStopped {{
    background-color: #2a1215;
    border: 1px solid #ef4444;
    border-radius: 8px;
    padding: 10px;
}}

.KPICardAmber {{
    background-color: #2b1d09;
    border: 1px solid #f59e0b;
    border-radius: 8px;
    padding: 10px;
}}

.KPICardLabel {{
    color: #94a3b8;
    font-size: 11px;
    font-weight: 600;
}}

.KPICardValue {{
    color: #ffffff;
    font-size: 20px;
    font-weight: bold;
}}

/* Status Badges */
.StatusBadge {{
    background-color: #334155;
    color: #cbd5e1;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 500;
}}

.StatusBadgeActive {{
    background-color: #064e3b;
    color: #6ee7b7;
    border: 1px solid #059669;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: bold;
}}

.StatusBadgeInactive {{
    background-color: #334155;
    color: #94a3b8;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
}}

.StatusBadgeError {{
    background-color: #7f1d1d;
    color: #fca5a5;
    border: 1px solid #ef4444;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: bold;
}}

/* Tab Widget & Navigation */
QTabWidget::pane {{
    border: 1px solid #334155;
    background-color: #1e293b;
    border-radius: 8px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: #0f172a;
    color: #94a3b8;
    border: 1px solid #334155;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 9px 18px;
    margin-right: 4px;
    font-weight: 600;
    font-size: 13px;
}}

QTabBar::tab:selected {{
    background-color: #1e293b;
    color: #38bdf8;
    border-bottom: 2px solid #38bdf8;
}}

QTabBar::tab:hover:!selected {{
    background-color: #1e293b;
    color: #f8fafc;
}}

/* Standard Push Buttons */
QPushButton {{
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #3b82f6;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #1d4ed8;
}}

QPushButton:pressed {{
    background-color: #1e40af;
}}

QPushButton#SecondaryBtn {{
    background-color: #334155;
    color: #f8fafc;
    border: 1px solid #475569;
}}
QPushButton#SecondaryBtn:hover {{
    background-color: #475569;
}}

QPushButton#BtnSaveSettings {{
    background-color: #059669;
    color: #ffffff;
    border: 1px solid #10b981;
    font-weight: bold;
    padding: 8px 18px;
}}
QPushButton#BtnSaveSettings:hover {{
    background-color: #047857;
}}

QPushButton#BtnResetDefaults {{
    background-color: #451a03;
    color: #fde68a;
    border: 1px solid #b45309;
    font-weight: 600;
    padding: 8px 16px;
}}
QPushButton#BtnResetDefaults:hover {{
    background-color: #78350f;
}}

QPushButton#ChipBtn {{
    background-color: #1e293b;
    color: #38bdf8;
    border: 1px solid #0284c7;
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#ChipBtn:hover {{
    background-color: #0369a1;
    color: #ffffff;
}}

/* Sticky Settings Footer */
#StickyFooter {{
    background-color: #1e293b;
    border-top: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 14px;
}}

#UnsavedChangesLabel {{
    color: #f59e0b;
    font-weight: bold;
    font-size: 13px;
}}

#AllSavedLabel {{
    color: #10b981;
    font-weight: 600;
    font-size: 13px;
}}

/* Line Edits & Text Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
    background-color: #0f172a;
    color: #ffffff;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 1px solid #38bdf8;
}}

/* Table Views */
QTableWidget, QTableView {{
    background-color: #0f172a;
    alternate-background-color: #141f32;
    border: 1px solid #334155;
    border-radius: 6px;
    gridline-color: #1e293b;
    color: #f8fafc;
    font-size: 12px;
}}

QHeaderView::section {{
    background-color: #1e293b;
    color: #94a3b8;
    padding: 7px;
    font-weight: bold;
    border: none;
    border-bottom: 1px solid #334155;
}}

QTableWidget::item {{
    padding: 5px;
}}

QTableWidget::item:selected {{
    background-color: #2563eb;
    color: #ffffff;
}}

/* ScrollBars */
QScrollBar:vertical {{
    background: #0f172a;
    width: 8px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: #334155;
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: #475569;
}}

/* Group Boxes & Cards */
QGroupBox {{
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    font-weight: bold;
    color: #38bdf8;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
}}

/* Checkboxes */
QCheckBox {{
    spacing: 8px;
    color: #f1f5f9;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #475569;
    background: #0f172a;
}}
QCheckBox::indicator:checked {{
    background-color: #2563eb;
    border-color: #38bdf8;
}}
"""

LIGHT_STYLESHEET = f"""
/* Global Reset and Font */
QWidget {{
    background-color: #f8fafc;
    color: #0f172a;
    font-family: {FONT_FAMILY};
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}}

/* Top Header Bar */
#HeaderCard {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px;
}}

#AppTitle {{
    font-size: 20px;
    font-weight: bold;
    color: #0f172a;
}}

#AppSubtitle {{
    font-size: 12px;
    color: #64748b;
}}

/* Master Power Button */
QPushButton#MasterPowerBtnRunning {{
    background-color: #10b981;
    color: #ffffff;
    border: 1px solid #059669;
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
    padding: 8px 18px;
}}
QPushButton#MasterPowerBtnRunning:hover {{
    background-color: #059669;
}}

QPushButton#MasterPowerBtnStopped {{
    background-color: #ef4444;
    color: #ffffff;
    border: 1px solid #dc2626;
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
    padding: 8px 18px;
}}
QPushButton#MasterPowerBtnStopped:hover {{
    background-color: #dc2626;
}}

/* Dynamic Top Status & KPI Cards */
.KPICard {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
}}

.KPICardActive {{
    background-color: #d1fae5;
    border: 1px solid #10b981;
    border-radius: 8px;
    padding: 10px;
}}

.KPICardInactive {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
}}

.KPICardStopped {{
    background-color: #fee2e2;
    border: 1px solid #ef4444;
    border-radius: 8px;
    padding: 10px;
}}

.KPICardAmber {{
    background-color: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 8px;
    padding: 10px;
}}

.KPICardLabel {{
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
}}

.KPICardValue {{
    color: #0f172a;
    font-size: 20px;
    font-weight: bold;
}}

/* Status Badges */
.StatusBadge {{
    background-color: #e2e8f0;
    color: #475569;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 500;
}}

.StatusBadgeActive {{
    background-color: #d1fae5;
    color: #065f46;
    border: 1px solid #10b981;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: bold;
}}

.StatusBadgeInactive {{
    background-color: #e2e8f0;
    color: #64748b;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
}}

.StatusBadgeError {{
    background-color: #fee2e2;
    color: #991b1b;
    border: 1px solid #ef4444;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: bold;
}}

/* Tab Widget & Navigation */
QTabWidget::pane {{
    border: 1px solid #e2e8f0;
    background-color: #ffffff;
    border-radius: 8px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: #f1f5f9;
    color: #64748b;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 9px 18px;
    margin-right: 4px;
    font-weight: 600;
    font-size: 13px;
}}

QTabBar::tab:selected {{
    background-color: #ffffff;
    color: #0284c7;
    border-bottom: 2px solid #0284c7;
}}

QTabBar::tab:hover:!selected {{
    background-color: #ffffff;
    color: #0f172a;
}}

/* Standard Push Buttons */
QPushButton {{
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #1d4ed8;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #1d4ed8;
}}

QPushButton#SecondaryBtn {{
    background-color: #e2e8f0;
    color: #1e293b;
    border: 1px solid #cbd5e1;
}}
QPushButton#SecondaryBtn:hover {{
    background-color: #cbd5e1;
}}

QPushButton#BtnSaveSettings {{
    background-color: #059669;
    color: #ffffff;
    border: 1px solid #047857;
    font-weight: bold;
    padding: 8px 18px;
}}
QPushButton#BtnSaveSettings:hover {{
    background-color: #047857;
}}

QPushButton#BtnResetDefaults {{
    background-color: #fef3c7;
    color: #92400e;
    border: 1px solid #d97706;
    font-weight: 600;
    padding: 8px 16px;
}}
QPushButton#BtnResetDefaults:hover {{
    background-color: #fde68a;
}}

QPushButton#ChipBtn {{
    background-color: #f0f9ff;
    color: #0284c7;
    border: 1px solid #bae6fd;
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#ChipBtn:hover {{
    background-color: #0284c7;
    color: #ffffff;
}}

/* Sticky Settings Footer */
#StickyFooter {{
    background-color: #ffffff;
    border-top: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px;
}}

#UnsavedChangesLabel {{
    color: #d97706;
    font-weight: bold;
    font-size: 13px;
}}

#AllSavedLabel {{
    color: #059669;
    font-weight: 600;
    font-size: 13px;
}}

/* Line Edits & Text Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 1px solid #0284c7;
}}

/* Table Views */
QTableWidget, QTableView {{
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #f1f5f9;
    color: #0f172a;
    font-size: 12px;
}}

QHeaderView::section {{
    background-color: #f1f5f9;
    color: #475569;
    padding: 7px;
    font-weight: bold;
    border: none;
    border-bottom: 1px solid #e2e8f0;
}}

QTableWidget::item:selected {{
    background-color: #2563eb;
    color: #ffffff;
}}

/* Group Boxes & Cards */
QGroupBox {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    font-weight: bold;
    color: #0284c7;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
}}

QCheckBox {{
    spacing: 8px;
    color: #1e293b;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
}}
QCheckBox::indicator:checked {{
    background-color: #2563eb;
    border-color: #1d4ed8;
}}
"""
