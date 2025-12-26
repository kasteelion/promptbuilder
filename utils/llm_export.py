"""Utility for exporting application data in an LLM-friendly format."""

from typing import Dict, Any, List
from utils.outfit_summary import generate_consolidated_outfit_data

def generate_llm_export_text(ctx: Any) -> str:
    """Generate a condensed text block for knowledge injection into an LLM."""
    
    # 1. System Instructions
    lines = [
        "### SYSTEM INSTRUCTIONS for PromptBuilder ###",
        "You are a creative director. Use the provided catalog to generate prompt configurations.",
        "Output MUST be in this specific format for the app to parse it:",
        "",
        "### PROMPT CONFIG ###",
        "Base: [Art Style Name]",
        "Scene: [Descriptive environment paragraph]",
        "---",
        "[1] [Character Name]",
        "Outfit: [Outfit Name]",
        "Colors: [Optional Team Color Scheme]",
        "Sig: [Yes/No - use character signature color]",
        "Pose: [Pose Name or Custom description]",
        "Note: [Specific action or facial expression detail]",
        "---",
        "Notes: [Interaction details between characters]",
        "",
        "RULES:",
        "- Use [1], [2], [3] for multiple characters.",
        "- Match character names and outfit names as closely as possible.",
        "- If a pose isn't in the list, describe it in the 'Pose' field.",
        "- 'Sig: Yes' applies the character's unique signature color to the outfit.",
        "- Outfits marked with (🎨) support 'Colors: [Scheme]'.",
        "- Outfits marked with (✨) support 'Sig: Yes'.",
        "- MODIFIER NOTE: 'F' = Female, 'M' = Male, 'H' = Hijabi.",
        "",
        "--- CATALOG BEGINS ---",
        ""
    ]

    # 2. Base Prompts (Art Styles)
    lines.append("## AVAILABLE ART STYLES (Base)")
    for name in sorted(ctx.base_prompts.keys()):
        lines.append(f"- {name}")
    lines.append("")

    # 3. Characters
    lines.append("## AVAILABLE CHARACTERS")
    lines.append("Format: Name (Modifier) [Signature Color] [Tags]")
    lines.append("Note: Modifier 'H' indicates the character is Hijabi.")
    for name, data in sorted(ctx.characters.items()):
        mod = data.get("modifier") or data.get("gender", "F")
        sig = data.get("signature_color", "None")
        tags = ", ".join(data.get("tags", []))
        lines.append(f"- {name} ({mod}) [{sig}] [{tags}]")
    lines.append("")

    # 4. Outfits (Consolidated)
    lines.append("## OUTFIT LIBRARY")
    lines.append("Legend: 🎨 = Supports Team Colors, ✨ = Supports Signature Color")
    
    outfit_data = generate_consolidated_outfit_data()
    for cat_name in sorted(outfit_data.keys()):
        lines.append(f"### {cat_name}")
        outfits = outfit_data[cat_name]
        for out_name in sorted(outfits.keys()):
            data = outfits[out_name]
            indicators = ""
            if data["has_color_scheme"]: indicators += " 🎨"
            if data["has_signature"]: indicators += " ✨"
            
            # Since outfits are synced across F/M/H, we just list the name and indicators
            lines.append(f"  * {out_name}{indicators}")
    lines.append("")

    # 5. Poses
    lines.append("## PRESET POSES")
    for cat, items in sorted(ctx.poses.items()):
        item_list = ", ".join(sorted(items.keys()))
        lines.append(f"  * {cat}: {item_list}")
    lines.append("")

    # 6. Color Schemes
    lines.append("## TEAM COLOR SCHEMES (Apply to 🎨 outfits)")
    lines.append(", ".join(sorted(ctx.color_schemes.keys())))
    
    lines.append("\n--- CATALOG ENDS ---")
    
    return "\n".join(lines)
