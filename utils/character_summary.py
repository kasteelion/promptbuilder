#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Character appearance summary script.

This script extracts appearance information (excluding outfits) from character
markdown files and prints a summary.
"""

from pathlib import Path

from .logger import logger


def extract_appearance(file_path, include_base=False):
    """Extract appearance section from a character markdown file.

    Args:
        file_path: Path to the character markdown file

    Returns:
        tuple: (character_name, appearance_text)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract character name from first heading
    lines = content.split("\n")
    character_name = None
    for line in lines:
        if line.startswith("###"):
            character_name = line.replace("###", "").strip()
            break

    if not character_name:
        character_name = Path(file_path).stem.replace("_", " ").title()

    # Extract appearance section (between **Appearance:** and **Outfits:**)
    appearance_start = content.find("**Appearance:**")
    outfits_start = content.find("**Outfits:**")

    if appearance_start == -1:
        appearance_text = "No appearance section found."
    else:
        if outfits_start == -1:
            # If no outfits section, take everything after appearance
            appearance_text = content[appearance_start + len("**Appearance:**") :].strip()
        else:
            # Extract only the appearance section
            appearance_text = content[appearance_start + len("**Appearance:**") : outfits_start].strip()

    # Capture style notes: HTML comment blocks and lines starting with '//' (preserve their content)
    import re

    style_notes_parts = []
    # Find HTML comment blocks inside the appearance section
    for m in re.finditer(r"(?s)<!--\s*(.*?)\s*-->", appearance_text):
        inner = m.group(1).strip()
        if inner:
            style_notes_parts.append(inner)

    # Find lines starting with // and capture their text (without the //)
    for ln in appearance_text.splitlines():
        sm = re.match(r"^\s*//\s?(.*)$", ln)
        if sm:
            style_notes_parts.append(sm.group(1).rstrip())

    style_notes = "\n".join(style_notes_parts).strip() if style_notes_parts else None

    # Normalize style notes: remove duplicate heading lines like "Style notes" or
    # "Style Notes:" that were included in the comment block so we don't print
    # a redundant header when the caller adds a "Style Notes:" label.
    if style_notes:
        sn_lines = style_notes.splitlines()
        if sn_lines:
            first = sn_lines[0].strip()
            import re as _re

            if _re.match(r"(?i)^style\s*notes\b[:\-]?", first):
                # drop the first line which is a heading
                sn_lines = sn_lines[1:]
        # Trim leading/trailing blank lines and rejoin
        style_notes = "\n".join([ln.rstrip() for ln in sn_lines]).strip()

    # Remove HTML comment blocks (legacy) and lines starting with '//' used for style notes
    appearance_text = re.sub(r"(?s)<!--.*?-->", "", appearance_text).strip()
    if appearance_text:
        appearance_lines = [ln for ln in appearance_text.splitlines() if not re.match(r"^\s*//", ln)]
        appearance_text = "\n".join(appearance_lines).strip()

    base_outfit = None
    if include_base and outfits_start != -1:
        # Try to capture the '#### Base' block under outfits
        outfits_block = content[outfits_start:]
        m = re.search(r"####\s+Base\s*(.*?)(?:\n####\s+|\Z)", outfits_block, re.DOTALL)
        if m:
            base_outfit = m.group(1).strip()

    return character_name, appearance_text, base_outfit, style_notes


def generate_summary(characters_dir=None, include_base=False, include_style=False):
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
    md_files = sorted(characters_dir.glob("*.md"))

    if not md_files:
        return "No character files found."

    summary_parts = ["=" * 80, "CHARACTER APPEARANCES SUMMARY", "=" * 80, ""]

    for i, md_file in enumerate(md_files, 1):
        name, appearance, base_outfit, style_notes = extract_appearance(
            md_file, include_base=include_base
        )
        summary_parts.append(f"[{i}] {name}")
        summary_parts.append("-" * 80)
        summary_parts.append(appearance)
        if include_base and base_outfit:
            summary_parts.append("")
            summary_parts.append("Base Outfit:")
            summary_parts.append(base_outfit)
        if include_style and style_notes:
            summary_parts.append("")
            summary_parts.append("Style Notes:")
            summary_parts.append(style_notes)
        summary_parts.append("")

    summary_parts.append("=" * 80)
    summary_parts.append(f"Total Characters: {len(md_files)}")
    summary_parts.append("=" * 80)

    from .text_utils import normalize_blank_lines

    return normalize_blank_lines("\n".join(summary_parts))


def main():
    """Main entry point for the script."""
    summary = generate_summary()
    logger.info(summary)


if __name__ == "__main__":
    main()
