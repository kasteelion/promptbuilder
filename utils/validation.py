# -*- coding: utf-8 -*-
"""Input validation utilities."""

import re
from pathlib import Path
from typing import Optional, Tuple


def validate_character_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate a character name.
    
    Args:
        name: Character name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Character name cannot be empty"
    
    if len(name) > 100:
        return False, "Character name too long (max 100 characters)"
    
    # Check for invalid characters
    if re.search(r'[<>:"/\\|?*]', name):
        return False, "Character name contains invalid characters"
    
    return True, None


def validate_text_length(text: str, max_length: int = 10000, field_name: str = "Text") -> Tuple[bool, Optional[str]]:
    """Validate text length.
    
    Args:
        text: Text to validate
        max_length: Maximum allowed length
        field_name: Name of field for error messages
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(text) > max_length:
        return False, f"{field_name} too long (max {max_length} characters)"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing dangerous characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and parent directory references
    safe_name = filename.replace('/', '').replace('\\', '').replace('..', '')
    
    # Remove other dangerous characters
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
    
    # Replace spaces with underscores
    safe_name = safe_name.replace(' ', '_')
    
    # Ensure not empty
    if not safe_name:
        safe_name = "untitled"
    
    return safe_name


def validate_file_path(filepath: Path, allowed_dir: Path) -> Tuple[bool, Optional[str]]:
    """Validate that a file path is within an allowed directory.
    
    Args:
        filepath: Path to validate
        allowed_dir: Allowed parent directory
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Resolve to absolute paths
        abs_filepath = filepath.resolve()
        abs_allowed = allowed_dir.resolve()
        
        # Check if filepath is within allowed_dir
        if not str(abs_filepath).startswith(str(abs_allowed)):
            return False, "Path is outside allowed directory"
        
        return True, None
    except Exception as e:
        from utils import logger
        logger.exception('Auto-captured exception')
        return False, f"Invalid path: {e}"


def validate_preset_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate a preset name.
    
    Args:
        name: Preset name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Preset name cannot be empty"
    
    if len(name) > 50:
        return False, "Preset name too long (max 50 characters)"
    
    # Check for invalid filename characters
    if re.search(r'[<>:"/\\|?*]', name):
        return False, "Preset name contains invalid characters"
    
    return True, None
