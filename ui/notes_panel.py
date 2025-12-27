# -*- coding: utf-8 -*-
"""Notes and multi-character interactions panel."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List

from config import TOOLTIPS
from utils import create_tooltip, logger
from utils.interaction_helpers import fill_template
from .searchable_combobox import SearchableCombobox
from .widgets import CollapsibleFrame


class NotesPanel(CollapsibleFrame):
    """Panel for adding notes and multi-character interaction templates."""

    def __init__(
        self,
        parent,
        data_loader,
        theme_manager,
        interactions_data: dict,
        on_change_callback: Callable[[], None],
        create_interaction_callback: Callable[[], None],
        get_selected_char_names: Callable[[], List[str]],
        **kwargs
    ):
        """Initialize NotesPanel.

        Args:
            parent: Parent widget
            data_loader: DataLoader instance
            theme_manager: ThemeManager instance
            interactions_data: Initial interactions data dictionary
            on_change_callback: Callback when content changes
            create_interaction_callback: Callback to open interaction creator dialog
            get_selected_char_names: Function to get list of currently selected character names
        """
        super().__init__(parent, text="📝 NOTES & INTERACTIONS", opened=True, show_clear=True, **kwargs)
        
        self.data_loader = data_loader
        self.theme_manager = theme_manager
        self.interactions = interactions_data
        self.on_change = on_change_callback
        self.create_interaction_callback = create_interaction_callback
        self.get_selected_char_names = get_selected_char_names
        
        self._after_id: Optional[str] = None
        self.pill_buttons_refs = []
        
        self._build_internal_ui()
        self._setup_theming()
        self.update_presets()

    def _build_internal_ui(self):
        """Build the widgets inside the collapsible frame."""
        content = self.get_content_frame()
        content.columnconfigure(0, weight=1)
        
        create_tooltip(self, TOOLTIPS.get("notes", ""))
        self.set_clear_command(self._clear_text)

        # Interaction template selector
        control = ttk.Frame(content, style="TFrame")
        control.grid(row=0, column=0, sticky="ew", padx=4, pady=(6, 10))
        control.columnconfigure(1, weight=1)
        control.columnconfigure(3, weight=1)

        ttk.Label(control, text="Category:", style="TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6))
        
        self.category_var = tk.StringVar()
        self.cat_combo = SearchableCombobox(
            control,
            textvariable=self.category_var,
            on_select=lambda val: self.update_presets(),
            placeholder="Search category...",
            width=15
        )
        self.cat_combo.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        ttk.Label(control, text="Template:", style="TLabel").grid(row=0, column=2, sticky="w", padx=(0, 6))

        self.template_var = tk.StringVar(value="Blank")
        self.template_combo = SearchableCombobox(
            control, 
            textvariable=self.template_var,
            on_double_click=lambda val: self._insert_template(),
            placeholder="Search template...",
            width=25
        )
        self.template_combo.grid(row=0, column=3, sticky="ew")

        # Action Buttons (Pill Style)
        action_frame = ttk.Frame(control, style="TFrame")
        action_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        
        def add_pill(text, command):
            # Styling is handled by apply_theme via registry
            pill = tk.Frame(action_frame, bg="#0078d7", padx=1, pady=1)
            pill.pack(side="left", padx=(0, 6))
            
            lbl = tk.Label(
                pill, text=text, bg="#1e1e1e", fg="#0078d7",
                font=("Lexend", 8, "bold"), padx=10, pady=2, cursor="hand2"
            )
            lbl.pack()
            
            def on_e(e, l=lbl):
                try:
                    theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
                    l.config(bg=theme.get("hover_bg", "#333333"))
                except: l.config(bg="#333333")
                
            def on_l(e, l=lbl):
                l.config(bg=getattr(l, "_base_bg", "#1e1e1e"))
                
            lbl.bind("<Enter>", on_e)
            lbl.bind("<Leave>", on_l)
            lbl.bind("<Button-1>", lambda e: command())
            self.pill_buttons_refs.append((pill, lbl))
            return pill

        add_pill("📥 Insert Template", self._insert_template)
        add_pill("🔄 Refresh", self._refresh_template)
        add_pill("✨ Create New", self.create_interaction_callback)

        self.text = tk.Text(content, wrap="word", height=4)
        self.text.grid(row=1, column=0, sticky="nsew", padx=4, pady=(4, 6))
        
        # Debounce text changes
        self.text.bind("<KeyRelease>", self._on_text_change)

    def _setup_theming(self):
        """Register with theme manager."""
        self.theme_manager.register(self, self._apply_custom_theme)
        self.theme_manager.register_text_widget(self.text)
        self.theme_manager.register(self.cat_combo, self.cat_combo.apply_theme)
        self.theme_manager.register(self.template_combo, self.template_combo.apply_theme)

    def _apply_custom_theme(self, theme):
        """Manual update for custom frame/label components."""
        self.apply_theme(theme) # Base CollapsibleFrame logic
        
        accent = theme.get("accent", "#0078d7")
        panel_bg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        
        for frame, lbl in self.pill_buttons_refs:
            frame.config(bg=accent)
            lbl._base_bg = panel_bg
            lbl.config(bg=panel_bg, fg=accent)

    def _clear_text(self):
        """Clear the text area."""
        self.text.delete("1.0", "end")
        self.on_change()

    def _on_text_change(self, event):
        """Handle text change with debouncing."""
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(300, self.on_change)

    def _insert_template(self):
        """Insert selected template with character names filled."""
        cat = self.category_var.get()
        name = self.template_var.get()

        if not cat or not name or cat not in self.interactions or name not in self.interactions[cat]:
            return

        template_data = self.interactions[cat][name]
        selected_chars = self.get_selected_char_names()

        if not selected_chars:
            from utils.notification import notify
            notify(self.winfo_toplevel(), "No Characters", "Please add characters first.", level="info")
            return

        # Check character count warning
        if isinstance(template_data, dict):
            min_chars = template_data.get("min_chars", 1)
            if len(selected_chars) < min_chars:
                from utils.notification import notify
                notify(self.winfo_toplevel(), "Character Count", f"Requires {min_chars} characters.", level="warning")

        filled_text = fill_template(template_data, selected_chars)

        current_text = self.text.get("1.0", "end-1c")
        if current_text.strip():
            self.text.insert("end", "\n" + filled_text)
        else:
            self.text.delete("1.0", "end")
            self.text.insert("1.0", filled_text)

        self.on_change()

    def _refresh_template(self):
        """Replace notes with re-filled current template."""
        cat = self.category_var.get()
        name = self.template_var.get()

        if not cat or not name or cat not in self.interactions or name not in self.interactions[cat]:
            return

        template_data = self.interactions[cat][name]
        selected_chars = self.get_selected_char_names()

        if not selected_chars:
            return

        filled_text = fill_template(template_data, selected_chars)
        self.text.delete("1.0", "end")
        self.text.insert("1.0", filled_text)
        self.on_change()

    def update_presets(self, new_interactions_data: Optional[dict] = None):
        """Update available categories and templates."""
        if new_interactions_data is not None:
            self.interactions = new_interactions_data
            
        cat = self.category_var.get()
        if cat and cat in self.interactions:
            self.template_combo.set_values([""] + sorted(list(self.interactions[cat].keys())))
        else:
            self.template_combo.set_values([""])
        
        self.template_var.set("")
        self.cat_combo.set_values([""] + sorted(list(self.interactions.keys())))

    def get_text(self) -> str:
        """Get the current notes text."""
        return self.text.get("1.0", "end").strip()

    def set_text(self, text: str):
        """Set the notes text."""
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
