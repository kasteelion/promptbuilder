"Pose creator dialog UI."

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
        self.parent = parent

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("CREATE POSE PRESET")
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
            border_color = theme.get("border", theme.get("muted_fg", "gray"))
            self.cancel_btn.config(bg=pbg, fg=theme.get("fg", "white"), highlightbackground=border_color)
            self.cancel_btn._base_bg = pbg

        if hasattr(self, "category_combo"): self.category_combo.apply_theme(theme)

        # Handle placeholders
        if self.description_text.get("1.0", "2.0").lower().startswith("[body position]"):
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
            values=get_pose_template_names(),
            state="readonly",
            width=22,
            font=("Lexend", 9),
        )
        template_combo.pack(side="left", padx=(0, 15))
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # Template description label
        self.template_desc_label = ttk.Label(
            template_frame,
            text=get_pose_template_description("Blank").upper(),
            style="Muted.TLabel",
        )
        self.template_desc_label.pack(side="left")

        # Info/help section (Refactor 1: Spatial Layout)
        help_frame = ttk.Frame(main_frame, style="TFrame", padding=(15, 10))
        help_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            help_frame,
            text="💡 TIP: DESCRIBE BODY POSITION, GESTURES, AND FACIAL EXPRESSION",
            style="Accent.TLabel",
        )
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

        self.example_widget = tk.Text(
            help_frame,
            font=("Lexend", 8),
            height=5,
            wrap="word",
            relief="flat",
            borderwidth=0,
        )
        self.example_widget.insert("1.0", example_text)
        self.example_widget.config(state="disabled")
        self.example_widget.pack(anchor="w", padx=10, pady=(0, 4), fill="x")

        # Category selection
        ttk.Label(main_frame, text="CATEGORY:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )

        cat_frame = ttk.Frame(main_frame, style="TFrame")
        cat_frame.pack(fill="x", pady=(0, 15))

        self.category_var = tk.StringVar()
        self.category_combo = SearchableCombobox(
            cat_frame,
            theme_manager=self.theme_manager,
            textvariable=self.category_var,
            values=[""] + sorted(list(getattr(self, "poses", {}).keys())), # Assuming self.poses might be set elsewhere or is empty
            on_select=lambda v: getattr(self, "_update_preset_list", lambda: None)(), # Assuming _update_preset_list might be set elsewhere
            placeholder="Search category...",
            width=25
        )
        self.category_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Load existing categories
        self._load_categories()

        # Pose name
        ttk.Label(main_frame, text="POSE NAME:", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, style="TEntry")
        name_entry.pack(fill="x", pady=(0, 15))
        name_entry.focus()

        # Description
        ttk.Label(main_frame, text="POSE DESCRIPTION:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        ttk.Label(
            main_frame,
            text="Describe the body position, gestures, and expression",
            style="Muted.TLabel",
        ).pack(anchor="w")

        desc_frame = ttk.Frame(main_frame, style="TFrame")
        desc_frame.pack(fill="both", expand=True, pady=(0, 15))

        self.description_text = tk.Text(
            desc_frame, 
            height=10, 
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

        # Add placeholder text
        placeholder = """[Body position], [arm/hand placement], [leg positioning], [facial expression and gaze], [overall energy/mood].

Example: Standing confidently with feet shoulder-width apart, arms crossed over chest, slight smile with direct eye contact, relaxed but assertive energy."""
        self.description_text.insert("1.0", placeholder)

        # Bind events to clear placeholder
        def on_focus_in(event):
            if self.description_text.get("1.0", "end").strip().startswith("[Body position]"):
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
        def on_c_leave(e): self.cancel_btn.config(bg=getattr(self.cancel_btn, "_base_bg", pbg))
        self.cancel_btn.bind("<Enter>", on_c_enter)
        self.cancel_btn.bind("<Leave>", on_c_leave)

        ttk.Button(button_frame, text="CREATE POSE", command=self._create_pose, style="TButton").pack(side="right")

        self.dialog.bind("<Escape>", lambda e: self._cancel())

    def _on_template_selected(self, event=None):
        """Handle template selection from dropdown."""
        template_name = self.template_var.get()
        template_data = get_pose_template(template_name)

        if not template_data:
            return

        # Update description label
        self.template_desc_label.config(text=get_pose_template_description(template_name).upper())

        # Get template content
        content = template_data.get("content", "")

        # Clear existing content
        self.description_text.delete("1.0", "end")

        # If blank template, restore placeholder
        if template_name == "Blank":
            placeholder = """[Body position], [arm/hand placement], [leg positioning], [facial expression and gaze], [overall energy/mood].

Example: Standing confidently with feet shoulder-width apart, arms crossed over chest, slight smile with direct eye contact, relaxed but assertive energy."""
            self.description_text.insert("1.0", placeholder)
            try:
                tm = self.winfo_toplevel().theme_manager
                theme = tm.themes.get(tm.current_theme, {})
                pfg = theme.get("placeholder_fg", "#666666")
            except: pfg = "#666666"
            self.description_text.config(foreground=pfg)
        else:
            # Insert template content with normal text color
            if content:
                self.description_text.insert("1.0", content)
                self.description_text.config(foreground="")

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