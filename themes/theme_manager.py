# -*- coding: utf-8 -*-
"""Theme management for the application."""

import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

from config import THEMES, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE
from utils import logger


def _parse_themes_md(path: str):
    """Parse a simple themes.md file format.

    Format: sections headed by '## Theme Name' followed by a ```yaml block
    containing simple `key: value` lines. Returns dict[name] = {k: v}
    """
    themes = {}
    if not os.path.exists(path):
        return themes

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    name = None
    in_yaml = False
    buf = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("## "):
            # flush previous
            if name and buf:
                themes[name] = _parse_yaml_like(buf)
            name = s[3:].strip()
            buf = []
            in_yaml = False
            continue
        if s.startswith("```"):
            # toggle yaml block
            if not in_yaml:
                in_yaml = True
                buf = []
            else:
                # close block
                in_yaml = False
                if name:
                    themes[name] = _parse_yaml_like(buf)
                buf = []
            continue
        if in_yaml:
            buf.append(ln.rstrip("\n"))

    # flush if file ended while in block
    if name and buf:
        themes[name] = _parse_yaml_like(buf)

    return themes


def _parse_yaml_like(lines):
    d = {}
    for ln in lines:
        # simple key: value parsing
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        if ":" not in ln:
            continue
        k, v = ln.split(":", 1)
        k = k.strip()
        v = v.strip()
        # strip quotes
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        d[k] = v
    return d


def _write_themes_md(path: str, themes: dict):
    lines = [
        "# Themes (auto-generated)\n",
        "# You can edit or add themes below. Each theme is a header and a YAML block.\n\n",
    ]
    for name in sorted(themes.keys()):
        lines.append(f"## {name}\n")
        lines.append("```yaml\n")
        vals = themes[name]
        for k, v in vals.items():
            # ensure value is quoted to be safe
            lines.append(f'{k}: "{v}"\n')
        lines.append("```\n\n")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


