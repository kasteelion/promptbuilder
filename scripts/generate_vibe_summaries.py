"""Generate short 'vibe' summaries for character markdown files.

This replaces or inserts a `**Summary:**` line containing a brief trope/vibe.
Backups are created before modification.
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

    # Simple keyword->vibe mapping
    mapping = [
        (re.compile(r"dance|ballet|hip hop|dancer|athletic|gym|training", re.I), "Athletic, energetic performer"),
        (re.compile(r"bohemian|maxi|floral|cottage|peasant|boho", re.I), "Bohemian / soft cottagecore aesthetic"),
        (re.compile(r"cosplay|anime|character|cosplay|egirl|eboy|soft egirl|soft eboy", re.I), "Playful, stylized/cosplay-inspired look"),
        (re.compile(r"goth|dark|leather|alternative|punk|edgy", re.I), "Alternative / edgy aesthetic"),
        (re.compile(r"formal|cocktail|evening|suit|tuxedo|elegant|bridal", re.I), "Elegant, formal evening-ready"),
        (re.compile(r"professional|office|medical|scrub|work", re.I), "Clean, professional / work-ready"),
        (re.compile(r"vintage|retro|pinup|1950s|dapper|dark academia", re.I), "Vintage / classic-inspired"),
        (re.compile(r"fantasy|armor|warrior|medieval|myth|god|goddess|ren faire", re.I), "Fantasy / historical-inspired archetype"),
        (re.compile(r"casual|streetwear|hoodie|jeans|everyday|comfort|yoga|athleisure", re.I), "Casual, modern streetwear vibe"),
        (re.compile(r"soft|gentle|warm|natural|friendly|romantic", re.I), "Soft, approachable and warm"),
    ]

    updated = []

    for p in md_files:
        text = p.read_text(encoding="utf-8")
        m = header_re.search(text)
        if not m:
            continue
        name = m.group(1).strip()

        # Use parsed characters data for appearance if available
        char_data = chars.get(name, {})
        appearance = char_data.get("appearance", "")

        # Build candidate vibes by scanning appearance
        vibe = None
        for rx, label in mapping:
            if rx.search(appearance):
                vibe = label
                break

        if not vibe:
            # Fallback heuristics
            if len(appearance) < 40:
                vibe = "Concise, defined identity"
            else:
                # try to pick a few adjectives from appearance
                words = re.findall(r"\b([A-Za-z]{5,})\b", appearance)
                if words:
                    sample = ", ".join(words[:3])
                    vibe = f"Notable traits: {sample}"
                else:
                    vibe = "Distinctive personal style"

        # Prefer short phrase
        summary_line = vibe

        # Update file with backup
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

        # If summary exists, replace; otherwise insert after header or photo
        if summary_re.search(text):
            new_text = summary_re.sub(f"**Summary:** {summary_line}", text)
        else:
            # find header and next line index
            lines = text.splitlines()
            insert_idx = None
            for i, line in enumerate(lines[:20]):
                if line.strip() == f"### {name}":
                    # place after photo if present
                    if i + 1 < len(lines) and lines[i + 1].strip().lower().startswith("**photo:"):
                        insert_idx = i + 2
                    else:
                        insert_idx = i + 1
                    break
            if insert_idx is None:
                insert_idx = 0
            new_lines = lines[:insert_idx] + ["", f"**Summary:** {summary_line}"] + lines[insert_idx:]
            new_text = "\n".join(new_lines)

        p.write_text(new_text, encoding="utf-8")
        updated.append((p.name, bak.name, summary_line))

    logger.info("Updated %d files. Backups created for each updated file.", len(updated))
    for u in updated:
        logger.info("%s -> %s", u[0], u[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
