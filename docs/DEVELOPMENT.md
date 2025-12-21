# Development Guide

This guide provides instructions for developers looking to contribute to Prompt Builder or modify the codebase.

## Environment Setup

1.  **Requirement**: Python 3.8+
2.  **Recommended**: Create a virtual environment.
3.  **Install Development Dependencies**:
    ```powershell
    python -m pip install -r requirements-dev.txt
    ```

## Code Quality Tools

We use several tools to maintain code quality:

*   **pytest**: For running the test suite.
*   **black**: For code formatting.
*   **isort**: For sorting imports.
*   **ruff**: For fast linting and code analysis.

### Running Quality Checks

```powershell
# Run all tests
python -m pytest

# Format code
python -m black .
python -m isort .

# Run linter
python -m ruff check .
```

## Testing Strategy

### Unit Tests
Located in the `tests/` directory. We aim for high coverage of logic and parsers.

### Import-Time Smoke Tests
Since UI modules (Tkinter) are difficult to unit test, we use a smoke test to ensure all modules can at least be imported without errors.

```powershell
# Run the smoke test
python -m pytest tests/test_cli.py # (or specific smoke test script if available)
```

## Architecture Principles

*   **Modular Design**: Use the manager pattern for UI components (e.g., `MenuManager`, `ThemeManager`).
*   **Data-Driven**: Logic should be separated from data. Data is stored in the `data/` folder as Markdown or JSON.
*   **Fail Gracefully**: Use the `logger` for error reporting and provide user-friendly notifications via `utils.notification`.
*   **Type Hinting**: Use Python type hints for better IDE support and maintainability.

## Debugging

*   **Verbose Logging**: Run the app with the `--debug` flag to see more detailed output in `promptbuilder_debug.log`.
    ```powershell
    python main.py --debug
    ```
*   **Debug Scripts**: Use `debug_log.py` for persistent logging during development.

## Commit Checklist

Before submitting a pull request, ensure:
1.  Tests pass: `pytest`
2.  Code is formatted: `black .`
3.  Imports are sorted: `isort .`
4.  Linter passes: `ruff check .`
5.  No `print()` statements remain (use `utils.logger`).
6.  Documentation is updated.

---

*Last updated: December 2025*