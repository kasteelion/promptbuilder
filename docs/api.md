# API Reference (Internal)

This document provides a high-level overview of the core classes and modules in the Prompt Builder codebase. This is intended for developers who wish to extend or modify the application.

## Logic Layer (`logic/`)

### `DataLoader`
The primary interface for the file system.
- **Responsibility**: Loads characters, outfits, scenes, and interactions from the `data/` directory.
- **Key Methods**:
    - `load_all_characters()`: Returns a list of character objects.
    - `get_outfits(gender)`: Returns shared outfits for the specified gender.
    - `get_scenes()`: Returns all scene presets.

### `MarkdownParser`
A regex-based parser for human-readable content.
- **Responsibility**: Converts Markdown files into structured Python dictionaries.
- **Key Methods**:
    - `parse_character(content)`: Parses a character's Markdown content.
    - `parse_outfits(content)`: Parses the shared outfit files.

### `PromptRandomizer`
Handles the intelligent randomization of prompt elements.
- **Responsibility**: Randomly selects characters, outfits, and scenes while respecting user-defined constraints and character counts.

## Core Engine (`core/`)

### `PromptBuilder`
The central engine for prompt assembly.
- **Responsibility**: Takes the current application state and produces a formatted prompt string.
- **Key Methods**:
    - `build_prompt(state)`: The main entry point for prompt generation.

### Renderers (`core/renderers.py`)
Small, focused functions for formatting specific parts of the prompt.
- `render_character()`: Formats a character's traits and outfit.
- `render_scene()`: Formats the environment and lighting.

## UI Layer (`ui/`)

### `ThemeManager` (`themes/theme_manager.py`)
Manages application styling and dynamic theming.
- **Responsibility**: Handles theme loading, switching, and color palette management.
- **Key Features**:
    - Derives `hover_bg` and `placeholder_fg` automatically if not provided by the theme.
    - `theme_toplevel(window)`: Applies theme background and attaches the manager to Toplevel dialogs.
    - `apply_theme(theme_name)`: Updates all standard `ttk` styles and triggers manual updates for custom widgets.

### `SearchableCombobox` (`ui/searchable_combobox.py`)
A custom themed combobox with filtering and favorites.
- **Responsibility**: Provides a better user experience for long lists (characters, outfits).
- **Key Features**:
    - Real-time filtering with smart prioritization (Starts With > Contains).
    - Favorites system with visual indicators.
    - Fully themed dropdown and entry components.

### `StateManager`
Orchestrates application state and undo/redo.
- **Responsibility**: Maintains the current selection, handles presets, and coordinates with `UndoManager`.

### `FontManager`
Handles UI scaling and responsive typography.
- **Responsibility**: Calculates font sizes based on window dimensions and updates registered widgets.

## Utilities (`utils/`)

### `Logger` (`utils/logger.py`)
- **Responsibility**: Provides consistent logging across the application. Logs are written to `promptbuilder_debug.log`.

### `Notification` (`utils/notification.py`)
- **Responsibility**: Provides a unified way to show feedback to the user via toasts, status bars, or modal dialogs.

---

*Last updated: December 2025*
