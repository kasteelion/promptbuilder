# Outfit Standards: The "Concise Component-based" Outfit Model

To ensure high-quality, photorealistic generation without overwhelming the AI's **Attention Budget**, we use the **Concise Component-based Outfit Model**.

## 1. Core Principles

- **Conciseness:** Every word must contribute to the visual identity.
- **Separation:** Define outfits as a list of components, each focusing on its primary feature (Material, Fit, Color).
- **Avoid Over-specifying:** Don't describe micro-details (e.g., "silver buttons") unless they are a primary feature of the look.

## 2. Schema Structure

Outfits are broken down into **Top**, **Bottom**, **Footwear**, and **Accessories**.

- **Top/Bottom/One-Piece:**
  - **Material:** Primary fabric (e.g., "Heavily distressed denim", "Silk satin").
  - **Fit/Silhouette:** The "Lens" of the item (e.g., "Oversized", "Bodycon").
  - **Pattern:** Only if distinct (e.g., "Pinstripe", "Floral").

## 3. Example: High-Standard Entry

```markdown
- **Top:** Black velvet corset top.
  - **Fit:** Structured with visible boning.
  - **Material:** Plush velvet.
  - **Neckline:** Sweetheart.
- **Bottom:** Wide-leg palazzo trousers.
  - **Fit:** Loose flowing silhouette.
  - **Material:** Silk satin.
  - **Pattern:** Art Deco geometric print.
- **Footwear:** Pointed toe pumps.
- **Accessories:** Pearl choker, velvet gloves.
```

## 4. Why This Model?

1. **Attention Management:** By limiting each component to 2-3 specific keys, we leave room for the AI to render the character and scene correctly.
2. **Material Clarity:** Strictly defining material prevents texture "bleeding" between layers.
3. **Modularity:** UI tools can easily swap individual components while maintaining a consistent style.
