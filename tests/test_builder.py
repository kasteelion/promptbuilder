import unittest
from core.builder import PromptBuilder
from core.definitions import PromptConfig

class TestPromptBuilder(unittest.TestCase):
    
    def setUp(self):
        self.characters = {
            "Alice": {
                "name": "Alice",
                "appearance": "Blonde hair",
                "signature_color": "red"
            }
        }
        self.base_prompts = {"Default": "Art style"}
        self.poses = {}
        self.modifiers = {"TestMod": "shiny"}
        
        self.builder = PromptBuilder(
            characters=self.characters,
            base_prompts=self.base_prompts,
            poses=self.poses,
            modifiers=self.modifiers
        )

    def test_modifier_substitution(self):
        # Outfit with {modifier} placeholder
        outfit_template = "Wearing a {modifier} dress"
        
        self.characters["Alice"]["outfits"] = {"TestOutfit": outfit_template}
        
        config: PromptConfig = {
            "base_prompt": "Default",
            "selected_characters": [
                {
                    "name": "Alice",
                    "outfit": "TestOutfit",
                    "outfit_traits": ["TestMod"] # Should resolve to "shiny"
                }
            ]
        }
        
        prompt = self.builder.generate(config)
        self.assertIn("Wearing a shiny dress", prompt)

    def test_signature_color(self):
        # Outfit with {signature_color} placeholder
        outfit_template = "Wearing a {signature_color} scarf"
        
        self.characters["Alice"]["outfits"] = {"TestOutfit": outfit_template}
        
        config: PromptConfig = {
            "base_prompt": "Default",
            "selected_characters": [
                {
                    "name": "Alice",
                    "outfit": "TestOutfit",
                    "use_signature_color": True
                }
            ]
        }
        
        prompt = self.builder.generate(config)
        self.assertIn("Wearing a red scarf", prompt)

if __name__ == '__main__':
    unittest.main()
