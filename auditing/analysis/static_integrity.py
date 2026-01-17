import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

class StaticIntegrityAuditor:
    """Unified auditor for checking data integrity and standards across all assets."""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.reports = {
            "Characters": [],
            "Scenes": [],
            "Poses": [],
            "Interactions": [],
            "Outfits": []
        }
        self.errors = {
            "Media": [],
            "Integrity": []
        }
        self.stats = {
            "Total Assets": 0,
            "Total Failures": 0,
            "Total Errors": 0
        }

    def _extract_pure_description(self, text):
        """Remove tags and placeholders to get the core descriptive text."""
        # Remove parenthesized tags at start or end
        clean = re.sub(r'^\s*\(.*?\)\s*[:]*\s*', '', text).strip()
        clean = re.sub(r'\s*\(.*?\)\s*$', '', clean).strip()
        # Remove bold headers
        clean = re.sub(r'^\s*[-\*]\s+\*\*.*?\*\*[:]*', '', clean).strip()
        # Remove placeholders
        clean = re.sub(r'\{char\d+\}', '', clean)
        return clean

    def audit_characters(self):
        print("Auditing Characters...")
        char_dir = self.data_dir / "characters"
        if not char_dir.exists():
            return

        for char_file in char_dir.glob("*.md"):
            content = char_file.read_text(encoding="utf-8")
            issues = []
            
            # 1. Structure Check
            if "**Photo:**" not in content and " Photo:" not in content:
                issues.append("Missing 'Photo'")
            if "**Summary:**" not in content:
                issues.append("Missing 'Summary'")
            if "**Tags:**" not in content and " Tags:" not in content:
                issues.append("Missing 'Tags'")
            
            # 2. Appearance Section
            if "**Appearance:**" not in content:
                issues.append("Missing 'Appearance'")
            else:
                for bullet in ["Body", "Face", "Hair", "Skin"]:
                    if not re.search(rf'[\-\*]\s+\*\*{bullet}', content, re.IGNORECASE):
                        issues.append(f"Missing '{bullet}' bullet")

            # 3. Photo Integrity
            photo_match = re.search(r'\*\*Photo:\*\*\s*(.*)', content, re.IGNORECASE)
            if photo_match:
                photo_name = photo_match.group(1).strip()
                if photo_name and not (char_dir / photo_name).exists():
                    self.errors["Media"].append(f"Missing photo for {char_file.name}: {photo_name}")
                    issues.append("Broken photo link")

            # 4. Density/Score
            words = self._extract_pure_description(content).split()
            density = len(words)
            
            status = "PASS" if not issues else "FAIL"
            score = 100 - (len(issues) * 10)
            score = max(0, score)
            
            self.reports["Characters"].append({
                "name": char_file.name,
                "status": status,
                "score": score,
                "density": density,
                "issues": issues
            })
            if status == "FAIL": self.stats["Total Failures"] += 1
            self.stats["Total Assets"] += 1

    def audit_scenes(self):
        print("Auditing Scenes...")
        scene_file = self.data_dir / "scenes.md"
        if not scene_file.exists():
            return

        content = scene_file.read_text(encoding="utf-8")
        scenes = re.split(r'(^### .*$)', content, flags=re.MULTILINE)[1:]

        for i in range(0, len(scenes), 2):
            header = scenes[i].strip()
            body = scenes[i+1].strip() if i+1 < len(scenes) else ""
            name = header[3:].split('(')[0].strip()
            
            issues = []
            if "(" not in header or ")" not in header:
                issues.append("Missing tags")
            if "**Visual Description:**" not in body:
                issues.append("Missing 'Visual Description'")
            if "**Sensory/Atmospheric Details:**" not in body:
                issues.append("Missing 'Sensory/Atmospheric Details'")
            if "- **Lighting:**" not in body:
                issues.append("Missing 'Lighting'")
            
            status = "PASS" if not issues else "FAIL"
            self.reports["Scenes"].append({"name": name, "status": status, "issues": issues})
            if status == "FAIL": self.stats["Total Failures"] += 1
            self.stats["Total Assets"] += 1

    def audit_poses(self):
        print("Auditing Poses...")
        poses_file = self.data_dir / "poses.md"
        if not poses_file.exists():
            return

        content = poses_file.read_text(encoding="utf-8")
        current_cat = "General"
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("## "):
                current_cat = line[3:].split('(')[0].strip()
            elif line.startswith("- **"):
                match = re.match(r"^\s*-\s*\*\*(.*?)\*\*\s*(\(.*?\))?:\s*(.*)$", line)
                if match:
                    name = match.group(1)
                    tags_str = match.group(2)
                    desc = match.group(3)
                    issues = []
                    
                    if not tags_str: issues.append("Missing tags")
                    if len(desc) < 20: issues.append("Description too brief")
                    
                    # Tag casing check
                    if tags_str:
                        tags = [t.strip() for t in tags_str[1:-1].split(',') if t.strip()]
                        for t in tags:
                            if t and not t[0].isupper():
                                issues.append(f"Tag '{t}' should be Title Case")

                    status = "PASS" if not issues else "FAIL"
                    self.reports["Poses"].append({"name": f"{current_cat}: {name}", "status": status, "issues": issues})
                    if status == "FAIL": self.stats["Total Failures"] += 1
                else:
                    self.errors["Integrity"].append(f"Malformed pose: {line[:50]}...")
                self.stats["Total Assets"] += 1

    def audit_interactions(self):
        print("Auditing Interactions...")
        int_file = self.data_dir / "interactions.md"
        if not int_file.exists():
            return

        content = int_file.read_text(encoding="utf-8")
        current_cat = "General"
        for i, line in enumerate(content.splitlines()):
            line = line.strip()
            if line.startswith("## "):
                current_cat = line[3:].strip()
            elif line.startswith("- **"):
                match = re.match(r"^\s*-\s*\*\*(.*?)\*\*\s*(\(.*?\))?:\s*(.*)$", line)
                if match:
                    name = match.group(1)
                    tags_str = match.group(2)
                    template = match.group(3)
                    issues = []
                    
                    if not tags_str: issues.append("Missing tags")
                    if "{char1}" not in template: issues.append("Missing {char1}")
                    if len(template) < 30: issues.append("Template too brief")
                    
                    # Placeholder vs Name count integrity
                    count_match = re.search(r'\((\d+)\+?\)', name)
                    if count_match:
                        expected = int(count_match.group(1))
                        placeholders = set(re.findall(r'\{char(\d+)\}', template))
                        if len(placeholders) != expected:
                            issues.append(f"Placeholder mismatch: expected {expected}, found {len(placeholders)}")

                    status = "PASS" if not issues else "FAIL"
                    self.reports["Interactions"].append({"name": f"{current_cat}: {name}", "status": status, "issues": issues})
                    if status == "FAIL": self.stats["Total Failures"] += 1
                else:
                    if "Blank" not in line:
                        self.errors["Integrity"].append(f"Malformed interaction line {i+1}: {line[:50]}...")
                self.stats["Total Assets"] += 1

    def audit_outfits(self):
        print("Auditing Outfits...")
        outfit_root = self.data_dir / "outfits"
        if not outfit_root.exists():
            return

        for outfit_file in outfit_root.glob("**/*.txt"):
            content = outfit_file.read_text(encoding="utf-8")
            rel_path = outfit_file.relative_to(outfit_root)
            issues = []
            
            # Check for dimensions [F], [M], [H]
            sections = {"F": 0, "M": 0, "H": 0}
            current_section = None
            for line in content.splitlines():
                line = line.strip()
                if line in ["[F]", "[M]", "[H]"]:
                    current_section = line[1]
                elif current_section and line.startswith("-"):
                    sections[current_section] += len(line.split())

            for sec, words in sections.items():
                if words < 15:
                    issues.append(f"Section [{sec}] too brief ({words} words)")

            if "tags:" not in content.lower():
                issues.append("Missing 'tags' field")

            status = "PASS" if not issues else "FAIL"
            self.reports["Outfits"].append({"name": str(rel_path), "status": status, "issues": issues})
            if status == "FAIL": self.stats["Total Failures"] += 1
            self.stats["Total Assets"] += 1

    def generate_report(self):
        report_path = PROJECT_ROOT / "auditing" / "reports" / "static_integrity.md"
        print(f"Generating consolidated report: {report_path}")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Consolidated Static Integrity Audit\n\n")
            
            # Summary Dashboard
            fail_rate = (self.stats["Total Failures"] / self.stats["Total Assets"] * 100) if self.stats["Total Assets"] else 0
            f.write("## 📊 System Health Dashboard\n")
            f.write(f"- **Total Assets Audited**: {self.stats['Total Assets']}\n")
            f.write(f"- **Failure Rate**: {fail_rate:.1f}%\n")
            f.write(f"- **Integrity Errors**: {len(self.errors['Integrity'])}\n")
            f.write(f"- **Media Errors**: {len(self.errors['Media'])}\n\n")

            if self.errors["Integrity"] or self.errors["Media"]:
                f.write("### 🚩 Critical Errors\n")
                for err in self.errors["Integrity"]: f.write(f"- **Integrity**: {err}\n")
                for err in self.errors["Media"]: f.write(f"- **Media**: {err}\n")
                f.write("\n")

            # detailed reports (compressed)
            for category, items in self.reports.items():
                failures = [i for i in items if i["status"] == "FAIL"]
                pass_count = len(items) - len(failures)
                f.write(f"### {category} ({pass_count}/{len(items)} Passed)\n")
                if failures:
                    f.write("| Asset Name | Issues |\n")
                    f.write("|---|---|\n")
                    for fail in failures[:20]: # Cap to top 20
                        f.write(f"| {fail['name']} | {', '.join(fail['issues'])} |\n")
                    if len(failures) > 20:
                        f.write(f"| ... and {len(failures)-20} more | |\n")
                else:
                    f.write("✅ All items meet the standard.\n")
                f.write("\n")

    def run_all(self):
        self.audit_characters()
        self.audit_scenes()
        self.audit_poses()
        self.audit_interactions()
        self.audit_outfits()
        self.generate_report()

if __name__ == "__main__":
    data_dir = PROJECT_ROOT / "data"
    auditor = StaticIntegrityAuditor(data_dir)
    auditor.run_all()
