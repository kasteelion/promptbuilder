"""Analyze tag casing mismatch between tags.md and character files."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from logic.data_loader import DataLoader

d = DataLoader()
d.clear_cache()
chars = d.load_characters()
tags_by_cat = d.load_categorized_tags()

all_md_tags = set()
for cat, tags in tags_by_cat.items():
    for t in tags:
        all_md_tags.add(t)

char_tags_used = set()
for name, cdata in chars.items():
    tags = cdata.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]
    for t in tags:
        char_tags_used.add(t)

md_lower_map = {t.lower(): t for t in all_md_tags}
char_lower_map = {t.lower(): t for t in char_tags_used}

case_mismatches = []
for cl, ct in char_lower_map.items():
    if cl in md_lower_map and md_lower_map[cl] != ct:
        case_mismatches.append((md_lower_map[cl], ct))

truly_missing = []
for cl, ct in char_lower_map.items():
    if cl not in md_lower_map:
        truly_missing.append(ct)

print(f"tags.md total: {len(all_md_tags)}")
print(f"Character tags total: {len(char_tags_used)}")
print(f"Case mismatches: {len(case_mismatches)}")
for md, ch in sorted(case_mismatches):
    print(f"  tags.md: '{md}' | chars: '{ch}'")
print(f"\nTruly new (in chars, not in tags.md): {len(truly_missing)}")
for t in sorted(truly_missing):
    print(f"  {t}")
