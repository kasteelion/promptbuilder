import os
import re

# Configuration
OUTFITS_DIR = r"c:\Users\parking\Desktop\promptbuilder\data\outfits\Athletics & Sports"

# Specific Sports to Purify
# If an outfit has one of these tags (case-insensitive check), we strip generic tags from it.
SPECIFIC_SPORTS = {
    "bowling", "baseball", "basketball", "football", "soccer", 
    "tennis", "volleyball", "softball", "mma", "boxing", 
    "wrestling", "track", "cheerleading", "cheer", "figure skating", 
    "gymnastics", "surfing", "swimming", "golf", "hockey", 
    "cricket", "rugby", "lacrosse", "skateboarding", "skiing", "snowboarding"
}

# Generic Tags to Remove if a Specific Sport is present
GENERIC_TAGS_TO_REMOVE = {
    "sport", "sports", "athletic", "athletics", 
    "fitness", "active", "training", "workout", "gym", "outdoor", "cold"
}

def process_outfits():
    print("Purifying Sport Outfits (Strict Mode)...")
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
                        match = re.search(r"tags:\s*\[(.*?)\]", line)
                        if match:
                            content = match.group(1)
                            # Split by comma and strip whitespace
                            current_tags = [t.strip() for t in content.split(',')]
                            
                            # Check if specific sport is present
                            has_specific_sport = False
                            for t in current_tags:
                                if t.lower() in SPECIFIC_SPORTS:
                                    has_specific_sport = True
                                    print(f"[{file}] Identified specific sport: {t}")
                                    break
                            
                            if has_specific_sport:
                                new_tags = []
                                removed = []
                                for tag in current_tags:
                                    if tag.lower() in GENERIC_TAGS_TO_REMOVE:
                                        removed.append(tag)
                                    else:
                                        new_tags.append(tag)
                                
                                if removed:
                                    print(f"  -> Removing: {removed}")
                                    new_line = f"tags: [{', '.join(new_tags)}]\n"
                                    new_lines.append(new_line)
                                    modified = True
                                else:
                                    new_lines.append(line)
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
                print(f"Error processing {file}: {e}")
                
    print(f"Refined purification complete. Modified {count} files.")

if __name__ == "__main__":
    process_outfits()
