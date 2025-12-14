 # Development Guide

Short, focused developer instructions for local checks, linting, import-time smoke tests, and common troubleshooting. Commands include Windows PowerShell examples.

## Install dev dependencies

The repository ships `requirements-dev.txt` for optional dev tools (formatters / linters).

Run in PowerShell:

    python -m pip install -r requirements-dev.txt

If you prefer specific tools only:

    python -m pip install ruff black isort pytest

## Run tests

Run the test suite from the project root:

    # From project root
    python -m pytest -q

## Lint & format

Run import sort, format, and ruff checks (examples):

    python -m isort .
    python -m black .
    python -m ruff check .

Consider adding these to a pre-commit config or CI workflow.

## Import-time smoke tests (UI modules)

UI files (Tkinter, image preview code) are not fully exercised by unit tests. To run a reliable import-time smoke test, create a small script `tools/import_smoke.py` with the following content:

    import importlib, pkgutil, traceback
    failed = []
    for _, name, _ in pkgutil.iter_modules(['ui']):
        mod = 'ui.' + name
        try:
            importlib.import_module(mod)
        except Exception:
            traceback.print_exc()
            failed.append(mod)
    print('Failed imports:', failed)

Then run:

    python tools/import_smoke.py

If any `ui.*` module raises an exception on import, open the traceback and fix import-time side-effects (defer heavy initialization behind functions or the Runner entrypoint).

## Debug logging

To run the application with verbose debug logging:

    python main.py --debug

Use the `debug_log.py` helper to capture persistent logs to `promptbuilder_debug.log` (the helper is a thin wrapper around `utils.logger`).

## Migration notes — outfits

The project uses gendered outfit files: `outfits_f.md` and `outfits_m.md`. If you previously maintained a single `outfits.md`, split entries into the appropriate gendered file or keep shared items in both files. The `logic/data_loader.py` and `logic/parsers.py` will read the gendered files.

## Commit checklist

- Run unit tests: `python -m pytest -q`
- Run `ruff` and `black` where applicable
- Ensure no `print()` statements remain for user-facing messages (use `utils.logger`)
- Avoid import-time side-effects in modules — prefer runtime initialization via `Runner` or guarded `if __name__ == '__main__'` blocks in scripts

## Further improvements

- Add a `pre-commit` configuration to run `isort`, `black`, and `ruff` on commit
- Add a dedicated import-smoke test to `tests/` that imports all `ui.*` modules in CI

---

Last updated: December 2025
