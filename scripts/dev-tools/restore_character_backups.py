"""
Restores character markdown files from their .bak backups, effectively
reverting the changes made by the migration script.

This script will:
- Scan all .md.bak files in the data/characters/ directory.
- Overwrite the corresponding .md file with the content of the .bak file.
- Remove the .bak file after a successful restoration.
"""

import os
from pathlib import Path
import shutil
import sys

def restore_backups():
    """Restores character files from .bak backups."""
    try:
        project_root = Path(__file__).resolve().parents[1]
        characters_dir = project_root / "data" / "characters"
    except IndexError:
        print("Error: This script appears to be in the wrong directory. It should be in a 'scripts' folder inside your project root.")
        sys.exit(1)


    if not characters_dir.is_dir():
        print(f"FATAL: Character directory not found at '{characters_dir}'")
        sys.exit(1)

    print("-" * 50)
    print("Restoring character files from backups.")
    print(f"Scanning directory: {characters_dir}")
    print("-" * 50)

    backups = list(characters_dir.glob("*.md.bak"))
    if not backups:
        print("No backup files (.md.bak) found to restore.")
        return

    restored_count = 0
    for backup_path in backups:
        original_path = backup_path.with_suffix("")  # Removes .bak

        try:
            # Copy the backup over the original
            shutil.copy(backup_path, original_path)
            print(f"  - Restored {original_path.name} from {backup_path.name}")
            
            # Remove the backup file
            os.remove(backup_path)
            print(f"  - Removed backup file {backup_path.name}")
            restored_count += 1
        except Exception as e:
            print(f"  ERROR: Failed to restore {original_path.name}: {e}")

    print("-" * 50)
    print(f"Restoration complete. {restored_count} file(s) restored.")
    print("-" * 50)

if __name__ == "__main__":
    restore_backups()
