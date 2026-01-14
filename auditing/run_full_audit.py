import subprocess
import argparse
import sys
import os

def run_command(command, description):
    print(f"\n[{description}]")
    print(f"> {command}")
    try:
        # Run command from project root
        # Using sys.executable ensures we use the same python interpreter
        full_command = f'"{sys.executable}" {command}' if command.startswith("auditing") or command.startswith("automation") else command
        
        # Actually, command is "python ...", so replacing "python" with sys.executable is safer
        if command.startswith("python "):
            full_command = f'"{sys.executable}" {command[7:]}'
        else:
            full_command = command

        result = subprocess.run(
            full_command, 
            shell=True, 
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), # Project root
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

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Starting Full Audit... (Root: {project_root})")

    # 1. Tag Inventory
    if not run_command(f"python auditing/analysis/tag_inventory.py", "Step 1: Tag Inventory Audit"):
        return

    # 2. Standards Validation (New Consolidated Steps)
    print("\n[Step 2] Validating Asset Standards...")
    
    if not run_command(f"python auditing/validators/check_character_standards.py", "Step 2.1: Character Standards"):
        pass # Don't error out entire suite, just report
        
    if not run_command(f"python auditing/validators/check_scene_standards.py", "Step 2.2: Scene Standards"):
        pass

    if not run_command(f"python auditing/validators/check_pose_standards.py", "Step 2.3: Pose Standards"):
        pass

    if not run_command(f"python auditing/validators/check_interaction_standards.py", "Step 2.4: Interaction Standards"):
        pass

    # 3. Quality & Integrity Audit (Included Descriptiveness)
    if not run_command(f"python auditing/analysis/quality_audit.py", "Step 3: Quality & Descriptiveness Audit"):
        return

    # 3.5 Outfit Precision Audit
    if not run_command(f"python auditing/analysis/audit_outfit_quality.py", "Step 3.5: Outfit Precision ('Scientific') Audit"):
        return

    # 4. Prompt Generation (Optional)
    if not args.skip_gen:
        # Clear old prompts first
        prompts_dir = os.path.join(project_root, "output", "prompts")
        if os.path.exists(prompts_dir):
            print(f"\n[Cleaning Output Directory] {prompts_dir}")
            try:
                for f in os.listdir(prompts_dir):
                    if f.endswith(".txt"):
                        os.remove(os.path.join(prompts_dir, f))
            except Exception as e:
                print(f"Warning: Could not clear some prompt files: {e}")
        
        cmd = f"python automation/automate_generation.py --prompts-only --count {args.count}"
        if not run_command(cmd, f"Step 4: Generate {args.count} Test Prompts"):
            return
    else:
        print("\n[Step 4] Skipping Prompt Generation (using existing files)...")

    # 5. Sankey Diagram
    if not run_command(f"python auditing/visualizations/generate_sankey_diagram.py", "Step 5: Generate Distribution Visualization (Sankey)"):
        return

    # 5.5 Vibe Cohesion Report
    if not run_command(f"python auditing/analysis/vibe_cohesion_report.py", "Step 5.5: Analyze Vibe Cohesion"):
        return

    # 5.6 Tag Distribution Flow
    if not run_command(f"python auditing/visualizations/generate_tag_sankey.py", "Step 5.6: Generate Tag Distribution Flow"):
        return
    
    # 6. Best/Worst Analysis
    if not run_command(f"python auditing/analysis/find_best_worst.py", "Step 6: Analyze Best & Worst Prompts"):
        return

    # 7. Consolidate Reports
    if not run_command(f"python auditing/consolidate_reports.py", "Step 7: Generate Comprehensive Report"):
        return
    
    print("\n" + "="*50)
    print("AUDIT COMPLETE")
    print("="*50)
    print(f"📄 COMPREHENSIVE REPORT: auditing/reports/comprehensive_audit.md")
    print("-" * 50)
    print(f"1. Tag Inventory:       auditing/reports/tag_inventory.md")
    # print(f"2. Connectivity Report: auditing/reports/connectivity_report.txt")
    print(f"3. Quality Audit:       auditing/reports/quality_audit.md")
    print(f"4. Descriptiveness:     auditing/reports/descriptiveness_audit.md")
    print(f"5. Distribution Flow:   auditing/reports/prompt_distribution_flow.md")
    print(f"6. Tag Flow:            auditing/reports/tag_distribution_flow.md")
    print(f"7. Best/Worst Prompts:  auditing/reports/best_worst_prompts.md")
    print("="*50)

if __name__ == "__main__":
    main()
