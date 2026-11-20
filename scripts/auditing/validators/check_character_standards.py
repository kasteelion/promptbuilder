import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CHAR_DIR = os.path.join(DATA_DIR, "characters")
STANDARD_FILE = os.path.join(DATA_DIR, "standards", "CHARACTER_STANDARDS.md")

def check_structure(content):
    score = 0
    issues = []
    
    # 1. Header (Photo/Summary/Tags)
    if "**Photo:**" not in content and " Photo:" not in content:
        issues.append("Missing 'Photo' field")
    else: score += 10
        
    if "**Summary:**" not in content:
        issues.append("Missing 'Summary' field")
    else: score += 10
        
    if "**Tags:**" not in content and " Tags:" not in content:
        issues.append("Missing 'Tags' field")
    else: score += 10
        
    # 2. Appearance Section
    if "**Appearance:**" not in content:
        issues.append("Missing 'Appearance' section")
    else:
        score += 10
        # Check for 4 bullets
        if re.search(r'\*\s+\*\*Body:\*\*', content): score += 5
        else: issues.append("Missing 'Body' bullet")
            
        if re.search(r'\*\s+\*\*Face:\*\*', content): score += 5
        else: issues.append("Missing 'Face' bullet")
            
        if re.search(r'\*\s+\*\*Hair( / Covering)?:\*\*', content): score += 5
        else: issues.append("Missing 'Hair' bullet")
            
        if re.search(r'\*\s+\*\*Skin:\*\*', content): score += 5
        else: issues.append("Missing 'Skin' bullet")

    # 3. Vibe Section
    if "**Vibe / Energy:**" not in content:
        issues.append("Missing 'Vibe / Energy' field")
    else: score += 10
        
    if "**Age Presentation:**" not in content:
        issues.append("Missing 'Age Presentation' field")
    else: score += 10

    # 4. Outfits
    if "**Outfits:**" not in content:
        issues.append("Missing 'Outfits' section")
    else: score += 10
        
    if "#### Base" not in content:
        issues.append("Missing '#### Base' outfit")
    else: score += 10

    return score, issues

def run_audit():
    print(f"Auditing Characters in {CHAR_DIR}...")
    
    results = []
    
    for fname in os.listdir(CHAR_DIR):
        if fname.endswith(".md"):
            path = os.path.join(CHAR_DIR, fname)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            score, issues = check_structure(content)
            if "sasha" in fname:
                 print(f"DEBUG: {fname} Appearance snippet repr:\n{repr(content[content.find('Appearance'):content.find('Appearance')+100])}")
            status = "PASS" if score == 100 else "FAIL"
            results.append((fname, status, score, issues))

    REPORT_FILE = os.path.join(PROJECT_ROOT, "auditing", "reports", "character_standards_report.md")
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as report:
        report.write("# Character Standards Audit Report\n\n")
        report.write(f"**Date:** {os.path.basename(CHAR_DIR)}\n\n")
        report.write("| Filename | Status | Score | Issues |\n")
        report.write("|---|---|---|---|\n")

        print("\nAudit Results:")
        print(f"{'Filename':<30} | {'Status':<5} | {'Score':<5} | {'Issues'}")
        print("-" * 80)
        
        failures = []
        for fname, status, score, issues in results:
            issue_str = ", ".join(issues) if issues else "None"
            
            # Write to report
            report.write(f"| {fname} | {status} | {score} | {issue_str} |\n")
            
            # Print failures to console
            if score < 100:
                print(f"{fname:<30} | {status:<5} | {score:<5} | {issue_str}")
                failures.append(fname)
        
        print("-" * 80)
        print(f"\nTOTAL FAILURES: {len(failures)}")
        if failures:
            print("Failing files:", failures)
            
        report.write(f"\n\n**Summary:** {len(results) - len(failures)}/{len(results)} Passed ({(len(results) - len(failures))/len(results)*100:.1f}%)\n")
        
    print(f"Report saved to: {REPORT_FILE}")

if __name__ == "__main__":
    run_audit()
