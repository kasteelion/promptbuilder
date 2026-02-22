# Scene Standards: The "Big 3" Environmental Markers

Immersive environments are rendered best when the AI is given 3-4 vivid, contrasting markers rather than an exhaustive list of architectural details.

## 1. The "Big 3" Framework

Every scene must define:

1. **Lighting Quality:** Not just "bright", but "Volumetric shafts of golden sunlight" or "Harsh fluorescent flickering."
2. **Atmospheric Texture:** The "grit" of the scene (e.g., "Thick hanging smoke", "Sterile chrome surfaces", "Rain-slicked pavement").
3. **The Key Prop:** One essential item that defines the space (e.g., "A sprawling mahogany desk", "Overflowing neon trash bins").

## 2. Tagging & Blocking

- **Environment:** `Indoor`, `Outdoor`, `Liminal`.
- **Style Blocker:** Use `block:[Genre]` to prevent style-clash (e.g., `block:Fantasy` for a Server Room).
- **Mood:** Use `mood:[Adjective]` for high-level emotional guiding.

## 3. Example Entry

```markdown
## Neon Rain Alley (Outdoor, Urban, mood:Gritty, block:Medieval)

**Visual Description:**
A narrow, rain-slicked alleyway between towering concrete megastructures. The air is thick with steam and the hum of holographic advertisements.

**The Big 3 Markers:**

- **Lighting:** Low-key, dominated by neon cycling between electric blue and magenta.
- **Atmosphere:** Claustrophobic, wet, and high-tech-low-life.
- **Key Prop:** A single flickering streetlamp casting long, distorted shadows across heavy industrial cables.
```

## 4. Quality Rules

1. **Sensory focus:** Prioritize what the "camera" sees first.
2. **Context Neutrality:** Ensure the scene can host multiple characters without feeling "pre-populated."
3. **Word Efficiency:** Keep descriptions under 50 words to save **Attention Budget** for the subject.
