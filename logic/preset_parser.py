"""Parser for scenes, poses, and interaction presets from markdown."""

import re

_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


class PresetParser:
    """Parses scenes, poses, and interactions from markdown content."""

    @staticmethod
    def parse_presets(content: str):
        """Parse preset categories and items from markdown content."""
        presets = {}
        current = "Default"
        presets[current] = {}

        for line in content.splitlines():
            cat = re.match(r"^##\s+(.+)$", line)
            if cat:
                current = cat.group(1).strip()
                presets.setdefault(current, {})
                continue

            # Match: - **Name** (Tag1, Tag2): Description
            # Group 1: Name
            # Group 2: (Tags) - Optional
            # Group 3: Description
            item = re.match(r"^-\s+\*\*([^\*]+)\*\*\s*(\([^)]+\))?\s*:\s*(.+)$", line)
            
            # Fallback for old format without colon if needed, or stricter?
            # Existing regex was: r"^-\s+\*\*([^:]+):\*\*\s*(.+)$"
            
            if item:
                name = item.group(1).strip()
                tags_str = item.group(2)
                desc = item.group(3).strip()
                
                tags = []
                if tags_str:
                    # Remove parens and split
                    content_inner = tags_str[1:-1]
                    tags = [t.strip() for t in content_inner.split(",") if t.strip()]

                presets.setdefault(current, {})[name] = {
                    "description": desc,
                    "tags": tags
                }
            else:
                # Try fallback for "Name: Description" without tags if strict regex failed
                # (The previous regex handled Name: Description)
                simple_item = re.match(r"^-\s+\*\*([^:]+):\*\*\s*(.+)$", line)
                if simple_item and not item:
                    name = simple_item.group(1).strip()
                    desc = simple_item.group(2).strip()
                    presets.setdefault(current, {})[name] = {
                        "description": desc,
                        "tags": []
                    }

        return presets

    @staticmethod
    def parse_interactions(content: str):
        """Parse interaction templates from markdown content with categories.
        
        Extracts character count requirements from names like "Interaction (2+)".
        
        Returns:
            dict: {category: {name: {'description': str, 'min_chars': int}}}
        """
        interactions = {}
        current = None

        for line in content.splitlines():
            cat = re.match(r"^##\s+(.+)$", line)
            if cat:
                current = cat.group(1).strip()
                if current.lower() == "notes":
                    current = None
                    continue
                interactions.setdefault(current, {})
                continue

            if current:
                item = re.match(r"^-\s+\*\*([^:]+):\*\*\s*(.*)$", line)
                if item:
                    name = item.group(1).strip()
                    desc = item.group(2).strip()
                    
                    # Extract min characters from name if present (e.g., "(2+)" or "(3)")
                    min_chars = 1
                    char_match = re.search(r"\((\d+)\+?\)", name)
                    if char_match:
                        min_chars = int(char_match.group(1))
                    
                    # Also infer from placeholders in description (e.g. {char3} -> needs 3)
                    # Find all {charN} patterns
                    placeholders = re.findall(r"\{char(\d+)\}", desc)
                    if placeholders:
                        max_placeholder = max(int(p) for p in placeholders)
                        min_chars = max(min_chars, max_placeholder)
                    
                    # Store as structured dict
                    interactions[current][name] = {
                        "description": re.sub(r"^\([^)]+\)\s*", "", desc),
                        "min_chars": min_chars
                    }

        interactions = {k: v for k, v in interactions.items() if v}
        return interactions
