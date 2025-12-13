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

## Theming notes

- Prefer ttk styles for label-like widgets; styles are declared and applied by the theme manager.
- `tk.Text` widgets are not fully styleable via ttk; placeholder/faint text is still managed by direct configuration in a few places. Consider creating a small helper for placeholder behavior if you need full theme consistency.

When adding UI widgets, favor creating or reusing styles instead of passing literal fonts/colours inline.

## Data files & formats

Content is stored as human-editable markdown files under the repository root:

- `characters/` — one markdown file per character
- `base_prompts.md`, `poses.md`, `scenes.md`, `outfits.md` — prompt component lists and presets

See the `docs/` directory for format examples and editor templates.


## Contributing

- Keep compatibility with Python 3.8+ unless there is a clear reason to bump the minimum supported version
- Prefer standard-library packages; if adding a dependency, update `requirements.txt` and document the reason
- Avoid import-time side effects. Use runtime entrypoints (`Runner` or `if __name__ == '__main__'`) for initialization logic
- Add tests for new or changed behavior and run `pytest` before submitting a PR

Please open PRs for larger refactors and include screenshots for UI changes where appropriate.

---

If you'd like, I can also add a `CONTRIBUTING.md` and a `docs/dev.md` with local development tips and common troubleshooting steps.

---

Updated: December 2025
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


