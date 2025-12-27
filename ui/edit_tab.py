"""Markdown file editor tab UI."""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Callable, List


class EditTab:
    """Tab for editing markdown data files."""

    def __init__(self, parent: ttk.Notebook, data_loader, theme_manager, on_reload_callback: Callable[[], None], existing_frame=None):
        """Initialize edit tab.

        Args:
            parent: Parent notebook widget
            data_loader: DataLoader instance
            theme_manager: ThemeManager instance
            on_reload_callback: Function to call after saving
            existing_frame: Optional frame to use instead of creating a new one
        """
        self.parent = parent
        self.data_loader = data_loader
        self.theme_manager = theme_manager
        self.on_reload = on_reload_callback

        if existing_frame:
            self.tab = existing_frame
        else:
            self.tab = ttk.Frame(parent, style="TFrame")
            parent.add(self.tab, text="Edit Data")

        self._build_ui()
        
        if self.theme_manager:
            self.theme_manager.register_text_widget(self.editor_text)
            
        self._refresh_file_list()
        self._load_markdown_for_editing()

    def _get_editable_files(self) -> List[str]:
        """Get current list of editable files including character files."""
        return self.data_loader.get_editable_files()

    def _refresh_file_list(self):
        """Refresh the list of editable files in the dropdown."""
        current_file = self.edit_file_var.get()
        files = self._get_editable_files()
        self.edit_file_combo["values"] = files

        # Restore selection if still valid, otherwise select first
        if current_file in files:
            self.edit_file_combo.set(current_file)
        elif files:
            self.edit_file_combo.current(0)

    def _build_ui(self):
        """Build the edit tab UI."""
        self.tab.columnconfigure(0, weight=1)
        self.tab.rowconfigure(1, weight=1)

        # Control frame - Refactor 1
        control_frame = ttk.Frame(self.tab, style="TFrame")
        control_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(15, 10))
        control_frame.columnconfigure(1, weight=1)

        # File selector
        ttk.Label(control_frame, text="File to Edit:").grid(
            row=0, column=0, sticky="w", padx=(0, 4)
        )
        self.edit_file_var = tk.StringVar()
        self.edit_file_combo = ttk.Combobox(
            control_frame, textvariable=self.edit_file_var, state="readonly"
        )
        self.edit_file_combo.grid(row=0, column=1, sticky="ew")
        self.edit_file_combo.bind("<<ComboboxSelected>>", self._on_file_selected)

        # Save button
        self.save_data_btn = ttk.Button(
            control_frame, text="Save & Reload Data", command=self._save_markdown
        )
        self.save_data_btn.grid(row=0, column=2, padx=(10, 0))

        # Editor text widget - Refactor 1
        # Refactor 3: custom dark scrollbar
        editor_frame = ttk.Frame(self.tab, style="TFrame")
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 15))
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(0, weight=1)

        self.editor_text = tk.Text(editor_frame, wrap="word", highlightthickness=0, borderwidth=0)
        self.editor_text.grid(row=0, column=0, sticky="nsew")
        
        editor_scroll = ttk.Scrollbar(
            editor_frame, orient="vertical", command=self.editor_text.yview, style="Themed.Vertical.TScrollbar"
        )
        editor_scroll.grid(row=0, column=1, sticky="ns")
        self.editor_text.configure(yscrollcommand=editor_scroll.set)

    def _on_file_selected(self, event):
        """Handle file selection change."""
        self._load_markdown_for_editing()

    def _load_markdown_for_editing(self):
        """Load selected markdown file into editor."""
        filename = self.edit_file_var.get()
        if not filename:
            return

        # Check if it's a character file (from characters/ folder)
        char_dir = self.data_loader._find_characters_dir()
        if char_dir.exists() and (char_dir / filename).exists():
            file_path = char_dir / filename
        else:
            file_path = self.data_loader.base_dir / filename

        self.editor_text.delete("1.0", "end")

        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                self.editor_text.insert("1.0", content)
            except Exception as e:
                from utils import logger

                logger.exception("Auto-captured exception")
                messagebox.showerror("File Read Error", f"Could not read {filename}:\n{str(e)}")
        else:
            self.editor_text.insert(
                "1.0",
                f"# WARNING: File '{filename}' not found.\n"
                f"# Content will be saved to a new file at {file_path}",
            )

    def _save_markdown(self):
        """Save editor content to file and reload data."""
        filename = self.edit_file_var.get()
        if not filename:
            messagebox.showwarning("Save Error", "No file selected for editing.")
            return

        # Check if it's a character file (from characters/ folder)
        char_dir = self.data_loader._find_characters_dir()
        if char_dir.exists() and (char_dir / filename).exists():
            file_path = char_dir / filename
        else:
            file_path = self.data_loader.base_dir / filename

        content = self.editor_text.get("1.0", "end").strip()

        try:
            file_path.write_text(content, encoding="utf-8")
            self._refresh_file_list()  # Refresh in case new files were created
            self.on_reload()
            # Prefer transient notification (toast), then status bar, then modal
            from utils.notification import notify

            root = self.tab.winfo_toplevel()
            msg = f"{filename} saved and data reloaded."
            notify(root, "Success", msg, level="success", duration=3000)
        except PermissionError:
            messagebox.showerror(
                "Permission Denied",
                f"Cannot write to {filename}\n\n"
                f"• File may be open in another program\n"
                f"• Check folder permissions\n"
                f"• Try running as administrator",
            )
        except OSError as e:
            messagebox.showerror("File System Error", f"Could not write to {filename}:\n{str(e)}")
        except Exception as e:
            from utils import logger

            logger.error(f"Unexpected error saving {filename}: {e}", exc_info=True)
            messagebox.showerror("Save Error", f"Unexpected error ({type(e).__name__}):\n{str(e)}")
