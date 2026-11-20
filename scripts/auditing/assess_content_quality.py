import sys
import re
from pathlib import Path
from collections import Counter

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
    
    for name, char_obj in chars.items():
        # Handle Pydantic model vs dict
        data = char_obj.dict() if hasattr(char_obj, "dict") else char_obj
        
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
        appearance = data.get("appearance", "")
        total_words = 0
        
        if isinstance(appearance, str):
            total_words = word_count(appearance)
        elif isinstance(appearance, dict):
            for v in appearance.values():
                total_words += word_count(str(v))
        
        if total_words < 20:
            issues.append("Very short description (< 20 words)")
            score -= 10
        elif total_words > 100:
            score += 10
            
        # Completeness (Metadata)
        if not data.get("age_presentation") and not data.get("age"):
            issues.append("Missing Age")
            score -= 5
        if not data.get("vibe"):
            issues.append("Missing Vibe")
            score -= 5
             
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
    
    for char_name, char_obj in chars.items():
        char_data = char_obj.dict() if hasattr(char_obj, "dict") else char_obj
        if not isinstance(char_data, dict):
            continue

        outfits = char_data.get("outfits", {})
        for outfit_name, outfit_data in outfits.items():
            # If it's a string, it's still "valid" as a simple format, but lower score
            is_simple = isinstance(outfit_data, str)
            
            score = 0
            issues = []
            
            if is_simple:
                score += 5 # Base for having a description
                score += word_count(outfit_data) // 5
                if len(outfit_data) < 20:
                    issues.append("Low detail")
                
                results.append({
                    "name": f"{char_name} - {outfit_name}",
                    "type": "Outfit",
                    "score": 50 + score,
                    "details": f"Simple format: {word_count(outfit_data)} words",
                    "issues": issues
                })
                continue

            if not isinstance(outfit_data, dict):
                results.append({
                    "name": f"{char_name} - {outfit_name}",
                    "type": "Outfit",
                    "score": 0,
                    "details": f"Invalid data type: {type(outfit_data)}",
                    "issues": ["Invalid format"]
                })
                continue
                
            # Component Analysis
            # normalize keys to lowercase for check
            norm_data = {k.lower(): v for k, v in outfit_data.items()}
            
            top = norm_data.get("top")
            bottom = norm_data.get("bottom")
            one_piece = norm_data.get("one_piece") or norm_data.get("dress")
            
            if top: score += 10
            if bottom or one_piece: score += 10
            
            # Check for detail richness within components
            for key in ["top", "bottom", "accessories", "hair/makeup", "footwear"]:
                val = norm_data.get(key)
                if val:
                    if isinstance(val, dict):
                         if val.get("material") or val.get("fabric"): score += 5
                         if val.get("fit") or val.get("cut"): score += 5
                    elif isinstance(val, str) and len(val) > 20:
                        score += 5
            
            if score < 15:
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

def extract_colors(text):
    """Extract HEX colors from text."""
    if not isinstance(text, str):
        return []
    hex_pattern = r'#([A-Fa-f0-9]{6})'
    return re.findall(hex_pattern, text.upper())

def analyze_color_diversity(loader):
    """Analyze the distribution of HEX colors in outfits."""
    print("Analyzing Color Diversity...")
    chars = loader.load_characters()
    color_counts = Counter()
    
    for char_name, char_data in chars.items():
        outfits = char_data.get("outfits", {})
        for outfit_name, outfit_data in outfits.items():
            if isinstance(outfit_data, dict):
                # Recursively check for colors in nested dicts
                def scan_dict(d):
                    for k, v in d.items():
                        if isinstance(v, dict):
                            scan_dict(v)
                        elif isinstance(v, str):
                            color_counts.update(extract_colors(v))
                        elif isinstance(v, list):
                            for item in v:
                                if isinstance(item, str):
                                    color_counts.update(extract_colors(item))
                scan_dict(outfit_data)
    return color_counts

def generate_color_report(color_counts):
    """Generate a markdown report for color diversity."""
    report_path = project_root / "auditing" / "reports" / "color_diversity.md"
    print(f"Generating color report: {report_path}")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🎨 Color Diversity Report\n\n")
        f.write("Distribution of HEX colors across the outfit library.\n\n")
        
        if not color_counts:
            f.write("⚠️ No HEX colors detected in outfits. Ensure colors are specified as `#RRGGBB`.\n")
            return
            
        f.write("| Color Swatch | HEX Code | Count | Frequency |\n")
        f.write("|---|---|---|---|\n")
        
        total = sum(color_counts.values())
        for color, count in color_counts.most_common(50):
            percent = (count / total) * 100
            # Note: Markdown doesn't support background colors easily, so we just use text and counts
            f.write(f"| `#{color}` | `#{color}` | {count} | {percent:.1f}% |\n")
            
        if len(color_counts) > 50:
            f.write(f"\n*...and {len(color_counts) - 50} more unique colors.*")

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
                colors = analyze_color_diversity(loader)
                generate_color_report(colors)
            except Exception as e:
                print(f"CRASH in analyze_color_diversity: {e}")

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
