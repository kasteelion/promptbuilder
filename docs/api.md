# API Reference (Internal)

This document provides a high-level overview of the core classes and modules in the Prompt Builder codebase.

## Logic Layer (logic/)

### DataLoader
The primary interface for the file system.
- **Responsibility**: Loads characters, outfits, scenes, and interactions from ssets/data/.
- **Key Methods**:
    - load_characters_metadata(): Lightweight load for gallery display.
    - get_character_details(name): Full lazy-load of character data.
    - load_presets(filename): Loads generic assets like scenes and poses.

### PromptRandomizer
Handles the intelligent randomization of prompt elements.
- **Responsibility**: Selects coherent combinations of character, scene, and style using a weighted scoring engine.
- **Key Methods**:
    - andomize(): Generates and scores candidates, returning the best configuration.

### AppState
Centralized state management.
- **Responsibility**: Coordinates between UI sections and logic controllers.
- **Key Methods**:
    - get_prompt(): Triggers the builder to generate the final prompt string.

## Core Engine (core/)

### PromptBuilder
The central engine for prompt assembly.
- **Responsibility**: Assembles formatted prompts from a PromptConfig model.
- **Key Methods**:
    - generate(config): Produces the final prompt string.
    - generate_summary(config): Produces the human-readable UI summary.

### PromptConfig (core/models.py)
The primary data model for prompt generation.
- **Fields**: ase_prompt, scene, selected_characters, 
otes, metadata.

### Renderers (core/renderers/)
Modules responsible for formatting specific segments of the prompt.
- CharacterRenderer, OutfitRenderer, PoseRenderer, SceneRenderer, NotesRenderer.

## UI Layer (ui/)

### FletPromptBuilder
The main application entry point.
- **Responsibility**: Initializes the Flet page and manages modular sections.

### Modular Sections (ui/sections/)
- ToolbarSection, GallerySection, RosterSection, SidebarSection, ConsoleSection.

### CharacterController (logic/controllers/)
- **Responsibility**: Handles additions, removals, and updates to the character roster.

## Utilities (utils/)

### PlatformUtils
- **Responsibility**: Provides web-safe wrappers for OS-specific operations like clipboard and file opening.

### ThemeManager (core/flet_theme_manager.py)
- **Responsibility**: Applies the "Nebula" design system styling to the Flet application.

---

*Last updated: May 2026*
