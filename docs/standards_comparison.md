# Standards Comparison: Legacy vs. Modular Tier-based Identity

**Objective:** Decide whether to deprecate `CHARACTER_STANDARDS.md` in favor of `asset_creation_guide.md`.

## 1. Core Philosophy

| Feature   | Legacy Standard (`CHARACTER_STANDARDS.md`)              | New Standard (`asset_creation_guide.md`)   |
| :-------- | :------------------------------------------------------ | :----------------------------------------- |
| **Goal**  | "Physical Truth" & Completeness                         | "Visual Identity" & Token Efficiency       |
| **Logic** | More detail = Better character.                         | Less detail = Better attention management. |
| **Focus** | Anatomical correctness, Kibbe body types, skull planes. | distinct "Core Features" (3-4 key traits). |

## 2. Appearance Field Guidelines

| Metric         | Legacy                                                                            | New (Modular Tier-based)                                  |
| :------------- | :-------------------------------------------------------------------------------- | :-------------------------------------------------------- |
| **Word Count** | Uncapped (often 100-150 words).                                                   | **40 - 80 words.**                                        |
| **Structure**  | 4 bullet points (Body, Face, Hair, Skin).                                         | Single paragraph focusing on Features + Trigger Words.    |
| **Content**    | Explicit details on "sinewy muscle," "diamond face shape," "weathered undertone." | Only visible, distinct traits ("Neon pink hair," "Scar"). |
| **Posing**     | "Poised, economical movement" (often conflates body with action).                 | **Forbidden.** Posing belongs in the Scene/Action prompt. |

## 3. Impact on Generation (Evidence from Experiment)

### Legacy Approach (Verbose)

- **Pros:** Highly detailed portraits in isolation.
- **Cons:**
  - **Scene Bleed:** "Modern gamer" descriptions leak into "Medieval Tavern" backgrounds.
  - **Action Failure:** "Skydiving" prompts fail because the AI is too busy rendering "micro-ribbed cotton."
  - **Rigidity:** Detailed posture descriptions fight against dynamic action prompts.

### New Approach (Modular Tier-based Identity)

- **Pros:**
  - **High Fidelity:** Identity is retained via specific core features (Headset, Hair Color).
  - **High Adaptability:** Minimal token cost allows the scene and action to take priority.
  - **No Bleed:** Context-neutral descriptions fit into any era/setting.
- **Cons:** Less "literary" description in the text file itself.

## Recommendation

**Deprecate Legacy Standards.**
The Legacy standards were built for a "Character Card" model (text-based roleplay), whereas the New Standards are optimized for **Image Generation Pipelines**.

**Proposal:**

1.  Archive `CHARACTER_STANDARDS.md` to `legacy/`.
2.  Rename `asset_creation_guide.md` to `CHARACTER_STANDARDS.md` as the new single source of truth.

## 4. Side-by-Side Implications

### Example A: Amina Benali

**Legacy Standard (Verbose - 146 words)**

> **Body:** Soft Natural frame; natural-soft flesh; balanced proportions with gentle curves... (30 words)
> **Face:** Soft-balanced facial structure; oval-to-heart face shape... (40 words)
> **Hair:** Type 2B-2C waves; very high density; long length... (25 words)
> **Skin:** Medium-tan with warm golden-olive undertones... (20 words)
> _Result:_ AI focuses on "soft flesh" and "Type 2B waves", ignoring the "Skydiving" prompt.

**New Standard (Modular Tiered - 42 words)**

> Moroccan-Canadian background. Three distinct core features: **Neon pink/orange ombre hair** in a topknot, **stylish clear-framed glasses**, and a **wireless headset** around her neck. Soft natural frame. Warm golden-olive skin.
> _Result:_ AI nails the Headset/Hair (Core Features) and uses the remaining attention checking the Action prompt.

### Example B: Mela Hart

**Legacy Standard (Verbose - 85 words)**

> **Body:** Flamboyant Natural frame; tall vertical line; broad shoulders; long limbs; somewhat straight silhouette; moderate bust and hip definition; athletic and springy presence.
> **Face:** Oval shape; high cheekbones; full lips; prominent expressive eyes; straight nose bridge; defined jawline.
> **Hair:** Type 4A (Natural texture) with Type 2B/2C (Wavy/Curly) ends; long, dark brown braids throughout the hair with loose wavy curls at the bottom.

**New Standard (Modular Tiered - 35 words)**

> Deep brown skin with warm golden undertones. **Signature long dark braids** with loose curly ends. Tall, athletic build with broad shoulders. Bright, buoyant expression with high cheekbones and full lips.
