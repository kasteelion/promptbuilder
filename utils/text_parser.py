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
            if not line: continue
            
            if line.startswith("🎬"):
                config["scene"] = line[1:].strip()
                continue
            if line.startswith("📝"):
                config["notes"] = line[1:].strip()
                continue
            
            if "Scene:" in line:
                config["scene"] = line.split("Scene:", 1)[1].strip()
                continue
            if "Notes:" in line:
                config["notes"] = line.split("Notes:", 1)[1].strip()
                continue
                
            char_match = re.search(r"(?:\[\d+\]\s*)?([^(]+)\(([^)]+)\)", line)
            if char_match:
                raw_name = char_match.group(1).strip()
                # Clean up (F) etc
                raw_name = re.sub(r"\s*\([FmMHh]\)\s*", "", raw_name)
                name = TextParser._fuzzy_match(raw_name, available_characters)
                
                if name:
                    params = [p.strip() for p in char_match.group(2).split(",")]
                    char_entry = {
                        "name": name,
                        "outfit": params[0] if len(params) > 0 else "Base",
                        "pose_preset": params[-1] if len(params) > 1 else "",
                        "use_signature_color": any("Sig:" in p for p in params)
                    }
                    if len(params) == 3:
                        char_entry["color_scheme"] = params[1]
                    config["selected_characters"].append(char_entry)
            else:
                name = TextParser._fuzzy_match(line, available_characters)
                if name:
                    config["selected_characters"].append({"name": name, "outfit": "Base", "pose_preset": ""})
                    
        return config

    @staticmethod
    def _fuzzy_match(raw_name: str, available: List[str]) -> Optional[str]:
        raw_low = raw_name.lower().strip()
        if not raw_low: return None
        for name in available:
            if name.lower() == raw_low: return name
        for name in available:
            if name.lower().startswith(raw_low): return name
        for name in available:
            if raw_low in name.lower(): return name
        return None
