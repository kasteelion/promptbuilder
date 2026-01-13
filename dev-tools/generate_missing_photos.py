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

# Regex patterns for file editing
_APPEARANCE_HEADER_RE = re.compile(r"(\**Appearance:\**)")
_PHOTO_FIELD_RE = re.compile(r"\**Photo:\**")

def _format_outfit(outfit_data):
    """Convert outfit data (dict or string) to a description string."""
    if isinstance(outfit_data, dict):
        parts = []
        for k, v in outfit_data.items():
            if v and isinstance(v, str):
                parts.append(f"{k}: {v}")
        return ", ".join(parts)
    return str(outfit_data)

async def generate_images_for_missing(characters_missing, output_dir, dry_run=False):
    """
    Generate images for the identified missing characters.
    
    Args:
        characters_missing: List of tuples (char_name, source_file_path, appearance_text, outfit_desc)
        output_dir: Directory to save images
        dry_run: If True, skip generation and file updates
    """
    if not characters_missing:
        print("No characters found missing photos.")
        return

    print(f"Found {len(characters_missing)} characters missing photos.")
    
    # 1. Prepare Prompts
    prompts = []
    for name, source_path, appearance, outfit_desc in characters_missing:
        # Construct a standardized portrait prompt
        short_app = appearance.split('\n\n')[0] if '\n\n' in appearance else appearance
        short_app = short_app[:800] # safety limit
        
        prompt_text = (
            f"Generate an image of: A high-quality photorealistic portrait of {name} against a simple white background. "
            f"Character description: {short_app}. "
            f"Outfit: {outfit_desc}. "
            "Pose: Neutral standing pose, neutral expression, facing forward. "
            "Lighting: Soft professional studio lighting."
        )
        prompts.append(prompt_text)
        
        if dry_run:
            print(f"[Dry Run] Would generate for: {name}")
            print(f"  Prompt: {prompt_text[:150]}... [truncated]")

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
        name, source_path, _, _ = characters_missing[i]
        
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
    parser.add_argument("--count", type=int, default=5, help="Max number of characters to process in this run")
    args = parser.parse_args()

    # 1. Scan for missing photos
    loader = DataLoader()
    
    # Check data/characters exists
    chars_dir = loader._find_characters_dir()
    if not chars_dir.exists():
        print(f"Characters directory not found at {chars_dir}")
        return

    # Ensure images directory exists (Using root characters dir for consistency)
    images_dir = chars_dir
    # images_dir.mkdir(exist_ok=True) # Directory already exists if we use chars_dir

    missing_queue = []
    
    # Iterate files
    for char_file in chars_dir.glob("*.md"):
        try:
            content = char_file.read_text(encoding="utf-8")
            # Parse chars in this file
            parsed_chars = CharacterParser.parse_characters(content)
            
            for name, data in parsed_chars.items():
                # Check if photo is missing
                photo_ref = data.get("photo")
                is_missing = False
                
                if not photo_ref:
                    is_missing = True
                else:
                    # Check if file exists
                    # photo_ref is usually relative to characters dir
                    photo_path = chars_dir / photo_ref
                    if not photo_path.exists():
                        print(f"Character {name} has photo '{photo_ref}' but file not found. Regenerating.")
                        is_missing = True
                
                if is_missing:
                    appearance = data.get("appearance", "")
                    
                    # Extract outfit
                    outfits = data.get("outfits", {})
                    outfit_desc = "Casual clothing" # Fallback
                    
                    # Priority: Base -> Default -> First
                    if "Base" in outfits:
                        outfit_desc = _format_outfit(outfits["Base"])
                    elif "Default" in outfits:
                        outfit_desc = _format_outfit(outfits["Default"])
                    elif outfits:
                        first_key = list(outfits.keys())[0]
                        outfit_desc = _format_outfit(outfits[first_key])
                        
                    if appearance:
                        missing_queue.append((name, str(char_file), appearance, outfit_desc))
        except Exception as e:
            print(f"Error reading {char_file}: {e}")

    # Limit count
    if len(missing_queue) > args.count:
        print(f"Found {len(missing_queue)} missing, limiting to first {args.count}")
        missing_queue = missing_queue[:args.count]

    # Run generation
    if missing_queue:
        asyncio.run(generate_images_for_missing(missing_queue, str(images_dir), args.dry_run))
    else:
        print("All characters have photos! Nothing to do.")

if __name__ == "__main__":
    main()