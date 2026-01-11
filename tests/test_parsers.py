import unittest
from logic.character_parser import CharacterParser

class TestCharacterParser(unittest.TestCase):

    def test_parse_basic_character(self):
        markdown = """
### Test Char
**Appearance:** A test character.
**Gender:** F
**Outfits:**
- **Outfit 1:** Description 1
"""
        chars = CharacterParser.parse_characters(markdown)
        self.assertIn("Test Char", chars)
        self.assertEqual(chars["Test Char"]["appearance"], "A test character.")
        self.assertEqual(chars["Test Char"]["gender"], "F")
        self.assertIn("Outfit 1", chars["Test Char"]["outfits"])
        self.assertEqual(chars["Test Char"]["outfits"]["Outfit 1"], "Description 1")

    def test_parse_multiple_characters(self):
        markdown = """
### Char 1
**Appearance:** Appearance 1
**Outfits:**
- **O1:** D1

### Char 2
**Appearance:** Appearance 2
**Outfits:**
- **O2:** D2
"""
        chars = CharacterParser.parse_characters(markdown)
        self.assertEqual(len(chars), 2)
        self.assertIn("Char 1", chars)
        self.assertIn("Char 2", chars)

    def test_parse_structured_outfit(self):
        markdown = """
### Structured Char
**Appearance:** Look
**Outfits:**
#### School Uniform
- Top: White shirt
- Bottom: Blue skirt
- Shoes: Loafers
"""
        chars = CharacterParser.parse_characters(markdown)
        outfits = chars["Structured Char"]["outfits"]
        self.assertIn("School Uniform", outfits)
        self.assertIsInstance(outfits["School Uniform"], dict)
        self.assertEqual(outfits["School Uniform"]["Top"], "White shirt")
        self.assertEqual(outfits["School Uniform"]["Bottom"], "Blue skirt")

    def test_missing_appearance_handled_gracefully(self):
        markdown = """
### Ghost Char
**Outfits:**
- **O1:** D1
"""
        chars = CharacterParser.parse_characters(markdown)
        # Parser adds empty appearance if missing
        self.assertEqual(chars["Ghost Char"]["appearance"], "")

    def test_invalid_character_block(self):
        # A block without a name header shouldn't crash it, but might be skipped or handled specific way
        # Based on current logic, split happens on ### so text before first ### is ignored
        markdown = """
Random text
### Valid Char
**Appearance:** OK
"""
        chars = CharacterParser.parse_characters(markdown)
        self.assertEqual(len(chars), 1)
        self.assertIn("Valid Char", chars)

    def test_identity_locks(self):
        text = """
Appearance (Identity Locks):
- Body: Tall
- Face: Round
- Hair: Short
- Skin: Pale
Age Presentation: 20s
"""
        result = CharacterParser.parse_identity_locks(text)
        self.assertIsNotNone(result)
        self.assertEqual(result["Body"], "Tall")
        self.assertEqual(result["Face"], "Round")
        self.assertEqual(result["Age Presentation"], "20s")

    def test_identity_locks_none(self):
        text = "Just some random text."
        result = CharacterParser.parse_identity_locks(text)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
