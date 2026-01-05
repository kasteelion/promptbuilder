"""Base style creator dialog UI."""

import tkinter as tk
from tkinter import messagebox, ttk

from utils import get_style_template, get_style_template_description, get_style_template_names


class BaseStyleCreatorDialog:
    """Dialog for creating new base art style prompts."""

    def __init__(self, parent, data_loader, on_success_callback):
        """Initialize base style creator dialog.

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
        self.dialog.title("CREATE NEW BASE ART STYLE")
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
        except Exception:
            pass

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

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
        if self.description_text.get("1.0", "2.0").lower().startswith("rendering"):
            try:
                tm = self.parent.theme_manager
                theme = tm.themes.get(tm.current_theme, {})
                pfg = theme.get("placeholder_fg", "#666666")
            except Exception:
                pfg = "#666666"
            self.description_text.config(foreground=pfg)
        else:
            self.description_text.config(foreground=theme.get("text_fg", "white"))

    def _build_ui(self):
        """Build the base style creator UI."""
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
            values=get_style_template_names(),
            state="readonly",
            width=20,
            font=("Lexend", 9),
        )
        template_combo.pack(side="left", padx=(0, 15))
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # Template description label
        self.template_desc_label = ttk.Label(
            template_frame,
            text=get_style_template_description("Blank").upper(),
            style="Muted.TLabel",
        )
        self.template_desc_label.pack(side="left")

        # Info/help section (Refactor 1: Spatial Layout)
        help_frame = ttk.Frame(main_frame, style="TFrame", padding=(15, 10))
        help_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            help_frame,
            text="💡 TIP: BASE STYLES DEFINE RENDERING, CHARACTER ACCURACY, BODY TYPES, HAIR/CLOTHING, AND DETAILS",
            style="Accent.TLabel",
        ).pack(anchor="w", padx=6, pady=4)

        example_text = """Typical base style sections:
• Rendering - Overall visual style and effects
• Character Accuracy - Feature rendering and expressions
• Body Types - How body shapes are rendered
• Hair & Clothing - Material and style approach
• Details - Additional visual elements and atmosphere"""

        self.example_widget = tk.Text(
            help_frame,
            font=("Consolas", 8),
            height=5,
            wrap="word",
            relief="flat",
            borderwidth=0
        )
        self.example_widget.insert("1.0", example_text)
        self.example_widget.config(state="disabled")
        self.example_widget.pack(anchor="w", padx=10, pady=(0, 4), fill="x")

        # Style name
        ttk.Label(main_frame, text="STYLE NAME:", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, style="TEntry")
        self.name_entry.pack(fill="x", pady=(0, 15))
        self.name_entry.focus()

        # Style description
        ttk.Label(main_frame, text="STYLE DESCRIPTION:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        ttk.Label(
            main_frame,
            text="Define the visual characteristics across all sections",
            style="Muted.TLabel",
        ).pack(anchor="w")

        desc_frame = ttk.Frame(main_frame, style="TFrame")
        desc_frame.pack(fill="both", expand=True, pady=(0, 15))

        self.description_text = tk.Text(
            desc_frame, 
            height=20, 
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

        # Add placeholder text with example format
        placeholder = """Rendering
[Describe the overall visual rendering style, lighting approach, effects, textures, and color treatment]

Character Accuracy
[Define how character features are rendered, expression style, and accuracy level]

Body Types
[Describe how body shapes and proportions are rendered in this style]

Hair & Clothing
Hair: [Hair rendering approach and typical styles]
Clothing: [Fabric types, textures, and how clothing is rendered]

