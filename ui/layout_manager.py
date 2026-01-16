import tkinter as tk
from tkinter import ttk

from core.config import DEFAULT_THEME
from ui.character_card import CharacterGalleryPanel
from ui.characters_tab import CharactersTab
from ui.controllers.menu_actions import MenuActions
from ui.menu_manager import MenuManager
from ui.components.toolbar import ToolbarComponent
from ui.components.status_bar import StatusBarComponent
from ui.scene_panel import ScenePanel
from ui.notes_panel import NotesPanel
from ui.summary_panel import SummaryPanel
from ui.preview_panel import PreviewPanel
from ui.widgets import CollapsibleFrame, ScrollableCanvas
from utils import create_tooltip

class LayoutManager:
    """Manages the construction and layout of the main application UI."""

    def __init__(self, app):
        """
        Args:
            app: The PromptBuilderApp instance.
        """
        self.app = app
        self.root = app.root
        self.theme_manager = app.theme_manager
        self.prefs = app.prefs

    def build_ui(self):
        """Build the entire UI layout."""
        self._build_menu()
        self._build_toolbar()
        
        # Main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        self._build_status_bar(self.main_container)
        self._build_main_panes(self.main_container)

    def _build_menu(self):
        # Create menu manager with callbacks provided by MenuActions controller
        self.app.menu_actions = MenuActions(self.app)
        menu_callbacks = {
            "save_preset": self.app.menu_actions.save_preset,
            "load_preset": self.app.menu_actions.load_preset,
            "export_config": self.app.menu_actions.export_config,
            "import_config": self.app.menu_actions.import_config,
            "export_for_llm": self.app.menu_actions.export_for_llm,
            "export_for_llm_creation": self.app.menu_actions.export_for_llm_creation,
            "bulk_prompt_generator": self.app.menu_actions.bulk_prompt_generator,
            "import_from_text": self.app.menu_actions.import_from_text,
            "reload_data": self.app.reload_data,
            "undo": self.app.menu_actions.undo,
            "redo": self.app.menu_actions.redo,
            "clear_all_characters": self.app.menu_actions.clear_all_characters,
            "reset_all_outfits": self.app.menu_actions.reset_all_outfits,
            "apply_same_pose_to_all": self.app.menu_actions.apply_same_pose_to_all,
            "toggle_character_gallery": self.app.menu_actions.toggle_character_gallery,
            "increase_font": self.app.menu_actions.increase_font,
            "decrease_font": self.app.menu_actions.decrease_font,
            "reset_font": self.app.menu_actions.reset_font,
            "randomize_all": self.app.menu_actions.randomize_all,
            "change_theme": self.app.menu_actions.change_theme,
            "get_themes": lambda: self.theme_manager.themes,
            "toggle_auto_theme": self.app.menu_actions.toggle_auto_theme,
            "show_dashboard": self.app.menu_actions.show_dashboard,
            "show_characters_summary": self.app.menu_actions.show_characters_summary,
            "show_outfits_summary": self.app.menu_actions.show_outfits_summary,
            "show_color_schemes_summary": self.app.menu_actions.show_color_schemes_summary,
            "show_tag_summary": self.app.menu_actions.show_tag_summary,
            "show_auditing_suite": self.app.menu_actions.show_auditing_suite,
            "show_automation_dialog": self.app.menu_actions.show_automation_dialog,
            "show_health_check": self.app.menu_actions.show_health_check,
            "open_data_folder": self.app.menu_actions.open_data_folder,
            "show_welcome": self.app.menu_actions.show_welcome,
            "show_shortcuts": self.app.menu_actions.show_shortcuts,
            "show_about": self.app.menu_actions.show_about,
            "open_theme_editor": self.app._open_theme_editor,
            "on_closing": self.app.menu_actions.on_closing,
            "change_ui_scale": self.app._change_ui_scale,
            "initial_theme": self.prefs.get("last_theme", DEFAULT_THEME),
            "initial_ui_scale": self.prefs.get("ui_scale", "Medium"),
            "auto_theme_enabled": self.prefs.get("auto_theme", False),
            "gallery_visible": self.prefs.get("gallery_visible", True),
        }

        self.app.menu_manager = MenuManager(self.root, menu_callbacks)
        self.app.menu_manager.bind_shortcuts()

    def _build_toolbar(self):
        toolbar_callbacks = {
            "save_preset": self.app._save_preset,
            "load_preset": self.app._load_preset,
            "undo": self.app._undo,
            "redo": self.app._redo,
            "randomize": self.app.randomize_all,
            "toggle_gallery": self.app._toggle_character_gallery
        }
        self.app.toolbar_component = ToolbarComponent(self.root, toolbar_callbacks, theme_manager=self.theme_manager)

    def _build_status_bar(self, parent):
        self.app.status_bar_component = StatusBarComponent(parent, theme_manager=self.theme_manager)

    def _build_main_panes(self, parent):
        # Create a paned window for gallery + main content
        try:
            panel_bg = ttk.Style().lookup("TFrame", "background")
        except Exception:
            panel_bg = "#1e1e1e"

        self.app.main_paned = tk.PanedWindow(
            parent, 
            orient="horizontal",
            bg=panel_bg,
            bd=0,
            sashwidth=6,
            sashrelief="flat",
            showhandle=False
        )
        self.app.main_paned.pack(side="top", fill="both", expand=True)

        # Left side: Character Gallery
        self._build_gallery()

        # Main Content PanedWindow
        paned = tk.PanedWindow(
            self.app.main_paned, 
            orient="horizontal",
            bg=panel_bg,
            bd=0,
            sashwidth=6,
            sashrelief="flat",
            showhandle=False
        )
        self.app.main_paned.add(paned, minsize=400) 

        # Characters Tab (Main Area)
        self.app.characters_tab = CharactersTab(
            paned, # Added directly to paned window
            self.app.data_loader,
            self.theme_manager,
            self.app.character_controller,
            self.app.schedule_preview_update,
            self.app.reload_data,
            self.app._save_state_for_undo,
        )
        paned.paneconfigure(self.app.characters_tab.tab, width=550, minsize=300)
        
        # Load initial data into tabs
        self.app.characters_tab.load_data(self.app.characters, self.app.base_prompts, self.app.poses, self.app.scenes)

        # Right side: Scrollable container
        self._build_right_panel(paned)

    def _build_gallery(self):
        if not self.app.lite_mode:
            self.app.gallery_frame = ttk.Frame(self.app.main_paned, style="TFrame", width=300)
            self.app.gallery_visible = self.prefs.get("gallery_visible", True)

            self.app.character_gallery = CharacterGalleryPanel(
                self.app.gallery_frame,
                self.app.data_loader,
                self.prefs,
                on_add_callback=self.app._on_gallery_character_selected,
                theme_manager=self.theme_manager,
                theme_colors=self.theme_manager.themes.get(DEFAULT_THEME, {}),
                on_create_callback=self.app._create_new_character
            )
            self.app.character_gallery.pack(fill="both", expand=True)

            if self.app.gallery_visible:
                self.app.main_paned.add(self.app.gallery_frame, width=300, minsize=200) 
        else:
            self.app.gallery_frame = None
            self.app.gallery_visible = False
            # Dummy gallery for lite mode
            class DummyGallery:
                def update_used_status(self, *args):
                    pass
                def _refresh_display(self, *args):
                    pass
                def load_characters(self, *args):
                    pass
            self.app.character_gallery = DummyGallery()

    def _build_right_panel(self, parent_paned):
        self.app.right_scroll_container = ScrollableCanvas(parent_paned)
        parent_paned.add(self.app.right_scroll_container, minsize=250) 
        right_frame = self.app.right_scroll_container.get_container()
        right_frame.columnconfigure(0, weight=1)

        SECTION_PAD_Y = (15, 20)
        INTERNAL_PAD_X = 15

        # Collapse/Expand Controls
        self._build_collapse_controls(right_frame, INTERNAL_PAD_X)

        # Scene Panel
        self.app.scene_panel = ScenePanel(
            right_frame, 
            self.app.data_loader, 
            self.theme_manager, 
            self.app.scenes,
            on_change_callback=self.app.schedule_preview_update,
            create_scene_callback=self.app._create_new_scene
        )
        self.app.scene_panel.grid(row=1, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=SECTION_PAD_Y)

        # Notes Panel
        self.app.notes_panel = NotesPanel(
            right_frame,
            self.app.data_loader,
            self.theme_manager,
            self.app.interactions,
            on_change_callback=self.app.schedule_preview_update,
            create_interaction_callback=self.app._create_new_interaction,
            get_selected_char_names=lambda: [c["name"] for c in self.app.characters_tab.get_selected_characters()]
        )
        self.app.notes_panel.grid(row=2, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=SECTION_PAD_Y)

        # Summary Panel
        self.app.summary_panel = SummaryPanel(
            right_frame,
            self.theme_manager,
            on_apply_callback=self.app._import_from_summary_box,
            on_import_callback=self.app.menu_actions.import_from_text
        )
        self.app.summary_panel.grid(row=3, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=SECTION_PAD_Y)

        # Preview Panel
        self._build_preview_panel(right_frame, INTERNAL_PAD_X, SECTION_PAD_Y)

    def _build_collapse_controls(self, parent, pad_x):
        controls_frame = ttk.Frame(parent, style="TFrame")
        controls_frame.grid(row=0, column=0, sticky="ew", padx=pad_x, pady=(15, 0))
        
        def _set_all_collapsible(state):
            for panel in [self.app.scene_panel, self.app.notes_panel, 
                           self.app.summary_panel]:
                panel.set_opened(state)
            self.app.preview_collapsible.set_opened(state)
            self.app.right_scroll_container.update_scroll_region()

        theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
        panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        muted_fg = theme.get("border", "gray")
        
        # Determine last panel bg for hover effects
        self.app._last_panel_bg = panel_bg 

        self.app.collapse_all_btn = tk.Button(controls_frame, text="COLLAPSE ALL", 
                   command=lambda: _set_all_collapsible(False), 
                   bg=panel_bg, fg=muted_fg, borderwidth=0, relief="flat", font=("Lexend", 8, "bold"),
                   cursor="hand2")
        self.app.collapse_all_btn.pack(side="right", padx=2)
        
        self.app.expand_all_btn = tk.Button(controls_frame, text="EXPAND ALL", 
                   command=lambda: _set_all_collapsible(True), 
                   bg=panel_bg, fg=muted_fg, borderwidth=0, relief="flat", font=("Lexend", 8, "bold"),
                   cursor="hand2")
        self.app.expand_all_btn.pack(side="right", padx=2)
        
        # Bind hover effects
        def on_btn_enter(e, b):
            try:
                curr_theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
                hbg = curr_theme.get("hover_bg", "#333333")
            except Exception:
                hbg = "#333333"
            b.config(bg=hbg)
        def on_btn_leave(e, b):
            b.config(bg=getattr(self.app, "_last_panel_bg", "#1e1e1e"))
            
        for b in [self.app.collapse_all_btn, self.app.expand_all_btn]:
            b.bind("<Enter>", lambda e, btn=b: on_btn_enter(e, btn))
            b.bind("<Leave>", lambda e, btn=b: on_btn_leave(e, btn))

    def _build_preview_panel(self, parent, pad_x, pad_y_tuple):
        self.app.preview_collapsible = CollapsibleFrame(parent, text="🔍 PROMPT PREVIEW", opened=True)
        self.app.preview_collapsible.grid(row=4, column=0, sticky="nsew", padx=pad_x, pady=(pad_y_tuple[0], 20))
        create_tooltip(self.app.preview_collapsible, "The full generated prompt for copying")
        
        preview_content = self.app.preview_collapsible.get_content_frame()
        preview_header = self.app.preview_collapsible.get_header_frame()

        self.app.preview_panel = PreviewPanel(
            preview_content,
            self.theme_manager,
            self.app.reload_data,
            self.app.randomize_all,
            status_callback=self.app._update_status,
            clear_callback=self.app._clear_interface,
            toast_callback=getattr(self.app, "toasts").notify,
            header_parent=preview_header,
            on_automation=self.app.menu_actions.generate_current_image
        )

        # Set preview callbacks
        self.app.preview_panel.set_callbacks(
            self.app._generate_prompt, self.app._validate_prompt, self.app.randomize_all
        )
        
        # Register for theme updates
        if self.theme_manager:
            self.theme_manager.register(self.app.preview_collapsible, self.app.preview_collapsible.apply_theme)
            self.theme_manager.register(self.app.scene_panel, self.app.scene_panel.apply_theme)
            self.theme_manager.register(self.app.notes_panel, self.app.notes_panel.apply_theme)
            self.theme_manager.register(self.app.summary_panel, self.app.summary_panel.apply_theme)
            
            # Register newly extracted components
            self.theme_manager.register(self.app.status_bar_component.label, lambda t: self.app.status_bar_component.apply_theme(t))
            self.theme_manager.register(self.app.toolbar_component.frame, lambda t: self.app.toolbar_component.apply_theme(t))
            
            self.theme_manager.register(self.app.right_scroll_container, self.app.right_scroll_container.apply_theme)
