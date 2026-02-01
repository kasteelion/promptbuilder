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
                if current_section is not None and current_outfit:
                    # Save previous
                    outfit_data = {
                        "description": "\n".join(current_desc).strip(),
                        "tags": current_tags
                    }
                    shared_outfits.setdefault(current_section, {})[current_outfit] = outfit_data

                current_section = section_match.group(1).strip()
                shared_outfits.setdefault(current_section, {})
                current_outfit = None
                current_tags = []
                current_desc = []
                continue

            # Match ### Name (Tags)
            outfit_match = re.match(r"^###\s+(.+)$", line)
            if outfit_match and current_section is not None:
                if current_outfit:
                    # Save previous
                    outfit_data = {
                        "description": "\n".join(current_desc).strip(),
                        "tags": current_tags
                    }
                    shared_outfits.setdefault(current_section, {})[current_outfit] = outfit_data

                raw_name = outfit_match.group(1).strip()
                
                # Check for tags in parens
                name = raw_name
                tags = []
                tag_match = re.search(r"\(([^)]+)\)$", raw_name)
                if tag_match:
                    tags_str = tag_match.group(1)
                    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                    name = raw_name[:tag_match.start()].strip()

                current_outfit = name
                current_tags = tags
                current_desc = []
                continue

            if current_outfit is not None:
                if line.strip():
                    current_desc.append(line)
                elif current_desc:
                    current_desc.append(line)

        if current_section is not None and current_outfit:
            outfit_data = {
                "description": "\n".join(current_desc).strip(),
                "tags": current_tags
            }
            shared_outfits.setdefault(current_section, {})[current_outfit] = outfit_data

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

    @staticmethod
    def parse_outfits_directory(directory_path):
        """Parse outfits from the new unified directory structure.
        
        Structure: data/outfits/<Category>/<OutfitName>.txt
        
        Returns:
            dict: { "F": { Cat: { Name: Data } }, "M": ..., "H": ... }
        """
        import re
        from pathlib import Path
        
        result = {"F": {}, "M": {}, "H": {}}
        
        root = Path(directory_path)
        if not root.exists():
            return result

        # Iterate through categories (subdirectories)
        for cat_dir in root.iterdir():
            if not cat_dir.is_dir():
                continue
                
            category = cat_dir.name
            
            # Iterate through outfit files
            for outfit_file in cat_dir.glob("*.txt"):
                try:
                    content = outfit_file.read_text(encoding="utf-8")
                    name = outfit_file.stem
                    
                    # Parse Tags
                    tags = []
                    tags_match = re.search(r"^tags:\s*\[(.*?)\]", content, re.MULTILINE)
                    if tags_match:
                        tags_str = tags_match.group(1)
                        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

                    # Parse Modifiers (YAML-style block)
                    # modifiers:
                    #   Name: Description
                    modifiers = {}
                    modifiers_match = re.search(r"^modifiers:\s*(.*?)(?=\n\[|\Z)", content, re.DOTALL | re.MULTILINE)
                    if modifiers_match:
                        mod_block = modifiers_match.group(1)
                        # Find lines looking like "  Key: Value"
                        for line in mod_block.splitlines():
                            line = line.strip()
                            if not line: continue
                            if ":" in line:
                                key, val = line.split(":", 1)
                                modifiers[key.strip()] = val.strip()
                    
                    # Parse Sections: [F], [M], [H]
                    parts = re.split(r"^\[([FMH])\]", content, flags=re.MULTILINE)
                    # parts[0] is header/tags, then alternating Key, Content
                    
                    # Iterate parts starting from index 1
                    for i in range(1, len(parts), 2):
                        modifier = parts[i]
                        body = parts[i+1].strip()
                        
                        # Skip if body is empty or explicitly missing content marker
                        if not body or body.startswith("- Content missing"):
                            continue
                            
                        item_data = {
                            "description": body,
                            "tags": tags,
                            "modifiers": modifiers
                        }
                        
                        result.setdefault(modifier, {}).setdefault(category, {})[name] = item_data
                        
                except Exception as e:
                    from utils import logger
                    logger.error(f"Error parsing outfit file {outfit_file}: {e}")
                    
        # Normalize Common category if needed (not strictly required if folders are correct)
        return result

