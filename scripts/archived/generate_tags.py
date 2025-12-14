"""Archived: generate_tags

Legacy script preserved for history. Not used by default.
"""

def main():
    print("This script is archived and disabled.")

if __name__ == '__main__':
    main()
"""Scan character files and insert/replace `**Tags:**` using heuristics.

Creates backups before modification.
"""
import sys
import pathlib
from pathlib import Path
import re
import shutil

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from logic.data_loader import DataLoader
from utils import logger


def main() -> int:
    loader = DataLoader()
    chars = loader.load_characters()
    chars_dir = loader._find_characters_dir()

    if not chars_dir.exists():
        logger.error("Characters directory not found: %s", chars_dir)
        return 1

    md_files = sorted(chars_dir.glob("*.md"))
    header_re = re.compile(r"^###\s+(.+)", re.MULTILINE)
    summary_re = re.compile(r"\*\*Summary:\*\*\s*(.+)", re.IGNORECASE)
    tags_re = re.compile(r"\*\*Tags:\*\*\s*(.+)", re.IGNORECASE)

    # Heuristic mapping from appearance/summary keywords to tags
    heuristics = [
        (re.compile(r"dance|gym|athletic|training|fit|workout|sports|soccer|basketball|mma|jiu jitsu", re.I), "athletic"),
        (re.compile(r"bohemian|cottage|maxi|floral|peasant|boho", re.I), "bohemian"),
        (re.compile(r"cosplay|anime|egirl|eboy|soft egirl|soft eboy|cosplay", re.I), "cosplay"),
        (re.compile(r"goth|gothic|punk|leather|edgy|alternative|dark academia", re.I), "edgy"),
        (re.compile(r"cocktail|formal|evening|gown|suit|tuxedo|elegant|bridal", re.I), "formal"),
        (re.compile(r"vintage|retro|pinup|1950s|dapper|greaser", re.I), "vintage"),
        (re.compile(r"fantasy|armor|warrior|medieval|myth|goddess|god|ren faire", re.I), "fantasy"),
        (re.compile(r"casual|streetwear|hoodie|jeans|everyday|comfort|yoga|athleisure|street", re.I), "casual"),
        (re.compile(r"soft|gentle|warm|natural|friendly|approach", re.I), "soft"),
        # 'soft' should be conservative: require an explicit soft cue and avoid conflicting edgy cues
        (re.compile(r"\b(soft|gentle|warm|natural|tender|delicate|subtle)\b", re.I), "soft"),
        (re.compile(r"romantic|romance|rosy|blush|dreamy", re.I), "romantic"),
        (re.compile(r"playful|youthful|quirky|bubbly|fun|cheerful", re.I), "playful"),
        (re.compile(r"mysterious|enigmatic|brood|smolder|sultry|moody", re.I), "mysterious"),
        (re.compile(r"chic|sleek|polished|stylish|minimalist|modern", re.I), "chic"),
        (re.compile(r"preppy|plaid|oxford|polo|prep|school|uniform", re.I), "preppy"),
        (re.compile(r"grunge|distressed|gritty|flannel|riot|grunge", re.I), "grunge"),
        (re.compile(r"glam|glossy|sequins|glamorous|dazzle", re.I), "glam"),
        (re.compile(r"androgynous|androgyny|gender[- ]?neutral", re.I), "androgynous"),
        (re.compile(r"nerd|geek|glasses|bookish|studious|academic", re.I), "nerdy"),
        (re.compile(r"curvy|plus|plus-size|plus size|full[- ]?figured|curv|hourglass", re.I), "curvy"),
    ]

    updated = []
    for p in md_files:
        text = p.read_text(encoding="utf-8")
        m = header_re.search(text)
        if not m:
            continue
        name = m.group(1).strip()

        char_data = chars.get(name, {})
        appearance = char_data.get("appearance", "") or ""
        summary = char_data.get("summary", "") or ""
        gender = char_data.get("gender", "").lower()

        found = set()
        # gender tag
        if gender in ("m", "male"):
            found.add("male")
        elif gender in ("f", "female"):
            found.add("female")

        combined = f"{summary}\n{appearance}"

        # First pass: detect all heuristic tags except 'soft'
        for rx, tag in heuristics:
            if tag == "soft":
                continue
            if rx.search(combined):
                found.add(tag)

        # Soft detection: only add if soft cues exist and no strong conflicting tags
        soft_rx = None
        for rx, tag in heuristics:
            if tag == "soft":
                soft_rx = rx
                break

        if soft_rx and soft_rx.search(combined):
            # Define conflicting tags that make 'soft' unlikely
            conflicts = {"edgy", "grunge", "cosplay", "fantasy", "formal", "glam"}
            if not (found & conflicts):
                found.add("soft")

        # fallbacks: prefer a neutral 'character' tag rather than 'soft'
        if not found:
            found.add("character")

        # canonical order
        ordered = sorted(found)
        tags_line = ", ".join(ordered)

        # backup
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

        # replace or insert
        if tags_re.search(text):
            new_text = tags_re.sub(f"**Tags:** {tags_line}", text)
        else:
            # insert after header or photo
            lines = text.splitlines()
            insert_idx = None
            for i, line in enumerate(lines[:20]):
                if line.strip() == f"### {name}":
                    if i + 1 < len(lines) and lines[i + 1].strip().lower().startswith("**photo:"):
                        insert_idx = i + 2
                    else:
                        insert_idx = i + 1
                    break
            if insert_idx is None:
                insert_idx = 0
            new_lines = lines[:insert_idx] + ["", f"**Tags:** {tags_line}"] + lines[insert_idx:]
            new_text = "\n".join(new_lines)

        p.write_text(new_text, encoding="utf-8")
        updated.append((p.name, tags_line))

    logger.info("Updated %d files with tags (backups created).", len(updated))
    for u in updated:
        logger.info("%s -> %s", u[0], u[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
