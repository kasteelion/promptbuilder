import sys
import os
from pathlib import Path

# Add project root to sys.path
# This assumes conftest.py is in tests/
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
