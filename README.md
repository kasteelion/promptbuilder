# Prompt Builder

Prompt Builder is a desktop application for authoring and managing prompts, characters, themes, and presets for AI image-generation workflows. It aims to be lightweight and self-contained at runtime (no external dependencies required for normal use). Developer tooling (linters, formatters, type checkers) is optional but provided to keep the codebase consistent.
**Project status:** Beta

**License:** MIT

**Table of contents**

- [Prompt Builder](#prompt-builder)
  - [Quick Start (User)](#quick-start-user)
  - [Command-line Usage](#command-line-usage)
  - [Developer Setup](#developer-setup)
  - [Development Workflow \& Tools](#development-workflow--tools)
  - [Repository Layout](#repository-layout)
  - [Character markdown format](#character-markdown-format)
  - [Useful scripts](#useful-scripts)
  - [Logging and debugging](#logging-and-debugging)
  - [Troubleshooting](#troubleshooting)
  - [Contributing](#contributing)
  - [Commit history \& changelog](#commit-history--changelog)
  - [Contact](#contact)
- [Prompt Builder](#prompt-builder-1)

## Quick Start (User)

Prerequisites: Python 3.10+ and a Python build that includes `tkinter`.

Run the GUI from the repository root:

```powershell
python main.py
```

The app launches a Tkinter window where you can browse and edit characters, presets, and themes. Character data is stored as Markdown files under `data/characters/`.
## Command-line Usage

The app supports a few CLI flags for non-GUI workflows or simple checks:

- `--version` / `-v` — Print app & Python version then exit
- `--check-compat` — Run a basic compatibility report
- `--debug` — Enable debug-mode behavior (causes exceptions to be re-raised in some code paths)

Examples:

```powershell
python main.py --version
python main.py --check-compat
python main.py --debug
```

Some helper scripts in `scripts/` are standalone and can be run directly, for example:

```powershell
# Update tags heuristically for character markdown files
python scripts/generate_tags.py
```

Note: many scripts modify files and create `.bak` backups — review and test them on a copy of your data if you are unsure.
## Developer Setup

Recommended: create a virtual environment and install dev tools (formatters, linters, test tools).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Run tests:

```powershell
python -m pytest -q
```

Format and lint:

```powershell
python -m black .
python -m isort .
python -m ruff check .
python -m flake8 .
python -m mypy .
```

## Development Workflow & Tools

- Formatting: `black` (configured via `pyproject.toml`).
- Import sorting: `isort`.
- Linting: `ruff` (fast), `flake8` (optional) and `pylint` available if you want stricter checks.
- Type checking: `mypy` (configured in `pyproject.toml`).

During the review I enabled `tool.ruff` exclusion for `scripts/archived/` to avoid lint noise from legacy helper scripts.

## Repository Layout

- `main.py` — minimal entrypoint shim that delegates to `Runner` in `runner.py`.
- `runner.py` — app lifecycle: CLI parsing, compatibility checks, debug logging, importing the GUI, and launching `root.mainloop()`.
- `core/` — core prompt-building engines and renderers.
- `logic/` — data loading, parsing, randomization, and validation utilities.
- `ui/` — Tkinter UI: windows, widgets, controllers, panels.
- `utils/` — utilities: `file_ops.py`, `logger.py`, preferences, presets manager, etc.
- `data/` — application data (prompts, characters, scenes, outfits).
- `scripts/` — convenience & maintenance scripts. `scripts/archived/` contains older helpers kept for reference.
- `tests/` — pytest test suite.
- `requirements-dev.txt` — development tooling.
- `pyproject.toml` — project metadata and tooling configuration.

## Character markdown format

Character data is stored under `data/characters/` as Markdown files. Files typically contain a header and metadata blocks such as `**Photo:**`, `**Summary:**`, and `**Tags:**` lines. Example snippet:

```markdown
### Noa Levi

**Photo:** noa_levi.jpg

**Summary:** An athletic dancer with a warm, friendly style.

**Tags:** athletic, soft
```

Scripts such as `scripts/generate_tags.py` rely on heuristics and the parsed character fields to add or update the `**Tags:**` line.

## Useful scripts

- `scripts/generate_tags.py` — Add/update `**Tags:**` entries using heuristics based on `appearance`/`summary`.
- `scripts/generate_vibe_summaries.py` — (helper) generate short vibe summaries for characters.
- `scripts/add_character_summaries.py` — Insert or adjust summary blocks.

Many scripts create `.bak` copies before modifying files. If you plan to run them on your dataset, ensure you have a backup or run against a copy.

## Logging and debugging

Runtime debug logging is managed by `debug_log.py`, which delegates to `utils/logger.py`. The debug log file is created at `promptbuilder_debug.log` in the working directory when the app runs with debug logging initialized.

If the application fails unexpectedly, check `promptbuilder_debug.log` for the full traceback and diagnostic messages.

## Troubleshooting

- If the GUI fails to start with an ImportError for `tkinter`, install a Python distribution that includes `tkinter` (e.g., the official Python.org Windows installer) or use your system package manager to add `tk` support.
- If a script errors or modifies files unexpectedly, restore from the `.bak` files created next to modified files or from your version control.
- Run tests to get immediate failure traces:

```powershell
python -m pytest tests/test_parsers.py -q
```

## Contributing

Contributions are welcome. Workflow suggestions:

1. Fork the repo and create a feature branch.
2. Run tests and linters locally.
3. Keep changes focused and include tests for new behavior where applicable.
4. Open a pull request describing the change and rationale.

Consider adding `pre-commit` hooks to enforce `black`/`isort`/`ruff` automatically.

## Commit history & changelog

This repository does not include a formal CHANGELOG file by default. If you maintain releases, add a `CHANGELOG.md` and reference it from this README.

## Contact

If you need help, open an issue describing the problem, include steps to reproduce and relevant log output from `promptbuilder_debug.log`.

---
Generated and expanded README: added usage examples, developer workflow, script guidance, and troubleshooting notes.
# Prompt Builder

Prompt Builder is a desktop application for helping create and manage prompts and character data for AI image generation and related workflows. It's a lightweight, cross-platform Tkinter-based GUI with zero runtime external dependencies (dev tools are optional).

**Project status:** Beta

**License:** MIT

**Key features**
- Build, edit and preview character entries stored under `data/characters/`.
- Manage presets, themes, and UI layout via a simple Tkinter GUI.
- Several helper scripts in `scripts/` for batch operations (some archived helpers in `scripts/archived/`).
- Safe file operations: atomic writes and backups for important data files.

**Quick start (user)**
- Install Python 3.10+.
- Run the app from the repository root:

```powershell
python main.py
```

This launches the GUI (requires `tkinter` available in your Python build).

**Command-line flags**
- `--version` / `-v` : show program & Python version (non-GUI mode)
- `--check-compat` : run simple compatibility checks
- `--debug` : enable debug re-raise behavior in some code paths

Example (show version):
```powershell
python main.py --version
```

**Developer / Contributing**
The project aims to avoid runtime external packages. For development and formatting, a set of dev tools is provided.

1. Create a virtual environment (recommended) and install dev dependencies:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

2. Run tests:
```powershell
python -m pytest
```

3. Formatting and linting (recommended before committing):
```powershell
python -m black .
python -m isort .
python -m ruff check .
python -m flake8 .
python -m mypy .
```

Notes:
- The repo contains a `pyproject.toml` with `black` and `mypy` settings and a `tool.ruff` exclusion for archived scripts.
- CI or pre-commit hooks are not included by default; consider adding `pre-commit` for enforcing formatting.

**Repository layout (high level)**
- `main.py` - small entrypoint shim that delegates to `Runner` (in `runner.py`).
- `runner.py` - application startup lifecycle (compat checks, debug log, GUI import & mainloop).
- `core/` - core prompt-building logic and renderer hooks.
- `logic/` - data loaders, parsers, validators, randomizers.
- `ui/` - Tkinter UI code (windows, panels, widgets, controllers).
- `utils/` - helper utilities (file_ops, logging, presets, preferences, etc.).
- `data/` - sample data and `data/characters/` (where character markdown files live).
- `scripts/` - useful helper scripts for bulk operations and maintenance (some scripts are archived in `scripts/archived/`).
- `tests/` - pytest test suite.
- `requirements-dev.txt` - dev dependencies (linters, formatters, test tools).
- `pyproject.toml` - project metadata and tooling configuration.

**Notable implementation notes**
- Logging: debug logging is routed through `debug_log.py` and uses the app logger configured in `utils/logger.py`.
- Safe file writes: `utils/file_ops.py` provides `atomic_write`, `safe_read`, and backup creation.
- The GUI requires `tkinter` to be available in the Python installation (most official distributions include it; some minimal builds do not).

**Scripts of interest**
- `scripts/generate_tags.py` - scans `data/characters/*.md` and inserts/updates a `**Tags:**` line using heuristics.
- `scripts/generate_vibe_summaries.py`, `scripts/add_character_summaries.py`, etc. - other helpers for batch maintenance.

**If something breaks**
- Check `promptbuilder_debug.log` in the working directory for debug traces created by `debug_log.py`.
- Run the test suite: `python -m pytest -q` to see failing tests and tracebacks.

**Contact / Contributing**
If you want to contribute, open an issue or a PR describing the change. The project follows a typical fork-and-PR workflow. Keep changes small and focused; run tests & linters before submitting.

--
Generated README created by an automated code scan to summarize the repository and provide helpful developer instructions.
