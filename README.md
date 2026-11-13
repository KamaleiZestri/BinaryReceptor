# BinaryReceptor v3.1.0

> **The ultra-lightweight, zero-bug, bilingual desktop companion server for [BinaryEye](https://github.com/markusfisch/BinaryEye) on Android.**  
> Native Windows architecture with Bluetooth RFCOMM, HTTP webhook listener, SendInput keyboard wedge, and visual token builder.

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?logo=windows&logoColor=white)](https://microsoft.com/windows)
[![Version](https://img.shields.io/badge/Release-v3.1.0-10B981)](https://github.com/ouncommono/BinaryReceptor/releases)
[![Build Status](https://github.com/ouncommono/BinaryReceptor/actions/workflows/build_release.yml/badge.svg)](https://github.com/ouncommono/BinaryReceptor/actions)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)

---

## 🌐 Languages / زبان‌ها
- [English Documentation](#-english-documentation)
- [راهنمای جامع فارسی (Persian Documentation)](#-راهنمای-جامع-فارسی-persian-documentation)

---

# 🇬🇧 English Documentation

## Executive Overview
**BinaryReceptor v3.1.0** is the ultimate desktop companion server for the Android barcode scanner [BinaryEye](https://github.com/markusfisch/BinaryEye). It delivers a clean-slate architectural rewrite of the legacy Haxe/C#/justfile codebase (`hxBluetooth` and `hxKeyType`) into native, high-performance Python and Win32 APIs, compiling into a standalone, portable Windows executable (`BinaryReceptor.exe`).

Whenever you scan any 1D barcode or 2D QR code with BinaryEye on your mobile device, BinaryReceptor captures the scan instantly over **Bluetooth RFCOMM**, **Wi-Fi / LAN HTTP**, or **both simultaneously in Hybrid mode**, and wedges it into your active Windows application (Excel, ERP, POS, Notepad, browser, inventory system) using low-level Win32 `SendInput` Unicode or instant clipboard paste (`Ctrl+V`).

---

## 🚀 Key Improvements in Version 3.1.0

Version 3.1.0 incorporates 15 targeted architectural fixes and UX refinements:

1. **Strict Operation Mode Isolation:** Switching to *HTTP Server Only* actively unregisters the SDP service (`RNRSERVICE_DELETE`) and closes Bluetooth RFCOMM sockets. Switching to *Bluetooth Only* terminates HTTP listeners. A second-layer guard immediately drops cross-transport packets.
2. **Working Synthesized Scanner Beep:** Generates an in-memory 16-bit PCM WAV dual-tone chime (1800Hz -> 2400Hz, 90ms) played non-blocking in a daemon thread, with a "Test Sound" button in Settings.
3. **Canonical Deduplication Normalization:** Shared thread-safe `ScanDeduplicator` normalizes CRLF variations (`\r\n`, `\n`) and URL encoding (`%20`), preventing double typing when connected via both Bluetooth and HTTP simultaneously.
4. **Unified Output Pipeline:** All transports route strictly through the central pipeline. Output modes (`copy_only`, `clipboard_paste`, `type`, `log_only`) are uniformly respected regardless of whether the scan came from Bluetooth or HTTP.
5. **Elimination of BinaryEye HTTP Client Error Beeps:** Fully consumes incoming POST request bodies before writing response headers, strictly returns exact `Content-Length`, `Connection: close`, and immediate `<50ms` `application/json` `200 OK` responses.
6. **Continuous Mode Deep Link Landing Page:** Web landing page at `/start` enables 1-tap continuous scan launching from mobile browsers, with self-link interception to prevent configuration URLs from being typed into Windows.
7. **Raw Barcode Generator:** The Barcode Generator section produces 100% raw text verbatim without forced `binaryeye://encode` wrappers, while preserving deep link options.
8. **Settings Tab Sticky Footer:** Settings form features a persistent footer bar with deferred "Save Settings", "Reset to Defaults" with confirmation, and live "Unsaved changes" indicator.
9. **Dynamic Top Status KPI Cards:** Master Server, Bluetooth, HTTP, and Mode cards feature immediate border and background color state transitions via Qt style unpolish/polish.
10. **Two-Way System Tray Synchronization:** Tray menu reflects current server states, mode checkmarks, and language selection in real time.
11. **Whitespace Keystroke Preview:** The live keystroke preview renders true whitespace (`\n`, `\t`, spaces) and character deletions instead of raw `{ENTER}` / `{TAB}` token syntax.
12. **100% Localization Parity:** Complete English (LTR) and Persian (RTL) dictionary parity across 145+ translation keys.
13. **Clean Application ID:** Windows Application User Model ID set to `BinaryReceptor.3.1.0`.
14. **Deterministic `settings.ini` Persistence & Hot-Reload:** Reads and writes `settings.ini` directly alongside `BinaryReceptor.exe` with a 1-second background file-watcher.
15. **Standalone CI/CD Pipeline:** Automated GitHub Actions build producing `BinaryReceptor-v3.1.0-win64.zip` and verified GPL-3.0 License.

---

## 💻 Quick Start Guide

### Option 1: Standalone Portable Binary (No Python Required)
1. Download `BinaryReceptor-v3.1.0-win64.zip` from [GitHub Releases](https://github.com/ouncommono/BinaryReceptor/releases).
2. Extract the archive and run `BinaryReceptor.exe`.
3. The server starts automatically and generates `settings.ini` alongside the executable.

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

### Method A: Instant 1-Scan Continuous Mode (Recommended)
1. Open BinaryReceptor and switch to the **Connection & QR Code** tab.
2. Select **2. 1-Scan Continuous Mode QR**.
3. Point BinaryEye at the QR code on your monitor. BinaryEye will automatically launch in continuous scan mode and stream all barcodes to your PC!

### Method B: Mobile Web Browser One-Click Launch
1. On your phone's browser, open: `http://<YOUR_PC_IP>:24234/start`
2. Tap **🚀 Start Continuous Scan**.

### Method C: Standard HTTP Webhook Setup
1. In BinaryEye, navigate to **Settings > Forwarding > URL**.
2. Enter: `http://<YOUR_PC_IP>:24234/` (or `http://<YOUR_PC_IP>:24234/scan`).

### Method D: Bluetooth RFCOMM Setup
1. Pair your Android phone with Windows in **Windows Bluetooth Settings**.
2. In BinaryEye, enable **Send scan via Bluetooth** and pick your PC.
3. In BinaryReceptor, set Mode to `both` or `bluetooth`.

---

## ⚙️ Configuration (`settings.ini`)

`settings.ini` resides alongside `BinaryReceptor.exe` and hot-reloads automatically upon external modification:

```ini
[general]
mode = both               # both (Hybrid), http, or bluetooth
language = en             # en (English) or fa (فارسی)
theme = dark              # dark, light, or system
auto_start = true         # auto-start server on app launch
start_minimized = false   # start minimized to tray
minimize_to_tray = true   # minimize to tray on close (X)
start_with_windows = false# run on Windows login
audio_feedback = true     # pleasant 16-bit PCM scanner chime
tray_notifications = true # Windows tray notifications

[network]
http_host = 0.0.0.0       # bind to all network interfaces
http_port = 24234         # HTTP server port

[bluetooth]
bt_enabled = true
service_uuid = 8a8478c9-2ca8-404b-a0de-101f34ab71ae
service_name = BinaryReceptor

[wedge]
output_mode = type        # type (keystroke), paste (Ctrl+V), copy_only, log_only
prefix =                  # tokens: {ENTER}, {TAB}, {SPACE}, {DATE}, {TIME}, etc.
suffix = {ENTER}          # tokens typed after barcode
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

Run the automated build script:
```powershell
python build.py
# or double-click build.bat
```
The compiled standalone binary and configuration file will be placed in `dist/BinaryReceptor.exe` and `dist/settings.ini`.

---

# 🇮🇷 راهنمای جامع فارسی (Persian Documentation)

## معرفی و معماری نرم‌افزار
**باینری‌رسپتور نسخه ۳.۱.۰ (BinaryReceptor v3.1.0)** کامل‌ترین، سبک‌ترین و پیشرفته‌ترین سرور همراه دسکتاپ برای اسکنر بارکد اندروید [BinaryEye](https://github.com/markusfisch/BinaryEye) است. این نرم‌افزار حاصل بازنویسی بنیادی و مدرن با پایتون ۳.۱۱+ و توابع سطح پایین Win32 بوده و بدون نیاز به نصب پایتون به صورت یک فایل اجرایی پرتابل (`BinaryReceptor.exe`) روی ویندوز ۱۰ و ۱۱ کار می‌کند.

با اسکن هرگونه بارکد میله‌ای، کدهای دوبعدی QR، DataMatrix و ... در گوشی، اطلاعات به صورت بلادرنگ از طریق **بلوتوث (Bluetooth RFCOMM)** یا **شبکه محلی / وای‌فای (HTTP Webhook)** یا **هر دو به صورت همزمان (حالت هیبریدی)** دریافت شده و مستقیماً مانند یک بارکدخوان فیزیکی حرفه‌ای در نرم‌افزار فعال سیستم (اکسل، نرم‌افزارهای حسابداری و انبارداری، فرم‌های وب، اتوماسیون اداری و ...) تایپ یا پیست می‌شود.

---

## 🌟 بهبودها و نوآوری‌های نسخه ۳.۱.۰

1. **تفکیک کامل و ایزولاسیون حالت‌های کاری (Mode Isolation):** در حالت «فقط سرور HTTP»، پورت‌ها و سوکت‌های بلوتوث بسته شده و سرویس SDP از رجیستری ویندوز حذف می‌شود. همچنین گارد دولایه مانع از ورود پکت‌های تداخل‌کننده می‌شود.
2. **صدای اسکنر شفاف و واقعی (Scanner Audio Chime):** تولید درون‌حافظه‌ای صدای دوتنه اسکنر (۱۸۰۰Hz تا ۲۴۰۰Hz) با فرمت ۱۶-بیت PCM به همراه دکمه پیش‌نمایش تست صدا در تنظیمات.
3. **حذف هوشمند تکراری‌ها با نرمال‌سازی کدهای دریافتی:** رفع مشکل تایپ دوباره بارکدها در حالت هیبریدی با یکپارچه‌سازی فضای حافظه و حذف کاراکترهای خط جدید (`\r\n`).
4. **خط لوله خروجی یکپارچه:** رعایت دقیق حالت خروجی (فقط کپی در کلیپ‌بورد، پیست سریع یا تایپ) برای هر دو روش دریافت بلوتوث و شبکه.
5. **حذف صدای خطای گوشی در ارسال HTTP:** ارسال فوری پاسخ `200 OK` با هدرهای استاندارد `Content-Length` و `Connection: close` در کمتر از ۵۰ میلی‌ثانیه.
6. **صفحه فرود تحت وب `/start` و مسدودسازی اسکن لینک‌های تنظیمی:** راه‌اندازی حالت اسکن پیوسته تنها با لمس یک دکمه در مرورگر گوشی و جلوگیری از تایپ شدن لینک‌های کانفیگ در ویندوز.
7. **تولیدکننده بارکد مستقیم (Raw Text):** تولید بارکد بدون پیشوندهای اضافی برای انواع استفاده‌های صنعتی و اداری.
8. **نوار ذخیره ثابت در تب تنظیمات:** نوار دکمه‌های شناور ذخیره با اعلام وضعیت تغییرات ذخیره‌نشده و امکان بازگردانی به تنظیمات پیش‌فرض کارخانه با تأییدیه کاربر.
9. **کارت‌های وضعیت پویا با رنگ‌بندی زنده:** کارت‌های سرور اصلی، بلوتوث، شبکه و حالت کاری با تغییر آنی رنگ کادر و پس‌زمینه (سبز فعال، خاکستری آماده‌باش، قرمز خطا).
10. **همگام‌سازی دوطرفه با منوی کنار ساعت (System Tray):** نمایش وضعیت و امکان تغییر حالت و زبان مستقیماً از آیکون کنار ساعت ویندوز.
11. **پیش‌نمایش زنده کلیدها با اعمال فاصله و اینتر واقعی:** نمایش خروجی دقیق شبیه‌سازی‌شده به جای کدهای متنی خام `{ENTER}` یا `{TAB}`.
12. **بومی‌سازی ۱۰۰٪ کامل فارسی و انگلیسی:** تطابق کامل ۱۴۵ کلید ترجمه بین زبان‌های فارسی (راست‌به‌چپ) و انگلیسی.
13. **شناسه استاندارد برنامه:** ثبت شناسه یکتای `BinaryReceptor.3.1.0` برای هماهنگی کامل تسک‌بار ویندوز.
14. **ذخیره‌سازی مطمئن `settings.ini` در کنار فایل اجرایی:** بازخوانی بلادرنگ تغییرات فایل تنظیمات در کمتر از ۱ ثانیه.
15. **خط لوله انتشار خودکار گیت‌هاب:** ساخت بسته فشرده `BinaryReceptor-v3.1.0-win64.zip` و اعتبارسنجی لایسنس رسمی GPL-3.0.

---

## 🧪 اجرای آزمون‌ها (Testing)

تمام ویژگی‌ها با ۴۴ تست جامع سنجیده شده و با موفقیت پاس می‌شوند:
```powershell
python -m pytest -v
```

---

## 📜 لایسنس و حقوق نشر (License)

این نرم‌افزار تحت پروانه عمومی همگانی گنو [GPL-3.0](LICENSE) منتشر شده است.  
توسعه و بازنویسی نسخه ۳ توسط **ouncommono**.  
مبتنی بر پروژه اصلی: [KamaleiZestri/BinaryReceptor](https://github.com/KamaleiZestri/BinaryReceptor).  
کلاینت همراه اندروید: [BinaryEye](https://github.com/markusfisch/BinaryEye) توسط Markus Fisch.
