# Character Definition Standards: The "Tier-based Identity" Model

To ensure consistent, high-fidelity character generation while honoring the **Attention Budget**, all character assets must adhere to these standards.

## 1. The Core Goal: Modularity

The primary purpose of these standards is to create **Portable Characters**. A character should be defined such that they remain recognizable as the same person whether they are in a "Cyberpunk City" or a "Victorian Ballroom."

- **Identity Persistence:** Core features like hair color, facial features (scars, glasses), and body type must be consistent.
- **Context Neutrality:** Avoid descriptors that "tie" the character to a specific setting (e.g., don't describe a character as "looking like a gamer" in their core physical description).

## 2. The Tier-Based Structure

To ensure modularity and high-fidelity, use the following tier-based organization:

### Section 1: Metadata & Traits

- **Metadata:** Photo, Summary, Tags, Gender, Signature Color.
- **Traits (The "Toggle" List):** Removable items or accessories that can be toggled on/off (e.g., glasses, piercings, signature hats). If it's permanent, it doesn't belong here.

### Section 2: Appearance (The Anatomical Core)

This section defines the permanent physical truth. Use exactly four bullet points:

- **Body:** Proportions, build (e.g., "Average Hourglass; Soft").
- **Face:** Structure, eyes, and permanent marks (e.g., "Oval face; tiny mole near lips").
- **Hair:** Texture, density, and base color.
- **Skin:** Tone, undertone, and permanent texture (e.g., "Freckled; Luminous").

### Section 3: Vibe & Presence

- **Age Presentation:** e.g., "Mid-20s".
- **Vibe / Energy:** Strategic keywords.
- **Bearing:** Movement and posture.

### Section 4: Style Notes & Outfits

- **// Style Notes:** Guidance for outfit selection.
- **Outfits:** Modular blocks following the `OUTFIT_STANDARDS.md`.

## 3. The Winning Standard: The Tokenized Archetype

Based on visual testing, the **Tokenized Archetype** provides the highest precision with the lowest token cost. It combines structural data (Frame/Shape/Flesh) with core identity features.

| Category | Taxonomy / Lexicon                        | Requirement                                     |
| :------- | :---------------------------------------- | :---------------------------------------------- |
| **Body** | [Frame] [Shape]; [Flesh]                  | `Average Hourglass; Soft rounded flesh`         |
| **Face** | [Shape]; [Eye Shape] [Color]; [Nose/Lips] | `Oval; Large almond dark brown eyes; Full lips` |
| **Hair** | [Type #] [Texture]; [Volume]; [Color]     | `Type 2B Waves; High volume; Dark brown`        |
| **Skin** | [Tone]; [Undertone]; [Finish]             | `Medium-tan; Warm Golden-Olive; Luminous`       |

## 4. Drafting Rules: The "Sketch Artist" Method

1.  **No Prose:** Eliminate "She has," "With a," or "Looks like."
2.  **Precision Tokens:** Use specific technical terms (Kibbe Frame, 1A-4C Texture).
3.  **Core Feature Focus:** Use the **Traits** block for persistent identity markers (scars, tattoos, distinct jewelry).

## Example: Amina Benali (Gold Standard Entry)

```markdown
### Amina Benali

**Photo:** amina_benali_photo.png
**Summary:** A sharp, agile Moroccan-Canadian strategist.
**Tags:** Female, Moroccan, Athletic, Intellectual
**Gender:** F
**Signature Color:** #C3B1E1

**Traits:**

- **Glasses:** Clear-framed cat-eye glasses.

**Appearance:**

- **Body:** Average Hourglass frame; Soft rounded flesh; 1:7 Proportions.
- **Face:** Oval-to-heart; Large almond dark brown eyes; Straight refined nose; Tiny freckle near left corner of lips.
- **Hair:** Type 2B-2C waves; Natural volume; Dark brown; Caramel balayage.
- **Skin:** Medium-tan; Warm Golden-Olive; Luminous finish.

**Age Presentation:** Mid-20s.
**Vibe / Energy:** Engaging, Strategic, Camera-Aware Confidence.
**Bearing:** Excellent upright posture; animated hand gestures.

// Style Notes:
// - Prefers cozy-cute aesthetics and pastel tones like lavender and sage.
```

> [!TIP]
> Think of each bullet as a **layer** in a sketch. The artist (or AI) needs the structure (Kibbe/Face Shape) before the decoration (Balayage/Glow).
