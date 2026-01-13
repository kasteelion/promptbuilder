# -*- coding: utf-8 -*-
"""Dialog management for the application."""

import tkinter as tk
from tkinter import messagebox, ttk

from typing import Callable, Optional

from core.config import WELCOME_MESSAGE


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
        self.active_dialogs = [] # Track open dialogs for theme updates

    def _register_dialog(self, dialog, apply_theme_fn=None):
        """Helper to track open dialogs."""
        self.active_dialogs.append({"window": dialog, "apply_theme": apply_theme_fn})
        dialog.bind("<Destroy>", lambda e: self._unregister_dialog(dialog))

    def _unregister_dialog(self, dialog):
        self.active_dialogs = [d for d in self.active_dialogs if d["window"] != dialog]

    def apply_theme(self, theme):
        """Propagate theme changes to all open dialogs."""
        for d in self.active_dialogs:
            if d["apply_theme"]:
                try:
                    d["apply_theme"](theme)
                except Exception:
                    pass

    def show_dashboard(self, data_loader, theme_manager, initial_tab: int = 0) -> None:
        """Show the consolidated Project Dashboard."""
        try:
            from ui.dashboard import DashboardDialog
            dash = DashboardDialog(self.root, data_loader, theme_manager, self.prefs)
            if initial_tab > 0:
                dash.nb.select(initial_tab)
        except Exception as e:
            self.show_error("Error", f"Failed to open Dashboard: {e}")

    def show_info(self, title: str, message: str) -> None:
        """Show an information dialog."""
        messagebox.showinfo(title, message, parent=self.root)

    def show_error(self, title: str, message: str) -> None:
        """Show an error dialog."""
        messagebox.showerror(title, message, parent=self.root)

    def ask_yes_no(self, title: str, message: str) -> bool:
        """Show a yes/no confirmation dialog."""
        return messagebox.askyesno(title, message, parent=self.root)

    def show_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("KEYBOARD SHORTCUTS")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        
        if hasattr(self.root, "theme_manager"):
            self.root.theme_manager.theme_toplevel(dialog)

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="APPLICATION SHORTCUTS", style="Title.TLabel").pack(pady=(0, 15))

        shortcuts = [
            ("FILE", [
                ("Ctrl + S", "Save Preset"),
                ("Ctrl + O", "Load Preset"),
                ("Ctrl + Shift + S", "Export Config"),
                ("Ctrl + Shift + O", "Import Config"),
            ]),
            ("EDIT", [
                ("Ctrl + Z", "Undo"),
                ("Ctrl + Y", "Redo"),
                ("Ctrl + G", "Toggle Gallery"),
                ("Alt + R", "Randomize All"),
            ]),
            ("VIEW", [
                ("Ctrl + Plus / =", "Increase Font Size"),
                ("Ctrl + Minus", "Decrease Font Size"),
                ("Ctrl + 0", "Reset Font Size"),
            ])
        ]

        for category, items in shortcuts:
            ttk.Label(main_frame, text=category, style="Bold.TLabel").pack(anchor="w", pady=(10, 5))
            for key, desc in items:
                row = ttk.Frame(main_frame)
                row.pack(fill="x", pady=2)
                ttk.Label(row, text=key, width=15).pack(side="left")
                ttk.Label(row, text=desc, style="Muted.TLabel").pack(side="left")

        ttk.Button(main_frame, text="CLOSE", command=dialog.destroy).pack(side="bottom", pady=10)

    def show_about(self) -> None:
        """Show about dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("ABOUT PROMPT BUILDER")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        
        if hasattr(self.root, "theme_manager"):
            self.root.theme_manager.theme_toplevel(dialog)

        main_frame = ttk.Frame(dialog, padding=30)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="PROMPT BUILDER", font=("Lexend", 18, "bold")).pack(pady=(0, 5))
        ttk.Label(main_frame, text="v2.5.0", style="Muted.TLabel").pack(pady=(0, 20))

        about_text = (
            "A professional tool for creating complex, multi-character prompts "
            "with consistent identity and outfit management.\n\n"
            "Built with Python and Tkinter."
        )
        
        lbl = ttk.Label(main_frame, text=about_text, wraplength=350, justify="center")
        lbl.pack(pady=10)

        ttk.Label(main_frame, text="© 2025 PromptBuilder Team", style="Muted.TLabel").pack(pady=(20, 0))
        
        ttk.Button(main_frame, text="CLOSE", command=dialog.destroy).pack(side="bottom", pady=10)

    def show_text_import(self, available_chars: list, on_success: callable) -> None:
        """Show natural language text import dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("IMPORT FROM TEXT")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()

        if hasattr(self.root, "theme_manager"):
            self.root.theme_manager.theme_toplevel(dialog)

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="PASTE PROMPT SUMMARY OR LLM BLOCK:", style="Title.TLabel").pack(anchor="w", pady=(0, 10))
        
        # Text Area
        text_frame = ttk.Frame(main_frame, style="TFrame")
        text_frame.pack(fill="both", expand=True, pady=5)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        import_text = tk.Text(text_frame, wrap="word", font=("Lexend", 10), highlightthickness=0, borderwidth=0)
        import_text.grid(row=0, column=0, sticky="nsew")
        
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=import_text.yview, style="Themed.Vertical.TScrollbar")
        scroll.grid(row=0, column=1, sticky="ns")
        import_text.configure(yscrollcommand=scroll.set)

        help_text = "Supported: App summaries, interaction templates, and structured LLM config blocks."
        ttk.Label(main_frame, text=help_text, style="Muted.TLabel").pack(anchor="w", pady=(10, 0))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(15, 0))

        def do_import():
            raw_text = import_text.get("1.0", "end-1c").strip()
            if not raw_text:
                return
            
            from utils.text_parser import TextParser
            try:
                config = TextParser.parse_import_text(raw_text, available_chars)
                if config["selected_characters"]:
                    on_success(config)
                    dialog.destroy()
                else:
                    self.show_error("Import Error", "No valid characters found in the provided text.")
            except Exception as e:
                self.show_error("Import Error", f"Failed to parse text: {str(e)}")

        ttk.Button(btn_frame, text="IMPORT", command=do_import, style="TButton").pack(side="right")
        ttk.Button(btn_frame, text="CANCEL", command=dialog.destroy).pack(side="right", padx=10)

        def _apply(t):
            self.root.theme_manager.apply_text_widget_theme(import_text, t)
            
        self._register_dialog(dialog, _apply)
        _apply(self.root.theme_manager.themes.get(self.root.theme_manager.current_theme, {}))

    def show_llm_content_creation(self, ctx) -> None:
        """Show segmented LLM prompts for creating new application content."""
        from utils.llm_export import get_content_creation_prompts

        dialog = tk.Toplevel(self.root)
        dialog.title("LLM CONTENT CREATION GUIDE")
        dialog.geometry("900x750")
        dialog.transient(self.root)
        dialog.grab_set()

        if hasattr(self.root, "theme_manager"):
            self.root.theme_manager.theme_toplevel(dialog)

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="SELECT A CONTENT CATEGORY TO GENERATE PROMPTS:", style="Title.TLabel").pack(anchor="w", pady=(0, 15))

        prompts = get_content_creation_prompts(ctx)
        
        # Notebook for categories
        nb = ttk.Notebook(main_frame, style="TNotebook")
        nb.pack(fill="both", expand=True)

        text_widgets = {}

        for category, text in prompts.items():
            tab = ttk.Frame(nb, style="TFrame")
            nb.add(tab, text=category.upper())
            
            t_frame = ttk.Frame(tab, style="TFrame", padding=10)
            t_frame.pack(fill="both", expand=True)
            t_frame.columnconfigure(0, weight=1)
            t_frame.rowconfigure(0, weight=1)

            txt = tk.Text(t_frame, wrap="word", font=("Lexend", 9), highlightthickness=0, borderwidth=0)
            txt.grid(row=0, column=0, sticky="nsew")
            
            sc = ttk.Scrollbar(t_frame, orient="vertical", command=txt.yview, style="Themed.Vertical.TScrollbar")
            sc.grid(row=0, column=1, sticky="ns")
            txt.configure(yscrollcommand=sc.set)
            
            txt.insert("1.0", text)
            txt.config(state="disabled")
            text_widgets[category] = txt

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(15, 0))

        def copy_current():
            current_tab = nb.tab(nb.select(), "text").title()
            # Handle the title casing difference
            for cat, text in prompts.items():
                if cat.upper() == current_tab.upper():
                    self.root.clipboard_clear()
                    self.root.clipboard_append(text)
                    self.show_info("Copied", f"{cat} prompt copied to clipboard!")
                    break

        ttk.Button(btn_frame, text="📋 COPY CURRENT TAB", command=copy_current).pack(side="right")
        ttk.Button(btn_frame, text="CLOSE", command=dialog.destroy).pack(side="right", padx=10)

        def _apply(t):
            for tw in text_widgets.values():
                self.root.theme_manager.apply_text_widget_theme(tw, t)
            
        self._register_dialog(dialog, _apply)
        _apply(self.root.theme_manager.themes.get(self.root.theme_manager.current_theme, {}))

    def show_outfits_summary(self, data_loader=None, on_reload=None) -> None:
        """Show the Asset Manager (replacing Outfits Summary)."""
        try:
            from ui.asset_editor import AssetEditorDialog
            
            if not data_loader:
                # Attempt to find data_loader on root if not provided
                if hasattr(self.root, "data_loader"):
                    data_loader = self.root.data_loader
                else:
                    messagebox.showerror("Error", "Data Loader not provided to Asset Manager.")
                    return

            tm = getattr(self.root, "theme_manager", None)
            
            AssetEditorDialog(self.root, data_loader, tm, on_reload_callback=on_reload)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Asset Manager:\n{e}")

    def show_color_schemes_summary(self) -> None:
        """Show color schemes summary dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("COLOR SCHEMES CATALOG")
        dialog.geometry("600x700")
        dialog.transient(self.root)
        
        if hasattr(self.root, "theme_manager"):
            self.root.theme_manager.theme_toplevel(dialog)

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="AVAILABLE TEAM COLOR SCHEMES", style="Title.TLabel").pack(pady=(0, 15))

        # Use canvas for scrollable list of schemes
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Load schemes
        from logic.data_loader import DataLoader
        loader = DataLoader()
        schemes = loader.load_color_schemes()

        for name, colors in sorted(schemes.items()):
            scheme_frame = ttk.LabelFrame(scrollable_frame, text=f" {name.upper()} ", padding=10)
            scheme_frame.pack(fill="x", padx=10, pady=10)
            
            for key, val in colors.items():
                row = ttk.Frame(scheme_frame)
                row.pack(fill="x", pady=2)
                ttk.Label(row, text=f"{key.capitalize()}:", width=15).pack(side="left")
                
                # Color Swatch
                try:
                    border_color = self.root.theme_manager.themes.get(self.root.theme_manager.current_theme, {}).get("border", "gray")
                    swatch = tk.Frame(row, width=20, height=20, bg=val, highlightthickness=1, highlightbackground=border_color)
                    swatch.pack(side="left", padx=5)
                except Exception:
                    pass
                
                ttk.Label(row, text=val, style="Muted.TLabel").pack(side="left")

        ttk.Button(main_frame, text="CLOSE", command=dialog.destroy).pack(side="bottom", pady=10)

    def _copy_detail(self, text_widget):
        """Helper to copy text from a widget."""
        content = text_widget.get("1.0", "end-1c")
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.show_info("Copied", "Content copied to clipboard!")


    def show_welcome(self) -> None:
        """Show welcome dialog for first-time users."""
        dialog = tk.Toplevel(self.root)
        dialog.title("WELCOME TO PROMPT BUILDER!") # Refactor 5: UPPERCASE
        dialog.geometry("600x550")
        dialog.transient(self.root)
        dialog.grab_set()

        # Theme colors
        try:
            tm = self.root.theme_manager
            theme = tm.themes.get(tm.current_theme, {})
        except: theme = {}

        # Apply basic top-level theme
        if hasattr(self.root, "theme_manager"):
            self.root.theme_manager.theme_toplevel(dialog, theme)

        # Welcome text
        text_frame = ttk.Frame(dialog, style="TFrame")
        text_frame.pack(fill="both", expand=True, padx=15, pady=15)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        text = tk.Text(text_frame, wrap="word", font=("Lexend", 10), highlightthickness=0, borderwidth=0)
        text.grid(row=0, column=0, sticky="nsew")
        
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview, style="Themed.Vertical.TScrollbar")
        scroll.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scroll.set)
        
        text.insert("1.0", WELCOME_MESSAGE)
        text.config(state="disabled")

        # Don't show again checkbox
        show_again_var = tk.BooleanVar(value=False)
        pill_frame = tk.Frame(dialog, bg=theme.get("accent", "#0078d7"), padx=1, pady=1)
        pill_frame.pack(pady=(0, 15))
        
        chk_lbl = tk.Label(
            pill_frame, text="DON'T SHOW THIS AGAIN", bg=theme.get("panel_bg", "#1e1e1e"),
            fg=theme.get("accent", "#0078d7"), font=("Lexend", 8, "bold"), padx=10, pady=2, cursor="hand2"
        )
        chk_lbl.pack()
        
        def toggle_again(e):
            new_val = not show_again_var.get()
            show_again_var.set(new_val)
            chk_lbl.config(text="✓ DON'T SHOW THIS AGAIN" if new_val else "DON'T SHOW THIS AGAIN")

        chk_lbl.bind("<Button-1>", toggle_again)

        def on_close():
            if show_again_var.get():
                self.prefs.set("show_welcome", False)
            dialog.destroy()

        # Get started button (Primary)
        btn = ttk.Button(dialog, text="GET STARTED!", command=on_close, style="TButton")
        btn.pack(pady=(0, 20))

        def _apply(t):
            self.root.theme_manager.apply_text_widget_theme(text, t)
            pill_frame.config(bg=t.get("accent", "#0078d7"))
            chk_lbl.config(bg=t.get("panel_bg", "#1e1e1e"), fg=t.get("accent", "#0078d7"))
            
        self._register_dialog(dialog, _apply)
        _apply(theme)
        dialog.wait_window()

    def show_llm_export(self, ctx) -> None:
        """Show dialog with condensed app data for LLM context injection."""
        from utils.llm_export import generate_llm_export_text

        dialog = tk.Toplevel(self.root)
        dialog.title("EXPORT FOR LLM CONTEXT")
        dialog.geometry("800x700")
        dialog.transient(self.root)
        dialog.grab_set()

        # Apply basic top-level theme
        if hasattr(self.root, "theme_manager"):
            self.root.theme_manager.theme_toplevel(dialog)

        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="COPY THE CONTEXT BELOW AND PASTE IT INTO YOUR LLM:", style="Title.TLabel").pack(anchor="w", pady=(0, 5))
        
        info_text = "This contains your character list, outfit names, poses, and parsing instructions."
        ttk.Label(main_frame, text=info_text, style="Muted.TLabel").pack(anchor="w", pady=(0, 10))

        # Refactor 3: Themed Text + Scrollbar
        text_frame = ttk.Frame(main_frame, style="TFrame")
        text_frame.pack(fill="both", expand=True, pady=5)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        text_area = tk.Text(text_frame, wrap="word", font=("Lexend", 9), highlightthickness=0, borderwidth=0)
        text_area.grid(row=0, column=0, sticky="nsew")
        
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text_area.yview, style="Themed.Vertical.TScrollbar")
        scroll.grid(row=0, column=1, sticky="ns")
        text_area.configure(yscrollcommand=scroll.set)
        
        # Generate and insert text
        export_text = generate_llm_export_text(ctx)
        text_area.insert("1.0", export_text)
        text_area.config(state="disabled")

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(export_text)
            self.show_info("Copied", "Context copied to clipboard!")

        # Helper for Pill buttons in dialogs
        def add_dialog_pill(parent, text, command):
            try:
                tm = self.root.theme_manager
                theme = tm.themes.get(tm.current_theme, {})
                accent = theme.get("accent", "#0078d7")
                pbg = theme.get("panel_bg", "#1e1e1e")
            except Exception:
                accent = "#0078d7"
                pbg = "#1e1e1e"
                
            frame = tk.Frame(parent, bg=accent, padx=1, pady=1)
            lbl = tk.Label(
                frame, text=text, bg=pbg, fg=accent,
                font=("Lexend", 8, "bold"), padx=12, pady=3, cursor="hand2"
            )
            lbl.pack()
            lbl.bind("<Button-1>", lambda e: command())
            lbl.bind("<Enter>", lambda e: lbl.config(bg=self.root.theme_manager.themes.get(self.root.theme_manager.current_theme, {}).get("hover_bg", "#333333")))
            lbl.bind("<Leave>", lambda e: lbl.config(bg=getattr(lbl, "_base_bg", "#1e1e1e")))
            return frame, lbl

        close_pill, _ = add_dialog_pill(btn_frame, "CLOSE", dialog.destroy)
        close_pill.pack(side="right", padx=(10, 0))
        
        copy_pill, _ = add_dialog_pill(btn_frame, "📋 COPY CONTEXT", copy_to_clipboard)
        copy_pill.pack(side="right")

        def _apply(t):
            self.root.theme_manager.apply_text_widget_theme(text_area, t)
            # Add logic here if we tracked the pills
            
        self._register_dialog(dialog, _apply)
        _apply(self.root.theme_manager.themes.get(self.root.theme_manager.current_theme, {}))
        dialog.wait_window()

    def show_characters_summary(self, data_loader=None, theme_manager=None) -> None:
        """Show character summary (now part of Dashboard)."""
        self.show_dashboard(data_loader, theme_manager, initial_tab=1)

    def show_tag_summary(self, data_loader=None, theme_manager=None) -> None:
        """Show tag distribution (now part of Dashboard)."""
        self.show_dashboard(data_loader, theme_manager, initial_tab=2)

    def show_health_check(self, data_loader=None, theme_manager=None) -> None:
        """Show health check (now part of Dashboard)."""
        self.show_dashboard(data_loader, theme_manager, initial_tab=3)

    def open_data_folder(self, data_loader) -> None:
        """Open the data directory in the system file explorer."""
        import os
        path = data_loader.base_dir / "data"
        if path.exists():
            os.startfile(path)
        else:
            self.show_error("Error", f"Data directory not found: {path}")

    def show_bulk_generator(self, data_loader, poses_data, builder) -> None:
        """Show bulk prompt generator dialog."""
        import bulk # Import local module

        dialog = tk.Toplevel(self.root)
        dialog.title("BULK PROMPT GENERATOR")
        dialog.geometry("900x700")
        dialog.transient(self.root)
        
        if hasattr(self.root, "theme_manager"):
            self.root.theme_manager.theme_toplevel(dialog)

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Instructions
        ttk.Label(main_frame, text="PASTE PROMPT CONFIGURATIONS:", style="Title.TLabel").pack(anchor="w")
        ttk.Label(main_frame, text="Format: 'PROMPT CONFIG' blocks with 'Base:', 'Scene:', '[1] Character Name', etc.", style="Muted.TLabel").pack(anchor="w", pady=(0, 10))

        # Input / Output Notebook
        nb = ttk.Notebook(main_frame, style="TNotebook")
        nb.pack(fill="both", expand=True)

        input_tab = ttk.Frame(nb, style="TFrame")
        nb.add(input_tab, text="INPUT")
        
        output_tab = ttk.Frame(nb, style="TFrame")
        nb.add(output_tab, text="GENERATED OUTPUTS")

        # Input Text
        input_frame = ttk.Frame(input_tab, padding=5)
        input_frame.pack(fill="both", expand=True)
        
        input_text = tk.Text(input_frame, wrap="word", font=("Lexend", 9), highlightthickness=0, borderwidth=0)
        input_text.pack(side="left", fill="both", expand=True)
        
        # Add demo text
        input_text.insert("1.0", bulk.DEMO_TEXT)

        input_scroll = ttk.Scrollbar(input_frame, orient="vertical", command=input_text.yview, style="Themed.Vertical.TScrollbar")
        input_scroll.pack(side="right", fill="y")
        input_text.configure(yscrollcommand=input_scroll.set)

        # Output Text
        output_frame = ttk.Frame(output_tab, padding=5)
        output_frame.pack(fill="both", expand=True)
        
        output_text = tk.Text(output_frame, wrap="word", font=("Lexend", 9), highlightthickness=0, borderwidth=0)
        output_text.pack(side="left", fill="both", expand=True)
        
        output_scroll = ttk.Scrollbar(output_frame, orient="vertical", command=output_text.yview, style="Themed.Vertical.TScrollbar")
        output_scroll.pack(side="right", fill="y")
        output_text.configure(yscrollcommand=output_scroll.set)

        # Actions
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(15, 0))

        def generate():
            raw = input_text.get("1.0", "end").strip()
            if not raw:
                return
            
            try:
                raw_configs = bulk.parse_bulk_text(raw)
                output_text.delete("1.0", "end")
                
                count = 0
                for idx, conf in enumerate(raw_configs):
                    try:
                        resolved = bulk.resolve_config(conf, data_loader, poses_data)
                        prompt = builder.generate(resolved)
                        
                        output_text.insert("end", f"--- PROMPT {idx+1} ---\n", "title")
                        output_text.insert("end", prompt + "\n\n\n")
                        count += 1
                    except Exception as e:
                        output_text.insert("end", f"Error generating prompt {idx+1}: {e}\n\n", "error")
                
                output_text.tag_configure("title", font=("Lexend", 10, "bold"), foreground="#0078d7") # Fallback color
                output_text.tag_configure("error", foreground="red")
                
                nb.select(output_tab)
                self.show_info("Success", f"Generated {count} prompts.")
                
            except Exception as e:
                self.show_error("Generation Error", str(e))

        def copy_output():
            content = output_text.get("1.0", "end").strip()
            if content:
                self.root.clipboard_clear()
                self.root.clipboard_append(content)
                self.show_info("Copied", "All prompts copied to clipboard!")

        def export_to_txt():
            content = output_text.get("1.0", "end").strip()
            if not content:
                self.show_error("Export Error", "Nothing to export!")
                return
            
            from tkinter import filedialog
            from pathlib import Path
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Bulk Prompts"
            )
            
            if filename:
                try:
                    Path(filename).write_text(content, encoding="utf-8")
                    self.show_info("Success", f"Prompts exported to {Path(filename).name}")
                except Exception as e:
                    self.show_error("Export Error", f"Failed to save file: {e}")

        ttk.Button(btn_frame, text="GENERATE", command=generate, style="TButton").pack(side="right", padx=5)
        ttk.Button(btn_frame, text="EXPORT TO TXT", command=export_to_txt).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="COPY OUTPUT", command=copy_output).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="CLOSE", command=dialog.destroy).pack(side="right", padx=5)

        def _apply(t):
            self.root.theme_manager.apply_text_widget_theme(input_text, t)
            self.root.theme_manager.apply_text_widget_theme(output_text, t)
            output_text.tag_configure("title", foreground=t.get("accent", "#0078d7"))
            
        self._register_dialog(dialog, _apply)
        _apply(self.root.theme_manager.themes.get(self.root.theme_manager.current_theme, {}))
