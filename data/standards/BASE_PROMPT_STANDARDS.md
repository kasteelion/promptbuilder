# Base Prompt Standards

Base Prompts define the "Lens" and "Medium" through which the request is interpreted. They must be technical, precise, and separated from content.

## The Prompt Schema

```markdown
## Style Name (Tag1, Tag2, Mood:MoodName)

**Medium/Format:**
[The artistic medium: Photography, Digital Art, Oil Painting, vector illustration.]

**Technical Specifications:**
[Camera settings, brush strokes, rendering engine, lighting style.]

**Stylistic Rules:**
[Color palette restrictions, composition guidelines, level of detail.]

**Negative Prompt (Optional):**
[Elements strictly forbidden in this style.]
```

## Tagging Rules

1.  **Medium Tag:** e.g., `Photography`, `Illustration`, `3D`.
2.  **Mood Tag:** If the style forces a mood (e.g., Noir forces `Mood:Dark`), include it.
3.  **Block Tag:** Use `Block:SceneTag` to prevent this style from generating incompatible scenes (e.g., `Block:Space` for a Medieval style).

## Example Entry

```markdown
## Analog Film (Photography, Realistic, Mood:Nostalgic, Block:Sci-Fi)

**Medium/Format:**
35mm Film Photography.

**Technical Specifications:**
Shot on Kodak Portra 400. Visible film grain, soft saturation, slight halation around highlights. Imperfect focus.

**Stylistic Rules:**
Warm, nostalgic color grading. Candid composition. Flash photography aesthetic allowed.

**Negative Prompt:**
Digital, smooth, 3D render, shiny, plastic, octane render.
```
