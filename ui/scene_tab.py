"""Scene presets and description tab UI."""

import tkinter as tk
from tkinter import ttk
from .widgets import CollapsibleFrame
from .scene_creator import SceneCreatorDialog


class SceneTab:
    """Tab for managing scene descriptions and presets."""
    
    def __init__(self, parent, data_loader, on_change_callback, reload_callback=None):
        """Initialize scene tab.
        
        Args:
            parent: Parent notebook widget
            data_loader: DataLoader instance
            on_change_callback: Function to call when data changes
            reload_callback: Function to call to reload all data
        """
        self.parent = parent
        self.data_loader = data_loader
        self.on_change = on_change_callback
        self.reload_data = reload_callback
        
        self.scenes = {}
        
        self.tab = ttk.Frame(parent, style="TFrame")
        parent.add(self.tab, text="Scene")
        
        self._build_ui()
    
    def load_data(self, scenes):
        """Load scene preset data.
        
        Args:
            scenes: Scene presets dict
        """
        self.scenes = scenes
        self._update_preset_combos()
    
    def _build_ui(self):
        """Build the scene tab UI."""
        self.tab.columnconfigure(0, weight=1)
        self.tab.rowconfigure(1, weight=1)

        # Collapsible presets section
        cf = CollapsibleFrame(self.tab, text="Scene Presets")
        cf.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        cf.set_clear_command(self._clear_preset)
        
        content = cf.get_content_frame()
        content.columnconfigure(3, weight=1)

        ttk.Label(content, text="Category:").grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.scene_category_var = tk.StringVar()
        self.scene_cat_combo = ttk.Combobox(
            content, 
            textvariable=self.scene_category_var, 
            state="readonly", 
            width=12
        )
        self.scene_cat_combo.grid(row=0, column=1, padx=(0, 10))
        self.scene_cat_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preset_combos())

        ttk.Label(content, text="Preset:").grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.scene_preset_var = tk.StringVar()
        self.scene_combo = ttk.Combobox(
            content, 
            textvariable=self.scene_preset_var, 
            state="readonly"
        )
        self.scene_combo.grid(row=0, column=3, sticky="ew")
        self.scene_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_preset())
        self.scene_combo.bind("<Return>", lambda e: self._apply_preset())
        
        # Add create scene button
        ttk.Button(content, text="✨ Create Scene", command=self._create_new_scene).grid(row=1, column=0, columnspan=4, sticky="ew", pady=(5, 0))

        # Scene text area
        self.scene_text = tk.Text(self.tab, wrap="word")
        self.scene_text.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.scene_text.bind("<KeyRelease>", lambda e: self.on_change())
    
    def _update_preset_combos(self):
        """Update preset combo values based on selected category."""
        cat = self.scene_category_var.get()
        if cat and cat in self.scenes:
            self.scene_combo["values"] = [""] + sorted(list(self.scenes[cat].keys()))
        else:
            self.scene_combo["values"] = [""]
        self.scene_preset_var.set("")
        
        # Update category combo with all categories
        self.scene_cat_combo["values"] = [""] + sorted(list(self.scenes.keys()))
    
    def _apply_preset(self):
        """Apply selected preset to text area."""
        cat = self.scene_category_var.get()
        name = self.scene_preset_var.get()
        if cat and name and cat in self.scenes and name in self.scenes[cat]:
            self.scene_text.delete("1.0", "end")
            self.scene_text.insert("1.0", self.scenes[cat][name])
            self.on_change()
    
    def _clear_preset(self):
        """Clear preset selection and text area."""
        self.scene_category_var.set("")
        self.scene_preset_var.set("")
        self._update_preset_combos()
        self.scene_text.delete("1.0", "end")
        self.on_change()
    
    def _create_new_scene(self):
        """Open dialog to create a new scene."""
        root = self.tab.winfo_toplevel()
        dialog = SceneCreatorDialog(root, self.data_loader, self.reload_data)
        result = dialog.show()
    
    def get_scene_text(self):
        """Get current scene text.
        
        Returns:
            str: Scene text content
        """
        return self.scene_text.get("1.0", "end").strip()

    def set_scene_text(self, text):
        """Set the scene text area with new content.
        
        Args:
            text: The text to set.
        """
        self.scene_text.delete("1.0", "end")
        self.scene_text.insert("1.0", text)
