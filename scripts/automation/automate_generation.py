import os
import sys
import argparse
import asyncio

# Ensure we can import from the root directory
# (Going up one level from 'automation2 directory)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(project_root, "src"))

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
from core.builder import PromptBuilder
from utils.ai_client import AIStudioClient

def generate_prompts(count=10, match_outfits_prob=0.3, format_type="markdown"):
    """Generate a list of random prompts using the app's logic."""
    print(f"Generating {count} prompts (Match Outfit Prob: {match_outfits_prob}, Format: {format_type})...")
    loader = DataLoader()
    chars = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    poses = loader.load_presets("poses.md")
    scenes = loader.load_presets("scenes.md")
    schemes = loader.load_color_schemes()
    modifiers = loader.load_modifiers()
    interactions = loader.load_interactions()
    framing = loader.load_framing()
    tag_rules = loader.load_tag_rules()
    scene_constraints = loader.load_scene_constraints()
    
    print(f"Stats: {len(chars)} chars, {len(poses)} poses, {len(scenes)} scenes, {len(tag_rules.get('hub_tags',[]))} hubs.")
    
    builder = PromptBuilder(chars, base_prompts, poses, schemes, modifiers, framing)
    randomizer = PromptRandomizer(chars, base_prompts, poses, scenes, interactions, schemes, modifiers, framing, scene_constraints, tag_rules)
    
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
        prompt_text = builder.generate(config, format_type=format_type)
        score = config.get("metadata", {}).get("score", 0) if isinstance(config, dict) else getattr(config, "metadata", {}).get("score", 0)
        prompts_with_scores.append((prompt_text, score, config))
        
    return prompts_with_scores

