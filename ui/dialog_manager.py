# -*- coding: utf-8 -*-
"""Dialog management for the application."""

import platform
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Callable, Optional

from config import WELCOME_MESSAGE


class DialogManager:
    """Manages application dialogs (welcome, about, error, shortcuts, etc).

    Provides centralized, consistent dialog creation and display.
    """

    def __init__(self, root: tk.Tk, preferences_manager):
        """Initialize dialog manager.

        Args:
            root: Tkinter root window
            preferences_manager: PreferencesManager instance
        """
        self.root = root
        self.prefs = preferences_manager

    def show_welcome(self) -> None:
        """Show welcome dialog for first-time users."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Welcome to Prompt Builder!")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        # Welcome text
        text = scrolledtext.ScrolledText(dialog, wrap="word", font=("Segoe UI", 10))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", WELCOME_MESSAGE)
        text.config(state="disabled")

        # Don't show again checkbox
        show_again_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(dialog, text="Don't show this again", variable=show_again_var)
        chk.pack(pady=(0, 10))

        def on_close():
            if show_again_var.get():
                self.prefs.set("show_welcome", False)
            dialog.destroy()

        ttk.Button(dialog, text="Get Started!", command=on_close).pack(pady=(0, 10))

        dialog.wait_window()

    def show_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        shortcuts = """
Keyboard Shortcuts

File Operations:
  Ctrl+Shift+S    Save Preset
  Ctrl+Shift+O    Load Preset

Editing:
  Ctrl+Z          Undo
  Ctrl+Y          Redo

View:
  Ctrl+G          Toggle Character Gallery
  Ctrl++          Increase Font Size
  Ctrl+-          Decrease Font Size
  Ctrl+0          Reset Font Size
  Alt+R           Randomize All

Preview Panel:
  Ctrl+C          Copy Prompt
  Ctrl+S          Save Prompt to File

