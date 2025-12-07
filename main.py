
# -*- coding: utf-8 -*-
"""Entry point for Prompt Builder application."""

import sys

# Check Python version compatibility FIRST (before any other imports)
if sys.version_info < (3, 8):
    print("=" * 70)
    print("ERROR: Python Version Too Old")
    print("=" * 70)
    print(f"Current version: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print("Required version: Python 3.8 or higher")
    print()
    print("This application requires Python 3.8+ for:")
    print("  - Modern standard library features")
    print("  - Better Unicode support")
    print("  - Security fixes and performance improvements")
    print()
    print("Please upgrade your Python installation:")
    print("  Windows: https://www.python.org/downloads/")
    print("  macOS:   brew install python@3.12")
    print("  Linux:   sudo apt-get install python3.12")
    print("=" * 70)
    sys.exit(1)

# Check tkinter availability
try:
    import tkinter as tk
except ImportError:
    print("=" * 70)
    print("ERROR: tkinter Not Available")
    print("=" * 70)
    print("tkinter is required but not installed.")
    print()
    print("Installation instructions:")
    print("  Ubuntu/Debian:  sudo apt-get install python3-tk")
    print("  Fedora/RHEL:    sudo dnf install python3-tkinter")
    print("  Arch Linux:     sudo pacman -S tk")
    print("  macOS/Windows:  tkinter should be included with Python")
    print()
    print("If you installed Python from python.org, tkinter should be included.")
    print("If using a system Python, you may need to install it separately.")
    print("=" * 70)
    sys.exit(1)

# Import application modules
from ui import PromptBuilderApp
from config import DEFAULT_WINDOW_GEOMETRY

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
        root = tk.Tk()
        root.geometry(DEFAULT_WINDOW_GEOMETRY)
        app = PromptBuilderApp(root)
        
        root.mainloop()
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        print("\nApplication closed by user.")
        sys.exit(0)
    except Exception as e:
        # Catch any unexpected errors and provide helpful information
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
        print("=" * 70)
        
        # Re-raise in debug mode
        if "--debug" in sys.argv:
            raise
        
        sys.exit(1)


if __name__ == "__main__":
    main()
