import json
import re
from pathlib import Path

# Project root setup
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
char_dir = project_root / "assets" / "data" / "characters"
config_path = project_root / "assets" / "config" / "tag_rules.json"

# Heuristic Mapping: Keyword -> Hub Tag
# Must match hub_tags in tag_rules.json
KEYWORD_MAP = {
    "Casual": ["casual", "everyday", "relaxed", "jeans", "t-shirt", "hoodie", "sneakers", "comfortable", "denim"],
    "Urban": ["urban", "city", "street", "modern", "concrete", "downtown", "metro", "apartment"],
    "Work": ["work", "office", "business", "professional", "corporate", "suit", "formal", "blazer", "job", "career"],
    "Social": ["social", "party", "event", "friend", "gathering", "outgoing", "charming", "charismatic"],
    "Home": ["home", "cozy", "lounge", "sleepwear", "pajamas", "bed", "domestic", "tea", "book", "relax"],
    "Sport": ["sport", "athletic", "gym", "active", "run", "training", "workout", "muscle", "fitness"],
    "Fantasy": ["fantasy", "magic", "sword", "armor", "ancient", "dragon", "spell", "mystical", "warrior", "priestess"],
    "Sci-Fi": ["sci-fi", "future", "tech", "robot", "cyber", "space", "hologram", "digital"],
    "Retro": ["retro", "vintage", "classic", "old-school", "1950s", "1960s", "1970s", "1980s", "1990s"],
    "Noir": ["noir", "mystery", "detective", "shadow", "dark", "crime", "smoke", "rain"],
    "Intimate": ["intimate", "sensual", "romance", "love", "bedroom", "boudoir"],
    "Action": ["action", "dynamic", "fast", "motion", "combat", "fight"],
    "Vintage": ["vintage", "antique", "historical", "classic"],
    "Magic": ["magic", "spell", "witch", "wizard", "arcane"]
}

def load_hub_tags():
    if not config_path.exists():
        print("Warning: tag_rules.json not found.")
        return []
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return data.get("hub_tags", [])
    except Exception as e:
        print(f"Error loading tag_rules: {e}")
        return []

def auto_tag():
    print(f"Scanning {char_dir}...")
    valid_hubs = set(load_hub_tags())
    print(f"Valid Hubs: {valid_hubs}")
    
    fixed_count = 0
    
    for filepath in char_dir.glob("*.md"):
        content = filepath.read_text(encoding="utf-8")
        original_content = content
        
        # Extract existing tags
        tags_match = re.search(r'\*\*Tags:\*\*(.*)', content, re.IGNORECASE)
        if not tags_match:
            print(f"⚠️ No Tags line in {filepath.name}")
            continue
            
        existing_tags_str = tags_match.group(1)
        existing_tags = [t.strip() for t in existing_tags_str.split(',') if t.strip()]
        
        # Identify new tags
        new_tags = set()
        
        # 1. Content check
        lower_content = content.lower()
        for hub, keywords in KEYWORD_MAP.items():
            if hub in valid_hubs:
                # Check if hub is already in tags (case insensitive)
                if any(t.lower() == hub.lower() for t in existing_tags):
                    continue
                
                # Check keywords
                for kw in keywords:
                    # boundary check using regex to avoid partial matches (e.g. "classic" in "classical")
                    if re.search(r'\b' + re.escape(kw) + r'\b', lower_content):
                        new_tags.add(hub)
                        break
        
        # 2. Apply new tags
        if new_tags:
            print(f"➕ {filepath.name}: Adding {new_tags}")
            # Append to existing tags
            # We recreate the line
            all_tags = existing_tags + list(new_tags)
            # Sort for neatness? Or just append.
            # Start uppercase check? "Casual" is preferred over "casual".
            
            new_tags_str = ", ".join(all_tags)
            new_line = f"**Tags:** {new_tags_str}"
            
            content = content.replace(tags_match.group(0), new_line)
            
            if content != original_content:
                filepath.write_text(content, encoding="utf-8")
                fixed_count += 1
                
    print(f"\nTotal character files updated: {fixed_count}")

if __name__ == "__main__":
    auto_tag()
