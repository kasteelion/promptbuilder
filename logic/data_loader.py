"""Data loading utilities for markdown files."""

import sys
from pathlib import Path
from .parsers import MarkdownParser


class DataLoader:
    """Loads markdown files from the same directory as this script (or cwd)."""

    def __init__(self):
        try:
            # Use Path(__file__).parent if run as a script
            self.base_dir = Path(sys.argv[0]).resolve().parent
        except Exception:
            # Fallback for environments where __file__ is not defined
            self.base_dir = Path.cwd()

    def load_outfits(self):
        """Load and parse shared outfits from outfits.md file. Creates file if not found."""
        f = self.base_dir / "outfits.md"
        if not f.exists():
            default_content = """## Common Outfits
### Casual
A simple and comfortable casual outfit.
"""
            f.write_text(default_content, encoding="utf-8")
            return {"Common": {"Casual": "A simple and comfortable casual outfit."}}
        
        text = f.read_text(encoding="utf-8")
        outfits = MarkdownParser.parse_shared_outfits(text)
        return outfits if outfits else {"Common": {}}

    def load_characters(self):
        """Load and parse character files from characters/ folder, merging with shared outfits.
        
        Looks for individual character markdown files in the characters/ folder.
        Falls back to characters.md for backwards compatibility.
        """
        chars_dir = self.base_dir / "characters"
        chars = {}
        # Try loading from characters folder first
        if chars_dir.exists() and chars_dir.is_dir():
            for char_file in sorted(chars_dir.glob("*.md")):
                try:
                    text = char_file.read_text(encoding="utf-8")
                    # Parse single character file
                    file_chars = MarkdownParser.parse_characters(text)
                    if not file_chars:
                        print(f"Warning: No characters found in {char_file.name}")
                    chars.update(file_chars)
                except Exception as e:
                    print(f"Error loading {char_file.name}: {e}")

        # If no character files were found, attempt to create a sample character
        if not chars:
            try:
                # Ensure characters directory exists
                chars_dir.mkdir(parents=True, exist_ok=True)

                sample_file = chars_dir / "sample_character.md"
                if not sample_file.exists():
                    default_content = """### Sample Character
**Appearance:** A sample character for you to get started.

**Outfits:**

#### Base
- **Top:** Simple tee
- **Bottom:** Basic jeans
"""
                    sample_file.write_text(default_content, encoding="utf-8")

                # Read all character files from the characters folder (including the sample)
                for char_file in sorted(chars_dir.glob("*.md")):
                    try:
                        text = char_file.read_text(encoding="utf-8")
                        file_chars = MarkdownParser.parse_characters(text)
                        chars.update(file_chars)
                    except Exception as e:
                        print(f"Error parsing {char_file.name}: {e}")
            except Exception as e:
                print(f"Error creating sample character: {e}")
                # Fallback to legacy characters.md location for backwards compatibility
                f = self.base_dir / "characters.md"
                if not f.exists():
                    default_content = """### Sample Character
**Appearance:** A sample character for you to get started.
**Outfits:**
- **Base:** A default outfit.
"""
                    f.write_text(default_content, encoding="utf-8")
                
                text = f.read_text(encoding="utf-8")
                chars = MarkdownParser.parse_characters(text)
        
        if not chars:
            raise ValueError("No characters parsed from characters/ folder or characters.md. Please check the file format.")
        
        # Load shared outfits and merge with each character
        shared_outfits = self.load_outfits()
        for char_name, char_data in chars.items():
            merged_outfits = MarkdownParser.merge_character_outfits(
                char_data, shared_outfits, char_name
            )
            char_data["outfits"] = merged_outfits
        
        return chars

    def load_base_prompts(self):
        """Load and parse base_prompts.md file. Creates file if not found."""
        f = self.base_dir / "base_prompts.md"
        default_prompt = {"Default": "Soft semi-realistic illustration with clear, natural lighting. Fresh muted florals, calm tonal balance."}
        
        if not f.exists():
            default_content = """## Default
Soft semi-realistic illustration with clear, natural lighting. Fresh muted florals, calm tonal balance.
---
"""
            f.write_text(default_content, encoding="utf-8")
            return default_prompt
        
        text = f.read_text(encoding="utf-8")
        prompts = MarkdownParser.parse_base_prompts(text)
        return prompts if prompts else default_prompt

    def load_presets(self, filename: str):
        """Load and parse preset files (scenes.md, poses.md, etc.). Creates file if not found."""
        f = self.base_dir / filename
        
        defaults_content = {
            "scenes.md": """## Default
- **Coffee Shop:** Cozy coffee shop interior, warm ambient lighting, wooden tables, comfortable seating.
- **Beach:** Sandy beach at golden hour, gentle waves, soft sunlight, relaxed atmosphere.
""",
            "poses.md": """## General
- **Standing:** Standing naturally, relaxed posture, arms at sides.
- **Sitting:** Sitting comfortably, casual pose.
"""
        }
        
        defaults_data = {
            "scenes.md": {
                "Default": {
                    "Coffee Shop": "Cozy coffee shop interior, warm ambient lighting, wooden tables, comfortable seating",
                    "Beach": "Sandy beach at golden hour, gentle waves, soft sunlight, relaxed atmosphere",
                }
            },
            "poses.md": {
                "General": {
                    "Standing": "Standing naturally, relaxed posture, arms at sides",
                    "Sitting": "Sitting comfortably, casual pose",
                }
            },
        }

        if not f.exists():
            if filename in defaults_content:
                f.write_text(defaults_content[filename], encoding="utf-8")
                return defaults_data.get(filename, {"Default": {}})
            else:
                return {"Default": {}}

        text = f.read_text(encoding="utf-8")
        parsed = MarkdownParser.parse_presets(text)
        return parsed if parsed else defaults_data.get(filename, {"Default": {}})
