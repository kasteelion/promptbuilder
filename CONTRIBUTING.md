# Contributing to Prompt Builder

First off, thank you for considering contributing to Prompt Builder! It's people like you who make this tool better for everyone.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct. Please be respectful and professional in all interactions.

## How Can I Contribute?

### Reporting Bugs

- **Check if the bug has already been reported** by searching the issues.
- If you can't find an open issue addressing the problem, **open a new one**. Be as specific as possible:
    - Describe the expected behavior.
    - Describe the actual behavior.
    - Provide steps to reproduce the issue.
    - Include your OS, Python version, and any relevant log output from `promptbuilder_debug.log`.

### Suggesting Enhancements

- **Check if the feature has already been suggested**.
- If not, **open a new issue** and describe:
    - The goal of the feature.
    - How it should work from a user perspective.
    - Any technical considerations or implementation ideas.

### Pull Requests

1.  **Fork the repository** and create your branch from `main`.
2.  **Install development dependencies**:
    ```powershell
    python -m pip install -r requirements-dev.txt
    ```
3.  **Make your changes**.
4.  **Run tests** to ensure everything is working correctly:
    ```powershell
    python -m pytest
    ```
5.  **Format and lint** your code:
    ```powershell
    python -m black .
    python -m isort .
    python -m ruff check .
    ```
6.  **Update documentation** if your changes add or modify features.
7.  **Submit a pull request**.

## Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/).
- Use `black` for formatting.
- Use `isort` for import sorting.
- Use `ruff` for linting.
- Add docstrings to all new functions, classes, and modules.

## Testing

We use `pytest` for unit testing. Please add tests for any new logic or bug fixes.
If you're modifying the UI, consider running the import smoke test mentioned in `docs/development.md`.

## Data Files

When contributing new characters, outfits, or scenes to the `data/` directory:
- Ensure they follow the existing Markdown format.
- Use descriptive names.
- Verify that they parse correctly by running the application.

## Questions?

If you have any questions, feel free to open an issue for discussion.
