"""Entrypoint for the Lite version of Prompt Builder.

This version launches the application without the resource-intensive
character gallery (no image loading), making it faster to start and
lower in memory usage.
"""

import sys
import os
import tkinter as tk
from debug_log import init_debug_log, log, close_debug_log
from utils import font_loader
from ui import PromptBuilderApp

def main(argv=None):
    """Entry point for the Lite application."""
    init_debug_log()
    log("Starting Prompt Builder Lite...", level=20)

    try:
        # Load custom font (Lexend)
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            font_path = os.path.join(base_dir, "ui", "Lexend-VariableFont_wght.ttf")
            
            if os.path.exists(font_path):
                font_loader.load_custom_font(font_path)
            else:
                log(f"Font file not found at expected path: {font_path}", level=30)
                
        except Exception:
            log("Failed to load custom font", level=40)

        # Create root window
        root = tk.Tk()
        root.title("Prompt Builder Lite")
        
        # Default geometry
        try:
            root.geometry("1200x800")
        except Exception:
            pass

        # Launch Lite App
        app = PromptBuilderApp(root, lite_mode=True)
        
        log("Entering mainloop...")
        root.mainloop()
        log("Mainloop exited normally")

    except KeyboardInterrupt:
        log("Application closed by user (Ctrl+C)")
    except Exception:
        import traceback
        log(f"FATAL ERROR: {traceback.format_exc()}", level=40)
    finally:
        close_debug_log()

if __name__ == "__main__":
    sys.exit(main())
