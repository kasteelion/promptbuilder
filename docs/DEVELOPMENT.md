# Development Guide

This guide provides instructions for developers looking to contribute to Prompt Builder or modify the codebase.

## Environment Setup

1.  **Requirement**: Python 3.10+
2.  **Recommended**: Create a virtual environment.
3.  **Install Core Dependencies**:
    `ash
    pip install -r requirements.txt
    `
4.  **Install Development Dependencies**:
    `ash
    pip install -r requirements-dev.txt
    `

## Code Quality Tools

We use several tools to maintain code quality:

*   **pytest**: For running the test suite.
*   **ruff**: For fast linting and code analysis.
*   **black**: For code formatting (optional, but recommended).

### Running Quality Checks

`powershell
# Run all tests
python -m pytest

# Run linter
python -m ruff check .
`

## Testing Strategy

### Unit & Integration Tests
Located in the 	ests/ directory. 
- 	est_builder.py: Validates prompt assembly and rendering.
- 	est_randomizer.py: Tests randomization logic and scoring.
- 	est_parsers.py: Ensures assets are correctly parsed into models.
- 	est_roster_logic.py: Validates roster management.

### UI Testing
Flet components are tested primarily through integration tests and manual verification. Use the --audit flag to run console-based randomization audits.

`powershell
python main.py --audit
`

## Architecture Principles

*   **Modular UI**: Sections should be self-contained and inherit from `ft.UserControl` or `ft.Container`.
*   **Logic Isolation**: Business logic belongs in `logic/` and should be independent of Flet components.
*   **Model-Driven**: Use the Pydantic models in `core/models.py` for data passing and validation.
*   **Local-First / Offline Fallbacks**: Ensure all features remain functional without internet connectivity. Features relying on cloud AI models (like the Gemma Client or AI Studio automation) must fail gracefully or attempt to use local offline inference (e.g. Ollama via `localhost:11434`) before resorting to Cloud APIs.

### Configuring Gemma Client (Development)
If testing the `GemmaClient` in `cloud` mode, ensure you have exported your API key:
```powershell
# Windows
$env:GEMINI_API_KEY="your-api-key"
```
Or ensure you have an active local Ollama instance running `gemma2` on port 11434 if using `local` mode.

## Debugging

*   **Logging**: Check logs/ directory for detailed application logs.
*   **Flet Inspection**: Use Flet's built-in developer tools if needed.

## Commit Checklist

Before submitting a pull request, ensure:
1.  Tests pass: pytest
2.  Linter passes: uff check .
3.  No print() statements remain (use utils.logger).
4.  Documentation is updated (especially docs/api.md if changing core logic).

---

*Last updated: May 2026*
