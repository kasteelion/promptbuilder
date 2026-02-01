"""
Outfit Builder Logic.

Responsible for assembling a final outfit description from a template file
and a set of user selections.
"""

from pathlib import Path
from typing import Dict, Any
import re

class OutfitBuilder:
    """Assembles outfits from templates."""

    def assemble(self, template_path: Path, selections: Dict[str, Dict[str, str]]) -> str:
        """
        Assemble an outfit string based on the template and selections.

        Args:
            template_path: Path to the .txt template file.
            selections: Dict of { Slot: { Attribute: SelectedValue } }
                        e.g. { "Top": { "Neckline": "Square", "Material": "Velvet" } }

        Returns:
            The formatted outfit text block (e.g. for saving to file).
        """
        text = template_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        
        # 1. Parse Modifiers (Key -> Description)
        modifiers_map = {}
        in_modifiers = False
        for line in lines:
            s = line.strip()
            if s.startswith("modifiers:"):
                in_modifiers = True
                continue
            if in_modifiers:
                if s.startswith("[") or (s and not line.startswith(" ")):
                    in_modifiers = False
                elif ":" in s:
                    # Capture "Square": "featuring a dramatic..."
                    parts = s.split(":", 1)
                    key = parts[0].strip()
                    desc = parts[1].strip()
                    modifiers_map[key] = desc

        # 2. Reconstruct Body
        output_lines = []
        current_slot = None
        
        # We only want to output the [F] block (or whatever gender we are building for).
        # For V1, let's assume we output the full file structure BUT acting on the [F] block
        # or maybe we just return the [F] block?
        # The user probably wants to save a specific outfit for a character.
        # Let's assume we are generating a snippet for a CHARACTER file or a CUSTOM OUTFIT file.
        # If custom outfit file, we might keep [F]/[M] structure if the user customized both?
        # Unlikely. Usually they customize for one target.
        # Let's default to outputting just the Gender block that was customized?
        # Or just output the whole file with replacements.
        # Let's output the whole file with replacements to preserve structure for now.
        
        for line in lines:
            stripped = line.strip()
            
            # Passthrough empty or modifier block (we might want to strip format block in final)
            # If we are "saving" a concrete outfit, we don't need the modifiers block anymore!
            # We should probably strip lines identifying as modifiers block.
            if stripped.startswith("modifiers:") or (stripped and line.startswith("  ") and line.split(":")[0].strip() in modifiers_map):
                continue
                
            # Detect Slot
            match = re.match(r"^-\s*\*\*(.+?):\*\*\s*(.*)", stripped)
            if match:
                key = match.group(1).strip()
                val = match.group(2).strip()
                
                if key in ["Top", "Bottom", "Footwear", "Accessories", "Hijab", "Underwear", "Outerwear", "One-Piece"]:
                    current_slot = key
                    
                    # 1. Start with the raw value from template
                    new_val = val
                    
                    # 2. Interpolate variables (e.g. {Material} -> "Silk")
                    new_val = self._interpolate(new_val, selections, current_slot)

                    output_lines.append(f"- **{key}:** {new_val}")
                    continue

            # Detect Attribute Line (Nested)
            # e.g. "  - **Material:** {Material}"
            attr_match = re.match(r"^\s*-\s*\*\*(.+?):\*\*\s*(.*)", line)
            if attr_match and current_slot:
                 attr_key = attr_match.group(1).strip()
                 attr_val = attr_match.group(2).strip()
                 
                 # 1. Try to get explicit selection first?
                 # Actually, with the new template format, the line IS "{Variable}".
                 # So we just interpolate the line.
                 
                 # Interpolate the VALUE part of the attribute line
                 interpolated_val = self._interpolate(attr_val, selections, current_slot)
                 
                 # If the result is empty (and it was a variable), we might want to hide the line?
                 # But sticking to the user's request: just show the result (even if empty).
                 # If the user selected nothing, it returns "".
                 # "- **Material:** " (empty) is better than "- **Material:** {Material}".
                 
                 # Reconstruct line with indentation
                 indent = line[:line.find("-")]
                 output_lines.append(f"{indent}- **{attr_key}:** {interpolated_val}.")
                 continue
            
            # Default/Other lines (just interpolate them too)
            # e.g. descriptions without bold keys
            interpolated_line = self._interpolate(line, selections, current_slot)
            output_lines.append(interpolated_line)

        return "\n".join(output_lines)

    def _interpolate(self, text: str, selections: Dict, current_slot: str) -> str:
        """Helper to replace {Variable} placeholders with selected values."""
        if not current_slot or not text:
            return text
            
        variables = re.findall(r"\{([^}]+)\}", text)
        new_text = text
        
        for var_name in variables:
            # Look up in selections
            replacement = selections.get(current_slot, {}).get(var_name)
            
            if replacement:
                # User made a selection -> Replace
                pattern = r"\{" + re.escape(var_name) + r"\}"
                new_text = re.sub(pattern, replacement, new_text)
            else:
                # User made NO selection.
                # User wants "basic stuff" visible in preview. 
                # Keep {Variable} so they know it's a dynamic slot.
                pass
            
        # Clean up artifacts
        # 1. Double spaces
        new_text = re.sub(r"\s+", " ", new_text).strip()
        # 2. Empty parenthesis "()" -> "" (optional)
        new_text = new_text.replace("()", "")
        # 3. Fix floating punctuation like " ." -> "."
        new_text = new_text.replace(" .", ".")
        new_text = new_text.replace(" ,", ",")
        
        return new_text
