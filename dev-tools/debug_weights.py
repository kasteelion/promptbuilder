import sys
import os
from collections import Counter
import random

# Add CWD to path
sys.path.append(os.getcwd())

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer

print("Initializing DataLoader...")
loader = DataLoader()
base_prompts = loader.load_base_prompts()
print(f"Loaded {len(base_prompts)} base prompts.")

# Initialize Randomizer (passing empty dicts for unused args)
r = PromptRandomizer({}, base_prompts, {})

# Debug Weights
print("\n--- Weight Debug ---")
for k, data in r.base_prompts.items():
    tags = data.get("tags", [])
    w = 1.0
    for t in tags:
        t_str = str(t).lower()
        if t_str.startswith("weight:"):
             w = float(t_str.split(":")[1])
    if w != 1.0:
        print(f"{k}: {w}")

print("\n--- Simulation (1000 Runs) ---")
counts = Counter()
keys = list(r.base_prompts.keys())
weights = []

# Pre-calculate weights to verify the list
for k in keys:
    data = r.base_prompts[k]
    w = 1.0
    if isinstance(data, dict):
        tags = data.get("tags", [])
        for t in tags:
            t_lower = str(t).lower()
            if t_lower.startswith("weight:"):
                try:
                    w = float(t_lower.split(":")[1])
                except ValueError:
                    pass
    weights.append(w)

for _ in range(1000):
   if keys:
       selected = random.choices(keys, weights=weights, k=1)[0]
       counts[selected] += 1

total = sum(counts.values())
for k, v in counts.most_common():
    print(f"{k}: {v} ({v/total*100:.1f}%)")
