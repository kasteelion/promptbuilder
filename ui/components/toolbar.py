import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional
from utils import create_tooltip

class ToolbarComponent:
    """Toolbar component for the main application window."""
    
    def __init__(self, parent: tk.Widget, callbacks: Dict[str, Callable], theme_manager=None):
        self.parent = parent
        self.callbacks = callbacks
        self.theme_manager = theme_manager
        self.buttons = []
        self._build()

    def _build(self):
        """Build the toolbar widget."""
        self.frame = ttk.Frame(self.parent, style="TFrame")
        self.frame.pack(side="top", fill="x", padx=4, pady=4)
        
        # File actions
        self._add_btn(self.frame, "💾", self.callbacks.get("save_preset"), "Save Preset", width=3)
        self._add_btn(self.frame, "📂", self.callbacks.get("load_preset"), "Load Preset", width=3)
        
        ttk.Separator(self.frame, orient="vertical").pack(side="left", fill="y", padx=4, pady=2)
        
        # Edit actions
        self._add_btn(self.frame, "↩️", self.callbacks.get("undo"), "Undo (Ctrl+Z)", width=3)
        self._add_btn(self.frame, "↪️", self.callbacks.get("redo"), "Redo (Ctrl+Y)", width=3)

        ttk.Separator(self.frame, orient="vertical").pack(side="left", fill="y", padx=4, pady=2)
        
        # Tools
        self._add_btn(self.frame, "🎲 Randomize", self.callbacks.get("randomize"), "Randomize Everything (Alt+R)")
        self._add_btn(self.frame, "👥 Gallery", self.callbacks.get("toggle_gallery"), "Toggle Character Gallery (Ctrl+G)")
        
        # Spacer
        ttk.Frame(self.frame).pack(side="left", fill="x", expand=True)

    def _add_btn(self, parent, text, command, tooltip=None, width=None):
        """Helper to add styled buttons."""
        if not command:
            return None
            
        # Try to get background safely
        try: 
            bg = parent.cget("background")
        except Exception: 
            try: 
                bg = ttk.Style().lookup("TFrame", "background")
            except Exception: 
                bg = "#121212"
        
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, relief="flat", highlightthickness=2, padx=10,
            font=("Lexend", 9)
        )
        btn._base_bg = bg # Store for hover restoration
        
        def on_btn_enter(e, b=btn):
            try:
                if self.theme_manager:
                    theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
                    hbg = theme.get("hover_bg", "#333333")
                else:
                    hbg = "#333333"
            except Exception: 
                hbg = "#333333"
            b.config(bg=hbg)
            
        def on_btn_leave(e, b=btn):
            b.config(bg=getattr(b, "_base_bg", "#121212"))
        
        btn.bind("<Enter>", on_btn_enter)
        btn.bind("<Leave>", on_btn_leave)
        
        if width:
            btn.config(width=width)
        btn.pack(side="left", padx=2)
        if tooltip:
            create_tooltip(btn, tooltip)
        
        self.buttons.append(btn)
        return btn

    def apply_theme(self, theme):
        """Update button styles based on new theme."""
        panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        accent = theme.get("accent", "#0078d7")
        
        for btn in self.buttons:
            btn.config(bg=panel_bg, fg=accent, highlightbackground=accent)
            btn._base_bg = panel_bg
