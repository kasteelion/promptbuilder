"""Markdown parsing utilities for character, prompt, and preset data.

This module acts as a facade, delegating to specialized parser classes
for better maintainability and separation of concerns.
"""

from .character_parser import CharacterParser
from .outfit_parser import OutfitParser
from .preset_parser import PresetParser
from .style_parser import StyleParser


class MarkdownParser(CharacterParser, OutfitParser, PresetParser, StyleParser):
    """Parses markdown files for characters, base prompts, and presets.

    Inherits from specialized parsers to maintain backward compatibility
    while organizing logic into separate classes.
    """
    pass