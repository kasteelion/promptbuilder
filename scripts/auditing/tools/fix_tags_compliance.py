import os
import re

# Tag Normalization Rules
# Maps "Bad/Duplicate" tags to "Canonical" tags
TAG_MAPPINGS = {
    # Case normalization
    "sport": "Sport",
    "sports": "Sport",
    "fantasy": "Fantasy",
    "sci-fi": "Sci-Fi",
    "tech": "Tech",
    "office": "Office",
    
    # Prefix normalization
    "block:fantasy": "Block:Fantasy",
    "block:combat": "Block:Combat",
    "block:sport": "Block:Sport",
    "mood:dark": "Mood:Dark",
    "mood:cozy": "Mood:Cozy",
    
    # Deduplication
    "athletic": "Athletic", 
    "urban": "Urban",
    "outdoor": "Outdoor",
    "indoor": "Indoor",
    "nature": "Nature",
    "costume": "Costume",
    "vintage": "Vintage",
    "historical": "Historical",
    "party": "Party",
    "work": "Job", # 'work' is vague, 'Job' matches outfit folders often
}

def fix_file_content(content):
    modified = False
    
    # Regex to find Tags: ... or (Tag1, Tag2) inside headers
    # We need to be careful not to replace text in descriptions
    
    # 1. Update "Tags: ..." lines
    def replace_tags_line(match):
        prefix = match.group(1) # "Tags:"
        tags_str = match.group(2)
        current_tags = [t.strip() for t in tags_str.split(',')]
        new_tags = []
        changed_this_line = False
        
        for t in current_tags:
            # Check direct match
            cleaned = t.lower()
            replacement = None
            
            # Check lower case mapping
            for bad, good in TAG_MAPPINGS.items():
                if cleaned == bad.lower():
                    replacement = good
                    break
            
            if replacement and replacement != t:
                new_tags.append(replacement)
                changed_this_line = True
            else:
                new_tags.append(t)
                
        if changed_this_line:
            nonlocal modified
            modified = True
            return f"{prefix} {', '.join(new_tags)}"
        return match.group(0)

    # Apply to "**Tags:** ..." lines
    content = re.sub(r'(\*\*Tags:\*\*)(.*?)(?:\n|$)', replace_tags_line, content)
    
    # Apply to "Tags: ..." lines
    content = re.sub(r'(^Tags:)(.*?)(?:\n|$)', replace_tags_line, content, flags=re.MULTILINE)
    
    # Apply to Markdown Headers ## Name (Tag1, Tag2)
    def replace_header_tags(match):
        header_start = match.group(1) # "## Name ("
        tags_str = match.group(2)
        header_end = match.group(3) # ")"
        
        current_tags = [t.strip() for t in tags_str.split(',')]
        new_tags = []
        changed_this_line = False
        
        for t in current_tags:
            cleaned = t.lower()
            replacement = None
            for bad, good in TAG_MAPPINGS.items():
                if cleaned == bad.lower():
                    replacement = good
                    break
            
            if replacement and replacement != t:
                new_tags.append(replacement)
                changed_this_line = True
            else:
                new_tags.append(t)
                
        if changed_this_line:
            nonlocal modified
            modified = True
            return f"{header_start}{', '.join(new_tags)}{header_end}"
        return match.group(0)

    content = re.sub(r'(^## .*?\()(.*?)(\))', replace_header_tags, content, flags=re.MULTILINE)
    
    return content, modified

def run_fix(data_dir):
    print(f"Fixing tags in {data_dir}...")
    files_fixed = 0
    
    # 1. Fix Markdown Lists (Scenes, Base Prompts)
    md_files = ["scenes.md", "base_prompts.md"]
    for md in md_files:
        path = os.path.join(data_dir, md)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, modified = fix_file_content(content)
            if modified:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed {md}")
                files_fixed += 1

    # 2. Fix Characters
    char_dir = os.path.join(data_dir, "characters")
    for fname in os.listdir(char_dir):
        if fname.endswith(".md"):
            path = os.path.join(char_dir, fname)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, modified = fix_file_content(content)
            if modified:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed Character: {fname}")
                files_fixed += 1
                
    # 3. Fix Outfits (They use 'Tags: ...' inside txt files)
    outfit_root = os.path.join(data_dir, "outfits")
    for root, dirs, files in os.walk(outfit_root):
        for fname in files:
            if fname.endswith(".txt"):
                path = os.path.join(root, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Outfits sometimes have "Tags: [Tag1, Tag2]" format
                    # We need to handle brackets if they exist
                    content_clean = content.replace("[", "").replace("]", "")
                    new_content, modified = fix_file_content(content_clean)
                    
                    # Only write if changed
                    if modified:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        # print(f"Fixed Outfit: {fname}") # Too spammy
                        files_fixed += 1
                except Exception as e:
                    print(f"Error fixing {fname}: {e}")

    print(f"Done! Fixed {files_fixed} files.")

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_fix(os.path.join(root_dir, "data"))
