# -*- coding: utf-8 -*-
"""Toast notification manager for transient, non-modal messages.

Provides a simple, theme-aware API: `notify(message, level='info', duration=3000)`.

To integrate: instantiate once with the application root and ThemeManager (optional),
then pass `toast.notify` as a callback to UI components.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional


class ToastManager:
    def __init__(self, root: tk.Tk, theme_manager=None, margin=(12, 60), gap=8, max_visible=5):
        self.root = root
        self.theme_manager = theme_manager
        self.margin = margin
        self.gap = gap
        self.max_visible = max_visible
        self.active: List[tk.Toplevel] = []
        # Theme colors (fallbacks)
        theme = {}
        if self.theme_manager:
             theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
        
        self.bg = theme.get("panel_bg", "#333333")
        self.fg = "#ffffff"
        self.accent = "#2ea44f"

    def apply_theme(self, theme: Optional[dict]):
        """Apply theme colors to toast styling."""
        if not theme:
            return
        # Theme keys are optional; fall back to defaults
        self.bg = theme.get("toast_bg", theme.get("preview_bg", self.bg))
        self.fg = theme.get("toast_fg", theme.get("preview_fg", self.fg))
        self.accent = theme.get("accent", self.accent)

    def notify(self, message: str, level: str = "info", duration: int = 3000):
        """Show a transient toast message.

        Args:
            message: Text to show
            level: One of 'info', 'success', 'warning', 'error'
            duration: Milliseconds before auto-dismiss
        """
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        try:
            win.attributes("-topmost", True)
        except Exception:
            from utils import logger

            logger.exception("Auto-captured exception")
            pass

        # Frame and label
        frm = ttk.Frame(win, padding=(10, 6), style="Toast.TFrame")
        frm.pack(fill="both", expand=True)

        # Simple color mapping per level
        bg = self.bg
        fg = self.fg
        if level == "success":
            bg = self.accent
            fg = "#ffffff"
        elif level == "error":
            bg = "#b00020"
            fg = "#ffffff"
        elif level == "warning":
            bg = "#e07b00"
            fg = "#000000"

        # Use a label with wrap
        lbl = tk.Label(frm, text=message, justify="left", wraplength=380, bg=bg, fg=fg)
        lbl.pack()

        # Store a reference and position
        self.active.insert(0, win)
        self._reposition()

        # Auto-dismiss
        self.root.after(duration, lambda: self._close(win))

        # Dismiss on click
        lbl.bind("<Button-1>", lambda e: self._close(win))

    def _reposition(self):
        # Position toasts bottom-right relative to root window
        try:
            x0 = self.root.winfo_rootx() + self.root.winfo_width() - self.margin[0]
            y0 = self.root.winfo_rooty() + self.root.winfo_height() - self.margin[1]
            for i, win in enumerate(self.active[: self.max_visible]):
                win.update_idletasks()
                w = win.winfo_width() or 200
                h = win.winfo_height() or 40
                win.geometry(f"{w}x{h}+{x0-w}+{y0 - (i*(h + self.gap))}")
        except Exception:
            from utils import logger

            logger.exception("Auto-captured exception")
            # Best-effort positioning; ignore if root not mapped
            pass

    def _close(self, win: tk.Toplevel):
        if win in self.active:
            try:
                self.active.remove(win)
            except ValueError:
                pass
        try:
            win.destroy()
        except Exception:
            from utils import logger

            logger.exception("Auto-captured exception")
            pass
        self._reposition()
