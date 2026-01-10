import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

from ui.widgets import ScrollableCanvas, CollapsibleFrame
from utils.backup import create_snapshot

class CharacterExplorer(ttk.Frame):
    """Interactive character explorer component."""
    
    def __init__(self, parent, data_loader, theme_manager, preferences, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.data_loader = data_loader
        self.tm = theme_manager
        self.prefs = preferences
        
        self.all_chars = []
        self.filtered_chars = []
        
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Top: Search and Stats
        top_frame = ttk.Frame(self, padding=(0, 0, 0, 10))
        top_frame.pack(fill="x")

        # --- Search & Filters ---
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side="left", fill="x", expand=True)

        ttk.Label(search_frame, text="🔍 SEARCH:", style="Bold.TLabel").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, style="TEntry")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10)

        ttk.Label(search_frame, text="🏷️ TAG:", style="Bold.TLabel").pack(side="left", padx=(10, 0))
        self.tag_var = tk.StringVar(value="All")
        self.tag_combo = ttk.Combobox(search_frame, textvariable=self.tag_var, state="readonly", width=15, font=("Lexend", 9))
        self.tag_combo.pack(side="left", padx=10)

        self.fav_only_var = tk.BooleanVar(value=False)
        self.fav_chk = ttk.Checkbutton(search_frame, text="⭐ FAVORITES ONLY", variable=self.fav_only_var, style="TCheckbutton")
        self.fav_chk.pack(side="left", padx=10)

        self.stats_label = ttk.Label(top_frame, text="TOTAL: 0", style="Title.TLabel")
        self.stats_label.pack(side="right")

        # Main Content: List | Detail
        try:
            pbg = self.tm.themes.get(self.tm.current_theme, {}).get("panel_bg", "#1e1e1e") if self.tm else "#1e1e1e"
        except: pbg = "#1e1e1e"

        self.paned = tk.PanedWindow(self, orient="horizontal", bg=pbg, bd=0, sashwidth=6, sashrelief="flat")
        self.paned.pack(fill="both", expand=True)

        # Left: List
        list_side = ttk.Frame(self.paned, style="TFrame")
        self.paned.add(list_side, width=300)

        self.char_listbox = tk.Listbox(list_side, font=("Lexend", 10), selectmode="single", exportselection=False, borderwidth=0, highlightthickness=0)
        self.char_listbox.pack(side="left", fill="both", expand=True)
        
        list_scroll = ttk.Scrollbar(list_side, orient="vertical", command=self.char_listbox.yview, style="Themed.Vertical.TScrollbar")
        list_scroll.pack(side="right", fill="y")
        self.char_listbox.config(yscrollcommand=list_scroll.set)

        # Right: Details
        detail_side = ttk.Frame(self.paned, style="TFrame")
        self.paned.add(detail_side)

        self.detail_nb = ttk.Notebook(detail_side, style="TNotebook")
        self.detail_nb.pack(fill="both", expand=True)

        # Details Tab
        self.preview_tab = ttk.Frame(self.detail_nb, style="TFrame")
        self.detail_nb.add(self.preview_tab, text="📄 DETAILS")
        
        self.preview_text = tk.Text(self.preview_tab, wrap="word", font=("Lexend", 10), highlightthickness=0, borderwidth=0, padx=20, pady=20)
        self.preview_text.pack(fill="both", expand=True)
        
        # Bindings
        self.search_var.trace_add("write", self.update_list)
        self.tag_var.trace_add("write", self.update_list)
        self.fav_only_var.trace_add("write", self.update_list)
        self.char_listbox.bind("<<ListboxSelect>>", self._on_select)

    def refresh(self):
        from utils.character_summary import generate_character_data
        chars_dir = self.data_loader._find_characters_dir()
        if chars_dir.exists():
            self.all_chars = generate_character_data(chars_dir)
            
            all_tags = set()
            for c in self.all_chars:
                for t in c.get("tags", []):
                    all_tags.add(t)
            self.tag_combo["values"] = ["All"] + sorted(list(all_tags))
            
            self.update_list()

    def update_list(self, *args):
        self.char_listbox.delete(0, tk.END)
        search = self.search_var.get().lower()
        tag = self.tag_var.get()
        fav_only = self.fav_only_var.get()
        
        self.filtered_chars = []
        favs = self.prefs.get("favorite_characters", []) if self.prefs else []

        for c in self.all_chars:
            if search and search not in c["name"].lower() and search not in c["appearance"].lower():
                continue
            if tag != "All" and tag not in c.get("tags", []):
                continue
            is_fav = c["name"] in favs
            if fav_only and not is_fav:
                continue
                
            self.filtered_chars.append(c)
            prefix = "★ " if is_fav else "  "
            self.char_listbox.insert(tk.END, f"{prefix}{c['name']}")
        
        self.stats_label.config(text=f"SHOWING: {len(self.filtered_chars)} / {len(self.all_chars)}")
        if self.filtered_chars:
            self.char_listbox.selection_set(0)
            self._on_select()

    def _on_select(self, event=None):
        selection = self.char_listbox.curselection()
        if not selection: return
        
        char = self.filtered_chars[selection[0]]
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("end", f"{char['name'].upper()}\n", "title")
        self.preview_text.insert("end", "=" * 40 + "\n\n")
        self.preview_text.insert("end", f"APPEARANCE:\n{char['appearance']}\n\n")
        if char.get("tags"):
            self.preview_text.insert("end", f"TAGS: {', '.join(char['tags'])}\n")
        self.preview_text.config(state="disabled")

    def apply_theme(self, theme):
        self.tm.apply_preview_theme(self.preview_text, theme)
        self.tm.apply_listbox_theme(self.char_listbox, theme)
        self.paned.config(bg=theme.get("panel_bg", theme["bg"]))


