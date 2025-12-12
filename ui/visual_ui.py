# ui/visual_ui.py
"""
Deprecated: visual_ui

This module previously provided an experimental "Visual Gallery" UI mode.
The implementation was removed from the active codebase on December 12, 2025.

The file remains as an archival placeholder. Do not import or instantiate
the VisualPromptBuilderUI class; it no longer exists in this runtime.
"""

raise ImportError("ui.visual_ui has been removed: Visual Gallery mode is deprecated (see docs/VISUAL_UI_GUIDE.md)")
    
    def _build_ui(self):
        """Build the visual UI layout."""
        # Main container with 3-pane layout
        # Left: Character Gallery | Middle: Settings | Right: Preview
        
        main_paned = ttk.PanedWindow(self.root, orient="horizontal")
        main_paned.pack(fill="both", expand=True)
        
        # LEFT PANEL: Character Gallery (fixed width ~250px)
        left_frame = ttk.Frame(main_paned, style="TFrame", width=250)
        main_paned.add(left_frame, weight=1)
        
        self.character_gallery = CharacterGalleryPanel(
            left_frame,
            self.data_loader,
            on_add_callback=self._on_character_selected,
            theme_colors=self.theme_manager.themes.get(
                self.theme_manager.current_theme or "Dark", {}
            )
        )
        self.character_gallery.pack(fill="both", expand=True)
        
        # Load characters into gallery
        self.character_gallery.load_characters(self.characters)
        
        # MIDDLE PANEL: Settings and controls
        middle_paned = ttk.PanedWindow(main_paned, orient="vertical")
        main_paned.add(middle_paned, weight=3)
        
        # Top section: Base prompt, scene, notes
        settings_frame = ttk.Frame(middle_paned, style="TFrame")
        middle_paned.add(settings_frame, weight=1)
        
        settings_frame.columnconfigure(0, weight=1)
        
        # Base prompt selector
        bp_frame = ttk.LabelFrame(settings_frame, text="📋 Base Prompt (Style)", style="TLabelframe")
        bp_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        bp_frame.columnconfigure(0, weight=1)
        
        self.base_prompt_var = tk.StringVar()
        base_combo = ttk.Combobox(bp_frame, state="readonly", textvariable=self.base_prompt_var)
        base_combo.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        base_combo.bind("<<ComboboxSelected>>", lambda e: self.schedule_preview_update())
        
        # Load base prompts
        base_combo['values'] = sorted(list(self.base_prompts.keys()))
        if self.base_prompts:
            base_combo.current(0)
        
        # Scene section
        scene_frame = ttk.LabelFrame(settings_frame, text="🎬 Scene", style="TLabelframe")
        scene_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        scene_frame.columnconfigure(0, weight=1)
        
        self.scene_text = tk.Text(scene_frame, wrap="word", height=3)
        self.scene_text.pack(fill="x", padx=4, pady=4)
        self.scene_text.bind("<KeyRelease>", lambda e: self.schedule_preview_update())
        
        # Notes section
        notes_frame = ttk.LabelFrame(settings_frame, text="📝 Notes & Interactions", style="TLabelframe")
        notes_frame.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)
        notes_frame.columnconfigure(0, weight=1)
        notes_frame.rowconfigure(1, weight=1)
        settings_frame.rowconfigure(2, weight=1)
        
        # Interaction template selector (with category grouping)
        interaction_control = ttk.Frame(notes_frame, style="TFrame")
        interaction_control.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        interaction_control.columnconfigure(1, weight=1)
        interaction_control.columnconfigure(3, weight=1)
        
        ttk.Label(interaction_control, text="Category:", style="TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 4)
        )
        
        self.interaction_category_var = tk.StringVar()
        self.interaction_cat_combo = ttk.Combobox(
            interaction_control,
            textvariable=self.interaction_category_var,
            state="readonly",
            width=15
        )
        self.interaction_cat_combo.grid(row=0, column=1, sticky="w", padx=(0, 8))
        self.interaction_cat_combo.bind("<<ComboboxSelected>>", lambda e: self._update_interaction_presets())
        create_tooltip(self.interaction_cat_combo, "Choose interaction category")
        
        ttk.Label(interaction_control, text="Template:", style="TLabel").grid(
            row=0, column=2, sticky="w", padx=(0, 4)
        )
        
        self.interaction_var = tk.StringVar(value="")
        self.interaction_combo = ttk.Combobox(
            interaction_control,
            textvariable=self.interaction_var,
            state="readonly"
        )
        self.interaction_combo.grid(row=0, column=3, sticky="ew")
        create_tooltip(self.interaction_combo, "Choose a multi-character interaction template")
        
        insert_btn = ttk.Button(
            interaction_control,
            text="Insert",
            command=self._insert_interaction_template
        )
        insert_btn.grid(row=0, column=4, padx=(4, 0))
        create_tooltip(insert_btn, "Insert template with selected characters")
        
        refresh_btn = ttk.Button(
            interaction_control,
            text="🔄",
            command=self._refresh_interaction_template,
            width=3
        )
        refresh_btn.grid(row=0, column=5, padx=(4, 0))
        create_tooltip(refresh_btn, "Re-fill template with current characters")
        
        create_btn = ttk.Button(
            interaction_control,
            text="+ Create",
            command=self._create_new_interaction
        )
        create_btn.grid(row=0, column=6, padx=(4, 0))
        create_tooltip(create_btn, "Create a new interaction template")
        
        self.notes_text = tk.Text(notes_frame, wrap="word", height=4)
        self.notes_text.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 4))
        self.notes_text.bind("<KeyRelease>", lambda e: self.schedule_preview_update())
        
        # Bottom section: Selected characters list
        selected_frame = ttk.LabelFrame(settings_frame, text="✨ Selected Characters", style="TLabelframe")
        selected_frame.grid(row=3, column=0, sticky="nsew", padx=4, pady=4)
        selected_frame.columnconfigure(0, weight=1)
        selected_frame.rowconfigure(0, weight=1)
        settings_frame.rowconfigure(3, weight=2)
        
        # Scrollable list of selected characters
        list_frame = ttk.Frame(selected_frame)
        list_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.selected_listbox = tk.Listbox(list_frame, height=6)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.selected_listbox.yview)
        self.selected_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.selected_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        btn_frame = ttk.Frame(selected_frame)
        btn_frame.pack(fill="x", padx=4, pady=(0, 4))
        
        ttk.Button(btn_frame, text="Remove Selected", 
                  command=self._remove_selected).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Clear All", 
                  command=self._clear_all).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🎲 Randomize", 
                  command=self.randomize_all).pack(side="right", padx=2)
        
        # RIGHT PANEL: Preview
        right_frame = ttk.Frame(main_paned, style="TFrame")
        main_paned.add(right_frame, weight=3)
        
        self.preview_panel = PreviewPanel(
            right_frame,
            self.theme_manager,
            self.reload_data,
            self.randomize_all
        )
        
        # Set preview callbacks
        self.preview_panel.set_callbacks(
            self._generate_prompt,
            self._validate_prompt,
            self.randomize_all
        )
    
    def _on_character_selected(self, character_name):
        """Handle character selection from gallery.
        
        Args:
            character_name: Name of selected character
        """
        # Add to selected characters
        char_def = self.characters.get(character_name, {})
        outfits = char_def.get("outfits", {})
        
        # Auto-assign first available outfit
        outfit = ""
        if "Base" in outfits:
            outfit = "Base"
        elif outfits:
            outfit = sorted(list(outfits.keys()))[0]
        
        # Add to selected characters list
        self.selected_characters.append({
            'name': character_name,
            'outfit': outfit,
            'pose_category': '',
            'pose_preset': '',
            'action_note': ''
        })
        
        # Update listbox
        self._update_selected_list()
        
        # Update preview
        self.schedule_preview_update()
    
    def _update_selected_list(self):
        """Update the selected characters listbox."""
        self.selected_listbox.delete(0, tk.END)
        
        for char in self.selected_characters:
            display = f"{char['name']}"
            if char.get('outfit'):
                display += f" - {char['outfit']}"
            self.selected_listbox.insert(tk.END, display)
    
    def _update_interaction_presets(self):
        """Update interaction template dropdown based on selected category."""
        cat = self.interaction_category_var.get()
        if cat and cat in self.interactions:
            templates = list(self.interactions[cat].keys())
            self.interaction_combo['values'] = templates
            if templates:
                self.interaction_var.set(templates[0])
            else:
                self.interaction_var.set("")
        else:
            self.interaction_combo['values'] = []
            self.interaction_var.set("")
    
    def _insert_interaction_template(self):
        """Insert interaction template with character placeholders filled."""
        from tkinter import messagebox
        from utils import logger
        
        cat = self.interaction_category_var.get()
        template_name = self.interaction_var.get()
        
        if not cat or cat not in self.interactions:
            return
        if not template_name or template_name not in self.interactions[cat]:
            return
        
        template_text = self.interactions[cat][template_name]
        
        if not template_text:
            return
        
        # Get list of selected character names
        selected_chars = [char['name'] for char in self.selected_characters]
        
        if not selected_chars:
            messagebox.showinfo(
                "No Characters",
                "Please add characters to your prompt first before using interaction templates.",
                parent=self.root
            )
            return
        
        # Fill template with character names
        filled_text = fill_template(template_text, selected_chars)
        
        # Insert at cursor position or append
        try:
            current_text = self.notes_text.get("1.0", "end-1c")
            if current_text.strip():
                # Add on new line if there's existing content
                self.notes_text.insert("end", "\n" + filled_text)
            else:
                # Replace empty content
                self.notes_text.delete("1.0", "end")
                self.notes_text.insert("1.0", filled_text)
            
            self.schedule_preview_update()
        except tk.TclError as e:
            logger.error(f"Error inserting interaction template: {e}")
    
    def _create_new_interaction(self):
        """Open dialog to create a new interaction template."""
        from .interaction_creator import InteractionCreatorDialog
        dialog = InteractionCreatorDialog(self.root, self.data_loader, self._reload_interaction_templates)
        result = dialog.show()
    
    def _refresh_interaction_template(self):
        """Replace notes with re-filled interaction template using current characters."""
        from utils import logger
        
        cat = self.interaction_category_var.get()
        template_name = self.interaction_var.get()
        
        if not cat or cat not in self.interactions:
            return
        if not template_name or template_name not in self.interactions[cat]:
            return
        
        template_text = self.interactions[cat][template_name]
        
        if not template_text:
            return
        
        # Get list of selected character names
        selected_chars = [char['name'] for char in self.selected_characters]
        
        if not selected_chars:
            from tkinter import messagebox
            messagebox.showinfo(
                "No Characters",
                "Please add characters to your prompt first before using interaction templates.",
                parent=self.root
            )
            return
        
        # Fill template with character names
        filled_text = fill_template(template_text, selected_chars)
        
        # Replace notes content
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", filled_text)
        
        self.schedule_preview_update()
        logger.info(f"Refreshed interaction template: {template_name}")
    
    def _reload_interaction_templates(self):
        """Reload interaction templates from file."""
        try:
            # Reload interactions from markdown file
            self.interactions = self.data_loader.load_interactions()
            
            # Update category combo
            categories = list(self.interactions.keys())
            self.interaction_cat_combo['values'] = categories
            
            # Keep current category if it exists, otherwise select first
            current_cat = self.interaction_category_var.get()
            if current_cat not in self.interactions and categories:
                self.interaction_category_var.set(categories[0])
            
            # Update template dropdown based on category
            self._update_interaction_presets()
            
            from utils import logger
            logger.info("Interaction templates reloaded successfully")
        except Exception as e:
            from utils import logger
            logger.error(f"Error reloading interaction templates: {e}")
    
    def _remove_selected(self):
        """Remove selected character from list."""
        selection = self.selected_listbox.curselection()
        if selection:
            idx = selection[0]
            self.selected_characters.pop(idx)
            self._update_selected_list()
            self.schedule_preview_update()
    
    def _clear_all(self):
        """Clear all selected characters."""
        from tkinter import messagebox
        if messagebox.askyesno("Clear All", "Remove all characters?"):
            self.selected_characters.clear()
            self._update_selected_list()
            self.schedule_preview_update()
    
    def load_characters(self, characters):
        """Load characters into gallery.
        
        Args:
            characters: Dict of character data
        """
        self.character_gallery.load_characters(characters)
    
    def schedule_preview_update(self):
        """Schedule a preview update with throttling."""
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(self._throttle_ms, self._update_preview)
    
    def _update_preview(self):
        """Update the preview panel."""
        self._after_id = None
        self.preview_panel.update_preview()
    
    def _generate_prompt(self):
        """Generate the final prompt."""
        builder = PromptBuilder()
        
        # Get base prompt
        base_key = self.base_prompt_var.get()
        base_text = self.base_prompts.get(base_key, {}).get('text', '')
        
        # Get scene
        scene = self.scene_text.get('1.0', 'end-1c').strip()
        
        # Get notes
        notes = self.notes_text.get('1.0', 'end-1c').strip()
        
        # Build character descriptions
        char_descriptions = []
        for char in self.selected_characters:
            char_name = char['name']
            char_def = self.characters.get(char_name, {})
            
            # Get outfit details
            outfit_name = char.get('outfit', '')
            outfit_details = char_def.get('outfits', {}).get(outfit_name, {})
            
            desc = f"{char_name}"
            if outfit_details:
                desc += f", {outfit_details.get('description', '')}"
            
            char_descriptions.append(desc)
        
        # Build prompt
        parts = []
        if base_text:
            parts.append(base_text)
        if scene:
            parts.append(f"Scene: {scene}")
        if char_descriptions:
            parts.append(f"Characters: {', '.join(char_descriptions)}")
        if notes:
            parts.append(notes)
        
        return '\\n\\n'.join(parts)
    
    def _validate_prompt(self):
        """Validate the current prompt configuration."""
        return len(self.selected_characters) > 0
    
    def randomize_all(self):
        """Randomize all settings using the randomizer."""
        config = self.randomizer.randomize(
            num_characters=None,  # Will randomize 2-3 characters
            include_scene=True,
            include_notes=True
        )
        
        # Apply base prompt
        if config["base_prompt"]:
            self.base_prompt_var.set(config["base_prompt"])
        
        # Apply selected characters
        self.selected_characters = config["selected_characters"]
        self._update_selected_list()
        
        # Apply scene
        if config.get("scene"):
            self.scene_text.delete("1.0", "end")
            self.scene_text.insert("1.0", config["scene"])
        
        # Apply interaction/notes
        if config.get("notes"):
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", config["notes"])
        
        self.schedule_preview_update()
    
    def reload_data(self):
        """Reload all data from files."""
        try:
            self.characters = self.data_loader.load_characters()
            self.base_prompts = self.data_loader.load_base_prompts()
            self.scenes = self.data_loader.load_presets("scenes.md")
            self.poses = self.data_loader.load_presets("poses.md")
            self.interactions = self.data_loader.load_interactions()
            self.randomizer = PromptRandomizer(
                self.characters, 
                self.base_prompts, 
                self.poses,
                self.scenes,
                self.interactions
            )
            self._reload_interaction_templates()
            
            # Reload gallery
            self.character_gallery.load_characters(self.characters)
            
            from tkinter import messagebox
            messagebox.showinfo("Success", "Data reloaded successfully!")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to reload data: {str(e)}")
    
    def _setup_menu(self):
        """Setup the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        for theme_name in self.theme_manager.themes.keys():
            theme_menu.add_command(
                label=theme_name,
                command=lambda t=theme_name: self._change_theme(t)
            )
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        
        # UI Mode submenu
        ui_mode_menu = tk.Menu(view_menu, tearoff=0)
        ui_mode_menu.add_command(label="Classic (Tabs)", command=lambda: self._switch_ui_mode("classic"))
        ui_mode_menu.add_command(label="Visual Gallery", command=lambda: self._switch_ui_mode("visual"))
        view_menu.add_cascade(label="UI Mode", menu=ui_mode_menu)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Reload Data", command=self.reload_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
    
    def _change_theme(self, theme_name):
        """Change the current theme."""
        self.theme_manager.apply_theme(theme_name)
        self.prefs.set("last_theme", theme_name)
        
        # Update gallery colors
        theme_colors = self.theme_manager.themes.get(theme_name, {})
        self.character_gallery.theme_colors = theme_colors
        self.character_gallery._refresh_display()
    
    def _switch_ui_mode(self, mode):
        """Switch UI mode."""
        self.prefs.set("ui_mode", mode)
        from tkinter import messagebox
        messagebox.showinfo("UI Mode", "UI mode changed. Please restart the application.")
    
    def _on_closing(self):
        """Handle window closing."""
        # Save preferences
        geometry = self.root.geometry()
        self.prefs.set("window_geometry", geometry)
        
        self.root.destroy()
