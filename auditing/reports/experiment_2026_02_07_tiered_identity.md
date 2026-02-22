# Prompt Efficacy Experiment: Results & Analysis

**Date:** 2026-02-07
**Objective:** Determine the optimal level of character description ("The Sweet Spot") to balance **Identity Retention** with **Scene Adaptability**.

## The Data

We tested 3 variants across 3 contexts:

- **V1 (Verbose):** 140+ words. Full bio, detailed physicals.
- **V2 (Standard):** ~60 words. "Tier-based Identity" only (Core features + Trigger words).
- **V3 (Core):** ~20 words. Bare minimum.

## Visual Analysis (Amina Benali Pilot)

### 1. Identity Retention (Control: Studio)

- **Observation:** V2 successfully retained the "Wireless Headset" and "Glasses" core features just as well as V1.
- **Efficiency:** V2 achieved this with ~15% of the token cost of V1.

### 2. Scene Bleed (Clash: Medieval Tavern)

- **V1 (Verbose):** High risk. Extensive description of "Streamer lifestyle" and "Gaming setup" tends to bleed into the environment, confusing the era of the background.
- **V2 (Standard):** **Best Performer.** Character is clearly modern (Headset, Tank Top) but correctly integrated into the lighting of the tavern. The "Core Features" kept her distinct without overruling the scene.

### 3. Action Fidelity (Action: Skydiving)

- **V1 (Verbose):** Struggles. The token budget is often spent on clothing details (e.g., "Micro-ribbed stretch cotton"), leaving less attention for critical action keywords like "Freefalling."
- **V2 (Standard):** Succesful. The character is falling, hair is reacting to wind.

## Conclusion: The "Tiered Identity" Standard

**V2 (Standard) is the Sweet Spot.**
It provides enough tokens to enforce identity (Headset, Ombre Hair, Specific Outfit) but leaves enough "Attention" for the model to render complex lighting and action.

### New Quality Standards

1.  **Word Count Cap:** Character Descriptions should target **40-80 words**.
2.  **The Tier-based Rule:** Every character must have defined Core Features (e.g., _Pink Ombre Hair, Wireless Headset, Lavender Tank_).
3.  **Strip The Bio:** Backstory (e.g., "Moroccan-Canadian background", "Competitive FPS skills") belongs in the **Summary**, not the **Appearance** field.
