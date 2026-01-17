import os
import re

DATA_DIR = r"c:\Users\parking\Desktop\promptbuilder\data"

def purge_action_if_sport_or_combat(file_path):
    print(f"Processing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines()
    new_lines = []
    modified = False

    for line in lines:
        # Match poses/interactions: - **Name** (Tag, Tag): Desc
        # Match scenes: ### Name (Tag, Tag)
        tags_match = re.search(r'\((.*?)\)', line)
        if tags_match:
            tags_str = tags_match.group(1)
            tags = [t.strip() for t in tags_str.split(',')]
            tags_lower = [t.lower() for t in tags]

            # Logic: If 'action' is present AND ('sport' or 'combat' or specific sports are present)
            # Specific sports: basketball, football, soccer, tennis, volleyball, mma, boxing, wrestling, baseball, bowling, track, gym, gymnastics, swim, skate, cheer
            sports_combat = {'sport', 'combat', 'combat_sport', 'martial arts', 'basketball', 'football', 'soccer', 'tennis', 'volleyball', 'mma', 'boxing', 'wrestling', 'baseball', 'bowling', 'track', 'gym', 'gymnastics', 'swim', 'skate', 'cheer', 'tactical', 'weapon_combat'}
            
            if 'action' in tags_lower and any(t in sports_combat for t in tags_lower):
                # Remove 'action'
                new_tags = [t for t in tags if t.lower() != 'action']
                new_tags_str = ", ".join(new_tags)
                line = line.replace(f"({tags_str})", f"({new_tags_str})")
                modified = True
        
        new_lines.append(line)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(new_lines) + "\n")
        print(f"  > Purged action from {os.path.basename(file_path)}")

if __name__ == "__main__":
    # Target files
    files = [
        os.path.join(DATA_DIR, "interactions.md"),
        os.path.join(DATA_DIR, "poses.md"),
        os.path.join(DATA_DIR, "scenes.md")
    ]
    
    for fp in files:
        if os.path.exists(fp):
            purge_action_if_sport_or_combat(fp)
