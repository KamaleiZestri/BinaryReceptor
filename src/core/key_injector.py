"""Low-level native Win32 keyboard injection and clipboard engine for BinaryReceptor v3.0.0.

Provides direct Win32 SendInput Unicode character injection (KEYEVENTF_UNICODE),
Virtual-Key injection (VK_RETURN, VK_TAB, etc.), Ctrl+V clipboard paste mode,
and clipboard content restoration.
"""
from __future__ import annotations

import ctypes
import os
import struct
import sys
import time
from ctypes import wintypes
from typing import Any, Sequence

from src.config import parse_tokens

# Win32 Constants
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_DELETE = 0x2E
VK_V = 0x56
VK_C = 0x43
VK_A = 0x41

ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUTunion),
    ]


# Win32 Clipboard API bindings
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

user32 = None
kernel32 = None

if os.name == "nt":
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        user32.SendInput.argtypes = [wintypes.UINT, ctypes.c_void_p, ctypes.c_int]
        user32.SendInput.restype = wintypes.UINT

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = wintypes.BOOL
        user32.EmptyClipboard.argtypes = []
        user32.EmptyClipboard.restype = wintypes.BOOL
        user32.GetClipboardData.argtypes = [wintypes.UINT]
        user32.GetClipboardData.restype = wintypes.HANDLE
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE

        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL
        kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalFree.restype = wintypes.HGLOBAL
    except Exception:
        pass


def win32_get_clipboard_text() -> str:
    """Retrieve UTF-16 text from Windows clipboard natively."""
    if not user32 or not kernel32:
        return ""
    text = ""
    for _ in range(5):
        if user32.OpenClipboard(None):
            try:
                h_data = user32.GetClipboardData(CF_UNICODETEXT)
                if h_data:
                    p_data = kernel32.GlobalLock(h_data)
                    if p_data:
                        try:
                            text = ctypes.wstring_at(p_data)
                        finally:
                            kernel32.GlobalUnlock(h_data)
            finally:
                user32.CloseClipboard()
            break
        time.sleep(0.01)
    return text


def win32_set_clipboard_text(text: str) -> bool:
    """Set UTF-16 text to Windows clipboard natively."""
    if not user32 or not kernel32:
        return False
    raw = (text + "\0").encode("utf-16-le")
    for _ in range(5):
        if user32.OpenClipboard(None):
            try:
                user32.EmptyClipboard()
                h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(raw))
                if h_mem:
                    ptr = kernel32.GlobalLock(h_mem)
                    if ptr:
                        ctypes.memmove(ptr, raw, len(raw))
                        kernel32.GlobalUnlock(h_mem)
                        user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                        return True
            finally:
                user32.CloseClipboard()
            break
        time.sleep(0.01)
    return False


