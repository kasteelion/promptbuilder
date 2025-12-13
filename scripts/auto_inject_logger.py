"""Auto-inject logger.exception into bare `except Exception` blocks.

This script scans Python files under the repo and for each `except Exception` or
`except Exception as e:` clause that does not call `logger.` already, it will
insert `from utils import logger` and `logger.exception(...)` as the first
statements of the except block. It tries to preserve indentation.

Run: python scripts/auto_inject_logger.py
"""

import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PY_EXT = ".py"

SKIP_DIRS = {"__pycache__", ".git", "venv", "env", ".venv"}

pattern = re.compile(r"^\s*except\s+Exception(?:\s+as\s+\w+)?\s*:\s*$")


def process_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    changed = False
    i = 0
    out_lines = []
    L = len(lines)
    while i < L:
        line = lines[i]
        out_lines.append(line)
        if pattern.match(line):
            # compute base indentation for the block
            m = re.match(r"^(\s*)", line)
            base_indent = m.group(1) if m else ""
            block_indent = base_indent + " " * 4
            # Peek ahead to find first non-blank/comment line in the block
            j = i + 1
            found_logger = False
            while j < L:
                nl = lines[j]
                # If indentation less-or-equal than base, block ended
                if nl.strip() and not nl.startswith(block_indent):
                    # block ended without statements (e.g., next except or dedent)
                    break
                if "logger." in nl or "from utils import logger" in nl or "import logger" in nl:
                    found_logger = True
                    break
                # If we encounter a "raise" or other statement, still inject
                if nl.strip():
                    break
                j += 1
            if not found_logger:
                # Insert logger import and exception call after the except line
                insert_lines = []
                insert_lines.append(block_indent + "from utils import logger\n")
                insert_lines.append(block_indent + "logger.exception('Auto-captured exception')\n")
                out_lines.extend(insert_lines)
                changed = True
        i += 1

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(out_lines)
    return changed


def walk_and_process(root):
    changed_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # modify dirnames in-place to skip
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(PY_EXT):
                continue
            path = os.path.join(dirpath, fn)
            # skip this script itself
            if os.path.abspath(path) == os.path.abspath(__file__):
                continue
            try:
                if process_file(path):
                    changed_files.append(path)
            except Exception as e:
                print(f"Failed to process {path}: {e}")
    return changed_files


if __name__ == "__main__":
    changed = walk_and_process(ROOT)
    print(f"Modified {len(changed)} files:")
    for p in changed:
        print(" -", os.path.relpath(p, ROOT))
