import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.randomizer import PromptRandomizer
from core.data_loader import DataLoader

def test_randomization():
    print("Initializing DataLoader...")
    loader = DataLoader()
    print("Initializing Randomizer...")
    randomizer = PromptRandomizer(loader)
    
    print("Testing randomization...")
    try:
        config = randomizer.randomize(num_characters=2, include_scene=True, include_notes=True)
        print("Success! Randomization complete.")
        print(f"Scenario: {config.scenario_name}")
        print(f"Hub Tag: {config.metadata.get('hub_tag')}")
    except Exception as e:
        print(f"Failed! Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_randomization()
