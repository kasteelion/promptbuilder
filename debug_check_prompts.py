from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
import os

# Ensure we are in the right dir
if not os.path.exists("logic"):
    print("Error: Run from project root.")
    exit(1)

loader = DataLoader()
data = loader.load_all()
randomizer = PromptRandomizer(data)

print(f"Loaded {len(randomizer.base_prompts)} base prompts.")
for name, p_data in randomizer.base_prompts.items():
    tags = p_data.get("tags", []) # tags are stored in data dict now
    print(f"Prompt: '{name}' | Tags: {tags}")

print("\nChecking Alias Expansion for 'female':")
expanded = randomizer._expand_tags(["female"])
print(f"Input: 'female' -> Output: {expanded}")

print("\nChecking Match Logic for 'Photorealistic'...")
photorealistic_keys = [k for k in randomizer.base_prompts.keys() if "Photorealistic" in k]
if photorealistic_keys:
    key = photorealistic_keys[0]
    # Check lower case conversion
    p_tags = set(t.lower() for t in randomizer.base_prompts[key]["tags"])
    expanded_lower = set(t.lower() for t in expanded)
    
    intersection = p_tags.intersection(expanded_lower)
    print(f"Target Prompt: {key}")
    print(f"Prompt Tags (Lower): {p_tags}")
    print(f"Context Tags (Lower): {expanded_lower}")
    print(f"Intersection: {intersection}")
    print(f"Is Match? {bool(intersection)}")
else:
    print("Photorealistic prompt NOT FOUND.")
