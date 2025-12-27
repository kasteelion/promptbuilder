"""Outfit creator dialogs UI."""

import tkinter as tk
from tkinter import messagebox, ttk

from .searchable_combobox import SearchableCombobox
from utils import get_outfit_template, get_outfit_template_names, get_outfit_template_description


class SharedOutfitCreatorDialog:
    """Dialog for creating new shared outfits."""

    def __init__(self, parent, data_loader, on_success_callback):
        """Initialize shared outfit creator dialog.

        Args:
            parent: Parent window
            data_loader: DataLoader instance
            on_success_callback: Function to call after successful creation
        """
        self.data_loader = data_loader
        self.on_success = on_success_callback
        self.result = None
        self.parent = parent

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("CREATE SHARED OUTFIT")
        self.dialog.geometry("700x750")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Apply basic top-level theme
        if hasattr(parent, "theme_manager"):
            parent.theme_manager.theme_toplevel(self.dialog)

        self._build_ui()

        # Register for theme updates
        if hasattr(parent, "dialog_manager"):
            parent.dialog_manager._register_dialog(self.dialog, self.apply_theme)
        
        # Initial theme application
        try:
            current_theme = parent.theme_manager.themes.get(parent.theme_manager.current_theme, {})
            self.apply_theme(current_theme)
        except: pass

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"{x}+{y}")

    def apply_theme(self, theme):
        """Apply theme to all dialog widgets. (Refactor 3)"""
        tm = self.parent.theme_manager
        tm.apply_text_widget_theme(self.example_widget, theme)
        tm.apply_text_widget_theme(self.description_text, theme)
        
        pbg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        
        # Update cancel btn manual overrides
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.config(bg=pbg, fg=theme.get("fg", "white"), highlightbackground="gray")
            self.cancel_btn._base_bg = pbg

        if hasattr(self, "category_combo"): self.category_combo.apply_theme(theme)

        # Handle placeholders
        if self.description_text.get("1.0", "2.0").lower().startswith("- **top:"):
            try:
                tm = self.parent.theme_manager
                theme = tm.themes.get(tm.current_theme, {})
                pfg = theme.get("placeholder_fg", "#666666")
            except: pfg = "#666666"
            self.description_text.config(foreground=pfg)
        else:
            self.description_text.config(foreground=theme.get("text_fg", "white"))

    def _build_ui(self):
        """Build the shared outfit creator UI."""
        main_frame = ttk.Frame(self.dialog, padding=15, style="TFrame")
        main_frame.pack(fill="both", expand=True)

        # Info/help section (Refactor 1: Spatial Layout)
        help_frame = ttk.Frame(main_frame, style="TFrame", padding=(15, 10))
        help_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            help_frame,
            text="🌟 TIP: SHARED OUTFITS ARE AVAILABLE TO ALL CHARACTERS AUTOMATICALLY!",
            style="Accent.TLabel",
        ).pack(anchor="w", padx=6, pady=4)

        example_text = """Categories are for organization only - all outfits here are shared.
Example outfit format:
• Main garments with fabric details
• Accessories section  
• Hair/Makeup notes
• Use italics for *Accessories:* and *Hair/Makeup:* sections"""

        self.example_widget = tk.Text(
            help_frame,
            font=("Lexend", 8),
            height=6,
            wrap="word",
            relief="flat",
            borderwidth=0
        )
        self.example_widget.insert("1.0", example_text)
        self.example_widget.config(state="disabled")
        self.example_widget.pack(anchor="w", padx=10, pady=(0, 4), fill="x")

        # Template Selection
        template_frame = ttk.Frame(main_frame, style="TFrame")
        template_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(template_frame, text="TEMPLATE:", style="Bold.TLabel").pack(side="left", padx=(0, 10))
        self.template_var = tk.StringVar(value="Blank")
        template_combo = ttk.Combobox(
            template_frame, 
            textvariable=self.template_var, 
            values=get_outfit_template_names(),
            state="readonly",
            width=20,
            font=("Lexend", 9)
        )
        template_combo.pack(side="left")
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # Template description label
        self.template_desc_label = ttk.Label(
            template_frame,
            text=get_outfit_template_description("Blank").upper(),
            style="Muted.TLabel",
        )
        self.template_desc_label.pack(side="left", padx=(15, 0))

        # Category
        ttk.Label(main_frame, text="CATEGORY:", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))

        cat_frame = ttk.Frame(main_frame, style="TFrame")
        cat_frame.pack(fill="x", pady=(0, 15))

        self.category_var = tk.StringVar()
        self.category_combo = SearchableCombobox(
            cat_frame, 
            textvariable=self.category_var, 
            placeholder="Search or type category..."
        )
        self.category_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._load_categories()

        # Modifier selector for shared outfit file
        ttk.Label(cat_frame, text="MODIFIER:", style="Bold.TLabel").pack(side="left", padx=(10, 10))
        
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

        self.modifier_var = tk.StringVar(value="F" if "F" in modifiers else modifiers[0])
        self.modifier_combo = ttk.Combobox(
            cat_frame, textvariable=self.modifier_var, values=modifiers, width=6, state="readonly", font=("Lexend", 9)
        )
        self.modifier_combo.pack(side="left")

        # Outfit name
        ttk.Label(main_frame, text="OUTFIT NAME:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, style="TEntry")
        name_entry.pack(fill="x", pady=(0, 15))
        name_entry.focus()

        # Description
        ttk.Label(main_frame, text="OUTFIT DESCRIPTION:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        ttk.Label(
            main_frame,
            text="Describe garments, accessories, and styling. Use {primary_color} etc.",
            style="Muted.TLabel",
        ).pack(anchor="w")

        desc_frame = ttk.Frame(main_frame, style="TFrame")
        desc_frame.pack(fill="both", expand=True, pady=(0, 15))

        self.description_text = tk.Text(
            desc_frame, 
            height=12, 
            wrap="word", 
            font=("Lexend", 9),
            relief="flat",
            padx=15,
            pady=15
        )
        desc_scroll = ttk.Scrollbar(desc_frame, orient="vertical", command=self.description_text.yview, style="Themed.Vertical.TScrollbar")
        self.description_text.configure(yscrollcommand=desc_scroll.set)

        placeholder = """- **Top:** [Detailed description]
- **Bottom:** [Detailed description]
- **Footwear:** [Detailed description]
- **Accessories:** [Detailed description]
- **Hair/Makeup:** [Specific look for this outfit]"""

        self.description_text.insert("1.0", placeholder)

        def on_focus_in(event):
            if self.description_text.get("1.0", "end").strip().startswith("- **Top:"):
                self.description_text.delete("1.0", "end")
                self.description_text.config(foreground="")

        def on_focus_out(event):
            if not self.description_text.get("1.0", "end").strip():
                self.description_text.insert("1.0", placeholder)
                try:
                    tm = self.winfo_toplevel().theme_manager
                    theme = tm.themes.get(tm.current_theme, {})
                    pfg = theme.get("placeholder_fg", "#666666")
                except: pfg = "#666666"
                self.description_text.config(foreground=pfg)

        self.description_text.bind("<FocusIn>", on_focus_in)
        self.description_text.bind("<FocusOut>", on_focus_out)

        self.description_text.pack(side="left", fill="both", expand=True)
        desc_scroll.pack(side="right", fill="y")

        # Buttons (Refactor 3: Hierarchy)
        button_frame = ttk.Frame(self.dialog, padding=15, style="TFrame")
        button_frame.pack(side="bottom", fill="x")

        # Cancel: Ghost Style (Secondary)
        self.cancel_btn = tk.Button(
            button_frame, 
            text="CANCEL", 
            command=self._cancel,
            relief="flat",
            highlightthickness=2,
            padx=20,
            font=("Lexend", 9, "bold"),
            cursor="hand2"
        )
        self.cancel_btn.pack(side="right", padx=(15, 0))
        
        def on_c_enter(e):
            try:
                tm = self.winfo_toplevel().theme_manager
                theme = tm.themes.get(tm.current_theme, {})
                hbg = theme.get("hover_bg", "#333333")
            except: hbg = "#333333"
            self.cancel_btn.config(bg=hbg)
        def on_c_leave(e): self.cancel_btn.config(bg=getattr(self.cancel_btn, "_base_bg", "#1e1e1e"))
        self.cancel_btn.bind("<Enter>", on_c_enter)
        self.cancel_btn.bind("<Leave>", on_c_leave)

        ttk.Button(button_frame, text="CREATE SHARED OUTFIT", command=self._create_outfit, style="TButton").pack(side="right")

        self.dialog.bind("<Escape>", lambda e: self._cancel())

    def _on_template_selected(self, event=None):
        template_name = self.template_var.get()
        content = get_outfit_template(template_name)
        if not content: return
        
        # Update description label if it exists
        if hasattr(self, "template_desc_label"):
            self.template_desc_label.config(text=get_outfit_template_description(template_name).upper())
            
        self.description_text.delete("1.0", "end")
        self.description_text.insert("1.0", content)
        self.description_text.config(foreground="")

    def _load_categories(self):
        """Load existing outfit categories from all available outfit files."""
        categories = []
        try:
            data_dir = self.data_loader.base_dir / "data"
            if not data_dir.exists():
                data_dir = self.data_loader.base_dir
                
            for outfits_file in data_dir.glob("outfits_*.md"):
                try:
                    content = outfits_file.read_text(encoding="utf-8")
                    lines = content.split("\n")
                    for line in lines:
                        if line.strip().startswith("## "):
                            cat = line.strip()[3:]
                            if cat not in categories:
                                categories.append(cat)
                except Exception:
                    from utils import logger
                    logger.debug(f"Failed to load outfit categories from {outfits_file}")
        except Exception:
            categories = []

        if not categories:
            categories = ["Common Outfits", "Formal", "Casual", "Athletic"]

        self.category_combo.set_values(sorted(categories))

    def _cancel(self):
        """Cancel and close dialog."""
        self.dialog.destroy()

    def _create_outfit(self):
        """Validate and create the outfit."""
        category = self.category_var.get().strip()
        name = self.name_var.get().strip()
        description = self.description_text.get("1.0", "end").strip()

        if not category:
            messagebox.showerror(
                "Validation Error", "Please enter or select a category.", parent=self.dialog
            )
            return

        if not name:
            messagebox.showerror(
                "Validation Error", "Please enter an outfit name.", parent=self.dialog
            )
            return

        if not description or description.startswith("- **Top:"):
            messagebox.showerror(
                "Validation Error", "Please enter an outfit description.", parent=self.dialog
            )
            return

        # Determine target file based on selection
        mod = self.modifier_var.get().strip().lower()
        outfits_file = self.data_loader.base_dir / "data" / f"outfits_{mod}.md"
        if not outfits_file.parent.exists():
            outfits_file = self.data_loader.base_dir / f"outfits_{mod}.md"

        try:
            if outfits_file.exists():
                content = outfits_file.read_text(encoding="utf-8")
            else:
                content = "# Shared Outfits\n\nThis file contains outfit templates shared across characters.\n\n---\n\n"

            # Find or create category section
            if f"## {category}" in content:
                lines = content.split("\n")
                insert_idx = -1

                for i, line in enumerate(lines):
                    if line.strip() == f"## {category}":
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip().startswith("##") or lines[j].strip() == "---":
                                insert_idx = j
                                break
                        if insert_idx == -1:
                            insert_idx = len(lines)
                        break

                new_entry = f"\n### {name}\n{description}\n"
                if insert_idx > 0:
                    lines.insert(insert_idx, new_entry)
                    content = "\n".join(lines)
            else:
                new_section = f"\n## {category}\n\n### {name}\n{description}\n\n---\n"
                content += new_section

            outfits_file.write_text(content, encoding="utf-8")

            from utils.notification import notify

            root = self.dialog.winfo_toplevel()
            msg = f"Shared outfit '{name}' created in category '{category}'!"
            notify(root, "Success", msg, level="success", duration=3000, parent=self.dialog)
            self.result = name
            self.dialog.destroy()
            if self.on_success:
                self.on_success()
        except Exception as e:
            from utils import logger

            logger.exception("Auto-captured exception")
            messagebox.showerror("Error", f"Failed to create outfit:\n{str(e)}", parent=self.dialog)

    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result


class CharacterOutfitCreatorDialog:
    """Dialog for creating character-specific outfits."""

    def __init__(self, parent, data_loader, character_name, on_success_callback):
        """Initialize character outfit creator dialog."""
        self.data_loader = data_loader
        self.character_name = character_name
        self.on_success = on_success_callback
        self.result = None
        self.parent = parent

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"CREATE OUTFIT FOR {character_name.upper()}")
        self.dialog.geometry("700x750")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Apply basic top-level theme
        if hasattr(parent, "theme_manager"):
            parent.theme_manager.theme_toplevel(self.dialog)

        self._build_ui()

        # Register for theme updates
        if hasattr(parent, "dialog_manager"):
            parent.dialog_manager._register_dialog(self.dialog, self.apply_theme)
        
        # Initial theme application
        try:
            current_theme = parent.theme_manager.themes.get(parent.theme_manager.current_theme, {})
            self.apply_theme(current_theme)
        except: pass

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"{x}+{y}")

    def apply_theme(self, theme):
        """Apply theme to all dialog widgets. (Refactor 3)"""
        tm = self.parent.theme_manager
        tm.apply_text_widget_theme(self.example_widget, theme)
        tm.apply_text_widget_theme(self.description_text, theme)
        
        pbg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        
        # Update cancel btn manual overrides
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.config(bg=pbg, fg=theme.get("fg", "white"), highlightbackground="gray")
            self.cancel_btn._base_bg = pbg

        # Handle placeholders
        if self.description_text.get("1.0", "2.0").lower().startswith("- **top:"):
            try:
                tm = self.parent.theme_manager
                theme = tm.themes.get(tm.current_theme, {})
                pfg = theme.get("placeholder_fg", "#666666")
            except: pfg = "#666666"
            self.description_text.config(foreground=pfg)
        else:
            self.description_text.config(foreground=theme.get("text_fg", "white"))

    def _build_ui(self):
        """Build the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=15, style="TFrame")
        main_frame.pack(fill="both", expand=True)

        # Info section (Refactor 1: Spatial Layout)
        help_frame = ttk.Frame(main_frame, style="TFrame", padding=(15, 10))
        help_frame.pack(fill="x", pady=(0, 15))

        help_label = ttk.Label(
            help_frame,
            text=f"💡 TIP: CREATING OUTFIT FOR {self.character_name.upper()}",
            style="Accent.TLabel"
        )
        help_label.pack(anchor="w", padx=6, pady=4)

        example_text = """Use markdown bullet format:
