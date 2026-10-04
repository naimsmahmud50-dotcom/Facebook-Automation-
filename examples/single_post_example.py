"""Example: How to publish a quick Facebook post using Python code."""

import asyncio
from src.core.browser import BrowserEngine
from src.modules.poster import FacebookPoster
from src.utils.logger import logger

async def main():
    logger.info("Initializing Facebook Automation Suite for Single Post...")

    # Initialize Browser Engine (headless=False allows you to watch the automation)
    engine = BrowserEngine(headless=False)

    try:
        poster = FacebookPoster(engine)

        content = (
            "🚀 Elevating digital workflows with automated intelligence!\n\n"
            "Consistent posting and smart scheduling empower brands to scale seamlessly. "
            "#Automation #Python #GrowthEngineering"
        )

        success = await poster.create_post(
            content=content,
            media_paths=None,  # Optional: e.g., ["assets/banner.png"]
        )

        if success:
            logger.info("🎉 Example post completed successfully!")
        else:
            logger.error("❌ Example post failed.")

    finally:
        await engine.close()

if __name__ == "__main__":
    asyncio.run(main())
