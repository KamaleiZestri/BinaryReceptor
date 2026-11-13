"""Comprehensive bilingual localization dictionaries (English & Persian / فارسی) for BinaryReceptor v3.0.0."""
from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # App & Header
        "app_title": "BinaryReceptor v3.0.0",
        "app_subtitle": "Desktop Companion Server for BinaryEye Android Barcode Scanner",
        "status_running": "SERVER ACTIVE",
        "status_stopped": "SERVER STOPPED",
        "status_listening": "Listening",
        "status_connected": "Connected",
        "status_standby": "Standby",
        "status_adapter_off": "Adapter Off",
        "status_error": "Port Error",
        "btn_start": "Start Server",
        "btn_stop": "Stop Server",
        "theme_dark": "Dark Theme",
        "theme_light": "Light Theme",
        "lang_switch": "فارسی",

        # KPI Metrics Cards
        "kpi_total_scans": "Total Scans",
        "kpi_bt_scans": "Bluetooth Scans",
        "kpi_http_scans": "HTTP Scans",
        "kpi_dedup_blocked": "Duplicates Blocked",

        # Channel Status Badges
        "badge_bt": "Bluetooth RFCOMM",
        "badge_http": "HTTP Server",

        # Tab Titles
        "tab_dashboard": "Live Scan Activity",
        "tab_wedge": "Prefix / Suffix Builder",
        "tab_connection": "Connection & QR Code",
        "tab_settings": "Settings & Hardware",

        # Dashboard / Activity Log
        "col_time": "Timestamp",
        "col_channel": "Channel",
        "col_format": "Format",
        "col_content": "Barcode Content",
        "col_status": "Status",
        "btn_retype": "Re-type Selected",
        "btn_copy": "Copy Content",
        "btn_clear_log": "Clear Activity Log",
        "btn_export_csv": "Export to CSV",
        "status_typed": "Typed (SendInput)",
        "status_pasted": "Pasted (Ctrl+V)",
        "status_copied": "Copied to Clipboard",
        "status_dedup": "Duplicate Suppressed",
        "status_filtered": "Filtered",
        "confirm_clear_log": "Are you sure you want to clear the entire activity log?",
        "export_success": "Successfully exported {count} scans to {path}",

        # Prefix & Suffix Builder
        "wedge_title": "Visual Keystroke & Token Builder",
        "wedge_desc": "Configure keys or text typed before (Prefix) and after (Suffix) each scanned barcode. Click tokens to append them instantly without typing escape sequences.",
        "lbl_prefix": "Prefix (Typed Before Barcode):",
        "lbl_suffix": "Suffix (Typed After Barcode):",
        "lbl_preview": "Live Keystroke Output Preview:",
        "preset_none": "None (Empty)",
        "preset_enter": "Enter (Next Line)",
        "preset_tab": "Tab (Next Field)",
        "preset_space": "Space",
        "preset_double_enter": "Double Enter",
        "preset_tab_enter": "Tab + Enter",
        "preset_backspace": "Backspace",
        "preset_esc": "Escape",
        "preset_down": "Down Arrow",
        "btn_add_enter": "+ Enter",
        "btn_add_tab": "+ Tab",
        "btn_add_space": "+ Space",
        "btn_add_backspace": "+ Backspace",
        "btn_add_esc": "+ Esc",
        "btn_add_down": "+ Down",
        "btn_add_date": "+ Date",
        "btn_add_time": "+ Time",
        "btn_clear_field": "Clear",

        # Connection Assistant & QR Generator
        "conn_title": "BinaryEye Connection Assistant & QR Generator",
        "conn_desc": "Scan one of the QR codes below using the BinaryEye Android camera to connect instantly.",
        "subtab_qr_url": "1. Standard Forwarding URL",
        "subtab_qr_direct": "2. 1-Scan Continuous Mode",
        "subtab_qr_encode": "3. Send Barcode to Phone",
        "lbl_lan_ip": "Active PC Network Address:",
        "lbl_http_url": "HTTP Forwarding Endpoint:",
        "btn_copy_url": "Copy URL",
        "url_copied": "URL copied to clipboard!",
        "desc_qr_url": "1. Open BinaryEye on Android\n2. Go to Settings > Forwarding > URL\n3. Paste this URL or scan this QR to copy the link.",
        "desc_qr_direct": "Scan this QR code with BinaryEye to IMMEDIATELY launch continuous barcode forwarding without configuring any settings in the app!",
        "lbl_encode_text": "Text to Encode on Phone:",
        "lbl_encode_format": "Target Barcode Symbology:",
        "btn_generate_encode_qr": "Update Encode QR",
        "desc_qr_encode": "Encodes your text into a barcode directly on your phone's screen using BinaryEye.",

        # Settings
        "sec_general": "General Configuration",
        "sec_network": "Network & HTTP Server",
        "sec_bluetooth": "Bluetooth RFCOMM",
        "sec_wedge": "Keystroke & Output Options",
        "sec_dedup": "Sliding Window Deduplication",
        "sec_filters": "Content Filters & Transformations",

        "lbl_mode": "Operating Mode:",
        "opt_mode_both": "Hybrid Simultaneous (Bluetooth + HTTP)",
        "opt_mode_http": "HTTP Server Only (Wi-Fi / LAN)",
        "opt_mode_bt": "Bluetooth RFCOMM Only",

        "lbl_port": "HTTP Port:",
        "lbl_host": "HTTP Bind Address:",
        "lbl_bt_uuid": "SDP Service UUID:",
        "lbl_out_mode": "Typing Injection Mode:",
        "opt_out_type": "Keystroke Simulation (SendInput Unicode)",
        "opt_out_paste": "Fast Clipboard Paste (Ctrl+V)",
        "opt_out_copy": "Copy to Clipboard Only (No Typing)",

        "lbl_inter_key": "Inter-Key Delay (ms):",
        "lbl_pre_delay": "Pre-Typing Delay (ms):",
        "chk_restore_clip": "Restore previous clipboard content after Ctrl+V paste",

        "chk_dedup_enabled": "Enable duplicate scan suppression",
        "lbl_dedup_window": "Deduplication Window (ms):",

        "chk_trim_space": "Strip leading and trailing whitespace",
        "lbl_replace_newlines": "Replace internal newlines with:",
        "opt_nl_none": "Keep Newlines",
        "opt_nl_tab": "Replace with Tab",
        "opt_nl_space": "Replace with Space",

        "lbl_regex_pat": "Regex Pattern to Search:",
        "lbl_regex_rep": "Regex Replacement Text:",
        "lbl_allowed_fmt": "Allowed Barcode Formats (comma separated or 'all'):",
        "chk_auto_url": "Automatically open in web browser if content is a valid URL",
        "chk_copy_always": "Always copy scanned barcode to clipboard",

        "chk_beep": "Play audio beep sound effect on successful scan",
        "chk_tray_notify": "Show Windows tray notifications for scans",
        "chk_start_windows": "Start BinaryReceptor automatically with Windows",
        "chk_auto_start": "Automatically start server on application launch",
        "chk_start_min": "Start minimized to system tray",
        "chk_min_tray": "Minimize to system tray on window close (X)",

        "btn_save_settings": "Save Settings to settings.ini",
        "settings_saved": "Settings successfully saved and applied!",

        # System Tray Menu
        "tray_title": "BinaryReceptor v3.0.0",
        "tray_status_header": "Status: {status}",
        "tray_start": "Start Server",
        "tray_stop": "Stop Server",
        "tray_mode_both": "Mode: Hybrid (Both)",
        "tray_mode_http": "Mode: HTTP Only",
        "tray_mode_bt": "Mode: Bluetooth Only",
        "tray_show_qr": "Show QR Codes & Connection...",
        "tray_show_window": "Open BinaryReceptor",
        "tray_exit": "Exit Completely",
        "toast_scan_title": "Barcode Scanned ({source})",
    },

    "fa": {
        # App & Header
        "app_title": "باینری‌رسپتور v3.0.0 (BinaryReceptor)",
        "app_subtitle": "سرور همراه دسکتاپ برای اسکنر بارکد اندروید BinaryEye",
        "status_running": "سرور فعال است",
        "status_stopped": "سرور متوقف است",
        "status_listening": "در حال گوش دادن",
        "status_connected": "دستگاه متصل شد",
        "status_standby": "آماده به کار",
        "status_adapter_off": "بلوتوث خاموش است",
        "status_error": "خطای پورت شبکه",
        "btn_start": "شروع به کار سرور",
        "btn_stop": "متوقف کردن سرور",
        "theme_dark": "پوسته تیره (دارک)",
        "theme_light": "پوسته روشن (لایت)",
        "lang_switch": "English",

        # KPI Metrics Cards
        "kpi_total_scans": "مجموع اسکن‌ها",
        "kpi_bt_scans": "اسکن از بلوتوث",
        "kpi_http_scans": "اسکن از شبکه (HTTP)",
        "kpi_dedup_blocked": "تکراری‌های مسدود شده",

        # Channel Status Badges
        "badge_bt": "بلوتوث RFCOMM",
        "badge_http": "سرور شبکه HTTP",

        # Tab Titles
        "tab_dashboard": "فعالیت و تاریخچه اسکن‌ها",
        "tab_wedge": "سازنده پیشوند و پسوند کلیدها",
        "tab_connection": "دستیار اتصال و کد QR",
        "tab_settings": "تنظیمات و سخت‌افزار",

        # Dashboard / Activity Log
        "col_time": "زمان دریافت",
        "col_channel": "کانال ارتباطی",
        "col_format": "نوع بارکد",
        "col_content": "محتوای بارکد اسکن شده",
        "col_status": "وضعیت پردازش",
        "btn_retype": "تایپ مجدد مورد انتخابی",
        "btn_copy": "کپی محتوا در کلیپ‌بورد",
        "btn_clear_log": "پاکسازی تاریخچه وقایع",
        "btn_export_csv": "خروجی فایل اکسل (CSV)",
        "status_typed": "تایپ شد (SendInput)",
        "status_pasted": "پیست شد (Ctrl+V)",
        "status_copied": "در کلیپ‌بورد کپی شد",
        "status_dedup": "تکراری - مسدود شد",
        "status_filtered": "فیلتر شد",
        "confirm_clear_log": "آیا از پاک کردن کامل تاریخچه اسکن‌ها اطمینان دارید؟",
        "export_success": "تعداد {count} رکورد با موفقیت در مسیر {path} ذخیره شد.",

        # Prefix & Suffix Builder
        "wedge_title": "سازنده بصری کلیدهای پیشوند و پسوند (بدون نیاز به کدنویسی)",
        "wedge_desc": "کلیدها یا متنی که قبل از بارکد (پیشوند) یا بعد از آن (پسوند) تایپ می‌شوند را تعیین کنید. با کلیک روی دکمه‌های زیر، کلیدها به سادگی اضافه می‌شوند.",
        "lbl_prefix": "پیشوند (قبل از بارکد تایپ می‌شود):",
        "lbl_suffix": "پسوند (بعد از بارکد تایپ می‌شود):",
        "lbl_preview": "پیش‌نمایش زنده خروجی تایپ:",
        "preset_none": "هیچکدام (خالی)",
        "preset_enter": "اینتر / Enter (خط بعد)",
        "preset_tab": "تب / Tab (پرش به فیلد بعد)",
        "preset_space": "فاصله / Space",
        "preset_double_enter": "دو بار اینتر (Double Enter)",
        "preset_tab_enter": "تب سپس اینتر (Tab + Enter)",
        "preset_backspace": "پاک کردن / Backspace",
        "preset_esc": "خروج / Escape",
        "preset_down": "فلش رو به پایین (Down)",
        "btn_add_enter": "+ اینتر (Enter)",
        "btn_add_tab": "+ تب (Tab)",
        "btn_add_space": "+ فاصله (Space)",
        "btn_add_backspace": "+ پاک‌کردن (Bksp)",
        "btn_add_esc": "+ خروج (Esc)",
        "btn_add_down": "+ فلش پایین (Down)",
        "btn_add_date": "+ تاریخ جاری",
        "btn_add_time": "+ ساعت جاری",
        "btn_clear_field": "پاک کردن",

        # Connection Assistant & QR Generator
        "conn_title": "دستیار اتصال هوشمند و تولیدکننده کد QR اختصاصی BinaryEye",
        "conn_desc": "یکی از کدهای QR زیر را با دوربین برنامه BinaryEye در گوشی اسکن کنید تا اتصال بدون معطلی برقرار شود.",
        "subtab_qr_url": "۱. آدرس فوروارد معمولی",
        "subtab_qr_direct": "۲. اسکن پیوسته مستقیم (فوری)",
        "subtab_qr_encode": "۳. ارسال بارکد به گوشی",
        "lbl_lan_ip": "آدرس آی‌پی کامپیوتر در شبکه محلی:",
        "lbl_http_url": "آدرس دریافت فوروارد شبکه (HTTP):",
        "btn_copy_url": "کپی کردن آدرس",
        "url_copied": "آدرس در کلیپ‌بورد کپی شد!",
        "desc_qr_url": "۱. برنامه BinaryEye را در گوشی باز کنید.\n۲. به مسیر Settings > Forwarding > URL بروید.\n۳. این آدرس را وارد کنید یا با اسکن این بارکد آدرس را در گوشی کپی نمایید.",
        "desc_qr_direct": "این کد QR را مستقیماً با برنامه BinaryEye اسکن کنید تا حالت اسکن پیوسته و فوروارد خودکار به کامپیوتر فوراً و بدون نیاز به تنظیمات شروع شود!",
        "lbl_encode_text": "متنی که می‌خواهید به بارکد تبدیل شود:",
        "lbl_encode_format": "نوع بارکد خروجی:",
        "btn_generate_encode_qr": "به‌روزرسانی کد بارکد",
        "desc_qr_encode": "این بارکد را اسکن کنید تا متن فوق مستقیماً توسط BinaryEye روی صفحه گوشی تولید شود.",

        # Settings
        "sec_general": "پیکربندی عمومی نرم‌افزار",
        "sec_network": "شبکه محلی و سرور HTTP",
        "sec_bluetooth": "ارتباط بلوتوث (RFCOMM)",
        "sec_wedge": "تنظیمات تایپ و تزریق کلیدها",
        "sec_dedup": "موتور جلوگیری از اسکن‌های تکراری",
        "sec_filters": "فیلترها و تبدیل‌های متنی",

        "lbl_mode": "حالت کاری سرور:",
        "opt_mode_both": "همزمان ترکیبی (بلوتوث + شبکه Wi-Fi)",
        "opt_mode_http": "فقط شبکه و وای‌فای (HTTP)",
        "opt_mode_bt": "فقط بلوتوث (RFCOMM)",

        "lbl_port": "پورت شبکه HTTP:",
        "lbl_host": "آدرس رابط شبکه:",
        "lbl_bt_uuid": "شناسه سرویس بلوتوث (UUID):",
        "lbl_out_mode": "حالت تزریق متن در ویندوز:",
        "opt_out_type": "شبیه‌سازی ضربه کلید (SendInput Unicode)",
        "opt_out_paste": "پیست سریع از کلیپ‌بورد (Ctrl+V)",
        "opt_out_copy": "فقط کپی در کلیپ‌بورد (بدون تایپ)",

        "lbl_inter_key": "فاصله زمانی بین هر کلید (میلی‌ثانیه):",
        "lbl_pre_delay": "تاخیر قبل از شروع تایپ (میلی‌ثانیه):",
        "chk_restore_clip": "بازگردانی محتوای قبلی کلیپ‌بورد بعد از پیست",

        "chk_dedup_enabled": "فعال‌سازی حذف هوشمند اسکن‌های تکراری",
        "lbl_dedup_window": "بازه زمانی بررسی تکرار (میلی‌ثانیه):",

        "chk_trim_space": "حذف فاصله‌های اضافی ابتدا و انتهای بارکد",
        "lbl_replace_newlines": "جایگزینی اینترهای داخل بارکد با:",
        "opt_nl_none": "بدون تغییر (حفظ خطوط)",
        "opt_nl_tab": "تبدیل به تب (Tab)",
        "opt_nl_space": "تبدیل به فاصله (Space)",

        "lbl_regex_pat": "الگوی جستجوی عبارات باقاعده (Regex):",
        "lbl_regex_rep": "متن جایگزین برای الگو:",
        "lbl_allowed_fmt": "انواع بارکد مجاز (با کاما جدا کنید یا 'all'):",
        "chk_auto_url": "اگر بارکد یک آدرس وب (URL) بود، در مرورگر باز شود",
        "chk_copy_always": "همیشه یک کپی از بارکد در کلیپ‌بورد ذخیره شود",

        "chk_beep": "پخش صدای بیپ هنگام دریافت موفق بارکد",
        "chk_tray_notify": "نمایش نوتیفیکیشن ویندوز در کنار ساعت",
        "chk_start_windows": "اجرای خودکار نرم‌افزار هنگام روشن شدن ویندوز",
        "chk_auto_start": "شروع به کار خودکار سرور پس از اجرای برنامه",
        "chk_start_min": "اجرا به صورت کوچک‌شده در کنار ساعت (Tray)",
        "chk_min_tray": "هنگام بستن پنجره (X)، برنامه در کنار ساعت فعال بماند",

        "btn_save_settings": "ذخیره تنظیمات در فایل settings.ini",
        "settings_saved": "تنظیمات با موفقیت ذخیره و اعمال شد!",

        # System Tray Menu
        "tray_title": "باینری‌رسپتور v3.0.0",
        "tray_status_header": "وضعیت: {status}",
        "tray_start": "شروع به کار سرور",
        "tray_stop": "توقف سرور",
        "tray_mode_both": "حالت: همزمان (بلوتوث و شبکه)",
        "tray_mode_http": "حالت: فقط شبکه (HTTP)",
        "tray_mode_bt": "حالت: فقط بلوتوث",
        "tray_show_qr": "نمایش کد QR و راهنمای اتصال...",
        "tray_show_window": "باز کردن پنجره اصلی",
        "tray_exit": "خروج کامل از برنامه",
        "toast_scan_title": "بارکد دریافت شد ({source})",
    },
}


def tr(key: str, lang: str = "en", **kwargs: Any) -> str:
    """Retrieve localized string with optional formatting arguments."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
