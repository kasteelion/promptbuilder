# 🕵️ Auditing & Analysis System

The **Auditing Suite** is a vital component of PromptBuilder designed to ensure the quality, integrity, and diversity of your generated prompts and character data.

It operates on the principle of **"Trust, but Verify"**—allowing you to generate thousands of prompts while maintaining high creative standards.

---

## 🚀 Quick Start: The Full Audit

The easiest way to check system health is to run the full audit suite. This orchestrator triggers all individual tools in the correct order and produces a consolidated report.

```bash
# Run full audit (generates 50 test prompts by default)
python auditing/run_full_audit.py

# Run with more samples for better statistical accuracy
python auditing/run_full_audit.py --count 100

# Run analysis only (skip new generation, useful for quick checks)
python auditing/run_full_audit.py --skip-gen
```

### 📄 The Comprehensive Report

After running the full audit, open the master report:
👉 **`auditing/reports/comprehensive_audit.md`**

This document combines:

- **Best & Worst Prompts**: Scored by the `find_best_worst.py` logic.
- **Quality Metrics**: Missing fields, low-detail descriptions, etc.
- **Tag Inventory**: Consolidated list of all tags for review.
- **Descriptiveness**: Word counts for outfits and interactions.

---

## 🛠️ Tool Reference

### 1. Quality & Integrity (`quality_audit.py`)

Scans all `.md` and `.txt` files in `data/` to ensure they meet quality standards.

- **Checks:**
  - **Character Density**: Ensures "Appearance" sections are detailed enough.
  - **Missing Assets**: Flags missing photos or broken links.
  - **Outfit Detail**: Counts words in outfit files to find "thin" descriptions.
  - **Interaction Integrity**: Verifies that `{charX}` placeholders match the character count.

### 2. Prompt Scoring (`find_best_worst.py`)

Analyzes generated prompt text files to "score" them based on heuristics:

- **Positive Signals**: "Photorealistic", "Cinematic lighting", high character detail.
- **Negative Signals**: "Rendering", "3D render", "plastic", "low quality".
- **Output**: Identifies the Top 3 and Bottom 3 prompts for manual review.

### 3. Distribution Visualization (`generate_sankey_diagram.py`)

Generates a mermaid.js Sankey diagram showing the flow of the randomizer:
`Character -> Scene -> Style -> Outfit`

- This helps visualize if a specific style or character is dominating the generations.
- Output: `auditing/reports/prompt_distribution_flow.md`

### 4. Tag Inventory (`tag_inventory.py`)

Aggregates every single tag used across Characters, Scenes, and Outfits.

- **Goal**: Identify synonyms (e.g., "Sci-Fi" vs "Science Fiction") or typos.
- **Output**: `auditing/reports/tag_inventory.md`

### 5. Connectivity Check (`check_character_connectivity.py`)

_Advanced check._ Ensures that every character has at least one valid Scene they can appear in based on tag intersections. Characters with `0` connectivity will never appear in valid generations.

### 6. Outfit Precision Audit (`audit_outfit_quality.py`)

Scans detailed [F] variant descriptions to score "completeness" against the 6 Key Dimensions defined in `OUTFIT_STANDARDS.md`.

- **Dimensions:** Fit, Material, Neckline, Sleeve, Waist, Length.
- **Goal:** Identify vague prompts (e.g. "A red dress") and flag them for improvement.

---

## 📂 Directory Structure

```text
auditing/
├── reports/                  # Generated report files (Gitignored)
├── run_full_audit.py         # Main entry point
├── quality_audit.py          # Static logic analyzer
├── find_best_worst.py        # Generated content scorer
├── generate_sankey_diagram.py# Visualization generator
├── tag_inventory.py          # Taxonomy checker
└── consolidate_reports.py    # Report merger
```
