import sys, os
import traceback

# FORCE path resolution
# 1. Project Root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
# 2. Src Directory
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

    from core.app_state import AppState
    
    # Initialize and load
    os.chdir(root_dir) # Must be in root for data finding
    state = AppState()
    state.theme_manager = None # Hack to avoid UI loading
    
    state.load_data()
    
    print("Data loaded successfully.")
    
    output = "=== RANDOMIZER AUDIT ===\n\n"
    scenarios = list(state.data['scenarios'].keys())
    
    for i in range(10):
        import random
        scenario_name = random.choice(scenarios)
        scenario_def = state.data['scenarios'][scenario_name]
        char_count = random.randint(1, min(3, scenario_def.max_chars))
        
        breakdown, score, chars = state.ctx.randomizer._generate_single_candidate(scenario_def, char_count)
        
        config_raw = {
            "base_prompt": chars[0].get("base_prompt") if chars else "Photography",
            "scene": breakdown.get("scene", ""),
            "selected_characters": chars,
            "notes": breakdown.get("notes", ""),
            "metadata": breakdown
        }
        prompt = state.ctx.builder.generate(config_raw)
        
        output += f"--- ROLL {i+1} ---\n"
        output += f"Scenario: {scenario_name} | Characters: {char_count}\n"
        output += f"Score: {score}\n"
        for c in chars:
            output += f"  - {c['name']} (Outfit: {c.get('outfit', 'Base')}, Age: {state.data['characters'][c['name']]['identity']['age']})\n"
        output += f"\nPROMPT:\n{prompt}\n\n"
        output += f"WARNINGS:\n"
        for w in breakdown.get('warnings', []):
            output += f"  - {w}\n"
        output += "==========================\n\n"

    with open("audit_prompts.txt", "w", encoding="utf-8") as f:
        f.write(output)
        
    print("Successfully wrote 10 prompts to audit_prompts.txt")
