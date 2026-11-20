import sys
sys.path.insert(0, 'C:/Users/parking/Desktop/promptbuilder/src')
try:
    from logic.app_state import AppState
    import random
    
    state = AppState()
    # Hack AppState to load from the correct directory without UI
    state.theme_manager = None
    import os
    os.chdir('C:/Users/parking/Desktop/promptbuilder')
    state.load_data()
    
    output = ''
    for i in range(5):
        scen = random.choice(list(state.data['scenarios'].values()))
        breakdown, score, chars = state.ctx.randomizer._generate_single_candidate(scen, random.randint(1, min(3, scen.max_chars)))
        prompt = state.ctx.prompt_generator.generate_prompt(chars, 'Photography', scen.category, scen.name, breakdown.get('composition_mode', 'None'), 'Randomized', '')
        output += f'\n--- ROLL {i+1} ---\n{prompt}\n\n'
    
    with open('output_prompts.txt', 'w', encoding='utf-8') as f:
        f.write(output)
    print('SUCCESS')
except Exception:
    import traceback
    traceback.print_exc()