- **Top:** [Description]
- **Bottom:** [Description]
- **Footwear:** [Description]
- **Accessories:** [Description]
- **Hair/Makeup:** [Description]

Or use free-form text with sections like:
Main garments with fabric details. *Accessories:* items. *Hair/Makeup:* notes."""

        self.example_widget = tk.Text(
            help_frame,
            font=("Lexend", 8),
            height=9,
            wrap="word",
            relief="flat",
            borderwidth=0,
        )
        self.example_widget.insert("1.0", example_text)
        self.example_widget.config(state="disabled")
        self.example_widget.pack(anchor="w", padx=10, pady=(0, 4), fill="x")

        # Template Selection
        template_frame = ttk.Frame(main_frame, style="TFrame")
        template_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(template_frame, text="TEMPLATE:", style="Bold.TLabel").pack(side="left", padx=(0, 10))
        self.template_var = tk.StringVar(value="Blank")
        template_combo = ttk.Combobox(
            template_frame, 
            textvariable=self.template_var, 
            values=get_outfit_template_names(),
            state="readonly",
            width=20,
            font=("Lexend", 9)
        )
        template_combo.pack(side="left")
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # Template description label
        self.template_desc_label = ttk.Label(
            template_frame,
            text=get_outfit_template_description("Blank").upper(),
            style="Muted.TLabel",
        )
        self.template_desc_label.pack(side="left", padx=(15, 0))

        # Category and Outfit name
        row1 = ttk.Frame(main_frame, style="TFrame")
        row1.pack(fill="x", pady=(0, 15))

        ttk.Label(row1, text="CATEGORY:", style="Bold.TLabel").pack(side="left")
        self.category_var = tk.StringVar(value="Personal")
        categories = ["Personal", "Signature", "Formal", "Action", "Casual", "Other"]
        cat_combo = ttk.Combobox(row1, textvariable=self.category_var, values=categories, width=12, font=("Lexend", 9))
        cat_combo.pack(side="left", padx=10)

        ttk.Label(row1, text="OUTFIT NAME:", style="Bold.TLabel").pack(side="left", padx=(10, 0))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(row1, textvariable=self.name_var, style="TEntry")
        name_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        name_entry.focus()

        # Outfit description
        ttk.Label(main_frame, text="OUTFIT DESCRIPTION:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        ttk.Label(
            main_frame,
            text="Describe garments, accessories, and styling. Use {primary_color} etc.",
            style="Muted.TLabel",
        ).pack(anchor="w")

        desc_frame = ttk.Frame(main_frame, style="TFrame")
        desc_frame.pack(fill="both", expand=True, pady=(0, 15))

        self.description_text = tk.Text(
            desc_frame, 
            height=12, 
            wrap="word", 
            font=("Lexend", 9),
            relief="flat",
            padx=15,
            pady=15,
            highlightthickness=0,
            borderwidth=0
        )
        desc_scroll = ttk.Scrollbar(desc_frame, orient="vertical", command=self.description_text.yview, style="Themed.Vertical.TScrollbar")
        self.description_text.configure(yscrollcommand=desc_scroll.set)

        placeholder = """- **Top:** [Detailed description]
