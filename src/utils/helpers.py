"""Helper functions for anti-detect human simulation, config parsing, and file management."""

import asyncio
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from .logger import logger

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def random_delay(min_seconds: float = 2.0, max_seconds: float = 5.0) -> float:
    """Calculates a randomized float delay within range."""
    return round(random.uniform(min_seconds, max_seconds), 2)

async def human_sleep(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    """Asynchronous pause simulating natural human thinking time."""
    delay = random_delay(min_seconds, max_seconds)
    logger.debug(f"Simulating human pause: {delay}s")
    await asyncio.sleep(delay)

async def human_type(page_or_element: Any, selector_or_locator: Any, text: str, min_delay_ms: int = 40, max_delay_ms: int = 150) -> None:
    """Types text character-by-character with randomized pauses to bypass bot detection."""
    try:
        # If locator was passed or selector was passed
        if hasattr(page_or_element, "locator"):
            element = page_or_element.locator(selector_or_locator) if isinstance(selector_or_locator, str) else selector_or_locator
        else:
            element = page_or_element

        await element.click()
        await asyncio.sleep(random.uniform(0.3, 0.7))

        for char in text:
            await element.press_sequentially(char, delay=random.randint(min_delay_ms, max_delay_ms))
            # Occasional micro-pauses between sentences or words
            if char in [".", ",", "!", "?"]:
                await asyncio.sleep(random.uniform(0.2, 0.5))
            elif char == " " and random.random() < 0.15:
                await asyncio.sleep(random.uniform(0.1, 0.3))

    except Exception as exc:
        logger.error(f"Error during human typing simulation: {exc}")
        raise

async def capture_debug_screenshot(page: Any, prefix: str = "error") -> str:
    """Captures and saves a debug screenshot for troubleshooting and client reporting."""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename
        await page.screenshot(path=str(filepath), full_page=False)
        logger.info(f"📸 Debug screenshot captured: {filepath.name}")
        return str(filepath)
    except Exception as e:
        logger.warning(f"Could not take debug screenshot: {e}")
        return ""

def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """Safely loads a YAML configuration file."""
    if not config_path.exists():
        logger.warning(f"Configuration file not found at {config_path}. Returning default empty config.")
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data or {}
    except Exception as err:
        logger.error(f"Failed to parse YAML file {config_path}: {err}")
        return {}
