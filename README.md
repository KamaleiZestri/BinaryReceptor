# BinaryReceptor 3.0.0

BinaryReceptor is a lightweight Windows desktop receiver for barcode scans forwarded by [BinaryEye](https://github.com/markusfisch/BinaryEye). It receives HTTP GET and POST scans, displays an activity log, and can output scans as Unicode keystrokes.

## Compatibility

BinaryEye's current README documents LAN HTTP forwarding and HTTPS callbacks for continuous scanning. The callback sends one JSON POST per scan with fields such as `content`, hexadecimal `raw`, `format`, `scanId`, `timestamp`, and optional barcode metadata. BinaryReceptor accepts these fields, form-urlencoded requests, query parameters, and raw text bodies on `/` and `/scan`. Retries with the same payload are suppressed during the configured deduplication window. The current BinaryEye documentation does not describe WebSocket forwarding.

The checked-in Python port did not contain the legacy `hxBluetooth` or `hxKeyType` implementations. Bluetooth SDP/RFCOMM registration therefore remains unavailable in this port. `bluetooth` mode reports this clearly; `both` currently runs the supported HTTP listener. No claim is made that Bluetooth is active. HTTP is the default.

## Run from source

Requires Python 3.11+ on Windows.

```powershell
py -3.12 -m pip install -r requirements-build.txt
py -3.12 -m binaryreceptor.app
```

In BinaryEye, enable scan forwarding and set the displayed LAN URL as the destination. Select JSON POST for complete format and metadata fields. Windows Firewall may ask to allow the listener on a private network.

## Configuration

Edit `settings.ini` next to `BinaryReceptor.exe`. Source runs use the repository root. The path is resolved independently of the current working directory and PyInstaller's extraction folder. Existing settings are loaded on startup, external file edits are polled while the app is open, and the reload button applies manual changes. Network settings restart the active listener when changed from disk.

`mode` supports `http`, `bluetooth`, or `both`; `host` supports an explicit address or `0.0.0.0`; `port` is 1024–65535; and `dedup_window_ms` is 0–10000. Output options include `type`, `paste`, `copy`, and `log`, plus configurable prefix/suffix tokens, typing delays, simple case transformation, regex replacement, symbology filtering, and optional CSV logging. Review the comments and defaults in `settings.ini` before changing network exposure.

Prefix/suffix strings accept `{ENTER}`, `{TAB}`, `{SPACE}`, `{BACKSPACE}`, `{ESC}`, and `{DELAY:100}` tokens. For example: `prefix = {ENTER}`. Plain text is emitted with Win32 Unicode `SendInput`.

## Build

```powershell
py -3.12 -m pip install -r requirements-build.txt
py -3.12 build.py
```

Or run `build.bat`. The one-file, no-console executable and editable `settings.ini` are written to `dist/`. GitHub Actions builds on pull requests and creates the `BinaryReceptor-v3.0.0-win64.zip` release asset when tag `v3.0.0` is pushed.

## License

See the repository history and upstream project for licensing details.
