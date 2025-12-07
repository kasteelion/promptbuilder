"""Main application window."""

import tkinter as tk
from tkinter import ttk, messagebox
from logic import DataLoader, PromptValidator, PromptGenerator, PromptRandomizer
from themes import ThemeManager
from config import DEFAULT_THEME, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE, PREVIEW_UPDATE_THROTTLE_MS
from .characters_tab import CharactersTab
from .scene_tab import SceneTab
from .notes_tab import NotesTab
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
        self._resize_throttle_ms = 150
        
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
        # Use PanedWindow directly in root to allow resizable left (notebook) and right (preview) panes
        # Drag the sash between them to resize
        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Left side: Notebook with tabs
        self.notebook = ttk.Notebook(paned, style="TNotebook")
        paned.add(self.notebook, weight=0)

        # Create tabs
        self.characters_tab = CharactersTab(
            self.notebook, 
            self.data_loader, 
            self.schedule_preview_update
        )
        self.scene_tab = SceneTab(
            self.notebook, 
            self.data_loader, 
            self.schedule_preview_update
        )
        self.notes_tab = NotesTab(
            self.notebook, 
            self.schedule_preview_update
        )
        self.edit_tab = EditTab(
            self.notebook, 
            self.data_loader, 
            self.reload_data
        )

        # Load data into tabs
        self.characters_tab.load_data(self.characters, self.base_prompts, self.poses)
        self.scene_tab.load_data(self.scenes)

        # Right side: Preview panel
        right_frame = ttk.Frame(paned, style="TFrame")
        paned.add(right_frame, weight=1)
        
        self.preview_panel = PreviewPanel(
            right_frame, 
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
    
    def _set_initial_fonts(self):
        """Set initial fonts on text widgets."""
        font = (DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE)
        for widget in [self.scene_tab.scene_text, 
                      self.notes_tab.notes_text, 
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
        for widget in [self.scene_tab.scene_text, 
                      self.notes_tab.notes_text, 
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
        generator = PromptGenerator(self.characters, self.base_prompts, self.poses)
        
        return generator.generate(
            self.characters_tab.get_selected_characters(),
            self.characters_tab.get_base_prompt_name(),
            self.scene_tab.get_scene_text(),
            self.notes_tab.get_notes_text(),
            outfit_mode=self.preview_panel.get_outfit_mode()
        )
    
    def _generate_prompt_or_error(self):
        """Generate prompt or return validation error.
        
        Returns:
            str: Generated prompt or error message
        """
        error = self._validate_prompt()
        if error:
            return f"--- VALIDATION ERROR ---\n\n{error}"
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
        """Handle window resize for dynamic font sizing.
        
        Args:
            event: Tkinter event
        """
        w = self.root.winfo_width()
        base_size = max(10, min(14, int(w / 70)))
        font_family = DEFAULT_FONT_FAMILY
        new_font = (font_family, base_size)

        # List of all text widgets to apply the new font size
        text_widgets = [
            self.scene_tab.scene_text,
            self.notes_tab.notes_text,
            self.edit_tab.editor_text,
            self.preview_panel.preview_text
        ]

        for widget in text_widgets:
            widget.config(font=new_font)

        # Special handling for preview panel tags
        preview = self.preview_panel.preview_text
        preview.tag_config("bold", font=(font_family, base_size, "bold"))
        preview.tag_config("title", font=(font_family, base_size + 2, "bold"))
        preview.tag_config("error", font=(font_family, base_size, "bold"))
