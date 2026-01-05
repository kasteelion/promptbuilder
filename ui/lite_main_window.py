# -*- coding: utf-8 -*-
"""Lite version of the main application window."""

import tkinter as tk
from tkinter import ttk

from config import DEFAULT_THEME
from utils import create_tooltip

# Imports required for _build_ui
from .main_window import PromptBuilderApp
from .lite_characters_tab import LiteCharactersTab
from .controllers.menu_actions import MenuActions
from .menu_manager import MenuManager
from .preview_panel import PreviewPanel
from .scene_panel import ScenePanel
from .notes_panel import NotesPanel
from .summary_panel import SummaryPanel
from .widgets import CollapsibleFrame, ScrollableCanvas

class LitePromptBuilderApp(PromptBuilderApp):
    """Lite version of PromptBuilderApp without character gallery images."""

    def _build_ui(self):
        """Build the main UI layout (Lite Version)."""
        # Create menu manager with callbacks provided by MenuActions controller
        self.menu_actions = MenuActions(self)
        menu_callbacks = {
            "save_preset": self.menu_actions.save_preset,
            "load_preset": self.menu_actions.load_preset,
            "export_config": self.menu_actions.export_config,
            "import_config": self.menu_actions.import_config,
            "export_for_llm": self.menu_actions.export_for_llm,
            "export_for_llm_creation": self.menu_actions.export_for_llm_creation,
            "bulk_prompt_generator": self.menu_actions.bulk_prompt_generator,
            "import_from_text": self.menu_actions.import_from_text,
            "reload_data": self.reload_data,
            "undo": self.menu_actions.undo,
            "redo": self.menu_actions.redo,
            "clear_all_characters": self.menu_actions.clear_all_characters,
            "reset_all_outfits": self.menu_actions.reset_all_outfits,
            "apply_same_pose_to_all": self.menu_actions.apply_same_pose_to_all,
            "toggle_character_gallery": lambda: None, # Disabled in Lite
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
            "gallery_visible": False, # Always false in Lite
        }

        self.menu_manager = MenuManager(self.root, menu_callbacks)

        # Build Toolbar
        self._build_toolbar()

        # Bind keyboard shortcuts
        self._bind_keyboard_shortcuts()

        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True)

        # Status bar at bottom
        try:
            tm = self.theme_manager
            theme = tm.themes.get(tm.current_theme, {})
            main_bg = theme.get("bg", "#121212")
            muted_fg = theme.get("border", "gray")
        except:
            main_bg = "#121212"
            muted_fg = "gray"

        self.status_bar = tk.Label(
            main_container,
            text="READY (LITE MODE)",
            anchor="w",
            bg=main_bg,
            fg=muted_fg,
            font=("Lexend", 8, "bold"),
            padx=15,
            pady=5
        )
        self.status_bar.pack(side="bottom", fill="x")

        # Create a paned window for main content
        try:
            panel_bg = ttk.Style().lookup("TFrame", "background")
        except:
            panel_bg = "#1e1e1e"

        self.main_paned = tk.PanedWindow(
            main_container, 
            orient="horizontal",
            bg=panel_bg,
            bd=0,
            sashwidth=6,
            sashrelief="flat",
            showhandle=False
        )
        self.main_paned.pack(side="top", fill="both", expand=True)

        # In Lite mode, we skip the gallery frame entirely
        self.gallery_frame = None
        self.gallery_visible = False
        
        # Class Dummy for compatibility
        class Dummy:
            def update_used_status(self, *args): pass
            def _refresh_display(self, *args): pass
        self.character_gallery = Dummy()

        # Left side: Lite Characters Tab (Directly in main area)
        self.characters_tab = LiteCharactersTab(
            self.main_paned,
            self.data_loader,
            self.theme_manager,
            self.character_controller,
            self.schedule_preview_update,
            self.reload_data,
            self._save_state_for_undo,
        )
        self.main_paned.add(self.characters_tab.tab, width=550, minsize=300)

        # Right side: Scrollable container for collapsible sections
        self.right_scroll_container = ScrollableCanvas(self.main_paned)
        self.main_paned.add(self.right_scroll_container, minsize=250) 
        right_frame = self.right_scroll_container.get_container()
        right_frame.columnconfigure(0, weight=1)

        SECTION_PAD_Y = (15, 20)
        INTERNAL_PAD_X = 15

        # Convenience controls row
        controls_frame = ttk.Frame(right_frame, style="TFrame")
        controls_frame.grid(row=0, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=(15, 0))
        
        def _set_all_collapsible(state):
            for section in [self.scene_panel, self.notes_panel, 
                           self.summary_panel, self.preview_collapsible]:
                section.set_opened(state)
            self.right_scroll_container.update_scroll_region()

        try:
            tm = self.theme_manager
            theme = tm.themes.get(tm.current_theme, {})
            panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
            muted_fg = theme.get("border", "gray")
        except:
            panel_bg = "#1e1e1e"
            muted_fg = "gray"

        self.collapse_all_btn = tk.Button(controls_frame, text="COLLAPSE ALL", 
                   command=lambda: _set_all_collapsible(False), 
                   bg=panel_bg, fg=muted_fg, borderwidth=0, relief="flat", font=("Lexend", 8, "bold"))
        self.collapse_all_btn.pack(side="right", padx=2)
        
        self.expand_all_btn = tk.Button(controls_frame, text="EXPAND ALL", 
                   command=lambda: _set_all_collapsible(True), 
                   bg=panel_bg, fg=muted_fg, borderwidth=0, relief="flat", font=("Lexend", 8, "bold"))
        self.expand_all_btn.pack(side="right", padx=2)

        # Scene section
        self.scene_panel = ScenePanel(
            right_frame, 
            self.data_loader, 
            self.theme_manager, 
            self.scenes,
            on_change_callback=self.schedule_preview_update,
            create_scene_callback=self._create_new_scene
        )
        self.scene_panel.grid(row=1, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=SECTION_PAD_Y)

        # Notes section
        self.notes_panel = NotesPanel(
            right_frame,
            self.data_loader,
            self.theme_manager,
            self.interactions,
            on_change_callback=self.schedule_preview_update,
            create_interaction_callback=self._create_new_interaction,
            get_selected_char_names=lambda: [c["name"] for c in self.characters_tab.get_selected_characters()]
        )
        self.notes_panel.grid(row=2, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=SECTION_PAD_Y)

        # Summary section
        self.summary_panel = SummaryPanel(
            right_frame,
            self.theme_manager,
            on_apply_callback=self._import_from_summary_box,
            on_import_callback=self.menu_actions.import_from_text
        )
        self.summary_panel.grid(row=3, column=0, sticky="ew", padx=INTERNAL_PAD_X, pady=SECTION_PAD_Y)

        # Preview panel
        self.preview_collapsible = CollapsibleFrame(right_frame, text="🔍 PROMPT PREVIEW", opened=True)
        self.preview_collapsible.grid(row=4, column=0, sticky="nsew", padx=INTERNAL_PAD_X, pady=(SECTION_PAD_Y[0], 20))
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

        self.preview_panel.set_callbacks(
            self._generate_prompt, self._validate_prompt, self.randomize_all
        )

        # Load data into characters_tab
        self.characters_tab.load_data(self.characters, self.base_prompts, self.poses, self.scenes)

    def _toggle_character_gallery(self):
        """No-op for Lite version."""
        pass

    def _build_toolbar(self):
        """Override to remove Gallery button."""
        toolbar_frame = ttk.Frame(self.root, style="TFrame")
        toolbar_frame.pack(side="top", fill="x", padx=4, pady=4)
        
        self.toolbar_buttons = []

        def add_tool_btn(parent, text, command, tooltip=None, width=None):
            try: 
                bg = parent.cget("background")
            except: 
                try: bg = ttk.Style().lookup("TFrame", "background")
                except: bg = "#121212"
            
            btn = tk.Button(
                parent, text=text, command=command,
                bg=bg, relief="flat", highlightthickness=2, padx=10,
                font=("Lexend", 9)
            )
            btn._base_bg = bg
            
            def on_btn_enter(e, b=btn):
                try:
                    theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
                    hbg = theme.get("hover_bg", "#333333")
                    b.config(bg=hbg)
                except: pass
            def on_btn_leave(e, b=btn):
                b.config(bg=getattr(b, "_base_bg", "#121212"))
            
            btn.bind("<Enter>", on_btn_enter)
            btn.bind("<Leave>", on_btn_leave)
            
            if width:
                btn.config(width=width)
            btn.pack(side="left", padx=2)
            if tooltip:
                create_tooltip(btn, tooltip)
            
            self.toolbar_buttons.append(btn)
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
        
        ttk.Frame(toolbar_frame).pack(side="left", fill="x", expand=True)