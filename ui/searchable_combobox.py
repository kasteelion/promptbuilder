# -*- coding: utf-8 -*-
"""Searchable combobox widget with filtering."""

import tkinter as tk
from tkinter import ttk


class SearchableCombobox(ttk.Frame):
    """Combobox with search/filter functionality."""

    def __init__(self, parent, values=None, on_select=None, show_favorites=False, **kwargs):
        """Initialize searchable combobox.

        Args:
            parent: Parent widget
            values: List of values
            on_select: Callback when item selected
            show_favorites: Whether to show favorites star
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)

        self.all_values = values or []
        self.on_select = on_select
        self.show_favorites = show_favorites
        self.favorites = set()
        self._selected_value = tk.StringVar()

        self._build_ui()

    def _build_ui(self):
        """Build the UI."""
        self.columnconfigure(0, weight=1)

        # Entry for search/display
        self.entry = ttk.Entry(self, textvariable=self._selected_value)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<Return>", self._on_return)
        self.entry.bind("<Down>", self._show_dropdown)

        # Dropdown button
        self.dropdown_btn = ttk.Button(self, text="▼", width=3, command=self._toggle_dropdown)
        self.dropdown_btn.grid(row=0, column=1)

        # Favorite button (optional)
        if self.show_favorites:
            self.fav_btn = ttk.Button(self, text="☆", width=3, command=self._toggle_favorite)
            self.fav_btn.grid(row=0, column=2)

        # Dropdown listbox (hidden by default)
        self.dropdown = None
        self.dropdown_visible = False

    def _build_dropdown(self):
        """Create dropdown listbox."""
        if self.dropdown:
            self.dropdown.destroy()

        # Create toplevel window
        self.dropdown = tk.Toplevel(self)
        self.dropdown.wm_overrideredirect(True)

        # Position below entry
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = self.winfo_width()
        self.dropdown.wm_geometry(f"{w}x200+{x}+{y}")

        # Listbox with scrollbar
        frame = ttk.Frame(self.dropdown)
        frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, height=10)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Populate with filtered values
        self._update_dropdown_values()

        # Bind events
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        self.listbox.bind("<Return>", self._on_listbox_select)
        self.dropdown.bind("<FocusOut>", self._hide_dropdown)

        self.dropdown_visible = True

    def _update_dropdown_values(self):
        """Update dropdown with filtered values."""
        if not self.dropdown or not self.listbox:
            return

        search_term = self._selected_value.get().lower()
        self.listbox.delete(0, tk.END)

        # Add favorites first
        if self.favorites:
            for item in sorted(self.favorites):
                if search_term in item.lower():
                    self.listbox.insert(tk.END, f"★ {item}")
            if self.listbox.size() > 0:
                self.listbox.insert(tk.END, "---")

        # Add filtered regular items
        for item in sorted(self.all_values):
            if item not in self.favorites and search_term in item.lower():
                self.listbox.insert(tk.END, item)

    def _show_dropdown(self, event=None):
        """Show the dropdown."""
        if not self.dropdown_visible:
            self._build_dropdown()

    def _hide_dropdown(self, event=None):
        """Hide the dropdown."""
        if self.dropdown:
            self.dropdown.destroy()
            self.dropdown = None
        self.dropdown_visible = False

    def _toggle_dropdown(self):
        """Toggle dropdown visibility."""
        if self.dropdown_visible:
            self._hide_dropdown()
        else:
            self._show_dropdown()

    def _on_key_release(self, event):
        """Handle key release in entry."""
        if self.dropdown_visible:
            self._update_dropdown_values()
        elif len(self._selected_value.get()) > 0:
            self._show_dropdown()

    def _on_return(self, event):
        """Handle return key."""
        if self.dropdown_visible and self.listbox.size() > 0:
            self.listbox.selection_set(0)
            self._on_listbox_select()

    def _on_listbox_select(self, event=None):
        """Handle listbox selection."""
        selection = self.listbox.curselection()
        if selection:
            value = self.listbox.get(selection[0])
            # Remove favorite star if present
            if value.startswith("★ "):
                value = value[2:]
            if value != "---":
                self._selected_value.set(value)
                self._hide_dropdown()
                if self.on_select:
                    self.on_select(value)

    def _toggle_favorite(self):
        """Toggle favorite status of current value."""
        value = self._selected_value.get()
        if value in self.all_values:
            if value in self.favorites:
                self.favorites.remove(value)
                self.fav_btn.config(text="☆")
            else:
                self.favorites.add(value)
                self.fav_btn.config(text="★")

    def set_values(self, values):
        """Set the list of values.

        Args:
            values: List of values
        """
        self.all_values = values or []
        if self.dropdown_visible:
            self._update_dropdown_values()

    def get(self):
        """Get current value."""
        return self._selected_value.get()

    def set(self, value):
        """Set current value.

        Args:
            value: Value to set
        """
        self._selected_value.set(value)
        if value in self.favorites and self.show_favorites:
            self.fav_btn.config(text="★")
        elif self.show_favorites:
            self.fav_btn.config(text="☆")

    def set_favorites(self, favorites):
        """Set favorites list.

        Args:
            favorites: Set or list of favorite items
        """
        self.favorites = set(favorites) if favorites else set()