class TagAnalyzer(ttk.Frame):
    """Tag distribution and analytics component."""
    
    def __init__(self, parent, data_loader, theme_manager, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.data_loader = data_loader
        self.tm = theme_manager
        
        # Header with Controls
        header = ttk.Frame(self, padding=(0, 0, 0, 10))
        header.pack(fill="x")
        
        ttk.Label(header, text="ASSET TYPE:", style="Bold.TLabel").pack(side="left")
        
        self.asset_type_var = tk.StringVar(value="Characters")
        self.type_combo = ttk.Combobox(
            header, 
            textvariable=self.asset_type_var,
            values=["Characters", "Outfits", "Scenes", "Poses", "Interactions", "Global Matrix"],
            state="readonly",
            width=20,
            font=("Lexend", 9)
        )
        self.type_combo.pack(side="left", padx=10)
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        
        ttk.Button(header, text="🔄 REFRESH", command=self.refresh, style="Small.TButton").pack(side="right")
        
        # Main Content
        self.scroll = ScrollableCanvas(self)
        self.scroll.pack(fill="both", expand=True)
        self.container = self.scroll.get_container()
        
        self.refresh()

    def refresh(self):
        # Clear existing
        for child in self.container.winfo_children():
            child.destroy()
            
        asset_type = self.asset_type_var.get()
        
        if asset_type == "Global Matrix":
            self._show_global_matrix()
            self.scroll.refresh_mousewheel_bindings()
            self.scroll.update_scroll_region()
            return

        tag_counts = {}
        
        try:
            if asset_type == "Characters":
                data = self.data_loader.load_characters()
                for d in data.values():
                    self._add_tags(tag_counts, d.get("tags"))
                    
            elif asset_type == "Outfits":
                data = self.data_loader.load_outfits()
                # Structure: {'F': {Cat: {Name: Data}}, ...}
                for gender_data in data.values():
                    for cat_data in gender_data.values():
                        for item in cat_data.values():
                            self._add_tags(tag_counts, item.get("tags"))

            elif asset_type == "Scenes":
                data = self.data_loader.load_presets("scenes.md")
                # Structure: {Cat: {Name: Data}}
                for cat_data in data.values():
                    for item in cat_data.values():
                        self._add_tags(tag_counts, item.get("tags"))
                        
            elif asset_type == "Poses":
                data = self.data_loader.load_presets("poses.md")
                for cat_data in data.values():
                    for item in cat_data.values():
                        self._add_tags(tag_counts, item.get("tags"))
                        
            elif asset_type == "Interactions":
                data = self.data_loader.load_interactions()
                for cat_data in data.values():
                    for item in cat_data.values():
                        self._add_tags(tag_counts, item.get("tags"))

        except Exception as e:
            ttk.Label(self.container, text=f"Error loading {asset_type} tags:\n{e}", foreground="red").pack(pady=20)
            return

        if not tag_counts:
            ttk.Label(self.container, text=f"No tags found for {asset_type}.", style="Muted.TLabel").pack(pady=20)
            return

        ttk.Label(self.container, text=f"{asset_type.upper()} TAG DISTRIBUTION", style="Title.TLabel").pack(pady=10)
        
        # Sort and display
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Grid layout for better density
        grid_frame = ttk.Frame(self.container)
        grid_frame.pack(fill="x", padx=10)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)
        
        for idx, (tag, count) in enumerate(sorted_tags):
            col = idx % 2
            row = idx // 2
            
            pbg = self.tm.themes.get(self.tm.current_theme, {}).get("panel_bg", "#1e1e1e") if self.tm else "#1e1e1e"
            card = tk.Frame(grid_frame, bg=pbg, padx=10, pady=5)
            card.grid(row=row, column=col, sticky="ew", padx=5, pady=2)
            
            # Inner labels
            fg = self.tm.themes.get(self.tm.current_theme, {}).get("fg", "white") if self.tm else "white"
            tk.Label(card, text=tag.upper(), bg=pbg, fg=fg, font=("Lexend", 9)).pack(side="left")
            tk.Label(card, text=str(count), bg=pbg, fg="gray", font=("Lexend", 9, "bold")).pack(side="right")
            
        self.scroll.refresh_mousewheel_bindings()
        self.scroll.update_scroll_region()

    def _show_global_matrix(self):
        """Display a cross-reference matrix of tags across all asset types."""
        # Aggregate data
        matrix = {} # {tag: {type: count}}
        
        def process_tags(source_name, tags):
            if not tags: return
            if isinstance(tags, str):
                tags = [t.strip().lower() for t in tags.split(",") if t.strip()]
            for t in tags:
                t = str(t).strip().lower()
                if t:
                    if t not in matrix:
                        matrix[t] = {"total": 0}
                    matrix[t][source_name] = matrix[t].get(source_name, 0) + 1
                    matrix[t]["total"] += 1

        # Load all data
        try:
            # Characters
            chars = self.data_loader.load_characters()
            for d in chars.values(): process_tags("Chars", d.get("tags"))
            
            # Outfits
            outfits = self.data_loader.load_outfits()
            for gd in outfits.values():
                for cat in gd.values():
                    for item in cat.values(): process_tags("Outfits", item.get("tags"))
            
            # Scenes
            scenes = self.data_loader.load_presets("scenes.md")
            for cat in scenes.values():
                for item in cat.values(): process_tags("Scenes", item.get("tags"))
                
            # Poses
            poses = self.data_loader.load_presets("poses.md")
            for cat in poses.values():
                for item in cat.values(): process_tags("Poses", item.get("tags"))
                
            # Interactions
            interactions = self.data_loader.load_interactions()
            for cat in interactions.values():
                for item in cat.values(): process_tags("Interact", item.get("tags"))
                
        except Exception as e:
            ttk.Label(self.container, text=f"Error building matrix: {e}", foreground="red").pack()
            return

        ttk.Label(self.container, text="GLOBAL TAG MATRIX", style="Title.TLabel").pack(pady=10)
        
        # Header Row
        headers = ["TAG", "TOTAL", "CHARS", "OUTFITS", "SCENES", "POSES", "INTERACT"]
        h_frame = ttk.Frame(self.container)
        h_frame.pack(fill="x", padx=10, pady=5)
        
        for i, h in enumerate(headers):
            h_frame.columnconfigure(i, weight=1 if i == 0 else 0)
            width = 20 if i == 0 else 8
            lbl = ttk.Label(h_frame, text=h, width=width, font=("Lexend", 9, "bold"))
            lbl.grid(row=0, column=i, sticky="w" if i == 0 else "e", padx=5)

        ttk.Separator(self.container, orient="horizontal").pack(fill="x", padx=10, pady=5)
        
        # Data Rows
        sorted_tags = sorted(matrix.items(), key=lambda x: x[1]["total"], reverse=True)
        
        pbg = self.tm.themes.get(self.tm.current_theme, {}).get("panel_bg", "#1e1e1e") if self.tm else "#1e1e1e"
        fg = self.tm.themes.get(self.tm.current_theme, {}).get("fg", "white") if self.tm else "white"
        
        for t, counts in sorted_tags:
            row = tk.Frame(self.container, bg=pbg, pady=2)
            row.pack(fill="x", padx=10, pady=1)
            row.columnconfigure(0, weight=1)
            
            # Tag Name
            tk.Label(row, text=t.upper(), bg=pbg, fg=fg, font=("Lexend", 9), anchor="w").grid(row=0, column=0, sticky="ew", padx=5)
            
            # Counts
            cols = ["total", "Chars", "Outfits", "Scenes", "Poses", "Interact"]
            for i, key in enumerate(cols):
                val = counts.get(key, "-")
                lbl = tk.Label(row, text=str(val), bg=pbg, fg="gray" if val == "-" else fg, width=8, anchor="e", font=("Lexend", 9))
                lbl.grid(row=0, column=i+1, padx=5)

    def _add_tags(self, counts, tags):
        """Helper to safely add tags to counter."""
        if not tags: return
        if isinstance(tags, str):
            tags = [t.strip().lower() for t in tags.split(",") if t.strip()]
        
        for t in tags:
            t = str(t).strip().lower() # Normalization
            if t:
                counts[t] = counts.get(t, 0) + 1

    def apply_theme(self, theme):
        self.scroll.apply_theme(theme)


