"""
Script to validate color_schemes.md for correct format and completeness.
"""
import re

SCHEME_HEADER = re.compile(r"^## (.+)")
PRIMARY = re.compile(r"^- \*\*primary:\*\* (.+)")
SECONDARY = re.compile(r"^- \*\*secondary:\*\* (.+)")
ACCENT = re.compile(r"^- \*\*accent:\*\* (.+)")
TEAM = re.compile(r"^- \*\*team:\*\* (.+)")


def validate_color_schemes(filepath):
    errors = []
    with open(filepath, encoding="utf-8") as f:
        lines = [line.rstrip() for line in f]
    i = 0
    while i < len(lines):
        line = lines[i]
        if SCHEME_HEADER.match(line):
            scheme = SCHEME_HEADER.match(line).group(1)
            found = {"primary": False, "secondary": False, "accent": False, "team": False}
            for j in range(1, 6):
                if i + j >= len(lines):
                    break
                l2 = lines[i + j]
                if PRIMARY.match(l2):
                    found["primary"] = True
                elif SECONDARY.match(l2):
                    found["secondary"] = True
                elif ACCENT.match(l2):
                    found["accent"] = True
                elif TEAM.match(l2):
                    found["team"] = True
                elif SCHEME_HEADER.match(l2):
                    break
            for k, v in found.items():
                if not v:
                    errors.append(f"Scheme '{scheme}' missing {k}")
        i += 1
    if errors:
        print("Validation errors found:")
        for e in errors:
            print("-", e)
    else:
        print("All color schemes are valid.")

if __name__ == "__main__":
    validate_color_schemes("data/color_schemes.md")
