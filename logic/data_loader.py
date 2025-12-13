"""Data loading utilities for markdown files."""

from pathlib import Path


from .parsers import MarkdownParser


class DataLoader:
    """Loads markdown files from the same directory as this script (or cwd)."""

    def __init__(self):
        # Use Path(__file__).parent to get the script's directory
        # This is more secure than using sys.argv[0] which can be manipulated
        try:
            # Get the directory containing this module
            module_dir = Path(__file__).parent
            # Go up one level to get the project root
            self.base_dir = module_dir.parent
        except (NameError, AttributeError):
            # Fallback for environments where __file__ is not defined (e.g., interactive shells)
            import sys

            try:
                self.base_dir = Path(sys.argv[0]).resolve().parent
            except (IndexError, AttributeError):
                self.base_dir = Path.cwd()

        # Cache for parsed data
        self._cache = {}
        self._file_mtimes = {}

    def _find_data_file(self, filename):
        """Find data file in new or old location.

        Checks data/ directory first (new structure), then root (old structure).

        Args:
            filename: Name of file to find (e.g., 'outfits.md')

        Returns:
            Path object or None if not found
        """
        # Try new location (data/filename)
        new_location = self.base_dir / "data" / filename
        if new_location.exists():
            return new_location

        # Fall back to old location (root/filename)
        old_location = self.base_dir / filename
        if old_location.exists():
            return old_location

        # Return new location as default for file creation
        return new_location

    def _find_characters_dir(self):
        """Find characters directory in new or old location.

        Returns:
            Path to characters directory (new or old location)
        """
        # Try new location first
        new_location = self.base_dir / "data" / "characters"
        if new_location.exists():
            return new_location

        # Fall back to old location
        old_location = self.base_dir / "characters"
        if old_location.exists():
            return old_location

        # Return new location as default
        return new_location

    def load_outfits(self):
        """Load and parse shared outfits from outfits.md file. Creates file if not found."""
        f = self._find_data_file("outfits.md")
        if not f.exists():
            default_content = """## Common Outfits
### Casual
A simple and comfortable casual outfit.
"""
            f.write_text(default_content, encoding="utf-8")
            return {"Common": {"Casual": "A simple and comfortable casual outfit."}}

        text = f.read_text(encoding="utf-8")
        outfits = MarkdownParser.parse_shared_outfits(text)
        return outfits if outfits else {"Common": {}}

    def load_characters(self):
        """Load and parse character files from characters/ folder, merging with shared outfits.

        Looks for individual character markdown files in the characters/ folder.
        Falls back to characters.md for backwards compatibility.
        Uses caching to avoid re-parsing unchanged files.
        """
        chars_dir = self._find_characters_dir()

        # Check if cache is valid
        cache_key = "characters"
        if chars_dir.exists():
            try:
                char_files = list(chars_dir.glob("*.md"))
                if char_files:
                    current_mtime = max(f.stat().st_mtime for f in char_files)

                    if (
                        cache_key in self._cache
                        and self._file_mtimes.get(cache_key) == current_mtime
                    ):
                        # Cache is valid, return cached data
                        return self._cache[cache_key]

                    # Update mtime
                    self._file_mtimes[cache_key] = current_mtime
            except (OSError, ValueError) as e:
                # If mtime check fails, continue with reload and log for diagnostics
                from utils import logger

                logger.debug(f"Failed to check character files mtimes: {e}")

        chars = {}
        # Try loading from characters folder first
        if chars_dir.exists() and chars_dir.is_dir():
            for char_file in sorted(chars_dir.glob("*.md")):
                try:
                    text = char_file.read_text(encoding="utf-8")
                    # Parse single character file
                    file_chars = MarkdownParser.parse_characters(text)
                    if not file_chars:
                        logger.warning(f"No characters found in {char_file.name}")
                    chars.update(file_chars)
                except UnicodeDecodeError as e:
                    logger.error(f"Encoding error in {char_file.name}: {e}")
                except PermissionError as e:
                    logger.error(f"Permission denied reading {char_file.name}: {e}")
                except Exception as e:
                    logger.error(f"Error loading {char_file.name}: {type(e).__name__} - {e}")

        # If no character files were found, attempt to create a sample character
        if not chars:
            try:
                # Ensure characters directory exists
                chars_dir.mkdir(parents=True, exist_ok=True)

                sample_file = chars_dir / "sample_character.md"
                if not sample_file.exists():
                    default_content = """### Sample Character
**Appearance:** A sample character for you to get started.

**Outfits:**

#### Base
- **Top:** Simple tee
- **Bottom:** Basic jeans
"""
                    sample_file.write_text(default_content, encoding="utf-8")

                # Read all character files from the characters folder (including the sample)
                for char_file in sorted(chars_dir.glob("*.md")):
                    try:
                        text = char_file.read_text(encoding="utf-8")
                        file_chars = MarkdownParser.parse_characters(text)
                        chars.update(file_chars)
                    except Exception as e:
                        logger.error(f"Error parsing {char_file.name}: {e}")
            except Exception as e:
                logger.error(f"Error creating sample character: {e}")
                # Fallback to legacy characters.md location for backwards compatibility
                f = self._find_data_file("characters.md")
                if not f.exists():
                    default_content = """### Sample Character
**Appearance:** A sample character for you to get started.
**Outfits:**
- **Base:** A default outfit.
"""
                    f.write_text(default_content, encoding="utf-8")

                text = f.read_text(encoding="utf-8")
                chars = MarkdownParser.parse_characters(text)

        if not chars:
            raise ValueError(
                "No characters parsed from characters/ folder or characters.md. Please check the file format."
            )

        # Load shared outfits and merge with each character
        shared_outfits = self.load_outfits()
        for char_name, char_data in chars.items():
            merged_outfits = MarkdownParser.merge_character_outfits(
                char_data, shared_outfits, char_name
            )
            char_data["outfits"] = merged_outfits

        # Cache the result
        self._cache[cache_key] = chars

        return chars

    def clear_cache(self):
        """Clear all cached data to force reload."""
        self._cache.clear()
        self._file_mtimes.clear()

    def load_base_prompts(self):
        """Load and parse base_prompts.md file. Creates file if not found."""
        f = self._find_data_file("base_prompts.md")
        default_prompt = {
            "Default": "Soft semi-realistic illustration with clear, natural lighting. Fresh muted florals, calm tonal balance."
        }

        if not f.exists():
            default_content = """## Default
Soft semi-realistic illustration with clear, natural lighting. Fresh muted florals, calm tonal balance.
---
"""
            f.write_text(default_content, encoding="utf-8")
            return default_prompt

        text = f.read_text(encoding="utf-8")
        prompts = MarkdownParser.parse_base_prompts(text)
        return prompts if prompts else default_prompt

    def load_presets(self, filename: str):
        """Load and parse preset files (scenes.md, poses.md, etc.). Creates file if not found."""
        f = self._find_data_file(filename)

        defaults_content = {
            "scenes.md": """## Default
- **Coffee Shop:** Cozy coffee shop interior, warm ambient lighting, wooden tables, comfortable seating.
- **Beach:** Sandy beach at golden hour, gentle waves, soft sunlight, relaxed atmosphere.
""",
            "poses.md": """## General
- **Standing:** Standing naturally, relaxed posture, arms at sides.
- **Sitting:** Sitting comfortably, casual pose.
""",
        }

        defaults_data = {
            "scenes.md": {
                "Default": {
                    "Coffee Shop": "Cozy coffee shop interior, warm ambient lighting, wooden tables, comfortable seating",
                    "Beach": "Sandy beach at golden hour, gentle waves, soft sunlight, relaxed atmosphere",
                }
            },
            "poses.md": {
                "General": {
                    "Standing": "Standing naturally, relaxed posture, arms at sides",
                    "Sitting": "Sitting comfortably, casual pose",
                }
            },
        }

        if not f.exists():
            if filename in defaults_content:
                f.write_text(defaults_content[filename], encoding="utf-8")
                return defaults_data.get(filename, {"Default": {}})
            else:
                return {"Default": {}}

        text = f.read_text(encoding="utf-8")
        parsed = MarkdownParser.parse_presets(text)
        return parsed if parsed else defaults_data.get(filename, {"Default": {}})

    def load_interactions(self):
        """Load and parse interactions.md file. Creates file if not found.

        Returns:
            dict: Dictionary mapping categories to interaction dictionaries
                  Example: {"Basic Interactions": {"Blank": "", "Conversation": "..."}, ...}
        """
        f = self._find_data_file("interactions.md")

        default_interactions = {
            "Basic Interactions": {
                "Blank": "",
                "Conversation": "{char1} engaged in conversation with {char2}, both looking at each other with friendly expressions",
            }
        }

        if not f.exists():
            default_content = """# Interaction Templates

Multi-character interaction templates with placeholder support. Use {char1}, {char2}, {char3}, etc. for character placeholders.

---

## Basic Interactions

- **Blank:** (Start from scratch)

- **Conversation:** {char1} engaged in conversation with {char2}, both looking at each other with friendly expressions
"""
            f.write_text(default_content, encoding="utf-8")
            return default_interactions

        text = f.read_text(encoding="utf-8")
        interactions = MarkdownParser.parse_interactions(text)
        return interactions if interactions else default_interactions

    def get_editable_files(self):
        """Get list of editable files, including character files from characters/ folder if they exist.

        Returns:
            list: List of editable filenames
        """
        from config import MAIN_EDITABLE_FILES

        files = list(MAIN_EDITABLE_FILES)

        # Check for character files in characters/ folder
        char_dir = self._find_characters_dir()
        if char_dir.exists() and char_dir.is_dir():
            char_files = sorted([f.name for f in char_dir.glob("*.md")])
            files.extend(char_files)

        # Check for legacy characters.md in root
        root_char = self.base_dir / "characters.md"
        if root_char.exists() and "characters.md" not in files:
            files.append("characters.md")

        return files
