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
    def _parse_outfit_file(content: str):
        import re
        result = {"tags": [], "modifiers": {}, "blocks": {}}
        # Parse Tags
        tags_match = re.search(r"^tags:\s*\[(.*?)\]", content, re.MULTILINE)
        if tags_match:
            tags_str = tags_match.group(1)
            result["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]

        # Parse Modifiers
        modifiers_match = re.search(r"^modifiers:\s*(.*?)(?=\n\[|\Z)", content, re.DOTALL | re.MULTILINE)
        if modifiers_match:
            mod_block = modifiers_match.group(1)
            for line in mod_block.splitlines():
                line = line.strip()
                if not line: continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    result["modifiers"][key.strip()] = val.strip()

        # Parse Sections: [F], [M], [H]
        parts = re.split(r"^\[([FMH])\]", content, flags=re.MULTILINE)
        for i in range(1, len(parts), 2):
            modifier = parts[i]
            body = parts[i+1].strip()
            if not body or body.startswith("- Content missing"):
                continue
            result["blocks"][modifier] = body
            
        return result

    @staticmethod
    def parse_outfits_directory(directory_path):
        """Parse outfits from the new unified directory structure.
        
        Structure: data/outfits/<Category>/<OutfitGroup>/<VariantName>.txt
        Fallback: data/outfits/<Category>/<OutfitName>.txt (treated as base variant)
        
        Returns:
            dict: { "F": { Cat: { GroupName: { "variants": {...}, ... } } }, ... }
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
            
            # Find groups and variants
            outfit_groups = {} # group_name -> {variant_name: file_path}
            
            for child in cat_dir.iterdir():
                if child.is_file() and child.suffix == ".txt":
                    outfit_groups.setdefault(child.stem, {})["base"] = child
                elif child.is_dir():
                    for variant_file in child.glob("*.txt"):
                        outfit_groups.setdefault(child.name, {})[variant_file.stem] = variant_file

            for group_name, variants in outfit_groups.items():
                if not variants:
                    continue
                    
                # Determine base
                base_name = "base" if "base" in variants else list(variants.keys())[0]
                
                parsed_variants = {}
                for v_name, v_path in variants.items():
                    try:
                        content = v_path.read_text(encoding="utf-8")
                        parsed_variants[v_name] = OutfitParser._parse_outfit_file(content)
                    except Exception as e:
                        from utils import logger
                        logger.error(f"Error parsing outfit variant {v_path}: {e}")
                        
                base_data = parsed_variants.get(base_name, {"tags": [], "modifiers": {}, "blocks": {}})
                
                # We need to construct the result by modifier (F, M, H)
                for modifier in ["F", "M", "H"]:
                    has_any_content = False
                    item_data = {
                        "description": "", 
                        "tags": base_data["tags"],
                        "modifiers": base_data["modifiers"],
                        "variants": {},
                        "default_variant": base_name
                    }
                    
                    for v_name, v_data in parsed_variants.items():
                        # Inheritance: if this variant is missing the block, fall back to base
                        body = v_data["blocks"].get(modifier)
                        if not body:
                            body = base_data["blocks"].get(modifier)
                        
                        if body:
                            has_any_content = True
                            v_item = {
                                "description": body,
                                "tags": v_data["tags"] if v_data["tags"] else base_data["tags"],
                                "modifiers": v_data["modifiers"] if v_data["modifiers"] else base_data["modifiers"]
                            }
                            item_data["variants"][v_name] = v_item
                            
                            # Ensure the top-level description matches the base variant (or default)
                            if v_name == base_name:
                                item_data["description"] = body
                                item_data["tags"] = v_item["tags"]
                                item_data["modifiers"] = v_item["modifiers"]
                                
                    # Only add if at least one variant has content for this gender
                    if has_any_content:
                        result.setdefault(modifier, {}).setdefault(category, {})[group_name] = item_data
                        
        # Normalize Common category if needed
        return result

