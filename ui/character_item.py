# -*- coding: utf-8 -*-
"""Individual character item widget for the characters tab."""

import tkinter as tk
from tkinter import ttk

from utils.outfit_color_check import outfit_has_color_vars
from .searchable_combobox import SearchableCombobox
from .widgets import FlowFrame


class CharacterItem(ttk.LabelFrame):
    """A widget representing a single character in the prompt list."""

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
            callbacks: Dict of callback functions (update_outfit, update_pose, etc.)
            **kwargs: Additional args for LabelFrame
        """
        char_name = char_data["name"]
        char_title = f"#{index + 1} — {char_name}"
        super().__init__(parent, text=char_title, padding=6, style="TLabelframe", **kwargs)

        self.index = index
        self.char_data = char_data
        self.char_def = all_characters.get(char_name, {})
        self.all_poses = all_poses
        self.color_schemes = color_schemes
        self.modifiers = callbacks.get("get_modifiers", lambda: {})()
        self.callbacks = callbacks

        self._build_ui()

    def _build_ui(self):
        """Build the character item UI components."""
        # Main header frame for title and drag handle
        header_row = ttk.Frame(self)
        header_row.pack(fill="x", pady=(0, 4))
        
        # Drag handle (visual indicator)
        self.drag_handle = ttk.Label(header_row, text="⠿", cursor="fleur", font=(None, 12))
        self.drag_handle.pack(side="left", padx=(0, 5))
        
        # Re-parent the outfit header content
        outfit_header = ttk.Frame(self)
        outfit_header.pack(fill="x", pady=(0, 2))

        outfit_label = ttk.Label(outfit_header, text="👕 Outfit:", style="Bold.TLabel")
        outfit_label.pack(side="left")

        # Show current outfit
        current_outfit = self.char_data.get("outfit", "")
        outfit_text = self.char_def.get("outfits", {}).get(current_outfit, "")
        if current_outfit:
            current_label = ttk.Label(
                outfit_header,
                text=f" {current_outfit}",
                style="Accent.TLabel",
            )
            current_label.pack(side="left")

        # Collapsible outfit frame
        outfit_container = ttk.Frame(self)
        outfit_expanded = tk.BooleanVar(value=False)

        def toggle_outfit():
            if outfit_expanded.get():
                outfit_container.pack_forget()
                outfit_expanded.set(False)
            else:
                outfit_container.pack(fill="both", expand=False, pady=(0, 6), after=outfit_header)
                outfit_expanded.set(True)
            if "update_scroll" in self.callbacks:
                self.callbacks["update_scroll"]()

        toggle_btn = ttk.Button(outfit_header, text="▼", width=3, command=toggle_outfit)
        toggle_btn.pack(side="right")

        # Outfit options inside collapsible frame
        outfit_keys = sorted(list(self.char_def.get("outfits", {}).keys()))
        
        if len(outfit_keys) > 12:
            # Use searchable combobox for many outfits
            outfit_search_var = tk.StringVar(value=current_outfit)
            outfit_combo = SearchableCombobox(
                outfit_container,
                values=outfit_keys,
                textvariable=outfit_search_var,
                on_select=lambda val: (
                    self.callbacks["update_outfit"](self.index, val),
                    toggle_outfit()
                ),
                placeholder="Search outfit..."
            )
            outfit_combo.pack(fill="x", padx=4, pady=4)
        else:
            # Use buttons for fewer outfits
            outfits_frame = FlowFrame(outfit_container, padding_x=6, padding_y=4)
            outfits_frame.pack(fill="both", expand=True, pady=(2, 2))

            for o in outfit_keys:
                btn_style = "Accent.TButton" if o == current_outfit else "TButton"
                outfits_frame.add_button(
                    text=o,
                    style=btn_style,
                    command=(
                        lambda name=o: (
                            self.callbacks["update_outfit"](self.index, name),
                            toggle_outfit(),
                        )
                    ),
                )

        # Outfit creator button
        ttk.Button(
            outfit_container,
            text="✨ New Outfit for Character",
            command=lambda: self.callbacks["create_outfit"](self.char_data["name"]),
        ).pack(fill="x", pady=(2, 0))

        # Pose preset selector
        ttk.Label(self, text="🎭 Pose (Optional):", font=("Consolas", 9, "bold")).pack(
            fill="x", pady=(6, 2)
        )
        pose_row = ttk.Frame(self)
        pose_row.pack(fill="x", pady=(0, 4))
        pose_row.columnconfigure(3, weight=1)

        ttk.Label(pose_row, text="Category:").grid(row=0, column=0, sticky="w", padx=(0, 4))
        pcat_var = tk.StringVar(value=self.char_data.get("pose_category", ""))
        
        # We'll need a reference to preset_combo to update it
        preset_var = tk.StringVar(value=self.char_data.get("pose_preset", ""))
        current_cat = pcat_var.get()
        preset_values = [""] + sorted(list(self.all_poses.get(current_cat, {}).keys())) if current_cat else [""]
        
        preset_combo = SearchableCombobox(
            pose_row,
            values=preset_values,
            textvariable=preset_var,
            on_select=lambda val: self.callbacks["update_pose_preset"](self.index, val),
            placeholder="Search preset...",
            width=20
        )
        preset_combo.grid(row=0, column=3, sticky="ew")

        pcat_combo = SearchableCombobox(
            pose_row,
            values=[""] + sorted(list(self.all_poses.keys())),
            textvariable=pcat_var,
            on_select=lambda val: self.callbacks["update_pose_category"](self.index, val, preset_combo),
            placeholder="Search category...",
            width=15
        )
        pcat_combo.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(pose_row, text="Preset:").grid(row=0, column=2, sticky="w", padx=(0, 4))

        # Add create pose button
        ttk.Button(pose_row, text="✨", width=3, command=self.callbacks["create_pose"]).grid(
            row=0, column=4, padx=(5, 0)
        )

        # Action note text area
        ttk.Label(
            self,
            text="💬 Custom Pose/Action (Optional - Overrides Preset):",
            font=("Consolas", 9, "bold"),
        ).pack(fill="x", pady=(6, 0))
        action_text = tk.Text(self, wrap="word", height=5)
        action_text.insert("1.0", self.char_data.get("action_note", ""))
        action_text.pack(fill="x", pady=(0, 6))
        action_text.config(padx=5, pady=5)
        action_text.bind(
            "<KeyRelease>", lambda e: self.callbacks["update_action_note"](self.index, action_text)
        )

        # Insert color scheme selector if outfit uses color variables
        if outfit_has_color_vars(str(outfit_text)):
            scheme_var = tk.StringVar(value=self.char_data.get("color_scheme", ""))
            scheme_names = list(self.color_schemes.keys())
            ttk.Label(self, text="Team Colors:").pack(anchor="w", padx=4)
            scheme_combo = ttk.Combobox(self, textvariable=scheme_var, state="readonly", values=scheme_names)
            scheme_combo.pack(fill="x", padx=4, pady=(0, 6))
            def on_scheme_selected(event):
                self.callbacks["update_color_scheme"](self.index, scheme_var.get())
            scheme_combo.bind("<<ComboboxSelected>>", on_scheme_selected)

        # Insert outfit modifier selector if outfit uses {modifier} variable
        if "{modifier}" in str(outfit_text):
            current_traits = self.char_data.get("outfit_traits", [])
            # Support legacy single-string modifier
            if not current_traits and self.char_data.get("outfit_modifier"):
                current_traits = [self.char_data.get("outfit_modifier")]
                self.char_data["outfit_traits"] = current_traits
            
            ttk.Label(self, text="👕 Outfit Options / Traits:", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=4, pady=(4, 2))
            
            traits_frame = FlowFrame(self, padding_x=4, padding_y=2)
            traits_frame.pack(fill="x", padx=4, pady=(0, 6))
            
            # Group traits by category (first word before hyphen)
            sorted_modifier_keys = sorted(list(self.modifiers.keys()))
            
            for mod_name in sorted_modifier_keys:
                # Use a closure to capture mod_name
                def make_toggle(name=mod_name):
                    def toggle():
                        traits = self.char_data.get("outfit_traits", [])
                        if name in traits:
                            traits.remove(name)
                        else:
                            traits.append(name)
                        self.char_data["outfit_traits"] = traits
                        self.callbacks["on_change"]()
                    return toggle

                var = tk.BooleanVar(value=mod_name in current_traits)
                chk = ttk.Checkbutton(
                    traits_frame, 
                    text=mod_name, 
                    variable=var, 
                    command=make_toggle(mod_name),
                    style="Action.TCheckbutton"
                )
                traits_frame._children.append(chk)
                # Position chk like a button in FlowFrame
                traits_frame._schedule_reflow()

        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=6)

        # Button row
        btnrow = ttk.Frame(self, style="TFrame")
        btnrow.pack(fill="x")

        mv = ttk.Frame(btnrow, style="TFrame")
        mv.pack(side="left", fill="x", expand=True)
        
        num_characters = self.callbacks.get("get_num_characters", lambda: 0)()
        
        if self.index > 0:
            ttk.Button(
                mv, text="↑ Move Up", width=10, command=lambda: self.callbacks["move_up"](self.index)
            ).pack(side="left", padx=(0, 4))
        if self.index < num_characters - 1:
            ttk.Button(
                mv, text="↓ Move Down", width=10, command=lambda: self.callbacks["move_down"](self.index)
            ).pack(side="left")

        ttk.Button(
            btnrow, text="✕ Remove", command=lambda: self.callbacks["remove_character"](self.index)
        ).pack(side="right")
