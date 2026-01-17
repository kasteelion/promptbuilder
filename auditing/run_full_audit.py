import subprocess
import argparse
import sys
import os
from pathlib import Path

def run_command(command, description):
    print(f"\n[{description}]")
    print(f"> {command}")
    try:
        # Run command from project root
        project_root = Path(__file__).parent.parent
        # Using sys.executable ensures we use the same python interpreter
        if command.startswith("python "):
            full_command = f'"{sys.executable}" {command[7:]}'
        else:
            full_command = command

        result = subprocess.run(
            full_command, 
            shell=True, 
            cwd=str(project_root),
        )
        if result.returncode != 0:
            print(f"Error running {description}. Exit code: {result.returncode}")
            return False
        return True
    except Exception as e:
        print(f"Failed to execute {description}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run full PromptBuilder audit suite.")
    parser.add_argument("--count", type=int, default=50, help="Number of prompts to generate for distribution audit")
    parser.add_argument("--skip-gen", action="store_true", help="Skip prompt generation (analyzes existing files)")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    print(f"Starting Consolidated Audit Suite... (Root: {project_root})")

    # 1. Static Integrity (Asset Standards & Quality)
    if not run_command("python auditing/analysis/static_integrity.py", "Step 1: Static Integrity & Standards"):
        pass

    # 2. Hub & Spoke Connectivity
    if not run_command("python auditing/analysis/hub_analysis.py", "Step 2: Hub & Spoke Connectivity"):
        pass

    # 3. Prompt Generation (Optional)
    if not args.skip_gen:
        # Clear old prompts first
        prompts_dir = project_root / "output" / "prompts"
        if prompts_dir.exists():
            print(f"\n[Cleaning Output Directory] {prompts_dir}")
            try:
                for f in prompts_dir.glob("*.txt"):
                    f.unlink()
            except Exception as e:
                print(f"Warning: Could not clear some prompt files: {e}")
        
        cmd = f"python automation/automate_generation.py --prompts-only --count {args.count}"
        if not run_command(cmd, f"Step 3: Generate {args.count} Test Prompts"):
            return
    else:
        print("\n[Step 3] Skipping Prompt Generation (using existing files)...")

    # 4. Analysis & Visualizations
    if not run_command("python auditing/visualizations/generate_sankey_diagram.py", "Step 4.1: Prompt Distribution (Sankey)"):
        pass

    if not run_command("python auditing/analysis/vibe_cohesion_report.py", "Step 4.2: Vibe Cohesion"):
        pass

    if not run_command("python auditing/visualizations/generate_tag_sankey.py", "Step 4.3: Tag Distribution Flow"):
        pass
    
    if not run_command("python auditing/analysis/find_best_worst.py", "Step 4.4: Best & Worst Scorers"):
        pass

    # 5. Master Consolidation
    if not run_command("python auditing/consolidate_reports.py", "Step 5: Generate System Health Dashboard"):
        return
    
    print("\n" + "="*50)
    print("CONSOLIDATED AUDIT COMPLETE")
    print("="*50)
    print(f"📄 MASTER REPORT: auditing/reports/comprehensive_audit.md")
    print("-" * 50)
    print(f"1. Static Integrity:    auditing/reports/static_integrity.md")
    print(f"2. Hub Connectivity:   auditing/reports/hub_connectivity.md")
    print(f"3. Scoring Analysis:   auditing/reports/best_worst_prompts.md")
    print(f"4. Distribution Flow:   auditing/reports/prompt_distribution_flow.md")
    print("="*50)

if __name__ == "__main__":
    main()
