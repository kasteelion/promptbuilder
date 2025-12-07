# AI Image Prompt Builder

A desktop application to help build complex and detailed prompts for AI image generation with an intuitive, resizable interface.

## Features

- **📝 In-App Content Creation** - Create characters, scenes, outfits, poses, and base art styles directly in the UI
- **🎨 Smart UI Resizing** - Adaptive font scaling and proportional panel resizing for optimal viewing at any window size
- **⌨️ User Font Controls** - Adjust font size with keyboard shortcuts (`Ctrl++`, `Ctrl+-`, `Ctrl+0`)
- **📁 Organized Data Structure** - Individual character files with shared and character-specific outfits
- **🔄 Live Preview** - Real-time prompt generation with syntax highlighting
- **🎲 Randomization** - Randomize characters, poses, and prompts for creative inspiration
- **🌙 Theme Support** - Light and dark themes for comfortable viewing

## How it works

This application is a data-driven prompt-building tool. It uses a set of user-editable markdown files as a database for different prompt components like characters, outfits, scenes, and poses.

The UI allows you to select these components, and the application will assemble them into a final prompt string that you can use with your favorite AI image generator.

## How to use

1.  **Run the application:**
    ```bash
    python main.py
    ```

2.  **Select Characters:** Choose from individual character files in the `characters/` folder. Click "**+ Add to Prompt**" to add them to your group.

3.  **Choose Outfits:** Select from shared outfits or character-specific variations. The outfit selector is collapsible for a cleaner interface.

4.  **Build a Scene:** Select different scene elements from `scenes.md`. You can also create new scenes directly in the UI.

5.  **Choose a Pose:** Select a pose from `poses.md` or create custom poses.

6.  **Add Notes:** Include any additional details or modifications in the Notes tab.

7.  **Generate:** The preview panel automatically updates as you make selections, showing the final assembled prompt.

### Keyboard Shortcuts

- `Ctrl++` or `Ctrl+=` - Increase font size
- `Ctrl+-` - Decrease font size
- `Ctrl+0` - Reset font size to automatic scaling

### Creating New Content

Use the built-in creator dialogs to add new content:

- **Characters Tab:** "Create New Character" button - includes syntax suggestions based on existing characters
- **Characters Tab:** "Create New Base Style" button - template with 5 standard sections
- **Characters Tab:** "Create New Pose" button - add custom poses
- **Characters Tab → Bulk Outfit Editor:** "Create Shared Outfit" - outfits available to all characters
- **Characters Tab → Individual Character:** "Create Outfit" - character-specific outfit variations
- **Scenes Tab:** "Create New Scene" button - add scenes organized by category

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
├── base_prompts.md        # Base art style templates
├── outfits.md            # Shared outfit definitions
├── poses.md              # Pose presets
├── scenes.md             # Scene presets
├── characters/           # Individual character files
│   ├── character_name.md
│   └── ...
├── core/                 # Core prompt building logic
│   ├── builder.py        # PromptBuilder class
│   ├── models.py         # Data models
│   └── renderers.py      # Prompt rendering
├── logic/                # Data loading and validation
│   ├── data_loader.py
│   ├── validator.py
│   └── randomizer.py
├── themes/               # Theme management
│   └── theme_manager.py
└── ui/                   # User interface components
    ├── main_window.py    # Main application window
    ├── characters_tab.py # Character selection UI
    ├── scene_tab.py      # Scene selection UI
    ├── notes_tab.py      # Notes input UI
    ├── edit_tab.py       # File editor UI
    ├── preview_panel.py  # Prompt preview panel
    ├── character_creator.py  # Character creation dialog
    ├── scene_creator.py      # Scene creation dialog
    ├── base_style_creator.py # Base style creation dialog
    ├── outfit_creator.py     # Outfit creation dialogs
    └── pose_creator.py       # Pose creation dialog
```
