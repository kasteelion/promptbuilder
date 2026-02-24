import re
from typing import Any, Dict, List, Optional, Union
from core.models import CharacterDetails, CharacterMetadata, OutfitItem
from pydantic import ValidationError
from utils import logger

# Pre-compile regex patterns for better performance
_SUBSECTION_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)
_OUTFIT_RE = re.compile(r"^####\s+(.+)$", re.MULTILINE)
_PHOTO_RE = re.compile(r"\*\*Photo:\*\*\s*([^\n\r]+)", re.IGNORECASE)
_APPEARANCE_RE = re.compile(r"\*\*Appearance:\*\*\s*(.*?)(?=\n\s*\*\*Outfits:|\n\s*\*\*(?:Tags|Gender|Signature Color|Traits|Age Presentation|Vibe|Bearing|Summary):|$)", re.DOTALL | re.IGNORECASE)
_GENDER_RE = re.compile(r"\*\*Gender:\*\*\s*([mfMF])\b", re.IGNORECASE)
_MODIFIER_RE = re.compile(r"\*\*Modifier:\*\*\s*([^\n\r]+)", re.IGNORECASE)
_SUMMARY_RE = re.compile(r"\*\*Summary:\*\*\s*(.+?)(?=\n\s*\*\*|$)", re.DOTALL | re.IGNORECASE)
_TAGS_RE = re.compile(r"\*\*Tags:\*\*\s*(.+?)(?=\n\s*\*\*|$)", re.DOTALL | re.IGNORECASE)
_SIGNATURE_COLOR_RE = re.compile(r"\*\*Signature Color:\*\*\s*([^\n\r]+)", re.IGNORECASE)
_AGE_PRESENTATION_RE = re.compile(r"\*\*Age Presentation:\*\*\s*(.+?)(?=\n\s*\*\*|\n\s*//|\n\s*---|\n\s*\n|$)", re.IGNORECASE)
_VIBE_RE = re.compile(r"\*\*Vibe\s*/\s*Energy:\*\*\s*(.+?)(?=\n\s*\*\*|\n\s*//|\n\s*---|\n\s*\n|$)", re.IGNORECASE)
_BEARING_RE = re.compile(r"\*\*Bearing:\*\*\s*(.+?)(?=\n\s*\*\*|\n\s*//|\n\s*---|\n\s*\n|$)", re.IGNORECASE)
_TRAITS_RE = re.compile(r"\*\*Traits:\*\*\s*(.*?)(?=\n\s*\*\*Outfits:|\n\s*\*\*(?:Tags|Gender|Signature Color|Age Presentation|Vibe|Bearing|Summary|Appearance):|\n\s*-{3,}|$)", re.DOTALL | re.IGNORECASE)
_IDENTITY_LOCKS_HEADER_RE = re.compile(
    r"^Appearance\s*\(Identity Locks\):\s*$", re.IGNORECASE | re.MULTILINE
)
_IDENTITY_LOCK_LINE_RE = re.compile(r"^\s*-\s*(Body|Face|Hair|Skin):\s*(.*)$", re.IGNORECASE)


