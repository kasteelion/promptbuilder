import os
import re

DATA_DIR = r"c:\Users\parking\Desktop\promptbuilder\data"

# Special casing for acronyms or specific styles
OVERRIDES = {
    "sci-fi": "Sci-Fi",
    "k-pop": "K-Pop",
    "ootd": "OOTD",
    "pov": "POV",
    "mma": "MMA",
    "vsco": "VSCO",
    "bff": "BFF",
    "led": "LED",
    "rgb": "RGB",
    "usb": "USB",
    "dnd": "DND",
    "rpg": "RPG",
    "npc": "NPC",
    "vs": "vs",
    "diy": "DIY",
    "y2k": "Y2K",
    "hd": "HD",
    "4k": "4K",
    "8k": "8K",
    "3d": "3D",
    "2d": "2D",
    "tv": "TV",
    "ui": "UI",
    "ux": "UX",
    "id": "ID",
    "sf": "SF",
    "hq": "HQ"
}

def standardize_tag_text(text):
    """
    Standardize a single tag string (e.g., 'Mood:Dark' or 'fantasy').
    """
    text = text.strip()
    lower_text = text.lower()
    
    # Handle prefixes
    prefix = ""
    content = text
    
    if lower_text.startswith("block:"):
        prefix = "block:"
        content = text[6:]
    elif lower_text.startswith("mood:"):
        prefix = "mood:"
        content = text[5:]
        
    content = content.strip()
    content_lower = content.lower()
    
    # Apply casing
    if content_lower in OVERRIDES:
        final_content = OVERRIDES[content_lower]
    else:
        # Title Change: capitalize words, keep hyphens
        words = re.split(r'(\s+|-|/)', content)
        final_words = []
        for w in words:
            if not w:
                continue
            if w.lower() in OVERRIDES:
                final_words.append(OVERRIDES[w.lower()])
            elif re.match(r'^[a-zA-Z0-9]+$', w):
                final_words.append(w.capitalize())
            else:
                final_words.append(w) # punctuation/separator
        final_content = "".join(final_words)

    return f"{prefix}{final_content}"


def process_header_tags(content):
    """
    Find headers like '## Style Name (tag1, tag2)' and standardize tags.
    """
    header_pattern = re.compile(r'^(#+\s+.*?)\s*\(([^)]+)\)\s*$', re.MULTILINE)
    
    def replacer(match):
        title_part = match.group(1)
        tags_part = match.group(2)
        tags = [t.strip() for t in tags_part.split(',') if t.strip()]
        new_tags = [standardize_tag_text(t) for t in tags]
        new_tags_str = ", ".join(new_tags)
        return f"{title_part} ({new_tags_str})"

    return header_pattern.sub(replacer, content)

def process_expanded_tags(content):
    """
    Find lines starting with '_expanded_tags'
    """
    tag_line_pattern = re.compile(r'^(\s*-\s*_expanded_tags:\s*)(.*)$', re.MULTILINE)
    
    def replacer(match):
        prefix = match.group(1)
        raw_val = match.group(2).strip()
        if raw_val.startswith("{") and raw_val.endswith("}"):
            inner = raw_val[1:-1]
            tags = re.findall(r"['\"](.*?)['\"]", inner)
            new_tags = [standardize_tag_text(t) for t in tags]
            sorted_tags = sorted(list(set(new_tags)))
            new_val = "{" + ", ".join([f"'{t}'" for t in sorted_tags]) + "}"
            return f"{prefix}{new_val}"
        return match.group(0)

    return tag_line_pattern.sub(replacer, content)

def process_character_metadata(content):
    """
    Handle character file specific lines:
    **Tags:** female, approachable...
    **Vibe / Energy:** grounded, warm...
    """
    pattern = re.compile(r'^(\s*\*\*(?:Tags|Vibe / Energy):\*\*\s*)(.*)$', re.MULTILINE)

    def replacer(match):
        prefix = match.group(1)
        values_str = match.group(2)
        trailing_punct = ""
        if values_str.strip().endswith('.'):
            trailing_punct = "."
            values_str = values_str.rstrip('.')
        tags = [t.strip() for t in values_str.split(',') if t.strip()]
        new_tags = [standardize_tag_text(t) for t in tags]
        new_values_str = ", ".join(new_tags)
        return f"{prefix}{new_values_str}{trailing_punct}"

    return pattern.sub(replacer, content)

def process_yaml_tags(content):
    """
    Handle lines like: tags: [fantasy, Magic]
    """
    pattern = re.compile(r'^(tags:\s*\[)(.*?)(\])', re.MULTILINE | re.IGNORECASE)
    
    def replacer(match):
        prefix = match.group(1)
        inner = match.group(2)
        suffix = match.group(3)
        tags = [t.strip() for t in inner.split(',') if t.strip()]
        new_tags = [standardize_tag_text(t) for t in tags]
        new_inner = ", ".join(new_tags)
        return f"{prefix}{new_inner}{suffix}"

    return pattern.sub(replacer, content)

def process_list_item_tags(content):
    """
    Regex for List Items processing
    - **Name** (Tag1, Tag2):
    """
    list_item_pattern = re.compile(r'^(\s*-\s*\*\*.*?\*\*\s*)\(([^)]+)\)(:.*)$', re.MULTILINE)
    
    def replacer(match):
        start = match.group(1)
        tags_part = match.group(2)
        end = match.group(3)
        tags = [t.strip() for t in tags_part.split(',') if t.strip()]
        new_tags = [standardize_tag_text(t) for t in tags]
        new_tags_str = ", ".join(new_tags)
        return f"{start}({new_tags_str}){end}"

    return list_item_pattern.sub(replacer, content)

def run():
    print("Starting Tag Standardization...")
    files_modified = 0
    
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            
            if ext not in ['.md', '.txt']:
                continue
                
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Apply transformations
                if ext == '.md':
                    content = process_header_tags(content)
                    content = process_character_metadata(content)
                    
                if ext == '.txt' or ext == '.md':
                    content = process_expanded_tags(content)
                    content = process_yaml_tags(content)
                    content = process_list_item_tags(content)

                if content != original_content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    files_modified += 1
            except Exception as e:
                print(f"Error processing {file}: {e}")

    print(f"Standardization Complete. Modified {files_modified} files.")

if __name__ == "__main__":
    run()
