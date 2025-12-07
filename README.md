# AI Image Prompt Builder

A simple desktop application to help build complex and detailed prompts for AI image generation.

## How it works

This application is a data-driven prompt-building tool. It uses a set of user-editable markdown files as a database for different prompt components like characters, outfits, scenes, and poses.

The UI allows you to select these components, and the application will assemble them into a final prompt string that you can use with your favorite AI image generator.

## How to use

1.  **Run the application:**
    ```bash
    python main.py
    ```

2.  **Select a Character:** The application will load the characters from individual files in the `characters/` folder.

3.  **Choose an Outfit:** Outfits are loaded from `outfits.md` and character files in `characters/`.

4.  **Build a Scene:** Select different scene elements from `scenes.md`.

5.  **Choose a Pose:** Select a pose from `poses.md`.

6.  **Generate:** Click the "Generate" button to see the final prompt in the preview panel.

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

This file contains shared outfit templates.

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

### `poses.md` & `scenes.md`

These files contain presets for poses and scenes.

**Format:**

```markdown
## Category Name
- **Item Name:** description
```
