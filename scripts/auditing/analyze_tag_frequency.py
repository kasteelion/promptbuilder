import os
from collections import Counter

# Configuration
INVENTORY_FILE = r"c:\Users\parking\Desktop\promptbuilder\auditing\reports\asset_inventory.md"
OUTPUT_FILE = r"c:\Users\parking\Desktop\promptbuilder\auditing\reports\tags_frequency.md"

def main():
    print("Analyzing Tag Frequencies...")
    
    tag_counts = Counter()
    
    if not os.path.exists(INVENTORY_FILE):
        print(f"Error: Inventory file not found at {INVENTORY_FILE}")
        return

    with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            # Parse lines starting with | AssetType |
            if line.startswith("|"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) > 5:
                    # Column 4 usually contains tags in the inventory format we saw earlier
                    # But let's be careful. The previous script assumed index 4.
                    # | Type | Category | Name | Tags | ...
                    tags_str = parts[4] 
                    if tags_str and tags_str != "Tags": # Skip header
                        tags = [t.strip().lower() for t in tags_str.split(",") if t.strip()]
                        tag_counts.update(tags)

    # Sort by count (descending)
    sorted_tags = tag_counts.most_common()
    
    # Bucketize
    high_freq = []
    mod_freq = []
    low_freq = []
    
    for tag, count in sorted_tags:
        if count >= 50:
            high_freq.append((tag, count))
        elif count >= 10:
            mod_freq.append((tag, count))
        else:
            low_freq.append((tag, count))
            
    # Generate Report
    lines = []
    lines.append("# Tag Frequency Analysis")
    lines.append(f"Total Unique Tags: {len(sorted_tags)}")
    lines.append("")
    
    lines.append("## High Frequency Tags (50+ uses)")
    lines.append("| Tag | Count |")
    lines.append("|---|---|")
    for tag, count in high_freq:
        lines.append(f"| **{tag}** | {count} |")
    lines.append("")
    
    lines.append("## Moderate Frequency Tags (10-49 uses)")
    lines.append("| Tag | Count |")
    lines.append("|---|---|")
    for tag, count in mod_freq:
        lines.append(f"| {tag} | {count} |")
    lines.append("")
    
    lines.append("## Low Frequency Tags (<10 uses) - **CANDIDATES FOR DELETION**")
    lines.append("| Tag | Count |")
    lines.append("|---|---|")
    for tag, count in low_freq:
        lines.append(f"| {tag} | {count} |")
    lines.append("")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
        
    print(f"Report generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
