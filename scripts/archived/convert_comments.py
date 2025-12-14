"""Archived: convert_comments

Legacy script preserved for history. Not used by default.
"""

def main():
    print("This script is archived and disabled.")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""Convert HTML comment blocks <!-- ... --> to // style note lines in character files.

Backs up original files with a .bak extension.
"""
from pathlib import Path
import re

CHAR_DIR = Path(__file__).resolve().parent.parent / "data" / "characters"

def convert_block(content: str) -> (str, int):
    """Convert all HTML comment blocks in content to // lines.

    Returns (new_content, replacements_count)
    """
    replacements = 0

    def _repl(match):
        nonlocal replacements
        inner = match.group(1)
        # Split into lines and prefix with //
        lines = inner.splitlines()
        # Remove leading/trailing blank lines
        while lines and lines[0].strip() == "":
            lines.pop(0)
        while lines and lines[-1].strip() == "":
            lines.pop()
        out_lines = ["// " + ln.rstrip() if ln.strip() != "" else "//" for ln in lines]
        replacements += 1
        return "\n" + "\n".join(out_lines) + "\n"

    # Replace any <!-- ... --> blocks (DOTALL)
    new_content = re.sub(r"(?s)<!--\s*(.*?)\s*-->", _repl, content)
    return new_content, replacements


def process_file(path: Path):
    text = path.read_text(encoding="utf-8")
    new_text, count = convert_block(text)
    if count > 0 and new_text != text:
        bak = path.with_suffix(path.suffix + ".bak")
        bak.write_text(text, encoding="utf-8")
        path.write_text(new_text, encoding="utf-8")
    return count


def main():
    if not CHAR_DIR.exists():
        print(f"Characters directory not found: {CHAR_DIR}")
        return

    total = 0
    for md in sorted(CHAR_DIR.glob("*.md")):
        c = process_file(md)
        if c:
            print(f"Updated {md.name}: {c} comment block(s) converted")
            total += c
    print(f"Done. Total converted: {total}")

if __name__ == '__main__':
    main()
