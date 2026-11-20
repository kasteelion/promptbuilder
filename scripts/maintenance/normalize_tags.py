"""Normalize tags.md to Title Case (matching character files) and add missing tags."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from logic.data_loader import DataLoader
from pathlib import Path

d = DataLoader()
d.clear_cache()
chars = d.load_characters()

# Collect all character tags (authoritative casing)
char_tag_casing = {}  # lowercase -> Title Case from characters
for name, cdata in chars.items():
    tags = cdata.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]
    for t in tags:
        char_tag_casing[t.lower()] = t

# Read tags.md
tags_path = Path(__file__).parent.parent.parent / "assets" / "data" / "lists" / "tags.md"
if not tags_path.exists():
    # Try alternate location
    tags_path = Path(__file__).parent.parent.parent / "assets" / "data" / "tags.md"
    
if not tags_path.exists():
    print("Error: tags.md not found in expected locations.")
    sys.exit(1)
content = tags_path.read_text(encoding='utf-8')
lines = content.split('\n')

new_lines = []
current_category = None
tags_in_md = set()

for line in lines:
    stripped = line.strip()
    
    # Category header
    if stripped.startswith('## '):
        current_category = stripped[3:].strip()
        new_lines.append(line)
        continue
    
    # Tag line (starts with -)
    if stripped.startswith('- '):
        tag = stripped[2:].strip()
        tag_lower = tag.lower()
        tags_in_md.add(tag_lower)
        
        # Use character's casing if available, otherwise Title Case
        if tag_lower in char_tag_casing:
            fixed_tag = char_tag_casing[tag_lower]
        else:
            # Title case but preserve hyphenated words
            fixed_tag = '-'.join(w.capitalize() for w in tag.split('-'))
        
        new_lines.append(f'- {fixed_tag}')
        continue
    
    new_lines.append(line)

# Add truly missing tags (in characters but not tags.md)
missing = []
for lower_tag, title_tag in char_tag_casing.items():
    if lower_tag not in tags_in_md:
        missing.append(title_tag)

if missing:
    # Add to end under a new section or existing "Other" section
    new_lines.append('')
    new_lines.append('## Uncategorized')
    for t in sorted(missing):
        new_lines.append(f'- {t}')

output = '\n'.join(new_lines)
tags_path.write_text(output, encoding='utf-8')

print(f"Normalized {len(tags_in_md)} tags to Title Case")
print(f"Added {len(missing)} missing tags: {sorted(missing)}")
print("Done!")
