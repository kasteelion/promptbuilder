import os
import datetime

def consolidate():
    report_dir = "auditing/reports"
    output_file = os.path.join(report_dir, "comprehensive_audit.md")
    
    # Order of reports in the consolidated file
    # (Section Title, Filename)
    report_order = [
        ("Distribution Visualizations", "prompt_distribution_flow.md"),
        ("Style Distribution Census", "style_census.md"),
        ("Vibe Cohesion Analysis", "vibe_cohesion_report.md"),
        ("Prompt Scoring Analysis (Best & Worst)", "best_worst_prompts.md"),
        ("Quality & Integrity Audit", "quality_audit.md"),
        ("Asset Descriptiveness", "descriptiveness_audit.md"),
        ("Tag System Inventory", "tag_inventory.md"),
        ("Tag Flow", "tag_distribution_flow.md")
    ]
    
    # Force Unix newlines for maximum compatibility with Mermaid parsers
    with open(output_file, 'w', encoding='utf-8', newline='\n') as outfile:
        # Title and Date
        outfile.write(f"# PromptBuilder Comprehensive Audit Report\n")
        outfile.write(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        outfile.write("This document combines all individual audit modules into a single overview of system health, content quality, and generation logic performance.\n\n")
        outfile.write("---\n\n")
        
        with open("auditing/reports/consolidation_debug.log", "w", encoding="utf-8", newline='\n') as debug_log:
            for title, filename in report_order:
                filepath = os.path.join(report_dir, filename)
                
                if os.path.exists(filepath):
                    outfile.write(f"<div style='page-break-before: always;'></div>\n\n")
                    outfile.write(f"# 📑 {title}\n\n")
                    debug_log.write(f"--- Consolidating {filename} ---\n")
                    
                    try:
                        # Use newline='' to preserve original newlines from the report files as much as possible
                        with open(filepath, 'r', encoding='utf-8', newline='') as infile:
                            in_code_block = False
                            for line in infile:
                                # Standardize to Unix \n for the output
                                clean_line = line.rstrip('\r\n')
                                stripped = clean_line.strip()
                                
                                if stripped.startswith('```'):
                                    in_code_block = not in_code_block
                                
                                if not in_code_block and stripped.startswith('#'):
                                    final_line = '#' + clean_line
                                else:
                                    final_line = clean_line
                                
                                outfile.write(final_line + '\n')
                                debug_log.write(f"WRITE: [{final_line}]\n")
                                
                    except Exception as e:
                        outfile.write(f"\n> *Error reading report file: {e}*\n")
                        debug_log.write(f"ERROR: {e}\n")
                    
                    outfile.write("\n\n---\n\n")
                else:
                    debug_log.write(f"SKIP: {filename} (Not found)\n")

    print(f"✅ Comprehensive report generated: {output_file}")

if __name__ == "__main__":
    consolidate()
