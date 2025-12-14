"""Utility to add a `**Gender:** F` tag to existing character markdown files if missing.

Run this from the project root to update files under `data/characters/`.

This script is non-destructive: it will create a `.bak` copy of any file it modifies.
"""
from pathlib import Path

CHAR_DIR = Path("data") / "characters"

if not CHAR_DIR.exists():
    print("Characters directory not found:", CHAR_DIR)
    raise SystemExit(1)

for p in sorted(CHAR_DIR.glob("*.md")):
    text = p.read_text(encoding="utf-8")
    if "**Gender:**" in text:
        print(f"Skipping {p.name}: already has Gender tag")
        continue

    lines = text.splitlines()
    insert_idx = None
    # Try to insert after the Photo line if present
    for i, line in enumerate(lines[:20]):
        if line.strip().lower().startswith("**photo:"):
            insert_idx = i + 1
            break
    if insert_idx is None:
        # Otherwise insert after the header line (### Name)
        for i, line in enumerate(lines[:6]):
            if line.strip().startswith("### "):
                insert_idx = i + 1
                break
    if insert_idx is None:
        # As a last resort, prepend
        insert_idx = 0

    new_lines = lines[:insert_idx] + ["", "**Gender:** F"] + lines[insert_idx:]
    import shutil

    bak = p.with_suffix(p.suffix + ".bak")
    # If backup exists, add a numeric suffix
    if bak.exists():
        idx = 1
        while True:
            candidate = p.with_suffix(p.suffix + f".bak{idx}")
            if not candidate.exists():
                bak = candidate
                break
            idx += 1

    shutil.copy(p, bak)
    p.write_text("\n".join(new_lines), encoding="utf-8")
    print(f"Updated {p.name} -> added Gender tag (backup saved as {bak.name})")

print("Done")
