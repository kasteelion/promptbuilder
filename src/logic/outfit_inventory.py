"""
Outfit Inventory Scanner.

This module is responsible for scanning the data/outfits directory and 
legacy outfit files to build a catalog of available components (parts, materials, fits).
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Any
from logic.data_loader import DataLoader

class OutfitInventory:
    """Scans and indexes outfit components from the data directory."""

    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self.inventory = {
            "Top": {},     # { "Neckline": { "Square", "V-Neck"... }, "Material": {...} }
            "Bottom": {},
            "Footwear": {},
            "Accessories": {},
            # Add other slots as discovered
        }
        self.base_templates = {} 
        self.curated_attributes = {} # Loaded from attributes.json

    def scan(self):
        """Perform a full scan of all outfit sources."""
        self._load_curated_attributes()
        # self._scan_directory() # Disable full scan for now to simplify? 
        # User wants simple options. Scanned data is too messy.
        # But we still need to know specific modifiers if the template asks for them?
        # Actually, let's keep scan but PRIORITIZE curated.
        self._scan_directory()
        self._scan_templates() 
        self._scan_legacy_files()
        return self.inventory

    def _load_curated_attributes(self):
        """Load curated attributes from json."""
        import json
        attr_file = self.loader.base_dir / "data" / "outfits" / "attributes.json"
        if attr_file.exists():
            try:
                self.curated_attributes = json.loads(attr_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Failed to load attributes.json: {e}")

    # ... (scan methods) ...

    def get_options(self, slot: str, attribute: str) -> List[str]:
        """Get list of available options for a specific slot attribute."""
        options = set()
        
        # 1. Curated options first - STRICT MODE
        # If we have a curated list, use it EXCLUSIVELY to avoid "metric crapload" of noise.
        if slot in self.curated_attributes and attribute in self.curated_attributes[slot]:
            return sorted(self.curated_attributes[slot][attribute])

        # 2. Scanned options (Fallback only)
        if slot in self.inventory and attribute in self.inventory[slot]:
            return sorted(list(self.inventory[slot][attribute]))
        return []

    def get_supported_attributes(self, slot: str) -> List[str]:
        """Get list of attributes we have data for."""
        # return sorted(list(self.inventory[slot].keys()))
        
        # Use curated keys order if available
        if slot in self.curated_attributes:
            return list(self.curated_attributes[slot].keys())
            
        if slot in self.inventory:
            return sorted(list(self.inventory[slot].keys()))
        return []

    def _scan_templates(self):
        """Scan data/outfits/Templates/*.txt"""
        base_dir = self.loader.base_dir
        templates_dir = base_dir / "data" / "outfits" / "Templates"
        
        if not templates_dir.exists():
            return

        for f in templates_dir.glob("*.txt"):
            try:
                # We store templates separately so they can be listed first/exclusively
                self.base_templates[f.stem] = f
                # Also parse them to populate inventory "slots" if needed, 
                # but usually templates CONSUME inventory, not provide it. 
                # So we might NOT want to call _parse_outfit_file(f) if that adds to inventory options.
                # However, for now, let's just index the file path.
            except Exception as e:
                print(f"Failed to parse template {f.name}: {e}")

    def _scan_directory(self):
        """Scan data/outfits/**/*.txt"""
        # We need to find the data directory. 
        # DataLoader has logic for this, but let's assume standard path relative to loader base.
        base_dir = self.loader.base_dir
        outfits_dir = base_dir / "data" / "outfits"
        
        if not outfits_dir.exists():
            return

        for f in outfits_dir.rglob("*.txt"):
            if "Templates" in f.parts: # Skip templates in general scan if needed
                continue
                
            try:
                self._parse_outfit_file(f)
            except Exception as e:
                print(f"Failed to parse {f.name}: {e}")

    def _scan_legacy_files(self):
        """Scan data/outfits_*.md"""
        # We can reuse DataLoader's load_outfits to get the parsed dict
        # then walk that dict to extract parts.
        raw_outfits = self.loader.load_outfits() 
        # format: {'F': {'Casual': {...}, ...}, 'M': ...}
        
        for gender, categories in raw_outfits.items():
            for cat_name, items in categories.items():
                # items is dict of outfit_name -> content text or dict
                # The legacy parser output might be unstructured text or structured.
                # If it's the standard parser, it returns text blobs usually.
                # We might need to re-parse the raw text if we want fine-grained attributes.
                pass 
                # For V1, let's focus on the new .txt format which is cleaner for parts.
                # Legacy markdown often has "Top: Description" as a single string.
                # Parsing that is harder. We will skip deep extraction for legacy for now
                # unless we write a specific fuzzy parser.

    def parse_slot_line(self, line: str):
        """Public helper to parse a line for slot/value data.
        
        Returns match object with groups (key, value) or None.
        """
        stripped = line.strip()
        return re.match(r"^-\s*\*\*(.+?):\*\*\s*(.*)", stripped)

    def _parse_outfit_file(self, file_path: Path):
        """Parse a structured outfit .txt file."""
        text = file_path.read_text(encoding="utf-8")
        outfit_name = file_path.stem

        # We don't verify base templates here anymore, we do it in _scan_templates
        # But for non-template files, we can still use them as bases if we want?
        # User wants "Wizard" flow, likely ONLY templates.
        
        lines = text.splitlines()
        current_slot = None # Top, Bottom, etc.
        file_modifiers = [] # List of modifier keys found in this file
        
        # 1. First Pass: Scan for modifiers block
        in_modifiers = False
        for line in lines:
            s = line.strip()
            if s.startswith("modifiers:"):
                in_modifiers = True
                continue
            if in_modifiers:
                # If we hit a block start like [F] or empty line? 
                # Usually modifiers block is indented or just keys.
                # Format: "  Square: description"
                if s.startswith("[") or (s and not line.startswith(" ")): 
                    # End of indented block
                    in_modifiers = False
                elif ":" in s:
                    # Capture key
                    key = s.split(":", 1)[0].strip()
                    file_modifiers.append(key)

        # 2. Second Pass: Parse structure
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # Detect indent
            indent_level = len(line) - len(line.lstrip())
            
            # Syntax check
            match = self.parse_slot_line(line)
            if match:
                key = match.group(1).strip()
                val = match.group(2).strip()
                
                # Check known slots first
                if key in ["Top", "Bottom", "Footwear", "Accessories", "Hijab", "Underwear", "Outerwear", "One-Piece"]:
                    current_slot = key
                    if current_slot not in self.inventory:
                        self.inventory[current_slot] = {}
                elif current_slot:
                    # Attribute
                    attr_name = key
                    
                    # Clean up value
                    values = [v.strip().rstrip(".") for v in val.split(";")]
                    
                    if attr_name not in self.inventory[current_slot]:
                        self.inventory[current_slot][attr_name] = set()
                    
                    for v in values:
                        if "{modifier}" in v:
                            # This attribute uses modifiers! Add them to options
                            for mod in file_modifiers:
                                self.inventory[current_slot][attr_name].add(mod)
                        elif v and "{" not in v:
                            self.inventory[current_slot][attr_name].add(v)

    def get_options(self, slot: str, attribute: str, style: str = None, context: Dict = None) -> List[str]:
        """Get list of available options for a specific slot attribute, with style context."""
        
        # 0. Handle Aliases (e.g. Accessory 1 -> Accessories)
        lookup_slot = slot
        if slot.startswith("Accessory"):
            lookup_slot = "Accessories"
            
        # 1. Check for Conditional Logic (Detail_Map)
        # We check this FIRST because specific overrides should beat generic lists
        if context and "Type" in context:
            selected_type = context["Type"]
            # Check if this attribute is mapped for this type
            # We need to find where Detail_Map is defined (Common or Style)
            
            # Helper to check a dictionary for Detail_Map
            def check_map(data_source):
                if lookup_slot in data_source and "Detail_Map" in data_source[lookup_slot]:
                    dmap = data_source[lookup_slot]["Detail_Map"]
                    if attribute in ["Detail", "Style", "Jewelry"] and selected_type in dmap:
                         # The map might be Key->List or Key->Dict->List? 
                         # Plan said: "Detail_Map": { "Hat": ["Wide Brim"] }
                         # So if attribute is broad, we look here.
                         # But wait, attributes.json structure for Detail_Map was: "Hat": ["..."]
                         # This implies "Detail_Map" REPLACES the "Detail" attribute options.
                         return dmap[selected_type]
                return None

            # Check Style then Common
            if style and style in self.curated_attributes:
                res = check_map(self.curated_attributes[style])
                if res: return sorted(res)
            
            if "Common" in self.curated_attributes:
                res = check_map(self.curated_attributes["Common"])
                if res: return sorted(res)

        # 2. Style-specific options (e.g. Gown -> Top -> Neckline)
        if style and style in self.curated_attributes:
            style_data = self.curated_attributes[style]
            if lookup_slot in style_data and attribute in style_data[lookup_slot]:
                return sorted(style_data[lookup_slot][attribute])

        # 3. Common options fallback
        if "Common" in self.curated_attributes:
            common = self.curated_attributes["Common"]
            
            # Special Color Handling: Color is in Common root, not just slots
            if attribute == "Color" and "Color" in common:
                 return sorted(common["Color"])

            if lookup_slot in common and attribute in common[lookup_slot]:
                 return sorted(common[lookup_slot][attribute])

        # 4. Scanned options (Fallback only)
        if lookup_slot in self.inventory and attribute in self.inventory[lookup_slot]:
            return sorted(list(self.inventory[lookup_slot][attribute]))
        
        return []

    def get_supported_attributes(self, slot: str, style: str = None) -> List[str]:
        """Get list of attributes we have data for."""
        attrs = set()
        
        # Style specific
        if style and style in self.curated_attributes:
            if slot in self.curated_attributes[style]:
                attrs.update(self.curated_attributes[style][slot].keys())
                
        # Common
        if "Common" in self.curated_attributes:
            if slot in self.curated_attributes["Common"]:
                 attrs.update(self.curated_attributes["Common"][slot].keys())
        
        # Scanned
        if slot in self.inventory:
            attrs.update(self.inventory[slot].keys())
            
        return sorted(list(attrs))
