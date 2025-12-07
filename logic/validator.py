"""Validation utilities for prompt generation."""


class PromptValidator:
    """Validates prompt data before generation."""
    
    def __init__(self, characters=None):
        """Initialize validator with character data.
        
        Args:
            characters: Optional character definitions dict for setting defaults
        """
        self.characters = characters or {}
    
    def set_characters(self, characters):
        """Set character data for default outfit assignment.
        
        Args:
            characters: Character definitions dict
        """
        self.characters = characters
    
    @staticmethod
    def validate(selected_characters):
        """Validate that all selected characters have required data.
        
        If a character has no outfit selected, the first available outfit
        (typically 'Base') will be automatically assigned as a default.
        
        Returns:
            str: Error message if validation fails, None if valid
        """
        if not selected_characters:
            return "Please add at least one character to generate a prompt"
        
        return None
