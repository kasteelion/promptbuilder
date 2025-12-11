"""Outfit creator dialogs UI."""

import tkinter as tk
from tkinter import ttk, messagebox


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
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Shared Outfit")
        self.dialog.geometry("600x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._build_ui()
        
        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _build_ui(self):
        """Build the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Info/help section
        help_frame = ttk.Frame(main_frame, relief="groove", borderwidth=1)
        help_frame.pack(fill="x", pady=(0, 10))
        
        help_label = ttk.Label(
            help_frame, 
            text="💡 Shared outfits can be used by all characters",
            font=("Segoe UI", 9, "bold"),
            foreground="#0066cc"
        )
        help_label.pack(anchor="w", padx=6, pady=4)
        
        example_text = """Example outfit format:
• Main garments with fabric details
• Accessories section
• Hair/Makeup notes
• Use italics for *Accessories:* and *Hair/Makeup:* sections"""
        
        example_widget = tk.Text(
            help_frame,
            font=("Consolas", 8),
            foreground="#555555",
            background="#f0f0f0",
            height=4,
            wrap="word",
            relief="flat",
            borderwidth=0
        )
        example_widget.insert("1.0", example_text)
        example_widget.config(state="disabled")
        example_widget.pack(anchor="w", padx=10, pady=(0, 4), fill="x")
        
        # Category
        ttk.Label(main_frame, text="Category:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        
        cat_frame = ttk.Frame(main_frame)
        cat_frame.pack(fill="x", pady=(0, 10))
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(cat_frame, textvariable=self.category_var, font=("Segoe UI", 10))
        self.category_combo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._load_categories()
        
        ttk.Label(cat_frame, text="(or type new)", foreground="gray", font=("Segoe UI", 8)).pack(side="left")
        
        # Outfit name
        ttk.Label(main_frame, text="Outfit Name:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, font=("Segoe UI", 10))
        name_entry.pack(fill="x", pady=(0, 10))
        name_entry.focus()
        
        # Description
        ttk.Label(main_frame, text="Outfit Description:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        ttk.Label(main_frame, text="Describe garments, accessories, and styling", foreground="gray", font=("Segoe UI", 8)).pack(anchor="w")
        
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.description_text = tk.Text(desc_frame, height=12, wrap="word", font=("Consolas", 9))
        desc_scroll = ttk.Scrollbar(desc_frame, command=self.description_text.yview)
        self.description_text.configure(yscrollcommand=desc_scroll.set)
        
        placeholder = """[Main garment description with fabric details]. *Accessories:* [Accessories list]. *Hair/Makeup:* [Styling notes].

Example:
Fitted **athletic top** (technical knit); high-waist **athletic shorts or leggings** (technical fabric). *Accessories:* Fitness watch or tracker, hair in ponytail. *Hair/Makeup:* Minimal or no makeup."""
        
        self.description_text.insert("1.0", placeholder)
        self.description_text.config(foreground="gray")
        
        def on_focus_in(event):
            if self.description_text.get("1.0", "end").strip().startswith("[Main garment"):
                self.description_text.delete("1.0", "end")
                self.description_text.config(foreground="black")
        
        def on_focus_out(event):
            if not self.description_text.get("1.0", "end").strip():
                self.description_text.insert("1.0", placeholder)
                self.description_text.config(foreground="gray")
        
        self.description_text.bind("<FocusIn>", on_focus_in)
        self.description_text.bind("<FocusOut>", on_focus_out)
        
        self.description_text.pack(side="left", fill="both", expand=True)
        desc_scroll.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Create Outfit", command=self._create_outfit).pack(side="right")
        
        self.dialog.bind("<Escape>", lambda e: self._cancel())
    
    def _load_categories(self):
        """Load existing outfit categories."""
        outfits_file = self.data_loader.base_dir / "outfits.md"
        categories = []
        
        if outfits_file.exists():
            try:
                content = outfits_file.read_text(encoding="utf-8")
                lines = content.split('\n')
                for line in lines:
                    if line.strip().startswith("## "):
                        categories.append(line.strip()[3:])
            except Exception:
                pass
        
        if not categories:
            categories = ["Common Outfits", "Formal", "Casual", "Athletic"]
        
        self.category_combo['values'] = categories
    
    def _cancel(self):
        """Cancel and close dialog."""
        self.dialog.destroy()
    
    def _create_outfit(self):
        """Validate and create the outfit."""
        category = self.category_var.get().strip()
        name = self.name_var.get().strip()
        description = self.description_text.get("1.0", "end").strip()
        
        if not category:
            messagebox.showerror("Validation Error", "Please enter or select a category.", parent=self.dialog)
            return
        
        if not name:
            messagebox.showerror("Validation Error", "Please enter an outfit name.", parent=self.dialog)
            return
        
        if not description or description.startswith("[Main garment"):
            messagebox.showerror("Validation Error", "Please enter an outfit description.", parent=self.dialog)
            return
        
        outfits_file = self.data_loader.base_dir / "outfits.md"
        
        try:
            if outfits_file.exists():
                content = outfits_file.read_text(encoding="utf-8")
            else:
                content = "# Shared Outfits\n\nThis file contains outfit templates shared across characters.\n\n---\n\n"
            
            # Find or create category section
            if f"## {category}" in content:
                lines = content.split('\n')
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
                    content = '\n'.join(lines)
            else:
                new_section = f"\n## {category}\n\n### {name}\n{description}\n\n---\n"
                content += new_section
            
            outfits_file.write_text(content, encoding="utf-8")
            
            messagebox.showinfo(
                "Success", 
                f"Shared outfit '{name}' created in category '{category}'!",
                parent=self.dialog
            )
            self.result = name
            self.dialog.destroy()
            if self.on_success:
                self.on_success()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create outfit:\n{str(e)}", parent=self.dialog)
    
    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result


class CharacterOutfitCreatorDialog:
    """Dialog for creating character-specific outfits."""
    
    def __init__(self, parent, data_loader, character_name, on_success_callback):
        """Initialize character outfit creator dialog.
        
        Args:
            parent: Parent window
            data_loader: DataLoader instance
            character_name: Name of the character
            on_success_callback: Function to call after successful creation
        """
        self.data_loader = data_loader
        self.character_name = character_name
        self.on_success = on_success_callback
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Create Outfit for {character_name}")
        self.dialog.geometry("600x550")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._build_ui()
        
        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _build_ui(self):
        """Build the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Info section
        help_frame = ttk.Frame(main_frame, relief="groove", borderwidth=1)
        help_frame.pack(fill="x", pady=(0, 10))
        
        help_label = ttk.Label(
            help_frame, 
            text=f"💡 Creating outfit for: {self.character_name}",
            font=("Segoe UI", 9, "bold"),
            foreground="#0066cc"
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
        
        example_widget = tk.Text(
            help_frame,
            font=("Consolas", 8),
            foreground="#555555",
            background="#f0f0f0",
            height=9,
            wrap="word",
            relief="flat",
            borderwidth=0
        )
        example_widget.insert("1.0", example_text)
        example_widget.config(state="disabled")
        example_widget.pack(anchor="w", padx=10, pady=(0, 4), fill="x")
        
        # Outfit name
        ttk.Label(main_frame, text="Outfit Name:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, font=("Segoe UI", 10))
        name_entry.pack(fill="x", pady=(0, 10))
        name_entry.focus()
        
        # Description
        ttk.Label(main_frame, text="Outfit Description:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.description_text = tk.Text(desc_frame, height=12, wrap="word", font=("Consolas", 9))
        desc_scroll = ttk.Scrollbar(desc_frame, command=self.description_text.yview)
        self.description_text.configure(yscrollcommand=desc_scroll.set)
        
        placeholder = """- **Top:** [Description]
- **Bottom:** [Description]
- **Footwear:** [Description or "None specified"]
- **Accessories:** [Description]
- **Hair/Makeup:** [Description]

Or use free-form:
[Main garments with fabric details]. *Accessories:* [items]. *Hair/Makeup:* [notes].

Example:
Fitted **athletic top** (technical knit); high-waist **athletic shorts or leggings**. *Accessories:* Fitness watch, hair in ponytail. *Hair/Makeup:* Minimal makeup."""
        
        self.description_text.insert("1.0", placeholder)
        self.description_text.config(foreground="gray")
        
        def on_focus_in(event):
            if self.description_text.get("1.0", "end").strip() == placeholder.strip():
                self.description_text.delete("1.0", "end")
                self.description_text.config(foreground="black")
        
        def on_focus_out(event):
            if not self.description_text.get("1.0", "end").strip():
                self.description_text.insert("1.0", placeholder)
                self.description_text.config(foreground="gray")
        
        self.description_text.bind("<FocusIn>", on_focus_in)
        self.description_text.bind("<FocusOut>", on_focus_out)
        
        self.description_text.pack(side="left", fill="both", expand=True)
        desc_scroll.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Create Outfit", command=self._create_outfit).pack(side="right")
        
        self.dialog.bind("<Escape>", lambda e: self._cancel())
    
    def _cancel(self):
        """Cancel and close dialog."""
        self.dialog.destroy()
    
    def _create_outfit(self):
        """Validate and create the outfit for the character."""
        name = self.name_var.get().strip()
        description = self.description_text.get("1.0", "end").strip()
        
        placeholder = """- **Top:** [Description]
- **Bottom:** [Description]
- **Footwear:** [Description or "None specified"]
- **Accessories:** [Description]
- **Hair/Makeup:** [Description]"""
        
        if not name:
            messagebox.showerror("Validation Error", "Please enter an outfit name.", parent=self.dialog)
            return
        
        if not description or description == placeholder:
            messagebox.showerror("Validation Error", "Please enter an outfit description.", parent=self.dialog)
            return
        
        # Find character file
        char_filename = self.character_name.lower().replace(" ", "_").replace("-", "_")
        char_filename = "\u0022".join(c for c in char_filename if c.isalnum() or c == "_")
        char_filename = f"{char_filename}.md"
        
        chars_dir = self.data_loader._find_characters_dir()
        char_file = chars_dir / char_filename
        
        if not char_file.exists():
            messagebox.showerror("Error", f"Character file not found: {char_filename}", parent=self.dialog)
            return
        
        try:
            content = char_file.read_text(encoding="utf-8")
            
            # Add new outfit section
            new_outfit = f"\n#### {name}\n{description}\n"
            content += new_outfit
            
            char_file.write_text(content, encoding="utf-8")
            
            messagebox.showinfo(
                "Success", 
                f"Outfit '{name}' created for {self.character_name}!",
                parent=self.dialog
            )
            self.result = name
            self.dialog.destroy()
            if self.on_success:
                self.on_success()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create outfit:\n{str(e)}", parent=self.dialog)
    
    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result
