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
        # Assuming run from root or installed package structure
        # Use relative path logic similar to other utilities
        data_dir = Path(__file__).resolve().parents[1] / "data"
    else:
        data_dir = Path(data_dir)

    outfits = {}
    
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
            
            for name, desc in outfits.items():
                if name not in consolidated[cat]:
                    consolidated[cat][name] = {
                        "variations": {},
                        "has_color_scheme": False,
                        "has_signature": False
                    }
                
                # Add variation
                consolidated[cat][name]["variations"][mod] = desc
                
                # Check modifiers
                if "{primary_color}" in desc or "{secondary_color}" in desc or "{accent}" in desc:
                    consolidated[cat][name]["has_color_scheme"] = True
                
                if "(signature)" in desc or "**Signature Color:**" in desc: # Check for signature syntax
                    # The syntax in outfits is ((default:...) or (signature))
                    if "(signature)" in desc:
                        consolidated[cat][name]["has_signature"] = True

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
