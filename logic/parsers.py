"""Markdown parsing utilities for character, prompt, and preset data."""

import re


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
        shared_outfits = {"Common": {}}
        
        current_section = None
        current_outfit = None
        current_desc = []
        
        for line in content.splitlines():
            # Detect section headers (##)
            section_match = re.match(r"^##\s+(.+)$", line)
            if section_match:
                # Save previous outfit if exists
                if current_outfit and current_desc:
                    if current_section == "Common Outfits":
                        shared_outfits["Common"][current_outfit] = "\n".join(current_desc).strip()
                
                current_section = section_match.group(1).strip()
                current_outfit = None
                current_desc = []
                continue
            
            # Detect outfit headers (###) in Common
            outfit_match = re.match(r"^###\s+(.+)$", line)
            if outfit_match and current_section == "Common Outfits":
                # Save previous outfit if exists
                if current_outfit and current_desc:
                    shared_outfits["Common"][current_outfit] = "\n".join(current_desc).strip()
                
                current_outfit = outfit_match.group(1).strip()
                current_desc = []
                continue
            
            # Accumulate outfit description
            if current_outfit is not None:
                if line.strip():  # Skip empty lines at the start
                    current_desc.append(line)
                elif current_desc:  # Keep empty lines within description
                    current_desc.append(line)
        
        # Save last outfit if exists
        if current_outfit and current_desc:
            if current_section == "Common Outfits":
                shared_outfits["Common"][current_outfit] = "\n".join(current_desc).strip()
        
        return shared_outfits

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
        parts = re.split(r"^###\s+(.+)$", content, flags=re.MULTILINE)
        for i in range(1, len(parts), 2):
            name = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""

            app_match = re.search(
                r"\*\*Appearance:\*\*\s*(.+?)(?:\n\*\*Outfits:|\n\*\*|$)",
                body,
                flags=re.DOTALL,
            )
            appearance = app_match.group(1).strip() if app_match else ""

            outfits = {}

            # First, try to parse the newer structured outfit format using H4 headings
            # Example:
            # #### Base
            # - **Top:** ...
            # - **Bottom:** ...
            outfit_parts = re.split(r"^####\s+(.+)$", body, flags=re.MULTILINE)
            if len(outfit_parts) > 1:
                # outfit_parts layout: [pre_text, outfit_name, outfit_body, outfit_name, outfit_body, ...]
                for j in range(1, len(outfit_parts), 2):
                    o_name = outfit_parts[j].strip()
                    o_body = outfit_parts[j + 1] if j + 1 < len(outfit_parts) else ""

                    # Parse key/value lines inside the outfit body (e.g. - **Top:** desc)
                    items = {}
                    # Improved parsing: accept - **Key:** value OR - Key: value
                    # and allow multi-line values (continuation lines that do not
                    # start with a new list marker are appended to the current value).
                    lines = o_body.splitlines()
                    i = 0
                    item_found = False
                    while i < len(lines):
                        line = lines[i]
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
                                    after = rest[end_bold+2:].lstrip()
                                    if after.startswith(":"):
                                        val_start = after[1:].lstrip()
                                    else:
                                        # maybe the colon was included inside bold, try to strip leading colon
                                        if val_start == "" and after:
                                            val_start = after
                                else:
                                    # malformed bold, fallback to split on first colon
                                    parts = content.split(":", 1)
                                    key = parts[0].strip()
                                    val_start = parts[1].strip() if len(parts) > 1 else ""
                            else:
                                parts = content.split(":", 1)
                                key = parts[0].strip()
                                val_start = parts[1].strip() if len(parts) > 1 else ""

                            # start value lines
                            val_lines = [val_start.rstrip()] if val_start is not None else [""]
                            j = i + 1
                            while j < len(lines) and not re.match(r"^\s*[-*]\s+", lines[j]) and not re.match(r"^####\s+", lines[j]):
                                val_lines.append(lines[j].rstrip())
                                j += 1
                            val = "\n".join([l for l in val_lines if l is not None]).strip()
                            # clean key and value of stray bold markers or leading/trailing colons
                            if key:
                                key = key.strip()
                                if key.endswith(":"):
                                    key = key[:-1].strip()
                            if val.startswith("**"):
                                val = val.lstrip("*").lstrip()
                            items[key] = val
                            i = j
                            continue
                        else:
                            i += 1

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

            # Normalize outfits: detect one-piece entries and canonicalize Bottom
            for o_name, o_val in list(outfits.items()):
                if isinstance(o_val, dict):
                    # Normalize key names by trimming whitespace
                    # Detect bottom-like keys (case-insensitive)
                    bottom_key = None
                    for k in o_val.keys():
                        if k.strip().lower() == 'bottom':
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
                            bv = str(bottom_val).strip().lower()
                            if bv == '' or bv.startswith('n/a') or bv.startswith('na') or bv.startswith('none') or 'one-piece' in bv or 'playsuit' in bv or 'teddy' in bv or 'dress' in bv:
                                is_one_piece = True

                    if is_one_piece:
                        # Canonicalize: ensure Bottom key exists and set to None, add flag
                        if bottom_key is None:
                            o_val['Bottom'] = None
                        else:
                            o_val[bottom_key] = None
                        o_val['one_piece'] = True

            characters[name] = {"appearance": appearance, "outfits": outfits}
        return characters

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
        
        Character-specific outfits override shared outfits of the same name.
        All shared common outfits are included unless overridden.
        """
        merged_outfits = {}
        
        # Add all common shared outfits first
        if "Common" in shared_outfits:
            merged_outfits.update(shared_outfits["Common"])
        
        # Override with character's own outfit definitions (from characters.md)
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