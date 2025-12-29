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
        
        # Safe Geometry Check: 
        # If the saved geometry is suspiciously small, ignore it.
        if saved_geometry:
            try:
                # Format: 1200x800+100+100
                size_part = saved_geometry.split('+')[0]
                w, h = map(int, size_part.split('x'))
                if w < 400 or h < 400:
                    saved_geometry = None # Discard collapsed geometry
            except Exception:
                saved_geometry = None

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
            # Helper to get sash position regardless of tk vs ttk
            def get_sash_pos(widget):
                if hasattr(widget, "sash_coord"): # tk.PanedWindow
                    return widget.sash_coord(0)[0] # Horizontal x-coord
                elif hasattr(widget, "sashpos"): # ttk.PanedWindow
                    return widget.sashpos(0)
                return None

            # Main paned (Gallery | Content)
            if hasattr(self.app, "main_paned"):
                pos = get_sash_pos(self.app.main_paned)
                if pos is not None:
                    positions["main_sash"] = pos
            
            # Content paned (Notebook | Right Scroll)
            if hasattr(self.app, "main_paned"):
                for pane in self.app.main_paned.panes():
                    try:
                        widget = self.root.nametowidget(pane)
                        if isinstance(widget, (tk.PanedWindow, tk.ttk.PanedWindow)):
                            pos = get_sash_pos(widget)
                            if pos is not None:
                                positions["content_sash"] = pos
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

            def set_sash_pos(widget, pos):
                if hasattr(widget, "sash_place"): # tk.PanedWindow
                    widget.sash_place(0, pos, 0)
                elif hasattr(widget, "sashpos"): # ttk.PanedWindow
                    widget.sashpos(0, pos)

            def _apply():
                # Apply with a slight delay to ensure window is mapped
                if "main_sash" in positions and hasattr(self.app, "main_paned"):
                    try:
                        set_sash_pos(self.app.main_paned, positions["main_sash"])
                    except tk.TclError:
                        pass
                
                if "content_sash" in positions and hasattr(self.app, "main_paned"):
                    for pane in self.app.main_paned.panes():
                        try:
                            widget = self.root.nametowidget(pane)
                            if isinstance(widget, (tk.PanedWindow, tk.ttk.PanedWindow)):
                                set_sash_pos(widget, positions["content_sash"])
                                break
                        except Exception:
                            continue

            # Use after to wait for layout to settle
            self.root.after(100, _apply)
            self.root.after(500, _apply) # Retry a bit later too
        except Exception:
            pass
