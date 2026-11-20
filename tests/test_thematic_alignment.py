import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from unittest.mock import MagicMock
import flet as ft
from core.models import SelectedCharacterConfig, CharacterDetails


class TestThematicAlignment(unittest.TestCase):
    def setUp(self):
        # Setup mock app and state
        self.app = MagicMock()
        self.state_dict = {
            "selected_characters": [],
            "base_prompt": "Default",
            "scene": "",
            "notes": "",
        }
        self.app.state.state = self.state_dict
        self.app.state.ctx = MagicMock()
        self.app.state.ctx.color_schemes = {
            "Maroon & Khaki": {"primary": "#800020", "secondary": "#C3B091"}
        }
        self.app.state.ctx.characters = {}
        self.app.state.ctx.characters_metadata = {}
        self.app.state.data_loader = MagicMock()
        
        # Mock get_character_details to return tags
        details = CharacterDetails(
            name="Amina",
            gender="F",
            appearance="Cool hacker look",
            tags=["cyberpunk", "hacker", "neon"],
            vibe="cool and mysterious",
            bearing="poised"
        )
        self.app.state.data_loader.get_character_details.return_value = details

        from ui.sections.sidebar import SidebarSection
        self.sidebar = SidebarSection(self.app)

    def test_alignment_progression(self):
        # 1. No characters selected -> Meter hidden
        self.sidebar.update_summary("")
        self.assertFalse(self.sidebar.quality_meter.visible)

        # 2. Add 1 character (Base outfit, no scene, default style) -> 20%
        char = SelectedCharacterConfig(name="Amina", outfit="Base", color_scheme="Default (No Scheme)")
        self.state_dict["selected_characters"] = [char]
        self.sidebar.update_summary("")
        self.assertTrue(self.sidebar.quality_meter.visible)
        self.assertAlmostEqual(self.sidebar.quality_bar.value, 0.20, places=2)
        self.assertIn("20%", self.sidebar.quality_text.value)

        # 3. Apply Scene (with matching tag 'cyberpunk') -> +25% + 10% = 55%
        self.state_dict["scene"] = "A neon-lit cyberpunk alleyway in the rain"
        self.sidebar.update_summary("")
        self.assertAlmostEqual(self.sidebar.quality_bar.value, 0.55, places=2)
        self.assertIn("55%", self.sidebar.quality_text.value)

        # 4. Equip Thematic Outfit (non-base) -> +15% = 70%
        char.outfit = "Tactical Runner"
        self.sidebar.update_summary("")
        self.assertAlmostEqual(self.sidebar.quality_bar.value, 0.70, places=2)
        self.assertIn("70%", self.sidebar.quality_text.value)

        # 5. Add Narrative Interaction -> +15% = 85%
        self.state_dict["notes"] = "Scanning perimeter for surveillance drones"
        self.sidebar.update_summary("")
        self.assertAlmostEqual(self.sidebar.quality_bar.value, 0.85, places=2)
        self.assertIn("85%", self.sidebar.quality_text.value)

        # 6. Apply Color Harmony -> +10% = 95%
        char.color_scheme = "Maroon & Khaki"
        self.sidebar.update_summary("")
        self.assertAlmostEqual(self.sidebar.quality_bar.value, 0.95, places=2)
        self.assertIn("95%", self.sidebar.quality_text.value)

        # 7. Select Art Style -> +5% = 100%
        self.state_dict["base_prompt"] = "Cinematic Anime"
        self.sidebar.update_summary("")
        self.assertAlmostEqual(self.sidebar.quality_bar.value, 1.0, places=2)
        self.assertIn("100%", self.sidebar.quality_text.value)


if __name__ == "__main__":
    unittest.main()
