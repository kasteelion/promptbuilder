import os

# Configuration
DATA_DIR = r"c:\Users\parking\Desktop\promptbuilder\data\outfits"

# Mapping of Filename -> Specific Tag to replace 'Combat' with
# Only files listed here will be touched if they have 'Combat' tag.

RETARGET_MAP = {
    # Sport Combat
    "Boxing.txt": "combat_sport",
    "MMA.txt": "combat_sport",
    "MMA Combat Gear.txt": "combat_sport",
    "Pro Wrestling.txt": "combat_sport",
    "Training.txt": "combat_sport",
    "Wrestling.txt": "combat_sport",
    
    # Weapon/Fantasy Combat
    "Archer.txt": "weapon_combat",
    "Assassin.txt": "weapon_combat",
    "Battle Priest.txt": "weapon_combat",
    "Beastmaster.txt": "weapon_combat",
    "Magic Knight.txt": "weapon_combat",
    "Red Mage.txt": "weapon_combat",
    "Spirit Priestess Warrior.txt": "weapon_combat",
    "Warrior.txt": "weapon_combat",
    "Barbarian.txt": "weapon_combat",
    "Knight.txt": "weapon_combat",
    "Samurai.txt": "weapon_combat",
    
    # Tactical Combat
    "Cyber-Tactical Combat.txt": "combat_tactical",
    "Tactical Scout.txt": "combat_tactical"
}

def process_file(filepath, specific_tag):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        modified = False
        new_lines = []
        for line in lines:
            if line.strip().startswith("tags:") and "Combat" in line:
                # Replace 'Combat' with strict tag
                # We do a simple string replace of "Combat" -> specific_tag
                # Only if it's the exact word "Combat" to avoid "Combatants" etc if that existed
                # But here formatting is [Tag, Tag], so "Combat" usually appears as "Combat," or ", Combat" or "[Combat"
                
                # Safer: standard replace since tags are capitalized usually
                new_line = line.replace("Combat", specific_tag)
                new_lines.append(new_line)
                modified = True
                print(f"Updated {os.path.basename(filepath)}: {line.strip()} -> {new_line.strip()}")
            else:
                new_lines.append(line)
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    print("Starting Combat Tag Separation...")
    
    # Walk through all outfit directories
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file in RETARGET_MAP:
                specific_tag = RETARGET_MAP[file]
                filepath = os.path.join(root, file)
                process_file(filepath, specific_tag)
                
    print("Done.")

if __name__ == "__main__":
    main()
