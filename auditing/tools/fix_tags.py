import os
import re
from tag_inventory import TagInventory

# Define explicit replacements (Old -> New)
# Case sensitive matching, but we will apply it carefully.
REPLACEMENTS = {
    "Sports": "Sport",
    "sports": "sport",
    "Soft": "soft", # unify casing where possible, though Scenes.md might resist
    "Costume": "costume",
    "Fantasy": "fantasy",
    "Medieval": "medieval",
    "Historical": "historical",
    "Urban": "urban",
    "Outdoor": "outdoor",
    "Indoor": "indoor",
    "Tech": "tech",
    "Nature": "nature",
    "Vintage": "vintage",
    "Luxury": "luxury",
    "Work": "work",
    "Combat": "combat",
    "Cyberpunk": "cyberpunk",
    "Noir": "noir",
    "Gritty": "gritty",
    "Relaxed": "relaxed",
    "Intimate": "intimate",
    "Cozy": "cozy",
    "Party": "party",
    "Event": "event",
    "Travel": "travel",
    "Medical": "medical",
    "Creative": "creative",
    "Culture": "cultural", # Unify Culture -> Cultural?
    "culture": "cultural",
    "Traditional": "traditional",
    "Formal": "formal",
    "Action": "action",
    "Social": "social",
    "Romantic": "romantic",
    "Sleep": "sleep",
    "Lounge": "lounge",
    "Armor": "armor",
    "Swimwear": "swimwear",
    "Tactical": "tactical",
    "Sci-Fi": "sci-fi",
    "Modern": "modern",
    "Pop": "pop",
    "Elegant": "elegant",
    "Professional": "professional",
    "Nightlife": "nightlife",
    "Cottagecore": "cottagecore",
    "Industrial": "industrial",
    "Ruins": "ruin", # Singular/Plural unification?
    "ruins": "ruin",
    "Warrior": "warrior",
    "Priestess": "priestess",
    "Healer": "healer",
    "Wizard": "wizard",
    "Hero": "hero",
    "Villain": "villain",
    "Greek": "greek",
    "Egypt": "egyptian",
    "China": "chinese",
    "Japan": "japanese",
    "India": "indian",
}

def apply_replacements(content, source_type):
    """
    Apply replacements to content.
    For Markdown files (Characters, Scenes), we look for Tags lines.
    For Text files (Outfits), we look for tags: lines.
    """
    
    lines = content.split('\n')
    new_lines = []
    modified = False
    
    for line in lines:
        original_line = line
        
        # Check if line is a tag line based on source type
        is_tag_line = False
        tag_content_start = -1
        tag_content_end = -1
        
        if source_type == "markdown":
            # Matches: "**Tags:** tag1, tag2" or "Tags: tag1, tag2" or "(tag1, tag2)" inside headers
            
            # Case 1: **Tags:**
            match = re.search(r'(\*\*Tags:\*\*|Tags:)\s*(.*)', line)
            if match:
                is_tag_line = True
                prefix = match.group(1)
                tags_str = match.group(2)
                # Reconstruct
                new_tags = process_tags(tags_str)
                if new_tags != tags_str:
                    line = line.replace(tags_str, new_tags)
                    modified = True
            
            # Case 2: (Tag1, Tag2) usually in headers or lists
            # Be careful not to replace text in normal parenthesis
            elif "(" in line and ")" in line and (line.strip().startswith("##") or line.strip().startswith("- **")):
                 match = re.search(r'\((.*?)\)', line)
                 if match:
                     tags_str = match.group(1)
                     # Heuristic: if it looks like a tag list (commas or known tags)
                     if ',' in tags_str or tags_str in REPLACEMENTS:
                         new_tags = process_tags(tags_str)
                         if new_tags != tags_str:
                             line = line.replace(f"({tags_str})", f"({new_tags})")
                             modified = True

        elif source_type == "text": # Outfits
            if "tags:" in line.lower():
                # tags: [tag1, tag2] or tags: tag1, tag2
                try:
                    prefix, content = line.split(":", 1)
                    clean_content = content.strip().replace("[", "").replace("]", "")
                    new_content = process_tags(clean_content)
                    
                    # reconstruct preserving brackets if they existed
                    if "[" in line:
                         new_line = f"{prefix}: [{new_content}]"
                    else:
                         new_line = f"{prefix}: {new_content}"
                    
                    if new_line != line:
                        line = new_line
                        modified = True
                except:
                    pass

        new_lines.append(line)
    
    return '\n'.join(new_lines), modified

def process_tags(tags_str):
    """Split string by comma, replace individual tags, join back."""
    tags = [t.strip() for t in tags_str.split(',')]
    new_tags = []
    for t in tags:
        # Handle prefixes
        prefix = ""
        clean_t = t
        if ":" in t and not t.lower().startswith("http"): # Avoid URLs
             parts = t.split(":", 1)
             if parts[0].lower() in ["block", "mood"]:
                 prefix = parts[0] + ":"
                 clean_t = parts[1]
        
        # Check replacement
        if clean_t in REPLACEMENTS:
            clean_t = REPLACEMENTS[clean_t]
        
        # Check title case version if not found
        elif clean_t.title() in REPLACEMENTS and clean_t != clean_t.lower():
             # If mapping has "Sport"->"sport" and we have "Sport", it matches
             # But if we have "sport", we shouldn't map if key is "Sport" unless we want to enforce casing
             pass

        new_tags.append(prefix + clean_t)
        
    return ', '.join(new_tags)

def run_fix():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root_dir, "data")
    
    print("Fixing tags...")
    
    # 1. Characters
    char_dir = os.path.join(data_dir, "characters")
    for filename in os.listdir(char_dir):
        if filename.endswith(".md"):
            path = os.path.join(char_dir, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, changed = apply_replacements(content, "markdown")
            if changed:
                print(f"Fixed {filename}")
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

    # 2. Scenes and Prompts
    for filename in ["scenes.md", "base_prompts.md"]:
        path = os.path.join(data_dir, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content, changed = apply_replacements(content, "markdown")
            if changed:
                print(f"Fixed {filename}")
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

    # 3. Outfits
    outfit_root = os.path.join(data_dir, "outfits")
    for root, dirs, files in os.walk(outfit_root):
        for file in files:
            if file.endswith(".txt"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                new_content, changed = apply_replacements(content, "text")
                if changed:
                    print(f"Fixed {file}")
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

if __name__ == "__main__":
    run_fix()
