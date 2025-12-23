"""Parser for shared outfits from markdown."""

import re

# Pre-compile regex patterns for better performance
_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_SUBSECTION_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)


class OutfitParser:
    """Parses shared outfit templates from markdown content."""

    @staticmethod
    def parse_shared_outfits(content: str):
        """Parse shared outfit templates from outfits.md."""
        shared_outfits: dict = {}

        current_section = None
        current_outfit = None
        current_desc: list[str] = []

        for line in content.splitlines():
            section_match = _SECTION_RE.match(line)
            if section_match:
                if current_section is not None and current_outfit and current_desc:
                    shared_outfits.setdefault(current_section, {})[current_outfit] = "\n".join(
                        current_desc
                    ).strip()

                current_section = section_match.group(1).strip()
                shared_outfits.setdefault(current_section, {})
                current_outfit = None
                current_desc = []
                continue

            outfit_match = _SUBSECTION_RE.match(line)
            if outfit_match and current_section is not None:
                if current_outfit and current_desc:
                    shared_outfits.setdefault(current_section, {})[current_outfit] = "\n".join(
                        current_desc
                    ).strip()

                current_outfit = outfit_match.group(1).strip()
                current_desc = []
                continue

            if current_outfit is not None:
                if line.strip():
                    current_desc.append(line)
                elif current_desc:
                    current_desc.append(line)

        if current_section is not None and current_outfit and current_desc:
            shared_outfits.setdefault(current_section, {})[current_outfit] = "\n".join(
                current_desc
            ).strip()

        normalized: dict = {}
        for sec_name, outfits in shared_outfits.items():
            if "common" in sec_name.lower():
                normalized.setdefault("Common", {}).update(outfits)
            else:
                normalized[sec_name] = outfits

        normalized.setdefault("Common", {})

        return normalized

    @staticmethod
    def merge_character_outfits(char_data: dict, shared_outfits: dict, character_name: str):
        """Merge shared outfits with character-specific outfits.
        
        Returns:
            tuple: (flat_outfits_dict, categorized_outfits_dict)
        """
        merged_outfits = {}
        categorized_outfits = {}

        modifier = char_data.get("modifier")
        if modifier:
            key = modifier.upper()
        else:
            key = char_data.get("gender", "F").upper()

        selected_shared = {}
        if isinstance(shared_outfits, dict) and key in shared_outfits:
            selected_shared = shared_outfits.get(key, {})
        elif isinstance(shared_outfits, dict) and not any(k in shared_outfits for k in ("F", "M")):
            selected_shared = shared_outfits
        else:
            if "F" in shared_outfits:
                selected_shared = shared_outfits.get("F", {})

        # Process shared outfits
        for category, outfits in selected_shared.items():
            merged_outfits.update(outfits)
            categorized_outfits[category] = outfits

        # Process personal outfits (treat as "Personal" category)
        personal_outfits = char_data.get("outfits", {})
        merged_outfits.update(personal_outfits)
        
        # If personal outfits exist, add/merge them into a "Personal" category
        if personal_outfits:
            if "Personal" not in categorized_outfits:
                categorized_outfits["Personal"] = {}
            categorized_outfits["Personal"].update(personal_outfits)

        # Move "Personal" to the top of categorized dict for UI priority
        # Python 3.7+ preserves insertion order, so we rebuild
        final_categorized = {}
        if "Personal" in categorized_outfits:
            final_categorized["Personal"] = categorized_outfits.pop("Personal")
        final_categorized.update(categorized_outfits)

        return merged_outfits, final_categorized
