# Auditing & Analysis Tools

This directory contains utilities for analyzing prompt generation quality, content distribution, and thematic coherence.

## 🚀 One-Click Audit (Recommended)

### `run_full_audit.py`

Run the entire auditing suite sequentially. This is the best way to verify system health.

**Usage:**

```bash
python auditing/run_full_audit.py [--count 50] [--skip-gen]
```

**Performs:**

1.  **Tag Inventory Check**: Checks for synonyms and duplicate tags (`tag_inventory.py`).
2.  **Connectivity Check**: Ensures all characters map to available scenes (`check_character_connectivity.py`).
3.  **Generation**: Creates fresh test prompts (`automate_generation.py`).
4.  **Visualization**: Generates Mermaid diagrams (`generate_sankey_diagram.py`).

**Outputs:**

- `output/reports/tag_inventory.md`
- `output/reports/connectivity_report.txt`
- `output/reports/prompt_distribution_flow.md`

---

## Individual Tools

### `tag_inventory.py`

Audits all tags across Characters, Scenes, Outfits, and Prompts to find discrepancies (e.g., "Sport" vs "Sports").

### `check_character_connectivity.py`

Verifies that every character has semantic links to the Scene database. Characters with 0 links are flagged as "CRITICAL".

### `generate_sankey_diagram.py`

Analyzes generated prompts and builds a Mermaid flow diagram (Character -> Scene -> Style -> Outfit) to visualize distribution and coherence.

### `automate_generation.py` (via `automation/`)

Generates raw prompts for testing.

```bash
python automation/automate_generation.py --prompts-only --count 50
```

---

## Reports Location

All reports are generated in the project root under:
`output/reports/`
