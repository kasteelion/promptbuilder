import os
import glob
import statistics

def find_best_worst():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    prompts_dir = os.path.join(project_root, "output", "prompts")
    
    if not os.path.exists(prompts_dir):
        print("No prompts found.")
        return

    scored_prompts = []
    
    files = glob.glob(os.path.join(prompts_dir, "*.txt"))
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
                
            score = 0
            # Look for Score: X line
            for line in content.splitlines():
                if line.strip().startswith("Score:"):
                    try:
                        score = int(line.split(":")[1].strip())
                        break
                    except ValueError:
                        pass
            
            scored_prompts.append((score, fpath, content))
        except Exception as e:
            print(f"Error reading {fpath}: {e}")

    if not scored_prompts:
        print("No scored prompts found.")
        return

    # Calculate Statistics
    all_scores = [s for s, _, _ in scored_prompts]
    mean_score = statistics.mean(all_scores)
    median_score = statistics.median(all_scores)
    try:
        mode_score = statistics.mode(all_scores)
    except statistics.StatisticsError:
        mode_score = "N/A (Multi-modal)"
    
    stdev_score = 0
    if len(all_scores) > 1:
        stdev_score = statistics.stdev(all_scores)

    # Sort by score (descending for best, ascending for worst)
    scored_prompts.sort(key=lambda x: x[0], reverse=True)
    
    best_3 = scored_prompts[:3]
    worst_3 = scored_prompts[-3:]
    # worst_3 is actually sorted high-to-low, so the last 3 are the lowest. 
    # But for "Worst 3", we usually want the absolute lowest first.
    worst_3 = sorted(worst_3, key=lambda x: x[0]) # Sort ascending

    report_path = os.path.join(project_root, "auditing", "reports", "best_worst_prompts.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Best and Worst Generated Prompts\n\n")
        
        f.write("## 📊 Statistical Summary\n\n")
        f.write(f"- **Total Prompts Analyzed:** {len(scored_prompts)}\n")
        f.write(f"- **Mean Score:** {mean_score:.2f}\n")
        f.write(f"- **Median Score:** {median_score}\n")
        f.write(f"- **Mode Score:** {mode_score}\n")
        f.write(f"- **Standard Deviation:** {stdev_score:.2f}\n")
        f.write(f"- **Score Range:** {min(all_scores)} - {max(all_scores)}\n\n")

        f.write("## 🏆 Top 3 Best Prompts\n\n")
        for i, (score, path, content) in enumerate(best_3):
            fname = os.path.basename(path)
            f.write(f"### {i+1}. {fname} (Score: {score})\n")
            f.write("```text\n")
            # Extract prompt text (usually first line or after "Generate an image of:")
            prompt_text = content.split("# METADATA")[0].strip()
            f.write(prompt_text)
            f.write("\n```\n\n")
            
        f.write("\n## 📉 Bottom 3 Worst Prompts\n\n")
        for i, (score, path, content) in enumerate(worst_3):
            fname = os.path.basename(path)
            f.write(f"### {i+1}. {fname} (Score: {score})\n")
            f.write("```text\n")
            prompt_text = content.split("# METADATA")[0].strip()
            f.write(prompt_text)
            f.write("\n```\n\n")

    print(f"Report saved to {report_path}")
    
    # Also print to console
    print("\n--- Best 3 ---")
    for s, p, _ in best_3:
        print(f"{os.path.basename(p)}: {s}")
        
    print("\n--- Worst 3 ---")
    for s, p, _ in worst_3:
        print(f"{os.path.basename(p)}: {s}")

if __name__ == "__main__":
    find_best_worst()
