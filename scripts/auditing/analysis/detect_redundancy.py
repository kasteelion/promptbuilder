import os
import sys
import difflib
from pathlib import Path
from collections import defaultdict

# Add project root and src to path
# scripts/auditing/analysis/detect_redundancy.py -> auditing/analysis -> auditing -> scripts -> root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "src"))

from logic.data_loader import DataLoader

def get_similarity(text1, text2):
    """Simple similarity ratio using difflib."""
    return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def analyze_redundancy():
    loader = DataLoader()
    print("Loading data for redundancy analysis...")
    
    scenes = loader.load_presets("scenes.md")
    interactions = loader.load_interactions()
    
    redundancies = []
    
    # 1. Analyze Scenes
    print("Analyzing Scenes for redundancy...")
    all_scenes = []
    for category, items in scenes.items():
        for name, data in items.items():
            desc = ""
            if isinstance(data, dict):
                # The scenes.md structure from parser is complex, usually has 'visual_description' or raw string
                desc = data.get("Visual Description", "") or data.get("description", "") or str(data)
                # If it's still a dict, it might be the raw items from parse_presets
                if isinstance(desc, dict):
                    desc = str(desc)
            else:
                desc = str(data)
            
            # Clean up desc from Markdown artifacts
            desc = desc.replace("**Visual Description:**", "").strip()
            
            all_scenes.append({"name": f"{category}: {name}", "desc": desc})
            
    for i in range(len(all_scenes)):
        # Progress indicator for large sets
        if i % 20 == 0 and i > 0:
            print(f"  Processed {i}/{len(all_scenes)} scenes...")
            
        for j in range(i + 1, len(all_scenes)):
            s1 = all_scenes[i]
            s2 = all_scenes[j]
            if len(s1['desc']) < 10 or len(s2['desc']) < 10: continue
            
            sim = get_similarity(s1['desc'], s2['desc'])
            if sim > 0.7:
                redundancies.append({
                    "type": "Scene",
                    "item1": s1['name'],
                    "item2": s2['name'],
                    "similarity": sim,
                    "desc1": s1['desc'][:100] + "...",
                    "desc2": s2['desc'][:100] + "..."
                })

    # 2. Analyze Interactions
    print("Analyzing Interactions for redundancy...")
    all_ints = []
    for category, items in interactions.items():
        if not isinstance(items, dict): continue
        for name, data in items.items():
            desc = data.get("description", "") if isinstance(data, dict) else str(data)
            all_ints.append({"name": f"{category}: {name}", "desc": desc})
            
    for i in range(len(all_ints)):
        if i % 20 == 0 and i > 0:
            print(f"  Processed {i}/{len(all_ints)} interactions...")
            
        for j in range(i + 1, len(all_ints)):
            i1 = all_ints[i]
            i2 = all_ints[j]
            if len(i1['desc']) < 10 or len(i2['desc']) < 10: continue
            
            sim = get_similarity(i1['desc'], i2['desc'])
            if sim > 0.7:
                redundancies.append({
                    "type": "Interaction",
                    "item1": i1['name'],
                    "item2": i2['name'],
                    "similarity": sim,
                    "desc1": i1['desc'][:100] + "...",
                    "desc2": i2['desc'][:100] + "..."
                })
                
    return redundancies

def generate_report(redundancies):
    report_dir = PROJECT_ROOT / "auditing" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "redundancy_report.md"
    print(f"Generating report: {report_path}")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🔄 Semantic Redundancy Report\n\n")
        f.write("Identifies assets that may describe the same visual concept.\n\n")
        
        if not redundancies:
            f.write("✅ No high-similarity redundancies detected (Threshold: 70%).\n")
            return
            
        f.write("| Type | Item 1 | Item 2 | Similarity |\n")
        f.write("|---|---|---|---|\n")
        
        # Sort by similarity
        sorted_reds = sorted(redundancies, key=lambda x: x['similarity'], reverse=True)
        for r in sorted_reds:
            f.write(f"| {r['type']} | {r['item1']} | {r['item2']} | {r['similarity']:.1%} |\n")
            
        f.write("\n## Details\n")
        for r in sorted_reds:
            f.write(f"### {r['item1']} vs {r['item2']} ({r['similarity']:.1%})\n")
            f.write(f"- **1**: {r['desc1']}\n")
            f.write(f"- **2**: {r['desc2']}\n\n")

if __name__ == "__main__":
    reds = analyze_redundancy()
    generate_report(reds)
