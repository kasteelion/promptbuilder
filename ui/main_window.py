# -*- coding: utf-8 -*-
"""Main application window."""

import platform
import tkinter as tk
from tkinter import ttk
from typing import Optional

from config import DEFAULT_THEME, TOOLTIPS, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE
from core.app_context import AppContext
from core.builder import PromptBuilder
from core.exceptions import DataLoadError
from logic import DataLoader, PromptRandomizer, validate_prompt_config
from themes import ThemeManager
from utils import PreferencesManager, create_tooltip, logger
from utils.interaction_helpers import fill_template

from .character_card import CharacterGalleryPanel
from .characters_tab import CharactersTab
from .constants import PREVIEW_UPDATE_THROTTLE_MS
from .controllers.gallery import GalleryController
from .controllers.menu_actions import MenuActions
from .controllers.window_state import WindowStateController
from .dialog_manager import DialogManager
from .edit_tab import EditTab
from .font_manager import FontManager
from .menu_manager import MenuManager
from .preview_controller import PreviewController
from .preview_panel import PreviewPanel
from .searchable_combobox import SearchableCombobox
from .state_manager import StateManager
from .widgets import CollapsibleFrame, ScrollableCanvas


class PromptBuilderApp:
    """Main application class for Prompt Builder."""

    def __init__(self, root: tk.Tk):
        """Initialize the application.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Prompt Builder — Group Picture Generator")

        # Initialize Application Context
        self.ctx = AppContext(self.root)
        self.ctx.initialize_ui_services()

        # Initialize preferences first (via context)
        self.prefs = self.ctx.prefs

        # Initialize managers (font and state managers will be set up after UI)
        self.font_manager: Optional[FontManager] = None
        self.state_manager: Optional[StateManager] = None
        self.menu_manager: Optional[MenuManager] = None
        self.dialog_manager = DialogManager(self.root, self.prefs)

        # Initialize data via context
        self.data_loader = self.ctx.data_loader
        
        # Throttling for preview updates
        self._after_id: Optional[str] = None
        self._throttle_ms = PREVIEW_UPDATE_THROTTLE_MS
        
        # Debounce tracking for text inputs
        self._scene_text_after_id: Optional[str] = None
        self._notes_text_after_id: Optional[str] = None
        
        # Initialize placeholder attributes
        self.preview_controller: Optional[PreviewController] = None

        # Build loading screen
        self._build_loading_screen()
        
        # Center and show window
        self._center_window()
        self.root.deiconify()

        # Start async data load
        self.ctx.load_data_async(self._on_init_success, self._on_init_error)

    def _build_loading_screen(self):
        """Build a simple loading screen."""
        self.loading_frame = ttk.Frame(self.root)
        self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Center container
        container = ttk.Frame(self.loading_frame)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(
            container, 
            text="Prompt Builder", 
            font=("Segoe UI", 24, "bold")
        ).pack(pady=(0, 20))
        
        ttk.Label(
            container, 
            text="Loading assets...", 
            font=("Segoe UI", 12)
        ).pack(pady=(0, 10))
        
        self.loading_progress = ttk.Progressbar(
            container, 
            mode="indeterminate", 
            length=300
        )
        self.loading_progress.pack(pady=10)
        self.loading_progress.start(10)

    def _on_init_success(self):
        """Handle successful initial data load."""
        # Stop progress bar
        self.loading_progress.stop()
        
        # Initialize references
        self._initialize_data_references()
        
        # Sync tags from characters (manual file additions)
        try:
            added = self.data_loader.sync_tags()
            if added:
                logger.info(f"Startup: Added {added} new tags from character files.")
        except Exception:
            logger.exception("Error syncing tags on startup")

        # Complete initialization
        self._complete_initialization()
        
        # Remove loading screen with a fade out effect (simulated by just destroying for now)
        self.loading_frame.destroy()
        del self.loading_frame

    def _on_init_error(self, error):
        """Handle initial data load error."""
        logger.exception("Error loading data", exc_info=error)
        self.loading_progress.stop()
        self.dialog_manager.show_error(
            "Error loading data", 
            f"Failed to load application data: {error}\nSee log for details."
        )
        self.root.destroy()

    def _initialize_data_references(self):
        """Initialize local references to context data."""
        self.characters = self.ctx.characters
        self.base_prompts = self.ctx.base_prompts
        self.scenes = self.ctx.scenes
        self.poses = self.ctx.poses
        self.interactions = self.ctx.interactions
        self.color_schemes = self.ctx.color_schemes
        self.modifiers = self.ctx.modifiers
        # Expose to root for easier access by components
        self.root.modifiers = self.modifiers
        self.randomizer = self.ctx.randomizer
        
        self.theme_manager = self.ctx.theme_manager
        self.toasts = self.ctx.toasts

        # Expose toast manager and status updater on the root
        try:
            self.root._update_status = self._update_status
        except Exception:
            logger.exception("Failed to attach status to root")

    def _complete_initialization(self):
        """Complete UI initialization after data is loaded."""
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

        # Restore UI scale
        saved_scale = self.prefs.get("ui_scale", "Medium")
        self._change_ui_scale(saved_scale)

        # Restore last base prompt
        last_base_prompt = self.prefs.get("last_base_prompt")
        if last_base_prompt and last_base_prompt in self.base_prompts:
            self.characters_tab.set_base_prompt(last_base_prompt)

        # Load characters into gallery
        self.character_gallery.load_characters(self.characters)

        # Initial preview update
        self.update_preview()

        # Position window properly if not restored
        if not saved_geometry:
            self._center_window()

        # Restore window state (maximized/zoomed state)
        if saved_state and saved_state in ("zoomed", "normal", "iconic"):
            try:
                self.root.state(saved_state)
            except tk.TclError as e:
                logger.warning(f"Could not restore window state: {e}")

        # Show welcome dialog for first-time users
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
            "export_for_llm": self.menu_actions.export_for_llm,
            "export_for_llm_creation": self.menu_actions.export_for_llm_creation,
            "import_from_text": self.menu_actions.import_from_text,
            "reload_data": self.reload_data,
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
            "get_themes": lambda: self.theme_manager.themes,
            "toggle_auto_theme": self.menu_actions.toggle_auto_theme,
            "show_characters_summary": self.menu_actions.show_characters_summary,
            "show_outfits_summary": self.menu_actions.show_outfits_summary,
            "show_color_schemes_summary": self.menu_actions.show_color_schemes_summary,
            "show_tag_summary": self.menu_actions.show_tag_summary,
            "show_welcome": self.menu_actions.show_welcome,
            "show_shortcuts": self.menu_actions.show_shortcuts,
            "show_about": self.menu_actions.show_about,
            "open_theme_editor": self._open_theme_editor,
            "on_closing": self.menu_actions.on_closing,
            "change_ui_scale": self._change_ui_scale,
            "initial_theme": self.prefs.get("last_theme", DEFAULT_THEME),
            "initial_ui_scale": self.prefs.get("ui_scale", "Medium"),
            "auto_theme_enabled": self.prefs.get("auto_theme", False),
            "gallery_visible": self.prefs.get("gallery_visible", True),
        }

        self.menu_manager = MenuManager(self.root, menu_callbacks)

        # Build Toolbar
        self._build_toolbar()

        # Bind keyboard shortcuts
        self._bind_keyboard_shortcuts()

        # Main container with optional character gallery
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True)

        # Status bar at bottom (pack first so it stays at bottom)
        self.status_bar = ttk.Label(
            main_container,
            text="Ready",
            relief="sunken",
            anchor="w",
            style="TLabel",
        )
        self.status_bar.pack(side="bottom", fill="x")

        # Create a paned window for gallery + main content
        self.main_paned = ttk.PanedWindow(main_container, orient="horizontal")
        self.main_paned.pack(side="top", fill="both", expand=True)

        # Left side: Character Gallery (collapsible, starts visible by default)
        self.gallery_frame = ttk.Frame(self.main_paned, style="TFrame", width=280)
        self.gallery_visible = self.prefs.get("gallery_visible", True)

        self.character_gallery = CharacterGalleryPanel(
            self.gallery_frame,
            self.data_loader,
            self.prefs,
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

        # Right side: Scrollable container for collapsible sections
        self.right_scroll_container = ScrollableCanvas(paned)
        paned.add(self.right_scroll_container, weight=4)
        right_frame = self.right_scroll_container.get_container()
        right_frame.columnconfigure(0, weight=1)

        # Standard spacing constants for consistent layout
        SECTION_PAD_Y = (6, 10)
        INTERNAL_PAD_X = 6

        # Convenience controls row (Expand/Collapse All)
        controls_frame = ttk.Frame(right_frame, style="TFrame")
        controls_frame.grid(row=0, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=(4, 0))
        
        def _set_all_collapsible(state):
            for section in [self.scene_collapsible, self.notes_collapsible, 
                           self.summary_collapsible, self.preview_collapsible]:
                section.set_opened(state)
            self.right_scroll_container.update_scroll_region()

        ttk.Button(controls_frame, text="Collapse All", width=12, 
                   command=lambda: _set_all_collapsible(False)).pack(side="right", padx=2)
        ttk.Button(controls_frame, text="Expand All", width=12, 
                   command=lambda: _set_all_collapsible(True)).pack(side="right", padx=2)

        # Scene section (compact)
        self.scene_collapsible = CollapsibleFrame(right_frame, text="🎬 Scene", opened=True, show_clear=True)
        self.scene_collapsible.grid(row=1, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=SECTION_PAD_Y)
        self.scene_collapsible.set_clear_command(lambda: (self.scene_text.delete("1.0", "end"), self.schedule_preview_update()))
        
        scene_content = self.scene_collapsible.get_content_frame()
        scene_content.columnconfigure(1, weight=1)
        create_tooltip(self.scene_collapsible, TOOLTIPS.get("scene", ""))

        # Scene presets row
        ttk.Label(scene_content, text="Category:", style="TLabel").grid(
            row=0, column=0, sticky="w", padx=(4, 4), pady=6
        )
        self.scene_category_var = tk.StringVar()
        self.scene_cat_combo = SearchableCombobox(
            scene_content, 
            textvariable=self.scene_category_var,
            on_select=lambda val: self._update_scene_presets(),
            placeholder="Search category...",
            width=14
        )
        self.scene_cat_combo.grid(row=0, column=1, sticky="w", padx=2, pady=6)

        ttk.Label(scene_content, text="Preset:", style="TLabel").grid(
            row=0, column=2, sticky="w", padx=(10, 4), pady=6
        )
        self.scene_preset_var = tk.StringVar()
        self.scene_combo = SearchableCombobox(
            scene_content, 
            textvariable=self.scene_preset_var,
            on_select=lambda val: self._apply_scene_preset(),
            placeholder="Search preset...",
            width=20
        )
        self.scene_combo.grid(row=0, column=3, sticky="ew", padx=2, pady=6)

        new_scene_btn = ttk.Button(scene_content, text="✨", width=3, command=self._create_new_scene)
        new_scene_btn.grid(row=0, column=4, padx=(6, 4), pady=6)
        create_tooltip(new_scene_btn, "Create a new scene preset")

        self.scene_text = tk.Text(scene_content, wrap="word", height=3)
        self.scene_text.grid(row=1, column=0, columnspan=5, sticky="ew", padx=4, pady=(2, 6))
        # Debounce scene text changes
        self._scene_text_after_id = None

        def _on_scene_change(e):
            if self._scene_text_after_id:
                self.root.after_cancel(self._scene_text_after_id)
            self._scene_text_after_id = self.root.after(300, self.schedule_preview_update)

        self.scene_text.bind("<KeyRelease>", _on_scene_change)

        # Notes section (expandable)
        self.notes_collapsible = CollapsibleFrame(right_frame, text="📝 Notes & Interactions", opened=True, show_clear=True)
        self.notes_collapsible.grid(row=2, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=SECTION_PAD_Y)
        self.notes_collapsible.set_clear_command(lambda: (self.notes_text.delete("1.0", "end"), self.schedule_preview_update()))
        
        notes_content = self.notes_collapsible.get_content_frame()
        notes_content.columnconfigure(0, weight=1)
        create_tooltip(self.notes_collapsible, TOOLTIPS.get("notes", ""))

        # Interaction template selector (with category grouping)
        interaction_control = ttk.Frame(notes_content, style="TFrame")
        interaction_control.grid(row=0, column=0, sticky="ew", padx=4, pady=(6, 4))
        interaction_control.columnconfigure(1, weight=1)
        interaction_control.columnconfigure(3, weight=1)

        ttk.Label(interaction_control, text="Category:", style="TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 6)
        )

        self.interaction_category_var = tk.StringVar()
        self.interaction_cat_combo = SearchableCombobox(
            interaction_control,
            textvariable=self.interaction_category_var,
            on_select=lambda val: self._update_interaction_presets(),
            placeholder="Search category...",
            width=15
        )
        self.interaction_cat_combo.grid(row=0, column=1, sticky="w", padx=(0, 10))

        ttk.Label(interaction_control, text="Template:", style="TLabel").grid(
            row=0, column=2, sticky="w", padx=(0, 6)
        )

        self.interaction_var = tk.StringVar(value="Blank")
        self.interaction_combo = SearchableCombobox(
            interaction_control, 
            textvariable=self.interaction_var,
            on_double_click=lambda val: self._insert_interaction_template(),
            placeholder="Search template...",
            width=25
        )
        self.interaction_combo.grid(row=0, column=3, sticky="ew")

        insert_btn = ttk.Button(
            interaction_control, text="Insert", command=self._insert_interaction_template
        )
        insert_btn.grid(row=0, column=4, padx=(6, 0))

        refresh_btn = ttk.Button(
            interaction_control, text="🔄", command=self._refresh_interaction_template, width=3
        )
        refresh_btn.grid(row=0, column=5, padx=(4, 0))

        create_btn = ttk.Button(
            interaction_control, text="+ Create", command=self._create_new_interaction
        )
        create_btn.grid(row=0, column=6, padx=(4, 0))

        self.notes_text = tk.Text(notes_content, wrap="word", height=4)
        self.notes_text.grid(row=1, column=0, sticky="nsew", padx=4, pady=(4, 6))
        # Debounce notes text changes
        self._notes_text_after_id = None

        def _on_notes_change(e):
            if self._notes_text_after_id:
                self.root.after_cancel(self._notes_text_after_id)
            self._notes_text_after_id = self.root.after(300, self.schedule_preview_update)

        self.notes_text.bind("<KeyRelease>", _on_notes_change)

        # Summary section
        self.summary_collapsible = CollapsibleFrame(right_frame, text="📋 Prompt Summary", opened=True, show_import=True)
        self.summary_collapsible.grid(row=3, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=SECTION_PAD_Y)
        self.summary_collapsible.set_import_command(self.menu_actions.import_from_text)
        create_tooltip(self.summary_collapsible, "Condensed overview of characters and scene. Click Import to load from text.")
        summary_content = self.summary_collapsible.get_content_frame()
        summary_content.columnconfigure(0, weight=1)
        
        self.summary_text = tk.Text(summary_content, wrap="word", height=3)
        self.summary_text.grid(row=0, column=0, sticky="ew", padx=4, pady=6)
        create_tooltip(self.summary_text, "Condensed overview. You can edit this text and click 'Apply' to update the whole prompt.")
        
        # Track summary editing state
        self._summary_modified = False
        
        def _on_summary_focus_in(e):
            self._summary_modified = True
            theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
            # Use text_bg or a fallback that isn't hardcoded white
            bg = theme.get("text_bg", theme.get("bg", "#ffffff"))
            fg = theme.get("text_fg", theme.get("fg", "#000000"))
            self.summary_text.config(background=bg, foreground=fg)

        def _on_summary_change(e):
            self._summary_modified = True
            # Change icon or text of the import button to show it's ready to apply? 
            # For now, keeping it simple.

        self.summary_text.bind("<FocusIn>", _on_summary_focus_in)
        self.summary_text.bind("<KeyRelease>", _on_summary_change)

        # Preview panel container
        self.preview_collapsible = CollapsibleFrame(right_frame, text="🔍 Prompt Preview", opened=True)
        self.preview_collapsible.grid(row=4, column=0, sticky="nsew", padx=INTERNAL_PAD_X, pady=(SECTION_PAD_Y[0], 20))
        create_tooltip(self.preview_collapsible, "The full generated prompt for copying")
        preview_content = self.preview_collapsible.get_content_frame()
        preview_header = self.preview_collapsible.get_header_frame()

        self.preview_panel = PreviewPanel(
            preview_content,
            self.theme_manager,
            self.reload_data,
            self.randomize_all,
            status_callback=self._update_status,
            clear_callback=self._clear_interface,
            toast_callback=getattr(self, "toasts").notify,
            header_parent=preview_header,
        )

        # Set preview callbacks
        self.preview_panel.set_callbacks(
            self._generate_prompt, self._validate_prompt, self.randomize_all
        )

        # Initialize scene presets
        self._update_scene_presets()

    def _build_toolbar(self):
        """Build the top toolbar with common actions."""
        toolbar_frame = ttk.Frame(self.root, style="TFrame")
        toolbar_frame.pack(side="top", fill="x", padx=4, pady=4)

        # Helper to create styled toolbar buttons
        def add_tool_btn(parent, text, command, tooltip=None, width=None):
            btn = ttk.Button(parent, text=text, command=command)
            if width:
                btn.config(width=width)
            btn.pack(side="left", padx=2)
            if tooltip:
                create_tooltip(btn, tooltip)
            return btn

        # File actions
        add_tool_btn(toolbar_frame, "💾", self._save_preset, "Save Preset", width=3)
        add_tool_btn(toolbar_frame, "📂", self._load_preset, "Load Preset", width=3)
        
        ttk.Separator(toolbar_frame, orient="vertical").pack(side="left", fill="y", padx=4, pady=2)

        # Edit actions
        add_tool_btn(toolbar_frame, "↩️", self._undo, "Undo (Ctrl+Z)", width=3)
        add_tool_btn(toolbar_frame, "↪️", self._redo, "Redo (Ctrl+Y)", width=3)

        ttk.Separator(toolbar_frame, orient="vertical").pack(side="left", fill="y", padx=4, pady=2)
        
        # Tools
        add_tool_btn(toolbar_frame, "🎲 Randomize", self.randomize_all, "Randomize Everything (Alt+R)")
        add_tool_btn(toolbar_frame, "👥 Gallery", self._toggle_character_gallery, "Toggle Character Gallery (Ctrl+G)")
        
        # Spacer
        ttk.Frame(toolbar_frame).pack(side="left", fill="x", expand=True)

        # Right side actions (Theme toggle could go here, but menu is fine)

    def _initialize_managers(self):
        """Initialize managers that depend on UI elements."""
        # Initialize font manager
        self.font_manager = FontManager(self.root, self.prefs)

        # Register text widgets for font management
        for widget in [
            self.scene_text,
            self.notes_text,
            self.summary_text,
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
        self.interaction_cat_combo.set_values(categories)
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

        import inspect

        for key, handler in shortcuts:
            # Determine whether handler expects an event parameter.
            try:
                sig = inspect.signature(handler)
                # Count positional parameters (exclude VAR_POSITIONAL/VAR_KEYWORD)
                pos_params = [
                    p
                    for p in sig.parameters.values()
                    if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                ]
                if len(pos_params) == 0:
                    # Handler expects no args
                    self.root.bind(key, lambda e, h=handler: h())
                else:
                    # Handler expects at least one arg (event)
                    self.root.bind(key, lambda e, h=handler: h(e))
            except (ValueError, TypeError):
                # Fallback: call with event argument
                self.root.bind(key, lambda e, h=handler: h(e))

    def _update_scene_presets(self):
        """Update scene preset combo based on selected category."""
        cat = self.scene_category_var.get()
        if cat and cat in self.scenes:
            self.scene_combo.set_values([""] + sorted(list(self.scenes[cat].keys())))
        else:
            self.scene_combo.set_values([""])
        self.scene_preset_var.set("")

        # Update category combo values
        self.scene_cat_combo.set_values([""] + sorted(list(self.scenes.keys())))
        self.root.update_idletasks()

    def _update_interaction_presets(self):
        """Update interaction preset combo based on selected category."""
        cat = self.interaction_category_var.get()
        if cat and cat in self.interactions:
            self.interaction_combo.set_values([""] + sorted(list(self.interactions[cat].keys())))
        else:
            self.interaction_combo.set_values([""])
        self.interaction_var.set("")

        # Update category combo values
        self.interaction_cat_combo.set_values([""] + sorted(list(self.interactions.keys())))
        self.root.update_idletasks()

    def _insert_interaction_template(self):
        """Insert interaction template with character placeholders filled."""
        cat = self.interaction_category_var.get()
        template_name = self.interaction_var.get()

        if not cat or not template_name:
            return

        if cat not in self.interactions or template_name not in self.interactions[cat]:
            return

        template_data = self.interactions[cat][template_name]

        if not template_data:
            return

        # Get list of selected character names from characters tab
        selected_chars = [char["name"] for char in self.characters_tab.selected_characters]

        if not selected_chars:
            from utils.notification import notify

            root = self.root
            msg = "Please add characters to your prompt first before using interaction templates."
            notify(root, "No Characters", msg, level="info", duration=3000, parent=self.root)
            return

        # Check character count if using new structured format
        if isinstance(template_data, dict):
            min_chars = template_data.get("min_chars", 1)
            if len(selected_chars) < min_chars:
                from utils.notification import notify
                msg = f"This interaction typically requires {min_chars} characters (you have {len(selected_chars)}). Some placeholders may not be filled."
                notify(self.root, "Character Count", msg, level="warning", duration=4000)

        # Fill template with character names
        filled_text = fill_template(template_data, selected_chars)

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

        template_data = self.interactions[cat][template_name]

        if not template_data:
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
        filled_text = fill_template(template_data, selected_chars)

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
            self.interaction_cat_combo.set_values(categories)

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

    def _open_theme_editor(self):
        """Open the Theme Editor dialog to create/edit custom themes."""
        try:
            from .theme_editor import ThemeEditorDialog

            dlg = ThemeEditorDialog(
                self.root,
                self.theme_manager,
                self.prefs,
                on_theme_change=self.menu_manager.refresh_theme_menu,
            )
            dlg.show()
        except Exception:
            from utils import logger as _logger

            _logger.exception("Failed to open Theme Editor")

    def _set_initial_fonts(self):
        """Set initial fonts on text widgets."""
        font = (DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE)
        for widget in [
            self.scene_text,
            self.notes_text,
            self.summary_text,
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

    def _change_ui_scale(self, scale_name):
        """Change the global UI scale.

        Args:
            scale_name: Name of scale ('Small', 'Medium', 'Large')
        """
        scales = {"Small": 0.8, "Medium": 1.0, "Large": 1.25, "Extra Large": 1.5}
        factor = scales.get(scale_name, 1.0)
        
        self.theme_manager.scale_factor = factor
        self.prefs.set("ui_scale", scale_name)
        
        if hasattr(self, "menu_manager"):
            self.menu_manager.ui_scale_var.set(scale_name)
        
        # Apply theme again to update all styles with new scale
        current_theme = self.theme_manager.current_theme or self.prefs.get("last_theme", DEFAULT_THEME)
        self._apply_theme(current_theme)
        
        # Update fonts in text widgets
        if hasattr(self, "font_manager"):
            self.font_manager.update_font_size(int(DEFAULT_FONT_SIZE * factor))

    def _apply_theme(self, theme_name):
        """Apply theme to all UI elements.

        Args:
            theme_name: Name of theme to apply
        """
        theme = self.theme_manager.apply_theme(theme_name)

        # Apply to text widgets
        self.theme_manager.apply_preview_theme(self.preview_panel.preview_text, theme)
        for widget in [self.scene_text, self.notes_text, self.summary_text, self.edit_tab.editor_text]:
            self.theme_manager.apply_text_widget_theme(widget, theme)
        
        # Reset summary background if not modified
        if not getattr(self, "_summary_modified", False):
            self.theme_manager.apply_text_widget_theme(self.summary_text, theme)

        # Apply to canvas
        self.theme_manager.apply_canvas_theme(self.characters_tab.chars_canvas, theme)
        if hasattr(self, "right_scroll_container"):
            self.theme_manager.apply_canvas_theme(self.right_scroll_container.canvas, theme)

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
        
        # Update summary only if not being manually edited
        if not getattr(self, "_summary_modified", False):
            summary = self._generate_summary()
            self.summary_text.config(state="normal")
            self.summary_text.delete("1.0", "end")
            self.summary_text.insert("1.0", summary)
        
        num_chars = len(self.characters_tab.get_selected_characters())
        self._update_status(f"Ready • {num_chars} character(s) selected")

    def _generate_summary(self):
        """Generate summary from current data.

        Returns:
            str: Summary text
        """
        builder = PromptBuilder(
            self.characters, self.base_prompts, self.poses, self.color_schemes, self.modifiers
        )

        config = {
            "selected_characters": self.characters_tab.get_selected_characters(),
            "scene": self.scene_text.get("1.0", "end").strip(),
            "notes": self.notes_text.get("1.0", "end").strip(),
        }

        return builder.generate_summary(config)

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
        builder = PromptBuilder(
            self.characters, self.base_prompts, self.poses, self.color_schemes, self.modifiers
        )

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
        """Reload all data from markdown files asynchronously."""
        self._update_status("🔄 Reloading data...")
        self.root.config(cursor="watch")
        
        # Clear data loader cache to force fresh read from disk
        try:
            self.data_loader.clear_cache()
        except Exception:
            logger.debug("Failed to clear data_loader cache during reload")

        # Show reloading overlay
        self._show_reload_overlay()

        # Start async load
        self.ctx.load_data_async(self._on_reload_success, self._on_reload_error)

    def _show_reload_overlay(self):
        """Show a modal overlay during reload."""
        self.reload_overlay = ttk.Frame(self.root)
        self.reload_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Semi-transparent background effect (simulated with a label if needed, or just opaque)
        # For simplicity, we use an opaque frame with a label
        
        container = ttk.Frame(self.reload_overlay)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(
            container, text="Reloading...", font=("Segoe UI", 16, "bold")
        ).pack(pady=10)
        
        self.reload_progress = ttk.Progressbar(container, mode="indeterminate", length=200)
        self.reload_progress.pack(pady=10)
        self.reload_progress.start(10)

    def _hide_reload_overlay(self):
        """Hide the reload overlay."""
        if hasattr(self, "reload_overlay"):
            self.reload_progress.stop()
            self.reload_overlay.destroy()
            del self.reload_overlay

    def _on_reload_success(self):
        """Handle successful data reload."""
        try:
            # Migration logic (preserved from original)
            self._handle_theme_migration()
            
            # Update local references
            self._initialize_data_references()
            
            # Reload themes (synchronous, but usually fast)
            if hasattr(self, "theme_manager") and self.theme_manager:
                self.theme_manager.reload_md_themes()

            # Sync tags from characters
            try:
                added = self.data_loader.sync_tags()
                if added:
                    logger.info(f"Reload: Added {added} new tags from character files.")
            except Exception:
                logger.exception("Error syncing tags on reload")

            # Update UI
            self._update_ui_after_reload()
            
            self._hide_reload_overlay()
            self.root.config(cursor="")
            self._update_status("✅ Data reloaded successfully")
            self.dialog_manager.show_info("Success", "Data reloaded successfully!")
            
        except Exception:
            logger.exception("Error during reload post-processing")
            self._hide_reload_overlay()
            self.root.config(cursor="")
            self.dialog_manager.show_error("Reload Error", "Error updating UI after reload.")

    def _on_reload_error(self, error):
        """Handle data reload error."""
        logger.exception("Error reloading data", exc_info=error)
        self._hide_reload_overlay()
        self.root.config(cursor="")
        self.dialog_manager.show_error(
            "Reload Error", f"Failed to reload data: {error}\nSee log for details."
        )
        self._update_status("❌ Error loading data")

    def _handle_theme_migration(self):
        """Handle one-time theme migration."""
        try:
            migrated = False
            if hasattr(self, "theme_manager") and self.theme_manager:
                migrated = self.theme_manager.migrate_from_prefs(self.prefs)
            if migrated:
                try:
                    if hasattr(self, "menu_manager") and self.menu_manager:
                        self.menu_manager.refresh_theme_menu()
                except Exception:
                    logger.debug("Failed to refresh theme menu after migration")
        except Exception:
            logger.exception("Theme migration failed during reload")

    def _update_ui_after_reload(self):
        """Update UI components with new data."""
        # Update character selection validity
        new_chars_keys = set(self.characters.keys())
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

        self.characters_tab.selected_characters = updated_selected

        if chars_removed:
            self.dialog_manager.show_info(
                "Reload Info",
                "Some previously selected characters were removed as they no longer exist in the updated data.",
            )

        # Reload data in tabs
        self.characters_tab.load_data(self.characters, self.base_prompts, self.poses, self.scenes)
        self._update_scene_presets()
        self._reload_interaction_templates()
        self.edit_tab._refresh_file_list()

        # Re-apply theme
        current = self.prefs.get("last_theme") or None
        if current:
            try:
                self._apply_theme(current)
                if hasattr(self, "menu_manager") and self.menu_manager:
                    self.menu_manager.refresh_theme_menu()
            except Exception:
                logger.debug("Failed to re-apply theme after reload")

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

        self.schedule_preview_update()

    def _import_from_summary_box(self):
        """Parse and apply the text currently in the summary box."""
        raw_text = self.summary_text.get("1.0", "end-1c").strip()
        if not raw_text:
            return

        available_chars = list(self.characters.keys())
        from utils.text_parser import TextParser
        
        try:
            config = TextParser.parse_import_text(raw_text, available_chars)
            self._save_state_for_undo()
            self._restore_state(config)
            self._summary_modified = False
            # Reset background
            self._apply_theme(self.theme_manager.current_theme) 
            self._update_status("Applied changes from summary console")
        except Exception as e:
            logger.error(f"Failed to parse summary box: {e}")
            self._update_status("❌ Error parsing summary text")

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
        # Use WindowStateController to save geometry, state, and sash positions
        if hasattr(self, "window_state_controller"):
            self.window_state_controller.save_geometry_and_state()

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
        cat_combo = SearchableCombobox(
            frame, 
            values=[""] + sorted(list(self.poses.keys())),
            textvariable=cat_var,
            on_select=lambda val: update_presets(),
            placeholder="Search category...",
            width=20
        )
        cat_combo.grid(row=0, column=1, sticky="ew", pady=5, padx=(5, 0))

        ttk.Label(frame, text="Preset:").grid(row=1, column=0, sticky="w", pady=5)
        preset_var = tk.StringVar()
        preset_combo = SearchableCombobox(
            frame,
            values=[""],
            textvariable=preset_var,
            on_select=lambda val: None,
            placeholder="Search preset...",
            width=20
        )
        preset_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=(5, 0))

        def update_presets():
            cat = cat_var.get()
            if cat and cat in self.poses:
                preset_combo.set_values([""] + sorted(list(self.poses[cat].keys())))
            else:
                preset_combo.set_values([""])
            preset_var.set("")
            dialog.update_idletasks()

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

            # Clear summary text
            if hasattr(self, "summary_text"):
                try:
                    self.summary_text.config(state="normal")
                    self.summary_text.delete("1.0", "end")
                    self.summary_text.config(state="disabled")
                except Exception:
                    from utils import logger as _logger

                    _logger.debug("Failed to clear summary text widget", exc_info=True)

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
