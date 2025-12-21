# Interaction Templates Guide

## Overview

Interaction Templates is a feature that allows you to quickly insert pre-built multi-character interaction descriptions into your prompts. Instead of manually typing out how characters interact, you can select from a library of common interactions that automatically fill in with your selected characters' names.

## How to Use

1. **Add Characters to Your Prompt**
   - Use the character selector to add at least one character (ideally 2+ for interactions)
   - Characters will appear in the selected list

2. **Open the Notes Section**
   - The interaction template selector is located in the "Notes & Interactions" section
   - You'll see a dropdown labeled "Interaction:"

3. **Select a Template**
   - Choose from templates like "Conversation", "Dancing Together", "High Five", etc.
   - Each template has a description shown when you hover over it

4. **Click "Insert"**
   - The template text will be inserted into the notes field
   - Character names will automatically replace placeholders ({char1}, {char2}, etc.)
   - If notes already contain text, the template is added on a new line

## Template Categories

### Two-Character Interactions

Perfect for scenes with 2 characters:

- **Conversation** - Characters talking to each other
- **Dancing Together** - Partner dancing
- **High Five** - Celebratory gesture
- **Walking Together** - Side by side movement
- **Handshake** - Formal greeting
- **Sharing Secret** - Whispering or confiding
- **Working Together** - Collaborative task
- **Laughing Together** - Shared amusement
- **Back to Back** - Defensive or confident pose
- **Pointing At** - One indicating the other
- **Teaching** - One instructing another
- **Helping Up** - Offering assistance
- **Playing Game** - Playful competition
- **Arm Wrestling** - Strength competition
- **Sharing Food** - Offering meal/snack
- **Photo Together** - Posing for camera
- **Fist Bump** - Casual greeting
- **Sitting Together** - Seated side by side
- **Mirror Pose** - Matching positions

### Multi-Character Interactions (3+)

Designed for group scenes with 3 or more characters:

- **Group Discussion (3+)** - Multiple characters in conversation
- **Circle Formation (3+)** - Characters arranged in a circle
- **Team Pose (3+)** - Heroic group pose
- **Chain Reaction (3+)** - Sequential interaction flow

## Examples

### Example 1: Simple Conversation
**Characters:** Maya, Nora  
**Template Selected:** Conversation  
**Result:**
```
Maya engaged in conversation with Nora, both looking at each other with friendly expressions
```

### Example 2: Group Photo
**Characters:** Alice, Bob, Carol  
**Template Selected:** Photo Together  
**Result:**
```
Alice and Bob posing together for a photo, both looking at camera with cheerful expressions
```
(Note: Template uses first 2 characters for 2-character templates)

### Example 3: Team Pose
**Characters:** Hero1, Hero2, Hero3, Hero4  
**Template Selected:** Team Pose (3+)  
**Result:**
```
Hero1, Hero2, and Hero3 in heroic team pose, standing together with confident expressions
```

### Example 4: Multiple Interactions
You can insert multiple templates to build complex scenes:
```
Alice engaged in conversation with Bob, both looking at each other with friendly expressions
Carol and David dancing together, holding hands in dance position, moving in sync with rhythm
```

## Tips & Best Practices

### 1. Match Template to Character Count
- Use 2-character templates when you have 2 characters selected
- Use 3+ templates when you have 3 or more characters
- Templates will use characters in the order they appear in your selection

### 2. Customize After Inserting
- Templates provide a starting point
- Edit the inserted text to add specific details
- Combine with scene descriptions for richer prompts

### 3. Build Complex Scenes
- Insert multiple templates to create layered interactions
- Mix interaction templates with action notes for individual characters
- Combine with scene presets for complete environments

### 4. Character Order Matters
- {char1} = first character in your selection
- {char2} = second character in your selection
- {char3} = third character, and so on
- Reorder characters in your selection if needed before inserting

## Creating Custom Templates

You can create your own custom interaction templates directly in the UI:

### Using the Creator Dialog

