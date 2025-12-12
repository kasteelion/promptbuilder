"""Helper functions for interaction templates."""


def fill_template(template_text: str, characters: list) -> str:
    """Fill interaction template with character names.
    
    Args:
        template_text: Template string with {char1}, {char2}, etc. placeholders
        characters: List of character names in order
        
    Returns:
        Template with placeholders replaced by character names
        
    Examples:
        >>> fill_template("{char1} talking with {char2}", ["Alice", "Bob"])
        "Alice talking with Bob"
        
        >>> fill_template("{char1}, {char2}, and {char3} standing", ["Alice", "Bob", "Carol"])
        "Alice, Bob, and Carol standing"
    """
    if not template_text or not characters:
        return template_text
    
    result = template_text
    for i, char_name in enumerate(characters, start=1):
        placeholder = f"{{char{i}}}"
        result = result.replace(placeholder, char_name)
    
    return result
