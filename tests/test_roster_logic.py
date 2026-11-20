import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.models import SelectedCharacterConfig, CharacterDetails
from core.flet_theme_manager import ThemeManager
from ui.sections.roster import RosterSection
from ui.components.roster_item import RosterItem

class MockApp:
    def __init__(self):
        self.state = MagicMock()
        self.state.state = {
            "selected_characters": [
                SelectedCharacterConfig(
                    name="Sarah",
                    outfit_category="Casual",
                    outfit="Jeans",
                    character_traits=[],
                    outfit_traits=[],
                ),
                SelectedCharacterConfig(
                    name="Mike",
                    outfit_category="Casual",
                    outfit="Base",
                ),
            ]
        }
        self.state.ctx = MagicMock()
        self.state.ctx.characters = {
            "Sarah": CharacterDetails(
                name="Sarah",
                appearance="Brown hair",
                traits={"Happy": "Yes", "Sad": "No"},
                outfits_categorized={
                    "Casual": {"Jeans": {"modifiers": {"Ripped": {}}}, "T-Shirt": {}}
                },
                outfits={"Jeans": {"modifiers": {"Ripped": {}}}, "T-Shirt": {}},
                signature_color="blue",
            ),
            "Mike": CharacterDetails(
                name="Mike",
                appearance="Tall",
                outfits={},
                outfits_categorized={},
            ),
        }
        self.state.ctx.poses = {"Standing": {"Default": "Standing straight"}}
        
        self.remove_character = MagicMock()
        self.clear_all_characters = MagicMock()
        self.handle_solo_randomize = MagicMock()
        self.update_preview = MagicMock()
        self.show_toast = MagicMock()
        self.open_outfit_builder = MagicMock()

class TestRosterLogic(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('flet.Control.update')
        self.mock_update = self.patcher.start()
        
        ThemeManager.colors = {
            "surface": "black", "panel_bg": "grey", 
            "outline": "white", "text_primary": "white", 
            "text_secondary": "grey", "active_item": "blue",
            "accent": "green", "surface_variant": "black",
            "error": "red", "header_bg": "black", "header_fg": "white"
        }
        ThemeManager.styles = {"radius": 5, "padding": 10}
        ThemeManager.color_schemes = {"Default": "None", "Red Theme": "Red and black"}
        
        self.app = MockApp()
        self.roster = RosterSection(self.app)
        # Make sure roster items build their internal refs for tests
        for item in self.roster.roster_list.controls:
            item.color_scheme_keys = ["Default", "Red Theme"]
            if hasattr(item, "build_ui") and ("header" not in getattr(item, "_refs", {})):
                item.build_ui()
        
    def tearDown(self):
        self.patcher.stop()

    def test_refresh_populates_items(self):
        print("\nTesting Refresh...")
        self.roster.refresh()
        
        # Check that we have 2 controls in the list (one for each character)
        items = self.roster.roster_list.controls
        self.assertEqual(len(items), 2)
        self.assertIsInstance(items[0], RosterItem)
        print(f"Roster populated with {len(items)} RosterItems.")

    def test_roster_item_expanded_toggle(self):
        """Test that a RosterItem can be toggled expanded/collapsed."""
        print("\nTesting RosterItem Toggle...")
        self.roster.refresh()
        item = self.roster.roster_list.controls[0]
        
        # Ensure it is properly initialized for testing UI updates
        # Since Flet isn't running an event loop, we mock ThemeManager strictly and ensure UI maps 
        if not hasattr(item, "_refs") or "header" not in item._refs:
            item.build_ui()
            item.sync_style()
        
        # RosterItem stores char_data as SelectedCharacterConfig
        # Toggle should change _expanded private attribute
        initial = getattr(item.char_data, '_expanded', True)
        item.toggle_expanded()
        toggled = getattr(item.char_data, '_expanded', True)
        self.assertNotEqual(initial, toggled)
        print("RosterItem toggled successfully.")

    def test_bulk_apply(self):
        print("\nTesting Bulk Apply Sig...")
        self.roster.bulk_sig_toggle.value = True
        
        self.roster.handle_bulk_apply_sig(None)
        
        char0 = self.app.state.state["selected_characters"][0]
        self.assertTrue(char0.use_signature_color)
        print("Bulk apply signature color updated state.")

if __name__ == '__main__':
    unittest.main()
