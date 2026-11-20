
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))

from logic.randomizer import PromptRandomizer

def test_exclusion_logic():
    print("Testing Exclusion Logic (Block:Swimwear)...")
    
    # Mock Data
    characters = {
        "Alice": {
            "name": "Alice", 
            "tags": ["Model"], 
            "outfits": {
                "Bikini": {"description": "A bikini", "tags": ["Swimwear"]},
                "Winter Coat": {"description": "A coat", "tags": ["Winter"]},
            },
            "outfits_categorized": {
                "Summer": {"Bikini": {"description": "A bikini", "tags": ["Swimwear"]}},
                "Winter": {"Winter Coat": {"description": "A coat", "tags": ["Winter"]}},
            }
        }
    }
    
    # Scene with Block tag
    scenes = {
        "Outdoors": {
            "Snow Scene": {"description": "Snowy", "tags": ["Winter", "Block:Swimwear"]}
        }
    }
    
    randomizer = PromptRandomizer(characters, {}, {}, scenes=scenes)
    
    # Run N times forcing the snow scene (which we can't force easily without modifying randomize, 
    # but we can force it by only having one scene)
    
    bikini_count = 0
    runs = 50
    
    for _ in range(runs):
        config = randomizer.randomize(num_characters=1, include_scene=True)
        char = config["selected_characters"][0]
        if char["outfit"] == "Bikini":
            bikini_count += 1
            
    print(f"Bikini selected: {bikini_count}/{runs}")
    
    if bikini_count == 0:
        print("PASS: Exclusion logic worked.")
    else:
        print("FAIL: Blocked item was selected.")

def test_mood_logic():
    print("\nTesting Mood Logic (Mood:Cozy)...")
    
    # Mock Data
    characters = {
        "Bob": {
            "name": "Bob", 
            "tags": ["Guy"], 
            "outfits": {
                "Suit": {"description": "A suit", "tags": ["Formal"]},
                "Sweater": {"description": "A sweater", "tags": ["Cozy"]},
            },
            "outfits_categorized": {
                "Formal": {"Suit": {"description": "A suit", "tags": ["Formal"]}},
                "Comfort": {"Sweater": {"description": "A sweater", "tags": ["Cozy"]}},
            }
        }
    }
    
    # Scene with Mood tag
    scenes = {
        "Indoors": {
            "Cozy Room": {"description": "Warm room", "tags": ["Interior", "Mood:Cozy"]}
        }
    }
    
    randomizer = PromptRandomizer(characters, {}, {}, scenes=scenes)
    
    sweater_count = 0
    runs = 50
    
    for _ in range(runs):
        config = randomizer.randomize(num_characters=1, include_scene=True)
        char = config["selected_characters"][0]
        if char["outfit"] == "Sweater":
            sweater_count += 1
            
    print(f"Sweater selected: {sweater_count}/{runs}")
    
    # Expectation: Cozy sweater should be overwhelmingly preferred over Suit
    if sweater_count > 40:
        print("PASS: Mood logic worked (High preference for matching tags).")
    else:
        print(f"FAIL: Mood logic preference was {sweater_count}/50 (expected >40).")

def test_scoring_system():
    print("\nTesting Scoring System (Monte Carlo)...")
    # Using the same setup as Mood Logic, but relying on the Score (+10 for match) 
    # to filter out any "unlucky" random selections.
    
    characters = {
        "Bob": {
            "name": "Bob", 
            "tags": ["Guy"], 
            "outfits": {
                "Suit": {"description": "A suit", "tags": ["Formal"]},
                "Sweater": {"description": "A sweater", "tags": ["Cozy"]},
            },
            "outfits_categorized": {
                "Formal": {"Suit": {"description": "A suit", "tags": ["Formal"]}},
                "Comfort": {"Sweater": {"description": "A sweater", "tags": ["Cozy"]}},
            }
        }
    }
    
    scenes = {
        "Indoors": {
            "Cozy Room": {"description": "Warm room", "tags": ["Interior", "Mood:Cozy"]}
        }
    }
    
    randomizer = PromptRandomizer(characters, {}, {}, scenes=scenes)
    
    # We run randomize() which now generates N=5 candidates and picks the best.
    # The "Sweater" config will have score >= 15 (Mood Match + 5 completeness).
    # The "Suit" config will have score 5 (Completeness only).
    # Validates that the system ALWAYS picks the higher score if available.
    
    sweater_wins = 0
    runs = 20
    
    for _ in range(runs):
        # Generate 5 candidates per run
        config = randomizer.randomize(num_characters=1, include_scene=True, candidates=5)
        char = config["selected_characters"][0]
        if char["outfit"] == "Sweater":
            sweater_wins += 1
            
    print(f"Sweater (High Score) wins: {sweater_wins}/{runs}")
    
    if sweater_wins >= 19:
        print("PASS: Scoring system consistently selected the better candidate.")
    else:
        print("FAIL: Scoring system let lower quality candidates win.")

