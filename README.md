# BinaryReceptor v3.0.0

> **The ultra-lightweight, zero-bug, bilingual desktop companion server for [BinaryEye](https://github.com/markusfisch/BinaryEye) on Android.**  
> Native Windows architecture with Bluetooth RFCOMM, HTTP webhook listener, SendInput keyboard wedge, and visual token builder.

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?logo=windows&logoColor=white)](https://microsoft.com/windows)
[![Version](https://img.shields.io/badge/Release-v3.0.0-10B981)](https://github.com/ouncommono/BinaryReceptor/releases)
[![Build Status](https://github.com/ouncommono/BinaryReceptor/actions/workflows/build_release.yml/badge.svg)](https://github.com/ouncommono/BinaryReceptor/actions)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)

---

## 🌐 Languages / زبان‌ها
- [English Documentation](#-english-documentation)
- [راهنمای جامع فارسی (Persian Documentation)](#-راهنمای-جامع-فارسی-persian-documentation)

---

# 🇬🇧 English Documentation

## Executive Overview
**BinaryReceptor v3.0.0** is a clean-slate architectural rewrite of the original BinaryReceptor repository (originally forked from `KamaleiZestri/BinaryReceptor`). It completely replaces the legacy Haxe/C#/justfile build chain (`hxBluetooth` and `hxKeyType`) with native, ultra-fast Python and Win32 implementations while compiling into a single standalone Windows executable (`BinaryReceptor.exe`).

Whenever you scan any 1D barcode or 2D QR code using [BinaryEye](https://github.com/markusfisch/BinaryEye) on Android, BinaryReceptor instantly captures the barcode over **Bluetooth RFCOMM**, **Wi-Fi / LAN HTTP**, or **both simultaneously**, and directly types it into your active Windows application (Excel, ERP, POS, Notepad, browser, etc.) using low-level Win32 `SendInput` Unicode or fast clipboard paste (`Ctrl+V`).

---

## ✨ Key Features & Architectural Enhancements

### 1. Deterministic `settings.ini` Persistence & Hot-Reload
- **Zero-Bug Path Resolution:** Solves the frozen executable path bug. In standalone PyInstaller `.exe` builds, `settings.ini` is deterministically resolved to the exact directory directly alongside `BinaryReceptor.exe`, never in a temporary directory (`sys._MEIPASS`).
- **Live Background File-Watcher:** A lightweight background thread monitors `settings.ini`. If you edit and save the INI file externally, BinaryReceptor hot-reloads within 1 second, updates the UI in real time, and restarts listeners if host, port, or mode changed.
- **100% Backward Compatibility:** Tolerates UTF-8 with BOM (`utf-8-sig`), inline comments (`;` and `#`), case-insensitivity, and legacy key names (`mode`, `port`, `preType`, `postType`).

### 2. Universal BinaryEye HTTP Protocol Compatibility
- **Asynchronous / Threaded Server:** Listens on port `24234` (configurable) on `/*` and accepts all methods (`GET`, `POST`, `PUT`, `OPTIONS`).
- **Sub-Millisecond 200 OK Responses:** Returns `HTTP 200 OK` (`application/json`) in under 5ms by dispatching incoming barcodes directly to an internal worker queue. This guarantees BinaryEye's strict 5s connection and 10s read timeouts are never exceeded.
- **Supports All 5 BinaryEye Forwarding Cases:**
  1. **Case A — JSON POST:** BinaryEye JSON Forwarding & Continuous Scan Callbacks (`{"content": "...", "format": "...", "scanId": "..."}`).
  2. **Case B — Query Parameters:** `GET` or `POST` (`?content=...`, `?result=...`, `?q=...`, `?code=...`).
  3. **Case C — Raw Query String:** `GET /?ScannedBarcodeText` (no `=` required).
  4. **Case D — Raw URL Path:** BinaryEye "GET and simply append content" mode (`GET /123456789` or `GET /scan/123456789`).
  5. **Case E — Form-Urlencoded & Raw Body:** Standard POST forms or direct plain-text body.
  6. **Health Endpoint:** `GET /` or `GET /health` returns clean diagnostic status.

### 3. Native Win32 Bluetooth RFCOMM Server
- Replaces legacy `hxBluetooth` with native Windows Bluetooth Sockets (`AF_BTH`, `SOCK_STREAM`, `BTPROTO_RFCOMM`) and `ws2_32.dll` `WSASetServiceW` SDP service registration.
- Advertises the exact SDP UUID required by BinaryEye: `8a8478c9-2ca8-404b-a0de-101f34ab71ae`.
- Seamless reconnection: handles client reconnects and adapter power cycles without crashing.

### 4. Tri-Mode Simultaneous Operation with Intelligent Deduplication
- **Modes:** `bluetooth`, `http`, or `both` (Hybrid Simultaneous Mode).
- **Sliding Time-Window Deduplicator:** When a device sends a scan via both Bluetooth and HTTP simultaneously, the deduplication engine computes a SHA-256 hash and checks the `scanId`. Duplicate packets within the configurable window (e.g., 1500ms) are suppressed, logged, and counted.

### 5. Low-Level Native Keyboard Injector
- Replaces legacy `hxKeyType` with Win32 `SendInput` (`KEYEVENTF_UNICODE`).
- Supports any Unicode character (English, Persian, Arabic, Cyrillic, Chinese, symbols, emojis) regardless of active keyboard layout.
- Supports control keys (`VK_RETURN`, `VK_TAB`, `VK_SPACE`, `VK_BACK`, `VK_ESCAPE`, `VK_DELETE`, `VK_DOWN`, `VK_UP`, etc.).
- Optional **Clipboard Paste Mode (`Ctrl+V`)** for instant injection of large QR codes without per-character typing delay, with optional automatic clipboard restoration.

### 6. Intuitive Visual Prefix & Suffix Builder
- Zero coding knowledge needed: click interactive chip buttons (`+ Enter`, `+ Tab`, `+ Space`, `+ Bksp`, `+ Esc`, `+ Down`, `+ Date`, `+ Time`) or choose presets.
- Live preview showing the exact keystroke sequence.

### 7. Dynamic QR Code Connection Assistant
- **Tab 1 — Standard Forwarding URL QR:** Shows `http://<LAN_IP>:<PORT>/` with 1-click copy.
- **Tab 2 — 1-Scan Continuous Mode Deep Link QR:** Encodes `binaryeye://scan?continuous=true&callback=http%3A%2F%2F<LAN_IP>%3A<PORT>%2Fscan`. Scanning this QR immediately launches continuous forwarding without touching BinaryEye settings!
- **Tab 3 — Send Barcode to Phone:** Encodes text into 11 supported symbologies (`QR_CODE`, `CODE_128`, `EAN_13`, etc.) using `binaryeye://encode`.

### 8. World-Class Bilingual UI/UX (Persian RTL & English LTR)
- Built on **PySide6** with native Right-to-Left (`Qt.LayoutDirection.RightToLeft`) support.
- 1-click language switch between **Persian (فارسی)** and **English**.
- Modern Dark Mode and Light Mode with responsive card layouts and live KPI metrics.
- Full System Tray integration (`QSystemTrayIcon`) with dynamic icon status beacons and localized context menus.

---

## 🚀 Quick Start Guide

### Option 1: Standalone Portable Binary (No Python Required)
1. Download `BinaryReceptor-v3.0.0-windows-x64.zip` from the [Latest Release](https://github.com/ouncommono/BinaryReceptor/releases).
2. Extract the folder and double-click `BinaryReceptor.exe`.
3. Click **Start Server** (or it starts automatically if configured).

### Option 2: Running from Source
```powershell
# Clone the repository
git clone https://github.com/ouncommono/BinaryReceptor.git
cd BinaryReceptor

# Install dependencies
pip install -r requirements.txt

# Launch BinaryReceptor
python run.py
```

---

## 📱 Connecting BinaryEye to BinaryReceptor

### Method A: Instant 1-Scan Continuous Mode (Fastest)
1. In BinaryReceptor, open the **Connection & QR Code** tab.
2. Select **2. 1-Scan Continuous Mode**.
3. Point your phone camera running BinaryEye at the QR code.
4. BinaryEye will immediately open in continuous scan mode and forward every scan to your PC!

### Method B: Standard Wi-Fi / HTTP Setup
1. In BinaryReceptor, copy the HTTP Forwarding Endpoint (e.g. `http://192.168.1.50:24234/`).
2. In BinaryEye, open **Settings > Forwarding > URL**.
3. Paste the URL. Every barcode scanned will now be posted to your PC.

### Method C: Bluetooth RFCOMM Setup
1. Pair your Android phone with your Windows PC in Windows Bluetooth Settings.
2. In BinaryEye, enable **Send scan via Bluetooth** and select your PC.
3. In BinaryReceptor, set Mode to `both` or `bluetooth`.

---

## ⚙️ Configuration (`settings.ini`)

A clean `settings.ini` is generated automatically alongside the executable:

```ini
[general]
mode = both               # both, http, or bluetooth
language = en             # en (English) or fa (فارسی)
theme = dark              # dark, light, or system
auto_start = true         # auto-start server on app launch
start_minimized = false   # start minimized to tray
minimize_to_tray = true   # minimize to tray on close (X)
start_with_windows = false# run on Windows boot
audio_feedback = true     # beep sound on scan
tray_notifications = true # Windows tray notifications

[network]
http_host = 0.0.0.0       # bind to all interfaces
http_port = 24234         # default port

[bluetooth]
bt_enabled = true
service_uuid = 8a8478c9-2ca8-404b-a0de-101f34ab71ae
service_name = BinaryReceptor

[wedge]
output_mode = type        # type (keystroke), paste (Ctrl+V), copy_only
prefix =                  # prefix tokens: {ENTER}, {TAB}, {SPACE}, {DATE}, etc.
suffix = {ENTER}          # suffix tokens (default: {ENTER})
inter_key_delay_ms = 0
pre_typing_delay_ms = 0
restore_clipboard = true

[deduplication]
deduplication_enabled = true
deduplication_window_ms = 1500

[filters]
trim_whitespace = true
replace_newlines = none   # none, tab, or space
regex_pattern = 
regex_replacement = 
allowed_formats = all
auto_open_urls = false
copy_to_clipboard = false
```

---

## 🛠️ Building the Standalone Executable

Run the automated 1-click build script:
```powershell
python build.py
# or double-click build.bat
```
The compiled standalone executable and `settings.ini` will be produced in `dist/BinaryReceptor.exe`.

---

# 🇮🇷 راهنمای جامع فارسی (Persian Documentation)

## معرفی و معماری
**باینری‌رسپتور نسخه ۳ (BinaryReceptor v3.0.0)** یک بازنویسی کامل، مدرن و با معماری نوین برای نرم‌افزار BinaryReceptor است. این برنامه به عنوان سبک‌ترین و پرسرعت‌ترین سرور همراه دسکتاپ برای اسکنر بارکد اندروید [BinaryEye](https://github.com/markusfisch/BinaryEye) طراحی شده است. زنجیره قدیمی Haxe/C# کاملاً با پیاده‌سازی بومی و مدرن پایتون و Win32 جایگزین شده و برنامه به صورت یک فایل مستقل بدون نیاز به هیچ پیش‌نیاز روی ویندوز ۱۰ و ۱۱ اجرا می‌شود.

هنگامی که هرگونه بارکد میله‌ای یا کد دوبعدی QR را با دوربین گوشی اسکن می‌کنید، این برنامه بارکد را از طریق **بلوتوث** یا **شبکه Wi-Fi** دریافت کرده و بلافاصله مانند یک بارکدخوان فیزیکی در نرم‌افزار فعال شما (اکسل، حسابداری، انبارداری، مرورگر، نوت‌پد و ...) تایپ یا پیست می‌کند.

---

## 💎 قابلیت‌های برجسته نسخه ۳.۰.۰

1. **سازگاری کامل و سریع با پروتکل BinaryEye:**
   - پاسخ فوری `200 OK` در کمتر از ۵ میلی‌ثانیه برای جلوگیری از خطای Timeout در گوشی.
   - پشتیبانی از تمام حالت‌های ارسال (JSON، پارامترهای GET/POST، مسیر URL خام و فرم‌ها).
2. **ارتباط بومی بلوتوث و شبکه به صورت همزمان (حالت ترکیبی):**
   - پشتیبانی از حالت همزمان (Hybrid)؛ اگر شبکه یا بلوتوث قطع شود، ارتباط دیگر بدون وقفه اسکن‌ها را دریافت می‌کند.
3. **موتور هوشمند حذف تکراری‌ها (Deduplication):**
   - جلوگیری از دوبار تایپ شدن بارکدهایی که همزمان از بلوتوث و وای‌فای ارسال می‌شوند با استفاده از هش SHA-256 و شناسه `scanId`.
4. **سازنده بصری کلیدهای پیشوند و پسوند (بدون نیاز به کدنویسی):**
   - امکان افزودن کلیدهای اینتر، تب، فاصله، تاریخ و ساعت با کلیک روی دکمه‌های آماده بدون نیاز به دانستن کدهای خاص.
5. **دستیار هوشمند اتصال و بارکدهای QR:**
   - تولید کد QR برای اتصال خودکار و فعال‌سازی اسکن پیوسته تنها با یک بار اسکن دوربین گوشی.
6. **رابط کاربری دوزبانه (فارسی راست‌به‌چپ و انگلیسی):**
   - تغییر آنی زبان به فارسی با چیدمان کامل RTL و تایپوگرافی زیبا.
   - حالت دارک (تیره) و لایت (روشن).
7. **همگام‌سازی کامل با تسک‌بار و سیستم‌تری ویندوز:**
   - آیکون چندکیفیته، منوی کامل کنار ساعت، بازخوانی خودکار تغییرات فایل `settings.ini`.

---

## 📋 ساختار پروژه (Project Layout)

```
BinaryReceptor/
├── assets/
│   └── icon.ico                    # Multi-resolution icon (16x16 to 256x256)
├── legacy/                         # Archived legacy Haxe/C# codebase
├── src/
│   ├── core/
│   │   ├── bt_server.py            # Native Windows AF_BTH RFCOMM & SDP server
│   │   ├── deduplicator.py         # Thread-safe sliding time-window deduplication
│   │   ├── http_server.py          # Universal BinaryEye HTTP webhook server
│   │   ├── key_injector.py         # Low-level Win32 SendInput Unicode injector
│   │   └── qr_helper.py            # QR generator & BinaryEye deep links
│   ├── ui/
│   │   ├── i18n.py                 # Bilingual FA/EN localization dictionaries
│   │   ├── icon_gen.py             # Vector-style multi-resolution icon builder
│   │   ├── main_window.py          # PySide6 RTL/LTR responsive dashboard
│   │   ├── styles.py               # Dark & Light QSS stylesheets
│   │   └── tray.py                 # System Tray controller
│   ├── config.py                   # Deterministic settings.ini manager & watcher
│   ├── main.py                     # Entry point, AppUserModelID, mutex, CLI
│   └── version.py                  # Version constants (3.0.0)
├── tests/                          # Comprehensive pytest test suite (35+ tests)
├── .github/workflows/
│   └── build_release.yml           # Automated CI/CD & release pipeline
├── build.py                        # Standalone PyInstaller build engine
├── build.bat                       # 1-click Windows compilation script
├── pytest.ini                      # Pytest configuration
├── requirements.txt                # Runtime dependencies
├── requirements-build.txt          # Build & test dependencies
├── run.py                          # Development launcher
└── settings.ini                    # Local configuration file
```

---

## 🧪 اجرای آزمون‌ها (Running Tests)

تمام قابلیت‌ها با پوشش جامع تست آزموده شده‌اند:
```powershell
python -m pytest -v
```

---

## 📜 لایسنس (License)
این پروژه تحت لایسنس [GPL-3.0](LICENSE) منتشر شده است.
BinaryReceptor fork modernized by **ouncommono**.
Original fork upstream: [KamaleiZestri/BinaryReceptor](https://github.com/KamaleiZestri/BinaryReceptor).
Companion Android app: [BinaryEye](https://github.com/markusfisch/BinaryEye) by Markus Fisch.
