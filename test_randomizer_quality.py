
import sys
import os
import random

# Add project root to path
sys.path.append(os.getcwd())

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer

def test_randomizer_quality():
    print("Initializing DataLoader...")
    loader = DataLoader()
    
    characters = loader.load_characters()
    print(f"Loaded {len(characters)} characters.")
    
    outfits = loader.load_outfits()
    print(f"Loaded {len(outfits)} outfit categories.")
    
    base_prompts = loader.load_base_prompts()
    print(f"Loaded {len(base_prompts)} base prompts.")
    
    scenes = loader.load_presets("scenes.md")
    poses = loader.load_presets("poses.md")
    interactions = loader.load_interactions()
    color_schemes = loader.load_color_schemes()
    framing = loader.load_framing()
    
    print("Initializing PromptRandomizer...")
    randomizer = PromptRandomizer(
        characters=characters,
        base_prompts=base_prompts,
        poses=poses,
        interactions=interactions,
        color_schemes=color_schemes,
        scenes=scenes,
        framing=framing
    )
    
    print("\nRunning Randomization Quality Tests (20 iterations)...")
    print("-" * 60)
    
    base_char_matches = 0
    coherence_matches = 0
    total = 0
    
    for i in range(20):
        # Randomize normally
        result = randomizer.randomize(
            num_characters=1,
            include_scene=True,
            include_notes=True
        )
        
        selected_chars_list = result.get('selected_characters', [])
        base_prompt_name = result.get('base_prompt', "None")
        scene_name = result.get('scene', "").split(":")[0] if result.get('scene') else "None"
        
        # Get tags for characters
        char_tags = set()
        char_names = []
        
        for char_data in selected_chars_list:
            if isinstance(char_data, dict):
                name = char_data.get('name', 'Unknown')
                char_names.append(name)
                
                # Look up tags in master list
                if name in characters:
                    c = characters[name]
                    ct = c.get('tags', [])
                    if isinstance(ct, str):
                        ct = [x.strip() for x in ct.split(',')]
                    for t in ct:
                        char_tags.add(str(t).lower())
            else:
                print(f"WARNING: char_data is not dict: {type(char_data)}")

        # Get Base Prompt Tags
        bp_data = base_prompts.get(base_prompt_name, {})
        bp_tags = set()
        if isinstance(bp_data, dict):
             t = bp_data.get('tags', [])
             for x in t:
                 bp_tags.add(str(x).lower())
        
        # Get content tags (Pose)
        pose_category = ""
        pose_preset = ""
        pose_tags = set()
        
        # Currently the randomizer output schema for characters is:
        # {name, outfit, pose_preset, ...}
        # But it doesn't return the raw tags of the chosen pose.
        # We need to look it up in 'poses' dict using category/preset name?
        # Wait, randomizer output structure:
        # char_data = {
        #    "name": char_name,
        #    "pose_category": pose_category,
        #    "pose_preset": pose_preset,
        #    ...
        # }
        
        for char_data in selected_chars_list:
            if isinstance(char_data, dict):
                p_cat = char_data.get("pose_category", "")
                p_pre = char_data.get("pose_preset", "")
                
                # Look up tags for this pose in 'poses'
                # poses is {Category: {PresetName: Description}}
                # Wait, PresetParser usually parses descriptions
                # If tags are embedded manually or via parser?
                # The Parser updates might have put tags in the dict if structured like base_prompts
                # But typically poses are simple Key:Value pairs in current simple parser?
                # Actually, earlier 'poses.md' review showed "- **Name** (Tag1, Tag2): Desc"
                # The 'MarkdownParser.parse_presets' handles this?
                # Let's check 'logic/parsers.py' or assume we need to re-parse the key "Name (Tag1)" to extract tags here for testing.
                if p_cat and p_pre:
                    pose_preset = p_pre # Capture for printing
                    
                    # Look up tags in the poses data structure
                    cat_dict = poses.get(p_cat, {})
                    if p_pre in cat_dict:
                        data = cat_dict[p_pre]
                        ptags = data.get("tags", [])
                        for t in ptags:
                            pose_tags.add(t.strip().lower())

        # Check overlap
        overlap = char_tags.intersection(bp_tags)
        is_match = len(overlap) > 0
        
        # Check coherence (Base vs Pose)
        coherence_overlap = pose_tags.intersection(bp_tags)
        is_coherent = len(coherence_overlap) > 0
        
        if is_match:
            base_char_matches += 1
        if is_coherent:
            coherence_matches += 1
        total += 1
        
        print(f"Iter {i+1}:")
        print(f"  Char: {char_names} (Tags: {list(char_tags)})")
        print(f"  Scene: {scene_name}")
        print(f"  Base: {base_prompt_name} (Tags: {list(bp_tags)})")
        print(f"  Pose: {pose_preset} (Tags: {list(pose_tags)})")
        print(f"  Base-Char Match: {'YES' if is_match else 'NO'} (Overlap: {list(overlap)})")
        print(f"  Base-Pose Match: {'YES' if is_coherent else 'NO'} (Overlap: {list(coherence_overlap)})")
        print("-" * 30)

    print(f"\nFinal Results:")
    print(f"Base-Char Coherence: {base_char_matches}/{total} ({base_char_matches/total*100:.1f}%)")
    print(f"Base-Pose Coherence: {coherence_matches}/{total} ({coherence_matches/total*100:.1f}%)") # This is what we care about now


if __name__ == "__main__":
    test_randomizer_quality()
