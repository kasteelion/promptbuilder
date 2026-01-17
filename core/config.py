"""Configuration constants for the Prompt Builder application.

Note: UI-specific constants have been moved to ui/constants.py
"""

# File paths
# NOTE: Character files are loaded dynamically from the characters/ folder.
# These are the main data files that can be edited through the UI.
# MAIN_EDITABLE_FILES has been deprecated in favor of dynamic discovery in DataLoader.


# Default theme
DEFAULT_THEME = "Dark"

# Fonts
DEFAULT_FONT_FAMILY = "Lexend" # Prioritize custom font
DEFAULT_FONT_SIZE = 10

# Theme definitions
# Theme definitions
THEMES = {
    "Light": {
        "bg": "#f0f0f0",
        "fg": "#1a1a1a",
        "panel_bg": "#f8f8f8",
        "preview_bg": "#ffffff",
        "preview_fg": "#2c2c2c",
        "text_bg": "#ffffff",
        "text_fg": "#2c2c2c",
        "accent": "#0066cc",
        "accent_hover": "#004c99",
        "border": "#cccccc",
        "selected_bg": "#e3f2fd",
    },
    "Dark": {
        "bg": "#1e1e1e",
        "fg": "#d4d4d4",
        "panel_bg": "#252526",
        "preview_bg": "#252526",
        "preview_fg": "#e0e0e0",
        "text_bg": "#2d2d2d",
        "text_fg": "#d4d4d4",
        "accent": "#0e639c",
        "accent_hover": "#1177bb",
        "border": "#3c3c3c",
        "selected_bg": "#2d3e50",
    },
    "High Contrast": {
        "bg": "#000000",
        "fg": "#ffffff",
        "panel_bg": "#111111",
        "preview_bg": "#000000",
        "preview_fg": "#ffffff",
        "text_bg": "#000000",
        "text_fg": "#ffffff",
        "accent": "#ffff00",
        "accent_hover": "#ffea00",
        "border": "#ffffff",
        "selected_bg": "#333333",
    },
}

DEFAULT_THEME = "Dark"

# Preferences settings
# Moved out of UI module so non-UI code can import this without importing tkinter
MAX_RECENT_ITEMS = 10  # Maximum recent items stored in preferences

# Tooltip help text
TOOLTIPS = {
    "base_prompt": "The base art style that defines the overall look and technique of the image (e.g., 'Anime style', 'Photorealistic', etc.)",
    "bulk_outfit": "Quickly apply the same outfit to multiple characters at once. Shared outfits are organized by modifiers in `outfits_*.md` (e.g., F, M, H).",
    "character": "Add a character to your prompt. Each character can have different outfits and poses",
    "scene": "Describe the environment, setting, location, lighting, and background details",
    "notes": "Additional details, modifications, or special instructions for the AI",
    "outfit": "Change what the character is wearing. Each character may have different outfit options",
    "pose": "Select a preset pose or leave empty. Can be overridden by Custom Pose/Action below",
    "action_note": "Describe specific actions, poses, or expressions for this character. Overrides pose preset",
    "randomize": "Generate a random prompt with random characters, outfits, poses, scene, and notes",
    "reload": "Reload all data from markdown files. Use this after editing character or preset files",
    "copy": "Copy the entire prompt to clipboard for pasting into AI image generators",
    "save": "Save the prompt to a text file",
    "preview": "Live preview of your generated prompt. Updates automatically as you make changes",
}

# Welcome message for first-time users
WELCOME_MESSAGE = """Welcome to Prompt Builder! 🎨

Get started by:
1. Select a Base Prompt (art style)
2. Add Characters using the dropdown
3. Customize their Outfits and Poses
4. Add a Scene description
5. Add any Notes for extra details

Your prompt will appear here as you build it.

💡 Tips:
• Use Ctrl+Z/Y for undo/redo
• Press Alt+R to randomize everything
• Right-click characters for quick actions
• Star ★ your favorite items for quick access

Need help? Hover over any element for tooltips!
"""
