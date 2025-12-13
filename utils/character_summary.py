#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Character appearance summary script.

This script extracts appearance information (excluding outfits) from character
markdown files and prints a summary.
"""

from pathlib import Path
from .logger import logger


def extract_appearance(file_path):
    """Extract appearance section from a character markdown file.
    
    Args:
        file_path: Path to the character markdown file
        
    Returns:
        tuple: (character_name, appearance_text)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract character name from first heading
    lines = content.split('\n')
    character_name = None
    for line in lines:
        if line.startswith('###'):
            character_name = line.replace('###', '').strip()
            break
    
    if not character_name:
        character_name = Path(file_path).stem.replace('_', ' ').title()
    
    # Extract appearance section (between **Appearance:** and **Outfits:**)
    appearance_start = content.find('**Appearance:**')
    outfits_start = content.find('**Outfits:**')
    
    if appearance_start == -1:
        return character_name, "No appearance section found."
    
    if outfits_start == -1:
        # If no outfits section, take everything after appearance
        appearance_text = content[appearance_start + len('**Appearance:**'):].strip()
    else:
        # Extract only the appearance section
        appearance_text = content[appearance_start + len('**Appearance:**'):outfits_start].strip()
    
    return character_name, appearance_text


def generate_summary(characters_dir=None):
    """Generate a summary of all character appearances.
    
    Args:
        characters_dir: Path to characters directory (defaults to script directory)
        
    Returns:
        str: Formatted summary of all characters
    """
    if characters_dir is None:
        characters_dir = Path(__file__).parent
    else:
        characters_dir = Path(characters_dir)
    
    # Find all markdown files
    md_files = sorted(characters_dir.glob('*.md'))
    
    if not md_files:
        return "No character files found."
    
    summary_parts = [
        "=" * 80,
        "CHARACTER APPEARANCES SUMMARY",
        "=" * 80,
        ""
    ]
    
    for i, md_file in enumerate(md_files, 1):
        name, appearance = extract_appearance(md_file)
        summary_parts.append(f"[{i}] {name}")
        summary_parts.append("-" * 80)
        summary_parts.append(appearance)
        summary_parts.append("")
    
    summary_parts.append("=" * 80)
    summary_parts.append(f"Total Characters: {len(md_files)}")
    summary_parts.append("=" * 80)
    
    return '\n'.join(summary_parts)


def main():
    """Main entry point for the script."""
    summary = generate_summary()
    logger.info(summary)


if __name__ == '__main__':
    main()
