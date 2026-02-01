import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
from core.builder import PromptBuilder

def generate_prompts():
    print("Initializing...")
    loader = DataLoader()
    chars = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    poses = loader.load_presets("poses.md")
    scenes = loader.load_presets("scenes.md")
    interactions = loader.load_interactions()
    schemes = loader.load_color_schemes()
    modifiers = loader.load_modifiers()
    framing = loader.load_framing()
    
    randomizer = PromptRandomizer(chars, base_prompts, poses, scenes, interactions, schemes, modifiers, framing)
    builder = PromptBuilder(chars, base_prompts, poses, schemes, modifiers)
    
    prompts = []
    print("Generating 3 prompts...")
    for i in range(3):
        config = randomizer.randomize(num_characters=None, include_scene=True, include_notes=True)
        # Ensure we have a valid config for builder
        # Builder needs 'selected_characters', 'base_prompt', 'scene', 'notes'
        # The key names match.
        full_prompt = builder.generate(config)
        prompts.append(full_prompt)
        print(f"Generated Prompt #{i+1}")

    with open("generated_prompts.txt", "w", encoding="utf-8") as f:
        for p in prompts:
            f.write(p + "\n" + "-"*80 + "\n")
    
    print("Done! Saved to generated_prompts.txt")

if __name__ == "__main__":
    generate_prompts()
