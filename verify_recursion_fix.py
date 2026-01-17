
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from logic.data_loader import DataLoader
    from logic.randomizer import PromptRandomizer
    
    print("Loading data...")
    loader = DataLoader()
    
    # Manual data loading
    characters = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    scenes = loader.load_presets("scenes.md")
    poses = loader.load_presets("poses.md")
    interactions = loader.load_interactions()
    color_schemes = loader.load_color_schemes()
    modifiers = loader.load_modifiers()
    framing = loader.load_framing()
    
    data = {
        "characters": characters,
        "base_prompts": base_prompts,
        "scenes": scenes,
        "poses": poses,
        "interactions": interactions,
        "color_schemes": color_schemes,
        "modifiers": modifiers,
        "framing": framing
    }
    
    print("Initializing Randomizer...")
    randomizer = PromptRandomizer(**data)
    
    print("Running generation test (20 iterations)...")
    for i in range(20):
        try:
            result = randomizer.randomize(candidates=5)
            print(f"  [{i+1}/20] Generated: {result.get('scene_category')} - {result.get('scenario_name')}")
        except RecursionError:
            print("  [ERROR] RecursionError detected!")
            sys.exit(1)
        except Exception as e:
            print(f"  [ERROR] Exception: {e}")
            sys.exit(1)
            
    print("\nSUCCESS: No recursion errors encountered.")
    
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Setup Error: {e}")
    sys.exit(1)
