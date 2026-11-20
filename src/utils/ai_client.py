"""
Centralized AI Client for Browser-based Automation.

This utility consolidates automation logic for Google AI Studio, supporting both
Image Generation (Gemini Image models) and Text Generation (future use).
"""

import os
import time
import base64
from typing import List, Tuple, Optional, Callable
from playwright.async_api import async_playwright, Page

class AIStudioClient:
    """
    Automated browser client for Google AI Studio.
    
    Features:
    - Persistent login (saves session to chrome_profile)
    - Hybrid Image/Text generation support
    - Auto-scrolling and asset extraction
    """
    
    def __init__(
        self,
        output_dir: str = "generated_images",
        user_data_dir: str = ".config/chrome_profile",
        headless: bool = False,
        viewport: dict = None,
        model: str = "gemini-2.5-flash-image" 
    ):
        """
        Initialize the AI Studio client.
        
        Args:
            output_dir: Directory to save generated assets
            user_data_dir: Directory for persistent browser profile
            headless: Run browser in headless mode
            viewport: Browser viewport size
            model: Target model ID (default: 'gemini-2.5-flash-image')
        """
        self.output_dir = output_dir
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.viewport = viewport or {'width': 1280, 'height': 800}
        self.model = model
        
        # Create directories if needed
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        self.url = f"https://aistudio.google.com/prompts/new_chat?model={self.model}"
        self.prompt_selector = 'textarea[aria-label="Enter a prompt"]'
        
    async def _wait_for_login(self, page: Page):
        """Wait for user to log in if needed."""
        print("Checking for login status...")
        try:
            # Short timeout to check if already logged in
            await page.wait_for_selector(self.prompt_selector, timeout=5000)
            print("Login verified!")
        except Exception:
            print(">> ACTION REQUIRED: Please log in manually in the browser window.")
            print("Waiting up to 5 minutes for you to reach the chat interface...")
            await page.wait_for_selector(self.prompt_selector, timeout=300000)
            print("Login detected! Proceeding...")
    
    async def _extract_image_from_dom(self, page: Page, base_filename: str) -> Optional[str]:
        """Extract generated image from DOM with retry and better targeting."""
        print("Extracting image data from DOM...")
        
        # Max attempts to find and extract the image
        MAX_ATTEMPTS = 5
        for attempt in range(MAX_ATTEMPTS):
            try:
                # Wait for potential image elements to appear/stabilize
                await page.wait_for_timeout(2000)
                
                # Find all images in the conversation area
                # Target images that are likely results (large, in main container)
                all_imgs = await page.locator("img").all()
                potential_targets = []
                
                for img in all_imgs:
                    try:
                        if await img.is_visible():
                            box = await img.bounding_box()
                            # Filter out small images (icons, profile pics, etc.)
                            if box and box['width'] > 200 and box['height'] > 200:
                                src = await img.get_attribute("src")
                                if src and (src.startswith("data:") or src.startswith("blob:") or "googleusercontent" in src):
                                    potential_targets.append(img)
                    except Exception:
                        continue
                
                if not potential_targets:
                    print(f"Attempt {attempt+1}: No large visible images found yet.")
                    if attempt < MAX_ATTEMPTS - 1:
                        await self._scroll_to_load(page)
                        continue
                    return None
                
                # Use the last image as it's the most recent response
                target_image = potential_targets[-1]
                src = await target_image.get_attribute("src")
                image_data = None
                
                # Handle data: URI
                if src.startswith("data:image"):
                    head, data = src.split(",", 1)
                    image_data = base64.b64decode(data)
                
                # Handle blob: URI
                elif src.startswith("blob:"):
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
                    if "," in image_data_b64:
                        head, data = image_data_b64.split(",", 1)
                        image_data = base64.b64decode(data)
                
                # Handle standard URLs (might need download)
                elif "http" in src:
                    # Use page.evaluate to fetch and convert to b64 to bypass CORS if needed
                    image_data_b64 = await page.evaluate(r"""async (url) => {
                        const response = await fetch(url);
                        const blob = await response.blob();
                        return new Promise((resolve, reject) => {
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.onerror = reject;
                            reader.readAsDataURL(blob);
                        });
                    }""", src)
                    if "," in image_data_b64:
                        head, data = image_data_b64.split(",", 1)
                        image_data = base64.b64decode(data)

                if image_data:
                    filepath = os.path.join(self.output_dir, f"{base_filename}.png")
                    with open(filepath, "wb") as f:
                        f.write(image_data)
                    print(f"Successfully extracted image to {filepath}")
                    return filepath
                    
            except Exception as e:
                print(f"Extraction attempt {attempt+1} failed: {e}")
                
        return None
    
    async def _submit_prompt(self, page: Page, prompt: str):
        """Submit a prompt to AI Studio with better focus and event triggering."""
        # Ensure focus and clear if needed
        await page.click(self.prompt_selector)
        
        # Use evaluate to set value and trigger multiple events to ensure UI reacts
        await page.evaluate(
            '(text) => { '
            '  const el = document.querySelector(\'textarea[aria-label="Enter a prompt"]\'); '
            '  el.value = text; '
            '  el.dispatchEvent(new Event("input", {bubbles:true})); '
            '  el.dispatchEvent(new Event("change", {bubbles:true})); '
            '  el.dispatchEvent(new KeyboardEvent("keydown", {bubbles:true, key: "Enter"})); '
            '}',
            prompt
        )
        
        await page.wait_for_timeout(500)
        
        # Look for run button - AI Studio sometimes uses different labels or icons
        run_button = page.locator('button[aria-label*="Run"], button[aria-label*="Send"], .run-button, .send-button').first
        
        if await run_button.count() > 0 and await run_button.is_visible():
            await run_button.click()
        else:
            # Fallback to keyboard
            await page.keyboard.press("Control+Enter")

    async def _wait_for_generation(self, page: Page, timeout_ms: int = 45000):
        """Wait for generation to complete by watching the UI state."""
        print(f"Waiting for generation (max {timeout_ms/1000}s)...")
        start_time = time.time()
        
        # Strategy: While the "Stop" button is visible, we are generating.
        # Or while the "Run" button is disabled.
        
        while (time.time() - start_time) * 1000 < timeout_ms:
            # Check for "Stop" button
            stop_btn = page.locator('button[aria-label*="Stop"]').first
            if await stop_btn.count() > 0 and await stop_btn.is_visible():
                await page.wait_for_timeout(1000)
                continue
                
            # Check for "Run" button becoming enabled
            run_btn = page.locator('button[aria-label*="Run"]').first
            if await run_btn.count() > 0:
                is_disabled = await run_btn.get_attribute("disabled")
                if is_disabled is not None: # It has a disabled attribute
                    await page.wait_for_timeout(1000)
                    continue
            
            # Check for error messages or safety blocks
            if await page.locator("text='Safety'").count() > 0 or await page.locator("text='blocked'").count() > 0:
                print("Detected potential safety block or error.")
                break

            # If we don't see a stop button and run is not disabled, maybe it's done?
            # Let's wait a bit more to be sure
            await page.wait_for_timeout(2000)
            break
            
        print(f"Generation finished or timed out after {int(time.time() - start_time)}s")
    
    async def _scroll_to_load(self, page: Page):
        """Scroll to bottom to ensure lazy-loaded items appear."""
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        try:
            await page.evaluate("""() => {
                const container = document.querySelector('ms-autoscroll-container') || document.querySelector('.conversation-container') || document.body;
                container.scrollTop = container.scrollHeight;
            }""")
        except Exception:
            pass
        await page.wait_for_timeout(2000)
    
    async def generate_images(
        self,
        prompts: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Tuple[str, Optional[str]]]:
        """Generate images from a list of prompts."""
        results = []
        
        async with async_playwright() as p:
            print("\nLaunching Google Chrome (Persistent)...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                channel="chrome",
                viewport=self.viewport,
                ignore_default_args=["--enable-automation"],
                args=["--no-sandbox", "--disable-infobars", "--disable-blink-features=AutomationControlled"]
            )
            
            page = context.pages[0]
            await page.goto(self.url)
            await self._wait_for_login(page)
            
            for i, prompt in enumerate(prompts):
                if progress_callback:
                    progress_callback(i + 1, len(prompts), f"Processing prompt {i+1}/{len(prompts)}")
                
                # Start new chat for subsequent prompts to keep context clean
                if i > 0:
                    await page.goto(self.url)
                    await page.wait_for_selector(self.prompt_selector)
                
                await page.wait_for_timeout(3000)
                
                # Submit
                await self._submit_prompt(page, prompt)
                
                # Wait for generation (Dynamic wait)
                await self._wait_for_generation(page)
                
                await self._scroll_to_load(page)
                
                # Extract
                timestamp = int(time.time())
                base_filename = f"gen_{timestamp}_{i+1}"
                image_path = await self._extract_image_from_dom(page, base_filename)
                
                # Fallback Screenshot
                if not image_path:
                    try:
                        image_path = os.path.join(self.output_dir, f"{base_filename}_fallback.png")
                        await page.screenshot(path=image_path)
                    except Exception:
                        image_path = None
                
                # Cache the prompt to a .txt file
                if image_path:
                    try:
                        prompt_path = os.path.join(self.output_dir, f"{base_filename}.txt")
                        with open(prompt_path, "w", encoding="utf-8") as f:
                            f.write(prompt)
                    except Exception as e:
                        print(f"Failed to cache prompt: {e}")
                
                results.append((prompt, image_path))
            
            await context.close()
        
        return results
