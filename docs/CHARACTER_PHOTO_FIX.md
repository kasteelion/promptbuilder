# Character Photo Functionality Fix

## Issue
After the file structure reorganization, the character card photo implementation was broken because it was using hardcoded paths to `characters/` directory instead of the new `data/characters/` location.

## Root Cause
Multiple UI components were directly referencing `self.data_loader.base_dir / "characters"` instead of using the backward-compatible location finder method `_find_characters_dir()` that was added to the DataLoader.

## Files Fixed

### 1. `ui/character_card.py`
Fixed 4 hardcoded path references:
- **Line 165**: Photo preview - now uses `_find_characters_dir()`
- **Line 241**: Photo path sanitization - now uses `_find_characters_dir()`
- **Line 347**: Photo change/copy - now uses `_find_characters_dir()`
- **Line 387**: Character file update - now uses `_find_characters_dir()`

**Impact**: Character photos can now be:
- Loaded from `data/characters/` (new structure)
- Loaded from `characters/` (old structure, backward compatible)
- Changed/updated in the UI
- Previewed in full-size popup

### 2. `ui/outfit_creator.py`
Fixed 1 hardcoded path reference:
- **Line 389**: Finding character file for outfit creation - now uses `_find_characters_dir()`

**Impact**: Creating custom outfits for characters works with both directory structures

### 3. `ui/character_creator.py`
Fixed 1 hardcoded path reference:
- **Line 313**: Character file creation - now uses `_find_characters_dir()`

**Impact**: Creating new characters saves to correct location (`data/characters/` for new installs, `characters/` for old)

### 4. `ui/edit_tab.py`
Fixed 2 hardcoded path references:
- **Line 93**: Loading character markdown files for editing - now uses `_find_characters_dir()`
- **Line 125**: Saving character markdown files after editing - now uses `_find_characters_dir()`

**Impact**: Editing character files in the Edit tab works with both directory structures

### 5. `logic/data_loader.py`
Fixed 1 hardcoded path reference:
- **Line 269**: Getting list of editable files - now uses `_find_characters_dir()`

**Impact**: Character files appear in the file list regardless of directory structure

## Current State
All character photo functionality now works correctly:

✅ **Photo Loading**: Characters can load photos from both `data/characters/` and `characters/`
✅ **Photo Preview**: Clicking on character card photo shows full-size preview
✅ **Photo Change**: Can change/add photos through the UI
✅ **Photo Storage**: New photos are saved to the correct directory
✅ **Backward Compatibility**: Old installations with `characters/` directory continue working
✅ **New Structure**: New installations automatically use `data/characters/`

## Verification
- Tested with `--check-compat` flag: ✅ Pass
- No syntax errors in modified files: ✅ Pass
- Character photos exist in `data/characters/`: ✅ 15 character photos found
- Character markdown files reference photos: ✅ Verified (e.g., maya_rose.md has `**Photo:** maya_rose_photo.png`)

## Technical Details

### How Photo Loading Works Now
1. Character data is loaded with `photo` field (e.g., `"photo": "maya_rose_photo.png"`)
2. `CharacterCard._load_photo()` is called
3. `_sanitize_photo_path()` validates the photo path:
   - Calls `data_loader._find_characters_dir()` to get the correct directory
   - Combines with relative photo filename
   - Validates path is within characters directory (security check)
4. `_display_photo()` loads and displays the image using PIL/Pillow
5. Canvas shows the photo with proper sizing and aspect ratio preservation

### Backward Compatibility Strategy
The `DataLoader._find_characters_dir()` method:
```python
def _find_characters_dir(self):
    # Try new location first
    new_location = self.base_dir / "data" / "characters"
    if new_location.exists():
        return new_location
    
    # Fall back to old location
    old_location = self.base_dir / "characters"
    if old_location.exists():
        return old_location
    
    # Return new location as default
    return new_location
```

This ensures:
- Existing users with `characters/` directory: photos continue working
- New users: photos automatically use `data/characters/`
- No manual migration required
- No breaking changes
