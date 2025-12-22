import re
from utils.color_scheme import parse_color_schemes

def outfit_has_color_vars(outfit_text: str) -> bool:
    """Return True if outfit text contains color scheme placeholders."""
    return bool(re.search(r"\{primary_color\}|\{secondary_color\}|\{accent\}|\{team\}", outfit_text))

# Usage example:
# if outfit_has_color_vars(outfit_text):
#     # Show color scheme dropdown
