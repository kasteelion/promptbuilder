import re
from pathlib import Path
from typing import Dict, Optional

def parse_color_schemes(filepath: str) -> Dict[str, Dict[str, str]]:
    """Parse color_schemes.md into a dictionary of schemes."""
    schemes = {}
    current = None
    colors = {}
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                if current:
                    schemes[current] = colors
                current = line[3:]
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

def substitute_colors(text: str, scheme: Dict[str, str]) -> str:
    """Substitute {primary_color}, {secondary_color}, {accent} in text."""
    for key, value in scheme.items():
        text = re.sub(r"\{" + key + r"\}", value, text)
    return text

# Example usage:
if __name__ == "__main__":
    schemes = parse_color_schemes("data/color_schemes.md")
    sample_text = "Jersey in {primary_color} with {secondary_color} accents, shoes {accent}."
    print(substitute_colors(sample_text, schemes["UCLA"]))
