# -*- coding: utf-8 -*-
"""Entry point for Prompt Builder application."""

import sys

# Initialize debug logging FIRST
from debug_log import close_debug_log, init_debug_log, log

init_debug_log()
log("Starting Prompt Builder...", level=20)

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
from ui import PromptBuilderApp  # noqa: E402
from ui.constants import DEFAULT_WINDOW_GEOMETRY  # noqa: E402

# Optional: Print version info for debugging
if "--version" in sys.argv or "-v" in sys.argv:
    print("Prompt Builder")
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
        _app = PromptBuilderApp(root)
        log("Entering mainloop...")
        root.mainloop()
        log("Mainloop exited normally")
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        log("Application closed by user (Ctrl+C)")
        # Keep console output minimal for CLI users
        print("Application closed by user.")
        close_debug_log()
        sys.exit(0)
    except Exception as e:
        from utils import logger

        logger.exception("Auto-captured exception")
        # Catch any unexpected errors and provide helpful information
        import traceback

        # Log details to the debug log (file + console via debug_log)
        log(f"FATAL ERROR: {type(e).__name__}: {str(e)}")
        log("Full traceback:")
        for line in traceback.format_exc().split("\n"):
            log(line)

        # Give the user a concise message and point them to the debug log
        print("An unexpected error occurred. See promptbuilder_debug.log for details.")

        close_debug_log()

        # Re-raise in debug mode for developers
        if "--debug" in sys.argv:
            raise

        sys.exit(1)


if __name__ == "__main__":
    main()
