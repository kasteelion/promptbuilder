# Changelog

## [1.1.0] – 2026-11-19

### Added
- **Target Engine Output Profiles:** Added dedicated generator engines in `core/builder.py` and a 4-way format toggle in `console.py`:
  - `[MJ]` **Midjourney Profile:** Formats prompts into clean, comma-separated tokens without Markdown syntax, automatically appending `--ar 16:9 --v 6.1 --stylize 250`.
  - `[SDXL]` **Stable Diffusion XL Profile:** Emits weighted tokens `(token:1.2)`, `BREAK` segment chunks, and derives automatic photographic or anime negative prompts.
  - `[🍌 Prose]` **Banana / Natural Language Prose:** Generates fluid natural-language narrative paragraphs tailored for Google Imagen 3 and Gemini.
  - `[Markdown]` **Structured Markdown:** Classic categorized output with bold headers and bullet points.
- **FIFO Prompt History Buffer:** Added a 20-item `collections.deque` buffer in `console.py` with auto-scrolling preview chips, click-to-restore with undo capability, and a clear action.
- **Smart 1-Click Suggestion Engine:** Introduced `SuggestionEngine` (`logic/suggestion_engine.py`) offering context-aware recommendations for missing Scenes, Multi-Character Interactions (names auto-resolved), Wardrobe upgrades, and Coordinated Palettes.
- **Thematic Alignment & Prompt Completeness Model:** Replaced vocabulary-ratio formula with a multi-dimensional prompt cohesion model scoring character baseline (20%), scene setting (+25-35%), wardrobe customization (+15%), interactions (+15%), color harmonies (+10%), and art styles (+5%) with dynamic color feedback.
- **Color Palette & Contrast System:** Added live wardrobe color swatches with character signature colors and curated Quick Color Harmonies (Maroon & Khaki, Olive & Rust, Navy & Amber, etc.) applicable across the active roster.
- **Automation Studio Target Profiles:** Added engine profile selection dropdown (`Markdown`, `Prose`, `Midjourney`, `SDXL`) to `AutomationDialog`, `AutomationOrchestrator`, and `GemmaPipelineRunner`.
- **CLI Batch Automation Formats:** Added `--format [markdown|prose|midjourney|sdxl]` CLI parameter to `scripts/automation/automate_generation.py` and `scripts/automation/bulk_generator.py`.
- **Automation Suite Standardization & Hardening:**
  - Consolidated browser automation: Replaced duplicate 338-line `scripts/automation/ai_studio_client.py` with a clean backward-compatible facade re-exporting canonical `src/utils/ai_client.py`.
  - Added concurrency guard in `AutomationOrchestrator.start_generation()` preventing duplicate thread launches or race conditions (`is_running()` check).
  - Gated background portrait scanning behind `auto_generate_missing_portraits` preference (default `False`), preventing unsolicited browser launches on app start.
  - Sanitized target engine prompt prefixing in `gemma_pipeline.py` to preserve raw Midjourney (`/imagine`) and SDXL syntax.
  - Relocated 11 legacy one-off tag migration scripts from `scripts/automation/` to `scripts/maintenance/legacy_tag_migrations/`.
