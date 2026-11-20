import unittest
from unittest.mock import MagicMock
from utils.gemma_client import GemmaClient
from ui.dialogs.director_takes_dialog import DirectorTakesDialog


class TestDirectorTakes(unittest.TestCase):
    def setUp(self):
        self.client = GemmaClient(api_key="test-key", mode="cloud")

    def test_director_takes_fallback_offline(self):
        # When cloud dispatch fails or returns invalid json, returns structured fallback takes
        self.client._call_cloud = MagicMock(return_value="Invalid text")
        takes = self.client.generate_director_takes("Alice in a library reading a book", num_takes=3)

        self.assertEqual(len(takes), 3)
        for take in takes:
            self.assertIn("title", take)
            self.assertIn("style_notes", take)
            self.assertIn("prompt", take)
            self.assertTrue(len(take["prompt"]) > 10)

    def test_director_takes_json_success(self):
        json_mock = """[
            {
                "title": "Take 1: Golden Hour Intimate",
                "style_notes": "Warm backlit natural light with 35mm lens.",
                "prompt": "Priya sitting in golden sunlight with a warm cup."
            },
            {
                "title": "Take 2: Dynamic Action High-Contrast",
                "style_notes": "Low-angle wide shot with bold shadows.",
                "prompt": "Priya moving dynamically through urban shadows."
            },
            {
                "title": "Take 3: Editorial Stylized",
                "style_notes": "Clean studio rim light with 85mm telephoto.",
                "prompt": "Priya posed in high fashion editorial precision."
            }
        ]"""
        self.client._call_cloud = MagicMock(return_value=json_mock)
        takes = self.client.generate_director_takes("Base prompt", num_takes=3)

        self.assertEqual(len(takes), 3)
        self.assertEqual(takes[0]["title"], "Take 1: Golden Hour Intimate")
        self.assertEqual(takes[1]["title"], "Take 2: Dynamic Action High-Contrast")

    def test_dialog_instantiation(self):
        mock_app = MagicMock()
        mock_apply = MagicMock()
        takes = [
            {"title": "Take 1", "style_notes": "Cinematic", "prompt": "Prompt 1"},
            {"title": "Take 2", "style_notes": "Action", "prompt": "Prompt 2"},
        ]
        dialog_mgr = DirectorTakesDialog(mock_app, takes, on_apply=mock_apply)
        dialog = dialog_mgr.build()

        self.assertIsNotNone(dialog)
        self.assertEqual(dialog_mgr.takes, takes)

        # Test apply trigger
        dialog_mgr._apply("Prompt 1", "Take 1")
        mock_apply.assert_called_once_with("Prompt 1")
        mock_app.show_toast.assert_called_once()


if __name__ == "__main__":
    unittest.main()
