import os
import re

# Configuration
OUTFITS_DIR = r"c:\Users\parking\Desktop\promptbuilder\data\outfits"
INTERACTIONS_FILE = r"c:\Users\parking\Desktop\promptbuilder\data\interactions.md"

# Tag Merges (Old -> New)
TAG_MERGES = {
    "chill": "relaxed",
    "relax": "relaxed",
    "relaxing": "relaxed",
    "celebratory": "celebration",
    "culture": "cultural",
    "daily": "casual",
    "workout": "fitness",
    "gym": "fitness",
    "city": "urban",
    "safe": "safety",
    "joyful": "happy",
    "positive": "happy",
    "hero": "heroic",
    "job": "work",
    "japanese fashion": "japanese",
    "90s": "1990s",
    "fancy": "formal",
    "gala": "event"
}

def process_outfits():
    print("Processing Outfits...")
    count = 0
    for root, dirs, files in os.walk(OUTFITS_DIR):
        for file in files:
            if not file.endswith(".txt"):
                continue
            
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                modified = False
                new_lines = []
                for line in lines:
                    if line.strip().startswith("tags:"):
                        # Extract list content: tags: [A, B, C]
                        match = re.search(r"tags:\s*\[(.*?)\]", line)
                        if match:
                            content = match.group(1)
                            current_tags = [t.strip() for t in content.split(',')]
                            
                            new_tags = []
                            line_changed = False
                            for tag in current_tags:
                                # Case insensitive check? Tags usually Capitalized or lowercase. 
                                # Let's try direct match first, then lower.
                                tag_lower = tag.lower()
                                if tag_lower in TAG_MERGES:
                                    new_tag = TAG_MERGES[tag_lower]
                                    # Preserve capitalization logic if simple? Or just Title Case.
                                    # "job" -> "Work" (if source was Job). 
                                    # Let's just use Title Case for uniformity or match dict value.
                                    # We'll use the dict value but Capitalize it since most tags are.
                                    formatted_new = new_tag.capitalize() if new_tag[0].isalpha() else new_tag
                                    
                                    # Avoid duplicates if new tag already exists
                                    if formatted_new not in new_tags and formatted_new.lower() not in [t.lower() for t in current_tags]:
                                        new_tags.append(formatted_new)
                                        line_changed = True
                                        print(f"[{file}] Replaced '{tag}' with '{formatted_new}'")
                                    elif formatted_new.lower() in [t.lower() for t in current_tags]:
                                         # Merging into existing tag, just drop the old one
                                         print(f"[{file}] Dropped '{tag}' (merged into existing '{formatted_new}')")
                                         line_changed = True
                                    else:
                                        new_tags.append(formatted_new) # Should match case of existing?
                                else:
                                    new_tags.append(tag)
                            
                            if line_changed:
                                # Reconstruct line
                                new_line = f"tags: [{', '.join(new_tags)}]\n"
                                new_lines.append(new_line)
                                modified = True
                            else:
                                new_lines.append(line)
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                
                if modified:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    count += 1
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    print(f"Updated {count} outfit files.")

def process_interactions():
    print("Processing Interactions...")
    try:
        with open(INTERACTIONS_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        modified_count = 0
        new_lines = []
        for line in lines:
            # Match interaction line: - **Name** (Tag, Tag): Desc
            # We want to edit the content inside constants ()
            match = re.search(r"(- \*\*.*?\*\* \()(.*?)(\):.*)", line)
            if match:
                prefix = match.group(1)
                tags_str = match.group(2)
                suffix = match.group(3)
                
                current_tags = [t.strip() for t in tags_str.split(',')]
                new_tags = []
                line_changed = False
                
                for tag in current_tags:
                    # interactions often have "poses:X;Y"
                    if tag.startswith("poses:"):
                        new_tags.append(tag)
                        continue
                        
                    tag_lower = tag.lower()
                    if tag_lower in TAG_MERGES:
                        new_tag = TAG_MERGES[tag_lower]
                        # Preserve case style? Interactions often used Title Case.
                        formatted_new = new_tag.capitalize()
                        
                        # Dedup
                        existing_lower = [t.lower() for t in current_tags]
                        # Don't check existing yet because we are building new_tags list
                        # Actually we need to be careful not to add "Relaxed" if "Relaxed" is already in the list
                        # But since we are rebuilding the list from scratch, we just check if new_tag is already in new_tags?
                        # No, we need to check if target tag was ALSO in the original list to avoid dupes.
                        
                        if formatted_new not in new_tags: 
                             # Check if we naturally have this tag later? Hard to know order.
                             # Simple dedup at the end.
                             new_tags.append(formatted_new)
                             line_changed = True
                             print(f"[Interaction] Replaced '{tag}' with '{formatted_new}'")
                    else:
                        new_tags.append(tag)
                
                # Final Dedup (case insensitive)
                final_tags = []
                seen = set()
                for t in new_tags:
                    if t.lower() not in seen:
                        final_tags.append(t)
                        seen.add(t.lower())
                
                if line_changed or len(final_tags) != len(current_tags):
                     new_line = f"{prefix}{', '.join(final_tags)}{suffix}\n"
                     new_lines.append(new_line)
                     modified_count += 1
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        if modified_count > 0:
            with open(INTERACTIONS_FILE, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"Updated {modified_count} interactions.")
            
    except Exception as e:
        print(f"Error processing interactions: {e}")

def main():
    process_outfits()
    process_interactions()
    print("Consolidation Complete.")

if __name__ == "__main__":
    main()
