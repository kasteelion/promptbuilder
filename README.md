# Prompt Builder

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Project Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)]()

**Prompt Builder** is a powerful desktop application for crafting detailed, consistent AI art prompts. It combines a visual character gallery, dynamic tag filtering, and smart randomization to streamline your workflow for Stable Diffusion, Midjourney, and other generative AI tools.

Built with a **local-first** philosophy, all content—characters, outfits, poses—is stored as simple Markdown and Text files, making it infinitely extensible and hackable.

---

## 🌟 Key Features

- **🎨 Visual Gallery:** Browse your character library with large previews and instant selection.
- **🏷️ Smart Tag Filtering:** Find characters instantly by filtering tags (e.g., `female`, `fantasy`, `sci-fi`) with real-time search.
- **👗 Modular Wardrobe:** Apply unified outfit presets (defined in `.txt` files) to _any_ character. Mix and match with context-aware "Modifiers" (e.g., _Soccer_ outfit → _Goalie_ variant).
- **🎲 Coherence Engine:** Randomize styles, outfits, and poses while maintaining thematic consistency.
- **⚡ Bulk Actions:** Apply outfits, color schemes, or signature colors to multiple characters at once.
- **📝 Natural Language Import:** Paste raw text descriptions to auto-generate character data.
- **🕵️ Auditing Suite:** Built-in tools to score prompt quality, visualize distribution (Sankey diagrams), and verify data integrity.
- **🔒 Privacy Focused:** Runs 100% locally. No cloud, no tracking.

## 🚀 Quick Start

### 1. Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/promptbuilder.git
    cd promptbuilder
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 2. Launching the App

- **Terminal:** Run `python main.py`
- **Windows (No Terminal):** Double-click `launchers/run_app.vbs` to start silently.

## 📚 Documentation

Detailed guides can be found in the `docs/` directory:

- **[User Guide](docs/text-import.md)**: How to use the Natural Language Import feature.
- **[Character System](docs/character-flexibility.md)**: Deep dive into defining characters and traits.
- **[Interaction Templates](docs/interaction-templates.md)**: creating complex multi-character scenes.
- **[Data Formats](docs/data-formats.md)**: Reference for `.md` and `.txt` file structures.

### For Developers

- **[Architecture](docs/architecture.md)**: System design and module overview.
- **[Development](docs/development.md)**: Setup, testing, and contribution guidelines.
- **[API Reference](docs/api.md)**: Internal class and method documentation.

## 📂 Project Structure

```text
├── core/           # Prompt assembly & rendering logic
├── data/           # User content (Characters, Outfits, Poses)
├── docs/           # Documentation guides
├── launchers/      # One-click startup scripts
├── logic/          # Business logic & data management
├── ui/             # Tkinter GUI components
├── utils/          # Logging, config, & preferences
├── main.py         # Entry point
└── runner.py       # Application bootstrap
```

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting bugs and submitting pull requests.

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