- **New Pose Presets:** Added *Playful Hair Twirl* (Casual & Domestic), *Playful Prone Bed Lounge* (Intimate & Sensual), and *Overhead Dreamy Surrender* (Intimate & Sensual) to `assets/data/poses.md`.
- **Inline Outfit Preset Dropdown:** Added direct preset outfit selection (`Outfit Preset` dropdown) on each active character card in `RosterItem`, enabling instant 1-click wardrobe swaps without requiring the modal `OutfitBuilderDialog`.
- **Gallery Quick Archetype Filter Chips:** Added interactive filter pills (`All`, `Female`, `Male`, `Chic`, `Athletic`, `Casual`, `Approachable`) above the gallery row to quickly narrow down the 83 characters.
- **Gallery Active Roster Counter:** Enhanced gallery counter badge to display both available matches and staged count (`83 available • 1 in roster`).
- **Prompt Completeness & Cohesion Rebranding:** Renamed "Thematic Alignment" to "Prompt Completeness" with an explanatory tooltip to clearly convey structural prompt readiness across all 6 layers.
- **Roster "Clear All" Undo Protection:** Added non-destructive undo capability to `clear_all_characters` via a snackbar toast with an `UNDO` action.
- **Modal Dialog Header Close Buttons:** Added explicit "✕" close icon buttons to the headers of `SettingsDialog` and `AutomationDialog` for desktop ergonomics.
- **Photorealism & Tactical Skin Directives:** Modernized `Studio Photorealism` base prompt in `assets/data/base_prompts.md` with tactile optical specifications (raw 85mm optics, dermal micro-pores, fine vellus hair, authentic specular sheen) and aggressive negative prompting against plastic, porcelain, and 3D CGI airbrushing; removed `grain` suppression.
- **Multi-Character Spatial Depth Staging:** Upgraded `generate_prose` in `src/core/builder.py` with multi-plane depth cues (foreground focus, mid-ground placement, background spatial anchoring) to prevent flat horizontal lineup compositions in multi-subject scenes.
- **Automation Pipeline Defaults:** Configured `AutomationDialog` to default batch generation to the narrative **Prose Engine (`[🍌 Prose]`)** and enabled **Gemma AI Enhancement** by default for maximum diffusion compositional coherence.
- **Automation Studio Launch Acceleration:** Slashed `AutomationDialog` launch latency from ~2.5s down to 14ms by virtualizing `ListView` rendering (`item_extent=32`), flattening nested container controls, implementing progressive batch loading (25 initial rows with background hydration), and caching the dialog instance in `main.py`.
- **Automation Candidate Pool Integrity:** Fixed bug where forcing a character without selecting pool checkboxes inadvertently restricted the candidate pool to only the forced character, enabling multi-character scenes to draw from all characters as intended.
- **Randomizer Multi-Character Aesthetic Anchoring:** Added anchor genre tracking across multi-subject scenes in `PromptRandomizer._generate_single_candidate` and `_randomize_character_with_role`, aligning group wardrobes to compatible aesthetic axes and filtering out discordant collisions (e.g. Western + Cyberpunk or Cottagecore + Combat Armor).
- **Peaceful Scene Wardrobe Enforcement:** Added automatic pre-filtering against tactical gear, combat armor, weapons, and spacesuits in domestic, home, bedroom, coffee, and library scenes within `PromptRandomizer`.
- **Scoring Engine Genre & Action Calibrations:** Upgraded cross-character outfit incoherence penalty from `-100` to `-300 * extra_genres` in `ScoringEngine.score_candidate`, and added an action-scene energy mismatch check penalizing combat/sprint/diving actions in quiet domestic scenes by `-150`.
- **Extended Genre Standards:** Expanded `assets/config/tag_rules.json` with canonical genre clusters for `GENRE_SCIFI`, `GENRE_CASUAL`, and `GENRE_HISTORICAL`.
- **Calibrated Heuristic Auto-Pass Floor:** Added high-confidence auto-passing in `GemmaPipelineRunner` for prompts scoring $\ge 400$ with zero warnings/penalties, passing pristine candidates in <1ms without calling the local LLM.
- **In-Memory Critic Audit Cache:** Implemented hash-based in-memory caching in `GemmaPipelineRunner` (`_audit_cache`) for `(scene, outfits, art_style)` profiles, eliminating redundant LLM evaluations during batch automation runs.
- **Critic Inference Acceleration:** Reduced `audit_prompt` local Ollama timeout from 180s to 35s and capped `num_predict=256` in `GemmaClient`, accelerating critic inference cycles by ~50% and preventing token runaway.

