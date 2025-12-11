# Data Directory

This directory contains all data files used by Prompt Builder.

## Structure

```
data/
├── base_prompts.md       # Base prompt templates
├── characters.md         # Character registry
├── outfits.md           # Outfit presets
├── poses.md             # Pose presets
├── scenes.md            # Scene presets
├── professional_woman.md # Professional woman templates
├── characters/          # Individual character files
│   ├── amira_character.md
│   ├── astrid_nielsen.md
│   └── ... (additional character files)
└── presets/             # User-created presets (gitignored)
```

## File Format

All data files use a markdown format with specific headers for parsing:

### Base Prompts (`base_prompts.md`)
```markdown
## PromptName
Prompt description text...
```

### Characters (`characters.md`, `characters/*.md`)
```markdown
## CharacterName
- **Name:** Full Name
- **Age:** Age
- **Ethnicity:** Ethnicity
- **Style:** Style description
- **Vibe:** Vibe description
```

### Presets (`outfits.md`, `poses.md`, `scenes.md`)
```markdown
## PresetName
Preset description text...
```

## Backward Compatibility

The application supports loading data files from both:
1. New location: `data/filename.md` (preferred)
2. Legacy location: `filename.md` (fallback)

This ensures existing installations continue working while new installations use the organized structure.

## User Data

User preferences and custom presets are stored separately:
- `preferences.json` - User settings (gitignored)
- `presets/` - User-created presets (gitignored)
