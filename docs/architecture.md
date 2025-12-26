# Architecture Overview

Prompt Builder is designed with a modular, layered architecture to ensure maintainability, extensibility, and ease of testing. This document describes the key components and patterns used in the codebase.

## System Layers

### 1. The UI Layer (`ui/`)
The GUI is built using Python's standard `tkinter` library. It follows a component-based approach:

*   **MainWindow**: The central coordinator that integrates various panels and managers.
*   **Managers**: Specialized classes that handle specific UI concerns (Menu, Theme, Font, State, Dialog).
*   **Controllers**: Decoupled logic for specific UI behaviors, such as gallery management and menu actions.
*   **Widgets**: Custom, reusable UI components like `CollapsibleFrame` and `SearchableCombobox`.

### 2. The Logic Layer (`logic/`)
This layer handles data processing and business rules, independent of the UI:

*   **DataLoader**: Manages file system interactions, caching, and data retrieval.
*   **Parsers**: Transform human-readable Markdown files into structured Python objects (Characters, Outfits, Scenes, Interactions).
*   **Randomizer**: Implements intelligent randomization logic for generating variety while respecting constraints.
*   **Validator**: Ensures data integrity and provides helpful error messages.

### 3. The Core Engine (`core/`)
The central engine that assembles the final output:

*   **PromptBuilder**: Orchestrates the assembly of prompts based on the current application state.
*   **Renderers**: Specialized modules for formatting different parts of the prompt (Characters, Scenes, Notes).

### 4. Utilities (`utils/`)
Cross-cutting concerns and helper functions:

*   **Logger**: Centralized logging system.
*   **Preferences**: Manages user settings and persistence.
*   **Undo/Redo**: Implements the command pattern for state management.
*   **Notification**: Handles user feedback (toasts, status bar, dialogs).
*   **OutfitSummary**: Generates structured summaries of the outfit library for the UI explorer.

## Key Design Patterns

### Manager Pattern
Used in the UI layer to prevent `MainWindow` from becoming a "God Object." Each manager has a specific responsibility (e.g., `ThemeManager` handles styling).

### Data-First Design
The application's content (characters, outfits, etc.) is stored in Markdown files. This allows users to add content without needing to understand the underlying Python code.

### Observer Pattern
Used for UI updates. For example, when the theme changes, the `ThemeManager` notifies all registered widgets to update their appearance.

## Data Flow

1.  **Startup**: `main.py` calls `runner.py`, which initializes the `DataLoader` and `ThemeManager`.
2.  **Loading**: `DataLoader` reads Markdown files from the `data/` directory and uses `Parsers` to create data objects.
3.  **User Interaction**: The user selects characters and options in the UI.
4.  **State Management**: `StateManager` tracks changes, enabling undo/redo and saving presets.
5.  **Prompt Generation**: `PromptBuilder` retrieves data from the state, passes it through `Renderers`, and updates the real-time preview.
6.  **Output**: The final prompt is displayed in the UI for the user to copy.

---

*Last updated: December 2025*