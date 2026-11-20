"""Tests for Settings Dialog and Preferences."""

import unittest
from unittest.mock import MagicMock
import tempfile
import json
from pathlib import Path
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.preferences import PreferencesManager
from ui.dialogs.settings_dialog import SettingsDialog


class TestSettings(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.prefs_file = Path(self.temp_dir.name) / "test_prefs.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_ai_preferences(self):
        mgr = PreferencesManager(prefs_file=str(self.prefs_file))
        self.assertEqual(mgr.get("ai_provider"), "auto")
        self.assertEqual(mgr.get("gemini_model"), "gemini-2.5-flash")
        self.assertEqual(mgr.get("ollama_model"), "gemma2")
        self.assertEqual(mgr.get("enhance_style"), "cinematic")

    def test_save_and_reload_ai_preferences(self):
        mgr = PreferencesManager(prefs_file=str(self.prefs_file))
        mgr.set("gemini_model", "gemini-2.0-flash")
        mgr.set("ai_provider", "gemini")
        mgr.set("enhance_style", "photorealistic")

        mgr2 = PreferencesManager(prefs_file=str(self.prefs_file))
        self.assertEqual(mgr2.get("gemini_model"), "gemini-2.0-flash")
        self.assertEqual(mgr2.get("ai_provider"), "gemini")
        self.assertEqual(mgr2.get("enhance_style"), "photorealistic")

    def test_settings_dialog_instantiation(self):
        mock_app = MagicMock()
        mock_app.state.ctx.gemma_client = None
        mock_app.page = MagicMock()

        dialog = SettingsDialog(mock_app)
        self.assertIsNotNone(dialog.provider_dd)
        self.assertIsNotNone(dialog.gemini_model_dd)
        self.assertIsNotNone(dialog.api_key_input)
        self.assertIsNotNone(dialog.style_dd)


if __name__ == "__main__":
    unittest.main()
