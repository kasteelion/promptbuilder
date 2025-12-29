"""Interactive CLI Wizard for Prompt Builder.

This script provides a guided, step-by-step terminal interface for generating
prompts without launching the full GUI.
"""

import sys
import os
import time

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.data_loader import DataLoader
from core.builder import PromptBuilder

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print(f"\n=== {title} ===")

def get_choice(options: list, title: str = "Select an option", allow_cancel: bool = False):
    """Generic menu selection. Returns the selected item (value), or None if cancelled."""
    if not options:
        print("No options available.")
        return None

    while True:
        print_header(title)
        for idx, item in enumerate(options):
            # If item is tuple (key, display_name), print display_name
            display = item[1] if isinstance(item, tuple) else item
            print(f"{idx + 1}. {display}")
        
        if allow_cancel:
            print("0. Cancel/Go Back")

        try:
            choice = input(f"\nEnter choice (1-{len(options)}): ").strip()
            if allow_cancel and choice == "0":
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx] # Return the whole item (tuple or string)
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

def input_yes_no(question: str) -> bool:
    while True:
        resp = input(f"{question} (y/n): ").lower().strip()
        if resp in ['y', 'yes']:
            return True
        if resp in ['n', 'no']:
            return False

def wizard_main():
    clear_screen()
    print("Initializing Prompt Builder Wizard...")
    
    try:
        loader = DataLoader()
        # Load all data
        print("Loading characters...")
        chars = loader.load_characters()
        print("Loading base prompts...")
        base_prompts = loader.load_base_prompts()
        print("Loading poses...")
        poses = loader.load_presets("poses.md")
        print("Loading scenes...")
        scenes = loader.load_presets("scenes.md")
        print("Loading color schemes...")
        schemes = loader.load_color_schemes()
        print("Loading modifiers...")
        modifiers = loader.load_modifiers()
        
        builder = PromptBuilder(chars, base_prompts, poses, schemes, modifiers)
        print("Ready!")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    config = {
        "base_prompt": "Default",
        "selected_characters": [],
        "scene": "",
        "notes": ""
    }

    # === Main Loop ===
    while True:
        clear_screen()
        print("=== Prompt Builder Wizard ===")
        print(f"Current Characters: {len(config['selected_characters'])}")
        for i, c in enumerate(config['selected_characters']):
            print(f"  {i+1}. {c['name']} - {c.get('outfit', 'Base')} ({c.get('pose_preset', 'Default')})")
        
        print("\nActions:")
        print("1. Add Character")
        print("2. Set Scene")
        print("3. Set Base Prompt Style")
        print("4. Generate Prompt")
        print("5. Clear All")
        print("6. Exit")

        choice = input("\nSelect action: ").strip()

        if choice == "1":
            # Add Character
            char_names = sorted(list(chars.keys()))
            selection = get_choice(char_names, "Select Character", allow_cancel=True)
            if not selection: continue
            
            char_name = selection
            char_data = chars[char_name]
            
            new_char = {
                "name": char_name,
                "outfit": "Base",
                "outfit_traits": [],
                "pose_category": "General",
                "pose_preset": "Standing",
                "color_scheme": "The Standard",
                "use_signature_color": False
            }

            # Outfit Selection
            outfits_cat = char_data.get("outfits_categorized", {})
            outfit = "Base"
            if outfits_cat:
                cat_list = sorted(list(outfits_cat.keys()))
                cat = get_choice(cat_list, f"Select Outfit Category for {char_name}", allow_cancel=True)
                if cat:
                    outfit_list = sorted(outfits_cat[cat])
                    outfit = get_choice(outfit_list, f"Select {cat} Outfit", allow_cancel=True)
                    if outfit:
                        new_char["outfit"] = outfit
            
            # Modifier/Trait Selection
            outfit_desc = str(char_data.get("outfits", {}).get(outfit, ""))
            if "{modifier}" in outfit_desc and modifiers:
                print_header("Select Specialized Traits")
                print("Selected outfit supports modifiers. Select traits (Enter 'done' when finished):")
                mod_keys = sorted(list(modifiers.keys()))
                selected_traits = []
                while True:
                    choice = get_choice(mod_keys + ["Done selecting"], "Available Traits", allow_cancel=False)
                    if choice == "Done selecting":
                        break
                    if choice not in selected_traits:
                        selected_traits.append(choice)
                        print(f"Added: {choice}")
                    else:
                        selected_traits.remove(choice)
                        print(f"Removed: {choice}")
                    print(f"Current selection: {', '.join(selected_traits) if selected_traits else 'None'}")
                new_char["outfit_traits"] = selected_traits

            # Color Scheme
            scheme_names = sorted(list(schemes.keys()))
            scheme = get_choice(scheme_names, "Select Color Scheme", allow_cancel=True)
            if scheme:
                new_char["color_scheme"] = scheme
            
            if input_yes_no("Use signature color?"):
                new_char["use_signature_color"] = True

            # Pose
            pose_cats = sorted(list(poses.keys()))
            p_cat = get_choice(pose_cats, "Select Pose Category", allow_cancel=True)
            if p_cat:
                new_char["pose_category"] = p_cat
                pose_list = sorted(list(poses[p_cat].keys()))
                pose = get_choice(pose_list, f"Select {p_cat} Pose", allow_cancel=True)
                if pose:
                    new_char["pose_preset"] = pose

            config["selected_characters"].append(new_char)

        elif choice == "2":
            # Set Scene
            scene_cats = sorted(list(scenes.keys()))
            s_cat = get_choice(scene_cats, "Select Scene Category", allow_cancel=True)
            if s_cat:
                scene_list = sorted(list(scenes[s_cat].keys()))
                scene_key = get_choice(scene_list, f"Select {s_cat} Scene", allow_cancel=True)
                if scene_key:
                    # Look up the actual scene text
                    config["scene"] = scenes[s_cat][scene_key]
                    print(f"Scene set to: {scene_key}")
                    time.sleep(1)

        elif choice == "3":
            # Base Prompt
            styles = sorted(list(base_prompts.keys()))
            style = get_choice(styles, "Select Art Style", allow_cancel=True)
            if style:
                config["base_prompt"] = style

        elif choice == "4":
            # Generate
            clear_screen()
            result = builder.generate(config)
            print("=== GENERATED PROMPT ===\n")
            print(result)
            print("\n========================\n")
            
            print("Options:")
            print("1. Copy to Clipboard (requires Tkinter)")
            print("2. Return to Menu")
            
            g_choice = input("Select: ").strip()
            if g_choice == "1":
                try:
                    import tkinter as tk
                    r = tk.Tk()
                    r.withdraw()
                    r.clipboard_clear()
                    r.clipboard_append(result)
                    r.update()
                    r.destroy()
                    print("Copied to clipboard!")
                    time.sleep(1)
                except Exception as e:
                    print(f"Clipboard failed: {e}")
                    input("Press Enter to continue...")
            elif g_choice == "2":
                pass
            else:
                input("Press Enter to continue...")

        elif choice == "5":
            config["selected_characters"] = []
            config["scene"] = ""
            print("Cleared.")
            time.sleep(0.5)

        elif choice == "6":
            print("Goodbye!")
            break

if __name__ == "__main__":
    try:
        wizard_main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
