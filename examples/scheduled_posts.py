"""Example: How to schedule posts using the PostScheduler engine."""

import asyncio
from pathlib import Path
from src.main import run_campaign_scheduler
from src.utils.logger import logger

def main():
    logger.info("Starting automated campaign scheduler...")
    config_path = Path(__file__).resolve().parent.parent / "config" / "settings.example.yaml"
    asyncio.run(run_campaign_scheduler(config_path))

if __name__ == "__main__":
    main()
