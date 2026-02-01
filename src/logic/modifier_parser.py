"""Parser for outfit modifiers from markdown."""

import re
from typing import Dict

# Pre-compile regex patterns
_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)

class ModifierParser:
    """Parses outfit modifiers from markdown content."""

    @staticmethod
    def parse_modifiers(content: str) -> Dict[str, str]:
        """Parse outfit modifiers from modifiers.md."""
        modifiers = {}
        current_modifier = None
        
        for line in content.splitlines():
            line = line.strip()
            section_match = _SECTION_RE.match(line)
            if section_match:
                current_modifier = section_match.group(1).strip()
                continue
                
            if current_modifier and line.startswith("- **text:**"):
                text = line.split("**text:**", 1)[1].strip()
                modifiers[current_modifier] = text
                
        return modifiers
