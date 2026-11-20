import os
import sys
import re

# Add project root to path to import logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.randomizer import PromptRandomizer
from logic.data_loader import DataLoader

def run_check():
    # Initialize loader and data
    print("Loading data via DataLoader...")
    loader = DataLoader()
    
    characters = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    poses = loader.load_presets("poses.md")
    scenes = loader.load_presets("scenes.md")
    interactions = loader.load_interactions()
    color_schemes = loader.load_color_schemes()
    modifiers = loader.load_modifiers()
    framing = loader.load_framing()
    
    rng = PromptRandomizer(
        characters=characters,
        base_prompts=base_prompts,
        poses=poses,
        scenes=scenes,
        interactions=interactions,
        color_schemes=color_schemes,
        modifiers=modifiers,
        framing=framing
    )
    
    rng.data_dir = loader.base_dir / "data" # Manually set if not in init
    
    # 1. Gather all Scene Tags
    scene_tags_set = set()
    scenes_path = os.path.join(rng.data_dir, "scenes.md")
    with open(scenes_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Match "- **Name** (Tag1, Tag2):"
            match = re.search(r'- \*\*.*?\*\* \((.*?)\):', line)
            if match:
                tags = [t.strip().lower() for t in match.group(1).split(',')]
                expanded = rng._expand_tags(tags)
                scene_tags_set.update(expanded)
    
    # Write to file
    report_path = os.path.join(rng.data_dir.parent, "output", "reports", "connectivity_report.txt")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Total Unique Scene Tags (Expanded): " + str(len(scene_tags_set)) + "\n\n")
        f.write("Checking Character Connectivity...\n")
        f.write(f"{'Character':<25} | {'Unique Links':<12} | {'Status'}\n")
        f.write("-" * 65 + "\n")
        
        low_connectivity = []
        
        for char_name, char_data in rng.characters.items():
            raw_tags = char_data.get("tags", [])
            expanded_tags = rng._expand_tags([t.lower() for t in raw_tags])
            
            # Calculate overlap
            intersection = expanded_tags.intersection(scene_tags_set)
            score = len(intersection)
            
            status = "OK"
            if score == 0:
                status = "CRITICAL: 0"
                low_connectivity.append((char_name, score, raw_tags))
            elif score < 2:
                status = "WEAK: < 2"
                low_connectivity.append((char_name, score, raw_tags))
                
            f.write(f"{char_name:<25} | {score:<12} | {status}\n")
            
        # 3. Report Findings
        if low_connectivity:
            f.write("\n\n=== Characters Needing Review ===\n")
            for name, score, tags in low_connectivity:
                f.write(f"\n{name} (Links: {score})\n")
                f.write(f"Current Tags: {tags}\n")
                f.write("Suggestion: Add 'indoor', 'outdoor', 'urban', 'nature', 'luxury', 'casual'...\n")
                
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    run_check()
