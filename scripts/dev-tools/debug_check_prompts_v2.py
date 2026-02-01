from logic.data_loader import DataLoader
import os
import sys

# Add project root to sys path if needed
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    loader = DataLoader() # Defaults to current dir structure
    print("Loading base prompts...")
    prompts = loader.load_base_prompts()
    print(f"Loaded {len(prompts)} prompts.")

    for k in prompts:
        tags = prompts[k].get('tags', [])
        print(f"Key: '{k}' | Tags: {tags}")
        
        if "Photorealistic" in k:
            print(f"--> Found Photorealistic! Tags: {tags}")

except Exception as e:
    import traceback
    traceback.print_exc()
