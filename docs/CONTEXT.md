# Prompt Builder - Project Context

## Overview

**Prompt Builder** is a desktop application for creating detailed, thematically coherent AI art prompts. It's designed for users generating images with Stable Diffusion, Midjourney, or similar tools who want consistent character representations across different scenes, outfits, and art styles.

**Core Philosophy**: Local-first, file-based, infinitely extensible. All content is stored as Markdown/text files, making it hackable and version-controllable.

## Primary Use Cases

1. **Character Consistency**: Generate prompts for the same character in different scenarios while maintaining visual consistency
2. **Bulk Generation**: Create large batches of thematically coherent prompts for training data or content creation
3. **Style Exploration**: Test characters across different art styles (Cyberpunk, Watercolor, Anime, etc.)
4. **Thematic Coherence**: Ensure outfits, poses, and scenes match stylistically (no medieval armor in cyberpunk scenes)

## Architecture Overview

### Entry Points

- **`main.py`** - Primary entry point, loads custom font and delegates to `Runner`
- **`runner.py`** - Application bootstrap, handles CLI args and launches Tkinter UI
- **`cli.py`** - Command-line interface (minimal usage)
- **`wizard.py`** - Setup wizard for new users

### Core Modules

#### `/core` - Prompt Assembly

- **`builder.py`** - Assembles final prompts from selected components
- **`prompt_generator.py`** - Generates prompt text with proper formatting
- **`summary_generator.py`** - Creates human-readable summaries

#### `/logic` - Business Logic

- **`data_loader.py`** - Loads all content from `/data` directory
- **`randomizer.py`** - **CRITICAL**: Monte Carlo randomization with thematic scoring
  - Generates candidate prompts and scores them for coherence
  - Implements blocking logic (e.g., `Block:Cyberpunk` prevents cyberpunk styles)
  - Tiered scoring: Mood matches (+30), Style alignment (+25), Tag matches (+5)
  - Mismatch penalty (-30) for incompatible combinations
- **`character_manager.py`** - Character CRUD operations
- **`outfit_manager.py`** - Outfit management and application
- **`interaction_manager.py`** - Multi-character interaction templates

#### `/ui` - Tkinter Interface

- **`main_window.py`** - Main application window
- **`character_gallery.py`** - Visual character browser with large previews
- **`outfit_panel.py`** - Outfit selection and modification
- **`summary_panel.py`** - Editable prompt summary
- **`controllers/`** - MVC controllers for UI logic

#### `/utils` - Runtime Utilities

- **`text_parser.py`** - Parses summaries and character descriptions
- **`character_summary.py`** - Generates character summaries
- **`preferences.py`** - User preferences management
- **`logger.py`** - Application logging

### Data Structure (`/data`)

#### Characters (`/data/characters/`)

- **71 characters** stored as `.md` files with photos
- Format: Name, tags, physical description, personality, base outfits
- Example: `priya_sharma.md`, `priya_sharma_photo.png`
- Tags enable filtering (e.g., `female`, `Indian`, `athletic`)

#### Outfits (`/data/outfits/`)

- **~250 outfits** organized in category folders
- Format: `.txt` files with gender-specific variants `[F]`, `[M]`, `[H]` (hijab)
- Tags for thematic matching (e.g., `Sport`, `Formal`, `Cyberpunk`)
- Categories: Casual Wear, Athletic & Sports, Formal Wear, Character & Costume, etc.

#### Content Files

- **`base_prompts.md`** - Art styles (20+ styles) with Mood/Block tags
  - Example: `Cyberpunk Neon (Mood:Futuristic, Block:Classical, Block:Formal)`
- **`scenes.md`** - Scene descriptions (~100 scenes) with thematic tags
- **`poses.md`** - Character poses (~80 poses) categorized by mood
- **`interactions.md`** - Multi-character interactions (~100 templates)
- **`modifiers.md`** - Outfit modifiers (e.g., Soccer → Goalie variant)
- **`color_schemes.md`** - Predefined color palettes
- **`framing.md`** - Camera angles and composition

### Key Directories (Post-Reorganization)

#### `/auditing` - Analysis Tools

- `generate_prompts_only.py` - Generate prompts without browser automation
- `tag_audit.py` - Analyze content distribution and identify gaps
- `prompt_distribution_analyzer.py` - Parse generated prompts for patterns
- `generate_sankey_diagram.py` - Visualize Scene → Style → Outfit flow

#### `/automation` - Browser Automation

- `automate_generation.py` - Selenium-based image generation via Google AI Studio
- `bulk_generator.py` - Batch processing

#### `/dev-tools` - Development Utilities

- `migrations/` - Data migration scripts
- `generators/` - Content generators (tags, summaries)
- `validators/` - Data validation tools

#### `/output` - Generated Content

- `images/` - Generated images
- `prompts/` - Generated prompt files with metadata
- `reports/` - Distribution analysis reports
- `logs/` - Application logs

#### `/.config` - Configuration

- `preferences.json` - User preferences
- `chrome_profile/` - Browser automation profile
- `temp/` - Temporary files

## Critical Features

### 6. Automation

**Path**: `automation/`

- **`ai_studio_client.py`**: Reusable Playwright client for Google AI Studio image generation. Handles persistent login and image extraction.
- **`automate_generation.py`**: Integration script combining prompt randomizer with the AI Studio client.
- **`bulk_generator.py`**: Tools for batch processing.

## Key Logic

### 1. Thematic Coherence System

**Problem**: Random selection creates incoherent combinations (e.g., Concert Hall + Cyberpunk style)

**Solution**: Multi-tiered scoring in `randomizer.py`:

