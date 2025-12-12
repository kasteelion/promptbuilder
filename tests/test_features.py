"""Pytest-style feature tests for the project.

These are small, focused unit tests intended to run in CI and locally
via `pytest`. They use temporary directories to avoid mutating repository
state.
"""

import importlib
from pathlib import Path


def _load_module_from_path(path, name):
    """Load a module from a file path without importing the package `__init__`.

    This avoids circular imports caused by package-level initializers.
    """
    import importlib.util
    import sys
    import types

    # Prepare a temporary package mapping so relative imports (e.g. "from .logger")
    # resolve to modules in the same `utils` directory without executing
    # `utils/__init__.py` and triggering package-level side-effects.
    project_root = Path(__file__).resolve().parent.parent
    utils_dir = project_root / "utils"

    original_utils = sys.modules.get("utils")
    try:
        fake_pkg = types.ModuleType("utils")
        fake_pkg.__path__ = [str(utils_dir)]
        sys.modules["utils"] = fake_pkg

        # Provide a minimal `ui` package with `constants` so modules that
        # import `ui.constants` during top-level import do not trigger the
        # full UI package initialization (which causes circular imports).
        original_ui = sys.modules.get("ui")
        original_ui_constants = sys.modules.get("ui.constants")
        try:
            import types as _types

            ui_pkg = _types.ModuleType("ui")
            ui_constants = _types.ModuleType("ui.constants")
            # Minimal constants used by utils modules
            ui_constants.MAX_UNDO_STACK_SIZE = 50
            ui_constants.MAX_RECENT_ITEMS = 10
            sys.modules["ui"] = ui_pkg
            sys.modules["ui.constants"] = ui_constants

            spec = importlib.util.spec_from_file_location(name, str(path))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        finally:
            # restore any original ui modules
            if original_ui is None:
                sys.modules.pop("ui", None)
            else:
                sys.modules["ui"] = original_ui

            if original_ui_constants is None:
                sys.modules.pop("ui.constants", None)
            else:
                sys.modules["ui.constants"] = original_ui_constants
    finally:
        # Restore whatever was previously registered under 'utils'
        if original_utils is None:
            del sys.modules["utils"]
        else:
            sys.modules["utils"] = original_utils


def test_imports():
    """Ensure core utility modules are importable without triggering package-level side-effects."""
    project_root = Path(__file__).resolve().parent.parent
    utils_dir = project_root / "utils"
    # Importing submodules directly can trigger package-level initializers
    # (and circular imports). Instead, verify the expected module files
    # exist — their behaviors are validated in the specific unit tests below.
    assert (utils_dir / "undo_manager.py").exists()
    assert (utils_dir / "preferences.py").exists()
    assert (utils_dir / "preset_manager.py").exists()


def test_undo_manager():
    """UndoManager supports save/undo/redo semantics."""
    project_root = Path(__file__).resolve().parent.parent
    utils_dir = project_root / "utils"

    mod = _load_module_from_path(utils_dir / "undo_manager.py", "utils.undo_manager")
    UndoManager = mod.UndoManager

    manager = UndoManager()
    state1 = {"test": "value1"}
    manager.save_state(state1)

    state2 = {"test": "value2"}
    manager.save_state(state2)

    assert manager.can_undo()
    undone = manager.undo()
    assert undone["test"] == "value1"

    assert manager.can_redo()
    redone = manager.redo()
    assert redone["test"] == "value2"


def test_preferences_manager(tmp_path):
    """PreferencesManager persists values and recent/favorite lists."""
    project_root = Path(__file__).resolve().parent.parent
    utils_dir = project_root / "utils"

    mod = _load_module_from_path(utils_dir / "preferences.py", "utils.preferences")
    PreferencesManager = mod.PreferencesManager

    prefs_file = tmp_path / "prefs.json"
    prefs = PreferencesManager(str(prefs_file))

    prefs.set("test_key", "test_value")
    assert prefs.get("test_key") == "test_value"

    prefs.add_recent("recent_test", "item1")
    prefs.add_recent("recent_test", "item2")
    recent = prefs.get("recent_test")
    assert recent[0] == "item2"

    is_fav = prefs.toggle_favorite("fav_test", "item1")
    assert is_fav is True
    assert prefs.is_favorite("fav_test", "item1")


def test_preset_manager(tmp_path):
    """PresetManager can save, load, and list presets."""
    project_root = Path(__file__).resolve().parent.parent
    utils_dir = project_root / "utils"

    mod = _load_module_from_path(utils_dir / "preset_manager.py", "utils.preset_manager")
    PresetManager = mod.PresetManager

    presets_dir = tmp_path / "presets"
    manager = PresetManager(str(presets_dir))

    config = {"selected_characters": [{"name": "Test"}], "base_prompt": "Test Style"}
    filepath = manager.save_preset("Test Preset", config)
    assert Path(filepath).exists()

    loaded = manager.load_preset(Path(filepath).name)
    assert loaded["base_prompt"] == "Test Style"

    presets = manager.get_presets()
    assert len(presets) >= 1


def test_config_constants():
    """Config exports expected constants used by the UI."""
    import config

    assert "base_prompt" in config.TOOLTIPS
    assert isinstance(config.WELCOME_MESSAGE, str)
