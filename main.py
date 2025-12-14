"""Entrypoint shim for Prompt Builder.

Delegates startup to the `Runner` class in `runner.py` so the
application lifecycle is centralized and easier to test.
"""

import sys

from runner import Runner


def main(argv=None) -> int:
    """Run the application via the Runner class.

    Accepts an optional argv list for testing; returns an exit code.
    """
    return Runner().run(argv)


if __name__ == "__main__":
    sys.exit(main())
# -*- coding: utf-8 -*-
"""Entry point for Prompt Builder application."""

import sys
import logging

from debug_log import close_debug_log, init_debug_log, log


# Note: avoid import-time side effects. Initialize logging and parse CLI
# inside `main()` so importing this module doesn't start the app.

from cli import parse_cli  # local module for CLI parsing


def _check_python_compatibility() -> None:
    """Exit if Python version is unsupported."""
    if sys.version_info < (3, 8):
        from compat import print_version_error

        print_version_error()
        sys.exit(1)






def main(argv=None):
    """Main entry point for the application.

    The debug log is closed in a finally block so that logs are flushed on
    any exit path. The function accepts `argv` to make it easier to call from
    tests if needed.
    """
    # Initialize runtime-only concerns (logging, CLI, compatibility)
    init_debug_log()
    log("Starting Prompt Builder...", level=20)

    cli_args = parse_cli(argv or sys.argv[1:])

    # Check Python compatibility before importing GUI-related modules
    _check_python_compatibility()

    if cli_args.version:
        log("Prompt Builder", level=logging.INFO)
        log(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", level=logging.INFO)
        log(f"Platform: {sys.platform}", level=logging.INFO)
        close_debug_log()
        return 0

    if cli_args.check_compat:
        try:
            from compat import print_compatibility_report

            print_compatibility_report()
        except ImportError:
            log("Compatibility module not found. Basic checks passed.", level=logging.INFO)
        close_debug_log()
        return 0

    # Now that checks are done, ensure tkinter is available and import app
    try:
        import tkinter as tk  # imported into local scope
    except ImportError:
        from compat import print_tkinter_error

        print_tkinter_error()
        close_debug_log()
        return 1

    # Import app modules now that tkinter is available
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
        log("Application closed by user.", level=logging.INFO)
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
        log("An unexpected error occurred. See promptbuilder_debug.log for details.", level=logging.ERROR)

        # Re-raise in debug mode for developers
        if 'cli_args' in locals() and cli_args.debug:
            raise
        return 1
    finally:
        # Ensure debug log is closed and flushed on every exit path
        try:
            close_debug_log()
        except Exception:
            # Best-effort cleanup; nothing else we can do safely here
            pass


from runner import Runner


def main(argv=None):
    """Compatibility shim: use `Runner` to run the application.

    Keeping a simple `main()` here preserves the original entrypoint
    layout while delegating logic to `Runner` for modularity.
    """
    return Runner().run(argv)


if __name__ == "__main__":
    sys.exit(main())
