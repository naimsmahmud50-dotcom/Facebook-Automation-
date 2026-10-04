"""Browser automation engine leveraging Playwright with stealth and humanized configurations."""

import os
from typing import Any, Dict, Optional, Tuple
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from ..utils.logger import logger
from .session import SessionManager

load_dotenv()

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

class BrowserEngine:
    """Enterprise-grade browser automation lifecycle controller."""

    def __init__(
        self,
        headless: Optional[bool] = None,
        slow_mo: Optional[int] = None,
        session_manager: Optional[SessionManager] = None,
    ):
        self.headless = (
            headless
            if headless is not None
            else os.getenv("HEADLESS", "false").lower() in ("true", "1")
        )
        self.slow_mo = (
            slow_mo
            if slow_mo is not None
            else int(os.getenv("SLOW_MO_MS", "100"))
        )
        self.session_manager = session_manager or SessionManager()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def initialize(self) -> Tuple[BrowserContext, Page]:
        """Launches browser with stealth flags and loads stored session if available."""
        logger.info(f"🚀 Initializing Stealth Browser (Headless: {self.headless}, SlowMo: {self.slow_mo}ms)")
        
        self.playwright = await async_playwright().start()

        # Stealth browser arguments to avoid bot detection flags
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--window-position=0,0",
            "--ignore-certificate-errors",
            "--disable-extensions",
        ]

        # Optional proxy configuration from environment
        proxy_config: Optional[Dict[str, str]] = None
        proxy_server = os.getenv("PROXY_SERVER")
        if proxy_server:
            proxy_config = {"server": proxy_server}
            proxy_user = os.getenv("PROXY_USERNAME")
            proxy_pass = os.getenv("PROXY_PASSWORD")
            if proxy_user and proxy_pass:
                proxy_config["username"] = proxy_user
                proxy_config["password"] = proxy_pass
            logger.info(f"🌐 Routing browser traffic through proxy: {proxy_server}")

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=launch_args,
            proxy=proxy_config,
        )

        # Storage state (session cookies)
        storage_state_path = self.session_manager.get_storage_state_path()
        if storage_state_path:
            logger.info("🔑 Resuming previous authenticated Facebook session...")

        self.context = await self.browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            viewport={
                "width": int(os.getenv("VIEWPORT_WIDTH", "1280")),
                "height": int(os.getenv("VIEWPORT_HEIGHT", "800")),
            },
            storage_state=storage_state_path,
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["notifications"],
        )

        # Inject script to overwrite navigator.webdriver
        await self.context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        )

        self.page = await self.context.new_page()
        return self.context, self.page

    async def save_session(self) -> bool:
        """Saves current cookies and storage."""
        if self.context:
            return await self.session_manager.save_storage_state(self.context)
        return False

    async def close(self) -> None:
        """Gracefully shuts down browser contexts and Playwright subprocess."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("🛑 Browser engine successfully closed.")
        except Exception as e:
            logger.warning(f"Notice while closing browser engine: {e}")
