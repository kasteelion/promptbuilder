import os
import sys
import time

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
from core.builder import PromptBuilder

def generate_prompts_only(count=20, match_outfits_prob=0.3):
    """Generate prompts and save to text files without browser automation."""
    print(f"Generating {count} prompts (Match Outfit Prob: {match_outfits_prob})...")
    
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
    
    timestamp = int(time.time())
    
    for i in range(count):
        print(f"  Randomizing prompt {i+1}...")
        config = randomizer.randomize(
            num_characters=None, # Random count
            include_scene=True,
            include_notes=True,
            match_outfits_prob=match_outfits_prob
        )
        # Get score and breakdown from metadata if available
        # The score is stored in metadata by randomizer.randomize
        score = config.get("metadata", {}).get("score", 0)
        breakdown = config.get("metadata", {}).get("score_breakdown", {})
        
        print(f"    [Score: {score}]")
        if breakdown:
            details = []
            if breakdown.get("mood_matches"): details.append(f"Mood: +{breakdown['mood_matches']}")
            if breakdown.get("style_matches"): details.append(f"Style: +{breakdown['style_matches']}")
            if breakdown.get("interaction_matches"): details.append(f"Int: +{breakdown['interaction_matches']}")
            if breakdown.get("tag_matches"): details.append(f"Tags: +{breakdown['tag_matches']}")
            if breakdown.get("diversity_bonus"): details.append(f"Div: +{breakdown['diversity_bonus']}")
            if breakdown.get("repetitive_penalty"): details.append(f"Rep: {breakdown['repetitive_penalty']}")
            
            if details:
                print(f"      ({', '.join(details)})")
            
            for warning in breakdown.get("warnings", []):
                print(f"      [!] {warning}")
        prompt_text = builder.generate(config)
        
        base_filename = f"gen_only_{timestamp}_{i+1}"
        
        # Build metadata header
        metadata_lines = ["# METADATA"]
        metadata_lines.append(f"Scene: {config.get('scene', 'None')}")
        metadata_lines.append(f"Base_Prompt: {config.get('base_prompt', 'None')}")
        
        # Characters with outfits and poses
        for char in config.get('selected_characters', []):
            char_name = char.get('name', 'Unknown')
            outfit = char.get('outfit', 'None')
            pose = char.get('pose', 'None')
            metadata_lines.append(f"Character: {char_name} | Outfit: {outfit} | Pose: {pose}")
        
        # Interaction/Notes
        notes = config.get('notes', '')
        if notes:
            # Try to extract interaction name if it's a template
            interaction_name = "Custom"
            # Simple heuristic: if notes contains character placeholders, it's likely a template
            if '{char' in notes:
                interaction_name = notes.split(',')[0] if ',' in notes else notes[:50]
            metadata_lines.append(f"Interaction: {interaction_name}")
        
        metadata_lines.append(f"Score: {score}")
        metadata_lines.append("")  # Blank line separator
        
        # Save Prompt as Text File
        text_path = os.path.join(output_dir, f"{base_filename}.txt")
        full_text = "\n".join(metadata_lines) + "\nGenerate an image of: " + prompt_text
        
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text)
            
    print(f"\nDone! Generated {count} prompts.")

if __name__ == "__main__":
    count = 20
    prob = 0.3
    
    # Simple argument parsing
    args = sys.argv[1:]
    if args:
        try:
            # First arg is count
            count = int(args[0])
            # Second arg could be prob
            if len(args) > 1:
                prob = float(args[1])
        except ValueError:
            pass
            
    generate_prompts_only(count, prob)
