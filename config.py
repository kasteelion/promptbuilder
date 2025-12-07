"""Configuration constants for the Prompt Builder application."""

# Font settings
DEFAULT_FONT_FAMILY = "Consolas"
DEFAULT_FONT_SIZE = 12
MIN_FONT_SIZE = 9
MAX_FONT_SIZE = 16

# Font size breakpoints: (window_width, font_size)
# These define how font size scales with window width
FONT_SIZE_BREAKPOINTS = [
    (600, 9),
    (800, 10),
    (1000, 11),
    (1200, 12),
    (1400, 13),
    (1600, 14),
    (1800, 15),
    (2000, 16)
]

# UI settings
PREVIEW_UPDATE_THROTTLE_MS = 200
RESIZE_THROTTLE_MS = 150
RESIZE_SIGNIFICANT_CHANGE_PX = 50  # Only update if width changes by this much
DEFAULT_WINDOW_GEOMETRY = "1000x700"
MIN_PANE_WIDTH = 250  # Minimum width for left panel
DEFAULT_SASH_POSITION = 400  # Initial position of the divider

# File paths
# NOTE: Character files are loaded dynamically from the characters/ folder.
# These are the main data files that can be edited through the UI.
MAIN_EDITABLE_FILES = ["base_prompts.md", "scenes.md", "poses.md", "outfits.md"]

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
        "selected_bg": "#e3f2fd"
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
        "selected_bg": "#2d3e50"
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
        "selected_bg": "#49483e"
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
        "selected_bg": "#434c5e"
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
        "selected_bg": "#44475a"
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
        "selected_bg": "#504945"
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
        "selected_bg": "#3e4451"
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
        "selected_bg": "#292e42"
    }
}

DEFAULT_THEME = "Dark"
