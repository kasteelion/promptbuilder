import os
from pathlib import Path

# Project root setup
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
char_dir = project_root / "assets" / "data" / "characters"

# Mapping: Filename -> (Old Target, New Target)
# Based on Audit Report vs File List analysis
fixes = {
    "aryan_kapoor.md": ("aryan_kapoor_photo.jpeg", "aryan_kapoor_photo.png"),
    "callum_doherty.md": ("callum_doherty_photo.jpeg", "callum_doherty_photo.png"),
    "chayton_red_elk.md": ("chayton_redelk_photo.jpeg", "chayton_red-elk_photo.png"),
    "elena_rosales.md": ("elena_rosales_photo.jpeg", "elena_rosales_photo.png"),
    "elias_thorne.md": ("elias_thorne_photo.jpeg", "elias_thorne_photo.png"),
    "julian_blackwood.md": ("julian_blackwood_photo.jpeg", "julian_blackwood_photo.png"),
    "kaito_sato.md": ("kaito_sato_photo.jpeg", "kaito_sato_photo.png"),
    "oliver_st_james.md": ("oliver_st_james_photo.jpeg", "oliver_st._james_photo.png"),
    "priya_sharma.md": ("priya_sharma_photo.jpeg", "priya_sharma_photo.png"),
    "roxanna_perez.md": ("roxanna_photo.png", "roxanna_perez_photo.png"),
    "sina_tuilagi.md": ("sina_tuilagi_photo.jpeg", "sina_tuilagi_photo.png"),
    "siofra_quinn.md": ("siofra_photo.png", "siofra_quinn_photo.png"),
    "zahara_el_amin.md": ("zahara_elamin_photo.png", "zahara_el-amin_photo.png"),
}

def fix_links():
    print(f"Scanning {char_dir}...")
    fixed_count = 0
    
    for filename, (old, new) in fixes.items():
        file_path = char_dir / filename
        if not file_path.exists():
            print(f"❌ File not found: {filename}")
            continue
            
        content = file_path.read_text(encoding="utf-8")
        
        # Check if replacement is needed
        if old in content:
            new_content = content.replace(old, new)
            file_path.write_text(new_content, encoding="utf-8")
            print(f"✅ Fixed {filename}: {old} -> {new}")
            fixed_count += 1
        elif new in content:
             print(f"ℹ️ Already fixed {filename}")
        else:
            print(f"⚠️ Target string '{old}' not found in {filename}")

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    fix_links()
