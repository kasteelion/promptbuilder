import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "automation")))

from core.builder import PromptBuilder
from core.models import SelectedCharacterConfig, CharacterDetails, PromptConfig
from logic.data_loader import DataLoader


class TestAutomationPipeline(unittest.TestCase):
    def setUp(self):
        self.loader = DataLoader()
        self.chars = self.loader.load_characters()
        self.base_prompts = self.loader.load_base_prompts()
        self.poses = self.loader.load_presets("poses.md")
        self.schemes = self.loader.load_color_schemes()
        self.modifiers = self.loader.load_modifiers()
        self.framing = self.loader.load_framing()
        self.builder = PromptBuilder(
            self.chars, self.base_prompts, self.poses, self.schemes, self.modifiers, self.framing
        )

    def test_automation_builder_formats(self):
        config = {
            "base_prompt": "Cinematic",
            "scene": "A bustling neon night market in Tokyo",
            "selected_characters": [
                SelectedCharacterConfig(
                    name="Amina Benali",
                    outfit="Base",
                    pose_preset="Natural Stance",
                    color_scheme="Maroon & Khaki",
                )
            ],
            "notes": "Exploring the street food stalls together",
        }

        # 1. Midjourney
        mj_prompt = self.builder.generate(config, format_type="midjourney")
        self.assertIn("--ar 16:9", mj_prompt)
        self.assertIn("--v 6.1", mj_prompt)
        self.assertNotIn("**CHARACTER", mj_prompt)

        # 2. SDXL
        sdxl_prompt = self.builder.generate(config, format_type="sdxl")
        self.assertIn("BREAK", sdxl_prompt)
        self.assertIn("NEGATIVE:", sdxl_prompt)

        # 3. Prose
        prose_prompt = self.builder.generate(config, format_type="prose")
        self.assertIn("Amina", prose_prompt)
        self.assertNotIn("**CHARACTER", prose_prompt)

        # 4. Markdown
        md_prompt = self.builder.generate(config, format_type="markdown")
        self.assertIn("**SCENE/SETTING:**", md_prompt)

    def test_automate_generation_script_integration(self):
        from automate_generation import generate_prompts
        prompts = generate_prompts(count=2, match_outfits_prob=0.3, format_type="midjourney")
        self.assertEqual(len(prompts), 2)
        for prompt_text, score, conf in prompts:
            self.assertIn("--ar 16:9", prompt_text)
            self.assertTrue(len(prompt_text) > 50)

    def test_bulk_generator_script_integration(self):
        from bulk_generator import parse_bulk_text, resolve_config
        sample_text = """
PROMPT CONFIG
Base: Film Noir
Scene: A foggy bridge at night
[1] Amina
Outfit: Casual
Pose: Arms Crossed
Notes: Waiting quietly in the mist
"""
        configs = parse_bulk_text(sample_text)
        self.assertEqual(len(configs), 1)
        resolved = resolve_config(configs[0], self.loader, self.poses)
        self.assertEqual(resolved["base_prompt"], "Film Noir")
        self.assertEqual(len(resolved["selected_characters"]), 1)
        
        # Verify Midjourney generation from resolved config
        out_mj = self.builder.generate(resolved, format_type="midjourney")
        self.assertIn("--ar 16:9", out_mj)

    def test_automation_reexport_client(self):
        """Verify ai_studio_client facade re-exports AIStudioClient cleanly."""
        from ai_studio_client import AIStudioClient, generate_images_simple
        from utils.ai_client import AIStudioClient as CanonicalClient
        self.assertIs(AIStudioClient, CanonicalClient)
        self.assertTrue(callable(generate_images_simple))

    def test_orchestrator_concurrency_guard(self):
        """Verify AutomationOrchestrator prevents overlapping generations."""
        from logic.automation.orchestrator import AutomationOrchestrator
        ctx = MagicMock()
        orchestrator = AutomationOrchestrator(ctx)
        self.assertFalse(orchestrator.is_running())

        errors = []
        # Simulate active running thread
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        orchestrator._thread = mock_thread

        self.assertTrue(orchestrator.is_running())

        orchestrator.start_generation(
            count=1,
            match_outfits_prob=0.5,
            prompts_only=True,
            on_progress=lambda c, t, m: None,
            on_complete=lambda res: None,
            on_error=lambda err: errors.append(err)
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("already running", str(errors[0]))

    def test_missing_portraits_preference_default(self):
        """Verify auto_generate_missing_portraits is disabled by default."""
        from utils.preferences import PreferencesManager
        prefs = PreferencesManager()
        self.assertFalse(prefs.get("auto_generate_missing_portraits", False))


if __name__ == "__main__":
    unittest.main()
