"""Validation utilities for prompt generation."""


def validate_prompt_config(selected_characters, ctx=None):
    """Validate that all selected characters have required data.

    Args:
        selected_characters: List of SelectedCharacterConfig objects
        ctx: Application context AppContext

    Returns:
        str: Error message if validation fails, None if valid
    """
    if not selected_characters:
        return "Please add at least one character to generate a prompt"

    if ctx:
        for char in selected_characters:
            name = getattr(char, "name", char.get("name") if isinstance(char, dict) else "")
            if name not in ctx.characters:
                return f"Character '{name}' is in roster but its data isn't loaded."

            outfit = getattr(char, "outfit", char.get("outfit") if isinstance(char, dict) else "")
            if not outfit:
                return f"Character '{name}' has no outfit selected."

            pose_cat = getattr(char, "pose_category", char.get("pose_category") if isinstance(char, dict) else "")
            pose_pre = getattr(char, "pose_preset", char.get("pose_preset") if isinstance(char, dict) else "")
            action = getattr(char, "action_note", char.get("action_note") if isinstance(char, dict) else "")
            
            # Need either an action override or a valid preset
            if not action and pose_cat and pose_pre:
                if pose_cat not in ctx.poses or pose_pre not in ctx.poses[pose_cat]:
                    return f"Character '{name}' has invalid pose preset: '{pose_cat} -> {pose_pre}'"

    return None
