import os
import sys
import json
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "src"))

from logic.data_loader import DataLoader

def word_count(text):
    if not text:
        return 0
    return len(text.split())

def assess_characters(loader):
    print("Assessing Characters...")
    chars = loader.load_characters()
    results = []
    
    for name, data in chars.items():
        # DATA TYPE CHECK
        if not isinstance(data, dict):
            results.append({
                "name": name,
                "type": "Character",
                "score": 0,
                "details": "Invalid Data",
                "issues": [f"Data is not a dict: {type(data)}"]
            })
            continue

        score = 0
        issues = []
        
        # Richness (Description Length)
        # Check appearance fields
        appearance = data.get("appearance", {})
        if isinstance(appearance, str):
             # Handle case where appearance is just a string
             body = appearance
             face = ""
             hair = ""
             skin = ""
        elif isinstance(appearance, dict):
             body = appearance.get("body", "")
             face = appearance.get("face", "")
             hair = appearance.get("hair", "")
             skin = appearance.get("skin", "")
        else:
             body = ""
             face = ""
             hair = ""
             skin = ""
        
        total_words = word_count(body) + word_count(face) + word_count(hair) + word_count(skin)
        
        if total_words < 20:
            issues.append("Very short description (< 20 words)")
            score -= 10
        elif total_words > 100:
            score += 10
            
        # Completeness (Metadata)
        if not data.get("age"):
            issues.append("Missing Age")
            score -= 5
        if not data.get("vibe"):
            issues.append("Missing Vibe")
            score -= 5
        if not data.get("nationality"):
             # Optional but good
             pass
             
        # Outfits
        outfits = data.get("outfits", {})
        if not outfits:
            issues.append("No Outfits")
            score -= 20
        else:
            score += len(outfits) * 2
            
        results.append({
            "name": name,
            "type": "Character",
            "score": 50 + score, # Base 50
            "details": f"{total_words} words, {len(outfits)} outfits",
            "issues": issues
        })
        
    return results

def assess_outfits(loader):
    print("Assessing Outfits (embedded in characters)...")
    chars = loader.load_characters()
    results = []
    
    for char_name, char_data in chars.items():
        if not isinstance(char_data, dict):
            continue

        outfits = char_data.get("outfits", {})
        for outfit_name, outfit_data in outfits.items():
            score = 0
            issues = []
            
            # Richness
            # Check components
            top = outfit_data.get("top", {})
            bottom = outfit_data.get("bottom", {})
            footwear = outfit_data.get("footwear", "")
            
            # Simple check: do we have details?
            if isinstance(top, dict):
                if top.get("material"): score += 5
                if top.get("fit"): score += 5
            elif top:
                score += 2 # String only
                
            if isinstance(bottom, dict):
                 if bottom.get("material"): score += 5
            elif bottom:
                score += 2
                
            # Description text (if any)
            desc = outfit_data.get("description", "")
            if desc:
                score += word_count(desc)
                
            if score < 10:
                issues.append("Low detail")
                
            results.append({
                "name": f"{char_name} - {outfit_name}",
                "type": "Outfit",
                "score": 50 + score,
                "details": f"Components check: {score} pts",
                "issues": issues
            })
            
    return results

def assess_interactions(loader):
    print("Assessing Interactions...")
    interactions = loader.load_interactions()
    results = []
    
    for category, interaction_dict in interactions.items():
        # Check if it's actually a dict (just in case)
        if not isinstance(interaction_dict, dict):
            continue
            
        for name, interaction in interaction_dict.items():
            if isinstance(interaction, str):
                # Should not happen given parser logic, but safety first
                results.append({
                    "name": name,
                    "type": "Interaction",
                    "score": 10,
                    "details": "Simple string interaction",
                    "issues": ["Legacy/Simple format"]
                })
                continue
                
            score = 0
            issues = []
            
            # Narrative Depth
            # interaction is a dict: {'description': ..., 'tags': ..., 'min_chars': ...}
            # Note: The parser keys are 'description' (which is the prompt), not 'prompt'
            prompt = interaction.get("description", "")
            w_count = word_count(prompt)
            
            if w_count < 5:
                issues.append("Extremely short prompt")
                score -= 10
            elif w_count > 20:
                score += 10
                
            # Role Distinctness
            if "{char1}" in prompt and "{char2}" in prompt:
                 # The file uses {char1}/{char2}, not {A}/{B}
                score += 10
            elif "{A}" in prompt and "{B}" in prompt:
                score += 10
            else:
                issues.append("Missing {char1}/{char2} placeholders")
                
            results.append({
                "name": name,
                "type": "Interaction",
                "score": 50 + score,
                "details": f"{w_count} words",
                "issues": issues
            })
            
    return results

