import os
import sys
import time

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
from core.builder import PromptBuilder

def generate_prompts_only(count=20):
    """Generate prompts and save to text files without browser automation."""
    print(f"Generating {count} prompts...")
    
    loader = DataLoader()
    chars = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    poses = loader.load_presets("poses.md")
    scenes = loader.load_presets("scenes.md")
    schemes = loader.load_color_schemes()
    modifiers = loader.load_modifiers()
    interactions = loader.load_interactions()
    framing = loader.load_framing()
    
    builder = PromptBuilder(chars, base_prompts, poses, schemes, modifiers, framing)
    randomizer = PromptRandomizer(chars, base_prompts, poses, scenes, interactions, schemes, modifiers, framing)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "generated_prompts_only")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Prompts will be saved to: {output_dir}")
    
    for i in range(count):
        print(f"  Randomizing prompt {i+1}...")
        config = randomizer.randomize(
            num_characters=None, # Random count
            include_scene=True,
            include_notes=True
        )
        prompt_text = builder.generate(config)
        
        timestamp = int(time.time())
        base_filename = f"gen_only_{timestamp}_{i+1}"
        
        # Save Prompt as Text File
        text_path = os.path.join(output_dir, f"{base_filename}.txt")
        full_text = "Generate an image of: " + prompt_text
        
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text)
            
    print(f"\nDone! Generated {count} prompts.")

if __name__ == "__main__":
    count = 20
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
            
    generate_prompts_only(count)
