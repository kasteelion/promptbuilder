# -*- coding: utf-8 -*-
"""Searchable combobox widget with filtering."""

import tkinter as tk
from tkinter import ttk


class SearchableCombobox(ttk.Frame):
    """Combobox with search/filter functionality and better UX for large lists."""

    def __init__(self, parent, theme_manager=None, values=None, on_select=None, on_favorite_toggle=None, on_double_click=None, show_favorites=False, placeholder="Search...", textvariable=None, **kwargs):
        """Initialize searchable combobox.

        Args:
            parent: Parent widget
            theme_manager: Optional ThemeManager instance
            values: List of values
            on_select: Callback when item selected (passes value)
            on_favorite_toggle: Callback when favorite toggled (passes value, is_fav)
            on_double_click: Callback when item double-clicked (passes value)
            show_favorites: Whether to show favorites star
            placeholder: Text to show when empty
            textvariable: Optional StringVar to use for the entry
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)

        self.theme_manager = theme_manager
        self.all_values = values or []
        self.on_select = on_select
        self.on_favorite_toggle = on_favorite_toggle
        self.on_double_click = on_double_click
        self.show_favorites = show_favorites
        self.placeholder = placeholder
        self.favorites = set()
        self._selected_value = textvariable or tk.StringVar()
        
        # Track dropdown state
        self.dropdown = None
        self.dropdown_visible = False
        self._after_id = None
        
        # Cache for filtered results to boost performance
        self._filter_cache = {}

        self._build_ui()
        
        if self.theme_manager:
            self.theme_manager.register(self, self.apply_theme)

    def _build_ui(self):
        """Build the UI."""
        self.columnconfigure(0, weight=1)

        # Entry container
        self.entry_container = ttk.Frame(self)
        self.entry_container.grid(row=0, column=0, sticky="ew")
        self.entry_container.columnconfigure(0, weight=1)

        # Entry for search/display
        self.entry = ttk.Entry(self.entry_container, textvariable=self._selected_value, style="TEntry")
        self.entry.grid(row=0, column=0, sticky="ew")
        
        # Bindings for the entry
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Return>", self._on_return)
        self.entry.bind("<Down>", self._on_arrow_down)
        self.entry.bind("<Up>", self._on_arrow_up)
        self.entry.bind("<Escape>", lambda e: self._hide_dropdown())
        self.entry.bind("<Double-Button-1>", self._on_entry_double_click)
        
        # Clear button next to entry (X) - Refactor 5: Lexend/Link
        self.clear_btn = ttk.Button(
            self.entry_container, 
            text="✕", 
            width=2,
            command=self._clear_text,
            style="Link.TButton"
        )
        # Configure style if needed, or rely on default
        
        # We'll place it dynamically in _on_key_release
        self._update_clear_btn_visibility()

        # Get initial colors from theme if available
        # Default fallbacks if no theme loaded
        panel_bg = "#1e1e1e"
        accent = "#0078d7"
        border = "#333333"
        sel_bg = "#333333"
        
        if self.theme_manager and self.theme_manager.current_theme in self.theme_manager.themes:
            theme = self.theme_manager.themes[self.theme_manager.current_theme]
            panel_bg = theme.get("panel_bg", theme.get("bg", panel_bg))
            accent = theme.get("accent", accent)
            border = theme.get("border", panel_bg)
            sel_bg = theme.get("hover_bg", theme.get("selected_bg", border))
        else:
            try:
                style = ttk.Style()
                panel_bg = style.lookup("TFrame", "background") or panel_bg
                accent = style.lookup("Tag.TLabel", "bordercolor") or accent
                border = style.lookup("Card.TFrame", "bordercolor") or accent
                sel_bg = style.lookup("TNotebook.Tab", "background", [("selected", "")]) or border
            except: pass

        # Dropdown button - Refactor 3: Ghost style
        self.dropdown_btn = tk.Button(
            self, 
            text="▾", 
            width=3, 
            command=self._toggle_dropdown,
            bg=panel_bg,
            fg=accent,
            relief="flat",
            highlightthickness=1,
            highlightbackground=border,
            cursor="hand2"
        )
        self.dropdown_btn.grid(row=0, column=1, padx=(2, 0))
        self.dropdown_btn._base_bg = panel_bg
        
        self.dropdown_btn.bind("<Enter>", lambda e: self.dropdown_btn.config(bg=sel_bg))
        self.dropdown_btn.bind("<Leave>", lambda e: self.dropdown_btn.config(bg=getattr(self.dropdown_btn, "_base_bg", panel_bg)))

        # Favorite button (optional)
        if self.show_favorites:
            self.fav_btn = tk.Button(
                self, 
                text="☆", 
                width=3, 
                command=self._toggle_favorite,
                bg=panel_bg,
                fg=accent,
                relief="flat",
                highlightthickness=1,
                highlightbackground=border
            )
            self.fav_btn.grid(row=0, column=2, padx=(2, 0))
            self.fav_btn._base_bg = panel_bg
            self.fav_btn.bind("<Enter>", lambda e: self.fav_btn.config(bg=sel_bg))
            self.fav_btn.bind("<Leave>", lambda e: self.fav_btn.config(bg=getattr(self.fav_btn, "_base_bg", panel_bg)))
            
        # Set initial placeholder
        if not self._selected_value.get():
            self._set_placeholder_mode(True)
            
        # Bind global click to handle click-away closing
        try:
            self.winfo_toplevel().bind("<Button-1>", self._check_click_outside, add="+")
        except Exception:
            pass

    def _on_entry_double_click(self, event):
        """Handle double click in entry."""
        val = self.get()
        if val and self.on_double_click:
            self.on_double_click(val)

    def _on_arrow_down(self, event):
        """Handle Down arrow key."""
        if not self.dropdown_visible:
            self._show_dropdown()
        elif self.listbox.size() > 0:
            current = self.listbox.curselection()
            if not current:
                self.listbox.selection_set(0)
                self.listbox.activate(0)
            else:
                next_idx = min(self.listbox.size() - 1, current[0] + 1)
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(next_idx)
                self.listbox.activate(next_idx)
                self.listbox.see(next_idx)
        return "break"

    def _on_arrow_up(self, event):
        """Handle Up arrow key."""
        if self.dropdown_visible and self.listbox.size() > 0:
            current = self.listbox.curselection()
            if current and current[0] > 0:
                next_idx = current[0] - 1
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(next_idx)
                self.listbox.activate(next_idx)
                self.listbox.see(next_idx)
        return "break"

    def _set_placeholder_mode(self, active):
        """Set entry placeholder mode (gray text)."""
        if active:
            self._selected_value.set(self.placeholder)
            pfg = "#666666"
            if self.theme_manager and self.theme_manager.current_theme in self.theme_manager.themes:
                theme = self.theme_manager.themes[self.theme_manager.current_theme]
                pfg = theme.get("placeholder_fg", "#666666")
            self.entry.config(foreground=pfg) # Refactor 3: Dark friendly gray
        else:
            if self._selected_value.get() == self.placeholder:
                self._selected_value.set("")
            self.entry.config(foreground="") # Reset to default (black/white from theme)

    def _clear_text(self):
        """Clear entry text."""
        self._set_placeholder_mode(False)
        self._selected_value.set("")
        self.entry.focus_set()
        self._update_clear_btn_visibility()
        if self.dropdown_visible:
            self._update_dropdown_values()
        if self.on_select:
            self.on_select("")

    def _update_clear_btn_visibility(self):
        """Show/hide X button based on content."""
        val = self._selected_value.get()
        if val and val != self.placeholder:
            self.clear_btn.grid(row=0, column=1, sticky="w", padx=(2, 0))
        else:
            self.clear_btn.grid_remove()

    def _on_focus_in(self, event):
        """Handle entry focus."""
        if self._selected_value.get() == self.placeholder:
            self._set_placeholder_mode(False)
        
        # Auto-select all text on focus
        self.after(10, lambda: self.entry.selection_range(0, tk.END))
        
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _on_focus_out(self, event):
        """Handle entry focus out."""
        if not self._selected_value.get():
            self._set_placeholder_mode(True)
        # Use after to allow clicking on dropdown items before hiding
        self._after_id = self.after(250, self._check_hide_dropdown)

    def _check_hide_dropdown(self):
        """Check if we should hide dropdown after focus loss."""
        try:
            focus = self.focus_get()
        except Exception:
            # focus_get() can raise KeyError if focus is on an internal widget like 'popdown'
            self._hide_dropdown()
            return

        if self.dropdown and self.dropdown.winfo_exists():
            # Check if focus is in dropdown or its children
            try:
                if focus == self.dropdown or focus == self.listbox or focus == self.entry:
                    return
                # Check if focus is a child of the listbox (like scrollbar)
                if str(focus).startswith(str(self.dropdown)):
                    return
            except Exception:
                pass
        self._hide_dropdown()

    def _build_dropdown(self):
        """Create dropdown listbox as a floating window."""
        if self.dropdown:
            self.dropdown.destroy()

        # Create toplevel window
        self.dropdown = tk.Toplevel(self)
        self.dropdown.wm_overrideredirect(True)
        self.dropdown.attributes("-topmost", True)
        
        # Ensure children can find the manager
        if self.theme_manager:
            self.theme_manager.theme_toplevel(self.dropdown)

        # Position below entry
        self.update_idletasks()
        
        # Determine geometry
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = self.entry.winfo_width() # Match entry width precisely
        
        # Ensure it doesn't go off screen
        screen_h = self.winfo_screenheight()
        
        # Calculate height based on items
        filtered_items = self._get_filtered_values()
        num_items = len(filtered_items)
        if num_items == 0:
            self._hide_dropdown()
            return

        # Measure font height for accurate row height
        from tkinter import font as tkfont
        f = tkfont.Font(font=("Lexend", 9))
        line_h = f.metrics("linespace") + 4
        
        h = max(30, min(300, (num_items * line_h) + 6))
        
        # Flip if it would go off bottom
        if y + h > screen_h - 60:
            y = self.entry.winfo_rooty() - h
        
        self.dropdown.wm_geometry(f"{w}x{h}+{x}+{y}")

        # Listbox with scrollbar
        # Attempt to get theme colors
        theme = {}
        accent_color = "#0078d7"
        bg_color = "#1e1e1e" # Darker default
        fg_color = "#eeeeee" # Lighter default
        border_color = "#333333" # Muted default
        
        if self.theme_manager and self.theme_manager.current_theme in self.theme_manager.themes:
            theme = self.theme_manager.themes[self.theme_manager.current_theme]
            accent_color = theme["accent"]
            bg_color = theme["text_bg"]
            fg_color = theme["text_fg"]
            border_color = theme["border"]

        frame = tk.Frame(self.dropdown, borderwidth=1, relief="solid", bg=border_color)
        frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            frame, 
            height=10, 
            borderwidth=0, 
            highlightthickness=0,
            font=("Lexend", 9), # Refactor 5: Lexend
            activestyle="none",
            selectbackground=accent_color,
            selectforeground=theme.get("bg", "white"),
            background=bg_color,
            foreground=fg_color
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.listbox.yview, style="Themed.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Populate with filtered values
        for item in filtered_items:
            self.listbox.insert(tk.END, item)

        # Bind events for the listbox
        self.listbox.bind("<ButtonRelease-1>", self._on_listbox_select)
        self.listbox.bind("<Double-Button-1>", self._on_listbox_select)
        self.listbox.bind("<Return>", self._on_listbox_select)
        self.listbox.bind("<Escape>", lambda e: self._hide_dropdown())
        
        # Hover effect
        self.listbox.bind("<Motion>", self._on_listbox_motion)

        self.dropdown_visible = True
        
        self.dropdown.bind("<FocusOut>", self._on_dropdown_focus_out)

    def _on_dropdown_focus_out(self, event):
        """Handle dropdown losing focus."""
        # Use a small delay to check if focus moved to entry or listbox child
        self.after(100, self._check_hide_dropdown)

    def _check_click_outside(self, event):
        """Check if click was outside the combobox components."""
        if not self.dropdown_visible:
            return
            
        # Check if widget clicked is part of this combobox or its dropdown
        widget = event.widget
        try:
            # Check if widget is the main frame or any of its children (entry, buttons, etc.)
            if str(widget).startswith(str(self)):
                return
            # Check if widget is the dropdown window or any of its children (listbox, scrollbar)
            if self.dropdown and str(widget).startswith(str(self.dropdown)):
                return
        except Exception:
            pass
            
        # Click was outside, hide dropdown
        self._hide_dropdown()

    def _get_accent_color(self):
        """Get accent color for selection."""
        # Fallback to standard blue
        return "#0078d7"

    def _on_listbox_motion(self, event):
        """Highlight item under mouse."""
        index = self.listbox.nearest(event.y)
        if index >= 0:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            self.listbox.activate(index)

    def _get_filtered_values(self):
        """Get list of values matching current search term with smart prioritization."""
        search_term = self._selected_value.get().lower()
        if search_term == self.placeholder.lower():
            search_term = ""
            
        # Check cache
        cache_key = (search_term, tuple(sorted(list(self.favorites))), tuple(self.all_values))
        if cache_key in self._filter_cache:
            return self._filter_cache[cache_key]

        filtered_favs = []
        if self.favorites:
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
                
        result = filtered_favs + starts_with + contains
        self._filter_cache[cache_key] = result
        return result

    def _update_dropdown_values(self):
        """Update dropdown with filtered values."""
        try:
            if not self.dropdown or not self.dropdown.winfo_exists():
                # If not visible, maybe show it if we have values
                if self.entry.winfo_exists() and self.entry.focus_get() == self.entry:
                     self._show_dropdown()
                return

            if not self.listbox or not self.listbox.winfo_exists():
                return

            filtered = self._get_filtered_values()
            if not filtered:
                self._hide_dropdown()
                return

            self.listbox.delete(0, tk.END)
            for item in filtered:
                self.listbox.insert(tk.END, item)
                
            # Adjust height
            h = max(40, min(300, (len(filtered) * 22) + 6))
            self.dropdown.wm_geometry(f"{self.winfo_width()}x{h}")

            # Highlight first match if searching
            if self.listbox.size() > 0 and self._selected_value.get():
                self.listbox.selection_set(0)
        except tk.TclError:
            # Widget likely destroyed during update
            pass

    def _show_dropdown(self, event=None):
        """Show the dropdown."""
        if not self.winfo_exists():
            return
        if not self.dropdown_visible:
            self._build_dropdown()
        else:
            self._update_dropdown_values()

    def _hide_dropdown(self, event=None):
        """Hide the dropdown."""
        try:
            if self.dropdown and self.dropdown.winfo_exists():
                self.dropdown.destroy()
            self.dropdown = None
        except tk.TclError:
            pass
        self.dropdown_visible = False

    def _toggle_dropdown(self):
        """Toggle dropdown visibility."""
        if not self.winfo_exists():
            return
        if self.dropdown_visible:
            self._hide_dropdown()
        else:
            self.entry.focus_set()
            self._show_dropdown()

    def _on_key_release(self, event):
        """Handle key release in entry."""
        if not self.winfo_exists():
            return
            
        val = self._selected_value.get()
        self._update_clear_btn_visibility()
        
        # If text is empty (and we just released a key, so user typed backspace/delete),
        # trigger on_select with empty value to ensure listeners know it's cleared.
        if not val and self.on_select:
             self.on_select("")
             
        # Check if we still exist after callback, as on_select might have 
        # triggered a UI refresh that destroyed this widget.
        if not self.winfo_exists():
            return
        
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
            # Skip separator or header
            if value.startswith("---"):
                return
                
            # Remove favorite star if present
            if value.startswith("★ "):
                value = value[2:]
                
            self._selected_value.set(value)
            self._hide_dropdown()
            self._update_clear_btn_visibility()
            
            if self.on_select:
                self.on_select(value)
                
            # Trigger double click if applicable
            if event and "Double" in str(event.type) and self.on_double_click:
                self.on_double_click(value)

    def _toggle_favorite(self):
        """Toggle favorite status of current value."""
        value = self._selected_value.get()
        if value in self.all_values:
            if value in self.favorites:
                self.favorites.remove(value)
                self.fav_btn.config(text="☆")
                is_fav = False
            else:
                self.favorites.add(value)
                self.fav_btn.config(text="★")
                is_fav = True
            self._filter_cache.clear() # Cache invalidated
            
            if self.on_favorite_toggle:
                self.on_favorite_toggle(value, is_fav)

    def set_values(self, values):
        """Update the list of values."""
        self.all_values = values or []
        self._filter_cache.clear()
        if self.dropdown_visible:
            self._update_dropdown_values()

    def get(self):
        """Get current value (strips placeholder)."""
        val = self._selected_value.get()
        return "" if val == self.placeholder else val

    def set(self, value):
        """Set current value."""
        if not hasattr(self, "entry") or not self.entry.winfo_exists():
            return

        if value:
            self._selected_value.set(value)
            self.entry.config(foreground="")
        else:
            self._set_placeholder_mode(True)
            
        if value in self.favorites and self.show_favorites:
            self.fav_btn.config(text="★")
        elif self.show_favorites:
            self.fav_btn.config(text="☆")
        self._update_clear_btn_visibility()

    def set_favorites(self, favorites):
        """Set favorites list."""
        self.favorites = set(favorites) if favorites else set()
        self._filter_cache.clear()

    def apply_theme(self, theme):
        """Apply theme to custom widgets. (Refactor 3)"""
        accent = theme.get("accent", "#0078d7")
        panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        border = theme.get("border", panel_bg)
        sel_bg = theme.get("hover_bg", theme.get("selected_bg", "#333333"))
        
        # Update custom buttons
        if hasattr(self, "dropdown_btn"):
            self.dropdown_btn.config(bg=panel_bg, fg=accent, highlightbackground=border)
            self.dropdown_btn._base_bg = panel_bg
            
        if hasattr(self, "fav_btn"):
            self.fav_btn.config(bg=panel_bg, fg=accent, highlightbackground=border)
            self.fav_btn._base_bg = panel_bg
            
        # Update placeholder color if currently active
        if self._selected_value.get() == self.placeholder:
             pfg = theme.get("placeholder_fg", "#666666")
             self.entry.config(foreground=pfg)
            
        # If dropdown is open, we need to update the listbox too
        if self.dropdown and self.dropdown.winfo_exists():
            try:
                # Find the frame and listbox
                for child in self.dropdown.winfo_children():
                    if isinstance(child, tk.Frame):
                        child.config(bg=border)
                        for inner in child.winfo_children():
                            if isinstance(inner, tk.Listbox):
                                inner.config(
                                    bg=theme.get("text_bg", panel_bg),
                                    fg=theme.get("text_fg", theme.get("fg", "white")),
                                    selectbackground=accent,
                                    selectforeground=theme.get("bg", "black")
                                )
            except: pass