import sys
from pathlib import Path

# Add project root and src/ to sys.path
# This assumes conftest.py is in tests/
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(SRC_DIR))
