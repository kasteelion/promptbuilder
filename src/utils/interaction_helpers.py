"""Helper functions for interaction templates."""


def fill_template(template_text: str | dict, characters: list) -> str:
    """Fill interaction template with character names.

    Args:
        template_text: Template string with {char1}, {char2}, etc. placeholders,
                      or a dictionary containing 'description'.
        characters: List of character names in order

    Returns:
        Template with placeholders replaced by character names
    """
    # Handle structured dictionary format if passed
    if isinstance(template_text, dict):
        template_text = template_text.get("description", "")

    if not template_text or not characters:
        return template_text or ""

    result = str(template_text)
    for i, char_name in enumerate(characters, start=1):
        placeholder = f"{{char{i}}}"
        result = result.replace(placeholder, char_name)

    return result
