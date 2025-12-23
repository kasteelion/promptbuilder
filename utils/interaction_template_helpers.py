"""Interaction templates for quick interaction creation."""

TEMPLATES = {
    "Blank": {"description": "Start from scratch", "content": ""},
    "Conversation": {
        "description": "Two characters talking",
        "content": "{char1} engaged in conversation with {char2}, both looking at each other with friendly expressions",
    },
    "Walking Together": {
        "description": "Two characters walking side-by-side",
        "content": "{char1} and {char2} walking side-by-side along a path, relaxed pace, casual atmosphere",
    },
    "Group Discussion": {
        "description": "Three characters talking in a group",
        "content": "{char1}, {char2}, and {char3} standing in a circle, engaged in an animated group discussion",
    },
    "Sharing a Drink": {
        "description": "Two characters having drinks",
        "content": "{char1} and {char2} sitting at a table sharing drinks, relaxed and happy expressions",
    },
    "Portrait Pose": {
        "description": "Two characters posing for a photo",
        "content": "{char1} and {char2} posing together for a portrait, looking towards the camera with smiles",
    },
    "Teaching": {
        "description": "One character teaching another",
        "content": "{char1} showing something to {char2}, teaching and explaining, {char2} listening attentively",
    },
}


def get_interaction_template_names():
    """Get list of template names for dropdown."""
    return list(TEMPLATES.keys())


def get_interaction_template(name):
    """Get template content by name.

    Args:
        name: Template name

    Returns:
        Content string, or empty string if not found
    """
    template = TEMPLATES.get(name)
    return template.get("content", "") if template else ""


def get_interaction_template_description(name):
    """Get template description.

    Args:
        name: Template name

    Returns:
        Description string or empty string if not found
    """
    template = TEMPLATES.get(name)
    return template.get("description", "") if template else ""
