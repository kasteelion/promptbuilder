# -*- coding: utf-8 -*-
"""Preview panel for displaying generated prompts."""

import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Callable, Optional

from utils import logger
from utils.notification import notify


class PreviewPanel:
    """Right-side panel showing formatted prompt preview."""

    def __init__(
        self,
        parent: ttk.Frame,
        theme_manager,
        on_reload: Callable[[], None],
        on_randomize: Callable[[], None],
        status_callback: Optional[Callable[[str], None]] = None,
        clear_callback: Optional[Callable[[], None]] = None,
        toast_callback: Optional[Callable[[str, str, int], None]] = None,
    ):
        """Initialize preview panel.

        Args:
            parent: Parent widget
            theme_manager: ThemeManager instance
            on_reload: Callback for reload button
            on_randomize: Callback for randomize button
        """
        self.parent = parent
        self.theme_manager = theme_manager
        self.on_reload = on_reload
        self.on_randomize = on_randomize
        self.status_callback = status_callback
        self.clear_callback = clear_callback
        self.toast_callback = toast_callback

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the preview panel UI."""
        self.parent.rowconfigure(1, weight=1)
        self.parent.columnconfigure(0, weight=1)

        # Header with buttons - use grid to properly constrain right-side elements
        hdr = ttk.Frame(self.parent, style="TFrame")
        hdr.grid(row=0, column=0, sticky="ew", padx=6, pady=4)
        hdr.columnconfigure(0, weight=1)  # Left title expands, right controls stay fixed

        ttk.Label(hdr, text="📄 Prompt Preview", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        # Right-side controls in a sub-frame so they don't wrap
        controls_frame = ttk.Frame(hdr, style="TFrame")
        controls_frame.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Copy menu button
        copy_menu_btn = ttk.Menubutton(controls_frame, text="Copy", style="TButton")
        copy_menu_btn.pack(side="left", padx=2)

        copy_menu = tk.Menu(copy_menu_btn, tearoff=0)
        copy_menu_btn["menu"] = copy_menu
        copy_menu.add_command(label="Full Prompt", command=self.copy_prompt, accelerator="Ctrl+C")
        copy_menu.add_separator()
        copy_menu.add_command(
            label="Characters Section", command=lambda: self._copy_section("characters")
        )
        copy_menu.add_command(label="Scene Section", command=lambda: self._copy_section("scene"))
        copy_menu.add_command(label="Notes Section", command=lambda: self._copy_section("notes"))

        # Save button
        ttk.Button(controls_frame, text="Save", command=self.save_prompt).pack(side="left", padx=2)

        # Clear button (clears preview and calls optional clear callback in host)
        ttk.Button(controls_frame, text="Clear", command=self._on_clear).pack(side="left", padx=2)

        # Randomize button
        ttk.Button(controls_frame, text="🎲 Randomize", command=self.on_randomize).pack(
            side="left", padx=2
        )

        # Reload button
        ttk.Button(controls_frame, text="🔄 Reload", command=self.on_reload).pack(
            side="left", padx=2
        )

        # Preview text widget
        self.preview_text = scrolledtext.ScrolledText(self.parent, wrap="word")
        self.preview_text.grid(row=1, column=0, sticky="nsew")

        # Bind Ctrl+C for copy and Ctrl+S for save
        self.preview_text.bind("<Control-c>", lambda e: self.copy_prompt())
        self.preview_text.bind("<Control-s>", lambda e: self.save_prompt())

        # Styling for tags is applied by ThemeManager via `apply_preview_theme`

        # Callback for getting current prompt
        self.get_prompt_callback = None
        self.validate_callback = None
        self.randomize_callback = None

    def _on_theme_selected(self, event):
        """Handle theme selection change."""
        self.on_theme_change(self.theme_var.get())

    def set_callbacks(self, get_prompt, validate, randomize):
        """Set callbacks for getting prompt data.

        Args:
            get_prompt: Function that returns current prompt text
            validate: Function that returns validation error or None
            randomize: Function that randomizes the prompt
        """
        self.get_prompt_callback = get_prompt
        self.validate_callback = validate
        self.randomize_callback = randomize

    def update_preview(self, prompt_text):
        """Update preview with formatted prompt text.

        Args:
            prompt_text: Generated prompt string
        """
        self._format_markdown_preview(prompt_text)

    def clear_preview(self):
        """Clear the preview and show the welcome message."""
        try:
            self.preview_text.delete("1.0", "end")
            self._show_welcome_message()
        except Exception:
            logger.exception("Auto-captured exception")

    def _on_clear(self):
        """Handler for Clear button: clear preview and call host clear callback if provided."""
        self.clear_preview()
        if self.clear_callback:
            try:
                self.clear_callback()
            except Exception:
                logger.exception("Clear callback raised an exception")

    def _format_markdown_preview(self, prompt):
        """Parse and format the prompt with Markdown support."""
        self.preview_text.delete("1.0", "end")

        # Show welcome message if prompt is empty or just whitespace
        if not prompt or not prompt.strip():
            from config import WELCOME_MESSAGE

            self.preview_text.insert("1.0", WELCOME_MESSAGE)
            self.preview_text.tag_add("section_label", "1.0", "end")
            return

        if prompt.startswith("--- VALIDATION ERROR ---"):
            self.preview_text.insert("1.0", prompt)
            self.preview_text.tag_add("error", "1.0", "end")
            return

        lines = prompt.split("\n")

        for line in lines:
            # Empty lines
            if not line.strip():
                self.preview_text.insert("end", "\n")
                continue

            # Separators (---)
            if line.strip() == "---":
                self.preview_text.insert("end", line + "\n", "separator")
                continue

            # Headers: # Header (h1), ## Header (h2), ### Header (h3)
            if line.startswith("### "):
                self.preview_text.insert("end", line[4:] + "\n", "h3")
                continue
            elif line.startswith("## "):
                self.preview_text.insert("end", line[3:] + "\n", "h2")
                continue
            elif line.startswith("# "):
                self.preview_text.insert("end", line[2:] + "\n", "h1")
                continue

            # Section headers like **APPEARANCE:** or **CHARACTER 1: NAME**
            if line.startswith("**") and line.endswith(":**"):
                label = line[2:-3]  # Remove ** and :**
                self.preview_text.insert("end", label + ":\n", "section_label")
                continue

            # List items (- or *)
            if line.lstrip().startswith("- ") or line.lstrip().startswith("* "):
                bullet = "• "
                rest = line.lstrip()[2:]
                self._insert_with_markdown(bullet + rest)
                self.preview_text.insert("end", "\n")
                continue

            # Regular text with inline markdown
            self._insert_with_markdown(line)
            self.preview_text.insert("end", "\n")

    def _insert_with_markdown(self, text):
        """Insert text while processing inline Markdown (**bold**, `code`, *italic*)."""
        # Process the text for inline markdown
        pos = 0

        while pos < len(text):
            # Find next markdown marker
            bold_start = text.find("**", pos)
            code_start = text.find("`", pos)
            italic_start = text.find("*", pos)

            # Determine which comes first
            markers = []
            if bold_start >= 0:
                markers.append((bold_start, "bold", 2))
            if code_start >= 0:
                markers.append((code_start, "code", 1))
            if (
                italic_start >= 0 and text[italic_start : italic_start + 2] != "**"
            ):  # Not part of bold
                markers.append((italic_start, "italic", 1))

            if not markers:
                # No more markers, insert rest of text
                self.preview_text.insert("end", text[pos:])
                break

            # Get the first marker
            marker_pos, marker_type, marker_len = min(markers, key=lambda x: x[0])

            # Insert text before marker
            if marker_pos > pos:
                self.preview_text.insert("end", text[pos:marker_pos])

            # Find closing marker
            if marker_type == "bold":
                close_pos = text.find("**", marker_pos + 2)
                if close_pos > marker_pos + 2:
                    content = text[marker_pos + 2 : close_pos]
                    self.preview_text.insert("end", content, "bold")
                    pos = close_pos + 2
                else:
                    # No closing marker, treat as literal
                    self.preview_text.insert("end", text[marker_pos : marker_pos + 2])
                    pos = marker_pos + 2

            elif marker_type == "code":
                close_pos = text.find("`", marker_pos + 1)
                if close_pos > marker_pos:
                    content = text[marker_pos + 1 : close_pos]
                    self.preview_text.insert("end", content, "code")
                    pos = close_pos + 1
                else:
                    # No closing marker
                    self.preview_text.insert("end", "`")
                    pos = marker_pos + 1

            elif marker_type == "italic":
                close_pos = text.find("*", marker_pos + 1)
                if close_pos > marker_pos and text[close_pos : close_pos + 2] != "**":
                    content = text[marker_pos + 1 : close_pos]
                    self.preview_text.insert("end", content, "italic")
                    pos = close_pos + 1
                else:
                    # No closing marker
                    self.preview_text.insert("end", "*")
                    pos = marker_pos + 1

    def _show_welcome_message(self):
        """Display welcome message for new users when preview is empty."""
        welcome_text = (
            "* Welcome to Prompt Builder! *\n\n"
            "To get started:\n"
            "1. Select a character from the dropdown below\n"
            "2. Click '+ Add to Group' to add them to your scene\n"
            "3. Choose their outfit and pose\n"
            "4. Add more characters if you'd like\n"
            "5. Optionally select a scene preset or write your own\n"
            "6. Watch your prompt appear here!\n\n"
            "Need help?\n"
            "- Use 'Create New Character' to design your own character\n"
            "- Try the 'Randomize' button for inspiration\n"
            "- Check the Edit Data tab to customize everything\n\n"
            "---\n\n"
            "Ready when you are! Add your first character to begin."
        )

        self.preview_text.delete(1.0, "end")

        # Process the welcome text with markdown formatting
        lines = welcome_text.split("\n")
        for i, line in enumerate(lines):
            if line.strip() == "---":
                # Horizontal separator
                self.preview_text.insert("end", "─" * 60 + "\n", "separator")
            elif line.startswith("* ") and line.endswith(" *"):
                # Title (centered style)
                title = line[2:-2]
                self.preview_text.insert("end", title + "\n", "h1")
            elif line.strip().startswith(("-", "•")):
                # Bullet list item
                self.preview_text.insert("end", line + "\n", "list_item")
            elif re.match(r"^\d+\.", line.strip()):
                # Numbered list item
                self.preview_text.insert("end", line + "\n", "list_item")
            else:
                # Regular text
                self.preview_text.insert("end", line + "\n")

    def copy_prompt(self):
        """Copy current prompt to clipboard."""
        if not self.validate_callback or not self.get_prompt_callback:
            return

        error = self.validate_callback()
        if error:
            messagebox.showwarning("Cannot Copy", error)
            return

        prompt = self.get_prompt_callback()
        self.parent.clipboard_clear()
        self.parent.clipboard_append(prompt)
        # Prefer toast (most visible), then status bar, then modal dialog
        if self.toast_callback:
            try:
                self.toast_callback("Prompt copied to clipboard", "success", 2500)
            except Exception:
                logger.exception("Toast callback failed while copying prompt")
        elif self.status_callback:
            try:
                self.status_callback("Prompt copied to clipboard")
            except Exception:
                logger.exception("Status callback failed while copying prompt")
        else:
            messagebox.showinfo("Success", "Prompt copied to clipboard")

    def _copy_section(self, section_type):
        """Copy specific section of prompt to clipboard.

        Args:
            section_type: Type of section ('characters', 'scene', 'notes')
        """
        if not self.get_prompt_callback:
            return

        prompt = self.get_prompt_callback()
        lines = prompt.split("\n")

        section_text = ""
        capture = False

        if section_type == "characters":
            # Capture from first character to scene section
            for line in lines:
                if line.startswith("**CHARACTER") or line.startswith("**APPEARANCE"):
                    capture = True
                elif line.startswith("## Scene") or line.startswith("**SCENE"):
                    break
                if capture:
                    section_text += line + "\n"

        elif section_type == "scene":
            # Capture scene section
            for line in lines:
                if line.startswith("## Scene") or line.startswith("**SCENE"):
                    capture = True
                elif (
                    line.startswith("## Notes")
                    or line.startswith("**NOTES")
                    or line.startswith("---")
                ):
                    if capture:
                        break
                if capture:
                    section_text += line + "\n"

        elif section_type == "notes":
            # Capture notes section
            for line in lines:
                if line.startswith("## Notes") or line.startswith("**NOTES"):
                    capture = True
                if capture:
                    section_text += line + "\n"

        if section_text.strip():
            self.parent.clipboard_clear()
            self.parent.clipboard_append(section_text.strip())
            # Prefer toast, then status, then modal
            if self.toast_callback:
                try:
                    self.toast_callback(
                        f"{section_type.capitalize()} section copied to clipboard", "success", 2500
                    )
                except Exception:
                    logger.exception("Toast callback failed while copying section")
            elif self.status_callback:
                try:
                    self.status_callback(f"{section_type.capitalize()} section copied to clipboard")
                except Exception:
                    logger.exception("Status callback failed while copying section")
            else:
                notify(
                    self.parent.winfo_toplevel(),
                    "Success",
                    f"{section_type.capitalize()} section copied to clipboard",
                    level="success",
                    duration=2500,
                    parent=self.parent.winfo_toplevel(),
                )
        else:
            # Prefer toast -> status -> modal for missing section info
            info_msg = f"No {section_type} section found in prompt"
            if self.toast_callback:
                try:
                    self.toast_callback(info_msg, "info", 3000)
                except Exception:
                    logger.exception("Auto-captured exception")
                    pass
            elif self.status_callback:
                try:
                    self.status_callback(info_msg)
                except Exception:
                    logger.exception("Auto-captured exception")

                    notify(
                        self.parent.winfo_toplevel(),
                        "Info",
                        info_msg,
                        level="info",
                        duration=3000,
                        parent=self.parent.winfo_toplevel(),
                    )
            else:
                notify(
                    self.parent.winfo_toplevel(),
                    "Info",
                    info_msg,
                    level="info",
                    duration=3000,
                    parent=self.parent.winfo_toplevel(),
                )

    def save_prompt(self):
        """Save current prompt to file."""
        if not self.validate_callback or not self.get_prompt_callback:
            return

        error = self.validate_callback()
        if error:
            messagebox.showwarning("Cannot Save", error)
            return

        prompt = self.get_prompt_callback()
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                Path(filename).write_text(prompt, encoding="utf-8")
                # Prefer toast, then status, then modal
                if self.toast_callback:
                    try:
                        # Use info level so it's visible but not green
                        self.toast_callback(f"Prompt saved to {filename}", "info", 3000)
                    except Exception:
                        logger.exception("Toast callback failed while saving prompt")
                elif self.status_callback:
                    try:
                        self.status_callback(f"Prompt saved to {filename}")
                    except Exception:
                        logger.exception("Status callback failed while saving prompt")
                else:
                    notify(
                        self.parent.winfo_toplevel(),
                        "Saved",
                        f"Prompt saved to {filename}",
                        level="info",
                        duration=3000,
                        parent=self.parent.winfo_toplevel(),
                    )
            except Exception:
                logger.exception("Failed to save prompt to file")
                messagebox.showerror("Save Error", "Could not save prompt; see log for details")
