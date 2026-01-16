# Pose Standards

To ensure high-quality, expressive pose generation, all entries in `poses.md` must adhere to the **Elite Pose Standard**. A pose is not just a static position; it is a combination of body language, expression, and energy.

## Schema

```markdown
- **Pose Name** (Tag1, Tag2, Tag3): [Visual Description]
```

## detailed Requirements

### 1. Naming

- **Format:** Title Case (e.g., `Arms Crossed`, `Leaning Against Wall`).
- **Uniqueness:** Must be unique within the file.
- **Clarity:** The name should reflect the core action or aesthetic (e.g., `Jacket Slung Over Shoulder` is better than `Cool Walk`).

### 2. Tags

- **Format:** Parentheses immediately following the name.
- **Content:** Comma-separated list.
- **Required Tags:**
  - **Category Tag:** At least one tag acting as a high-level category (e.g., `Sitting`, `Standing`, `Dynamic`, `Portrait`).
  - **Vibe Tag:** At least one tag describing the mood/energy (e.g., `Confident`, `Relaxed`, `Intense`, `Playful`).
  - **Framing Tag:** (New) Describe the intended shot type (e.g., `Full Body`, `Upper Body`, `Close-up`, `Wide Shot`).
- **Casing:** Tags should be **Title Case** (e.g., `Casual`, not `casual`).

### 3. Visual Description

The description is the most critical part. It must be descriptive enough to guide the AI without over-constraining the outfit or character details.

- **Length:** 1-2 conciseness sentences.
- **Components:**
  - **Body Positioning:** How are the limbs arranged? Be specific: "left hand on hip", "weight on right leg" instead of "hand on hip".
  - **Weight/balance:** Where is the center of gravity? (e.g., "leaning heavily on left leg", "mid-stride").
  - **Expression/Head:** (Optional but recommended) Head tilt or expression cues (e.g., "looking back over shoulder", "chin lifted confidently").
  - **Vibe:** The energy the pose conveys (e.g., "exuding quiet dominion", "bursting with energy").

## Common Tag Vocabulary

To maintain a searchable and clean database, use these standardized tags:

| Category     | Recommended Tags                                                   |
| :----------- | :----------------------------------------------------------------- |
| **Position** | `Standing`, `Sitting`, `Squatting`, `Lying`, `Kneeling`, `Jumping` |
| **Energy**   | `Dynamic`, `Static`, `Action`, `Relaxed`, `Rigid`                  |
| **Framing**  | `Full Body`, `Upper Body`, `Close-up`, `Wide Shot`, `Portrait`     |
| **Mood**     | `Confident`, `Shy`, `Intense`, `Playful`, `Moody`, `Professional`  |

## Example (Good vs Bad)

**BAD:**
` - **Sitting** (Basic, Sitting): Sitting down using a chair.`
_(Too vague, redundant tags, no weight distribution)._

**GOOD:**
`- **Executive Perch** (Sitting, Confident, Professional, Full Body): Perched on the edge of a desk with the right leg resting on the floor and the left dangling, arms crossed loosely at the chest, projecting casual authority.`

## Quality Rules

1.  **Avoid generic descriptions.** "Standing there" is unacceptable. "Standing with weight shifted to the right hip" is better.
2.  **No "Blank" entries.** Every pose must have a description.
3.  **Tags must be relevant.** Do not tag "Portrait" if it's a full-body jumping shot.
4.  **Limb Specificity.** Mention at least one specific limb (left/right) to anchor the AI.
5.  **Explicit Positioning.** If a character is on their back, stomach, side, or in a specific orientation relative to the environment (e.g., "prone", "supine"), it must be explicitly mentioned in the description (e.g., "Lying flat on the back", "Crouched low to the ground").
