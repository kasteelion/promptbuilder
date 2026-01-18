# Prompt Builder

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Project Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)]()

**Prompt Builder** is a powerful desktop application for crafting detailed, consistent AI art prompts. It combines a visual character gallery (71 characters), dynamic tag filtering, and smart randomization to streamline your workflow for Stable Diffusion, Midjourney, and other generative AI tools.

Built with a **local-first, zero-dependency** philosophy, all content—characters, outfits (~250 across 25 categories), poses—is stored as simple Markdown and Text files, making it infinitely extensible and hackable.

---

## 🌟 Key Features

- **🎨 Visual Gallery:** Browse your character library with large previews and instant selection.
- **🏷️ Smart Tag Filtering:** Find characters instantly by filtering tags (e.g., `female`, `fantasy`, `sci-fi`) with real-time search.
- **👗 Modular Wardrobe:** Apply unified outfit presets (defined in `.txt` files) to _any_ character. Mix and match with context-aware "Modifiers" (e.g., _Soccer_ outfit → _Goalie_ variant).
- **🎲 Coherence Engine:** Randomize styles, outfits, and poses while maintaining thematic consistency through cascading context and a **strict Score 250 quality floor** (re-rolls until "Elite" standard is met).
- **🎨 Signature Colors:** Characters have signature colors that dynamically apply to compatible outfits using `(signature)` tokens.
- **⚡ Bulk Actions:** Apply outfits, color schemes, or signature colors to multiple characters at once.
- **📥 Natural Language Import:** Paste raw text descriptions or LLM-generated configs to auto-populate prompts.
- **📊 Visual Explorers:** Browse tag distribution statistics and outfit library with category filtering.
- **🤖 LLM Export:** Export condensed catalog for AI knowledge injection and automated prompt generation.
- **🕵️ Auditing Suite:** Built-in tools to score prompt quality, visualize distribution (Sankey diagrams), and verify data integrity.
- **🔒 Privacy Focused:** Runs 100% locally. No cloud, no tracking.

## 🚀 Quick Start

### 1. Installation

1.  **Verify Python version** (3.10 or higher required):
    ```bash
    python --version
    ```
2.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/promptbuilder.git
    cd promptbuilder
    ```
3.  **Core app has zero dependencies!** Optional tools require:

    ```bash
    # For browser automation (optional)
    pip install playwright
    playwright install chromium

    # For development tools (optional)
    pip install -r requirements-dev.txt
    ```

### 2. Launching the App

- **Terminal:** Run `python main.py`
- **Windows (Silent):** Double-click `launchers/run_app.vbs` (no console window)
- **Windows (PowerShell):** Run `launchers/run_app.ps1`
- **Windows (Batch):** Run `launchers/run_app.bat`
- **Lite Mode:** Run `python launchers/lite_launcher.py` for minimal UI
- **First-time Setup:** Run `python launchers/wizard.py` for guided configuration

## 📚 Documentation

Detailed guides can be found in the `docs/` directory:

### User Guides

- **[Natural Language Import](docs/text-import.md)**: How to use the text import feature.
- **[Character System](docs/character-flexibility.md)**: Deep dive into defining characters, traits, and signature colors.
- **[Interaction Templates](docs/interaction-templates.md)**: Creating complex multi-character scenes.
- **[Data Formats](docs/data-formats.md)**: Reference for `.md` and `.txt` file structures.

### Developer Guides

- **[Architecture](docs/architecture.md)**: System design and module overview.
- **[Development](docs/DEVELOPMENT.md)**: Setup, testing, and contribution guidelines.
- **[API Reference](docs/api.md)**: Internal class and method documentation.
- **[Compatibility](docs/COMPATIBILITY.md)**: Platform and version compatibility notes.
- **[Prompt Rating](docs/PROMPT_RATING_CRITERIA.md)**: Criteria for scoring prompt quality.

### Specialized Tools

- **[Auditing Suite](auditing/README.md)**: Quality assurance and distribution analysis.
- **[Automation](automation/README.md)**: Browser automation for image generation.
- **[Dev Tools](dev-tools/README.md)**: Migration and content generation utilities.

## 📂 Project Structure

```text
├── core/           # Prompt assembly & rendering logic
├── data/           # User content (71 characters, ~250 outfits, scenes, poses)
├── docs/           # Documentation guides
├── launchers/      # One-click startup scripts & setup wizard
├── logic/          # Business logic & data management (parsers, randomizer)
├── ui/             # Tkinter GUI components & controllers
├── utils/          # Logging, config, preferences, & templates
├── auditing/       # Quality assurance & distribution analysis tools
├── automation/     # Browser automation for image generation (Playwright)
├── dev-tools/      # Migration & content generation utilities
├── tests/          # Unit and integration tests
├── .config/        # User preferences & browser profiles
├── main.py         # Entry point
└── pyproject.toml  # Project metadata & configuration
```

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting bugs and submitting pull requests.

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