- **Bottom:** [Detailed description]
- **Footwear:** [Detailed description]
- **Accessories:** [Detailed description]
- **Hair/Makeup:** [Specific look for this outfit]"""

        self.description_text.insert("1.0", placeholder)

        def on_focus_in(event):
            if self.description_text.get("1.0", "end").strip().startswith("- **Top:"):
                self.description_text.delete("1.0", "end")
                self.description_text.config(foreground="")

        def on_focus_out(event):
            if not self.description_text.get("1.0", "end").strip():
                self.description_text.insert("1.0", placeholder)
                try:
                    tm = self.winfo_toplevel().theme_manager
                    theme = tm.themes.get(tm.current_theme, {})
                    pfg = theme.get("placeholder_fg", "#666666")
                except: pfg = "#666666"
                self.description_text.config(foreground=pfg)

        self.description_text.bind("<FocusIn>", on_focus_in)
        self.description_text.bind("<FocusOut>", on_focus_out)

        self.description_text.pack(side="left", fill="both", expand=True)
        desc_scroll.pack(side="right", fill="y")

        # Buttons (Refactor 3: Hierarchy)
        button_frame = ttk.Frame(self.dialog, padding=15, style="TFrame")
        button_frame.pack(side="bottom", fill="x")

        # Cancel: Ghost Style (Secondary)
        self.cancel_btn = tk.Button(
            button_frame, 
            text="CANCEL", 
            command=self._cancel,
            relief="flat",
            highlightthickness=2,
            padx=20,
            font=("Lexend", 9, "bold"),
            cursor="hand2"
        )
        self.cancel_btn.pack(side="right", padx=(15, 0))
        
        def on_c_enter(e):
            try:
                tm = self.winfo_toplevel().theme_manager
                theme = tm.themes.get(tm.current_theme, {})
                hbg = theme.get("hover_bg", "#333333")
            except: hbg = "#333333"
            self.cancel_btn.config(bg=hbg)
        def on_c_leave(e): self.cancel_btn.config(bg=getattr(self.cancel_btn, "_base_bg", "#1e1e1e"))
        self.cancel_btn.bind("<Enter>", on_c_enter)
        self.cancel_btn.bind("<Leave>", on_c_leave)

        ttk.Button(button_frame, text="SAVE OUTFIT", command=self._create_outfit, style="TButton").pack(side="right")

        self.dialog.bind("<Escape>", lambda e: self._cancel())

    def _on_template_selected(self, event=None):
        template_name = self.template_var.get()
        content = get_outfit_template(template_name)
        if not content: return
        
        # Update description label if it exists
        if hasattr(self, "template_desc_label"):
            self.template_desc_label.config(text=get_outfit_template_description(template_name).upper())
            
        self.description_text.delete("1.0", "end")
        self.description_text.insert("1.0", content)
        self.description_text.config(foreground="")

    def _cancel(self):
        """Cancel and close the dialog."""
        self.dialog.destroy()

    def _create_outfit(self):
        """Validate and create the outfit for the character."""
        name = self.name_var.get().strip()
        description = self.description_text.get("1.0", "end").strip()

        placeholder = """- **Top:** [Description]