Navigation:
  Tab             Navigate between fields
  Enter           Add character/Apply selection
  Del             Remove selected character
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def show_about(self) -> None:
        """Show about dialog."""
        about_text = f"""Prompt Builder
Version 2.0

A desktop application for building complex AI image prompts.

Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}
Platform: {platform.system()} {platform.release()}

© 2025 - Open Source
"""
        messagebox.showinfo("About Prompt Builder", about_text)

    def show_characters_summary(self, callback: Optional[Callable[[], str]] = None) -> None:
        """Show character appearances summary.

        Args:
            callback: Optional function that generates the summary text
        """
        try:
            # Default to importing summary generator if no callback provided
            if callback is None:
                # Prefer the utils.character_summary helper (moved during refactor)
                try:
                    # Attempt to locate the characters directory under data/ first
                    from pathlib import Path

                    from utils.character_summary import generate_summary

                    project_root = Path(__file__).resolve().parents[1]
                    data_chars = project_root / "data" / "characters"
                    legacy_chars = project_root / "characters"
                    if data_chars.exists():
                        summary = generate_summary(data_chars)
                    elif legacy_chars.exists():
                        summary = generate_summary(legacy_chars)
                    else:
                        # Fallback to default behavior of generate_summary()
                        summary = generate_summary()
                except Exception:
                    from utils import logger

                    logger.exception("Auto-captured exception")
                    # Backwards-compatible fallback to old location if present
                    from characters.summary import generate_summary

                    summary = generate_summary()
            else:
                summary = callback()

            # Create a dialog with options and scrollable text
            dialog = tk.Toplevel(self.root)
            dialog.title("Characters Summary")
            dialog.geometry("800x600")

            # Top controls: checkbox to include base outfit and regenerate
            ctrl_frame = ttk.Frame(dialog)
            ctrl_frame.pack(fill="x", padx=10, pady=(10, 0))

            include_base_var = tk.BooleanVar(value=False)
            include_chk = ttk.Checkbutton(
                ctrl_frame, text="Include Base Outfit", variable=include_base_var
            )
            include_chk.pack(side="left")

            include_style_var = tk.BooleanVar(value=False)
            style_chk = ttk.Checkbutton(
                ctrl_frame, text="Show Style Notes (//)", variable=include_style_var
            )
            style_chk.pack(side="left", padx=(8, 0))

            # Add scrollbar and text widget
            frame = ttk.Frame(dialog)
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side="right", fill="y")

            text_widget = tk.Text(
                frame, wrap="word", yscrollcommand=scrollbar.set, font=("Consolas", 10)
            )
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=text_widget.yview)

            def regenerate_summary(*args):
                try:
                    # Recompute summary using the same discovery logic as above
                    from pathlib import Path

                    project_root = Path(__file__).resolve().parents[1]
                    data_chars = project_root / "data" / "characters"
                    legacy_chars = project_root / "characters"
                    if data_chars.exists():
                        new_summary = generate_summary(
                            data_chars,
                            include_base=include_base_var.get(),
                            include_style=include_style_var.get(),
                        )
                    elif legacy_chars.exists():
                        new_summary = generate_summary(
                            legacy_chars,
                            include_base=include_base_var.get(),
                            include_style=include_style_var.get(),
                        )
                    else:
                        new_summary = generate_summary(
                            include_base=include_base_var.get(), include_style=include_style_var.get()
                        )
                except Exception:
                    from utils import logger

                    logger.exception("Auto-captured exception")
                    new_summary = generate_summary(include_base=include_base_var.get())

                text_widget.config(state="normal")
                text_widget.delete("1.0", "end")
                text_widget.insert("1.0", new_summary)
                text_widget.config(state="disabled")

            # Initial fill
            text_widget.insert("1.0", summary)
            text_widget.config(state="disabled")  # Make read-only

            # Bind checkbox changes to regenerate
            include_base_var.trace_add("write", regenerate_summary)
            include_style_var.trace_add("write", regenerate_summary)

            # Add close button
            close_btn = ttk.Button(dialog, text="Close", command=dialog.destroy)
            close_btn.pack(pady=(0, 10))

        except Exception as e:
            from utils import logger

            logger.exception("Auto-captured exception")
            self.show_error("Error", f"Failed to generate character summary:\n{str(e)}")

    def show_error(self, title: str, error_msg: str, friendly: bool = True) -> None:
        """Show error dialog with optional user-friendly message conversion.

        Args:
            title: Error dialog title
            error_msg: Error message
            friendly: Whether to convert technical errors to user-friendly messages
        """
        if friendly:
            error_msg = self._make_user_friendly(error_msg)

        messagebox.showerror(title, error_msg)

    def show_info(self, title: str, message: str) -> None:
        """Show info dialog.

        Args:
            title: Dialog title
            message: Info message
        """
        # Prefer transient, non-blocking notifications when available:
        # 1) Toast manager on the root window
        # 2) Main window status bar via `_update_status`
        # 3) Fallback to modal messagebox
        root = getattr(self, "root", None)
        try:
            if root is not None and hasattr(root, "toasts"):
                try:
                    # Use 'info' level for neutral messages
                    root.toasts.notify(message, "info", 3000)
                    return
                except Exception:
                    from utils import logger

                    logger.exception("Auto-captured exception")
                    pass
            if root is not None and hasattr(root, "_update_status"):
                try:
                    root._update_status(message)
                    return
                except Exception:
                    from utils import logger

                    logger.exception("Auto-captured exception")
                    pass
        except Exception:
            from utils import logger

            logger.exception("Auto-captured exception")
            # Defensive: if accessing root fails, fall through to modal
            pass

        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str) -> None:
        """Show warning dialog.

        Args:
            title: Dialog title
            message: Warning message
        """
        messagebox.showwarning(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        """Show yes/no confirmation dialog.

        Args:
            title: Dialog title
            message: Question message

        Returns:
            True if user clicked Yes, False otherwise
        """
        return messagebox.askyesno(title, message)

    def ask_ok_cancel(self, title: str, message: str) -> bool:
        """Show OK/Cancel confirmation dialog.

        Args:
            title: Dialog title
            message: Question message

        Returns:
            True if user clicked OK, False otherwise
        """
        return messagebox.askokcancel(title, message)

    def _make_user_friendly(self, error_msg: str) -> str:
        """Convert technical error messages to user-friendly text.

        Args:
            error_msg: Technical error message

        Returns:
            User-friendly error message
        """
        if "FileNotFoundError" in error_msg or "No such file" in error_msg:
            return "File not found. Try clicking 'Reload Data' from the menu."
        elif "PermissionError" in error_msg:
            return "Permission denied. Check file permissions and try again."
        elif "JSONDecodeError" in error_msg:
            return "Invalid file format. The file may be corrupted."
        elif "characters/" in error_msg:
            return "Error loading character files. Check the characters folder."

        return error_msg
