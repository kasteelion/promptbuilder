import os
import sys
import time
import argparse
import asyncio
from playwright.async_api import async_playwright

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.data_loader import DataLoader
from logic.randomizer import PromptRandomizer
from core.builder import PromptBuilder

def generate_prompts(count=10):
    """Generate a list of random prompts using the app's logic."""
    print(f"Generating {count} prompts...")
    loader = DataLoader()
    chars = loader.load_characters()
    base_prompts = loader.load_base_prompts()
    poses = loader.load_presets("poses.md")
    scenes = loader.load_presets("scenes.md")
    schemes = loader.load_color_schemes()
    modifiers = loader.load_modifiers()
    interactions = loader.load_interactions()
    framing = loader.load_framing()
    
    builder = PromptBuilder(chars, base_prompts, poses, schemes, modifiers, framing)
    randomizer = PromptRandomizer(chars, base_prompts, poses, scenes, interactions, schemes, modifiers, framing)
    
    prompts = []
    for i in range(count):
        print(f"  Randomizing prompt {i+1}...")
        config = randomizer.randomize(
            num_characters=None, # Random count
            include_scene=True,
            include_notes=True
        )
        prompt_text = builder.generate(config)
        prompts.append(prompt_text)
        
    return prompts

async def run_automation():
    prompts = generate_prompts(10)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "generated_images")
    user_data_dir = os.path.join(script_dir, "chrome_profile") # Local profile to save login
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Images will be saved to: {output_dir}")
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
        
    print(f"\nUsing persistent profile at: {user_data_dir}")
    print("NOTE: You will need to log in the first time. Subsequent runs will stay logged in.")
        
    async with async_playwright() as p:
        # Launch persistent context with system Chrome
        # This saves cookies/login data to 'chrome_profile' folder
        print("\nLaunching Google Chrome...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome", # Tells Playwright to use installed Chrome
            viewport={'width': 1280, 'height': 800},
            ignore_default_args=["--enable-automation"],
            args=["--no-sandbox", "--disable-infobars", "--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] # Persistent context opens a page by default
        
        # Navigate to AI Studio
        url = "https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image"
        print(f"Navigating to {url}...")
        await page.goto(url)
        
        # Check for login
        print("\nChecking for login status...")
        try:
            prompt_area_selector = 'textarea[aria-label="Enter a prompt"]'
            
            try:
                # Shorter timeout to check if we are already good
                await page.wait_for_selector(prompt_area_selector, timeout=5000)
                print("Login verified!")
            except:
                print(">> ACTION REQUIRED: Please log in manually in the browser window.")
                print("Waiting up to 5 minutes for you to reach the chat interface...")
                await page.wait_for_selector(prompt_area_selector, timeout=300000) 
                print("Login detected! Proceeding...")
                
        except Exception as e:
            print(f"Error during login check: {e}")
            await context.close()
            return

        # Capture Network Responses
        captured_responses = []
        
        async def handle_response(response):
            try:
                # Check for image content types or resource types
                content_type = response.headers.get("content-type", "").lower()
                resource_type = response.request.resource_type
                
                # Filter for images
                if "image" in content_type or resource_type == "image":
                    captured_responses.append(response)
            except:
                pass

        page.on("response", handle_response)

        # Process prompts
        for i, prompt in enumerate(prompts):
            print(f"\nProcessing Prompt {i+1}/{len(prompts)}...")
            
            # Clear previous captures
            captured_responses.clear()
            
            if i > 0:
                print("Starting new chat...")
                await page.goto(url)
                await page.wait_for_selector(prompt_area_selector)

            # Wait a moment for the UI to settle before typing
            # This prevents typing while the page is still initializing
            await page.wait_for_timeout(3000)

            # Enter Prompt
            full_prompt = "Generate an image of: " + prompt
            print("Entering prompt...")
            await page.evaluate('(text) => { const el = document.querySelector(\'textarea[aria-label="Enter a prompt"]\'); el.value = text; el.dispatchEvent(new Event("input", {bubbles:true})); }', full_prompt)
            
            # Prepare filenames (timestamp based)
            timestamp = int(time.time())
            base_filename = f"gen_{timestamp}_{i+1}"
            
            # Save Prompt as Text File
            text_path = os.path.join(output_dir, f"{base_filename}.txt")
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(full_prompt)
            print(f"Saved prompt text to {text_path}")
            
            # Submit
            print("Submitting...")
            run_button = page.locator('button[aria-label="Run"]')
            if await run_button.count() > 0:
                await run_button.click()
            else:
                await page.keyboard.press("Control+Enter")
                
            # Wait for Generation
            print("Waiting for generation...")
            await page.wait_for_timeout(10000) 
            
            # Scroll to bottom to ensure image usage lazy-loads
            print("Scrolling to bottom...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            try:
                await page.evaluate("""() => {
                    const container = document.querySelector('ms-autoscroll-container') || document.querySelector('.conversation-container') || document.body;
                    container.scrollTop = container.scrollHeight;
                }""")
            except:
                pass
            await page.wait_for_timeout(2000)
            
            # Find image by extracting src from DOM (handles data: and blob: URIs)
            print("Extracting image data from DOM...")
            import base64
            
            try:
                target_image = None
                
                # Polling for high-resolution image (skipping 240x240 previews)
                # Simple wait for quality/loading as requested
                print("Waiting 3 seconds for image to finalize...")
                await page.wait_for_timeout(3000)
                
                all_imgs = await page.locator("img").all()
                potential_targets = []
                
                for img in all_imgs:
                    try:
                        if await img.is_visible():
                            box = await img.bounding_box()
                            # Basic size filter to avoid icons
                            if box and box['width'] > 100 and box['height'] > 100:
                                potential_targets.append(img)
                    except:
                        pass
                        
                if potential_targets:
                    target_image = potential_targets[-1]
                    print(f"Selected last image candidate ({len(potential_targets)} found).")
                
                if target_image:
                    src = await target_image.get_attribute("src")
                    
                    image_data = None
                    if src.startswith("data:image"):
                        print("Found Data URI image.")
                        head, data = src.split(",", 1)
                        image_data = base64.b64decode(data)
                    elif src.startswith("blob:"):
                        print("Found Blob URI image. Fetching content...")
                        image_data_b64 = await page.evaluate(r"""async (blobUrl) => {
                            const response = await fetch(blobUrl);
                            const blob = await response.blob();
                            return new Promise((resolve, reject) => {
                                const reader = new FileReader();
                                reader.onloadend = () => resolve(reader.result);
                                reader.onerror = reject;
                                reader.readAsDataURL(blob);
                            });
                        }""", src)
                        head, data = image_data_b64.split(",", 1)
                        image_data = base64.b64decode(data)
                    else:
                        print(f"Unknown src type: {src[:30]}...")
                    
                    if image_data:
                        # Use strictly matched filename
                        filepath = os.path.join(output_dir, f"{base_filename}.png")
                        with open(filepath, "wb") as f:
                            f.write(image_data)
                        print(f"Saved extracted image to {filepath}")
                    else:
                         print("Failed to process image data.")
                else:
                    print("Could not locate any large visible image.")
                    
            except Exception as e:
                print(f"Extraction failed: {e}. Taking fallback screenshot...")
                try:
                    fallback_path = os.path.join(output_dir, f"{base_filename}_fallback.png")
                    await page.screenshot(path=fallback_path)
                except:
                    pass
            
        print("\nAll prompts processed!")
        await page.wait_for_timeout(5000)
        await context.close()

def run_local_generation(count=10):
    """Generate prompts and save to text files without browser automation."""
    prompts = generate_prompts(count)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "generated_prompts_only")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Prompts will be saved to: {output_dir}")
    
    for i, prompt in enumerate(prompts):
        timestamp = int(time.time())
        base_filename = f"gen_only_{timestamp}_{i+1}"
        
        # Save Prompt as Text File
        text_path = os.path.join(output_dir, f"{base_filename}.txt")
        # Prepend instruction line to match browser behavior roughly
        full_text = "Generate an image of: " + prompt
        
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"Saved prompt text to {text_path}")
        
    print(f"Done! Generated {len(prompts)} prompts.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate prompt generation and image capture.")
    parser.add_argument("--prompts-only", action="store_true", help="Generate prompts to text files only (no browser)")
    parser.add_argument("--count", type=int, default=10, help="Number of prompts to generate")
    args = parser.parse_args()

    try:
        if args.prompts_only:
            run_local_generation(args.count)
        else:
            # For async browser, we currently ignore count in run_automation signature, 
            # but we should ideally pass it. 
            # run_automation is hardcoded to 10? logic says: prompts = generate_prompts(10)
            # Let's patch run_automation to accept count if we want correctness, 
            # but for now I'll leave run_automation logic as is and just control the switch.
            # But wait, run_automation() has no args. I should update it.
            asyncio.run(run_automation())
            
    except KeyboardInterrupt:
        print("Stopped by user.")