- **Bottom:** [Description]
- **Footwear:** [Description]
- **Accessories:** [Description]
- **Hair/Makeup:** [Description]"""

        if not name:
            messagebox.showerror(
                "Validation Error", "Please enter an outfit name.", parent=self.dialog
            )
            return

        if not description or description == placeholder:
            messagebox.showerror(
                "Validation Error", "Please enter an outfit description.", parent=self.dialog
            )
            return

        # Find character file
        from utils.validation import sanitize_filename
        safe_name = sanitize_filename(self.character_name)
        char_filename = f"{safe_name.lower()}.md"
        chars_dir = self.data_loader._find_characters_dir()
        char_file = chars_dir / char_filename

        if not char_file.exists():
            messagebox.showerror("Error", f"Character file not found: {char_filename}", parent=self.dialog)
            return

        try:
            content = char_file.read_text(encoding="utf-8")
            new_outfit = f"\n#### {name}\n{description}\n"
            content += new_outfit
            char_file.write_text(content, encoding="utf-8")
            from utils.notification import notify
            root = self.dialog.winfo_toplevel()
            msg = f"Outfit '{name}' created for {self.character_name}!"
            notify(root, "Success", msg, level="success", duration=3000, parent=self.dialog)
            self.result = name
            self.dialog.destroy()
            if self.on_success:
                self.on_success()
        except Exception as e:
            from utils import logger
            logger.exception("Auto-captured exception")
            messagebox.showerror("Error", f"Failed to create outfit:\n{str(e)}", parent=self.dialog)

    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result
