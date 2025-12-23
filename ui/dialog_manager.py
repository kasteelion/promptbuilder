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
                    preview_text.insert("end", f"{', '.join(char['tags'])}\n")

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
