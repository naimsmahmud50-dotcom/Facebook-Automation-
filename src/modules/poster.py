"""Facebook Post Automation Engine.

Automates organic content publishing to personal feeds, brand pages,
and groups with stealth human typing, media attachments, and failure recovery.
"""

import asyncio
import os
from pathlib import Path
from typing import List, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..core.browser import BrowserEngine
from ..utils.helpers import capture_debug_screenshot, human_sleep, human_type
from ..utils.logger import logger

class FacebookPoster:
    """Enterprise-grade Facebook Post Publisher."""

    def __init__(self, browser_engine: BrowserEngine):
        self.engine = browser_engine
        self.page: Optional[Page] = None

    async def verify_login_state(self, page: Page) -> bool:
        """Navigates to Facebook and checks if the user session is authenticated."""
        logger.info("🔍 Checking Facebook authentication state...")
        try:
            await page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=45000)
            await human_sleep(2.0, 4.0)

            # Check if login input form is present
            email_field = await page.query_selector('input[name="email"], input#email')
            pass_field = await page.query_selector('input[name="pass"], input#pass')

            if email_field and pass_field:
                # If login form is shown, attempt automated login if credentials exist in .env
                fb_email = os.getenv("FB_EMAIL")
                fb_pass = os.getenv("FB_PASSWORD")

                if fb_email and fb_pass and fb_email != "your_email_or_phone_here":
                    logger.info("🔑 Stored session expired or missing. Attempting credential login...")
                    await human_type(page, 'input[name="email"], input#email', fb_email)
                    await human_sleep(0.8, 1.5)
                    await human_type(page, 'input[name="pass"], input#pass', fb_pass)
                    await human_sleep(0.8, 1.5)

                    login_btn = await page.query_selector('button[name="login"], button[type="submit"]')
                    if login_btn:
                        await login_btn.click()
                        logger.info("⏳ Waiting for login confirmation...")
                        await page.wait_for_load_state("networkidle", timeout=30000)
                        await human_sleep(3.0, 5.0)
                        await self.engine.save_session()
                        return True
                else:
                    logger.warning("⚠️ No active session found and credentials are blank. Please configure .env or login interactively.")
                    return False

            # If no login form or profile/navigation elements are detected
            logger.info("✅ Facebook authenticated session confirmed.")
            return True

        except Exception as e:
            logger.error(f"Error during login verification: {e}")
            await capture_debug_screenshot(page, "login_check_failed")
            return False

    async def create_post(
        self,
        content: str,
        media_paths: Optional[List[str]] = None,
        target_url: str = "https://www.facebook.com/",
    ) -> bool:
        """Publishes a new post with text and optional images to Facebook.

        Args:
            content: The text/caption for the post.
            media_paths: Optional list of local image file paths to attach.
            target_url: Facebook URL (Feed home, Page, or Group).

        Returns:
            bool: True if post published successfully, False otherwise.
        """
        if not self.engine.page:
            _, self.page = await self.engine.initialize()
        else:
            self.page = self.engine.page

        assert self.page is not None

        try:
            # 1. Verify Authentication
            is_logged_in = await self.verify_login_state(self.page)
            if not is_logged_in:
                logger.error("❌ Cannot post: User is not authenticated on Facebook.")
                return False

            # 2. Navigate to Target (Home Feed, Group, or Page)
            if self.page.url != target_url:
                logger.info(f"🌐 Navigating to destination: {target_url}")
                await self.page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                await human_sleep(2.5, 4.5)

            # 3. Locate & Click 'Create Post' Trigger Button
            logger.info("📝 Locating 'Create Post' trigger...")
            create_post_selectors = [
                'div[role="button"]:has-text("What\'s on your mind")',
                'div[aria-label*="What\'s on your mind"]',
                'div[role="button"]:has-text("Write something...")',
                'div[role="button"]:has-text("Create a post")',
                'span:has-text("What\'s on your mind")',
            ]

            post_trigger_element = None
            for selector in create_post_selectors:
                try:
                    locator = self.page.locator(selector).first
                    if await locator.is_visible(timeout=3000):
                        post_trigger_element = locator
                        logger.info(f"Found post trigger with selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            if not post_trigger_element:
                logger.warning("Could not locate post trigger via standard text. Trying fallback role search...")
                post_trigger_element = self.page.locator('div[role="region"] div[role="button"]').first

            await post_trigger_element.click()
            await human_sleep(2.0, 3.5)

            # 4. Locate the Text Input Box (contenteditable)
            logger.info("⌨️ Typing post content with stealth cadence...")
            input_box_selectors = [
                'div[role="dialog"] div[contenteditable="true"]',
                'div[aria-label*="What\'s on your mind"][contenteditable="true"]',
                'div[contenteditable="true"][role="textbox"]',
                'div[role="dialog"] form div[contenteditable="true"]',
            ]

            input_element = None
            for sel in input_box_selectors:
                try:
                    locator = self.page.locator(sel).first
                    if await locator.is_visible(timeout=3000):
                        input_element = locator
                        break
                except PlaywrightTimeoutError:
                    continue

            if not input_element:
                raise RuntimeError("Failed to find editable post input box inside dialog.")

            # Type text using randomized human keystrokes
            await human_type(self.page, input_element, content)
            await human_sleep(1.5, 3.0)

            # 5. Attach Images / Media (if specified)
            if media_paths:
                for media_path in media_paths:
                    media_file = Path(media_path)
                    if media_file.exists():
                        logger.info(f"🖼️ Attaching media: {media_file.name}")
                        file_input = self.page.locator('input[type="file"][accept*="image"]').first
                        if await file_input.count() > 0:
                            await file_input.set_input_files(str(media_file))
                            await human_sleep(3.0, 5.0)
                        else:
                            logger.warning("File upload input not immediately exposed. Clicking Photo/video button...")
                            photo_btn = self.page.locator('div[aria-label*="Photo/video"], div[aria-label*="Photo"]').first
                            if await photo_btn.is_visible():
                                await photo_btn.click()
                                await human_sleep(1.5, 2.5)
                                file_input = self.page.locator('input[type="file"][accept*="image"]').first
                                await file_input.set_input_files(str(media_file))
                                await human_sleep(3.0, 5.0)
                    else:
                        logger.warning(f"Media file not found at: {media_path}")

            # 6. Locate & Click the 'Post' Submission Button
            logger.info("🚀 Submitting publication...")
            post_button_selectors = [
                'div[role="dialog"] div[aria-label="Post"][role="button"]',
                'div[role="dialog"] div[role="button"]:has-text("Post")',
                'div[aria-label="Post"][role="button"]',
                'div[role="button"]:has-text("Publish")',
            ]

            submit_button = None
            for sel in post_button_selectors:
                try:
                    locator = self.page.locator(sel).first
                    if await locator.is_visible(timeout=3000):
                        # Ensure button is not disabled
                        is_disabled = await locator.get_attribute("aria-disabled")
                        if is_disabled != "true":
                            submit_button = locator
                            break
                except PlaywrightTimeoutError:
                    continue

            if not submit_button:
                raise RuntimeError("Could not find active 'Post' submit button.")

            await submit_button.click()
            logger.info("⏳ Awaiting post confirmation and dialog dismissal...")
            await human_sleep(4.0, 7.0)

            # 7. Update Session State
            await self.engine.save_session()
            logger.info("🎉 Post published successfully to Facebook!")
            return True

        except Exception as e:
            logger.error(f"Failed to publish Facebook post: {e}")
            if self.page:
                screenshot_path = await capture_debug_screenshot(self.page, "post_failure")
                logger.info(f"Inspect error screenshot: {screenshot_path}")
            return False