### Fixed
- **Flet 0.80 Web Dialog Lifecycle:** Modernized dialog invocation in `main.py` (`_open_dialog` / `close_dialog`) to prioritize `page.show_dialog()` and `page.pop_dialog()`, restoring modal dialogs (Settings, Automation Studio, Context Studio, Outfit Builder) in Flet 0.80 web sessions.
- **Roster & Console Flex Constraints:** Assigned explicit integer flex weights (`roster.expand = 6`, `console.expand = 5`) to prevent lengthy generated prompts in the Console from collapsing the Active Roster into an unreadable sliver.
- **Streamlined Single-Character Roster:** Conditionally hidden the bulk operations toolbar when only one character is staged (`len(items) >= 2`), maximizing card interaction space.
- **Character Card Typography & Ellipsis Truncation:** Re-architected gallery cards to give names full horizontal container width and merged age into subtitle traits (`mid-20s • Female • Approachable`), eliminating ellipsis truncation on character names.
- **First-Frame Gallery Initialization:** Invoked `self.gallery.refresh(update_ui=False)` during `build_ui()` so all 83 characters render instantly on the initial frame using fast metadata cache.
- **Sidebar Ergonomics & Suggestion Prominence:** Relocated the Thematic Alignment meter and context-aware 1-Click Suggestions to the top of the sidebar above the fold, ensuring immediate feedback on character additions.
- **Art Style Chip Indicators:** Added visual checkmark and semi-bold typography to the active art style pill, with guarded dictionary resolution.
- **Character Load Latency:** Cached `DataLoader.load_outfits()` via `self._cache["shared_outfits"]`, slashing individual character load times from 135ms to 2ms (eliminating redundant disk scans of 280+ files on every roster click).
- **Startup Frame Latency:** Added fast metadata preloading (`load_metadata_fast()`) in `AppState` before `build_ui()`, ensuring characters render on the very first frame.
- **Ollama & Cloud AI Fallback Resilience:** Fixed Ollama auto-detection selecting corrupted/unsupported models (e.g. `gemma4:latest`) by prioritizing verified models (`gemma2:latest`, `gemma3:latest`) and respecting user-configured preferences; added multi-model local retry on error and detailed error message extraction; intercepted `API_KEY_INVALID` to fail fast with Settings guidance; added graceful fallback to PromptRandomizer in `GemmaPipelineRunner` if AI inference fails.
- **Gallery Double-Render:** Removed duplicate 30-line post-click loop in `gallery.py` that caused redundant roster, preview, and gallery rebuilds.
- **Async & Threading Safety:** Migrated background UI calls in `main.py` and `app_state.py` to `page.run_task()`, wrapped blocking AI calls in `asyncio.to_thread()`, and eliminated unattached Flet control update crashes.
- **Automation Pydantic Model Crashes:** Fixed `AttributeError` crashes in `automate_generation.py` (`char.get('name')`), `bulk_generator.py` (`char_outfits = chars[real_name].get('outfits')`), and `gemma_pipeline.py` (`config.scene`, `config.selected_characters`).

### Tests
- Added `tests/test_builder_profiles.py` (Midjourney, SDXL, and Negative Prompt tests).
- Added `tests/test_suggestion_engine.py` (Recommendation engine tests).
- Added `tests/test_thematic_alignment.py` (Progression and cohesion model tests).
- Added `tests/test_automation_pipeline.py` (Batch generator and multi-engine format tests).
- Test suite expanded to 62 passing tests.

## [1.0.0] – 2026-04-11

### Fixed

- **Debug Prints:** Replaced 3 leftover `print(f"DEBUG:...")` statements in `app_state.py`, `flet_theme_manager.py`, and `interaction_logic.py` with proper `logger` calls.
- **Deprecated Widgets:** Replaced all 7 remaining `ft.ElevatedButton` instances with `ft.FilledTonalButton` across dashboard, dialogs, and gallery explorer.
- **Duplicate Dataclass Fields:** Removed duplicate `blocked_global_tags` and `default_style_tags` field declarations in `Scenario` dataclass (`scenarios.py`).
- **LLM Export Dialog:** Wired up the "LLM Export" menu item to the existing `LLMExportDialog` (was showing "Coming Soon" toast despite dialog being implemented).
- **Content Guide Dialog:** Wired up the "Content Guide" menu item to the existing `LLMContentCreationDialog`.
- **Prompt Quality – _expanded_tags Leak:** Internal `_expanded_tags` metadata no longer appears in generated prompt output. Added regex post-processing in `builder.py`.
- **Prompt Quality – {Color} Placeholders:** Unresolved `{Color}` and `{Style}` placeholders are now stripped from final output if color scheme substitution didn't resolve them.
- **Duplicate Imports:** Removed duplicate import block in `builder.py`.
- **Gallery Explorer:** Removed duplicate `_build_ui()` call that was initializing UI twice.

### Improved

- **Thematic Alignment Meter:** Replaced the hardcoded 65-95% fake quality meter with real tag intersection scoring between character tags/vibes and scene keywords.
- **Asset Editor Metadata Tab:** Replaced "Coming Soon" placeholder with helpful guidance pointing users to character `.md` files.
- **PromptConfig Model:** Added missing `scene_category`, `scene_preset`, `interaction_category`, and `interaction_preset` fields.

