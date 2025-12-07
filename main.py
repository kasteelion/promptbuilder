
"""Entry point for Prompt Builder application."""

import sys
import tkinter as tk
from ui import PromptBuilderApp
from config import DEFAULT_WINDOW_GEOMETRY


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    root.geometry(DEFAULT_WINDOW_GEOMETRY)
    app = PromptBuilderApp(root)
    
    try:
        root.mainloop()
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
