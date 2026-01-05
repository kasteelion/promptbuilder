"""Markdown file editor tab UI with syntax highlighting and visual tools."""

import re
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, List, Dict

from logic.parsers import MarkdownParser
from utils import create_tooltip


class EditTab:
    """Tab for editing markdown data files with advanced features."""

    def __init__(self, parent: ttk.Notebook, data_loader, theme_manager, on_reload_callback: Callable[[], None], existing_frame=None):
        """Initialize edit tab.

        Args:
            parent: Parent notebook widget
            data_loader: DataLoader instance
            theme_manager: ThemeManager instance
            on_reload_callback: Function to call after saving
            existing_frame: Optional frame to use instead of creating a new one
        """
        self.parent = parent
        self.data_loader = data_loader
        self.theme_manager = theme_manager
        self.on_reload = on_reload_callback
        self.current_file_path = None
        self.is_visual_mode = False
        
        # Data for visual editor
        self.parsed_data = {} 
        self.current_visual_item = None
        
        # Track visual widgets for theme updates
        self._visual_widgets = []

        if existing_frame:
            self.tab = existing_frame
        else:
            self.tab = ttk.Frame(parent, style="TFrame")
            parent.add(self.tab, text="Edit Data")

        self._build_ui()
        
        # Register for theme updates
        if self.theme_manager:
            self.theme_manager.register_text_widget(self.editor_text)
            self.theme_manager.register(self.tab, self._apply_syntax_colors)
            
        self._refresh_file_list()
        self._load_markdown_for_editing()

    def _get_editable_files(self) -> List[str]:
        """Get current list of editable files including character files."""
        return self.data_loader.get_editable_files()

    def _refresh_file_list(self):
        """Refresh the list of editable files in the dropdown."""
        current_file = self.edit_file_var.get()
        files = self._get_editable_files()
        self.edit_file_combo["values"] = files

        if current_file in files:
            self.edit_file_combo.set(current_file)
        elif files:
            self.edit_file_combo.current(0)

    def _build_ui(self):
        """Build the edit tab UI."""
        self.tab.columnconfigure(0, weight=1)
        self.tab.rowconfigure(2, weight=1) 

        # 1. Control Bar
        control_frame = ttk.Frame(self.tab, style="TFrame")
        control_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 5))
        control_frame.columnconfigure(1, weight=1)

        # File Selector
        ttk.Label(control_frame, text="File:").pack(side="left", padx=(0, 5))
        
        self.edit_file_var = tk.StringVar()
        self.edit_file_combo = ttk.Combobox(
            control_frame, textvariable=self.edit_file_var, state="readonly", width=30
        )
        self.edit_file_combo.pack(side="left", padx=(0, 10))
        self.edit_file_combo.bind("<<ComboboxSelected>>", self._on_file_selected)

        # Toolbar
        self.toolbar_frame = ttk.Frame(control_frame)
        self.toolbar_frame.pack(side="left", fill="x")

        def mk_btn(text, cmd, tip, width=None):
            b = ttk.Button(self.toolbar_frame, text=text, command=cmd, width=width)
            b.pack(side="left", padx=2)
            create_tooltip(b, tip)
            return b

        self.btn_save = mk_btn("💾 Save", self._save_markdown, "Save changes and reload data")
        self.btn_validate = mk_btn("✅ Validate", self._validate_content, "Check for syntax errors")
        self.btn_snippet = mk_btn("➕ Snippet", self._show_snippet_menu, "Insert template code")
        self.btn_find = mk_btn("🔍 Find", self._toggle_search, "Show/hide search bar")
        
        ttk.Separator(self.toolbar_frame, orient="vertical").pack(side="left", padx=5, fill="y")
        
        self.btn_visual = mk_btn("🎨 Visual Editor", self._toggle_visual_mode, "Switch between Text and Visual editing")
        self.btn_visual.state(["disabled"]) # Enabled only for supported files

        # 2. Search Bar
        self.search_frame = ttk.Frame(self.tab, style="TFrame")
        self.search_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 5))
        self.search_frame.grid_remove() 

        ttk.Label(self.search_frame, text="Find:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self._find_next())
        
        ttk.Button(self.search_frame, text="Next", command=self._find_next, width=6).pack(side="left", padx=2)
        ttk.Button(self.search_frame, text="❌", command=self._toggle_search, width=3).pack(side="left", padx=2)
        
        self.search_status = ttk.Label(self.search_frame, text="", foreground="gray")
        self.search_status.pack(side="left", padx=10)

        # 3. Main Content Area (Stack for Text vs Visual)
        self.content_stack = ttk.Frame(self.tab)
        self.content_stack.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 15))
        self.content_stack.columnconfigure(0, weight=1)
        self.content_stack.rowconfigure(0, weight=1)

        # --- Text Editor View ---
        self.text_editor_frame = ttk.Frame(self.content_stack)
        self.text_editor_frame.grid(row=0, column=0, sticky="nsew")
        self.text_editor_frame.columnconfigure(0, weight=1)
        self.text_editor_frame.rowconfigure(0, weight=1)

        self.editor_text = tk.Text(
            self.text_editor_frame, 
            wrap="word", 
            undo=True,
            font=("Consolas", 10)
        )
        self.editor_text.grid(row=0, column=0, sticky="nsew")
        
        editor_scroll = ttk.Scrollbar(
            self.text_editor_frame, orient="vertical", command=self.editor_text.yview
        )
        editor_scroll.grid(row=0, column=1, sticky="ns")
        self.editor_text.configure(yscrollcommand=editor_scroll.set)
        
        self.editor_text.bind("<KeyRelease>", self._on_key_release)

        # --- Visual Editor View ---
        self.visual_editor_frame = ttk.Frame(self.content_stack)
        self.visual_editor_frame.grid(row=0, column=0, sticky="nsew")
        self.visual_editor_frame.grid_remove() # Hidden by default
        self.visual_editor_frame.columnconfigure(1, weight=1)
        self.visual_editor_frame.rowconfigure(0, weight=1)

        # Left: Treeview
        tree_frame = ttk.Frame(self.visual_editor_frame)
        tree_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        
        self.visual_tree = ttk.Treeview(tree_frame, columns=("count"), show="tree", selectmode="browse")
        self.visual_tree.column("#0", width=200)
        self.visual_tree.pack(side="left", fill="y", expand=True)
        self.visual_tree.bind("<<TreeviewSelect>>", self._on_visual_select)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.visual_tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.visual_tree.configure(yscrollcommand=tree_scroll.set)
        
        # Tools under tree
        tree_tools = ttk.Frame(self.visual_editor_frame)
        tree_tools.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        ttk.Button(tree_tools, text="➕ New", command=self._visual_add_new).pack(side="left", fill="x", expand=True)
        ttk.Button(tree_tools, text="🗑️ Del", command=self._visual_delete).pack(side="left", fill="x", expand=True)

        # Right: Detail Editor
        self.detail_frame = ttk.Frame(self.visual_editor_frame)
        self.detail_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")
        self.detail_frame.columnconfigure(1, weight=1)
        
        # Header Fields
        ttk.Label(self.detail_frame, text="Category:", font=("Lexend", 9, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.vis_cat_var = tk.StringVar()
        self.vis_cat_entry = ttk.Entry(self.detail_frame, textvariable=self.vis_cat_var)
        self.vis_cat_entry.grid(row=0, column=1, sticky="ew", pady=(0, 10), padx=(5, 0))
        
        ttk.Label(self.detail_frame, text="Name:", font=("Lexend", 9, "bold")).grid(row=1, column=0, sticky="w", pady=(0, 2))
        self.vis_name_var = tk.StringVar()
        self.vis_name_entry = ttk.Entry(self.detail_frame, textvariable=self.vis_name_var)
        self.vis_name_entry.grid(row=1, column=1, sticky="ew", pady=(0, 15), padx=(5, 0))
        
        # Structured Fields
        self.vis_fields = {}
        field_labels = [
            ("Top", "Main upper garment"), 
            ("Bottom", "Main lower garment"), 
            ("Footwear", "Shoes/socks"), 
            ("Accessories", "Jewelry, bags, etc."), 
            ("Hair/Makeup", "Specific styling")
        ]
        
        current_row = 2
        for key, tooltip in field_labels:
            lbl = ttk.Label(self.detail_frame, text=f"{key}:", font=("Lexend", 8))
            lbl.grid(row=current_row, column=0, sticky="nw", pady=(4, 0))
            create_tooltip(lbl, tooltip)
            
            var = tk.StringVar()
            entry = ttk.Entry(self.detail_frame, textvariable=var)
            entry.grid(row=current_row, column=1, sticky="ew", pady=(2, 5), padx=(5, 0))
            
            self.vis_fields[key] = var
            # Bind commit on focus out
            entry.bind("<FocusOut>", self._visual_commit_change)
            current_row += 1

        # Extra/Raw Text
        ttk.Label(self.detail_frame, text="Extra/Raw:", font=("Lexend", 8)).grid(row=current_row, column=0, sticky="nw", pady=(10, 0))
        
        self.visual_raw_text = tk.Text(self.detail_frame, height=5, font=("Lexend", 9), wrap="word")
        self.visual_raw_text.grid(row=current_row, column=1, sticky="nsew", pady=(10, 0), padx=(5, 0))
        self.detail_frame.rowconfigure(current_row, weight=1)
        
        # Bind changes
        self.vis_name_entry.bind("<FocusOut>", self._visual_commit_change)
        self.vis_cat_entry.bind("<FocusOut>", self._visual_commit_change)
        self.visual_raw_text.bind("<FocusOut>", self._visual_commit_change)


    def _apply_syntax_colors(self, theme=None):
        """Apply colors to syntax tags based on current theme."""
        if not theme:
            theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})

        is_dark = "dark" in self.theme_manager.current_theme.lower() or theme.get("bg", "#000000") < "#888888"
        
        colors = {
            "header": "#569CD6" if is_dark else "#0000FF",
            "key": "#DCDCAA" if is_dark else "#795E26",
            "bullet": "#C586C0" if is_dark else "#AF00DB",
            "comment": "#6A9955" if is_dark else "#008000",
            "highlight": "#264F78" if is_dark else "#ADD6FF",
        }

        self.editor_text.tag_config("header", foreground=colors["header"], font=("Consolas", 11, "bold"))
        self.editor_text.tag_config("key", foreground=colors["key"], font=("Consolas", 10, "bold"))
        self.editor_text.tag_config("bullet", foreground=colors["bullet"])
        self.editor_text.tag_config("comment", foreground=colors["comment"], font=("Consolas", 10, "italic"))
        self.editor_text.tag_config("search_match", background=colors["highlight"])
        
        self._highlight_syntax()

    def _highlight_syntax(self, event=None):

        """Apply syntax highlighting to the text."""

        if not self.editor_text.get("1.0", "end-1c"):

            return



        for tag in ["header", "key", "bullet", "comment"]:

            self.editor_text.tag_remove(tag, "1.0", "end")



        content = self.editor_text.get("1.0", "end")



        # Headers

        for match in re.finditer(r"^#+ .*", content, re.MULTILINE):

            self.editor_text.tag_add("header", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")



        # Keys

        for match in re.finditer(r"^\s*(-)\s+(\*\*.+?:\*\*)", content, re.MULTILINE):

            self.editor_text.tag_add("bullet", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")

            self.editor_text.tag_add("key", f"1.0 + {match.start(2)} chars", f"1.0 + {match.end(2)} chars")



    def _on_key_release(self, event):
        if event.keysym in ("Return", "BackSpace", "Delete") or len(event.char) > 0:
            self._highlight_syntax()
    
    
    
    def _on_file_selected(self, event):

        self.is_visual_mode = False

        self.visual_editor_frame.grid_remove()

        self.text_editor_frame.grid()

        self._load_markdown_for_editing()



    def _load_markdown_for_editing(self):

        filename = self.edit_file_var.get()

        if not filename: return



        # Enable visual mode only for outfit files for now

        if filename.startswith("outfits_"):

            self.btn_visual.state(["!disabled"])

        else:

            self.btn_visual.state(["disabled"])



        # Resolve path

        char_dir = self.data_loader._find_characters_dir()

        if char_dir.exists() and (char_dir / filename).exists():

            self.current_file_path = char_dir / filename

        else:

            self.current_file_path = self.data_loader._find_data_file(filename)



        self.editor_text.delete("1.0", "end")



        if self.current_file_path.exists():

            try:

                content = self.current_file_path.read_text(encoding="utf-8")

                self.editor_text.insert("1.0", content)

                self._highlight_syntax()

                self.editor_text.edit_reset()

            except Exception as e:

                messagebox.showerror("File Read Error", f"Could not read {filename}:\n{str(e)}")

        else:

            self.editor_text.insert("1.0", f"## New File: {filename}\n")

            self._highlight_syntax()



    def _save_markdown(self):

        # Sync visual to text if needed

        if self.is_visual_mode:

            self._sync_visual_to_text()



        if not self.current_file_path: return



        content = self.editor_text.get("1.0", "end-1c")



        try:

            self.current_file_path.write_text(content, encoding="utf-8")

            self._refresh_file_list()

            self.on_reload()

            

            from utils.notification import notify

            root = self.tab.winfo_toplevel()

            notify(root, "Success", f"{self.current_file_path.name} saved.", level="success", duration=2000)

            

        except Exception as e:

            messagebox.showerror("Save Error", f"Could not write file:\n{str(e)}")



    def _validate_content(self):

        if self._run_validation():

            from utils.notification import notify

            root = self.tab.winfo_toplevel()

            notify(root, "Valid", "Syntax looks correct!", level="success")



    def _run_validation(self, silent=False) -> bool:

        if self.is_visual_mode:

            return True # Visual mode is structurally safe by definition



        filename = self.edit_file_var.get()

        content = self.editor_text.get("1.0", "end-1c")

        

        try:

            if filename.startswith("outfits"):

                MarkdownParser.parse_shared_outfits(content)

            elif filename == "base_prompts.md":

                MarkdownParser.parse_base_prompts(content)

            elif filename == "color_schemes.md":

                MarkdownParser.parse_color_schemes(content)

            elif filename in ("scenes.md", "poses.md"):

                MarkdownParser.parse_presets(content)

            elif filename == "interactions.md":

                MarkdownParser.parse_interactions(content)

            else:

                if "characters" in str(self.current_file_path):

                    MarkdownParser.parse_characters(content)

            return True

        except Exception as e:

            if not silent:

                messagebox.showerror("Validation Error", f"Syntax Error in {filename}:\n\n{str(e)}")

            return False



    def _show_snippet_menu(self):

        if self.is_visual_mode: return # No snippets in visual mode

        

        menu = tk.Menu(self.tab, tearoff=0)

        filename = self.edit_file_var.get()

        

        if filename.startswith("outfits"):

            menu.add_command(label="New Outfit", command=lambda: self._insert_text("\n### Outfit Name\n- **Top:** ...\n"))

        elif filename in ("scenes.md", "poses.md"):

            menu.add_command(label="New Category", command=lambda: self._insert_text("\n## New Category\n"))

            menu.add_command(label="New Item", command=lambda: self._insert_text("- **Name:** ...\n"))

        

        try:

            x = self.tab.winfo_pointerx()

            y = self.tab.winfo_pointery()

            menu.tk_popup(x, y)

        except: pass



    def _insert_text(self, text):

        self.editor_text.insert("insert", text)

        self.editor_text.see("insert")

        self._highlight_syntax()



    # --- Search ---

    def _toggle_search(self):

        if self.search_frame.winfo_viewable():

            self.search_frame.grid_remove()

            self.editor_text.tag_remove("search_match", "1.0", "end")

        else:

            self.search_frame.grid()

            self.search_entry.focus_set()



    def _find_next(self):

        query = self.search_var.get()

        if not query: return

        self.editor_text.tag_remove("search_match", "1.0", "end")

        start_pos = self.editor_text.index("insert")

        pos = self.editor_text.search(query, start_pos, stopindex="end", nocase=True)

        if not pos:

            pos = self.editor_text.search(query, "1.0", stopindex=start_pos, nocase=True)

        if pos:

            end_pos = f"{pos} + {len(query)} chars"

            self.editor_text.tag_add("search_match", pos, end_pos)

            self.editor_text.see(pos)

            self.editor_text.mark_set("insert", end_pos)

            self.search_status.config(text="")

        else:

            self.search_status.config(text="Not found")



    # --- Visual Editor Logic ---



    def _toggle_visual_mode(self):

        if self.is_visual_mode:

            # Switch to Text

            self._sync_visual_to_text()

            self.visual_editor_frame.grid_remove()

            self.text_editor_frame.grid()

            self.is_visual_mode = False

            self.btn_validate.state(["!disabled"])

            self.btn_snippet.state(["!disabled"])

            self.btn_find.state(["!disabled"])

            self._highlight_syntax()

        else:

            # Switch to Visual

            if self._load_visual_data():

                self.text_editor_frame.grid_remove()

                self.visual_editor_frame.grid()

                self.is_visual_mode = True

                self.btn_validate.state(["disabled"])

                self.btn_snippet.state(["disabled"])

                self.btn_find.state(["disabled"]) # Search not impl in visual yet



    def _load_visual_data(self):

        """Parse text content into self.parsed_data and populate tree."""

        content = self.editor_text.get("1.0", "end-1c")

        filename = self.edit_file_var.get()

        

        try:

            if filename.startswith("outfits"):

                self.parsed_data = MarkdownParser.parse_shared_outfits(content)

            else:

                return False

                

            self._populate_visual_tree()

            return True

        except Exception as e:

            messagebox.showerror("Parse Error", f"Cannot switch to Visual Mode:\n{str(e)}\n\nFix syntax errors first.")

            return False



    def _populate_visual_tree(self):

        self.visual_tree.delete(*self.visual_tree.get_children())

        

        # Sort categories, keeping Common/Personal specific if needed

        cats = sorted(self.parsed_data.keys())

        

        for cat in cats:

            cat_node = self.visual_tree.insert("", "end", text=cat, open=True)

            outfits = self.parsed_data[cat]

            for name in sorted(outfits.keys()):

                self.visual_tree.insert(cat_node, "end", text=name, values=(cat, name))



    def _on_visual_select(self, event):

        sel = self.visual_tree.selection()

        if not sel: return

        

        item_id = sel[0]

        item_text = self.visual_tree.item(item_id, "text")

        parent_id = self.visual_tree.parent(item_id)

        

        # If parent_id is empty, it's a category

        if not parent_id:

            self.current_visual_item = None

            self._clear_detail_view()

            return

            

        parent_text = self.visual_tree.item(parent_id, "text")

        

        self.current_visual_item = (parent_text, item_text)

        

        full_desc = self.parsed_data.get(parent_text, {}).get(item_text, "")

        

        # Parse structure

        parts = self._parse_description_structure(full_desc)

        

        self.vis_cat_var.set(parent_text)

        self.vis_name_var.set(item_text)

        

        # Populate fields

        for key, var in self.vis_fields.items():

            var.set(parts.get(key, ""))

            

        self.visual_raw_text.delete("1.0", "end")

        self.visual_raw_text.insert("1.0", parts.get("Raw", ""))

        

        # Enable editing

        self.vis_cat_entry.config(state="normal")

        self.vis_name_entry.config(state="normal")

        self.visual_raw_text.config(state="normal")



    def _parse_description_structure(self, description: str) -> Dict[str, str]:

        """Parse structured fields from description text."""

        parts = {

            "Top": "", "Bottom": "", "Footwear": "", 

            "Accessories": "", "Hair/Makeup": "", "Raw": ""

        }

        

        lines = description.split('\n')

        raw_lines = []

        

        for line in lines:

            # Regex for "- **Key:** Value"

            m = re.match(r"^\s*-\s*\*\*([^:]+):\*\*\s*(.*)$", line)

            if m:

                key = m.group(1).strip()

                val = m.group(2).strip()

                # Map loose keys if needed

                if key in parts:

                    parts[key] = val

                    continue

            

            # If not matched or unknown key, keep as raw

            if line.strip():

                raw_lines.append(line)

                

        parts["Raw"] = "\n".join(raw_lines)

        return parts



    def _clear_detail_view(self):

        self.vis_cat_var.set("")

        self.vis_name_var.set("")

        for var in self.vis_fields.values():

            var.set("")

        self.visual_raw_text.delete("1.0", "end")

        self.vis_cat_entry.config(state="disabled")

        self.vis_name_entry.config(state="disabled")

        self.visual_raw_text.config(state="disabled")



    def _visual_commit_change(self, event=None):

        """Save changes from detail view back to parsed_data."""

        if not self.current_visual_item: return

        

        old_cat, old_name = self.current_visual_item

        

        new_cat = self.vis_cat_var.get().strip()

        new_name = self.vis_name_var.get().strip()

        

        # Reconstruct description

        new_desc_lines = []

        

        # Add structured fields if present

        for key in ["Top", "Bottom", "Footwear", "Accessories", "Hair/Makeup"]:

            val = self.vis_fields[key].get().strip()

            if val:

                new_desc_lines.append(f"- **{key}:** {val}")

        

        # Add raw text

        raw = self.visual_raw_text.get("1.0", "end-1c").strip()

        if raw:

            new_desc_lines.append(raw)

            

        new_desc = "\n".join(new_desc_lines)

        

        if not new_cat or not new_name: return

        

        # If renamed or moved

        if new_cat != old_cat or new_name != old_name:

            if old_cat in self.parsed_data and old_name in self.parsed_data[old_cat]:

                del self.parsed_data[old_cat][old_name]

                if not self.parsed_data[old_cat]: 

                    del self.parsed_data[old_cat]

            

            self.current_visual_item = (new_cat, new_name)

            self._populate_visual_tree()

        

        if new_cat not in self.parsed_data:

            self.parsed_data[new_cat] = {}

        self.parsed_data[new_cat][new_name] = new_desc



    def _visual_add_new(self):

        """Add a new item in visual mode."""

        cat = "New Category"

        name = "New Item"

        

        i = 1

        while cat in self.parsed_data and name in self.parsed_data[cat]:

            name = f"New Item {i}"

            i += 1

            

        if cat not in self.parsed_data:

            self.parsed_data[cat] = {}

        self.parsed_data[cat][name] = "- **Top:** ...\n"

        

        self._populate_visual_tree()



    def _visual_delete(self):

        sel = self.visual_tree.selection()

        if not sel: return

        

        item_id = sel[0]

        parent_id = self.visual_tree.parent(item_id)

        

        if not parent_id: 

            cat = self.visual_tree.item(item_id, "text")

            if messagebox.askyesno("Delete", f"Delete category '{cat}' and all items?"):

                if cat in self.parsed_data:

                    del self.parsed_data[cat]

                    self._populate_visual_tree()

            return

            

        name = self.visual_tree.item(item_id, "text")

        cat = self.visual_tree.item(parent_id, "text")

        

        if messagebox.askyesno("Delete", f"Delete '{name}'?"):

            if cat in self.parsed_data and name in self.parsed_data[cat]:

                del self.parsed_data[cat][name]

                if not self.parsed_data[cat]:

                    del self.parsed_data[cat]

                self._populate_visual_tree()

                self._clear_detail_view()



    def _sync_visual_to_text(self):

        """Reconstruct markdown from parsed_data."""

        lines = ["# Shared Outfits", "", "This file contains outfit templates shared across characters.", "", "---"]

        

        cats = sorted(self.parsed_data.keys())

        if "Common" in cats:

            cats.remove("Common")

            cats.insert(0, "Common")

            

        for cat in cats:

            lines.append("")

            lines.append(f"## {cat}")

            

            outfits = self.parsed_data[cat]

            for name in sorted(outfits.keys()):

                lines.append("")

                lines.append(f"### {name}")

                lines.append(outfits[name])

            

            lines.append("")

            lines.append("---")

            

        text_content = "\n".join(lines)

        self.editor_text.delete("1.0", "end")

        self.editor_text.insert("1.0", text_content)

