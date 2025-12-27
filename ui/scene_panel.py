# -*- coding: utf-8 -*-
"""Scene selection and editing panel."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from config import TOOLTIPS
from utils import create_tooltip, logger
from .searchable_combobox import SearchableCombobox
from .widgets import CollapsibleFrame


class ScenePanel(CollapsibleFrame):
    """Panel for selecting and editing the prompt scene."""

    def __init__(
        self, 
        parent, 
        data_loader, 
        theme_manager, 
        scenes_data: dict,
        on_change_callback: Callable[[], None],
        create_scene_callback: Callable[[], None],
        **kwargs
    ):
        """Initialize ScenePanel.

        Args:
            parent: Parent widget
            data_loader: DataLoader instance
            theme_manager: ThemeManager instance
            scenes_data: Initial scenes data dictionary
            on_change_callback: Callback when content changes
            create_scene_callback: Callback to open scene creator dialog
        """
        super().__init__(parent, text="🎬 SCENE", opened=True, show_clear=True, **kwargs)
        
        self.data_loader = data_loader
        self.theme_manager = theme_manager
        self.scenes = scenes_data
        self.on_change = on_change_callback
        self.create_scene_callback = create_scene_callback
        
        self._after_id: Optional[str] = None
        
        self._build_internal_ui()
        self._setup_theming()
        self.update_presets()

    def _build_internal_ui(self):
        """Build the widgets inside the collapsible frame."""
        content = self.get_content_frame()
        content.columnconfigure(1, weight=1)
        
        create_tooltip(self, TOOLTIPS.get("scene", ""))
        self.set_clear_command(self._clear_text)

        # Scene presets row
        ttk.Label(content, text="Category:", style="TLabel").grid(
            row=0, column=0, sticky="w", padx=(4, 4), pady=6
        )
        
        self.category_var = tk.StringVar()
        self.cat_combo = SearchableCombobox(
            content, 
            textvariable=self.category_var,
            on_select=lambda val: self.update_presets(),
            placeholder="Search category...",
            width=14
        )
        self.cat_combo.grid(row=0, column=1, sticky="w", padx=2, pady=6)

        ttk.Label(content, text="Preset:", style="TLabel").grid(
            row=0, column=2, sticky="w", padx=(10, 4), pady=6
        )
        
        self.preset_var = tk.StringVar()
        self.preset_combo = SearchableCombobox(
            content, 
            textvariable=self.preset_var,
            on_select=lambda val: self._apply_preset(),
            placeholder="Search preset...",
            width=20
        )
        self.preset_combo.grid(row=0, column=3, sticky="ew", padx=2, pady=6)

        self.new_btn = ttk.Button(content, text="✨", width=3, command=self.create_scene_callback)
        self.new_btn.grid(row=0, column=4, padx=(6, 4), pady=6)
        create_tooltip(self.new_btn, "Create a new scene preset")

        self.text = tk.Text(content, wrap="word", height=3)
        self.text.grid(row=1, column=0, columnspan=5, sticky="ew", padx=4, pady=(2, 6))
        
        # Debounce text changes
        self.text.bind("<KeyRelease>", self._on_text_change)

    def _setup_theming(self):
        """Register widgets with theme manager."""
        self.theme_manager.register(self, self.apply_theme)
        self.theme_manager.register_text_widget(self.text)
        self.theme_manager.register(self.cat_combo, self.cat_combo.apply_theme)
        self.theme_manager.register(self.preset_combo, self.preset_combo.apply_theme)

    def _clear_text(self):
        """Clear the text area and trigger update."""
        self.text.delete("1.0", "end")
        self.on_change()

    def _on_text_change(self, event):
        """Handle text change with debouncing."""
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(300, self.on_change)

    def _apply_preset(self):
        """Apply selected scene preset to text area."""
        cat = self.category_var.get()
        name = self.preset_var.get()

        if cat and name and cat in self.scenes and name in self.scenes[cat]:
            self.text.delete("1.0", "end")
            self.text.insert("1.0", self.scenes[cat][name])
            self.on_change()

    def update_presets(self, new_scenes_data: Optional[dict] = None):
        """Update available categories and presets."""
        if new_scenes_data is not None:
            self.scenes = new_scenes_data
            
        cat = self.category_var.get()
        if cat and cat in self.scenes:
            self.preset_combo.set_values([""] + sorted(list(self.scenes[cat].keys())))
        else:
            self.preset_combo.set_values([""])
        
        self.preset_var.set("")
        self.cat_combo.set_values([""] + sorted(list(self.scenes.keys())))

    def get_text(self) -> str:
        """Get the current scene text."""
        return self.text.get("1.0", "end").strip()

    def set_text(self, text: str):
        """Set the scene text."""
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
