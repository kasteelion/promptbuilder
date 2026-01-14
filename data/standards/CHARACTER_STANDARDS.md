# Character Definition Standards

To ensure consistent, high-fidelity character generation, all character files must adhere to the **Elite Character Standard**. This models the character not just as a visual description, but as a structured entity with physical, stylistic, and personality dimensions.

## File Structure

### 1. Header Metadata

- **Photo:** `filename.png` (Must exist in `assets/`)
- **Summary:** A concise 2-3 sentence "elevator pitch" of the character.
- **Tags:** Comma-separated list. MUST include:
  - Gender tag (`female`, `male`, `non-binary`)
  - Ethnicity/Background tag (e.g., `latina`, `japanese`, `celtic`)
  - Vibe tags (e.g., `athletic`, `intellectual`, `gritty`)
- **Gender:** Single letter code (`F`, `M`, `N`).
- **Signature Color:** Hex code (e.g., `#FF4500`).

### 2. Appearance Section (The "Physical Truth")

This section MUST be broken down into four distinct bullet points:

- **Body:** Kibbe body type, flesh quality, vertical line, and specific build details (muscle definition, proportions).
- **Face:** Facial structure (shape, planes), eye shape/color, nose/mouth details, and resting expression.
- **Hair:** Type (1A-4C), density, cut/style, texture/finish, and color.
- **Skin:** Undertone (warm/cool/olive), texture/finish, and unique details (freckles, scars).

### 3. Personality & Vibe

- **Age Presentation:** e.g., "Early 20s", "Ageless".
- **Vibe / Energy:** Keywords describing their presence.
- **Bearing:** How they move or stand (posture, gait).

### 4. Style Notes (Comment Block)

Use `//` comments to define style rules that guide outfit selection but aren't prompt text.

- Makeup preferences.
- Fabric/Material preferences.
- Cultural markers.

### 5. Outfits Section

Must include at least one **#### Base** outfit following the `OUTFIT_STANDARDS.md` schema (Top/Bottom/Footwear/Accessories).

## Example Entry

```markdown
### Name Definition

**Photo:** name.png
**Summary:** A sharp, agile warrior-scholar.
**Tags:** female, athletic, intellectual
**Gender:** F
**Signature Color:** #006400

**Appearance:**

- **Body:** Dramatic Gamine; lean sinewy muscle; compact torso.
- **Face:** Angular structure; diamond shape; intense focused eyes.
- **Hair:** Type 2A waves; copper-red; versatile practical braids.
- **Skin:** Fair neutral; weathered undertone.

**Age Presentation:** 20s.
**Vibe / Energy:** Vigilant, precise.
**Bearing:** Poised, economical movement.

// Style Notes
// - Minimal makeup
// - Functional layers

---

**Outfits:**

#### Base

- **Top:** ...
```
