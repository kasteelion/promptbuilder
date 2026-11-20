# Prompt Builder - Project Context

## Overview

**Prompt Builder** is a desktop application for creating detailed, thematically coherent AI art prompts. It's designed for users generating images with Stable Diffusion, Midjourney, or similar tools who want consistent character representations across different scenes, outfits, and art styles.

**Core Philosophy**: Local-first, file-based, infinitely extensible. All content is stored as Markdown/text files, making it hackable and version-controllable.

## Primary Use Cases

1. **Character Consistency**: Generate prompts for the same character in different scenarios while maintaining visual consistency.
2. **Bulk Generation**: Create large batches of thematically coherent prompts for training data or content creation.
3. **Style Exploration**: Test characters across different art styles (Cyberpunk, Watercolor, Anime, etc.).
4. **Thematic Coherence**: Ensure outfits, poses, and scenes match stylistically through a weighted scoring engine.

## Architecture Overview

### Entry Points

- **main.py** - Primary entry point. Initializes the Flet application and coordinates modular UI sections.

### Core Modules

#### /core - Prompt Assembly & Modeling

- **uilder.py** - Orchestrates final prompt assembly using specialized renderers.
- **models.py** - Pydantic models for structured data (CharacterDetails, PromptConfig, etc.).
- **pp_state.py** - Centralized state management and data synchronization.
- **enderers/** - Modular components for formatting specific prompt segments.

#### /logic - Business Logic & Data Management

- **data_loader.py** - Handles file system interactions, caching, and lazy loading.
- **andomizer.py** - **CRITICAL**: Monte Carlo randomization engine with thematic scoring.
- **controllers/** - Bridges UI events to state changes (e.g., CharacterController).
- **interaction_logic.py** - Complex logic for multi-character interaction templates.

#### /ui - Flet Interface

- **sections/** - Modular UI components (Toolbar, Gallery, Roster, Sidebar, Console).
- **dialogs/** - specialized overlay dialogs (Automation, LLM Export, Asset Editor).
- **let_theme_manager.py** - Manages the "Nebula" design system and electric azure styling.

#### /utils - Runtime Utilities

- **logger.py** - Application logging.
- **color_scheme.py** - Logic for signature colors and team palettes.
- **	ext_utils.py** - String sanitization and formatting.

### Data Structure (/assets/data)

#### Characters (/assets/data/characters/)

- **70+ characters** stored as .md files with corresponding .png photos.
- Format: Appearance, personality, signature color, and base outfits.
- Tags enable semantic filtering (e.g., emale, Indian, thletic).

#### Outfits (/assets/data/outfits/)

- **~250 outfits** organized in categorized subfolders.
- Format: .txt files with [F], [M], and [H] (hijab) blocks.
- Supports dynamic placeholders like {primary_color} and {signature_color}.

#### Content Files

- **ase_prompts.md** - Art styles with thematic Mood/Block tags.
- **scenes.md** - Detailed scene descriptions with environmental tags.
- **poses.md** - Character poses categorized by mood and activity.
- **interactions.md** - Multi-character templates with placeholders ({char1}, {char2}).

## Key Logic

### 1. Thematic Coherence System (Randomizer)

The system ensures quality through a multi-tiered scoring engine:

- **Mood Match (+30)**: Outfit tags match scene mood.
- **Style Alignment (+25)**: Art style matches scene theme.
- **Diversity Bonus (+10)**: Rewarding variety in group shots.
- **Mismatch Penalty (-100)**: Constraint violations (e.g., Swimwear in an Office).
- **Genre Clash (-1000)**: Critical firewall between incompatible worlds (e.g., Fantasy vs. Tech).

### 2. Scenario-First Randomization

Instead of purely random picks, the system selects a **Scenario** first, which defines:
- Required/Allowed scene categories.
- Role slots for characters.
- Vibe tags and blocked global tags.

## Workflow

### Typical User Flow
1. **Browse**: Filter and select characters in the visual gallery.
2. **Configure**: Customize outfits, poses, and color schemes in the roster.
3. **Contextualize**: Set the scene, base prompt, and interaction notes in the sidebar.
4. **Iterate**: Use "Randomize All" to find high-scoring coherent combinations.
5. **Generate**: Copy the prompt or launch AI Studio automation for image creation.

---

*Last updated: May 2026*

