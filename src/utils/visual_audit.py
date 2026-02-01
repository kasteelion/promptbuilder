# -*- coding: utf-8 -*-
"""Visual auditing utility to capture app screenshots."""

import os
from PIL import ImageGrab
from utils.debug_log import log

def capture_app_screenshot(path=None):
    """Capture the current screen and save to path."""
    if not path:
        # Default to artifacts dir if we can find it, otherwise current dir
        path = "app_screenshot.png"
    
    try:
        log(f"Capturing screenshot to {path}...")
        # Grab the whole screen (primary monitor)
        screenshot = ImageGrab.grab()
        screenshot.save(path)
        log("Screenshot captured successfully.")
        return True
    except Exception as e:
        log(f"Failed to capture screenshot: {str(e)}", level=30)
        return False