class KeyInjector:
    """Zero-dependency Win32 SendInput Unicode and Virtual-Key injector."""

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run or (user32 is None)
        self.recorded_events: list[tuple[str, Any]] = []

    def _send_inputs(self, events: Sequence[INPUT]) -> int:
        if not events:
            return 0
        if self.dry_run or not user32:
            return len(events)
        arr = (INPUT * len(events))(*events)
        return user32.SendInput(len(events), ctypes.byref(arr), ctypes.sizeof(INPUT))

    @staticmethod
    def make_vk_event(vk_code: int, key_up: bool = False) -> INPUT:
        dw_flags = KEYEVENTF_KEYUP if key_up else 0
        return INPUT(
            type=INPUT_KEYBOARD,
            union=_INPUTunion(
                ki=KEYBDINPUT(
                    wVk=vk_code,
                    wScan=0,
                    dwFlags=dw_flags,
                    time=0,
                    dwExtraInfo=0,
                )
            ),
        )

    @staticmethod
    def make_unicode_event(code_unit: int, key_up: bool = False) -> INPUT:
        dw_flags = KEYEVENTF_UNICODE
        if key_up:
            dw_flags |= KEYEVENTF_KEYUP
        return INPUT(
            type=INPUT_KEYBOARD,
            union=_INPUTunion(
                ki=KEYBDINPUT(
                    wVk=0,
                    wScan=code_unit,
                    dwFlags=dw_flags,
                    time=0,
                    dwExtraInfo=0,
                )
            ),
        )

    def press_vk(self, vk_code: int) -> None:
        """Press and release a virtual key."""
        if self.dry_run:
            self.recorded_events.append(("vk", vk_code))
            return
        events = [
            self.make_vk_event(vk_code, key_up=False),
            self.make_vk_event(vk_code, key_up=True),
        ]
        self._send_inputs(events)

    def type_unicode_string(self, text: str, inter_key_delay_ms: int = 0) -> None:
        """Inject arbitrary Unicode text using SendInput KEYEVENTF_UNICODE."""
        if not text:
            return
        if self.dry_run:
            self.recorded_events.append(("unicode", text))
            return

        utf16_bytes = text.encode("utf-16-le")
        code_units = [
            struct.unpack("<H", utf16_bytes[i : i + 2])[0]
            for i in range(0, len(utf16_bytes), 2)
        ]

        if inter_key_delay_ms <= 0:
            events = []
            for cu in code_units:
                events.append(self.make_unicode_event(cu, key_up=False))
                events.append(self.make_unicode_event(cu, key_up=True))
            self._send_inputs(events)
        else:
            delay_sec = inter_key_delay_ms / 1000.0
            for cu in code_units:
                events = [
                    self.make_unicode_event(cu, key_up=False),
                    self.make_unicode_event(cu, key_up=True),
                ]
                self._send_inputs(events)
                time.sleep(delay_sec)

    def paste_via_clipboard(self, text: str, restore_clipboard: bool = True) -> bool:
        """Inject text by copying to Windows clipboard and sending Ctrl+V."""
        if not text:
            return True
        if self.dry_run:
            self.recorded_events.append(("paste", text))
            return True

        old_clipboard = win32_get_clipboard_text() if restore_clipboard else ""

        # Set new content to clipboard
        if not win32_set_clipboard_text(text):
            # Fallback to Unicode typing if clipboard access fails
            self.type_unicode_string(text)
            return False

        time.sleep(0.015)

        # Send Ctrl+V keystrokes
        ctrl_down = self.make_vk_event(VK_CONTROL, key_up=False)
        v_down = self.make_vk_event(VK_V, key_up=False)
        v_up = self.make_vk_event(VK_V, key_up=True)
        ctrl_up = self.make_vk_event(VK_CONTROL, key_up=True)

        self._send_inputs([ctrl_down, v_down, v_up, ctrl_up])

        # Delay to ensure target application reads clipboard before restoration
        if restore_clipboard:
            time.sleep(0.05)
            win32_set_clipboard_text(old_clipboard)

        return True

    def execute_actions(self, actions: list[tuple[str, Any]], inter_key_delay_ms: int = 0) -> None:
        """Execute parsed token actions sequentially."""
        for action_type, val in actions:
            if action_type == "text":
                self.type_unicode_string(str(val), inter_key_delay_ms)
            elif action_type == "vk":
                self.press_vk(int(val))
            elif action_type == "delay":
                time.sleep(max(0, int(val)) / 1000.0)

    def inject_scan(
        self,
        content: str,
        prefix_template: str = "",
        suffix_template: str = "{ENTER}",
        output_mode: str = "type",
        inter_key_delay_ms: int = 0,
        pre_typing_delay_ms: int = 0,
        restore_clipboard: bool = True,
        copy_to_clipboard: bool = False,
    ) -> None:
        """Inject full scanned content with prefix, suffix, and configured mode."""
        if copy_to_clipboard and not self.dry_run:
            win32_set_clipboard_text(content)

        if output_mode == "copy_only":
            if not self.dry_run:
                win32_set_clipboard_text(content)
            else:
                self.recorded_events.append(("copy_only", content))
            return

        if pre_typing_delay_ms > 0:
            time.sleep(pre_typing_delay_ms / 1000.0)

        # 1. Type Prefix
        if prefix_template:
            prefix_actions = parse_tokens(prefix_template)
            self.execute_actions(prefix_actions, inter_key_delay_ms)

        # 2. Type/Paste Content
        if output_mode == "paste":
            self.paste_via_clipboard(content, restore_clipboard=restore_clipboard)
        else:
            self.type_unicode_string(content, inter_key_delay_ms)

        # 3. Type Suffix
        if suffix_template:
            suffix_actions = parse_tokens(suffix_template)
            self.execute_actions(suffix_actions, inter_key_delay_ms)
