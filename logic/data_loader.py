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
        """Load and parse shared outfits from all outfits_*.md files in data/.

        Priority / behavior:
        - Scans for all files matching `data/outfits_*.md`.
        - The suffix after the underscore (e.g. 'f' in outfits_f.md) becomes the key.
        - Keys are converted to uppercase for consistency (e.g. 'F', 'M', 'H').
        - If legacy `outfits.md` exists and no `outfits_f.md` exists, it migrates it.

        Returns a dict: {"F": {...}, "M": {...}, "H": {...}, ...}
        """
        data_dir = self.base_dir / "data"
        if not data_dir.exists():
            data_dir = self.base_dir

        # Migration logic for legacy outfits.md
        legacy = self._find_data_file("outfits.md")
        f_f = data_dir / "outfits_f.md"
        if not f_f.exists() and legacy.exists():
            try:
                legacy_text = legacy.read_text(encoding="utf-8")
                f_f.write_text(legacy_text, encoding="utf-8")
            except Exception:
                pass

        # Ensure at least a basic outfits_f.md exists
        if not f_f.exists():
            default_content = """## Common Outfits
### Casual
A simple and comfortable casual outfit.
"""
            try:
                f_f.write_text(default_content, encoding="utf-8")
            except Exception:
                pass

        parsed_outfits = {}
        # Scan for all outfits_*.md files
        for f in data_dir.glob("outfits_*.md"):
            try:
                # Extract suffix: outfits_suffix.md -> suffix
                suffix = f.stem.split("_", 1)[1].upper()
                text = f.read_text(encoding="utf-8")
                parsed = MarkdownParser.parse_shared_outfits(text)
                if parsed:
                    parsed_outfits[suffix] = parsed
            except Exception:
                from utils import logger
                logger.exception(f"Error loading outfit file: {f}")

        return parsed_outfits

    def load_categorized_tags(self):
        """Load tags organized by category from `data/tags.md`.

        Returns:
            dict: { category_name: [tags] }
        """
        f = self._find_data_file("tags.md")
        if not f.exists():
            return {"Demographics": ["male", "female"], "Other": []}

        text = f.read_text(encoding="utf-8")
        categorized = {}
        current_cat = "Other"
        
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("## "):
                current_cat = line[3:].strip()
                categorized[current_cat] = []
            elif line.startswith("- "):
                tag = line[2:].strip().lower()
                if current_cat not in categorized:
                    categorized[current_cat] = []
                categorized[current_cat].append(tag)
        
        return categorized

    def load_tags(self):
        """Load canonical tag list from `data/tags.md`, sorted by category priority.

        Returns a list of tag strings.
        """
        categorized = self.load_categorized_tags()
        
        # Priority order for categories
        priority = ["Demographics", "Body Type", "Style", "Vibe", "Other"]
        
        ordered_tags = []
        for cat in priority:
            if cat in categorized:
                ordered_tags.extend(sorted(categorized[cat]))
        
        # Also include any tags actually used by characters that weren't in tags.md
        try:
            chars = self._cache.get("characters")
            if chars is None:
                try:
                    chars = self.load_characters()
                except Exception:
                    chars = None

            if chars:
                known_tags = set(ordered_tags)
                extra_tags = set()
                for _, data in chars.items():
                    tlist = data.get("tags") or []
                    if isinstance(tlist, str):
                        tlist = [t.strip().lower() for t in tlist.split(",") if t.strip()]
                    for tt in tlist:
                        if tt and tt not in known_tags:
                            extra_tags.add(tt)
                
                if extra_tags:
                    ordered_tags.extend(sorted(list(extra_tags)))
        except Exception:
            pass

        return ordered_tags

    def sync_tags(self):
        """Scan characters for tags not in tags.md and append them.
        
        Returns:
            int: Number of new tags added
        """
        # 1. Load existing tags from file
        tags_file = self._find_data_file("tags.md")
        if not tags_file.exists():
            return 0

        known_tags = set()
        try:
            categorized = self.load_categorized_tags()
            for cat_tags in categorized.values():
                known_tags.update(cat_tags)
        except Exception:
            return 0

        # 2. Scan characters
        try:
            chars = self.load_characters()
        except Exception:
            return 0

        new_tags = set()
        for char_data in chars.values():
            tlist = char_data.get("tags") or []
            if isinstance(tlist, str):
                tlist = [t.strip().lower() for t in tlist.split(",") if t.strip()]
            elif isinstance(tlist, (list, tuple)):
                tlist = [str(t).strip().lower() for t in tlist if t]
            
            for t in tlist:
                if t and t not in known_tags:
                    new_tags.add(t)
        
        if not new_tags:
            return 0

        # 3. Append to file
        try:
            current_content = tags_file.read_text(encoding="utf-8")
            
            # Prepare append text
            append_text = ""
            
            # If "## Other" doesn't exist, add it.
            # We use a loose check; stricter parsing is complex for simple append.
            if "## Other" not in current_content:
                if not current_content.endswith("\n"):
                    append_text += "\n"
                append_text += "\n## Other"
            
            for t in sorted(list(new_tags)):
                append_text += f"\n- {t}"
            
            # Append
            with open(tags_file, "a", encoding="utf-8") as f:
                f.write(append_text)
            
            from utils import logger
            logger.info(f"Synced {len(new_tags)} new tags to tags.md")
            
            return len(new_tags)
        except Exception as e:
            from utils import logger
            logger.error(f"Failed to sync tags: {e}")
            return 0

    def load_characters(self):
        """Load and parse character files from characters/ folder, merging with shared outfits.

        Looks for individual character markdown files in the characters/ folder.
        Uses granular per-file caching to only re-parse changed files.
        """
        chars_dir = self._find_characters_dir()
        
        # Initialize caches if not present
        if "characters_map" not in self._cache:
            self._cache["characters_map"] = {}
        if "file_mtimes_map" not in self._cache:
            self._cache["file_mtimes_map"] = {}

        cached_chars = self._cache["characters_map"]
        mtimes_map = self._cache["file_mtimes_map"]

        if chars_dir.exists() and chars_dir.is_dir():
            all_files = list(chars_dir.glob("*.md"))
            found_any = False
            
            # Identify which files need parsing
            for char_file in all_files:
                found_any = True
                try:
                    mtime = char_file.stat().st_mtime
                    # If not in cache or mtime changed, parse it
                    if char_file.name not in cached_chars or mtimes_map.get(char_file.name) != mtime:
                        text = char_file.read_text(encoding="utf-8")
                        file_chars = MarkdownParser.parse_characters(text)
                        if file_chars:
                            # We expect one character per file usually, but parse_characters returns a dict
                            # We'll associate these characters with this file for cache invalidation
                            cached_chars[char_file.name] = file_chars
                            mtimes_map[char_file.name] = mtime
                except Exception as e:
                    from utils import logger
                    logger.error(f"Error loading {char_file.name}: {e}")

            # Remove characters from cache if their file is gone
            current_filenames = {f.name for f in all_files}
            for cached_filename in list(cached_chars.keys()):
                if cached_filename not in current_filenames:
                    del cached_chars[cached_filename]
                    if cached_filename in mtimes_map:
                        del mtimes_map[cached_filename]

        # Flatten the per-file character dicts into one master dict
        chars = {}
        for file_dict in cached_chars.values():
            chars.update(file_dict)

        # If no character files were found, attempt to create a sample character
        if not chars:
            try:
                # ... (rest of fallback logic remains similar but uses chars_dir)
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
                
                # Re-run logic for the newly created sample
                text = sample_file.read_text(encoding="utf-8")
                chars = MarkdownParser.parse_characters(text)
            except Exception as e:
                from utils import logger
                logger.error(f"Error creating sample character: {e}")

        if not chars:
            from core.exceptions import DataLoadError
            raise DataLoadError(
                "No characters parsed from characters/ folder. Please check the file format."
            )

        # Load shared outfits and merge with each character
        shared_outfits = self.load_outfits()
        for char_name, char_data in chars.items():
            merged_outfits, categorized_outfits = MarkdownParser.merge_character_outfits(
                char_data, shared_outfits, char_name
            )
            char_data["outfits"] = merged_outfits
            char_data["outfits_categorized"] = categorized_outfits

        # Resolve photo filenames
        for char_name, char_data in chars.items():
            try:
                resolved = self.resolve_photo_for_character(char_name, char_data.get("photo"))
                char_data["photo"] = resolved
            except Exception:
                pass

        return chars

    def clear_cache(self):
        """Clear all cached data to force reload."""
        self._cache.clear()
        self._file_mtimes.clear()

    def resolve_photo_for_character(
        self, character_name: str, photo_field: str | None
    ) -> str | None:
        """Resolve a character's photo to a filename located in the characters directory.

        Priority:
        1. If `photo_field` is provided and the file exists under characters/, use it.
        2. Try standardized name: `<sanitized_name>_photo.<ext>` (png/jpg/jpeg)
        3. Try lowercase/underscore variants of the sanitized name.
        4. If nothing found, return None.

        Returns a filename relative to the characters directory, or None.
        """
        from pathlib import Path

        from utils.validation import sanitize_filename

        chars_dir = self._find_characters_dir()

        # Helper to check candidate names
        def check_candidate(name: str):
            p = chars_dir / name
            if p.exists():
                return name
            return None

        # 1) explicit field if present
        if photo_field:
            try:
                # If field is an absolute path, try to match by basename
                cand = Path(photo_field)
                if cand.is_absolute():
                    # prefer file inside characters dir
                    local = chars_dir / cand.name
                    if local.exists():
                        return cand.name
                    # otherwise, do not return absolute paths (keep relative)
                else:
                    # relative to characters dir
                    res = check_candidate(photo_field)
                    if res:
                        return res
            except Exception:
                pass

        # 2) standardized sanitized name
        base = sanitize_filename(character_name).lower().replace(" ", "_")
        # Try common extensions
        for ext in (".png", ".jpg", ".jpeg"):
            cand = f"{base}_photo{ext}"
            found = check_candidate(cand)
            if found:
                return found

        # 3) try variants (strip diacritics not implemented here; try simple lowercase)
        simple = "".join(c for c in character_name.lower() if c.isalnum() or c == "_").replace(
            " ", "_"
        )
        for ext in (".png", ".jpg", ".jpeg"):
            cand = f"{simple}_photo{ext}"
            found = check_candidate(cand)
            if found:
                return found

        # 4) nothing found
        return None

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
                "Blank": {"description": "", "min_chars": 1},
                "Conversation": {
                    "description": "{char1} engaged in conversation with {char2}, both looking at each other with friendly expressions",
                    "min_chars": 2
                },
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
        """Get list of editable files, dynamically scanning data directory.

        Returns:
            list: List of editable filenames
        """
        editable_files = set()
        
        # Priority list for ordering
        priority_files = ["base_prompts.md", "scenes.md", "poses.md", "outfits_f.md", "outfits_m.md", "interactions.md", "color_schemes.md"]
        
        # Scan data directory
        data_dir = self.base_dir / "data"
        if data_dir.exists() and data_dir.is_dir():
            for f in data_dir.glob("*.md"):
                editable_files.add(f.name)

        # Also check root for legacy compatibility
        for f in self.base_dir.glob("*.md"):
             # Simple check to avoid README etc if we only want data files, 
             # but keeping it simple to match previous behavior of "checking root"
             if f.name in priority_files or f.name == "characters.md":
                 editable_files.add(f.name)

        # Sort: priority files first, then alphabetical
        sorted_files = []
        for f in priority_files:
            if f in editable_files:
                sorted_files.append(f)
                editable_files.remove(f)
        
        sorted_files.extend(sorted(list(editable_files)))

        # Check for character files in characters/ folder
        char_dir = self._find_characters_dir()
        if char_dir.exists() and char_dir.is_dir():
            char_files = sorted([f.name for f in char_dir.glob("*.md")])
            sorted_files.extend(char_files)

        return sorted_files

    def load_color_schemes(self):
        """Load and parse color_schemes.md file. Creates file if not found.

        Uses caching to avoid repeated parsing of the same file.
        """
        f = self._find_data_file("color_schemes.md")
        cache_key = "color_schemes"

        # Check if cache is valid
        if f.exists():
            try:
                mtime = f.stat().st_mtime
                if cache_key in self._cache and self._file_mtimes.get(cache_key) == mtime:
                    return self._cache[cache_key]
                self._file_mtimes[cache_key] = mtime
            except OSError:
                pass

        default_schemes = {
            "The Standard": {
                "primary_color": "white",
                "secondary_color": "black",
                "accent": "blue",
            }
        }

        if not f.exists():
            default_content = """## The Standard
- **primary:** white
- **secondary:** black
- **accent:** blue
"""
            try:
                f.write_text(default_content, encoding="utf-8")
            except Exception:
                pass
            return default_schemes

        try:
            text = f.read_text(encoding="utf-8")
            schemes = MarkdownParser.parse_color_schemes(text)
            result = schemes if schemes else default_schemes
            self._cache[cache_key] = result
            return result
        except Exception:
            from utils import logger
            logger.exception("Error loading color schemes")
            return default_schemes

    def load_modifiers(self):
        """Load and parse modifiers.md file. Creates file if not found."""
        f = self._find_data_file("modifiers.md")
        cache_key = "modifiers"

        # Check if cache is valid
        if f.exists():
            try:
                mtime = f.stat().st_mtime
                if cache_key in self._cache and self._file_mtimes.get(cache_key) == mtime:
                    return self._cache[cache_key]
                self._file_mtimes[cache_key] = mtime
            except OSError:
                pass

        default_modifiers = {
            "Volleyball - Libero": ", wearing a contrasting {secondary_color} jersey to denote libero position,"
        }

        if not f.exists():
            return default_modifiers

        try:
            text = f.read_text(encoding="utf-8")
            modifiers = MarkdownParser.parse_modifiers(text)
            result = modifiers if modifiers else default_modifiers
            self._cache[cache_key] = result
            return result
        except Exception:
            from utils import logger
            logger.exception("Error loading modifiers")
            return default_modifiers

    def load_framing(self):
        """Load and parse framing.md file. Creates file if not found."""
        f = self._find_data_file("framing.md")
        cache_key = "framing"

        # Check if cache is valid
        if f.exists():
            try:
                mtime = f.stat().st_mtime
                if cache_key in self._cache and self._file_mtimes.get(cache_key) == mtime:
                    return self._cache[cache_key]
                self._file_mtimes[cache_key] = mtime
            except OSError:
                pass

        default_framing = {
            "Full Body": "full body shot showing the character from head to toe,"
        }

        if not f.exists():
            return default_framing

        try:
            text = f.read_text(encoding="utf-8")
            # Use the same parser as modifiers since format is identical
            framing = MarkdownParser.parse_modifiers(text)
            result = framing if framing else default_framing
            self._cache[cache_key] = result
            return result
        except Exception:
            from utils import logger
            logger.exception("Error loading framing")
            return default_framing
