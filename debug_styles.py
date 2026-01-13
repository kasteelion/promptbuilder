
import sys
import os
sys.path.append(os.getcwd())

from logic.data_loader import DataLoader
from logic.parsers import MarkdownParser

loader = DataLoader()
prompts = loader.load_base_prompts()

with open("style_debug_output.txt", "w", encoding="utf-8") as f:
    f.write(f"Total Base Prompts Loaded: {len(prompts)}\n")
    f.write("-" * 80 + "\n")
    f.write(f"{'STYLE NAME':<40} | {'WEIGHT':<10} | {'TAGS':<30}\n")
    f.write("-" * 80 + "\n")

    for name in sorted(prompts.keys()):
        data = prompts[name]
        tags = data.get("tags", [])
        weight = 1.0
        for t in tags:
            if t.lower().startswith("weight:"):
                try:
                    weight = float(t.split(":")[1])
                except:
                    pass
        tags_str = ", ".join(tags[:3]) + ("..." if len(tags) > 3 else "")
        f.write(f"{name[:40]:<40} | {weight:<10} | {tags_str}\n")
print("Saved to style_debug_output.txt")
