# -*- coding: utf-8 -*-
"""AI Studio Browser Automation Client.

Re-exports the centralized AIStudioClient from src.utils.ai_client for
backwards compatibility across automation scripts and dev tools.
"""

import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Ensure 'src' is in python path
_src_dir = Path(__file__).resolve().parent.parent.parent / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from utils.ai_client import AIStudioClient, generate_images_simple

__all__ = ["AIStudioClient", "generate_images_simple"]
