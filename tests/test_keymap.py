"""Tests for keymap-driven help overlay."""

from __future__ import annotations

from tuical.ui import keymap


def test_keymap_has_expected_sections():
    sections = set(keymap.KEYMAP.keys())
    assert {"quit", "navigation", "view", "actions", "search_palette"} <= sections


def test_quit_includes_q():
    keys = [k for k, _ in keymap.KEYMAP["quit"]]
    assert "q" in keys


def test_actions_includes_enter_edit_delete():
    keys = [k for k, _ in keymap.KEYMAP["actions"]]
    assert any("Enter" in k for k in keys)
    assert any("e" in k for k in keys)
    assert any("D" in k for k in keys)


def test_view_includes_all_5_views():
    keys = " ".join(k for k, _ in keymap.KEYMAP["view"])
    for v in ("y", "m", "w", "d", "a"):
        assert v in keys, f"view key '{v}' missing from keymap"


def test_render_help_contains_all_key_labels():
    text = keymap.render_help()
    for section in keymap.KEYMAP.values():
        for keys, _ in section:
            assert keys in text, f"key label '{keys}' not in rendered help"


def test_render_help_includes_header():
    text = keymap.render_help()
    assert "tuical — keybindings" in text


def test_render_help_default_uses_module_keymap():
    text = keymap.render_help()
    explicit = keymap.render_help(keymap.KEYMAP)
    assert text == explicit


def test_render_help_custom_keymap_works():
    custom = {"custom": [("x", "do x")]}
    text = keymap.render_help(custom)
    assert "do x" in text
    assert "x" in text


def test_nav_hint_for_truncates_to_few_items():
    hint = keymap.nav_hint_for("month")
    assert isinstance(hint, str)
    assert hint.startswith("  ")
    assert " · " in hint


def test_help_text_matches_rendered_keymap():
    """ui/help.HELP_TEXT should be identical to render_help(KEYMAP)."""
    from tuical.ui import help as help_view

    assert keymap.render_help(keymap.KEYMAP) == help_view.HELP_TEXT
