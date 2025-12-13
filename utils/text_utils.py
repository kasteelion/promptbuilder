#!/usr/bin/env python3
"""Simple text utilities for normalizing generated prompt and summary text."""
import re


def normalize_blank_lines(text: str) -> str:
    """Normalize blank lines and trailing spaces in a text blob.

    - Converts CRLF to LF
    - Strips trailing whitespace on each line
    - Collapses 3+ consecutive newlines down to exactly two (single blank line)
    - Strips leading/trailing blank lines

    Returns normalized text.
    """
    if text is None:
        return ""

    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Trim end-of-line whitespace
    lines = [ln.rstrip() for ln in text.split("\n")]
    text = "\n".join(lines)

    # Collapse runs of 3+ newlines into two newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing blank lines and whitespace
    return text.strip()
