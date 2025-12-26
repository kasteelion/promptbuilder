# -*- coding: utf-8 -*-
"""Menu bar management for the application."""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Dict

from config import THEMES


class MenuManager:
    """Manages the application menu bar and all menu items.

    Separates menu creation and management from the main window,
    making the code more maintainable and testable.
    """

    def __init__(self, root: tk.Tk, callbacks: Dict[str, Callable]):
        """Initialize menu manager.

        Args:
            root: Tkinter root window
            callbacks: Dictionary of callback functions for menu actions
                Required keys:
                - save_preset, load_preset
                - export_config, import_config
                - undo, redo
                - clear_all_characters, reset_all_outfits, apply_same_pose_to_all
                - toggle_character_gallery
                - increase_font, decrease_font, reset_font
                - randomize_all
                - change_theme, toggle_auto_theme
                - show_characters_summary, show_welcome, show_shortcuts, show_about
                - on_closing
        """
        self.root = root
        self.callbacks = callbacks

        # Variables that need to be accessible
        self.theme_var = tk.StringVar(value=callbacks.get("initial_theme", "Dark"))
        self.ui_scale_var = tk.StringVar(value=callbacks.get("initial_ui_scale", "Medium"))
        self.auto_theme_var = tk.BooleanVar(value=callbacks.get("auto_theme_enabled", False))
        self.gallery_visible_var = tk.BooleanVar(value=callbacks.get("gallery_visible", True))

        # Create menu bar
        self.menubar = tk.Menu(root)
        root.config(menu=self.menubar)

        # Build menus
        self._build_file_menu()
        self._build_edit_menu()
        self._build_characters_menu()
        self._build_view_menu()
        self._build_tools_menu()
        self._build_help_menu()

    def _build_file_menu(self):
        """Build File menu."""
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(
            label="💾 Save Preset...",
            command=self.callbacks["save_preset"],
            accelerator="Ctrl+Shift+S",
        )
        file_menu.add_command(
            label="📂 Load Preset...",
            command=self.callbacks["load_preset"],
            accelerator="Ctrl+Shift+O",
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="📤 Export Configuration...", command=self.callbacks["export_config"]
        )
        file_menu.add_command(
            label="🤖 Export for LLM (Context Injection)...", command=self.callbacks["export_for_llm"]
        )
        file_menu.add_command(
            label="📥 Import Configuration...", command=self.callbacks["import_config"]
        )
        file_menu.add_command(
            label="📝 Import from Text...", command=self.callbacks["import_from_text"]
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="🔄 Reload Data", command=self.callbacks["reload_data"]
        )

        file_menu.add_separator()

        file_menu.add_command(label="🚪 Exit", command=self.callbacks["on_closing"])

    def _build_edit_menu(self):
        """Build Edit menu."""
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

        edit_menu.add_command(label="↩️ Undo", command=self.callbacks["undo"], accelerator="Ctrl+Z")
        edit_menu.add_command(label="↪️ Redo", command=self.callbacks["redo"], accelerator="Ctrl+Y")

    def _build_characters_menu(self):
        """Build Characters menu."""
        char_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Characters", menu=char_menu)

        char_menu.add_command(
            label="❌ Clear All Characters", command=self.callbacks["clear_all_characters"]
        )
        char_menu.add_command(
            label="👕 Reset All Outfits", command=self.callbacks["reset_all_outfits"]
        )
        char_menu.add_command(
            label="🧘 Apply Same Pose to All", command=self.callbacks["apply_same_pose_to_all"]
        )

    def _build_tools_menu(self):
        """Build Tools menu."""
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)

        tools_menu.add_command(
            label="🎲 Randomize All", command=self.callbacks["randomize_all"], accelerator="Alt+R"
        )

    def _build_view_menu(self):
        """Build View menu with theme and display options."""
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)

        # Character Gallery toggle
        view_menu.add_checkbutton(
            label="👥 Show Character Gallery",
            variable=self.gallery_visible_var,
            command=self.callbacks["toggle_character_gallery"],
            accelerator="Ctrl+G",
        )
        view_menu.add_separator()

        # Font controls
        view_menu.add_command(
            label="🔍 Increase Font Size",
            command=self.callbacks["increase_font"],
            accelerator="Ctrl++",
        )
        view_menu.add_command(
            label="🔍 Decrease Font Size",
            command=self.callbacks["decrease_font"],
            accelerator="Ctrl+-",
        )
        view_menu.add_command(
            label="🔄 Reset Font Size", command=self.callbacks["reset_font"], accelerator="Ctrl+0"
        )

        view_menu.add_separator()

        # Theme submenu
        self._build_theme_submenu(view_menu)

        # UI Scale submenu
        self._build_ui_scale_submenu(view_menu)

        # Auto theme detection
        view_menu.add_separator()
        view_menu.add_checkbutton(
            label="⚙️ Auto-detect OS Theme",
            variable=self.auto_theme_var,
            command=self.callbacks["toggle_auto_theme"],
        )

    def _build_ui_scale_submenu(self, parent_menu):
        """Build UI scaling submenu.

        Args:
            parent_menu: Parent menu to add scaling submenu to
        """
        scale_menu = tk.Menu(parent_menu, tearoff=0)
        parent_menu.add_cascade(label="UI Scale", menu=scale_menu)

        scales = ["Small", "Medium", "Large", "Extra Large"]
        for scale in scales:
            scale_menu.add_radiobutton(
                label=scale,
                variable=self.ui_scale_var,
                value=scale,
                command=lambda s=scale: self.callbacks["change_ui_scale"](s),
            )

    def _build_theme_submenu(self, parent_menu):
        """Build theme selection submenu.

        Args:
            parent_menu: Parent menu to add theme submenu to
        """
        self.theme_menu = tk.Menu(parent_menu, tearoff=0)
        parent_menu.add_cascade(label="Theme", menu=self.theme_menu)

        # Populate menu entries
        self._populate_theme_menu()

    def _populate_theme_menu(self):
        """(Re)build the theme submenu entries and icons."""
        # Clear existing items if any
        try:
            self.theme_menu.delete(0, "end")
        except Exception:
            pass

        # Use a supplier callback if provided so themes can be dynamic
        supplier = self.callbacks.get("get_themes", lambda: THEMES)
        themes = supplier() or THEMES

        # Prepare small color swatch images for each theme (keep references to avoid GC)
        self._theme_icons = {}
        for theme_name, theme_vals in themes.items():
            color = theme_vals.get("accent") or theme_vals.get("preview_fg") or "#888888"
            try:
                img = tk.PhotoImage(width=12, height=12)
                img.put(color, to=(0, 0, 12, 12))
            except Exception:
                img = None
            self._theme_icons[theme_name] = img

        for theme_name in sorted(themes.keys()):
            img = self._theme_icons.get(theme_name)
            if img is not None:
                self.theme_menu.add_radiobutton(
                    label=theme_name,
                    variable=self.theme_var,
                    value=theme_name,
                    image=img,
                    compound="left",
                    command=lambda t=theme_name: self.callbacks["change_theme"](t),
                )
            else:
                self.theme_menu.add_radiobutton(
                    label=theme_name,
                    variable=self.theme_var,
                    value=theme_name,
                    command=lambda t=theme_name: self.callbacks["change_theme"](t),
                )

        # Editor entry
        self.theme_menu.add_separator()
        self.theme_menu.add_command(
            label="Edit Themes...",
            command=self.callbacks.get(
                "open_theme_editor",
                lambda: messagebox.showinfo("Edit Themes", "No theme editor available"),
            ),
        )

    def refresh_theme_menu(self):
        """Public method to refresh theme submenu after runtime changes."""
        try:
            self._populate_theme_menu()
        except Exception:
            # best effort
            pass

    def _build_help_menu(self):
        """Build Help menu."""
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        help_menu.add_command(
            label="📊 Characters Summary", command=self.callbacks["show_characters_summary"]
        )
        help_menu.add_command(
            label="👗 Outfits Summary", command=self.callbacks["show_outfits_summary"]
        )
        help_menu.add_command(
            label="🎨 Team Colors Summary", command=self.callbacks["show_color_schemes_summary"]
        )
        help_menu.add_command(
            label="🏷️ Tag Distribution Summary", command=self.callbacks["show_tag_summary"]
        )

        help_menu.add_separator()

        help_menu.add_command(label="👋 Show Welcome Screen", command=self.callbacks["show_welcome"])
        help_menu.add_command(label="⌨️ Keyboard Shortcuts", command=self.callbacks["show_shortcuts"])

        help_menu.add_separator()

        help_menu.add_command(label="ℹ️ About", command=self.callbacks["show_about"])

    def set_theme(self, theme_name: str):
        """Set the current theme selection.

        Args:
            theme_name: Name of theme to select
        """
        self.theme_var.set(theme_name)

    def get_theme(self) -> str:
        """Get the current theme selection.

        Returns:
            Current theme name
        """
        return self.theme_var.get()

    def set_auto_theme(self, enabled: bool):
        """Set auto theme detection state.

        Args:
            enabled: Whether auto theme detection is enabled
        """
        self.auto_theme_var.set(enabled)

    def get_auto_theme(self) -> bool:
        """Get auto theme detection state.

        Returns:
            True if auto theme detection is enabled
        """
        return self.auto_theme_var.get()

    def set_gallery_visible(self, visible: bool):
        """Set gallery visibility state.

        Args:
            visible: Whether gallery is visible
        """
        self.gallery_visible_var.set(visible)

    def get_gallery_visible(self) -> bool:
        """Get gallery visibility state.

        Returns:
            True if gallery is visible
        """
        return self.gallery_visible_var.get()
