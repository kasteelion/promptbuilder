
import re
import sys

STANDARD_FILE = "data/standards/POSE_STANDARDS.md"
TARGET_FILE = "data/poses.md"

import os

def audit_poses():
    print(f"Auditing {TARGET_FILE} against {STANDARD_FILE}...")
    
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    errors = []
    poses = []
    pose_count = 0
    
    # Regex for: - **Name** (Tag, Tag): Description
    # We are lenient on spaces/tabs
    pose_pattern = re.compile(r"^\s*-\s*\*\*(.*?)\*\*\s*\((.*?)\):\s*(.*)$")
    
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
            
        # Check against pose pattern
        match = pose_pattern.match(line)
        if match:
            pose_count += 1
            name = match.group(1)
            tags_str = match.group(2)
            desc = match.group(3)
            
            pose_issues = []
            
            # 1. Check Tags
            tags = [t.strip() for t in tags_str.split(',') if t.strip()]
            if not tags:
                pose_issues.append("No tags found")
            
            # Check casing
            for tag in tags:
                if not tag[0].isupper():
                     pose_issues.append(f"Tag '{tag}' should be Title Case")
                     
            # 2. Check Description Quality
            if len(desc) < 20:
                 pose_issues.append(f"Desc too short ({len(desc)} chars).")
                 
            if "Basic" in tags and len(desc) < 40:
                 pose_issues.append("Basic Pose desc weak.")
            
            status = "PASS" if not pose_issues else "FAIL"
            poses.append({
                "line": line_num,
                "name": name,
                "category": current_category,
                "status": status,
                "issues": pose_issues
            })
            
            if pose_issues:
                for issue in pose_issues:
                    errors.append(f"Line {line_num} ({name}): {issue}")

        elif line.startswith("-"):
             errors.append(f"Line {line_num}: Malformed entry.")

    # Write Report
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    REPORT_FILE = os.path.join(PROJECT_ROOT, "auditing", "reports", "pose_standards_report.md")
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as report:
        report.write("# Pose Standards Audit Report\n\n")
        report.write(f"**Date:** {os.path.basename(TARGET_FILE)}\n")
        report.write(f"**Total Poses:** {pose_count}\n\n")
        report.write("| Line | Category | Pose Name | Status | Issues |\n")
        report.write("|---|---|---|---|---|\n")
        
        for p in poses:
            issue_str = ", ".join(p['issues']) if p['issues'] else "None"
            report.write(f"| {p['line']} | {p['category']} | {p['name']} | {p['status']} | {issue_str} |\n")
    
    print("\nAudit Complete.")
    print(f"Total Poses Found: {pose_count}")
    print(f"Total Errors: {len(errors)}")
    print(f"Report saved to: {REPORT_FILE}")
    
    if errors:
        print("\nErrors Found:")
        for e in errors:
            print(f"- {e}")
        return False
    else:
        print("\nAll Poses passed standard audit!")
        return True

if __name__ == "__main__":
    if not audit_poses():
        sys.exit(1)
