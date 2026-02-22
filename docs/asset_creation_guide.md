# Asset Creation Guide: The "Modular Tiered" Standard

**Version:** 1.0 (Feb 2026)
**Objective:** Create character assets that are _consistent_ (recognizable identity) and _adaptable_ (flexible in varied scenes).

## 1. The Core Philosophy: "Modular Distillation"

Generative AI has a limited "Attention Budget." Every word you spend describing a character's shoelaces is attention taken away from their face or the scene's lighting.

**Do not aim for "Richness" (Word Count). Aim for "Distillation".**

### The "Core Feature" Rule

Every character must be defined by **3-4 Distinct Core Features** that make them instantly recognizable even in a crowd or a simple sketch.

- _Bad Feature:_ "Beautiful eyes." (Generic)
- _Bad Feature:_ "Wearing a t-shirt." (Generic)
- _Good Feature:_ "Neon pink bob cut." (Distinct)
- _Good Feature:_ "Cybernetic left arm." (Distinct)
- _Good Feature:_ "Scar across left cheek." (Distinct)

## 2. Character Description Standards

### The Appearance Field

- **Target Length:** 40 - 80 words.
- **Content:** purely physical traits. No personality. No backstory.
- **Structure:**
  1.  **Core Features First:** Mention the key defining features immediately.
  2.  **Trigger Words:** Use efficient tokens ("Ombre hair") instead of long prose ("Hair that fades from pink to orange").
  3.  **No Posing:** Do not describe the character as "standing", "sitting", or "leaning." This overrides scene interactions.

**Example (Amina Benali - Refactored):**

> "Moroccan-Canadian streamer with three distinct features: neon pink/orange ombre hair in a topknot, stylish clear-framed glasses, and a wireless headset around her neck. Soft natural frame. Warm golden-olive skin. Wearing a form-fitting lavender ribbed tank top." (42 words)

### The Summary Field

- **Target Length:** Unlimited (within reason).
- **Content:** This is where the "Soul" lives. Backstory, personality, origin, skills.
- **Usage:** This field helps the _User_ understand the character but is NOT sent to the image generator effectively (unless specifically requested), preventing "concept bleed."

## 3. Interaction Standards

### Legacy vs. Narrative

- **Legacy (Avoid):** `Interaction: "Sword Fight"` (The AI has to guess what a sword fight looks like).
- **Narrative (Required):** `Interaction: "**Action:** {char1} and {char2} are locked in a duel, clashing steel blades with sparks flying. **Dynamic:** Motion blur on the weapons, intense expressions."`

### Placeholders

- Always use `{char1}` / `{char2}` (or `{A}`/`{B}`) to ensure the AI knows where to put the actors.

## 4. Outfit Standards

- **Separation:** Outfits must be defined in the `Outfits` block, not the `Appearance` block (unless it's the default/base look).
- **Detail Level:** +1 word per item.
  - _Bad:_ "A pair of blue jeans that are worn at the knees and have a silver button."
  - _Good:_ "Distressed blue jeans."
