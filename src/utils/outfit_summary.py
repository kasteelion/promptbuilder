#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Outfit summary generator.

Parses outfit files (outfits_f.md, outfits_m.md, outfits_h.md) and generates
structured data for summary display.
"""

from pathlib import Path
from logic.outfit_parser import OutfitParser

def generate_outfit_data(data_dir=None):
    """Generate structured outfit data from markdown files.

    Returns:
        dict: {
            "F": {category: {name: description, ...}},
            "M": {category: {name: description, ...}},
            "H": {category: {name: description, ...}}
        }
    """
    if data_dir is None:
        # Get the directory of the current script (src/utils)
        current_dir = Path(__file__).resolve().parent
        # Project root is two levels up (src/utils -> src -> root)
        root = current_dir.parent.parent
        
        data_dir = root / "assets" / "data"
        if not data_dir.exists():
             # Fallback for different execution environments
             data_dir = Path.cwd() / "assets" / "data"
             if not data_dir.exists():
                 data_dir = root / "data"
    else:
        data_dir = Path(data_dir)

    outfits = {}
    
    # 1. Try New Directory Structure (Preferred)
    outfits_dir = data_dir / "outfits"
    if outfits_dir.exists() and outfits_dir.is_dir():
        return OutfitParser.parse_outfits_directory(outfits_dir)

    # 2. Fallback to Legacy Files
    for modifier in ["f", "m", "h"]:
        file_path = data_dir / f"outfits_{modifier}.md"
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                parsed = OutfitParser.parse_shared_outfits(content)
                outfits[modifier.upper()] = parsed
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                outfits[modifier.upper()] = {}
        else:
            outfits[modifier.upper()] = {}

    return outfits

def generate_consolidated_outfit_data(data_dir=None):
    """Generate outfit data grouped by Category -> Outfit Name -> Variations.
    
    Also detects modifiers.
    
    Returns:
        dict: {
            category_name: {
                outfit_name: {
                    "variations": {"F": desc, "M": desc, "H": desc},
                    "has_color_scheme": bool,
                    "has_signature": bool
                }
            }
        }
    """
    raw_data = generate_outfit_data(data_dir)
    consolidated = {}
    
    
    # Iterate through all modifiers
    for mod, categories in raw_data.items():
        for cat, outfits in categories.items():
            if cat not in consolidated:
                consolidated[cat] = {}
            
            for name, data in outfits.items():
                if name not in consolidated[cat]:
                    consolidated[cat][name] = {
                        "variations": {}, # F/M/H variations
                        "has_color_scheme": False,
                        "has_signature": False,
                        "tags": [],
                        "variants": [] # Outfit styling variants
                    }
                
                # 'data' is a dict: {'description': str, 'tags': list}
                # We need the description string for the variations map and checks
                desc_str = data.get("description", "")
                
                # Add variation
                consolidated[cat][name]["variations"][mod] = desc_str
                
                # Extract outfit styling variants
                if not consolidated[cat][name]["variants"]:
                    v_dict = data.get("variants", {})
                    if len(v_dict) > 1:
                        consolidated[cat][name]["variants"] = list(v_dict.keys())
                
                # Check modifiers in the description text
                if "{primary_color}" in desc_str or "{secondary_color}" in desc_str or "{accent}" in desc_str:
                    consolidated[cat][name]["has_color_scheme"] = True
                
                if "(signature)" in desc_str or "**Signature Color:**" in desc_str: # Check for signature syntax
                    # The syntax in outfits is ((default:...) or (signature))
                    if "(signature)" in desc_str:
                        consolidated[cat][name]["has_signature"] = True

                # Extract tags (if available in any variation)
                # Assuming tags are consistent across gender variations for the same outfit name
                if "tags" not in consolidated[cat][name] or not consolidated[cat][name]["tags"]:
                    # Try to find tags in the current item
                    t = data.get("tags")
                    if t:
                        consolidated[cat][name]["tags"] = t
                    else:
                        consolidated[cat][name]["tags"] = []

    return consolidated

def format_outfit_summary(outfit_data):
    """Format outfit data into a readable string summary."""
    lines = []
    lines.append("=" * 80)
    lines.append("OUTFIT LIBRARY SUMMARY")
    lines.append("=" * 80)
    lines.append("")

    for modifier, categories in outfit_data.items():
        mod_name = "Female" if modifier == "F" else "Male" if modifier == "M" else "Hijabi"
        lines.append(f"## {mod_name} Outfits ({modifier})")
        lines.append("-" * 40)
        
        for cat, items in sorted(categories.items()):
            lines.append(f"\n[{cat}]")
            for name, desc in sorted(items.items()):
                lines.append(f"  • {name}")
                # Optional: include truncated description
                # short_desc = desc.split('\n')[0][:60] + "..." if len(desc) > 60 else desc.split('\n')[0]
                # lines.append(f"    {short_desc}")
        
        lines.append("\n")

    return "\n".join(lines)

if __name__ == "__main__":
    data = generate_outfit_data()
    print(format_outfit_summary(data))
