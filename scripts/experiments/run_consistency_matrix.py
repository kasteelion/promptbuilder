import sys
import copy
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "src"))

import asyncio
from logic.data_loader import DataLoader
from core.builder import PromptBuilder
from utils.ai_client import AIStudioClient

# --- EXPERIMENT CONFIGURATION ---

VARIANTS = {
    "Amina Benali": {
        "V1_Verbose": None, # Will load from file
        "V2_Standard": "Moroccan-Canadian streamer. Neon pink/orange ombre hair in topknot. Wireless headset. Stylish clear-framed glasses. Soft natural frame. Wearing ribbed lavender tank top and high-waist black shorts.",
        "V3_Core": "Female streamer, pink ombre hair, glasses, lavender tank top."
    },
    "Diego Morales": {
        "V1_Verbose": None,
        "V2_Standard": "Latino digital designer. Sun-bleached tousled brown hair. Warm tan skin with sun lines. Wearing vintage rust orange t-shirt and jeans. Leather cord necklace. Relaxed athletic build.",
        "V3_Core": "Male, Latino, sun-bleached hair, orange t-shirt, jeans."
    },
    "Isla MacLeod": {
        "V1_Verbose": None,
        "V2_Standard": "Indie-folk photographer. Auburn wavy hair. Fair skin with freckles. Oversized cream cardigan over gray tank. Green corduroy pants. Vintage film camera accessory.",
        "V3_Core": "Female, auburn hair, freckles, cream cardigan, green pants."
    },
    "Kaito Sato": {
        "V1_Verbose": None,
        "V2_Standard": "Japanese urban explorer. Bleached platinum blonde textured hair (undercut). Sharp angular face. Wearing black graphic techwear tee and strappy cargo joggers. Neon green accents. Band-aid on cheek.",
        "V3_Core": "Male, Japanese, white hair, black techwear, neon green accents."
    }
}

CONTEXTS = {
    "Control": {
        "scene": "Studio Simple Background",
        "action": "Standing",
        "notes": "Simple portrait."
    },
    "Clash": {
        "scene": "**SCENE:** A dimly lit medieval tavern with wooden tables and candlelight.",
        "action": "Sitting",
        "notes": "Theme Clash Test: Character should look out of place."
    },
    "Action": {
        "scene": "**SCENE:** Skydiving high above the clouds, freefalling with intense wind.",
        "action": "Skydiving",
        "notes": "Action Test: High dynamism."
    }
}

def run_matrix():
    print("Initializing Consistency Matrix Experiment...")
    loader = DataLoader()
    
    # Load base data
    real_chars = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    poses = loader.load_presets("poses.md")
    
    # Ensure output dir exists
    output_dir = project_root / "output" / "experiments" / "consistency_matrix"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output Directory: {output_dir}")
    
    total_generated = 0
    
    for char_name, variants in VARIANTS.items():
        if char_name not in real_chars:
            print(f"WARNING: Character '{char_name}' not found in loaded data. Skipping.")
            continue
            
        print(f"\nProcessing {char_name}...")
        
        for variant_name, variant_text in variants.items():
            # Create a clean mock of the character data
            # Deepcopy to avoid polluting the cache or other iterations
            mock_char = copy.deepcopy(real_chars[char_name])
            
            if variant_name == "V1_Verbose":
                # Use existing data as-is
                pass
            else:
                # OVERRIDE for V2/V3
                # 1. Update appearance
                mock_char["appearance"] = variant_text
                # 2. Clear metadata that PromptBuilder appends (Age, Vibe, Bearing)
                #    to ensure the prompt is EXACTLY what we defined for the test.
                mock_char["age_presentation"] = None
                mock_char["vibe"] = None
                mock_char["bearing"] = None
                mock_char["traits"] = {} # Clear traits definitions
            
            # Temporary Char Dict for the Builder
            # We mock the entire chars dict so builder finds it by name
            mock_chars_dict = {char_name: mock_char}
            
            builder = PromptBuilder(
                characters=mock_chars_dict, 
                base_prompts=base_prompts, 
                poses=poses
            )
            
            for context_name, context_data in CONTEXTS.items():
                # Build Config
                config = {
                    "base_prompt": "Photorealistic", # Force a standard style
                    "scene": context_data["scene"],
                    "notes": context_data["notes"],
                    "selected_characters": [
                        {
                            "name": char_name,
                            "outfit": "Base", # Use Base outfit (or we could clear this too for V3?) 
                                              # For consistency, let's keep the Base outfit defined in the file
                                              # unless V3 explicitly includes clothing in text.
                                              # The V3 text I wrote INCLUDES clothing ("lavender tank top").
                                              # So for V3, we should probably disable the Outfit renderer 
                                              # or set outfit to None/Empty.
                            "pose_raw": context_data["action"] # Direct string override
                        }
                    ]
                }
                
                # SPECIAL HANDLING FOR V3 (Core)
                # If V3 description includes clothes, we shouldn't append the Output block too.
                # My V3 texts DO include clothes.
                # So for V3, let's suppress the outfit in the config.
                if variant_name == "V3_Core":
                     config["selected_characters"][0]["outfit"] = None
                
                # Check if V2 has clothes... yes "Wearing...". 
                # So V2 also duplicates outfit if we aren't careful.
                # BUT V2's text description is "Wearing...". 
                # usually PromptBuilder adds a whole "**Outfit**" section.
                # If we want to test "Just the description", we should disable the Outfit block for V2/V3.
                if variant_name in ["V2_Standard", "V3_Core"]:
                    config["selected_characters"][0]["outfit"] = None
                
                # Generate
                prompt_text = builder.generate(config)
                
                # Save
                safe_char = char_name.replace(" ", "_")
                filename = f"{safe_char}_{variant_name}_{context_name}.txt"
                file_path = output_dir / filename
                
                file_path.write_text(f"Generate an image of: {prompt_text}", encoding="utf-8")
                total_generated += 1
                
    print(f"\nExperiment Complete. Generated {total_generated} prompt files.")
    
    # --- IMAGE GENERATION PHASE ---
    print("\nStarting Image Generation Sequence...")
    
    # Collect all generated files to process
    prompt_files = sorted(list(output_dir.glob("*.txt")))
    prompts_to_run = []
    
    for p_file in prompt_files:
        content = p_file.read_text(encoding="utf-8")
        # Extract the raw prompt (remove "Generate an image of: " prefix if present, 
        # but AIStudioClient might expect it or not. automate_generation ADDS it. 
        # The text file HAS it. So let's use it as is?
        # automate_generation.py: prompts = [f"Generate an image of: {prompt}" ...]
        # My text files ALREADY contain "Generate an image of: ..."
        # So we can just read the content.
        prompts_to_run.append(content.strip())
        
    if not prompts_to_run:
        print("No prompts found to generate.")
        return

    # Setup paths for AI Client
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    user_data_dir = project_root / ".config" / "chrome_profile"
    
    client = AIStudioClient(
        output_dir=str(images_dir),
        user_data_dir=str(user_data_dir),
        headless=False # User might want to watch or debug
    )
    
    async def run_gen():
        print(f"Sending {len(prompts_to_run)} prompts to AI Studio...")
        
        def progress(current, total, message):
            print(f"[{current}/{total}] {message}")
            
        await client.generate_images(prompts_to_run, progress_callback=progress)
        
    try:
        asyncio.run(run_gen())
        print(f"\nGeneration Complete. Images saved to {images_dir}")
    except Exception as e:
        print(f"\nERROR during generation: {e}")

if __name__ == "__main__":
    run_matrix()