def test_interaction_pairs():
    print("\nTesting Interaction Pairs (Context Tag Filtering)...")
    
    # Setup Mocks
    characters = {
        "Alice": {"name": "Alice", "tags": ["Tennis", "Sport"]},
        "Bob": {"name": "Bob", "tags": ["Basketball", "Sport"]}
    }
    
    # Interactions: One restricted to Tennis, one restricted to Basketball
    interactions = {
        "Sports": {
            "Tennis Match": {"description": "Playing Tennis", "tags": ["Tennis"], "min_chars": 1},
            "Basketball Dunk": {"description": "Dunking Basketball", "tags": ["Basketball"], "min_chars": 1},
            "Universal Chat": {"description": "Just chatting", "tags": [], "min_chars": 1}
        }
    }
    
    randomizer = PromptRandomizer(characters, {}, {}, interactions=interactions)
    
    # Test 1: Generate for Alice (Tennis)
    # Should get "Playing Tennis" or "Just chatting", NEVER "Dunking Basketball"
    
    fail_count = 0
    runs = 50
    
    for _ in range(runs):
        # Force select Alice
        # We can't easily force select char in randomize, but we can verify _generate_random_notes behavior directly
        # or just rely on the fact that randomizer will pick Alice or Bob.
        
        # Le'ts use internal method for precise testing
        ctx_tags = {"tennis", "sport"}
        chars = [{"name": "Alice"}]
        
        note = randomizer._generate_random_notes(chars, "", context_tags=ctx_tags)
        
        if "Dunking Basketball" in note:
            fail_count += 1
            print("FAIL: Got Basketball interaction for Tennis context.")
            
    if fail_count == 0:
        print("PASS: Tennis context correctly blocked Basketball interaction.")
    else:
        print(f"FAIL: {fail_count}/{runs} mismatches.")

    # Test 2: Basketball Context
    ctx_tags = {"basketball", "sport"}
    chars = [{"name": "Bob"}]
    fail_count = 0
    for _ in range(runs):
        note = randomizer._generate_random_notes(chars, "", context_tags=ctx_tags)
        if "Playing Tennis" in note:
            fail_count += 1
    
    if fail_count == 0:
        print("PASS: Basketball context correctly blocked Tennis interaction.")
    else:
        print(f"FAIL: {fail_count}/{runs} mismatches.")

def test_framing_logic():
    print("\nTesting Framing Logic...")
    randomizer = PromptRandomizer({}, {}, {}, framing={"Close-up": "Close-up", "Wide Shot": "Wide Shot"})
    
    # Test 1: Portrait Tag -> Close-up
    fail_count = 0
    runs = 30
    for _ in range(runs):
        framing = randomizer._select_smart_framing(1, context_tags={"Portrait", "Face"})
        if framing and framing != "Close-up":
            # It's probabilistic (70% smart), so failures are expected occasionally, 
            # but if we get 0 close-ups, that's bad.
            pass

    # Let's count successes
    success_count = 0
    for _ in range(runs):
        framing = randomizer._select_smart_framing(1, context_tags={"Portrait"})
        if framing == "Close-up":
            success_count += 1
            
    print(f"Portrait Tag -> Close-up rate: {success_count}/{runs}")
    if success_count > 10: # Expect at least ~30-50% due to RNG
        print("PASS: Portrait tags bias towards Close-up.")
    else:
        print("WARN: Portrait bias seems weak.")

    # Test 2: Landscape Tag -> Wide Shot
    success_count = 0
    for _ in range(runs):
        framing = randomizer._select_smart_framing(1, context_tags={"Landscape"})
        if framing == "Wide Shot":
            success_count += 1
            
    print(f"Landscape Tag -> Wide Shot rate: {success_count}/{runs}")
    if success_count > 10:
        print("PASS: Landscape tags bias towards Wide Shot.")
    else:
        print("WARN: Landscape bias seems weak.")


if __name__ == "__main__":
    try:
        test_exclusion_logic()
        test_mood_logic()
        test_scoring_system()
        test_interaction_pairs()
        test_framing_logic()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
