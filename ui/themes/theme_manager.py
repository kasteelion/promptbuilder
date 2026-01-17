# -*- coding: utf-8 -*-
"""Theme management for the application."""

import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

from core.config import THEMES, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE
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
        
        # Registry for theme-aware widgets: list of (widget, callback)
        self._registry = []

        # Set base theme
        try:
            self.style.theme_use("clam")
        except tk.TclError as e:
            logger.debug(f"Could not set clam theme: {e}")

        # Load additional themes from data/themes.md if present
        try:
            md_path = os.path.join(os.getcwd(), "data", "lists", "themes.md")
            md_themes = _parse_themes_md(md_path)
            # Merge: md themes override builtins
            if md_themes:
                merged = dict(self.themes)
                merged.update(md_themes)
                self.themes = merged
        except Exception:
            logger.debug("Failed to load themes from themes.md")

    def register(self, widget, callback):
        """Register a widget to receive theme updates.

        Args:
            widget: tk.Widget instance
            callback: Function to call with (theme_dict)
        """
        self._registry.append((widget, callback))
        
        # Auto-unregister on destruction
        widget.bind("<Destroy>", lambda e: self.unregister(widget), add="+")
        
        # Apply current theme immediately if available
        if self.current_theme and self.current_theme in self.themes:
            try:
                callback(self.themes[self.current_theme])
            except Exception:
                logger.exception(f"Failed initial theme apply for {widget}")

    def unregister(self, widget):
        """Remove a widget from the theme registry."""
        self._registry = [(w, c) for w, c in self._registry if w != widget]

    def _notify_registry(self, theme):
        """Notify all registered widgets of a theme change."""
        to_remove = []
        for widget, callback in self._registry:
            try:
                if widget.winfo_exists():
                    callback(theme)
                else:
                    to_remove.append(widget)
            except (tk.TclError, Exception):
                to_remove.append(widget)
        
        # Clean up stale widgets
        for w in to_remove:
            self.unregister(w)

    def register_text_widget(self, widget):
        """Convenience to register a tk.Text widget for themed updates."""
        self.register(widget, lambda t: self.apply_text_widget_theme(widget, t))

    def register_entry(self, widget):
        """Convenience to register an Entry widget for themed updates."""
        self.register(widget, lambda t: self.apply_entry_theme(widget, t))

    def register_canvas(self, widget):
        """Convenience to register a Canvas widget for themed updates."""
        self.register(widget, lambda t: self.apply_canvas_theme(widget, t))

    def register_preview(self, widget):
        """Convenience to register the preview text widget."""
        self.register(widget, lambda t: self.apply_preview_theme(widget, t))

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
        
        # Notify registered widgets
        self._notify_registry(theme)

        return theme

    def theme_toplevel(self, window, theme=None):
        """Apply theme background and styles to a Toplevel window."""
        # Attach self for children to find
        window.theme_manager = self

        if theme is None:
            if self.current_theme in self.themes:
                theme = self.themes[self.current_theme]
            else:
                return

        bg = theme.get("bg", "#121212")
        window.config(bg=bg)
        
        # Recursive apply to frames
        def _theme_recursive(parent):
            for child in parent.winfo_children():
                if isinstance(child, (tk.Frame, tk.LabelFrame)) and not isinstance(child, (ttk.Frame, ttk.LabelFrame)):
                    child.config(bg=theme.get("panel_bg", bg))
                elif isinstance(child, (tk.Label)) and not isinstance(child, (ttk.Label)):
                    child.config(bg=theme.get("panel_bg", bg), fg=theme.get("fg", "#ffffff"))
                elif isinstance(child, tk.Canvas):
                    self.apply_canvas_theme(child, theme)
                elif isinstance(child, tk.Text):
                    self.apply_text_widget_theme(child, theme)
                elif isinstance(child, (tk.Entry, ttk.Entry)):
                    self.apply_entry_theme(child, theme)
                elif isinstance(child, tk.Listbox):
                    self.apply_listbox_theme(child, theme)
                
                if child.winfo_children():
                    _theme_recursive(child)
        
        _theme_recursive(window)

    def _get_hover_color(self, color):
        """Derive a hover color from a base color."""
        # If it's dark, make it lighter. If it's light, make it darker.
        is_dark = self._is_dark(color)
        try:
            color = color.lstrip('#')
            r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            
            factor = 1.2 if is_dark else 0.8
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception:
            return "#333333" if is_dark else "#cccccc"

    def _update_ttk_styles(self, theme):
        """Update all ttk widget styles with theme colors."""
        # Principal Colors
        bg = theme.get("bg", "#121212")
        fg = theme.get("fg", "#ffffff")
        
        # Sectional Colors (with intelligent fallbacks to avoid white/gray leaks)
        panel_bg = theme.get("panel_bg", bg)
        text_bg = theme.get("text_bg", bg)
        text_fg = theme.get("text_fg", fg)
        accent = theme.get("accent", fg)
        accent_hover = theme.get("accent_hover", accent)
        border = theme.get("border", bg)
        selected_bg = theme.get("selected_bg", text_bg)
        
        # Derive additional colors if missing
        if "hover_bg" not in theme:
            theme["hover_bg"] = theme.get("selected_bg", self._get_hover_color(panel_bg))
        if "placeholder_fg" not in theme:
            theme["placeholder_fg"] = "#666666" if self._is_dark(text_bg) else "#999999"
        
        # Scale fonts
        def s(size):
            return int(size * self.scale_factor)

        # General Layout Elements
        self.style.configure("TFrame", background=panel_bg, borderwidth=0, highlightthickness=0)
        self.style.configure("TLabel", background=panel_bg, foreground=fg, font=("Lexend", s(9)))
        self.style.configure("TCheckbutton", background=panel_bg, foreground=fg, font=("Lexend", s(9)))
        
        # Explicit background for main application containers
        self.style.configure("Main.TFrame", background=bg)
        self.style.configure("Panel.TFrame", background=panel_bg)

        # Custom widget styles
        self.style.configure("Collapsible.TFrame", background=panel_bg, borderwidth=0, relief="flat")
        self.style.configure("Card.TFrame", background=panel_bg, borderwidth=1, bordercolor=border, relief="solid")
        self.style.configure("Selected.Card.TFrame", background=panel_bg, borderwidth=2, bordercolor=accent, relief="solid")
        
        # Typography-based Headers
        self.style.configure(
            "Title.TLabel", 
            font=("Lexend", s(11), "bold"), 
            background=panel_bg, 
            foreground=accent,
            padding=(0, s(5))
        )

        # Notebook tabs
        self.style.configure("TNotebook", background=bg, bordercolor=border, borderwidth=0)
        self.style.configure(
            "TNotebook.Tab", background=bg, foreground=fg, bordercolor=border, padding=[s(10), s(4)],
            font=("Lexend", s(9))
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", selected_bg), ("active", text_bg)],
            foreground=[("selected", accent), ("active", fg)],
        )

        # Combobox/Entry
        self.style.configure(
            "TCombobox",
            fieldbackground=text_bg,
            foreground=text_fg,
            background=bg,
            selectbackground=accent,
            selectforeground=bg,
            bordercolor=border,
            borderwidth=1,
            arrowcolor=fg,
            font=("Lexend", s(9))
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", text_bg), ("disabled", bg)],
            foreground=[("readonly", text_fg), ("disabled", border)],
            bordercolor=[("active", accent), ("focus", accent)],
            arrowcolor=[("disabled", border)],
        )

        self.style.configure(
            "TEntry",
            fieldbackground=text_bg,
            foreground=text_fg,
            background=bg,
            selectbackground=accent,
            selectforeground=bg,
            bordercolor=border,
            borderwidth=1,
            font=("Lexend", s(9))
        )
        self.style.map(
            "TEntry",
            fieldbackground=[("disabled", bg)],
            foreground=[("disabled", border)],
            bordercolor=[("active", accent), ("focus", accent)],
        )

        # Primary Button
        self.style.configure(
            "TButton",
            background=accent,
            foreground=text_bg,
            bordercolor=accent,
            borderwidth=1,
            padding=[s(12), s(5)],
            font=("Lexend", s(9), "bold")
        )
        self.style.map(
            "TButton",
            background=[("active", accent_hover), ("pressed", border)],
            foreground=[("active", text_bg), ("pressed", text_bg)],
            bordercolor=[("active", accent_hover), ("pressed", border)],
        )

        # Accent Button (used for chips)
        self.style.configure(
            "Accent.TButton",
            background=panel_bg,
            foreground=accent,
            bordercolor=accent,
            borderwidth=1,
            padding=[s(8), s(2)],
            font=("Lexend", s(8), "bold")
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", accent), ("pressed", border)],
            foreground=[("active", text_bg), ("pressed", text_bg)],
            bordercolor=[("active", accent), ("pressed", border)],
        )

        # Ghost Button
        self.style.configure(
            "Ghost.TButton",
            background=panel_bg,
            foreground=accent,
            bordercolor=accent,
            borderwidth=1,
            padding=[s(10), s(4)],
            font=("Lexend", s(9))
        )
        self.style.map(
            "Ghost.TButton",
            background=[("active", selected_bg)],
            foreground=[("active", accent_hover)],
            bordercolor=[("active", accent_hover)],
        )

        # Link Button
        self.style.configure(
            "Link.TButton",
            background=panel_bg,
            foreground=fg,
            bordercolor=panel_bg,
            borderwidth=0,
            padding=[s(5), s(2)],
            font=("Lexend", s(9))
        )
        self.style.map(
            "Link.TButton",
            foreground=[("active", accent)],
            background=[("active", panel_bg)],
        )

        # Label Frames
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
            font=("Lexend", s(9), "bold"),
            padding=(s(5), 0)
        )

        # Utility labels
        self.style.configure("Bold.TLabel", font=("Lexend", s(9), "bold"), background=panel_bg, foreground=fg)
        self.style.configure("Accent.TLabel", font=("Lexend", s(9)), background=panel_bg, foreground=accent)
        self.style.configure("Muted.TLabel", font=("Lexend", s(8)), background=panel_bg, foreground=border)
        
        # Tags
        self.style.configure(
            "Tag.TLabel",
            font=("Lexend", s(8), "bold"),
            background=panel_bg,
            foreground=accent,
            padding=(s(8), s(2)),
            borderwidth=1,
            relief="solid",
            bordercolor=accent
        )

        # Scrollbar Style
        # Define a simplified layout without arrows for a modern look
        try:
            self.style.layout("Themed.Vertical.TScrollbar", [
                ('Vertical.Scrollbar.trough', {'children': [
                    ('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})
                ], 'sticky': 'ns'})
            ])
        except Exception:
            pass

        self.style.configure(
            "Themed.Vertical.TScrollbar",
            background=theme.get("scrollbar_thumb", border), # Use border or specific key for better visibility
            troughcolor=bg,
            bordercolor=border,
            arrowcolor=accent,
            width=10,
            borderwidth=0,
            relief="flat"
        )
        self.style.map(
            "Themed.Vertical.TScrollbar",
            background=[("active", accent), ("pressed", accent_hover)],
            arrowcolor=[("active", bg)]
        )

        # Standard mapping
        self.style.configure(
            "Vertical.TScrollbar",
            background=text_bg,
            troughcolor=bg,
            bordercolor=border,
            borderwidth=0,
            arrowcolor=fg,
        )

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
                path = os.path.join(os.getcwd(), "data", "lists", "themes.md")
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
            md_path = os.path.join(os.getcwd(), "data", "lists", "themes.md")
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
                path = os.path.join(os.getcwd(), "data", "lists", "themes.md")
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

    def get_current_theme_data(self):
        """Safe access to current theme dictionary."""
        return self.themes.get(self.current_theme, self.themes.get("Dark", {}))

    def get_panel_bg(self):
        """Get the panel background color for the current theme."""
        theme = self.get_current_theme_data()
        return theme.get("panel_bg", theme.get("bg", "#1e1e1e"))

    def get_fg(self):
        """Get the foreground color for the current theme."""
        theme = self.get_current_theme_data()
        return theme.get("fg", "#ffffff")

    def get_muted_fg(self):
        """Get the muted foreground color for the current theme."""
        theme = self.get_current_theme_data()
        return theme.get("muted_fg", theme.get("border", "#999999"))

    def get_accent(self):
        """Get the accent color for the current theme."""
        theme = self.get_current_theme_data()
        return theme.get("accent", "#0078d7")

    def apply_text_widget_theme(self, widget, theme):
        """Apply theme colors and font to a tk.Text widget."""
        input_bg = theme["text_bg"]
        input_fg = theme["text_fg"]
        accent = theme["accent"]
        
        # Dynamic caret color
        caret_color = "white" if self._is_dark(input_bg) else "black"
        
        # Scale font
        font_size = int(DEFAULT_FONT_SIZE * self.scale_factor)
        
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
            pady=10,
            font=("Lexend", font_size)
        )

    def apply_entry_theme(self, widget, theme):
        """Apply theme colors to a ttk.Entry or tk.Entry widget."""
        input_bg = theme["text_bg"]
        input_fg = theme["text_fg"]
        accent = theme["accent"]
        caret_color = "white" if self._is_dark(input_bg) else "black"
        
        if isinstance(widget, ttk.Entry):
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
        """Apply theme colors to preview widget with formatted tags."""
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
        # Section labels
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
        """Apply theme background to a tk.Canvas widget."""
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