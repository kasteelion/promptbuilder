# -*- coding: utf-8 -*-
"""Entry point for Prompt Builder application."""

import sys
import argparse

# Initialize debug logging FIRST
from debug_log import close_debug_log, init_debug_log, log

init_debug_log()
log("Starting Prompt Builder...", level=20)


def parse_cli(argv=None):
    """Parse command-line arguments and return namespace.

    The parser intentionally keeps only the flags we previously supported so
    behavior remains unchanged while making future extensions easier.
    """
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--check-compat", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--version", "-v", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return p.parse_args(argv)


# Check Python version compatibility FIRST (before any other imports)
if sys.version_info < (3, 8):
    from compat import print_version_error

    print_version_error()
    sys.exit(1)


# Parse CLI early so flags behave exactly like before
_cli_args = parse_cli(sys.argv[1:])

if _cli_args.version:
    print("Prompt Builder")
    print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Platform: {sys.platform}")
    close_debug_log()
    sys.exit(0)

if _cli_args.check_compat:
    try:
        from compat import print_compatibility_report

        print_compatibility_report()
    except ImportError:
        print("Compatibility module not found. Basic checks passed.")
    close_debug_log()
    sys.exit(0)


# Check tkinter availability and import app modules only after compatibility checks
try:
    import tkinter as tk
except ImportError:
    from compat import print_tkinter_error

    print_tkinter_error()
    close_debug_log()
    sys.exit(1)

# Import application modules
from ui import PromptBuilderApp  # noqa: E402
from ui.constants import DEFAULT_WINDOW_GEOMETRY  # noqa: E402


def create_root(geometry: str = DEFAULT_WINDOW_GEOMETRY):
    """Create and configure the Tk root window.

    Factored out so the creation is easier to test and reason about.
    """
    root = tk.Tk()
    try:
        root.geometry(geometry)
    except Exception:
        # Non-fatal: if geometry fails, continue with default
        log("Warning: failed to apply DEFAULT_WINDOW_GEOMETRY", level=30)
    return root


def main(argv=None):
    """Main entry point for the application.

    The debug log is closed in a finally block so that logs are flushed on
    any exit path. The function accepts `argv` to make it easier to call from
    tests if needed.
    """
    try:
        log("Creating Tkinter root window...")
        root = create_root()
        log("Creating PromptBuilderApp...")
        _app = PromptBuilderApp(root)
        log("Entering mainloop...")
        root.mainloop()
        log("Mainloop exited normally")
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        log("Application closed by user (Ctrl+C)")
        print("Application closed by user.")
        return 0
    except Exception:
        from utils import logger

        logger.exception("Auto-captured exception")
        # Catch any unexpected errors and provide helpful information
        import traceback

        # Log details to the debug log (file + console via debug_log)
        exc_text = traceback.format_exc()
        log(f"FATAL ERROR: {exc_text}")

        # Give the user a concise message and point them to the debug log
        print("An unexpected error occurred. See promptbuilder_debug.log for details.")

        # Re-raise in debug mode for developers
        if _cli_args.debug:
            raise
        return 1
    finally:
        # Ensure debug log is closed and flushed on every exit path
        try:
            close_debug_log()
        except Exception:
            # Best-effort cleanup; nothing else we can do safely here
            pass


if __name__ == "__main__":
    sys.exit(main())
