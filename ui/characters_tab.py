# -*- coding: utf-8 -*-
"""Characters and poses tab UI."""

import tkinter as tk
from tkinter import ttk, messagebox
from .widgets import FlowFrame, CollapsibleFrame, ScrollableCanvas
from .character_creator import CharacterCreatorDialog
from .base_style_creator import BaseStyleCreatorDialog
from .outfit_creator import SharedOutfitCreatorDialog, CharacterOutfitCreatorDialog
from .pose_creator import PoseCreatorDialog
from .scene_creator import SceneCreatorDialog
from utils import create_tooltip
from config import TOOLTIPS
from .constants import DEFAULT_TEXT_WIDGET_HEIGHT


class CharactersTab:
    """Tab for managing characters, outfits, and poses."""
    
    def __init__(self, parent, data_loader, on_change_callback, reload_callback=None, undo_callback=None):
        """Initialize characters tab.
        
        Args:
            parent: Parent notebook widget
            data_loader: DataLoader instance
            on_change_callback: Function to call when data changes
            reload_callback: Function to call to reload all data
            undo_callback: Function to call to save state for undo
        """
        self.parent = parent
        self.data_loader = data_loader
        self.on_change = on_change_callback
        self.reload_data = reload_callback
        self.save_for_undo = undo_callback
        
        self.characters = {}
        self.base_prompts = {}
        self.poses = {}
        self.scenes = {}
        self.selected_characters = []
        
        # Debounce tracking for action notes
        self._action_note_after_ids = {}
        
        # Drag and drop state
        self._drag_data = {"index": None, "widget": None}
        
        # Guard against recursive refresh
        self._refreshing = False
        
        self.tab = ttk.Frame(parent, style="TFrame")
        parent.add(self.tab, text="Prompt Builder")
        
        self._build_ui()
    
    def load_data(self, characters, base_prompts, poses, scenes=None):
        """Load character and prompt data.
        
        Args:
            characters: Character definitions dict
            base_prompts: Base prompts dict
            poses: Pose presets dict
            scenes: Scene presets dict (optional, handled by main_window now)
        """
        self.characters = characters
        self.base_prompts = base_prompts
        self.poses = poses
        if scenes:
            self.scenes = scenes
        
        # Update UI - preserve current selections
        current_base = self.base_combo.get()
        self.base_combo['values'] = sorted(list(self.base_prompts.keys()))
        if self.base_prompts:
            # Try to restore previous selection, otherwise use first item
            if current_base and current_base in self.base_prompts:
                self.base_combo.set(current_base)
            else:
                self.base_combo.current(0)
        
        self.char_combo['values'] = sorted(list(self.characters.keys()))
        
        # Update bulk outfit combo with all available outfits across characters
        all_outfits = set()
        for char_data in self.characters.values():
            all_outfits.update(char_data.get("outfits", {}).keys())
        self.bulk_outfit_combo['values'] = sorted(list(all_outfits))
        
        self._refresh_list()
    
    def _build_ui(self):
        """Build the characters tab UI."""
        self.tab.columnconfigure(0, weight=1)
        self.tab.rowconfigure(3, weight=1)  # Selected characters area expands

        # Base prompt selector
        bp = ttk.LabelFrame(self.tab, text="📋 Base Prompt (Style)", style="TLabelframe")
        bp.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        bp.columnconfigure(0, weight=1)
        help_label = ttk.Label(bp, text="Choose a base art style", foreground="gray", font=("Consolas", 9))
        help_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 0))
        create_tooltip(help_label, TOOLTIPS.get("base_prompt", ""))
        
        self.base_prompt_var = tk.StringVar()
        self.base_combo = ttk.Combobox(bp, state="readonly", textvariable=self.base_prompt_var)
        self.base_combo.grid(row=1, column=0, sticky="ew", padx=(4, 2), pady=(0, 4))
        self.base_combo.bind("<<ComboboxSelected>>", lambda e: self.on_change())
        create_tooltip(self.base_combo, TOOLTIPS.get("base_prompt", ""))
        
        ttk.Button(bp, text="✨ Create Style", command=self._create_new_style).grid(row=1, column=1, sticky="ew", padx=(2, 4), pady=(0, 4))

        # Bulk outfit editor section (Collapsible)
        self.bulk_container = CollapsibleFrame(self.tab, text="⚡ Bulk Outfit Editor")
        self.bulk_container.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        # Start collapsed
        self.bulk_container._toggle_cb()
        
        bulk = self.bulk_container.get_content_frame()
        bulk.columnconfigure(1, weight=1)
        
        # Info section
        info_frame = ttk.Frame(bulk, relief="groove", borderwidth=1)
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 8))
        info_frame.columnconfigure(0, weight=1)
        
        info_text = ttk.Label(info_frame, 
            text="💡 Apply the same outfit to multiple characters at once",
            foreground="#0066cc", font=("Consolas", 9, "bold"))
        info_text.pack(anchor="w", padx=6, pady=2)
        
        help_text = ttk.Label(info_frame,
            text="Select an outfit and click a button to apply it",
            foreground="gray", font=("Consolas", 8))
        help_text.pack(anchor="w", padx=6, pady=(0, 2))
        
        ttk.Label(bulk, text="Select Outfit:").grid(row=1, column=0, sticky="w", padx=(4, 2))
        self.bulk_outfit_var = tk.StringVar()
        self.bulk_outfit_combo = ttk.Combobox(bulk, textvariable=self.bulk_outfit_var, state="readonly")
        self.bulk_outfit_combo.grid(row=1, column=1, sticky="ew", padx=2)
        self.bulk_outfit_combo['values'] = []
        self.bulk_outfit_combo.bind("<<ComboboxSelected>>", lambda e: self._update_bulk_preview())
        self.bulk_outfit_combo.bind("<Return>", lambda e: self._apply_bulk_outfit())
        create_tooltip(self.bulk_outfit_combo, "Choose an outfit to apply to selected characters")
        
        # Preview/status label
        self.bulk_preview_var = tk.StringVar(value="")
        self.bulk_preview_label = ttk.Label(bulk, textvariable=self.bulk_preview_var, 
                                           foreground="gray", font=("Consolas", 8))
        self.bulk_preview_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 4))
        
        # Button row
        btn_frame = ttk.Frame(bulk)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)
        
        ttk.Button(btn_frame, text="✓ Apply to All", 
                  command=self._apply_bulk_to_all).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        ttk.Button(btn_frame, text="✓ Apply to Selected", 
                  command=self._apply_bulk_to_selected).grid(row=0, column=1, sticky="ew", padx=2)
        ttk.Button(btn_frame, text="✨ Create Shared Outfit", 
                  command=self._create_shared_outfit).grid(row=0, column=2, sticky="ew", padx=(2, 0))

        # Add character section
        add = ttk.LabelFrame(self.tab, text="👥 Add Character", style="TLabelframe")
        add.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        add.columnconfigure(0, weight=1)
        char_help = ttk.Label(add, text="Select a character and press Add or Enter", foreground="gray", font=("Consolas", 9))
        char_help.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 4))
        create_tooltip(char_help, TOOLTIPS.get("character", ""))
        
        # Search field
        search_frame = ttk.Frame(add)
        search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 2))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="🔍", font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0, 2))
        self.char_search_var = tk.StringVar()
        self.char_search_entry = ttk.Entry(search_frame, textvariable=self.char_search_var)
        self.char_search_entry.grid(row=0, column=1, sticky="ew")
        self.char_search_var.trace('w', lambda *args: self._filter_characters())
        create_tooltip(self.char_search_entry, "Type to filter characters")
        
        # Clear search button
        ttk.Button(search_frame, text="✕", width=3, command=lambda: self.char_search_var.set("")).grid(row=0, column=2, padx=(2, 0))
        
        self.char_var = tk.StringVar()
        self.char_combo = ttk.Combobox(add, state="readonly", textvariable=self.char_var)
        self.char_combo.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 4), padx=4)
        self.char_combo.bind("<Return>", lambda e: self._add_character())
        self.char_combo.bind("<KP_Enter>", lambda e: self._add_character())  # Numpad Enter
        create_tooltip(self.char_combo, TOOLTIPS.get("character", ""))
        
        button_frame = ttk.Frame(add)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        ttk.Button(button_frame, text="+ Add to Prompt", command=self._add_character).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        ttk.Button(button_frame, text="✨ Create New Character", command=self._create_new_character).grid(row=0, column=1, sticky="ew", padx=(2, 0))

        # Use ScrollableCanvas for selected characters
        self.scrollable_canvas = ScrollableCanvas(self.tab)
        self.scrollable_canvas.grid(row=3, column=0, sticky="nsew", padx=4, pady=4)
        
        # Get container for characters
        self.chars_container = self.scrollable_canvas.get_container()
        # Keep reference to canvas for backward compatibility
        self.chars_canvas = self.scrollable_canvas.canvas
    
    def _safe_update_canvas_width(self, width):
        """Safely update canvas window width.
        
        Args:
            width: New width value
        """
        try:
            if self.chars_canvas.winfo_exists():
                self.chars_canvas.itemconfig(self._chars_window, width=width)
        except tk.TclError as e:
            # Canvas destroyed - expected during cleanup
            from utils import logger
            logger.debug(f"Canvas update skipped: widget destroyed")
        except AttributeError as e:
            # Canvas attribute missing - shouldn't happen
            from utils import logger
            logger.warning(f"Canvas attribute error: {e}")
    
    def _update_bulk_preview(self):
        """Update preview text showing which characters will be affected."""
        outfit_name = self.bulk_outfit_var.get()
        
        if not outfit_name or not self.selected_characters:
            self.bulk_preview_var.set("")
            return
        
        # All selected characters have all outfits
        count = len(self.selected_characters)
        if count == 1:
            self.bulk_preview_var.set(f"✓ Will update: {self.selected_characters[0]['name']}")
        else:
            self.bulk_preview_var.set(f"✓ Will update {count} characters")
    
    def _apply_bulk_to_all(self):
        """Apply selected outfit to all selected characters."""
        outfit_name = self.bulk_outfit_var.get()
        
        if not outfit_name:
            messagebox.showwarning("Selection Required", "Please select an outfit to apply")
            return
        
        if not self.selected_characters:
            messagebox.showwarning("No Characters", "No characters are currently selected")
            return
        
        # Save state for undo
        if self.save_for_undo:
            self.save_for_undo()
        
        # Apply to all selected characters
        count = len(self.selected_characters)
        for char in self.selected_characters:
            char["outfit"] = outfit_name
        
        self._refresh_list()
        self.on_change()
        self.bulk_outfit_var.set("")  # Clear for next use
        
        # Show status feedback
        root = self.tab.winfo_toplevel()
        if hasattr(root, '_update_status'):
            root._update_status(f"Applied '{outfit_name}' to all {count} character(s)")
    
    def _apply_bulk_to_selected(self):
        """Apply selected outfit to a specific selected character via dialog."""
        outfit_name = self.bulk_outfit_var.get()
        
        if not outfit_name:
            messagebox.showwarning("Selection Required", "Please select an outfit to apply")
            return
        
        if not self.selected_characters:
            messagebox.showwarning("No Characters", "No characters are currently selected")
            return
        
        # If only one character, apply directly
        if len(self.selected_characters) == 1:
            if self.save_for_undo:
                self.save_for_undo()
            
            self.selected_characters[0]["outfit"] = outfit_name
            self._refresh_list()
            self.on_change()
            self.bulk_outfit_var.set("")
            
            root = self.tab.winfo_toplevel()
            if hasattr(root, '_update_status'):
                root._update_status(f"Applied '{outfit_name}' to {self.selected_characters[0]['name']}")
            return
        
        # Multiple characters - show selection dialog
        from tkinter import simpledialog
        
        # Create a custom dialog for character selection
        dialog = tk.Toplevel(self.tab)
        dialog.title("Select Character")
        dialog.transient(self.tab.winfo_toplevel())
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text=f"Apply '{outfit_name}' to:", font=("Consolas", 10, "bold")).pack(pady=(10, 5))
        
        # Listbox with characters
        listbox_frame = ttk.Frame(dialog)
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")
        
        char_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set)
        char_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=char_listbox.yview)
        
        for char in self.selected_characters:
            char_listbox.insert(tk.END, char["name"])
        
        char_listbox.selection_set(0)  # Select first by default
        
        result = {"selected": None}
        
        def on_ok():
            selection = char_listbox.curselection()
            if selection:
                result["selected"] = self.selected_characters[selection[0]]
                dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Apply", command=on_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)
        
        # Bind double-click
        char_listbox.bind("<Double-Button-1>", lambda e: on_ok())
        
        dialog.wait_window()
        
        # Apply the outfit if a character was selected
        if result["selected"]:
            if self.save_for_undo:
                self.save_for_undo()
            
            result["selected"]["outfit"] = outfit_name
            self._refresh_list()
            self.on_change()
            self.bulk_outfit_var.set("")
            
            root = self.tab.winfo_toplevel()
            if hasattr(root, '_update_status'):
                root._update_status(f"Applied '{outfit_name}' to {result['selected']['name']}")
    
    def _filter_characters(self):
        """Filter character dropdown based on search text."""
        search = self.char_search_var.get().lower()
        
        # Get currently used characters
        used = {c["name"] for c in self.selected_characters}
        available = [k for k in self.characters.keys() if k not in used]
        
        if search:
            # Filter by search term
            filtered = [c for c in available if search in c.lower()]
            self.char_combo['values'] = sorted(filtered)
        else:
            # Show all available
            self.char_combo['values'] = sorted(available)
        
        # Clear selection if current selection not in filtered list
        if self.char_var.get() not in self.char_combo['values']:
            self.char_var.set("")
    
    def _add_character(self):
        """Add selected character to the list."""
        name = self.char_var.get()
        if not name:
            return
        if any(c['name'] == name for c in self.selected_characters):
            messagebox.showinfo("Already Added", f"{name} is already in the prompt")
            return
        
        # Save state for undo
        if self.save_for_undo:
            self.save_for_undo()
        
        # Auto-assign first available outfit as default
        outfit = ""
        char_def = self.characters.get(name, {})
        outfits = char_def.get("outfits", {})
        if "Base" in outfits:
            outfit = "Base"
        elif outfits:
            outfit = sorted(list(outfits.keys()))[0]
        
        self.selected_characters.append({
            'name': name,
            'outfit': outfit,
            'pose_category': '',
            'pose_preset': '',
            'action_note': ''
        })
        self.char_var.set("")
        self._refresh_list()
        # Auto-scroll to the newly added character
        self.chars_canvas.yview_moveto(1.0)
    
    def _create_new_character(self):
        """Open dialog to create a new character."""
        # Get the root window to use as parent
        root = self.tab.winfo_toplevel()
        dialog = CharacterCreatorDialog(root, self.data_loader, self.reload_data)
        result = dialog.show()
        
        # If character was created and reload callback exists, it will be called automatically
    
    def _create_new_style(self):
        """Open dialog to create a new base art style."""
        root = self.tab.winfo_toplevel()
        dialog = BaseStyleCreatorDialog(root, self.data_loader, self.reload_data)
        result = dialog.show()
    
    def _create_shared_outfit(self):
        """Open dialog to create a new shared outfit."""
        root = self.tab.winfo_toplevel()
        dialog = SharedOutfitCreatorDialog(root, self.data_loader, self.reload_data)
        result = dialog.show()
    
    def _create_character_outfit(self, character_name):
        """Open dialog to create a new character-specific outfit."""
        root = self.tab.winfo_toplevel()
        dialog = CharacterOutfitCreatorDialog(root, self.data_loader, character_name, self.reload_data)
        result = dialog.show()
    
    def _create_new_pose(self):
        """Open dialog to create a new pose preset."""
        root = self.tab.winfo_toplevel()
        dialog = PoseCreatorDialog(root, self.data_loader, self.reload_data)
        result = dialog.show()
    
    def _remove_character(self, idx):
        """Remove character at index."""
        # Add confirmation for destructive action
        char_name = self.selected_characters[idx].get('name', 'this character')
        if not messagebox.askyesno("Remove Character", 
                                   f"Remove {char_name} from the prompt?",
                                   icon='question'):
            return
        
        if self.save_for_undo:
            self.save_for_undo()
        self.selected_characters.pop(idx)
        self._refresh_list()
    
    def _move_up(self, idx):
        """Move character up in list."""
        if idx > 0:
            if self.save_for_undo:
                self.save_for_undo()
            self.selected_characters[idx - 1], self.selected_characters[idx] = (
                self.selected_characters[idx],
                self.selected_characters[idx - 1],
            )
            self._refresh_list()
    
    def _move_down(self, idx):
        """Move character down in list."""
        if idx < len(self.selected_characters) - 1:
            if self.save_for_undo:
                self.save_for_undo()
            self.selected_characters[idx + 1], self.selected_characters[idx] = (
                self.selected_characters[idx],
                self.selected_characters[idx + 1],
            )
            self._refresh_list()
    
    def _update_outfit(self, idx, outfit_name):
        """Update character outfit."""
        self.selected_characters[idx]["outfit"] = outfit_name
        # Refresh the list so outfit buttons update their visual state
        self._refresh_list()
    
    def _update_action_note(self, idx, text_widget):
        """Update character action note with debouncing."""
        from .constants import TEXT_UPDATE_DEBOUNCE_MS
        
        # Cancel any pending update for this index
        if idx in self._action_note_after_ids:
            try:
                self.tab.after_cancel(self._action_note_after_ids[idx])
            except (tk.TclError, ValueError):
                # Widget destroyed or invalid ID
                pass
        
        # Schedule new update after debounce delay
        def _do_update():
            text = text_widget.get("1.0", "end").strip()
            self.selected_characters[idx]["action_note"] = text
            self.on_change()
            if idx in self._action_note_after_ids:
                del self._action_note_after_ids[idx]
        
        self._action_note_after_ids[idx] = self.tab.after(TEXT_UPDATE_DEBOUNCE_MS, _do_update)
    
    def _update_pose_category(self, idx, category_var, preset_combo):
        """Update character pose category."""
        cat = category_var.get()
        self.selected_characters[idx]["pose_category"] = cat
        self.selected_characters[idx]["pose_preset"] = ""
        
        if cat and cat in self.poses:
            preset_combo["values"] = [""] + sorted(list(self.poses[cat].keys()))
        else:
            preset_combo["values"] = [""]
        preset_combo.set("") 
        # Refresh the list to rebuild comboboxes with current values showing
        self._refresh_list()
    
    def _update_pose_preset(self, idx, preset_name):
        """Update character pose preset."""
        self.selected_characters[idx]["pose_preset"] = preset_name
        # Refresh to show the selection
        self._refresh_list()
    
    def _refresh_list(self):
        """Refresh the list of selected characters."""
        if self._refreshing:
            return
        
        self._refreshing = True
        
        for w in self.chars_container.winfo_children():
            w.destroy()

        # Update available characters
        used = {c["name"] for c in self.selected_characters}
        available = sorted([k for k in self.characters.keys() if k not in used])
        self.char_combo["values"] = available
        
        # Show empty state if no characters
        if not self.selected_characters:
            empty_frame = ttk.Frame(self.chars_container, style="TFrame")
            empty_frame.pack(fill="both", expand=True, padx=4, pady=20)
            empty_label = ttk.Label(empty_frame, text="👈 Add characters to get started", foreground="gray", font=("Consolas", 11))
            empty_label.pack()
            # Manually update scroll region
            try:
                self.chars_canvas.config(scrollregion=self.chars_canvas.bbox("all"))
            except Exception:
                pass
            self._refreshing = False
            return

        for i, cd in enumerate(self.selected_characters):
            char_title = f"#{i+1} — {cd['name']}"
            frame = ttk.LabelFrame(self.chars_container, text=char_title, 
                                 padding=6, style="TLabelframe")
            frame.pack(fill="x", pady=(0, 8), padx=4)
            
            # Add context menu to frame
            self._add_context_menu(frame, i)
            
            # Outfit selector - collapsible
            outfit_header = ttk.Frame(frame)
            outfit_header.pack(fill="x", pady=(0, 2))
            
            outfit_label = ttk.Label(outfit_header, text="👕 Outfit:", font=("Consolas", 9, "bold"))
            outfit_label.pack(side="left")
            
            # Show current outfit
            current_outfit = cd.get("outfit", "")
            if current_outfit:
                current_label = ttk.Label(outfit_header, text=f" {current_outfit}", font=("Consolas", 9), foreground="#0066cc")
                current_label.pack(side="left")
            
            # Collapsible outfit frame
            outfit_container = ttk.Frame(frame)
            outfit_expanded = tk.BooleanVar(value=False)
            
            def make_toggle(container, expanded, parent_frame, header_widget):
                def toggle():
                    if expanded.get():
                        container.pack_forget()
                        expanded.set(False)
                    else:
                        # Pack after the header widget - fill both to allow vertical expansion
                        container.pack(fill="both", expand=False, pady=(0, 6), after=header_widget)
                        expanded.set(True)
                    # Update scroll region after toggle to account for height change
                    self.tab.after(100, self.scrollable_canvas.update_scroll_region)
                return toggle
            
            toggle_func = make_toggle(outfit_container, outfit_expanded, frame, outfit_header)
            toggle_btn = ttk.Button(outfit_header, text="▼", width=3, command=toggle_func)
            toggle_btn.pack(side="right")
            
            # Outfit options inside collapsible frame
            outfits_frame = FlowFrame(outfit_container, padding_x=6, padding_y=4)
            outfits_frame.pack(fill="both", expand=True, pady=(2, 2))

            outfit_keys = sorted(list(self.characters.get(cd["name"], {}).get("outfits", {}).keys()))
            for o in outfit_keys:
                btn_style = "Accent.TButton" if o == current_outfit else "TButton"
                outfits_frame.add_button(
                    text=o,
                    style=btn_style,
                    command=(lambda idx=i, name=o, tog=toggle_func: (self._update_outfit(idx, name), tog()))
                )
            
            # Outfit creator button
            ttk.Button(outfit_container, text="✨ New Outfit for Character", 
                      command=lambda name=cd["name"]: self._create_character_outfit(name)).pack(fill="x", pady=(2, 0))
            
            # Pose preset selector
            ttk.Label(frame, text="🎭 Pose (Optional):", font=("Consolas", 9, "bold")).pack(fill="x", pady=(6, 2))
            pose_row = ttk.Frame(frame)
            pose_row.pack(fill="x", pady=(0, 4))
            pose_row.columnconfigure(3, weight=1)

            ttk.Label(pose_row, text="Category:").grid(row=0, column=0, sticky="w", padx=(0, 4))
            pcat_var = tk.StringVar(value=cd.get("pose_category", ""))
            pcat_combo = ttk.Combobox(pose_row, textvariable=pcat_var, state="readonly", width=15)
            pcat_combo["values"] = [""] + sorted(list(self.poses.keys()))
            pcat_combo.grid(row=0, column=1, padx=(0, 10))
            
            ttk.Label(pose_row, text="Preset:").grid(row=0, column=2, sticky="w", padx=(0, 4))
            preset_var = tk.StringVar(value=cd.get("pose_preset", ""))
            preset_combo = ttk.Combobox(pose_row, textvariable=preset_var, state="readonly", width=20)
            preset_combo.grid(row=0, column=3, sticky="ew")
            
            # Add create pose button
            ttk.Button(pose_row, text="✨", width=3, command=self._create_new_pose).grid(row=0, column=4, padx=(5, 0))

            # Initialize preset values
            current_cat = pcat_var.get()
            if current_cat and current_cat in self.poses:
                preset_combo["values"] = [""] + sorted(list(self.poses[current_cat].keys()))
            else:
                preset_combo["values"] = [""]

            pcat_combo.bind(
                "<<ComboboxSelected>>",
                lambda e, idx=i, cat_var=pcat_var, p_combo=preset_combo: 
                    self._update_pose_category(idx, cat_var, p_combo)
            )
            preset_combo.bind(
                "<<ComboboxSelected>>",
                lambda e, idx=i, var=preset_var: self._update_pose_preset(idx, var.get())
            )

            # Action note text area
            ttk.Label(frame, text="💬 Custom Pose/Action (Optional - Overrides Preset):", font=("Consolas", 9, "bold")).pack(fill="x", pady=(6, 0))
            action_text = tk.Text(frame, wrap="word", height=5)
            action_text.insert("1.0", cd.get("action_note", ""))
            action_text.pack(fill="x", pady=(0, 6))
            action_text.config(padx=5, pady=5)
            action_text.bind(
                "<KeyRelease>",
                lambda e, idx=i, tw=action_text: self._update_action_note(idx, tw)
            )

            # Separator
            ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=6)
            
            # Button row
            btnrow = ttk.Frame(frame, style="TFrame")
            btnrow.pack(fill="x")
            
            mv = ttk.Frame(btnrow, style="TFrame")
            mv.pack(side="left", fill="x", expand=True)
            if i > 0:
                ttk.Button(mv, text="↑ Move Up", width=10, 
                         command=lambda idx=i: self._move_up(idx)).pack(side="left", padx=(0, 4))
            if i < len(self.selected_characters) - 1:
                ttk.Button(mv, text="↓ Move Down", width=10, 
                         command=lambda idx=i: self._move_down(idx)).pack(side="left")
            
            ttk.Button(btnrow, text="✕ Remove", 
                     command=lambda idx=i: self._remove_character(idx)).pack(side="right")
        
        # Update scroll region and refresh mousewheel bindings
        self.scrollable_canvas.refresh_mousewheel_bindings()
        self.scrollable_canvas.update_scroll_region()
        
        # Defer on_change to avoid event queue overflow
        self.tab.after(1, self.on_change)
        self._refreshing = False
    
    def get_base_prompt_name(self):
        """Get selected base prompt name."""
        return self.base_prompt_var.get()
    
    def get_selected_characters(self):
        """Get list of selected characters with their data."""
        return self.selected_characters

    def set_selected_characters(self, characters_data):
        """Set the list of selected characters and refresh the UI.
        
        Args:
            characters_data: A list of character dictionaries.
        """
        self.selected_characters = characters_data
        self._refresh_list()

    def set_base_prompt(self, prompt_name):
        """Set the base prompt combobox to a specific value.
        
        Args:
            prompt_name: The name of the prompt to select.
        """
        if prompt_name in self.base_combo["values"]:
            self.base_prompt_var.set(prompt_name)

    def get_num_characters(self):
        """Get the number of selected characters."""
        return len(self.selected_characters)
    
    def apply_theme_to_action_texts(self, theme_manager, theme):
        """Apply theme to dynamic action text widgets.
        
        Args:
            theme_manager: ThemeManager instance
            theme: Theme color dict
        """
        for char_frame in self.chars_container.winfo_children():
            for widget in char_frame.winfo_children():
                if isinstance(widget, tk.Text):
                    theme_manager.apply_text_widget_theme(widget, theme)
    
    def _add_context_menu(self, widget, char_index):
        """Add context menu to character widget.
        
        Args:
            widget: Widget to add menu to
            char_index: Index of character
        """
        menu = tk.Menu(widget, tearoff=0)
        
        menu.add_command(label="Duplicate Character", 
                        command=lambda: self._duplicate_character(char_index))
        menu.add_separator()
        
        if char_index > 0:
            menu.add_command(label="Move Up", 
                            command=lambda: self._move_up(char_index))
        if char_index < len(self.selected_characters) - 1:
            menu.add_command(label="Move Down", 
                            command=lambda: self._move_down(char_index))
        
        menu.add_separator()
        menu.add_command(label="Copy Character Data", 
                        command=lambda: self._copy_character_data(char_index))
        menu.add_separator()
        menu.add_command(label="Remove Character", 
                        command=lambda: self._remove_character(char_index))
        
        def show_menu(event):
            menu.post(event.x_root, event.y_root)
        
        widget.bind("<Button-3>", show_menu)  # Right-click
    
    def _duplicate_character(self, idx):
        """Duplicate character at index.
        
        Args:
            idx: Index of character to duplicate
        """
        if self.save_for_undo:
            self.save_for_undo()
        
        import copy
        char = copy.deepcopy(self.selected_characters[idx])  # Use deep copy to avoid shared references
        self.selected_characters.insert(idx + 1, char)
        self._refresh_list()
        self.on_change()
    
    def _copy_character_data(self, idx):
        """Copy character data to clipboard.
        
        Args:
            idx: Index of character
        """
        char = self.selected_characters[idx]
        data = f"{char['name']}"
        if char.get('outfit'):
            data += f" - {char['outfit']}"
        if char.get('pose_preset'):
            data += f" - Pose: {char['pose_preset']}"
        if char.get('action_note'):
            data += f" - Action: {char['action_note']}"
        
        self.tab.clipboard_clear()
        self.tab.clipboard_append(data)
        
        # Show brief feedback
        root = self.tab.winfo_toplevel()
        if hasattr(root, '_update_status'):
            root._update_status("Character data copied to clipboard")
    
    def add_character_from_gallery(self, character_name):
        """Add a character from the gallery to selected characters.
        
        Args:
            character_name: Name of the character to add
        """
        if self.save_for_undo:
            self.save_for_undo()
        
        # Auto-assign first available outfit as default
        outfit = ""
        char_def = self.characters.get(character_name, {})
        outfits = char_def.get("outfits", {})
        if "Base" in outfits:
            outfit = "Base"
        elif outfits:
            outfit = sorted(list(outfits.keys()))[0]
        
        self.selected_characters.append({
            'name': character_name,
            'outfit': outfit,
            'pose_category': '',
            'pose_preset': '',
            'action_note': ''
        })
        self._refresh_list()
        # Auto-scroll to the newly added character
        self.chars_canvas.yview_moveto(1.0)
        self.on_change()


