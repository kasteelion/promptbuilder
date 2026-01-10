"""Bulk Prompt Generator for Prompt Builder.

Parses a specific text format containing multiple prompt configurations
and generates full prompts for each one.

Usage:
    python bulk.py <input_file>
    python bulk.py --demo (runs with built-in demo data)
"""

import sys
import os
import re
import argparse

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.data_loader import DataLoader
from core.builder import PromptBuilder

def parse_bulk_text(text):
    """Parse text containing multiple PROMPT CONFIG blocks."""
    configs = []
    # Split by the header
    raw_blocks = text.split("PROMPT CONFIG")
    
    for block in raw_blocks:
        if not block.strip():
            continue
            
        config = {
            "base_prompt": "Default",
            "scene": "",
            "notes": "",
            "selected_characters": []
        }
        
        lines = block.strip().split('\n')
        
        # Temporary storage for current character being parsed
        current_char = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Global config keys
            if line.startswith("Base:"):
                # Extract style name (e.g. 'Victoria's Secret Magazine' from 'Victoria's Secret Magazine: "High-Fashion..."')
                # But PromptBuilder needs the exact key from base_prompts.md.
                # The input format often has 'Style: "Description"'. 
                # We'll assume the part before the first colon or quote is the key, 
                # or just try to match fuzzy later. For now, store the whole string.
                val = line.split("Base:", 1)[1].strip()
                # Heuristic: if there's a colon inside the value (Style: "Desc"), take left part
                if ":" in val:
                    val = val.split(":", 1)[0].strip()
                config["base_prompt"] = val
                
            elif line.startswith("Scene:"):
                config["scene"] = line.split("Scene:", 1)[1].strip()
                
            elif line.startswith("Notes:"):
                # Notes can apply to character or global?
                # In the example, notes appear at the end or inside character blocks?
                # "Notes: Two powerful figures..." implies global if at end.
                # "Notes: Confident, sophisticated..." inside [1] implies character?
                # The example format is ambiguous. Let's look closely at the examples.
                # Example 1: [1] Elena ... Notes: Confident... (Last line of block)
                # Example 2: [1] Keiko ... [2] Roxanna ... Notes: Two powerful figures... (Last line of block)
                # It seems 'Notes' at the end of the block are global notes for the prompt.
                # If 'Notes' appears before another [N], it might be char specific?
                # Actually, prompt builder usually takes global notes.
                # Let's assign to global config["notes"] for now.
                config["notes"] = line.split("Notes:", 1)[1].strip()
                
            # Character detection [1] Name
            elif re.match(r"^\[\d+\]", line):
                # Start new character
                if current_char:
                    config["selected_characters"].append(current_char)
                
                # Extract name
                # [1] Elena Rosales -> Elena Rosales
                name_part = re.sub(r"^\[\d+\]\s*", "", line).strip()
                current_char = {
                    "name": name_part,
                    "outfit": "Base",
                    "pose_category": "General",
                    "pose_preset": "Standing",
                    "color_scheme": None,
                    "use_signature_color": False,
                    "action_note": "" # Used if preset not found
                }
                
            # Character specific fields
            elif current_char and line.startswith("Outfit:"):
                current_char["outfit"] = line.split("Outfit:", 1)[1].strip()
                
            elif current_char and line.startswith("Colors:"):
                val = line.split("Colors:", 1)[1].strip()
                if val.lower() != "n/a":
                    current_char["color_scheme"] = val
                else:
                    current_char["color_scheme"] = "The Standard" # Default
                    
            elif current_char and line.startswith("Sig:"):
                val = line.split("Sig:", 1)[1].strip().lower()
                current_char["use_signature_color"] = (val == "yes")
                
            elif current_char and line.startswith("Pose:"):
                # Will try to resolve to category/preset later
                # Store raw value for now
                val = line.split("Pose:", 1)[1].strip()
                current_char["raw_pose"] = val

        # Append last char
        if current_char:
            config["selected_characters"].append(current_char)
            
        configs.append(config)
        
    return configs

