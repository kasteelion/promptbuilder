# Scene Definition Standards

To ensure immersive and consistent environments, all Scene files (e.g., within `scenes.md`) must adhere to the **Atmospheric Scene Standard**.

## The Scene Schema

Every scene entry must follow this structure:

```markdown
## Scene Name (Tag1, Tag2, Mood:MoodName, Block:BlockName)

**Visual Description:**
[Deep visual description focusing on lighting, architecture, materials, and atmosphere. ~2-3 sentences.]

**Sensory/Atmospheric Details:**

- **Lighting:** Specific light sources (neon, golden hour, candlelight) and quality (harsh, diffuse, volumetric).
- **Atmosphere:** The "feeling" of the space (crowded, sterile, cozy,abandoned).
- **Key Elements:** 2-3 essential props or features that anchor the scene.
```

## Tagging Rules

1.  **Environment Tag:** Must have at least one of `Indoor`, `Outdoor`, `Urban`, `Nature`.
2.  **Mood Tag:** Optional but recommended. Must use `Mood:` prefix (e.g., `Mood:Cozy`).
3.  **Block Tag:** Use `Block:Name` to prevent specific styles from using this scene (e.g., `Block:Fantasy` for a Modern Office).

## Example Entry

```markdown
## Cyberpunk Alley (Urban, Outdoor, Mood:Gritty, Mood:Dark, Block:Historical)

**Visual Description:**
A narrow, rain-slicked alleyway wedged between towering megastructures. Holographic ads flicker senselessly in puddles, reflecting neon pink and electric blue light off wet pavement and steam pipes.

**Sensory/Atmospheric Details:**

- **Lighting:** Low-key, dominated by neon signage and bioluminescent street gore.
- **Atmosphere:** Claustrophobic, dangerous, wet, and high-tech.
- **Key Elements:** Overflowing dumpsters, exposed cabling, steaming vents.
```
