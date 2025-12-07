# -*- coding: utf-8 -*-
"""Main application window."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from logic import DataLoader, validate_prompt_config, PromptRandomizer
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
    MIN_PANE_WIDTH,
    THEMES,
    TOOLTIPS,
    WELCOME_MESSAGE
)
from utils import UndoManager, PreferencesManager, PresetManager, create_tooltip
from .characters_tab import CharactersTab
from .edit_tab import EditTab
from .preview_panel import PreviewPanel
import sys
import platform


class PromptBuilderApp:
    """Main application class for Prompt Builder."""
    
    def __init__(self, root):
        """Initialize the application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Prompt Builder — Group Picture Generator")
        
        # Initialize managers
        self.undo_manager = UndoManager()
        self.prefs = PreferencesManager()
        self.preset_manager = PresetManager()
        
        # Initialize data
        self.data_loader = DataLoader()
        
        try:
            self.characters = self.data_loader.load_characters()
        except Exception as e:
            self._show_user_friendly_error("Error loading characters", str(e))
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
        self._user_font_adjustment = self.prefs.get("font_adjustment", 0)
        
        # Debounce tracking for text inputs
        self._scene_text_after_id = None
        self._notes_text_after_id = None
        
        # Build UI
        self._build_ui()
        
        # Set initial fonts and theme
        self._set_initial_fonts()
        
        # Auto-detect theme or use saved preference
        theme_to_use = self.prefs.get("last_theme", DEFAULT_THEME)
        if self.prefs.get("auto_theme", False):
            theme_to_use = self._detect_os_theme()
        self._apply_theme(theme_to_use)
        
        # Restore window geometry
        saved_geometry = self.prefs.get("window_geometry")
        if saved_geometry:
            try:
                self.root.geometry(saved_geometry)
            except:
                pass
        
        # Restore last base prompt
        last_base_prompt = self.prefs.get("last_base_prompt")
        if last_base_prompt and last_base_prompt in self.base_prompts:
            self.characters_tab.set_base_prompt(last_base_prompt)
        
        # Initial preview update
        self.update_preview()
        
        # Show welcome dialog for first-time users
        if self.prefs.get("show_welcome", True):
            self._show_welcome_dialog()
        
        # Bind resize event
        self.root.bind("<Configure>", self._on_resize)
        
        # Save state on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _build_ui(self):
        """Build the main UI layout."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Preset...", command=self._save_preset, accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="Load Preset...", command=self._load_preset, accelerator="Ctrl+Shift+O")
        file_menu.add_separator()
        file_menu.add_command(label="Export Configuration...", command=self._export_config)
        file_menu.add_command(label="Import Configuration...", command=self._import_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self._redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear All Characters", command=self._clear_all_characters)
        edit_menu.add_command(label="Reset All Outfits", command=self._reset_all_outfits)
        edit_menu.add_command(label="Apply Same Pose to All", command=self._apply_same_pose_to_all)
        
        # View menu for font controls and theme
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Increase Font Size", command=self._increase_font, accelerator="Ctrl++")
        view_menu.add_command(label="Decrease Font Size", command=self._decrease_font, accelerator="Ctrl+-")
        view_menu.add_command(label="Reset Font Size", command=self._reset_font, accelerator="Ctrl+0")
        view_menu.add_separator()
        
        # Add randomize to view menu
        view_menu.add_command(label="Randomize All", command=self.randomize_all, accelerator="Alt+R")
        view_menu.add_separator()
        
        # Theme submenu
        self.theme_var = tk.StringVar(value=DEFAULT_THEME)
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        for theme_name in THEMES.keys():
            theme_menu.add_radiobutton(
                label=theme_name,
                variable=self.theme_var,
                value=theme_name,
                command=lambda t=theme_name: self._change_theme(t)
            )
        
        # Auto theme checkbox
        view_menu.add_separator()
        self.auto_theme_var = tk.BooleanVar(value=self.prefs.get("auto_theme", False))
        view_menu.add_checkbutton(label="Auto-detect OS Theme", variable=self.auto_theme_var, 
                                  command=self._toggle_auto_theme)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Show Welcome Screen", command=self._show_welcome_dialog)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts_dialog)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about_dialog)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-z>', lambda e: self._undo())
        self.root.bind('<Control-Z>', lambda e: self._undo())
        self.root.bind('<Control-y>', lambda e: self._redo())
        self.root.bind('<Control-Y>', lambda e: self._redo())
        self.root.bind('<Control-Shift-s>', lambda e: self._save_preset())
        self.root.bind('<Control-Shift-S>', lambda e: self._save_preset())
        self.root.bind('<Control-Shift-o>', lambda e: self._load_preset())
        self.root.bind('<Control-Shift-O>', lambda e: self._load_preset())
        self.root.bind('<Control-plus>', lambda e: self._increase_font())
        self.root.bind('<Control-equal>', lambda e: self._increase_font())  # + without shift
        self.root.bind('<Control-minus>', lambda e: self._decrease_font())
        self.root.bind('<Control-0>', lambda e: self._reset_font())
        
        # Bind Alt+R for randomize
        self.root.bind('<Alt-r>', lambda e: self.randomize_all())
        self.root.bind('<Alt-R>', lambda e: self.randomize_all())
        
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
            self.reload_data,
            self._save_state_for_undo
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
        create_tooltip(scene_frame, TOOLTIPS.get("scene", ""))
        
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
        create_tooltip(self.scene_text, TOOLTIPS.get("scene", ""))
        # Debounce scene text changes
        self._scene_text_after_id = None
        def _on_scene_change(e):
            if self._scene_text_after_id:
                self.root.after_cancel(self._scene_text_after_id)
            self._scene_text_after_id = self.root.after(300, self.schedule_preview_update)
        self.scene_text.bind("<KeyRelease>", _on_scene_change)
        
        # Notes section (compact)
        notes_frame = ttk.LabelFrame(right_frame, text="📝 Notes", style="TLabelframe")
        notes_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=2)
        notes_frame.columnconfigure(0, weight=1)
        create_tooltip(notes_frame, TOOLTIPS.get("notes", ""))
        
        self.notes_text = tk.Text(notes_frame, wrap="word", height=2)
        self.notes_text.pack(fill="x", padx=4, pady=4)
        create_tooltip(self.notes_text, TOOLTIPS.get("notes", ""))
        # Debounce notes text changes
        self._notes_text_after_id = None
        def _on_notes_change(e):
            if self._notes_text_after_id:
                self.root.after_cancel(self._notes_text_after_id)
            self._notes_text_after_id = self.root.after(300, self.schedule_preview_update)
        self.notes_text.bind("<KeyRelease>", _on_notes_change)
        
        # Preview panel container
        preview_container = ttk.Frame(right_frame, style="TFrame")
        preview_container.grid(row=2, column=0, sticky="nsew", padx=0, pady=(2, 0))
        
        self.preview_panel = PreviewPanel(
            preview_container, 
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
        
        # Status bar at bottom of right panel
        self.status_bar = ttk.Label(right_frame, text="Ready", relief="sunken", anchor="w", 
                                    style="TLabel", font=("Consolas", 8))
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        
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
    
    def _change_theme(self, theme_name):
        """Handle theme change from menu.
        
        Args:
            theme_name: Name of new theme
        """
        self.theme_var.set(theme_name)
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
        self._update_status("Updating preview...")
    
    def update_preview(self):
        """Update the preview panel with current prompt."""
        prompt = self._generate_prompt_or_error()
        self.preview_panel.update_preview(prompt)
        num_chars = len(self.characters_tab.get_selected_characters())
        self._update_status(f"Ready • {num_chars} character(s) selected")
    
    def _update_status(self, message):
        """Update status bar message.
        
        Args:
            message: Status message to display
        """
        if hasattr(self, 'status_bar'):
            self.status_bar.config(text=message)
    
    def _validate_prompt(self):
        """Validate current prompt data.
        
        Returns:
            str: Error message or None if valid
        """
        selected_chars = self.characters_tab.get_selected_characters()
        return validate_prompt_config(selected_chars)
    
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
            str: Generated prompt or empty string if validation fails
        """
        error = self._validate_prompt()
        if error:
            # Return empty string - preview panel will show welcome message
            return ""
        return self._generate_prompt()
    
    def reload_data(self):
        """Reload all data from markdown files."""
        self._update_status("🔄 Reloading data...")
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            new_characters = self.data_loader.load_characters()
            self.base_prompts = self.data_loader.load_base_prompts()
            self.scenes = self.data_loader.load_presets("scenes.md")
            self.poses = self.data_loader.load_presets("poses.md")
        except Exception as e:
            self.root.config(cursor="")
            self._show_user_friendly_error("Reload Error", str(e))
            self._update_status("❌ Error loading data")
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
        self._update_scene_presets()  # Reload scene presets in UI
        self.edit_tab._refresh_file_list()  # Refresh file list to show new character files
        
        self.root.config(cursor="")
        self.schedule_preview_update()
        self._update_status("✅ Data reloaded successfully")
        messagebox.showinfo("Success", "Data reloaded successfully!")

    def randomize_all(self):
        """Generate a random prompt and update the UI."""
        self._update_status("🎲 Randomizing...")
        self._save_state_for_undo()
        
        config = self.randomizer.randomize(
            num_characters=self.characters_tab.get_num_characters(),
            include_scene=True,
            include_notes=True
        )
        
        self.characters_tab.set_selected_characters(config["selected_characters"])
        self.characters_tab.set_base_prompt(config["base_prompt"])
        
        # Set scene and notes directly
        self.scene_text.delete("1.0", "end")
        self.scene_text.insert("1.0", config.get("scene", ""))
        
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", config.get("notes", ""))
        
        self.schedule_preview_update()
        self._update_status("✨ Randomized successfully")
    
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
        self.prefs.set("font_adjustment", 0)
        self._last_resize_width = 0  # Force update
        self._perform_resize(None)
    
    def _on_closing(self):
        """Handle window closing - save preferences."""
        # Save window geometry
        self.prefs.set("window_geometry", self.root.geometry())
        
        # Save current theme
        self.prefs.set("last_theme", self.theme_var.get())
        
        # Save last base prompt
        base_prompt = self.characters_tab.get_base_prompt_name()
        if base_prompt:
            self.prefs.set("last_base_prompt", base_prompt)
        
        # Save font adjustment
        self.prefs.set("font_adjustment", self._user_font_adjustment)
        
        self.root.destroy()
    
    def _get_current_state(self):
        """Get current application state for undo/redo.
        
        Returns:
            Dictionary of current state
        """
        return {
            "selected_characters": self.characters_tab.get_selected_characters(),
            "base_prompt": self.characters_tab.get_base_prompt_name(),
            "scene": self.scene_text.get("1.0", "end").strip(),
            "notes": self.notes_text.get("1.0", "end").strip()
        }
    
    def _restore_state(self, state):
        """Restore application state from dictionary.
        
        Args:
            state: State dictionary
        """
        if not state:
            return
        
        # Restore characters
        self.characters_tab.set_selected_characters(state.get("selected_characters", []))
        
        # Restore base prompt
        base_prompt = state.get("base_prompt", "")
        if base_prompt:
            self.characters_tab.set_base_prompt(base_prompt)
        
        # Restore scene
        self.scene_text.delete("1.0", "end")
        self.scene_text.insert("1.0", state.get("scene", ""))
        
        # Restore notes
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", state.get("notes", ""))
        
        self.update_preview()
    
    def _save_state_for_undo(self):
        """Save current state for undo."""
        self.undo_manager.save_state(self._get_current_state())
    
    def _undo(self):
        """Undo last action."""
        if not self.undo_manager.can_undo():
            self._update_status("Nothing to undo")
            return
        
        state = self.undo_manager.undo()
        if state:
            self._restore_state(state)
            self._update_status("Undo successful")
    
    def _redo(self):
        """Redo last undone action."""
        if not self.undo_manager.can_redo():
            self._update_status("Nothing to redo")
            return
        
        state = self.undo_manager.redo()
        if state:
            self._restore_state(state)
            self._update_status("Redo successful")
    
    def _save_preset(self):
        """Save current configuration as a preset."""
        # Ask for preset name
        from tkinter import simpledialog
        name = simpledialog.askstring("Save Preset", "Enter preset name:")
        if not name:
            return
        
        config = self._get_current_state()
        try:
            filepath = self.preset_manager.save_preset(name, config)
            self.prefs.add_recent("recent_presets", filepath.name)
            messagebox.showinfo("Success", f"Preset '{name}' saved successfully!")
            self._update_status(f"Preset '{name}' saved")
        except Exception as e:
            self._show_user_friendly_error("Error saving preset", str(e))
    
    def _load_preset(self):
        """Load a preset configuration."""
        presets = self.preset_manager.get_presets()
        if not presets:
            messagebox.showinfo("No Presets", "No saved presets found.")
            return
        
        # Create preset selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Preset")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select a preset to load:", font=("Segoe UI", 10, "bold")).pack(pady=10, padx=10, anchor="w")
        
        # Listbox with presets
        frame = ttk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        for filename, name, created in presets:
            listbox.insert(tk.END, f"{name} ({created[:10]})")
        
        selected_preset = [None]
        
        def on_load():
            selection = listbox.curselection()
            if selection:
                filename = presets[selection[0]][0]
                selected_preset[0] = filename
                dialog.destroy()
        
        def on_delete():
            selection = listbox.curselection()
            if selection:
                filename = presets[selection[0]][0]
                name = presets[selection[0]][1]
                if messagebox.askyesno("Delete Preset", f"Delete preset '{name}'?"):
                    if self.preset_manager.delete_preset(filename):
                        listbox.delete(selection[0])
                        presets.pop(selection[0])
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Load", command=on_load).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Delete", command=on_delete).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=2)
        
        listbox.bind("<Double-Button-1>", lambda e: on_load())
        
        dialog.wait_window()
        
        # Load selected preset
        if selected_preset[0]:
            config = self.preset_manager.load_preset(selected_preset[0])
            if config:
                self._save_state_for_undo()
                self._restore_state(config)
                self._update_status("Preset loaded successfully")
            else:
                self._show_user_friendly_error("Error", "Failed to load preset")
    
    def _export_config(self):
        """Export current configuration to JSON file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Configuration"
        )
        if not filepath:
            return
        
        import json
        config = self._get_current_state()
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Success", "Configuration exported successfully!")
        except Exception as e:
            self._show_user_friendly_error("Export Error", str(e))
    
    def _import_config(self):
        """Import configuration from JSON file."""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Configuration"
        )
        if not filepath:
            return
        
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self._save_state_for_undo()
            self._restore_state(config)
            messagebox.showinfo("Success", "Configuration imported successfully!")
        except Exception as e:
            self._show_user_friendly_error("Import Error", str(e))
    
    def _clear_all_characters(self):
        """Clear all selected characters."""
        if not self.characters_tab.get_selected_characters():
            return
        
        if messagebox.askyesno("Clear All", "Remove all characters from the prompt?"):
            self._save_state_for_undo()
            self.characters_tab.set_selected_characters([])
            self._update_status("All characters cleared")
    
    def _reset_all_outfits(self):
        """Reset all characters to their base/first outfit."""
        characters = self.characters_tab.get_selected_characters()
        if not characters:
            return
        
        if messagebox.askyesno("Reset Outfits", "Reset all characters to their default outfit?"):
            self._save_state_for_undo()
            for char in characters:
                char_def = self.characters.get(char['name'], {})
                outfits = char_def.get('outfits', {})
                if 'Base' in outfits:
                    char['outfit'] = 'Base'
                elif outfits:
                    char['outfit'] = sorted(list(outfits.keys()))[0]
            self.characters_tab.set_selected_characters(characters)
            self._update_status("All outfits reset to default")
    
    def _apply_same_pose_to_all(self):
        """Apply same pose to all characters."""
        characters = self.characters_tab.get_selected_characters()
        if not characters:
            return
        
        # Create dialog to select pose
        dialog = tk.Toplevel(self.root)
        dialog.title("Apply Pose to All")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select pose to apply to all characters:", font=("Segoe UI", 10, "bold")).pack(pady=10, padx=10)
        
        frame = ttk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ttk.Label(frame, text="Category:").grid(row=0, column=0, sticky="w", pady=5)
        cat_var = tk.StringVar()
        cat_combo = ttk.Combobox(frame, textvariable=cat_var, state="readonly", width=20)
        cat_combo['values'] = [""] + sorted(list(self.poses.keys()))
        cat_combo.grid(row=0, column=1, sticky="ew", pady=5, padx=(5, 0))
        
        ttk.Label(frame, text="Preset:").grid(row=1, column=0, sticky="w", pady=5)
        preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(frame, textvariable=preset_var, state="readonly", width=20)
        preset_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=(5, 0))
        
        def update_presets(e=None):
            cat = cat_var.get()
            if cat and cat in self.poses:
                preset_combo['values'] = [""] + sorted(list(self.poses[cat].keys()))
            else:
                preset_combo['values'] = [""]
            preset_var.set("")
        
        cat_combo.bind("<<ComboboxSelected>>", update_presets)
        
        frame.columnconfigure(1, weight=1)
        
        def apply_pose():
            cat = cat_var.get()
            preset = preset_var.get()
            if cat or preset:
                self._save_state_for_undo()
                for char in characters:
                    char['pose_category'] = cat
                    char['pose_preset'] = preset
                self.characters_tab.set_selected_characters(characters)
                self._update_status(f"Applied pose to {len(characters)} character(s)")
                dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Apply", command=apply_pose).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=2)
        
        dialog.wait_window()
    
    def _detect_os_theme(self):
        """Detect OS theme preference.
        
        Returns:
            Theme name based on OS settings
        """
        try:
            if platform.system() == "Windows":
                import winreg
                try:
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    winreg.CloseKey(key)
                    return "Light" if value == 1 else "Dark"
                except:
                    pass
            elif platform.system() == "Darwin":  # macOS
                import subprocess
                result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], 
                                      capture_output=True, text=True)
                return "Light" if result.returncode != 0 else "Dark"
        except:
            pass
        
        return DEFAULT_THEME
    
    def _toggle_auto_theme(self):
        """Toggle auto theme detection."""
        auto = self.auto_theme_var.get()
        self.prefs.set("auto_theme", auto)
        if auto:
            detected_theme = self._detect_os_theme()
            self._change_theme(detected_theme)
            self._update_status(f"Auto-detected theme: {detected_theme}")
    
    def _show_welcome_dialog(self):
        """Show welcome dialog for first-time users."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Welcome to Prompt Builder!")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Welcome text
        from tkinter import scrolledtext
        text = scrolledtext.ScrolledText(dialog, wrap="word", font=("Segoe UI", 10))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", WELCOME_MESSAGE)
        text.config(state="disabled")
        
        # Don't show again checkbox
        show_again_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(dialog, text="Don't show this again", variable=show_again_var)
        chk.pack(pady=(0, 10))
        
        def on_close():
            if show_again_var.get():
                self.prefs.set("show_welcome", False)
            dialog.destroy()
        
        ttk.Button(dialog, text="Get Started!", command=on_close).pack(pady=(0, 10))
        
        dialog.wait_window()
    
    def _show_shortcuts_dialog(self):
        """Show keyboard shortcuts dialog."""
        shortcuts = """
Keyboard Shortcuts

File Operations:
  Ctrl+Shift+S    Save Preset
  Ctrl+Shift+O    Load Preset

Editing:
  Ctrl+Z          Undo
  Ctrl+Y          Redo

View:
  Ctrl++          Increase Font Size
  Ctrl+-          Decrease Font Size
  Ctrl+0          Reset Font Size
  Alt+R           Randomize All

Preview Panel:
  Ctrl+C          Copy Prompt
  Ctrl+S          Save Prompt to File

Navigation:
  Tab             Navigate between fields
  Enter           Add character/Apply selection
  Del             Remove selected character
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def _show_about_dialog(self):
        """Show about dialog."""
        about_text = f"""Prompt Builder
Version 2.0

A desktop application for building complex AI image prompts.

Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}
Platform: {platform.system()} {platform.release()}

© 2025 - Open Source
"""
        messagebox.showinfo("About Prompt Builder", about_text)
    
    def _show_user_friendly_error(self, title, error_msg):
        """Show user-friendly error message.
        
        Args:
            title: Error dialog title
            error_msg: Error message
        """
        # Convert technical errors to user-friendly messages
        friendly_msg = error_msg
        
        if "FileNotFoundError" in error_msg or "No such file" in error_msg:
            friendly_msg = "File not found. Try clicking 'Reload Data' from the menu."
        elif "PermissionError" in error_msg:
            friendly_msg = "Permission denied. Check file permissions and try again."
        elif "JSONDecodeError" in error_msg:
            friendly_msg = "Invalid file format. The file may be corrupted."
        elif "characters/" in error_msg:
            friendly_msg = "Error loading character files. Check the characters folder."
        
        messagebox.showerror(title, friendly_msg)
        self._update_status(f"Error: {title}")

