"""Tests for CharacterController (Flet-era logic layer)."""

import unittest
from unittest.mock import MagicMock
from core.models import CharacterDetails
from logic.controllers import CharacterController


class MockAppState:
    """Minimal AppState mock for controller tests."""

    def __init__(self):
        self.page = MagicMock()
        self.state = {
            "selected_characters": [],
            "base_prompt": "Detailed",
            "scene": "",
            "notes": "",
        }
        self.ctx = MagicMock()
        self.ctx.characters = {
            "Alice": CharacterDetails(
                name="Alice",
                appearance="Blonde hair",
                tags=["Student"],
                outfits={"Base": "Default outfit"},
                outfits_categorized={"Personal": {"Base": "Default outfit"}},
            )
        }
        self.ctx.poses = {"Standing": {"Default": "Standing straight"}}
        self.ctx.interactions = {}
        self.ctx.color_schemes = {}
        self.builder = MagicMock()

    def ensure_character_loaded(self, name):
        return name in self.ctx.characters


class TestCharacterController(unittest.TestCase):

    def setUp(self):
        self.app_state = MockAppState()
        self.controller = CharacterController(self.app_state)

    def test_add_character(self):
        result = self.controller.add_character("Alice")
        self.assertTrue(result)
        self.assertEqual(len(self.app_state.state["selected_characters"]), 1)
        self.assertEqual(self.app_state.state["selected_characters"][0].name, "Alice")

    def test_toggle_removes_character(self):
        self.controller.add_character("Alice")
        result = self.controller.add_character("Alice")
        self.assertFalse(result)
        self.assertEqual(len(self.app_state.state["selected_characters"]), 0)

    def test_add_unknown_character(self):
        result = self.controller.add_character("UnknownChar")
        self.assertFalse(result)
        self.assertEqual(len(self.app_state.state["selected_characters"]), 0)

    def test_move_character(self):
        self.app_state.ctx.characters["Bob"] = CharacterDetails(
            name="Bob",
            appearance="Dark hair",
            tags=["Office"],
            outfits={"Base": "Default"},
            outfits_categorized={"Personal": {"Base": "Default"}},
        )
        self.app_state.ensure_character_loaded = lambda n: True
        self.controller = CharacterController(self.app_state)
        self.controller.add_character("Alice")
        self.controller.add_character("Bob")
        self.controller.move_character(0, 1)
        self.assertEqual(self.app_state.state["selected_characters"][0].name, "Bob")
        self.assertEqual(self.app_state.state["selected_characters"][1].name, "Alice")

    def test_get_summary(self):
        self.controller.add_character("Alice")
        summary = self.controller.get_summary(0)
        self.assertIsInstance(summary, str)
        self.assertIn("|", summary)


if __name__ == "__main__":
    unittest.main()
