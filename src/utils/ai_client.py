"""
Centralized AI Client for Browser-based Automation.

This utility consolidates automation logic for Google AI Studio, supporting both
Image Generation (Gemini Image models) and Text Generation (future use).
"""

import os
import time
import base64
from typing import List, Tuple, Optional, Callable
from playwright.async_api import async_playwright, Page, BrowserContext

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
        except:
            print(">> ACTION REQUIRED: Please log in manually in the browser window.")
            print("Waiting up to 5 minutes for you to reach the chat interface...")
            await page.wait_for_selector(self.prompt_selector, timeout=300000)
            print("Login detected! Proceeding...")
    
    async def _extract_image_from_dom(self, page: Page, base_filename: str) -> Optional[str]:
        """Extract generated image from DOM."""
        print("Extracting image data from DOM...")
        try:
            # Wait for image to finalize
            print("Waiting 3 seconds for image to finalize...")
            await page.wait_for_timeout(3000)
            
            # Find all visible images
            all_imgs = await page.locator("img").all()
            potential_targets = []
            
            for img in all_imgs:
                try:
                    if await img.is_visible():
                        box = await img.bounding_box()
                        # Filter out small images (icons, etc.)
                        if box and box['width'] > 100 and box['height'] > 100:
                            potential_targets.append(img)
                except:
                    pass
            
            if not potential_targets:
                print("Could not locate any large visible image.")
                return None
            
            target_image = potential_targets[-1]
            src = await target_image.get_attribute("src")
            image_data = None
            
            # Handle data: URI
            if src.startswith("data:image"):
                head, data = src.split(",", 1)
                image_data = base64.b64decode(data)
            
            # Handle blob: URI
            elif src.startswith("blob:"):
                # Fetch blob content via JS
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
            
            if image_data:
                filepath = os.path.join(self.output_dir, f"{base_filename}.png")
                with open(filepath, "wb") as f:
                    f.write(image_data)
                return filepath
                
        except Exception as e:
            print(f"Extraction failed: {e}")
            return None
    
    async def _submit_prompt(self, page: Page, prompt: str):
        """Submit a prompt to AI Studio."""
        await page.evaluate(
            '(text) => { const el = document.querySelector(\'textarea[aria-label="Enter a prompt"]\'); el.value = text; el.dispatchEvent(new Event("input", {bubbles:true})); }',
            prompt
        )
        run_button = page.locator('button[aria-label="Run"]')
        if await run_button.count() > 0:
            await run_button.click()
        else:
            await page.keyboard.press("Control+Enter")
    
    async def _scroll_to_load(self, page: Page):
        """Scroll to bottom to ensure lazy-loaded items appear."""
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        try:
            await page.evaluate("""() => {
                const container = document.querySelector('ms-autoscroll-container') || document.querySelector('.conversation-container') || document.body;
                container.scrollTop = container.scrollHeight;
            }""")
        except:
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
                
                # Wait for generation (Fixed wait + polling could be better, but fixed is safe for now)
                print("Waiting for generation...")
                await page.wait_for_timeout(10000)
                
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
