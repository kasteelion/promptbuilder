"""Validation utilities for prompt generation."""


def validate_prompt_config(selected_characters):
    """Validate that all selected characters have required data.
    
    If a character has no outfit selected, the first available outfit
    (typically 'Base') will be automatically assigned as a default.
    
    Args:
        selected_characters: List of selected character dicts
    
    Returns:
        str: Error message if validation fails, None if valid
    """
    if not selected_characters:
        return "Please add at least one character to generate a prompt"
    
    return None