def generate_report(results):
    report_path = project_root / "auditing" / "reports" / "content_quality.md"
    
    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    top_10 = results[:10]
    bottom_10 = results[-10:]
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Content Quality Assessment Report\n\n")
        f.write("## 🏆 Top 10 Highest Quality Assets\n")
        for item in top_10:
             f.write(f"- **{item['type']}**: {item['name']} (Score: {item['score']}) - {item['details']}\n")
             
        f.write("\n## ⚠️ Bottom 10 Requires Improvement\n")
        for item in bottom_10:
             f.write(f"- **{item['type']}**: {item['name']} (Score: {item['score']}) - {item['details']}\n")
             if item['issues']:
                 f.write(f"  - Issues: {', '.join(item['issues'])}\n")
                 
        f.write("\n## Full Breakdown by Type\n")
        # Group by type
        by_type = {}
        for r in results:
            t = r["type"]
            if t not in by_type: by_type[t] = []
            by_type[t].append(r)
            
        for t, items in by_type.items():
            avg_score = sum(i["score"] for i in items) / len(items) if items else 0
            f.write(f"\n### {t} (Avg Score: {avg_score:.1f})\n")
            # List low scorers only to save space
            low_scorers = [i for i in items if i["score"] < 50]
            if low_scorers:
                f.write("#### Needs Attention:\n")
                for item in low_scorers:
                    f.write(f"- {item['name']}: {', '.join(item['issues'])}\n")
            else:
                f.write("All assets in this category meet the baseline quality.\n")

    print(f"Report generated at: {report_path}")

if __name__ == "__main__":
    import sys
    sys.stdout = open("debug_output.txt", "w")
    sys.stderr = sys.stdout
    
    import contextlib
    from io import StringIO
    
    buffer = StringIO()
    
    try:
        with contextlib.redirect_stdout(buffer):
            print("--- START DEBUG ---")
            loader = DataLoader()
            
            # MANUAL TEST
            from logic.parsers import MarkdownParser
            test_file = loader.base_dir / "assets" / "data" / "characters" / "Diego_Morales.md"
            if test_file.exists():
                print(f"DEBUG: Reading {test_file}")
                text = test_file.read_text(encoding="utf-8")
                print(f"DEBUG: File length: {len(text)} bytes")
                try:
                    parsed = MarkdownParser.parse_characters(text)
                    print(f"DEBUG: Parsed result type: {type(parsed)}")
                    print(f"DEBUG: Parsed keys: {list(parsed.keys()) if parsed else 'None'}")
                except Exception as e:
                    print(f"DEBUG: Parse Error: {e}")
            else:
                print(f"DEBUG: Test file not found at {test_file}")

            all_results = []
            
            try:
                all_results.extend(assess_characters(loader))
            except Exception as e:
                print(f"CRASH in assess_characters: {e}")
                import traceback
                traceback.print_exc()

            try:
                all_results.extend(assess_outfits(loader))
            except Exception as e:
                print(f"CRASH in assess_outfits: {e}")
                import traceback
                traceback.print_exc()

            try:
                all_results.extend(assess_interactions(loader))
            except Exception as e:
                print(f"CRASH in assess_interactions: {e}")
                import traceback
                traceback.print_exc()

            try:
                generate_report(all_results)
            except Exception as e:
                print(f"CRASH in generate_report: {e}")
                import traceback
                traceback.print_exc()
            print("--- END DEBUG ---")
            
    except Exception as e:
        buffer.write(f"\nCRITICAL ERROR: {e}")
        
    with open("debug_output_clean.txt", "w", encoding="utf-8") as f:
        f.write(buffer.getvalue())
