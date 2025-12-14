"""Archived: add_character_photo

Legacy script preserved for history. Not used by default.
"""

from pathlib import Path

def main():
    print("This script is archived and disabled.")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""Helper: copy an image into `data/characters` with the expected filename.

Usage:
  python scripts/add_character_photo.py --source "C:\path\to\image.png" --dest roxanne_perez_photo.png

If `--dest` is omitted the script will ask for the target filename.
"""
import argparse
import shutil
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Copy a character photo into data/characters")
    parser.add_argument("--source", "-s", required=True, help="Path to source image file")
    parser.add_argument(
        "--dest",
        "-d",
        default=None,
        help="Destination filename inside data/characters (e.g. roxanne_perez_photo.png)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    characters_dir = repo_root / "data" / "characters"
    characters_dir.mkdir(parents=True, exist_ok=True)

    src = Path(args.source).expanduser()
    if not src.exists():
        print(f"Source file does not exist: {src}")
        sys.exit(2)

    if args.dest:
        dest_name = args.dest
    else:
        dest_name = input("Enter destination filename (e.g. roxanne_perez_photo.png): ").strip()
        if not dest_name:
            print("No destination filename provided. Aborting.")
            sys.exit(3)

    dest = characters_dir / dest_name
    try:
        shutil.copy2(src, dest)
        print(f"Copied {src} -> {dest}")
    except Exception as e:
        from utils import logger

        logger.exception("Auto-captured exception")
        print(f"Failed to copy file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
