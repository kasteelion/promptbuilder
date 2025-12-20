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

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create New Base Art Style")
        self.dialog.geometry("650x700")
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

        ttk.Label(template_frame, text="Template:", style="Bold.TLabel").pack(
            side="left", padx=(0, 5)
        )

        self.template_var = tk.StringVar(value="Blank")
        template_combo = ttk.Combobox(
            template_frame,
            textvariable=self.template_var,
            values=get_style_template_names(),
            state="readonly",
            width=20,
            font=("Segoe UI", 9),
        )
        template_combo.pack(side="left", padx=(0, 10))
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # Template description label
        self.template_desc_label = ttk.Label(
            template_frame,
            text=get_style_template_description("Blank"),
            style="Muted.TLabel",
        )
        self.template_desc_label.pack(side="left")

        # Info/help section
        help_frame = ttk.Frame(main_frame, relief="groove", borderwidth=1)
        help_frame.pack(fill="x", pady=(0, 10))

        help_label = ttk.Label(
            help_frame,
            text="💡 Tip: Base styles define rendering, character accuracy, body types, hair/clothing, and details",
            style="Accent.TLabel",
        )
        help_label.pack(anchor="w", padx=6, pady=4)

        example_text = """Typical base style sections:
• Rendering - Overall visual style and effects
• Character Accuracy - Feature rendering and expressions
• Body Types - How body shapes are rendered
• Hair & Clothing - Material and style approach
• Details - Additional visual elements and atmosphere"""

        example_widget = tk.Text(
            help_frame,
            font=("Consolas", 8),
            height=5,
            wrap="word",
            relief="flat",
            borderwidth=0,
        )
        example_widget.insert("1.0", example_text)
        example_widget.config(state="disabled")
        example_widget.pack(anchor="w", padx=10, pady=(0, 4), fill="x")

        # Style name
        ttk.Label(main_frame, text="Style Name:", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, font=("Segoe UI", 10))
        name_entry.pack(fill="x", pady=(0, 10))
        name_entry.focus()

        # Style description
        ttk.Label(main_frame, text="Style Description:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        ttk.Label(
            main_frame,
            text="Define the visual characteristics across all sections",
            style="Muted.TLabel",
        ).pack(anchor="w")

        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.description_text = tk.Text(desc_frame, height=20, wrap="word", font=("Consolas", 9))
        desc_scroll = ttk.Scrollbar(desc_frame, command=self.description_text.yview)
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

        # Bind events to clear placeholder
        def on_focus_in(event):
            current = self.description_text.get("1.0", "end").strip()
            if current.startswith("Rendering\n[Describe"):
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

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(button_frame, text="Create Style", command=self._create_style).pack(side="right")

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
