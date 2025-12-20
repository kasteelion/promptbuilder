import os

from themes.theme_manager import ThemeManager


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


def test_notify_prefers_toast_then_status(monkeypatch):
    # Create a fake root with toasts
    class FakeToasts:
        def __init__(self):
            self.called = False

        def notify(self, message, level, duration):
            self.called = True

    class Root:
        pass

    root = Root()
    root.toasts = FakeToasts()

    # import lazily to allow monkeypatching messagebox
    from utils.notification import notify

    # Should call toast and not raise
    notify(root, "Title", "hi", level="info", duration=10)
    assert root.toasts.called


def test_notify_falls_back_to_status(monkeypatch):
    class Root:
        def __init__(self):
            self.updated = None

        def _update_status(self, msg):
            self.updated = msg

    root = Root()

    from utils.notification import notify

    notify(root, "T", "status-msg", level="info")
    assert root.updated == "status-msg"


def test_notify_modal_fallback(monkeypatch):
    # Remove both toasts and status; patch messagebox to capture calls
    import tkinter.messagebox as mb

    called = {}

    def fake_info(title, message, parent=None):
        called["info"] = (title, message)

    monkeypatch.setattr(mb, "showinfo", fake_info)

    from utils.notification import notify

    notify(None, "T", "modal-msg", level="info")
    assert "info" in called and called["info"][1] == "modal-msg"
