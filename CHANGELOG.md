# Changelog

## Unreleased

- tests: strengthen import checks and add parser edge-case tests
- tests: add ThemeManager and notification unit tests (migration, reload, notify fallback)
- docs: remove duplicate QUICK_REFERENCE and tidy README links
- refactor: centralize startup in `runner.py` and simplify `main.py` to a runner shim
- cleanup: move legacy ad-hoc migration scripts to `scripts/archived/` to reduce repo clutter
- logging: revert default logger level to INFO and add debug logging via `--debug` / `debug_log.py`

