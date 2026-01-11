# AI Studio Browser Automation

Browser automation tools for Google AI Studio image generation.

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

# Custom outfit matching probability
python automation/automate_generation.py --count 5 --match-outfits-prob 0.5
```

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

## Notes

- First run requires manual login
- Subsequent runs use saved session
- Images are extracted from DOM (handles data: and blob: URIs)
- Fallback screenshot if extraction fails
- Works with Google AI Studio's Gemini 2.5 Flash Image model
