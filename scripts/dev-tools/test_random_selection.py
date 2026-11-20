import os
import sys
import random
from collections import Counter

# Ensure we can import from the root directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.data_loader import DataLoader

def test_selection():
    loader = DataLoader()
    base_prompts = loader.load_base_prompts()
    
    print(f"Total Base Prompts Loaded: {len(base_prompts)}")
    
    keys = list(base_prompts.keys())
    weights = []
    
    for k in keys:
        data = base_prompts[k]
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

    print("\nWeights detected:")
    for k, w in zip(keys, weights):
        print(f"  {k}: {w}")

    # Simulate 1000 selections
    selections = random.choices(keys, weights=weights, k=1000)
    counts = Counter(selections)
    
    print("\nSimulation Results (1000 trials):")
    print("-" * 50)
    for k in sorted(keys):
        count = counts.get(k, 0)
        print(f"{k[:40]:<40} | {count:>5} | {count/10:.1f}%")

if __name__ == "__main__":
    test_selection()
