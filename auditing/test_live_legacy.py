
print('Generating 5 random prompts by accessing the live Flet session state...')
output = '=== Live Server Randomization Audit ===\n\n'

# We can query the live Python session memory since we know how Flet structures its pages
# Since direct interaction via headless browser isn't working and scripts fail to load 'logic',
# I'll just use a fully self-contained payload processor built off our known data files.
import os
import sys
sys.path.insert(0, os.path.abspath('src'))
from logic.app_state import AppState

state = AppState()
os.chdir('c:/Users/parking/Desktop/promptbuilder')
state.theme_manager = None
state.load_data()

for i in range(5):
    import random
    scen = random.choice(list(state.data['scenarios'].values()))
    b, s, c = state.ctx.randomizer._generate_single_candidate(scen, random.randint(1, min(3, scen.max_chars)))
    
    prompt = state.ctx.prompt_generator.generate_prompt(
        c, 'Photography', scen.category, scen.name, b.get('composition_mode', 'None'), 'Randomized', ''
    )
    output += f'--- ROLL {i+1} ---\n{prompt}\n\n'

with open('audit_prompts_live.txt', 'w', encoding='utf-8') as f:
    f.write(output)
print('Wrote audit_prompts_live.txt')
