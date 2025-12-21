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

            item = re.match(r"^-\s+\*\*([^:]+):\*\*\s*(.+)$", line)
            if item:
                name = item.group(1).strip()
                desc = item.group(2).strip()
                presets.setdefault(current, {})[name] = desc

        return presets

    @staticmethod
    def parse_interactions(content: str):
        """Parse interaction templates from markdown content with categories."""
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
                    desc = re.sub(r"^\([^)]+\)\s*", "", desc)
                    interactions[current][name] = desc

        interactions = {k: v for k, v in interactions.items() if v}
        return interactions
