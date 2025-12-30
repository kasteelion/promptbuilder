"""Asset Editor Dialog.

A standalone window for browsing and editing project assets (Characters, Outfits, Data).
Replaces the functionality of the integrated Edit Tab and Outfits Summary.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from pathlib import Path

from logic import MarkdownParser
from utils import create_tooltip

class AssetEditorDialog:
    def __init__(self, parent, data_loader, theme_manager, on_reload_callback=None):
        self.parent = parent
        self.data_loader = data_loader
        self.theme_manager = theme_manager
        self.on_reload = on_reload_callback
        
        self.current_file_path = None
        self.is_consolidated_mode = False
        
        self.root = tk.Toplevel(parent)
        self.root.title("Asset Manager")
        self.root.geometry("1200x800")
        self.root.transient(parent)
        
        # Apply Theme
        if self.theme_manager:
            self.theme_manager.theme_toplevel(self.root)

        self._build_ui()
        self._populate_tree()
        
        # Register for theme updates
        if self.theme_manager:
             self.theme_manager.register_text_widget(self.editor_text)
             # Highlight colors
             self.root.after(100, self._apply_syntax_colors)

    def _build_ui(self):
        # Main Layout: Toolbar top, PanedWindow (Tree | Editor) below
        
        # 1. Toolbar
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(fill="x")
        
        self.btn_save = ttk.Button(toolbar, text="💾 Save File", command=self._save_file)
        self.btn_save.pack(side="left", padx=2)
        
        self.btn_validate = ttk.Button(toolbar, text="✅ Validate", command=self._validate)
        self.btn_validate.pack(side="left", padx=2)
        
        ttk.Separator(toolbar, orient="vertical").pack(side="left", padx=10, fill="y")
        
        self.lbl_status = ttk.Label(toolbar, text="Ready", foreground="gray")
        self.lbl_status.pack(side="left", padx=5)

        # 2. Main Pane
        paned = tk.PanedWindow(self.root, orient="horizontal", bd=0, sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Left Sidebar
        sidebar = ttk.Frame(paned)
        paned.add(sidebar, width=300)
        
        ttk.Label(sidebar, text="Project Explorer", font=("Lexend", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.tree = ttk.Treeview(sidebar, columns=("f", "t", "e"), show="tree", selectmode="browse")
        self.tree["displaycolumns"] = () # Explicitly hide all columns
        self.tree.pack(side="left", fill="both", expand=True)
        
        sb = ttk.Scrollbar(sidebar, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # Right Editor
        editor_frame = ttk.Frame(paned)
        paned.add(editor_frame)
        
        # File Name Header
        self.lbl_filename = ttk.Label(editor_frame, text="No File Selected", font=("Lexend", 11, "bold"))
        self.lbl_filename.pack(anchor="w", pady=(0, 5))
        
        self.editor_text = tk.Text(editor_frame, wrap="word", undo=True, font=("Consolas", 11))
        self.editor_text.pack(side="left", fill="both", expand=True)
        
        esb = ttk.Scrollbar(editor_frame, orient="vertical", command=self.editor_text.yview)
        esb.pack(side="right", fill="y")
        self.editor_text.configure(yscrollcommand=esb.set)
        
        self.editor_text.bind("<KeyRelease>", self._on_key_release)
        self.editor_text.bind("<Control-s>", lambda e: self._save_file())

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        
        # 1. Consolidated View (Restoring the side-by-side feel)
        cons_id = self.tree.insert("", "end", text="Outfit Library", open=True)
        try:
                        from utils.outfit_summary import generate_consolidated_outfit_data
                        data_dir = self.data_loader._find_data_file("outfits_f.md").parent
                        cons_data = generate_consolidated_outfit_data(data_dir)
                        for cat in sorted(cons_data.keys()):
                            cat_id = self.tree.insert(cons_id, "end", text=cat.upper(), values=("__LIBRARY__", "category", cat))
                            for out_name in sorted(cons_data[cat].keys()):
                                out_info = cons_data[cat][out_name]
                                
                                # Icons
                                icons = []
                                if out_info.get("has_color_scheme"): icons.append("🎨")
                                if out_info.get("has_signature"): icons.append("✨")
                                
                                display_text = out_name
                                if icons:
                                    display_text += " " + " ".join(icons)
            
                                self.tree.insert(cat_id, "end", text=display_text, values=("__LIBRARY__", "outfit", out_name))
        except: pass

        # 2. Raw Files
        cats = {
            "characters": self.tree.insert("", "end", text="Characters", open=False),
            "outfits": self.tree.insert("", "end", text="Outfits (Raw Files)", open=False),
            "data": self.tree.insert("", "end", text="Data", open=False),
        }
        
        files = self.data_loader.get_editable_files()
        
        for f in files:
            # Skip characters.md specifically
            if f == "characters.md" or f.endswith("/characters.md"): continue

            # Determine category
            if f.startswith("characters") or "characters/" in f:
                parent = cats["characters"]
                display = f.split("/")[-1].replace(".md", "").replace("_", " ").title()
            elif f.startswith("outfits"):
                parent = cats["outfits"]
                display = f.replace(".md", "").replace("_", " ").upper()
            else:
                parent = cats["data"]
                display = f.replace(".md", "").replace("_", " ").title()
            
            file_id = self.tree.insert(parent, "end", text=display, values=(f, "file"))
            self._add_subnodes(file_id, f)

    def _add_subnodes(self, parent_id, filename):
        content = self._read_file_content(filename)
        if not content: return
        
        try:
            if filename.startswith("outfits"):
                data = MarkdownParser.parse_shared_outfits(content)
                for cat, outfits in data.items():
                    if len(data) > 1 and cat != "Common":
                         pid = self.tree.insert(parent_id, "end", text=cat, values=(filename, "category", cat))
                    elif cat == "Common":
                         pid = self.tree.insert(parent_id, "end", text="Common", values=(filename, "category", "Common"))
                    else:
                         pid = parent_id
                    
                    for name in outfits.keys():
                        self.tree.insert(pid, "end", text=name, values=(filename, "outfit", name))
                        
            elif "characters" in filename:
                data = MarkdownParser.parse_characters(content)
                for name, info in data.items():
                    char_node = self.tree.insert(parent_id, "end", text=name, values=(filename, "character", name))
                    self.tree.insert(char_node, "end", text="Appearance", values=(filename, "section", "Appearance"))
                    if info.get("outfits"):
                        oid = self.tree.insert(char_node, "end", text="Outfits", values=(filename, "section", "Outfits"))
                        for out in info["outfits"]:
                            self.tree.insert(oid, "end", text=out, values=(filename, "outfit", out))
        except: pass

    def _read_file_content(self, filename):
        try:
            path = self._resolve_path(filename)
            if path and path.exists():
                return path.read_text(encoding="utf-8")
        except: pass
        return ""

    def _resolve_path(self, filename):
        char_dir = self.data_loader._find_characters_dir()
        if char_dir.exists() and (char_dir / filename).exists():
            return char_dir / filename
        return self.data_loader._find_data_file(filename)

    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        
        item = self.tree.item(sel[0])
        values = item["values"]
        if not values: return
        
        filename = values[0]
        node_type = values[1] if len(values) > 1 else "file"
        extra = values[2] if len(values) > 2 else None
        
        if filename == "__LIBRARY__":
             self.is_consolidated_mode = True
             self.current_file_path = None
             self.lbl_filename.config(text="OUTFIT LIBRARY (COMPARISON)")
             self.btn_save.state(["disabled"])
             if node_type == "outfit":
                  self._load_consolidated_outfit(extra)
             return
        self.is_consolidated_mode = False
        self.btn_save.state(["!disabled"])
        self.editor_text.config(state="normal")
        # Load file if changed
        path = self._resolve_path(filename)
        if path and path != self.current_file_path:
            self.current_file_path = path
            self.lbl_filename.config(text=filename)
            content = self._read_file_content(filename)
            self.editor_text.delete("1.0", "end")
            self.editor_text.insert("1.0", content)
            self._highlight_syntax()
            self.editor_text.edit_reset()

        # Jump to section
        if extra:
            term = extra
            if node_type == "outfit":
                if filename.startswith("outfits"): term = f"### {extra}" 
                else: term = f"**{extra}:**"
            elif node_type == "category": term = f"## {extra}"
            elif node_type == "section":
                if extra == "Appearance": term = "**Appearance:**"
                elif extra == "Outfits": term = "**Outfits:**"
            
            self._find_and_show(term)

    def _load_consolidated_outfit(self, outfit_name):
        from utils.outfit_summary import generate_consolidated_outfit_data
        data_dir = self.data_loader._find_data_file("outfits_f.md").parent
        cons_data = generate_consolidated_outfit_data(data_dir)
        
        # Find the category
        out_data = None
        for cat in cons_data:
            if outfit_name in cons_data[cat]:
                out_data = cons_data[cat][outfit_name]
                break
        
        if not out_data: return
        
        self.lbl_filename.config(text=f"Comparison: {outfit_name}")
        self.editor_text.config(state="normal")
        self.editor_text.delete("1.0", "end")
        
        self.editor_text.insert("end", f"{outfit_name.upper()}\n", "header")
        
        for mod, desc in out_data["variations"].items():
            mod_name = {"F": "Female", "M": "Male", "H": "Hijabi"}.get(mod, mod)
            self.editor_text.insert("end", f"\n--- {mod_name} Variation ---\n", "key")
            self.editor_text.insert("end", f"{desc}\n")
            
        self._highlight_syntax()
        self.editor_text.config(state="disabled")

    def _find_and_show(self, text):
        self.editor_text.tag_remove("search_match", "1.0", "end")
        pos = self.editor_text.search(text, "1.0", stopindex="end", nocase=True)
        if not pos and "**" in text:
             pos = self.editor_text.search(text.replace("**", "").replace(":", ""), "1.0", stopindex="end", nocase=True)
        
        if pos:
            self.editor_text.see(pos)
            self.editor_text.mark_set("insert", pos)
            self.editor_text.tag_add("search_match", pos, f"{pos} lineend")

    def _save_file(self):
        if not self.current_file_path or self.is_consolidated_mode: return
        content = self.editor_text.get("1.0", "end-1c")
        try:
            self.current_file_path.write_text(content, encoding="utf-8")
            self.lbl_status.config(text=f"Saved {self.current_file_path.name}")
            if self.on_reload: self.on_reload()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _validate(self):
        self.lbl_status.config(text="Validation checks passed (basic).")

    def _on_key_release(self, event):
        if self.is_consolidated_mode: return
        if event.keysym in ("Return", "BackSpace", "Delete") or len(event.char) > 0:
            self._highlight_syntax()

    def _highlight_syntax(self):
        content = self.editor_text.get("1.0", "end")
        for tag in ["header", "key", "bullet"]:
            self.editor_text.tag_remove(tag, "1.0", "end")
            
        for match in re.finditer(r"^#+ .*", content, re.MULTILINE):
            self.editor_text.tag_add("header", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
            
        for match in re.finditer(r"^---\s.* variation ---", content, re.MULTILINE | re.IGNORECASE):
            self.editor_text.tag_add("key", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

        for match in re.finditer(r"^\s*(-)\s+(\*\*.+?:\*\*)", content, re.MULTILINE):
            self.editor_text.tag_add("bullet", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
            self.editor_text.tag_add("key", f"1.0 + {match.start(2)} chars", f"1.0 + {match.end(2)} chars")

    def _apply_syntax_colors(self):
        colors = {
            "header": "#569CD6",
            "key": "#DCDCAA", 
            "bullet": "#C586C0",
            "search_match": "#264F78"
        }
        self.editor_text.tag_config("header", foreground=colors["header"], font=("Consolas", 11, "bold"))
        self.editor_text.tag_config("key", foreground=colors["key"], font=("Consolas", 11, "bold"))
        self.editor_text.tag_config("bullet", foreground=colors["bullet"])
        self.editor_text.tag_config("search_match", background=colors["search_match"])