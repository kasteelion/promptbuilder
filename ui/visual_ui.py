# -*- coding: utf-8 -*-
"""Experimental UI with visual character gallery side panel."""

import tkinter as tk
from tkinter import ttk
from .character_card import CharacterGalleryPanel
from .preview_panel import PreviewPanel
from .edit_tab import EditTab
from logic import DataLoader, PromptRandomizer
from core.builder import PromptBuilder
from utils import create_tooltip, UndoManager, PreferencesManager, PresetManager
from config import TOOLTIPS, DEFAULT_THEME
from .constants import MAX_UNDO_STACK_SIZE, PREVIEW_UPDATE_THROTTLE_MS
from themes import ThemeManager


class VisualPromptBuilderUI:
    """Alternative UI layout with character gallery side panel (standalone version)."""
    
    def __init__(self, root):
        """Initialize visual UI.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Prompt Builder — Visual Gallery Mode")
        
        # Initialize managers (same as PromptBuilderApp)
        self.undo_manager = UndoManager(max_history=MAX_UNDO_STACK_SIZE)
        self.prefs = PreferencesManager()
        self.preset_manager = PresetManager()
        
        # Initialize data
        self.data_loader = DataLoader()
        
        try:
            self.characters = self.data_loader.load_characters()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Error loading characters: {str(e)}")
            self.root.destroy()
            return
        
        self.base_prompts = self.data_loader.load_base_prompts()
        self.scenes = self.data_loader.load_presets("scenes.md")
        self.poses = self.data_loader.load_presets("poses.md")
        self.randomizer = PromptRandomizer(self.characters, self.base_prompts, self.poses)
        
        # Initialize theme manager
        self.style = ttk.Style()
        self.theme_manager = ThemeManager(self.root, self.style)
        
        # Throttling for preview updates
        self._after_id = None
        self._throttle_ms = PREVIEW_UPDATE_THROTTLE_MS
        
        # Selected characters list
        self.selected_characters = []
        
        # Apply saved theme
        last_theme = self.prefs.get("last_theme", DEFAULT_THEME)
        self.theme_manager.apply_theme(last_theme)
        
        # Build UI
        self._build_ui()
        
        # Setup menu
        self._setup_menu()
        
        # Bind save event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _build_ui(self):
        """Build the visual UI layout."""
        # Main container with 3-pane layout
        # Left: Character Gallery | Middle: Settings | Right: Preview
        
        main_paned = ttk.PanedWindow(self.root, orient="horizontal")
        main_paned.pack(fill="both", expand=True)
        
        # LEFT PANEL: Character Gallery (fixed width ~250px)
        left_frame = ttk.Frame(main_paned, style="TFrame", width=250)
        main_paned.add(left_frame, weight=1)
        
        self.character_gallery = CharacterGalleryPanel(
            left_frame,
            self.data_loader,
            on_add_callback=self._on_character_selected,
            theme_colors=self.theme_manager.themes.get(
                self.theme_manager.current_theme or "Dark", {}
            )
        )
        self.character_gallery.pack(fill="both", expand=True)
        
        # Load characters into gallery
        self.character_gallery.load_characters(self.characters)
        
        # MIDDLE PANEL: Settings and controls
        middle_paned = ttk.PanedWindow(main_paned, orient="vertical")
        main_paned.add(middle_paned, weight=3)
        
        # Top section: Base prompt, scene, notes
        settings_frame = ttk.Frame(middle_paned, style="TFrame")
        middle_paned.add(settings_frame, weight=1)
        
        settings_frame.columnconfigure(0, weight=1)
        
        # Base prompt selector
        bp_frame = ttk.LabelFrame(settings_frame, text="📋 Base Prompt (Style)", style="TLabelframe")
        bp_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        bp_frame.columnconfigure(0, weight=1)
        
        self.base_prompt_var = tk.StringVar()
        base_combo = ttk.Combobox(bp_frame, state="readonly", textvariable=self.base_prompt_var)
        base_combo.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        base_combo.bind("<<ComboboxSelected>>", lambda e: self.schedule_preview_update())
        
        # Load base prompts
        base_combo['values'] = sorted(list(self.base_prompts.keys()))
        if self.base_prompts:
            base_combo.current(0)
        
        # Scene section
        scene_frame = ttk.LabelFrame(settings_frame, text="🎬 Scene", style="TLabelframe")
        scene_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        scene_frame.columnconfigure(0, weight=1)
        
        self.scene_text = tk.Text(scene_frame, wrap="word", height=3)
        self.scene_text.pack(fill="x", padx=4, pady=4)
        self.scene_text.bind("<KeyRelease>", lambda e: self.schedule_preview_update())
        
        # Notes section
        notes_frame = ttk.LabelFrame(settings_frame, text="📝 Notes", style="TLabelframe")
        notes_frame.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)
        notes_frame.columnconfigure(0, weight=1)
        settings_frame.rowconfigure(2, weight=1)
        
        self.notes_text = tk.Text(notes_frame, wrap="word", height=4)
        self.notes_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.notes_text.bind("<KeyRelease>", lambda e: self.schedule_preview_update())
        
        # Bottom section: Selected characters list
        selected_frame = ttk.LabelFrame(settings_frame, text="✨ Selected Characters", style="TLabelframe")
        selected_frame.grid(row=3, column=0, sticky="nsew", padx=4, pady=4)
        selected_frame.columnconfigure(0, weight=1)
        selected_frame.rowconfigure(0, weight=1)
        settings_frame.rowconfigure(3, weight=2)
        
        # Scrollable list of selected characters
        list_frame = ttk.Frame(selected_frame)
        list_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.selected_listbox = tk.Listbox(list_frame, height=6)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.selected_listbox.yview)
        self.selected_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.selected_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        btn_frame = ttk.Frame(selected_frame)
        btn_frame.pack(fill="x", padx=4, pady=(0, 4))
        
        ttk.Button(btn_frame, text="Remove Selected", 
                  command=self._remove_selected).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Clear All", 
                  command=self._clear_all).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🎲 Randomize", 
                  command=self.randomize_all).pack(side="right", padx=2)
        
        # RIGHT PANEL: Preview
        right_frame = ttk.Frame(main_paned, style="TFrame")
        main_paned.add(right_frame, weight=3)
        
        self.preview_panel = PreviewPanel(
            right_frame,
            self.theme_manager,
            self.reload_data,
            self.randomize_all
        )
        
        # Set preview callbacks
        self.preview_panel.set_callbacks(
            self._generate_prompt,
            self._validate_prompt,
            self.randomize_all
        )
    
    def _on_character_selected(self, character_name):
        """Handle character selection from gallery.
        
        Args:
            character_name: Name of selected character
        """
        # Add to selected characters
        char_def = self.characters.get(character_name, {})
        outfits = char_def.get("outfits", {})
        
        # Auto-assign first available outfit
        outfit = ""
        if "Base" in outfits:
            outfit = "Base"
        elif outfits:
            outfit = sorted(list(outfits.keys()))[0]
        
        # Add to selected characters list
        self.selected_characters.append({
            'name': character_name,
            'outfit': outfit,
            'pose_category': '',
            'pose_preset': '',
            'action_note': ''
        })
        
        # Update listbox
        self._update_selected_list()
        
        # Update preview
        self.schedule_preview_update()
    
    def _update_selected_list(self):
        """Update the selected characters listbox."""
        self.selected_listbox.delete(0, tk.END)
        
        for char in self.selected_characters:
            display = f"{char['name']}"
            if char.get('outfit'):
                display += f" - {char['outfit']}"
            self.selected_listbox.insert(tk.END, display)
    
    def _remove_selected(self):
        """Remove selected character from list."""
        selection = self.selected_listbox.curselection()
        if selection:
            idx = selection[0]
            self.selected_characters.pop(idx)
            self._update_selected_list()
            self.schedule_preview_update()
    
    def _clear_all(self):
        """Clear all selected characters."""
        from tkinter import messagebox
        if messagebox.askyesno("Clear All", "Remove all characters?"):
            self.selected_characters.clear()
            self._update_selected_list()
            self.schedule_preview_update()
    
    def load_characters(self, characters):
        """Load characters into gallery.
        
        Args:
            characters: Dict of character data
        """
        self.character_gallery.load_characters(characters)
    
    def schedule_preview_update(self):
        """Schedule a preview update with throttling."""
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(self._throttle_ms, self._update_preview)
    
    def _update_preview(self):
        """Update the preview panel."""
        self._after_id = None
        self.preview_panel.update_preview()
    
    def _generate_prompt(self):
        """Generate the final prompt."""
        builder = PromptBuilder()
        
        # Get base prompt
        base_key = self.base_prompt_var.get()
        base_text = self.base_prompts.get(base_key, {}).get('text', '')
        
        # Get scene
        scene = self.scene_text.get('1.0', 'end-1c').strip()
        
        # Get notes
        notes = self.notes_text.get('1.0', 'end-1c').strip()
        
        # Build character descriptions
        char_descriptions = []
        for char in self.selected_characters:
            char_name = char['name']
            char_def = self.characters.get(char_name, {})
            
            # Get outfit details
            outfit_name = char.get('outfit', '')
            outfit_details = char_def.get('outfits', {}).get(outfit_name, {})
            
            desc = f"{char_name}"
            if outfit_details:
                desc += f", {outfit_details.get('description', '')}"
            
            char_descriptions.append(desc)
        
        # Build prompt
        parts = []
        if base_text:
            parts.append(base_text)
        if scene:
            parts.append(f"Scene: {scene}")
        if char_descriptions:
            parts.append(f"Characters: {', '.join(char_descriptions)}")
        if notes:
            parts.append(notes)
        
        return '\\n\\n'.join(parts)
    
    def _validate_prompt(self):
        """Validate the current prompt configuration."""
        return len(self.selected_characters) > 0
    
    def randomize_all(self):
        """Randomize all settings."""
        # Randomize base prompt
        if self.base_prompts:
            import random
            random_base = random.choice(list(self.base_prompts.keys()))
            self.base_prompt_var.set(random_base)
        
        # Randomize characters
        if self.characters:
            import random
            num_chars = random.randint(1, min(4, len(self.characters)))
            random_chars = random.sample(list(self.characters.keys()), num_chars)
            
            self.selected_characters.clear()
            for char_name in random_chars:
                char_def = self.characters.get(char_name, {})
                outfits = char_def.get("outfits", {})
                outfit = ""
                if "Base" in outfits:
                    outfit = "Base"
                elif outfits:
                    outfit = random.choice(list(outfits.keys()))
                
                self.selected_characters.append({
                    'name': char_name,
                    'outfit': outfit,
                    'pose_category': '',
                    'pose_preset': '',
                    'action_note': ''
                })
            
            self._update_selected_list()
        
        self.schedule_preview_update()
    
    def reload_data(self):
        """Reload all data from files."""
        try:
            self.characters = self.data_loader.load_characters()
            self.base_prompts = self.data_loader.load_base_prompts()
            self.scenes = self.data_loader.load_presets("scenes.md")
            self.poses = self.data_loader.load_presets("poses.md")
            self.randomizer = PromptRandomizer(self.characters, self.base_prompts, self.poses)
            
            # Reload gallery
            self.character_gallery.load_characters(self.characters)
            
            from tkinter import messagebox
            messagebox.showinfo("Success", "Data reloaded successfully!")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to reload data: {str(e)}")
    
    def _setup_menu(self):
        """Setup the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        for theme_name in self.theme_manager.themes.keys():
            theme_menu.add_command(
                label=theme_name,
                command=lambda t=theme_name: self._change_theme(t)
            )
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        
        # UI Mode submenu
        ui_mode_menu = tk.Menu(view_menu, tearoff=0)
        ui_mode_menu.add_command(label="Classic (Tabs)", command=lambda: self._switch_ui_mode("classic"))
        ui_mode_menu.add_command(label="Visual Gallery", command=lambda: self._switch_ui_mode("visual"))
        view_menu.add_cascade(label="UI Mode", menu=ui_mode_menu)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Reload Data", command=self.reload_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
    
    def _change_theme(self, theme_name):
        """Change the current theme."""
        self.theme_manager.apply_theme(theme_name)
        self.prefs.set("last_theme", theme_name)
        
        # Update gallery colors
        theme_colors = self.theme_manager.themes.get(theme_name, {})
        self.character_gallery.theme_colors = theme_colors
        self.character_gallery._refresh_display()
    
    def _switch_ui_mode(self, mode):
        """Switch UI mode."""
        self.prefs.set("ui_mode", mode)
        from tkinter import messagebox
        messagebox.showinfo("UI Mode", "UI mode changed. Please restart the application.")
    
    def _on_closing(self):
        """Handle window closing."""
        # Save preferences
        geometry = self.root.geometry()
        self.prefs.set("window_geometry", geometry)
        
        self.root.destroy()
