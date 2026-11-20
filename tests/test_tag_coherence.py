
import sys
import os
from collections import Counter

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.randomizer import PromptRandomizer
from logic.data_loader import DataLoader

def test_sport_coherence():
    print("Initializing components...")
    loader = DataLoader()
    # Manually construct data dict
    data = {
        "scenes": loader.load_presets("scenes.md"),
        "poses": loader.load_presets("poses.md"),
        "base_prompts": loader.load_base_prompts(),
        "characters": loader.load_characters(), 
        "outfits": loader.load_outfits()
    }
    randomizer = PromptRandomizer(
        characters=data["characters"],
        base_prompts=data["base_prompts"],
        poses=data["poses"],
        scenes=data["scenes"]
    )
    
    # Define a test configuration with forced context
    # Context: A character in a Football Field
    # We want to see if they get Bowling poses
    
    print("\n--- Test: Football Field Context ---")
    football_matches = 0
    bowling_matches = 0
    total_runs = 50
    
    # Mocking a character setup that would lead to a football scene logic
    # We'll just check the _select_smart_pose method directly if possible, 
    # or run full randomize loops with fixed scene.
    
    # Let's use the internal logic to see scores for clarity
    # Context tags for a Football Field + Athlete
    context_tags = {"Sport", "Football", "Outdoor", "Athletic"} # "Athletic" from character likely
    context_tags = randomizer._expand_tags(context_tags)
    
    print(f"Context Tags: {context_tags}")
    
    # Get all poses
    all_poses = data.get("poses", {})
    
    # Check scores for specific known poses
    print("\nChecking score for specific poses:")
    
    # Known Football Pose
    football_pose = "Flag Football Catch"
    fb_pose_data = all_poses.get("Sports", {}).get(football_pose)
    if fb_pose_data:
        fb_tags = randomizer._expand_tags(set(fb_pose_data.get("tags", [])))
        fb_score = len(context_tags.intersection(fb_tags))
        print(f"Pose: '{football_pose}' | Tags: {fb_tags} | Score: {fb_score}")
    else:
        print(f"WARNING: Pose '{football_pose}' not found!")

    # Known Bowling Pose
    bowling_pose = "Bowling Approach"
    bw_pose_data = all_poses.get("Sports", {}).get(bowling_pose) or all_poses.get("Bowling", {}).get(bowling_pose) 
    # Note: Category might be Sports or Bowling depending on file structure, likely 'Sports' key in dict based on file headers? 
    # Actually poses.md has "## Sports", so they are in "Sports" dict key.
    
    if bw_pose_data:
        bw_tags = randomizer._expand_tags(set(bw_pose_data.get("tags", [])))
        bw_score = len(context_tags.intersection(bw_tags))
        print(f"Pose: '{bowling_pose}' | Tags: {bw_tags} | Score: {bw_score}")
        
        if bw_score > 0:
            print("FAILURE: Bowling pose has positive score in Football context!")
        else:
            print("SUCCESS: Bowling pose has 0 score in Football context.")
    else:
        print(f"WARNING: Pose '{bowling_pose}' not found!")

    # Known Generic Fitness Pose (should match)
    gym_pose = "Stretching Pre-Fight"
    gym_data = all_poses.get("Sports", {}).get(gym_pose)
    if gym_data:
        gym_tags = randomizer._expand_tags(set(gym_data.get("tags", [])))
        gym_score = len(context_tags.intersection(gym_tags))
        print(f"Pose: '{gym_pose}' | Tags: {gym_tags} | Score: {gym_score}")


    # Now run a full simulation loop to see what actually gets picked
    print("\n--- Simulation: 50 selections ---")
    
    # We will manually call _select_smart_pose with our context
    # format of _select_smart_pose(character_data: dict, context_tags: set)
    dummy_char = {"name": "TestAthlete"}
    
    selections = []
    for _ in range(total_runs):
        # Correct signature: (all_poses, char_tags, scene_category, personality, theme_tags)
        pose_cat = randomizer._select_smart_pose(data["poses"], context_tags, "Sports", "", None)
        
        # Determine pose name from category
        pose_presets = data["poses"].get(pose_cat, {})
        if pose_presets:
            import random
            pose_name = random.choice(list(pose_presets.keys()))
        else:
            pose_name = "None"
            
        selections.append(pose_name)
    
    counts = Counter(selections)
    print("\nTop 10 selected poses:")
    for name, count in counts.most_common(10):
        print(f"{name}: {count}")
        
    # Verify no bowling
    bowling_hits = sum(1 for p in selections if "Bowling" in p)
    print(f"\nTotal Bowling Poses Selected: {bowling_hits}")
    
    if bowling_hits == 0:
        print("VERIFICATION PASSED: No bowling poses selected in Football context.")
    else:
        print("VERIFICATION FAILED: Bowling poses were selected.")

if __name__ == "__main__":
    test_sport_coherence()
