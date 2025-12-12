# AI Image Prompt Builder

A desktop application to help build complex and detailed prompts for AI image generation with an intuitive, resizable interface.

## Features

### Core Features
- **📝 In-App Content Creation** - Create characters, scenes, outfits, poses, and base art styles directly in the UI
- **🎨 Smart UI Resizing** - Adaptive font scaling and proportional panel resizing for optimal viewing at any window size
- **📁 Organized Data Structure** - Individual character files with shared and character-specific outfits
- **🔄 Live Preview** - Real-time prompt generation with syntax highlighting
- **🎲 Randomization** - Randomize characters, poses, and prompts for creative inspiration
- **🌙 Theme Support** - 8 themes including auto-detection for your OS dark/light mode

### Advanced Features
- **⏪ Undo/Redo** - Full undo/redo support (`Ctrl+Z`/`Ctrl+Y`) for all operations
- **💾 Presets** - Save and load entire prompt configurations (`Ctrl+Shift+S`/`Ctrl+Shift+O`)
- **🖱️ Context Menus** - Right-click characters for quick actions (duplicate, move, remove)
- **⚡ Batch Operations** - Clear all, reset outfits, apply poses to all characters at once
- **📋 Smart Copy** - Copy full prompt or individual sections (characters/scene/notes)
- **💡 Tooltips** - Helpful hints appear when hovering over UI elements
- **⌨️ 20+ Keyboard Shortcuts** - Fast workflow with extensive keyboard support
- **📤 Export/Import** - Share configurations as JSON files
- **🎓 Welcome Guide** - First-run tutorial to get you started quickly
- **💬 Better Errors** - User-friendly error messages with actionable suggestions
- **🎴 Visual Gallery** - Optional visual character browser with photo support (experimental)
- **🎴 Visual Gallery** - Optional visual character browser with photo support (experimental). Note: this feature has been deprecated/removed from the runtime; see `docs/VISUAL_UI_GUIDE.md` for archived implementation and migration notes.
- **🔍 Character Search** - Quick filter to find characters in large collections
- **🌊 Drag & Drop** - Reorder characters by dragging (in character list)
- **🤝 Interaction Templates** - Pre-built multi-character interaction templates (NEW!)

## Requirements

- **Python 3.8 or higher** (Tested on Python 3.8 through 3.14)
- **tkinter** (Usually included with Python, but may need separate installation on some Linux distributions)
- **Zero external dependencies** - Uses only Python standard library

