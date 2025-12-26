"""Parser for character definitions from markdown."""

import re

# Pre-compile regex patterns for better performance
_SUBSECTION_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)
_OUTFIT_RE = re.compile(r"^####\s+(.+)$", re.MULTILINE)
_PHOTO_RE = re.compile(r"\*\*Photo:\*\*\s*(.+?)(?:\n|$)", re.MULTILINE)
_APPEARANCE_RE = re.compile(r"\*\*Appearance:\*\*\s*(.+?)(?:\n\s*\*\*Outfits:|\n\s*\*\*|$)", re.DOTALL)
_GENDER_RE = re.compile(r"\*\*Gender:\*\*\s*([mfMF])\b")
_MODIFIER_RE = re.compile(r"\*\*Modifier:\*\*\s*(.+?)(?:\n\s*\*\*|$)")
_SUMMARY_RE = re.compile(r"\*\*Summary:\*\*\s*(.+?)(?:\n\s*\*\*|$)", re.DOTALL)
_TAGS_RE = re.compile(r"\*\*Tags:\*\*\s*(.+?)(?:\n\s*\*\*|$)", re.DOTALL)
_SIGNATURE_COLOR_RE = re.compile(r"\*\*Signature Color:\*\*\s*(.+?)(?:\n\s*\*\*|$)")
_IDENTITY_LOCKS_HEADER_RE = re.compile(
    r"^Appearance\s*\(Identity Locks\):\s*$", re.IGNORECASE | re.MULTILINE
)
_IDENTITY_LOCK_LINE_RE = re.compile(r"^\s*-\s*(Body|Face|Hair|Skin):\s*(.*)$", re.IGNORECASE)