def resolve_config(config, loader, poses_data):
    """Resolve names to internal keys."""
    
    # 1. Resolve Base Prompt
    # Input might be "Victoria's Secret Magazine"
    # Loaded keys might be "Victoria's Secret Magazine", "Artgerm", etc.
    # We try exact match, then case-insensitive.
    base_prompts = loader.load_base_prompts() # dict
    target = config["base_prompt"]
    
    match = None
    if target in base_prompts:
        match = target
    else:
        # Try case insensitive
        for k in base_prompts.keys():
            if k.lower() == target.lower():
                match = k
                break
        # Try starts with
        if not match:
            for k in base_prompts.keys():
                if target.lower() in k.lower():
                    match = k
                    break
    
    if match:
        config["base_prompt"] = match
    
    # 2. Resolve Characters
    chars = loader.load_characters()
    
    for char in config["selected_characters"]:
        # Name resolution
        target_name = char["name"]
        real_name = None
        
        # Exact or partial match
        if target_name in chars:
            real_name = target_name
        else:
            for k in chars.keys():
                if target_name.lower() in k.lower():
                    real_name = k
                    break
        
        if real_name:
            char["name"] = real_name
            
            # Resolve Outfit
            # The outfit string "Intimate" needs to match a key in char["outfits"]
            target_outfit = char["outfit"]
            char_outfits = chars[real_name].get("outfits", {})
            
            # Try exact match first
            if target_outfit in char_outfits:
                char["outfit"] = target_outfit
            else:
                # Fuzzy match
                # Often input is "Intimate", key might be "Intimate" or "Sleepwear - Intimate"
                found_outfit = None
                for k in char_outfits.keys():
                    if target_outfit.lower() == k.lower():
                        found_outfit = k
                        break
                if not found_outfit:
                     # substring search
                     for k in char_outfits.keys():
                        if target_outfit.lower() in k.lower():
                            found_outfit = k
                            break
                if found_outfit:
                    char["outfit"] = found_outfit
        
        # Resolve Pose
        # Input: "Soft Lingerie Lean"
        # We need to find {Category: {Name: Desc}}
        # If found, set category/preset. If not, set action_note.
        target_pose = char.get("raw_pose", "")
        found_pose = False
        
        if target_pose:
            for cat, presets in poses_data.items():
                for pname in presets.keys():
                    if target_pose.lower() == pname.lower():
                        char["pose_category"] = cat
                        char["pose_preset"] = pname
                        found_pose = True
                        break
                if found_pose:
                    break
            
            if not found_pose:
                # Treat as custom note
                char["action_note"] = target_pose

    return config

