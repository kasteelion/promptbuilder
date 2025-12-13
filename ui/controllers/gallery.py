"""Gallery controller: isolates gallery-related interactions from main_window.

The controller holds references to the app's gallery widgets and exposes
small adapter methods (load, apply_theme, toggle_visibility, on_character_selected)
so `ui/main_window.py` can be simplified incrementally.
"""

import tkinter as tk
from typing import Optional


class GalleryController:
    """Lightweight controller for the character gallery.

    This intentionally minimizes logic and keeps behavior identical while
    providing a single place to add gallery-related behaviors and tests.
    """

    def __init__(self, app):
        self.app = app
        # These are populated when UI is built
        self.character_gallery = getattr(app, "character_gallery", None)
        self.gallery_frame = getattr(app, "gallery_frame", None)
        self.main_paned = getattr(app, "main_paned", None)
        self.prefs = getattr(app, "prefs", None)
        self.menu_manager = getattr(app, "menu_manager", None)

        # If a gallery widget exists, ensure its callback points here
        if self.character_gallery is not None:
            try:
                self.character_gallery.on_add_callback = self.on_character_selected
            except Exception:
                # Best-effort binding; keep app functional if attribute differs
                pass

    def load_characters(self, characters: dict):
        """Load characters into the gallery widget."""
        if not self.character_gallery:
            return
        try:
            self.character_gallery.load_characters(characters)
        except Exception:
            # Defer to central logger on the app if available
            try:
                from utils import logger

                logger.exception("GalleryController: failed to load_characters")
            except Exception:
                pass

    def apply_theme(self, theme: dict):
        """Apply theme to gallery display."""
        if not self.character_gallery:
            return
        try:
            self.character_gallery.theme_colors = theme
            # Try to call the refresh helper if present
            if hasattr(self.character_gallery, "_refresh_display"):
                self.character_gallery._refresh_display()
        except Exception:
            try:
                from utils import logger

                logger.debug("GalleryController: failed to apply theme", exc_info=True)
            except Exception:
                pass

    def toggle_visibility(self, visible: bool, characters: Optional[dict] = None):
        """Show or hide the gallery pane.

        Args:
            visible: desired visibility state
            characters: optional characters dict to reload when showing
        """
        try:
            if visible:
                # Show gallery - insert at position 0 (leftmost)
                try:
                    self.main_paned.insert(0, self.gallery_frame, weight=2)
                    if characters is not None:
                        self.load_characters(characters)
                except tk.TclError:
                    # already present
                    pass
            else:
                try:
                    self.main_paned.forget(self.gallery_frame)
                except tk.TclError:
                    pass
        except Exception:
            try:
                from utils import logger

                logger.exception("GalleryController: toggle_visibility failed")
            except Exception:
                pass

    def on_character_selected(self, character_name: str):
        """Callback invoked when a character is selected in the gallery.

        The default behavior mirrors the previous implementation in
        `main_window._on_gallery_character_selected` by delegating to
        the characters tab and scheduling a preview update.
        """
        try:
            # Delegate to characters tab to add the selected character
            self.app.characters_tab.add_character_from_gallery(character_name)
            # Schedule preview update via the app's method
            try:
                self.app.schedule_preview_update()
            except Exception:
                # fallback: do nothing
                pass
        except Exception:
            try:
                from utils import logger

                logger.exception("GalleryController: error handling character selection")
            except Exception:
                pass
