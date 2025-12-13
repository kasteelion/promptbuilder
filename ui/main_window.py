# -*- coding: utf-8 -*-
"""Main application window."""

import platform
import tkinter as tk
from tkinter import ttk
from typing import Optional

from config import DEFAULT_THEME, TOOLTIPS
from core.builder import PromptBuilder
from logic import DataLoader, PromptRandomizer, validate_prompt_config
from themes import ThemeManager
from utils import PreferencesManager, create_tooltip, logger
from utils.interaction_helpers import fill_template

from .character_card import CharacterGalleryPanel
from .characters_tab import CharactersTab
from .constants import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE, PREVIEW_UPDATE_THROTTLE_MS
from .controllers.gallery import GalleryController
from .controllers.menu_actions import MenuActions
from .controllers.window_state import WindowStateController
from .dialog_manager import DialogManager
from .edit_tab import EditTab
from .font_manager import FontManager
from .menu_manager import MenuManager
from .preview_controller import PreviewController
from .preview_panel import PreviewPanel
from .state_manager import StateManager


class PromptBuilderApp:
    """Main application class for Prompt Builder."""

    def __init__(self, root: tk.Tk):
        """Initialize the application.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Prompt Builder — Group Picture Generator")

        # Hide window during setup to prevent flickering/resizing
        self.root.withdraw()

        # Initialize preferences first
        self.prefs = PreferencesManager()

        # Initialize managers (font and state managers will be set up after UI)
        self.font_manager: Optional[FontManager] = None
        self.state_manager: Optional[StateManager] = None
        self.menu_manager: Optional[MenuManager] = None
        self.dialog_manager = DialogManager(self.root, self.prefs)

        # Initialize data
        self.data_loader = DataLoader()

        try:
            self.characters = self.data_loader.load_characters()
        except Exception:
            logger.exception("Error loading characters")
            # Show a concise message to the user and exit
            self.dialog_manager.show_error(
                "Error loading characters", "Failed to load character data; see log for details."
            )
            self.root.destroy()
            return

        self.base_prompts = self.data_loader.load_base_prompts()
        self.scenes = self.data_loader.load_presets("scenes.md")
        self.poses = self.data_loader.load_presets("poses.md")
        self.interactions = self.data_loader.load_interactions()
        self.randomizer = PromptRandomizer(
            self.characters, self.base_prompts, self.poses, self.scenes, self.interactions
        )

        # Initialize theme manager
        self.style = ttk.Style()
        self.theme_manager = ThemeManager(self.root, self.style)
        # Toast manager for transient notifications
        from .toast import ToastManager

        self.toasts = ToastManager(self.root, self.theme_manager)

        # Throttling for preview updates
        self._after_id: Optional[str] = None
        self._throttle_ms = PREVIEW_UPDATE_THROTTLE_MS

        # Debounce tracking for text inputs
        self._scene_text_after_id: Optional[str] = None
        self._notes_text_after_id: Optional[str] = None
        # Preview controller (created after UI initialization)
        self.preview_controller: Optional[PreviewController] = None

        # Build UI
        self._build_ui()

        # Initialize managers that depend on UI elements
        self._initialize_managers()

        # Create preview controller after UI elements are ready
        try:
            # Will be re-assigned in _initialize_managers once preview_panel exists
            self.preview_controller = None
        except Exception:
            logger.exception("Failed to initialize preview controller placeholder")

        # Bind keyboard shortcuts
        self._bind_keyboard_shortcuts()

        # Set initial fonts and theme
        self._set_initial_fonts()

        # Auto-detect theme or use saved preference
        theme_to_use = self.prefs.get("last_theme", DEFAULT_THEME)
        if self.prefs.get("auto_theme", False):
            theme_to_use = self._detect_os_theme()
        self._apply_theme(theme_to_use)

        # Restore window geometry and state via WindowStateController
        try:
            self.window_state_controller = WindowStateController(self)
            restored = self.window_state_controller.restore_geometry_and_state()
            saved_geometry = None if not restored else self.prefs.get("window_geometry")
            saved_state = self.prefs.get("window_state")
        except Exception:
            logger.exception("Failed to initialize WindowStateController")
            saved_geometry = None
            saved_state = None

        # Restore last base prompt
        last_base_prompt = self.prefs.get("last_base_prompt")
        if last_base_prompt and last_base_prompt in self.base_prompts:
            self.characters_tab.set_base_prompt(last_base_prompt)

        # Load characters into gallery
        self.character_gallery.load_characters(self.characters)

        # Initial preview update
        self.update_preview()

        # Position window properly BEFORE showing (center if first run, else already set)
        if not saved_geometry:
            self._center_window()

        # Now show the window after everything is set up and positioned
        self.root.deiconify()

        # Restore window state AFTER deiconify (maximized/zoomed state)
        if saved_state and saved_state in ("zoomed", "normal", "iconic"):
            try:
                self.root.state(saved_state)
            except tk.TclError as e:
                logger.warning(f"Could not restore window state: {e}")

        # Show welcome dialog for first-time users (after window is shown)
        if self.prefs.get("show_welcome", True):
            self.root.after(100, self.dialog_manager.show_welcome)

        # Save state on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self):
        """Build the main UI layout."""
        # Create menu manager with callbacks
        # Create menu manager with callbacks provided by MenuActions controller
        self.menu_actions = MenuActions(self)
        menu_callbacks = {
            "save_preset": self.menu_actions.save_preset,
            "load_preset": self.menu_actions.load_preset,
            "export_config": self.menu_actions.export_config,
            "import_config": self.menu_actions.import_config,
            "undo": self.menu_actions.undo,
            "redo": self.menu_actions.redo,
            "clear_all_characters": self.menu_actions.clear_all_characters,
            "reset_all_outfits": self.menu_actions.reset_all_outfits,
            "apply_same_pose_to_all": self.menu_actions.apply_same_pose_to_all,
            "toggle_character_gallery": self.menu_actions.toggle_character_gallery,
            "increase_font": self.menu_actions.increase_font,
            "decrease_font": self.menu_actions.decrease_font,
            "reset_font": self.menu_actions.reset_font,
            "randomize_all": self.menu_actions.randomize_all,
            "change_theme": self.menu_actions.change_theme,
            "toggle_auto_theme": self.menu_actions.toggle_auto_theme,
            "show_characters_summary": self.menu_actions.show_characters_summary,
            "show_welcome": self.menu_actions.show_welcome,
            "show_shortcuts": self.menu_actions.show_shortcuts,
            "show_about": self.menu_actions.show_about,
            "on_closing": self.menu_actions.on_closing,
            "initial_theme": self.prefs.get("last_theme", DEFAULT_THEME),
            "auto_theme_enabled": self.prefs.get("auto_theme", False),
            "gallery_visible": self.prefs.get("gallery_visible", True),
        }

        self.menu_manager = MenuManager(self.root, menu_callbacks)

        # Bind keyboard shortcuts
        self._bind_keyboard_shortcuts()

        # Main container with optional character gallery
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True)

        # Create a paned window for gallery + main content
        self.main_paned = ttk.PanedWindow(main_container, orient="horizontal")
        self.main_paned.pack(fill="both", expand=True)

        # Left side: Character Gallery (collapsible, starts visible by default)
        self.gallery_frame = ttk.Frame(self.main_paned, style="TFrame", width=280)
        self.gallery_visible = self.prefs.get("gallery_visible", True)

        self.character_gallery = CharacterGalleryPanel(
            self.gallery_frame,
            self.data_loader,
            on_add_callback=self._on_gallery_character_selected,
            theme_colors=self.theme_manager.themes.get(DEFAULT_THEME, {}),
        )
        self.character_gallery.pack(fill="both", expand=True)

        if self.gallery_visible:
            self.main_paned.add(self.gallery_frame, weight=2)

        # Use PanedWindow directly for main content to allow resizable left (notebook) and right (preview) panes
        # Drag the sash between them to resize
        paned = ttk.PanedWindow(self.main_paned, orient="horizontal")
        self.main_paned.add(paned, weight=15)

        # Left side: Notebook with tabs (give it more weight for better visibility)
        self.notebook = ttk.Notebook(paned, style="TNotebook")
        paned.add(self.notebook, weight=5)

        # Create tabs
        self.characters_tab = CharactersTab(
            self.notebook,
            self.data_loader,
            self.schedule_preview_update,
            self.reload_data,
            self._save_state_for_undo,
        )
        self.edit_tab = EditTab(self.notebook, self.data_loader, self.reload_data)

        # Load data into tabs
        self.characters_tab.load_data(self.characters, self.base_prompts, self.poses, self.scenes)

        # Right side: Preview panel
        right_frame = ttk.Frame(paned, style="TFrame")
        paned.add(right_frame, weight=4)
        right_frame.rowconfigure(1, weight=1)  # Notes section gets expanding space
        right_frame.rowconfigure(2, weight=3)  # Preview gets most expanding space
        right_frame.columnconfigure(0, weight=1)

        # Scene section (compact)
        scene_frame = ttk.LabelFrame(right_frame, text="🎬 Scene", style="TLabelframe")
        scene_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        scene_frame.columnconfigure(1, weight=1)
        create_tooltip(scene_frame, TOOLTIPS.get("scene", ""))

        # Scene presets row
        ttk.Label(scene_frame, text="Category:", font=("Consolas", 9)).grid(
            row=0, column=0, sticky="w", padx=(4, 2), pady=2
        )
        self.scene_category_var = tk.StringVar()
        self.scene_cat_combo = ttk.Combobox(
            scene_frame, textvariable=self.scene_category_var, state="readonly", width=10
        )
        self.scene_cat_combo.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        self.scene_cat_combo.bind("<<ComboboxSelected>>", lambda e: self._update_scene_presets())

        ttk.Label(scene_frame, text="Preset:", font=("Consolas", 9)).grid(
            row=0, column=2, sticky="w", padx=(8, 2), pady=2
        )
        self.scene_preset_var = tk.StringVar()
        self.scene_combo = ttk.Combobox(
            scene_frame, textvariable=self.scene_preset_var, state="readonly", width=15
        )
        self.scene_combo.grid(row=0, column=3, sticky="ew", padx=2, pady=2)
        self.scene_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_scene_preset())

        ttk.Button(scene_frame, text="✨", width=3, command=self._create_new_scene).grid(
            row=0, column=4, padx=(4, 4), pady=2
        )

        self.scene_text = tk.Text(scene_frame, wrap="word", height=3)
        self.scene_text.grid(row=1, column=0, columnspan=5, sticky="ew", padx=4, pady=(0, 4))
        create_tooltip(self.scene_text, TOOLTIPS.get("scene", ""))
        # Debounce scene text changes
        self._scene_text_after_id = None

        def _on_scene_change(e):
            if self._scene_text_after_id:
                self.root.after_cancel(self._scene_text_after_id)
            self._scene_text_after_id = self.root.after(300, self.schedule_preview_update)

        self.scene_text.bind("<KeyRelease>", _on_scene_change)

        # Notes section (expandable)
        notes_frame = ttk.LabelFrame(
            right_frame, text="📝 Notes & Interactions", style="TLabelframe"
        )
        notes_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        notes_frame.columnconfigure(0, weight=1)
        notes_frame.rowconfigure(1, weight=1)
        create_tooltip(notes_frame, TOOLTIPS.get("notes", ""))

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
            width=15,
        )
        self.interaction_cat_combo.grid(row=0, column=1, sticky="w", padx=(0, 8))
        self.interaction_cat_combo.bind(
            "<<ComboboxSelected>>", lambda e: self._update_interaction_presets()
        )
        create_tooltip(self.interaction_cat_combo, "Choose interaction category")

        ttk.Label(interaction_control, text="Template:", style="TLabel").grid(
            row=0, column=2, sticky="w", padx=(0, 4)
        )

        self.interaction_var = tk.StringVar(value="Blank")
        self.interaction_combo = ttk.Combobox(
            interaction_control, textvariable=self.interaction_var, state="readonly"
        )
        self.interaction_combo.grid(row=0, column=3, sticky="ew")
        create_tooltip(self.interaction_combo, "Choose a multi-character interaction template")

        insert_btn = ttk.Button(
            interaction_control, text="Insert", command=self._insert_interaction_template
        )
        insert_btn.grid(row=0, column=4, padx=(4, 0))
        create_tooltip(insert_btn, "Insert template with selected characters")

        refresh_btn = ttk.Button(
            interaction_control, text="🔄", command=self._refresh_interaction_template, width=3
        )
        refresh_btn.grid(row=0, column=5, padx=(4, 0))
        create_tooltip(refresh_btn, "Re-fill template with current characters")

        create_btn = ttk.Button(
            interaction_control, text="+ Create", command=self._create_new_interaction
        )
        create_btn.grid(row=0, column=6, padx=(4, 0))
        create_tooltip(create_btn, "Create a new interaction template")

        self.notes_text = tk.Text(notes_frame, wrap="word", height=4)
        self.notes_text.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 4))
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
            self.randomize_all,
            status_callback=self._update_status,
            clear_callback=self._clear_interface,
            toast_callback=getattr(self, "toasts").notify,
        )

        # Set preview callbacks
        self.preview_panel.set_callbacks(
            self._generate_prompt, self._validate_prompt, self.randomize_all
        )

        # Status bar at bottom of right panel (slightly larger for readability)
        self.status_bar = ttk.Label(
            right_frame,
            text="Ready",
            relief="sunken",
            anchor="w",
            style="TLabel",
            font=("Consolas", 10),
        )
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=0, pady=(4, 2))

        # Initialize scene presets
        self._update_scene_presets()

    def _initialize_managers(self):
        """Initialize managers that depend on UI elements."""
        # Initialize font manager
        self.font_manager = FontManager(self.root, self.prefs)

        # Register text widgets for font management
        for widget in [
            self.scene_text,
            self.notes_text,
            self.preview_panel.preview_text,
            self.edit_tab.editor_text,
        ]:
            self.font_manager.register_widget(widget)

        # Initialize state manager
        self.state_manager = StateManager(self.root, self.prefs)
        self.state_manager.set_callbacks(
            get_state=self._get_current_state,
            restore_state=self._restore_state,
            update_preview=self.schedule_preview_update,
        )

        # Initialize interaction category combo
        categories = list(self.interactions.keys())
        self.interaction_cat_combo["values"] = categories
        if categories:
            self.interaction_category_var.set(categories[0])
            self._update_interaction_presets()

        # Create preview controller now that preview_panel and characters_tab exist
        try:
            self.preview_controller = PreviewController(
                self.root,
                self.preview_panel,
                self._generate_prompt_or_error,
                lambda: len(self.characters_tab.get_selected_characters()),
                throttle_ms=self._throttle_ms,
            )
        except Exception:
            logger.exception("Failed to create PreviewController")
        # Initialize gallery controller to encapsulate gallery behaviors
        try:
            self.gallery_controller = GalleryController(self)
        except Exception:
            logger.exception("Failed to create GalleryController")

    def _bind_keyboard_shortcuts(self):
        """Bind all keyboard shortcuts."""
        shortcuts = [
            ("<Control-z>", self._undo),
            ("<Control-Z>", self._undo),
            ("<Control-y>", self._redo),
            ("<Control-Y>", self._redo),
            ("<Control-Shift-s>", self._save_preset),
            ("<Control-Shift-S>", self._save_preset),
            ("<Control-Shift-o>", self._load_preset),
            ("<Control-Shift-O>", self._load_preset),
            ("<Control-plus>", self._increase_font),
            ("<Control-equal>", self._increase_font),  # + without shift
            ("<Control-minus>", self._decrease_font),
            ("<Control-0>", self._reset_font),
            ("<Alt-r>", lambda e: self.randomize_all()),
            ("<Alt-R>", lambda e: self.randomize_all()),
            ("<Control-g>", lambda e: self._toggle_character_gallery()),
            ("<Control-G>", lambda e: self._toggle_character_gallery()),
        ]

        for key, handler in shortcuts:
            # Wrap handlers that don't expect an event
            if callable(handler) and handler.__name__ in [
                "_increase_font",
                "_decrease_font",
                "_reset_font",
            ]:
                self.root.bind(key, lambda e, h=handler: h())
            else:
                self.root.bind(key, lambda e, h=handler: h())

    def _update_scene_presets(self):
        """Update scene preset combo based on selected category."""
        cat = self.scene_category_var.get()
        if cat and cat in self.scenes:
            self.scene_combo["values"] = [""] + sorted(list(self.scenes[cat].keys()))
        else:
            self.scene_combo["values"] = [""]
        self.scene_preset_var.set("")

        # Update category combo values
        self.scene_cat_combo["values"] = [""] + sorted(list(self.scenes.keys()))

        # Force both combos to refresh their display
        self.scene_cat_combo.selection_clear()
        self.scene_combo.selection_clear()
        self.root.update_idletasks()

    def _update_interaction_presets(self):
        """Update interaction preset combo based on selected category."""
        cat = self.interaction_category_var.get()
        if cat and cat in self.interactions:
            self.interaction_combo["values"] = [""] + sorted(list(self.interactions[cat].keys()))
        else:
            self.interaction_combo["values"] = [""]
        self.interaction_var.set("")

        # Update category combo values
        self.interaction_cat_combo["values"] = [""] + sorted(list(self.interactions.keys()))

        # Force both combos to refresh their display
        self.interaction_cat_combo.selection_clear()
        self.interaction_combo.selection_clear()
        self.root.update_idletasks()

    def _insert_interaction_template(self):
        """Insert interaction template with character placeholders filled."""
        cat = self.interaction_category_var.get()
        template_name = self.interaction_var.get()

        if not cat or not template_name:
            return

        if cat not in self.interactions or template_name not in self.interactions[cat]:
            return

        template_text = self.interactions[cat][template_name]

        if not template_text:
            return

        # Get list of selected character names from characters tab
        selected_chars = [char["name"] for char in self.characters_tab.selected_characters]

        if not selected_chars:
            from utils.notification import notify

            root = self.root
            msg = "Please add characters to your prompt first before using interaction templates."
            notify(root, "No Characters", msg, level="info", duration=3000, parent=self.root)
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
            self._update_status(f"Inserted: {template_name}")
        except tk.TclError:
            logger.exception("Error inserting interaction template")

    def _refresh_interaction_template(self):
        """Replace notes with re-filled interaction template using current characters."""
        cat = self.interaction_category_var.get()
        template_name = self.interaction_var.get()

        if not cat or not template_name:
            return

        if cat not in self.interactions or template_name not in self.interactions[cat]:
            return

        template_text = self.interactions[cat][template_name]

        if not template_text:
            return

        # Get list of selected character names from characters tab
        selected_chars = [char["name"] for char in self.characters_tab.selected_characters]

        if not selected_chars:
            from utils.notification import notify

            root = self.root
            msg = "Please add characters to your prompt first before using interaction templates."
            notify(root, "No Characters", msg, level="info", duration=3000, parent=self.root)
            return

        # Fill template with character names
        filled_text = fill_template(template_text, selected_chars)

        # Replace notes content
        try:
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", filled_text)

            self.schedule_preview_update()
            self._update_status(f"Refreshed: {template_name}")
        except tk.TclError:
            logger.exception("Error refreshing interaction template")

    def _apply_scene_preset(self):
        """Apply selected scene preset to text area."""
        cat = self.scene_category_var.get()
        name = self.scene_preset_var.get()

        if cat and name and cat in self.scenes and name in self.scenes[cat]:
            self.scene_text.delete("1.0", "end")
            self.scene_text.insert("1.0", self.scenes[cat][name])
            self.schedule_preview_update()

    def _reload_interaction_templates(self):
        """Reload interaction templates from file."""
        try:
            # Reload interactions from markdown file
            self.interactions = self.data_loader.load_interactions()

            # Update category combo
            categories = list(self.interactions.keys())
            self.interaction_cat_combo["values"] = categories

            # Keep current category if it exists, otherwise select first
            current_cat = self.interaction_category_var.get()
            if current_cat not in self.interactions and categories:
                self.interaction_category_var.set(categories[0])

            # Update template dropdown based on category
            self._update_interaction_presets()

            logger.info("Interaction templates reloaded successfully")
        except Exception:
            logger.exception("Error reloading interaction templates")

    def _create_new_interaction(self):
        """Open dialog to create a new interaction template."""
        from .interaction_creator import InteractionCreatorDialog

        dialog = InteractionCreatorDialog(
            self.root, self.data_loader, self._reload_interaction_templates
        )
        dialog.show()

    def _create_new_scene(self):
        """Open dialog to create a new scene."""
        from .scene_creator import SceneCreatorDialog

        dialog = SceneCreatorDialog(self.root, self.data_loader, self.reload_data)
        dialog.show()

    def _set_initial_fonts(self):
        """Set initial fonts on text widgets."""
        font = (DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE)
        for widget in [
            self.scene_text,
            self.notes_text,
            self.preview_panel.preview_text,
            self.edit_tab.editor_text,
        ]:
            widget.config(padx=10, pady=10, font=font)

    def _change_theme(self, theme_name):
        """Handle theme change from menu.

        Args:
            theme_name: Name of new theme
        """
        if hasattr(self, "menu_manager") and self.menu_manager:
            self.menu_manager.set_theme(theme_name)
        self._apply_theme(theme_name)

    def _apply_theme(self, theme_name):
        """Apply theme to all UI elements.

        Args:
            theme_name: Name of theme to apply
        """
        theme = self.theme_manager.apply_theme(theme_name)

        # Apply to text widgets
        self.theme_manager.apply_preview_theme(self.preview_panel.preview_text, theme)
        for widget in [self.scene_text, self.notes_text, self.edit_tab.editor_text]:
            self.theme_manager.apply_text_widget_theme(widget, theme)

        # Apply to canvas
        self.theme_manager.apply_canvas_theme(self.characters_tab.chars_canvas, theme)

        # Apply to dynamic character action texts
        self.characters_tab.apply_theme_to_action_texts(self.theme_manager, theme)

        # Apply to character gallery (use controller if available)
        if hasattr(self, "gallery_controller") and self.gallery_controller:
            try:
                self.gallery_controller.apply_theme(theme)
            except Exception:
                logger.exception("Failed to apply theme via GalleryController")
        elif hasattr(self, "character_gallery"):
            try:
                self.character_gallery.theme_colors = theme
                self.character_gallery._refresh_display()
            except Exception:
                logger.exception("Failed to apply theme to character_gallery")

        # Apply theme to toasts
        if hasattr(self, "toasts"):
            try:
                self.toasts.apply_theme(theme)
            except Exception:
                from utils import logger as _logger

                _logger.debug("Failed to apply theme to toasts", exc_info=True)

    def schedule_preview_update(self):
        """Schedule a preview update with adaptive throttling."""
        # Adaptive throttling - faster for simpler prompts
        num_chars = len(self.characters_tab.get_selected_characters())
        delay = 50 if num_chars <= 2 else self._throttle_ms

        if self.preview_controller:
            try:
                self.preview_controller.schedule_update(delay)
            except Exception:
                logger.exception("Failed to schedule preview update via controller")
        else:
            # Fallback: do synchronous update after delay
            try:
                self.root.after(delay, lambda: self.update_preview())
            except Exception:
                logger.exception("Failed to schedule synchronous preview update")

    # Preview submission is handled by PreviewController now.

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
        if hasattr(self, "status_bar"):
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
            "notes": self.notes_text.get("1.0", "end").strip(),
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
            self._reload_interaction_templates()
        except Exception:
            logger.exception("Error reloading data")
            self.root.config(cursor="")
            self.dialog_manager.show_error(
                "Reload Error", "Failed to reload data; see log for details"
            )
            self._update_status("❌ Error loading data")
            return

        # Update character selection validity
        new_chars_keys = set(new_characters.keys())
        selected = self.characters_tab.get_selected_characters()
        updated_selected = []
        chars_removed = False

        for c in selected:
            if c["name"] in new_chars_keys:
                c.setdefault("pose_category", "")
                c.setdefault("pose_preset", "")
                c.setdefault("action_note", "")
                updated_selected.append(c)
            else:
                chars_removed = True

        self.characters = new_characters
        self.characters_tab.selected_characters = updated_selected

        if chars_removed:
            self.dialog_manager.show_info(
                "Reload Info",
                "Some previously selected characters were removed as they no longer exist in the updated data.",
            )

        # Reload data in tabs
        self.characters_tab.load_data(self.characters, self.base_prompts, self.poses)
        self._update_scene_presets()  # Reload scene presets in UI
        self.edit_tab._refresh_file_list()  # Refresh file list to show new character files

        # Reload character gallery
        if hasattr(self, "gallery_controller") and self.gallery_controller:
            try:
                self.gallery_controller.load_characters(self.characters)
            except Exception:
                logger.exception("Failed to reload gallery via GalleryController")
        elif hasattr(self, "character_gallery"):
            try:
                self.character_gallery.load_characters(self.characters)
            except Exception:
                logger.exception("Failed to reload character_gallery")

        self.root.config(cursor="")
        self.schedule_preview_update()
        self._update_status("✅ Data reloaded successfully")
        self.dialog_manager.show_info("Success", "Data reloaded successfully!")

    def randomize_all(self):
        """Generate a random prompt and update the UI."""
        self._update_status("🎲 Randomizing...")
        self._save_state_for_undo()

        config = self.randomizer.randomize(
            num_characters=self.characters_tab.get_num_characters(),
            include_scene=True,
            include_notes=True,
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

    def _center_window(self):
        """Center the window on the screen using current geometry."""
        # Get current geometry string (e.g., "1000x700")
        geom = self.root.geometry()
        # Parse width and height
        if "x" in geom:
            dims = geom.split("+")[0]  # Get "1000x700" part
            width, height = map(int, dims.split("x"))
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _increase_font(self):
        """Increase font size by user preference."""
        self.font_manager.increase_font_size()

    def _decrease_font(self):
        """Decrease font size by user preference."""
        self.font_manager.decrease_font_size()

    def _reset_font(self):
        """Reset font size to automatic scaling."""
        self.font_manager.reset_font_size()

    def _on_closing(self):
        """Handle window closing - save preferences."""
        # Save window state (normal/zoomed/iconic)
        window_state = self.root.state()
        self.prefs.set("window_state", window_state)

        # Save window geometry
        self.prefs.set("window_geometry", self.root.geometry())

        # Save current theme
        if hasattr(self, "menu_manager") and self.menu_manager:
            self.prefs.set("last_theme", self.menu_manager.get_theme())

        # Save last base prompt
        base_prompt = self.characters_tab.get_base_prompt_name()
        if base_prompt:
            self.prefs.set("last_base_prompt", base_prompt)

        # Shutdown preview controller if present
        try:
            if self.preview_controller:
                self.preview_controller.shutdown()
        except Exception:
            logger.exception("Error shutting down preview controller")

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
            "notes": self.notes_text.get("1.0", "end").strip(),
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
        self.state_manager.save_state_for_undo()

    def _undo(self):
        """Undo last action."""
        success = self.state_manager.undo()
        if success:
            self._update_status("Undo successful")
        else:
            self._update_status("Nothing to undo")

    def _redo(self):
        """Redo last undone action."""
        success = self.state_manager.redo()
        if success:
            self._update_status("Redo successful")
        else:
            self._update_status("Nothing to redo")

    def _save_preset(self):
        """Save current configuration as a preset."""
        success = self.state_manager.save_preset()
        if success:
            self._update_status("Preset saved")

    def _load_preset(self):
        """Load a preset configuration."""
        success = self.state_manager.load_preset()
        if success:
            self._update_status("Preset loaded successfully")

    def _export_config(self):
        """Export current configuration to JSON file."""
        self.state_manager.export_config()

    def _import_config(self):
        """Import configuration from JSON file."""
        success = self.state_manager.import_config()
        if success:
            self._update_status("Configuration imported successfully")

    def _clear_all_characters(self):
        """Clear all selected characters."""
        if not self.characters_tab.get_selected_characters():
            return

        if self.dialog_manager.ask_yes_no("Clear All", "Remove all characters from the prompt?"):
            self._save_state_for_undo()
            self.characters_tab.set_selected_characters([])
            self._update_status("All characters cleared")

    def _reset_all_outfits(self):
        """Reset all characters to their base/first outfit."""
        characters = self.characters_tab.get_selected_characters()
        if not characters:
            return

        if self.dialog_manager.ask_yes_no(
            "Reset Outfits", "Reset all characters to their default outfit?"
        ):
            self._save_state_for_undo()
            for char in characters:
                char_def = self.characters.get(char["name"], {})
                outfits = char_def.get("outfits", {})
                if "Base" in outfits:
                    char["outfit"] = "Base"
                elif outfits:
                    char["outfit"] = sorted(list(outfits.keys()))[0]
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

        ttk.Label(
            dialog, text="Select pose to apply to all characters:", font=("Segoe UI", 10, "bold")
        ).pack(pady=10, padx=10)

        frame = ttk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Category:").grid(row=0, column=0, sticky="w", pady=5)
        cat_var = tk.StringVar()
        cat_combo = ttk.Combobox(frame, textvariable=cat_var, state="readonly", width=20)
        cat_combo["values"] = [""] + sorted(list(self.poses.keys()))
        cat_combo.grid(row=0, column=1, sticky="ew", pady=5, padx=(5, 0))

        ttk.Label(frame, text="Preset:").grid(row=1, column=0, sticky="w", pady=5)
        preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(frame, textvariable=preset_var, state="readonly", width=20)
        preset_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=(5, 0))

        def update_presets(e=None):
            cat = cat_var.get()
            if cat and cat in self.poses:
                preset_combo["values"] = [""] + sorted(list(self.poses[cat].keys()))
            else:
                preset_combo["values"] = [""]
            preset_var.set("")
            # Force display refresh
            cat_combo.selection_clear()
            preset_combo.selection_clear()
            dialog.update_idletasks()

        cat_combo.bind("<<ComboboxSelected>>", update_presets)

        frame.columnconfigure(1, weight=1)

        def apply_pose():
            cat = cat_var.get()
            preset = preset_var.get()
            if cat or preset:
                self._save_state_for_undo()
                for char in characters:
                    char["pose_category"] = cat
                    char["pose_preset"] = preset
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
                    key = winreg.OpenKey(
                        registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                    )
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    winreg.CloseKey(key)
                    return "Light" if value == 1 else "Dark"
                except (OSError, FileNotFoundError) as e:
                    logger.debug(f"Could not read Windows theme registry: {e}")
            elif platform.system() == "Darwin":  # macOS
                import subprocess

                try:
                    result = subprocess.run(
                        ["defaults", "read", "-g", "AppleInterfaceStyle"],
                        capture_output=True,
                        text=True,
                        timeout=2.0,  # 2 second timeout
                        check=False,  # Don't raise on non-zero exit
                    )
                    return "Light" if result.returncode != 0 else "Dark"
                except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                    logger.debug(f"macOS theme detection failed: {e}")
        except Exception as e:
            logger.debug(f"Failed to detect OS theme: {e}")

        return DEFAULT_THEME

    def _clear_interface(self):
        """Clear UI inputs: preview, notes, scene, and selected characters."""
        try:
            # Clear preview panel
            if hasattr(self, "preview_panel"):
                try:
                    self.preview_panel.clear_preview()
                except Exception:
                    from utils import logger as _logger

                    _logger.debug(
                        "Could not delete temp file while replacing content", exc_info=True
                    )

            # Clear scene and notes text
            if hasattr(self, "scene_text"):
                try:
                    self.scene_text.delete("1.0", "end")
                except Exception:
                    from utils import logger as _logger

                    _logger.debug("Failed to clear scene text widget", exc_info=True)
            if hasattr(self, "notes_text"):
                try:
                    self.notes_text.delete("1.0", "end")
                except Exception:
                    from utils import logger as _logger

                    _logger.debug("Failed to clear notes text widget", exc_info=True)

            # Clear selected characters
            if hasattr(self, "characters_tab"):
                try:
                    self.characters_tab.set_selected_characters([])
                except Exception:
                    from utils import logger as _logger

                    _logger.debug("Failed to clear selected characters", exc_info=True)

            self._update_status("Interface cleared")
        except Exception:
            from utils import logger

            logger.exception("Auto-captured exception")
            # Best-effort; if clearing fails, show status
            self._update_status("Interface cleared")

    def _toggle_auto_theme(self):
        """Toggle auto theme detection."""
        auto = self.menu_manager.get_auto_theme() if hasattr(self, "menu_manager") else False
        self.prefs.set("auto_theme", auto)
        if auto:
            detected_theme = self._detect_os_theme()
            self._change_theme(detected_theme)
            self._update_status(f"Auto-detected theme: {detected_theme}")

    def _toggle_character_gallery(self):
        """Toggle the character gallery panel visibility."""
        self.gallery_visible = not self.gallery_visible
        if hasattr(self, "menu_manager") and self.menu_manager:
            self.menu_manager.set_gallery_visible(self.gallery_visible)
        self.prefs.set("gallery_visible", self.gallery_visible)

        # Delegate gallery show/hide to controller when available
        if hasattr(self, "gallery_controller") and self.gallery_controller:
            try:
                self.gallery_controller.toggle_visibility(
                    self.gallery_visible, self.characters if self.gallery_visible else None
                )
            except Exception:
                logger.exception("Failed to toggle gallery via GalleryController")
        else:
            if self.gallery_visible:
                # Show gallery - insert at position 0 (leftmost)
                try:
                    self.main_paned.insert(0, self.gallery_frame, weight=2)
                    # Reload characters in case they changed
                    self.character_gallery.load_characters(self.characters)
                except tk.TclError:
                    # Already added
                    pass
            else:
                # Hide gallery
                try:
                    self.main_paned.forget(self.gallery_frame)
                except tk.TclError:
                    # Not in paned window
                    pass

    def _on_gallery_character_selected(self, character_name):
        """Handle character selection from gallery.

        Args:
            character_name: Name of selected character
        """
        # Add character to the characters tab
        self.characters_tab.add_character_from_gallery(character_name)
        self.schedule_preview_update()
