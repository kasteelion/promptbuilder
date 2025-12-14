# AI Image Prompt Builder

A desktop application to help build complex and detailed prompts for AI image generation with an intuitive, resizable interface.

## Features

# AI Image Prompt Builder

A desktop application for composing complex prompts for AI image generation. It provides a graphical interface to create and combine characters, poses, outfits, and scene elements into shareable prompt text.

This repository focuses on a lightweight, dependency-free design (standard library only). Optional functionality (image previews) uses Pillow.

Supported Python: 3.8+
---

**Table of contents**
- What it does
- Requirements
- Quick start
- CLI options
- Tests
- Development & recent refactors
- Theming notes
- Data files & content format
- Contributing

---

## What it does

- Create characters, outfits, poses, and base art styles.
- Assemble those pieces into AI image prompts in a preview panel.
- Batch operations (apply outfit to many characters), randomization, and interaction templates.
- Themeable UI using Tkinter/ttk styles.

## Requirements

- Python 3.8 or newer (3.11+ recommended). The app was validated on local Python 3.14.
- Tkinter (usually included with Python installs).
- Optional: Pillow (`pip install Pillow`) to enable photo previews in the character gallery.

No other external packages are required for basic functionality.

## Quick start

Clone the repository and run from the project root. Examples below are intentionally generic (no absolute, machine-specific paths).

Run the application (example):

```powershell
python main.py
```

Run tests with `pytest`:

```powershell
python -m pytest -q
```

## CLI options

- `--version` or `-v` : print version and exit
- `--check-compat` : run a compatibility check (Python version, tkinter availability)
- `--debug` : enable debug logging and full tracebacks

CLI parsing is implemented in `cli.py` and executed by `runner.py` at runtime.

## Tests

The project uses `pytest`. Unit tests live under `tests/`.

Run the suite:

```bash
python -m pytest -q
```

Add tests alongside new features where applicable.

## Development & recent refactors

Key architecture choices and recent improvements:

- `cli.py` — centralized CLI parsing; minimizes import-time side-effects
- `runner.py` — encapsulates startup lifecycle (compat checks, logging, app bootstrap)
- `debug_log.py` — provides a context manager for deterministic log lifecycle
- `themes/theme_manager.py` — defines ttk label styles (e.g. `Bold.TLabel`, `Accent.TLabel`, `Muted.TLabel`) to make UI elements theme-aware

Many UI modules were updated to prefer ttk styles instead of inline `foreground`/`font` arguments; this improves theming consistency and testability.

**Developer Notes**

- **Entrypoint:** Runtime startup is centralized in `runner.py`. Use `python main.py` (the `main.py` file is a small shim that delegates to `Runner`). This avoids import-time side-effects.
- **Archived scripts:** Several legacy, one-off migration scripts were moved to `scripts/archived/` to keep the project root tidy. If you need an archived script, open it from that folder.
- **Outfits files:** The project now uses gendered outfit files `outfits_f.md` and `outfits_m.md`. If you previously used a single `outfits.md`, see `docs/DEVELOPMENT.md` for migration notes.
- **Logging:** Core logging is configured via `utils/logger.py`. Use `--debug` to enable verbose logging, or the `debug_log.py` utility for persistent debug logs.
- **Running checks:** See `docs/DEVELOPMENT.md` for recommended linter, formatter, and import-time smoke-test commands (PowerShell examples included).

## Theming notes

- Prefer ttk styles for label-like widgets; styles are declared and applied by the theme manager.
- `tk.Text` widgets are not fully styleable via ttk; placeholder/faint text is still managed by direct configuration in a few places. Consider creating a small helper for placeholder behavior if you need full theme consistency.

When adding UI widgets, favor creating or reusing styles instead of passing literal fonts/colours inline.

## Data files & formats

# AI Image Prompt Builder

A lightweight desktop application to compose detailed prompts for AI image generation. Use the GUI to build characters, poses, outfits and scene elements, then export the assembled prompt text for image-generation models.

Table of contents
- What it is
- Requirements
- Quick start
- Running the app (GUI & CLI)
- Development (tests & linters)
- Contributing
- Documentation & changelog

---

## What it is

- GUI-first tool to create modular prompt components (characters, poses, outfits, scenes) and combine them into exportable prompt strings.
- Supports batch operations, randomization, and templates.
- Themeable UI (Tkinter/ttk) with optional image previews via Pillow.

## Requirements

- Python 3.8 or newer (3.11+ recommended). The project has been validated locally on Python 3.14.
- Tkinter (usually included with most Python distributions).
- Optional: Pillow to enable photo previews in the character gallery (`pip install Pillow`).

The core functionality avoids runtime external dependencies; add optional packages only if you need specific features.

## Quick start

Clone the repo and run from the project root.

```powershell
git clone https://github.com/kasteelion/promptbuilder.git
cd promptbuilder
python -m pip install -r requirements.txt  # optional, for development tools
python main.py
```

The GUI will open; if you prefer the runner-based entrypoint you can use:

```powershell
python runner.py
```

## Running the app (GUI & CLI)

- Start GUI: `python main.py` (recommended for most users)
- CLI helpers are provided by `cli.py` and `runner.py`. Common options:
	- `--version` / `-v`: print version and exit
	- `--check-compat`: run compatibility checks (Python, tkinter)
	- `--debug`: enable verbose logging and debug output

Example (PowerShell):

```powershell
python main.py --debug
```

## Development (tests & linters)

We use `pytest` for unit tests and standard formatters/linters in CI. Example commands (from project root):

```powershell
python -m pytest -q
python -m isort .
python -m black .
python -m ruff check .
```

If you prefer a virtual environment, create one and activate it before running the commands above.

### CI

There is a GitHub Actions workflow at `.github/workflows/ci.yml` that runs formatting checks, linters and the test suite on pushes and pull requests.

## Contributing

- Keep compatibility with Python 3.8+ unless there is a documented reason to bump the minimum version.
- Prefer standard-library tools for core functionality; when adding a dependency, add it to `requirements.txt` and document the reason.
- Avoid import-time side-effects; use `Runner`/`runner.py` or `if __name__ == '__main__'` for runtime initialization.
- Add tests for any new or changed behavior and run `pytest` locally before submitting a PR.

If you want, I can add a `CONTRIBUTING.md` with local development tips, a recommended pre-commit configuration, and common troubleshooting steps.

## Documentation & changelog

- User-facing guides and design notes live in the `docs/` directory (see `docs/QUICK_REFERENCE.md`, `docs/COMPATIBILITY.md`, `docs/README.md`).
- Prompt components and content live under the repository root as plain markdown:
	- `characters/` — character files
	- `base_prompts.md`, `poses.md`, `scenes.md`, `outfits_f.md`, `outfits_m.md`

Changelog (high-level updates):

- Updated: December 2025 — UI improvements, undo/redo, presets, theme detection, improved copy/export options, batch operations, and performance work.

---

## License

This project is open-source. Use, modify and redistribute as permitted by the project's license.

---

If you'd like, I can:
- Add a `CONTRIBUTING.md` and a short `docs/dev.md` with PowerShell development commands.
- Add a small `README` badge section or a short GIF showing the main UI.

Updated: December 2025


