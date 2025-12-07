"""Markdown file editor tab UI."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from config import MAIN_EDITABLE_FILES


class EditTab:
    """Tab for editing markdown data files."""
    
    def __init__(self, parent, data_loader, on_reload_callback):
        """Initialize edit tab.
        
        Args:
            parent: Parent notebook widget
            data_loader: DataLoader instance
            on_reload_callback: Function to call after saving
        """
        self.parent = parent
        self.data_loader = data_loader
        self.on_reload = on_reload_callback
        
        self.tab = ttk.Frame(parent, style="TFrame")
        parent.add(self.tab, text="Edit Data")
        
        self._build_ui()
        self._refresh_file_list()
        self._load_markdown_for_editing()
    
    def _get_editable_files(self):
        """Get current list of editable files including character files."""
        files = list(MAIN_EDITABLE_FILES)
        
        # Check for character files in characters/ folder
        char_dir = self.data_loader.base_dir / "characters"
        if char_dir.exists() and char_dir.is_dir():
            char_files = sorted([f.name for f in char_dir.glob("*.md")])
            files.extend(char_files)
        
        # Check for legacy characters.md in root
        root_char = self.data_loader.base_dir / "characters.md"
        if root_char.exists() and "characters.md" not in files:
            files.append("characters.md")
        
        return files
    
    def _refresh_file_list(self):
        """Refresh the list of editable files in the dropdown."""
        current_file = self.edit_file_var.get()
        files = self._get_editable_files()
        self.edit_file_combo['values'] = files
        
        # Restore selection if still valid, otherwise select first
        if current_file in files:
            self.edit_file_combo.set(current_file)
        elif files:
            self.edit_file_combo.current(0)
    
    def _build_ui(self):
        """Build the edit tab UI."""
        self.tab.columnconfigure(0, weight=1)
        self.tab.rowconfigure(1, weight=1)

        # Control frame
        control_frame = ttk.Frame(self.tab, style="TFrame")
        control_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        control_frame.columnconfigure(1, weight=1)

        # File selector
        ttk.Label(control_frame, text="File to Edit:").grid(
            row=0, column=0, sticky="w", padx=(0, 4)
        )
        self.edit_file_var = tk.StringVar()
        self.edit_file_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.edit_file_var, 
            state="readonly"
        )
        self.edit_file_combo.grid(row=0, column=1, sticky="ew")
        self.edit_file_combo.bind("<<ComboboxSelected>>", self._on_file_selected)

        # Save button
        self.save_data_btn = ttk.Button(
            control_frame, 
            text="Save & Reload Data", 
            command=self._save_markdown
        )
        self.save_data_btn.grid(row=0, column=2, padx=(10, 0))

        # Editor text widget
        self.editor_text = scrolledtext.ScrolledText(self.tab, wrap="word")
        self.editor_text.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
    
    def _on_file_selected(self, event):
        """Handle file selection change."""
        self._load_markdown_for_editing()
    
    def _load_markdown_for_editing(self):
        """Load selected markdown file into editor."""
        filename = self.edit_file_var.get()
        if not filename:
            return
        
        # Check if it's a character file (from characters/ folder)
        char_dir = self.data_loader.base_dir / "characters"
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
                messagebox.showerror(
                    "File Read Error", 
                    f"Could not read {filename}:\n{str(e)}"
                )
        else:
            self.editor_text.insert(
                "1.0", 
                f"# WARNING: File '{filename}' not found.\n"
                f"# Content will be saved to a new file at {file_path}"
            )
    
    def _save_markdown(self):
        """Save editor content to file and reload data."""
        filename = self.edit_file_var.get()
        if not filename:
            messagebox.showwarning("Save Error", "No file selected for editing.")
            return

        # Check if it's a character file (from characters/ folder)
        char_dir = self.data_loader.base_dir / "characters"
        if char_dir.exists() and (char_dir / filename).exists():
            file_path = char_dir / filename
        else:
            file_path = self.data_loader.base_dir / filename
        
        content = self.editor_text.get("1.0", "end").strip()
        
        try:
            file_path.write_text(content, encoding="utf-8")
            self._refresh_file_list()  # Refresh in case new files were created
            self.on_reload()
            messagebox.showinfo("Success", f"{filename} saved and data reloaded.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not write to {filename}:\n{str(e)}")
