# AI Studio Browser Automation

Browser automation tools for Google AI Studio image generation using **Playwright**.

## Modules

### `ai_studio_client.py`

Reusable browser automation client for AI image generation.

**Features:**

- Persistent login (saves session)
- Handles `data:` and `blob:` URI image extraction
- Auto-scrolling for lazy-loaded images
- Progress callbacks
- Configurable output directory

**Usage:**

```python
from automation.ai_studio_client import AIStudioClient
import asyncio

async def main():
    client = AIStudioClient(
        output_dir="my_images",
        user_data_dir=".config/chrome_profile"
    )

    prompts = [
        "Generate an image of: a sunset over mountains",
        "Generate an image of: a cyberpunk city at night"
    ]

    results = await client.generate_images(prompts)

    for prompt, image_path in results:
        if image_path:
            print(f"✓ {prompt} -> {image_path}")
        else:
            print(f"✗ {prompt} -> Failed")

asyncio.run(main())
```

**Simple wrapper:**

```python
from automation.ai_studio_client import generate_images_simple
import asyncio

prompts = ["Generate an image of: a cat wearing a hat"]
results = asyncio.run(generate_images_simple(prompts))
```

---

### `automate_generation.py`

Main automation script that combines prompt generation with browser automation.

**Usage:**

```bash
# Generate images with browser automation
python automation/automate_generation.py --count 10

# Generate prompts only (no browser)
python automation/automate_generation.py --prompts-only --count 20

# Custom outfit matching probability (0.0-1.0)
# Higher values = more likely to use character's base outfits
python automation/automate_generation.py --count 5 --match-outfits-prob 0.5
```

**How it works:**

- Integrates with `PromptRandomizer` from the core app
- Generates thematically coherent prompts using Monte Carlo selection
- `--match-outfits-prob` controls whether to use character base outfits vs random outfits
- Automatically submits prompts to AI Studio and downloads generated images

---

### `bulk_generator.py`

Bulk prompt generation with batch processing.

---

## Integration Examples

### Use in your own script:

```python
from automation.ai_studio_client import AIStudioClient
import asyncio

async def generate_custom_images():
    client = AIStudioClient(output_dir="custom_output")

    # Your custom prompts
    my_prompts = [
        "A detailed portrait of a warrior",
        "A serene landscape with mountains"
    ]

    # Optional progress callback
    def on_progress(current, total, message):
        print(f"[{current}/{total}] {message}")

    results = await client.generate_images(
        my_prompts,
        progress_callback=on_progress
    )

    return results

# Run it
results = asyncio.run(generate_custom_images())
```

### Integrate with other tools:

```python
# Example: Generate images from a CSV file
import csv
import asyncio
from automation.ai_studio_client import generate_images_simple

with open('prompts.csv', 'r') as f:
    reader = csv.reader(f)
    prompts = [f"Generate an image of: {row[0]}" for row in reader]

results = asyncio.run(generate_images_simple(prompts, output_dir="csv_images"))
```

---

## Configuration

### AIStudioClient Parameters

- **`output_dir`** - Where to save images (default: `"generated_images"`)
- **`user_data_dir`** - Browser profile directory for persistent login (default: `".config/chrome_profile"`)
- **`headless`** - Run browser in headless mode (default: `False`)
- **`viewport`** - Browser window size (default: `{'width': 1280, 'height': 800}`)

---

## Requirements

- `playwright` - Browser automation
- `asyncio` - Async support

Install:

```bash
pip install playwright
playwright install chromium
```

---

## Output Structure

Generated content is organized as follows:

```text
generated_images/
├── prompt_001.txt       # Full prompt text
├── prompt_001.png       # Generated image
├── prompt_002.txt
├── prompt_002.png
└── ...
```

Each `.txt` file contains:

- Full prompt text
- Metadata (character, outfit, scene, style)
- Coherence score and breakdown

---

## Troubleshooting

### Login Issues

- **First run requires manual login** - browser will open, log in to Google AI Studio
- Session is saved in `.config/chrome_profile/` for subsequent runs
- If login fails repeatedly, delete `.config/chrome_profile/` and try again

### Image Extraction Failures

- Script uses auto-scrolling to trigger lazy-loaded images
- Polls for image size to detect when generation completes
- Falls back to screenshot if DOM extraction fails
- Check console output for detailed error messages

### Browser Profile Issues

- Profile corruption: Delete `.config/chrome_profile/` directory
- Permission errors: Ensure directory is writable
- Multiple instances: Close all Chrome/Chromium processes before running

### Common Errors

- **"Browser not found"**: Run `playwright install chromium`
- **"Timeout waiting for image"**: Increase wait times in script or check network connection
- **"Failed to extract image"**: AI Studio UI may have changed, check for script updates

---

## Notes

- First run requires manual login to Google AI Studio
- Subsequent runs use saved session from `.config/chrome_profile/`
- Images are extracted from DOM (handles `data:` and `blob:` URIs)
- Fallback screenshot if extraction fails
- Works with Google AI Studio's Gemini 2.5 Flash Image model
- Auto-scrolling ensures lazy-loaded images are fully rendered
