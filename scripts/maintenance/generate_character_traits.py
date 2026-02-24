import os
import re
from pathlib import Path

def analyze_character_traits():
    characters_dir = Path("assets/data/characters")
    if not characters_dir.exists():
        print(f"Error: Directory {characters_dir} not found.")
        return

    char_files = list(characters_dir.glob("*.md"))
    missing_traits = []
    
    # regex for traits section
    traits_pattern = re.compile(r"^\*\*Traits:\*\*", re.MULTILINE)
    
    for char_file in char_files:
        content = char_file.read_text(encoding='utf-8')
        
        # Check if Traits section exists and has content
        has_traits = False
        match = traits_pattern.search(content)
        if match:
            # Check if there are list items following the header
            lines = content[match.end():].splitlines()
            for line in lines:
                line = line.strip()
                if not line: continue
                if line.startswith("---") or line.startswith("##") or line.startswith("**"):
                    break # Reached next section
                if line.startswith("-") or line.startswith("*"):
                    has_traits = True
                    break
        
        if not has_traits:
            missing_traits.append(char_file)
            
    print(f"Audit complete. {len(missing_traits)} / {len(char_files)} characters missing Traits.")
    
    if missing_traits:
        print("\nCharacters missing traits:")
        for char in sorted(missing_traits):
            print(f"- {char.name}")
            
    return missing_traits

def suggest_traits_for_file(char_file):
    """
    Proposed helper to suggest traits based on Tags and Summary.
    This can be used in an interactive mode or to generate a report.
    """
    content = char_file.read_text(encoding='utf-8')
    # Extract tags
    tags_match = re.search(r"^\*\*Tags:\*\*\s*(.*)$", content, re.MULTILINE)
    summary_match = re.search(r"^\*\*Summary:\*\*\s*(.*)$", content, re.MULTILINE)
    
    tags = tags_match.group(1) if tags_match else ""
    summary = summary_match.group(1) if summary_match else ""
    
    # simple heuristic for suggestions
    suggestions = []
    if "Glasses" in tags or "glasses" in summary.lower():
        suggestions.append("- Glasses: characteristic eyewear")
    if "Jewelry" in summary.lower() or "necklace" in summary.lower():
        suggestions.append("- Jewelry: signature accessories")
    if "Traditional" in tags:
        suggestions.append("- Cultural Accents: traditional signature elements")
        
    return suggestions

if __name__ == "__main__":
    analyze_character_traits()
