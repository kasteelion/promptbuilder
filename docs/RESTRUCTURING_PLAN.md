# File Structure Restructuring Plan

## Current Issues

1. **Mixed Content in Root**: Data files (`.md`), config files, code files, and docs all in root
2. **No Package Structure**: Code not in a proper Python package
3. **User Data in Repo**: `preferences.json` and `promptbuilder_debug.log` shouldn't be in git
4. **No Separation**: Data, docs, and code not properly separated
5. **Test Files Scattered**: `test_features.py` in root instead of `tests/`

## Standard Python Project Structure

```
promptbuilder/                    # Project root
├── src/                          # Source code (NEW)
│   └── promptbuilder/            # Main package
│       ├── __init__.py
│       ├── __main__.py           # Entry point for `python -m promptbuilder`
│       ├── core/                 # Core business logic
│       ├── logic/                # Data loading and processing
│       ├── ui/                   # User interface
│       ├── themes/               # Theme management
│       └── utils/                # Utilities
├── data/                         # Default data files (NEW)
│   ├── base_prompts.md
│   ├── outfits.md
│   ├── poses.md
│   ├── scenes.md
│   └── characters/
│       └── *.md
├── docs/                         # Documentation (NEW)
│   ├── README.md
│   ├── QUICK_REFERENCE.md
│   ├── COMPATIBILITY.md
│   ├── MODULARITY_REFACTORING.md
│   ├── VISUAL_UI_GUIDE.md
│   └── VISUAL_UI_IMPLEMENTATION.md
├── tests/                        # Test files (NEW)
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_parsers.py
│   ├── test_validation.py
│   └── fixtures/
│       └── sample_data.md
├── .github/                      # CI/CD (NEW)
│   └── workflows/
│       └── test.yml
├── main.py                       # Simple entry point (keep for compatibility)
├── pyproject.toml                # Modern Python packaging (NEW)
├── setup.py                      # Legacy support (NEW)
├── requirements.txt              # Dependencies
├── requirements-dev.txt          # Dev dependencies (NEW)
├── .gitignore                    # Updated
├── LICENSE                       # License file (NEW)
└── README.md                     # Main readme (move to root)
```

## Migration Steps

### Phase 1: Create Package Structure (No Breaking Changes)
1. Create `src/promptbuilder/` directory
2. Move code modules while maintaining imports
3. Add `__init__.py` files
4. Update import paths gradually

### Phase 2: Organize Data Files
1. Create `data/` directory
2. Move `.md` files to `data/`
3. Update `DataLoader` to check both old and new locations (backward compatible)
4. Move `characters/` to `data/characters/`

### Phase 3: Organize Documentation
1. Create `docs/` directory
2. Move documentation `.md` files
3. Keep main `README.md` in root (standard)
4. Add links from root README to docs

### Phase 4: Organize Tests
1. Create `tests/` structure
2. Move `test_features.py` to `tests/`
3. Add pytest configuration
4. Create test fixtures

### Phase 5: Add Modern Packaging
1. Create `pyproject.toml`
2. Create `setup.py` for legacy support
3. Add `requirements-dev.txt`
4. Update `.gitignore`

### Phase 6: User Data Directory
1. Update preferences to use app data directory
2. Update debug logging to use app data directory
3. Add migration logic for existing users

## Implementation Priority

### High Priority (Do First)
- ✅ Create directory structure
- [ ] Move data files to `data/`
- [ ] Update `.gitignore` for user data
- [ ] Move docs to `docs/`
- [ ] Create `pyproject.toml`

### Medium Priority
- [ ] Create `src/promptbuilder/` package
- [ ] Update imports
- [ ] Move tests to `tests/`
- [ ] Add `__main__.py` for module execution

### Low Priority (Polish)
- [ ] Add LICENSE file
- [ ] Create `requirements-dev.txt`
- [ ] Set up GitHub Actions
- [ ] Add pre-commit hooks

## Backward Compatibility

To ensure no breaking changes for existing users:

1. **DataLoader** will check multiple locations:
   ```python
   # Check new location first, fall back to old
   if (self.base_dir / "data" / "characters").exists():
       chars_dir = self.base_dir / "data" / "characters"
   elif (self.base_dir / "characters").exists():
       chars_dir = self.base_dir / "characters"
   ```

2. **Keep main.py** as entry point for backward compatibility

3. **Gradual migration** of user data with automatic detection

## Benefits

1. **Clear Organization**: Code, data, docs, and tests clearly separated
2. **Standard Structure**: Follows Python packaging best practices
3. **Easier Testing**: Proper test directory structure
4. **Better Distribution**: Can be installed with `pip install -e .`
5. **Cleaner Git**: User data excluded from repository
6. **Professional**: Industry-standard project layout

## Files to Move

### To `data/`:
- base_prompts.md
- outfits.md
- poses.md
- scenes.md
- characters/ (directory)
- characters.md (legacy, keep for backward compat)
- professional_woman.md (example)

### To `docs/`:
- QUICK_REFERENCE.md
- COMPATIBILITY.md
- MODULARITY_REFACTORING.md
- VISUAL_UI_GUIDE.md
- VISUAL_UI_IMPLEMENTATION.md

### To `tests/`:
- test_features.py → tests/test_features.py

### To `.gitignore`:
- preferences.json
- promptbuilder_debug.log
- *.log
- presets/ (user-generated)

### Stay in Root:
- README.md (main documentation)
- main.py (entry point)
- requirements.txt
- .gitignore
- LICENSE (to add)

## Next Steps

1. Review and approve this plan
2. Implement Phase 1 (create structure)
3. Implement Phase 2 (move data files)
4. Test thoroughly
5. Continue with remaining phases
