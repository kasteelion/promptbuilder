
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.builder import PromptBuilder
from logic.randomizer import PromptRandomizer

from logic.data_loader import DataLoader

def run_repro():
    print("Loading Data...")
    loader = DataLoader() # DataLoader takes no args
    data = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    poses = loader.load_presets("poses.md")
    scenes = loader.load_presets("scenes.md")
    
    # Optional: Builder needs these
    # builder = PromptBuilder(data, base_prompts, poses, {}, {}, {}) # We don't need builder instance for this test really
    
    randomizer = PromptRandomizer(
        characters=data,
        base_prompts=base_prompts,
        poses=poses,
        scenes=scenes
    )
    
    # 1. Verify Sports Action Tags
    bp_name = 'Sports Action: "Frozen Velocity"'
    bp_data = base_prompts.get(bp_name)
    if not bp_data:
        print(f"ERROR: Could not find base prompt '{bp_name}'")
        return
        
    tags = bp_data.get("tags", [])
    _, _, blocked = randomizer._extract_special_tags(tags)
    print(f"Sports Action Blocked Tags: {blocked}")
    
    if "noir" not in blocked:
        print("FAIL: 'noir' is missing from blocked tags!")
    else:
        print("PASS: 'noir' is in blocked tags.")

    # 2. Verify Jazz Club Patron Tags (via a character)
    char_name = list(data.keys())[0] # Pick first char
    outfits = data[char_name].get("outfits", {})
    jazz_outfit = outfits.get("Jazz Club Patron")
    if not jazz_outfit:
        # Try to find it
        for name in outfits:
            if "Jazz" in name:
                jazz_outfit = outfits[name]
                print(f"Found outfit: {name}")
                break
    
    if jazz_outfit:
        jazz_tags = randomizer._get_tags(jazz_outfit)
        print(f"Jazz Club Patron Tags: {jazz_tags}")
        jazz_tags_lower = [t.lower() for t in jazz_tags]
        if "noir" in jazz_tags_lower:
             print("PASS: 'noir' tag found on outfit.")
        else:
             print("FAIL: 'noir' tag MISSING on outfit.")
    else:
        print("FAIL: Could not find Jazz Club Patron on character.")

    # 3. Test _find_matching_outfit
    print("\nTesting _find_matching_outfit...")
    # Force search for Jazz Club Patron
    # matching logic only considers COMMON outfits. Jazz Club Patron is likely common.
    # Pass 'noir' in blocked tags.
    
    # We'll patch _find_matching_outfit to only consider Jazz Club Patron if possible, 
    # or just see if it gets filtered.
    
    # Actually, let's just check if is_blocked logic works manually
    if jazz_outfit:
        is_blocked = False
        outfit_tags = [t.lower() for t in randomizer._get_tags(jazz_outfit)]
        if any(bt in outfit_tags for bt in blocked):
            is_blocked = True
        
        print(f"Manual Block Check: is_blocked={is_blocked}")
        if is_blocked:
            print("PASS: Logic correctly blocks it.")
        else:
            print("FAIL: Logic failed to block it.")

if __name__ == "__main__":
    run_repro()
