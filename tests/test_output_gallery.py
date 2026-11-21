import unittest
import os
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ui.dialogs.output_gallery import OutputGalleryDialog


class DummyState:
    def __init__(self):
        self.state = {
            "base_prompt": "",
            "scene": "",
            "notes": "",
            "selected_characters": []
        }

    def ensure_character_loaded(self, name):
        pass


class DummyApp:
    def __init__(self, is_web=False):
        self.is_web = is_web
        self.page = None
        self.state = DummyState()
        self.toast_msg = None
        self.toast_color = None

    def show_toast(self, msg, color=None):
        self.toast_msg = msg
        self.toast_color = color

    def close_dialog(self, dlg):
        pass


class TestOutputGallery(unittest.TestCase):
    def setUp(self):
        self.app = DummyApp(is_web=False)
        self.dialog = OutputGalleryDialog(self.app)

    def test_initialization_paths(self):
        self.assertTrue(os.path.exists(self.dialog.images_dir))
        self.assertTrue(os.path.exists(self.dialog.prompts_dir))
        self.assertIn("generated_images", self.dialog.images_dir)
        self.assertIn("prompts", self.dialog.prompts_dir)
        self.assertGreaterEqual(self.dialog.images_count, 0)
        self.assertGreaterEqual(self.dialog.prompts_count, 0)

    def test_metadata_parsing(self):
        sample_text = """Generate an image of: A hero standing in the rain.

# METADATA
Base_Prompt: Cinematic 3D
Scene: Rainy Rooftop
Interaction: Looking over city skyline
Score: 420
Character: Maya Lin | Outfit: Stealth Combat Suit | Pose: Standing | Color_Scheme: Midnight Blue
Character: Alex Cole | Outfit: Tactical Vest | Pose: Crouching | Color_Scheme: Gunmetal Grey
"""
        meta = OutputGalleryDialog.parse_prompt_metadata(sample_text)
        self.assertEqual(meta["base_prompt"], "Cinematic 3D")
        self.assertEqual(meta["scene"], "Rainy Rooftop")
        self.assertEqual(meta["interaction"], "Looking over city skyline")
        self.assertEqual(meta["score"], 420)
        self.assertEqual(len(meta["selected_characters"]), 2)
        self.assertEqual(meta["selected_characters"][0]["name"], "Maya Lin")
        self.assertEqual(meta["selected_characters"][0]["outfit"], "Stealth Combat Suit")
        self.assertEqual(meta["selected_characters"][1]["name"], "Alex Cole")

    def test_switch_modes(self):
        self.assertEqual(self.dialog.current_mode, "images")
        self.dialog.switch_mode("prompts")
        self.assertEqual(self.dialog.current_mode, "prompts")
        self.assertEqual(self.dialog.directory, self.dialog.prompts_dir)
        self.dialog.switch_mode("images")
        self.assertEqual(self.dialog.current_mode, "images")
        self.assertEqual(self.dialog.directory, self.dialog.images_dir)

    def test_web_mode_thumbnail_generation(self):
        app_web = DummyApp(is_web=True)
        dlg_web = OutputGalleryDialog(app_web)
        if dlg_web.items:
            first_path = dlg_web.items[0]["path"]
            b64 = dlg_web._get_thumbnail_base64(first_path)
            self.assertTrue(len(b64) > 100)
            self.assertLess(len(b64), 200000)  # Verify compressed thumbnail size

    def test_load_settings(self):
        sample_text = """Generate an image of: ...
# METADATA
Base_Prompt: Watercolor
Scene: Sunlit Meadow
Interaction: Running through flowers
Score: 350
Character: Maya Lin | Outfit: Summer Dress | Pose: Joyful | Color_Scheme: Pastel
"""
        self.dialog.handle_load_settings(sample_text)
        self.assertEqual(self.app.state.state["base_prompt"], "Watercolor")
        self.assertEqual(self.app.state.state["scene"], "Sunlit Meadow")
        self.assertEqual(self.app.state.state["notes"], "Running through flowers")
        self.assertIn("loaded into workspace", self.app.toast_msg)


if __name__ == "__main__":
    unittest.main()