class ThemeManager:
    """Manages application themes and applies them to widgets."""

    def __init__(self, root, style):
        """Initialize theme manager.

        Args:
            root: Tkinter root window
            style: ttk.Style instance
        """
        self.root = root
        self.style = style
        self.current_theme = None
        self.themes = THEMES
        self.default_font_family = DEFAULT_FONT_FAMILY
        self.default_font_size = DEFAULT_FONT_SIZE
        self.scale_factor = 1.0  # Default scale

        # Set base theme
        try:
            self.style.theme_use("clam")
        except tk.TclError as e:
            logger.debug(f"Could not set clam theme: {e}")

        # Load additional themes from data/themes.md if present
        try:
            md_path = os.path.join(os.getcwd(), "data", "themes.md")
            md_themes = _parse_themes_md(md_path)
            # Merge: md themes override builtins
            if md_themes:
                merged = dict(self.themes)
                merged.update(md_themes)
                self.themes = merged
        except Exception:
            logger.debug("Failed to load themes from themes.md")

    def apply_theme(self, theme_name):
        """Apply a theme to all ttk styles and return theme colors.

        Args:
            theme_name: Name of theme from THEMES dict

        Returns:
            dict: Theme color dictionary
        """
        if theme_name not in self.themes:
            theme_name = "Dark"

        self.current_theme = theme_name
        theme = self.themes[theme_name]

        # Update all ttk styles
        self._update_ttk_styles(theme)

        # Apply background to root window
        self.root.config(bg=theme["bg"])

        return theme

    def add_theme(self, name: str, theme_vals: dict):
        """Add or update a theme at runtime.

        Args:
            name: Theme name
            theme_vals: Dictionary of theme values (colors)
        """
        try:
            self.themes[name] = theme_vals
        except Exception:
            logger.exception(f"Failed to add theme {name}")

    def save_themes_md(self, path: str = None):
        """Write non-default and overridden themes to `data/themes.md`.

        The file will contain themes that are either new or differ from built-in defaults.
        """
        try:
            if path is None:
                path = os.path.join(os.getcwd(), "data", "themes.md")
            # Only persist themes that are new or different from built-ins
            built_in = THEMES
            to_write = {}
            for name, vals in self.themes.items():
                if name not in built_in or built_in.get(name) != vals:
                    to_write[name] = vals
            _write_themes_md(path, to_write)
        except Exception:
            logger.exception("Failed to save themes to themes.md")

    def migrate_from_prefs(self, prefs):
        """Migrate `custom_themes` from PreferencesManager into data/themes.md.

        This is intended as a one-time migration: after writing to themes.md,
        the prefs key `custom_themes` will be cleared (set to empty dict) so
        the migration won't re-run.
        Returns True if migration performed, False otherwise.
        """
        try:
            custom = prefs.get("custom_themes", {}) or {}
            if not custom:
                return False

            # Read existing md themes and merge (md earlier than prefs)
            md_path = os.path.join(os.getcwd(), "data", "themes.md")
            md_themes = _parse_themes_md(md_path) or {}
            merged = dict(md_themes)
            # prefs should override md
            merged.update(custom)

            # Write merged themes back to md
            _write_themes_md(md_path, merged)

            # Clear prefs custom_themes to avoid re-migration
            try:
                prefs.set("custom_themes", {})
            except Exception:
                # Best-effort: if prefs.set fails, continue
                logger.debug("Failed to clear custom_themes from prefs after migration")

            # Update runtime themes map
            self.themes = dict(THEMES)
            self.themes.update(merged)

            return True
        except Exception:
            logger.exception("Failed to migrate themes from prefs to themes.md")
            return False

    def reload_md_themes(self, path: str = None):
        """Reload themes from `data/themes.md` and merge them into runtime themes.

        This re-parses the markdown file and updates `self.themes` so callers
        (e.g., a Reload action) can pick up manual edits to the file.
        """
        try:
            if path is None:
                path = os.path.join(os.getcwd(), "data", "themes.md")
            md_themes = _parse_themes_md(path) or {}
            # Merge: md themes override built-ins but preserve other runtime themes
            merged = dict(THEMES)
            merged.update(md_themes)
            # Preserve any runtime-only themes
            for k, v in list(self.themes.items()):
                if k not in merged:
                    merged[k] = v

            self.themes = merged
            return True
        except Exception:
            logger.exception("Failed to reload themes.md into ThemeManager")
            return False

    def remove_theme(self, name: str):
        """Remove a theme if it exists.

        Args:
            name: Theme name
        """
        try:
            if name in self.themes:
                del self.themes[name]
        except Exception:
            logger.exception(f"Failed to remove theme {name}")

    def _update_ttk_styles(self, theme):
        """Update all ttk widget styles with theme colors."""
        bg = theme["bg"]
        fg = theme["fg"]
        panel_bg = theme.get("panel_bg", bg)
        text_bg = theme["text_bg"]
        accent = theme["accent"]
        accent_hover = theme.get("accent_hover", accent)
        border = theme["border"]
        selected_bg = theme.get("selected_bg", text_bg)
        
        # Scale fonts
        def s(size):
            return int(size * self.scale_factor)

        # General Layout Elements - Refactor 1
        self.style.configure("TFrame", background=panel_bg, borderwidth=0, highlightthickness=0)
        self.style.configure("TLabel", background=panel_bg, foreground=fg, font=(None, s(9)))
        self.style.configure("TCheckbutton", background=panel_bg, foreground=fg, font=(None, s(9)))

        # Custom widget styles
        self.style.configure("Collapsible.TFrame", background=panel_bg, borderwidth=0, relief="flat")
        self.style.configure("Card.TFrame", background=panel_bg, borderwidth=1, bordercolor=border, relief="solid")
        self.style.configure("Selected.Card.TFrame", background=panel_bg, borderwidth=2, bordercolor=accent, relief="solid")
        
        # Typography-based Headers (Refactor 3)
        self.style.configure(
            "Title.TLabel", 
            font=(None, s(16), "bold"), 
            background=panel_bg, 
            foreground=accent,
            padding=(0, s(5))
        )

        # Notebook tabs with better selection contrast
        self.style.configure("TNotebook", background=bg, bordercolor=border, borderwidth=0)
        self.style.configure(
            "TNotebook.Tab", background=bg, foreground=fg, bordercolor=border, padding=[s(10), s(4)],
            font=(None, s(9))
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", selected_bg), ("active", text_bg)],
            foreground=[("selected", accent), ("active", fg)],
        )

        # Combobox/Entry with better contrast and visibility
        self.style.configure(
            "TCombobox",
            fieldbackground=text_bg,
            foreground=fg,
            background=bg,
            selectbackground=accent,
            selectforeground=bg,
            bordercolor=border,
            borderwidth=1,
            arrowcolor=fg,
            font=(None, s(9))
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", text_bg), ("disabled", bg)],
            foreground=[("readonly", fg), ("disabled", border)],
            bordercolor=[("active", accent), ("focus", accent)],
            arrowcolor=[("disabled", border)],
        )

        self.style.configure(
            "TEntry",
            fieldbackground=text_bg,
            foreground=fg,
            background=bg,
            selectbackground=accent,
            selectforeground=bg,
            bordercolor=border,
            borderwidth=1,
            font=(None, s(9))
        )
        self.style.map(
            "TEntry",
            fieldbackground=[("disabled", bg)],
            foreground=[("disabled", border)],
            bordercolor=[("active", accent), ("focus", accent)],
        )

        # Primary Button (Refactor 2: High Importance)
        self.style.configure(
            "TButton",
            background=accent,
            foreground=text_bg,
            bordercolor=accent,
            borderwidth=1,
            padding=[s(12), s(5)],
            font=(None, s(9), "bold")
        )
        self.style.map(
            "TButton",
            background=[("active", accent_hover), ("pressed", border)],
            foreground=[("active", text_bg), ("pressed", text_bg)],
            bordercolor=[("active", accent_hover), ("pressed", border)],
        )

        # Ghost Button (Refactor 2: Medium Importance)
        self.style.configure(
            "Ghost.TButton",
            background=panel_bg,
            foreground=accent,
            bordercolor=accent,
            borderwidth=1,
            padding=[s(10), s(4)],
            font=(None, s(9))
        )
        self.style.map(
            "Ghost.TButton",
            background=[("active", selected_bg)],
            foreground=[("active", accent_hover)],
            bordercolor=[("active", accent_hover)],
        )

        # Link Button (Refactor 2: Low Importance)
        self.style.configure(
            "Link.TButton",
            background=panel_bg,
            foreground=fg,
            bordercolor=panel_bg,
            borderwidth=0,
            padding=[s(5), s(2)],
            font=(None, s(9))
        )
        self.style.map(
            "Link.TButton",
            foreground=[("active", accent)],
            background=[("active", panel_bg)],
        )

        # Accent Button (deprecated in favor of TButton primary, but keeping for compat)
        self.style.configure(
            "Accent.TButton",
            background=accent,
            foreground=text_bg,
            bordercolor=accent,
            borderwidth=1,
            padding=[s(12), s(5)],
            font=(None, s(9), "bold")
        )

        # Label Frames (Refactor 1: The Flattening)
        self.style.configure(
            "TLabelframe",
            background=panel_bg,
            foreground=accent,
            bordercolor=border,
            borderwidth=0,
            relief="flat",
        )
        self.style.configure(
            "TLabelframe.Label", 
            background=panel_bg, 
            foreground=accent, 
            font=(None, s(11), "bold"),
            padding=(s(5), 0)
        )

        # Bold and Accent label styles for small inline headings and badges
        self.style.configure("Bold.TLabel", font=(None, s(9), "bold"), background=panel_bg, foreground=fg)
        self.style.configure("Accent.TLabel", font=(None, s(9)), background=panel_bg, foreground=accent)
        # Muted label for small helper text
        self.style.configure("Muted.TLabel", font=(None, s(8)), background=panel_bg, foreground=border)
        
        # Tag-style (Refactor 4: Outlined Pill)
        tag_fg = accent
        tag_bg = panel_bg
        self.style.configure(
            "Tag.TLabel",
            font=(None, s(8), "bold"),
            background=tag_bg,
            foreground=tag_fg,
            padding=(s(8), s(2)),
            borderwidth=1,
            relief="solid",
            bordercolor=accent
        )

        # Tag-style button for interactive chips (Refactor 4: Outlined Pill)
        try:
            self.style.configure(
                "Tag.TButton",
                font=(None, s(8), "bold"),
                background=tag_bg,
                foreground=tag_fg,
                padding=[s(8), s(2)],
                bordercolor=accent,
                borderwidth=1,
                relief="solid"
            )
            self.style.map(
                "Tag.TButton",
                background=[("active", accent), ("pressed", accent_hover)],
                foreground=[("active", panel_bg), ("pressed", panel_bg)],
                bordercolor=[("active", accent), ("pressed", accent_hover)],
            )
        except Exception:
            pass

        # Scrollbar Style - Refactor 3: Dynamic Theme-aware Scrollbars
        self.style.configure(
            "Themed.Vertical.TScrollbar",
            background=text_bg,
            troughcolor=bg,
            bordercolor=border,
            arrowcolor=accent,
            width=10,
            borderwidth=0
        )
        self.style.map(
            "Themed.Vertical.TScrollbar",
            background=[("active", accent), ("pressed", accent_hover)],
            arrowcolor=[("active", bg)]
        )

        # Legacy/Standard mapping
        self.style.configure(
            "Vertical.TScrollbar",
            background=text_bg,
            troughcolor=bg,
            bordercolor=border,
            borderwidth=0,
            arrowcolor=fg,
        )

    def apply_text_widget_theme(self, widget, theme):
        """Apply theme colors to a tk.Text widget. (Refactor 1: Global Input Styling)"""
        input_bg = theme["text_bg"]
        input_fg = theme["text_fg"]
        accent = theme["accent"]
        
        # Dynamic caret color
        caret_color = "white" if self._is_dark(input_bg) else "black"
        
        widget.config(
            bg=input_bg,
            fg=input_fg,
            insertbackground=caret_color,
            selectbackground=accent,
            selectforeground=theme["bg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=theme["border"],
            highlightcolor=accent,
            padx=10,
            pady=10
        )

    def apply_entry_theme(self, widget, theme):
        """Apply theme colors to a ttk.Entry or tk.Entry widget. (Refactor 1)"""
        input_bg = theme["text_bg"]
        input_fg = theme["text_fg"]
        accent = theme["accent"]
        caret_color = "white" if self._is_dark(input_bg) else "black"
        
        if isinstance(widget, ttk.Entry):
            # For ttk.Entry, we style the TEntry element via style.configure
            # but we can force the insertbackground here
            try:
                widget.config(insertbackground=caret_color)
            except Exception: pass
        else:
            # tk.Entry
            widget.config(
                bg=input_bg,
                fg=input_fg,
                insertbackground=caret_color,
                selectbackground=accent,
                selectforeground=theme["bg"],
                relief="flat",
                highlightthickness=1,
                highlightbackground=theme["border"],
                highlightcolor=accent
            )

    def _is_dark(self, hex_color):
        """Simple check if a hex color is dark."""
        if not hex_color or not hex_color.startswith("#"):
            return True
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            # HSP color model formula
            hsp = (0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b)) ** 0.5
            return hsp < 127.5
        except Exception:
            return True

    def apply_preview_theme(self, widget, theme):
        """Apply theme colors to preview widget with formatted tags. (Refactor 1)"""
        input_bg = theme["preview_bg"]
        input_fg = theme["preview_fg"]
        accent = theme["accent"]
        caret_color = "white" if self._is_dark(input_bg) else "black"
        
        # Base widget colors
        widget.config(
            bg=input_bg,
            fg=input_fg,
            insertbackground=caret_color,
            selectbackground=accent,
            selectforeground=input_fg,
            relief="flat",
            highlightthickness=1,
            highlightbackground=theme["border"],
            highlightcolor=accent,
            padx=15,
            pady=15
        )

        # Get current font size safely
        font_family = self.default_font_family
        try:
            font_size = tkfont.Font(font=widget.cget("font")).cget("size")
        except (tk.TclError, KeyError, AttributeError):
            font_size = self.default_font_size

        # Configure text tags
        widget.tag_config("bold", font=(font_family, font_size, "bold"))
        widget.tag_config(
            "title",
            font=(font_family, font_size + 2 if font_size > 0 else 14, "bold"),
            foreground=theme.get("accent", "#66d9ef"),
        )
        widget.tag_config("separator", foreground=theme.get("border", "#49483e"))
        widget.tag_config(
            "error",
            foreground="red",
            background=theme["text_bg"],
            font=(font_family, font_size, "bold"),
        )
        # Section labels (smaller than title, bold). Use accent if available, fall back to preview_fg
        widget.tag_config(
            "section_label",
            font=(font_family, font_size, "bold"),
            foreground=theme.get("accent", theme.get("preview_fg", theme.get("fg"))),
        )
        # Additional tags for richer formatting
        widget.tag_config(
            "h1",
            font=(font_family, font_size + 3 if font_size > 0 else 16, "bold"),
            foreground=theme.get("accent", theme.get("preview_fg")),
        )
        widget.tag_config(
            "h2",
            font=(font_family, font_size + 2 if font_size > 0 else 14, "bold"),
            foreground=theme.get("accent", theme.get("preview_fg")),
        )
        widget.tag_config(
            "h3",
            font=(font_family, font_size + 1 if font_size > 0 else 12, "bold"),
            foreground=theme.get("accent", theme.get("preview_fg")),
        )
        widget.tag_config(
            "italic",
            font=(font_family, font_size, "italic"),
            foreground=theme.get("preview_fg", theme.get("fg")),
        )
        widget.tag_config(
            "code",
            font=("Courier", max(9, font_size - 1)),
            foreground=theme.get("code_fg", theme.get("preview_fg", theme.get("fg"))),
            background=theme.get("code_bg", theme.get("text_bg")),
        )
        widget.tag_config("list_item", foreground=theme.get("preview_fg", theme.get("fg")))

    def apply_canvas_theme(self, canvas, theme):
        """Apply theme background to a tk.Canvas widget.

        Args:
            canvas: tk.Canvas widget
            theme: Theme color dictionary
        """
        # Use text_bg for better contrast with content
        canvas.config(bg=theme.get("text_bg", theme["bg"]))

    def apply_container_theme(self, widget, theme):
        """Apply theme background to a container (tk.Frame)."""
        panel_bg = theme.get("panel_bg", theme["bg"])
        widget.config(bg=panel_bg)

    def apply_listbox_theme(self, widget, theme):
        """Apply theme colors to a tk.Listbox widget."""
        text_bg = theme["text_bg"]
        text_fg = theme["text_fg"]
        accent = theme["accent"]
        
        widget.config(
            bg=text_bg,
            fg=text_fg,
            selectbackground=accent,
            selectforeground=theme["bg"],
            borderwidth=0,
            highlightthickness=0,
            activestyle="none"
        )
