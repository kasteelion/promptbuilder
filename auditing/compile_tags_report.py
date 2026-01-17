import os
import glob

# Configuration
DATA_DIR = r"c:\Users\parking\Desktop\promptbuilder\data"
OUTPUT_FILE = r"c:\Users\parking\Desktop\promptbuilder\auditing\reports\assets_by_tag.md"

def main():
    print("Compiling Assets by Tag...")
    
    # Store as dictionary: tag -> list of (Type, Category, Name)
    tag_index = {}
    
    # helper to add to index
    def add_to_index(asset_type, category, name, tags):
        if not tags:
            return
        for tag in tags:
            # Normalize tag
            clean_tag = tag.lower().strip()
            if not clean_tag:
                continue
            if clean_tag not in tag_index:
                tag_index[clean_tag] = []
            tag_index[clean_tag].append(f"{asset_type} | {category} | {name}")

    # GENERIC INVENTORY PARSER
    # Reads asset_inventory.md directly for ALL asset types
    inventory_file = r"c:\Users\parking\Desktop\promptbuilder\auditing\reports\asset_inventory.md"
    if os.path.exists(inventory_file):
        print(f"Reading from {inventory_file}...")
        with open(inventory_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Format: | Type | Category | Name | Tags | ...
                if line.startswith("|") and not line.startswith("| Type") and not line.startswith("|---"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) > 5:
                        asset_type = parts[1]
                        category = parts[2]
                        name = parts[3]
                        tags_str = parts[4]
                        
                        if tags_str and tags_str.lower() != "tags":
                             tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                             add_to_index(asset_type, category, name, tags)

    # OUTPUT GENERATION
    # Sort tags alphabetically
    sorted_tags = sorted(tag_index.keys())
    
    output_lines = []
    output_lines.append("# Assets Indexed by Tag")
    output_lines.append(f"Generated report of {len(sorted_tags)} unique tags from `asset_inventory.md`.\n")
    
    for tag in sorted_tags:
        assets = tag_index[tag]
        output_lines.append(f"## [{tag}] ({len(assets)})")
        for asset in sorted(assets):
            output_lines.append(f"- {asset}")
        output_lines.append("")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines))
    
    print(f"Report written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
