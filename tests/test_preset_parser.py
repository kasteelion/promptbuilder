import unittest
from logic.preset_parser import PresetParser

class TestPresetParser(unittest.TestCase):
    
    def test_parse_presets_basic(self):
        content = """## Default
- **Scene A**: A beautiful scene.
- **Scene B** (tag1, tag2): Another scene.
"""
        presets = PresetParser.parse_presets(content)
        self.assertIn("Default", presets)
        self.assertIn("Scene A", presets["Default"])
        self.assertEqual(presets["Default"]["Scene A"]["description"], "A beautiful scene.")
        self.assertEqual(presets["Default"]["Scene B"]["tags"], ["tag1", "tag2"])

    def test_parse_interactions_standard(self):
        content = """## Basic
- **Talk** (social): Two people talking.
"""
        interactions = PresetParser.parse_interactions(content)
        self.assertIn("Basic", interactions)
        self.assertIn("Talk", interactions["Basic"])
        self.assertEqual(interactions["Basic"]["Talk"]["description"], "Two people talking.")
        self.assertEqual(interactions["Basic"]["Talk"]["tags"], ["social"])

    def test_parse_interactions_colon_inside_bold(self):
        """Test the bug fix: **Name:** format."""
        content = """## Mixed
- **Talk:** Two people talking.
- **Fight:** Two people fighting.
"""
        interactions = PresetParser.parse_interactions(content)
        self.assertIn("Mixed", interactions)
        self.assertIn("Talk", interactions["Mixed"])
        self.assertEqual(interactions["Mixed"]["Talk"]["description"], "Two people talking.")

    def test_parse_interactions_char_count(self):
        content = """## Group
- **Party (3+)**: A big party.
"""
        interactions = PresetParser.parse_interactions(content)
        self.assertEqual(interactions["Group"]["Party (3+)"]["min_chars"], 3)

    def test_parse_interactions_char_count_from_description(self):
        content = """## Implicit
- **Chat**: {char1} and {char2} chatting.
"""
        interactions = PresetParser.parse_interactions(content)
        self.assertEqual(interactions["Implicit"]["Chat"]["min_chars"], 2)

if __name__ == '__main__':
    unittest.main()