async def run_automation(count=10, match_outfits_prob=0.3, format_type="markdown"):
    """Generate prompts and images using browser automation."""
    prompts_with_scores = generate_prompts(count, match_outfits_prob, format_type=format_type)
    
    # Extract just the prompts (add "Generate an image of: " prefix)
    prompts = [f"Generate an image of: {prompt}" for prompt, score, _ in prompts_with_scores]
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    output_dir = os.path.join(project_root, "output", "images", "generated_images")
    user_data_dir = os.path.join(project_root, ".config", "chrome_profile")
    
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
    
    # Save text files for successful generations
    print("\nSaving paired text files...")
    for i, (prompt_used, img_path) in enumerate(results):
        if not img_path:
            continue
            
        # Get corresponding config
        if i < len(prompts_with_scores):
            _, score, config = prompts_with_scores[i]
            
            # Construct text path (same basename as image)
            # img_path is like ".../gen_TIMESTAMP_IDX.png"
            txt_path = os.path.splitext(img_path)[0] + ".txt"
            
            # Build Metadata Block
            meta_block = "\n\n# METADATA\n"
            
            # Scene
            if "scene" in config:
                s_val = config["scene"]
                s_name = s_val.get("name", str(s_val)) if isinstance(s_val, dict) else str(s_val)
                meta_block += f"Scene: {s_name}\n"
                if "scene_category" in config:
                    meta_block += f"Scene_Category: {config['scene_category']}\n"
            
            # Base Prompt
            if "base_prompt" in config:
                bp_val = config["base_prompt"]
                bp_name = bp_val.get("name", str(bp_val)) if isinstance(bp_val, dict) else str(bp_val)
                meta_block += f"Base_Prompt: {bp_name}\n"
            
            # Interaction
            score_meta = config.get("metadata", {})
            if "interaction" in score_meta:
                 meta_block += f"Interaction: {score_meta['interaction']}\n"
            elif "notes" in config and config["notes"]:
                 meta_block += f"Interaction_Note: {config['notes']}\n"
                 
            # Composition
            if "composition_mode" in score_meta:
                 meta_block += f"Composition_Mode: {score_meta['composition_mode']}\n"

            # Characters
            for char in config.get("selected_characters", []):
                name = char.get('name', 'Unknown')
                outfit = char.get('outfit', {})
                outfit_name = outfit.get('name', str(outfit)) if isinstance(outfit, dict) else str(outfit)
                pose = char.get('pose', {})
                pose_name = pose.get('name', str(pose)) if isinstance(pose, dict) else str(pose)
                meta_block += f"Character: {name} | Outfit: {outfit_name} | Pose: {pose_name}\n"
                
            meta_block += f"Score: {score}\n"
            
            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(prompt_used + meta_block)
            except Exception as e:
                print(f"Failed to save text for {img_path}: {e}")

    # Print summary
    print("\n=== Generation Summary ===")
    successful = sum(1 for _, img_path in results if img_path)
    print(f"Total prompts: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

def run_local_generation(count=10, match_outfits_prob=0.3, format_type="markdown"):
    """Generate prompts and save to text files without browser automation."""
    prompts_with_scores = generate_prompts(count, match_outfits_prob, format_type=format_type)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    output_dir = os.path.join(project_root, "output", "prompts")
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"Prompts will be saved to: {output_dir}")
    
    import time
    timestamp = int(time.time())
    for i, (prompt, score, config) in enumerate(prompts_with_scores):
        print(f"  Saving prompt {i+1}/{len(prompts_with_scores)}... [Score: {score}]")
        base_filename = f"gen_only_{timestamp}_{i+1}"
        
        # Save Prompt as Text File
        text_path = os.path.join(output_dir, f"{base_filename}.txt")
        full_text = prompt if format_type in ("midjourney", "sdxl") else "Generate an image of: " + prompt
        
        # Append Metadata
        meta_block = "\n\n# METADATA\n"
        meta_block += f"Format_Profile: {format_type}\n"
        
        # Scene
        if isinstance(config, dict) and "scene" in config:
            s_val = config["scene"]
            s_name = s_val.get("name", str(s_val)) if isinstance(s_val, dict) else str(s_val)
            meta_block += f"Scene: {s_name}\n"
            if "scene_category" in config:
                meta_block += f"Scene_Category: {config['scene_category']}\n"
        elif hasattr(config, "scene"):
            meta_block += f"Scene: {config.scene}\n"
            if hasattr(config, "scene_category"):
                meta_block += f"Scene_Category: {config.scene_category}\n"
            
        # Base Prompt / Art Style
        if isinstance(config, dict) and "base_prompt" in config:
            bp_val = config["base_prompt"]
            bp_name = bp_val.get("name", str(bp_val)) if isinstance(bp_val, dict) else str(bp_val)
            meta_block += f"Base_Prompt: {bp_name}\n"
        elif hasattr(config, "base_prompt"):
            meta_block += f"Base_Prompt: {config.base_prompt}\n"
            
        # Interaction (Notes)
        notes = config.get("notes") if isinstance(config, dict) else getattr(config, "notes", None)
        if notes:
            score_meta = config.get("metadata", {}) if isinstance(config, dict) else getattr(config, "metadata", {})
            if "interaction" in score_meta:
                 i_name = score_meta["interaction"]
                 meta_block += f"Interaction: {i_name}\n"
            
        # Composition Mode
        score_meta = config.get("metadata", {}) if isinstance(config, dict) else getattr(config, "metadata", {})
        if "composition_mode" in score_meta:
             c_mode = score_meta["composition_mode"]
             meta_block += f"Composition_Mode: {c_mode}\n"

        # Characters
        chars_list = config.get("selected_characters", []) if isinstance(config, dict) else getattr(config, "selected_characters", [])
        for char in chars_list:
            name = getattr(char, "name", None) or (char.get("name", "Unknown") if isinstance(char, dict) else "Unknown")
            outfit = getattr(char, "outfit", None) or (char.get("outfit", "") if isinstance(char, dict) else "")
            outfit_name = outfit.get("name", str(outfit)) if isinstance(outfit, dict) else str(outfit)
            
            pose = getattr(char, "pose_preset", None) or getattr(char, "pose", None) or (char.get("pose", "") if isinstance(char, dict) else "")
            pose_name = pose.get("name", str(pose)) if isinstance(pose, dict) else str(pose)
            
            scheme = getattr(char, "color_scheme", None) or (char.get("color_scheme") if isinstance(char, dict) else None)
            scheme_str = f" | Color_Scheme: {scheme}" if scheme and scheme != "The Standard" else ""
            
            meta_block += f"Character: {name} | Outfit: {outfit_name} | Pose: {pose_name}{scheme_str}\n"
            
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
    parser.add_argument("--format", choices=["markdown", "prose", "midjourney", "sdxl"], default="markdown", help="Output prompt format profile")
    args = parser.parse_args()

    try:
        if args.prompts_only:
            run_local_generation(args.count, args.match_outfits_prob, format_type=args.format)
        else:
            asyncio.run(run_automation(args.count, args.match_outfits_prob, format_type=args.format))
            
    except KeyboardInterrupt:
        print("Stopped by user.")
