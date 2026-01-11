"""Archived: scan_photos

Legacy script preserved for history. Not used by default.
"""


def main():
    print("This script is archived and disabled.")


if __name__ == "__main__":
    main()
"""Scan character markdown files for **Photo:** metadata and report missing files.

Usage: python scripts/scan_photos.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import logic.parsers as parsers
from logic.data_loader import DataLoader
from utils import logger


def main() -> int:
    loader = DataLoader()
    chars_dir = loader._find_characters_dir()
    if not chars_dir.exists():
        logger.error("Characters directory not found: %s", chars_dir)
        return 1

    md_files = sorted(chars_dir.glob("*.md"))
    total = 0
    missing_photo = []
    broken_photo = []
    multiple_photos = []

    for p in md_files:
        total += 1
        text = p.read_text(encoding="utf-8")
        # Find all photo occurrences
        photos = parsers._PHOTO_RE.findall(text)
        if not photos:
            missing_photo.append(p.name)
            continue

        if len(photos) > 1:
            multiple_photos.append((p.name, photos))

        # Check existence of first photo reference
        ph = photos[0].strip()
        # Try relative to characters dir first
        candidate = chars_dir / ph
        exists = candidate.exists()
        if not exists:
            # Try resolving as absolute path
            candidate2 = Path(ph)
            exists = candidate2.exists()

        if not exists:
            broken_photo.append((p.name, ph))

    # Report
    logger.info("Photo scan report")
    logger.info("==================")
    logger.info("Character files scanned: %d", total)
    logger.info("Files missing **Photo:** line: %d", len(missing_photo))
    for n in missing_photo:
        logger.info("  - %s", n)

    logger.info("Files with broken/missing image file: %d", len(broken_photo))
    for n, ph in broken_photo:
        logger.info("  - %s: %s", n, ph)

    logger.info("Files with multiple **Photo:** lines: %d", len(multiple_photos))
    for n, phs in multiple_photos:
        logger.info("  - %s: %s", n, phs)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
