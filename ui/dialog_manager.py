# -*- coding: utf-8 -*-
"""Dialog management for the application."""

import platform
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext

from typing import Callable, Optional

from config import WELCOME_MESSAGE


class DialogManager:
    """Manages application dialogs (welcome, about, error, shortcuts, etc).

    Provides centralized, consistent dialog creation and display.
    """

    def __init__(self, root: tk.Tk, preferences_manager):
        """Initialize dialog manager.

        Args:
            root: Tkinter root window
            preferences_manager: PreferencesManager instance
        """
        self.root = root
        self.prefs = preferences_manager

    def show_welcome(self) -> None:
        """Show welcome dialog for first-time users."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Welcome to Prompt Builder!")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        # Welcome text
        text = scrolledtext.ScrolledText(dialog, wrap="word", font=("Segoe UI", 10))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", WELCOME_MESSAGE)
        text.config(state="disabled")

        # Don't show again checkbox
        show_again_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(dialog, text="Don't show this again", variable=show_again_var)
        chk.pack(pady=(0, 10))

        def on_close():
            if show_again_var.get():
                self.prefs.set("show_welcome", False)
            dialog.destroy()

        ttk.Button(dialog, text="Get Started!", command=on_close).pack(pady=(0, 10))

        dialog.wait_window()

    def show_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        shortcuts = """
Keyboard Shortcuts

File Operations:
  Ctrl+Shift+S    Save Preset
  Ctrl+Shift+O    Load Preset

Editing:
  Ctrl+Z          Undo
  Ctrl+Y          Redo

View:
  Ctrl+G          Toggle Character Gallery
  Ctrl++          Increase Font Size
  Ctrl+-          Decrease Font Size
  Ctrl+0          Reset Font Size
  Alt+R           Randomize All

Preview Panel:
  Ctrl+C          Copy Prompt
  Ctrl+S          Save Prompt to File

