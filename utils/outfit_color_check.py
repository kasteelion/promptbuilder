import re
from utils.color_scheme import parse_color_schemes

def outfit_has_color_vars(outfit_text: str) -> bool:
    """Return True if outfit text contains {primary_color} or {secondary_color}."""
    return bool(re.search(r"\{primary_color\}|\{secondary_color\}", outfit_text))

# Usage example:
# if outfit_has_color_vars(outfit_text):
#     # Show color scheme dropdown
