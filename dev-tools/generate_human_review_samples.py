"""
Human Review Prompt Generator

Generates a targeted set of prompts from specific score buckets:
- ELITE (600+)
- HIGH (450-600)
- MID (300-450)
- LOW (150-300)
- CLASH (<150)
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
from core.builder import PromptBuilder

def generate_samples():
    loader = DataLoader()
    characters = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    poses = loader.load_presets("poses.md")
    scenes = loader.load_presets("scenes.md")
    interactions = loader.load_interactions()
    color_schemes = loader.load_color_schemes()
    modifiers = loader.load_modifiers()
    framing = loader.load_framing()

    randomizer = PromptRandomizer(
        characters=characters,
        base_prompts=base_prompts,
        poses=poses,
        scenes=scenes,
        interactions=interactions,
        color_schemes=color_schemes,
        modifiers=modifiers,
        framing=framing,
    )
    
    builder = PromptBuilder(
        characters=characters,
        base_prompts=base_prompts,
        poses=poses,
        color_schemes=color_schemes,
        modifiers=modifiers,
        framing=framing
    )

    buckets = {
        "ELITE (600+)": [],
        "HIGH (450-600)": [],
        "MID (300-450)": [],
        "LOW (150-300)": [],
        "CLASH (<150)": []
    }
    
    target_per_bucket = 2
    total_needed = target_per_bucket * len(buckets)
    attempts = 0
    max_attempts = 1000
    
    print(f"Generating samples for human review (Target: {target_per_bucket} per bucket)...")
    
    while sum(len(b) for b in buckets.values()) < total_needed and attempts < max_attempts:
        attempts += 1
        # Use single candidate generation to get raw scores without retry logic interference
        config = randomizer._generate_single_candidate(include_scene=True)
        score = randomizer._score_candidate(config)
        
        bucket_key = None
        if score >= 600: bucket_key = "ELITE (600+)"
        elif score >= 450: bucket_key = "HIGH (450-600)"
        elif score >= 300: bucket_key = "MID (300-450)"
        elif score >= 150: bucket_key = "LOW (150-300)"
        else: bucket_key = "CLASH (<150)"
        
        if bucket_key and len(buckets[bucket_key]) < target_per_bucket:
            # Generate the full prompt text
            full_prompt = builder.generate(config)
            
            # Format a simple preview for the report
            chars_list = config.get("selected_characters", [])
            chars_names = ", ".join([c["name"] for c in chars_list])
            scene = config.get("scene", "N/A")
            style = config.get("base_prompt", "N/A")
            
            prompt_text = f"**Score: {score}**\n"
            prompt_text += f"- **Style:** {style}\n"
            prompt_text += f"- **Scene:** {scene}\n"
            prompt_text += f"- **Characters:** {chars_names}\n\n"
            prompt_text += f"**Full Prompt:**\n```\n{full_prompt}\n```\n"
            
            buckets[bucket_key].append(prompt_text)

    # Print results
    output = "# Human Review Samples\n\n"
    for bucket, samples in buckets.items():
        output += f"## {bucket}\n"
        if not samples:
            output += "_No samples found in this range._\n"
        for i, s in enumerate(samples):
            output += f"### Sample {i+1}\n{s}\n"
        output += "\n---\n"
    
    print(output)
    
    # Save to file
    report_path = Path("auditing/reports/human_review_samples.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(output, encoding="utf-8")
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    generate_samples()
