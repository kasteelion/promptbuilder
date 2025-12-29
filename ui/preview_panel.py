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
        header_parent: Optional[ttk.Frame] = None,
    ):
        """Initialize preview panel.

        Args:
            parent: Parent widget
            theme_manager: ThemeManager instance
            on_reload: Callback for reload button
            on_randomize: Callback for randomize button
            header_parent: Optional alternative parent for the header buttons
        """
        self.parent = parent
        self.header_parent = header_parent or parent
        self.theme_manager = theme_manager
        self.on_reload = on_reload
        self.on_randomize = on_randomize
        self.status_callback = status_callback
        self.clear_callback = clear_callback
        self.toast_callback = toast_callback
        self.pill_buttons = [] # Track for theme updates

        self._build_ui()
        
        if self.theme_manager:
            self.theme_manager.register(self.parent, self.apply_theme)
            self.theme_manager.register_preview(self.preview_text)

    def _build_ui(self) -> None:
        """Build the preview panel UI."""
        if self.header_parent == self.parent:
            self.parent.rowconfigure(1, weight=1)
            self.parent.columnconfigure(0, weight=1)
            header_row = 0
        else:
            self.parent.rowconfigure(0, weight=1)
            self.parent.columnconfigure(0, weight=1)
            header_row = 0

        # Header with buttons - Refactor 1
        hdr = ttk.Frame(self.header_parent, style="TFrame")
        if self.header_parent == self.parent:
            hdr.grid(row=header_row, column=0, sticky="ew", padx=12, pady=(15, 10))
        else:
            # When in a separate header (like a CollapsibleFrame header), use grid
            # Position it in column 1 (after the toggle button)
            hdr.grid(row=0, column=1, sticky="ew", padx=(10, 0))
            self.header_parent.columnconfigure(1, weight=1)
            
        hdr.columnconfigure(0, weight=1)

        # Only show title if we're in the default parent
        if self.header_parent == self.parent:
            ttk.Label(hdr, text="📄 Prompt Preview", style="Title.TLabel").grid(
                row=0, column=0, sticky="w"
            )

        # Right-side controls - Use grid for better layout control
        controls_frame = ttk.Frame(hdr, style="TFrame")
        controls_frame.grid(row=0, column=1, sticky="e", padx=(5, 0))
        
        # Configure button grid
        controls_frame.columnconfigure(0, weight=0)
        controls_frame.columnconfigure(1, weight=0)
        controls_frame.columnconfigure(2, weight=0)

        # Get current theme for manual button overrides
        theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})

        # Helper for Pill buttons in Phase 3
        def add_pill_btn(parent, text, command, row, col):
            pbg = theme.get("panel_bg", theme.get("text_bg", "#1e1e1e"))
            accent = theme.get("accent", "#0078d7")
            
            # Outer Frame (The Border)
            pill = tk.Frame(parent, bg=accent, padx=1, pady=1)
            pill.grid(row=row, column=col, padx=2, pady=2)
            
            # Inner Label (The hollow center)
            lbl = tk.Label(
                pill, 
                text=text, 
                bg=pbg, 
                fg=accent,
                font=("Lexend", 9, "bold"), # Refactor 5
                padx=12,
                pady=3,
                cursor="hand2"
            )
            lbl.pack()
            
            # Hover restoration storage
            lbl._base_bg = pbg
            
            def on_enter(e, l=lbl):
                try:
                    theme = self.theme_manager.themes.get(self.theme_manager.current_theme, {})
                    hbg = theme.get("hover_bg", "#333333")
                except: hbg = "#333333"
                l.config(bg=hbg)
            def on_leave(e, l=lbl):
                l.config(bg=getattr(l, "_base_bg", "#1e1e1e"))
                
            lbl.bind("<Enter>", on_enter)
            lbl.bind("<Leave>", on_leave)
            lbl.bind("<Button-1>", lambda e: command())
            
            self.pill_buttons.append((pill, lbl))
            return pill

        # Refactor 3: Pill style for Copy, Save, Clear, Randomize, Reload
        # Row 0: Generation/Data Actions
        add_pill_btn(controls_frame, "🎲 Randomize", self.on_randomize, 0, 1)
        add_pill_btn(controls_frame, "🔄 Reload", self.on_reload, 0, 2)

        # Row 1: File/Clipboard Actions
        add_pill_btn(controls_frame, "📋 Copy", self._show_copy_menu_pill, 1, 0)
        # Store for menu access
        self.copy_btn_frame, self.copy_btn_lbl = self.pill_buttons[-1]

        add_pill_btn(controls_frame, "💾 Save", self.save_prompt, 1, 1)
        add_pill_btn(controls_frame, "🗑️ Clear", self._on_clear, 1, 2)

        # Quick Actions Row (New)
        # We'll use a slightly different style for these secondary quick-actions
        quick_frame = ttk.Frame(hdr, style="TFrame")
        quick_frame.grid(row=0, column=0, sticky="w", padx=(15, 0))
        
        def add_quick_link(parent, text, command, tooltip):
            btn = tk.Button(
                parent, text=text, command=command,
                bg=theme.get("panel_bg", "#1e1e1e"), 
                fg=theme.get("accent", "#0078d7"),
                borderwidth=0, relief="flat", cursor="hand2",
                font=("Lexend", 8, "bold", "underline")
            )
            btn.pack(side="left", padx=5)
            from utils import create_tooltip
            create_tooltip(btn, tooltip)
            return btn

        self.quick_copy_btn = add_quick_link(quick_frame, "⚡ QUICK COPY", self.copy_prompt, "Copy full prompt immediately")
        self.open_editor_btn = add_quick_link(quick_frame, "📝 OPEN IN EDITOR", self._open_in_external_editor, "Open prompt in system default text editor")

        # Preview text widget with scrollbar - Refactor 1
        # Refactor 3: Switch to custom dark scrollbar
        text_frame = ttk.Frame(self.parent, style="TFrame")
        text_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 15))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.preview_text = tk.Text(text_frame, wrap="word", highlightthickness=0, borderwidth=0)
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        
        preview_scroll = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.preview_text.yview, style="Themed.Vertical.TScrollbar"
        )
        preview_scroll.grid(row=0, column=1, sticky="ns")
        self.preview_text.configure(yscrollcommand=preview_scroll.set)

        # Bind Ctrl+C for copy and Ctrl+S for save
        self.preview_text.bind("<Control-c>", lambda e: self.copy_prompt())
        self.preview_text.bind("<Control-s>", lambda e: self.save_prompt())

        # Callback for getting current prompt
        self.get_prompt_callback = None
        self.validate_callback = None
        self.randomize_callback = None

    def _open_in_external_editor(self):
        """Save current prompt to a temp file and open in system default editor."""
        if not self.get_prompt_callback:
            return
            
        error = self.validate_callback() if self.validate_callback else None
        if error:
            if self.toast_callback: self.toast_callback(error, "warning", 3500)
            return

        prompt = self.get_prompt_callback()
        import tempfile
        import os
        import subprocess
        import platform

        try:
            # Create a named temporary file that persists after closing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tf:
                tf.write(prompt)
                temp_path = tf.name

            if platform.system() == "Windows":
                os.startfile(temp_path)
            elif platform.system() == "Darwin": # macOS
                subprocess.run(["open", temp_path])
            else: # Linux
                subprocess.run(["xdg-open", temp_path])
                
            if self.toast_callback:
                self.toast_callback("Opening in external editor...", "info", 2000)
        except Exception as e:
            logger.exception("Failed to open external editor")
            messagebox.showerror("Error", f"Could not open editor: {e}")

    def _show_copy_menu_pill(self):
        """Show the copy dropdown menu at the pill button location."""
        copy_menu = tk.Menu(self.copy_btn_lbl, tearoff=0)
        copy_menu.add_command(label="Full Prompt", command=self.copy_prompt, accelerator="Ctrl+C")
        copy_menu.add_separator()
        copy_menu.add_command(
            label="Characters Section", command=lambda: self._copy_section("characters")
        )
        copy_menu.add_command(label="Scene Section", command=lambda: self._copy_section("scene")
        )
        copy_menu.add_command(label="Notes Section", command=lambda: self._copy_section("notes")
        )
        
        # Position menu under button
        x = self.copy_btn_lbl.winfo_rootx()
        y = self.copy_btn_lbl.winfo_rooty() + self.copy_btn_lbl.winfo_height()
        copy_menu.post(x, y)

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

    def apply_theme(self, theme):
        """Apply theme to custom widgets. (Refactor 3)"""
        accent = theme.get("accent", "#0078d7")
        panel_bg = theme.get("panel_bg", theme.get("text_bg", "#1e1e1e"))
        
        if hasattr(self, "pill_buttons"):
            for frame, lbl in self.pill_buttons:
                frame.config(bg=accent)
                lbl._base_bg = panel_bg
                lbl.config(bg=panel_bg, fg=accent)
                
        # Update quick links
        if hasattr(self, "quick_copy_btn"):
            self.quick_copy_btn.config(bg=panel_bg, fg=accent)
        if hasattr(self, "open_editor_btn"):
            self.open_editor_btn.config(bg=panel_bg, fg=accent)

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
            if line.startswith("**") and line.endswith("::"):
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
            # Prefer toast -> status -> modal for validation warnings
            if self.toast_callback:
                try:
                    self.toast_callback(error, "warning", 3500)
                except Exception:
                    logger.exception("Toast callback failed while copying prompt (warning)")
            elif self.status_callback:
                try:
                    self.status_callback(error)
                except Exception:
                    logger.exception("Status callback failed while copying prompt (warning)")
            else:
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
            # Prefer toast -> status -> modal for validation warnings
            if self.toast_callback:
                try:
                    self.toast_callback(error, "warning", 3500)
                except Exception:
                    logger.exception("Toast callback failed while saving prompt (warning)")
            elif self.status_callback:
                try:
                    self.status_callback(error)
                except Exception:
                    logger.exception("Status callback failed while saving prompt (warning)")
            else:
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