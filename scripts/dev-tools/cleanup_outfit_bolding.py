import re
from pathlib import Path

def clean_value(text):
    """Remove redundant bolding from the start of a value."""
    # Matches "**Value** (desc)" or "**Value**" and strips outer bolding
    # But only if it's the very first thing in the string.
    m = re.match(r'^\s*\*\*(.*?)\*\*(.*)$', text)
    if m:
        return m.group(1) + m.group(2)
    return text

def migrate_file(filepath):
    path = Path(filepath)
    if not path.exists(): return

    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        m = re.match(r'^(\s*-\s*\*\*[^:]+:\*\*\s*)(.*)$', line)
        if m:
            prefix = m.group(1)
            value = m.group(2)
            new_lines.append(prefix + clean_value(value))
        else:
            new_lines.append(line)

    path.write_text('\n'.join(new_lines), encoding='utf-8')
    print(f"Cleaned {path}")

if __name__ == "__main__":
    migrate_file("data/outfits_f.md")
    migrate_file("data/outfits_m.md")
    migrate_file("data/outfits_h.md")

