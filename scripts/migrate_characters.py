"""
Migrates character markdown files from the legacy free-form appearance format
to the new structured "Appearance (Identity Locks)" format.

This script will:
- Scan all .md files in the data/characters/ directory.
- Create a .bak backup of each original file before modifying it.
- Parse the old format to extract Body, Face, Hair, Skin, and other fields.
- Write a new version of the file with the standardized
  "Appearance (Identity Locks):" block.
"""

import re
from pathlib import Path
import shutil
import sys

# Add the project root to the Python path to allow imports from logic
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from logic.parsers import MarkdownParser
except ImportError:
    print("Error: Could not import MarkdownParser. Make sure you are running this script from the 'scripts' directory.")
    sys.exit(1)


def migrate_character_file(file_path: Path):
    """Migrates a single character file to the new Identity Locks format."""
    print(f"Processing {file_path.name}...")
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ERROR: Could not read file: {e}")
        return

    # 1. Check if already migrated
    if "Appearance (Identity Locks):" in content:
        print("  INFO: Skipping, already in new format.")
        return

    # 2. Backup the original file
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    if backup_path.exists():
        print(f"  INFO: Skipping, backup file already exists at {backup_path.name}")
        return
    
    try:
        shutil.copy(file_path, backup_path)
        print(f"  - Backed up original file to {backup_path.name}")
    except Exception as e:
        print(f"  ERROR: Could not create backup file: {e}")
        return

    # 3. Parse old format to extract data
    fields = {
        "Body": "", "Face": "", "Hair": "", "Skin": "",
        "Age Presentation": "", "Vibe / Energy": "", "Bearing": ""
    }
    
    # Extract the main Appearance block
    appearance_match = re.search(r"\*\*Appearance:\*\*(.*?)(?=\n---\s*\n\*\*Outfits:\*\*|\Z)", content, re.DOTALL)
    if not appearance_match:
        print(f"  WARNING: Could not find a distinct Appearance block in {file_path.name}.")
        # Continue, as some fields might be outside
    else:
        appearance_block = appearance_match.group(1)
        # Parse bullet points inside the appearance block
        for line in appearance_block.splitlines():
            stripped_line = line.strip()
            if stripped_line.startswith(("* ", "- ")):
                parts = stripped_line[2:].split(':', 1)
                if len(parts) == 2:
                    key = parts[0].replace('*', '').strip()
                    if key in fields:
                        fields[key] = parts[1].strip()

    # Some fields might be defined outside the main block
    for key in fields:
        if not fields[key]: # Only search if not already found
            # Regex to find 'Key: value' or '**Key:** value'
            match = re.search(rf"^\s*(?:\*\*)?{re.escape(key)}(?:\*\*)?:\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
            if match:
                fields[key] = match.group(1).strip()

    # 4. Format the new appearance block
    new_appearance_block = MarkdownParser.format_identity_locks(fields)

    # 5. Reconstruct the file content
    # Find everything before the appearance block
    pre_appearance_match = re.search(r"(.*?\*\*Appearance:\*\*)", content, re.DOTALL)
    if pre_appearance_match:
        pre_content = pre_appearance_match.group(1).replace("**Appearance:**", "").strip()
    else:
        # If no appearance block, find header and metadata
        header_match = re.search(r"(###.*\n(?:.*\n)*?)(?=\n---\s*\n\*\*Outfits:\*\*|\Z)", content, re.DOTALL)
        if header_match:
            pre_content = header_match.group(1).strip()
        else:
            print(f"  ERROR: Could not structure file {file_path.name}. Manual edit may be required.")
            return
            
    # Find the outfits block
    outfits_match = re.search(r"(\n---\s*\n\*\*Outfits:\*\*.*)", content, re.DOTALL)
    outfits_content = outfits_match.group(1) if outfits_match else ""

    # Clean up old fields from the pre-content
    lines = pre_content.splitlines()
    cleaned_lines = []
    for line in lines:
        if not any(line.strip().lower().startswith(f"{key.lower()}:") for key in ["age presentation", "vibe / energy", "bearing"]):
            cleaned_lines.append(line)
    
    cleaned_pre_content = "\n".join(cleaned_lines)

    new_content = f"{cleaned_pre_content}\n\n{new_appearance_block}{outfits_content}"
    
    try:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"  SUCCESS: Migrated {file_path.name} to the new format.")
    except Exception as e:
        print(f"  ERROR: Could not write updated file: {e}")


def main():
    """Main function to find and migrate all character files."""
    project_root = Path(__file__).resolve().parents[1]
    characters_dir = project_root / "data" / "characters"

    if not characters_dir.is_dir():
        print(f"FATAL: Character directory not found at '{characters_dir}'")
        sys.exit(1)

    print("-" * 50)
    print("Starting character migration to Identity Locks format.")
    print(f"Scanning directory: {characters_dir}")
    print("-" * 50)

    character_files = list(characters_dir.glob("*.md"))
    if not character_files:
        print("No character files (.md) found to migrate.")
        return

    for file_path in character_files:
        migrate_character_file(file_path)
    
    print("-" * 50)
    print("Migration process complete.")
    print("-" * 50)


if __name__ == "__main__":
    main()
