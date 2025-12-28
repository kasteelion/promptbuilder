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


def substitute_signature_color(text: str, signature_color: str, use_signature: bool) -> str:
    """Substitute conditional signature color blocks and standalone tags.
    
    Syntax 1: ((default:white) or (signature)) 
              Uses character sig color if active, else 'white'.
    Syntax 2: ((default:white) or (signature) text)
              Uses character sig color + ' text' if active, else 'white'.
    Syntax 3: {signature_color}
              Uses character sig color if active, else 'vibrant color'.
    """
    # 1. Handle conditional block syntax
    # Allow optional text after (signature) before the closing paren
    pattern = re.compile(r"\(\(default:(.*?)\)\s+or\s+\(signature\)(.*?)\)", re.IGNORECASE)
    
    def replacer(match):
        default_val = match.group(1).strip()
        sig_suffix = match.group(2) # preserve spacing if present
        
        if use_signature and signature_color:
            return signature_color + sig_suffix
        return default_val
        
    text = pattern.sub(replacer, text)

    # 2. Handle standalone placeholder syntax
    if "{signature_color}" in text:
        replacement = signature_color if (use_signature and signature_color) else "vibrant color"
        text = text.replace("{signature_color}", replacement)
        
    return text


# Example usage:
if __name__ == "__main__":
    schemes = parse_color_schemes("data/color_schemes.md")
    sample_text = "Jersey in {primary_color} with {secondary_color} accents, shoes {accent}."
    print(substitute_colors(sample_text, schemes["UCLA"]))
