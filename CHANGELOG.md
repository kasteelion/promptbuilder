# Changelog

## [Unreleased]

- docs: comprehensive documentation overhaul to follow industry standards
- docs: added MIT LICENSE and CONTRIBUTING.md guidelines
- docs: reorganized docs/ directory with a central README index and legacy/ archive
- docs: added internal API Reference for developers
- docs: renamed documentation files to lowercase-kebab-case for consistency
- cleanup: removed redundant and temporary files from project root
- cleanup: fixed redundant exit call in `main.py`
- readme: completely rewritten with professional structure and detailed installation guide
- tests: strengthen import checks and add parser edge-case tests
- tests: add ThemeManager and notification unit tests (migration, reload, notify fallback)
- refactor: centralize startup in `runner.py` and simplify `main.py` to a runner shim
- cleanup: move legacy ad-hoc migration scripts to `scripts/archived/` to reduce repo clutter
- logging: revert default logger level to INFO and add debug logging via `--debug` / `debug_log.py`

