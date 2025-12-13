"""Menu actions controller: centralize menu callbacks for `PromptBuilderApp`.

This adapter keeps `main_window` smaller and makes menu-related logic
easier to test and evolve.
"""
from typing import Any


class MenuActions:
    """Adapter exposing menu callbacks used by `MenuManager`.

    Each method delegates to the corresponding `PromptBuilderApp` method
    to preserve existing behavior while keeping `main_window` focused on UI layout.
    """
    def __init__(self, app: Any):
        self.app = app

    def save_preset(self):
        return self.app._save_preset()

    def load_preset(self):
        return self.app._load_preset()

    def export_config(self):
        return self.app._export_config()

    def import_config(self):
        return self.app._import_config()

    def undo(self):
        return self.app._undo()

    def redo(self):
        return self.app._redo()

    def clear_all_characters(self):
        return self.app._clear_all_characters()

    def reset_all_outfits(self):
        return self.app._reset_all_outfits()

    def apply_same_pose_to_all(self):
        return self.app._apply_same_pose_to_all()

    def toggle_character_gallery(self):
        # Toggle the flag then delegate to main_window logic which now uses GalleryController
        self.app._toggle_character_gallery()

    def increase_font(self):
        return self.app._increase_font()

    def decrease_font(self):
        return self.app._decrease_font()

    def reset_font(self):
        return self.app._reset_font()

    def randomize_all(self):
        return self.app.randomize_all()

    def change_theme(self, theme_name: str):
        return self.app._change_theme(theme_name)

    def toggle_auto_theme(self):
        return self.app._toggle_auto_theme()

    def show_characters_summary(self):
        return self.app.dialog_manager.show_characters_summary()

    def show_welcome(self):
        return self.app.dialog_manager.show_welcome()

    def show_shortcuts(self):
        return self.app.dialog_manager.show_shortcuts()

    def show_about(self):
        return self.app.dialog_manager.show_about()

    def on_closing(self):
        return self.app._on_closing()

    def get_theme(self):
        try:
            return self.app.menu_manager.get_theme()
        except Exception:
            return None

    def get_auto_theme(self):
        try:
            return self.app.menu_manager.get_auto_theme()
        except Exception:
            return False

    def set_gallery_visible(self, visible: bool):
        try:
            if hasattr(self.app, 'menu_manager'):
                self.app.menu_manager.set_gallery_visible(visible)
        except Exception:
            pass
