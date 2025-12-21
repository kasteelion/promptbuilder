# Prompt Builder: Group Picture Generator & AI Prompt Authoring Tool

Prompt Builder is a powerful desktop application designed to streamline the creation and management of detailed prompts, characters, themes, and presets for AI image-generation workflows (like Stable Diffusion, Midjourney, etc.). It simplifies the process of building complex, multi-character prompts, ensuring consistency and creative flexibility.

The application is built on a "data-first" philosophy, where all content is driven by human-readable Markdown files, allowing users to extend the system without touching any code.

**Project status:** Beta  
**License:** MIT

---

## Core Philosophy

*   **Data-Driven Design:** Everything from character appearances to UI themes is stored in Markdown or JSON. If you can edit text, you can customize this app.
*   **Privacy & Local-First:** No cloud dependencies, no tracking, and no internet required for core functionality. Your data and prompts stay on your machine.
*   **Consistency is Key:** Features like "Identity Locks" ensure that character descriptions remain stable even as you change their outfits or actions.
*   **Extensible Logic:** The modular architecture allows for easy addition of new renderers, parsers, or UI components.

---

## Table of Contents

- [Features](#features)
- [Key Concepts](#key-concepts)
- [Workflow Example](#workflow-example)
- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
- [Data Structure and Customization](#data-structure-and-customization)
- [Developer Setup](#developer-setup)
- [Repository Layout](#repository-layout)
- [Logging and Debugging](#logging-and-debugging)

---

## Features

*   **Intuitive Tkinter GUI:** A professional, responsive interface with collapsible panels and resizable panes.
*   **Character Management:** A gallery-style selection system for managing a vast library of characters.
*   **Structured Outfits:** Support for complex outfit definitions (Top, Bottom, Footwear, Accessories) with automatic "one-piece" detection.
*   **Interaction Templates:** A robust placeholder system (`{char1}`, `{char2}`) for defining how multiple characters interact in a scene.
*   **Identity Locks:** A specialized format for character appearance that "locks" core traits (Body, Face, Hair, Skin) separately from temporary actions.
*   **Real-time Prompt Preview:** Instant feedback as you build your prompt, with adaptive throttling to keep the UI snappy.
*   **Advanced Theming:** A built-in theme editor to customize colors, fonts, and UI scaling.
*   **Undo/Redo & Presets:** Full state management to save your work or experiment safely.
*   **Randomization Engine:** Intelligent randomization that respects character counts and stylistic constraints.

---

## Key Concepts

### Identity Locks
To maintain character consistency across different generations, Prompt Builder supports "Identity Locks." In a character's Markdown file, you can define core physical traits that the generator will always include, ensuring the character looks the same whether they are at the beach or in a coffee shop.

### Interaction Templates
Building prompts for multiple people is hard. Interaction templates allow you to define patterns like:
`{char1} is leaning against a wall while {char2} laughs at something on their phone.`
The app automatically replaces these placeholders with your currently selected characters.

### Adaptive Preview
The preview panel doesn't just show text; it validates your configuration in real-time. If you have too many characters or missing data, the app provides helpful hints to fix your prompt.

---

## Workflow Example

1.  **Select Characters:** Browse the gallery and add characters to your current session.
2.  **Configure Details:** For each character, choose an outfit (from their personal list or shared global outfits) and a pose.
3.  **Set the Scene:** Pick a scene preset (e.g., "Neon City") or write a custom environment description.
4.  **Add Interactions:** Select an interaction template to define the relationship between the characters.
5.  **Refine & Copy:** Watch the prompt build itself in the preview panel. Once satisfied, copy it to your image generator of choice.

---

## Architecture Overview

The application follows a modular, layered architecture designed for maintainability:

*   **Lifecycle & Entry (`main.py`, `runner.py`)**: Manages startup, environment checks (Python version, Tkinter availability), and global error handling.
*   **The UI Layer (`ui/`)**: A component-based GUI architecture.
    *   **Main Window**: Orchestrates the interaction between the Gallery, Character Tabs, and Preview Panel.
    *   **Controllers**: Decoupled logic for specific UI behaviors like Gallery management, Menu actions, and Window state.
    *   **Theme Manager**: Handles dynamic UI updates and custom styling.
*   **The Core Engine (`core/`)**:
    *   **`PromptBuilder`**: The central logic that assembles the prompt. It uses specialized **Renderers** for Characters, Scenes, and Notes to ensure consistent formatting.
*   **The Logic Layer (`logic/`)**:
    *   **`DataLoader`**: A robust file system interface with caching and legacy support.
    *   **`MarkdownParser`**: A regex-powered engine that transforms human-readable text into structured data objects.
*   **Utilities (`utils/`)**: Shared services for Logging, Preferences, Undo/Redo, and File I/O.

---

## Getting Started

### Prerequisites

*   **Python 3.8+**: Ensure Python is installed.
*   **Tkinter**: Usually bundled with Python. On Linux, you may need `sudo apt install python3-tk`.

### Running the Application

```powershell
python main.py
```

---

## Data Structure and Customization

All data lives in the `data/` folder:
*   `data/characters/`: Individual `.md` files for each character.
*   `data/outfits_f.md` / `data/outfits_m.md`: Shared wardrobe items.
*   `data/scenes.md`: Environment presets.
*   `data/interactions.md`: Multi-character behavior templates.

Example Character File:
```markdown
### Maya
**Appearance:** Athletic build, tan skin, long dark hair.
**Outfits:**
#### Base
- **Top:** White tank top
- **Bottom:** Blue jeans
```

---

## Developer Setup

1.  **Install Dev Tools:** `pip install -r requirements-dev.txt`
2.  **Run Tests:** `pytest`
3.  **Lint & Format:** Use `ruff`, `black`, and `isort` to keep the codebase clean.

---

## Repository Layout

*   `core/` — Prompt assembly and rendering.
*   `logic/` — Data parsing and business logic.
*   `ui/` — Tkinter components and controllers.
*   `utils/` — Shared helpers (Logging, Prefs, Undo).
*   `data/` — Markdown content files.
*   `tests/` — Automated test suite.

---

## Logging and Debugging

The app generates a `promptbuilder_debug.log` for troubleshooting. If the UI fails to load, check this file for a full stack trace.

---

## Contributing

Contributions are welcome! Please ensure you run the test suite and linters before submitting a PR.

---

## Contact

For assistance, please open an issue on the GitHub repository.