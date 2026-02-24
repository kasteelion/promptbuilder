from typing import Any, Dict
from core.app_state import AppState
from logic.character_logic import CharacterLogic

class CharacterController:
    """Manages character-related operations, bridging UI actions to logic and state."""
    
    def __init__(self, state: AppState):
        self.state = state
        self.logic = CharacterLogic(state.ctx, state.state)
        
    def add_character(self, name: str):
        """Standard entry point for adding a character, ensuring data is loaded first."""
        if self.state.ensure_character_loaded(name):
            added = self.logic.toggle_character(name)
            # Sync UI
            self.state.page.page_event = "character_added" # Custom signaling if needed
            return added
        return False

    def remove_character(self, name: str):
        """Defensive toggle."""
        return self.add_character(name)

    def move_character(self, index: int, direction: int):
        self.logic.move_character(index, direction)
        
    def update_character(self, index: int, updates: Dict[str, Any]):
        self.logic.update_character(index, updates)
        
    def get_summary(self, index: int) -> str:
        return self.logic.get_character_summary(index)
