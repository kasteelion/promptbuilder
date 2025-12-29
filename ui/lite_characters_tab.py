# -*- coding: utf-8 -*-
"""Lite version of CharactersTab with integrated tagging."""

import tkinter as tk
from tkinter import messagebox, ttk

from config import TOOLTIPS
from utils import create_tooltip, logger
from .characters_tab import CharactersTab
from .character_item import CharacterItem
from .searchable_combobox import SearchableCombobox
from .widgets import CollapsibleFrame, FlowFrame, ScrollableCanvas

class LiteCharactersTab(CharactersTab):
    """Lite version of CharactersTab with integrated tagging/filtering."""

    def __init__(self, parent, data_loader, theme_manager, character_controller, on_change_callback, reload_callback=None, undo_callback=None):
        # Initialize tagging state before parent init
        self.selected_tags = []
        self.categorized_tags_map = {}
        
        super().__init__(parent, data_loader, theme_manager, character_controller, on_change_callback, reload_callback, undo_callback)

    def load_data(self, characters, base_prompts, poses, scenes=None):
        """Load data and also tagging data."""
        super().load_data(characters, base_prompts, poses, scenes)
        
        # Load tagging data
        try:
            self.categorized_tags_map = self.data_loader.load_categorized_tags()
        except Exception:
            self.categorized_tags_map = {}
            
        # Initialize tag UI if it exists
        if hasattr(self, "tag_cat_combo"):
            self._update_tag_categories()
            self._update_tag_list()
        
        # Initial filter to populate list
        self._filter_characters()

    def _update_tag_categories(self):
        categories = ["All"] + sorted(list(self.categorized_tags_map.keys()))
        self.tag_cat_combo.set_values(categories)

    def _build_ui(self):
        """Build the characters tab UI with added tagging support."""
        # Mostly copied from CharactersTab._build_ui but modified
        self.tab.columnconfigure(0, weight=1)
        self.tab.rowconfigure(3, weight=1)

        SECTION_PAD_Y = (10, 15)

        # 1. Base Prompt (Same as original)
        bp = ttk.LabelFrame(self.tab, text="📋 BASE PROMPT (STYLE)", style="TLabelframe", padding=12)
        bp.grid(row=0, column=0, sticky="ew", padx=10, pady=SECTION_PAD_Y)
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

        # 2. Bulk Outfit Editor (Same as original)
        self.bulk_container = CollapsibleFrame(self.tab, text="⚡ BULK OUTFIT EDITOR")
        self.bulk_container.grid(row=1, column=0, sticky="ew", padx=10, pady=SECTION_PAD_Y)
        self.bulk_container.set_opened(False)

        bulk = self.bulk_container.get_content_frame()
        bulk.columnconfigure(1, weight=1)

        # Info section
        info_frame = ttk.Frame(bulk)
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 10))
        info_frame.columnconfigure(0, weight=1)

        info_text = ttk.Label(info_frame, text="💡 Apply the same outfit to multiple characters at once", style="Accent.TLabel")
        info_text.pack(anchor="w", padx=6, pady=4)

        # Bulk Category
        cat_frame = ttk.Frame(bulk)
        cat_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
        ttk.Label(cat_frame, text="Category:", width=10).pack(side="left")
        
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
        name_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
        ttk.Label(name_frame, text="Outfit:", width=10).pack(side="left")

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

        # Helper for Pill Toggle (copied from original)
        def add_pill_toggle(parent, text, variable, command=None, tooltip=None):
            # Get current theme colors
            theme = self.tab.winfo_toplevel().theme_manager.themes.get(
                self.tab.winfo_toplevel().theme_manager.current_theme, {}
            )
            pbg = theme.get("panel_bg", "#1e1e1e")
            accent = theme.get("accent", "#0078d7")
                
            frame = tk.Frame(parent, bg=accent, padx=1, pady=1)
            initial_text = f"✓ {text}" if variable.get() else text
            lbl = tk.Label(frame, text=initial_text, bg=pbg, fg=accent, font=("Lexend", 8, "bold"), padx=8, pady=2, cursor="hand2")
            lbl.pack()
            lbl._base_bg = pbg
            
            def toggle(e):
                new_val = not variable.get()
                variable.set(new_val)
                lbl.config(text=f"✓ {text}" if new_val else text)
                if command: command()
                
            def on_e(e, l=lbl):
                try:
                    tm = self.tab.winfo_toplevel().theme_manager
                    curr_theme = tm.themes.get(tm.current_theme, {})
                    hbg = curr_theme.get("hover_bg", "#333333")
                except: hbg = "#333333"
                l.config(bg=hbg)
            def on_l(e, l=lbl):
                l.config(bg=getattr(l, "_base_bg", "#1e1e1e"))
                
            lbl.bind("<Button-1>", toggle)
            lbl.bind("<Enter>", on_e)
            lbl.bind("<Leave>", on_l)
            
            if tooltip: create_tooltip(lbl, tooltip)
            if not hasattr(self, "pill_buttons_info"): self.pill_buttons_info = []
            self.pill_buttons_info.append((frame, lbl, text, variable))
            return frame

        self.bulk_lock_var = tk.BooleanVar(value=False)
        self.bulk_lock_pill = add_pill_toggle(name_frame, "LOCK", self.bulk_lock_var, tooltip="Keep selection")
        self.bulk_lock_pill.pack(side="left", padx=(6, 0))

        # Bulk Team Colors
        scheme_row = ttk.Frame(bulk)
        scheme_row.grid(row=3, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
        ttk.Label(scheme_row, text="Team Colors:", width=12).pack(side="left")
        self.bulk_scheme_var = tk.StringVar()
        
        # We need schemes loaded here if not already done in load_data (CharactersTab usually does it later)
        # But for UI build, we just set empty for now, loaded later.
        
        self.bulk_scheme_combo = SearchableCombobox(
            scheme_row,
            values=[],
            textvariable=self.bulk_scheme_var,
            on_select=lambda val: self._update_bulk_preview(),
            placeholder="Select team colors...",
            width=25
        )
        self.bulk_scheme_combo.pack(side="left", fill="x", expand=True)

        self.bulk_scheme_lock_var = tk.BooleanVar(value=False)
        self.bulk_scheme_lock_pill = add_pill_toggle(scheme_row, "LOCK", self.bulk_scheme_lock_var, tooltip="Keep selection")
        self.bulk_scheme_lock_pill.pack(side="left", padx=(6, 0))

        self.bulk_sig_color_var = tk.BooleanVar(value=False)
        self.bulk_sig_pill = add_pill_toggle(bulk, "USE SIGNATURE COLORS", self.bulk_sig_color_var, command=lambda: self._update_bulk_preview())
        self.bulk_sig_pill.grid(row=4, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 8))

        self.bulk_preview_var = tk.StringVar(value="")
        self.bulk_preview_label = ttk.Label(bulk, textvariable=self.bulk_preview_var, style="Muted.TLabel")
        self.bulk_preview_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 10))

        btn_frame = ttk.Frame(bulk)
        btn_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=4, pady=10)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        ttk.Button(btn_frame, text="✓ Apply to All", command=self._apply_bulk_to_all).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(btn_frame, text="✓ Apply to Selected", command=self._apply_bulk_to_selected).grid(row=0, column=1, sticky="ew", padx=2)
        
        self.create_shared_btn = tk.Button(
            btn_frame, 
            text="✨ Create Shared Outfit", 
            command=self._create_shared_outfit, 
            bg=pbg,
            fg=accent,
            highlightbackground=accent,
            highlightthickness=2,
            relief="flat", 
            font=("Lexend", 9)
        )
        self.create_shared_btn.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        self.create_shared_btn._base_bg = pbg
        
        self.create_shared_btn.bind("<Enter>", lambda e: self.create_shared_btn.config(bg=theme.get("hover_bg", "#333333")))
        self.create_shared_btn.bind("<Leave>", lambda e: self.create_shared_btn.config(bg=getattr(self.create_shared_btn, "_base_bg", "#1e1e1e")))


        # 3. Add Character (MODIFIED with Tagging)
        add = ttk.LabelFrame(self.tab, text="👥 ADD CHARACTER", style="TLabelframe", padding=12)
        add.grid(row=2, column=0, sticky="ew", padx=10, pady=SECTION_PAD_Y)
        add.columnconfigure(0, weight=1)
        add.columnconfigure(1, weight=1) # Extra column for flexibility

        # --- TAGGING UI START ---
        
        # Tag filter section
        tag_frame = ttk.Frame(add, style="TFrame")
        tag_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 10))
        tag_frame.columnconfigure(1, weight=1)
        tag_frame.columnconfigure(3, weight=1)

        ttk.Label(tag_frame, text="Cat:", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.tag_category_var = tk.StringVar(value="All")
        self.tag_cat_combo = SearchableCombobox(
            tag_frame,
            theme_manager=self.theme_manager, # Pass theme manager
            textvariable=self.tag_category_var,
            on_select=lambda val: self._update_tag_list(),
            placeholder="Category...",
            width=10
        )
        self.tag_cat_combo.grid(row=0, column=1, sticky="ew", padx=(2, 4))

        ttk.Label(tag_frame, text="Tag:", style="Muted.TLabel").grid(row=0, column=2, sticky="w")
        self.tag_var = tk.StringVar()
        self.tag_combo = SearchableCombobox(
            tag_frame,
            theme_manager=self.theme_manager, # Pass theme manager
            textvariable=self.tag_var,
            on_select=self._add_selected_tag,
            placeholder="Filter by tag...",
            width=12
        )
        self.tag_combo.grid(row=0, column=3, sticky="ew", padx=(2, 4))

        self.clear_tags_btn = ttk.Button(tag_frame, text="✕", width=3, command=self._clear_tag_filter)
        self.clear_tags_btn.grid(row=0, column=4)
        create_tooltip(self.clear_tags_btn, "Clear tag filters")
        
        # Selected tags area (chips)
        self.selected_tags_frame = FlowFrame(add, padding_x=8, padding_y=6)
        self.selected_tags_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 10))
        self._render_selected_tags()
        
        # --- TAGGING UI END ---

        self.char_var = tk.StringVar()
        self.char_combo = SearchableCombobox(
            add,
            values=[], # populated later
            on_select=lambda val: None,
            on_double_click=lambda val: self._add_character(),
            placeholder="Search character...",
            textvariable=self.char_var
        )
        self.char_combo.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 8), padx=4)
        create_tooltip(self.char_combo, "Select a character to add")

        button_frame = ttk.Frame(add)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 8))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(button_frame, text="+ Add to Prompt", command=self._add_character).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        
        theme = self.tab.winfo_toplevel().theme_manager.themes.get(
            self.tab.winfo_toplevel().theme_manager.current_theme, {}
        )
        pbg = theme.get("panel_bg", "#1e1e1e")
        accent = theme.get("accent", "#0078d7")

        self.create_char_btn = tk.Button(
            button_frame, 
            text="✨ Create New Character", 
            command=self._create_new_character, 
            bg=pbg,
            fg=accent,
            highlightbackground=accent,
            highlightthickness=2,
            relief="flat", 
            font=("Lexend", 9)
        )
        self.create_char_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self.create_char_btn._base_bg = pbg
        
        self.create_char_btn.bind("<Enter>", lambda e: self.create_char_btn.config(bg=theme.get("hover_bg", "#333333")))
        self.create_char_btn.bind("<Leave>", lambda e: self.create_char_btn.config(bg=getattr(self.create_char_btn, "_base_bg", "#1e1e1e")))


        # 4. Selected Characters List (Same as original)
        self.scrollable_canvas = ScrollableCanvas(self.tab)
        self.scrollable_canvas.grid(row=3, column=0, sticky="nsew", padx=10, pady=SECTION_PAD_Y)

        self.chars_container = self.scrollable_canvas.get_container()
        self.chars_canvas = self.scrollable_canvas.canvas

    # --- Tagging Helper Methods ---

    def _update_tag_list(self):
        """Update the tag selector based on selected category and character usage."""
        try:
            cat = self.tag_category_var.get()
            
            # Find all tags used by ALL available characters
            used = set()
            for _, data in (self.characters or {}).items():
                char_tags = data.get("tags") or []
                if isinstance(char_tags, str):
                    char_tags = [t.strip().lower() for t in char_tags.split(",") if t.strip()]
                for t in char_tags:
                    if t:
                        used.add(t)

            if cat == "All":
                tag_values = sorted(list(used))
            else:
                cat_tags = set([t.lower() for t in self.categorized_tags_map.get(cat, [])])
                tag_values = sorted(list(used & cat_tags))

            self.tag_combo.set_values(tag_values)
            self.tag_var.set("")
            
        except Exception:
            from utils import logger
            logger.exception("Failed to update tag list")

    def _add_selected_tag(self, tag_value: str):
        """Add a tag to the selected tags list and refresh."""
        if not tag_value: return
            
        if tag_value not in self.selected_tags:
            self.selected_tags.append(tag_value)
            self._render_selected_tags()
            self._filter_characters() # Trigger filter update
            
        self.tag_var.set("")

    def _remove_selected_tag(self, tag_value: str):
        """Remove a tag from the selected tags list and refresh."""
        if tag_value in self.selected_tags:
            self.selected_tags.remove(tag_value)
            self._render_selected_tags()
            self._filter_characters()

    def _clear_tag_filter(self):
        self.tag_category_var.set("All")
        self.tag_var.set("")
        self.selected_tags = []
        self._render_selected_tags()
        self._update_tag_list()
        self._filter_characters()

    def _render_selected_tags(self):
        try:
            self.selected_tags_frame.clear()
        except Exception:
            for w in self.selected_tags_frame.winfo_children(): w.destroy()

        if not self.selected_tags: return

        for t in self.selected_tags:
            try:
                self.selected_tags_frame.add_button(
                    text=f"{t} ✕",
                    style="Accent.TButton",
                    command=lambda v=t: self._remove_selected_tag(v),
                )
            except Exception:
                pass

    def _filter_characters(self, *args):
        """Filter character dropdown based on search text AND tags."""
        # Note: Original CharactersTab has _filter_characters called by char_search_var trace?
        # Actually in CharactersTab, it uses SearchableCombobox which handles its own text filtering usually, 
        # but if we want to filter the AVAILABLE values in the combobox, we should do it here.
        
        # However, SearchableCombobox already filters based on what you type.
        # We need to filter the BASE values of the combobox based on TAGS.
        
        search_text = self.char_var.get().lower()

        # Get currently used characters
        used = {c["name"] for c in self.selected_characters}
        
        # Start with all characters
        candidates = []
        for name, data in self.characters.items():
            if name in used: continue
            
            # Apply Tag Filter
            if self.selected_tags:
                char_tags = data.get("tags") or []
                if isinstance(char_tags, str):
                    char_tags = [t.strip().lower() for t in char_tags.split(",") if t.strip()]
                else:
                    char_tags = [t.lower() for t in char_tags]
                
                # Must have ALL selected tags
                missing = [t.lower() for t in self.selected_tags if t.lower() not in char_tags]
                if missing:
                    continue
            
            candidates.append(name)
        
        # Update combobox values
        self.char_combo.set_values(sorted(candidates))
        
        # Trigger on_change in case we need to update search text filtering
        # The searchable combobox does not automatically refilter against current text when values change unless we tell it.
        # But set_values usually resets the list.
        # We can leave it as is.
