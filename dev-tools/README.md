# Development Tools

**Target Audience:** Developers and power users working on content creation, data migration, or system maintenance.

**Important:** These tools are NOT needed for normal app usage. They are for development, bulk operations, and data management tasks.

---

## When to Use These Tools

Use dev-tools when you need to:

- **Migrate data** after schema changes or format updates
- **Generate metadata** in bulk (tags, summaries, vibes)
- **Validate data integrity** before committing changes
- **Add content in bulk** (multiple characters, photos, outfits)
- **Clean up formatting** issues across many files
- **Analyze content** for duplicates or overlaps
- **Restructure directories** when reorganizing the data folder

---

## Tool Categories

### Migrations (`migrations/`)

Scripts for updating data formats when the schema changes.

**When to run:**

- After pulling schema changes from the repository
- When upgrading to a new major version
- When restructuring the data directory

**Tools:**

- `migrate_characters.py` - Update character file format (e.g., adding new fields)
- `migrate_outfits.py` - Update outfit structure (e.g., adding gender variants)
- `migrate_outfits_structure.py` - Reorganize outfit directory hierarchy

**Safety:** Always backup `data/` before running migrations!

---

### Generators (`generators/`)

Tools for automatically creating metadata and content.

**When to use:**

- Adding new characters without manually writing all metadata
- Generating outfit vibe summaries for better randomization
- Auto-tagging content based on patterns

**Tools:**

- `generate_tags.py` - Auto-generate tags for characters/outfits based on content
- `generate_vibe_summaries.py` - Create atmospheric descriptions for outfits

**Example workflow:**

```bash
# After adding new outfit files
python dev-tools/generators/generate_tags.py --target outfits
python dev-tools/generators/generate_vibe_summaries.py
```

---

### Validators (`validators/`)

Data quality and integrity checking tools.

**When to use:**

- Before committing changes to version control
- After running migrations
- When troubleshooting randomizer issues

**Tools:**

- `validate_color_schemes.py` - Ensure color scheme definitions are valid hex codes

**Recommended workflow:**

```bash
# Pre-commit validation
python dev-tools/validators/validate_color_schemes.py
python auditing/quality_audit.py
```

---

### Other Utilities

**Character Management:**

- `add_character_photo.py` - Batch add photos to character definitions
- `add_gender_tags.py` - Automatically add gender tags to characters
- `scan_photos.py` - Scan for character photos and report missing ones

**Outfit Management:**

- `analyze_outfit_overlap.py` - Find duplicate or very similar outfits
- `cleanup_outfit_bolding.py` - Fix markdown formatting issues (bold tags)

---

## Common Workflows

### Adding a New Character with Photo

```bash
# 1. Create character file manually or use template
# 2. Add photo
python dev-tools/add_character_photo.py --character "Character Name" --photo path/to/photo.png

# 3. Generate tags if needed
python dev-tools/generators/generate_tags.py --target characters

# 4. Validate
python auditing/quality_audit.py
```

### Restructuring Outfit Directories

```bash
# 1. Backup first!
cp -r data/outfits data/outfits_backup

# 2. Run migration
python dev-tools/migrate_outfits_structure.py

# 3. Verify integrity
python auditing/verify_integrity.py

# 4. Test in app
python main.py
```

### Cleaning Up Formatting Issues

```bash
# Fix bold tag issues in outfit files
python dev-tools/cleanup_outfit_bolding.py

# Validate changes
git diff data/outfits/
```

### Finding Duplicate Content

```bash
# Check for outfit overlaps
python dev-tools/analyze_outfit_overlap.py

# Review output and manually merge duplicates
```

---

## Archived Scripts

The `scripts/archived/` directory contains legacy migration scripts that may still be useful for reference:

- Old migration patterns
- One-off data transformations
- Experimental tools

**Note:** Archived scripts may not work with current data formats. Review carefully before using.

---

## Safety Guidelines

### Always Backup Before Migrations

```bash
# Create timestamped backup
cp -r data/ data_backup_$(date +%Y%m%d_%H%M%S)/
```

### Test on a Single File First

```bash
# Test migration on one file
python dev-tools/migrate_characters.py --file data/characters/test_character.md --dry-run
```

### Review Changes Before Committing

```bash
# Check what changed
git diff data/

# Review carefully, then commit
git add data/
git commit -m "Applied character migration"
```

### Validate After Every Operation

```bash
# Always run quality checks after bulk operations
python auditing/quality_audit.py
python auditing/verify_integrity.py
```

---

## Directory Structure

```text
dev-tools/
├── migrations/           # Data format migration scripts
├── generators/           # Metadata generation tools
├── validators/           # Data integrity checkers
├── add_character_photo.py
├── add_gender_tags.py
├── analyze_outfit_overlap.py
├── cleanup_outfit_bolding.py
├── scan_photos.py
└── README.md
```

---

## Getting Help

If you're unsure about a tool:

1. Check if it has a `--help` flag: `python dev-tools/tool_name.py --help`
2. Review the source code (most scripts are well-commented)
3. Ask in the project discussions or issues
4. Test with `--dry-run` flag if available

**Remember:** When in doubt, backup first!
