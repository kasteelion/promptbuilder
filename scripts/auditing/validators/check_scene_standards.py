import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SCENE_FILE = os.path.join(DATA_DIR, "scenes.md")

def run_audit():
    print(f"Auditing Scenes in {SCENE_FILE}...")
    
    if not os.path.exists(SCENE_FILE):
        print("scenes.md not found!")
        return

    with open(SCENE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by headers (### Scene Name)
    scenes = re.split(r'(^### .*$)', content, flags=re.MULTILINE)[1:] # Skip preamble
    
    total_scenes = 0
    passed = 0
    
    REPORT_FILE = os.path.join(PROJECT_ROOT, "auditing", "reports", "scene_standards_report.md")
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as report:
        report.write("# Scene Standards Audit Report\n\n")
        report.write(f"**Date:** {os.path.basename(SCENE_FILE)}\n\n")
        report.write("| Scene Name | Status | Issues |\n")
        report.write("|---|---|---|\n")

        print(f"{'Scene Name':<40} | {'Status':<5} | {'Issues'}")
        print("-" * 80)

        for i in range(0, len(scenes), 2):
            header = scenes[i].strip()
            body = scenes[i+1].strip() if i+1 < len(scenes) else ""
            total_scenes += 1
            
            issues = []
            
            # Check Header Tags
            if "(" not in header or ")" not in header:
                issues.append("Header tags missing parenthesis")
                
            # Check Body Sections
            if "**Visual Description:**" not in body:
                issues.append("Missing 'Visual Description'")
                
            if "**Sensory/Atmospheric Details:**" not in body:
                issues.append("Missing 'Sensory/Atmospheric Details'")
            else:
                # Check subsections
                if "- **Lighting:**" not in body: issues.append("Missing 'Lighting'")
                if "- **Atmosphere:**" not in body: issues.append("Missing 'Atmosphere'")
                
            status = "PASS" if not issues else "FAIL"
            if status == "PASS": passed += 1
            
            name = header[3:].split('(')[0].strip()[:35]
            issue_str = ", ".join(issues) if issues else "None"
            
            # Console output for failures only usually, but let's show all or just summary? 
            # Original showed all failures.
            if status == "FAIL":
                print(f"{name:<40} | {status:<5} | {issue_str}")
                
            # Report output - All rows
            report.write(f"| {name} | {status} | {issue_str} |\n")

        print("-" * 80)
        print(f"Total Scenes: {total_scenes}")
        print(f"Passed: {passed}")
        print(f"Failed: {total_scenes - passed}")
        
        report.write(f"\n\n**Summary:** {passed}/{total_scenes} Passed ({passed/total_scenes*100:.1f}%)\n")
    
    print(f"Report saved to: {REPORT_FILE}")

if __name__ == "__main__":
    run_audit()
