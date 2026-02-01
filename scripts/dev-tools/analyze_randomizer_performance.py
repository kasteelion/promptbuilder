"""
Prompt Randomizer Performance Analyzer

Generates a large batch of prompts and analyzes:
- Score distribution
- Retry frequency
- Rejection rates
- Performance metrics
- Quality trends

Usage:
    python dev-tools/analyze_randomizer_performance.py --count 2000
    python dev-tools/analyze_randomizer_performance.py --count 500 --threshold 250
"""

import os
import sys
import time
import json
from collections import Counter, defaultdict
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer


class RandomizerAnalyzer:
    """Analyzes randomizer performance and quality metrics."""
    
    def __init__(self, count=2000, threshold=None):
        self.count = count
        self.threshold = threshold
        self.results = []
        self.stats = {
            "total_prompts": 0,
            "total_candidates": 0,
            "total_retries": 0,
            "total_time": 0,
            "scores": [],
            "attempts_distribution": Counter(),
            "rejection_count": 0,
        }
        
        # Load data
        print("Loading data...")
        loader = DataLoader()
        self.randomizer = PromptRandomizer(
            characters=loader.load_characters(),
            base_prompts=loader.load_base_prompts(),
            poses=loader.load_presets("poses.md"),
            scenes=loader.load_presets("scenes.md"),
            interactions=loader.load_interactions(),
            color_schemes=loader.load_color_schemes(),
            modifiers=loader.load_modifiers(),
            framing=loader.load_framing(),
        )
        
        # Optionally override threshold
        if threshold:
            print(f"Overriding MIN_SCORE_FLOOR to {threshold}")
            # We'll need to modify the randomizer to track this
    
    def generate_prompts(self):
        """Generate prompts and collect detailed metrics."""
        print(f"\nGenerating {self.count} prompts...")
        print("=" * 60)
        
        start_time = time.time()
        
        for i in range(self.count):
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                avg_time = (elapsed / (i + 1)) * 1000
                print(f"Progress: {i + 1}/{self.count} ({(i + 1) / self.count * 100:.1f}%) - Avg: {avg_time:.1f}ms/prompt")
            
            # Generate with tracking
            prompt_start = time.time()
            result = self._generate_with_tracking()
            prompt_time = (time.time() - prompt_start) * 1000
            
            # Store result
            result["generation_time_ms"] = prompt_time
            self.results.append(result)
            
            # Update stats
            self.stats["total_prompts"] += 1
            self.stats["total_candidates"] += result["candidates_generated"]
            self.stats["total_retries"] += result["retry_count"]
            self.stats["total_time"] += prompt_time
            self.stats["scores"].append(result["final_score"])
            self.stats["attempts_distribution"][result["attempts"]] += 1
            if result["retry_count"] > 0:
                self.stats["rejection_count"] += 1
        
        total_time = time.time() - start_time
        print(f"\nCompleted in {total_time:.2f}s")
        print(f"Average: {(total_time / self.count) * 1000:.1f}ms per prompt")
    
    def _generate_with_tracking(self):
        """Generate a single prompt with detailed tracking."""
        # Temporarily instrument the randomizer
        best_score = -float('inf')
        all_scores = []
        attempts = 0
        candidates_generated = 0
        
        MAX_RETRIES = 2
        MIN_SCORE_FLOOR = self.threshold if self.threshold else 150
        
        for attempt in range(MAX_RETRIES + 1):
            attempts += 1
            
            # Generate 3 candidates per attempt
            for _ in range(3):
                candidates_generated += 1
                config = self.randomizer._generate_single_candidate(
                    num_characters=None,
                    include_scene=True,
                    include_notes=False
                )
                score = self.randomizer._score_candidate(config)
                all_scores.append(score)
                
                if score > best_score:
                    best_score = score
                    best_config = config
            
            # Check if we should stop
            if best_score >= MIN_SCORE_FLOOR:
                break
        
        return {
            "final_score": best_score,
            "all_scores": all_scores,
            "attempts": attempts,
            "candidates_generated": candidates_generated,
            "retry_count": attempts - 1,
            "rejected_scores": [s for s in all_scores if s < MIN_SCORE_FLOOR],
            "threshold": MIN_SCORE_FLOOR,
        }
    
    def analyze_results(self):
        """Analyze collected data and generate statistics."""
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)
        
        scores = self.stats["scores"]
        
        # Basic stats
        print(f"\n📊 Generation Statistics:")
        print(f"  Total Prompts: {self.stats['total_prompts']}")
        print(f"  Total Candidates: {self.stats['total_candidates']}")
        print(f"  Avg Candidates/Prompt: {self.stats['total_candidates'] / self.stats['total_prompts']:.1f}")
        print(f"  Total Retries: {self.stats['total_retries']}")
        print(f"  Prompts Needing Retry: {self.stats['rejection_count']} ({self.stats['rejection_count'] / self.stats['total_prompts'] * 100:.1f}%)")
        
        # Performance
        avg_time = self.stats["total_time"] / self.stats["total_prompts"]
        print(f"\n⚡ Performance:")
        print(f"  Total Time: {self.stats['total_time'] / 1000:.2f}s")
        print(f"  Average Time: {avg_time:.1f}ms per prompt")
        print(f"  Throughput: {1000 / avg_time:.1f} prompts/second")
        
        # Score distribution
        print(f"\n🎯 Score Distribution:")
        print(f"  Mean: {sum(scores) / len(scores):.2f}")
        print(f"  Median: {sorted(scores)[len(scores) // 2]:.2f}")
        print(f"  Min: {min(scores)}")
        print(f"  Max: {max(scores)}")
        print(f"  Std Dev: {self._std_dev(scores):.2f}")
        
        # Score ranges
        ranges = {
            "0-99": 0,
            "100-199": 0,
            "200-299": 0,
            "300-399": 0,
            "400-499": 0,
            "500-599": 0,
            "600+": 0,
        }
        
        for score in scores:
            if score < 100:
                ranges["0-99"] += 1
            elif score < 200:
                ranges["100-199"] += 1
            elif score < 300:
                ranges["200-299"] += 1
            elif score < 400:
                ranges["300-399"] += 1
            elif score < 500:
                ranges["400-499"] += 1
            elif score < 600:
                ranges["500-599"] += 1
            else:
                ranges["600+"] += 1
        
        print(f"\n📈 Score Ranges:")
        for range_name, count in ranges.items():
            pct = count / len(scores) * 100
            bar = "█" * int(pct / 2)
            print(f"  {range_name:10} | {count:5} ({pct:5.1f}%) {bar}")
        
        # Retry distribution
        print(f"\n🔄 Retry Distribution:")
        for attempts in sorted(self.stats["attempts_distribution"].keys()):
            count = self.stats["attempts_distribution"][attempts]
            pct = count / self.stats["total_prompts"] * 100
            retry_count = attempts - 1
            print(f"  {retry_count} retries: {count:5} ({pct:5.1f}%)")
        
        # Threshold analysis
        threshold = self.threshold if self.threshold else 150
        below_threshold = sum(1 for s in scores if s < threshold)
        print(f"\n🚫 Threshold Analysis (MIN_SCORE_FLOOR = {threshold}):")
        print(f"  Scores below threshold: {below_threshold} ({below_threshold / len(scores) * 100:.1f}%)")
        print(f"  Would need retry with this threshold: {below_threshold}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if below_threshold / len(scores) < 0.05:
            print(f"  ✅ Current threshold ({threshold}) is appropriate")
            print(f"     Only {below_threshold / len(scores) * 100:.1f}% of prompts need retry")
        elif below_threshold / len(scores) < 0.10:
            print(f"  ⚠️  Threshold ({threshold}) is acceptable")
            print(f"     {below_threshold / len(scores) * 100:.1f}% retry rate is manageable")
        else:
            print(f"  ❌ Threshold ({threshold}) may be too high")
            print(f"     {below_threshold / len(scores) * 100:.1f}% retry rate could impact performance")
            
            # Suggest better threshold
            sorted_scores = sorted(scores)
            pct_95 = sorted_scores[int(len(sorted_scores) * 0.05)]
            print(f"     Consider lowering to {int(pct_95)} (95th percentile)")
    
    def _std_dev(self, values):
        """Calculate standard deviation."""
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def save_report(self, output_dir="auditing/reports"):
        """Save detailed report to file."""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = int(time.time())
        report_file = os.path.join(output_dir, f"randomizer_analysis_{timestamp}.md")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Randomizer Performance Analysis\n\n")
            f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Sample Size:** {self.count} prompts\n")
            f.write(f"**Threshold:** {self.threshold if self.threshold else 150}\n\n")
            
            f.write("## Summary Statistics\n\n")
            scores = self.stats["scores"]
            f.write(f"- **Mean Score:** {sum(scores) / len(scores):.2f}\n")
            f.write(f"- **Median Score:** {sorted(scores)[len(scores) // 2]:.2f}\n")
            f.write(f"- **Score Range:** {min(scores)} - {max(scores)}\n")
            f.write(f"- **Retry Rate:** {self.stats['rejection_count'] / self.stats['total_prompts'] * 100:.1f}%\n")
            f.write(f"- **Avg Time:** {self.stats['total_time'] / self.stats['total_prompts']:.1f}ms\n\n")
            
            f.write("## Score Distribution\n\n")
            f.write("| Range | Count | Percentage |\n")
            f.write("|-------|-------|------------|\n")
            
            ranges = {
                "0-99": sum(1 for s in scores if s < 100),
                "100-199": sum(1 for s in scores if 100 <= s < 200),
                "200-299": sum(1 for s in scores if 200 <= s < 300),
                "300-399": sum(1 for s in scores if 300 <= s < 400),
                "400-499": sum(1 for s in scores if 400 <= s < 500),
                "500-599": sum(1 for s in scores if 500 <= s < 600),
                "600+": sum(1 for s in scores if s >= 600),
            }
            
            for range_name, count in ranges.items():
                pct = count / len(scores) * 100
                f.write(f"| {range_name} | {count} | {pct:.1f}% |\n")
        
        print(f"\n📄 Report saved to: {report_file}")
        return report_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze randomizer performance")
    parser.add_argument("--count", type=int, default=2000, help="Number of prompts to generate")
    parser.add_argument("--threshold", type=int, default=None, help="Override MIN_SCORE_FLOOR")
    parser.add_argument("--no-save", action="store_true", help="Don't save report to file")
    
    args = parser.parse_args()
    
    analyzer = RandomizerAnalyzer(count=args.count, threshold=args.threshold)
    analyzer.generate_prompts()
    analyzer.analyze_results()
    
    if not args.no_save:
        analyzer.save_report()


if __name__ == "__main__":
    main()