1. **Click "+ Create" Button**
   - Located next to the "Insert" button in the Notes & Interactions section

2. **Choose a Template Type**
   - **Blank** - Start from scratch
   - **Two Characters - Custom** - Pre-filled template for 2-character interactions
   - **Three+ Characters - Custom** - Pre-filled template for multi-character interactions

3. **Fill in Template Details**
   - **Template Name:** Give your template a descriptive name (e.g., "Cooking Together")
   - **Description:** Brief description shown in tooltips
   - **Content:** The actual template text with placeholders

4. **Use Placeholders**
   - `{char1}` - First selected character
   - `{char2}` - Second selected character  
   - `{char3}` - Third selected character, and so on

5. **Click "Create Template"**
   - Your template will be added to `utils/interaction_templates.py`
   - Restart the application to see your new template in the dropdown

### Template Content Examples

**Example 1: Two-Character Template**
```
Template Name: Cooking Together
Description: Characters preparing food together
Content: {char1} cooking alongside {char2}, both working on meal preparation with friendly collaboration
```

**Example 2: Multi-Character Template**
```
Template Name: Study Group
Description: Characters studying together
Content: {char1}, {char2}, and {char3} gathered around table studying, sharing notes and discussing concepts
```

**Example 3: Complex Interaction**
```
Template Name: Teaching Moment
Description: One character teaching multiple others
Content: {char1} demonstrating technique to {char2} and {char3}, who watch attentively and take notes
```

### Tips for Creating Templates

1. **Be Descriptive** - Include details about body language, expressions, positioning
2. **Use Consistent Formatting** - Follow the pattern of existing templates
3. **Test Your Placeholders** - Make sure {char1}, {char2}, etc. are properly formatted
4. **Think About Flexibility** - Templates should work with different character combinations
5. **Include Context** - Mention relationships, emotions, or dynamics when relevant

### Editing Existing Templates (Advanced)

Developers can directly edit `utils/interaction_templates.py`:

```python
TEMPLATES = {
    # ... existing templates ...
    
    "Your Template Name": {
        "description": "Brief description",
        "content": "{char1} doing something with {char2}, descriptive details"
    },
}
```

**Important:** After editing the file manually, restart the application to reload templates.

## Technical Details

### How It Works
1. You select a template from the dropdown
2. Click "Insert" button
3. System gets list of selected character names
4. Template placeholders are replaced with actual names using `fill_template()` function
5. Result is inserted into notes text field

### File Location
- Template definitions: `utils/interaction_templates.py`
- Integration: `ui/main_window.py` (the experimental `ui/visual_ui.py` was deprecated and removed)

### Compatibility
- Works in the Classic UI (the Visual Gallery mode has been deprecated and removed)
- Templates are applied at insertion time (editing characters later won't update)
- Can be saved with presets for reusable prompt configurations

## FAQ

**Q: Can I edit the text after inserting?**  
A: Yes! The template is just inserted as regular text. Edit it freely.

**Q: What if I don't have enough characters?**  
A: Templates will use the characters you have. Unused placeholders like {char3} will remain in the text if you only have 2 characters.

**Q: Can I save templates with my presets?**  
A: Yes! When you save a preset, the current notes content (including inserted templates) is saved.

**Q: Can I use templates without characters?**  
A: You'll get a reminder to add characters first. Templates need at least one character to be useful.

**Q: Can I make my own templates?**  
A: Yes! Click the "+ Create" button next to the interaction dropdown to open the template creator dialog. You can also manually edit `utils/interaction_templates.py` for advanced customization.

**Q: Do I need to restart after creating a template?**  
A: Yes, currently you need to restart the application for new templates to appear in the dropdown. This ensures the templates are properly loaded.

## Future Enhancements

Potential improvements being considered:
- Visual template preview
- Category grouping in dropdown
- Template favorites/recent
- Per-character role assignment (leader, follower, etc.)
- Dynamic template suggestions based on character count

---

**Added:** December 11, 2025  
**Version:** 2.1  
**Status:** Stable
