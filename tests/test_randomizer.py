
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from logic.randomizer import PromptRandomizer


# Mock Data
MOCK_CHARACTERS = {
    "Alice": {
        "tags": ["Red", "Student", "Happy"],
        "outfits": {"Uniform": "School uniform", "Casual": "Jeans and tee"},
        "outfits_categorized": {
            "School": {"Uniform": "School uniform"},
            "Casual": {"Casual": "Jeans and tee"}
        }
    },
    "Bob": {
        "tags": ["Blue", "Office", "Serious"],
        "outfits": {"Suit": "Business suit", "Gym": "Sportswear"},
        "outfits_categorized": {
            "Formal": {"Suit": "Business suit"},
            "Sport": {"Gym": "Sportswear"}
        }
    },
    "Charlie": {"tags": ["Green"], "outfits": {}, "outfits_categorized": {}}
}

MOCK_SCENES = {
    "School": {"Classroom": "A classroom"},
    "Office": {"Boardroom": "A boardroom"},
    "Night": {"Club": "A night club"}
}

MOCK_OUTFITS_ALL = {
    "Uniform": "School uniform", 
    "Suit": "Business suit", 
    "Casual": "Jeans and tee", 
    "Clubwear": "Party dress"
}

MOCK_COLOR_SCHEMES = {
    "Red Theme": "Red and black",
    "Blue Theme": "Blue and white",
    "Dark Theme": "Black and grey",
    "Default": "None"
}

MOCK_FRAMING = {
    "Close Up": "Face focus",
    "Portrait": "Head and shoulders",
    "Wide Shot": "Full environment",
    "Full Body": "Head to toe"
}

@pytest.fixture
def randomizer():
    return PromptRandomizer(
        characters=MOCK_CHARACTERS,
        base_prompts={"Standard": "Standard style"},
        poses={"Standing": {"Pose1": "Standing straight"}},
        scenes=MOCK_SCENES,
        color_schemes=MOCK_COLOR_SCHEMES,
        framing=MOCK_FRAMING
    )

def test_smart_framing_single(randomizer):
    """Single character should bias towards close-ups."""
    # Run multiple times to check probability (statistically weak test but good for coverage)
    results = []
    for _ in range(20):
        framing = randomizer._select_smart_framing(1)
        results.append(framing)
    
    # Should see at least some close-up types
    assert any(f in ["Close Up", "Portrait"] for f in results)

def test_smart_framing_group(randomizer):
    """Group should bias towards wide shots."""
    results = []
    for _ in range(20):
        framing = randomizer._select_smart_framing(3)
        results.append(framing)
    
    # Should see at least some wide types
    assert any(f in ["Wide Shot", "Full Body"] for f in results)

def test_smart_color_scheme(randomizer):
    """Should pick color scheme matching tags."""
    # Alice has "Red", should likely pick "Red Theme"
    results = []
    for _ in range(20):
        scheme = randomizer._select_smart_color_scheme({"Red"}, "")
        results.append(scheme)
    
    assert "Red Theme" in results

def test_smart_outfit_scene_match(randomizer):
    """Scene 'Night' should prefer 'Party' or related outfits if available."""
    # We need to mock outfit categorization for this specific check to work well
    # Current implementation checks THEME_MAPPINGS. 
    # 'Night' maps to 'Party', 'Evening', 'Clubwear'.
    
    categorized = {
        "Party": {"Clubwear": "Party dress"}, 
        "Casual": {"Jeans": "Denim"}
    }
    
    results = []
    for _ in range(20):
        outfit = randomizer._select_smart_outfit(MOCK_OUTFITS_ALL, categorized, [], "Night")
        results.append(outfit)
        
    assert "Clubwear" in results

def test_randomize_structure(randomizer):
    """Ensure full randomization returns correct structure."""
    config = randomizer.randomize(num_characters=1, include_scene=True)
    
    assert "selected_characters" in config
    assert len(config["selected_characters"]) == 1
    assert "color_scheme" in config
    assert "base_prompt" in config
    assert "scene" in config