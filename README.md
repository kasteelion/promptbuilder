# Prompt Builder: Group Picture Generator & AI Prompt Authoring Tool

Prompt Builder is a desktop application designed to streamline the creation and management of detailed prompts, characters, themes, and presets for AI image-generation workflows. It simplifies the process of building complex prompts, especially for scenarios involving multiple characters, specific scenes, interactions, and diverse stylistic elements.

The application aims to be lightweight and self-contained, requiring no external dependencies for normal runtime operation. Developer tooling (linters, formatters, type checkers) is optional but provided to maintain codebase consistency.

**Project status:** Beta

**License:** MIT

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Running the Application](#running-the-application)
  - [Command-line Usage](#command-line-usage)
- [Data Structure and Customization](#data-structure-and-customization)
- [Developer Setup](#developer-setup)
- [Repository Layout](#repository-layout)
- [Useful Scripts](#useful-scripts)
- [Logging and Debugging](#logging-and-debugging)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Contact](#contact)

---

## Features

*   **Intuitive Tkinter GUI:** A user-friendly interface for building and managing prompts.
*   **Character Management:** Easily select, configure outfits, poses, and details for multiple characters.
*   **Scene and Interaction Definition:** Define custom scenes and multi-character interactions to enrich your prompts.
*   **Real-time Prompt Preview:** Instantly see the generated prompt as you make selections and edits, with adaptive throttling for smooth performance.
*   **Markdown-based Data Storage:** All configurable data (characters, outfits, scenes, poses, interactions, themes) is stored in human-readable Markdown files, making it easy to edit and extend.
*   **Theming Support:** Customize the application's appearance with built-in themes or create your own.
*   **Undo/Redo Functionality:** Safely experiment with prompt configurations.
*   **Preset Saving/Loading:** Save and load entire prompt configurations as presets for quick reuse.
*   **Random Prompt Generation:** Generate diverse and creative prompts with a single click.
*   **Cross-platform Compatibility:** Built with Python and Tkinter, it runs on various operating systems.
*   **Minimal Runtime Dependencies:** Designed for ease of use without complex setup.

## Architecture Overview

The Prompt Builder application follows a modular, layered architecture:

*   **Entrypoint (`main.py`)**: A minimal shim that delegates application startup to the `Runner`.
*   **Application Lifecycle (`runner.py`)**: The `Runner` class manages the application's lifecycle, including CLI argument parsing, compatibility checks, debug logging, and launching the main Tkinter GUI. It also handles top-level error catching and graceful shutdowns.
*   **User Interface (`ui/`)**: The core of the application's interaction. Built with Tkinter, it comprises:
    *   **`PromptBuilderApp` (`ui/main_window.py`)**: The main application window, orchestrating all UI components.
    *   **Tabs (`ui/characters_tab.py`, `ui/edit_tab.py`)**: For managing characters and potentially editing raw data files.
    *   **Panels and Widgets**: Including `CharacterGalleryPanel`, `PreviewPanel`, and various input controls for scene, notes, and interactions.
    *   **Managers/Controllers**: Dedicated classes (e.g., `MenuManager`, `FontManager`, `ThemeManager`, `StateManager`, `PreviewController`, `GalleryController`) encapsulate specific UI behaviors and state management.
*   **Data Management (`logic/data_loader.py` & `data/`)**:
    *   `DataLoader` is responsible for loading all application data from Markdown files located in the `data/` directory.
    *   The `data/` directory contains definitions for `characters`, `base_prompts`, `poses`, `scenes`, `outfits` (female and male), `interactions`, and `themes`.
*   **Prompt Generation Logic (`core/`, `logic/`)**:
    *   **`PromptBuilder` (`core/builder.py`)**: The central engine for constructing the final prompt string based on the user's selections and inputs.
    *   **`PromptRandomizer` (`logic/randomizer.py`)**: Generates random configurations for characters, poses, scenes, and interactions.
    *   **`Validator` (`logic/validator.py`)**: Ensures that prompt configurations are valid.
*   **Utilities (`utils/`)**: A collection of common helper modules for preferences, logging, notifications, file operations, undo/redo management, and more.

This structure ensures a clear separation of concerns, making the application maintainable, testable, and extensible.

## Getting Started

### Prerequisites

*   **Python 3.8 or newer**: Download from [python.org](https://www.python.org/downloads/).
*   **Tkinter**: Your Python installation must include Tkinter. Most official Python distributions (e.g., from python.org) include it by default. If you encounter a `tkinter.TclError` or `ImportError`, you might need to install `tk` support via your system's package manager (e.g., `sudo apt-get install python3-tk` on Debian/Ubuntu, `brew install python-tk` on macOS for Homebrew Python).

### Running the Application

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/promptbuilder.git # Replace with actual repo URL
    cd promptbuilder
    ```
2.  **Run the GUI:**
    ```powershell
    python main.py
    ```
    This will launch the main application window.

### Command-line Usage

The application supports a few command-line flags for non-GUI workflows or simple checks:

*   `--version` / `-v`: Print application and Python version information, then exit.
*   `--check-compat`: Run a basic compatibility report for your system.
*   `--debug`: Enable debug-mode behavior, which causes exceptions to be re-raised in some code paths for easier debugging.

**Examples:**
```powershell
python main.py --version
python main.py --check-compat
python main.py --debug
```

## Data Structure and Customization

The core of Prompt Builder's flexibility comes from its Markdown-based data files, all located within the `data/` directory. You can easily modify or extend the application's content by editing these files:

*   `data/characters/`: Contains individual Markdown files for each character, defining their properties, descriptions, and character-specific outfits.
*   `data/base_prompts.md`: Defines base prompt templates that can be selected as a starting point.
*   `data/poses.md`: Lists various poses with their descriptions.
*   `data/scenes.md`: Contains scene categories and specific scene descriptions.
*   `data/outfits_f.md`, `data/outfits_m.md`: Define shared outfits for female and male characters, respectively. These are automatically available to all characters.
*   `data/interactions.md`: Stores templates for multi-character interactions.
*   `data/color_schemes.md`, `data/tags.md`, `data/themes.md`: Used for UI theming and metadata management.

By modifying these Markdown files, users can expand the application's content, add new characters, define new outfit styles, or create custom scenes and interactions without touching the Python code.

## Developer Setup

For developers interested in contributing or extending the application, follow these steps to set up your development environment:

1.  **Create a Virtual Environment (Recommended):**
    ```powershell
    python -m venv .venv
    # On Windows:
    .\.venv\Scripts\Activate.ps1
    # On macOS/Linux:
    source .venv/bin/activate
    ```

2.  **Install Development Dependencies:**
    ```powersell
    python -m pip install -r requirements-dev.txt
    ```
    This will install tools for testing, formatting, and linting.

3.  **Run Tests:**
    ```powershell
    python -m pytest -q
    ```

4.  **Formatting and Linting (Recommended before committing):**
    Ensure your code adheres to the project's style guidelines:
    ```powershell
    python -m black .
    python -m isort .
    python -m ruff check .
    python -m flake8 .
    python -m mypy .
    ```

*   **Notes:**
    *   The `pyproject.toml` file contains configuration for `black` and `mypy`, and `ruff` exclusions for archived scripts.
    *   Pre-commit hooks are not included by default; consider adding them (e.g., using `pre-commit` framework) to automate formatting and linting checks.

## Repository Layout

*   `main.py` — The minimal entrypoint shim, delegating to `Runner` in `runner.py`.
*   `runner.py` — Manages the application lifecycle: CLI parsing, compatibility checks, debug logging, importing the GUI, and launching `root.mainloop()`.
*   `core/` — Contains the core prompt-building engines and renderers.
*   `logic/` — Houses utilities for data loading, parsing, randomization, and validation.
*   `ui/` — All Tkinter UI code: windows, widgets, controllers, and panels.
*   `utils/` — General utility modules: `file_ops.py`, `logger.py`, preferences manager, presets manager, etc.
*   `data/` — The primary location for application data: characters, base prompts, scenes, outfits, interactions, and themes (all in Markdown format).
*   `scripts/` — Convenience and maintenance scripts. `scripts/archived/` contains older helpers kept for reference.
*   `tests/` — The `pytest` test suite for the application.
*   `requirements-dev.txt` — Lists development-specific dependencies (linters, formatters, test tools).
*   `pyproject.toml` — Contains project metadata and configuration for various development tools.

## Useful Scripts

Several scripts in the `scripts/` directory assist with data management and maintenance:

*   `scripts/generate_tags.py`: Scans `data/characters/*.md` files and heuristically inserts or updates the `**Tags:**` entry based on character appearance and summary.
*   `scripts/generate_vibe_summaries.py`: A helper script to generate short vibe summaries for characters.
*   `scripts/add_character_summaries.py`: Used to insert or adjust summary blocks within character Markdown files.

**Caution:** Many scripts modify files and create `.bak` backups. Always review changes and test on a copy of your data if you are unsure.

## Logging and Debugging

Runtime debug logging is managed by `debug_log.py`, which delegates to `utils/logger.py`. A debug log file named `promptbuilder_debug.log` is created in the working directory when the app runs with debug logging initialized, providing detailed diagnostic messages.

If the application encounters an unexpected error, consult `promptbuilder_debug.log` for the full traceback and relevant information.

## Troubleshooting

*   **Tkinter ImportError/TclError**: If the GUI fails to start due to `tkinter` not being found, ensure you have a Python distribution that includes `tkinter` (e.g., the official Python.org Windows installer), or install `tk` support via your system's package manager.
*   **Script Errors/Unexpected File Modifications**: If a script produces errors or modifies files incorrectly, restore from the `.bak` files created alongside modified files or from your version control system.
*   **Debugging Tests**: To get immediate failure traces for specific components, run `pytest` directly: `python -m pytest tests/test_parsers.py -q`.

## Contributing

Contributions are welcome! Please follow these general guidelines:

1.  **Fork the repository** and create a feature branch for your changes.
2.  **Run tests and linters locally** to ensure your changes are consistent with the project's standards.
3.  **Focus your changes** and include unit tests for any new behavior or bug fixes where applicable.
4.  **Open a pull request** describing your changes and the rationale behind them.

Consider integrating `pre-commit` hooks to automatically enforce `black`, `isort`, and `ruff` before committing.

## Contact

For assistance, please open an issue on the GitHub repository. Describe the problem, include steps to reproduce, and attach relevant log output from `promptbuilder_debug.log`.