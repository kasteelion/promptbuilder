"""Tests for ThemeManager (Flet-based)."""

from unittest.mock import MagicMock
from core.flet_theme_manager import ThemeManager


def test_get_available_themes():
    """ThemeManager should return a sorted list of theme names."""
    themes = ThemeManager.get_available_themes()
    assert isinstance(themes, list)
    assert len(themes) > 0
    # Should be sorted
    assert themes == sorted(themes)


def test_get_theme_accent_known():
    """Get accent for a known theme."""
    themes = ThemeManager.get_themes()
    if themes:
        first_name = next(iter(themes))
        accent = ThemeManager.get_theme_accent(first_name)
        assert accent.startswith("#")


def test_get_theme_accent_unknown():
    """Unknown theme returns default accent."""
    accent = ThemeManager.get_theme_accent("NonExistentTheme_12345")
    assert accent == "#3ea6ff"


def test_apply_theme_updates_colors():
    """Applying a theme should update the semantic color palette."""
    page = MagicMock()
    page.update = MagicMock()

    old_surface = ThemeManager.colors["surface"]
    themes = ThemeManager.get_themes()
    if len(themes) >= 2:
        # Pick a theme different from current
        names = list(themes.keys())
        target = names[0] if ThemeManager.colors["surface"] != themes[names[0]].get("bg") else names[1]
        ThemeManager.apply_theme(page, target)
        # Surface should have been updated
        assert ThemeManager.colors["surface"] == themes[target].get("bg", "#1e1e1e")
        page.update.assert_called()

    # Restore
    ThemeManager.apply_theme(page, "Dark")


def test_apply_unknown_theme_falls_back():
    """Applying an unknown theme name should fall back to Dark."""
    page = MagicMock()
    page.update = MagicMock()
    ThemeManager.apply_theme(page, "NonExistentTheme_12345")
    # Should not crash, and should use Dark fallback
    page.update.assert_called()