### Installing tkinter (if needed)

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-tkinter
```

**macOS/Windows:** tkinter is included with standard Python installations

## How it works

This application is a data-driven prompt-building tool. It uses a set of user-editable markdown files as a database for different prompt components like characters, outfits, scenes, and poses.

The UI allows you to select these components, and the application will assemble them into a final prompt string that you can use with your favorite AI image generator.

## How to use

1.  **Run the application:**
    ```bash
    python main.py
    ```

2.  **Check compatibility (optional):**
    ```bash
    python main.py --check-compat
    ```
    This will display your Python version and verify all requirements are met.

3.  **Check version (optional):**
    ```bash
    python main.py --version
    ```

4.  **Select Characters:** Choose from individual character files in the `characters/` folder. Click "**+ Add to Prompt**" to add them to your group.

5.  **Choose Outfits:** Select from shared outfits or character-specific variations. The outfit selector is collapsible for a cleaner interface.

4.  **Build a Scene:** Select different scene elements from `scenes.md`. You can also create new scenes directly in the UI.

5.  **Choose a Pose:** Select a pose from `poses.md` or create custom poses.

6.  **Add Notes & Interactions:** Include any additional details in the Notes section. Use the **Interaction Templates** dropdown to quickly insert pre-built multi-character interactions like "Conversation", "Dancing Together", "High Five", etc. The template will automatically fill in with your selected characters' names.

7.  **Generate:** The preview panel automatically updates as you make selections, showing the final assembled prompt.

### Using Interaction Templates

The Notes section includes a powerful feature for creating multi-character interactions:

1. **Add your characters** to the prompt (at least 2 characters recommended)
2. **Select an interaction** from the dropdown (e.g., "Conversation", "Dancing Together", "Working Together")
3. **Click "Insert"** - the template will be added with character names filled in automatically

**Example:**
- Characters selected: Alice, Bob, Carol
- Template: "Group Discussion (3+)"
- Result: "Alice, Bob, and Carol engaged in group discussion, all contributing to conversation"

Available templates include:
- **Two-character interactions:** Conversation, Dancing Together, High Five, Handshake, Working Together, and more
- **Multi-character interactions:** Group Discussion, Circle Formation, Team Pose, Chain Reaction
- **Create your own:** Click "+ Create" to make custom interaction templates

6.  **Add Notes:** Include any additional details or modifications in the Notes tab.

7.  **Generate:** The preview panel automatically updates as you make selections, showing the final assembled prompt.

### Keyboard Shortcuts

**File Operations:**
- `Ctrl+Shift+S` - Save current configuration as preset
- `Ctrl+Shift+O` - Load a saved preset

**Editing:**
- `Ctrl+Z` - Undo last action
- `Ctrl+Y` - Redo last undone action

**View:**
- `Ctrl++` or `Ctrl+=` - Increase font size
- `Ctrl+-` - Decrease font size
- `Ctrl+0` - Reset font size to automatic scaling
- `Ctrl+G` - Toggle character gallery
- `Alt+R` - Randomize all selections

**Preview Panel:**
- `Ctrl+C` - Copy prompt to clipboard
- `Ctrl+S` - Save prompt to file

**Navigation:**
- `Tab` - Navigate between fields
- `Enter` - Add selected character to prompt

### Creating New Content

Use the built-in creator dialogs to add new content:

- **Characters Tab:** "Create New Character" button - includes syntax suggestions based on existing characters
- **Characters Tab:** "Create New Base Style" button - template with 5 standard sections
- **Characters Tab:** "Create New Pose" button - add custom poses
- **Characters Tab → Bulk Outfit Editor:** "Create Shared Outfit" - outfits available to all characters
- **Characters Tab → Individual Character:** "Create Outfit" - character-specific outfit variations
- **Scenes Tab:** "Create New Scene" button - add scenes organized by category
- **Notes & Interactions:** "+ Create" button - create custom multi-character interaction templates

All creator dialogs include copyable help text to assist with proper formatting.

## Data Files

The core of this application is the set of markdown files that it uses as a database. You can edit these files to add, remove, or modify the available options.

### `base_prompts.md`

This file contains base style prompts.

**Format:**

```markdown
## Prompt Name
Prompt content...
---
```

### Characters

Character definitions are stored as individual markdown files in the `characters/` folder. Each character gets its own file for better organization and maintainability.

**File naming:** Use lowercase with underscores (e.g., `mela_hart.md`, `nora_alvarez.md`)

**Format:**

```markdown
### Character Name
**Appearance:** description
**Outfits:**

#### Outfit Name
- **Top:** ...
- **Bottom:** ...
- **Footwear:** ...
- **Accessories:** ...
- **Hair/Makeup:** ...
```

**Example structure:**
- `characters/mela_hart.md` - Mela Hart's character definition
- `characters/nora_alvarez.md` - Nora Alvarez's character definition
- etc.

### `outfits.md`

This file contains shared outfit templates that can be used with any character.

**Format:**

```markdown
## Common Outfits
### Outfit Name
Outfit description...

