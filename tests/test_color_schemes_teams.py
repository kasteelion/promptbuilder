import unittest
from utils.color_scheme import parse_color_schemes, substitute_colors
from logic.style_parser import StyleParser

class TestColorSchemesTeams(unittest.TestCase):
    def setUp(self):
        with open("data/lists/color_schemes.md", "r", encoding="utf-8") as f:
            self.content = f.read()
            
    def test_utils_parse_color_schemes(self):
        schemes = parse_color_schemes("data/lists/color_schemes.md")
        self.assertIn("The Coastal Bears", schemes)
        self.assertIn("team", schemes["The Coastal Bears"])
        self.assertEqual(schemes["The Coastal Bears"]["team"], "The Coastal Bears")
        
    def test_logic_parse_color_schemes(self):
        schemes = StyleParser.parse_color_schemes(self.content)
        self.assertIn("The Coastal Bears", schemes)
        self.assertIn("team", schemes["The Coastal Bears"])
        self.assertEqual(schemes["The Coastal Bears"]["team"], "The Coastal Bears")

    def test_substitution(self):
        schemes = parse_color_schemes("data/lists/color_schemes.md")
        scheme = schemes["The Coastal Bears"]
        text = "Team: {team}"
        result = substitute_colors(text, scheme)
        self.assertEqual(result, "Team: The Coastal Bears")

    def test_outfit_substitution(self):
        schemes = parse_color_schemes("data/lists/color_schemes.md")
        scheme = schemes["The Coastal Bears"]
        outfit_template = "**Football jersey** for **{team}** in **{primary_color}**"
        result = substitute_colors(outfit_template, scheme)
        self.assertEqual(result, "**Football jersey** for **The Coastal Bears** in **#2774AE**")

if __name__ == "__main__":
    unittest.main()
