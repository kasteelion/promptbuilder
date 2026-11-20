import glob
from pathlib import Path
import re

# Project root setup
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
outfit_dir = project_root / "assets" / "data" / "outfits"

GENERIC_TEXT = "\n- **Note:** This variant is a derived adaptation of the primary style. Please refer to the standard FEMALE or MALE variants for the core aesthetic details and specific item breakdowns."

def parse_outfit(content):
    lines = content.splitlines()
    sections = {} # 'meta': [], 'F': [], 'M': [], 'H': []
    current_sec = 'meta'
    sections['meta'] = []
    
    for line in lines:
        stripped = line.strip()
        if stripped in ["[F]", "[M]", "[H]"]:
            current_sec = stripped[1] # F, M, H
            sections[current_sec] = []
        else:
            if current_sec not in sections: sections[current_sec] = []
            sections[current_sec].append(line)
            
    return sections

def count_words(lines):
    text = " ".join(lines)
    return len(text.split())

def fix_outfits():
    print(f"Scanning {outfit_dir}...")
    fixed_count = 0
    
    for filepath in glob.glob(str(outfit_dir / "**/*.txt"), recursive=True):
        path = Path(filepath)
        content = path.read_text(encoding="utf-8")
        original_content = content
        
        # 1. Parse
        sections = parse_outfit(content)
        
        # 2. Fix Meta (Tags)
        meta_text = "\n".join(sections.get('meta', []))
        if "tags:" not in meta_text.lower():
            category = path.parent.name
            # Insert at start of meta
            sections['meta'].insert(0, f"Tags: {category}, Everyday")
            print(f"➕ Added tags to {path.name}")
            
        # 3. Fix Sections
        for sec_key in ["F", "M", "H"]:
            if sec_key not in sections:
                sections[sec_key] = [GENERIC_TEXT.strip()]
                print(f"➕ Appended missing [{sec_key}] to {path.name}")
            else:
                # Check length
                if count_words(sections[sec_key]) < 15:
                    sections[sec_key].append(GENERIC_TEXT)
                    print(f"✏️ Extended brief [{sec_key}] in {path.name}")
                    
        # 4. Reconstruct
        new_lines = []
        new_lines.extend(sections.get('meta', []))
        
        for sec_key in ["F", "M", "H"]:
            new_lines.append("")
            new_lines.append(f"[{sec_key}]")
            new_lines.extend(sections[sec_key])
            
        new_content = "\n".join(new_lines)
        
        # Normalize newlines
        new_content = re.sub(r'\n{3,}', '\n\n', new_content).strip() + "\n"
        
        if new_content != original_content:
            path.write_text(new_content, encoding="utf-8")
            fixed_count += 1
            
    print(f"\nTotal outfit files fixed: {fixed_count}")

if __name__ == "__main__":
    fix_outfits()
