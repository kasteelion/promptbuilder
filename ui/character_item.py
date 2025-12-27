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
        """
        super().__init__(parent, style="Card.TFrame", padding=2)

        self.index = index
        self.char_data = char_data
        self.char_name = char_data["name"]
        self.char_def = all_characters.get(self.char_name, {})
        self.all_poses = all_poses
        self.color_schemes = color_schemes
        self.modifiers = callbacks.get("get_modifiers", lambda: {})()
        self.callbacks = callbacks
        
        # Use existing expanded state or default to True for new items
        self._expanded = char_data.get("_expanded", True)

        self._build_ui()

    def _build_ui(self):
        """Build the character item UI components."""
        # Header Row (Refactor 1: Accordion)
        self.header = ttk.Frame(self, style="TFrame", cursor="hand2")
        self.header.pack(fill="x", padx=10, pady=8)
        
        # Drag handle
        self.drag_handle = ttk.Label(self.header, text="⠿", cursor="fleur", font=(None, 12))
        self.drag_handle.pack(side="left", padx=(0, 10))
        
        # Title
        title_text = f"#{self.index + 1} — {self.char_name}"
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
        self.header.bind("<Button-1>", lambda e: self.toggle_collapse())
        self.title_label.bind("<Button-1>", lambda e: self.toggle_collapse())
        self.drag_handle.bind("<Button-1>", lambda e: self.toggle_collapse())

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
            values=initial_outfits,
            textvariable=self.outfit_var,
            on_select=lambda val: self.callbacks["update_outfit"](self.index, val),
            placeholder="Select outfit...",
            width=25
        )
        self.outfit_combo.pack(side="left", fill="x", expand=True)

        # Signature Color Checkbox
        sig_color = self.char_def.get("signature_color")
        if sig_color and outfit_has_signature_vars(str(outfit_text)):
            sig_var = tk.BooleanVar(value=self.char_data.get("use_signature_color", False))
            
            def on_sig_toggle():
                self.char_data["use_signature_color"] = sig_var.get()
                self.callbacks["on_change"]()
                
            sig_frame = ttk.Frame(self.controls_frame)
            sig_frame.pack(fill="x", pady=(0, 10))
            
            ttk.Checkbutton(
                sig_frame, 
                text="Use Signature Color", 
                variable=sig_var, 
                command=on_sig_toggle
            ).pack(side="left")
            
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
            values=[""] + sorted(list(self.all_poses.keys())),
            textvariable=pcat_var,
            on_select=self._on_pose_cat_select,
            placeholder="Category...",
            width=15
        )
        self.pcat_combo.pack(side="left", padx=10)

        self.preset_combo = SearchableCombobox(
            pose_section,
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
            text="💬 Custom Pose/Action (Optional - Overrides Preset):",
            style="Muted.TLabel",
        ).pack(fill="x", pady=(5, 2))
        
        self.action_text = tk.Text(self.controls_frame, wrap="word", height=3)
        self.action_text.insert("1.0", self.char_data.get("action_note", ""))
        self.action_text.pack(fill="x", pady=(0, 15))
        self.action_text.bind(
            "<KeyRelease>", lambda e: self.callbacks["update_action_note"](self.index, self.action_text)
        )

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

        accent_color = self.char_def.get("signature_color", "#0078d7")
        if not accent_color.startswith("#"): accent_color = "#0078d7"
        
        # Get theme colors safely
        try:
            style = ttk.Style()
            panel_bg = style.lookup("TFrame", "background")
        except:
            panel_bg = "#ffffff"

        # Move Up/Down use Ghost style overrides
        move_frame = ttk.Frame(footer)
        move_frame.pack(side="left")
        
        if self.index > 0:
            tk.Button(
                move_frame, text="↑ Up", width=6, command=lambda: self.callbacks["move_up"](self.index),
                bg=panel_bg, fg=accent_color, highlightbackground=accent_color, highlightthickness=1,
                relief="flat", font=("Segoe UI", 8)
            ).pack(side="left", padx=2)
        
        num_characters = self.callbacks.get("get_num_characters", lambda: 0)()
        if self.index < num_characters - 1:
            tk.Button(
                move_frame, text="↓ Down", width=6, command=lambda: self.callbacks["move_down"](self.index),
                bg=panel_bg, fg=accent_color, highlightbackground=accent_color, highlightthickness=1,
                relief="flat", font=("Segoe UI", 8)
            ).pack(side="left", padx=2)

        # Remove uses Link style override
        tk.Button(
            footer, text="✕ Remove Character", command=lambda: self.callbacks["remove_character"](self.index),
            bg=panel_bg, fg="gray", borderwidth=0, relief="flat", font=("Segoe UI", 8),
            activeforeground="red"
        ).pack(side="right")

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
