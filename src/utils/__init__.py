# -*- coding: utf-8 -*-
"""Utility modules for Prompt Builder."""

from .character_templates import get_template as get_character_template
from .character_templates import get_template_description as get_character_template_description
from .character_templates import get_template_names as get_character_template_names
from .file_ops import atomic_write, create_backup, safe_read
from .logger import logger, setup_logger
from .outfit_templates import get_template as get_outfit_template
from .outfit_templates import get_template_description as get_outfit_template_description
from .outfit_templates import get_template_names as get_outfit_template_names
from .pose_templates import get_template as get_pose_template
from .pose_templates import get_template_description as get_pose_template_description
from .pose_templates import get_template_names as get_pose_template_names
from .preferences import PreferencesManager
from .preset_manager import PresetManager
from .scene_templates import get_template as get_scene_template
from .scene_templates import get_template_description as get_scene_template_description
from .scene_templates import get_template_names as get_scene_template_names
from .style_templates import get_template as get_style_template
from .style_templates import get_template_description as get_style_template_description
from .style_templates import get_template_names as get_style_template_names
from .tooltip import create_tooltip
from .undo_manager import UndoManager
from .validation import (
    sanitize_filename,
    validate_character_name,
    validate_file_path,
    validate_preset_name,
    validate_text_length,
)

__all__ = [
    "UndoManager",
    "PreferencesManager",
    "create_tooltip",
    "PresetManager",
    "logger",
    "setup_logger",
    "atomic_write",
    "safe_read",
    "create_backup",
    "validate_character_name",
    "validate_text_length",
    "sanitize_filename",
    "validate_file_path",
    "validate_preset_name",
    # Character templates
    "get_character_template_names",
    "get_character_template",
    "get_character_template_description",
    # Outfit templates
    "get_outfit_template_names",
    "get_outfit_template",
    "get_outfit_template_description",
    # Scene templates
    "get_scene_template_names",
    "get_scene_template",
    "get_scene_template_description",
    # Pose templates
    "get_pose_template_names",
    "get_pose_template",
    "get_pose_template_description",
    # Style templates
    "get_style_template_names",
    "get_style_template",
    "get_style_template_description",
]
