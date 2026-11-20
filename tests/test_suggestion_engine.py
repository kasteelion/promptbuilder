import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from core.models import SelectedCharacterConfig, CharacterDetails, CharacterMetadata
from logic.suggestion_engine import SuggestionEngine


class MockAppContext:
    def __init__(self):
        self.characters = {
            "Priya Sharma": CharacterDetails(
                name="Priya Sharma",
                appearance="Warm brown eyes, sleek dark hair",
                tags=["Athletic", "Chic", "Urban"],
                vibe="Focused, Intense",
                outfits={
                    "Base": "Basic tank top",
                    "Cyber-Tactical Combat": "Spandex tactical jumpsuit",
                    "Casual Street": "Fitted denim and leather jacket",
                },
            ),
            "Nora Alvarez": CharacterDetails(
                name="Nora Alvarez",
                appearance="Hazel eyes, glasses",
                tags=["Intellectual", "Deliberate"],
                vibe="Thoughtful, Calm",
                outfits={
                    "Base": "Casual knit",
                    "Dark Academia": "Tweed blazer and pleated skirt",
                },
            ),
        }
        self.characters_metadata = {
            "Priya Sharma": CharacterMetadata(name="Priya Sharma", tags=["Athletic", "Chic", "Urban"], vibe="Focused, Intense"),
            "Nora Alvarez": CharacterMetadata(name="Nora Alvarez", tags=["Intellectual", "Deliberate"], vibe="Thoughtful, Calm"),
        }
        self.scenes = {
            "Thematic & Cinematic": {
                "Rain-Slicked Alley": {
                    "description": "Dark rain-slicked alley with neon reflections",
                    "tags": ["Urban", "Noir", "Night"],
                },
                "Sunny Park": {
                    "description": "Lush green grass under warm sunlight",
                    "tags": ["Nature", "Day"],
                },
            }
        }
        self.interactions = {
            "Casual & Domestic": {
                "Deep Conversation": {
                    "description": "{char1} and {char2} talking intently",
                    "min_chars": 2,
                    "tags": ["Intellectual", "Social"],
                }
            }
        }
        self.color_schemes = {
            "Midnight & Crimson": {"primary": "#0A0F24", "secondary": "#990000"},
            "Maroon & Khaki": {"primary": "#800020", "secondary": "#C3B091"},
        }


class MockDataLoader:
    def __init__(self, ctx):
        self.ctx = ctx

    def get_character_details(self, name):
        return self.ctx.characters.get(name)


class MockAppState:
    def __init__(self):
        self.ctx = MockAppContext()
        self.data_loader = MockDataLoader(self.ctx)
        self.state = {
            "selected_characters": [],
            "scene": "",
            "notes": "",
            "base_prompt": "Detailed",
        }


class TestSuggestionEngine(unittest.TestCase):
    def setUp(self):
        self.app_state = MockAppState()

    def test_empty_roster_returns_empty(self):
        suggestions = SuggestionEngine.get_suggestions(self.app_state)
        self.assertEqual(len(suggestions["scenes"]), 0)
        self.assertEqual(len(suggestions["interactions"]), 0)

    def test_single_character_scene_and_outfit_suggestions(self):
        self.app_state.state["selected_characters"] = [
            SelectedCharacterConfig(name="Priya Sharma", outfit="Base")
        ]
        suggestions = SuggestionEngine.get_suggestions(self.app_state)

        # Should suggest scenes matching Urban tag
        self.assertGreater(len(suggestions["scenes"]), 0)
        self.assertEqual(suggestions["scenes"][0].label, "Rain-Slicked Alley")

        # Should suggest wardrobe since outfit is Base
        self.assertGreater(len(suggestions["outfits"]), 0)

        # Single character should NOT suggest multi-character interaction
        self.assertEqual(len(suggestions["interactions"]), 0)

    def test_multi_character_interaction_suggestions_with_names_resolved(self):
        self.app_state.state["selected_characters"] = [
            SelectedCharacterConfig(name="Priya Sharma", outfit="Base"),
            SelectedCharacterConfig(name="Nora Alvarez", outfit="Base"),
        ]
        suggestions = SuggestionEngine.get_suggestions(self.app_state)

        # 2 characters should trigger interaction recommendations
        self.assertGreater(len(suggestions["interactions"]), 0)
        top_int = suggestions["interactions"][0]
        self.assertIn("Priya", top_int.description)
        self.assertIn("Nora", top_int.description)
        self.assertNotIn("{char1}", top_int.description)


if __name__ == "__main__":
    unittest.main()
