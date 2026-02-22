# Pose Standards: Center of Gravity & Lead Limb

A pose is a narrative anchor. To ensure expressive generation, we focus on the **Center of Gravity** and a single **Key Limb** to ground the AI's understanding of weight and movement.

## 1. Schema

```markdown
- **Pose Name** (Categorical, Vibe, ShotType): [Narrative Description]
```

## 2. The "Grounded" Description

The description must be concise (1-2 sentences) and focus on:

1. **Center of Gravity:** Where is the weight? (e.g., "Leaning heavily on the right hip", "Weight shifted forward onto the balls of the feet").
2. **The Lead Limb:** Ground the AI with one specific limb placement (e.g., "Left hand tucked into back pocket", "Right arm raised to shield eyes").
3. **Shot Compatibility:** Description should complement the **ShotType** tag (e.g., "Close-up" focuses on head tilt; "Full Body" focuses on stance).

## 3. Standardized Tags

| Category     | Allowed Tags                                                      |
| :----------- | :---------------------------------------------------------------- |
| **Position** | `Standing`, `Sitting`, `Squatting`, `Lying`, `Kneeling`, `Action` |
| **Vibe**     | `Confident`, `Vulnerable`, `Aggressive`, `Relaxed`, `Stiff`       |
| **ShotType** | `Full Body`, `Upper Body`, `Close-up`, `Wide Shot`, `POV`         |

## 4. Example (Good vs Legacy)

- **Legacy (Too technical):** "Standing with legs 12 inches apart, arms at 45 degree angles..."
- **Grounded Stance:**
  > - **The Defiant Stance** (Standing, Confident, Full Body): Standing with weight centered and feet planted wide, chin lifted slightly, and the right hand resting firmly on the hip to project immovable resolve.

## 5. Quality Rules

1. **Limb Specificity:** Mention at least one specific limb (left/right) to ground the AI's understanding.
2. **Energy:** Describe the _tension_ of the pose, not just the geometry.
3. **No Character Details:** Never mention specific clothing or hair in a pose definition.
