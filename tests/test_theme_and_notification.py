import os

from ui.themes.theme_manager import ThemeManager


class _FakeStyle:
    def __init__(self):
        self._used = None

    def theme_use(self, name):
        self._used = name

    def configure(self, *args, **kwargs):
        # accept configure calls
        pass

    def map(self, *args, **kwargs):
        pass


class _FakeRoot:
    def __init__(self):
        self.configured = {}

    def config(self, **kwargs):
        self.configured.update(kwargs)


class PrefsMock:
    def __init__(self, store=None):
        self._store = store or {}

    def get(self, k, default=None):
        return self._store.get(k, default)

    def set(self, k, v):
        self._store[k] = v


def test_parse_themes_md_and_reload(tmp_path):
    md_path = tmp_path / "themes.md"
    md_path.write_text(
        """
## Custom Theme
```yaml
bg: "#101010"
fg: "#ffffff"
preview_bg: "#121212"
preview_fg: "#eeeeee"
text_bg: "#111111"
text_fg: "#dddddd"
accent: "#FF0000"
border: "#222222"
```
"""
    )

    style = _FakeStyle()
    root = _FakeRoot()
    tm = ThemeManager(root, style)
    # reload from our md path
    assert tm.reload_md_themes(path=str(md_path)) is True
    assert "Custom Theme" in tm.themes
    assert tm.themes["Custom Theme"]["bg"] == "#101010"


def test_migrate_from_prefs_writes_md_and_clears(tmp_path, monkeypatch):
    # Create a temp cwd so ThemeManager writes into tmp data/themes.md
    old_cwd = os.getcwd()
    try:
        os.chdir(str(tmp_path))
        prefs = PrefsMock({"custom_themes": {"FromPrefs": {"bg": "#010101", "fg": "#f1f1f1"}}})

        style = _FakeStyle()
        root = _FakeRoot()
        tm = ThemeManager(root, style)
        migrated = tm.migrate_from_prefs(prefs)
        assert migrated is True
        # file should exist
        md_file = tmp_path / "data" / "themes.md"
        assert md_file.exists()
        # prefs custom_themes should now be cleared
        assert prefs.get("custom_themes") == {}
        # runtime themes include migrated theme
        assert "FromPrefs" in tm.themes
    finally:
        os.chdir(old_cwd)

