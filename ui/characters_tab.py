"""Characters and poses tab UI."""

import tkinter as tk
from tkinter import ttk, messagebox
from .widgets import FlowFrame


class CharactersTab:
    """Tab for managing characters, outfits, and poses."""
    
    def __init__(self, parent, data_loader, on_change_callback):
        """Initialize characters tab.
        
        Args:
            parent: Parent notebook widget
            data_loader: DataLoader instance
            on_change_callback: Function to call when data changes
        """
        self.parent = parent
        self.data_loader = data_loader
        self.on_change = on_change_callback
        
        self.characters = {}
        self.base_prompts = {}
        self.poses = {}
        self.selected_characters = []
        
        self.tab = ttk.Frame(parent, style="TFrame")
        parent.add(self.tab, text="Characters/Poses")
        
        self._build_ui()
    
    def load_data(self, characters, base_prompts, poses):
        """Load character and prompt data.
        
        Args:
            characters: Character definitions dict
            base_prompts: Base prompts dict
            poses: Pose presets dict
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
        
        # Update UI
        self.base_combo['values'] = sorted(list(self.base_prompts.keys()))
        if self.base_prompts:
            self.base_combo.current(0)
        
        self.char_combo['values'] = sorted(list(self.characters.keys()))
        
        # Update bulk outfit combo with all available outfits across characters
        all_outfits = set()
        for char_data in self.characters.values():
            all_outfits.update(char_data.get("outfits", {}).keys())
        self.bulk_outfit_combo['values'] = sorted(list(all_outfits))
        
        self._refresh_list()
    
    def _build_ui(self):
        """Build the characters tab UI."""
        self.tab.columnconfigure(0, weight=1)
        self.tab.rowconfigure(3, weight=1)

        # Base prompt selector
        bp = ttk.LabelFrame(self.tab, text="📋 Base Prompt (Style)", style="TLabelframe")
        bp.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ttk.Label(bp, text="Choose a base art style", foreground="gray", font=("Consolas", 9)).pack(fill="x", padx=4, pady=(2, 0))
        
        self.base_prompt_var = tk.StringVar()
        self.base_combo = ttk.Combobox(bp, state="readonly", textvariable=self.base_prompt_var)
        self.base_combo.pack(fill="x", padx=4, pady=(0, 4))
        self.base_combo.bind("<<ComboboxSelected>>", lambda e: self.on_change())

        # Bulk outfit editor section
        bulk = ttk.LabelFrame(self.tab, text="⚡ Bulk Outfit Editor (Speed Tool)", style="TLabelframe")
        bulk.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        bulk.columnconfigure(1, weight=1)
        ttk.Label(bulk, text="Apply same outfit to multiple characters at once", foreground="gray", font=("Consolas", 9)).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 4))
        
        ttk.Label(bulk, text="Shared Outfit:").grid(row=1, column=0, sticky="w", padx=(4, 2))
        self.bulk_outfit_var = tk.StringVar()
        self.bulk_outfit_combo = ttk.Combobox(bulk, textvariable=self.bulk_outfit_var, state="readonly")
        self.bulk_outfit_combo.grid(row=0, column=1, sticky="ew", padx=2)
        self.bulk_outfit_combo['values'] = []
        self.bulk_outfit_combo.bind("<Return>", lambda e: self._apply_bulk_outfit())
        
        ttk.Label(bulk, text="Apply to:").grid(row=1, column=0, sticky="w", padx=(4, 2), pady=(4, 0))
        self.bulk_chars_var = tk.StringVar()
        self.bulk_chars_combo = ttk.Combobox(bulk, textvariable=self.bulk_chars_var, state="readonly")
        self.bulk_chars_combo.grid(row=1, column=1, sticky="ew", padx=2, pady=(4, 0))
        self.bulk_chars_combo.bind("<Return>", lambda e: self._apply_bulk_outfit())
        
        ttk.Button(bulk, text="Apply Outfit", 
                  command=self._apply_bulk_outfit).grid(row=2, column=0, columnspan=2, 
                                                         sticky="ew", padx=4, pady=4)

        # Add character section
        add = ttk.LabelFrame(self.tab, text="👥 Add Character", style="TLabelframe")
        add.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        ttk.Label(add, text="Select a character and press Add or Enter", foreground="gray", font=("Consolas", 9)).pack(fill="x", padx=4, pady=(2, 4))
        
        self.char_var = tk.StringVar()
        self.char_combo = ttk.Combobox(add, state="readonly", textvariable=self.char_var)
        self.char_combo.pack(fill="x", pady=(0, 4), padx=4)
        self.char_combo.bind("<Return>", lambda e: self._add_character())
        ttk.Button(add, text="+ Add to Group", command=self._add_character).pack(fill="x", padx=4, pady=(0, 4))

        # Selected characters scrollable area
        chars_frame = ttk.Frame(self.tab, style="TFrame")
        chars_frame.grid(row=3, column=0, sticky="nsew", padx=4, pady=4)
        chars_frame.columnconfigure(0, weight=1)
        chars_frame.rowconfigure(0, weight=1)
        
        self.chars_canvas = tk.Canvas(chars_frame, highlightthickness=0)
        vsb = ttk.Scrollbar(chars_frame, orient="vertical", 
                          command=self.chars_canvas.yview, 
                          style="Vertical.TScrollbar")
        self.chars_container = ttk.Frame(self.chars_canvas, style="TFrame")
        
        self.chars_container.bind(
            "<Configure>", 
            lambda e: self.chars_canvas.configure(scrollregion=self.chars_canvas.bbox("all"))
        )
        # Create a window holding the container and keep its width in sync
        # with the canvas so child frames (like the outfit FlowFrame) are
        # constrained and will wrap correctly instead of being clipped.
        self._chars_window = self.chars_canvas.create_window((0, 0), window=self.chars_container, anchor="nw")
        # Ensure the canvas reports scrollregion when container changes
        self.chars_canvas.configure(yscrollcommand=vsb.set)

        # When the canvas is resized, set the inner window's width to match
        # the canvas width so packed/fill='x' children expand to available space.
        # Use after_idle to defer expensive layout updates and avoid lag during drag.
        self._canvas_config_after_id = None
        
        def _on_canvas_config(e):
            try:
                if self._canvas_config_after_id:
                    self.chars_canvas.after_cancel(self._canvas_config_after_id)
                # Defer the config update to avoid blocking drag events
                self._canvas_config_after_id = self.chars_canvas.after_idle(
                    lambda: self.chars_canvas.itemconfig(self._chars_window, width=e.width)
                )
            except Exception:
                pass

        self.chars_canvas.bind('<Configure>', _on_canvas_config)
        
        self.chars_canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        
        self.chars_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.chars_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _apply_bulk_outfit(self):
        """Apply selected outfit to chosen character(s)."""
        outfit_name = self.bulk_outfit_var.get()
        target = self.bulk_chars_var.get()
        
        if not outfit_name:
            messagebox.showwarning("Error", "Please select an outfit")
            return
        
        if not target:
            messagebox.showwarning("Error", "Please select target character(s)")
            return
        
        # Apply to single character
        if target in [c["name"] for c in self.selected_characters]:
            for char in self.selected_characters:
                if char["name"] == target:
                    char["outfit"] = outfit_name
            self._refresh_list()
            self.on_change()
            self.bulk_outfit_var.set("")  # Clear for next use
            return
        
        # Apply to all characters with this outfit available
        if target == "All (with outfit)":
            count = 0
            for char in self.selected_characters:
                char_def = self.characters.get(char["name"], {})
                outfits = char_def.get("outfits", {})
                if outfit_name in outfits:
                    char["outfit"] = outfit_name
                    count += 1
            
            if count == 0:
                messagebox.showinfo("Info", f"No selected characters have the '{outfit_name}' outfit")
            else:
                self._refresh_list()
                self.on_change()
                self.bulk_outfit_var.set("")  # Clear for next use
                messagebox.showinfo("Success", f"Applied '{outfit_name}' to {count} character(s)")
            return
    
    def _add_character(self):
        """Add selected character to the list."""
        name = self.char_var.get()
        if not name:
            return
        if any(c['name'] == name for c in self.selected_characters):
            messagebox.showinfo("Info", f"{name} is already added")
            return
        
        # Auto-assign first available outfit as default
        outfit = ""
        char_def = self.characters.get(name, {})
        outfits = char_def.get("outfits", {})
        if "Base" in outfits:
            outfit = "Base"
        elif outfits:
            outfit = sorted(list(outfits.keys()))[0]
        
        self.selected_characters.append({
            'name': name,
            'outfit': outfit,
            'pose_category': '',
            'pose_preset': '',
            'action_note': ''
        })
        self.char_var.set("")
        self._refresh_list()
        # Auto-scroll to the newly added character
        self.chars_canvas.yview_moveto(1.0)
    
    def _remove_character(self, idx):
        """Remove character at index."""
        self.selected_characters.pop(idx)
        self._refresh_list()
        self.on_change()
    
    def _move_up(self, idx):
        """Move character up in list."""
        if idx > 0:
            self.selected_characters[idx - 1], self.selected_characters[idx] = (
                self.selected_characters[idx],
                self.selected_characters[idx - 1],
            )
            self._refresh_list()
            self.on_change()
    
    def _move_down(self, idx):
        """Move character down in list."""
        if idx < len(self.selected_characters) - 1:
            self.selected_characters[idx + 1], self.selected_characters[idx] = (
                self.selected_characters[idx],
                self.selected_characters[idx + 1],
            )
            self._refresh_list()
            self.on_change()
    
    def _update_outfit(self, idx, outfit_name):
        """Update character outfit."""
        self.selected_characters[idx]["outfit"] = outfit_name
        # Refresh the list so outfit buttons update their visual state
        self._refresh_list()
        self.on_change()
    
    def _update_action_note(self, idx, text_widget):
        """Update character action note."""
        text = text_widget.get("1.0", "end").strip()
        self.selected_characters[idx]["action_note"] = text
        self.on_change()
    
    def _update_pose_category(self, idx, category_var, preset_combo):
        """Update character pose category."""
        cat = category_var.get()
        self.selected_characters[idx]["pose_category"] = cat
        self.selected_characters[idx]["pose_preset"] = ""
        
        if cat and cat in self.poses:
            preset_combo["values"] = [""] + sorted(list(self.poses[cat].keys()))
        else:
            preset_combo["values"] = [""]
        preset_combo.set("")
        self.on_change()
    
    def _update_pose_preset(self, idx, preset_name):
        """Update character pose preset."""
        self.selected_characters[idx]["pose_preset"] = preset_name
        self.on_change()
    
    def _refresh_list(self):
        """Refresh the list of selected characters."""
        for w in self.chars_container.winfo_children():
            w.destroy()

        # Update available characters
        used = {c["name"] for c in self.selected_characters}
        available = sorted([k for k in self.characters.keys() if k not in used])
        self.char_combo["values"] = available
        
        # Update bulk outfit target combo with selected characters + all option
        char_names = [c["name"] for c in self.selected_characters]
        self.bulk_chars_combo["values"] = ["All (with outfit)"] + char_names
        
        # Show empty state if no characters
        if not self.selected_characters:
            empty_frame = ttk.Frame(self.chars_container, style="TFrame")
            empty_frame.pack(fill="both", expand=True, padx=4, pady=20)
            empty_label = ttk.Label(empty_frame, text="👈 Add characters to get started", foreground="gray", font=("Consolas", 11))
            empty_label.pack()
            self.chars_container.update_idletasks()
            self.chars_canvas.config(scrollregion=self.chars_canvas.bbox("all"))
            return

        for i, cd in enumerate(self.selected_characters):
            char_title = f"#{i+1} — {cd['name']}"
            frame = ttk.LabelFrame(self.chars_container, text=char_title, 
                                 padding=6, style="TLabelframe")
            frame.pack(fill="x", pady=(0, 8), padx=4)
            
            # Outfit selector (clickable bubbles)
            ttk.Label(frame, text="👕 Outfit:", font=("Consolas", 9, "bold")).pack(fill="x", pady=(0, 2))
            outfits_frame = FlowFrame(frame, padding_x=6, padding_y=4)
            outfits_frame.pack(fill="x", pady=(0, 6))

            outfit_keys = sorted(list(self.characters.get(cd["name"], {}).get("outfits", {}).keys()))
            for o in outfit_keys:
                # Use accent button style for the selected outfit so it's visually distinct
                btn_style = "Accent.TButton" if o == cd.get("outfit", "") else "TButton"
                outfits_frame.add_button(
                    text=o,
                    style=btn_style,
                    command=(lambda idx=i, name=o: self._update_outfit(idx, name))
                )
            
            # Pose preset selector
            ttk.Label(frame, text="🎭 Pose (Optional):", font=("Consolas", 9, "bold")).pack(fill="x", pady=(6, 2))
            pose_row = ttk.Frame(frame)
            pose_row.pack(fill="x", pady=(0, 0))
            pose_row.columnconfigure(3, weight=1)

            ttk.Label(pose_row, text="Category:").grid(row=0, column=0, sticky="w", padx=(0, 4))
            pcat_var = tk.StringVar(value=cd.get("pose_category", ""))
            pcat_combo = ttk.Combobox(pose_row, textvariable=pcat_var, state="readonly", width=10)
            pcat_combo["values"] = [""] + sorted(list(self.poses.keys()))
            pcat_combo.grid(row=0, column=1, padx=(0, 10))
            
            ttk.Label(pose_row, text="Preset:").grid(row=0, column=2, sticky="w", padx=(0, 4))
            preset_var = tk.StringVar(value=cd.get("pose_preset", ""))
            preset_combo = ttk.Combobox(pose_row, textvariable=preset_var, state="readonly")
            preset_combo.grid(row=0, column=3, sticky="ew")

            # Initialize preset values
            current_cat = pcat_var.get()
            if current_cat and current_cat in self.poses:
                preset_combo["values"] = [""] + sorted(list(self.poses[current_cat].keys()))
            else:
                preset_combo["values"] = [""]

            pcat_combo.bind(
                "<<ComboboxSelected>>",
                lambda e, idx=i, cat_var=pcat_var, p_combo=preset_combo: 
                    self._update_pose_category(idx, cat_var, p_combo)
            )
            preset_combo.bind(
                "<<ComboboxSelected>>",
                lambda e, idx=i, var=preset_var: self._update_pose_preset(idx, var.get())
            )

            # Action note text area
            ttk.Label(frame, text="💬 Custom Pose/Action (Optional - Overrides Preset):", font=("Consolas", 9, "bold")).pack(fill="x", pady=(6, 0))
            action_text = tk.Text(frame, wrap="word", height=2)
            action_text.insert("1.0", cd.get("action_note", ""))
            action_text.pack(fill="x", pady=(0, 6))
            action_text.config(padx=5, pady=5)
            action_text.bind(
                "<KeyRelease>",
                lambda e, idx=i, tw=action_text: self._update_action_note(idx, tw)
            )

            # Separator
            ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=6)
            
            # Button row
            btnrow = ttk.Frame(frame, style="TFrame")
            btnrow.pack(fill="x")
            
            mv = ttk.Frame(btnrow, style="TFrame")
            mv.pack(side="left", fill="x", expand=True)
            if i > 0:
                ttk.Button(mv, text="↑ Move Up", width=10, 
                         command=lambda idx=i: self._move_up(idx)).pack(side="left", padx=(0, 4))
            if i < len(self.selected_characters) - 1:
                ttk.Button(mv, text="↓ Move Down", width=10, 
                         command=lambda idx=i: self._move_down(idx)).pack(side="left")
            
            ttk.Button(btnrow, text="✕ Remove", 
                     command=lambda idx=i: self._remove_character(idx)).pack(side="right")
        
        self.chars_container.update_idletasks()
        self.chars_canvas.config(scrollregion=self.chars_canvas.bbox("all"))
        self.on_change()
    
    def get_base_prompt_name(self):
        """Get selected base prompt name."""
        return self.base_prompt_var.get()
    
    def get_selected_characters(self):
        """Get list of selected characters with their data."""
        return self.selected_characters

    def set_selected_characters(self, characters_data):
        """Set the list of selected characters and refresh the UI.
        
        Args:
            characters_data: A list of character dictionaries.
        """
        self.selected_characters = characters_data
        self._refresh_list()

    def set_base_prompt(self, prompt_name):
        """Set the base prompt combobox to a specific value.
        
        Args:
            prompt_name: The name of the prompt to select.
        """
        if prompt_name in self.base_combo["values"]:
            self.base_prompt_var.set(prompt_name)

    def get_num_characters(self):
        """Get the number of selected characters."""
        return len(self.selected_characters)
    
    def apply_theme_to_action_texts(self, theme_manager, theme):
        """Apply theme to dynamic action text widgets.
        
        Args:
            theme_manager: ThemeManager instance
            theme: Theme color dict
        """
        for char_frame in self.chars_container.winfo_children():
            for widget in char_frame.winfo_children():
                if isinstance(widget, tk.Text):
                    theme_manager.apply_text_widget_theme(widget, theme)
