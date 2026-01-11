"""
Browser automation module for AI image generation.

This module provides a reusable browser automation client for generating images
via Google AI Studio using Playwright. It handles login persistence, image extraction,
and can be used standalone or integrated into other tools.
"""

import os
import time
import base64
from typing import List, Tuple, Optional, Callable
from playwright.async_api import async_playwright, Page, BrowserContext


class AIStudioClient:
    """
    Automated browser client for Google AI Studio image generation.
    
    Features:
    - Persistent login (saves session to chrome_profile)
    - Handles data: and blob: URI image extraction
    - Auto-scrolling for lazy-loaded images
    - Configurable output directory
    - Progress callbacks
    """
    
    def __init__(
        self,
        output_dir: str = "generated_images",
        user_data_dir: str = ".config/chrome_profile",
        headless: bool = False,
        viewport: dict = None
    ):
        """
        Initialize the AI Studio client.
        
        Args:
            output_dir: Directory to save generated images
            user_data_dir: Directory for persistent browser profile (login data)
            headless: Run browser in headless mode
            viewport: Browser viewport size (default: 1280x800)
        """
        self.output_dir = output_dir
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.viewport = viewport or {'width': 1280, 'height': 800}
        
        # Create directories if needed
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        self.url = "https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image"
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
        """
        Extract generated image from DOM (handles data: and blob: URIs).
        
        Args:
            page: Playwright page object
            base_filename: Base filename for saving
            
        Returns:
            Path to saved image file, or None if extraction failed
        """
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
            
            # Use the last (most recent) image
            target_image = potential_targets[-1]
            print(f"Selected last image candidate ({len(potential_targets)} found).")
            
            src = await target_image.get_attribute("src")
            image_data = None
            
            # Handle data: URI
            if src.startswith("data:image"):
                print("Found Data URI image.")
                head, data = src.split(",", 1)
                image_data = base64.b64decode(data)
            
            # Handle blob: URI
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
                return None
            
            if image_data:
                filepath = os.path.join(self.output_dir, f"{base_filename}.png")
                with open(filepath, "wb") as f:
                    f.write(image_data)
                print(f"Saved extracted image to {filepath}")
                return filepath
            else:
                print("Failed to process image data.")
                return None
                
        except Exception as e:
            print(f"Extraction failed: {e}")
            return None
    
    async def _submit_prompt(self, page: Page, prompt: str):
        """Submit a prompt to AI Studio."""
        print("Entering prompt...")
        await page.evaluate(
            '(text) => { const el = document.querySelector(\'textarea[aria-label="Enter a prompt"]\'); el.value = text; el.dispatchEvent(new Event("input", {bubbles:true})); }',
            prompt
        )
        
        print("Submitting...")
        run_button = page.locator('button[aria-label="Run"]')
        if await run_button.count() > 0:
            await run_button.click()
        else:
            await page.keyboard.press("Control+Enter")
    
    async def _scroll_to_load_image(self, page: Page):
        """Scroll to bottom to ensure lazy-loaded images appear."""
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
    
    async def generate_images(
        self,
        prompts: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Tuple[str, Optional[str]]]:
        """
        Generate images from a list of prompts.
        
        Args:
            prompts: List of text prompts
            progress_callback: Optional callback(current, total, status_message)
            
        Returns:
            List of tuples: (prompt_text, image_path or None)
        """
        results = []
        
        print(f"\nUsing persistent profile at: {self.user_data_dir}")
        print("NOTE: You will need to log in the first time. Subsequent runs will stay logged in.")
        
        async with async_playwright() as p:
            print("\nLaunching Google Chrome...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                channel="chrome",
                viewport=self.viewport,
                ignore_default_args=["--enable-automation"],
                args=["--no-sandbox", "--disable-infobars", "--disable-blink-features=AutomationControlled"]
            )
            
            page = context.pages[0]
            
            # Navigate and login
            print(f"Navigating to {self.url}...")
            await page.goto(self.url)
            await self._wait_for_login(page)
            
            # Process each prompt
            for i, prompt in enumerate(prompts):
                if progress_callback:
                    progress_callback(i + 1, len(prompts), f"Processing prompt {i+1}/{len(prompts)}")
                
                print(f"\nProcessing Prompt {i+1}/{len(prompts)}...")
                
                # Start new chat for subsequent prompts
                if i > 0:
                    print("Starting new chat...")
                    await page.goto(self.url)
                    await page.wait_for_selector(self.prompt_selector)
                
                # Wait for UI to settle
                await page.wait_for_timeout(3000)
                
                # Prepare filenames
                timestamp = int(time.time())
                base_filename = f"gen_{timestamp}_{i+1}"
                
                # Save prompt text
                text_path = os.path.join(self.output_dir, f"{base_filename}.txt")
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(prompt)
                print(f"Saved prompt text to {text_path}")
                
                # Submit prompt
                await self._submit_prompt(page, prompt)
                
                # Wait for generation
                print("Waiting for generation...")
                await page.wait_for_timeout(10000)
                
                # Scroll to load image
                await self._scroll_to_load_image(page)
                
                # Extract image
                image_path = await self._extract_image_from_dom(page, base_filename)
                
                # Fallback screenshot if extraction failed
                if not image_path:
                    print("Taking fallback screenshot...")
                    try:
                        image_path = os.path.join(self.output_dir, f"{base_filename}_fallback.png")
                        await page.screenshot(path=image_path)
                        print(f"Saved fallback screenshot to {image_path}")
                    except Exception as e:
                        print(f"Fallback screenshot failed: {e}")
                        image_path = None
                
                results.append((prompt, image_path))
            
            print("\nAll prompts processed!")
            await page.wait_for_timeout(5000)
            await context.close()
        
        return results


# Convenience function for simple usage
async def generate_images_simple(
    prompts: List[str],
    output_dir: str = "generated_images",
    headless: bool = False
) -> List[Tuple[str, Optional[str]]]:
    """
    Simple wrapper for generating images from prompts.
    
    Args:
        prompts: List of text prompts
        output_dir: Directory to save images
        headless: Run browser in headless mode
        
    Returns:
        List of tuples: (prompt_text, image_path or None)
    """
    client = AIStudioClient(output_dir=output_dir, headless=headless)
    return await client.generate_images(prompts)
