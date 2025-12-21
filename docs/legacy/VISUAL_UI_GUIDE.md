# Visual Character Gallery - (Deprecated / Archived)

> DEPRECATED — The Visual Gallery UI was removed from the codebase on December 12, 2025. This guide is preserved as an archive of the experimental feature.

## Overview (archived)

The Visual Character Gallery was an experimental UI mode that provided a visual, card-based approach to building prompts. Instead of dropdown lists, characters were displayed as photo-backed cards in a side panel.

## Features

### 📸 Character Photos
- Attach photos to your characters
- Visual reference for each character
- Click on any character card photo to add/change it
- Photos are automatically resized and centered

### 🎴 Card-Based Interface
- Each character shown as a visual card
- Cards display: Photo, Name, Quick Description, Add Button
- Cleaner, more intuitive character selection
- Faster visual scanning

### 🔍 Search & Filter
- Search box at top of gallery
- Instantly filter characters by name
- Easier to find characters in large collections

### 📐 Three-Panel Layout
- **Left Panel:** Character Gallery (scrollable)
- **Middle Panel:** Settings (scene, notes, selected characters)
- **Right Panel:** Preview (same as classic mode)

## How to Use

### Enabling Visual Mode

1. Go to **View → UI Mode → Visual Gallery (Experimental)**
2. Restart the application
3. The new interface will load automatically

### Switching Back

1. Go to **View → UI Mode → Classic (Current)**
2. Restart the application
3. Returns to the familiar interface

## Adding Photos to Characters

### Method 1: Click on Character Card
1. In Visual Gallery mode, find the character
2. Click on the photo placeholder (📷)
3. Select an image file (JPG, PNG, GIF, BMP)
4. Photo is automatically copied to `characters/` folder
5. Character file is updated with photo reference

### Method 2: Manual File Addition
1. Add a photo to the `characters/` folder
2. Edit the character's `.md` file
3. Add after the character name:
   ```markdown
   ### Character Name
   **Photo:** filename.jpg
   **Appearance:** ...
   ```

### Supported Image Formats
- JPEG/JPG
- PNG
- GIF
- BMP

### Image Requirements
- No minimum size (images are auto-resized)
- Recommended: Square images (100x100 or larger)
- Photos are displayed at 100x100 pixels

## Character File Format

With photos, your character files look like this:

```markdown
### Maya Rose
**Photo:** maya_rose_photo.jpg
**Appearance:** 
Light skin tone with natural freckles and wavy auburn hair.
- Young adult, early-mid 20s
- Hazel eyes with cheerful expression
- Athletic build with confident posture
- Makeup: Minimal, natural glow
- Fabrics: Comfortable, casual styles
- Accessories: Simple jewelry, often a small necklace

**Outfits:**

#### Base
- **Top:** Soft cotton tee in pastel colors
- **Bottom:** Well-fitted jeans or casual pants
- **Footwear:** Canvas sneakers or ankle boots
- **Accessories:** Small hoop earrings, casual watch
- **Hair/Makeup:** Hair naturally wavy, light mascara
```

## Optional: Install Pillow for Image Support

The visual UI works without any additional packages, but character photos require Pillow (PIL):

```bash
pip install Pillow
```

### Without Pillow:
- Character cards display placeholder text
- All other features work normally
- You can still add photos (they just won't display)

### With Pillow:
- Photos display in character cards
- Automatic image resizing
- Better visual experience

## Tips & Tricks

### Organizing Characters
- Use descriptive photo filenames: `character_casual.jpg`, `character_formal.jpg`
- Photos are stored in `characters/` folder
- One photo per character (can be changed anytime)

### Performance
- Visual mode works well with 50+ characters
- Search/filter keeps interface responsive
- Photos are cached after first load

### Best Practices
1. Use clear, well-lit photos
2. Square aspect ratio works best
3. Keep file sizes reasonable (<1MB)
4. Use consistent naming: `charactername_photo.jpg`

## Workflow Comparison

### Classic Mode
1. Select character from dropdown
2. Click "Add to Prompt"
3. Character appears in scrollable list
4. Configure outfit, pose for each

### Visual Mode
1. Browse visual gallery
2. Click "Add" on character card
3. Character appears in selected list
4. Configure settings in middle panel

## Known Limitations

### Experimental Status
- First iteration of visual UI
- Layout may change in future versions
- Some advanced features from classic mode not yet available

### Current Limitations
- Cannot configure outfits/poses directly in gallery view
- Selected characters shown as simple list (not full cards)
- Drag-and-drop reordering not yet implemented
- No visual preview of outfits

### Planned Improvements
- Full character card view for selected characters
- Outfit thumbnails
- Drag-and-drop reordering
- Inline outfit/pose selection
- Photo gallery view for outfits

## Troubleshooting

### Photos Not Displaying
1. Check if Pillow is installed: `pip install Pillow`
2. Verify photo file exists in `characters/` folder
3. Check filename matches what's in character `.md` file
4. Try a different image format (PNG instead of JPG)

### Search Not Working
- Restart the application
- Characters must be loaded first (check characters folder)

### UI Not Switching
- Make sure to restart the application after changing mode
- Check preferences.json to see saved mode
- Try deleting preferences.json to reset

### Photos Taking Up Space
- Each photo is copied to characters folder
- You can delete original files after import
- Photos are typically 10-50KB each (after resize)

## Future Development

This is an **experimental feature** - your feedback shapes its future!

### Possible Enhancements
- 📱 Mobile-friendly responsive layout
- 🎨 Outfit preview cards
- 🖼️ Multiple photos per character
- 🏷️ Character tags/categories
- ⭐ Favorites system
- 📊 Usage statistics
- 🎭 Pose preview images
- 🎬 Scene thumbnails

### Send Feedback
If you have ideas or find issues:
1. Note which features you use most
2. What's confusing or unclear
3. What would make it better
4. Screenshot any errors

## Comparison Matrix

| Feature | Classic Mode | Visual Mode |
|---------|--------------|-------------|
| Character Selection | Dropdown | Visual Cards |
| Photos | Not supported | Full support |
| Search | No | Yes |
| Quick Add | 2 clicks | 1 click |
| Outfit Config | Inline | Separate panel |
| Pose Config | Inline | Separate panel |
| Screen Space | Compact | More spacious |
| Best For | Power users | Visual browsing |

## Conclusion

The Visual Character Gallery offers a more modern, visual approach to prompt building. While experimental, it provides a fresh perspective on character selection with the added benefit of photo support.

Try both modes and use whichever fits your workflow better!

---

**Current Version:** Experimental (December 2025)  
**Requires:** Python 3.8+, Optional: Pillow for photos  
**Status:** Beta - Feedback Welcome!