## Character-Specific Variations
### Character Name
#### Outfit Name
Outfit description...
```

**Note:** Character-specific outfits can also be defined within individual character files in the `characters/` folder.

### `poses.md` & `scenes.md`

These files contain presets for poses and scenes, organized by category.

**Format:**

```markdown
## Category Name
- **Item Name:** description
```

## UI Resizing & Display

The application features an intelligent resizing system:

- **Adaptive Font Scaling:** Font size automatically adjusts based on window width using smart breakpoints (9-16pt range)
- **Proportional Panels:** Both the left (controls) and right (preview) panels resize proportionally for balanced viewing
- **Performance Optimized:** Font updates only trigger on significant size changes (50px+) to prevent excessive reconfiguration
- **User Control:** Override automatic scaling with manual font adjustments using keyboard shortcuts or the View menu

The resizing system ensures optimal readability whether you're using the app on a small laptop screen or a large desktop monitor.

## Project Structure

```
promptbuilder/
├── main.py                 # Application entry point
├── config.py              # Configuration constants and theme definitions
├── compat.py              # Python version compatibility utilities
├── base_prompts.md        # Base art style templates
├── outfits.md            # Shared outfit definitions
├── poses.md              # Pose presets
├── scenes.md             # Scene presets
├── characters/           # Individual character files
│   ├── character_name.md
│   └── ...
├── presets/              # Saved user presets
├── core/                 # Core prompt building logic
│   ├── builder.py        # PromptBuilder class
│   └── renderers.py      # Prompt rendering
├── logic/                # Data loading and validation
│   ├── data_loader.py    # Markdown file loading
│   ├── parsers.py        # Markdown parsing utilities
│   ├── validator.py      # Prompt validation
│   └── randomizer.py     # Random prompt generation
├── themes/               # Theme management
│   └── theme_manager.py  # Theme switching and color schemes
├── ui/                   # User interface components (modular architecture)
│   ├── main_window.py    # Main application coordinator (851 lines)
│   ├── menu_manager.py   # Menu bar creation and management
│   ├── font_manager.py   # Adaptive font sizing and resize handling
│   ├── state_manager.py  # Undo/redo and preset coordination
│   ├── dialog_manager.py # Centralized dialog management
│   ├── constants.py      # UI-specific constants (throttle delays, sizes)
│   ├── characters_tab.py # Character selection UI
│   ├── edit_tab.py       # File editor UI
│   ├── preview_panel.py  # Prompt preview panel
│   ├── widgets.py        # Custom widgets (CollapsibleFrame, FlowFrame)
│   ├── character_creator.py  # Character creation dialog
│   ├── scene_creator.py      # Scene creation dialog
│   ├── base_style_creator.py # Base style creation dialog
│   ├── outfit_creator.py     # Outfit creation dialogs
│   ├── pose_creator.py       # Pose creation dialog
│   ├── character_card.py     # Visual gallery character cards
│   ├── (visual_ui removed)    # Visual gallery mode deprecated and removed
│   └── searchable_combobox.py # Enhanced combobox widget
└── utils/                # Utility modules
    ├── logger.py         # Centralized logging
    ├── validation.py     # Input validation
    ├── preferences.py    # User preferences persistence
    ├── preset_manager.py # Preset save/load
    ├── undo_manager.py   # Undo/redo functionality
    ├── tooltip.py        # Tooltip widget
    └── *_templates.py    # Creator dialog templates
