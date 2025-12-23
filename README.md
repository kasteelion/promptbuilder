# Prompt Builder

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Project Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)]()

Prompt Builder is a sophisticated desktop application designed to streamline the creation and management of detailed prompts, characters, themes, and presets for AI image-generation workflows (e.g., Stable Diffusion, Midjourney). It simplifies the construction of complex, multi-character prompts while ensuring consistency and creative flexibility.

Built with a "data-first" philosophy, the application uses human-readable Markdown files for all content, allowing for easy extension and customization without modifying code.

## 🌟 Key Features

*   **Intuitive GUI:** A professional, responsive Tkinter interface with collapsible panels and real-time feedback.
*   **Character Management:** A gallery-based selection system for managing extensive character libraries.
*   **Modular Character Design:** Refined "Ingredient-based" character descriptions for maximum flexibility across varied prompt contexts (e.g., Noir, Sports, Fantasy).
*   **Identity Locks:** Maintain character consistency by "locking" core physical traits separately from outfits or actions.
*   **Outfit Traits & Specializations:** A dynamic multi-select checkbox system for specialized gear (e.g., *Softball Face Mask*, *Volleyball Libero*, *Baseball Catcher*).
*   **Interaction Templates:** Use placeholders (e.g., `{char1}`, `{char2}`) to define complex multi-character scenes with cinematic framing.
*   **Structured Outfits:** Support for detailed outfit definitions with automatic "one-piece" detection and team color substitution.
*   **Optimized UX:** Advanced searchable comboboxes with keyboard navigation, auto-focus, and double-click shortcuts.
*   **Real-time Preview:** Instant prompt generation with adaptive validation and condensed summary view.
*   **Advanced Theming:** Built-in theme editor for customizing colors, fonts, and UI scaling.
*   **Extensible Data:** Add characters, scenes, and interactions simply by editing Markdown files.
*   **Privacy First:** Fully local execution with no cloud dependencies or tracking.

## 🚀 Getting Started

### Prerequisites

*   **Python 3.8 or higher**: [Download Python](https://www.python.org/downloads/)
*   **Tkinter**: Usually included with Python. On Linux, you may need to install it:
    *   `sudo apt install python3-tk` (Ubuntu/Debian)
    *   `sudo dnf install python3-tkinter` (Fedora)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/promptbuilder_github.git
    cd promptbuilder_github
    ```

2.  **(Optional) Create a virtual environment**:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies** (only standard library is required for core app, but some scripts use `Pillow`):
    ```bash
    pip install -r requirements.txt
    ```

### Running the App

Execute the main script to start the application:

```bash
python main.py
```

*For Windows users, see [LAUNCH.md](LAUNCH.md) for instructions on running the app without a terminal.*

## 📂 Project Structure

```text
├── core/           # Prompt assembly and rendering engine
├── logic/          # Data parsing, validation, and business logic
├── ui/             # Tkinter GUI components and controllers
├── utils/          # Shared utilities (logging, preferences, notifications)
├── data/           # Markdown-based content (characters, outfits, scenes)
├── tests/          # Automated test suite
└── docs/           # Detailed documentation and guides
```

## 🛠️ Development

For information on setting up a development environment, running tests, and contributing, please see:

*   **[Development Guide](docs/development.md)**
*   **[Contributing](CONTRIBUTING.md)**
*   **[Architecture Overview](docs/architecture.md)**

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Whether it's reporting a bug, suggesting a feature, or submitting a pull request, please see our [Contributing Guidelines](CONTRIBUTING.md) to get started.

## 📧 Contact

For support or questions, please open an issue on the GitHub repository.
