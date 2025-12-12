"""Interaction template creator dialog UI."""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from utils import logger
from utils.interaction_template_helpers import (
    get_interaction_template_names,
    get_interaction_template,
    get_interaction_template_description
)


class InteractionCreatorDialog:
    """Dialog for creating new interaction templates."""
    
    def __init__(self, parent, data_loader, on_success_callback):
        """Initialize interaction creator dialog.
        
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
        self.dialog.title("Create New Interaction Template")
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
        
        # Template selection
        template_frame = ttk.Frame(main_frame)
        template_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(template_frame, text="Template:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 5))
        
        self.template_var = tk.StringVar(value="Blank")
        template_combo = ttk.Combobox(
            template_frame, 
            textvariable=self.template_var,
            values=get_interaction_template_names(),
            state="readonly",
            width=28,
            font=("Segoe UI", 9)
        )
        template_combo.pack(side="left", padx=(0, 10))
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)
        
        # Template description label
        self.template_desc_label = ttk.Label(
            template_frame,
            text=get_interaction_template_description("Blank"),
            foreground="gray",
            font=("Segoe UI", 8, "italic")
        )
        self.template_desc_label.pack(side="left")
        
        # Info/help section
        help_frame = ttk.Frame(main_frame, relief="groove", borderwidth=1)
        help_frame.pack(fill="x", pady=(0, 10))
        
        help_label = ttk.Label(
            help_frame, 
            text="💡 Tip: Use {char1}, {char2}, {char3} as placeholders for character names",
            font=("Segoe UI", 9, "bold"),
            foreground="#0066cc"
        )
        help_label.pack(anchor="w", padx=6, pady=4)
        
        example_text = """Placeholder Guide:
• {char1} - First selected character
• {char2} - Second selected character
• {char3} - Third selected character, etc.

Examples:
• "{char1} hugging {char2} warmly"
• "{char1}, {char2}, and {char3} celebrating together"
• "{char1} teaching {char2} while {char3} observes"

The placeholders will be replaced with actual character names when inserted."""
        
        example_widget = tk.Text(
            help_frame,
            font=("Consolas", 8),
            foreground="#555555",
            background="#f0f0f0",
            height=8,
            wrap="word",
            relief="flat",
            borderwidth=0
        )
        example_widget.insert("1.0", example_text)
        example_widget.config(state="disabled")
        example_widget.pack(fill="x", padx=6, pady=(0, 4))
        
        # Template name input
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(name_frame, text="Template Name:", font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))
        
        self.name_entry = ttk.Entry(name_frame, font=("Segoe UI", 9))
        self.name_entry.pack(side="left", fill="x", expand=True)
        
        # Description input
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(desc_frame, text="Description:", font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))
        
        self.desc_entry = ttk.Entry(desc_frame, font=("Segoe UI", 9))
        self.desc_entry.pack(side="left", fill="x", expand=True)
        
        # Content editor
        ttk.Label(main_frame, text="Template Content:", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        
        self.content_text = scrolledtext.ScrolledText(
            main_frame,
            wrap="word",
            height=8,
            font=("Consolas", 10)
        )
        self.content_text.pack(fill="both", expand=True, pady=(0, 10))
        
        # Validation message
        self.validation_label = ttk.Label(
            main_frame,
            text="",
            foreground="red",
            font=("Segoe UI", 8)
        )
        self.validation_label.pack(fill="x", pady=(0, 5))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(
            button_frame,
            text="Create Template",
            command=self._create_template
        ).pack(side="right", padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel
        ).pack(side="right")
    
    def _on_template_selected(self, event):
        """Handle template selection change."""
        template_name = self.template_var.get()
        content = get_interaction_template(template_name)
        desc = get_interaction_template_description(template_name)
        
        # Update description label
        self.template_desc_label.config(text=desc)
        
        # Update content if not blank
        if content:
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", content)
    
    def _validate_inputs(self):
        """Validate user inputs.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        content = self.content_text.get("1.0", "end-1c").strip()
        
        if not name:
            return False, "⚠️ Template name is required"
        
        if not desc:
            return False, "⚠️ Description is required"
        
        if not content:
            return False, "⚠️ Template content is required"
        
        # Check for valid placeholder syntax
        if "{char" in content:
            # Basic validation that placeholders are properly formatted
            import re
            placeholders = re.findall(r'\{char\d+\}', content)
            if not placeholders:
                return False, "⚠️ Placeholders should be in format: {char1}, {char2}, etc."
        
        return True, ""
    
    def _create_template(self):
        """Create the new interaction template."""
        # Validate inputs
        is_valid, error_msg = self._validate_inputs()
        
        if not is_valid:
            self.validation_label.config(text=error_msg)
            return
        
        self.validation_label.config(text="")
        
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        content = self.content_text.get("1.0", "end-1c").strip()
        
        # Get the interactions.md file path
        interactions_file = self.data_loader.base_dir / "data" / "interactions.md"
        
        try:
            # Read current file
            with open(interactions_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Create the new template entry in markdown format
            # Find the last category section or create one
            new_entry = f"\n- **{name}:** {content}\n"
            
            # If there's a description, add it as a comment (optional)
            # For now, we'll just append to the end of the file before any trailing whitespace
            file_content = file_content.rstrip() + new_entry
            
            # Write back to file
            with open(interactions_file, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            logger.info(f"Created new interaction template: {name}")
            
            messagebox.showinfo(
                "Success",
                f"Interaction template '{name}' created successfully!\n\n"
                "The template is now available in the dropdown.",
                parent=self.dialog
            )
            
            self.result = {"name": name, "description": desc, "content": content}
            self.dialog.destroy()
            
            if self.on_success:
                self.on_success()
            
        except Exception as e:
            logger.error(f"Error creating interaction template: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to create interaction template:\n{str(e)}",
                parent=self.dialog
            )
    
    def _cancel(self):
        """Cancel and close the dialog."""
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and wait for it to close.
        
        Returns:
            Result dict or None if cancelled
        """
        self.dialog.wait_window()
        return self.result
