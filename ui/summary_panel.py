# -*- coding: utf-8 -*-
"""Condensed prompt summary and quick-import panel."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from utils import create_tooltip, logger
from .widgets import CollapsibleFrame


class SummaryPanel(CollapsibleFrame):
    """Panel for viewing and editing a condensed prompt summary."""

    def __init__(
        self, 
        parent, 
        theme_manager, 
        on_apply_callback: Callable[[], None],
        on_import_callback: Callable[[], None],
        **kwargs
    ):
        """Initialize SummaryPanel.

        Args:
            parent: Parent widget
            theme_manager: ThemeManager instance
            on_apply_callback: Callback when user manually edits and applies changes
            on_import_callback: Callback to open text import dialog
        """
        super().__init__(parent, text="📋 PROMPT SUMMARY", opened=True, show_import=True, **kwargs)
        
        self.theme_manager = theme_manager
        self.on_apply = on_apply_callback
        self.on_import = on_import_callback
        
        self._modified = False
        
        self._build_internal_ui()
        self._setup_theming()

    def _build_internal_ui(self):
        """Build widgets."""
        content = self.get_content_frame()
        content.columnconfigure(0, weight=1)
        
        create_tooltip(self, "Condensed overview. You can edit this text and click 'Apply' to update the whole prompt.")
        self.set_import_command(self.on_import)
        
        self.text = tk.Text(content, wrap="word", height=3)
        self.text.grid(row=0, column=0, sticky="ew", padx=4, pady=6)
        create_tooltip(self.text, "Condensed overview. Click 'Import' to load from text.")
        
        self.text.bind("<FocusIn>", self._on_focus_in)
        self.text.bind("<KeyRelease>", self._on_change)

    def _setup_theming(self):
        """Register with theme manager."""
        self.theme_manager.register(self, self.apply_theme)
        # We don't use register_text_widget here because we want custom behavior on focus
        # but let's register it anyway for initial style
        self.theme_manager.register_text_widget(self.text)

    def _on_focus_in(self, event):
        """Mark as modified and ensure readable colors."""
        self._modified = True
        theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
        bg = theme.get("text_bg", theme.get("bg", "#ffffff"))
        fg = theme.get("text_fg", theme.get("fg", "#000000"))
        self.text.config(background=bg, foreground=fg, insertbackground=fg)

    def _on_change(self, event):
        """Mark as modified."""
        self._modified = True

    def get_text(self) -> str:
        """Get current text."""
        return self.text.get("1.0", "end-1c").strip()

    def set_text(self, text: str):
        """Set text and reset modified flag if needed."""
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self._modified = False

    @property
    def is_modified(self) -> bool:
        """Return True if user has manually edited the summary."""
        return self._modified

    @is_modified.setter
    def is_modified(self, value: bool):
        self._modified = value
