
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from logic.randomizer import PromptRandomizer
from core.models import CharacterDetails

# Mock Data
MOCK_CHARACTERS = {
    "Alice": CharacterDetails(
        name="Alice",
        appearance="Blonde",
        tags=["Red", "Student", "Happy"],
        outfits={"Uniform": "School uniform {primary_color}", "Casual": "Jeans and tee {primary_color}"},
        outfits_categorized={
            "School": {"Uniform": "School uniform {primary_color}"},
            "Casual": {"Casual": "Jeans and tee {primary_color}"}
        }
    ),
    "Bob": CharacterDetails(
        name="Bob",
        appearance="Dark hair",
        tags=["Blue", "Office", "Serious"],
        outfits={"Suit": "Business suit {primary_color}", "Gym": "Sportswear {primary_color}"},
        outfits_categorized={
            "Formal": {"Suit": "Business suit {primary_color}"},
            "Sport": {"Gym": "Sportswear {primary_color}"}
        }
    ),
    "Charlie": CharacterDetails(
        name="Charlie", 
        appearance="Green hair",
        tags=["Green"], 
        outfits={"Base": "Shirt {primary_color}"}, 
        outfits_categorized={"Personal": {"Base": "Shirt {primary_color}"}}
    )
}

MOCK_SCENES = {
    "School": {"Classroom": "A classroom", "Library": "Quiet library"},
    "Office": {"Boardroom": "A boardroom", "Desk": "A desk"},
    "Night": {"Club": "A night club", "Bar": "A bar"}
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
        base_prompts={
            "Standard": {"description": "Standard style"},
            "Anime": {"description": "Anime style"}
        },
        poses={"Standing": {"Pose1": "Standing straight"}},
        scenes=MOCK_SCENES,
        interactions={"Social": {"Chat": {"description": "Chatting"}}},
        color_schemes=MOCK_COLOR_SCHEMES,
        framing=MOCK_FRAMING,
        tag_rules={"hub_tags": ["TestHub", "Indoor"]}
    )

def test_smart_framing_single(randomizer):
    """Single character should bias towards close-ups."""
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

def test_randomize_structure(randomizer):
    """Ensure full randomization returns correct structure."""
    config = randomizer.randomize(num_characters=1, include_scene=True)
    
    assert "selected_characters" in config
    assert len(config["selected_characters"]) == 1
    assert "base_prompt" in config
    assert "scene" in config
    
    # Check that color_scheme made it to the character config
    char_config = config["selected_characters"][0]
    assert getattr(char_config, "color_scheme", None) is not None

def test_smart_color_scheme_contrast_harmonies():
    """Verify curated contrast harmonies (e.g. Maroon & Khaki, Navy & Amber) are favored in casual/dramatic contexts."""
    schemes = {
        "Maroon & Khaki": {"primary": "maroon"},
        "Navy & Amber": {"primary": "navy"},
        "Olive & Rust": {"primary": "olive"},
        "The Standard": {"primary": "white"},
    }
    r = PromptRandomizer(
        characters=MOCK_CHARACTERS,
        base_prompts={"Standard": {"description": "Standard"}},
        poses={"Standing": {"Pose1": "Standing"}},
        scenes=MOCK_SCENES,
        interactions={},
        color_schemes=schemes,
        framing=MOCK_FRAMING,
        tag_rules={},
    )

    results = [r._select_smart_color_scheme(tags=set(), scene_category="Casual", context_tags={"cafe", "urban"}) for _ in range(25)]
    # Curated harmonies should appear frequently
    assert any(s in ["Maroon & Khaki", "Navy & Amber", "Olive & Rust"] for s in results)

def test_smart_color_scheme_multi_character_differentiation():
    """Verify that multiple characters are assigned non-duplicate color schemes when alternatives exist."""
    schemes = {
        "Maroon & Khaki": {"primary": "maroon"},
        "Navy & Amber": {"primary": "navy"},
        "Olive & Rust": {"primary": "olive"},
    }
    r = PromptRandomizer(
        characters=MOCK_CHARACTERS,
        base_prompts={"Standard": {"description": "Standard"}},
        poses={"Standing": {"Pose1": "Standing"}},
        scenes=MOCK_SCENES,
        interactions={},
        color_schemes=schemes,
        framing=MOCK_FRAMING,
        tag_rules={},
    )

    assigned = []
    first = r._select_smart_color_scheme(tags=set(), scene_category="Casual")
    assigned.append(first)
    second = r._select_smart_color_scheme(tags=set(), scene_category="Casual", existing_schemes=assigned)

    assert second in schemes
    # Should differentiate if possible
    assert second != first or len(schemes) == 1

def test_color_harmony_scoring_bonus(randomizer):
    """Verify scoring engine gives contrast harmony bonuses and penalizes accidental non-sport duplicates."""
    from logic.scoring_heuristics import ScoringEngine
    from core.models import SelectedCharacterConfig

    scorer = ScoringEngine(randomizer)

    # 1. Config with curated harmony (Maroon & Khaki) and signature color
    config_harmony = {
        "base_prompt": "Standard",
        "selected_characters": [
            SelectedCharacterConfig(
                name="Alice",
                outfit="Uniform",
                color_scheme="Maroon & Khaki",
                use_signature_color=True,
            )
        ],
        "metadata": {"scene_tags": ["cafe", "casual"]},
    }
    randomizer.characters["Alice"].signature_color = "Red"
    score_harmony = scorer.score_candidate(config_harmony)
    breakdown_harmony = config_harmony["metadata"]["score_breakdown"]
    assert breakdown_harmony["color_harmony_bonus"] > 0

    # 2. Config with duplicate scheme in non-sport scene
    config_duplicate = {
        "base_prompt": "Standard",
        "selected_characters": [
            SelectedCharacterConfig(name="Alice", outfit="Casual", color_scheme="The Standard"),
            SelectedCharacterConfig(name="Bob", outfit="Suit", color_scheme="The Standard"),
        ],
        "metadata": {"scene_tags": ["library", "casual"]},
    }
    scorer.score_candidate(config_duplicate)
    breakdown_dup = config_duplicate["metadata"]["score_breakdown"]
    assert breakdown_dup["color_clash_penalty"] < 0
