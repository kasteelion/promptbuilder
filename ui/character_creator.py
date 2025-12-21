"""Character creator dialog UI."""

import tkinter as tk
from tkinter import messagebox, ttk

import logic.parsers as parsers
from logic.parsers import MarkdownParser
from ui.widgets import ScrollableCanvas
from utils import (
    get_character_template,
    get_character_template_description,
    get_character_template_names,
    logger,
)
from utils.notification import notify


class CharacterCreatorDialog:
    """Dialog for creating new characters."""

    def __init__(self, parent, data_loader, on_success_callback, edit_character=None):
        """Initialize character creator dialog.

        Args:
            parent: Parent window
            data_loader: DataLoader instance
            on_success_callback: Function to call after successful creation
            edit_character: Name of character to edit (None for new character)
        """
        self.data_loader = data_loader
        self.on_success = on_success_callback
        self.result = None
        self.edit_character = edit_character

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        if edit_character:
            self.dialog.title(f"Edit Character - {edit_character}")
        else:
            self.dialog.title("Create New Character")
        self.dialog.geometry("600x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._build_ui()

        # Load existing character data if editing
        if edit_character:
            self._load_character_data(edit_character)

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _build_ui(self):
        """Build the dialog UI."""
        # Use a scrollable canvas for main content so fields can scroll while
        # the action buttons remain docked at the bottom.
        scroll = ScrollableCanvas(self.dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        main_frame = scroll.get_container()

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
            values=get_character_template_names(),
            state="readonly",
            width=25,
            font=("Segoe UI", 9),
        )
        template_combo.pack(side="left", padx=(0, 10))
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # Template description label
        self.template_desc_label = ttk.Label(
            template_frame,
            text=get_character_template_description("Blank"),
            style="Muted.TLabel",
        )
        self.template_desc_label.pack(side="left")

        # Info/help section
        help_frame = ttk.Frame(main_frame, relief="groove", borderwidth=1)
        help_frame.pack(fill="x", pady=(0, 10))

        help_label = ttk.Label(
            help_frame,
            text="💡 Tip: Follow the pattern of existing characters for consistency",
            style="Accent.TLabel",
        )
        help_label.pack(anchor="w", padx=6, pady=4)

        example_text = """✓ CORE FEATURES (unchangeable - describe these):
• Skin tone, undertone, finish (matte/dewy/natural)
• Ethnicity, heritage, age range
• Eye color and typical gaze quality
• Body type, proportions, build
• Hair color, texture, natural state (not specific styles)

✓ STYLE NOTES (preferences that inform outfits - flexible):
• Typical makeup approach when applicable
• Fabric preferences for casual/signature looks
• Jewelry preferences (metals, scale) when worn
• General personality/expression tendencies

✗ AVOID: Specific hairstyles, fixed accessories, pose descriptions,
  outfit-specific makeup, or anything that limits scene adaptability"""

        example_widget = tk.Text(
            help_frame,
            font=("Consolas", 8),
            height=7,
            wrap="word",
            relief="flat",
            borderwidth=0,
        )
        example_widget.insert("1.0", example_text)
        example_widget.config(state="disabled")  # Make read-only but still copyable
        example_widget.pack(anchor="w", padx=10, pady=(0, 4), fill="x")

        # Character name
        ttk.Label(main_frame, text="Character Name:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, font=("Segoe UI", 10))
        self.name_entry.pack(fill="x", pady=(0, 10))
        self.name_entry.focus()

        # Modifier selector (replaces Gender)
        ttk.Label(main_frame, text="Outfit Modifier:", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        
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
            main_frame, textvariable=self.modifier_var, values=modifiers, width=6, state="readonly"
        )
        self.modifier_combo.pack(anchor="w", pady=(0, 10))
        create_tooltip(self.modifier_combo, "Determines which shared outfit library (outfits_*.md) is used for this character.")

        # Summary (short)
        ttk.Label(main_frame, text="Summary (short):", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        self.summary_var = tk.StringVar()
        self.summary_entry = ttk.Entry(
            main_frame, textvariable=self.summary_var, font=("Segoe UI", 10)
        )
        self.summary_entry.pack(fill="x", pady=(0, 10))

        # Tags (comma-separated)
        ttk.Label(main_frame, text="Tags (comma-separated):", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        self.tags_var = tk.StringVar()
        self.tags_entry = ttk.Entry(main_frame, textvariable=self.tags_var, font=("Segoe UI", 10))
        self.tags_entry.pack(fill="x", pady=(0, 10))
        # Autocomplete popup for tags
        self._tag_popup = None
        self._available_tags = []
        self._init_tag_autocomplete()

        # Appearance
        ttk.Label(main_frame, text="Appearance:", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(
            main_frame,
            text="Core features (skin, eyes, body, hair quality) + Style notes (preferences, not requirements)",
            style="Muted.TLabel",
        ).pack(anchor="w")

        appearance_frame = ttk.Frame(main_frame)
        appearance_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.appearance_text = tk.Text(
            appearance_frame, height=8, wrap="word", font=("Consolas", 9)
        )
        appearance_scroll = ttk.Scrollbar(appearance_frame, command=self.appearance_text.yview)
        self.appearance_text.configure(yscrollcommand=appearance_scroll.set)

        # Add placeholder text
        placeholder = """[Skin tone] skin with [undertone] and [finish - matte/dewy/natural glow]. [Hair color and texture] hair with natural [quality - e.g., wave, coil, straight].
- [Ethnicity/heritage] [age descriptor], [age range]
- [Eye color] eyes with [gaze quality - e.g., warm, focused, gentle]
- [Body type] build: [proportions and notable features]
- Neutral expression: [personality baseline]; signature [emotion] shows in [how it manifests]
- Typical makeup approach: [style when applicable - e.g., minimal/warm/bold]
- Style preferences: [fabrics, colors, jewelry metals] when choosing outfits
- General vibe: [personality traits that inform styling]"""
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

        # Structured Identity Locks toggle and fields
        self.use_identity_var = tk.BooleanVar(value=False)
        identity_toggle = ttk.Checkbutton(
            main_frame,
            text="Use Identity Locks (structured)",
            variable=self.use_identity_var,
            command=self._toggle_identity_mode,
        )
        identity_toggle.pack(anchor="w", pady=(6, 4))

        # Structured fields container (hidden by default)
        self.structured_frame = ttk.Frame(main_frame)
        # Four primary lines: Body, Face, Hair, Skin
        row = ttk.Frame(self.structured_frame)
        ttk.Label(row, text="Body:", width=10).pack(side="left")
        self.body_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.body_var, width=60).pack(
            side="left", fill="x", expand=True
        )
        row.pack(fill="x", pady=(2, 2))

        row = ttk.Frame(self.structured_frame)
        ttk.Label(row, text="Face:", width=10).pack(side="left")
        self.face_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.face_var, width=60).pack(
            side="left", fill="x", expand=True
        )
        row.pack(fill="x", pady=(2, 2))

        row = ttk.Frame(self.structured_frame)
        ttk.Label(row, text="Hair:", width=10).pack(side="left")
        self.hair_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.hair_var, width=60).pack(
            side="left", fill="x", expand=True
        )
        row.pack(fill="x", pady=(2, 2))

        row = ttk.Frame(self.structured_frame)
        ttk.Label(row, text="Skin:", width=10).pack(side="left")
        self.skin_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.skin_var, width=60).pack(
            side="left", fill="x", expand=True
        )
        row.pack(fill="x", pady=(2, 6))

        # Age / Vibe / Bearing
        row = ttk.Frame(self.structured_frame)
        ttk.Label(row, text="Age Presentation:", width=14).pack(side="left")
        self.age_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.age_var, width=48).pack(side="left", fill="x", expand=True)
        row.pack(fill="x", pady=(2, 2))

        row = ttk.Frame(self.structured_frame)
        ttk.Label(row, text="Vibe / Energy:", width=14).pack(side="left")
        self.vibe_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.vibe_var, width=48).pack(
            side="left", fill="x", expand=True
        )
        row.pack(fill="x", pady=(2, 2))

        row = ttk.Frame(self.structured_frame)
        ttk.Label(row, text="Bearing:", width=14).pack(side="left")
        self.bearing_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.bearing_var, width=48).pack(
            side="left", fill="x", expand=True
        )
        row.pack(fill="x", pady=(2, 6))

        # Initially hide structured_frame
        self.structured_frame.pack_forget()

        # Default outfit
        ttk.Label(main_frame, text="Default Outfit:", style="Bold.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        ttk.Label(
            main_frame,
            text="Use sections: Top, Bottom, Footwear, Accessories, Hair/Makeup",
            style="Muted.TLabel",
        ).pack(anchor="w")

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

        # Make dialog resizable and set a sensible minimum size so controls fit
        try:
            self.dialog.resizable(True, True)
            self.dialog.minsize(520, 420)
        except Exception:
            pass

        # Docked bottom button bar so actions remain visible even when content scrolls
        bottom_btn_frame = ttk.Frame(self.dialog)
        bottom_btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        ttk.Button(bottom_btn_frame, text="Cancel", command=self._cancel).pack(
            side="right", padx=(5, 0)
        )
        self.create_btn = ttk.Button(
            bottom_btn_frame, text="Create Character", command=self._create_character
        )
        self.create_btn.pack(side="right")

        # Bind Enter/Escape keys
        self.dialog.bind("<Return>", lambda e: self._create_character())
        self.dialog.bind("<Escape>", lambda e: self._cancel())

        # Refresh scrollable canvas bindings/region now that content is added
        try:
            scroll.refresh_mousewheel_bindings()
            scroll.update_scroll_region()
        except Exception:
            pass

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
            # If the template appearance matches the identity-locks structure,
            # toggle into structured mode and populate fields; otherwise use freeform.
            parsed = None
            try:
                parsed = MarkdownParser.parse_identity_locks(appearance)
            except Exception:
                parsed = None

            if parsed:
                # populate structured fields and switch mode on
                self.use_identity_var.set(True)
                self._populate_structured_fields(parsed)
                self._toggle_identity_mode()
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

    def _populate_structured_fields(self, parsed: dict):
        try:
            self.body_var.set(parsed.get("Body", ""))
            self.face_var.set(parsed.get("Face", ""))
            self.hair_var.set(parsed.get("Hair", ""))
            self.skin_var.set(parsed.get("Skin", ""))
            self.age_var.set(parsed.get("Age Presentation", ""))
            self.vibe_var.set(parsed.get("Vibe / Energy", ""))
            self.bearing_var.set(parsed.get("Bearing", ""))
        except Exception:
            pass

    def _gather_structured_fields(self) -> dict:
        return {
            "Body": self.body_var.get().strip(),
            "Face": self.face_var.get().strip(),
            "Hair": self.hair_var.get().strip(),
            "Skin": self.skin_var.get().strip(),
            "Age Presentation": self.age_var.get().strip(),
            "Vibe / Energy": self.vibe_var.get().strip(),
            "Bearing": self.bearing_var.get().strip(),
        }

    def _toggle_identity_mode(self):
        """Show or hide structured identity-lock fields."""
        use_struct = bool(self.use_identity_var.get())
        try:
            if use_struct:
                # Hide freeform text and show structured entries
                self.appearance_text.pack_forget()
                self.structured_frame.pack(fill="x", pady=(0, 10))
            else:
                # Show freeform text and hide structured entries
                self.structured_frame.pack_forget()
                self.appearance_text.pack(side="left", fill="both", expand=True)
        except Exception:
            pass

    def _init_tag_autocomplete(self):
        """Initialize tag autocomplete handlers and preload available tags."""
        try:
            # Use DataLoader to fetch known tags (may return only used tags)
            self._available_tags = list(self.data_loader.load_tags() or [])
        except Exception:
            self._available_tags = []

        # Bind events on the tags entry
        self.tags_entry.bind("<KeyRelease>", self._on_tags_keyrelease)
        self.tags_entry.bind("<Down>", self._focus_tag_list)
        self.tags_entry.bind("<FocusOut>", lambda e: self.dialog.after(150, self._hide_tag_popup))

    def _on_tags_keyrelease(self, event=None):
        """Update suggestions when user types in tags entry."""
        # Do not trigger on navigation keys
        if event and event.keysym in ("Up", "Down", "Left", "Right", "Return", "Escape", "Tab"):
            return

        text = self.tags_var.get()
        # Determine the token after the last comma
        if "," in text:
            parts = [p.strip() for p in text.split(",")]
            current = parts[-1]
            existing = set(p.lower() for p in parts[:-1] if p)
        else:
            current = text.strip()
            existing = set()

        if not current:
            self._hide_tag_popup()
            return

        prefix = current.lower()
        suggestions = [
            t
            for t in self._available_tags
            if t.lower().startswith(prefix) and t.lower() not in existing
        ]
        # If no suggestions, hide popup
        if not suggestions:
            self._hide_tag_popup()
            return

        # Limit suggestions
        suggestions = suggestions[:8]
        self._show_tag_popup(suggestions)

    def _show_tag_popup(self, suggestions):
        """Show or update the suggestion popup with given suggestions."""
        try:
            if self._tag_popup and self._tag_popup.winfo_exists():
                listbox = self._tag_popup.listbox
                listbox.delete(0, "end")
            else:
                self._tag_popup = tk.Toplevel(self.dialog)
                self._tag_popup.wm_overrideredirect(True)
                self._tag_popup.attributes("-topmost", True)
                listbox = tk.Listbox(self._tag_popup, height=6)
                listbox.pack(side="left", fill="both", expand=True)
                listbox.bind("<Button-1>", self._on_tag_click)
                listbox.bind("<Return>", self._on_tag_select)
                listbox.bind("<Escape>", lambda e: self._hide_tag_popup())
                listbox.bind("<Double-Button-1>", self._on_tag_select)
                # store for later
                self._tag_popup.listbox = listbox

            # populate
            lb = self._tag_popup.listbox
            lb.delete(0, "end")
            for s in suggestions:
                lb.insert("end", s)

            # position under the entry
            x = self.tags_entry.winfo_rootx()
            y = self.tags_entry.winfo_rooty() + self.tags_entry.winfo_height()
            width = self.tags_entry.winfo_width()
            # set geometry
            self._tag_popup.geometry(f"{width}x{min(150, 24 * len(suggestions))}+{x}+{y}")
            self._tag_popup.deiconify()
        except Exception:
            self._hide_tag_popup()

    def _hide_tag_popup(self):
        try:
            if self._tag_popup and self._tag_popup.winfo_exists():
                self._tag_popup.destroy()
        except Exception:
            pass
        finally:
            self._tag_popup = None

    def _on_tag_click(self, event):
        lb = event.widget
        idx = lb.nearest(event.y)
        if idx is not None:
            self._apply_tag_from_list(lb.get(idx))

    def _on_tag_select(self, event=None):
        if not self._tag_popup or not self._tag_popup.winfo_exists():
            return
        lb = self._tag_popup.listbox
        sel = lb.curselection()
        if not sel:
            return
        value = lb.get(sel[0])
        self._apply_tag_from_list(value)

    def _focus_tag_list(self, event=None):
        if self._tag_popup and self._tag_popup.winfo_exists():
            try:
                self._tag_popup.listbox.focus_set()
                self._tag_popup.listbox.selection_set(0)
            except Exception:
                pass
            return "break"

    def _apply_tag_from_list(self, tag_value):
        """Insert the selected tag into the tags entry, normalizing punctuation."""
        text = self.tags_var.get()
        if "," in text:
            parts = [p.strip() for p in text.split(",")]
            prefix_parts = parts[:-1]
        else:
            prefix_parts = []

        # normalize tag (preserve suggested casing)
        new_parts = prefix_parts + [tag_value]
        new_text = ", ".join(new_parts)
        # add a trailing comma+space so user can continue typing
        new_text = new_text + ", "
        self.tags_var.set(new_text)
        self.tags_entry.icursor("end")
        self._hide_tag_popup()

    def _cancel(self):
        """Cancel and close dialog."""
        self.dialog.destroy()

    def _create_character(self):
        """Validate and create/update the character file."""
        name = self.name_var.get().strip()
        # If structured identity-locks mode is active, build the appearance block
        if getattr(self, "use_identity_var", None) and self.use_identity_var.get():
            try:
                structured = self._gather_structured_fields()
                appearance = MarkdownParser.format_identity_locks(structured)
            except Exception:
                appearance = self.appearance_text.get("1.0", "end").strip()
        else:
            appearance = self.appearance_text.get("1.0", "end").strip()
        outfit = self.outfit_text.get("1.0", "end").strip()
        summary = self.summary_var.get().strip()
        tags_text = self.tags_var.get().strip()
        tags_line = tags_text

        # In edit mode, use the edit_character name
        if self.edit_character:
            name = self.edit_character

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
            messagebox.showerror(
                "Validation Error", "Please enter a character name.", parent=self.dialog
            )
            return

        # Validate name for filesystem safety
        from utils.validation import validate_character_name

        is_valid, error_msg = validate_character_name(name)
        if not is_valid:
            messagebox.showerror("Invalid Character Name", error_msg, parent=self.dialog)
            return

        if not appearance or appearance == appearance_placeholder:
            messagebox.showerror(
                "Validation Error", "Please enter an appearance description.", parent=self.dialog
            )
            return

        # Create filename from character name (sanitize using validation utility)
        from utils.validation import sanitize_filename

        filename = sanitize_filename(name)
        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        # Standardize photo filename to <sanitized_name>_photo.png (lowercase)
        base_name = sanitize_filename(name).lower().replace(" ", "_")
        photo_filename = f"{base_name}_photo.png"
        photo_block = f"**Photo:** {photo_filename}\n"

        # If editing an existing character, try to locate the original file
        # so we overwrite it (preserve metadata like **Photo:**). This
        # searches the characters directory for a file that parses to the
        # same character name. If found, use that file path instead of the
        # sanitized-name-derived path which can create duplicates.
        existing_file_path = None
        if self.edit_character:
            try:
                chars_dir = self.data_loader._find_characters_dir()
                matches = []
                for cf in sorted(chars_dir.glob("*.md")):
                    try:
                        txt = cf.read_text(encoding="utf-8")
                        parsed = MarkdownParser.parse_characters(txt)
                        if self.edit_character in parsed:
                            matches.append((cf, txt))
                    except Exception:
                        continue

                # Prefer a matching file that already contains a **Photo:** line
                chosen = None
                for cf, txt in matches:
                    if parsers._PHOTO_RE.search(txt):
                        chosen = cf
                        break
                if chosen is None and matches:
                    chosen = matches[0][0]

                existing_file_path = chosen
            except Exception:
                existing_file_path = None

        if existing_file_path is not None:
            file_path = existing_file_path
        else:
            # Default new file path under characters directory
            chars_dir = self.data_loader._find_characters_dir()
            chars_dir.mkdir(parents=True, exist_ok=True)
            file_path = chars_dir / filename

        # Check if file already exists (skip check in edit mode)
        chars_dir = self.data_loader._find_characters_dir()
        chars_dir.mkdir(parents=True, exist_ok=True)
        file_path = chars_dir / filename

        if file_path.exists() and not self.edit_character:
            overwrite = messagebox.askyesno(
                "File Exists",
                f"A character file '{filename}' already exists. Overwrite?",
                parent=self.dialog,
            )
            if not overwrite:
                return

        # Create markdown content
        # Use placeholder if outfit wasn't filled in
        outfit_content = outfit if outfit and outfit != outfit_placeholder else "A simple outfit."

        # Insert modifier tag for downstream parsing
        modifier_tag = self.modifier_var.get().strip().upper() if self.modifier_var.get() else "F"

        # Include summary field if provided
        summary_block = f"**Summary:** {summary}\n" if summary else ""
        tags_block = f"**Tags:** {tags_line}\n" if tags_line else ""
        
        content = f"### {name}\n"
        content += f"{summary_block}{tags_block}**Modifier:** {modifier_tag}\n"
        content += f"**Appearance:**\n{appearance}\n\n"
        content += f"**Outfits:**\n\n#### Base\n{outfit_content}\n"

        # Write file
        try:
            # If file exists, create a backup first
            if file_path.exists():
                bak = file_path.with_suffix(file_path.suffix + ".bak")
                if bak.exists():
                    idx = 1
                    while True:
                        candidate = file_path.with_suffix(file_path.suffix + f".bak{idx}")
                        if not candidate.exists():
                            bak = candidate
                            break
                        idx += 1
                import shutil

                shutil.copy(file_path, bak)

                # Preserve existing metadata lines (e.g., **Photo:** and other custom metadata)
                try:
                    existing = file_path.read_text(encoding="utf-8")
                    lines = existing.splitlines()
                    # find header line index (the character section)
                    header_idx = None
                    for i, ln in enumerate(lines):
                        if ln.strip().startswith(f"### {name}"):
                            header_idx = i
                            break

                    # find appearance section index (where metadata ends)
                    appearance_idx = None
                    for i in range(header_idx + 1 if header_idx is not None else 0, len(lines)):
                        if lines[i].strip().lower().startswith("**appearance:"):
                            appearance_idx = i
                            break

                    # Collect preserved metadata lines between header and appearance (excluding summary/tags/gender)
                    preserved_meta = []
                    if header_idx is not None:
                        start = header_idx + 1
                        end = appearance_idx if appearance_idx is not None else len(lines)
                        for ln in lines[start:end]:
                            s = ln.strip()
                            # Skip existing summary/tags/gender lines (we'll write fresh ones)
                            if not s:
                                # preserve blank lines for readability
                                preserved_meta.append(ln)
                                continue
                            low = s.lower()
                            if (
                                low.startswith("**summary:")
                                or low.startswith("**tags:")
                                or low.startswith("**gender:")
                                or low.startswith("**modifier:")
                            ):
                                continue
                            # Skip existing photo lines; we'll write a standardized one
                            if low.startswith("**photo:"):
                                continue
                            # Preserve any other metadata lines
                            preserved_meta.append(ln)

                    # Reconstruct the content: header + preserved metadata + new summary/tags/modifier + rest (appearance/outfits)
                    if header_idx is not None:
                        before = "\n".join(lines[: header_idx + 1])
                        meta_block = "\n".join(preserved_meta).rstrip()
                        # Build new metadata block in a stable order: standardized photo, preserved meta, then summary/tags/modifier
                        # Photo comes first so it's easy to spot in files
                        new_meta_parts = []
                        new_meta_parts.append(photo_block.strip())
                        if meta_block:
                            new_meta_parts.append(meta_block)
                        if summary_block:
                            new_meta_parts.append(summary_block.strip())
                        if tags_block:
                            new_meta_parts.append(tags_block.strip())
                        # modifier is always present
                        new_meta_parts.append(f"**Modifier:** {modifier_tag}")
                        new_meta = "\n".join(new_meta_parts)

                        # Rest of file from appearance onwards (or from end if none)
                        rest = ""
                        if appearance_idx is not None:
                            rest = "\n".join(lines[appearance_idx:])
                        else:
                            # If no appearance marker found, append the rest after header/meta
                            rest = ""

                        content = before + "\n" + new_meta + "\n\n" + rest
                except Exception:
                    # If preservation fails, continue with overwriting but we already made a backup
                    pass

            file_path.write_text(content, encoding="utf-8")
            root = self.dialog.winfo_toplevel()
            msg = (
                f"Character '{name}' updated successfully!"
                if self.edit_character
                else f"Character '{name}' created successfully!\n\nFile: {filename}"
            )
            notify(root, "Success", msg, level="success", duration=3000, parent=self.dialog)
            self.result = name
            self.dialog.destroy()
            if self.on_success:
                self.on_success()
        except Exception:
            logger.exception("Failed to save character file")
            messagebox.showerror(
                "Error", "Failed to save character file; see log for details.", parent=self.dialog
            )

    def _load_character_data(self, character_name):
        """Load existing character data into the form.

        Args:
            character_name: Name of character to load
        """
        try:
            # Load all characters
            characters = self.data_loader.load_characters()
            char_data = characters.get(character_name)

            if not char_data:
                messagebox.showwarning("Not Found", f"Character '{character_name}' not found.")
                return

            # Populate form fields
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, character_name)
            self.name_entry.config(state="readonly")  # Don't allow name changes when editing

            # Load appearance. Prefer structured identity-locks if present.
            appearance = char_data.get("appearance", "")
            parsed = None
            try:
                parsed = MarkdownParser.parse_identity_locks(appearance)
            except Exception:
                parsed = None

            self.appearance_text.delete("1.0", tk.END)
            if parsed:
                # populate structured fields and show structured UI
                self._populate_structured_fields(parsed)
                self.use_identity_var.set(True)
                self._toggle_identity_mode()
            else:
                # freeform fallback
                self.use_identity_var.set(False)
                self._toggle_identity_mode()
                self.appearance_text.insert("1.0", appearance)

            # Load summary
            summary = char_data.get("summary", "")
            try:
                self.summary_var.set(summary)
            except Exception:
                self.summary_var.set("")

            # Load tags
            tags = char_data.get("tags", [])
            try:
                self.tags_var.set(", ".join(tags) if isinstance(tags, (list, tuple)) else str(tags))
            except Exception:
                self.tags_var.set("")

            # Load modifier (fallback to gender, default F)
            modifier = char_data.get("modifier") or char_data.get("gender", "F")
            try:
                self.modifier_var.set(modifier.upper())
            except Exception:
                self.modifier_var.set("F")

            # Load base outfit if exists
            outfits = char_data.get("outfits", {})
            base_outfit = outfits.get("Base", {})
            if isinstance(base_outfit, dict):
                outfit_desc = base_outfit.get("description", "")
            else:
                outfit_desc = str(base_outfit)

            self.outfit_text.delete("1.0", tk.END)
            self.outfit_text.insert("1.0", outfit_desc)

            # Update button text
            self.create_btn.config(text="💾 Save Changes")

        except Exception:
            logger.exception("Failed to load character data")
            messagebox.showerror(
                "Error", "Failed to load character; see log for details.", parent=self.dialog
            )

    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result
