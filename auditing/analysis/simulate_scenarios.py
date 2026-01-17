import os
import sys
import random
from collections import Counter

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer

def run_simulation(iterations=2000):
    print(f"Running comprehensive simulation with {iterations} iterations...")
    loader = DataLoader()
    
    # Load all data
    chars = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    poses = loader.load_presets("poses.md")
    scenes = loader.load_presets("scenes.md")
    interactions = loader.load_interactions()
    
    randomizer = PromptRandomizer(chars, base_prompts, poses, scenes, interactions)
    
    stats = Counter()
    scenarios_stats = Counter()
    char_stats = Counter()
    style_stats = Counter()
    mode_stats = Counter()
    
    for i in range(iterations):
        if i % 200 == 0:
            print(f"  Processed {i}...")

        # Randomly toggle flags to test different flows
        inc_scene = random.choice([True, False])
        inc_notes = random.choice([True, False])
        
        # Scenario weights: Use scenario registry effectively
        config = randomizer.randomize(include_scene=inc_scene, include_notes=inc_notes)
        if not config:
            continue
        
        meta = config.get("metadata", {})
        scenario_name = meta.get("scenario", "Unknown")
        mode = meta.get("composition_mode", "Unknown")
        interaction_name = meta.get("interaction", "None")
        style = config.get("base_prompt", "Unknown")
        
        scenarios_stats[scenario_name] += 1
        mode_stats[mode] += 1
        style_stats[style] += 1
        
        selected_chars = config.get("selected_characters", [])
        for c in selected_chars:
            char_stats[c.get("name")] += 1

        # 1. Solo Intimate Pose
        # Mode=SOLO + Intimate tag in Pose OR Interaction
        is_solo_intimate = False
        if mode == PromptRandomizer.MODE_SOLO and selected_chars:
            c = selected_chars[0]
            p_name = c.get("pose_preset")
            pose_data = randomizer.poses.get(c.get("pose_category"), {}).get(p_name, {})
            p_tags = set(t.lower() for t in pose_data.get("tags", []))
            if randomizer._expand_tags(p_tags) & {"intimate", "sensual", "boudoir", "glamour"}:
                is_solo_intimate = True

        if is_solo_intimate:
            stats["Scenario: Solo Intimate"] += 1

        # 2. MMA Combat/Competition
        is_mma_combat = False
        i_tags = set(t.lower() for t in meta.get("interaction_tags", []))
        expanded_i_tags = randomizer._expand_tags(i_tags)
        is_combat_interaction = any(k in expanded_i_tags for k in ["combat", "fight", "mma", "wrestling", "boxing", "martial arts"])
        
        if is_combat_interaction:
            for char_data in selected_chars:
                char_def = randomizer.characters.get(char_data["name"], {})
                o_name = char_data.get("outfit")
                outfit_data = char_def.get("outfits", {}).get(o_name, {})
                
                o_tags = set()
                if isinstance(outfit_data, dict):
                    o_tags = set(t.lower() for t in outfit_data.get("tags", []))
                
                expanded_o_tags = randomizer._expand_tags(o_tags)
                if any(k in expanded_o_tags for k in ["mma", "boxing", "martial arts", "wrestling", "sport", "athletic", "combat"]):
                    is_mma_combat = True
                    break

        if is_mma_combat:
            stats["Scenario: MMA Combat"] += 1

        # 3. Precise Interaction Check
        if "precise" in expanded_i_tags:
            stats["Interaction: Precise"] += 1
            # Verify suppression
            if selected_chars and any(c.get("pose_preset") for c in selected_chars):
                 stats["DEBUG: Precise FAILED Suppression"] += 1

        # 4. Character Count Synchronization Check
        if interaction_name != "None":
            # Find the interaction object to get its min_chars
            # This is a bit hacky as we don't have the object directly here without re-searching,
            # but we can trust the metadata if we added it there.
            # Let's assume the randomizer added min_chars to metadata for us.
            target_min = meta.get("min_chars", 0)
            if target_min > 0 and len(selected_chars) != target_min:
                stats[f"DEBUG: Count Mismatch ({len(selected_chars)} vs {target_min})"] += 1

    print("\n=== Simulation Results ===")
    print(f"Total Iterations: {iterations}")

    print("\n--- Target Scenarios ---")
    for s, count in stats.items():
        print(f"{s}: {count} ({count/iterations*100:.1f}%)")

    print("\n--- Composition Modes ---")
    for m, count in mode_stats.most_common():
        print(f"Mode: {m}: {count} ({count/iterations*100:.1f}%)")

    print("\n--- Top Scenarios ---")
    for s, count in scenarios_stats.most_common(10):
        print(f"{s}: {count} ({count/iterations*100:.1f}%)")

    print("\n--- Top Characters ---")
    for name, count in char_stats.most_common(10):
        print(f"{name}: {count} ({count/(iterations*randomizer.scenario_registry.get_random().max_characters)*100:.1f}% approx frequency)")

    print("\n--- Top Styles ---")
    for st, count in style_stats.most_common(10):
        print(f"{st}: {count} ({count/iterations*100:.1f}%)")

if __name__ == "__main__":
    run_simulation(2000)
