import re
from pathlib import Path

def parse_blob(text):
    """Parse a text blob into structured components."""
    # Initialize dictionary
    data = {
        "Top": "",
        "Bottom": "",
        "Footwear": "",
        "Accessories": "",
        "Hair/Makeup": ""
    }

    # Extract Hair/Makeup
    hair_match = re.search(r'\*Hair/Makeup:\*(.*)', text, re.IGNORECASE | re.DOTALL)
    if hair_match:
        data["Hair/Makeup"] = hair_match.group(1).strip()
        text = text[:hair_match.start()].strip()

    # Extract Accessories
    acc_match = re.search(r'\*Accessories:\*(.*)', text, re.IGNORECASE | re.DOTALL)
    if acc_match:
        data["Accessories"] = acc_match.group(1).strip()
        text = text[:acc_match.start()].strip()

    # Split remaining text by semicolons
    # We clean up the segments to remove Markdown bolding for cleaner re-insertion if needed, 
    # but generally we want to keep the description rich.
    # Actually, the user's current format often has **Item Name** (desc). 
    # We might want to keep that or simplify it.
    # Let's keep the bolding for now as it highlights the item name.
    
    parts = [p.strip() for p in text.split(';') if p.strip()]
    
    if len(parts) >= 1:
        data["Top"] = parts[0]
    if len(parts) >= 2:
        data["Bottom"] = parts[1]
    if len(parts) >= 3:
        # Check if the 3rd part looks like footwear
        # or if it's a 3rd clothing item. 
        # usually 3rd is shoes in this dataset.
        data["Footwear"] = parts[2]
        
    # If there are more parts, append them to the previous field or a generic one?
    # In strict Top/Bottom/Footwear structure, extra items (jackets, etc) usually go with Top or are separate.
    # For now, let's append extra parts to "Top" if they seem like layers, or just append to Bottom.
    # Actually, safer to append to the last used field to avoid data loss.
    if len(parts) > 3:
        data["Footwear"] += "; " + "; ".join(parts[3:])

    return data

def migrate_file(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"Skipping {path} (not found)")
        return

    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    new_lines = []
    
    # We iterate through the file. 
    # If we find a header ### Name, we look at the next line.
    # If it's a blob, we parse and replace.
    # If it's already a list (starts with -), we keep it.
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for Outfit Header
        if line.startswith('### '):
            new_lines.append(line)
            i += 1
            
            # Collect the content block for this outfit
            block_lines = []
            while i < len(lines) and not lines[i].startswith('#') and not lines[i].startswith('--'):
                if lines[i].strip():
                    block_lines.append(lines[i])
                i += 1
            
            # Process block
            if not block_lines:
                continue
                
            first_line = block_lines[0].strip()
            
            # Check if already structured
            if first_line.startswith('- **'):
                # Already structured, keep as is
                new_lines.extend(block_lines)
            else:
                # It's a blob, parse it
                blob_text = " ".join([l.strip() for l in block_lines])
                data = parse_blob(blob_text)
                
                # Write structured format
                if data["Top"]:
                    new_lines.append(f"- **Top:** {data['Top']}")
                if data["Bottom"]:
                    new_lines.append(f"- **Bottom:** {data['Bottom']}")
                if data["Footwear"]:
                    new_lines.append(f"- **Footwear:** {data['Footwear']}")
                if data["Accessories"]:
                    new_lines.append(f"- **Accessories:** {data['Accessories']}")
                if data["Hair/Makeup"]:
                    new_lines.append(f"- **Hair/Makeup:** {data['Hair/Makeup']}")
                
            # Add a blank line after outfit
            new_lines.append("")
            
            # We already advanced i in the inner loop, but we need to handle the line that broke the loop
            # The line at 'i' is either a new header, '---', or EOF.
            # We do NOT increment i here because the outer loop needs to process this line.
            
        else:
            new_lines.append(line)
            i += 1

    # Write back
    path.write_text('\n'.join(new_lines), encoding='utf-8')
    print(f"Migrated {path}")

if __name__ == "__main__":
    migrate_file("data/outfits_f.md")
    migrate_file("data/outfits_m.md")
    # outfits_h.md is already structured, but running it is safe (it will skip)
    migrate_file("data/outfits_h.md") 
