#!/usr/bin/env python3
"""
Tool to automatically generate profile photos for characters that lack them.

Usage:
    python dev-tools/generate_missing_photos.py [--dry-run] [--count 5]

Workflow:
1. Scans data/characters/*.md for characters missing a **Photo:** field.
2. Generates a "Portrait" prompt based on their appearance and Base outfit.
3. Uses the AI Studio automation (browser) to generate the image.
4. Saves the image to data/characters/images/<name>.png.
5. Updates the markdown file to reference the new photo.
"""

import os
import sys
import re
import argparse
import asyncio
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.data_loader import DataLoader
from logic.character_parser import CharacterParser
from automation.ai_studio_client import AIStudioClient
from utils.validation import sanitize_filename

from core.builder import PromptBuilder
from core.definitions import PromptConfig, SelectedCharacterConfig

async def generate_images_for_missing(characters_info, data_assets, output_dir, dry_run=False):
    """
    Generate images for the identified missing characters using the main app's PromptBuilder.
    
    Args:
        characters_info: List of dicts with character metadata
        data_assets: Dict containing all loaded data assets (base_prompts, poses, etc.)
        output_dir: Directory to save images
        dry_run: If True, skip generation and file updates
    """
    if not characters_info:
        print("No characters found missing photos.")
        return

    print(f"Found {len(characters_info)} characters missing photos.")
    
    # Initialize PromptBuilder
    builder = PromptBuilder(
        characters=data_assets['characters'],
        base_prompts=data_assets['base_prompts'],
        poses=data_assets['poses'],
        color_schemes=data_assets['color_schemes'],
        modifiers=data_assets['modifiers'],
        framing=data_assets['framing']
    )

    # 1. Prepare Prompts
    prompts = []
    
    # Standard settings for profile photos
    # These must match the KEYS in base_prompts.md and scenes.md exactly
    BASE_STYLE = 'Photorealistic: "High-Fidelity Candid"'
    SCENE_NAME = "Photo Studio"
    POSE_CATEGORY = "Basic Poses"
    POSE_PRESET = "Standing"

    # Flatten scenes for easier lookup (original is {category: {name: data}})
    flat_scenes = {}
    for cat_name, items in data_assets['scenes'].items():
        for item_name, item_data in items.items():
            flat_scenes[item_name] = item_data

    # Find the scene text
    scene_lookup = flat_scenes.get(SCENE_NAME, "")
    if isinstance(scene_lookup, dict):
        scene_text = scene_lookup.get("description", str(scene_lookup))
    else:
        scene_text = scene_lookup

    for char_data in characters_info:
        name = char_data['name']
        char_def = data_assets['characters'].get(name, {})
        
        # Include all character traits (like Glasses, freckles, etc.)
        # The user specifically mentioned wanting these "modifiers" used.
        available_traits = char_def.get("traits", {})
        selected_traits = list(available_traits.keys())
        
        # We manually ensure traits are joined properly if appends happen
        appearance = char_def.get("appearance", "")

        # Create a PromptConfig for this character's portrait
        config = PromptConfig(
            base_prompt=BASE_STYLE,
            scene=scene_text, # Pass the full text
            selected_characters=[
                SelectedCharacterConfig(
                    name=name,
                    outfit="Base",
                    pose_category=POSE_CATEGORY,
                    pose_preset=POSE_PRESET,
                    character_traits=selected_traits, # Include character-specific traits
                    use_signature_color=True 
                )
            ]
        )

        # Generate the professional prompt using the main logic
        prompt_text = builder.generate(config)
        prompts.append(prompt_text)
        
        if dry_run:
            print(f"[Dry Run] Would generate for: {name}")
            print(f"  Prompt: {prompt_text[:250]}... [truncated]")

    # Save prompts to file for manual backup
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_file = os.path.join(script_dir, "missing_photos_prompts.txt")
    with open(prompts_file, "w", encoding="utf-8") as f:
        for p in prompts:
            f.write(p + "\n\n")
    print(f"Saved {len(prompts)} prompts to {prompts_file}")

    if dry_run:
        return

    # Save prompts to file for manual backup
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_file = os.path.join(script_dir, "missing_photos_prompts.txt")
    with open(prompts_file, "w", encoding="utf-8") as f:
        for p in prompts:
            f.write(p + "\n\n")
    print(f"Saved {len(prompts)} prompts to {prompts_file}")

    if dry_run:
        return

    # 2. Generate Images via Automation
    print(f"\nStarting generation batch for {len(prompts)} images...")
    
    # We use a temp directory for generation, then move to final
    temp_gen_dir = os.path.join(output_dir, "temp_gen")
    client = AIStudioClient(output_dir=temp_gen_dir, headless=False)
    
    def progress(current, total, msg):
        print(f"{msg} ({current}/{total})")

    # Run the batch generation
    results = await client.generate_images(prompts, progress_callback=progress)
    
    # 3. Process Results and Update Files
    print("\nProcessing results...")
    
    for i, (prompt_text, img_path) in enumerate(results):
        char_data = characters_info[i]
        name = char_data['name']
        source_path = char_data['source_path']
        
        if not img_path:
            print(f"Failed to generate image for {name}")
            continue
            
        if not os.path.exists(img_path):
            print(f"Image file missing for {name}: {img_path}")
            continue

        # Move to final location
        # Standardized filename: name_photo.png
        safe_name = sanitize_filename(name).lower().replace(" ", "_")
        final_filename = f"{safe_name}_photo.png"
        final_path = os.path.join(output_dir, final_filename)
        
        try:
            shutil.move(img_path, final_path)
            print(f"Saved image to: {final_path}")
            
            # Update Markdown File
            update_markdown_file(source_path, name, final_filename)
            
        except Exception as e:
            print(f"Error processing {name}: {e}")

    # Cleanup temp
    try:
        os.rmdir(temp_gen_dir)
    except:
        pass

