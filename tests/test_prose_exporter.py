import unittest
from core.builder import PromptBuilder
from core.models import PromptConfig, SelectedCharacterConfig, CharacterDetails


class TestProseExporter(unittest.TestCase):
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
            }
        }
        self.poses = {
            "Casual": {"Standing": {"description": "leaning casually against a brick wall"}},
            "Seated": {"Relaxed": {"description": "seated comfortably with arms crossed"}},
        }
        self.color_schemes = {
            "Maroon & Khaki": {
                "primary_color": "maroon",
                "secondary_color": "khaki",
                "accent": "brass",
            },
            "Navy & Amber": {
                "primary_color": "navy blue",
                "secondary_color": "amber",
                "accent": "cream",
            },
        }
        self.framing = {
            "Cowboy Shot": "Medium-wide cowboy shot framing,"
        }
        self.builder = PromptBuilder(
            characters=self.characters,
            base_prompts=self.base_prompts,
            poses=self.poses,
            color_schemes=self.color_schemes,
            framing=self.framing,
        )

    def test_single_character_prose_generation(self):
        config = PromptConfig(
            base_prompt="Cinematic Film",
            scene="Sunlit urban coffee shop courtyard with golden afternoon light",
            selected_characters=[
                SelectedCharacterConfig(
                    name="Priya",
                    outfit="Urban Chic",
                    pose_category="Casual",
                    pose_preset="Standing",
                    color_scheme="Maroon & Khaki",
                    use_signature_color=True,
                )
            ],
            notes="Enjoying an espresso between photo shoots.",
        )

        prose = self.builder.generate(config, format_type="prose")

        # Must not contain technical markdown bullets or headers
        self.assertNotIn("---", prose)
        self.assertNotIn("**CHARACTER", prose)
        self.assertNotIn("- Top:", prose)

        # Must contain rich narrative prose elements
        self.assertIn("Priya", prose)
        self.assertIn("coffee shop courtyard", prose)
        self.assertIn("Maroon & Khaki", prose)
        self.assertIn("Teal", prose)
        self.assertIn("Silk blouse", prose)
        self.assertIn("leaning casually", prose)
        self.assertIn("Enjoying an espresso", prose)

    def test_multi_character_prose_coordination(self):
        config = PromptConfig(
            base_prompt="Cinematic Film",
            scene="Neon-lit downtown alleyway at twilight",
            selected_characters=[
                SelectedCharacterConfig(
                    name="Priya",
                    outfit="Urban Chic",
                    pose_category="Casual",
                    pose_preset="Standing",
                    color_scheme="Maroon & Khaki",
                ),
                SelectedCharacterConfig(
                    name="Nora",
                    outfit="Casual Street",
                    pose_category="Seated",
                    pose_preset="Relaxed",
                    color_scheme="Navy & Amber",
                ),
            ],
            notes="{char1} and {char2} are reviewing camera test shots together.",
        )

        prose = self.builder.generate(config, format_type="prose")

        # Check multi-character connectivity
        self.assertIn("Priya", prose)
        self.assertIn("Alongside, Nora", prose)
        self.assertIn("Maroon & Khaki", prose)
        self.assertIn("Navy & Amber", prose)
        self.assertIn("Priya and Nora are reviewing camera test shots together.", prose)

    def test_markdown_format_remains_backward_compatible(self):
        config = PromptConfig(
            base_prompt="Cinematic Film",
            scene="Studio backdrop",
            selected_characters=[
                SelectedCharacterConfig(
                    name="Priya",
                    outfit="Urban Chic",
                )
            ],
        )

        # Default is markdown
        md = self.builder.generate(config)
        self.assertIn("---", md)
        self.assertIn("**CHARACTER: Priya**", md)
        self.assertIn("**Outfit:**", md)


if __name__ == "__main__":
    unittest.main()
