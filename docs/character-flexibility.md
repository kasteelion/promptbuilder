# Character Flexibility Guide

## Purpose
This guide explains how to structure character descriptions for maximum adaptability across all scenes, outfits, and contexts in the prompt builder.

---

## The Problem

Your characters need to work in vastly different scenarios:
- **Film Noir** (1940s hairstyles, dramatic makeup, period accessories)
- **Sports/Athletic** (hair tied back, minimal/no makeup, performance gear)
- **Formal Events** (elegant updos, refined styling)
- **Sleepwear** (hair down, no makeup)
- **Swimming** (no glasses, waterproof considerations)
- **Fantasy/Renaissance** (period-appropriate styling)
- **Modern Casual** (everyday looks)

**Current issues** found in character files:
1. ❌ Overly specific hairstyles ("high sleek ponytail", "full picked-out afro")
2. ❌ Fixed accessories ("wears thin black rectangular glasses by default")
3. ❌ Pose-specific descriptions ("dynamic ready stance", "buoyant forward-lean")
4. ❌ Context-specific makeup (detailed makeup that doesn't work for sports/swimming)
5. ❌ Rigid styling notes that conflict with outfit requirements

---

## The Solution: Modular Character Design

### **Tier 1: CORE FEATURES** (Unchangeable Physical Traits)

These are the essential, immutable characteristics that define the character visually:

✅ **Skin**: Tone, undertone, natural finish
- Example: "Warm olive skin with golden undertone and natural matte-soft finish"
- NOT: "Skin with bronze glow and highlighter on cheekbones" (too specific to one look)

✅ **Ethnicity/Heritage & Age**: Demographics
- Example: "Korean-American woman, early 20s"
- NOT: "Young K-pop inspired woman" (too stylistic)

✅ **Eyes**: Color and natural gaze quality
- Example: "Warm dark brown eyes with gentle inviting gaze"
- NOT: "Eyes with cat-eye liner and double winged effect" (that's makeup)

✅ **Body Type**: Build, proportions, natural structure
- Example: "Petite athletic build: compact frame, defined shoulders, lean legs"
- NOT: "Athletic build in ready stance for action" (that's a pose)

✅ **Hair**: Color, texture, natural quality (NOT specific styles)
- Example: "Long thick dark brown hair with natural wave and volume"
- NOT: "Long hair in high ponytail with face-framing pieces" (too specific)

---

### **Tier 2: STYLE NOTES** (Preferences, Not Requirements)

These inform outfit choices but are flexible guidelines, not rigid rules:

✅ **Typical Makeup Approach**: General preference when applicable
- Example: "Typically prefers minimal warm-toned makeup when worn"
- NOT: "Terracotta lip, bronze contour, peachy blush" (too specific)

✅ **Fabric Preferences**: What the character gravitates toward
- Example: "Prefers soft jersey knits, flowing rayon, comfortable cotton"
- NOT: "Never wears chiffon or light lace" (too restrictive)

✅ **Color Palette**: Preferred tones for personal style
- Example: "Drawn to rich warm tones—burgundy, deep orange, golden yellow"
- This helps inform outfit choices while allowing flexibility

✅ **Jewelry Preferences**: Metal type and scale when worn
- Example: "Favors gold jewelry, typically simple and understated"
- NOT: "Always wears large gold hoop earrings" (too fixed)

✅ **Personality Baseline**: Expression tendencies
- Example: "Neutral expression: calm and composed; warmth shows in genuine smile with soft eye sparkle"
- NOT: "Confident posture with hand on hip" (too pose-specific)

---

### **Tier 3: AVOID** (Scene/Outfit-Specific Details)

These should NEVER be in the core character description:

❌ **Specific Hairstyles**: These change with outfits
- Bad: "Hair in high ponytail"
- Bad: "Afro picked out with headwrap"
- Good: "Natural afro texture with dense coils and healthy sheen"

❌ **Fixed Accessories**: These vary by outfit
- Bad: "Wears thin black rectangular glasses by default"
- Bad: "Large gold hoop earrings and layered necklaces"
- Good: "Prefers simple gold jewelry when accessorizing"

❌ **Pose Descriptions**: These change with scenes
- Bad: "Dynamic ready stance with forward lean"
- Bad: "Grounded powerful posture with hip sway"
- Good: "Tends toward confident, relaxed bearing"

❌ **Outfit-Specific Makeup**: This changes dramatically
- Bad: "Terracotta lip, soft bronze contour, warm brown liner"
- Bad: "Victory rolls, winged liner, beauty mark"
- Good: "Prefers warm-toned makeup in natural to bold range"

❌ **Context-Dependent Features**: These limit scenes
- Bad: "Skin with highlight on cheekbone and collarbone only"
- Good: "Skin with natural radiance and subtle dimension"

---

## Recommended Character Description Template

```markdown
### [Character Name]
**Photo:** [filename].png

**Appearance:**
[Skin tone] skin with [undertone] and [natural finish quality]. [Hair color and texture] hair with natural [wave/coil/straight quality and shine].
- [Ethnicity/heritage] [age descriptor], [age range]
- [Eye color] eyes with [natural gaze quality - warm/focused/gentle/etc]
- [Body type] build: [key proportions and natural features]
- Neutral expression: [baseline personality]; signature [emotion] shows in [how it manifests naturally]
- Typical makeup approach: [minimal/natural/bold/warm/cool-toned] when worn
- Style preferences: [fabric types, color palette, jewelry metals] for personal styling
- General vibe: [personality traits that influence fashion choices]

**Outfits:**

#### Base
- **Top:** [Description]
- **Bottom:** [Description]
- **Footwear:** [Description]
- **Accessories:** [Description]
- **Hair/Makeup:** [Description]
```

---

## Examples: Before & After

### **Example 1: Priya (Athletic Character)**

❌ **BEFORE** (Too Specific):
```
Long dark brown hair in high sleek ponytail with controlled movement.
Dynamic ready stance with forward lean and spring in step.
Makeup: minimal and warm-toned (soft bronze glow, nude-pink lip, defined brows)
```

✅ **AFTER** (Flexible):
```
Long dark brown hair with natural wave, typically worn in practical styles.
Tends toward energetic, forward-moving bearing when active.
Typical makeup: minimal warm-toned approach when worn; bronze/nude tones preferred.
```

### **Example 2: Nora (Glasses-Wearing Character)**

❌ **BEFORE** (Too Fixed):
```
Deep almond eyes; wears thin black rectangular glasses by default
Long wavy dark-brown hair loosely pinned or tied
Grounded, heel-weighted stance; movement deliberate
```

✅ **AFTER** (Modular):
```
Deep almond eyes with steady observant gaze (sometimes wears glasses)
Long wavy dark-brown hair with natural body and controlled fall
Generally calm and deliberate in movement and bearing
```

### **Example 3: Zara (Afro Texture)**

❌ **BEFORE** (Style-Locked):
```
Full natural afro with dense coily texture—styled in various ways including 
picked-out volume, twist-outs, or adorned with headwraps and accessories
Grounded powerful posture with natural hip sway and deliberate movement
Makeup: warm and bold (burnt sienna or deep berry lip, warm bronze contour, gold shimmer)
```

✅ **AFTER** (Adaptable):
```
Natural afro with dense coily texture and healthy sheen; versatile styling options
Confident bearing with natural ease and presence
Typical makeup: warm and bold when worn; drawn to earth tones and rich berry shades
```

---

## Character Update Priority List

Based on analysis of current characters, here's the update priority:

### **High Priority** (Most Restrictive):
1. **Priya Sharma** - Fixed ponytail, specific pose, detailed makeup
2. **Nora Alvarez** - Glasses always, fixed hair tie, specific stance
3. **Zara Washington** - Very specific afro styling, fixed accessories, pose description
4. **Marisol Rivera** - Bandana as default, specific hair state, stance details
5. **Siofra** - Action-ready stance, very specific braid/ponytail combo

### **Medium Priority** (Some Issues):
6. **Mela Hart** - Playful braids specified, buoyant stance
7. **Yuki Tanaka** - Specific curl style mentioned
8. **Lucia Reyes** - Detailed makeup specification
9. **Hana Park** - Very specific K-beauty makeup details

### **Low Priority** (Relatively Flexible):
10. **Selene Voss** - Mostly good, minor refinements
11. **Astrid Nielsen** - Good structure, minimal changes needed
12. **Fiona O'Sullivan** - Generally flexible
13. **Maya Rose** - Mostly adaptive
14. **Jena Marlowe** - Acceptable flexibility
15. **Amira Khalil** - Special case (hijab is core feature, well-documented)

---

## Implementation Strategy

### **Option 1: Gradual Updates** (Recommended)
- Update high-priority characters first (top 5)
- Test with multiple outfit types (noir, athletic, formal, casual)
- Refine approach based on results
- Update remaining characters in batches

### **Option 2: Template-Based Rebuild**
- Create new modular template
- Rebuild each character file from scratch
- Ensures consistency but more work upfront

### **Option 3: Hybrid Approach**
- Update character creator (DONE)
- Use improved creator for new characters
- Gradually update existing characters as needed

---

## Testing Your Updated Characters

After updating a character, test with these outfit combinations:

1. **Film Noir** outfit + Character → Should work with victory rolls/waves
2. **Athletic/Sport** outfit + Character → Should work with tied-back hair, minimal makeup
3. **Formal/Wedding** outfit + Character → Should work with elegant styling
4. **Sleepwear** outfit + Character → Should work with relaxed/down hair, no makeup
5. **Bikini/Beach** outfit + Character → Should work without glasses, waterproof makeup

If any combination feels forced or conflicting, the character description may still be too specific.

---

## Key Takeaway

**Think of characters as INGREDIENTS, not FINISHED DISHES**

- Core features are your ingredients (flour, eggs, sugar)
- Style notes are your flavor preferences (vanilla vs chocolate)
- The OUTFIT determines the final dish (cake vs cookies vs bread)

Your character description should provide enough information to recognize the character in ANY context, without locking them into one specific look.

---

## Signature Colors

To further distinguish characters while using shared outfits, you can assign a **Signature Color**. This allows a single outfit definition to automatically adapt its color palette to the specific character wearing it.

### 1. Defining a Signature Color
In your character markdown file, add the `**Signature Color:**` field (typically after Gender or Tags). Use a Hex code for precision.

```markdown
### Marisol Rivera
**Tags:** female, athletic, ...
**Gender:** F
**Signature Color:** #FF7F50
...
```

### 2. Using Signature Colors in Outfits
In `outfits_*.md` files, use the following syntax to create a dynamic color slot:

`((default:DEFAULT_COLOR) or (signature))`

**Example:**
```markdown
### Casual - Color Block Chic
Fitted **white v-neck tee**; high-waist **tailored pants** in ((default:rust orange) or (signature)).
```

- **If "Use Signature Color" is UNCHECKED:** The prompt will generate "rust orange".
- **If "Use Signature Color" is CHECKED:** The prompt will generate "#FF7F50" (or whatever color is defined for that character).

This system allows for highly reusable outfit templates that still feel personalized to each character.