Navigation:
  Tab             Navigate between fields
  Enter           Add character/Apply selection
  Del             Remove selected character
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def show_about(self) -> None:
        """Show about dialog."""
        about_text = f"""Prompt Builder
Version 2.0

A desktop application for building complex AI image prompts.

Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}
Platform: {platform.system()} {platform.release()}

© 2025 - Open Source
"""
        messagebox.showinfo("About Prompt Builder", about_text)

    def show_text_import(self, available_characters: list, on_success: Callable[[dict], None]) -> None:
        """Show dialog to import prompt configuration from text."""
        from utils.text_parser import TextParser

        dialog = tk.Toplevel(self.root)
        dialog.title("Import Prompt from Text")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Paste your prompt configuration below:", style="Bold.TLabel").pack(anchor="w", pady=(0, 5))
        
        help_text = "Supported formats:\n• [1] Name (Outfit, Pose)\n• [1] Name\\nOutfit: Name\\nPose: Name\\n...\n• 🎬 Scene description\\n📝 Interaction notes"
        ttk.Label(main_frame, text=help_text, style="Muted.TLabel", justify="left").pack(anchor="w", pady=(0, 10))

        text_area = scrolledtext.ScrolledText(main_frame, wrap="word", font=("Consolas", 10))
        text_area.pack(fill="both", expand=True, pady=5)
        text_area.focus_set()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        def do_import():
            raw_text = text_area.get("1.0", "end-1c").strip()
            if not raw_text:
                messagebox.showwarning("Empty Input", "Please paste some text to import.")
                return

            try:
                config = TextParser.parse_import_text(raw_text, available_characters)
                
                char_count = len(config.get("selected_characters", []))
                if char_count == 0 and not config.get("scene") and not config.get("notes"):
                    messagebox.showwarning("No Data Found", "Could not identify any characters, scenes, or notes in the text.")
                    return

                # Confirm with user
                summary = f"Detected:\n• {char_count} character(s)"
                if config.get("scene"): summary += "\n• Scene description"
                if config.get("notes"): summary += "\n• Interaction notes"
                summary += "\n\nApply this configuration? (This will overwrite current selection)"

                if messagebox.askyesno("Import Confirmation", summary, parent=dialog):
                    on_success(config)
                    dialog.destroy()
            except Exception as e:
                from utils import logger
                logger.exception("Error during text import")
                messagebox.showerror("Import Error", f"Failed to parse text: {e}", parent=dialog)

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=(5, 0))
        ttk.Button(btn_frame, text="Import Configuration", command=do_import).pack(side="right")

        dialog.wait_window()

    def show_characters_summary(self, callback: Optional[Callable[[], str]] = None) -> None:
        """Show character appearances summary with an interactive explorer."""
        try:
            from pathlib import Path
            from utils.character_summary import generate_character_data, generate_summary

            project_root = Path(__file__).resolve().parents[1]
            data_chars = project_root / "data" / "characters"
            legacy_chars = project_root / "characters"
            chars_dir = data_chars if data_chars.exists() else (legacy_chars if legacy_chars.exists() else None)

            if not chars_dir:
                self.show_error("Error", "Character directory not found.")
                return

            # Load raw data
            all_chars = generate_character_data(chars_dir)
            
            # Create a dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Character Explorer & Summary")
            dialog.geometry("1100x750")
            dialog.minsize(900, 600)

            # --- Layout ---
            # Top: Search and Stats
            top_frame = ttk.Frame(dialog, padding=(10, 10, 10, 0))
            top_frame.pack(fill="x")

            # Middle: Paned window for list and detail
            paned = ttk.PanedWindow(dialog, orient="horizontal")
            paned.pack(fill="both", expand=True, padx=10, pady=10)

            # Left: Character list
            list_side = ttk.Frame(paned)
            paned.add(list_side, weight=1)

            # Right: Detail view
            detail_side = ttk.Frame(paned)
            paned.add(detail_side, weight=2)

            # --- Search & Filters ---
            search_frame = ttk.Frame(top_frame)
            search_frame.pack(side="left", fill="x", expand=True)

            ttk.Label(search_frame, text="🔍 Search:").pack(side="left")
            search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=search_var)
            search_entry.pack(side="left", fill="x", expand=True, padx=5)

            ttk.Label(search_frame, text="🏷️ Tag:").pack(side="left", padx=(10, 0))
            tag_var = tk.StringVar(value="All")
            # Get all unique tags
            all_tags = set()
            for c in all_chars:
                for t in c.get("tags", []):
                    all_tags.add(t)
            tag_combo = ttk.Combobox(search_frame, textvariable=tag_var, values=["All"] + sorted(list(all_tags)), state="readonly", width=15)
            tag_combo.pack(side="left", padx=5)

            fav_only_var = tk.BooleanVar(value=False)
            fav_chk = ttk.Checkbutton(search_frame, text="⭐ Favorites Only", variable=fav_only_var)
            fav_chk.pack(side="left", padx=10)

            # --- Stats ---
            stats_frame = ttk.Frame(top_frame)
            stats_frame.pack(side="right")
            stats_label = ttk.Label(stats_frame, text=f"Total: {len(all_chars)}", font=(None, 9, "bold"))
            stats_label.pack(side="right")

            # --- List Side ---
            list_header = ttk.Frame(list_side)
            list_header.pack(fill="x", pady=(0, 5))
            ttk.Label(list_header, text="Characters", font=(None, 10, "bold")).pack(side="left")

            char_listbox = tk.Listbox(list_side, font=("Segoe UI", 10), selectmode="single", exportselection=False)
            char_listbox.pack(side="left", fill="both", expand=True)
            
            list_scroll = ttk.Scrollbar(list_side, orient="vertical", command=char_listbox.yview)
            list_scroll.pack(side="right", fill="y")
            char_listbox.config(yscrollcommand=list_scroll.set)

            # --- Detail Side ---
            detail_notebook = ttk.Notebook(detail_side)
            detail_notebook.pack(fill="both", expand=True)

            # Tab 1: Formatted Preview
            preview_tab = ttk.Frame(detail_notebook)
            detail_notebook.add(preview_tab, text="📄 Details")

            # Tab 2: Full Text Summary (the original feature)
            full_text_tab = ttk.Frame(detail_notebook)
            detail_notebook.add(full_text_tab, text="📝 Full Summary")

            # --- Preview Tab Content ---
            preview_scroll_frame = ttk.Frame(preview_tab)
            preview_scroll_frame.pack(fill="both", expand=True)

            preview_scroll = ttk.Scrollbar(preview_scroll_frame)
            preview_scroll.pack(side="right", fill="y")

            preview_text = tk.Text(preview_scroll_frame, wrap="word", yscrollcommand=preview_scroll.set, font=("Segoe UI", 10), state="disabled", padx=15, pady=15)
            preview_text.pack(side="left", fill="both", expand=True)
            preview_scroll.config(command=preview_text.yview)

            # Control buttons for preview
            preview_btns = ttk.Frame(preview_tab)
            preview_btns.pack(fill="x", pady=5)
            
            fav_btn_var = tk.StringVar(value="☆ Favorite")
            fav_btn = ttk.Button(preview_btns, textvariable=fav_btn_var)
            fav_btn.pack(side="left", padx=10)

            copy_btn = ttk.Button(preview_btns, text="📋 Copy Details", command=lambda: self._copy_detail(preview_text))
            copy_btn.pack(side="left")

            # --- Full Text Tab Content ---
            full_text_frame = ttk.Frame(full_text_tab)
            full_text_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            full_text_scroll = ttk.Scrollbar(full_text_frame)
            full_text_scroll.pack(side="right", fill="y")
            
            full_text_widget = tk.Text(full_text_frame, wrap="word", yscrollcommand=full_text_scroll.set, font=("Consolas", 10), state="disabled")
            full_text_widget.pack(side="left", fill="both", expand=True)
            full_text_scroll.config(command=full_text_widget.yview)

            # Filter options for full summary
            full_filter_frame = ttk.Frame(full_text_tab)
            full_filter_frame.pack(fill="x", pady=5)
            
            full_include_base = tk.BooleanVar(value=True)
            ttk.Checkbutton(full_filter_frame, text="Base Outfit", variable=full_include_base).pack(side="left", padx=5)
            
            full_include_style = tk.BooleanVar(value=True)
            ttk.Checkbutton(full_filter_frame, text="Style Notes", variable=full_include_style).pack(side="left", padx=5)

            def refresh_full_summary(*args):
                new_sum = generate_summary(
                    chars_dir, 
                    include_base=full_include_base.get(), 
                    include_style=full_include_style.get(),
                    include_summary=True,
                    include_tags=True
                )
                full_text_widget.config(state="normal")
                full_text_widget.delete("1.0", "end")
                full_text_widget.insert("1.0", new_sum)
                full_text_widget.config(state="disabled")

            # --- Logic ---
            filtered_chars = []

            def update_list(*args):
                nonlocal filtered_chars
                char_listbox.delete(0, tk.END)
                search = search_var.get().lower()
                tag = tag_var.get()
                fav_only = fav_only_var.get()
                
                filtered_chars = []
                favs = self.prefs.get("favorite_characters", []) if self.prefs else []

                for c in all_chars:
                    # Search filter
                    if search and search not in c["name"].lower() and search not in c["appearance"].lower():
                        continue
                    # Tag filter
                    if tag != "All" and tag not in c.get("tags", []):
                        continue
                    # Favorite filter
                    is_fav = c["name"] in favs
                    if fav_only and not is_fav:
                        continue
                        
                    filtered_chars.append(c)
                    prefix = "★ " if is_fav else "  "
                    char_listbox.insert(tk.END, f"{prefix}{c['name']}")
                
                stats_label.config(text=f"Showing: {len(filtered_chars)} / {len(all_chars)}")
                if filtered_chars:
                    char_listbox.selection_set(0)
                    on_select()

            def on_select(event=None):
                selection = char_listbox.curselection()
                if not selection:
                    return
                
                idx = selection[0]
                char = filtered_chars[idx]
                
                # Update Preview
                preview_text.config(state="normal")
                preview_text.delete("1.0", "end")
                
                # Use tags for formatting
                preview_text.insert("end", f"{char['name']}\n", "title")
                preview_text.insert("end", "=" * 40 + "\n\n", "separator")
                
                if char.get("summary"):
                    preview_text.insert("end", "SUMMARY:\n", "section_label")
                    preview_text.insert("end", f"{char['summary']}\n\n")

                preview_text.insert("end", "APPEARANCE:\n", "section_label")
                preview_text.insert("end", f"{char['appearance']}\n\n")
                
                if char.get("base_outfit"):
                    preview_text.insert("end", "BASE OUTFIT:\n", "section_label")
                    preview_text.insert("end", f"{char['base_outfit']}\n\n")
                
                if char.get("style_notes"):
                    preview_text.insert("end", "STYLE NOTES:\n", "section_label")
                    preview_text.insert("end", f"{char['style_notes']}\n\n")
                
                if char.get("tags"):
                    preview_text.insert("end", "TAGS:\n", "section_label")
                    preview_text.insert("end", f"{', '.join(char['tags'])}\n\n")

                if char.get("signature_color"):
                    preview_text.insert("end", "SIGNATURE COLOR:\n", "section_label")
                    sig_color = char['signature_color']
                    preview_text.insert("end", f"{sig_color}  ", "normal")
                    # Add a colored tag
                    preview_text.tag_configure("sig_bg", background=sig_color, foreground="white" if not sig_color.upper().startswith("#F") and not sig_color.upper().startswith("#E") else "black", font=("Consolas", 10, "bold"))
                    preview_text.insert("end", "   COLOR   ", "sig_bg")
                    preview_text.insert("end", "\n")

                preview_text.config(state="disabled")
                
                # Update Favorite Button
                favs = self.prefs.get("favorite_characters", []) if self.prefs else []
                if char["name"] in favs:
                    fav_btn_var.set("★ Unfavorite")
                else:
                    fav_btn_var.set("☆ Favorite")

            def toggle_fav():
                selection = char_listbox.curselection()
                if not selection:
                    return
                idx = selection[0]
                char = filtered_chars[idx]
                
                if self.prefs:
                    self.prefs.toggle_favorite("favorite_characters", char["name"])
                    # Refresh list while preserving selection
                    update_list()
                    char_listbox.selection_set(idx)
                    on_select()

            # --- Bindings ---
            search_var.trace_add("write", update_list)
            tag_var.trace_add("write", update_list)
            fav_only_var.trace_add("write", update_list)
            char_listbox.bind("<<ListboxSelect>>", on_select)
            fav_btn.config(command=toggle_fav)
            
            full_include_base.trace_add("write", refresh_full_summary)
            full_include_style.trace_add("write", refresh_full_summary)

            # --- Apply Theme ---
            if hasattr(self.root, "theme_manager"):
                theme = self.root.theme_manager.themes.get(self.root.theme_manager.current_theme)
                if theme:
                    self.root.theme_manager.apply_preview_theme(preview_text, theme)
                    self.root.theme_manager.apply_preview_theme(full_text_widget, theme)

            # Initialize
            update_list()
            refresh_full_summary()

            # Close button
            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

        except Exception as e:
            from utils import logger
            logger.exception("Error in characters summary explorer")
            self.show_error("Error", f"Failed to open character explorer: {e}")

    def show_tag_summary(self) -> None:
        """Show tag distribution summary across all characters."""
        try:
            from logic.data_loader import DataLoader
            from ui.widgets import ScrollableCanvas
            
            loader = DataLoader()
            chars = loader.load_characters()
            categorized_map = loader.load_categorized_tags()
            
            if not chars:
                self.show_error("Error", "No character data found.")
                return

            # Count tag frequencies and map characters
            tag_counts = {}
            tag_to_chars = {}
            total_chars = len(chars)
            
            for name, data in chars.items():
                char_tags = data.get("tags") or []
                if isinstance(char_tags, str):
                    char_tags = [t.strip().lower() for t in char_tags.split(",") if t.strip()]
                else:
                    char_tags = [str(t).strip().lower() for t in char_tags if t]
                
                for t in char_tags:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
                    if t not in tag_to_chars:
                        tag_to_chars[t] = []
                    tag_to_chars[t].append(name)

            dialog = tk.Toplevel(self.root)
            dialog.title("Tag Distribution Summary")
            dialog.geometry("600x700")
            dialog.minsize(500, 500)
            dialog.transient(self.root)

            main_frame = ttk.Frame(dialog, padding=15)
            main_frame.pack(fill="both", expand=True)

            ttk.Label(main_frame, text="Tag Distribution", style="Title.TLabel").pack(pady=(0, 5))
            ttk.Label(main_frame, text=f"Stats based on {total_chars} characters", font=(None, 9, "italic")).pack(pady=(0, 15))

            # Scrollable area
            scroll_container = ScrollableCanvas(main_frame)
            scroll_container.pack(fill="both", expand=True)
            
            container = scroll_container.get_container()
            container.columnconfigure(0, weight=1)

            # Category priorities
            priority = ["Demographics", "Body Type", "Style", "Vibe", "Other"]
            
            # Map used tags to categories
            tag_to_cat = {}
            for cat, tag_list in categorized_map.items():
                for t in tag_list:
                    tag_to_cat[t.lower()] = cat

            row = 0
            for cat in priority:
                # Get tags for this category
                cat_tag_counts = []
                for tag, count in tag_counts.items():
                    if tag_to_cat.get(tag, "Other") == cat:
                        cat_tag_counts.append((tag, count))
                
                if not cat_tag_counts:
                    continue
                    
                # Header for category
                cat_frame = ttk.LabelFrame(container, text=f" {cat.upper()} ", padding=10)
                cat_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=8)
                cat_frame.columnconfigure(0, weight=1)
                
                cat_tag_counts.sort(key=lambda x: x[1], reverse=True)
                
                # Get theme accent color safely
                accent_color = "blue"
                if hasattr(self.root, "theme_manager") and self.root.theme_manager:
                    current = self.root.theme_manager.current_theme
                    accent_color = self.root.theme_manager.themes.get(current, {}).get("accent", "blue")

                for tag, count in cat_tag_counts:
                    item_frame = ttk.Frame(cat_frame)
                    item_frame.pack(fill="x", pady=2)
                    
                    percent = (count / total_chars) * 100
                    
                    # Tag name (Interactive)
                    tag_label = ttk.Label(
                        item_frame, 
                        text=tag, 
                        font=("Segoe UI", 10, "underline"),
                        foreground=accent_color,
                        cursor="hand2"
                    )
                    tag_label.pack(side="left")
                    
                    # Bind character list popup
                    tag_label.bind("<Button-1>", lambda e, t=tag, c=tag_to_chars.get(tag, []): self._show_tag_characters(t, c))
                    
                    # Count and bar
                    stats_label = ttk.Label(item_frame, text=f"{count} ({percent:.1f}%)", foreground="gray")
                    stats_label.pack(side="right")
                    
                    # Visual bar
                    bar_container = tk.Frame(item_frame, height=4, bg="#eeeeee")
                    bar_container.pack(side="right", padx=10, fill="x", expand=True)
                    
                    colors = {
                        "Demographics": "#4a90e2", "Body Type": "#50e3c2", "Style": "#f5a623", 
                        "Vibe": "#bd10e0", "Other": "#9b9b9b"
                    }
                    bar_color = colors.get(cat, "#9b9b9b")
                    
                    canvas = tk.Canvas(bar_container, height=4, highlightthickness=0, bg="#eeeeee", width=150)
                    canvas.pack(fill="both")
                    canvas.create_rectangle(0, 0, int(150 * (count/total_chars)), 4, fill=bar_color, outline="")

                row += 1

            scroll_container.update_scroll_region()
            ttk.Button(main_frame, text="Close", command=dialog.destroy).pack(pady=(15, 0))

        except Exception as e:
            from utils import logger
            logger.exception("Error showing tag distribution")
            self.show_error("Error", f"Failed to generate tag distribution: {e}")

    def show_outfits_summary(self) -> None:
        """Show outfit library summary with filtering."""
        try:
            from utils.outfit_summary import generate_consolidated_outfit_data
            
            # Load consolidated data
            outfit_data = generate_consolidated_outfit_data()
            
            if not outfit_data:
                self.show_error("Error", "No outfit data found.")
                return

            dialog = tk.Toplevel(self.root)
            dialog.title("Outfit Library Explorer")
            dialog.geometry("1000x700")
            dialog.minsize(800, 500)
            dialog.transient(self.root)

            # --- Layout ---
            # Top: Legend
            top_frame = ttk.Frame(dialog, padding=10)
            top_frame.pack(fill="x")
            
            ttk.Label(top_frame, text="Legend: ", font=("Segoe UI", 9, "bold")).pack(side="left")
            ttk.Label(top_frame, text="🎨 = Color Scheme  ", foreground="blue").pack(side="left")
            ttk.Label(top_frame, text="✨ = Signature Color", foreground="#d35400").pack(side="left")

            # Main content: Paned window
            paned = ttk.PanedWindow(dialog, orient="horizontal")
            paned.pack(fill="both", expand=True, padx=10, pady=5)

            # Left: Treeview
            tree_frame = ttk.Frame(paned)
            paned.add(tree_frame, weight=1)
            
            tree_scroll = ttk.Scrollbar(tree_frame)
            tree_scroll.pack(side="right", fill="y")
            
            tree = ttk.Treeview(tree_frame, selectmode="browse", yscrollcommand=tree_scroll.set)
            tree.pack(side="left", fill="both", expand=True)
            tree_scroll.config(command=tree.yview)
            
            tree.heading("#0", text="Categories & Outfits", anchor="w")

            # Right: Detail view
            detail_frame = ttk.Frame(paned, padding=10)
            paned.add(detail_frame, weight=2)
            
            detail_header = ttk.Label(detail_frame, text="Select an outfit", font=("Segoe UI", 12, "bold"), wraplength=400)
            detail_header.pack(fill="x", pady=(0, 10))
            
            detail_text = tk.Text(detail_frame, wrap="word", font=("Segoe UI", 10), state="disabled", height=15)
            detail_text.pack(fill="both", expand=True)

            # Populate Tree
            for cat_name in sorted(outfit_data.keys()):
                cat_id = tree.insert("", "end", text=cat_name, open=True)
                
                outfits = outfit_data[cat_name]
                for out_name in sorted(outfits.keys()):
                    data = outfits[out_name]
                    
                    # Build label with indicators
                    label = out_name
                    if data["has_color_scheme"]:
                        label += " 🎨"
                    if data["has_signature"]:
                        label += " ✨"
                        
                    outfit_id = tree.insert(cat_id, "end", text=label, values=("outfit", cat_name, out_name))
                    
                    # Add variations as children
                    variations = data["variations"]
                    for mod in ["F", "M", "H"]:
                        if mod in variations:
                            mod_label = "Female" if mod == "F" else "Male" if mod == "M" else "Hijabi"
                            tree.insert(outfit_id, "end", text=f"({mod}) {mod_label}", values=("variation", cat_name, out_name, mod))

            def on_tree_select(event):
                sel = tree.selection()
                if not sel: return
                
                item = tree.item(sel[0])
                vals = item["values"]
                
                if not vals: return # Category folder
                
                type_ = vals[0]
                
                if type_ == "outfit":
                    cat, name = vals[1], vals[2]
                    data = outfit_data[cat][name]
                    
                    detail_header.config(text=name)
                    
                    # Show all variations in text
                    detail_text.config(state="normal")
                    detail_text.delete("1.0", "end")
                    
                    if data["has_color_scheme"]:
                        detail_text.insert("end", "🎨 Supports Team Colors\n", "info")
                    if data["has_signature"]:
                        detail_text.insert("end", "✨ Supports Signature Color\n", "info")
                    if data["has_color_scheme"] or data["has_signature"]:
                        detail_text.insert("end", "\n")
                        
                    detail_text.tag_configure("info", foreground="gray", font=("Segoe UI", 9, "italic"))
                    detail_text.tag_configure("header", font=("Segoe UI", 10, "bold"))

                    for mod in ["F", "M", "H"]:
                        if mod in data["variations"]:
                            mod_label = "Female" if mod == "F" else "Male" if mod == "M" else "Hijabi"
                            detail_text.insert("end", f"--- {mod_label} ({mod})---\n", "header")
                            detail_text.insert("end", f"{data['variations'][mod]}\n\n")
                            
                    detail_text.config(state="disabled")
                    
                elif type_ == "variation":
                    cat, name, mod = vals[1], vals[2], vals[3]
                    desc = outfit_data[cat][name]["variations"][mod]
                    mod_label = "Female" if mod == "F" else "Male" if mod == "M" else "Hijabi"
                    
                    detail_header.config(text=f"{name} - {mod_label}")
                    detail_text.config(state="normal")
                    detail_text.delete("1.0", "end")
                    detail_text.insert("1.0", desc)
                    detail_text.config(state="disabled")

            tree.bind("<<TreeviewSelect>>", on_tree_select)
            
            # Close button
            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

        except Exception as e:
            from utils import logger
            logger.exception("Error in outfit summary explorer")
            self.show_error("Error", f"Failed to open outfit explorer: {e}")

    def _show_tag_characters(self, tag: str, characters: list) -> None:
        """Show a small popup listing characters with a specific tag."""
        popup = tk.Toplevel(self.root)
        popup.title(f"Characters with tag: {tag}")
        popup.geometry("350x400")
        popup.transient(self.root)
        
        main_frame = ttk.Frame(popup, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text=f"Tag: {tag}", style="Bold.TLabel").pack(pady=(0, 10))
        
        # Scrollable list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        lb = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 10))
        lb.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=lb.yview)
        
        for char in sorted(characters):
            lb.insert(tk.END, f"  {char}")
            
        ttk.Button(main_frame, text="Close", command=popup.destroy).pack(pady=(10, 0))

    def show_color_schemes_summary(self) -> None:
        """Show a visual summary of all available team color schemes."""
        try:
            from ui.widgets import ScrollableCanvas
            from logic.data_loader import DataLoader
            
            # Load schemes
            loader = DataLoader()
            schemes = loader.load_color_schemes()
            
            if not schemes:
                self.show_error("Error", "No color schemes found.")
                return

            dialog = tk.Toplevel(self.root)
            dialog.title("Team Colors Summary")
            dialog.geometry("800x600")
            dialog.minsize(600, 400)
            dialog.transient(self.root)

            # Main container
            main_frame = ttk.Frame(dialog, padding=10)
            main_frame.pack(fill="both", expand=True)

            ttk.Label(main_frame, text="Available Team Colors", style="Title.TLabel").pack(pady=(0, 10))

            # Scrollable area
            scroll_container = ScrollableCanvas(main_frame)
            scroll_container.pack(fill="both", expand=True)
            
            container = scroll_container.get_container()
            container.columnconfigure(0, weight=1)

            # Grid of schemes
            # We'll use a grid with 2 columns if window is wide enough, but for simplicity 
            # let's start with a list of wide rows.
            
            row = 0
            for name in sorted(schemes.keys()):
                scheme = schemes[name]
                
                # Each scheme gets a frame
                item_frame = ttk.LabelFrame(container, text=name, padding=10)
                item_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
                item_frame.columnconfigure(1, weight=1)
                
                # Color swatches
                swatch_frame = ttk.Frame(item_frame)
                swatch_frame.grid(row=0, column=0, sticky="w")
                
                def is_valid_color(c):
                    if not c or c.startswith("{"): return False
                    return True

                for label, key in [("Primary", "primary_color"), ("Secondary", "secondary_color"), ("Accent", "accent")]:
                    val = scheme.get(key)
                    if is_valid_color(val):
                        f = ttk.Frame(swatch_frame)
                        f.pack(side="left", padx=10)
                        try:
                            # Color box
                            swatch = tk.Label(f, width=4, height=2, bg=val, relief="solid", borderwidth=1)
                            swatch.pack()
                            ttk.Label(f, text=label, font=("Segoe UI", 8)).pack()
                            ttk.Label(f, text=val, font=("Consolas", 8), foreground="gray").pack()
                        except Exception:
                            pass
                
                # Team name
                team_name = scheme.get("team", name)
                team_label = ttk.Label(item_frame, text=f"Team Name: {team_name}", font=("Segoe UI", 10, "bold"))
                team_label.grid(row=0, column=1, sticky="e", padx=10)
                
                row += 1

            # Update scroll region
            scroll_container.update_scroll_region()

            # Close button at bottom
            ttk.Button(main_frame, text="Close", command=dialog.destroy).pack(pady=10)

        except Exception as e:
            from utils import logger
            logger.exception("Error in color schemes summary")
            self.show_error("Error", f"Failed to open color schemes summary: {e}")

    def _copy_detail(self, text_widget):
        """Copy text from widget to clipboard."""
        try:
            content = text_widget.get("1.0", "end-1c")
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.show_info("Copied", "Character details copied to clipboard.")
        except Exception:
            pass

        except Exception as e:
            from utils import logger

            logger.exception("Auto-captured exception")
            self.show_error("Error", f"Failed to generate character summary:\n{str(e)}")

    def show_error(self, title: str, error_msg: str, friendly: bool = True) -> None:
        """Show error dialog with optional user-friendly message conversion.

        Args:
            title: Error dialog title
            error_msg: Error message
            friendly: Whether to convert technical errors to user-friendly messages
        """
        if friendly:
            error_msg = self._make_user_friendly(error_msg)

        messagebox.showerror(title, error_msg)

    def show_info(self, title: str, message: str) -> None:
        """Show info dialog.

        Args:
            title: Dialog title
            message: Info message
        """
        # Prefer transient, non-blocking notifications when available:
        # 1) Toast manager on the root window
        # 2) Main window status bar via `_update_status`
        # 3) Fallback to modal messagebox
        root = getattr(self, "root", None)
        try:
            if root is not None and hasattr(root, "toasts"):
                try:
                    # Use 'info' level for neutral messages
                    root.toasts.notify(message, "info", 3000)
                    return
                except Exception:
                    from utils import logger

                    logger.exception("Auto-captured exception")
                    pass
            if root is not None and hasattr(root, "_update_status"):
                try:
                    root._update_status(message)
                    return
                except Exception:
                    from utils import logger

                    logger.exception("Auto-captured exception")
                    pass
        except Exception:
            from utils import logger

            logger.exception("Auto-captured exception")
            # Defensive: if accessing root fails, fall through to modal
            pass

        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str) -> None:
        """Show warning dialog.

        Args:
            title: Dialog title
            message: Warning message
        """
        messagebox.showwarning(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        """Show yes/no confirmation dialog.

        Args:
            title: Dialog title
            message: Question message

        Returns:
            True if user clicked Yes, False otherwise
        """
        return messagebox.askyesno(title, message)

    def ask_ok_cancel(self, title: str, message: str) -> bool:
        """Show OK/Cancel confirmation dialog.

        Args:
            title: Dialog title
            message: Question message

        Returns:
            True if user clicked OK, False otherwise
        """
        return messagebox.askokcancel(title, message)

    def _make_user_friendly(self, error_msg: str) -> str:
        """Convert technical error messages to user-friendly text.

        Args:
            error_msg: Technical error message

        Returns:
            User-friendly error message
        """
        if "FileNotFoundError" in error_msg or "No such file" in error_msg:
            return "File not found. Try clicking 'Reload Data' from the menu."
        elif "PermissionError" in error_msg:
            return "Permission denied. Check file permissions and try again."
        elif "JSONDecodeError" in error_msg:
            return "Invalid file format. The file may be corrupted."
        elif "characters/" in error_msg:
            return "Error loading character files. Check the characters folder."

        return error_msg
