"""Entrypoint shim for Prompt Builder.

Keep this file minimal: delegate runtime behavior to `Runner` in
`runner.py` so the startup sequence is easier to test and maintain.
"""

import sys
import os
from core.runner import Runner
from utils import logger, font_loader

def main(argv=None):
    """Entry point for the application."""
    if argv is None:
        argv = sys.argv[1:]

    # Load custom font (Lexend)
    try:
        # Assuming font is in promptbuilder/ui/Lexend-VariableFont_wght.ttf
        # We need to get the absolute path relative to this main.py file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base_dir, "ui", "Lexend-VariableFont_wght.ttf")
        
        if os.path.exists(font_path):
            font_loader.load_custom_font(font_path)
        else:
            logger.warning(f"Font file not found at expected path: {font_path}")
            
    except Exception:
        logger.exception("Failed to load custom font")

    return Runner().run(argv)

if __name__ == "__main__":
    sys.exit(main())
