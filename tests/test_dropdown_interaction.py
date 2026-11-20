import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.models import SelectedCharacterConfig, CharacterDetails
from ui.components.roster_item import RosterItem
from core.flet_theme_manager import ThemeManager

class MockApp:
    def __init__(self):
        self.state = MagicMock()
        self.state.ctx = MagicMock()
        self.state.ctx.characters = {
            "TestChar": CharacterDetails(
                name="TestChar",
                appearance="Look",
                outfits_categorized={
                    "Casual": {"Shirt": {}},
                    "Formal": {"Suit": {}}
                },
                traits={},
                signature_color="blue",
                age_presentation="20s",
                vibe="Cool"
            )
        }
        self.state.get_character_summary.return_value = "Summary"
        self.remove_character = MagicMock()
        self.handle_solo_randomize = MagicMock()
        self.update_preview = MagicMock()

class TestRosterDropdowns(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('flet.Control.update')
        self.mock_update = self.patcher.start()

        # Patch ThemeManager to avoid color issues if not loaded
        ThemeManager.colors = {
            "surface": "black", "panel_bg": "grey", 
            "outline": "white", "text_primary": "white", 
            "text_secondary": "grey", "active_item": "blue",
            "accent": "cyan", "surface_variant": "black",
            "error": "red"
        }
        ThemeManager.styles = {"radius": 5, "padding": 10}
        ThemeManager.color_schemes = {"Default": "None", "Red Theme": "Red and black"}

        self.app = MockApp()
        self.app.state.ctx.poses = {
            "Standing": {"Default": "Standing straight"},
            "Action": {"Running": "Running fast", "Jumping": "Jumping high"}
        }
        self.char_data = SelectedCharacterConfig(
            name="TestChar", 
            pose_category="Standing", 
            pose_preset="Default"
        )
        self.item = RosterItem(self.app, 0, self.char_data)
        self.item.color_scheme_keys = ["Default", "Red Theme"]
        # RosterItem actually builds via sync_style() and build_ui() after init in normal usage, but we patch it so we need to ensure refs exist
        if not hasattr(self.item, "_refs") or "header" not in self.item._refs:
            self.item.build_ui()

    def tearDown(self):
        self.patcher.stop()

    def test_pose_category_cascade(self):
        # Simulate Change Event
        e = MagicMock()
        e.control.value = "Action"

        # Call Handler
        self.item.handle_pose_cat_change(e)
        
        # Verify Context Updated
        self.assertEqual(self.char_data.pose_category, "Action")
        # Sorted keys for "Action" are "Jumping", "Running", so first is "Jumping"
        self.assertEqual(self.char_data.pose_preset, "Jumping")
        
        # Verify UI Updated
        self.assertEqual(self.item._refs["pose_cat_dd"].value, "Action")
        self.assertEqual(self.item._refs["pose_preset_dd"].value, "Jumping")
        
        options = [o.key for o in self.item._refs["pose_preset_dd"].options]
        self.assertIn("Jumping", options)
        self.assertIn("Running", options)
        self.assertNotIn("Default", options)
        print("Cascade successful: Pose category change updated Pose preset options and value.")

class TestSidebarDropdowns(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('flet.Control.update')
        self.mock_update = self.patcher.start()

        ThemeManager.colors = {
            "surface": "black", "panel_bg": "grey", 
            "outline": "white", "text_primary": "white", 
            "text_secondary": "grey", "active_item": "blue",
            "accent": "cyan", "surface_variant": "black",
            "error": "red", "header_bg": "black", "header_fg": "white"
        }
        ThemeManager.styles = {"radius": 5, "padding": 10}
        ThemeManager.color_schemes = {"Default": "None", "Red Theme": "Red and black"}
        
        self.app = MockApp()
        self.app.handle_randomize = MagicMock() # Mock missing method
        
        # Mock Context Data for Sidebar
        self.app.state.ctx.scenes = {"Urban": {"Street": {}}}
        self.app.state.ctx.interactions = {"Social": {"Chat": {"description": "Chatting"}}}
        self.app.state.state = {} # Initialize state dict
        
        # Mock Interaction Logic
        self.app.interaction_logic = MagicMock()
        self.app.interaction_logic.process_scene_selection.return_value = "A busy street."
        self.app.interaction_logic.process_interaction_selection.return_value = {"description": "Chatting"}
        self.app.interaction_logic.resolve_interaction.return_value = "Chatting resolved."
        
        from ui.sections.sidebar import SidebarSection
        self.sidebar = SidebarSection(self.app)
        self.sidebar.populate_data()

    def tearDown(self):
        self.patcher.stop()

    def test_scene_cascade(self):
        print("\nTesting Scene Cascade...")
        # Simulate Change
        e = MagicMock()
        e.control.value = "Urban"
        self.sidebar.handle_scene_cat_change(e)
        
        options = [o.key for o in self.sidebar.scene_preset_dd.options]
        self.assertIn("Street", options)
        print("Scene cascade successful.")

if __name__ == '__main__':
    unittest.main()
