"""Markdown parsing utilities for character, prompt, and preset data."""

import re

# Pre-compile regex patterns for better performance
_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_SUBSECTION_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)
_OUTFIT_RE = re.compile(r"^####\s+(.+)$", re.MULTILINE)
_PHOTO_RE = re.compile(r"\*\*Photo:\*\*\s*(.+?)(?:\n|$)", re.MULTILINE)
_APPEARANCE_RE = re.compile(r"\*\*Appearance:\*\*\s*(.+?)(?:\n\*\*Outfits:|\n\*\*|$)", re.DOTALL)
_GENDER_RE = re.compile(r"\*\*Gender:\*\*\s*([mfMF])\b")
_SUMMARY_RE = re.compile(r"\*\*Summary:\*\*\s*(.+?)(?:\n\*\*|$)", re.DOTALL)
_TAGS_RE = re.compile(r"\*\*Tags:\*\*\s*(.+?)(?:\n\*\*|$)", re.DOTALL)
_LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+(.*)$")
_PRESET_ITEM_RE = re.compile(r"^-\s+\*\*([^:]+):\*\*\s*(.+)$")


class MarkdownParser:
    """Parses markdown files for characters, base prompts, and presets."""

    @staticmethod
    def parse_shared_outfits(content: str):
        """Parse shared outfit templates from outfits.md.

        Expected format:
        ## Common Outfits
        ### Outfit Name
        Outfit description...
        """
        # Parse all sections (##) and their outfits (###). Return a dict
        # mapping section_name -> {outfit_name: description, ...}
        shared_outfits: dict = {}

        current_section = None
        current_outfit = None
        current_desc: list[str] = []

        for line in content.splitlines():
            # Detect section headers (##)
            section_match = _SECTION_RE.match(line)
            if section_match:
                # Save previous outfit if exists
                if current_section is not None and current_outfit and current_desc:
                    shared_outfits.setdefault(current_section, {})[current_outfit] = "\n".join(
                        current_desc
                    ).strip()

                current_section = section_match.group(1).strip()
                # Initialize section bucket
                shared_outfits.setdefault(current_section, {})
                current_outfit = None
                current_desc = []
                continue

            # Detect outfit headers (###)
            outfit_match = _SUBSECTION_RE.match(line)
            if outfit_match and current_section is not None:
                # Save previous outfit if exists
                if current_outfit and current_desc:
                    shared_outfits.setdefault(current_section, {})[current_outfit] = "\n".join(
                        current_desc
                    ).strip()

                current_outfit = outfit_match.group(1).strip()
                current_desc = []
                continue

            # Accumulate outfit description lines if we are within an outfit
            if current_outfit is not None:
                # Skip leading empty lines, but preserve internal blank lines
                if line.strip():
                    current_desc.append(line)
                elif current_desc:
                    current_desc.append(line)

        # Save last outfit if exists
        if current_section is not None and current_outfit and current_desc:
            shared_outfits.setdefault(current_section, {})[current_outfit] = "\n".join(
                current_desc
            ).strip()

        # Normalize section names for backwards compatibility: map any
        # section containing the word 'common' to the 'Common' key.
        normalized: dict = {}
        for sec_name, outfits in shared_outfits.items():
            if "common" in sec_name.lower():
                normalized.setdefault("Common", {}).update(outfits)
            else:
                normalized[sec_name] = outfits

        # Ensure at least a 'Common' key exists for older callers/tests
        normalized.setdefault("Common", {})

        return normalized

    @staticmethod
    def parse_characters(content: str):
        """Parse character definitions from markdown content.

        Expected format:
        ### Character Name
        **Appearance:** description
        **Outfits:**
        - **Outfit Name:** description
        """
        characters = {}
        parts = _SUBSECTION_RE.split(content)
        for i in range(1, len(parts), 2):
            name = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""

            # Extract photo path if present
            photo = None
            photo_match = _PHOTO_RE.search(body)
            if photo_match:
                photo = photo_match.group(1).strip()

            app_match = _APPEARANCE_RE.search(body)
            appearance = app_match.group(1).strip() if app_match else ""

            # Extract optional summary if present
            summary = None
            summary_match = _SUMMARY_RE.search(body)
            if summary_match:
                summary = summary_match.group(1).strip()

            # Remove HTML comment blocks from appearance (legacy marker)
            appearance = re.sub(r"(?s)<!--.*?-->", "", appearance).strip()

            # Support '//' style notes: drop any lines starting with '//' (trim leading whitespace)
            if appearance:
                lines = [ln for ln in appearance.splitlines() if not re.match(r"^\s*//", ln)]
                appearance = "\n".join(lines).strip()

            outfits = {}

            # First, try to parse the newer structured outfit format using H4 headings
            # Example:
            # #### Base
            # - **Top:** ...
            # - **Bottom:** ...
            outfit_parts = _OUTFIT_RE.split(body)
            if len(outfit_parts) > 1:
                # outfit_parts layout: [pre_text, outfit_name, outfit_body, outfit_name, outfit_body, ...]
                for outfit_idx in range(1, len(outfit_parts), 2):
                    o_name = outfit_parts[outfit_idx].strip()
                    o_body = (
                        outfit_parts[outfit_idx + 1] if outfit_idx + 1 < len(outfit_parts) else ""
                    )

                    # Parse key/value lines inside the outfit body (e.g. - **Top:** desc)
                    items = {}
                    # Improved parsing: accept - **Key:** value OR - Key: value
                    # and allow multi-line values (continuation lines that do not
                    # start with a new list marker are appended to the current value).
                    lines = o_body.splitlines()
                    line_idx = 0
                    item_found = False
                    while line_idx < len(lines):
                        line = lines[line_idx]
                        # detect list marker and strip it
                        m_marker = re.match(r"^\s*[-*]\s+(.*)$", line)
                        if m_marker:
                            content = m_marker.group(1)
                            item_found = True
                            # Parse key and starting value robustly. Support **Key:**, **Key**:, Key:, and cases where the colon is inside the bold markers.
                            key = None
                            val_start = ""
                            if content.startswith("**"):
                                rest = content[2:]
                                end_bold = rest.find("**")
                                if end_bold != -1:
                                    # content like **Top:** or **Top**: or **Top**: value
                                    key = rest[:end_bold].strip()
                                    after = rest[end_bold + 2 :].lstrip()
                                    if after.startswith(":"):
                                        val_start = after[1:].lstrip()
                                    else:
                                        # maybe the colon was included inside bold, try to strip leading colon
                                        if val_start == "" and after:
                                            val_start = after
                                else:
                                    # malformed bold, fallback to split on first colon
                                    key_val_parts = content.split(":", 1)
                                    key = key_val_parts[0].strip()
                                    val_start = (
                                        key_val_parts[1].strip() if len(key_val_parts) > 1 else ""
                                    )
                            else:
                                key_val_parts = content.split(":", 1)
                                key = key_val_parts[0].strip()
                                val_start = (
                                    key_val_parts[1].strip() if len(key_val_parts) > 1 else ""
                                )

                            # start value lines
                            val_lines = [val_start.rstrip()] if val_start is not None else [""]
                            next_line_idx = line_idx + 1
                            while (
                                next_line_idx < len(lines)
                                and not re.match(r"^\s*[-*]\s+", lines[next_line_idx])
                                and not re.match(r"^####\s+", lines[next_line_idx])
                            ):
                                val_lines.append(lines[next_line_idx].rstrip())
                                next_line_idx += 1
                            val = "\n".join(
                                [entry for entry in val_lines if entry is not None]
                            ).strip()
                            # clean key and value of stray bold markers or leading/trailing colons
                            if key:
                                key = key.strip()
                                if key.endswith(":"):
                                    key = key[:-1].strip()
                            if val.startswith("**"):
                                val = val.lstrip("*").lstrip()
                            items[key] = val
                            line_idx = next_line_idx
                            continue
                        else:
                            line_idx += 1

                    # If we found structured items, store them as a dict; otherwise store raw text
                    if item_found:
                        outfits[o_name] = items
                    else:
                        outfits[o_name] = o_body.strip()
            else:
                # Fallback: legacy format where each outfit is a single list item
                for m in re.finditer(r"-\s+\*\*([^:]+):\*\*\s*(.+)", body):
                    o_name = m.group(1).strip()
                    o_desc = m.group(2).strip()
                    outfits[o_name] = o_desc

            # Extract optional tags if present (comma-separated)
            tags = []
            tags_match = _TAGS_RE.search(body)
            if tags_match:
                raw = tags_match.group(1).strip()
                tags = [t.strip() for t in re.split(r",|;", raw) if t.strip()]

            # Detect gender tag (default to 'F' for backwards compatibility)
            gender = "F"
            gender_explicit = False
            gender_match = _GENDER_RE.search(body)
            if gender_match:
                gender = gender_match.group(1).upper()
                gender_explicit = True

            # Normalize outfits: detect one-piece entries and canonicalize Bottom
            for o_name, o_val in list(outfits.items()):
                if isinstance(o_val, dict):
                    # Normalize key names by trimming whitespace
                    # Detect bottom-like keys (case-insensitive)
                    bottom_key = None
                    for k in o_val.keys():
                        if k.strip().lower() == "bottom":
                            bottom_key = k
                            break

                    bottom_val = None
                    if bottom_key is not None:
                        bottom_val = o_val.get(bottom_key)

                    # Determine if this outfit is a one-piece when Bottom missing or marked N/A
                    is_one_piece = False
                    if bottom_key is None:
                        is_one_piece = True
                    else:
                        if bottom_val is None:
                            is_one_piece = True
                        else:
                            # Cache the normalized bottom value to avoid repeated operations
                            bottom_val_normalized = str(bottom_val).strip().lower()
                            if (
                                bottom_val_normalized == ""
                                or bottom_val_normalized.startswith(("n/a", "na", "none"))
                                or any(
                                    keyword in bottom_val_normalized
                                    for keyword in ["one-piece", "playsuit", "teddy", "dress"]
                                )
                            ):
                                is_one_piece = True

                    if is_one_piece:
                        # Canonicalize: ensure Bottom key exists and set to None, add flag
                        if bottom_key is None:
                            o_val["Bottom"] = None
                        else:
                            o_val[bottom_key] = None
                            # Normalize to canonical 'Bottom' key if different
                            if bottom_key != "Bottom":
                                o_val["Bottom"] = None
                                del o_val[bottom_key]
                        o_val["one_piece"] = True

            characters[name] = {
                "appearance": appearance,
                "summary": summary,
                "tags": tags,
                "outfits": outfits,
                "photo": photo,
                "gender": gender,
                "gender_explicit": gender_explicit,
            }

        # Validate parsed character structure
        validated_chars = {}
        for name, data in characters.items():
            if not isinstance(data, dict):
                # Import logger locally to avoid circular imports
                from utils import logger

                logger.warning(f"Invalid character data for {name}, skipping")
                continue

            # Ensure required fields exist
            if "appearance" not in data:
                from utils import logger

                logger.warning(f"Character {name} missing appearance, adding empty")
                data["appearance"] = ""

            if "outfits" not in data or not isinstance(data["outfits"], dict):
                from utils import logger

                logger.warning(f"Character {name} has invalid outfits, adding empty dict")
                data["outfits"] = {}

            if "photo" not in data:
                data["photo"] = None

            validated_chars[name] = data

        return validated_chars

    @staticmethod
    def parse_base_prompts(content: str):
        """Parse base style prompts from markdown content.

        Expected format:
        ## Prompt Name
        Prompt content...
        ---
        """
        prompts = {}
        parts = re.split(r"^##\s+(.+)$", content, flags=re.MULTILINE)
        for i in range(1, len(parts), 2):
            name = parts[i].strip()
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            body = re.sub(r"\n*---\s*$", "", body).strip()
            prompts[name] = body
        return prompts

    @staticmethod
    def merge_character_outfits(char_data: dict, shared_outfits: dict, character_name: str):
        """Merge shared outfits with character-specific outfits.

        ALL outfits from outfits.md (all categories) are shared with every character.
        Character-specific outfits override shared outfits of the same name.

        Args:
            char_data: Character data dictionary
            shared_outfits: Shared outfits dictionary from outfits.md (organized by category)
            character_name: Name of the character

        Returns:
            Dictionary of merged outfits (outfit_name -> outfit_description)
        """
        merged_outfits = {}

        # If shared_outfits is gendered (dict with 'F' and/or 'M'), pick the right one
        # Otherwise, fall back to the legacy structure where shared_outfits is a single dict
        gender = char_data.get("gender", "F") if isinstance(char_data, dict) else "F"

        if isinstance(shared_outfits, dict) and any(k in shared_outfits for k in ("F", "M")):
            selected = shared_outfits.get(gender, {})
            # Add all categories from the selected gender file
            for category, outfits in selected.items():
                merged_outfits.update(outfits)
        else:
            # Legacy: shared_outfits is a single dict of categories
            for category, outfits in shared_outfits.items():
                merged_outfits.update(outfits)

        # Character-specific outfits override shared ones with the same name
        merged_outfits.update(char_data.get("outfits", {}))

        return merged_outfits

    @staticmethod
    def parse_presets(content: str):
        """Parse preset categories and items from markdown content.

        Expected format:
        ## Category Name
        - **Item Name:** description
        """
        presets = {}
        current = "Default"
        presets[current] = {}

        for line in content.splitlines():
            cat = re.match(r"^##\s+(.+)$", line)
            if cat:
                current = cat.group(1).strip()
                presets.setdefault(current, {})
                continue

            item = re.match(r"^-\s+\*\*([^:]+):\*\*\s*(.+)$", line)
            if item:
                name = item.group(1).strip()
                desc = item.group(2).strip()
                presets.setdefault(current, {})[name] = desc

        return presets

    @staticmethod
    def parse_interactions(content: str):
        """Parse interaction templates from markdown content with categories.

        Expected format:
        ## Category Name
        - **Template Name:** template content with {char1}, {char2}, etc.

        Returns:
            dict: Dictionary mapping categories to template dictionaries
                  Example: {"Basic Interactions": {"Conversation": "...", ...}, ...}
        """
        interactions = {}
        current = None

        for line in content.splitlines():
            # Check for category header
            cat = re.match(r"^##\s+(.+)$", line)
            if cat:
                current = cat.group(1).strip()
                # Skip "Notes" section
                if current.lower() == "notes":
                    current = None
                    continue
                interactions.setdefault(current, {})
                continue

            # Parse interaction items (only if we have a valid category)
            if current:
                item = re.match(r"^-\s+\*\*([^:]+):\*\*\s*(.*)$", line)
                if item:
                    name = item.group(1).strip()
                    desc = item.group(2).strip()

                    # Remove parenthetical descriptions like "(Start from scratch)"
                    desc = re.sub(r"^\([^)]+\)\s*", "", desc)

                    interactions[current][name] = desc

        # Remove any empty categories
        interactions = {k: v for k, v in interactions.items() if v}

        return interactions
