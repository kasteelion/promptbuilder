import os
import re
import sys
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class QualityAuditor:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.character_reports = {}
        self.outfit_reports = {}
        self.pose_reports = defaultdict(list)
        self.interaction_reports = []
        self.interaction_errors = []
        self.media_errors = []

    def audit_characters(self):
        char_dir = os.path.join(self.data_dir, "characters")
        if not os.path.exists(char_dir):
            return

        for filename in os.listdir(char_dir):
            if filename.endswith(".md"):
                path = os.path.join(char_dir, filename)
                self.character_reports[filename] = self._audit_single_character(path)

    def _audit_single_character(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        sections = {
            "Body": bool(re.search(r'^[-\*]\s+\*\*Body', content, re.MULTILINE | re.IGNORECASE)),
            "Face": bool(re.search(r'^[-\*]\s+\*\*Face', content, re.MULTILINE | re.IGNORECASE)),
            "Hair": bool(re.search(r'^[-\*]\s+\*\*Hair', content, re.MULTILINE | re.IGNORECASE)),
            "Skin": bool(re.search(r'^[-\*]\s+\*\*Skin', content, re.MULTILINE | re.IGNORECASE)),
            "Appearance": "Appearance:" in content or "appearance" in content.lower(),
            "History/Summary": "Summary:" in content or "Summary" in content or "History:" in content
        }

        appearance_match = re.search(r'Appearance:(.*?)(?:\n---|\n\*\*Outfits\*\*|$)', content, re.IGNORECASE | re.DOTALL)
        density = 0
        if appearance_match:
            desc_text = appearance_match.group(1)
            clean_text = re.sub(r'^[*-]\s+\*\*.*?\*\*[:\s]*', '', desc_text, flags=re.MULTILINE)
            words = clean_text.split()
            density = len(words)

        photo_match = re.search(r'\*\*Photo:\*\*\s*(.*)', content, re.IGNORECASE)
        photo_exists = False
        photo_name = ""
        if photo_match:
            photo_name = photo_match.group(1).strip()
            if photo_name:
                photo_path = os.path.join(os.path.dirname(path), photo_name)
                if os.path.exists(photo_path):
                    photo_exists = True
                else:
                    self.media_errors.append(f"Missing photo for {os.path.basename(path)}: {photo_name}")

        mandatory_score = sum(list(sections.values())[:4]) * 20
        density_score = min(density // 5, 20)
        score = mandatory_score + density_score
        
        return {
            "name": os.path.basename(path),
            "sections": sections,
            "density": density,
            "photo_exists": photo_exists,
            "photo_name": photo_name,
            "score": score
        }

    def audit_outfits(self):
        outfit_root = os.path.join(self.data_dir, "outfits")
        if not os.path.exists(outfit_root):
            return

        for root, dirs, files in os.walk(outfit_root):
            for file in files:
                if file.endswith(".txt"):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, outfit_root)
                    self.outfit_reports[rel_path] = self._audit_single_outfit(path)

    def _audit_single_outfit(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        sections = {"F": 0, "M": 0, "H": 0}
        current_section = None
        
        for line in content.split('\n'):
            line = line.strip()
            if line in ["[F]", "[M]", "[H]"]:
                current_section = line[1]
            elif current_section and line.startswith("-"):
                # Count words in the line, excluding the bullet and bold headers
                clean_line = re.sub(r'^- \*\*.*?\*\*[:\s]*', '', line)
                sections[current_section] += len(clean_line.split())

        return {
            "name": os.path.basename(path),
            "sections": sections,
            "total_words": sum(sections.values()),
            "is_detailed": all(v > 20 for v in sections.values())
        }

    def _extract_pure_description(self, line):
        # 1. Remove bullet and bold header
        clean = re.sub(r'^\s*[-\*]\s+\*\*.*?\*\*[:]*', '', line).strip()
        # 2. Remove leading tags in parentheses if they exist
        clean = re.sub(r'^\s*\(.*?\)\s*[:]*\s*', '', clean).strip()
        # 3. Remove trailing tags in parentheses
        clean = re.sub(r'\s*\(.*?\)\s*$', '', clean).strip()
        # 4. Remove interaction placeholders for counting
        clean = re.sub(r'\{char\d+\}', '', clean)
        return clean

    def audit_poses(self):
        poses_path = os.path.join(self.data_dir, "poses.md")
        if not os.path.exists(poses_path):
            return

        with open(poses_path, 'r', encoding='utf-8') as f:
            current_category = "General"
            for line in f:
                line = line.strip()
                if line.startswith("##"):
                    current_category = line[2:].split('(')[0].strip()
                elif line.startswith("- **"):
                    description = self._extract_pure_description(line)
                    word_count = len(description.split())
                    self.pose_reports[current_category].append({
                        "line": line[:50] + "...",
                        "count": word_count
                    })

    def audit_interactions(self):
        interactions_path = os.path.join(self.data_dir, "interactions.md")
        if not os.path.exists(interactions_path):
            return

        with open(interactions_path, 'r', encoding='utf-8') as f:
            line_num = 0
            for line in f:
                line_num += 1
                line = line.strip()
                if line.startswith("- **"):
                    # Integrity check
                    count_match = re.search(r'\*\*.*?\s*\((\d+)\+?\)\*\*', line)
                    if count_match:
                        expected_chars = int(count_match.group(1))
                        placeholders = set(re.findall(r'\{char(\d+)\}', line))
                        actual_chars = len(placeholders)
                        if actual_chars != expected_chars:
                            self.interaction_errors.append(
                                f"Line {line_num}: Expected {expected_chars} characters but found {actual_chars} placeholders."
                            )

                    # Descriptiveness check
                    description = self._extract_pure_description(line)
                    word_count = len(description.split())
                    name_match = re.search(r'\*\*(.*?)\*\*', line)
                    name = name_match.group(1) if name_match else f"Line {line_num}"
                    
                    self.interaction_reports.append({
                        "name": name,
                        "count": word_count
                    })

    def run_all(self):
        print("Running Quality Audit...")
        self.audit_characters()
        self.audit_outfits()
        self.audit_poses()
        self.audit_interactions()
        self.generate_reports()

    def generate_reports(self):
        self._generate_quality_report()
        self._generate_descriptiveness_report()

    def _generate_quality_report(self):
        report_path = os.path.join(self.data_dir, "..", "auditing", "reports", "quality_audit.md")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Content Quality & Integrity Audit\n\n")
            f.write("## 👥 Character Detail Audit\n")
            f.write("| Character | Score | Density | Sections | Photo | Status |\n")
            f.write("|---|---|---|---|---|---|\n")
            sorted_chars = sorted(self.character_reports.values(), key=lambda x: x["score"], reverse=True)
            for char in sorted_chars:
                mandatory = ["Body", "Face", "Hair", "Skin"]
                missing = [m for m in mandatory if not char["sections"].get(m, False)]
                sections_str = "✅" if not missing else f"❌ Missing: {', '.join(missing)}"
                photo_str = "✅" if char["photo_exists"] else f"❌ `{char['photo_name']}`"
                status = "🌟 Elite" if char["score"] >= 95 else "✅ Good" if char["score"] >= 80 else "⚠️ Needs Detail"
                f.write(f"| {char['name']} | {char['score']} | {char['density']} | {sections_str} | {photo_str} | {status} |\n")

            if self.interaction_errors:
                f.write("\n## 🎭 Interaction Integrity Errors\n")
                for err in self.interaction_errors:
                    f.write(f"- {err}\n")
            if self.media_errors:
                f.write("\n## 🖼️ Media Integrity Errors\n")
                for err in self.media_errors:
                    f.write(f"- {err}\n")

    def _generate_descriptiveness_report(self):
        report_path = os.path.join(self.data_dir, "..", "auditing", "reports", "descriptiveness_audit.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Asset Descriptiveness Audit\n\n")
            f.write("## 🧥 Outfit Detail Depth\n")
            f.write("| Outfit | Total Words | [F] | [M] | [H] | Status |\n")
            f.write("|---|---|---|---|---|---|\n")
            sorted_outfits = sorted(self.outfit_reports.items(), key=lambda x: x[1]["total_words"], reverse=True)
            for path, data in sorted_outfits:
                s = data["sections"]
                status = "✅ Detailed" if data["is_detailed"] else "⚠️ Needs Detail"
                f.write(f"| {path} | {data['total_words']} | {s['F']} | {s['M']} | {s['H']} | {status} |\n")

            f.write("\n## 🧘 Pose Category Average Length\n")
            f.write("| Category | Avg Words | Item Count |\n")
            f.write("|---|---|---|\n")
            cat_stats = []
            for cat, items in self.pose_reports.items():
                avg = sum(i["count"] for i in items) / len(items) if items else 0
                cat_stats.append((cat, avg, len(items)))
            for cat, avg, count in sorted(cat_stats, key=lambda x: x[1], reverse=True):
                f.write(f"| {cat} | {avg:.1f} | {count} |\n")

            f.write("\n## 🤝 Interaction Template Complexity\n")
            f.write("| Interaction | Template Words | Status |\n")
            f.write("|---|---|---|\n")
            sorted_inter = sorted(self.interaction_reports, key=lambda x: x["count"], reverse=True)
            for item in sorted_inter:
                status = "✅ Detailed" if item["count"] > 10 else "⚠️ Brief"
                f.write(f"| {item['name']} | {item['count']} | {status} |\n")

        print(f"Descriptiveness report saved to {report_path}")

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(root_dir, "data")
    auditor = QualityAuditor(data_dir)
    auditor.run_all()
