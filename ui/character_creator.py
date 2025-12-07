"""Character creator dialog UI."""

import tkinter as tk
from tkinter import ttk, messagebox
from utils import get_character_template_names, get_character_template, get_character_template_description
from pathlib import Path


class CharacterCreatorDialog:
    """Dialog for creating new characters."""
    
    def __init__(self, parent, data_loader, on_success_callback):
        """Initialize character creator dialog.
        
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
        self.dialog.title("Create New Character")
        self.dialog.geometry("600x650")
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
        
        # Template selection
        template_frame = ttk.Frame(main_frame)
        template_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(template_frame, text="Template:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 5))
        
        self.template_var = tk.StringVar(value="Blank")
        template_combo = ttk.Combobox(
            template_frame, 
            textvariable=self.template_var,
            values=get_character_template_names(),
            state="readonly",
            width=25,
            font=("Segoe UI", 9)
        )
        template_combo.pack(side="left", padx=(0, 10))
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)
        
        # Template description label
        self.template_desc_label = ttk.Label(
            template_frame,
            text=get_character_template_description("Blank"),
            foreground="gray",
            font=("Segoe UI", 8, "italic")
        )
        self.template_desc_label.pack(side="left")
        
        # Info/help section
        help_frame = ttk.Frame(main_frame, relief="groove", borderwidth=1)
        help_frame.pack(fill="x", pady=(0, 10))
        
        help_label = ttk.Label(
            help_frame, 
            text="💡 Tip: Follow the pattern of existing characters for consistency",
            font=("Segoe UI", 9, "bold"),
            foreground="#0066cc"
        )
        help_label.pack(anchor="w", padx=6, pady=4)
        
        example_text = """Example Appearance format:
• Physical description (skin tone, features, hair)
• Age and demographics
• Eye color and expression style
• Body type and posture
• Makeup preferences
• Fabric/style preferences
• Signature accessories"""
        
        example_widget = tk.Text(
            help_frame,
            font=("Consolas", 8),
            foreground="#555555",
            background="#f0f0f0",
            height=7,
            wrap="word",
            relief="flat",
            borderwidth=0
        )
        example_widget.insert("1.0", example_text)
        example_widget.config(state="disabled")  # Make read-only but still copyable
        example_widget.pack(anchor="w", padx=10, pady=(0, 4), fill="x")
        
        # Character name
        ttk.Label(main_frame, text="Character Name:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, font=("Segoe UI", 10))
        name_entry.pack(fill="x", pady=(0, 10))
        name_entry.focus()
        
        # Appearance
        ttk.Label(main_frame, text="Appearance:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        ttk.Label(main_frame, text="Describe physical features, age, eyes, build, style", foreground="gray", font=("Segoe UI", 8)).pack(anchor="w")
        
        appearance_frame = ttk.Frame(main_frame)
        appearance_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.appearance_text = tk.Text(appearance_frame, height=8, wrap="word", font=("Consolas", 9))
        appearance_scroll = ttk.Scrollbar(appearance_frame, command=self.appearance_text.yview)
        self.appearance_text.configure(yscrollcommand=appearance_scroll.set)
        
        # Add placeholder text
        placeholder = """Light/medium/dark skin tone with natural features and [hair description].
- Young/mature [demographics], [age range]
- [Eye color] eyes with [expression style]
- [Body type] build with [posture description]
- Makeup: [preference]
- Fabrics: [preferences]
- Accessories: [signature items]"""
        self.appearance_text.insert("1.0", placeholder)
        self.appearance_text.config(foreground="gray")
        
        # Bind events to clear placeholder
        def on_focus_in(event):
            if self.appearance_text.get("1.0", "end").strip() == placeholder.strip():
                self.appearance_text.delete("1.0", "end")
                self.appearance_text.config(foreground="black")
        
        def on_focus_out(event):
            if not self.appearance_text.get("1.0", "end").strip():
                self.appearance_text.insert("1.0", placeholder)
                self.appearance_text.config(foreground="gray")
        
        self.appearance_text.bind("<FocusIn>", on_focus_in)
        self.appearance_text.bind("<FocusOut>", on_focus_out)
        
        self.appearance_text.pack(side="left", fill="both", expand=True)
        appearance_scroll.pack(side="right", fill="y")
        
        # Default outfit
        ttk.Label(main_frame, text="Default Outfit:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        ttk.Label(main_frame, text="Use sections: Top, Bottom, Footwear, Accessories, Hair/Makeup", foreground="gray", font=("Segoe UI", 8)).pack(anchor="w")
        
        outfit_frame = ttk.Frame(main_frame)
        outfit_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.outfit_text = tk.Text(outfit_frame, height=6, wrap="word", font=("Consolas", 9))
        outfit_scroll = ttk.Scrollbar(outfit_frame, command=self.outfit_text.yview)
        self.outfit_text.configure(yscrollcommand=outfit_scroll.set)
        
        # Add outfit placeholder
        outfit_placeholder = """- **Top:** [Description]
