import unittest
from unittest.mock import MagicMock
import sys
import os

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.interaction_logic import InteractionLogic

class MockAppState:
    def __init__(self):
        self.ctx = MagicMock()
        self.ctx.scenes = {
            "Urban": {"Coffee Shop": {"description": "A quiet coffee shop."}}
        }
        self.ctx.interactions = {
            "Social": {
                "Chat": {
                    "description": "{char1} and {char2} are chatting.",
                    "required_poses": ["Sitting", "Standing"]
                }
            }
        }

class TestInteractionLogic(unittest.TestCase):
    def setUp(self):
        self.app_state = MockAppState()
        self.logic = InteractionLogic(self.app_state)
        
    def test_placeholder_replacement(self):
        text = "{char1} looks at {char2}."
        chars = [{"name": "Alice"}, {"name": "Bob"}]
        result = self.logic.resolve_interaction(text, chars)
        self.assertEqual(result, "Alice looks at Bob.")
        
    def test_sync_poses(self):
        interaction_data = {
            "required_poses": ["Kneeling", "Standing"]
        }
        chars = [
            {"name": "Alice", "action_note": "Walking"},
            {"name": "Bob", "action_note": "Sitting"}
        ]
        
        updated = self.logic.sync_poses_from_interaction(interaction_data, chars)
        
        self.assertEqual(len(updated), 2)
        self.assertEqual(chars[0]["action_note"], "Kneeling")
        self.assertEqual(chars[1]["action_note"], "Standing")
        
    def test_scene_selection(self):
        desc = self.logic.process_scene_selection("Urban", "Coffee Shop")
        self.assertEqual(desc, "A quiet coffee shop.")

if __name__ == '__main__':
    unittest.main()
