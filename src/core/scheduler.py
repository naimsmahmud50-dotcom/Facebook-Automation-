"""Scheduler engine for managing scheduled Facebook posting campaigns."""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import schedule

from ..utils.logger import logger

class PostScheduler:
    """Manages periodic and time-targeted social media publication tasks."""

    def __init__(self):
        self.jobs: List[Dict[str, Any]] = []
        self.is_running = False

    def add_daily_job(self, time_str: str, job_func: Callable, *args, **kwargs) -> None:
        """Schedules a daily recurring posting task at specific HH:MM."""
        logger.info(f"⏰ Registered daily campaign task at: {time_str}")
        schedule.every().day.at(time_str).do(job_func, *args, **kwargs)
        self.jobs.append({
            "type": "daily",
            "time": time_str,
            "registered_at": datetime.now().isoformat(),
        })

    def add_interval_job(self, minutes: int, job_func: Callable, *args, **kwargs) -> None:
        """Schedules recurring task every N minutes."""
        logger.info(f"⏰ Registered interval campaign task every {minutes} minutes")
        schedule.every(minutes).minutes.do(job_func, *args, **kwargs)
        self.jobs.append({
            "type": "interval",
            "interval_minutes": minutes,
            "registered_at": datetime.now().isoformat(),
        })

    async def start(self, check_interval_sec: int = 5) -> None:
        """Starts the scheduler polling loop asynchronously."""
        self.is_running = True
        logger.info("🟢 Post Scheduler engine started. Waiting for triggered campaigns...")
        try:
            while self.is_running:
                schedule.run_pending()
                await asyncio.sleep(check_interval_sec)
        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled.")
        finally:
            self.is_running = False

    def stop(self) -> None:
        """Stops the scheduler loop."""
        self.is_running = False
        schedule.clear()
        logger.info("🔴 Post Scheduler stopped and queues cleared.")
