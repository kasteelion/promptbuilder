import tkinter as tk

class StatusBarComponent:
    """Status Bar component for the main application window."""
    
    def __init__(self, parent: tk.Widget, initial_text="READY", theme_manager=None):
        self.parent = parent
        self.theme_manager = theme_manager
        self.label = None
        self._build(initial_text)

    def _build(self, text):
        """Build the status label."""
        # Default styling
        bg = "#121212"
        fg = "gray"
        
        if self.theme_manager:
            try:
                tm = self.theme_manager
                theme = tm.themes.get(tm.current_theme, {})
                # Prefer panel_bg, then bg
                bg = theme.get("panel_bg", theme.get("bg", "#121212"))
                fg = theme.get("border", "gray")
            except Exception:
                pass

        self.label = tk.Label(
            self.parent,
            text=text,
            anchor="w",
            bg=bg,
            fg=fg,
            font=("Lexend", 8, "bold"),
            padx=15,
            pady=5
        )
        self.label.pack(side="bottom", fill="x")

    def update_status(self, message):
        """Update the status text."""
        if self.label:
            self.label.config(text=message)
            self.label.update_idletasks()

    def apply_theme(self, theme):
        """Update status bar colors."""
        if self.label:
            bg = theme.get("panel_bg", theme.get("bg", "#121212"))
            self.label.config(bg=bg, fg=theme.get("border", "gray"))
