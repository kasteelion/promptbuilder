# Architecture Overview

Prompt Builder is designed with a modular, layered architecture to ensure maintainability, extensibility, and ease of testing. This document describes the key components and patterns used in the Flet-based codebase.

## System Layers

### 1. The UI Layer (ui/)
The GUI is built using the **Flet** framework, which provides a reactive and modern interface. It follows a modular, section-based approach:

*   **FletPromptBuilder**: The central application class that initializes the page and coordinates modular sections.
*   **Modular Sections**:
    *   ToolbarSection: Top navigation and global actions (Theme, Refresh, Dashboard).
    *   GallerySection: Visual character browser with real-time filtering and selection.
    *   RosterSection: Manages selected characters and their specific configurations (outfits, poses).
    *   SidebarSection: Controls for scene selection, base prompt, interaction notes, live palette swatches, 1-click recommendations, and real-time Thematic Alignment meter.
    *   ConsoleSection: Real-time preview of the generated prompt, 4-way output format selector (Markdown, Prose, Midjourney, SDXL), FIFO prompt history buffer with undo/restore, and copy actions.
    *   DashboardSection: Statistical overview of the asset library.
*   **Theme Management**:
    *   ThemeManager: Handles global theme application (Electric Azure, Glassmorphism) and component-level styling.

### 2. The Logic & Controller Layer (logic/)
This layer handles business rules and mediates between the state and the UI:

*   **AppState**: Centralized state management for the application. It holds the current selection, loaded data, and provides methods for data synchronization.
*   **Controllers**:
    *   CharacterController: High-level operations for character management in the roster.
*   **Business Logic**:
    *   InteractionLogic: Handles the complex logic for multi-character interaction templates.
    *   CharacterLogic: Lower-level logic for character data processing.
    *   DataLoader: Manages file system interactions, high-speed fast metadata loading, cached outfit parsing, and lazy loading of characters.
    *   SuggestionEngine: Analyzes prompt completeness gaps and scores candidates for Scenes, Interactions, Thematic Wardrobes, and Coordinated Palettes.
    *   Randomizer: Implements the Monte Carlo randomization logic with thematic scoring.
    *   Automation: Background batch generation, AI critic auditing, and pipeline orchestration (`AutomationOrchestrator`, `GemmaPipelineRunner`).

### 3. The Core Engine (core/)
The central engine that assembles the final output:

*   **PromptBuilder**: Orchestrates the assembly of prompts across target engines (Markdown, Banana Prose, Midjourney, SDXL) using specialized renderers.
*   **Renderers**: Modular components for formatting different parts of the prompt:
    *   CharacterRenderer, OutfitRenderer, PoseRenderer, SceneRenderer, NotesRenderer, ColorSchemeRenderer.
*   **Models**: Pydantic models (e.g., CharacterDetails, PromptConfig, SelectedCharacterConfig) that provide structure and validation for application data.

### 4. Utilities (utils/)
Cross-cutting concerns and helper functions:

*   **Logger**: Centralized logging system.
*   **PlatformUtils**: Web-safe operations for file opening and clipboard management.
*   **Color Utilities**: Helpers for handling signature colors and team color schemes.

## Key Design Patterns

### Modular Component Pattern
The UI is divided into independent Section classes (inheriting from t.UserControl or t.Container). This isolation makes the interface easier to maintain and scale.

### Controller Pattern
Controllers bridge the gap between UI events and state changes, ensuring that business logic remains decoupled from the presentation layer.

### Data-First Design
The application's content (characters, outfits, etc.) is stored in Markdown and Text files. This allows users to add content without needing to understand the underlying Python code.

### Reactive State Management
Flet's reactive nature ensures that when the AppState changes, the corresponding UI components can be refreshed efficiently.

## Data Flow

1.  **Startup**: main.py initializes AppState, which triggers DataLoader to perform an initial data sweep.
2.  **Lazy Loading**: Basic metadata is loaded for all characters, while full details are loaded only when a character is added to the roster.
3.  **User Interaction**: UI sections capture events (e.g., clicking a character) and delegate to controllers.
4.  **State Sync**: Controllers update the AppState, which notifies the FletPromptBuilder to refresh relevant UI sections.
5.  **Prompt Generation**: When the state changes, PromptBuilder retrieves the current config, passes it through Renderers, and updates the preview in the ConsoleSection.
6.  **Randomization**: The Randomizer generates and scores multiple candidate configurations, selecting the best one and updating the state in a single operation.

---

*Last updated: May 2026*