### Cleaned

- **Root Directory:** Moved 12+ orphaned debug/audit files (`debug_output.txt`, `audit_log.txt`, `final.txt`, etc.) out of project root into `auditing/artifacts/` or deleted them.
- **Legacy Test Scripts:** Moved `test_gen.py` and `test_live.py` (stale API references) to `auditing/` as legacy artifacts.
- **`.gitignore`:** Updated patterns to prevent debug/temp file clutter. Removed overly broad `test_*.py` glob that was gitignoring real test files.
- **`requirements.txt`:** Rewritten to accurately list Flet + Pydantic as runtime dependencies (was still referencing tkinter/Python 3.8).

## [0.9.0] – 2026-02-21

### Added

- **Automation Dialog:** Stop button to halt background generation mid-run.
- **Output Gallery:** Refresh, Open Folder, and Delete buttons for better file management.
- **Console Theme Support:** Console section now responds to theme switching via `ThemeManager`.
- **Gallery Theme Support:** Gallery section now updates header text and count label on theme change.
- **Outfit Builder Dialog:** New dialog for assembling outfits from templates with variable interpolation.
- **Asset Editor Dialog:** New dialog for editing character assets directly within the app.
- **Import Text Dialog:** New dialog for importing prompt configurations from raw text.
- **Debouncer Utility:** 300ms debounce for sidebar text fields to reduce unnecessary updates.
- **Character Logic Module:** Extracted character lifecycle logic into dedicated `CharacterLogic` class.

### Fixed

- **Critical: Bearing parser bug** — `bearing` field was present in all 82 character files but never extracted by the parser. Root cause: regex lookahead `(?:\n\s*\*\*|$)` couldn't match `//` comments or `---` dividers that follow the field. Fixed all three Tier-3 field regexes (`_BEARING_RE`, `_VIBE_RE`, `_AGE_PRESENTATION_RE`).
- **TypedDict sync** — Added missing `age_presentation`, `vibe`, and `bearing` fields to `CharacterData` in `definitions.py`.
- **Missing type imports** — Added `List`, `Dict`, `Any` imports to `interaction_logic.py`.
- **Duplicate config** — Removed duplicate `DEFAULT_THEME = "Dark"` assignment in `config.py`.
- **Stale welcome message** — Updated `WELCOME_MESSAGE` to reference Flet features instead of removed Tkinter shortcuts (Ctrl+Z/Y, Alt+R, right-click).
- **Toolbar layout** — Changed `MainAxisAlignment.START` to `SPACE_BETWEEN` so action buttons spread across the toolbar.
- **Automation performance** — Controller now reuses app's cached `builder` and `randomizer` instead of re-reading 12 files from disk per generation.
- **Deprecated widgets** — Replaced `ft.ElevatedButton` with `ft.FilledButton` across dialogs.

### Removed

- **Debug prints** — Removed 8 active `DEBUG_ROSTER`, `DEBUG_CLICK` prints from UI components.
- **Duplicate comment** — Removed duplicate `# --- Surgical Update ---` block in `roster_item.py`.

### Changed

- **Character data** — Updated 82 character files with refined descriptions, tags, and outfit definitions.
- **Standards** — Updated `CHARACTER_STANDARDS.md`, `OUTFIT_STANDARDS.md`, `POSE_STANDARDS.md`, `SCENE_STANDARDS.md`.
- **Outfits** — Updated 38 shared outfit template files across Athletics, Casual, Fantasy, and other categories.

## [Unreleased]

### Added

- **Refactored Logging:** Added verbose debug logging for randomizer auditing tools.

### Changed

- **Randomizer Simplification (Phase 1-3):** Streamlined the generation algorithm by introducing scoring simplifications, pose selection coherence, and extensive caching mechanisms. This results in ~50% faster scoring and eliminates redundant logic.
- **Tag Normalization:** Standardized all character tag casing to lowercase for better system predictability and easier matching during generation. Over 80 character files updated with detailed traits and unified tags.

### Fixed

- **Audit Reports:** Fixed various warnings related to tag casing and redundancy metrics.

---

## [0.9.0] – 2026-02-21

### Added

- **Directory Structure:** Standardized codebase by moving core logic to `src/`, user data to `assets/data/`, and scripts to `scripts/`.
- **Cleanup:** Removed dead code in `archive/` and unified `sys.path` handling in `main.py`.

