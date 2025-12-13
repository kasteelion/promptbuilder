"""Application runner that encapsulates startup/shutdown logic.

Provides a `Runner` class with a single `run()` method so the startup
sequence is easy to test and reuse programmatically.
"""
from __future__ import annotations

import sys
import traceback
from typing import Optional

from debug_log import close_debug_log, init_debug_log, log
from cli import parse_cli


class Runner:
    """Encapsulate application lifecycle: init, run, and cleanup.

    This mirrors the previous `main()` logic but keeps startup steps
    grouped in a class for easier testing and potential reuse.
    """

    def __init__(self) -> None:
        self.cli_args = None

    def _check_python_compatibility(self) -> None:
        if sys.version_info < (3, 8):
            from compat import print_version_error

            print_version_error()
            sys.exit(1)

    def _create_root(self, tk, DEFAULT_WINDOW_GEOMETRY: str):
        root = tk.Tk()
        try:
            root.geometry(DEFAULT_WINDOW_GEOMETRY)
        except Exception:
            log("Warning: failed to apply DEFAULT_WINDOW_GEOMETRY", level=30)
        return root

    def run(self, argv: Optional[list[str]] = None) -> int:
        init_debug_log()
        log("Starting Prompt Builder...", level=20)

        self.cli_args = parse_cli(argv or sys.argv[1:])

        self._check_python_compatibility()

        if self.cli_args.version:
            print("Prompt Builder")
            print(
                f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            )
            print(f"Platform: {sys.platform}")
            close_debug_log()
            return 0

        if self.cli_args.check_compat:
            try:
                from compat import print_compatibility_report

                print_compatibility_report()
            except ImportError:
                print("Compatibility module not found. Basic checks passed.")
            close_debug_log()
            return 0

        try:
            import tkinter as tk
        except ImportError:
            from compat import print_tkinter_error

            print_tkinter_error()
            close_debug_log()
            return 1

        # Import application modules now that tkinter is available
        from ui import PromptBuilderApp  # noqa: E402
        from ui.constants import DEFAULT_WINDOW_GEOMETRY  # noqa: E402

        try:
            log("Creating Tkinter root window...")
            root = self._create_root(tk, DEFAULT_WINDOW_GEOMETRY)
            log("Creating PromptBuilderApp...")
            _app = PromptBuilderApp(root)
            log("Entering mainloop...")
            root.mainloop()
            log("Mainloop exited normally")
        except KeyboardInterrupt:
            log("Application closed by user (Ctrl+C)")
            print("Application closed by user.")
            return 0
        except Exception:
            from utils import logger

            logger.exception("Auto-captured exception")
            exc_text = traceback.format_exc()
            log(f"FATAL ERROR: {exc_text}")
            print("An unexpected error occurred. See promptbuilder_debug.log for details.")
            if self.cli_args and getattr(self.cli_args, "debug", False):
                raise
            return 1
        finally:
            try:
                close_debug_log()
            except Exception:
                pass

        return 0


__all__ = ["Runner"]
