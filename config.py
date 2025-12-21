"""Configuration constants for the Prompt Builder application.

Note: UI-specific constants have been moved to ui/constants.py
"""

# File paths
# NOTE: Character files are loaded dynamically from the characters/ folder.
# These are the main data files that can be edited through the UI.
MAIN_EDITABLE_FILES = ["base_prompts.md", "scenes.md", "poses.md", "outfits_f.md", "outfits_m.md"]

# Default theme
DEFAULT_THEME = "Light"

# Theme definitions
THEMES = {
    "Light": {
        "bg": "#f0f0f0",
        "fg": "#1a1a1a",
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
        "preview_bg": "#252526",
        "preview_fg": "#e0e0e0",
        "text_bg": "#2d2d2d",
        "text_fg": "#d4d4d4",
        "accent": "#0e639c",
        "accent_hover": "#1177bb",
        "border": "#3c3c3c",
        "selected_bg": "#2d3e50",
    },
    "Monokai": {
        "bg": "#272822",
        "fg": "#f8f8f2",
        "preview_bg": "#1e1f1c",
        "preview_fg": "#f8f8f2",
        "text_bg": "#3e3d32",
        "text_fg": "#f8f8f2",
        "accent": "#66d9ef",
        "accent_hover": "#89e4f7",
        "border": "#49483e",
        "selected_bg": "#49483e",
    },
    "Nord": {
        "bg": "#2e3440",
        "fg": "#d8dee9",
        "preview_bg": "#3b4252",
        "preview_fg": "#eceff4",
        "text_bg": "#3b4252",
        "text_fg": "#d8dee9",
        "accent": "#88c0d0",
        "accent_hover": "#8fbcbb",
        "border": "#4c566a",
        "selected_bg": "#434c5e",
    },
    "Dracula": {
        "bg": "#282a36",
        "fg": "#f8f8f2",
        "preview_bg": "#21222c",
        "preview_fg": "#f8f8f2",
        "text_bg": "#44475a",
        "text_fg": "#f8f8f2",
        "accent": "#bd93f9",
        "accent_hover": "#caa6fc",
        "border": "#6272a4",
        "selected_bg": "#44475a",
    },
    "Gruvbox Dark": {
        "bg": "#282828",
        "fg": "#ebdbb2",
        "preview_bg": "#1d2021",
        "preview_fg": "#ebdbb2",
        "text_bg": "#3c3836",
        "text_fg": "#ebdbb2",
        "accent": "#83a598",
        "accent_hover": "#a89984",
        "border": "#504945",
        "selected_bg": "#504945",
    },
    "One Dark": {
        "bg": "#282c34",
        "fg": "#abb2bf",
        "preview_bg": "#21252b",
        "preview_fg": "#abb2bf",
        "text_bg": "#2c313a",
        "text_fg": "#abb2bf",
        "accent": "#61afef",
        "accent_hover": "#84c0f4",
        "border": "#3e4451",
        "selected_bg": "#3e4451",
    },
    "Tokyo Night": {
        "bg": "#1a1b26",
        "fg": "#a9b1d6",
        "preview_bg": "#16161e",
        "preview_fg": "#c0caf5",
        "text_bg": "#24283b",
        "text_fg": "#a9b1d6",
        "accent": "#7aa2f7",
        "accent_hover": "#9db3f5",
        "border": "#414868",
        "selected_bg": "#292e42",
    },
    "Solarized Light": {
        "bg": "#fdf6e3",
        "fg": "#657b83",
        "preview_bg": "#eee8d5",
        "preview_fg": "#586e75",
        "text_bg": "#ffffff",
        "text_fg": "#586e75",
        "accent": "#268bd2",
        "accent_hover": "#0b6fa4",
        "border": "#93a1a1",
        "selected_bg": "#eee8d5",
    },
    "Solarized Dark": {
        "bg": "#002b36",
        "fg": "#839496",
        "preview_bg": "#073642",
        "preview_fg": "#93a1a1",
        "text_bg": "#002b36",
        "text_fg": "#93a1a1",
        "accent": "#b58900",
        "accent_hover": "#d29922",
        "border": "#073642",
        "selected_bg": "#073642",
    },
    "Sepia": {
        "bg": "#f4ecd8",
        "fg": "#5b4636",
        "preview_bg": "#f6eee1",
        "preview_fg": "#5b4636",
        "text_bg": "#fbf6ee",
        "text_fg": "#5b4636",
        "accent": "#b57f50",
        "accent_hover": "#9c5f2f",
        "border": "#d7c9b1",
        "selected_bg": "#efe6d1",
    },
    "High Contrast": {
        "bg": "#000000",
        "fg": "#ffffff",
        "preview_bg": "#000000",
        "preview_fg": "#ffffff",
        "text_bg": "#000000",
        "text_fg": "#ffffff",
        "accent": "#ffff00",
        "accent_hover": "#ffea00",
        "border": "#ffffff",
        "selected_bg": "#333333",
    },
    "Pastel": {
        "bg": "#fffaf0",
        "fg": "#3b3a3a",
        "preview_bg": "#fff8f2",
        "preview_fg": "#3b3a3a",
        "text_bg": "#fffaf0",
        "text_fg": "#3b3a3a",
        "accent": "#ff9a9e",
        "accent_hover": "#ffb3b8",
        "border": "#f2e9e9",
        "selected_bg": "#fff1f2",
    },
    "Midnight Blue": {
        "bg": "#0b1b2b",
        "fg": "#cfe8ff",
        "preview_bg": "#071426",
        "preview_fg": "#bcdff6",
        "text_bg": "#0f2a44",
        "text_fg": "#cfe8ff",
        "accent": "#4aa3ff",
        "accent_hover": "#66b8ff",
        "border": "#12324a",
        "selected_bg": "#0f3a55",
    },
    "Packers Dark": {
        "bg": "#203731",
        "fg": "#FFFFFF",
        "preview_bg": "#1a2b26",
        "preview_fg": "#f0f0f0",
        "text_bg": "#2d4d45",
        "text_fg": "#FFFFFF",
        "accent": "#FFB612",
        "accent_hover": "#e6a410",
        "border": "#FFB612",
        "selected_bg": "#3d5e56",
    },
    "Packers Light": {
        "bg": "#f5f5f5",
        "fg": "#203731",
        "preview_bg": "#FFFFFF",
        "preview_fg": "#203731",
        "text_bg": "#FFFFFF",
        "text_fg": "#203731",
        "accent": "#203731",
        "accent_hover": "#2d4d45",
        "border": "#FFB612",
        "selected_bg": "#fff8e1",
    },
    "FC Cincinnati Dark": {
        "bg": "#1a1a1a",
        "fg": "#FFFFFF",
        "preview_bg": "#263B94",
        "preview_fg": "#FFFFFF",
        "text_bg": "#2d2d2d",
        "text_fg": "#FFFFFF",
        "accent": "#FE5000",
        "accent_hover": "#e54800",
        "border": "#263B94",
        "selected_bg": "#3d3d3d",
    },
    "FC Cincinnati Light": {
        "bg": "#f0f4f8",
        "fg": "#263B94",
        "preview_bg": "#FFFFFF",
        "preview_fg": "#263B94",
        "text_bg": "#FFFFFF",
        "text_fg": "#263B94",
        "accent": "#FE5000",
        "accent_hover": "#e54800",
        "border": "#263B94",
        "selected_bg": "#e1e8f0",
    },
    "ONU Dark": {
        "bg": "#000000",
        "fg": "#FFFFFF",
        "preview_bg": "#1a1a1a",
        "preview_fg": "#FFFFFF",
        "text_bg": "#222222",
        "text_fg": "#FFFFFF",
        "accent": "#FF6600",
        "accent_hover": "#e55c00",
        "border": "#333333",
        "selected_bg": "#333333",
    },
    "ONU Light": {
        "bg": "#FFFFFF",
        "fg": "#000000",
        "preview_bg": "#f5f5f5",
        "preview_fg": "#000000",
        "text_bg": "#FFFFFF",
        "text_fg": "#000000",
        "accent": "#FF6600",
        "accent_hover": "#e55c00",
        "border": "#CCCCCC",
        "selected_bg": "#fff0e6",
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