DEMO_TEXT = """PROMPT CONFIG
Base: Victoria's Secret Magazine
Scene: A luxurious penthouse suite at golden hour, floor-to-ceiling windows revealing a city skyline at dusk. Warm amber light spills across polished marble floors, creating a glow that catches on silk and skin. Sheer curtains billow gently in the breeze.
[1] Elena Rosales
Outfit: Intimate
Colors: N/A
Sig: Yes
Pose: Soft Lingerie Lean
Notes: Confident, sophisticated energy with glamorous lighting emphasizing curves and elegance.

PROMPT CONFIG
Base: Artgerm Style
Scene: A moonlit rooftop garden in a cyberpunk city. Neon lights from below cast colorful glows through rising mist. Bioluminescent flowers create soft purple and blue ambient light. The atmosphere is mysterious and seductive.
[1] Keiko Yamamoto
Outfit: Catsuit
Colors: N/A
Sig: Yes
Pose: Predatory Focus
[2] Roxanna Perez
Outfit: Catsuit
Colors: N/A
Sig: Yes
Pose: Coat Flip
Notes: Two powerful figures facing each other with electric tension, backlit by neon city lights creating dramatic silhouettes.

PROMPT CONFIG
Base: Cinematic 3D Animation
Scene: An intimate jazz club in dim lighting, smoke curling through beams of amber spotlight. Rich velvet textures and brass fixtures create a sensual, nostalgic atmosphere. A vintage microphone stands center stage.
[1] Audrey Thorne
Outfit: Nightclub Singer
Colors: N/A
Sig: Yes
Pose: Hand Through Hair
Notes: Solo spotlight performance, commanding attention with sultry confidence and old Hollywood glamour.

PROMPT CONFIG
Base: Photorealistic
Scene: A private yacht at sunset on calm waters. Golden light reflects off the ocean, creating a dreamy bokeh effect. White linen and teak wood details suggest luxury and intimacy.
[1] Marisol Rivera
Outfit: Swimwear
Colors: N/A
Sig: Yes
Pose: Wind Blown
Notes: Natural, sun-kissed beauty with ocean breeze creating movement, embodying effortless beach goddess energy.

PROMPT CONFIG
Base: Film Noir
Scene: A private detective's office at midnight. Venetian blinds cast dramatic shadows across the room. A desk lamp provides the only light source, creating high contrast between light and shadow. Rain streaks down the window behind.
[1] Avery Blake
Outfit: Private Detective
Colors: N/A
Sig: Yes
Pose: Sitting on Edge
Notes: Mysterious and alluring, perched on a desk with one leg crossed, cigarette smoke curling in the lamplight.

PROMPT CONFIG
Base: Vintage Pin-Up
Scene: A classic 1950s diner after hours, checkered floor gleaming under warm pendant lights. Chrome fixtures and red vinyl booths create a retro Americana atmosphere with playful sensuality.
[1] Lucía Reyes
Outfit: Pinup
Colors: N/A
Sig: Yes
Pose: Hip Pop
Notes: Classic pin-up energy with curves celebrated, playful wink and confident smile embodying vintage glamour.

PROMPT CONFIG
Base: Soft Semi-Realistic
Scene: A luxury bedroom at dawn, soft morning light filtering through sheer curtains. Rumpled silk sheets in cream and champagne tones. An aesthetic of intimate elegance and quiet sensuality.
[1] Yuki Tanaka
Outfit: Satin Sleepwear
Colors: N/A
Sig: Yes
Pose: Bed Pose
Notes: Natural morning beauty, relaxed and intimate with soft focus creating dreamy romantic atmosphere.

PROMPT CONFIG
Base: Western Comic Book
Scene: A rain-soaked city rooftop at night. Lightning illuminates the scene intermittently. Dramatic shadows and bold colors create a superhero aesthetic with romantic tension.
[1] Jordan Vance
Outfit: Superhero
Colors: N/A
Sig: Yes
Pose: Hero Landing
[2] Kassandra Lykaios
Outfit: Superhero
Colors: N/A
Sig: Yes
Pose: Brave Stand
Notes: Two heroines meeting on a rooftop, electric tension between them, rain creating dramatic effect on their forms, powerful and alluring simultaneously."""

def main():
    parser = argparse.ArgumentParser(description="Bulk Prompt Generator")
    parser.add_argument("input_file", nargs="?", help="Path to input text file")
    parser.add_argument("--demo", action="store_true", help="Run with demo text")
    parser.add_argument("--output", "-o", help="Path to output text file")
    
    args = parser.parse_args()
    
    text = ""
    if args.demo:
        print("Running with DEMO text...\n")
        text = DEMO_TEXT
    elif args.input_file:
        try:
            with open(args.input_file, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    else:
        print("No input provided. Use --demo or provide a filename.")
        return

    # Initialize System
    loader = DataLoader()
    try:
        chars = loader.load_characters()
        base_prompts = loader.load_base_prompts()
        poses = loader.load_presets("poses.md")
        # scenes = loader.load_presets("scenes.md") # Scene is raw text in this format
        schemes = loader.load_color_schemes()
        modifiers = loader.load_modifiers()
        
        builder = PromptBuilder(chars, base_prompts, poses, schemes, modifiers)
    except Exception as e:
        print(f"System initialization failed: {e}")
        return

    # Parse and Generate
    raw_configs = parse_bulk_text(text)
    
    print(f"Found {len(raw_configs)} configs.\n")
    
    all_prompts = []
    for idx, raw_conf in enumerate(raw_configs):
        resolved_conf = resolve_config(raw_conf, loader, poses)
        
        prompt = builder.generate(resolved_conf)
        all_prompts.append(f"--- PROMPT {idx+1} ---\n{prompt}")
        
        print(f"--- PROMPT {idx+1} ---")
        print(prompt)
        print("\n\n")

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("\n\n".join(all_prompts))
            print(f"Saved {len(all_prompts)} prompts to: {args.output}")
        except Exception as e:
            print(f"Error saving output file: {e}")

if __name__ == "__main__":
    main()
