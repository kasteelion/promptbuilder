# Outfit Definition Standards (Scientific Component Model)

To ensure high-quality, photorealistic generation, we use the **Component-Scientific Standard**. This model breaks an outfit down into its core components (**Top**, **Bottom**, **Footwear**) and strictly defines their physical properties using standardized dimensions.

## The Component-Scientific Schema

Every outfit entry in the `[F]`, `[M]`, and `[H]` sections must follow this nested structure:

```markdown
- **Component Name:** [Brief Description]
  - **[Dimension 1]:** [Value]
  - **[Dimension 2]:** [Value]
```

### Required Dimensions by Component

#### 1. Top (The "Frame")

- **Fit:** (e.g., Oversized, Bodycon, Corset, Tailored)
- **Material:** (e.g., Chunky Knit, Silk Satin, Distressed Denim)
- **Neckline:** (e.g., Turtleneck, Plunging V, Off-Shoulder)
- **Sleeve:** (e.g., Sleeveless, Bell Sleeve, Long tapered)

#### 2. Bottom (The "Anchor")

- **Fit:** (e.g., A-Line, Skinny, Wide-Leg, Pencil)
- **Material:** (e.g., Heavy Wool, Pleated Chiffon, Rigid Denim)
- **Waist:** (e.g., High-waisted, Low-rise, Paperbag)
- **Length:** (e.g., Mini, Midi, Floor-length, Ankle-grazer)

### Advanced Dimensions (For High-Fidelity)

To push photorealism further, consider including these optional keys:

#### 7. Pattern (The "Surface")

- **Definition:** The visual print or color variation.
- **Examples:** Pinstripe, Polka Dot, Gradient, Tartan Plaid, Floral Print, Solid.

#### 8. Trim & Hardware (The "Finish")

- **Definition:** Edges, fasteners, and embellishments.
- **Examples:** Lace trim, Gold buttons, Sequin clusters, Raw hem, Zipper details.

#### 3. One-Piece (Dresses/Jumpsuits)

- **Fit:** (Overall silhouette)
- **Material:** (Primary fabric)
- **Neckline:** (Neck shape)
- **Sleeve:** (Arm coverage)
- **Waist:** (Waist definition)
- **Length:** (Hemline)

---

## Example: High-Standard Entry

```markdown
[F]

- **Top:** Black velvet corset top with lace trim.
  - **Fit:** Structured corset with boning.
  - **Material:** Plush velvet.
  - **Pattern:** Solid (Jet Black).
  - **Trim:** Chantilly lace edging; Silver grommets.
  - **Neckline:** Sweetheart.
  - **Sleeve:** Sleeveless (spaghetti strap).
- **Bottom:** Wide-leg palazzo trousers.
  - **Fit:** Loose flowing.
  - **Material:** Silk satin.
  - **Pattern:** Vintage Art Deco geometric print.
  - **Waist:** High natural waist.
  - **Length:** Floor-length.
- **Footwear:** Pointed toe pumps.
- **Accessories:** Pearl choker, velvet gloves.
```

## Why This Matters

1.  **Precision:** Ensures the AI knows exactly what material the _skirt_ is (silk) vs the _top_ (velvet), preventing material bleeding.
2.  **Completeness:** Identifying "Fit" and "Length" prevents generic output like "a dress" and forces "a floor-length bodycon dress".
3.  **Parsability:** Future tools can easily swap out just the "Material" of the "Bottom" component programmatically.
