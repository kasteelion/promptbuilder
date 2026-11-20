
import sys
import os

sys.path.append(os.getcwd())
try:
    from logic.data_loader import DataLoader
except ImportError:
    # If logic is not in path, try adding current dir
    print("Adjusting path...")
    sys.path.append(os.path.join(os.getcwd(), 'promptbuilder'))
    from logic.data_loader import DataLoader

loader = DataLoader()
chars = loader.load_characters()

print(f"Loaded {len(chars)} characters.")
missing_tags = []
for name, data in chars.items():
    tags = data.get('tags', [])
    if not tags:
        missing_tags.append(name)
        
print(f"Characters with NO tags: {len(missing_tags)}")
for m in missing_tags:
    print(f" - {m}")
