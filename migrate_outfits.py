
import os
import re

DATA_DIR = r"C:\Users\parking\Desktop\promptbuilder\data"
OUTFITS_OUT_DIR = os.path.join(DATA_DIR, "outfits")

FILES = {
    'F': os.path.join(DATA_DIR, "outfits_f.md"),
    'M': os.path.join(DATA_DIR, "outfits_m.md"),
    'H': os.path.join(DATA_DIR, "outfits_h.md"),
}

NAME_ALIASES = {
    "Sorcerer": "Sorceress", # Map Sorcerer (M) to Sorceress (Base)
}

def parse_markdown_file(filepath, modifier):
    """
    Parses an outfit markdown file.
    Returns a dict: { "Outfit Name": { "category": "...", "tags": [...], "content": "..." } }
    """
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return {}

    outfits = {}
    current_category = "Uncategorized"
    current_outfit = None
    buffer = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            
            # Category Header
            if stripped.startswith("## "):
                current_category = stripped[3:].strip()
                continue
                
            # Outfit Header
            if stripped.startswith("### "):
                # Save previous outfit if exists
                if current_outfit:
                    outfits[current_outfit]['content'] = "\n".join(buffer).strip()
                
                raw_name = stripped[4:].strip()
                name = raw_name
                tags = []
                
                # Extract Tags
                tag_match = re.search(r"\(([^)]+)\)$", raw_name)
                if tag_match:
                    tags_str = tag_match.group(1)
                    # Split by comma
                    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                    name = raw_name[:tag_match.start()].strip()
                
                # Handle Aliases
                if name in NAME_ALIASES:
                    name = NAME_ALIASES[name]

                current_outfit = name
                buffer = []
                
                if name not in outfits:
                    outfits[name] = {
                        "category": current_category,
                        "tags": tags, # Will be merged later
                        "content": "" 
                    }
                else:
                     # Merge tags if they exist for this entry
                    if tags:
                        existing = set(outfits[name]['tags'])
                        existing.update(tags)
                        outfits[name]['tags'] = list(existing)

                continue
            
            # Content Lines (skip empty lines if buffer is empty)
            if current_outfit:
               buffer.append(line.rstrip())

        # Save last outfit
        if current_outfit:
            outfits[current_outfit]['content'] = "\n".join(buffer).strip()
            
    return outfits

def main():
    merged_data = {} # { "OutfitName": { "category": "...", "tags": [], "F": "...", "M": "...", "H": "..." } }

    # Parse all files
    for modifier, filepath in FILES.items():
        print(f"Parsing {modifier} from {filepath}...")
        parsed = parse_markdown_file(filepath, modifier)
        
        for name, data in parsed.items():
            if name not in merged_data:
                merged_data[name] = {
                    "category": data["category"],
                    "tags": data["tags"],
                    "F": "", "M": "", "H": ""
                }
            else:
                # Merge Tags (Union)
                existing_tags = set(merged_data[name]["tags"])
                new_tags = set(data["tags"])
                merged_data[name]["tags"] = list(existing_tags.union(new_tags))
                
                # Ensure category consistency (first one wins or prioritize specific files? Usually they match)
                if not merged_data[name]["category"]:
                     merged_data[name]["category"] = data["category"]

            merged_data[name][modifier] = data["content"]

    # Write files
    print(f"Writing parsed data to {OUTFITS_OUT_DIR}...")
    
    if not os.path.exists(OUTFITS_OUT_DIR):
        os.makedirs(OUTFITS_OUT_DIR)
        
    for name, data in merged_data.items():
        category = data['category']
        # Sanitize category for folder name
        safe_cat = "".join([c for c in category if c.isalnum() or c in (' ', '-', '_')]).strip()
        cat_dir = os.path.join(OUTFITS_OUT_DIR, safe_cat)
        
        if not os.path.exists(cat_dir):
            os.makedirs(cat_dir)
            
        # Sanitize filename
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"{safe_name}.txt"
        filepath = os.path.join(cat_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write Tags
            tags_line = ", ".join(sorted(data['tags']))
            f.write(f"tags: [{tags_line}]\n\n")
            
            # Write Content
            # F
            f.write("[F]\n")
            if data['F']:
                f.write(data['F'] + "\n")
            else:
                 f.write("- Content missing for F\n")
            f.write("\n")

            # M
            f.write("[M]\n")
            if data['M']:
                f.write(data['M'] + "\n")
            else:
                 f.write("- Content missing for M\n")
            f.write("\n")

            # H
            f.write("[H]\n")
            if data['H']:
                f.write(data['H'] + "\n")
            else:
                 f.write("- Content missing for H\n")
            f.write("\n")
            
    print("Migration complete!")

if __name__ == "__main__":
    main()
