import os
import collections

# Configuration
INVENTORY_FILE = r"c:\Users\parking\Desktop\promptbuilder\auditing\reports\asset_inventory.md"
OUTPUT_FILE = r"c:\Users\parking\Desktop\promptbuilder\auditing\reports\hub_connectivity.md"

def main():
    print("Analyzing Hub Connectivity...")
    
    # Store: tag -> set of types found
    tag_coverage = collections.defaultdict(set)
    tag_counts = collections.defaultdict(lambda: collections.defaultdict(int))

    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                # | Type | Category | Name | Tags | ...
                if line.startswith("|") and not line.startswith("| Type") and not line.startswith("|---"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) > 5:
                        asset_type = parts[1] # Style, Scene, Outfit, Interaction, Pose
                        tags_str = parts[4]
                        
                        if tags_str and tags_str.lower() != "tags":
                             tags = [t.strip().lower() for t in tags_str.split(",") if t.strip()]
                             for tag in tags:
                                 tag_coverage[tag].add(asset_type)
                                 tag_counts[tag][asset_type] += 1

    # Generate Report
    lines = []
    lines.append("# Hub Connectivity Report")
    lines.append("Analysis of which tags serve as complete 'Hubs' connecting all asset types.\n")
    
    lines.append("## Strong Hubs (Style + Scene + Outfit + Interaction)")
    lines.append("| Tag | Styles | Scenes | Outfits | Interactions | Poses |")
    lines.append("|---|---|---|---|---|---|")
    
    strong_hubs = []
    weak_hubs = []
    style_gaps = []
    
    sorted_tags = sorted(tag_coverage.keys())
    
    for tag in sorted_tags:
        types = tag_coverage[tag]
        counts = tag_counts[tag]
        
        has_style = "Style" in types
        has_scene = "Scene" in types
        has_outfit = "Outfit" in types
        has_interaction = "Interaction" in types
        
        # Define "Strong Hub" as having at least Style, Scene, Outfit, Interaction
        is_strong = has_style and has_scene and has_outfit and has_interaction
        
        row = f"| **{tag}** | {counts['Style']} | {counts['Scene']} | {counts['Outfit']} | {counts['Interaction']} | {counts['Pose']} |"
        
        if is_strong:
            strong_hubs.append(row)
        else:
            # Filter out very low signal tags (fragments)
            total_assets = sum(counts.values())
            if total_assets > 5:
                # Candidate for expansion
                missing = []
                if not has_style: missing.append("Style")
                if not has_scene: missing.append("Scene")
                if not has_outfit: missing.append("Outfit")
                if not has_interaction: missing.append("Interaction")
                
                weak_hubs.append(f"| **{tag}** | {counts['Style']} | {counts['Scene']} | {counts['Outfit']} | {counts['Interaction']} | {counts['Pose']} | Missing: {', '.join(missing)}")
                
                if not has_style and (has_scene or has_outfit):
                    style_gaps.append(tag)

    lines.extend(strong_hubs)
    lines.append("")
    
    lines.append("## Potential Hubs (Missing Key Components)")
    lines.append("| Tag | Styles | Scenes | Outfits | Interactions | Poses | Status |")
    lines.append("|---|---|---|---|---|---|---|")
    lines.extend(weak_hubs)
    lines.append("")

    lines.append("## Action Items: Missing Styles")
    lines.append("Tags that have content but NO Base Style (High Priority for 'Broadening'):")
    for t in style_gaps:
         lines.append(f"- [ ] Add `{t}` to a suitable Base Prompt")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
        
    print(f"Report written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
