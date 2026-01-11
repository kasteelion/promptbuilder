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
    if not run_command(f"python auditing/tag_inventory.py", "Step 1: Tag Inventory Audit"):
        return

    # 2. Connectivity Check
    if not run_command(f"python auditing/check_character_connectivity.py", "Step 2: Character-Scene Connectivity Check"):
        return

    # 3. Prompt Generation (Optional)
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
        if not run_command(cmd, f"Step 3: Generate {args.count} Test Prompts"):
            return
    else:
        print("\n[Step 3] Skipping Prompt Generation (using existing files)...")

    # 4. Sankey Diagram
    if not run_command(f"python auditing/generate_sankey_diagram.py", "Step 4: Generate Distribution Visualization (Sankey)"):
        return
    
    print("\n" + "="*50)
    print("AUDIT COMPLETE")
    print("="*50)
    print(f"1. Tag Inventory:       output/reports/tag_inventory.md")
    print(f"2. Connectivity Report: output/reports/connectivity_report.txt")
    print(f"3. Distribution Flow:   output/reports/prompt_distribution_flow.md")
    print("="*50)

if __name__ == "__main__":
    main()
