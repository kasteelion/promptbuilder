"""Parser for base prompts and color schemes from markdown."""

import re


class StyleParser:
    """Parses base style prompts and color schemes from markdown content."""

    @staticmethod
    def parse_base_prompts(content: str):
        """Parse base style prompts from markdown content."""
        prompts = {}
        parts = re.split(r"^##\s+(.+)$", content, flags=re.MULTILINE)
        for i in range(1, len(parts), 2):
            name = parts[i].strip()
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            body = re.sub(r"\n*---\s*$", "", body).strip()
            prompts[name] = body
        return prompts

    @staticmethod
    def parse_color_schemes(content: str):
        """Parse color schemes from markdown content."""
        schemes = {}
        current = None
        colors = {}

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("## "):
                if current:
                    schemes[current] = colors
                current = line[3:].strip()
                colors = {}
            elif line.startswith("- **primary:**"):
                colors["primary_color"] = line.split("**primary:**", 1)[1].strip()
            elif line.startswith("- **secondary:**"):
                colors["secondary_color"] = line.split("**secondary:**", 1)[1].strip()
            elif line.startswith("- **accent:**"):
                colors["accent"] = line.split("**accent:**", 1)[1].strip()
            elif line.startswith("- **team:**"):
                colors["team"] = line.split("**team:**", 1)[1].strip()

        if current:
            schemes[current] = colors

        return schemes
