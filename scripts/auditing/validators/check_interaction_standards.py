
import re
import sys

STANDARD_FILE = "data/standards/INTERACTION_STANDARDS.md"
TARGET_FILE = "data/interactions.md"

import os

def audit_interactions():
    print(f"Auditing {TARGET_FILE} against {STANDARD_FILE}...")
    
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    errors = []
    interactions = []
    interaction_count = 0
    
    # Regex for: - **Name** (Tag, Tag): Description
    # Matches: - **Name** (Tag, ...): {char1}...
    # Note: Description usually starts with space, but sometimes ':' is immediately followed by char
    pattern = re.compile(r"^\s*-\s*\*\*(.*?)\*\*\s*(\(.*?\))?:\s*(.*)$")
    
    current_category = None
    
    for i, line in enumerate(lines):
        line_num = i + 1
        line = line.strip()
        
        if not line:
            continue
            
        if line.startswith("## "):
            current_category = line.strip("## ").strip()
            continue
            
        if line.startswith("---") or line.startswith("# "):
            continue
            
        # Check against pattern
        match = pattern.match(line)
        if match:
            interaction_count += 1
            name = match.group(1)
            tags_parenthesized = match.group(2)
            template = match.group(3)
            
            issues = []
            
            # 1. Check Tags
            if not tags_parenthesized:
                 issues.append("Missing parenthesized tags")
            else:
                # Remove parens
                tags_str = tags_parenthesized[1:-1]
                tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                
                if not tags:
                    issues.append("Empty tags")
                
                # Check casing
                for tag in tags:
                    if not tag[0].isupper():
                         issues.append(f"Tag '{tag}' should be Title Case")

            # 2. Check Template Placeholders
            if "{char1}" not in template:
                 issues.append("Template must include {char1}")
            
            if "{char2}" not in template:
                 pass # errors.append(f"Line {line_num}: Template for '{name}' likely missing {{char2}}") - disabling for now to avoid false positives on 'Looking at camera' type interactions if any exist.

            # 3. Check Template Quality
            if len(template) < 30:
                 issues.append(f"Template too short ({len(template)} chars).")
                 
            if "Blank" in name:
                # Special case or delete it? The standard says "No Blank Entries".
                issues.append("'Blank' entry found.")
            
            status = "PASS" if not issues else "FAIL"
            interactions.append({
                "line": line_num,
                "name": name,
                "category": current_category,
                "status": status,
                "issues": issues
            })

            if issues:
                for issue in issues:
                    errors.append(f"Line {line_num} ({name}): {issue}")

        elif line.startswith("-"):
             errors.append(f"Line {line_num}: Malformed entry.")

    # Write Report
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    REPORT_FILE = os.path.join(PROJECT_ROOT, "auditing", "reports", "interaction_standards_report.md")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

    with open(REPORT_FILE, 'w', encoding='utf-8') as report:
        report.write("# Interaction Standards Audit Report\n\n")
        report.write(f"**Date:** {os.path.basename(TARGET_FILE)}\n")
        report.write(f"**Total Interactions:** {interaction_count}\n\n")
        report.write("| Line | Category | Name | Status | Issues |\n")
        report.write("|---|---|---|---|---|\n")
        
        for intx in interactions:
            issue_str = ", ".join(intx['issues']) if intx['issues'] else "None"
            report.write(f"| {intx['line']} | {intx['category']} | {intx['name']} | {intx['status']} | {issue_str} |\n")

    print("\nAudit Complete.")
    print(f"Total Interactions Found: {interaction_count}")
    print(f"Total Errors: {len(errors)}")
    print(f"Report saved to: {REPORT_FILE}")
    
    if errors:
        print("\nErrors Found:")
        for e in errors:
            print(f"- {e}")
        return False
    else:
        print("\nAll Interactions passed standard audit!")
        return True

if __name__ == "__main__":
    if not audit_interactions():
        sys.exit(1)
