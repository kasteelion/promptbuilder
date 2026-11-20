# Data File Syntax & Conventions

This document outlines the standard file formats, syntax, and norms used within the ssets/data/ directory.

---

## 1. Character Files
**Path:** ssets/data/characters/*.md

Character files are Markdown documents that define the visual identity and metadata of a persona.

### Structure
`markdown
### Character Name
**Photo:** filename.png
**Tags:** comma, separated, tags
**Gender:** F (or M)
**Signature Color:** #HEXCODE

**Appearance:**
- **Body:** ...
- **Face:** ...
- **Hair:** ...
- **Skin:** ...

**Outfits:**
#### Base
- **Top:** ...
- **Bottom:** ...
`

---

## 2. Outfit Libraries
**Path:** ssets/data/outfits/[Category]/[filename].txt

Outfits are stored in plain text files, organized by category folders.

### Structure
`	ext
tags: [Thematic, Tags]

[F]
- **Top:** Description
- **Bottom:** Description

[M]
- **Top:** Description
...
`

### Dynamic Placeholders
- (signature): Injects the character's Signature Color.
- {primary_color}, {secondary_color}, {accent}: Injects colors from the selected team scheme.
- {modifier}: Slot for snippets from modifiers.md.

---

## 3. Global Assets
**Paths:** ssets/data/scenes.md, ssets/data/poses.md, ssets/data/interactions.md

These files use a header-based categorization with bulleted presets.

### Interaction Templates (interactions.md)
Use placeholders for character mapping:
- {char1}, {char2}, etc.

---

## 4. Logical Constraints
**Path:** ssets/config/tag_rules.json, ssets/config/scene_constraints.json

- **tag_rules.json**: Defines tag aliases, groups, and Hub Tags for the randomizer.
- **scene_constraints.json**: Defines allowed/blocked tags for specific scene categories.

---

*Last updated: May 2026*
