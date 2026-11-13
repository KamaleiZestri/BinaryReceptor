"""Tests for KeyInjector Unicode keystroke simulation and token execution."""
from __future__ import annotations

from src.core.key_injector import KeyInjector, VK_RETURN, VK_TAB


def test_dry_run_unicode_keystroke_recording():
    injector = KeyInjector(dry_run=True)
    injector.type_unicode_string("HELLO فارسی 123")

    assert len(injector.recorded_events) == 1
    assert injector.recorded_events[0] == ("unicode", "HELLO فارسی 123")


def test_dry_run_vk_key_press():
    injector = KeyInjector(dry_run=True)
    injector.press_vk(VK_RETURN)
    injector.press_vk(VK_TAB)

    assert len(injector.recorded_events) == 2
    assert injector.recorded_events[0] == ("vk", VK_RETURN)
    assert injector.recorded_events[1] == ("vk", VK_TAB)


def test_dry_run_full_scan_injection_sequence():
    injector = KeyInjector(dry_run=True)
    injector.inject_scan(
        content="SCAN-1234",
        prefix_template="{TAB}",
        suffix_template="{ENTER}",
        output_mode="type",
    )

    events = injector.recorded_events
    # Expected sequence: [ ('vk', VK_TAB), ('unicode', 'SCAN-1234'), ('vk', VK_RETURN) ]
    assert len(events) == 3
    assert events[0] == ("vk", VK_TAB)
    assert events[1] == ("unicode", "SCAN-1234")
    assert events[2] == ("vk", VK_RETURN)


def test_dry_run_copy_only_mode():
    injector = KeyInjector(dry_run=True)
    injector.inject_scan(
        content="COPY-THIS",
        output_mode="copy_only",
    )

    assert len(injector.recorded_events) == 1
    assert injector.recorded_events[0] == ("copy_only", "COPY-THIS")
