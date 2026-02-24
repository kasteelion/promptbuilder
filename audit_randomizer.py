import sys
sys.path.insert(0, r"C:\Users\parking\Desktop\promptbuilder\src")

import traceback

try:
    from logic.app_state import AppState
    import os
    os.chdir(r"C:\Users\parking\Desktop\promptbuilder")
    
    # Initialize and load
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
        
        prompt = state.ctx.prompt_generator.generate_prompt(
            chars,
            art_style="Photography",
            scene_category=scenario_def.category,
            scene_preset=scenario_name,
            interaction_category=breakdown.get('composition_mode', 'None'),
            interaction_preset="Randomized",
            custom_scene=""
        )
        
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

    with open(r"C:\Users\parking\Desktop\promptbuilder\audit_prompts.txt", "w", encoding="utf-8") as f:
        f.write(output)
        
    print("Successfully wrote 10 prompts to audit_prompts.txt")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
