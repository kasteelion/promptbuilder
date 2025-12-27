# -*- coding: utf-8 -*-
"""Theme Editor dialog: create, edit, delete, and save custom themes."""

import tkinter as tk
from tkinter import colorchooser, messagebox, ttk
from typing import Dict

from config import DEFAULT_THEME
from utils import logger


class ThemeEditorDialog:
    """Simple dialog to edit themes and persist them via PreferencesManager.

    It expects a ThemeManager instance and a PreferencesManager.
    """

    KEYS = [
        "bg",
        "fg",
        "preview_bg",
        "preview_fg",
        "text_bg",
        "text_fg",
        "accent",
        "accent_hover",
        "border",
        "selected_bg",
    ]

    def __init__(self, parent, theme_manager, prefs, on_theme_change=None):
        self.parent = parent
        self.theme_manager = theme_manager
        self.prefs = prefs
        self.on_theme_change = on_theme_change

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("THEME EDITOR")
        self.dialog.geometry("750x550")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._build_ui()

        # Load existing themes (including custom from prefs)
        self._load_themes()

        # Register for theme updates
        if hasattr(parent, "dialog_manager"):
            parent.dialog_manager._register_dialog(self.dialog, self.apply_theme)
        
        # Initial theme application
        try:
            current_theme = theme_manager.themes.get(theme_manager.current_theme, {})
            self.apply_theme(current_theme)
        except: pass

    def apply_theme(self, theme):
        """Apply theme to all dialog widgets. (Refactor 3)"""
        tm = self.theme_manager
        tm.apply_listbox_theme(self.listbox, theme)
        
        pbg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        accent = theme.get("accent", "#0078d7")
        
        # Update swatch background for empty entries
        for k in self.KEYS:
            val = self.entries[k].get()
            if not val:
                try: self.swatches[k].config(bg=pbg)
                except: pass

    def _build_ui(self):
        main = ttk.Frame(self.dialog, style="TFrame", padding=15)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)

        # Left: list of themes
        left = ttk.Frame(main, style="TFrame")
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 15), pady=4)
        ttk.Label(left, text="THEMES:", style="Bold.TLabel").pack(anchor="w", pady=(0, 5))
        
        list_frame = ttk.Frame(left, style="TFrame")
        list_frame.pack(fill="both", expand=True)
        
        self.listbox = tk.Listbox(list_frame, height=18, font=("Lexend", 10), borderwidth=0, highlightthickness=0)
        self.listbox.pack(side="left", fill="both", expand=True)
        
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview, style="Themed.Vertical.TScrollbar")
        list_scroll.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=list_scroll.set)
        
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_theme_select())

        btns = ttk.Frame(left, style="TFrame")
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="NEW", command=self._new_theme, style="TButton").pack(side="left", padx=(0, 4))
        ttk.Button(btns, text="DELETE", command=self._delete_theme, style="Ghost.TButton").pack(side="left")
        ttk.Button(btns, text="DUPLICATE", command=self._duplicate_theme, style="Ghost.TButton").pack(
            side="left", padx=(6, 0)
        )

        # Right: editor fields
        right = ttk.Frame(main, style="TFrame")
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(1, weight=1)

        ttk.Label(right, text="THEME NAME:", style="Bold.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.name_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.name_var, style="TEntry").grid(row=0, column=1, sticky="ew", pady=(0, 10))

        self.entries: Dict[str, tk.StringVar] = {}
        self.swatches: Dict[str, tk.Label] = {}
        for i, key in enumerate(self.KEYS, start=1):
            ttk.Label(right, text=f"{key.upper()}:", style="Muted.TLabel").grid(row=i, column=0, sticky="w", pady=2)
            sv = tk.StringVar()
            self.entries[key] = sv
            entry = ttk.Entry(right, textvariable=sv, style="TEntry")
            entry.grid(row=i, column=1, sticky="ew", pady=2)

            # Color picker button and swatch
            btn = ttk.Button(right, text="◉", width=3, command=lambda k=key: self._choose_color(k), style="Ghost.TButton")
            btn.grid(row=i, column=2, sticky="w", padx=(10, 0))

            sw = tk.Label(right, width=2, relief="solid", borderwidth=1)
            sw.grid(row=i, column=3, sticky="w", padx=(10, 0))
            self.swatches[key] = sw

        # Save/Apply/Close buttons
        action_row = ttk.Frame(self.dialog, style="TFrame", padding=15)
        action_row.pack(fill="x")
        ttk.Button(action_row, text="APPLY", command=self._apply_theme, style="TButton").pack(side="left")
        ttk.Button(action_row, text="SAVE", command=self._save_all, style="TButton").pack(side="left", padx=(10, 0))
        ttk.Button(action_row, text="CLOSE", command=self._close, style="TButton").pack(side="right")

    def _load_themes(self):
        # Start with current ThemeManager themes
        self.themes = dict(self.theme_manager.themes)
        # Merge custom themes from prefs if present
        custom = self.prefs.get("custom_themes", {}) or {}
        for k, v in custom.items():
            self.themes[k] = v

        self._refresh_listbox()

    def _refresh_listbox(self):
        self.listbox.delete(0, "end")
        for name in sorted(self.themes.keys()):
            self.listbox.insert("end", name)

    def _on_theme_select(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        theme = self.themes.get(name, {})
        self.name_var.set(name)
        for k in self.KEYS:
            val = theme.get(k, "")
            self.entries[k].set(val)
            # update swatch bg
            try:
                if val:
                    self.swatches[k].config(bg=val)
                else:
                    self.swatches[k].config(bg=self.dialog.cget("bg"))
            except Exception:
                # ignore invalid colors
                pass

    def _new_theme(self):
        # Clear fields for new theme
        self.listbox.selection_clear(0, "end")
        self.name_var.set("")
        for k in self.KEYS:
            self.entries[k].set("")
            try:
                self.swatches[k].config(bg=self.dialog.cget("bg"))
            except Exception:
                pass

    def _duplicate_theme(self):
        """Duplicate the selected theme into a new theme with a unique name."""
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Duplicate Theme", "No theme selected to duplicate")
            return
        src_name = self.listbox.get(sel[0])
        src = self.themes.get(src_name)
        if not src:
            messagebox.showerror("Duplicate Theme", "Selected theme not found")
            return

        # Propose a unique name
        base = f"{src_name} Copy"
        new_name = base
        i = 1
        while new_name in self.themes:
            i += 1
            new_name = f"{base} {i}"

        # Shallow copy the dict
        new_vals = dict(src)
        self.themes[new_name] = new_vals

        # Refresh list and select the new one
        self._refresh_listbox()
        try:
            idx = list(sorted(self.themes.keys())).index(new_name)
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
        except Exception:
            pass

        # Prefill editor fields with the duplicated values
        self.name_var.set(new_name)
        for k in self.KEYS:
            val = new_vals.get(k, "")
            self.entries[k].set(val)
            try:
                if val:
                    self.swatches[k].config(bg=val)
                else:
                    self.swatches[k].config(bg=self.dialog.cget("bg"))
            except Exception:
                pass

        # Notify UI/menu that themes changed
        try:
            if callable(self.on_theme_change):
                self.on_theme_change()
        except Exception:
            logger.debug("on_theme_change callback failed during duplicate")

    def _delete_theme(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Delete Theme", "No theme selected")
            return
        name = self.listbox.get(sel[0])
        if messagebox.askyesno("Delete Theme", f"Delete theme '{name}'?"):
            try:
                # Remove from local themes and from ThemeManager
                if name in self.themes:
                    del self.themes[name]
                try:
                    self.theme_manager.remove_theme(name)
                except Exception:
                    logger.debug("Theme manager may not support remove_theme")
                self._refresh_listbox()
                # Persist to markdown file
                try:
                    self.theme_manager.save_themes_md()
                except Exception:
                    logger.debug("Failed to save themes to themes.md after delete")

                # If the deleted theme was the last selected, reset preference
                try:
                    last = self.prefs.get("last_theme")
                    if last == name:
                        self.prefs.set("last_theme", DEFAULT_THEME)
                except Exception:
                    logger.debug("Failed to update last_theme in preferences")

                # notify UI that themes changed
                try:
                    if callable(self.on_theme_change):
                        self.on_theme_change()
                except Exception:
                    logger.debug("on_theme_change callback failed")
            except Exception as e:
                logger.exception("Failed to delete theme")
                messagebox.showerror("Error", f"Failed to delete theme: {e}")

    def _apply_theme(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Invalid", "Please enter a theme name")
            return
        vals = {k: self.entries[k].get().strip() for k in self.KEYS}
        # Basic validation: at least accent and bg present
        if not vals.get("bg") or not vals.get("accent"):
            if not messagebox.askyesno(
                "Missing Colors",
                "Some recommended colors are missing (bg/accent). Apply anyway?",
            ):
                return

        try:
            # Add to local cache and ThemeManager
            self.themes[name] = vals
            try:
                self.theme_manager.add_theme(name, vals)
            except Exception:
                logger.debug("ThemeManager.add_theme failed or not available")
            # Update swatches to reflect applied values
            for k, v in vals.items():
                try:
                    if v:
                        self.swatches[k].config(bg=v)
                except Exception:
                    pass
            self._refresh_listbox()
            # Keep selection on saved theme
            idx = list(sorted(self.themes.keys())).index(name)
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
            # Apply theme immediately across the app
            try:
                self.theme_manager.apply_theme(name)
            except Exception:
                logger.debug("ThemeManager.apply_theme failed")

            # Persist themes to data/themes.md and remember last_theme
            try:
                self.theme_manager.save_themes_md()
                self.prefs.set("last_theme", name)
            except Exception:
                logger.debug("Failed to persist themes to themes.md or set last_theme")

            # notify UI that themes changed (so menus can refresh)
            try:
                if callable(self.on_theme_change):
                    self.on_theme_change()
            except Exception:
                logger.debug("on_theme_change callback failed")
        except Exception as e:
            logger.exception("Failed to apply theme")
            messagebox.showerror("Error", f"Failed to apply theme: {e}")

    def _save_all(self):
        # Persist themes to preferences (store full set)
        try:
            # Save to themes.md
            try:
                self.theme_manager.save_themes_md()
                messagebox.showinfo("Saved", "Themes saved to data/themes.md")
            except Exception:
                logger.exception("Failed saving themes to themes.md")

            # notify UI that themes changed
            try:
                if callable(self.on_theme_change):
                    self.on_theme_change()
            except Exception:
                logger.debug("on_theme_change callback failed")
        except Exception as e:
            logger.exception("Failed to save themes")
            messagebox.showerror("Error", f"Failed to save themes: {e}")

    def _choose_color(self, key: str):
        """Open color chooser and set the chosen color for `key`."""
        current = self.entries.get(key).get() or None
        try:
            chosen = colorchooser.askcolor(color=current, parent=self.dialog)
            if chosen and chosen[1]:
                hexc = chosen[1]
                self.entries[key].set(hexc)
                try:
                    self.swatches[key].config(bg=hexc)
                except Exception:
                    pass
        except Exception:
            logger.exception("Color chooser failed")

    def _close(self):
        self.dialog.destroy()

    def show(self):
        self.dialog.wait_window()
