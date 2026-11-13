"""Small Win32 SendInput wrapper for Unicode text and common key tokens."""
from __future__ import annotations
import ctypes
import os
import re
import time
from ctypes import wintypes

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK = {"enter": 0x0D, "tab": 0x09, "space": 0x20, "backspace": 0x08, "escape": 0x1B, "esc": 0x1B}
VK.update({"ctrl": 0x11, "v": 0x56})

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]
class INPUTUNION(ctypes.Union): _fields_ = [("ki", KEYBDINPUT)]
class INPUT(ctypes.Structure): _fields_ = [("type", wintypes.DWORD), ("union", INPUTUNION)]

def _send(vk: int = 0, scan: int = 0, flags: int = 0) -> None:
    if os.name != "nt": raise OSError("Win32 keyboard output is available on Windows only")
    event = INPUT(type=INPUT_KEYBOARD, union=INPUTUNION(ki=KEYBDINPUT(vk, scan, flags, 0, 0)))
    if ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT)) != 1:
        raise ctypes.WinError()

def type_text(text: str, delay_ms: int = 0) -> None:
    for char in text:
        code = ord(char)
        # SendInput Unicode uses UTF-16 code units; emit surrogate pairs for non-BMP text.
        units = char.encode("utf-16-le", "surrogatepass")
        for offset in range(0, len(units), 2):
            unit = int.from_bytes(units[offset:offset + 2], "little")
            _send(scan=unit, flags=KEYEVENTF_UNICODE); _send(scan=unit, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)
        if delay_ms: time.sleep(delay_ms / 1000)

def type_token(token: str) -> None:
    name = token.strip().strip("{}").lower()
    if name in ("", "none"): return
    if name == "ctrl+v":
        _send(vk=VK["ctrl"]); _send(vk=VK["v"]); _send(vk=VK["v"], flags=KEYEVENTF_KEYUP); _send(vk=VK["ctrl"], flags=KEYEVENTF_KEYUP)
        return
    if name in VK:
        vk = VK[name]; _send(vk=vk); _send(vk=vk, flags=KEYEVENTF_KEYUP)
    elif name.startswith("delay:"):
        time.sleep(max(0, min(10000, int(name.split(":", 1)[1]))) / 1000)
    elif name.startswith("text:"): type_text(token[5:])
    elif name.startswith("legacy:"):
        type_text(token[7:].replace(r"\n", "\n").replace(r"\r", "\r").replace(r"\t", "\t"))
    else: type_text(token)

TOKEN = re.compile(r"\{(ENTER|TAB|SPACE|BACKSPACE|ESC|DELAY:\d+)\}", re.IGNORECASE)
def type_template(value: str, delay_ms: int = 0) -> None:
    cursor = 0
    for match in TOKEN.finditer(value):
        type_text(value[cursor:match.start()], delay_ms)
        type_token(match.group(1))
        cursor = match.end()
    type_text(value[cursor:], delay_ms)
