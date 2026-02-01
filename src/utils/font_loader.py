# -*- coding: utf-8 -*-
"""Utility for loading custom fonts at runtime."""

import ctypes
import os
import platform
from utils import logger

def load_custom_font(font_path: str) -> bool:
    """Load a custom font file into the application session.

    Args:
        font_path: Absolute path to the .ttf or .otf font file.

    Returns:
        bool: True if loaded successfully, False otherwise.
    """
    if platform.system() != "Windows":
        logger.warning("Custom font loading is currently only supported on Windows.")
        return False

    if not os.path.exists(font_path):
        logger.error(f"Font file not found: {font_path}")
        return False

    try:
        # GDI32.AddFontResourceExW
        # FR_PRIVATE = 0x10 (font is private to this process)
        # FR_NOT_ENUM = 0x20 (font is not enumerable)
        FR_PRIVATE = 0x10
        result = ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
        
        if result > 0:
            logger.info(f"Successfully loaded font: {font_path}")
            return True
        else:
            logger.error(f"Failed to load font (GDI Error): {font_path}")
            return False
            
    except Exception as e:
        logger.exception(f"Exception loading font {font_path}: {e}")
        return False
