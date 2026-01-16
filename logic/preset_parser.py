"""Parser for scenes, poses, and interaction presets from markdown."""

import re

_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


class PresetParser:
    """Parses scenes, poses, and interactions from markdown content."""

    @staticmethod
    def parse_presets(content: str):
        """Parse preset categories and items from markdown content."""
        presets = {}
        current_cat = "Default"
        presets[current_cat] = {}

        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Category Header: ## Category
            cat_match = re.match(r"^##\s+(.+)$", line)
            if cat_match:
                current_cat = cat_match.group(1).strip()
                presets.setdefault(current_cat, {})
                i += 1
                continue

            # Detailed Header: ### Name (Tags)
            detailed_match = re.match(r"^###\s+([^(]+)(?:\(([^)]+)\))?$", line)
            if detailed_match:
                name = detailed_match.group(1).strip()
                tags_str = detailed_match.group(2) or ""
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                
                # Consume following lines until next header or horizontal rule
                desc_lines = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith("##") or next_line.startswith("---"):
                        break
                    desc_lines.append(next_line)
                    i += 1
                
                full_desc = "\n".join(desc_lines).strip()
                presets[current_cat][name] = {
                    "description": full_desc,
                    "tags": tags
                }
                continue

            # Simple List Item: - **Name** (Tags): Description
            item_match = re.match(r"^-\s+\*\*([^\*]+)\*\*\s*(\([^)]+\))?\s*:\s*(.+)$", line)
            if item_match:
                name = item_match.group(1).strip()
                tags_str = item_match.group(2)
                desc = item_match.group(3).strip()
                
                tags = []
                if tags_str:
                    content_inner = tags_str[1:-1]
                    tags = [t.strip() for t in content_inner.split(",") if t.strip()]

                presets[current_cat][name] = {
                    "description": desc,
                    "tags": tags
                }
                i += 1
                continue

            # Simple List Item Fallback: - **Name:** Description
            simple_match = re.match(r"^-\s+\*\*([^:]+):\*\*\s*(.+)$", line)
            if simple_match:
                name = simple_match.group(1).strip()
                desc = simple_match.group(2).strip()
                presets[current_cat][name] = {
                    "description": desc,
                    "tags": []
                }
                i += 1
                continue

            i += 1

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
                # Match: - **Name** (Tags): Description  OR  - **Name**: Description
                # Also handle **Name:** Description (colon inside bold)
                item = re.match(r"^-\s+\*\*([^\*]+)\*\*\s*(\([^)]+\))?\s*:\s*(.*)$", line)
                item_inside = re.match(r"^-\s+\*\*([^\*]+):\*\*\s*(\([^)]+\))?\s*(.*)$", line)
                
                if item or item_inside:
                    if item:
                        raw_name = item.group(1).strip()
                        tags_str = item.group(2)
                        desc = item.group(3).strip()
                    else:
                        raw_name = item_inside.group(1).strip()
                        tags_str = item_inside.group(2)
                        desc = item_inside.group(3).strip()
                        if desc.startswith(":"): # Handle weird edge case
                             desc = desc[1:].strip()

                    
                    name = raw_name
                    tags = []
                    
                    if tags_str:
                        # Remove parens and split
                        content_inner = tags_str[1:-1]
                        tags = [t.strip() for t in content_inner.split(",") if t.strip()]
                    
                    # Extract min characters from name if present (e.g., "Interaction (2+)")
                    # Note: We need to be careful if title has both tags and count in parens 
                    # But usually format is **Name (2+)** (Tags): 
                    # Let's assume (2+) is part of the name inside **
                    
                    min_chars = 1
                    char_match = re.search(r"\((\d+)\+?\)", name)
                    if char_match:
                        min_chars = int(char_match.group(1))
                    
                    # Also infer from placeholders in description
                    placeholders = re.findall(r"\{char(\d+)\}", desc)
                    if placeholders:
                        max_placeholder = max(int(p) for p in placeholders)
                        min_chars = max(min_chars, max_placeholder)
                    
                    interactions[current][name] = {
                        "description": re.sub(r"^\([^)]+\)\s*", "", desc),
                        "min_chars": min_chars,
                        "tags": tags
                    }

        interactions = {k: v for k, v in interactions.items() if v}
        return interactions
