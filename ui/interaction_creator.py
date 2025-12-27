"""Interaction template creator dialog UI."""

import tkinter as tk
from tkinter import messagebox, ttk

from utils import logger
from utils.interaction_template_helpers import (
    get_interaction_template,
    get_interaction_template_description,
    get_interaction_template_names,
)
from utils.notification import notify


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
        self.parent = parent

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("CREATE INTERACTION TEMPLATE")
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
        tm.apply_text_widget_theme(self.content_text, theme)
        
        pbg = theme.get("panel_bg", theme.get("bg", "#1e1e1e"))
        
        # Update cancel btn manual overrides
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.config(bg=pbg, fg=theme.get("fg", "white"), highlightbackground="gray")
            self.cancel_btn._base_bg = pbg

    def _build_ui(self):
        """Build the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=15, style="TFrame")
        main_frame.pack(fill="both", expand=True)

        # Template selection
        template_frame = ttk.Frame(main_frame, style="TFrame")
        template_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(template_frame, text="TEMPLATE:", style="Bold.TLabel").pack(
            side="left", padx=(0, 10)
        )

        self.template_var = tk.StringVar(value="Blank")
        template_combo = ttk.Combobox(
            template_frame,
            textvariable=self.template_var,
            values=get_interaction_template_names(),
            state="readonly",
            width=28,
            font=("Lexend", 9),
        )
        template_combo.pack(side="left", padx=(0, 15))
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # Template description label
        self.template_desc_label = ttk.Label(
            template_frame,
            text=get_interaction_template_description("Blank").upper(),
            style="Muted.TLabel",
        )
        self.template_desc_label.pack(side="left")

        # Info/help section (Refactor 1: Spatial Layout)
        help_frame = ttk.Frame(main_frame, style="TFrame", padding=(15, 10))
        help_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            help_frame,
            text="💡 TIP: USE {char1}, {char2}, {char3} AS PLACEHOLDERS FOR CHARACTER NAMES",
            style="Accent.TLabel",
        ).pack(anchor="w", padx=6, pady=4)

        example_text = """Placeholder Guide:
• {char1} - First selected character
• {char2} - Second selected character
• {char3} - Third selected character, etc.

Examples:
• \"{char1} hugging {char2} warmly\" 
• \"{char1}, {char2}, and {char3} celebrating together\"
• \"{char1} teaching {char2} while {char3} observes\"

The placeholders will be replaced with actual character names when inserted.
"""

        self.example_widget = tk.Text(
            help_frame,
            font=("Lexend", 8),
            height=8,
            wrap="word",
            relief="flat",
            borderwidth=0,
        )
        self.example_widget.insert("1.0", example_text)
        self.example_widget.config(state="disabled")
        self.example_widget.pack(fill="x", padx=6, pady=(0, 4))

        # Template name input
        name_frame = ttk.Frame(main_frame, style="TFrame")
        name_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(name_frame, text="TEMPLATE NAME:", style="Bold.TLabel").pack(
            side="left", padx=(0, 10)
        )

        self.name_entry = ttk.Entry(name_frame, style="TEntry")
        self.name_entry.pack(side="left", fill="x", expand=True)

        # Description input
        desc_frame = ttk.Frame(main_frame, style="TFrame")
        desc_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(desc_frame, text="DESCRIPTION:", style="Bold.TLabel").pack(
            side="left", padx=(0, 10)
        )

        self.desc_entry = ttk.Entry(desc_frame, style="TEntry")
        self.desc_entry.pack(side="left", fill="x", expand=True)

        # Content editor
        ttk.Label(main_frame, text="TEMPLATE CONTENT:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 5)
        )

        # Refactor 3: custom dark scrollbar
        content_frame = ttk.Frame(main_frame, style="TFrame")
        content_frame.pack(fill="both", expand=True, pady=(0, 15))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        self.content_text = tk.Text(
            content_frame, 
            wrap="word", 
            height=8, 
            font=("Lexend", 10),
            relief="flat",
            padx=15,
            pady=15,
            highlightthickness=0,
            borderwidth=0
        )
        self.content_text.grid(row=0, column=0, sticky="nsew")
        
        content_scroll = ttk.Scrollbar(
            content_frame, orient="vertical", command=self.content_text.yview, style="Themed.Vertical.TScrollbar"
        )
        content_scroll.grid(row=0, column=1, sticky="ns")
        self.content_text.configure(yscrollcommand=content_scroll.set)

        # Validation message
        self.validation_label = ttk.Label(
            main_frame, text="", foreground="red", style="Muted.TLabel"
        )
        self.validation_label.pack(fill="x", pady=(0, 5))

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

        ttk.Button(button_frame, text="CREATE TEMPLATE", command=self._create_template, style="TButton").pack(side="right")

        self.dialog.bind("<Escape>", lambda e: self._cancel())

    def _on_template_selected(self, event):
        """Handle template selection change."""
        template_name = self.template_var.get()
        content = get_interaction_template(template_name)
        desc = get_interaction_template_description(template_name)

        # Update description label
        self.template_desc_label.config(text=desc.upper())

        # Update content if not blank
        if content:
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", content)

    def _validate_inputs(self):
        """Validate user inputs."""
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        content = self.content_text.get("1.0", "end-1c").strip()

        if not name:
            return False, "⚠️ TEMPLATE NAME IS REQUIRED"
        if not desc:
            return False, "⚠️ DESCRIPTION IS REQUIRED"
        if not content:
            return False, "⚠️ TEMPLATE CONTENT IS REQUIRED"

        return True, ""

    def _create_template(self):
        """Create the new interaction template."""
        is_valid, error_msg = self._validate_inputs()
        if not is_valid:
            self.validation_label.config(text=error_msg)
            return

        self.validation_label.config(text="")
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        content = self.content_text.get("1.0", "end-1c").strip()

        interactions_file = self.data_loader.base_dir / "data" / "interactions.md"

        try:
            with open(interactions_file, "r", encoding="utf-8") as f:
                file_content = f.read()

            new_entry = f"\n- **{name}:** {content}\n"
            file_content = file_content.rstrip() + new_entry

            with open(interactions_file, "w", encoding="utf-8") as f:
                f.write(file_content)

            root = self.dialog.winfo_toplevel()
            msg = f"Interaction template '{name}' created successfully!"
            notify(root, "Success", msg, level="success", duration=3000, parent=self.dialog)
            self.result = {"name": name, "description": desc, "content": content}
            self.dialog.destroy()
            if self.on_success:
                self.on_success()
        except Exception as e:
            logger.error(f"Error creating interaction template: {e}")
            messagebox.showerror("Error", f"Failed to create interaction template:\n{str(e)}", parent=self.dialog)

    def _cancel(self):
        """Cancel and close the dialog."""
        self.dialog.destroy()

    def show(self):
        """Show the dialog and wait for it to close."""
        self.dialog.wait_window()
        return self.result