```python
# Scoring weights (higher = more important)
Mood Match: +30 per match  # Outfit tags match scene moods
Style Alignment: +25 per match  # Art style matches scene theme
Interaction: +10 per match
Tag Match: +5 per match
Mismatch Penalty: -30  # Style blocks scene theme
```

**Blocking Logic**:

- Art styles have `Block:` tags (e.g., `Cyberpunk Neon` blocks `Classical`, `Historical`)
- Scenes have `Block:` tags (e.g., `Museum` blocks `Sport`, `Combat`)
- Prevents thematically incompatible combinations

### 2. Monte Carlo Randomization

Generates **50 candidate prompts**, scores each, selects best:

- Ensures variety while maintaining quality
- Exposes score and breakdown in metadata
- Enables auditing and improvement

### 3. Modular Outfit System

Outfits are **character-agnostic** and support:

- Gender variants (`[F]`, `[M]`, `[H]`)
- Color customization via `(signature)` or `(default:color)` tokens
- Modifiers (e.g., Soccer outfit + Goalie modifier)

### 4. Interaction Templates

Multi-character scenes with placeholders:

```
{char1} and {char2} in classic slow dance embrace
```

System fills in character names and handles grammar.

## Workflow

### Typical User Flow

1. Launch app (`python main.py`)
2. Browse character gallery, select characters
3. Apply outfits (individual or bulk)
4. Select scene, pose, art style
5. Click "Randomize All" for coherent combinations
6. Review summary, copy prompt
7. Generate image in external tool

### Developer/Power User Flow

1. Generate test batch: `python auditing/generate_prompts_only.py 50`
2. Analyze distribution: `python auditing/generate_sankey_diagram.py`
3. Identify gaps: `python auditing/tag_audit.py`
4. Add content to `/data` files
5. Re-test and verify improvements

## Recent Major Improvements

### Phase 10: Style-Scene Coherence (Latest)

- Added Mood/Block tags to 14 art styles
- Increased scoring weights (Style +15→+25, Mood +20→+30)
- Implemented -30 mismatch penalty
- **Result**: Scores jumped from 20-100 to 95-348 range
- Eliminated incoherent combinations (Concert Hall → Cyberpunk)

### Phase 9: Distribution Analysis

- Created Sankey diagram visualization
- Identified thematic mismatches
- Enabled data-driven content expansion

### Phase 8: Content Expansion

- Added Sci-Fi/Cyberpunk poses and scenes
- Added Sexy/Intimate theme content
- Cross-tagged existing outfits for better coverage

### Phase 7: Granular Scoring

- Implemented tiered scoring system
- Added score breakdown metadata
- Enabled transparency and debugging

## File Formats

### Character File (`.md`)

```markdown
# Character Name

tags: [female, Asian, athletic, modern]

## Physical Description

[Detailed description]

## Personality

[Personality traits]

## Base Outfits

- Outfit Name 1
- Outfit Name 2
```

### Outfit File (`.txt`)

```
tags: [Sport, Athletic, Casual]

[F]
- **Top:** Description
- **Bottom:** Description
- **Footwear:** Description

[M]
- **Top:** Description
...
```

### Scene Entry (`scenes.md`)

```markdown
- **Scene Name** (Theme1, Theme2, Mood:Energetic, Block:Formal):
  Detailed scene description with lighting, atmosphere, etc.
```

## Common Tasks

### Adding a New Character

1. Create `character_name.md` in `/data/characters/`
2. Add photo as `character_name_photo.png`
3. Restart app to load

### Adding a New Outfit

1. Create `.txt` file in appropriate `/data/outfits/` subfolder
2. Define `[F]`, `[M]`, `[H]` variants
3. Add thematic tags

### Adding a New Art Style

1. Edit `/data/base_prompts.md`
2. Add Mood and Block tags for coherence
3. Define rendering, character accuracy, details sections

### Debugging Low Scores

1. Run performance analysis: `python dev-tools/analyze_randomizer_performance.py --count 100 --threshold 250`
2. Generate human review samples: `python dev-tools/generate_human_review_samples.py`
3. Check score breakdown and retry tracking in report
4. Adjust tags or add blocking rules in `randomizer.py`

## Dependencies

- **Python 3.8+**
- **Tkinter** - GUI framework (usually bundled with Python)
- **Pillow** - Image handling
- **Selenium** - Browser automation (optional, for image generation)
- **Plotly** - Sankey diagram generation (dev tool)

## Configuration

- **Preferences**: Stored in `.config/preferences.json`
- **Window geometry, last selections, UI state**
- **No cloud sync, fully local**

## Testing

- Unit tests in `/tests`
- Smoke tests for bulk generation and gallery
- Tag coherence validation

## Key Constraints

1. **Local-first**: No external APIs, no cloud storage
2. **File-based**: All data in plain text for version control
3. **Extensible**: Users can add content without code changes
4. **Privacy**: No telemetry, no tracking

## Performance Notes

- Character gallery lazy-loads images
- Randomization uses Monte Carlo approach with up to 2 retries to meet **MIN_SCORE_FLOOR = 250**
- Large character libraries (70+) load quickly due to efficient caching

## Known Patterns

- **Character names**: `firstname_lastname.md` (lowercase, underscore)
- **Photos**: `character_name_photo.{png|jpeg}`
- **Outfit categories**: Folder names with double spaces (e.g., `Casual  Wear`)
- **Tags**: Case-sensitive, use Title Case for themes
- **Special tags**: `Mood:`, `Block:`, `Signature:` prefixes

## Future Considerations

- More art styles (currently 20+)
- More interaction templates
- Better outfit color scheme integration
- Pose + Scene compatibility scoring
- Export to different prompt formats (Midjourney vs SD)
