# -*- coding: utf-8 -*-
"""Individual character item widget for the characters tab."""

import tkinter as tk
from tkinter import ttk

from utils.outfit_color_check import outfit_has_color_vars
import re

def outfit_has_signature_vars(text: str) -> bool:
    return bool(re.search(r"\(\(default:.*?\)\s+or\s+\(signature\)\)", text, re.IGNORECASE))

from .searchable_combobox import SearchableCombobox
from .widgets import FlowFrame


class CharacterItem(ttk.Frame):
    """A widget representing a single character in the prompt list with accordion behavior."""

    def __init__(
        self,
        parent,
        index,
        char_data,
        all_characters,
        all_poses,
        color_schemes,
        callbacks,
        theme_manager=None,
        **kwargs
    ):
        """Initialize character item.

        Args:
            parent: Parent widget
            index: 0-based index of character in list
            char_data: Data for this specific character instance (name, outfit, etc.)
            all_characters: Full character definitions dict
            all_poses: Pose presets dict
            color_schemes: Color schemes dict
            callbacks: Dict of callback functions
            theme_manager: Optional ThemeManager instance
        """
        super().__init__(parent, style="Card.TFrame", padding=2)

        self.index = index
        self.char_data = char_data
        self.char_name = char_data["name"]
        self.char_def = all_characters.get(self.char_name, {})
        self.all_poses = all_poses
        self.color_schemes = color_schemes
        self.theme_manager = theme_manager
        self.modifiers = callbacks.get("get_modifiers", lambda: {})()
        self.callbacks = callbacks
        
        # Use existing expanded state or default to True for new items
        self._expanded = char_data.get("_expanded", True)

        self._build_ui()
        
        if self.theme_manager:
            self.theme_manager.register(self, self._update_theme_overrides)

    def _build_ui(self):
        """Build the character item UI components."""
        # Header Row (Refactor 1: Accordion)
        self.header = ttk.Frame(self, style="TFrame", cursor="hand2")
        self.header.pack(fill="x", padx=10, pady=8)
        
        # Drag handle
        self.drag_handle = ttk.Label(self.header, text="⠿", cursor="fleur", font=(None, 12))
        self.drag_handle.pack(side="left", padx=(0, 10))
        
        # Title - Refactor 5: Semantic Typography
        title_text = f"#{self.index + 1} — {self.char_name.upper()}"
        self.title_label = ttk.Label(self.header, text=title_text, style="Bold.TLabel")
        self.title_label.pack(side="left")
        
        # Indicator - Refactor 3
        self.toggle_indicator = ttk.Label(self.header, text="▼" if self._expanded else "▶", style="Muted.TLabel")
        self.toggle_indicator.pack(side="right", padx=5)

        # Controls container (The part that collapses)
        self.controls_frame = ttk.Frame(self, style="TFrame", padding=(15, 5, 15, 15))
        if self._expanded:
            self.controls_frame.pack(fill="x")
            
        # Bind toggle to header, title and handle - Refactor 3
        for widget in [self.header, self.title_label, self.drag_handle, self.toggle_indicator]:
            widget.bind("<Button-1>", lambda e: self.toggle_collapse())
            # Hover effect for clearer affordance
            widget.bind("<Enter>", self._on_header_hover)
            widget.bind("<Leave>", self._on_header_leave)

        # Get initial colors from theme if available
        panel_bg = "#1e1e1e"
        muted_fg = "gray"
        theme = {}
        
        if self.theme_manager and self.theme_manager.current_theme in self.theme_manager.themes:
            theme = self.theme_manager.themes[self.theme_manager.current_theme]
            panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
            muted_fg = theme.get("border", "gray")
        else:
            try:
                style = ttk.Style()
                panel_bg = style.lookup("TFrame", "background")
            except: pass
            
        self._last_pbg = panel_bg

        # --- Content inside controls_frame ---
        
        # Outfit Section
        outfit_row = ttk.Frame(self.controls_frame)
        outfit_row.pack(fill="x", pady=(0, 10))

        ttk.Label(outfit_row, text="👕 Outfit:", style="Bold.TLabel").pack(side="left")
        
        current_outfit = self.char_data.get("outfit", "")
        outfit_text = self.char_def.get("outfits", {}).get(current_outfit, "")
        
        self.outfit_var = tk.StringVar(value=current_outfit)
        
        # Prepare data for two-step selection
        outfits_categorized = self.char_def.get("outfits_categorized", {})
        
        # Determine initial category
        current_cat = ""
        if outfits_categorized:
            for cat, outfits in outfits_categorized.items():
                if current_outfit in outfits:
                    current_cat = cat
                    break
            if not current_cat:
                current_cat = "Personal" if "Personal" in outfits_categorized else sorted(list(outfits_categorized.keys()))[0]

        # Compact outfit selectors
        self.outfit_cat_combo = SearchableCombobox(
            outfit_row,
            theme_manager=self.theme_manager,
            values=sorted(list(outfits_categorized.keys())),
            on_select=self._on_outfit_cat_select,
            placeholder="Category...",
            width=12
        )
        self.outfit_cat_combo.pack(side="left", padx=10)
        self.outfit_cat_combo.set(current_cat)

        initial_outfits = sorted(list(outfits_categorized.get(current_cat, {}).keys())) if current_cat else []
        self.outfit_combo = SearchableCombobox(
            outfit_row,
            theme_manager=self.theme_manager,
            values=initial_outfits,
            textvariable=self.outfit_var,
            on_select=lambda val: self.callbacks["update_outfit"](self.index, val),
            placeholder="Select outfit...",
            width=25
        )
        self.outfit_combo.pack(side="left", fill="x", expand=True)

        # Signature Color Checkbox - Refactor 6: Pill Strategy
        sig_color = self.char_def.get("signature_color")
        if sig_color and outfit_has_signature_vars(str(outfit_text)):
            self.sig_var = tk.BooleanVar(value=self.char_data.get("use_signature_color", False))
            
            def toggle_sig(e):
                new_val = not self.sig_var.get()
                self.sig_var.set(new_val)
                self.char_data["use_signature_color"] = new_val
                self.sig_pill_lbl.config(text=f"✓ USE SIGNATURE COLOR" if new_val else "USE SIGNATURE COLOR")
                self.callbacks["on_change"]()
                
            sig_frame = ttk.Frame(self.controls_frame)
            sig_frame.pack(fill="x", pady=(0, 10))
            
            # Use theme accent/panel colors
            accent = theme.get("accent", "#0078d7")

            self.sig_pill_frame = tk.Frame(sig_frame, bg=accent, padx=1, pady=1)
            self.sig_pill_frame.pack(side="left")
            
            initial_text = "✓ USE SIGNATURE COLOR" if self.sig_var.get() else "USE SIGNATURE COLOR"
            self.sig_pill_lbl = tk.Label(
                self.sig_pill_frame, 
                text=initial_text, 
                bg=panel_bg, 
                fg=accent,
                font=("Lexend", 8, "bold"),
                padx=8,
                pady=2,
                cursor="hand2"
            )
            self.sig_pill_lbl.pack()
            self.sig_pill_lbl._base_bg = panel_bg
            
            def on_s_enter(e):
                try:
                    theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
                    hbg = theme.get("hover_bg", "#333333")
                except: hbg = "#333333"
                self.sig_pill_lbl.config(bg=hbg)
            def on_s_leave(e):
                self.sig_pill_lbl.config(bg=getattr(self.sig_pill_lbl, "_base_bg", "#1e1e1e"))
                
            self.sig_pill_lbl.bind("<Button-1>", toggle_sig)
            self.sig_pill_lbl.bind("<Enter>", on_s_enter)
            self.sig_pill_lbl.bind("<Leave>", on_s_leave)
            
            # Color swatch
            try:
                swatch = tk.Label(sig_frame, bg=sig_color, width=2, height=1, relief="solid", borderwidth=1)
                swatch.pack(side="left", padx=10)
            except Exception: pass

        # Pose Section
        pose_section = ttk.Frame(self.controls_frame)
        pose_section.pack(fill="x", pady=(0, 10))
        
        ttk.Label(pose_section, text="🎭 Pose:", style="Bold.TLabel").pack(side="left")
        
        pcat_var = tk.StringVar(value=self.char_data.get("pose_category", ""))
        preset_var = tk.StringVar(value=self.char_data.get("pose_preset", ""))
        current_pcat = pcat_var.get()
        preset_values = [""] + sorted(list(self.all_poses.get(current_pcat, {}).keys())) if current_pcat else [""]
        
        self.pcat_combo = SearchableCombobox(
            pose_section,
            theme_manager=self.theme_manager,
            values=[""] + sorted(list(self.all_poses.keys())),
            textvariable=pcat_var,
            on_select=self._on_pose_cat_select,
            placeholder="Category...",
            width=15
        )
        self.pcat_combo.pack(side="left", padx=10)

        self.preset_combo = SearchableCombobox(
            pose_section,
            theme_manager=self.theme_manager,
            values=preset_values,
            textvariable=preset_var,
            on_select=lambda val: self.callbacks["update_pose_preset"](self.index, val),
            placeholder="Search preset...",
            width=20
        )
        self.preset_combo.pack(side="left", fill="x", expand=True)

        # Action note text area
        ttk.Label(
            self.controls_frame,
            text="💬 CUSTOM POSE/ACTION (OVERRIDES PRESET):",
            style="Muted.TLabel",
        ).pack(fill="x", pady=(5, 2))
        
        # Refactor 3: Visual Comfort - Blending Inputs
        self.action_text = tk.Text(
            self.controls_frame, 
            wrap="word", 
            height=3,
            relief="flat",
            padx=10,
            pady=10,
            font=("Lexend", 9)
        )
        self.action_text.insert("1.0", self.char_data.get("action_note", ""))
        self.action_text.pack(fill="x", pady=(0, 15))
        self.action_text.bind(
            "<KeyRelease>", lambda e: self.callbacks["update_action_note"](self.index, self.action_text)
        )
        
        if self.theme_manager:
            self.theme_manager.register_text_widget(self.action_text)

        # Color scheme selector if needed
        if outfit_has_color_vars(str(outfit_text)):
            scheme_var = tk.StringVar(value=self.char_data.get("color_scheme", ""))
            
            color_row = ttk.Frame(self.controls_frame)
            color_row.pack(fill="x", pady=(0, 15))
            ttk.Label(color_row, text="🎨 Team Colors:").pack(side="left", padx=(0, 5))
            
            scheme_combo = ttk.Combobox(color_row, textvariable=scheme_var, state="readonly", values=list(self.color_schemes.keys()), width=25)
            scheme_combo.pack(side="left")
            scheme_combo.bind("<<ComboboxSelected>>", lambda e: self.callbacks["update_color_scheme"](self.index, scheme_var.get()))

        # Footer Actions (Refactor 3: Ghost/Link Hierarchy)
        footer = ttk.Frame(self.controls_frame)
        footer.pack(fill="x")

        accent_color = self.char_def.get("signature_color", theme.get("accent", "#0078d7"))
        if not str(accent_color).startswith("#"): accent_color = theme.get("accent", "#0078d7")
        
        # Move Up/Down use Ghost style overrides
        move_frame = ttk.Frame(self.controls_frame)
        move_frame.pack(side="left")
        
        if self.index > 0:
            up_btn = tk.Button(
                move_frame, text="↑ UP", width=6, command=lambda: self.callbacks["move_up"](self.index),
                bg=panel_bg, fg=accent_color, highlightbackground=accent_color, highlightthickness=2,
                relief="flat", font=("Lexend", 8, "bold")
            )
            up_btn.pack(side="left", padx=2)
            up_btn.bind("<Enter>", lambda e, b=up_btn: b.config(bg=self.theme_manager.themes.get(self.theme_manager.current_theme, {}).get("hover_bg", "#333333")))
            up_btn.bind("<Leave>", lambda e, b=up_btn: b.config(bg=self._last_pbg))
        
        num_characters = self.callbacks.get("get_num_characters", lambda: 0)()
        if self.index < num_characters - 1:
            down_btn = tk.Button(
                move_frame, text="↓ DOWN", width=6, command=lambda: self.callbacks["move_down"](self.index),
                bg=panel_bg, fg=accent_color, highlightbackground=accent_color, highlightthickness=2,
                relief="flat", font=("Lexend", 8, "bold")
            )
            down_btn.pack(side="left", padx=2)
            down_btn.bind("<Enter>", lambda e, b=down_btn: b.config(bg=self.theme_manager.themes.get(self.theme_manager.current_theme, {}).get("hover_bg", "#333333")))
            down_btn.bind("<Leave>", lambda e, b=down_btn: b.config(bg=self._last_pbg))

        # Remove uses Link style override - Refactor 5: Lexend
        self.remove_btn = tk.Button(
            footer, text="✕ REMOVE CHARACTER", command=lambda: self.callbacks["remove_character"](self.index),
            bg=panel_bg, fg=muted_fg, borderwidth=0, relief="flat", font=("Lexend", 8, "bold"),
            activeforeground="red"
        )
        self.remove_btn.pack(side="right")

    def _on_header_hover(self, event):
        """Highlight header on hover."""
        try:
            self.title_label.configure(style="Accent.TLabel")
        except: pass

    def _on_header_leave(self, event):
        """Restore header on leave."""
        try:
            self.title_label.configure(style="Bold.TLabel")
        except: pass

    def _on_outfit_cat_select(self, val):
        outfits = sorted(list(self.char_def.get("outfits_categorized", {}).get(val, {}).keys()))
        self.outfit_combo.set_values(outfits)
        self.outfit_combo.set("")

    def _on_pose_cat_select(self, val):
        presets = [""] + sorted(list(self.all_poses.get(val, {}).keys()))
        self.preset_combo.set_values(presets)
        self.preset_combo.set("")
        self.callbacks["update_pose_category"](self.index, val, self.preset_combo)

    def toggle_collapse(self):
        """Toggle the visibility of controls. (Refactor 3: Accordion)"""
        if self._expanded:
            self.controls_frame.pack_forget()
            self.toggle_indicator.config(text="▶")
            self._expanded = False
        else:
            # Auto-collapse others if requested by parent/tab
            if self.callbacks.get("auto_collapse"):
                self.callbacks["auto_collapse"](self.index)
            
            self.controls_frame.pack(fill="x")
            self.toggle_indicator.config(text="▼")
            self._expanded = True
            
        self.char_data["_expanded"] = self._expanded
        if "update_scroll" in self.callbacks:
            self.callbacks["update_scroll"]()

    def set_expanded(self, expanded):
        """Programmatically set expanded state."""
        if self._expanded != expanded:
            self.toggle_collapse()

    def set_selected(self, selected):
        """Update visual state to show selection."""
        if selected:
            self.config(style="Selected.Card.TFrame")
        else:
            self.config(style="Card.TFrame")

    def _update_theme_overrides(self, theme):
        """Update manual button overrides when theme changes. (Refactor 3)"""
        accent_color = self.char_def.get("signature_color", theme.get("accent", "#0078d7"))
        if not str(accent_color).startswith("#"): accent_color = theme.get("accent", "#0078d7")
        panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        self._last_pbg = panel_bg # Store for hover restoration

        # Update sig pill - Refactor 6
        if hasattr(self, "sig_pill_frame"):
            accent = theme.get("accent", "#0078d7")
            self.sig_pill_frame.config(bg=accent)
            self.sig_pill_lbl.config(bg=panel_bg, fg=accent)
            self.sig_pill_lbl._base_bg = panel_bg
            self.sig_pill_lbl.config(text=f"✓ USE SIGNATURE COLOR" if self.sig_var.get() else "USE SIGNATURE COLOR")

        # Update nested comboboxes - Refactor 3
        for cb in ["outfit_cat_combo", "outfit_combo", "pcat_combo", "preset_combo"]:
            if hasattr(self, cb):
                getattr(self, cb).apply_theme(theme)

        # Update Ghost buttons
        for btn in self.controls_frame.winfo_children():
            if isinstance(btn, tk.Button):
                if "↑" in btn.cget("text") or "↓" in btn.cget("text"):
                    btn.config(bg=panel_bg, fg=accent_color, highlightbackground=accent_color)
                elif "✕" in btn.cget("text"):
                    btn.config(bg=panel_bg) # Link button stays muted gray/red