"""Window state controller: manages window geometry, state, and related prefs."""
from typing import Any
import tkinter as tk


class WindowStateController:
    """Encapsulates saving/restoring window geometry and state.

    This isolates platform-specific handling (e.g., invalid geometry strings)
    from `PromptBuilderApp` and centralizes preferences updates.
    """
    def __init__(self, app: Any):
        self.app = app
        self.root = getattr(app, 'root', None)
        self.prefs = getattr(app, 'prefs', None)

    def restore_geometry_and_state(self):
        """Restore saved geometry and state if present. Returns True on success."""
        if not self.root or not self.prefs:
            return False
        saved_geometry = self.prefs.get('window_geometry')
        saved_state = self.prefs.get('window_state')
        if saved_geometry:
            try:
                self.root.geometry(saved_geometry)
            except (tk.TclError, ValueError):
                # ignore invalid geometry and leave defaults
                return False
        if saved_state and saved_state in ('zoomed', 'normal', 'iconic'):
            try:
                self.root.state(saved_state)
            except tk.TclError:
                pass
        return True

    def save_geometry_and_state(self):
        """Save current geometry and window state into preferences."""
        if not self.root or not self.prefs:
            return False
        try:
            window_state = self.root.state()
            self.prefs.set('window_state', window_state)
        except Exception:
            # Best effort; ignore failures
            pass
        try:
            geom = self.root.geometry()
            self.prefs.set('window_geometry', geom)
        except Exception:
            pass
        return True