class DashboardDialog:
    """Consolidated Project Dashboard and health monitor."""

    def __init__(self, root: tk.Tk, data_loader, theme_manager, preferences):
        self.root = tk.Toplevel(root)
        self.root.title("PROJECT DASHBOARD")
        self.root.geometry("1100x800")
        self.root.minsize(900, 600)
        self.root.transient(root)
        
        self.data_loader = data_loader
        self.tm = theme_manager
        self.prefs = preferences
        
        if self.tm:
            self.tm.theme_toplevel(self.root)
            
        self._build_ui()
        self._refresh_data()
        
        # Register for theme updates
        if hasattr(root, "dialog_manager"):
             root.dialog_manager._register_dialog(self.root, self._apply_theme)

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Tab Control
        self.nb = ttk.Notebook(main_frame, style="TNotebook")
        self.nb.pack(fill="both", expand=True)

        # 1. Overview Tab
        self.overview_tab = ttk.Frame(self.nb, style="TFrame")
        self.nb.add(self.overview_tab, text="🏠 OVERVIEW")
        self._setup_overview_tab()

        # 2. Characters Tab (Explorer)
        self.char_explorer = CharacterExplorer(self.nb, self.data_loader, self.tm, self.prefs)
        self.nb.add(self.char_explorer, text="👥 CHARACTERS")

        # 3. Tags Tab (Analyzer)
        self.tag_analyzer = TagAnalyzer(self.nb, self.data_loader, self.tm)
        self.nb.add(self.tag_analyzer, text="🏷️ TAGS")

        # 4. Health Tab
        self.health_tab = ttk.Frame(self.nb, style="TFrame")
        self.nb.add(self.health_tab, text="⚖️ HEALTH")
        self._setup_health_tab()

        # Bottom Bar
        btn_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="REFRESH ALL DATA", command=self._refresh_data).pack(side="left")
        ttk.Button(btn_frame, text="CLOSE", command=self.root.destroy).pack(side="right")

    def _setup_overview_tab(self):
        self.overview_scroll = ScrollableCanvas(self.overview_tab)
        self.overview_scroll.pack(fill="both", expand=True)
        self.ov_container = self.overview_scroll.get_container()
        
        ttk.Label(self.ov_container, text="PROJECT OVERVIEW", style="Title.TLabel").pack(pady=20)
        
        self.stats_label = ttk.Label(self.ov_container, text="Loading info...", font=("Lexend", 11))
        self.stats_label.pack(pady=10)
        
        ttk.Separator(self.ov_container, orient="horizontal").pack(fill="x", pady=20, padx=50)
        
        ttk.Label(self.ov_container, text="QUICK ACTIONS", style="Bold.TLabel").pack(pady=10)
        
        actions_frame = ttk.Frame(self.ov_container)
        actions_frame.pack(pady=10)
        
        ttk.Button(actions_frame, text="📸 CREATE PROJECT SNAPSHOT", command=self._create_snapshot_cb).pack(side="left", padx=10)
        ttk.Button(actions_frame, text="♻️ RELOAD ALL ASSETS", command=self._refresh_data).pack(side="left", padx=10)

    def _create_snapshot_cb(self):
        root_dir = Path(self.data_loader.base_dir)
        success, msg = create_snapshot(root_dir)
        if success:
            messagebox.showinfo("Snapshot Success", msg)
        else:
            messagebox.showerror("Snapshot Failed", msg)

    def _setup_health_tab(self):
        self.health_scroll = ScrollableCanvas(self.health_tab)
        self.health_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        self.health_container = self.health_scroll.get_container()
        
        ttk.Label(self.health_container, text="DATA INTEGRITY CHECK", style="Title.TLabel").pack(anchor="w")
        self.health_list = ttk.Frame(self.health_container)
        self.health_list.pack(fill="x", pady=10)

    def _refresh_data(self):
        # Refresh components
        self.char_explorer.refresh()
        self.tag_analyzer.refresh()
        self._run_health_checks()
        
        # Update Overview Stats
        char_count = len(self.char_explorer.all_chars)
        outfit_count = len(self.data_loader.load_outfits())
        
        stats_text = f"Total Characters: {char_count}\n"
        stats_text += f"Total Collective Outfits: {outfit_count}\n"
        self.stats_label.config(text=stats_text)

    def _run_health_checks(self):
        """Scan data directories for inconsistencies."""
        for child in self.health_list.winfo_children():
            child.destroy()
            
        chars = self.char_explorer.all_chars
        char_dir = self.data_loader._find_characters_dir()
        
        issues = []
        
        # 1. Photo Check
        missing_photos = []
        for c in chars:
            photo_name = c.get("filename", "").replace(".md", ".png") # Conventional assuming 1:1
            # Actual check in character data
            # The character_summary script doesn't parse 'Photo' field explicitly except path
            # Let's check for the existence of the expected .png
            photo_path = char_dir / photo_name
            if not photo_path.exists():
                missing_photos.append(c["name"])
        
        if missing_photos:
            issues.append(f"⚠️ {len(missing_photos)} characters missing photo files.")
            for name in missing_photos[:5]:
                ttk.Label(self.health_list, text=f"  • Missing photo: {name}", style="Muted.TLabel").pack(anchor="w")
            if len(missing_photos) > 5:
                ttk.Label(self.health_list, text=f"  • ... and {len(missing_photos)-5} more", style="Muted.TLabel").pack(anchor="w")

        # 2. Tag Consistency
        # Load global tags for reference
        global_tags = set()
        tag_data = self.data_loader.load_categorized_tags()
        if tag_data:
            for cat_tags in tag_data.values():
                for t in cat_tags:
                    global_tags.add(t.lower())
        
        unregistered_tags = set()
        for c in chars:
            for t in c.get("tags", []):
                if t.lower() not in global_tags:
                    unregistered_tags.add(t)
        
        if unregistered_tags:
            issues.append(f"ℹ️ {len(unregistered_tags)} tags are not in the global tags.md reference.")
            ttk.Label(self.health_list, text=f"  • Unregistered: {', '.join(list(unregistered_tags)[:10])}", style="Muted.TLabel", wraplength=800).pack(anchor="w")

        # 3. Orphan Outfits Check
        # (Compare filenames in data/outfits/ with what's actually loadable)
        outfit_dir = Path(self.data_loader.base_dir) / "data" / "outfits"
        if outfit_dir.exists():
            files = list(outfit_dir.rglob("*.txt"))
            issues.append(f"✓ Scanned {len(files)} modular outfit files.")
        
        if not issues:
            ttk.Label(self.health_list, text="🌟 NO ISSUES FOUND! YOUR PROJECT IS IN GREAT SHAPE.", foreground="#4caf50", font=("Lexend", 10, "bold")).pack(pady=20)
        else:
            for issue in issues:
                ttk.Label(self.health_list, text=issue, font=("Lexend", 10, "bold")).pack(anchor="w", pady=(10, 0))
                
        self.health_scroll.update_scroll_region()

    def _apply_theme(self, theme):
        self.char_explorer.apply_theme(theme)
        self.tag_analyzer.apply_theme(theme)
        self.overview_scroll.apply_theme(theme)
        self.health_scroll.apply_theme(theme)
