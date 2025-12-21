# -*- coding: utf-8 -*-
"""Searchable combobox widget with filtering."""

import tkinter as tk
from tkinter import ttk


class SearchableCombobox(ttk.Frame):
    """Combobox with search/filter functionality and better UX for large lists."""

    def __init__(self, parent, values=None, on_select=None, show_favorites=False, placeholder="Search...", textvariable=None, **kwargs):
        """Initialize searchable combobox.

        Args:
            parent: Parent widget
            values: List of values
            on_select: Callback when item selected (passes value)
            show_favorites: Whether to show favorites star
            placeholder: Text to show when empty
            textvariable: Optional StringVar to use for the entry
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)

        self.all_values = values or []
        self.on_select = on_select
        self.show_favorites = show_favorites
        self.placeholder = placeholder
        self.favorites = set()
        self._selected_value = textvariable or tk.StringVar()
        
        # Track dropdown state
        self.dropdown = None
        self.dropdown_visible = False
        self._after_id = None

        self._build_ui()

    def _build_ui(self):
        """Build the UI."""
        self.columnconfigure(0, weight=1)

        # Entry for search/display
        self.entry = ttk.Entry(self, textvariable=self._selected_value)
        self.entry.grid(row=0, column=0, sticky="ew")
        
        # Bindings for the entry
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Return>", self._on_return)
        self.entry.bind("<Down>", lambda e: self._show_dropdown())
        self.entry.bind("<Escape>", lambda e: self._hide_dropdown())

        # Dropdown button
        self.dropdown_btn = ttk.Button(self, text="▾", width=3, command=self._toggle_dropdown)
        self.dropdown_btn.grid(row=0, column=1)

        # Favorite button (optional)
        if self.show_favorites:
            self.fav_btn = ttk.Button(self, text="☆", width=3, command=self._toggle_favorite)
            self.fav_btn.grid(row=0, column=2)

    def _on_focus_in(self, event):
        """Handle entry focus."""
        if self._selected_value.get() == self.placeholder:
            self._selected_value.set("")
        self.entry.selection_range(0, tk.END)

    def _on_focus_out(self, event):
        """Handle entry focus out."""
        # Use after to allow clicking on dropdown items before hiding
        self._after_id = self.after(200, self._check_hide_dropdown)

    def _check_hide_dropdown(self):
        """Check if we should hide dropdown after focus loss."""
        if self.dropdown and not self.dropdown.focus_get():
            self._hide_dropdown()

    def _build_dropdown(self):
        """Create dropdown listbox as a floating window."""
        if self.dropdown:
            self.dropdown.destroy()

        # Create toplevel window
        self.dropdown = tk.Toplevel(self)
        self.dropdown.wm_overrideredirect(True)
        self.dropdown.attributes("-topmost", True)

        # Position below entry
        self.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = self.entry.winfo_width() + self.dropdown_btn.winfo_width()
        
        # Calculate height based on items (max 250px)
        num_items = len(self._get_filtered_values())
        h = max(40, min(250, (num_items * 22) + 10))
        
        self.dropdown.wm_geometry(f"{w}x{h}+{x}+{y}")

        # Listbox with scrollbar
        frame = ttk.Frame(self.dropdown, borderwidth=1, relief="solid")
        frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            frame, 
            yscrollcommand=scrollbar.set, 
            height=10, 
            borderwidth=0, 
            highlightthickness=0,
            font=("Segoe UI", 9)
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Populate with filtered values
        self._update_dropdown_values()

        # Bind events for the listbox
        self.listbox.bind("<ButtonRelease-1>", self._on_listbox_select)
        self.listbox.bind("<Return>", self._on_listbox_select)
        self.listbox.bind("<Escape>", lambda e: self._hide_dropdown())
        
        # Ensure dropdown stays visible when clicking scrollbar
        self.dropdown.bind("<FocusIn>", lambda e: self.after_cancel(self._after_id) if self._after_id else None)

        self.dropdown_visible = True

    def _get_filtered_values(self):
        """Get list of values matching current search term with smart prioritization."""
        search_term = self._selected_value.get().lower()
        if search_term == self.placeholder.lower():
            search_term = ""
            
        filtered_favs = []
        if self.favorites:
            # Separate starts-with and contains for favorites
            starts_with = []
            contains = []
            for item in sorted(self.favorites):
                if not search_term or item.lower().startswith(search_term):
                    starts_with.append(f"★ {item}")
                elif search_term in item.lower():
                    contains.append(f"★ {item}")
            filtered_favs = starts_with + contains
            if filtered_favs:
                filtered_favs.append("---")

        # Separate starts-with and contains for regular items
        starts_with = []
        contains = []
        for item in sorted(self.all_values):
            if item in self.favorites:
                continue
            if not search_term or item.lower().startswith(search_term):
                starts_with.append(item)
            elif search_term in item.lower():
                contains.append(item)
                
        return filtered_favs + starts_with + contains

    def _update_dropdown_values(self):
        """Update dropdown with filtered values."""
        if not self.dropdown or not self.listbox:
            return

        filtered = self._get_filtered_values()
        self.listbox.delete(0, tk.END)
        for item in filtered:
            self.listbox.insert(tk.END, item)
            
        # Highlight first match if searching
        if self.listbox.size() > 0 and self._selected_value.get():
            self.listbox.selection_set(0)

    def _show_dropdown(self, event=None):
        """Show the dropdown."""
        if not self.dropdown_visible:
            self._build_dropdown()
        else:
            self._update_dropdown_values()

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
            self.entry.focus_set()
            self._show_dropdown()

    def _on_key_release(self, event):
        """Handle key release in entry."""
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return
            
        if not self.dropdown_visible:
            self._show_dropdown()
        else:
            self._update_dropdown_values()

    def _on_return(self, event):
        """Handle return key."""
        if self.dropdown_visible and self.listbox.size() > 0:
            # If nothing selected, select first
            if not self.listbox.curselection():
                self.listbox.selection_set(0)
            self._on_listbox_select()
        else:
            # If dropdown hidden, maybe just trigger select with current text
            val = self._selected_value.get()
            if val and val != self.placeholder:
                if self.on_select:
                    self.on_select(val)

    def _on_listbox_select(self, event=None):
        """Handle listbox selection."""
        selection = self.listbox.curselection()
        if selection:
            value = self.listbox.get(selection[0])
            # Skip separator
            if value == "---":
                return
                
            # Remove favorite star if present
            if value.startswith("★ "):
                value = value[2:]
                
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
        """Update the list of values."""
        self.all_values = values or []
        if self.dropdown_visible:
            self._update_dropdown_values()

    def get(self):
        """Get current value (strips placeholder)."""
        val = self._selected_value.get()
        return "" if val == self.placeholder else val

    def set(self, value):
        """Set current value."""
        self._selected_value.set(value or "")
        if value in self.favorites and self.show_favorites:
            self.fav_btn.config(text="★")
        elif self.show_favorites:
            self.fav_btn.config(text="☆")

    def set_favorites(self, favorites):
        """Set favorites list."""
        self.favorites = set(favorites) if favorites else set()