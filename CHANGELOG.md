# Changelog

## [Unreleased]

### Added
- **Export for LLM:** New utility to export a condensed catalog of characters, outfits, and poses along with system instructions. Designed for "knowledge injection" into LLMs to generate valid prompt configurations.
- **Victoria's Secret Magazine Base Prompt:** Added a new "High-Fashion Glamour" art style designed for high-end fashion photography aesthetics.
- **Natural Language Import:** New feature to import entire prompt configurations from raw text. Supports two formats: standard app summaries and a new structured LLM-friendly block format. Includes fuzzy character matching.
- **Robust Data Reload:** Improved the data reload function to force-clear all internal caches. Added **🔄 Reload Data** to the **File** menu for better visibility.
- **Import Button:** Added a quick-access 📥 Import button to the Prompt Summary header.
- **Auto-Tag Sync:** The application now automatically scans character files on startup (and reload) and adds any new, unknown tags to `tags.md`. This supports the workflow of manually adding character files.
- **Signature Colors:** Implemented a new system allowing characters to have a defined signature color (hex code). Outfits can now dynamically switch between a default color and the character's signature color using the `((default:Color) or (signature))` syntax.
- **UI Explorers:** Added two new visual summary tools accessible via the Help menu:
    - **Tag Distribution Explorer:** Visualizes tag usage statistics across the character database.
    - **Outfit Library Explorer:** Browse all available outfits, filter by category, and see which outfits support team colors or signature colors.
- **Bulk Edit:** Added "Use Signature Color" checkbox to the Bulk Edit panel in the Characters tab.
- **New Outfits:** Significantly expanded the outfit library with new categories:
    - **International:** Japanese Harajuku, African Print Contemporary.
    - **Fantasy Classes:** Knight, Paladin, Barbarian, Samurai, Wizard, Sorcerer, Necromancer, Druid, Thief, Assassin, Ninja, Priest, Hunter, Beastmaster, Red Mage, Monk, Bard, Alchemist, Engineer.
    - **Performance:** Vintage Tap, Oktoberfest.
    - **Historical:** Renaissance Noble.
    - **Period:** 1970s Disco.

### Changed
- **Character Data:** Updated all character profiles to include `**Signature Color:**` definitions and refined tag categorization. Added new character: **Ayame Shiratori**.
- **Outfit Data:** Updated existing outfits (Cyberpunk, Goth, etc.) to utilize the new Signature Color syntax.
- **Documentation:**
    - Added "Signature Colors" section to `docs/character-flexibility.md`.
    - Created `docs/data-formats.md` detailing file syntax and conventions for characters, outfits, and global assets.
- **Architecture:** Updated `docs/architecture.md` to include the new `OutfitSummary` component.

### Fixed
- **UI:** Improved `CharacterItem` to show a signature color swatch if applicable.

### Internal
- **Utils:** Added `utils/outfit_summary.py` for generating consolidated outfit data.
- **Docs:** Updated `data/tags.md` with clearer categorization.

- docs: comprehensive documentation overhaul to follow industry standards
- docs: added MIT LICENSE and CONTRIBUTING.md guidelines
- docs: reorganized docs/ directory with a central README index and legacy/ archive
- docs: added internal API Reference for developers
- docs: renamed documentation files to lowercase-kebab-case for consistency
- cleanup: removed redundant and temporary files from project root
- cleanup: fixed redundant exit call in `main.py`
- readme: completely rewritten with professional structure and detailed installation guide
- tests: strengthen import checks and add parser edge-case tests
- tests: add ThemeManager and notification unit tests (migration, reload, notify fallback)
- refactor: centralize startup in `runner.py` and simplify `main.py` to a runner shim
- cleanup: move legacy ad-hoc migration scripts to `scripts/archived/` to reduce repo clutter
- logging: revert default logger level to INFO and add debug logging via `--debug` / `debug_log.py`