- **Bottom:** [Description]
- **Footwear:** [Description or "None specified"]
- **Accessories:** [Description]
- **Hair/Makeup:** [Description]"""
        self.outfit_text.insert("1.0", outfit_placeholder)
        self.outfit_text.config(foreground="gray")
        
        def on_outfit_focus_in(event):
            if self.outfit_text.get("1.0", "end").strip() == outfit_placeholder.strip():
                self.outfit_text.delete("1.0", "end")
                self.outfit_text.config(foreground="black")
        
        def on_outfit_focus_out(event):
            if not self.outfit_text.get("1.0", "end").strip():
                self.outfit_text.insert("1.0", outfit_placeholder)
                self.outfit_text.config(foreground="gray")
        
        self.outfit_text.bind("<FocusIn>", on_outfit_focus_in)
        self.outfit_text.bind("<FocusOut>", on_outfit_focus_out)
        
        self.outfit_text.pack(side="left", fill="both", expand=True)
        outfit_scroll.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Create Character", command=self._create_character).pack(side="right")
        
        # Bind Enter key to create
        self.dialog.bind("<Return>", lambda e: self._create_character())
        self.dialog.bind("<Escape>", lambda e: self._cancel())
    
    def _on_template_selected(self, event=None):
        """Handle template selection from dropdown."""
        template_name = self.template_var.get()
        template_data = get_character_template(template_name)
        
        if not template_data:
            return
        
        # Update description label
        self.template_desc_label.config(text=get_character_template_description(template_name))
        
        # Get template content
        appearance = template_data.get("appearance", "")
        outfit = template_data.get("outfit", "")
        
        # Clear existing content and placeholders
        self.appearance_text.delete("1.0", "end")
        self.outfit_text.delete("1.0", "end")
        
        # If blank template, restore placeholders
        if template_name == "Blank":
            appearance_placeholder = """Light/medium/dark skin tone with natural features and [hair description].
- Young/mature [demographics], [age range]
- [Eye color] eyes with [expression style]
- [Body type] build with [posture description]
- Makeup: [preference]
- Fabrics: [preferences]
- Accessories: [signature items]"""
            self.appearance_text.insert("1.0", appearance_placeholder)
            self.appearance_text.config(foreground="gray")
            
            outfit_placeholder = """- **Top:** [Description]
- **Bottom:** [Description]
- **Footwear:** [Description or "None specified"]
- **Accessories:** [Description]
- **Hair/Makeup:** [Description]"""
            self.outfit_text.insert("1.0", outfit_placeholder)
            self.outfit_text.config(foreground="gray")
        else:
            # Insert template content with normal text color
            if appearance:
                self.appearance_text.insert("1.0", appearance)
                self.appearance_text.config(foreground="black")
            
            if outfit:
                self.outfit_text.insert("1.0", outfit)
                self.outfit_text.config(foreground="black")
        
        # Focus on name field so user can start typing character name
        self.name_var.set("")
        self.dialog.after(50, lambda: self.dialog.focus_set())
    
    def _cancel(self):
        """Cancel and close dialog."""
        self.dialog.destroy()
    
    def _create_character(self):
        """Validate and create the character file."""
        name = self.name_var.get().strip()
        appearance = self.appearance_text.get("1.0", "end").strip()
        outfit = self.outfit_text.get("1.0", "end").strip()
        
        # Check if appearance is still placeholder
        appearance_placeholder = """Light/medium/dark skin tone with natural features and [hair description].
- Young/mature [demographics], [age range]
- [Eye color] eyes with [expression style]
- [Body type] build with [posture description]
- Makeup: [preference]
- Fabrics: [preferences]
- Accessories: [signature items]"""
        
        outfit_placeholder = """- **Top:** [Description]
- **Bottom:** [Description]
- **Footwear:** [Description or "None specified"]
- **Accessories:** [Description]
- **Hair/Makeup:** [Description]"""
        
        # Validate
        if not name:
            messagebox.showerror("Validation Error", "Please enter a character name.", parent=self.dialog)
            return
        
        if not appearance or appearance == appearance_placeholder:
            messagebox.showerror("Validation Error", "Please enter an appearance description.", parent=self.dialog)
            return
        
        # Create filename from character name (sanitize)
        filename = name.lower().replace(" ", "_").replace("-", "_")
        # Remove special characters
        filename = "".join(c for c in filename if c.isalnum() or c == "_")
        filename = f"{filename}.md"
        
        # Check if file already exists
        chars_dir = self.data_loader.base_dir / "characters"
        chars_dir.mkdir(parents=True, exist_ok=True)
        file_path = chars_dir / filename
        
        if file_path.exists():
            overwrite = messagebox.askyesno(
                "File Exists", 
                f"A character file '{filename}' already exists. Overwrite?",
                parent=self.dialog
            )
            if not overwrite:
                return
        
        # Create markdown content
        # Use placeholder if outfit wasn't filled in
        outfit_content = outfit if outfit and outfit != outfit_placeholder else "A simple outfit."
        
        content = f"""### {name}
**Appearance:**
{appearance}

**Outfits:**

#### Base
{outfit_content}
"""
        
        # Write file
        try:
            file_path.write_text(content, encoding="utf-8")
            messagebox.showinfo(
                "Success", 
                f"Character '{name}' created successfully!\n\nFile: {filename}",
                parent=self.dialog
            )
            self.result = name
            self.dialog.destroy()
            if self.on_success:
                self.on_success()
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Failed to create character file:\n{str(e)}",
                parent=self.dialog
            )
    
    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result
