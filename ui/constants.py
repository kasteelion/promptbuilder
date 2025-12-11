"""UI-specific constants for the Prompt Builder application."""

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

# Performance settings
PREVIEW_UPDATE_THROTTLE_MS = 150  # Balanced for responsiveness and performance
RESIZE_THROTTLE_MS = 150
RESIZE_SIGNIFICANT_CHANGE_PX = 50  # Only update if width changes by this much
TEXT_UPDATE_DEBOUNCE_MS = 300  # Debounce delay for text input changes
WIDGET_REFLOW_RETRY_LIMIT = 5  # Maximum retries for widget reflow operations

# Window settings
DEFAULT_WINDOW_GEOMETRY = "1000x700"
MIN_PANE_WIDTH = 250  # Minimum width for left panel
DEFAULT_SASH_POSITION = 400  # Initial position of the divider

# Widget sizes
DEFAULT_TEXT_WIDGET_HEIGHT = 3  # Height for text input widgets in rows
BUTTON_PADDING_X = 5
BUTTON_PADDING_Y = 2
FRAME_PADDING = 5
SECTION_PADDING_Y = 10

# Undo/Redo settings
MAX_UNDO_STACK_SIZE = 50  # Maximum number of undo states to keep

# Gallery settings
GALLERY_CARD_WIDTH = 200
GALLERY_CARD_HEIGHT = 250
GALLERY_IMAGE_SIZE = (180, 180)
GALLERY_COLUMNS = 3

# Character card settings
CARD_MIN_WIDTH = 150
CARD_MAX_WIDTH = 300
CARD_IMAGE_HEIGHT = 150

# Tooltip settings
TOOLTIP_DELAY_MS = 500  # Delay before showing tooltips

# Search settings
SEARCH_MIN_CHARS = 2  # Minimum characters needed to trigger search

# FlowFrame settings
FLOW_FRAME_PADDING_X = 6  # Horizontal padding for FlowFrame
FLOW_FRAME_PADDING_Y = 4  # Vertical padding for FlowFrame
FLOW_FRAME_BUTTON_WIDTH = 20  # Default button width in FlowFrame
FLOW_FRAME_MIN_WIDTH_THRESHOLD = 10  # Minimum width change to trigger reflow
FLOW_FRAME_REFLOW_DELAY_MS = 50  # Delay before retrying reflow when window not mapped

# Preferences settings
MAX_RECENT_ITEMS = 10  # Maximum recent items in preferences

# Character photo thumbnail size
CHARACTER_CARD_SIZE = 100  # Width and height of character photo thumbnail
