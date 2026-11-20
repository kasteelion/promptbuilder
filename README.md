# Prompt Builder

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Project Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)]()

**Prompt Builder** is a powerful desktop application for crafting detailed, consistent AI art prompts. It combines a visual character gallery (71 characters), dynamic tag filtering, and smart randomization to streamline your workflow for Stable Diffusion, Midjourney, and other generative AI tools.

Built with a **local-first, zero-dependency** philosophy, all contentâ€”characters, outfits (~250 across 25 categories), posesâ€”is stored as simple Markdown and Text files, making it infinitely extensible and hackable.

## ðŸ–¼ï¸ Visual Preview

![Dashboard Overview](file:///C:/Users/parking/.gemini/antigravity/brain/5e378a55-535e-4e86-a93f-f13788a81175/main_dashboard_1772257040774.png)
_A sleek, modern interface designed for visual clarity and rapid prompt iterative design._

---

## 🌟 Key Features

- **🎯 Target Engine Output Profiles:** Seamlessly switch prompt generation modes on the fly:
  - **Midjourney:** Clean comma-separated tokens, stripped markdown, auto-appended parameters (--ar 16:9 --v 6.1 --stylize 250).
  - **SDXL:** Weighted token syntax (token:1.2), BREAK chunks, and automatic negative prompt extraction.
  - **Banana Prose:** Natural language narrative prose optimized for Google Imagen 3 and Gemini.
  - **Structured Markdown:** Rich categorized blocks with headers and bulleted descriptions.
- **📜 FIFO Prompt History Strip:** 20-entry FIFO buffer in the console with preview chips, click-to-restore, and undo.
- **💡 Smart Suggestion Engine:** Context-aware 1-click recommendations for missing scenes, multi-character interactions, thematic wardrobe, and coordinated palettes.
- **📊 Real-time Thematic Alignment:** Multi-dimensional prompt completeness meter dynamically scoring character cohesion, environment, wardrobe, interactions, and color harmony.
- **🎨 Color Palette & Contrast:** Live wardrobe swatches with character signature colors and curated Quick Color Harmonies (Maroon & Khaki, Olive & Rust, etc.).
- **🖼️ Visual Gallery:** Browse your character library with high-res portraits, instant multi-character selection, and sub-millisecond fast loading.
- **🏷️ Smart Tag Filtering:** Find characters instantly by filtering tags (e.g., female, fantasy, sci-fi) with real-time search.
- **👗 Modular Wardrobe:** Apply unified outfit presets to any character. Mix and match with context-aware 'Modifiers'.
- **🎲 Coherence Engine:** Randomize styles, outfits, and poses while maintaining thematic consistency through cascading context and a quality floor.
- **⚡ Automation Studio:** Batch prompt and image generation via browser automation with full target engine format support.
- **✨ Gemma AI Integration:** Enhance and flesh out your structured prompts instantly using local Ollama or the official Google GenAI SDK.
- **🔒 Privacy Focused:** Runs 100% locally. No mandatory cloud, no tracking.

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

    # For Gemma Prompt Enhancer (optional)
    pip install google-genai requests

    # For development tools (optional)
    pip install -r requirements-dev.txt
    ```

### 2. Launching the App

- **Terminal:** Run `python main.py`
- **Windows (Silent):** Double-click `launchers/run_app.vbs` (no console window)
- **Windows (PowerShell):** Run `launchers/run_app.ps1`
- **Windows (Batch):** Run `launchers/run_app.bat`
- **Web Browser Mode:** Run `python main.py --web`

## ðŸ“š Documentation

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

## ðŸ“‚ Project Structure

```text
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ core/           # Prompt assembly & rendering logic
â”‚   â”œâ”€â”€ logic/          # Business logic & data management
â”‚   â”œâ”€â”€ ui/             # Flet GUI components & controllers
â”‚   â””â”€â”€ utils/          # Logging & config
â”œâ”€â”€ assets/
â”‚   â””â”€â”€ data/           # User content (characters, outfits, scenes)
â”œâ”€â”€ docs/               # Documentation guides
â”œâ”€â”€ scripts/            # Utility scripts
â”œâ”€â”€ auditing/           # Quality assurance tools
â”œâ”€â”€ automation/         # Browser automation
â”œâ”€â”€ tests/              # Unit and integration tests
â”œâ”€â”€ logs/               # Application logs
â”œâ”€â”€ main.py             # Entry point
â””â”€â”€ pyproject.toml      # Project metadata
```

## ðŸ¤ Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting bugs and submitting pull requests.

## ðŸ“œ License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

