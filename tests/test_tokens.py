"""Tests for visual Prefix & Suffix token compiler and canonicalization."""
from __future__ import annotations

from src.config import canonicalize_token, parse_tokens, format_token_preview, TOKEN_VK_MAP


def test_canonicalize_token_aliases():
    assert canonicalize_token("\\n") == "{ENTER}"
    assert canonicalize_token("\\r\\n") == "{ENTER}"
    assert canonicalize_token("enter") == "{ENTER}"
    assert canonicalize_token("ENTER") == "{ENTER}"
    assert canonicalize_token("{ENTER}") == "{ENTER}"
    assert canonicalize_token("\\t") == "{TAB}"
    assert canonicalize_token("tab") == "{TAB}"
    assert canonicalize_token("space") == "{SPACE}"
    assert canonicalize_token("backspace") == "{BACKSPACE}"
    assert canonicalize_token("esc") == "{ESC}"
    assert canonicalize_token("down") == "{DOWN}"
    assert canonicalize_token("none") == ""


def test_parse_simple_tokens():
    actions = parse_tokens("{ENTER}")
    assert len(actions) == 1
    assert actions[0] == ("vk", TOKEN_VK_MAP["ENTER"])

    actions_tab = parse_tokens("{TAB}")
    assert len(actions_tab) == 1
    assert actions_tab[0] == ("vk", TOKEN_VK_MAP["TAB"])


def test_parse_compound_tokens():
    actions = parse_tokens("{TAB}{ENTER}")
    assert len(actions) == 2
    assert actions[0] == ("vk", TOKEN_VK_MAP["TAB"])
    assert actions[1] == ("vk", TOKEN_VK_MAP["ENTER"])


def test_parse_mixed_literal_and_tokens():
    actions = parse_tokens("PREFIX_{TAB}_SUFFIX_{ENTER}")
    assert len(actions) == 4
    assert actions[0] == ("text", "PREFIX_")
    assert actions[1] == ("vk", TOKEN_VK_MAP["TAB"])
    assert actions[2] == ("text", "_SUFFIX_")
    assert actions[3] == ("vk", TOKEN_VK_MAP["ENTER"])


def test_parse_dynamic_date_and_time():
    actions = parse_tokens("{DATE}_{TIME}")
    assert len(actions) == 3
    assert actions[0][0] == "text"
    assert len(actions[0][1]) == 10  # YYYY-MM-DD
    assert actions[1] == ("text", "_")
    assert actions[2][0] == "text"
    assert len(actions[2][1]) == 8   # HH:MM:SS


def test_format_token_preview():
    preview = format_token_preview("{TAB}", "123456", "{ENTER}")
    assert preview == "\t123456\n"
    assert "{TAB}" not in preview
    assert "{ENTER}" not in preview


def test_backspace_keystroke_rendering():
    preview = format_token_preview("", "ABCD{BACKSPACE}E", "{ENTER}")
    assert preview == "ABCE\n"
