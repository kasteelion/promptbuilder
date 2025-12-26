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
        if "### PROMPT CONFIG ###" in text or "---" in text:
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
        
        # Extract Scene
        scene_match = re.search(r"Scene:\s*(.*?)(?:\n---|\n\[|$)", text, re.IGNORECASE | re.DOTALL)
        if scene_match:
            config["scene"] = scene_match.group(1).strip()
            
        # Extract Base Prompt
        base_match = re.search(r"Base:\s*(.*?)(?:\n|$)", text, re.IGNORECASE)
        if base_match:
            config["base_prompt"] = base_match.group(1).strip()

        # Extract Notes
        notes_match = re.search(r"\nNotes?:\s*(.*)$", text, re.IGNORECASE | re.DOTALL)
        if notes_match:
            config["notes"] = notes_match.group(1).strip()

        # Split by character blocks
        char_parts = re.split(r"\[\d+\]", text)
        for block in char_parts[1:]:
            # Ignore the rest if we hit notes
            if "Notes:" in block:
                block = block.split("Notes:")[0]
            
            lines = block.strip().splitlines()
            if not lines: continue
            
            raw_name = lines[0].strip()
            name = TextParser._fuzzy_match(raw_name, available_characters)
            
            if name:
                char_entry = {
                    "name": name,
                    "outfit": "Base",
                    "pose_category": "",
                    "pose_preset": "",
                    "action_note": "",
                    "color_scheme": "",
                    "use_signature_color": False
                }
                
                block_text = "\n".join(lines[1:])
                
                m = re.search(r"Outfit:\s*(.*?)(?:\n|$)", block_text, re.IGNORECASE)
                if m: char_entry["outfit"] = m.group(1).strip()
                
                m = re.search(r"Pose:\s*(.*?)(?:\n|$)", block_text, re.IGNORECASE)
                if m: char_entry["pose_preset"] = m.group(1).strip()
                
                m = re.search(r"Note:\s*(.*?)(?:\n|$)", block_text, re.IGNORECASE)
                if m: char_entry["action_note"] = m.group(1).strip()
                
                m = re.search(r"Colors?:\s*(.*?)(?:\n|$)", block_text, re.IGNORECASE)
                if m: char_entry["color_scheme"] = m.group(1).strip()
                
                m = re.search(r"Sig(?:nature)?:\s*(.*?)(?:\n|$)", block_text, re.IGNORECASE)
                if m: 
                    sig_val = m.group(1).strip().lower()
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
