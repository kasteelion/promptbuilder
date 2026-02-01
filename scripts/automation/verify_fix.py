import sys
import os
import random

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.randomizer import PromptRandomizer
from logic.data_loader import DataLoader

def test_randomization():
    print("Initializing DataLoader...")
    loader = DataLoader()
    
    # Load all data components separately
    characters = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    poses = loader.load_presets("poses.md")
    scenes = loader.load_presets("scenes.md")
    interactions = loader.load_interactions()
    color_schemes = loader.load_color_schemes()
    modifiers = loader.load_modifiers()
    framing = loader.load_framing()
    
    print("Initializing Randomizer...")
    randomizer = PromptRandomizer(
        characters=characters,
        base_prompts=base_prompts,
        poses=poses,
        scenes=scenes,
        interactions=interactions,
        color_schemes=color_schemes,
        modifiers=modifiers,
        framing=framing
    )
    
    print("\n--- Testing Randomization (3 Batches) ---\n")
    for i in range(3):
        try:
            config = randomizer.randomize(num_characters=2, include_scene=True, include_notes=True)
            print(f"Candidate {i+1}:")
            print(f"  Hub Tag:   {config['metadata'].get('hub_tag')}")
            print(f"  Scenario:  {config['scenario_name']}")
            print(f"  Style:     {config['base_prompt']}")
            print(f"  Scene:     {config['scene_category']} - {config['scene']}")
            print(f"  Outfits:   {[c['outfit'] for c in config['selected_characters']]}")
            print(f"  Notes:     {config['notes']}")
            print("-" * 40)
        except Exception as e:
            print(f"Failed! Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_randomization()
