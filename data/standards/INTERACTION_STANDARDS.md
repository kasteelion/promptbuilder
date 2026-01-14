# Interaction Standards

Interactions are complex prompts that define how two or more characters relate to each other in a scene. They must be dynamic, coherent, and structurally sound.

## Schema

```markdown
- **Interaction Name** (Tag1, Tag2, ...): [Template String]
```

## Detailed Requirements

### 1. Naming

- **Format:** Title Case.
- **Descriptive:** Should clearly indicate the nature of the interaction (e.g., `Whispering Secret` vs just `Talking`).

### 2. Tags

- **Format:** Parentheses immediately following the name.
- **Required Tags:**
  - **Type Tag:** (e.g., `Social`, `Romantic`, `Conflict`, `Professional`).
  - **Vibe Tag:** (e.g., `Intimate`, `Tense`, `Joyful`).
- **Casing:** **Title Case**.

### 3. The Template String

This is the raw prompt text used for generation.

- **Placeholders:** MUST use standardized placeholders:
  - `{char1}`: The primary subject (usually the one initiating action).
  - `{char2}`: The secondary subject (usually the recipient or partner).
  - `{char3}`: (Rare) Third participant.
- **Perspective:** Write in the third person describing the scene.
- **Content Requirements:**
  - **Physical Connection:** Describe how they are touching or positioned relative to each other (e.g., "holding hands", "standing back-to-back").
  - **Eye Contact/Focus:** Where are they looking? (e.g., "gazing into each other's eyes", "looking at a shared document").
  - **Emotional specific:** Describe the shared mood (e.g., "sharing a laugh", "tense standoff").
  - **Action:** What are they doing? (e.g., "walking", "dancing", "fighting").

## Example (Good vs Bad)

**BAD:**
`- **Hugging** (Social): {char1} and {char2} hug.`
_(Too simple, low fidelity)._

**GOOD:**
`- **Emotional Reunion** (Social, Emotional, Hug): {char1} embracing {char2} tightly with eyes closed, {char2} burying their face in {char1}'s shoulder, expressing relief and deep affection.`

## Quality Rules

1.  **Grammar:** Sentences must flow naturally when names are substituted.
    - _Check:_ "{char1} helps {char2}" -> "Alice helps Bob".
2.  **No Dialogue:** Do not include spoken words in quotes.
3.  **Participant Limit:** Most interactions should be designed for 2 characters unless specified otherwise.
4.  **Vibe consistency:** The description must match the tags.
