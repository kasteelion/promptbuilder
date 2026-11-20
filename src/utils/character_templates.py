"""Character templates for quick character creation.
Now loaded from assets/character_templates.json to reduce code bloat.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

# Base path relative to this file (src/utils/character_templates.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_PATH = os.path.join(BASE_DIR, "assets", "character_templates.json")

def _load_templates():
    if not os.path.exists(TEMPLATES_PATH):
        # Fallback to empty if file missing
        return {}
    try:
        with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load character templates from {TEMPLATES_PATH}: {e}")
        return {}

# Load templates once at module level for performance/compatibility
TEMPLATES = _load_templates()

def get_template_names():
    """Get list of template names for dropdown."""
    return list(TEMPLATES.keys())

def get_template(name):
    """Get template data by name.

    Args:
        name: Template name

    Returns:
        Dict with 'appearance' and 'outfit' keys, or None if not found
    """
    return TEMPLATES.get(name)

def get_template_description(name):
    """Get template description.

    Args:
        name: Template name

    Returns:
        Description string or empty string if not found
    """
    template = TEMPLATES.get(name)
    return template.get("description", "") if template else ""