class CharacterParser:
    """Parses character definitions from markdown content."""

    @staticmethod
    def parse_characters(content: str):
        """Parse character definitions from markdown content.

        Expected format:
        ### Character Name
        **Appearance:** description
        **Outfits:**
        - **Outfit Name:** description
        """
        characters = {}
        parts = _SUBSECTION_RE.split(content)
        for i in range(1, len(parts), 2):
            name = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""

            # Extract photo path if present
            photo = None
            photo_match = _PHOTO_RE.search(body)
            if photo_match:
                photo = photo_match.group(1).strip()

            app_match = _APPEARANCE_RE.search(body)
            appearance = app_match.group(1).strip() if app_match else ""

            # Extract optional summary if present
            summary = None
            summary_match = _SUMMARY_RE.search(body)
            if summary_match:
                summary = summary_match.group(1).strip()

            # Remove HTML comment blocks from appearance (legacy marker)
            appearance = re.sub(r"(?s)<!--.*?-->", "", appearance).strip()

            # Support '//' style notes: drop any lines starting with '//' (trim leading whitespace)
            if appearance:
                lines = [ln for ln in appearance.splitlines() if not re.match(r"^\s*//", ln)]
                appearance = "\n".join(lines).strip()

            outfits = {}

            # First, try to parse the newer structured outfit format using H4 headings
            outfit_parts = _OUTFIT_RE.split(body)
            if len(outfit_parts) > 1:
                for outfit_idx in range(1, len(outfit_parts), 2):
                    o_name = outfit_parts[outfit_idx].strip()
                    o_body = (
                        outfit_parts[outfit_idx + 1] if outfit_idx + 1 < len(outfit_parts) else ""
                    )

                    items = {}
                    lines = o_body.splitlines()
                    line_idx = 0
                    item_found = False
                    while line_idx < len(lines):
                        line = lines[line_idx]
                        m_marker = re.match(r"^\s*[-*]\s+(.*)$", line)
                        if m_marker:
                            content_item = m_marker.group(1)
                            item_found = True
                            key = None
                            val_start = ""
                            if content_item.startswith("**"):
                                rest = content_item[2:]
                                end_bold = rest.find("**")
                                if end_bold != -1:
                                    key = rest[:end_bold].strip()
                                    after = rest[end_bold + 2 :].lstrip()
                                    if after.startswith(":"):
                                        val_start = after[1:].lstrip()
                                    else:
                                        if val_start == "" and after:
                                            val_start = after
                                else:
                                    key_val_parts = content_item.split(":", 1)
                                    key = key_val_parts[0].strip()
                                    val_start = (
                                        key_val_parts[1].strip() if len(key_val_parts) > 1 else ""
                                    )
                            else:
                                key_val_parts = content_item.split(":", 1)
                                key = key_val_parts[0].strip()
                                val_start = (
                                    key_val_parts[1].strip() if len(key_val_parts) > 1 else ""
                                )

                            val_lines = [val_start.rstrip()] if val_start is not None else [""]
                            next_line_idx = line_idx + 1
                            while (
                                next_line_idx < len(lines)
                                and not re.match(r"^\s*[-*]\s+", lines[next_line_idx])
                                and not re.match(r"^####\s+", lines[next_line_idx])
                            ):
                                val_lines.append(lines[next_line_idx].rstrip())
                                next_line_idx += 1
                            val = "\n".join(
                                [entry for entry in val_lines if entry is not None]
                            ).strip()
                            if key:
                                key = key.strip()
                                if key.endswith(":"):
                                    key = key[:-1].strip()
                            if val.startswith("**"):
                                val = val.lstrip("*").lstrip()
                            items[key] = val
                            line_idx = next_line_idx
                            continue
                        else:
                            line_idx += 1

                    if item_found:
                        outfits[o_name] = items
                    else:
                        outfits[o_name] = o_body.strip()
            else:
                for m in re.finditer(r"-\s+\*\*([^:]+):\*\*\s*(.+)", body):
                    o_name = m.group(1).strip()
                    o_desc = m.group(2).strip()
                    outfits[o_name] = o_desc

            tags = []
            tags_match = _TAGS_RE.search(body)
            if tags_match:
                raw = tags_match.group(1).strip()
                tags = [t.strip() for t in re.split(r",|;", raw) if t.strip()]

            gender = "F"
            gender_explicit = False
            gender_match = _GENDER_RE.search(body)
            if gender_match:
                gender = gender_match.group(1).upper()
                gender_explicit = True

            modifier = None
            modifier_match = _MODIFIER_RE.search(body)
            if modifier_match:
                modifier = modifier_match.group(1).strip()
                gender_explicit = True

            signature_color = None
            sig_match = _SIGNATURE_COLOR_RE.search(body)
            if sig_match:
                signature_color = sig_match.group(1).strip()

            for o_name, o_val in list(outfits.items()):
                if isinstance(o_val, dict):
                    bottom_key = None
                    for k in o_val.keys():
                        if k.strip().lower() == "bottom":
                            bottom_key = k
                            break

                    bottom_val = None
                    if bottom_key is not None:
                        bottom_val = o_val.get(bottom_key)

                    is_one_piece = False
                    if bottom_key is None:
                        is_one_piece = True
                    else:
                        if bottom_val is None:
                            is_one_piece = True
                        else:
                            bottom_val_normalized = str(bottom_val).strip().lower()
                            if (
                                bottom_val_normalized == ""
                                or bottom_val_normalized.startswith(("n/a", "na", "none"))
                                or any(
                                    keyword in bottom_val_normalized
                                    for keyword in ["one-piece", "playsuit", "teddy", "dress"]
                                )
                            ):
                                is_one_piece = True

                    if is_one_piece:
                        if bottom_key is None:
                            o_val["Bottom"] = None
                        else:
                            o_val[bottom_key] = None
                            if bottom_key != "Bottom":
                                o_val["Bottom"] = None
                                del o_val[bottom_key]
                        o_val["one_piece"] = True

            characters[name] = {
                "appearance": appearance,
                "summary": summary,
                "tags": tags,
                "outfits": outfits,
                "photo": photo,
                "gender": gender,
                "gender_explicit": gender_explicit,
                "modifier": modifier,
                "signature_color": signature_color,
            }

        validated_chars = {}
        for name, data in characters.items():
            if not isinstance(data, dict):
                from utils import logger
                logger.warning(f"Invalid character data for {name}, skipping")
                continue

            if "appearance" not in data:
                from utils import logger
                logger.warning(f"Character {name} missing appearance, adding empty")
                data["appearance"] = ""

            if "outfits" not in data or not isinstance(data["outfits"], dict):
                from utils import logger
                logger.warning(f"Character {name} has invalid outfits, adding empty dict")
                data["outfits"] = {}

            if "photo" not in data:
                data["photo"] = None

            validated_chars[name] = data

        return validated_chars

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
