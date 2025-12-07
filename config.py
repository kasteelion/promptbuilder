"""Configuration constants for the Prompt Builder application."""

# Font settings
DEFAULT_FONT_FAMILY = "Consolas"
DEFAULT_FONT_SIZE = 12

# UI settings
PREVIEW_UPDATE_THROTTLE_MS = 200
DEFAULT_WINDOW_GEOMETRY = "1000x700"

# File paths
# NOTE: Character files are loaded dynamically from the characters/ folder.
# These are the main data files that can be edited through the UI.
MAIN_EDITABLE_FILES = ["base_prompts.md", "scenes.md", "poses.md", "outfits.md"]

# For backwards compatibility, include characters.md if it exists
def get_editable_files():
    """Get list of editable files, including character files from characters/ folder if they exist."""
    from pathlib import Path
    import os
    
    files = list(MAIN_EDITABLE_FILES)
    
    # Check for character files in characters/ folder
    char_dir = Path(__file__).parent / "characters"
    if char_dir.exists() and char_dir.is_dir():
        char_files = sorted([f.name for f in char_dir.glob("*.md")])
        files.extend(char_files)
    
    # Check for legacy characters.md in root
    root_char = Path(__file__).parent / "characters.md"
    if root_char.exists() and "characters.md" not in files:
        files.append("characters.md")
    
    return files

EDITABLE_FILES = get_editable_files()

# Theme definitions
THEMES = {
    "Light": {
        "bg": "#f5f5f5",
        "fg": "#2c2c2c",
        "preview_bg": "#ffffff",
        "preview_fg": "#1a1a1a",
        "text_bg": "#ffffff",
        "text_fg": "#2c2c2c",
        "accent": "#0078d4",
        "border": "#d0d0d0"
    },
    "Dark": {
        "bg": "#1e1e1e",
        "fg": "#e0e0e0",
        "preview_bg": "#252526",
        "preview_fg": "#d4d4d4",
        "text_bg": "#2d2d2d",
        "text_fg": "#e0e0e0",
        "accent": "#0e639c",
        "border": "#3c3c3c"
    },
    "Modern Dark": {
        "bg": "#2c3e50",
        "fg": "#ecf0f1",
        "preview_bg": "#34495e",
        "preview_fg": "#ecf0f1",
        "text_bg": "#34495e",
        "text_fg": "#ecf0f1",
        "accent": "#3498db",
        "border": "#2c3e50"
    },
    "Monokai": {
        "bg": "#272822",
        "fg": "#f8f8f2",
        "preview_bg": "#1e1f1c",
        "preview_fg": "#f8f8f2",
        "text_bg": "#3e3d32",
        "text_fg": "#f8f8f2",
        "accent": "#66d9ef",
        "border": "#49483e"
    },
    "Solarized Dark": {
        "bg": "#002b36",
        "fg": "#839496",
        "preview_bg": "#073642",
        "preview_fg": "#93a1a1",
        "text_bg": "#073642",
        "text_fg": "#839496",
        "accent": "#268bd2",
        "border": "#586e75"
    },
    "Nord": {
        "bg": "#2e3440",
        "fg": "#d8dee9",
        "preview_bg": "#3b4252",
        "preview_fg": "#eceff4",
        "text_bg": "#3b4252",
        "text_fg": "#d8dee9",
        "accent": "#88c0d0",
        "border": "#4c566a"
    },
    "Dracula": {
        "bg": "#282a36",
        "fg": "#f8f8f2",
        "preview_bg": "#21222c",
        "preview_fg": "#f8f8f2",
        "text_bg": "#44475a",
        "text_fg": "#f8f8f2",
        "accent": "#bd93f9",
        "border": "#6272a4"
    }
}

DEFAULT_THEME = "Dark"
