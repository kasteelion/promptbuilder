# AI Image Prompt Builder

A desktop application to help build complex and detailed prompts for AI image generation with an intuitive, resizable interface.

## Features

# AI Image Prompt Builder

A desktop application to help build complex and detailed prompts for AI image generation with an intuitive, resizable interface.

**Quick status:** refactored startup into `cli.py` + `runner.py`, added theme-aware ttk label styles, and introduced a `DebugLog` context manager. Tests are available and the project uses only standard-library deps except optional Pillow for image previews.

**Supported Python:** 3.8+

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

From the project root:

```powershell
# Run the app
& C:/path/to/python.exe main.py

# Run the test suite
& C:/path/to/python.exe -m pytest -q
```

On Windows you can normally just run `python main.py` if `python` points to your Python installation.

## CLI options

- `--version` or `-v` : print version and exit.
- `--check-compat` : perform a compatibility check (Python version, tkinter available).
- `--debug` : run in debug mode (full tracebacks, extra logging).

These are handled by `cli.py` and executed at runtime by `runner.py`.

## Tests

This project uses `pytest` for unit tests. Run all tests with:

```powershell
python -m pytest -q
```

A small test suite covering CLI parsing and other logic is included in `tests/`.

## Development & recent refactors

Recent work improved startup modularity and themability:

- `cli.py` — centralizes command-line parsing (no import-time side effects).
- `runner.py` — encapsulates application lifecycle (init, compatibility checks, debug logging, create root, run mainloop).
- `debug_log.py` — added a `DebugLog` context manager to ensure logs are opened/closed cleanly.
- `themes/theme_manager.py` — new ttk label styles added (`Bold.TLabel`, `Accent.TLabel`, `Muted.TLabel`, `Title.TLabel`) so labels respond to theme changes.
- Many UI modules under `ui/` were updated to prefer ttk styles over hard-coded font/foreground values.

These changes make the code easier to import in tests and easier to maintain.

## Theming notes

- Most labels now use ttk styles; theme colors are defined and applied in `themes/theme_manager.py`.
- Classic `tk.Text` widgets still use direct configuration for placeholder/faint text; a follow-up helper can centralize placeholder color so it follows the theme.
- If you add UI elements, prefer creating or reusing a ttk style instead of passing `foreground`/`font` inline.

## Data files & formats

- `characters/` — individual character markdown files. File names should be lowercase with underscores.
- `base_prompts.md`, `poses.md`, `scenes.md`, `outfits.md` — structured markdown used as the "database" for prompt components.

Refer to the `docs/` directory for format examples and templates.

## Contributing

- Keep changes compatible with Python 3.8+.
- Prefer standard library modules. If you add a dependency, update `requirements.txt` and explain why it is necessary.
- Avoid import-time side effects; use `Runner` or `if __name__ == '__main__'` to perform runtime initialization.
- Follow existing style and test any UI code you modify. Run `python -m pytest -q` before opening PRs.

If you want, open a PR for larger refactors and include screenshots of UI changes where relevant.

---

If you'd like I can also:
- Add a short `CONTRIBUTING.md` template.
- Add a small `dev.md` describing how to run and debug the GUI on Windows and common troubleshooting steps.


***
Updated: December 2025
***
- ✅ Undo/Redo system (Ctrl+Z/Y)
- ✅ Presets & Templates (Save/Load configurations)
- ✅ Smart preferences (Auto-save settings)
- ✅ Auto theme detection (Follows OS dark/light mode)
- ✅ Enhanced copy options (Copy sections separately)
- ✅ Right-click context menus
- ✅ Batch operations (Clear all, reset outfits, apply poses)
- ✅ Tooltips throughout UI
- ✅ 20+ keyboard shortcuts
- ✅ Export/Import configurations (JSON)
- ✅ Live status updates
- ✅ User-friendly error messages
- ✅ Welcome screen for new users
- ✅ Collapsible sections
- ✅ Performance optimizations

### Version 1.0
- Initial release

---

## Contributing

Contributions are welcome! This project follows standard Python best practices:

- Python 3.8+ compatibility
- Zero external dependencies for core functionality
- Type hints where possible
- Centralized logging using the `utils.logger` module
- Modular architecture with specialized manager classes

See the documentation in the `docs/` directory for more technical details.

## Tests & CI

- **Run tests locally:**

```powershell
# From project root (Windows PowerShell)
C:/Users/parking/miniforge3/Scripts/conda.exe run -p C:\Users\parking\miniforge3 --no-capture-output python -m pytest -q
```

- **Run linters & formatters locally:**

```powershell
C:/Users/parking/miniforge3/Scripts/conda.exe run -p C:\Users\parking\miniforge3 --no-capture-output python -m isort .
C:/Users/parking/miniforge3/Scripts/conda.exe run -p C:\Users\parking\miniforge3 --no-capture-output python -m black .
C:/Users/parking/miniforge3/Scripts/conda.exe run -p C:\Users\parking\miniforge3 --no-capture-output python -m ruff check .
```

- **CI:** A GitHub Actions workflow is included at `.github/workflows/ci.yml` that runs formatting checks, linters, and `pytest` on pushes and pull requests to `master`.

If you want me to also add a pre-commit configuration or extend the CI matrix, tell me which tools/versions you prefer and I will add them.

## Documentation

- **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Keyboard shortcuts and quick tips
- **[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)** - Python version compatibility information
 - **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Keyboard shortcuts and quick tips
 - **[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)** - Python version compatibility information

**Note:** The Visual Gallery UI has been deprecated and removed from the codebase. Archived notes are available at `docs/VISUAL_UI_GUIDE.md` and `docs/VISUAL_UI_IMPLEMENTATION.md`.

## License

This project is open source. Feel free to use, modify, and distribute as needed.

## Acknowledgments

Built with Python's tkinter library for maximum compatibility and zero dependencies.


