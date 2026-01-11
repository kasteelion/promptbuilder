# -*- coding: utf-8 -*-
"""Reusable Pill Button component."""

import tkinter as tk
from typing import Callable, Optional

class PillButton(tk.Frame):
    """A pill-shaped button with hover effects and theme support."""

    def __init__(
        self,
        parent,
        text: str,
        command: Callable[[], None],
        theme_manager=None,
        **kwargs
    ):
        """Initialize the pill button.

        Args:
            parent: Parent widget
            text: Button text
            command: Click handler
            theme_manager: Optional theme manager for auto-theming
            **kwargs: Additional arguments for the Frame
        """
        super().__init__(parent, padx=1, pady=1, **kwargs)
        
        self.command = command
        self.theme_manager = theme_manager
        self._text = text
        
        # Create label
        self.label = tk.Label(
            self,
            text=text,
            font=("Lexend", 8, "bold"),
            padx=10,
            pady=2,
            cursor="hand2"
        )
        self.label.pack(fill="both", expand=True)
        
        # Bind events
        self.label.bind("<Enter>", self._on_enter)
        self.label.bind("<Leave>", self._on_leave)
        self.label.bind("<Button-1>", lambda e: self.command())
        
        # Initial style setup if theme manager provided
        if self.theme_manager:
             self.theme_manager.register(self, self.apply_theme)
        
    def _on_enter(self, event):
        """Handle mouse enter."""
        if self.theme_manager:
            theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
            hover_bg = theme.get("hover_bg", "#333333")
            self.label.config(bg=hover_bg)
        else:
            # Fallback
            self.label.config(bg="#333333")

    def _on_leave(self, event):
        """Handle mouse leave."""
        # Restore to base background
        bg = getattr(self.label, "_base_bg", "#1e1e1e")
        self.label.config(bg=bg)

    def apply_theme(self, theme: dict):
        """Apply theme colors."""
        accent = theme.get("accent", "#0078d7")
        panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        
        # Frame border/bg is the accent color
        self.config(bg=accent)
        
        # Label is the panel background
        self.label.config(bg=panel_bg, fg=accent)
        self.label._base_bg = panel_bg
