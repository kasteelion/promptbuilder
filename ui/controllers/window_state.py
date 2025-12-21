"""Window state controller: manages window geometry, state, and related prefs."""

import tkinter as tk
from typing import Any


class WindowStateController:
    """Encapsulates saving/restoring window geometry and state.

    This isolates platform-specific handling (e.g., invalid geometry strings)
    from `PromptBuilderApp` and centralizes preferences updates.
    """

    def __init__(self, app: Any):
        self.app = app
        self.root = getattr(app, "root", None)
        self.prefs = getattr(app, "prefs", None)

    def restore_geometry_and_state(self):
        """Restore saved geometry and state if present. Returns True on success."""
        if not self.root or not self.prefs:
            return False
        saved_geometry = self.prefs.get("window_geometry")
        saved_state = self.prefs.get("window_state")
        if saved_geometry:
            try:
                self.root.geometry(saved_geometry)
            except (tk.TclError, ValueError):
                # ignore invalid geometry and leave defaults
                return False
        if saved_state and saved_state in ("zoomed", "normal", "iconic"):
            try:
                self.root.state(saved_state)
            except tk.TclError:
                pass

        # Restore sash positions
        self._restore_sash_positions()
        return True

    def save_geometry_and_state(self):
        """Save current geometry and window state into preferences."""
        if not self.root or not self.prefs:
            return False
        try:
            window_state = self.root.state()
            self.prefs.set("window_state", window_state)
        except Exception:
            # Best effort; ignore failures
            pass
        try:
            geom = self.root.geometry()
            self.prefs.set("window_geometry", geom)
        except Exception:
            pass

        # Save sash positions
        self._save_sash_positions()
        return True

    def _save_sash_positions(self):
        """Save positions of all paned window sashes."""
        try:
            positions = {}
            # Main paned (Gallery | Content)
            if hasattr(self.app, "main_paned"):
                try:
                    positions["main_sash"] = self.app.main_paned.sashpos(0)
                except tk.TclError:
                    pass
            
            # Content paned (Notebook | Right Scroll)
            # Find the paned window inside main_paned.panes()
            if hasattr(self.app, "main_paned"):
                for pane in self.app.main_paned.panes():
                    try:
                        widget = self.root.nametowidget(pane)
                        if isinstance(widget, tk.PanedWindow) or isinstance(widget, tk.ttk.PanedWindow):
                            positions["content_sash"] = widget.sashpos(0)
                            break
                    except Exception:
                        continue
            
            if positions:
                self.prefs.set("sash_positions", positions)
        except Exception:
            pass

    def _restore_sash_positions(self):
        """Restore positions of all paned window sashes."""
        try:
            positions = self.prefs.get("sash_positions")
            if not positions:
                return

            def _apply():
                # Apply with a slight delay to ensure window is mapped
                if "main_sash" in positions and hasattr(self.app, "main_paned"):
                    try:
                        self.app.main_paned.sashpos(0, positions["main_sash"])
                    except tk.TclError:
                        pass
                
                if "content_sash" in positions and hasattr(self.app, "main_paned"):
                    for pane in self.app.main_paned.panes():
                        try:
                            widget = self.root.nametowidget(pane)
                            if isinstance(widget, tk.PanedWindow) or isinstance(widget, tk.ttk.PanedWindow):
                                widget.sashpos(0, positions["content_sash"])
                                break
                        except Exception:
                            continue

            # Use after to wait for layout to settle
            self.root.after(100, _apply)
            self.root.after(500, _apply) # Retry a bit later too
        except Exception:
            pass
