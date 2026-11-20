import re
from typing import Any, Dict, List, Optional

class TextParser:
    """Parses natural language or structured text blocks into prompt configurations."""

    @staticmethod
    def parse_import_text(text: str, available_characters: List[str]) -> Dict[str, Any]:
        """Parse a text block into a configuration dictionary."""
        config = {
            "selected_characters": [],
            "base_prompt": "Default",
            "scene": "",
            "notes": ""
        }

        if not text.strip():
            return config
        
        # Detect format type
        if "### PROMPT CONFIG ###" in text or "---" in text or "Base:" in text:
            return TextParser._parse_structured(text, available_characters)
        else:
            return TextParser._parse_summary_style(text, available_characters)

    @staticmethod
    def _parse_structured(text: str, available_characters: List[str]) -> Dict[str, Any]:
        config = {
            "selected_characters": [],
            "base_prompt": "Default",
            "scene": "",
            "notes": ""
        }
        
        # Comprehensive list of labels that mark the start of a new field
        ALL_LABELS = [
            "Base:", "Scene:", "Outfit:", "Traits:", "Colors?:", "Sig:", "Pose:", "Note:", 
            "Notes?:", "---", r"\[\d+\]"
        ]

        def get_field(label, source, markers=None):
            if markers is None:
                markers = ALL_LABELS
            # Look for Label: (Capture) Stop before any other known Label or end of string
            pattern = rf"{label}\s*(.*?)(?=\s*(?:{'|'.join(markers)})|$)"
            m = re.search(pattern, source, re.IGNORECASE | re.DOTALL)
            return m.group(1).strip().strip(":") if m else ""

        # 1. Extract Global Metadata
        config["base_prompt"] = get_field("Base:", text)
        config["scene"] = get_field("Scene:", text)
        
        # Extract global notes (usually at the end)
        global_notes_match = re.search(r"(?:\n|^)Notes?:\s*(.*)$", text, re.IGNORECASE | re.DOTALL)
        if global_notes_match:
            config["notes"] = global_notes_match.group(1).strip()

        # 2. Extract Characters
        char_parts = re.split(r"\[\d+\]", text)
        for block in char_parts[1:]:
            # Clean character block from global notes
            if "Notes:" in block:
                block = block.split("Notes:")[0]
            
            # Name is everything from start of block until first field label
            name_markers = ["Outfit:", "Colors?:", "Sig:", "Pose:", "Note:"]
            name_pattern = rf"^(.*?)(?=\s*(?:{'|'.join(name_markers)})|$)"
            name_match = re.search(name_pattern, block.strip(), re.DOTALL | re.IGNORECASE)
            raw_name = name_match.group(1).strip() if name_match else ""
            
            # IMPROVED: Clean up modifiers like (F), (M), (H) case-insensitively
            raw_name = re.sub(r"\s*\([FmMHh]\)\s*", "", raw_name)
            name = TextParser._fuzzy_match(raw_name, available_characters)
            
            if name:
                char_entry = {
                    "name": name,
                    "outfit": "Base",
                    "outfit_traits": [],
                    "pose_category": "",
                    "pose_preset": "",
                    "action_note": "",
                    "color_scheme": "",
                    "use_signature_color": False
                }
                
                char_entry["outfit"] = get_field("Outfit:", block)
                
                traits_val = get_field("Traits:", block)
                if traits_val:
                    char_entry["outfit_traits"] = [t.strip() for t in traits_val.split(",") if t.strip()]
                
                char_entry["pose_preset"] = get_field("Pose:", block)
                char_entry["action_note"] = get_field("Note:", block)
                char_entry["color_scheme"] = get_field("Colors?:", block)
                
                sig_val = get_field("Sig:", block).lower()
                if sig_val:
                    char_entry["use_signature_color"] = sig_val not in ("no", "false", "off")

                config["selected_characters"].append(char_entry)
                
        return config

    @staticmethod
    def _parse_summary_style(text: str, available_characters: List[str]) -> Dict[str, Any]:
        config = {
            "selected_characters": [],
            "base_prompt": "Default",
            "scene": "",
            "notes": ""
        }
        
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            
            # Handle icons/labels
            if line.startswith("🎨"):
                config["base_prompt"] = line[1:].strip().strip("*")
                continue
            if line.startswith("🎬"):
                config["scene"] = line[1:].strip()
                continue
            if line.startswith("📝") or line.startswith("🤝"):
                config["notes"] = line[1:].strip()
                # Clean up bold labels if present
                config["notes"] = re.sub(r"^\*\*(?:Action|Interaction)\*\*:\s*", "", config["notes"])
                continue
            if line.startswith("✨"):
                # Moods are primarily for display, might not need strict parsing back
                continue
            
            if "Style:" in line:
                config["base_prompt"] = line.split("Style:", 1)[1].strip()
                continue
            if "Scene:" in line:
                config["scene"] = line.split("Scene:", 1)[1].strip()
                continue
            if "Notes:" in line or "Note:" in line:
                config["notes"] = line.split("ote:", 1)[1].strip()
                continue
                
            # Support for the 👤 **Name**: Outfit • Pose format
            char_colon_match = re.search(r"(?:👤\s*)?\*\*?([^*:]+)\*\*?:\s*(.+)", line)
            if char_colon_match:
                raw_name = char_colon_match.group(1).strip()
                params_text = char_colon_match.group(2).strip()
                
                name = TextParser._fuzzy_match(raw_name, available_characters)
                if name:
                    # Logic: Outfit [Tags] • Pose
                    # Split by bullet first! This is the most reliable way to separate Outfit from Pose.
                    if " • " in params_text:
                        outfit_part, pose_part = params_text.split(" • ", 1)
                        params = [outfit_part.strip()]
                        pose_preset = pose_part.strip()
                    else:
                        # Fallback for comma-only lists
                        params = [p.strip() for p in params_text.split(",")]
                        pose_preset = params[-1] if len(params) > 1 else ""
                    
                    # Clean up Outfit name (remove [Tags])
                    outfit_name = params[0]
                    outfit_name = re.sub(r"\s*\[[^\]]*\]\s*", "", outfit_name).strip()
                    
                    char_entry = {
                        "name": name,
                        "outfit": outfit_name,
                        "pose_preset": pose_preset,
                        "use_signature_color": "✨" in params_text or "Sig:" in params_text
                    }
                    
                    # If we have a middle part (like a color scheme), it would be in params[1] if comma split
                    # For now, let's just make sure outfit and pose are safe.
                    
                    config["selected_characters"].append(char_entry)
                    continue

            # Support for the legacy Name(Params) format
            char_matches = list(re.finditer(r"(?:[👥\[]\d*\]?\s*)?(\**[^(*]+\**)\(([^)]+)\)", line))
            if char_matches:
                for char_match in char_matches:
                    raw_name = char_match.group(1).strip().strip("*")
                    raw_name = re.sub(r"\s*\([FmMHh]\)\s*", "", raw_name)
                    raw_name = re.sub(r"^[^\w\s]+", "", raw_name).strip()
                    
                    name = TextParser._fuzzy_match(raw_name, available_characters)
                    
                    if name:
                        params_text = char_match.group(2).replace(" • ", ",")
                        params = [p.strip() for p in params_text.split(",")]
                        
                        outfit_name = params[0] if len(params) > 0 else "Base"
                        outfit_name = re.sub(r"\s*\[[^\]]*\]\s*", "", outfit_name).strip()

                        char_entry = {
                            "name": name,
                            "outfit": outfit_name,
                            "pose_preset": params[-1] if len(params) > 1 else "",
                            "use_signature_color": any("Sig:" in p or "✨" in p for p in params)
                        }
                        if len(params) >= 3:
                            char_entry["color_scheme"] = params[1]
                        config["selected_characters"].append(char_entry)
            else:
                # Direct name match (only if no characters with parens or colons were found)
                clean_line = re.sub(r"^[^\w\s]+", "", line).strip().strip("*")
                name = TextParser._fuzzy_match(clean_line, available_characters)
                if name:
                    config["selected_characters"].append({"name": name, "outfit": "Base", "pose_preset": ""})
                    
        return config

    @staticmethod
    def _fuzzy_match(raw_name: str, available: List[str]) -> Optional[str]:
        raw_low = raw_name.lower().strip()
        if not raw_low:
            return None
        
        # Clean up common prefixes/formatting
        raw_clean = re.sub(r"^[^\w\s]+", "", raw_low).strip() # Remove leading emojis/punctuation
        raw_clean = re.sub(r"\s*\(.*?\)\s*", "", raw_clean).strip() # Remove gender tags like (F)
        
        if not raw_clean:
            return None

        # 1. Exact match
        for name in available:
            if name.lower() == raw_clean:
                return name
            
        # 2. Starts with / Contains
        for name in available:
            name_low = name.lower()
            if name_low.startswith(raw_clean) or raw_clean in name_low:
                return name
            
        # 3. Handle Reversed Names (e.g., "Hart Mela" vs "Mela Hart")
        parts = raw_clean.split()
        if len(parts) > 1:
            reversed_name = " ".join(reversed(parts))
            for name in available:
                if name.lower() == reversed_name:
                    return name
                
        return None