def update_markdown_file(file_path, char_name, relative_image_path):
    """
    Insert the **Photo:** field into the markdown file for the specific character.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # We need to find the specific character block
        # Pattern: ### Character Name ... **Appearance:**
        # We want to insert **Photo:** before **Appearance:** or inside the block.
        # Convention: Usually goes after the header or before appearance.
        
        # Split by character headers to isolate the block
        parts = re.split(r"(^###\s+.*$)", content, flags=re.MULTILINE)
        
        new_content = parts[0] # Preamble
        
        for i in range(1, len(parts), 2):
            header = parts[i]
            body = parts[i+1]
            
            if char_name in header:
                # This is our character
                if "**Photo:**" not in body:
                    print(f"Updating file {file_path} for {char_name}...")
                    
                    # Insert Photo field before Appearance
                    # Use a replacement on the body string
                    if "**Appearance:**" in body:
                        new_body = body.replace("**Appearance:**", f"**Photo:** {relative_image_path}\n**Appearance:**", 1)
                    else:
                        # Fallback: Just append to start of body
                        new_body = f"\n**Photo:** {relative_image_path}\n" + body
                        
                    body = new_body
                elif "[" in body and "]" in body and "photo" in body.lower():
                     # Fix broken markdown link syntax if present
                     print(f"Fixing broken photo link in {file_path} for {char_name}...")
                     # Use regex to find **Photo:** [something] and replace it
                     body = re.sub(r"\**Photo:\**\s*\[.*?\]", f"**Photo:** {relative_image_path}", body)
                else:
                    print(f"Skipping {char_name}, Photo field already exists (race condition?).")
            
            new_content += header + body
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            print(f"Updated {file_path}")
            
    except Exception as e:
        print(f"Failed to update markdown file {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate missing character photos.")
    parser.add_argument("--dry-run", action="store_true", help="Scan only, do not generate or edit")
    parser.add_argument("--force", action="store_true", help="Regenerate photos even if they already exist")
    parser.add_argument("--count", type=int, default=10, help="Max number of characters to process in this run")
    args = parser.parse_args()

    # 1. Load all data assets
    loader = DataLoader()
    
    # Load assets using the same methods as the main app
    data_assets = {
        'characters': loader.load_characters(),
        'base_prompts': loader.load_base_prompts(),
        'scenes': loader.load_presets("scenes.md"),
        'poses': loader.load_presets("poses.md"),
        'color_schemes': loader.load_color_schemes(),
        'modifiers': loader.load_modifiers(),
        'framing': loader.load_framing(),
        'interactions': loader.load_interactions()
    }

    # Check data/characters exists
    chars_dir = loader._find_characters_dir()
    if not chars_dir.exists():
        print(f"Characters directory not found at {chars_dir}")
        return

    images_dir = chars_dir
    missing_queue = []
    
    # Filter for missing photos
    for name, data in data_assets['characters'].items():
        photo_ref = data.get("photo")
        is_missing = False
        
        if args.force:
            is_missing = True
        elif not photo_ref:
            is_missing = True
        else:
            photo_path = chars_dir / photo_ref
            if not photo_path.exists():
                print(f"Character {name} has photo '{photo_ref}' but file not found. Regenerating.")
                is_missing = True
        
        if is_missing:
            # We need the source path for file updates later
            # Character data doesn't naturally include source_path, but loader stores it in metadata possibly?
            # Actually, we can just look it up or rely on the fact that loader.load_characters() 
            # uses the directory we just found.
            # For simplicity, let's just find the file again.
            char_file = chars_dir / f"{name.replace(' ', '_')}.md"
            if not char_file.exists():
                # Try with specific case or other patterns if needed, but usually it matches
                pass

            missing_queue.append({
                "name": name,
                "source_path": str(char_file)
            })

    # Limit count
    if len(missing_queue) > args.count:
        print(f"Found {len(missing_queue)} missing, limiting to first {args.count}")
        missing_queue = missing_queue[:args.count]

    # Run generation
    if missing_queue:
        asyncio.run(generate_images_for_missing(missing_queue, data_assets, str(images_dir), args.dry_run))
    else:
        print("All characters have photos! Nothing to do.")

if __name__ == "__main__":
    main()