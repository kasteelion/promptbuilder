"""Add a `**Summary:**` field to character markdown files when missing.

This script creates backups and inserts a Summary after the character header or photo line.
"""
from pathlib import Path
import re
import shutil
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from logic.data_loader import DataLoader

loader = DataLoader()
chars = loader.load_characters()
chars_dir = loader._find_characters_dir()

if not chars_dir.exists():
    print("Characters directory not found:", chars_dir)
    raise SystemExit(1)

md_files = sorted(chars_dir.glob("*.md"))
summary_re = re.compile(r"\*\*Summary:\*\*", re.IGNORECASE)
photo_re = re.compile(r"\*\*Photo:\*\*")
header_re = re.compile(r"^###\s+(.+)", re.MULTILINE)

updated = []
for p in md_files:
    text = p.read_text(encoding="utf-8")
    if summary_re.search(text):
        # already has summary
        continue

    # Find first character heading in this file
    m = header_re.search(text)
    if not m:
        continue
    name = m.group(1).strip()

    # Get appearance from parser if available
    char_data = chars.get(name, {})
    appearance = char_data.get("appearance", "")

    # Generate a short summary: prefer first sentence, fallback to first 120 chars
    summary = ""
    if appearance:
        # Try to get first sentence (ends with . ? !)
        s_match = re.search(r"(.*?[\.\?!])\s", appearance)
        if s_match:
            summary = s_match.group(1).strip()
        else:
            # fallback to first line or 120 chars
            first_line = appearance.split("\n")[0].strip()
            summary = first_line if len(first_line) <= 140 else first_line[:137] + "..."
    else:
        summary = ""  # empty summary if no appearance

    # Prepare backup
    bak = p.with_suffix(p.suffix + ".bak")
    if bak.exists():
        idx = 1
        while True:
            candidate = p.with_suffix(p.suffix + f".bak{idx}")
            if not candidate.exists():
                bak = candidate
                break
            idx += 1
    shutil.copy(p, bak)

    # Insert summary after header or photo line
    lines = text.splitlines()
    insert_idx = None
    for i, line in enumerate(lines[:20]):
        if line.strip().startswith(f"### {name}"):
            # Check next lines for photo
            if i + 1 < len(lines) and photo_re.search(lines[i + 1]):
                insert_idx = i + 2
            else:
                insert_idx = i + 1
            break
    if insert_idx is None:
        insert_idx = 0

    new_lines = lines[:insert_idx] + ["", f"**Summary:** {summary}"] + lines[insert_idx:]
    p.write_text("\n".join(new_lines), encoding="utf-8")
    updated.append((p.name, bak.name))

print(f"Updated {len(updated)} files. Backups created for each updated file.")
for u in updated[:20]:
    print(u)
