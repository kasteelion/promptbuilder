# -*- coding: utf-8 -*-
"""Characters and poses tab UI."""

import tkinter as tk
from tkinter import messagebox, ttk

from config import TOOLTIPS
from utils import create_tooltip, logger
from utils.outfit_color_check import outfit_has_color_vars
from utils.color_scheme import parse_color_schemes

from .base_style_creator import BaseStyleCreatorDialog
from .character_creator import CharacterCreatorDialog
from .character_item import CharacterItem
from .outfit_creator import CharacterOutfitCreatorDialog, SharedOutfitCreatorDialog
from .pose_creator import PoseCreatorDialog
from .searchable_combobox import SearchableCombobox
from .widgets import CollapsibleFrame, FlowFrame, ScrollableCanvas


class CharactersTab:
    """Tab for managing characters, outfits, and poses."""

    def __init__(
        self, parent, data_loader, on_change_callback, reload_callback=None, undo_callback=None
    ):
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
        self.categorized_all = {}

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
        base_keys = sorted(list(self.base_prompts.keys()))
        self.base_combo.set_values(base_keys)
        if self.base_prompts:
            # Try to restore previous selection, otherwise use first item
            if current_base and current_base in self.base_prompts:
                self.base_combo.set(current_base)
            else:
                self.base_combo.set(base_keys[0])

        self.char_combo.set_values(sorted(list(self.characters.keys())))

        # Update bulk outfit combo with categorized lists
        self.categorized_all = {}
        
        # 1. From shared files (source of truth for categories)
        try:
            shared = self.data_loader.load_outfits()
            # Flatten F/M/H differentiation for the bulk list categories
            if isinstance(shared, dict):
                for gender_key, categories in shared.items():
                    if isinstance(categories, dict):
                        for cat, outfits in categories.items():
                            if cat not in self.categorized_all:
                                self.categorized_all[cat] = set()
                            self.categorized_all[cat].update(outfits.keys())
        except Exception:
            pass

        # 2. From individual characters (for Personal or unique ones)
        for char_data in self.characters.values():
            char_cats = char_data.get("outfits_categorized", {})
            for cat, outfits in char_cats.items():
                if cat not in self.categorized_all:
                    self.categorized_all[cat] = set()
                self.categorized_all[cat].update(outfits.keys())

        # Set values for category combo
        self.bulk_cat_combo.set_values(sorted(list(self.categorized_all.keys())))
        self.bulk_outfit_combo.set_values([]) # Clear outfits until category selected

        self._refresh_list()

    def _on_bulk_cat_select(self, val):
        """Handle bulk category selection."""
        outfits = sorted(list(self.categorized_all.get(val, set())))
        self.bulk_outfit_combo.set_values(outfits)
        self.bulk_outfit_combo.set("")

    def _build_ui(self):
        """Build the characters tab UI."""
        self.tab.columnconfigure(0, weight=1)
        self.tab.rowconfigure(3, weight=1)  # Selected characters area expands

        # Standard section padding
        SECTION_PAD_Y = (4, 8)

        # Base prompt selector
        bp = ttk.LabelFrame(self.tab, text="📋 Base Prompt (Style)", style="TLabelframe")
        bp.grid(row=0, column=0, sticky="ew", padx=6, pady=SECTION_PAD_Y)
        bp.columnconfigure(0, weight=1)
        help_label = ttk.Label(bp, text="Choose a base art style", style="Muted.TLabel")
        help_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2))
        create_tooltip(help_label, TOOLTIPS.get("base_prompt", ""))

        self.base_prompt_var = tk.StringVar()
        self.base_combo = SearchableCombobox(
            bp, 
            values=sorted(list(self.base_prompts.keys())),
            on_select=lambda val: self.on_change(),
            placeholder="Search style...",
            textvariable=self.base_prompt_var
        )
        self.base_combo.grid(row=1, column=0, sticky="ew", padx=(4, 2), pady=(2, 6))
        create_tooltip(self.base_combo, TOOLTIPS.get("base_prompt", ""))

        ttk.Button(bp, text="✨ Create Style", command=self._create_new_style).grid(
            row=1, column=1, sticky="ew", padx=(2, 4), pady=(2, 6)
        )

        # Bulk outfit editor section (Collapsible)
        self.bulk_container = CollapsibleFrame(self.tab, text="⚡ Bulk Outfit Editor")
        self.bulk_container.grid(row=1, column=0, sticky="ew", padx=6, pady=SECTION_PAD_Y)
        # Start collapsed
        self.bulk_container._toggle_cb()

        bulk = self.bulk_container.get_content_frame()
        bulk.columnconfigure(1, weight=1)

        # Info section
        info_frame = ttk.Frame(bulk, relief="groove", borderwidth=1)
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 10))
        info_frame.columnconfigure(0, weight=1)

        info_text = ttk.Label(
            info_frame,
            text="💡 Apply the same outfit to multiple characters at once",
            style="Accent.TLabel",
        )
        info_text.pack(anchor="w", padx=6, pady=4)

        help_text = ttk.Label(
            info_frame,
            text="Select an outfit and click a button to apply it",
            style="Muted.TLabel",
        )
        help_text.pack(anchor="w", padx=6, pady=(0, 4))

        # Bulk Category
        cat_frame = ttk.Frame(bulk)
        cat_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=4, pady=2)
        ttk.Label(cat_frame, text="Category:", width=9).pack(side="left")
        
        self.bulk_cat_var = tk.StringVar()
        self.bulk_cat_combo = SearchableCombobox(
            cat_frame,
            textvariable=self.bulk_cat_var,
            on_select=self._on_bulk_cat_select,
            placeholder="Select category...",
            width=25
        )
        self.bulk_cat_combo.pack(side="left", fill="x", expand=True)

        # Bulk Outfit Name
        name_frame = ttk.Frame(bulk)
        name_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=4, pady=2)
        ttk.Label(name_frame, text="Outfit:", width=9).pack(side="left")

        self.bulk_outfit_var = tk.StringVar()
        self.bulk_outfit_combo = SearchableCombobox(
            name_frame,
            values=[],
            textvariable=self.bulk_outfit_var,
            on_select=lambda val: self._update_bulk_preview(),
            placeholder="Select outfit...",
            width=25
        )
        self.bulk_outfit_combo.pack(side="left", fill="x", expand=True)

        # Lock checkbox: when checked, keep the selected outfit after applying
        self.bulk_lock_var = tk.BooleanVar(value=False)
        self.bulk_lock_chk = ttk.Checkbutton(
            bulk, text="Lock", variable=self.bulk_lock_var, width=5
        )
        # Actually grid layout above used columnspan=3. Let's put lock check in the name frame or separate row?
        # Simpler: put lock check in name_frame
        self.bulk_lock_chk.pack(in_=name_frame, side="left", padx=(6, 0))
        create_tooltip(self.bulk_lock_chk, "Keep the selected outfit after applying")

        # Bulk Team Colors
        scheme_row = ttk.Frame(bulk)
        scheme_row.grid(row=3, column=0, columnspan=3, sticky="ew", padx=4, pady=2)
        
        ttk.Label(scheme_row, text="Team Colors:", width=11).pack(side="left")
        self.bulk_scheme_var = tk.StringVar()
        
        # Get color schemes
        schemes = sorted(list(self.data_loader.load_color_schemes().keys()))
        
        self.bulk_scheme_combo = SearchableCombobox(
            scheme_row,
            values=schemes,
            textvariable=self.bulk_scheme_var,
            on_select=lambda val: self._update_bulk_preview(),
            placeholder="Select team colors...",
            width=25
        )
        self.bulk_scheme_combo.pack(side="left", fill="x", expand=True)

        # Lock checkbox for schemes
        self.bulk_scheme_lock_var = tk.BooleanVar(value=False)
        self.bulk_scheme_lock_chk = ttk.Checkbutton(
            bulk, text="Lock", variable=self.bulk_scheme_lock_var, width=5
        )
        self.bulk_scheme_lock_chk.pack(in_=scheme_row, side="left", padx=(6, 0))
        create_tooltip(self.bulk_scheme_lock_chk, "Keep the selected colors after applying")

        # Preview/status label
        self.bulk_preview_var = tk.StringVar(value="")
        self.bulk_preview_label = ttk.Label(
            bulk, textvariable=self.bulk_preview_var, style="Muted.TLabel"
        )
        self.bulk_preview_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 6))

        # Button row
        btn_frame = ttk.Frame(bulk)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=4, pady=6)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        ttk.Button(btn_frame, text="✓ Apply to All", command=self._apply_bulk_to_all).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(
            btn_frame, text="✓ Apply to Selected", command=self._apply_bulk_to_selected
        ).grid(row=0, column=1, sticky="ew", padx=2)
        ttk.Button(
            btn_frame, text="✨ Create Shared Outfit", command=self._create_shared_outfit
        ).grid(row=0, column=2, sticky="ew", padx=(4, 0))

        # Add character section
        add = ttk.LabelFrame(self.tab, text="👥 Add Character", style="TLabelframe")
        add.grid(row=2, column=0, sticky="ew", padx=6, pady=SECTION_PAD_Y)
        add.columnconfigure(0, weight=1)
        char_help = ttk.Label(
            add, text="Select a character and press Add or Enter", style="Muted.TLabel"
        )
        char_help.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 4))
        create_tooltip(char_help, TOOLTIPS.get("character", ""))

        self.char_var = tk.StringVar()
        self.char_combo = SearchableCombobox(
            add,
            values=sorted(list(self.characters.keys())),
            on_select=lambda val: None, # Don't add on simple select
            on_double_click=lambda val: self._add_character(),
            placeholder="Search character...",
            textvariable=self.char_var
        )
        self.char_combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 6), padx=4)
        create_tooltip(self.char_combo, TOOLTIPS.get("character", ""))

        button_frame = ttk.Frame(add)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 6))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(button_frame, text="+ Add to Prompt", command=self._add_character).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(
            button_frame, text="✨ Create New Character", command=self._create_new_character
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # Use ScrollableCanvas for selected characters
        self.scrollable_canvas = ScrollableCanvas(self.tab)
        self.scrollable_canvas.grid(row=3, column=0, sticky="nsew", padx=6, pady=SECTION_PAD_Y)

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
        except tk.TclError:
            # Canvas destroyed - expected during cleanup
            from utils import logger

            logger.debug("Canvas update skipped: widget destroyed")
        except AttributeError as e:
            # Canvas attribute missing - shouldn't happen
            from utils import logger

            logger.warning(f"Canvas attribute error: {e}")

    def _update_bulk_preview(self):
        """Update preview text showing which characters will be affected."""
        outfit_name = self.bulk_outfit_var.get()
        scheme_name = self.bulk_scheme_var.get()

        if not outfit_name and not scheme_name:
            self.bulk_preview_var.set("")
            return
            
        changes = []
        if outfit_name: changes.append("outfit")
        if scheme_name: changes.append("colors")
        change_text = " & ".join(changes)

        if not self.selected_characters:
            self.bulk_preview_var.set(f"Select characters to apply {change_text}")
            return

        count = len(self.selected_characters)
        if count == 1:
            self.bulk_preview_var.set(f"✓ Apply {change_text} to: {self.selected_characters[0]['name']}")
        else:
            self.bulk_preview_var.set(f"✓ Apply {change_text} to {count} characters")

    def _apply_bulk_to_all(self):
        """Apply selected outfit and/or color scheme to all selected characters."""
        outfit_name = self.bulk_outfit_var.get()
        scheme_name = self.bulk_scheme_var.get()

        if not outfit_name and not scheme_name:
            messagebox.showwarning("Selection Required", "Please select an outfit or color scheme to apply")
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
            if outfit_name:
                char["outfit"] = outfit_name
            if scheme_name:
                char["color_scheme"] = scheme_name

        self._refresh_list()
        self.on_change()
        
        # Clear selections only if not locked
        if outfit_name and (not getattr(self, "bulk_lock_var", None) or not self.bulk_lock_var.get()):
            self.bulk_outfit_var.set("")
        if scheme_name and (not getattr(self, "bulk_scheme_lock_var", None) or not self.bulk_scheme_lock_var.get()):
            self.bulk_scheme_var.set("")

        # Show status feedback
        root = self.tab.winfo_toplevel()
        changes = []
        if outfit_name: changes.append(f"outfit '{outfit_name}'")
        if scheme_name: changes.append(f"colors '{scheme_name}'")
        msg = f"Applied {', '.join(changes)} to all {count} character(s)"
        
        if hasattr(root, "_update_status"):
            root._update_status(msg)
        else:
            try:
                messagebox.showinfo("Applied Bulk Changes", msg)
            except Exception:
                pass

    def _apply_bulk_to_selected(self):
        """Apply selected outfit/colors to a specific selected character via dialog."""
        outfit_name = self.bulk_outfit_var.get()
        scheme_name = self.bulk_scheme_var.get()

        if not outfit_name and not scheme_name:
            messagebox.showwarning("Selection Required", "Please select an outfit or color scheme to apply")
            return

        if not self.selected_characters:
            messagebox.showwarning("No Characters", "No characters are currently selected")
            return

        # If only one character, apply directly
        if len(self.selected_characters) == 1:
            if self.save_for_undo:
                self.save_for_undo()

            char = self.selected_characters[0]
            if outfit_name: char["outfit"] = outfit_name
            if scheme_name: char["color_scheme"] = scheme_name
            
            self._refresh_list()
            self.on_change()
            
            if outfit_name and (not getattr(self, "bulk_lock_var", None) or not self.bulk_lock_var.get()):
                self.bulk_outfit_var.set("")
            if scheme_name and (not getattr(self, "bulk_scheme_lock_var", None) or not self.bulk_scheme_lock_var.get()):
                self.bulk_scheme_var.set("")

            root = self.tab.winfo_toplevel()
            if hasattr(root, "_update_status"):
                root._update_status(f"Applied changes to {char['name']}")
            return

        # Multiple characters - show selection dialog
        dialog = tk.Toplevel(self.tab)
        dialog.title("Select Character")
        dialog.transient(self.tab.winfo_toplevel())
        dialog.grab_set()
        dialog.geometry("300x250")

        msg = "Apply "
        if outfit_name: msg += f"outfit '{outfit_name}' "
        if scheme_name: msg += f"colors '{scheme_name}' "
        msg += "to:"
        
        ttk.Label(dialog, text=msg, style="Bold.TLabel", wraplength=280).pack(pady=(10, 5))

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

        char_listbox.selection_set(0)

        def on_ok():
            selection = char_listbox.curselection()
            if selection:
                char = self.selected_characters[selection[0]]
                if self.save_for_undo:
                    self.save_for_undo()
                
                if outfit_name: char["outfit"] = outfit_name
                if scheme_name: char["color_scheme"] = scheme_name
                
                self._refresh_list()
                self.on_change()
                
                if outfit_name and (not getattr(self, "bulk_lock_var", None) or not self.bulk_lock_var.get()):
                    self.bulk_outfit_var.set("")
                if scheme_name and (not getattr(self, "bulk_scheme_lock_var", None) or not self.bulk_scheme_lock_var.get()):
                    self.bulk_scheme_var.set("")
                    
                dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Apply", command=on_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)

        char_listbox.bind("<Double-Button-1>", lambda e: on_ok())
        dialog.wait_window()

    def _filter_characters(self):
        """Filter character dropdown based on search text."""
        search = self.char_search_var.get().lower()

        # Get currently used characters
        used = {c["name"] for c in self.selected_characters}
        available = [k for k in self.characters.keys() if k not in used]

        if search:
            # Filter by search term
            filtered = [c for c in available if search in c.lower()]
            self.char_combo.set_values(sorted(filtered))
        else:
            # Show all available
            self.char_combo.set_values(sorted(available))

        # Clear selection if current selection not in filtered list
        if self.char_var.get() not in self.char_combo.all_values:
            self.char_var.set("")

    def _add_character(self):
        """Add selected character to the list."""
        name = self.char_var.get()
        if not name:
            return
        # If the parsed character data indicates modifier wasn't explicit, or the raw
        # character file lacks a Modifier/Gender tag, prompt the user to add it.
        try:
            need_prompt = False

            char_def = self.characters.get(name, {})
            # If no modifier and no explicit gender, we need more info
            if not char_def or (not char_def.get("modifier") and not char_def.get("gender_explicit")):
                need_prompt = True

            if need_prompt:
                # Ask user for a quick inline modifier choice or open editor
                choice = self._prompt_modifier_choice(name)
                if choice and choice != "editor":
                    # Try to write modifier tag directly into the character file
                    try:
                        fp = self._find_character_file(name)
                        if fp:
                            import shutil

                            bak = fp.with_suffix(fp.suffix + ".bak")
                            if bak.exists():
                                idx = 1
                                while True:
                                    candidate = fp.with_suffix(fp.suffix + f".bak{idx}")
                                    if not candidate.exists():
                                        bak = candidate
                                        break
                                    idx += 1
                            shutil.copy(fp, bak)

                            text = fp.read_text(encoding="utf-8")
                            # Insert Modifier tag after header or photo line
                            lines = text.splitlines()
                            insert_idx = None
                            for i, line in enumerate(lines[:20]):
                                if line.strip().lower().startswith("**photo:"):
                                    insert_idx = i + 1
                                    break
                            if insert_idx is None:
                                for i, line in enumerate(lines[:6]):
                                    if line.strip().startswith("### "):
                                        insert_idx = i + 1
                                        break
                            if insert_idx is None:
                                insert_idx = 0

                            # Replace Gender with Modifier if it exists, otherwise insert Modifier
                            new_lines = []
                            replaced = False
                            for line in lines:
                                if line.strip().startswith("**Gender:**"):
                                    new_lines.append(f"**Modifier:** {choice}")
                                    replaced = True
                                else:
                                    new_lines.append(line)
                            
                            if not replaced:
                                new_lines = (
                                    lines[:insert_idx]
                                    + ["", f"**Modifier:** {choice}"]
                                    + lines[insert_idx:]
                                )
                                
                            fp.write_text("\n".join(new_lines), encoding="utf-8")
                            # Reload characters and continue
                            if self.reload_data:
                                self.reload_data()
                            self.characters = self.data_loader.load_characters()
                        else:
                            # No file found; open editor as fallback
                            root = self.tab.winfo_toplevel()
                            dialog = CharacterCreatorDialog(
                                root, self.data_loader, self.reload_data, edit_character=name
                            )
                            dialog.show()
                            if self.reload_data:
                                self.reload_data()
                            self.characters = self.data_loader.load_characters()
                    except Exception:
                        # If writing fails, open editor as fallback
                        root = self.tab.winfo_toplevel()
                        dialog = CharacterCreatorDialog(
                            root, self.data_loader, self.reload_data, edit_character=name
                        )
                        dialog.show()
                        if self.reload_data:
                            self.reload_data()
                        self.characters = self.data_loader.load_characters()

                    # Abort if still missing
                    char_def = self.characters.get(name, {})
                    if not char_def.get("modifier") and not char_def.get("gender_explicit"):
                        return
                elif choice == "editor":
                    root = self.tab.winfo_toplevel()
                    dialog = CharacterCreatorDialog(
                        root, self.data_loader, self.reload_data, edit_character=name
                    )
                    dialog.show()
                    if self.reload_data:
                        self.reload_data()
                    self.characters = self.data_loader.load_characters()
                    char_def = self.characters.get(name, {})
                    if not char_def.get("modifier") and not char_def.get("gender_explicit"):
                        return
                else:
                    return
        except Exception:
            # Non-fatal; continue with existing behavior
            pass
        if any(c["name"] == name for c in self.selected_characters):
            from utils.notification import notify

            root = self.tab.winfo_toplevel()
            msg = f"{name} is already in the prompt"
            notify(root, "Already Added", msg, level="info", duration=2500)
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

        self.selected_characters.append(
            {
                "name": name,
                "outfit": outfit,
                "pose_category": "",
                "pose_preset": "",
                "action_note": "",
            }
        )
        self.char_var.set("")
        self._refresh_list()
        # Auto-scroll to the newly added character
        self.chars_canvas.yview_moveto(1.0)

    def _create_new_character(self):
        """Open dialog to create a new character."""
        # Get the root window to use as parent
        root = self.tab.winfo_toplevel()
        dialog = CharacterCreatorDialog(root, self.data_loader, self.reload_data)
        dialog.show()

        # If character was created and reload callback exists, it will be called automatically

    def _create_new_style(self):
        """Open dialog to create a new base art style."""
        root = self.tab.winfo_toplevel()
        dialog = BaseStyleCreatorDialog(root, self.data_loader, self.reload_data)
        dialog.show()

    def _create_shared_outfit(self):
        """Open dialog to create a new shared outfit."""
        root = self.tab.winfo_toplevel()
        dialog = SharedOutfitCreatorDialog(root, self.data_loader, self.reload_data)
        dialog.show()

    def _create_character_outfit(self, character_name):
        """Open dialog to create a new character-specific outfit."""
        root = self.tab.winfo_toplevel()
        dialog = CharacterOutfitCreatorDialog(
            root, self.data_loader, character_name, self.reload_data
        )
        dialog.show()

    def _create_new_pose(self):
        """Open dialog to create a new pose preset."""
        root = self.tab.winfo_toplevel()
        dialog = PoseCreatorDialog(root, self.data_loader, self.reload_data)
        dialog.show()

    def _remove_character(self, idx):
        """Remove character at index."""
        # Add confirmation for destructive action
        char_name = self.selected_characters[idx].get("name", "this character")
        if not messagebox.askyesno(
            "Remove Character", f"Remove {char_name} from the prompt?", icon="question"
        ):
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
            except (tk.TclError, ValueError) as e:
                # Widget destroyed or invalid ID; log for diagnostics
                from utils import logger

                logger.debug(f"Could not cancel scheduled action note update for idx {idx}: {e}")

        # Schedule new update after debounce delay
        def _do_update():
            text = text_widget.get("1.0", "end").strip()
            self.selected_characters[idx]["action_note"] = text
            self.on_change()
            if idx in self._action_note_after_ids:
                del self._action_note_after_ids[idx]

        self._action_note_after_ids[idx] = self.tab.after(TEXT_UPDATE_DEBOUNCE_MS, _do_update)

    def _update_pose_category(self, idx, category_val, preset_combo):
        """Update character pose category."""
        cat = category_val
        self.selected_characters[idx]["pose_category"] = cat
        self.selected_characters[idx]["pose_preset"] = ""

        if cat and cat in self.poses:
            preset_combo.set_values([""] + sorted(list(self.poses[cat].keys())))
        else:
            preset_combo.set_values([""])
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
        self.char_combo.set_values(available)

        # Show empty state if no characters
        if not self.selected_characters:
            empty_frame = ttk.Frame(self.chars_container, style="TFrame")
            empty_frame.pack(fill="both", expand=True, padx=4, pady=20)
            empty_label = ttk.Label(
                empty_frame,
                text="👈 Add characters to get started",
                foreground="gray",
                font=("Consolas", 11),
            )
            empty_label.pack()
            # Manually update scroll region
            try:
                self.chars_canvas.config(scrollregion=self.chars_canvas.bbox("all"))
            except Exception as e:
                from utils import logger

                logger.debug(f"Failed to update chars canvas scrollregion: {e}")
            self._refreshing = False
            return

        # Load color schemes from file
        color_schemes = self.data_loader.load_color_schemes()

        # Define callbacks for CharacterItem
        callbacks = {
            "update_outfit": self._update_outfit,
            "create_outfit": self._create_character_outfit,
            "update_pose_preset": self._update_pose_preset,
            "update_pose_category": self._update_pose_category,
            "create_pose": self._create_new_pose,
            "update_action_note": self._update_action_note,
            "update_color_scheme": self._update_color_scheme,
            "move_up": self._move_up,
            "move_down": self._move_down,
            "remove_character": self._remove_character,
            "get_num_characters": lambda: len(self.selected_characters),
            "get_modifiers": lambda: getattr(self.parent.winfo_toplevel(), "modifiers", {}),
            "update_scroll": self.scrollable_canvas.update_scroll_region,
            "on_change": self.on_change
        }

        for i, cd in enumerate(self.selected_characters):
            item = CharacterItem(
                self.chars_container,
                index=i,
                char_data=cd,
                all_characters=self.characters,
                all_poses=self.poses,
                color_schemes=color_schemes,
                callbacks=callbacks
            )
            item.pack(fill="x", pady=(0, 8), padx=4)

            # Bind drag and drop events to handle
            if hasattr(item, "drag_handle"):
                item.drag_handle.bind("<Button-1>", lambda e, i=i, w=item: self._on_drag_start(e, i, w))
                item.drag_handle.bind("<B1-Motion>", self._on_drag_motion)
                item.drag_handle.bind("<ButtonRelease-1>", self._on_drag_stop)

            # Add context menu to item
            self._add_context_menu(item, i)

        # Update scroll region and refresh mousewheel bindings
        self.scrollable_canvas.refresh_mousewheel_bindings()
        self.scrollable_canvas.update_scroll_region()

        # Defer on_change to avoid event queue overflow
        self.tab.after(1, self.on_change)
        self._refreshing = False

    def _update_color_scheme(self, index, scheme_name):
        """Update color scheme for a character.

        Args:
            index: Character index
            scheme_name: Name of color scheme
        """
        if 0 <= index < len(self.selected_characters):
            self.selected_characters[index]["color_scheme"] = scheme_name
            self.on_change()

    def _on_drag_start(self, event, index, widget):
        """Handle start of drag-and-drop reordering."""
        self._drag_data["index"] = index
        self._drag_data["widget"] = widget
        # Change cursor to indicate dragging
        self.parent.winfo_toplevel().config(cursor="fleur")
        widget.configure(relief="groove")

    def _on_drag_motion(self, event):
        """Handle mouse movement during drag."""
        if self._drag_data["widget"] is None:
            return
            
        # Optional: Show visual indicator of drop target
        pass

    def _on_drag_stop(self, event):
        """Handle end of drag-and-drop reordering."""
        if self._drag_data["index"] is None:
            return

        # Reset cursor
        self.parent.winfo_toplevel().config(cursor="")
        if self._drag_data["widget"]:
            self._drag_data["widget"].configure(relief="solid")

        # Find drop index based on mouse Y position
        # Get Y relative to container
        canvas_y = self.chars_canvas.canvasy(event.y_root - self.chars_canvas.winfo_rooty())
        drop_idx = self._find_drop_index(canvas_y)

        if drop_idx is not None and drop_idx != self._drag_data["index"]:
            # Move item in list
            item = self.selected_characters.pop(self._drag_data["index"])
            
            # Adjust drop_idx if it was after the original position
            if drop_idx > self._drag_data["index"]:
                drop_idx -= 1
                
            self.selected_characters.insert(drop_idx, item)
            
            # Save for undo and refresh
            if self.save_for_undo:
                self.save_for_undo()
            self._refresh_list()
            self.on_change()

        # Clear drag data
        self._drag_data = {"index": None, "widget": None}

    def _find_drop_index(self, y):
        """Find character index at given Y coordinate."""
        for i, child in enumerate(self.chars_container.winfo_children()):
            # Get widget position
            wy = child.winfo_y()
            wh = child.winfo_height()
            
            # If mouse is in upper half of widget, drop before it
            if y < wy + (wh / 2):
                return i
        
        # If below all items, drop at end
        return len(self.selected_characters)

        # Update scroll region and refresh mousewheel bindings
        self.scrollable_canvas.refresh_mousewheel_bindings()
        self.scrollable_canvas.update_scroll_region()

        # Defer on_change to avoid event queue overflow
        self.tab.after(1, self.on_change)
        self._refreshing = False

    def _find_character_file(self, character_name):
        """Locate the markdown file for a character by scanning the characters dir.

        Returns Path or None.
        """
        chars_dir = self.data_loader._find_characters_dir()
        try:
            for p in sorted(chars_dir.glob("*.md")):
                try:
                    text = p.read_text(encoding="utf-8")
                except Exception:
                    continue
                # Look for header '### Name' within the first part of the file
                lines = text.splitlines()
                for ln in lines[:8]:
                    if ln.strip().startswith("### ") and ln.strip()[4:].strip() == character_name:
                        return p
                # Fallback: substring search
                if f"### {character_name}" in text:
                    return p
        except Exception:
            return None
        return None

    def _prompt_modifier_choice(self, character_name):
        """Show a modal dialog to pick an outfit modifier (e.g. F, M, H).

        Returns the modifier string (e.g. 'F', 'M', 'H'), 'editor', or None.
        """
        root = self.tab.winfo_toplevel()
        dlg = tk.Toplevel(root)
        dlg.transient(root)
        dlg.grab_set()
        dlg.title(f"Add Modifier for {character_name}")
        
        ttk.Label(
            dlg, 
            text=f"Select an outfit modifier for '{character_name}':",
            font=("Segoe UI", 9, "bold")
        ).pack(padx=12, pady=(12, 6))
        
        ttk.Label(
            dlg, 
            text="This determines which shared outfit library (outfits_*.md) is used.",
            style="Muted.TLabel",
            wraplength=350
        ).pack(padx=12, pady=(0, 10))

        # Scan for available modifiers
        data_dir = self.data_loader.base_dir / "data"
        modifiers = []
        for f in data_dir.glob("outfits_*.md"):
            suffix = f.stem.split("_", 1)[1].upper()
            modifiers.append(suffix)
        
        if not modifiers:
            modifiers = ["F", "M"]
        else:
            modifiers.sort()

        choice_var = tk.StringVar(value="F" if "F" in modifiers else modifiers[0])
        
        frame = ttk.Frame(dlg)
        frame.pack(padx=12, pady=6, fill="x")
        
        for mod in modifiers:
            label = mod
            if mod == "F": label = "F (Female)"
            elif mod == "M": label = "M (Male)"
            elif mod == "H": label = "H (Hijabi)"
            
            ttk.Radiobutton(frame, text=label, variable=choice_var, value=mod).pack(anchor="w", pady=2)

        btns = ttk.Frame(dlg)
        btns.pack(padx=12, pady=(10, 12))

        result = {"val": None}

        def _ok():
            result["val"] = choice_var.get()
            dlg.destroy()

        def _editor():
            result["val"] = "editor"
            dlg.destroy()

        def _cancel():
            result["val"] = None
            dlg.destroy()

        ttk.Button(btns, text="OK", command=_ok).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Open Editor", command=_editor).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Cancel", command=_cancel).pack(side="left")

        # Center
        dlg.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() // 2) - (dlg.winfo_width() // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (dlg.winfo_height() // 2)
        dlg.geometry(f"+{x}+{y}")

        dlg.wait_window()

        return result["val"]

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
        if prompt_name in self.base_combo.all_values:
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

        menu.add_command(
            label="Duplicate Character", command=lambda: self._duplicate_character(char_index)
        )
        menu.add_separator()

        if char_index > 0:
            menu.add_command(label="Move Up", command=lambda: self._move_up(char_index))
        if char_index < len(self.selected_characters) - 1:
            menu.add_command(label="Move Down", command=lambda: self._move_down(char_index))

        menu.add_separator()
        menu.add_command(
            label="Copy Character Data", command=lambda: self._copy_character_data(char_index)
        )
        menu.add_separator()
        menu.add_command(
            label="Remove Character", command=lambda: self._remove_character(char_index)
        )

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

        char = copy.deepcopy(
            self.selected_characters[idx]
        )  # Use deep copy to avoid shared references
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
        if char.get("outfit"):
            data += f" - {char['outfit']}"
        if char.get("pose_preset"):
            data += f" - Pose: {char['pose_preset']}"
        if char.get("action_note"):
            data += f" - Action: {char['action_note']}"

        self.tab.clipboard_clear()
        self.tab.clipboard_append(data)

        # Show brief feedback
        root = self.tab.winfo_toplevel()
        if hasattr(root, "_update_status"):
            root._update_status("Character data copied to clipboard")

    def add_character_from_gallery(self, character_name):
        """Add a character from the gallery to selected characters.

        Args:
            character_name: Name of the character to add
        """
        # If the parsed character data indicates modifier wasn't explicit, prompt
        # the user before adding.
        try:
            char_def = self.characters.get(character_name, {})
            if not char_def or (not char_def.get("modifier") and not char_def.get("gender_explicit")):
                choice = self._prompt_modifier_choice(character_name)
                if choice and choice != "editor":
                    try:
                        fp = self._find_character_file(character_name)
                        if fp:
                            import shutil

                            bak = fp.with_suffix(fp.suffix + ".bak")
                            if bak.exists():
                                idx = 1
                                while True:
                                    candidate = fp.with_suffix(fp.suffix + f".bak{idx}")
                                    if not candidate.exists():
                                        bak = candidate
                                        break
                                    idx += 1
                            shutil.copy(fp, bak)
                            text = fp.read_text(encoding="utf-8")
                            lines = text.splitlines()
                            insert_idx = None
                            for i, line in enumerate(lines[:20]):
                                if line.strip().lower().startswith("**photo:"):
                                    insert_idx = i + 1
                                    break
                            if insert_idx is None:
                                for i, line in enumerate(lines[:6]):
                                    if line.strip().startswith("### "):
                                        insert_idx = i + 1
                                        break
                            if insert_idx is None:
                                insert_idx = 0
                            
                            new_lines = []
                            replaced = False
                            for line in lines:
                                if line.strip().startswith("**Gender:**"):
                                    new_lines.append(f"**Modifier:** {choice}")
                                    replaced = True
                                else:
                                    new_lines.append(line)
                            
                            if not replaced:
                                new_lines = (
                                    lines[:insert_idx]
                                    + ["", f"**Modifier:** {choice}"]
                                    + lines[insert_idx:]
                                )
                                
                            fp.write_text("\n".join(new_lines), encoding="utf-8")
                            if self.reload_data:
                                self.reload_data()
                            self.characters = self.data_loader.load_characters()
                        else:
                            # fallback to open editor
                            root = self.tab.winfo_toplevel()
                            dialog = CharacterCreatorDialog(
                                root,
                                self.data_loader,
                                self.reload_data,
                                edit_character=character_name,
                            )
                            dialog.show()
                            if self.reload_data:
                                self.reload_data()
                            self.characters = self.data_loader.load_characters()
                    except Exception:
                        root = self.tab.winfo_toplevel()
                        dialog = CharacterCreatorDialog(
                            root, self.data_loader, self.reload_data, edit_character=character_name
                        )
                        dialog.show()
                        if self.reload_data:
                            self.reload_data()
                        self.characters = self.data_loader.load_characters()
                    
                    char_def = self.characters.get(character_name, {})
                    if not char_def.get("modifier") and not char_def.get("gender_explicit"):
                        return
                elif choice == "editor":
                    root = self.tab.winfo_toplevel()
                    dialog = CharacterCreatorDialog(
                        root, self.data_loader, self.reload_data, edit_character=character_name
                    )
                    dialog.show()
                    if self.reload_data:
                        self.reload_data()
                    self.characters = self.data_loader.load_characters()
                    char_def = self.characters.get(character_name, {})
                    if not char_def.get("modifier") and not char_def.get("gender_explicit"):
                        return
                else:
                    return
        except Exception:
            pass

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

        self.selected_characters.append(
            {
                "name": character_name,
                "outfit": outfit,
                "pose_category": "",
                "pose_preset": "",
                "action_note": "",
            }
        )
        self._refresh_list()
        # Auto-scroll to the newly added character
        self.chars_canvas.yview_moveto(1.0)
        self.on_change()
