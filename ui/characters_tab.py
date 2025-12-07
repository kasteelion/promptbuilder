"""Characters and poses tab UI."""

import tkinter as tk
from tkinter import ttk, messagebox
from .widgets import FlowFrame
from .character_creator import CharacterCreatorDialog
from .base_style_creator import BaseStyleCreatorDialog
from .outfit_creator import SharedOutfitCreatorDialog, CharacterOutfitCreatorDialog
from .pose_creator import PoseCreatorDialog


class CharactersTab:
    """Tab for managing characters, outfits, and poses."""
    
    def __init__(self, parent, data_loader, on_change_callback, reload_callback=None):
        """Initialize characters tab.
        
        Args:
            parent: Parent notebook widget
            data_loader: DataLoader instance
            on_change_callback: Function to call when data changes
            reload_callback: Function to call to reload all data
        """
        self.parent = parent
        self.data_loader = data_loader
        self.on_change = on_change_callback
        self.reload_data = reload_callback
        
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
        bp.columnconfigure(0, weight=1)
        ttk.Label(bp, text="Choose a base art style", foreground="gray", font=("Consolas", 9)).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 0))
        
        self.base_prompt_var = tk.StringVar()
        self.base_combo = ttk.Combobox(bp, state="readonly", textvariable=self.base_prompt_var)
        self.base_combo.grid(row=1, column=0, sticky="ew", padx=(4, 2), pady=(0, 4))
        self.base_combo.bind("<<ComboboxSelected>>", lambda e: self.on_change())
        
        ttk.Button(bp, text="✨ Create Style", command=self._create_new_style).grid(row=1, column=1, sticky="ew", padx=(2, 4), pady=(0, 4))

        # Bulk outfit editor section
        bulk = ttk.LabelFrame(self.tab, text="⚡ Bulk Outfit Editor (Speed Tool)", style="TLabelframe")
        bulk.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        bulk.columnconfigure(1, weight=1)
        ttk.Label(bulk, text="Apply same outfit to multiple characters at once", foreground="gray", font=("Consolas", 9)).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 4))
        
        ttk.Label(bulk, text="Shared Outfit:").grid(row=1, column=0, sticky="w", padx=(4, 2))
        self.bulk_outfit_var = tk.StringVar()
        self.bulk_outfit_combo = ttk.Combobox(bulk, textvariable=self.bulk_outfit_var, state="readonly")
        self.bulk_outfit_combo.grid(row=1, column=1, sticky="ew", padx=2)
        self.bulk_outfit_combo['values'] = []
        self.bulk_outfit_combo.bind("<Return>", lambda e: self._apply_bulk_outfit())
        
        ttk.Label(bulk, text="Apply to:").grid(row=2, column=0, sticky="w", padx=(4, 2), pady=(4, 0))
        self.bulk_chars_var = tk.StringVar()
        self.bulk_chars_combo = ttk.Combobox(bulk, textvariable=self.bulk_chars_var, state="readonly")
        self.bulk_chars_combo.grid(row=2, column=1, sticky="ew", padx=2, pady=(4, 0))
        self.bulk_chars_combo.bind("<Return>", lambda e: self._apply_bulk_outfit())
        
        # Button row
        btn_frame = ttk.Frame(bulk)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        ttk.Button(btn_frame, text="Apply Outfit", 
                  command=self._apply_bulk_outfit).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        ttk.Button(btn_frame, text="✨ Create Shared Outfit", 
                  command=self._create_shared_outfit).grid(row=0, column=1, sticky="ew", padx=(2, 0))

        # Add character section
        add = ttk.LabelFrame(self.tab, text="👥 Add Character", style="TLabelframe")
        add.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        add.columnconfigure(0, weight=1)
        ttk.Label(add, text="Select a character and press Add or Enter", foreground="gray", font=("Consolas", 9)).grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 4))
        
        self.char_var = tk.StringVar()
        self.char_combo = ttk.Combobox(add, state="readonly", textvariable=self.char_var)
        self.char_combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 4), padx=4)
        self.char_combo.bind("<Return>", lambda e: self._add_character())
        
        button_frame = ttk.Frame(add)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        ttk.Button(button_frame, text="+ Add to Prompt", command=self._add_character).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        ttk.Button(button_frame, text="✨ Create New Character", command=self._create_new_character).grid(row=0, column=1, sticky="ew", padx=(2, 0))

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
    
    def _create_new_character(self):
        """Open dialog to create a new character."""
        # Get the root window to use as parent
        root = self.tab.winfo_toplevel()
        dialog = CharacterCreatorDialog(root, self.data_loader, self.reload_data)
        result = dialog.show()
        
        # If character was created and reload callback exists, it will be called automatically
    
    def _create_new_style(self):
        """Open dialog to create a new base art style."""
        root = self.tab.winfo_toplevel()
        dialog = BaseStyleCreatorDialog(root, self.data_loader, self.reload_data)
        result = dialog.show()
    
    def _create_shared_outfit(self):
        """Open dialog to create a new shared outfit."""
        root = self.tab.winfo_toplevel()
        dialog = SharedOutfitCreatorDialog(root, self.data_loader, self.reload_data)
        result = dialog.show()
    
    def _create_character_outfit(self, character_name):
        """Open dialog to create a new character-specific outfit."""
        root = self.tab.winfo_toplevel()
        dialog = CharacterOutfitCreatorDialog(root, self.data_loader, character_name, self.reload_data)
        result = dialog.show()
    
    def _create_new_pose(self):
        """Open dialog to create a new pose preset."""
        root = self.tab.winfo_toplevel()
        dialog = PoseCreatorDialog(root, self.data_loader, self.reload_data)
        result = dialog.show()
    
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
            
            # Outfit selector - collapsible
            outfit_header = ttk.Frame(frame)
            outfit_header.pack(fill="x", pady=(0, 2))
            
            outfit_label = ttk.Label(outfit_header, text="👕 Outfit:", font=("Consolas", 9, "bold"))
            outfit_label.pack(side="left")
            
            # Show current outfit
            current_outfit = cd.get("outfit", "")
            if current_outfit:
                current_label = ttk.Label(outfit_header, text=f" {current_outfit}", font=("Consolas", 9), foreground="#0066cc")
                current_label.pack(side="left")
            
            # Collapsible outfit frame
            outfit_container = ttk.Frame(frame)
            outfit_expanded = tk.BooleanVar(value=False)
            
            def make_toggle(container, expanded, parent_frame):
                def toggle():
                    if expanded.get():
                        container.pack_forget()
                        expanded.set(False)
                    else:
                        # Pack after the first child (outfit_header)
                        container.pack(fill="x", pady=(0, 6))
                        # Move to correct position
                        container.pack_configure(after=parent_frame.winfo_children()[0])
                        expanded.set(True)
                return toggle
            
            toggle_func = make_toggle(outfit_container, outfit_expanded, frame)
            toggle_btn = ttk.Button(outfit_header, text="▼", width=3, command=toggle_func)
            toggle_btn.pack(side="right")
            
            # Outfit options inside collapsible frame
            outfits_frame = FlowFrame(outfit_container, padding_x=6, padding_y=4)
            outfits_frame.pack(fill="x", pady=(2, 2))

            outfit_keys = sorted(list(self.characters.get(cd["name"], {}).get("outfits", {}).keys()))
            for o in outfit_keys:
                btn_style = "Accent.TButton" if o == current_outfit else "TButton"
                outfits_frame.add_button(
                    text=o,
                    style=btn_style,
                    command=(lambda idx=i, name=o, tog=toggle_func: (self._update_outfit(idx, name), tog()))
                )
            
            # Outfit creator button
            ttk.Button(outfit_container, text="✨ New Outfit for Character", 
                      command=lambda name=cd["name"]: self._create_character_outfit(name)).pack(fill="x", pady=(2, 0))
            
            # Pose preset selector
            ttk.Label(frame, text="🎭 Pose (Optional):", font=("Consolas", 9, "bold")).pack(fill="x", pady=(6, 2))
            pose_row = ttk.Frame(frame)
            pose_row.pack(fill="x", pady=(0, 4))
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
            
            # Add create pose button
            ttk.Button(pose_row, text="✨", width=3, command=self._create_new_pose).grid(row=0, column=4, padx=(5, 0))

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