```

### Modular Architecture

The UI layer uses a **modular manager pattern** for improved maintainability:

- **MenuManager**: Handles all menu creation, theme switching, and menu state
- **FontManager**: Manages adaptive font scaling based on window size with breakpoint interpolation
- **StateManager**: Coordinates undo/redo operations and preset management
- **DialogManager**: Centralizes all user dialogs (welcome, about, shortcuts, errors) with consistent styling

This architecture reduces the main window from 1210 to 851 lines (~30% reduction) while improving code organization and testability.

## Troubleshooting

### "Python version too old" error

**Problem:** You see an error about Python version being too old.

**Solution:** Upgrade to Python 3.8 or higher:
- Windows: Download from [python.org](https://www.python.org/downloads/)
- macOS: `brew install python@3.12`
- Linux: `sudo apt-get install python3.12` (or use your distro's package manager)

### "tkinter not available" error

**Problem:** Application won't start due to missing tkinter.

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora/RHEL
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

On Windows/macOS, tkinter should be included with Python. If it's missing, reinstall Python from python.org.

### Character files not loading

**Problem:** Characters aren't showing up in the dropdown.

**Solution:**
1. Check that `.md` files exist in the `characters/` folder
2. Verify file format matches the expected structure (see README)
3. Run `python main.py --check-compat` to verify setup
4. Check console output for parsing errors

### Performance issues (lag during typing)

**Problem:** Application feels slow or laggy.

**Solution:** This has been fixed in the latest version with debouncing. Make sure you're running the latest code. If issues persist:
- Close other applications
- Try a smaller window size
- Check Python version (3.11+ recommended for best performance)

### Unicode/emoji display issues

**Problem:** Emoji characters don't display correctly.

**Solution:** This is typically a font issue. The application uses emojis in buttons and labels:
- Windows: Should work out of the box on Windows 10+
- macOS: Should work out of the box
- Linux: Install a font with emoji support (e.g., `fonts-noto-color-emoji`)

For more detailed compatibility information, see [COMPATIBILITY.md](COMPATIBILITY.md).

## Command-Line Options

```bash
python main.py              # Run normally
python main.py --version    # Show version info
python main.py --check-compat  # Check system compatibility
python main.py --debug      # Run in debug mode (shows full error traces)
```

## Contributing

Contributions are welcome! This project aims to maintain compatibility with Python 3.8+ and uses only standard library modules to minimize dependencies.

When contributing:
- Test on multiple Python versions if possible
- Use only standard library modules
- Include UTF-8 encoding declarations in new files
- Follow existing code style and patterns

## Changelog

### Version 2.0 (December 2025)
**Major UX Overhaul with 20+ new features!**

- ✅ Undo/Redo system (Ctrl+Z/Y)
- ✅ Presets & Templates (Save/Load configurations)
- ✅ Smart preferences (Auto-save settings)
- ✅ Auto theme detection (Follows OS dark/light mode)
- ✅ Enhanced copy options (Copy sections separately)
- ✅ Right-click context menus
- ✅ Batch operations (Clear all, reset outfits, apply poses)
- ✅ Tooltips throughout UI
- ✅ 20+ keyboard shortcuts
- ✅ Export/Import configurations (JSON)
- ✅ Live status updates
- ✅ User-friendly error messages
- ✅ Welcome screen for new users
- ✅ Collapsible sections
- ✅ Performance optimizations

### Version 1.0
- Initial release

---

## Contributing

Contributions are welcome! This project follows standard Python best practices:

- Python 3.8+ compatibility
- Zero external dependencies for core functionality
- Type hints where possible
- Centralized logging using the `utils.logger` module
- Modular architecture with specialized manager classes

See the documentation in the `docs/` directory for more technical details.

## Tests & CI

- **Run tests locally:**

```powershell
# From project root (Windows PowerShell)
C:/Users/parking/miniforge3/Scripts/conda.exe run -p C:\Users\parking\miniforge3 --no-capture-output python -m pytest -q
```

- **Run linters & formatters locally:**

```powershell
C:/Users/parking/miniforge3/Scripts/conda.exe run -p C:\Users\parking\miniforge3 --no-capture-output python -m isort .
C:/Users/parking/miniforge3/Scripts/conda.exe run -p C:\Users\parking\miniforge3 --no-capture-output python -m black .
C:/Users/parking/miniforge3/Scripts/conda.exe run -p C:\Users\parking\miniforge3 --no-capture-output python -m ruff check .
```

- **CI:** A GitHub Actions workflow is included at `.github/workflows/ci.yml` that runs formatting checks, linters, and `pytest` on pushes and pull requests to `master`.

If you want me to also add a pre-commit configuration or extend the CI matrix, tell me which tools/versions you prefer and I will add them.

## Documentation

- **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Keyboard shortcuts and quick tips
- **[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)** - Python version compatibility information
 - **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Keyboard shortcuts and quick tips
 - **[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)** - Python version compatibility information

**Note:** The Visual Gallery UI has been deprecated and removed from the codebase. Archived notes are available at `docs/VISUAL_UI_GUIDE.md` and `docs/VISUAL_UI_IMPLEMENTATION.md`.

## License

This project is open source. Feel free to use, modify, and distribute as needed.

## Acknowledgments

Built with Python's tkinter library for maximum compatibility and zero dependencies.


