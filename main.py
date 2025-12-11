
# -*- coding: utf-8 -*-
"""Entry point for Prompt Builder application."""

import sys

# Initialize debug logging FIRST
from debug_log import init_debug_log, log, close_debug_log
init_debug_log()
log("Starting Prompt Builder...")

# Check Python version compatibility FIRST (before any other imports)
if sys.version_info < (3, 8):
    from compat import print_version_error
    print_version_error()
    sys.exit(1)

# Check tkinter availability
try:
    import tkinter as tk
except ImportError:
    from compat import print_tkinter_error
    print_tkinter_error()
    sys.exit(1)

# Import application modules
from ui import PromptBuilderApp
from ui.constants import DEFAULT_WINDOW_GEOMETRY

# Optional: Print version info for debugging
if "--version" in sys.argv or "-v" in sys.argv:
    print(f"Prompt Builder")
    print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Platform: {sys.platform}")
    sys.exit(0)

# Optional: Run compatibility check
if "--check-compat" in sys.argv:
    try:
        from compat import print_compatibility_report
        print_compatibility_report()
    except ImportError:
        print("Compatibility module not found. Basic checks passed.")
    sys.exit(0)


def main():
    """Main entry point for the application."""
    try:
        log("Creating Tkinter root window...")
        root = tk.Tk()
        root.geometry(DEFAULT_WINDOW_GEOMETRY)
        log("Creating PromptBuilderApp...")
        app = PromptBuilderApp(root)
        log("Entering mainloop...")
        root.mainloop()
        log("Mainloop exited normally")
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        log("Application closed by user (Ctrl+C)")
        print("\nApplication closed by user.")
        close_debug_log()
        sys.exit(0)
    except Exception as e:
        # Catch any unexpected errors and provide helpful information
        import traceback
        log(f"FATAL ERROR: {type(e).__name__}: {str(e)}")
        log("Full traceback:")
        for line in traceback.format_exc().split('\n'):
            log(line)
        
        print("=" * 70)
        print("UNEXPECTED ERROR")
        print("=" * 70)
        print(f"An error occurred: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print()
        print("If this error persists, please report it with:")
        print(f"  - Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print(f"  - Platform: {sys.platform}")
        print(f"  - Error type: {type(e).__name__}")
        print(f"  - Error message: {str(e)}")
        print(f"  - Debug log saved to: promptbuilder_debug.log")
        print("=" * 70)
        
        close_debug_log()
        
        # Re-raise in debug mode
        if "--debug" in sys.argv:
            raise
        
        sys.exit(1)


if __name__ == "__main__":
    main()
