"""Main application window."""

import tkinter as tk
from tkinter import ttk, messagebox
from logic import DataLoader, PromptValidator, PromptRandomizer
from core.builder import PromptBuilder
from themes import ThemeManager
from config import (
    DEFAULT_THEME, 
    DEFAULT_FONT_FAMILY, 
    DEFAULT_FONT_SIZE, 
    MIN_FONT_SIZE,
    MAX_FONT_SIZE,
    FONT_SIZE_BREAKPOINTS,
    PREVIEW_UPDATE_THROTTLE_MS,
    RESIZE_THROTTLE_MS,
    RESIZE_SIGNIFICANT_CHANGE_PX,
    MIN_PANE_WIDTH
)
from .characters_tab import CharactersTab
from .edit_tab import EditTab
from .preview_panel import PreviewPanel


class PromptBuilderApp:
    """Main application class for Prompt Builder."""
    
    def __init__(self, root):
        """Initialize the application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Prompt Builder — Group Picture Generator")
        
        # Initialize data
        self.data_loader = DataLoader()
        self.validator = PromptValidator()
        
        try:
            self.characters = self.data_loader.load_characters()
        except Exception as e:
            messagebox.showerror("Error loading characters", str(e))
            self.root.destroy()
            return
        
        self.base_prompts = self.data_loader.load_base_prompts()
        self.scenes = self.data_loader.load_presets("scenes.md")
        self.poses = self.data_loader.load_presets("poses.md")
        self.randomizer = PromptRandomizer(self.characters, self.base_prompts, self.poses)
        
        # Initialize theme manager
        self.style = ttk.Style()
        self.theme_manager = ThemeManager(self.root, self.style)
        
        # Throttling for preview updates
        self._after_id = None
        self._throttle_ms = PREVIEW_UPDATE_THROTTLE_MS
        
        # Throttling for resize events
        self._resize_after_id = None
        self._resize_throttle_ms = RESIZE_THROTTLE_MS
        self._last_resize_width = 0
        self._user_font_adjustment = 0  # User can adjust font size +/-
        
        # Build UI
        self._build_ui()
        
        # Set initial fonts and theme
        self._set_initial_fonts()
        self._apply_theme(DEFAULT_THEME)
        
        # Initial preview update
        self.update_preview()
        
        # Bind resize event
        self.root.bind("<Configure>", self._on_resize)
    
    def _build_ui(self):
        """Build the main UI layout."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu for font controls
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Increase Font Size", command=self._increase_font, accelerator="Ctrl++")
        view_menu.add_command(label="Decrease Font Size", command=self._decrease_font, accelerator="Ctrl+-")
        view_menu.add_command(label="Reset Font Size", command=self._reset_font, accelerator="Ctrl+0")
        
        # Bind keyboard shortcuts for font control
        self.root.bind('<Control-plus>', lambda e: self._increase_font())
        self.root.bind('<Control-equal>', lambda e: self._increase_font())  # + without shift
        self.root.bind('<Control-minus>', lambda e: self._decrease_font())
        self.root.bind('<Control-0>', lambda e: self._reset_font())
        
        # Use PanedWindow directly in root to allow resizable left (notebook) and right (preview) panes
        # Drag the sash between them to resize
        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Left side: Notebook with tabs (give it more weight for better visibility)
        self.notebook = ttk.Notebook(paned, style="TNotebook")
        paned.add(self.notebook, weight=3)

        # Create tabs
        self.characters_tab = CharactersTab(
            self.notebook, 
            self.data_loader, 
            self.schedule_preview_update,
            self.reload_data
        )
        self.edit_tab = EditTab(
            self.notebook, 
            self.data_loader, 
            self.reload_data
        )

        # Load data into tabs
        self.characters_tab.load_data(self.characters, self.base_prompts, self.poses, self.scenes)

        # Right side: Preview panel (less weight so it takes less space)
        right_frame = ttk.Frame(paned, style="TFrame")
        paned.add(right_frame, weight=2)
        right_frame.rowconfigure(2, weight=1)  # Preview gets all expanding space
        right_frame.columnconfigure(0, weight=1)
        
        # Scene section (compact)
        scene_frame = ttk.LabelFrame(right_frame, text="🎬 Scene", style="TLabelframe")
        scene_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        scene_frame.columnconfigure(1, weight=1)
        
        # Scene presets row
        ttk.Label(scene_frame, text="Category:", font=("Consolas", 9)).grid(row=0, column=0, sticky="w", padx=(4, 2), pady=2)
        self.scene_category_var = tk.StringVar()
        self.scene_cat_combo = ttk.Combobox(scene_frame, textvariable=self.scene_category_var, state="readonly", width=10)
        self.scene_cat_combo.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        self.scene_cat_combo.bind("<<ComboboxSelected>>", lambda e: self._update_scene_presets())
        
        ttk.Label(scene_frame, text="Preset:", font=("Consolas", 9)).grid(row=0, column=2, sticky="w", padx=(8, 2), pady=2)
        self.scene_preset_var = tk.StringVar()
        self.scene_combo = ttk.Combobox(scene_frame, textvariable=self.scene_preset_var, state="readonly", width=15)
        self.scene_combo.grid(row=0, column=3, sticky="ew", padx=2, pady=2)
        self.scene_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_scene_preset())
        
        ttk.Button(scene_frame, text="✨", width=3, command=self._create_new_scene).grid(row=0, column=4, padx=(4, 4), pady=2)
        
        self.scene_text = tk.Text(scene_frame, wrap="word", height=2)
        self.scene_text.grid(row=1, column=0, columnspan=5, sticky="ew", padx=4, pady=(0, 4))
        self.scene_text.bind("<KeyRelease>", lambda e: self.schedule_preview_update())
        
        # Notes section (compact)
        notes_frame = ttk.LabelFrame(right_frame, text="📝 Notes", style="TLabelframe")
        notes_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=2)
        notes_frame.columnconfigure(0, weight=1)
        
        self.notes_text = tk.Text(notes_frame, wrap="word", height=2)
        self.notes_text.pack(fill="x", padx=4, pady=4)
        self.notes_text.bind("<KeyRelease>", lambda e: self.schedule_preview_update())
        
        # Preview panel container
        preview_container = ttk.Frame(right_frame, style="TFrame")
        preview_container.grid(row=2, column=0, sticky="nsew", padx=0, pady=(2, 0))
        
        self.preview_panel = PreviewPanel(
            preview_container, 
            self.theme_manager,
            self.reload_data,
            self._on_theme_change,
            self.randomize_all
        )
        
        # Set preview callbacks
        self.preview_panel.set_callbacks(
            self._generate_prompt,
            self._validate_prompt,
            self.randomize_all
        )
        
        # Initialize scene presets
        self._update_scene_presets()
    
    def _update_scene_presets(self):
        """Update scene preset combo based on selected category."""
        cat = self.scene_category_var.get()
        if cat and cat in self.scenes:
            self.scene_combo["values"] = [""] + sorted(list(self.scenes[cat].keys()))
        else:
            self.scene_combo["values"] = [""]
        self.scene_preset_var.set("")
        
        # Update category combo
        self.scene_cat_combo["values"] = [""] + sorted(list(self.scenes.keys()))
    
    def _apply_scene_preset(self):
        """Apply selected scene preset to text area."""
        cat = self.scene_category_var.get()
        name = self.scene_preset_var.get()
        
        if cat and name and cat in self.scenes and name in self.scenes[cat]:
            self.scene_text.delete("1.0", "end")
            self.scene_text.insert("1.0", self.scenes[cat][name])
            self.schedule_preview_update()
    
    def _create_new_scene(self):
        """Open dialog to create a new scene."""
        from .scene_creator import SceneCreatorDialog
        dialog = SceneCreatorDialog(self.root, self.data_loader, self.reload_data)
        result = dialog.show()
    
    def _set_initial_fonts(self):
        """Set initial fonts on text widgets."""
        font = (DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE)
        for widget in [self.scene_text, 
                      self.notes_text, 
                      self.preview_panel.preview_text,
                      self.edit_tab.editor_text]:
            widget.config(padx=10, pady=10, font=font)
    
    def _on_theme_change(self, theme_name):
        """Handle theme change event.
        
        Args:
            theme_name: Name of new theme
        """
        self._apply_theme(theme_name)
    
    def _apply_theme(self, theme_name):
        """Apply theme to all UI elements.
        
        Args:
            theme_name: Name of theme to apply
        """
        theme = self.theme_manager.apply_theme(theme_name)
        
        # Apply to text widgets
        self.theme_manager.apply_preview_theme(self.preview_panel.preview_text, theme)
        for widget in [self.scene_text, 
                      self.notes_text, 
                      self.edit_tab.editor_text]:
            self.theme_manager.apply_text_widget_theme(widget, theme)
        
        # Apply to canvas
        self.theme_manager.apply_canvas_theme(self.characters_tab.chars_canvas, theme)
        
        # Apply to dynamic character action texts
        self.characters_tab.apply_theme_to_action_texts(self.theme_manager, theme)
    
    def schedule_preview_update(self):
        """Schedule a preview update with throttling."""
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(self._throttle_ms, self.update_preview)
    
    def update_preview(self):
        """Update the preview panel with current prompt."""
        prompt = self._generate_prompt_or_error()
        self.preview_panel.update_preview(prompt)
    
    def _validate_prompt(self):
        """Validate current prompt data.
        
        Returns:
            str: Error message or None if valid
        """
        selected_chars = self.characters_tab.get_selected_characters()
        return self.validator.validate(selected_chars)
    
    def _generate_prompt(self):
        """Generate prompt from current data (assumes valid).
        
        Returns:
            str: Generated prompt text
        """
        builder = PromptBuilder(self.characters, self.base_prompts, self.poses)
        
        config = {
            "selected_characters": self.characters_tab.get_selected_characters(),
            "base_prompt": self.characters_tab.get_base_prompt_name(),
            "scene": self.scene_text.get("1.0", "end").strip(),
            "notes": self.notes_text.get("1.0", "end").strip()
        }
        
        return builder.generate(config)
    
    def _generate_prompt_or_error(self):
        """Generate prompt or return validation error.
        
        Returns:
            str: Generated prompt or error message
        """
        error = self._validate_prompt()
        if error:
            # Friendly welcome message instead of harsh error
            return """✨ Welcome to Prompt Builder! ✨

To get started:
1. Select a character from the dropdown below
2. Click "+ Add to Group" to add them to your scene
3. Choose their outfit and pose
4. Add more characters if you'd like
5. Optionally select a scene preset or write your own
6. Watch your prompt appear here!

Need help? 
• Use "✨ Create New Character" to design your own character
• Try the "🎲 Randomize" button for inspiration
• Check the Edit Data tab to customize everything

---

Ready when you are! Add your first character to begin."""
        return self._generate_prompt()
    
    def reload_data(self):
        """Reload all data from markdown files."""
        try:
            new_characters = self.data_loader.load_characters()
            self.base_prompts = self.data_loader.load_base_prompts()
            self.scenes = self.data_loader.load_presets("scenes.md")
            self.poses = self.data_loader.load_presets("poses.md")
        except Exception as e:
            messagebox.showerror("Reload Error", str(e))
            return

        # Update character selection validity
        new_chars_keys = set(new_characters.keys())
        selected = self.characters_tab.get_selected_characters()
        updated_selected = []
        chars_removed = False
        
        for c in selected:
            if c['name'] in new_chars_keys:
                c.setdefault('pose_category', '')
                c.setdefault('pose_preset', '')
                c.setdefault('action_note', '')
                updated_selected.append(c)
            else:
                chars_removed = True

        self.characters = new_characters
        self.characters_tab.selected_characters = updated_selected

        if chars_removed:
            messagebox.showinfo(
                "Reload Info", 
                "Some previously selected characters were removed as they no longer exist in the updated data."
            )

        # Reload data in tabs
        self.characters_tab.load_data(self.characters, self.base_prompts, self.poses)
        self.scene_tab.load_data(self.scenes)
        self.edit_tab._refresh_file_list()  # Refresh file list to show new character files
        
        self.schedule_preview_update()
        messagebox.showinfo("Success", "Data reloaded")

    def randomize_all(self):
        """Generate a random prompt and update the UI."""
        config = self.randomizer.randomize(
            num_characters=self.characters_tab.get_num_characters(),
            include_scene=True,
            include_notes=True
        )
        
        self.characters_tab.set_selected_characters(config["selected_characters"])
        self.characters_tab.set_base_prompt(config["base_prompt"])
        self.scene_tab.set_scene_text(config["scene"])
        self.notes_tab.set_notes_text(config["notes"])
        
        self.schedule_preview_update()
    
    def _on_resize(self, event):
        """Throttle window resize events to prevent excessive updates."""
        if self._resize_after_id:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(self._resize_throttle_ms, 
                                                 lambda: self._perform_resize(event))

    def _perform_resize(self, event):
        """Handle window resize for dynamic font sizing with performance optimization.
        
        Args:
            event: Tkinter event
        """
        try:
            w = self.root.winfo_width()
            if w <= 1:  # Window not yet mapped
                return

            # Only update if width changed significantly
            if abs(w - self._last_resize_width) < RESIZE_SIGNIFICANT_CHANGE_PX:
                return
            
            self._last_resize_width = w

            # Calculate font size using breakpoints
            base_size = self._calculate_font_size(w)
            final_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, base_size + self._user_font_adjustment))
            font_family = DEFAULT_FONT_FAMILY
            new_font = (font_family, final_size)

            # List of all text widgets to apply the new font size
            text_widgets = [
                self.scene_text,
                self.notes_text,
                self.edit_tab.editor_text,
                self.preview_panel.preview_text
            ]

            for widget in text_widgets:
                widget.config(font=new_font)

            # Special handling for preview panel tags
            preview = self.preview_panel.preview_text
            preview.tag_config("bold", font=(font_family, final_size, "bold"))
            preview.tag_config("title", font=(font_family, final_size + 2, "bold"))
            preview.tag_config("error", font=(font_family, final_size, "bold"))
        
        except Exception:
            pass  # Ignore errors during resize
    
    def _calculate_font_size(self, width):
        """Calculate font size based on window width using breakpoints.
        
        Args:
            width: Current window width in pixels
            
        Returns:
            Calculated font size
        """
        # Find the appropriate breakpoint
        for i, (breakpoint_width, font_size) in enumerate(FONT_SIZE_BREAKPOINTS):
            if width < breakpoint_width:
                if i == 0:
                    return font_size
                # Interpolate between breakpoints for smooth scaling
                prev_width, prev_size = FONT_SIZE_BREAKPOINTS[i - 1]
                ratio = (width - prev_width) / (breakpoint_width - prev_width)
                return int(prev_size + ratio * (font_size - prev_size))
        # If wider than all breakpoints, use the largest size
        return FONT_SIZE_BREAKPOINTS[-1][1]
    
    def _increase_font(self):
        """Increase font size by user preference."""
        self._user_font_adjustment = min(4, self._user_font_adjustment + 1)
        self._last_resize_width = 0  # Force update
        self._perform_resize(None)
    
    def _decrease_font(self):
        """Decrease font size by user preference."""
        self._user_font_adjustment = max(-4, self._user_font_adjustment - 1)
        self._last_resize_width = 0  # Force update
        self._perform_resize(None)
    
    def _reset_font(self):
        """Reset font size to automatic scaling."""
        self._user_font_adjustment = 0
        self._last_resize_width = 0  # Force update
        self._perform_resize(None)
