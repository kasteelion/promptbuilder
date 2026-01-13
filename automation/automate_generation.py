import os
import sys
import argparse
import asyncio

# Ensure we can import from the root directory
# (Going up one level from 'automation2 directory)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
from core.builder import PromptBuilder
from automation.ai_studio_client import AIStudioClient

def generate_prompts(count=10, match_outfits_prob=0.3):
    """Generate a list of random prompts using the app's logic."""
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
    
    prompts_with_scores = []
    for i in range(count):
        print(f"  Randomizing prompt {i+1}...")
        config = randomizer.randomize(
            num_characters=None, # Random count
            include_scene=True,
            include_notes=True,
            match_outfits_prob=match_outfits_prob,
            candidates=1
        )
        prompt_text = builder.generate(config)
        score = config.get("metadata", {}).get("score", 0)
        prompts_with_scores.append((prompt_text, score, config))
        
    return prompts_with_scores

async def run_automation(count=10, match_outfits_prob=0.3):
    """Generate prompts and images using browser automation."""
    prompts_with_scores = generate_prompts(count, match_outfits_prob)
    
    # Extract just the prompts (add "Generate an image of: " prefix)
    prompts = [f"Generate an image of: {prompt}" for prompt, score, _ in prompts_with_scores]
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    output_dir = os.path.join(parent_dir, "output", "images", "generated_images")
    user_data_dir = os.path.join(parent_dir, ".config", "chrome_profile")
    
    print(f"Images will be saved to: {output_dir}")
    
    # Create AI Studio client
    client = AIStudioClient(
        output_dir=output_dir,
        user_data_dir=user_data_dir,
        headless=False
    )
    
    # Progress callback
    def progress(current, total, message):
        score = prompts_with_scores[current-1][1] if current <= len(prompts_with_scores) else 0
        print(f"\n{message} [Score: {score}]")
    
    # Generate images
    results = await client.generate_images(prompts, progress_callback=progress)
    
    # Print summary
    print("\n=== Generation Summary ===")
    successful = sum(1 for _, img_path in results if img_path)
    print(f"Total prompts: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

def run_local_generation(count=10, match_outfits_prob=0.3):
    """Generate prompts and save to text files without browser automation."""
    prompts_with_scores = generate_prompts(count, match_outfits_prob)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    output_dir = os.path.join(parent_dir, "output", "prompts")
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"Prompts will be saved to: {output_dir}")
    
    import time
    import time
    timestamp = int(time.time())
    for i, (prompt, score, config) in enumerate(prompts_with_scores):
        print(f"  Saving prompt {i+1}/{len(prompts_with_scores)}... [Score: {score}]")
        base_filename = f"gen_only_{timestamp}_{i+1}"
        
        # Save Prompt as Text File
        text_path = os.path.join(output_dir, f"{base_filename}.txt")
        full_text = "Generate an image of: " + prompt
        
        # Append Metadata
        # Note: 'metadata' key usually contains scoring info, while scene/prompt choices are at root
        meta_block = "\n\n# METADATA\n"
        
        # Schene
        if "scene" in config:
            s_val = config["scene"]
            # Handle if it's a dict or string
            s_name = s_val.get("name", str(s_val)) if isinstance(s_val, dict) else str(s_val)
            meta_block += f"Scene: {s_name}\n"
            
        # Base Prompt
        if "base_prompt" in config:
            bp_val = config["base_prompt"]
            bp_name = bp_val.get("name", str(bp_val)) if isinstance(bp_val, dict) else str(bp_val)
            meta_block += f"Base_Prompt: {bp_name}\n"
            
        # Interaction (Notes)
        if "notes" in config and config["notes"]:
            # Notes usually string, but sometimes we track Interaction name in metadata
            # Let's check if the specific interaction name is available in specific metadata
            # or just use the notes text snippet as ID if needed, 
            # BUT the analyzer expects 'Interaction: Name'.
            # The randomizer logic calculates interaction tags.
            # If we don't have the clean name, we might skip or use a hint.
            # Usually randomizer puts 'interaction' in metadata if it chose from a file.
            
            # Check internal metadata for specific keys
            score_meta = config.get("metadata", {})
            if "interaction" in score_meta:
                 i_name = score_meta["interaction"]
                 meta_block += f"Interaction: {i_name}\n"
            else:
                 # Fallback: Use first few words of notes? or Skip.
                 pass

        # Characters
        for char in config.get("selected_characters", []): # Key is 'selected_characters'
            name = char.get('name', 'Unknown')
            outfit = char.get('outfit', {})
            outfit_name = outfit.get('name', str(outfit)) if isinstance(outfit, dict) else str(outfit)
            
            pose = char.get('pose', {})
            pose_name = pose.get('name', str(pose)) if isinstance(pose, dict) else str(pose)
            
            meta_block += f"Character: {name} | Outfit: {outfit_name} | Pose: {pose_name}\n"
            
        meta_block += f"Score: {score}\n"
        
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text + meta_block)
        print(f"    -> {text_path}")
        
    print(f"Done! Generated {len(prompts_with_scores)} prompts.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate prompt generation and image capture.")
    parser.add_argument("--prompts-only", action="store_true", help="Generate prompts to text files only (no browser)")
    parser.add_argument("--count", type=int, default=10, help="Number of prompts to generate")
    parser.add_argument("--match-outfits-prob", type=float, default=0.3, help="Probability of matching outfits (0.0-1.0)")
    args = parser.parse_args()

    try:
        if args.prompts_only:
            run_local_generation(args.count, args.match_outfits_prob)
        else:
            asyncio.run(run_automation(args.count, args.match_outfits_prob))
            
    except KeyboardInterrupt:
        print("Stopped by user.")