class CharacterParser:
    """Parses character definitions from markdown content."""

    @staticmethod
    def parse_characters(content: str) -> Dict[str, CharacterDetails]:
        """Parse character definitions from markdown content with validation."""
        characters = {}
        parts = _SUBSECTION_RE.split(content)
        for i in range(1, len(parts), 2):
            name = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""

            try:
                char_data = CharacterParser._parse_single_character_body(body)
                char_data["name"] = name
                characters[name] = CharacterDetails(**char_data)
            except ValidationError as e:
                logger.error(f"Validation error for character '{name}': {e}")
                # Optional: Add a partial/broken character or skip
                continue
            except Exception as e:
                logger.error(f"Unexpected error parsing character '{name}': {e}")
                continue

        return characters

    @staticmethod
    def scan_metadata(content: str, mtime: float = 0.0, file_size: int = 0) -> Dict[str, CharacterMetadata]:
        """Lightweight scan of character metadata (for gallery/lazy loading)."""
        metadata = {}
        parts = _SUBSECTION_RE.split(content)
        for i in range(1, len(parts), 2):
            name = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            
            # Extracts only what's needed for the gallery
            photo_match = _PHOTO_RE.search(body)
            t_match = _TAGS_RE.search(body)
            v_match = _VIBE_RE.search(body)
            b_match = _BEARING_RE.search(body)
            g_match = _GENDER_RE.search(body)
            
            a_match = _AGE_PRESENTATION_RE.search(body)
            
            def truncate(s):
                if not s: return None
                # Take only the first part before a semicolon or comma
                clean = re.split(r'[;]', s)[0].strip()
                if len(clean) > 30:
                    clean = clean[:27] + "..."
                return clean

            metadata[name] = CharacterMetadata(
                name=name,
                photo=photo_match.group(1).strip() if photo_match else None,
                tags=[t.strip() for t in re.split(r",|;", t_match.group(1))] if t_match else [],
                vibe=truncate(v_match.group(1)) if v_match else None,
                bearing=truncate(b_match.group(1)) if b_match else None,
                age_presentation=truncate(a_match.group(1)) if a_match else None,
                gender=g_match.group(1).upper() if g_match else "F",
                mtime=mtime,
                file_size=file_size
            )
        return metadata

    @staticmethod
    def _parse_single_character_body(body: str) -> dict:
        """Parse the body content of a single character section."""
        # 1. High-level Metadata
        photo_match = _PHOTO_RE.search(body)
        photo = photo_match.group(1).strip() if photo_match else None

        app_match = _APPEARANCE_RE.search(body)
        appearance = app_match.group(1).strip() if app_match else ""
        
        # Clean appearance
        appearance = re.sub(r"(?s)<!--.*?-->", "", appearance).strip()
        if appearance:
            lines = [ln for ln in appearance.splitlines() if not re.match(r"^\s*//", ln)]
            appearance = "\n".join(lines).strip()

        summary_match = _SUMMARY_RE.search(body)
        summary = summary_match.group(1).strip() if summary_match else None

        # 2. Outfits
        outfits = CharacterParser._parse_outfits(body)

        # 3. Attributes & Traits (Metadata block)
        meta = CharacterParser._parse_metadata(body)

        # 4. Post-process outfits (One-piece detection etc)
        CharacterParser._post_process_outfits(outfits)

        return {
            "appearance": appearance,
            "summary": summary,
            "outfits": outfits,
            "photo": photo,
            **meta
        }

    @staticmethod
    def _parse_outfits(body: str) -> dict:
        """Extract and parse outfits from the character body."""
        outfits = {}
        outfit_parts = _OUTFIT_RE.split(body)
        
        if len(outfit_parts) > 1:
            for i in range(1, len(outfit_parts), 2):
                o_name = outfit_parts[i].strip()
                o_body = outfit_parts[i + 1] if i + 1 < len(outfit_parts) else ""
                outfits[o_name] = CharacterParser._parse_outfit_details(o_body)
        else:
            # Legacy single-line format: - **Name:** description
            for m in re.finditer(r"-\s+\*\*([^:]+):\*\*\s*(.+)", body):
                outfits[m.group(1).strip()] = m.group(2).strip()
        
        return outfits

    @staticmethod
    def _parse_outfit_details(o_body: str) -> Union[str, Dict[str, Any]]:
        """Parse structured items within a single outfit block."""
        items = {}
        o_tags = []
        lines = o_body.splitlines()
        line_idx = 0
        
        # Extract Meta Header (Tags)
        while line_idx < len(lines):
            line = lines[line_idx].strip()
            if not line:
                line_idx += 1
                continue
            tags_m = re.match(r"\*\*Tags:\*\*\s*(.+)", line, re.IGNORECASE)
            if tags_m:
                o_tags = [t.strip() for t in re.split(r",|;", tags_m.group(1)) if t.strip()]
                line_idx += 1
                continue
            # Look ahead for items (bullet or key: value)
            if re.match(r"^\s*[-*]\s+", line) or (":" in line and not line.startswith("//")):
                break
            line_idx += 1

        last_key = None
        last_indent = 0
        item_found = False

        # Parse Items
        while line_idx < len(lines):
            line = lines[line_idx]
            if not line.strip():
                line_idx += 1
                continue
            
            # Match bullet or raw key: value
            m_marker = re.match(r"^\s*([-*])\s+(.*)$", line)
            
            if m_marker:
                item_found = True
                content = m_marker.group(2)
                current_indent = len(line) - len(line.lstrip())
                
                # Handle Nested Bullets (Indentation logic)
                if last_key and current_indent > last_indent:
                    items[last_key] = f"{items[last_key]}\n{line.strip()}"
                    line_idx += 1
                    continue
                
                last_indent = current_indent
                key, val = CharacterParser._split_key_val(content)
                
                # Collect continuation lines for this item
                next_idx = line_idx + 1
                val_lines = [val] if val else []
                while next_idx < len(lines) and not re.match(r"^\s*[-*]\s+", lines[next_idx]) and not re.match(r"^####\s+", lines[next_idx]):
                    val_lines.append(lines[next_idx].strip())
                    next_idx += 1
                
                final_val = " ".join(val_lines).strip()
                if key:
                    items[key] = final_val
                    last_key = key
                line_idx = next_idx
            else:
                # [RESILIENCE] Try to parse raw Key: Value if no bullet found but it seems structured
                if ":" in line and not line.strip().startswith("//"):
                    key, val = CharacterParser._split_key_val(line.strip())
                    if key and key.lower() in ["top", "bottom", "outerwear", "footwear", "accessories", "hair/makeup", "makeup", "dress", "suit"]:
                        item_found = True
                        items[key] = val
                        last_key = key
                line_idx += 1

        if item_found:
            items["tags"] = o_tags
            return items
        return o_body.strip()

    @staticmethod
    def _split_key_val(text: str) -> tuple:
        """Split a bullet point or line into key and value."""
        # 1. Match **Key**: Value or **Key:** Value
        m = re.match(r"^\s*\*\*(.*?)(?::\s*)?\*\*[:\s]+(.*)$", text)
        if m:
            return m.group(1).strip(), m.group(2).strip()
        
        # 2. Match Key: Value
        if ":" in text:
            parts = text.split(":", 1)
            # Ensure the key isn't too long (avoid splitting sentences)
            if len(parts[0]) < 30:
                return parts[0].strip(), parts[1].strip()
            
        return None, text.strip()

    @staticmethod
    def _parse_metadata(body: str) -> dict:
        """Extract character attributes and traits."""
        meta = {}
        
        # Gender
        gender_match = _GENDER_RE.search(body)
        meta["gender"] = gender_match.group(1).upper() if gender_match else "F"
        meta["gender_explicit"] = bool(gender_match or _MODIFIER_RE.search(body))

        # Modifiers & Signature
        m_match = _MODIFIER_RE.search(body)
        meta["modifier"] = m_match.group(1).strip() if m_match else None
        
        s_match = _SIGNATURE_COLOR_RE.search(body)
        meta["signature_color"] = s_match.group(1).strip() if s_match else None

        # Tags
        t_match = _TAGS_RE.search(body)
        meta["tags"] = [t.strip() for t in re.split(r",|;", t_match.group(1))] if t_match else []

        # Tiers (Truncated for clean UI/Prompting)
        def truncate_metadata(s):
            if not s: return None
            # Take only the first part before a semicolon
            clean = re.split(r'[;]', s)[0].strip()
            if len(clean) > 40: # Slightly more lenient for full details
                clean = clean[:37] + "..."
            return clean

        pairs = [
            ("age_presentation", _AGE_PRESENTATION_RE),
            ("vibe", _VIBE_RE),
            ("bearing", _BEARING_RE)
        ]
        for key, regex in pairs:
            m = regex.search(body)
            meta[key] = truncate_metadata(m.group(1)) if m else None

        # Traits
        traits = {}
        tr_match = _TRAITS_RE.search(body)
        if tr_match:
            for line in tr_match.group(1).strip().splitlines():
                line = line.strip()
                if line.startswith("- "):
                    content = line[2:].strip()
                    if ":" in content:
                        k, v = content.split(":", 1)
                        traits[k.strip().strip("*")] = v.strip()
                    else:
                        traits[content.strip().strip("*")] = content
        meta["traits"] = traits
        
        return meta

    @staticmethod
    def _post_process_outfits(outfits: dict):
        """Analyze outfits for one-piece detection and other logic."""
        for name, data in outfits.items():
            if not isinstance(data, dict): continue
            
            # Detect One-Piece
            bottom_val = None
            bottom_key = next((k for k in data if k.lower() == "bottom"), None)
            if bottom_key:
                bottom_val = str(data[bottom_key]).lower()
            
            is_one_piece = not bottom_key or not bottom_val or any(k in bottom_val for k in ["na", "none", "one-piece", "dress", "teddy"])
            
            if is_one_piece:
                data["Bottom"] = None
                data["one_piece"] = True

    @staticmethod
    def parse_identity_locks(appearance_text: str) -> dict | None:
        """Attempt to parse an "Appearance (Identity Locks)" structured block."""
        if not appearance_text:
            return None

        if not _IDENTITY_LOCKS_HEADER_RE.search(appearance_text):
            if not re.search(r"^\s*-\s*Body:\s*", appearance_text, re.MULTILINE | re.IGNORECASE):
                return None

        result = {
            "Body": "",
            "Face": "",
            "Hair": "",
            "Skin": "",
            "Age Presentation": "",
            "Vibe / Energy": "",
            "Bearing": "",
        }

        for ln in appearance_text.splitlines():
            m = _IDENTITY_LOCK_LINE_RE.match(ln)
            if m:
                key = m.group(1).strip().title()
                val = m.group(2).strip()
                if key in result:
                    result[key] = val

        for key in ("Age Presentation", "Vibe / Energy", "Bearing"):
            pat = re.compile(rf"^{re.escape(key)}:\s*(.*)$", re.IGNORECASE | re.MULTILINE)
            mm = pat.search(appearance_text)
            if mm:
                result[key] = mm.group(1).strip()

        if not any(result[k] for k in ("Body", "Face", "Hair", "Skin")):
            return None

        return result

    @staticmethod
    def format_identity_locks(fields: dict) -> str:
        """Format a dict of identity-locks into the exact block the framework expects."""
        def g(k):
            v = fields.get(k, "")
            return v.strip() if isinstance(v, str) else ""

        parts = ["Appearance (Identity Locks):\n"]
        parts.append(f"- Body: {g('Body')}\n")
        parts.append(f"- Face: {g('Face')}\n")
        parts.append(f"- Hair: {g('Hair')}\n")
        parts.append(f"- Skin: {g('Skin')}\n\n")
        parts.append(f"Age Presentation: {g('Age Presentation')}\n")
        parts.append(f"Vibe / Energy: {g('Vibe / Energy')}\n")
        parts.append(f"Bearing: {g('Bearing')}\n")

        return "".join(parts).strip()
