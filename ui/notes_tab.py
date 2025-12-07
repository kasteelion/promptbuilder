"""Additional notes tab UI."""

import tkinter as tk
from tkinter import ttk


class NotesTab:
    """Tab for additional notes and instructions."""
    
    def __init__(self, parent, on_change_callback):
        """Initialize notes tab.
        
        Args:
            parent: Parent notebook widget
            on_change_callback: Function to call when data changes
        """
        self.parent = parent
        self.on_change = on_change_callback
        
        self.tab = ttk.Frame(parent, style="TFrame")
        parent.add(self.tab, text="Notes")
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the notes tab UI."""
        self.tab.columnconfigure(0, weight=1)
        self.tab.rowconfigure(0, weight=1)

        self.notes_text = tk.Text(self.tab, wrap="word")
        self.notes_text.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.notes_text.bind("<KeyRelease>", lambda e: self.on_change())
    
    def get_notes_text(self):
        """Get current notes text.
        
        Returns:
            str: Notes text content
        """
        return self.notes_text.get("1.0", "end").strip()

    def set_notes_text(self, text):
        """Set the notes text area with new content.
        
        Args:
            text: The text to set.
        """
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", text)
