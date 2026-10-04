"""Logging utility module with Rich terminal integration and rotating file handlers."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Create logs directory if not exists
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class LogColors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    DIM = "\033[2m"

class ColoredFormatter(logging.Formatter):
    """Custom formatter to provide sleek visual logs in standard terminals."""

    LEVEL_COLORS = {
        logging.DEBUG: LogColors.CYAN,
        logging.INFO: LogColors.GREEN,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.RED + LogColors.BOLD,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, LogColors.RESET)
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"{LogColors.DIM}[{timestamp}]{LogColors.RESET} {color}[{record.levelname:<8}]{LogColors.RESET}"
        return f"{prefix} {record.getMessage()}"

def setup_logger(name: str = "FBAuto", log_file: str = "automation.log") -> logging.Logger:
    """Configures and returns an application logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)

        # File Handler
        log_path = LOGS_DIR / log_file
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

# Global default logger instance
logger = setup_logger()