### Added

- **Asset Refresh:** Added a "Refresh Assets" button to the toolbar to hot-reload character data and settings without restarting the application.
- **Smart Randomization Coherence:** Implemented "Cascading Context" logic where tags from the selected Base Style (e.g., "Sports Action") strictly enforce thematic consistency in subsequent selections (Poses, Outfits).
- **Strict Theme Filtering:** The randomizer now prioritizes exact tag matches over generic ones, significantly improving the logical consistency of generated prompts (e.g., ensuring "Sports" styles only select "Sports" poses).
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
  - **Athletic:** LFL Performance Uniform, Tech-Athletic Compression, Street-Dance Set.
  - **Alternative:** High-Gloss Tech-Suit, Tactical Scout.
  - **Professional:** Modern Power Suit.
  - **Formal:** Sculpted Bandage Set.
  - **International:** Japanese Harajuku, African Print Contemporary.
  - **Fantasy Classes:** Knight, Paladin, Barbarian, Samurai, Wizard, Sorcerer, Necromancer, Druid, Thief, Assassin, Ninja, Priest, Hunter, Beastmaster, Red Mage, Monk, Bard, Alchemist, Engineer.
  - **Performance:** Vintage Tap, Oktoberfest.
  - **Historical:** Renaissance Noble.
  - **Period:** 1970s Disco.

### Changed

- **Performance Optimizations:**
  - **Lazy Loading:** UI tabs (like Edit Data) are now initialized on-demand to reduce initial startup time.
  - **Async Image Engine:** Character gallery now uses a shared `ThreadPoolExecutor` for background image loading, preventing UI lag and reducing system resource usage.
  - **Optimized Rendering:** Improved scroll region updates and batched rendering for smoother gallery navigation.
- **Character Data:** Updated all character profiles to include `**Signature Color:**` definitions and refined tag categorization. Added new character: **Ayame Shiratori**.
- **Outfit Data:** Updated existing outfits (Cyberpunk, Goth, etc.) to utilize the new Signature Color syntax.
- **Documentation:**
  - Added "Signature Colors" section to `docs/character-flexibility.md`.
  - Created `docs/data-formats.md` detailing file syntax and conventions for characters, outfits, and global assets.
- **Architecture:** Updated `docs/architecture.md` to include the new `OutfitSummary` component.

### Fixed

- **Images Path:** Fixed an issue where generated images were saving to `src/output` instead of the project root `output/`.
- **Themes Loading:** Resolves `themes.md` correctly from `assets/data/lists/`.
- **Legacy Cleanup:** Removed unused legacy code and consolidated scripts into `scripts/`.
- **UI:** Resolved persistent hover highlighting issues on pill buttons and chips.
- **Theme Compliance:** Fixed hardcoded colors (#333333, #666666) across all UI components.
- **Typography:** Unified application font to "Lexend" (replacing Segoe UI/Consolas).
- **Dialogs:** Ensured consistent theming for all modal dialogs via `ThemeManager`.
- **SearchableCombobox:** Added full theme support including hover states and placeholders.
- **Theme Contrast:** Improved accessibility for Nord, Monokai, and One Dark themes by adjusting border and text background contrast while maintaining palette authenticity.
- **UI:** Improved `CharacterItem` to show a signature color swatch if applicable.
- **Data Standardization:** Renamed `Sport` tags to `Sports` in `data/poses.md` and standardized category names for reliable matching.
- **Base Prompts:** Refined tags for "Sports Action" style to remove ambiguous terms, preventing unrelated pose selection.

### Refactored

- **MainWindow Decomposition:** Broken down the monolithic `MainWindow` into reusable functional components: `ScenePanel`, `NotesPanel`, and `SummaryPanel`.
- **Declarative Theming:** Implemented a central Theme Registry in `ThemeManager`. Widgets now subscribe to theme updates, eliminating manual update loops and improving responsiveness to theme changes.
- **Logic Extraction (Controllers):** Extracted business logic from UI classes into dedicated controllers:
  - `PromptController`: Handles prompt generation, summary assembly, and validation.
  - `CharacterController`: Manages character lifecycle operations (add, duplicate, remove) and file updates.
  - `DataController`: Orchestrates data loading, syncing, and lifecycle management.
- **Dependency Injection:** Improved modularity by passing managers and controllers explicitly via constructors, reducing tight coupling to the root window.

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
