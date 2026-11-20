import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "src"))

from logic.data_loader import DataLoader

def check():
    loader = DataLoader()
    chars = loader.load_characters()
    diego = chars.get("Diego Morales")
    if diego:
        app = diego.get("appearance")
        print(f"Diego Appearance Type: {type(app)}")
        if isinstance(app, dict):
             print(f"Keys: {app.keys()}")
        else:
             print(f"Content: {app[:50]}...")

if __name__ == "__main__":
    check()
