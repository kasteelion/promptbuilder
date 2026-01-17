"""
Script to compile a unified inventory of all assets (Scenes, Outfits, Interactions, Poses).
Outputs a Markdown table to `auditing/reports/asset_inventory.md`.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.data_loader import DataLoader
from utils.validation import sanitize_filename

def main():
    loader = DataLoader()
    
    # Data containers
    rows = []
    
    print("Loading assets...")

    # 0. BASE PROMPTS (STYLES)
    print("...Loading Styles (Base Prompts)")
    styles_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "base_prompts.md")
    if os.path.exists(styles_file):
        with open(styles_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Split by headers
            sections = content.split("## ")
            for section in sections[1:]:
                lines = section.split('\n')
                header = lines[0].strip()
                # Format: Name (Tag, Tag)
                if "(" in header and ")" in header:
                    param_start = header.rfind("(")
                    name = header[:param_start].strip()
                    tag_part = header[param_start+1:header.rfind(")")]
                    tags = [t.strip() for t in tag_part.split(",")]
                    
                    desc = ""
                    # Find description (text after header until ---)
                    body_lines = [l.strip() for l in lines[1:] if l.strip() and not l.strip().startswith("---")]
                    if body_lines:
                        desc = " ".join(body_lines)[:100]
                        
                    rows.append({
                        "Type": "Style",
                        "Category": "Base",
                        "Name": name,
                        "Tags": ", ".join(sorted(tags)),
                        "Description": desc
                    })
    
    # 1. SCENES
    print("...Loading Scenes")
    scenes_data = loader.load_presets("scenes.md")
    # Structure: {Category: {Name: Data/String}}
    for category, items in scenes_data.items():
        for name, data in items.items():
            tags = []
            desc = ""
            if isinstance(data, dict):
                tags = data.get("tags", [])
                desc = data.get("description", "")
            else:
                desc = str(data)
                
            rows.append({
                "Type": "Scene",
                "Category": category,
                "Name": name,
                "Tags": ", ".join(sorted(tags)),
                "Description": desc.replace("\n", " ")[:100] + ("..." if len(desc) > 100 else "")
            })

    # 2. POSES
    print("...Loading Poses")
    poses_data = loader.load_presets("poses.md")
    for category, items in poses_data.items():
        for name, data in items.items():
            tags = []
            desc = ""
            if isinstance(data, dict):
                tags = data.get("tags", [])
                desc = data.get("description", "")
            else:
                desc = str(data)
                
            rows.append({
                "Type": "Pose",
                "Category": category,
                "Name": name,
                "Tags": ", ".join(sorted(tags)),
                "Description": desc.replace("\n", " ")[:100]
            })

    # 3. INTERACTIONS
    print("...Loading Interactions")
    int_data = loader.load_interactions()
    for category, items in int_data.items():
        for name, data in items.items():
            tags = []
            desc = ""
            if isinstance(data, dict):
                tags = data.get("tags", [])
                desc = data.get("description", "")
            else:
                desc = str(data) # specific case if text only
                
            rows.append({
                "Type": "Interaction",
                "Category": category,
                "Name": name,
                "Tags": ", ".join(sorted(tags)),
                "Description": desc.replace("\n", " ")[:100]
            })

    # 4. OUTFITS (Shared)
    # 4. OUTFITS (Direct Scan)
    print("...Loading Outfits (Direct Scan)")
    outfits_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "outfits")
    
    # Walk directory
    for root, dirs, files in os.walk(outfits_dir):
        for file in files:
            if file.endswith(".txt"):
                # Path: data/outfits/Category/SubFolder/Name.txt
                rel_path = os.path.relpath(root, outfits_dir)
                category = rel_path.split(os.sep)[0] 
                if category == ".": category = "Uncategorized"
                
                name = os.path.splitext(file)[0]
                full_path = os.path.join(root, file)
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    tags = []
                    desc = ""
                    # Simple parsing: find "tags: [...]" line
                    header_lines = []
                    for line in lines:
                        if line.strip().startswith("tags:"):
                            parts = line.split(":", 1)
                            if len(parts) > 1:
                                tag_part = parts[1].strip().strip("[]")
                                tags = [t.strip() for t in tag_part.split(",") if t.strip()]
                        elif not line.startswith("-") and not line.startswith("["):
                            header_lines.append(line.strip())
                            
                    # Rough description from first non-tag lines
                    desc = " ".join([l for l in header_lines if l])
                    
                    rows.append({
                        "Type": "Outfit",
                        "Category": category,
                        "Name": name,
                        "Tags": ", ".join(sorted(tags)),
                        "Description": desc[:100]
                    })
                except Exception as e:
                    print(f"Error reading {full_path}: {e}")

    # OUTPUT
    report_path = Path(__file__).parent / "reports" / "asset_inventory.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing report to {report_path}...")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Unified Asset Inventory\n\n")
        f.write(f"Generated on {sys.version}\n\n")
        f.write("| Type | Category | Name | Tags | Description |\n")
        f.write("|---|---|---|---|---|\n")
        
        # Sort by Type, then Category
        rows.sort(key=lambda x: (x["Type"], x["Category"], x["Name"]))
        
        for r in rows:
            f.write(f"| {r['Type']} | {r['Category']} | {r['Name']} | {r['Tags']} | {r['Description']} |\n")
            
    print("Done!")

if __name__ == "__main__":
    main()
