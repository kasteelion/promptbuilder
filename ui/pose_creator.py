"""Pose creator dialog UI."""

import tkinter as tk
from tkinter import messagebox, ttk

from utils import get_pose_template, get_pose_template_description, get_pose_template_names

from .searchable_combobox import SearchableCombobox


class PoseCreatorDialog:
    """Dialog for creating new pose presets."""

    def __init__(self, parent, data_loader, on_success_callback):
        """Initialize pose creator dialog.

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
        self.dialog.title("Create New Pose Preset")
        self.dialog.geometry("550x500")
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
            values=get_pose_template_names(),
            state="readonly",
            width=22,
            font=("Segoe UI", 9),
        )
        template_combo.pack(side="left", padx=(0, 10))
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # Template description label
        self.template_desc_label = ttk.Label(
            template_frame,
            text=get_pose_template_description("Blank"),
            style="Muted.TLabel",
        )
        self.template_desc_label.pack(side="left")

        # Info/help section
        help_frame = ttk.Frame(main_frame, relief="groove", borderwidth=1)
        help_frame.pack(fill="x", pady=(0, 10))

        help_label = ttk.Label(
            help_frame,
            text="💡 Tip: Describe body position, gestures, and facial expression",
            style="Accent.TLabel",
        )
        help_label.pack(anchor="w", padx=6, pady=4)

        example_text = """Example pose format:
• Body position and stance
• Arm and hand placement
• Leg positioning
• Facial expression and gaze direction
• Overall energy/mood of the pose"""

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

        # Category selection
        ttk.Label(main_frame, text="Category:", font=("Segoe UI", 10, "bold")).pack(
            anchor="w", pady=(0, 4)
        )

        cat_frame = ttk.Frame(main_frame)
        cat_frame.pack(fill="x", pady=(0, 10))

        self.category_var = tk.StringVar()
        self.category_combo = SearchableCombobox(
            cat_frame, 
            textvariable=self.category_var, 
            placeholder="Search or type category..."
        )
        self.category_combo.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Load existing categories
        self._load_categories()

        ttk.Label(cat_frame, text="(or type new)", style="Muted.TLabel").pack(side="left")

        # Pose name
        ttk.Label(main_frame, text="Pose Name:", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, font=("Segoe UI", 10))
        name_entry.pack(fill="x", pady=(0, 10))
        name_entry.focus()

        # Description
        ttk.Label(main_frame, text="Pose Description:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        ttk.Label(
            main_frame,
            text="Describe the body position, gestures, and expression",
            style="Muted.TLabel",
        ).pack(anchor="w")

        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.description_text = tk.Text(desc_frame, height=10, wrap="word", font=("Consolas", 9))
        desc_scroll = ttk.Scrollbar(desc_frame, command=self.description_text.yview)
        self.description_text.configure(yscrollcommand=desc_scroll.set)

        # Add placeholder text
        placeholder = """[Body position], [arm/hand placement], [leg positioning], [facial expression and gaze], [overall energy/mood].

Example: Standing confidently with feet shoulder-width apart, arms crossed over chest, slight smile with direct eye contact, relaxed but assertive energy."""
        self.description_text.insert("1.0", placeholder)
        self.description_text.config(foreground="gray")

        # Bind events to clear placeholder
        def on_focus_in(event):
            if self.description_text.get("1.0", "end").strip().startswith("[Body position]"):
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
        ttk.Button(button_frame, text="Create Pose", command=self._create_pose).pack(side="right")

        # Bind Escape to cancel
        self.dialog.bind("<Escape>", lambda e: self._cancel())

    def _on_template_selected(self, event=None):
        """Handle template selection from dropdown."""
        template_name = self.template_var.get()
        template_data = get_pose_template(template_name)

        if not template_data:
            return

        # Update description label
        self.template_desc_label.config(text=get_pose_template_description(template_name))

        # Get template content
        content = template_data.get("content", "")

        # Clear existing content
        self.description_text.delete("1.0", "end")

        # If blank template, restore placeholder
        if template_name == "Blank":
            placeholder = """[Body position], [arm/hand placement], [leg positioning], [facial expression and gaze], [overall energy/mood].

Example: Standing confidently with feet shoulder-width apart, arms crossed over chest, slight smile with direct eye contact, relaxed but assertive energy."""
            self.description_text.insert("1.0", placeholder)
            self.description_text.config(foreground="gray")
        else:
            # Insert template content with normal text color
            if content:
                self.description_text.insert("1.0", content)
                self.description_text.config(foreground="black")

    def _load_categories(self):
        """Load existing pose categories from poses.md."""
        poses_file = self.data_loader.base_dir / "poses.md"
        categories = []

        if poses_file.exists():
            try:
                from logic.parsers import MarkdownParser

                content = poses_file.read_text(encoding="utf-8")
                poses_dict = MarkdownParser.parse_presets(content)
                categories = sorted(list(poses_dict.keys()))
            except Exception as e:
                from utils import logger

                logger.debug(f"Failed to load pose categories from {poses_file}: {e}")

        # Add some default categories if none exist
        if not categories:
            categories = ["Standing", "Sitting", "Action", "Relaxed", "Dynamic"]

        self.category_combo.set_values(categories)

    def _cancel(self):
        """Cancel and close dialog."""
        self.dialog.destroy()

    def _create_pose(self):
        """Validate and create the pose preset."""
        category = self.category_var.get().strip()
        name = self.name_var.get().strip()
        description = self.description_text.get("1.0", "end").strip()

        # Check placeholder
        if not category:
            messagebox.showerror(
                "Validation Error", "Please enter or select a category.", parent=self.dialog
            )
            return

        if not name:
            messagebox.showerror(
                "Validation Error", "Please enter a pose name.", parent=self.dialog
            )
            return

        if not description or description.startswith("[Body position]"):
            messagebox.showerror(
                "Validation Error", "Please enter a pose description.", parent=self.dialog
            )
            return

        # Read existing poses.md
        poses_file = self.data_loader.base_dir / "poses.md"

        try:
            if poses_file.exists():
                content = poses_file.read_text(encoding="utf-8")
            else:
                content = "# Pose Presets\n\nPose descriptions for your characters.\n\n---\n\n"

            # Find or create category section
            if f"## {category}" in content:
                # Add to existing category
                lines = content.split("\n")
                insert_idx = -1

                # Find the category header
                for i, line in enumerate(lines):
                    if line.strip() == f"## {category}":
                        # Find the next section or end
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip().startswith("##") or lines[j].strip() == "---":
                                insert_idx = j
                                break
                        if insert_idx == -1:
                            insert_idx = len(lines)
                        break

                # Insert the new pose
                new_entry = f"\n- **{name}:** {description}\n"
                if insert_idx > 0:
                    lines.insert(insert_idx, new_entry)
                    content = "\n".join(lines)
            else:
                # Create new category section
                new_section = f"\n## {category}\n\n- **{name}:** {description}\n\n---\n"
                content += new_section

            # Write back to file
            poses_file.write_text(content, encoding="utf-8")

            from utils.notification import notify

            root = self.dialog.winfo_toplevel()
            msg = f"Pose '{name}' created in category '{category}'!"
            notify(root, "Success", msg, level="success", duration=3000, parent=self.dialog)
            self.result = (category, name)
            self.dialog.destroy()
            if self.on_success:
                self.on_success()
        except Exception as e:
            from utils import logger

            logger.exception("Auto-captured exception")
            messagebox.showerror("Error", f"Failed to create pose:\n{str(e)}", parent=self.dialog)

    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result
