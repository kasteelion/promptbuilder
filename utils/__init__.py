# -*- coding: utf-8 -*-
"""Utility modules for Prompt Builder."""

from .undo_manager import UndoManager
from .preferences import PreferencesManager
from .tooltip import create_tooltip
from .preset_manager import PresetManager
from .character_templates import (
    get_template_names as get_character_template_names,
    get_template as get_character_template,
    get_template_description as get_character_template_description
)
from .scene_templates import (
    get_template_names as get_scene_template_names,
    get_template as get_scene_template,
    get_template_description as get_scene_template_description
)
from .pose_templates import (
    get_template_names as get_pose_template_names,
    get_template as get_pose_template,
    get_template_description as get_pose_template_description
)
from .style_templates import (
    get_template_names as get_style_template_names,
    get_template as get_style_template,
    get_template_description as get_style_template_description
)

__all__ = [
    'UndoManager', 
    'PreferencesManager', 
    'create_tooltip', 
    'PresetManager',
    # Character templates
    'get_character_template_names',
    'get_character_template',
    'get_character_template_description',
    # Scene templates
    'get_scene_template_names',
    'get_scene_template',
    'get_scene_template_description',
    # Pose templates
    'get_pose_template_names',
    'get_pose_template',
    'get_pose_template_description',
    # Style templates
    'get_style_template_names',
    'get_style_template',
    'get_style_template_description'
]
