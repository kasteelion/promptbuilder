import re
from typing import Any, Dict, List, Optional

class TextParser:
    """Parses natural language or structured text blocks into prompt configurations."""

    @staticmethod
    def parse_import_text(text: str, available_characters: List[str]) -> Dict[str, Any]:
        """Parse a text block into a configuration dictionary.
        
        Args:
            text: The text to parse
            available_characters: List of valid character names for fuzzy matching
            
        Returns:
            Dict: Config ready for state manager
        """
        config = {
            "selected_characters": [],
            "base_prompt": "Default",
            "scene": "",
            "notes": ""
        }

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        # 1. Detect format type
        is_structured = "### PROMPT CONFIG ###" in text or "---" in text
        
        if is_structured:
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
        scene_match = re.search(r"Scene:\s*(.*?)(?:\n---\n|\n\[|$)", text, re.IGNORECASE | re.DOTALL)
        if scene_match:
            config["scene"] = scene_match.group(1).strip()
            
        # Extract Base Prompt
        base_match = re.search(r"Base:\s*(.*?)(?:\n|$)", text, re.IGNORECASE)
        if base_match:
            config["base_prompt"] = base_match.group(1).strip()

        # Extract Notes
        notes_match = re.search(r"Notes?:\s*(.*?)(?:\n---\n|\n\[|$)", text, re.IGNORECASE | re.DOTALL)
        if notes_match:
            config["notes"] = notes_match.group(1).strip()

        # Extract Characters
        # Pattern: [1] Name followed by fields until next [ or --- or end
        char_blocks = re.findall(r"\\[\d+\\]\s*(.*?)(?:\n\\[|\n---\n|\nNotes:|$)", text, re.DOTALL | re.IGNORECASE)
        
        for block in char_blocks:
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
                
                # Parse fields in block
                block_text = "\n".join(lines[1:])
                
                outfit_match = re.search(r"Outfit:\s*(.*?)(?:\n|$)", block_text, re.IGNORECASE)
                if outfit_match: char_entry["outfit"] = outfit_match.group(1).strip()
                
                pose_match = re.search(r"Pose:\s*(.*?)(?:\n|$)", block_text, re.IGNORECASE)
                if pose_match: char_entry["pose_preset"] = pose_match.group(1).strip()
                
                note_match = re.search(r"Note:\s*(.*?)(?:\n|$)", block_text, re.IGNORECASE)
                if note_match: char_entry["action_note"] = note_match.group(1).strip()
                
                color_match = re.search(r"Colors?:\s*(.*?)(?:\n|$)", block_text, re.IGNORECASE)
                if color_match: char_entry["color_scheme"] = color_match.group(1).strip()
                
                sig_match = re.search(r"Sig(nature)?:\s*(.*?)(?:\n|$)", block_text, re.IGNORECASE)
                if sig_match: char_entry["use_signature_color"] = True

                config["selected_characters"].append(char_entry)
                
        return config

    @staticmethod
    def _parse_summary_style(text: str, available_characters: List[str]) -> Dict[str, Any]:
        """Parses the shorthand format: [1] Name (Outfit, Pose)"""
        config = {
            "selected_characters": [],
            "base_prompt": "Default",
            "scene": "",
            "notes": ""
        }
        
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Detect icons/prefixes
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
                
            # Character pattern: [Index] Name (Outfit, Optional, Pose)
            # Or just Name (Outfit, Pose)
            char_match = re.search(r"(?:\\[\d+\\]\s*)?(.*?)\s*\((.*?)\)", line)
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
                    # If 3 params, middle is likely color scheme
                    if len(params) == 3:
                        char_entry["color_scheme"] = params[1]
                    
                    config["selected_characters"].append(char_entry)
            else:
                # Try just a name on a line
                name = TextParser._fuzzy_match(line, available_characters)
                if name:
                    config["selected_characters"].append({
                        "name": name,
                        "outfit": "Base",
                        "pose_preset": ""
                    })
                    
        return config

    @staticmethod
    def _fuzzy_match(raw_name: str, available: List[str]) -> Optional[str]:
        """Simple fuzzy match for character names."""
        raw_low = raw_name.lower().strip()
        if not raw_low: return None
        
        # 1. Exact match (case insensitive)
        for name in available:
            if name.lower() == raw_low:
                return name
                
        # 2. Starts with
        for name in available:
            if name.lower().startswith(raw_low):
                return name
                
        # 3. Contains
        for name in available:
            if raw_low in name.lower():
                return name
                
        return None