Details
[Additional visual elements, atmosphere, accessories approach, and environmental integration]"""

        self.description_text.insert("1.0", placeholder)

        # Bind events to clear placeholder
        def on_focus_in(event):
            current = self.description_text.get("1.0", "end").strip()
            if current.startswith("Rendering\n[Describe"):
                self.description_text.delete("1.0", "end")
                self.description_text.config(foreground="")

        def on_focus_out(event):
            if not self.description_text.get("1.0", "end").strip():
                self.description_text.insert("1.0", placeholder)
                try:
                    tm = self.winfo_toplevel().theme_manager
                    theme = tm.themes.get(tm.current_theme, {})
                    pfg = theme.get("placeholder_fg", "#666666")
                except Exception:
                    pfg = "#666666"
                self.description_text.config(foreground=pfg)

        self.description_text.bind("<FocusIn>", on_focus_in)
        self.description_text.bind("<FocusOut>", on_focus_out)

        self.description_text.pack(side="left", fill="both", expand=True)
        desc_scroll.pack(side="right", fill="y")

        # Buttons (Refactor 3: Hierarchy)
        button_frame = ttk.Frame(main_frame, style="TFrame")
        button_frame.pack(fill="x", pady=(10, 0))

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
            except Exception:
                hbg = "#333333"
            self.cancel_btn.config(bg=hbg)
        def on_c_leave(e):
            self.cancel_btn.config(bg=getattr(self.cancel_btn, "_base_bg", "#1e1e1e"))
        self.cancel_btn.bind("<Enter>", on_c_enter)
        self.cancel_btn.bind("<Leave>", on_c_leave)

        ttk.Button(button_frame, text="CREATE STYLE", command=self._create_style, style="TButton").pack(side="right")

        # Bind Escape to cancel
        self.dialog.bind("<Escape>", lambda e: self._cancel())

    def _on_template_selected(self, event=None):
        """Handle template selection from dropdown."""
        template_name = self.template_var.get()
        template_data = get_style_template(template_name)

        if not template_data:
            return

        # Update description label
        self.template_desc_label.config(text=get_style_template_description(template_name))

        # Get template content
        content = template_data.get("content", "")

        # Clear existing content
        self.description_text.delete("1.0", "end")

        # If blank template, restore placeholder
        if template_name == "Blank":
            placeholder = """Rendering
[Describe the overall visual rendering style, lighting approach, effects, textures, and color treatment]

Character Accuracy
[Define how character features are rendered, expression style, and accuracy level]

Body Types
[Describe how body shapes and proportions are rendered in this style]

Hair & Clothing
Hair: [Hair rendering approach and typical styles]
Clothing: [Fabric types, textures, and how clothing is rendered]

Details
[Additional visual elements, atmosphere, accessories approach, and environmental integration]

---

Example:
Rendering
High-contrast, dark rendering with strong neon lighting. Heavy volumetric fog effects. Chromatic aberration for retro-futuristic feel. High saturation in lights only.

Character Accuracy
Stylized features with sharp, angular aesthetic. Stoic expressions. Dynamic asymmetrical posture.

Body Types
Lean athletic builds. Hard-edged silhouettes with strong rim lighting.

Hair & Clothing
Hair: High-gloss, unnatural colors, wet-look finish
Clothing: Techwear, synthetic fabrics, integrated LED components

Details
Holographic displays, circuit patterns, rain-slicked atmosphere."""
            self.description_text.insert("1.0", placeholder)
            self.description_text.config(foreground="gray")
        else:
            # Insert template content with normal text color
            if content:
                self.description_text.insert("1.0", content)
                self.description_text.config(foreground="black")

    def _cancel(self):
        """Cancel and close dialog."""
        self.dialog.destroy()

    def _create_style(self):
        """Validate and create the base style."""
        name = self.name_var.get().strip()
        description = self.description_text.get("1.0", "end").strip()

        # Validate
        if not name:
            messagebox.showerror(
                "Validation Error", "Please enter a style name.", parent=self.dialog
            )
            return

        # Check if still placeholder
        if not description or description.startswith("Rendering\n[Describe"):
            messagebox.showerror(
                "Validation Error", "Please enter a style description.", parent=self.dialog
            )
            return

        # Read existing base_prompts.md
        prompts_file = self.data_loader.base_dir / "base_prompts.md"

        try:
            if prompts_file.exists():
                content = prompts_file.read_text(encoding="utf-8")
            else:
                content = "# Base Style Prompts\n\nDifferent base style prompts for your character images. Select one from the dropdown in the app.\n\n---\n\n"

            # Add new style section
            new_section = f"\n## {name}\n\n{description}\n\n---\n"
            content += new_section

            # Write back to file
            prompts_file.write_text(content, encoding="utf-8")

            root = self.dialog.winfo_toplevel()
            msg = f"Base style '{name}' created successfully!"
            from utils.notification import notify

            notify(root, "Success", msg, level="success", duration=3000, parent=self.dialog)
            self.result = name
            self.dialog.destroy()
            if self.on_success:
                self.on_success()
        except Exception as e:
            from utils import logger

            logger.exception("Auto-captured exception")
            messagebox.showerror(
                "Error", f"Failed to create base style:\n{str(e)}", parent=self.dialog
            )

    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result
