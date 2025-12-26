# Data File Syntax & Conventions

This document outlines the standard file formats, syntax, and norms used within the `data/` directory. Adhering to these conventions ensures that characters, outfits, and prompt assets are correctly parsed and utilized by the PromptBuilder application.

---

## 1. Character Files
**Path:** `data/characters/*.md`

Character files are Markdown documents that define the visual identity, metadata, and default style of a specific persona. The filename should generally match the character's name (e.g., `diego_morales.md`).

### Basic Structure

```markdown
### Character Name
**Photo:** filename.png
**Summary:** A brief narrative description of the character's vibe and personality.
**Tags:** comma, separated, tags, for, filtering
**Gender:** F (or M)
**Signature Color:** #HEXCODE (Optional)

**Appearance:**
* **Body:** Detailed description of body type, flesh quality, and proportions.
* **Face:** Description of facial structure, eyes, nose, and expression.
* **Hair:** Texture, length, style, and color.
* **Skin:** Complexion, undertones, and texture.

**Age Presentation:** text description (e.g., "mid-20s")
**Vibe / Energy:** list of adjectives
**Bearing:** description of posture and movement

---

**Outfits:**

#### Base
- **Top:** Description
- **Bottom:** Description
- **Footwear:** Description
- **Accessories:** Description
- **Hair/Makeup:** Specific styling for this base look
```

### Key Fields
- **Header (`### Name`):** Must match the character's display name.
- **Photo:** The filename of the corresponding image in `data/characters/`.
- **Gender:** Critical for mapping to the correct outfit library (`outfits_f.md` vs `outfits_m.md`).
- **Signature Color:** A Hex code (e.g., `#FF7F50`) used to personalize generic outfits.
- **Appearance:** Bullet points are parsed to build the core visual prompt.
- **Base Outfit:** Defines the "Default" look if no specific outfit is selected in the UI.

### Advanced Features
- **Identity Locks:** You can replace the standard `**Appearance:**` header with `**Appearance (Identity Locks):**`. This signals the parser that specific physical traits (like a signature hairstyle) should *never* be overridden by outfit definitions.

---

## 2. Outfit Libraries
**Paths:**
- `data/outfits_f.md` (Female)
- `data/outfits_m.md` (Male)
- `data/outfits_h.md` (Hijabi adaptations)

These files contain a categorized library of clothing options.

### Structure

```markdown
# File Title

## Category Name (e.g., Athletic & Sports)

### Outfit Name
Description text goes here. Bold **key items** to ensure they are emphasized in the final prompt.
```

### Syntax & Logic

#### 1. Bold Emphasis
Enclosing text in double asterisks (e.g., `**red leather jacket**`) is a convention to signal key visual elements.

#### 2. Dynamic Placeholders
Outfits can adapt to specific color schemes defined in `data/color_schemes.md`.
- `{primary_color}`: The team/scheme's main color.
- `{secondary_color}`: The supporting color.
- `{accent}`: A highlight color.
- `{team}`: The text name of the team/organization.
- `{modifier}`: A special slot for appending text from `data/modifiers.md`.

#### 3. Signature Color Logic
To support characters with defined `**Signature Color:**`, you can use two different syntaxes:

**A. Conditional Block (Recommended):**
`((default:Color Name) or (signature))`
*   **Logic:** If the character has a signature color and "Use Signature Color" is checked, uses the Hex code. Otherwise, defaults to "Color Name".
*   **Example:** `A **((default:white) or (signature)) dress**`

**B. Standalone Tag:**
`{signature_color}`
*   **Logic:** If the character has a signature color and "Use Signature Color" is checked, uses the Hex code. Otherwise, defaults to the generic term `"vibrant color"`.
*   **Example:** `Energy glow in {signature_color}.`

---

## 3. Color Schemes
**Path:** `data/color_schemes.md`

Defines reusable palettes for team jerseys, uniforms, and themed outfits.

### Structure

```markdown
## Scheme Name
- **primary:** #HexCode
- **secondary:** #HexCode
- **accent:** #HexCode
- **team:** Display Name of Team
```

---

## 4. Global Asset Lists
**Paths:** `data/poses.md`, `data/scenes.md`, `data/interactions.md`

These files provide reusable snippets for prompt construction.

### Structure
All three files follow a simple list format grouped by headers.

```markdown
## Category Header

- **Asset Name:** The actual text description that will be injected into the prompt.
- **Another Asset:** Description...
```

### Interaction Placeholders (`interactions.md`)
Interactions often involve multiple subjects. Use specific placeholders to map characters:
- `{char1}`: The primary character.
- `{char2}`: The secondary character.
- `{char3+}`: Additional characters.

---

## 5. Tags & Modifiers
**Paths:** `data/tags.md`, `data/modifiers.md`

- **Tags:** Simple categorization lists used for UI filtering.
- **Modifiers:** Small text snippets appended to outfits when the `{modifier}` placeholder is present (e.g., adding specific equipment to a generic sports uniform).

```markdown
## Category (e.g., Volleyball - Libero)
- **text:** , wearing a contrasting {secondary_color} jersey...
```
