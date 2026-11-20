import datetime
import re
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORT_DIR = PROJECT_ROOT / "auditing" / "reports"

def get_report_content(filename):
    path = REPORT_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None

def safe_float(v):
    try:
        return float(str(v).strip('%'))
    except (ValueError, TypeError):
        return 0.0

def safe_int(v):
    try:
        return int(str(v).replace(',', ''))
    except (ValueError, TypeError):
        return 0

def extract_dashboard_metrics():
    """Extract metrics from static_integrity and hub_connectivity for the master dashboard."""
    metrics = {
        "Total Assets": "N/A",
        "Failure Rate": "N/A",
        "Integrity Errors": "0",
        "Media Errors": "0",
        "Established Hubs": "0",
        "Weak Hubs": "0",
        "Characters with 0 Hubs": "0"
    }
    
    # 1. Static Integrity
    static_content = get_report_content("static_integrity.md")
    if static_content:
        m = re.search(r"- \*\*Total Assets Audited\*\*: (\d+)", static_content)
        if m: metrics["Total Assets"] = m.group(1)
        m = re.search(r"- \*\*Failure Rate\*\*: ([\d\.]+%?)", static_content)
        if m: metrics["Failure Rate"] = m.group(1)
        m = re.search(r"- \*\*Integrity Errors\*\*: (\d+)", static_content)
        if m: metrics["Integrity Errors"] = m.group(1)
        m = re.search(r"- \*\*Media Errors\*\*: (\d+)", static_content)
        if m: metrics["Media Errors"] = m.group(1)
        
    # 2. Hub Connectivity
    hub_content = get_report_content("hub_connectivity.md")
    if hub_content:
        # Count rows in Established Hubs table
        est_hubs = re.findall(r"\| \*\*([^*]+)\*\* \|", hub_content)
        metrics["Established Hubs"] = str(len(est_hubs))
        # Count rows in Weak Hubs table
        weak_hubs = re.findall(r"\| ([^|]+) \| ([^|]*Style|Scene|Outfit|Interaction[^|]*) \|", hub_content)
        metrics["Weak Hubs"] = str(len(weak_hubs))
        # Count characters with 0 Hubs
        zero_reach = re.findall(r"\| [^|]+ \| 0 \| ❌ NONE \|", hub_content)
        metrics["Characters with 0 Hubs"] = str(len(zero_reach))
        
    return metrics

def consolidate():
    output_file = REPORT_DIR / "comprehensive_audit.md"
    
    # Order of reports in the consolidated file
    report_order = [
        ("Static Integrity Audit", "static_integrity.md"),
        ("Content Quality & Enrichment", "content_quality.md"),
        ("Color Palette Diversity", "color_diversity.md"),
        ("Semantic Redundancy Analysis", "redundancy_report.md"),
        ("Hub & Spoke Connectivity", "hub_connectivity.md"),
        ("Character-Hub Accessibility Matrix", "character_hub_matrix.md"),
        ("Vibe Cohesion Analysis", "vibe_cohesion_report.md"),
        ("Prompt Scoring Analysis (Best & Worst)", "best_worst_prompts.md"),
        ("Distribution Visualizations", "prompt_distribution_flow.md"),
        ("Tag Flow", "tag_distribution_flow.md")
    ]
    
    metrics = extract_dashboard_metrics()
    
    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write("# 🕵️ PromptBuilder Comprehensive Audit\n")
        f.write(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 🛂 System Health Dashboard\n")
        f.write("| Metric | Value | Status |\n")
        f.write("|---|---|---|\n")
        
        # Color coding status
        fail_val = metrics["Failure Rate"]
        f_val = safe_float(fail_val)
        fail_status = "🔴 ACTION REQUIRED" if f_val > 10 else "🟡 CAUTION" if f_val > 5 else "🟢 HEALTHY"
        
        f.write(f"| **Content Quality** | {metrics['Failure Rate']} Failure Rate | {fail_status} |\n")
        
        err_count = safe_int(metrics['Integrity Errors']) + safe_int(metrics['Media Errors'])
        f.write(f"| **Data Integrity** | {metrics['Integrity Errors']} Logic / {metrics['Media Errors']} Media | {'🔴 ERROR' if err_count > 0 else '🟢 OK'} |\n")
        
        strong_hubs = safe_int(metrics['Established Hubs'])
        f.write(f"| **Thematic Reach** | {metrics['Established Hubs']} Strong Hubs / {metrics['Weak Hubs']} Potential | {'🟢 GOOD' if strong_hubs > 10 else '🟡 LOW DIVERSITY'} |\n")
        
        isolated = safe_int(metrics['Characters with 0 Hubs'])
        f.write(f"| **Char Accessibility** | {metrics['Characters with 0 Hubs']} Isolated Characters | {'🔴 RE-TAG NEEDED' if isolated > 0 else '🟢 OK'} |\n")
        
        f.write("\n---\n\n")
        
        for title, filename in report_order:
            content = get_report_content(filename)
            if content:
                # Remove top-level header from source file to avoid redundancy
                content = re.sub(r"^# .*?\n", "", content, flags=re.MULTILINE)
                
                f.write(f"## 📑 {title}\n\n")
                f.write(content)
                f.write("\n\n---\n\n")

    print(f"✅ Comprehensive report generated: {output_file}")

if __name__ == "__main__":
    consolidate()
