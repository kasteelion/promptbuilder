import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from core.builder import PromptBuilder
from core.models import PromptConfig, SelectedCharacterConfig, CharacterDetails


class TestEngineOutputProfiles(unittest.TestCase):
    def setUp(self):
        self.characters = {
            "Priya": CharacterDetails(
                name="Priya",
                appearance="Warm brown eyes, sleek dark hair, confident presence",
                signature_color="Teal",
                outfits={
                    "Urban Chic": {
                        "Top": "Silk blouse",
                        "Bottom": "Tailored trousers",
                        "Footwear": "Leather ankle boots",
                    }
                },
                outfits_categorized={"Fashion": {"Urban Chic": "Top: Silk blouse"}},
            ),
            "Nora": CharacterDetails(
                name="Nora",
                appearance="Striking hazel eyes, athletic bearing",
                signature_color="Emerald",
                outfits={
                    "Casual Street": {
                        "Top": "Fitted jacket",
                        "Bottom": "Dark denim",
                    }
                },
                outfits_categorized={"Casual": {"Casual Street": "Top: Fitted jacket"}},
            ),
        }
        self.base_prompts = {
            "Cinematic Film": {
                "description": "High-fidelity 35mm film photograph, subtle grain, cinematic optics"
            },
            "Anime Cel": {
                "description": "Vibrant anime cel shading, clean linework, studio animation"
            }
        }
        self.poses = {
            "Casual": {"Standing": {"description": "leaning casually against a brick wall"}},
        }
        self.builder = PromptBuilder(
            characters=self.characters,
            base_prompts=self.base_prompts,
            poses=self.poses,
        )

    def test_midjourney_output_format(self):
        config = PromptConfig(
            base_prompt="Cinematic Film",
            scene="Neon-lit alleyway in cyberpunk city",
            selected_characters=[
                SelectedCharacterConfig(
                    name="Priya",
                    outfit="Urban Chic",
                    pose_category="Casual",
                    pose_preset="Standing",
                )
            ],
            notes="Exchanging knowing glances",
        )
        prompt = self.builder.generate(config, format_type="midjourney")

        # Verify Midjourney parameters appended
        self.assertIn("--ar 16:9 --v 6.1 --stylize 250", prompt)
        # Verify no markdown formatting symbols
        self.assertNotIn("**", prompt)
        self.assertNotIn("##", prompt)
        self.assertNotIn("---", prompt)
        # Verify components present
        self.assertIn("Priya", prompt)
        self.assertIn("Neon-lit alleyway", prompt)
        self.assertIn("Silk blouse", prompt)

    def test_sdxl_output_format(self):
        config = PromptConfig(
            base_prompt="Cinematic Film",
            scene="Rainy evening downtown",
            selected_characters=[
                SelectedCharacterConfig(
                    name="Priya",
                    outfit="Urban Chic",
                    pose_category="Casual",
                    pose_preset="Standing",
                )
            ],
        )
        prompt = self.builder.generate(config, format_type="sdxl")

        # Verify positive and negative separation
        self.assertIn("NEGATIVE:", prompt)
        self.assertIn("BREAK", prompt)
        # Verify weighting syntax
        self.assertIn("(Priya", prompt)
        # Verify auto-derived photo negative tags
        self.assertIn("illustration", prompt)
        self.assertIn("cartoon", prompt)
        self.assertIn("bad anatomy", prompt)

    def test_sdxl_anime_negative_derivation(self):
        config = PromptConfig(
            base_prompt="Anime Cel",
            scene="Cherry blossom garden",
            selected_characters=[
                SelectedCharacterConfig(name="Nora", outfit="Casual Street")
            ],
        )
        prompt = self.builder.generate(config, format_type="sdxl")

        # In anime style, photorealistic should be in negative prompt
        self.assertIn("photorealistic", prompt)
        self.assertIn("NEGATIVE:", prompt)


if __name__ == "__main__":
    unittest.main()
