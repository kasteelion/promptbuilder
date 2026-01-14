import os
import sys
from collections import defaultdict
from tag_inventory import TagInventory

class ContentGapAnalyzer:
    def __init__(self, data_dir):
        self.inventory = TagInventory(data_dir)
        self.data_dir = data_dir
        
    def load_data(self):
        print("Crawling data for Gap Analysis...")
        self.inventory.crawl_characters()
        self.inventory.crawl_markdown_list(os.path.join(self.data_dir, "scenes.md"), "Scenes")
        self.inventory.crawl_markdown_list(os.path.join(self.data_dir, "base_prompts.md"), "Base Prompts")
        self.inventory.crawl_outfits()
        # We don't strictly need poses/interactions for this high-level gap check, but could add later
        
    def analyze(self):
        # 1. Normalize all tags
        # Structure: normalized_tags[base_tag] = { "Scenes": count, "Outfits": count, ... }
        normalized_data = defaultdict(lambda: defaultdict(int))
        
        for source, tags in self.inventory.tags_by_source.items():
            for raw_tag, count in tags.items():
                base, _ = self.inventory.normalize_tag(raw_tag)
                normalized_data[base][source] += count

        # 2. Identify Gaps
        critical_gaps = [] # Demand (Prompts/Scenes) > 0, Supply (Chars/Outfits) == 0
        imbalances = []    # Supply < Demand
        oversaturated = [] # One tag dominates > 50% of a category
        
        # Calculate totals for percentage checks
        totals = {
            "Characters": sum(self.inventory.tags_by_source["Characters"].values()),
            "Outfits": sum(self.inventory.tags_by_source["Outfits"].values()),
            "Scenes": sum(self.inventory.tags_by_source["Scenes"].values())
        }
        
        for tag, counts in normalized_data.items():
            # Skip UI/Descriptive tags for gap analysis (gender, hair color, etc)
            if tag in ["female", "male", "curvy", "petite", "tall", "shorthair", "longhair"]:
                continue
                
            prompts = counts["Base Prompts"]
            scenes = counts["Scenes"]
            chars = counts["Characters"]
            outfits = counts["Outfits"]
            
            # Demand = Prompts OR Scenes (Scenes imply a need for matching actors/clothes)
            demand = max(prompts, scenes)
            
            if demand > 0:
                # Check Supply
                if chars == 0 and outfits == 0:
                    critical_gaps.append(f"**{tag}**: {demand} Scenes/Prompts defined, but **0** Characters or Outfits support it.")
                elif chars == 0:
                     critical_gaps.append(f"**{tag}**: {demand} Scenes/Prompts, but **0** Characters.")
                elif outfits == 0:
                     imbalances.append(f"**{tag}**: {demand} Scenes, but **0** Outfits (Sims will be mis-dressed).")
                elif outfits < demand:
                     imbalances.append(f"**{tag}**: High demand ({demand}), low outfit supply ({outfits}).")

            # Check Saturation 
            if totals["Outfits"] > 0 and (outfits / totals["Outfits"] > 0.10): # >10% of total tags is A LOT
                 oversaturated.append(f"**{tag}** in Outfits ({outfits} occurrences)")
            
        return {
            "critical_gaps": critical_gaps,
            "imbalances": imbalances,
            "oversaturated": oversaturated,
            "raw_data": normalized_data 
        }

    def generate_chart(self, analysis, output_path):
        try:
            import plotly.graph_objects as go
        except ImportError:
            print("Plotly not installed. Skipping visualization.")
            return

        # Prepare Data
        # We want to show the tags with the most activity, or the biggest gaps.
        # Let's show "Top 40 Tags by Total Volume" to see the landscape.
        
        data_rows = []
        for tag, counts in analysis.get("raw_data", {}).items(): # We need to expose raw data in analyze() first
            total_vol = counts["Characters"] + counts["Outfits"] + counts["Scenes"] + counts["Base Prompts"]
            data_rows.append({
                "tag": tag,
                "Characters": counts["Characters"],
                "Outfits": counts["Outfits"],
                "Scenes": counts["Scenes"],
                "Prompts": counts["Base Prompts"],
                "Total": total_vol
            })
            
        # Sort by total volume
        data_rows.sort(key=lambda x: x["Total"], reverse=True)
        top_tags = data_rows[:40]
        
        tags = [d["tag"] for d in top_tags]
        chars = [d["Characters"] for d in top_tags]
        outfits = [d["Outfits"] for d in top_tags]
        scenes = [d["Scenes"] for d in top_tags]
        
        fig = go.Figure(data=[
            go.Bar(name='Scenes', x=tags, y=scenes, marker_color='#FFA07A'), # Light Salmon
            go.Bar(name='Characters', x=tags, y=chars, marker_color='#98FB98'), # Pale Green
            go.Bar(name='Outfits', x=tags, y=outfits, marker_color='#87CEFA'), # Light Sky Blue
        ])

        fig.update_layout(
            title='Content Supply vs Demand (Top 40 Tags)',
            xaxis_tickfont_size=10,
            yaxis=dict(title='Count'),
            barmode='group',
            template='plotly_dark'
        )

        fig.write_html(output_path)
        print(f"Visualization saved to: {output_path}")

    def generate_report(self, analysis, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 📉 Content Gap Analysis\n")
            f.write("Identifies themes where we have 'Demand' (Scenes/Prompts) but no 'Supply' (Characters/Outfits).\n\n")
            
            f.write("## 📊 Visualization\n")
            f.write(f"See [Content Balance Chart](content_balance_chart.html) for an interactive view.\n\n")

            f.write("## 🚨 Critical Gaps (Missing Content)\n")
            if analysis["critical_gaps"]:
                for gap in sorted(analysis["critical_gaps"]):
                    f.write(f"- 🔴 {gap}\n")
            else:
                f.write("✅ No critical gaps found.\n")
                
            f.write("\n## ⚠️ Supply/Demand Imbalances\n")
            if analysis["imbalances"]:
                for imb in sorted(analysis["imbalances"]):
                    f.write(f"- 🔸 {imb}\n")
            else:
                f.write("✅ Content is well diversified.\n")
                
            f.write("\n## ℹ️ Dominant Themes (Oversaturation)\n")
            f.write("Tags appearing in >10% of all assets in their category.\n\n")
            if analysis["oversaturated"]:
                for sat in sorted(analysis["oversaturated"]):
                    f.write(f"- {sat}\n")
            else:
                f.write("✅ No single theme dominates.\n")

        print(f"Gap Report saved to: {output_path}")

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    analyzer = ContentGapAnalyzer(os.path.join(root_dir, "data"))
    analyzer.load_data()
    results = analyzer.analyze()
    
    report_path = os.path.join(root_dir, "auditing", "reports", "content_gaps.md")
    chart_path = os.path.join(root_dir, "auditing", "reports", "content_balance_chart.html")
    
    analyzer.generate_report(results, report_path)
    analyzer.generate_chart(results, chart_path)
