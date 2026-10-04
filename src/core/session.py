"""Session and Cookie Persistence Manager for zero-checkpoint continuous automation."""

import json
from pathlib import Path
from typing import Any, List, Optional
from ..utils.logger import logger

class SessionManager:
    """Manages persistent browser storage states and cookies to avoid continuous re-logins."""

    def __init__(self, session_path: Optional[str] = None):
        if session_path:
            self.session_file = Path(session_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.session_file = base_dir / "sessions" / "fb_session.json"

        # Ensure directory exists
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

    def session_exists(self) -> bool:
        """Checks if a saved session file exists and is non-empty."""
        return self.session_file.exists() and self.session_file.stat().st_size > 10

    async def save_storage_state(self, context: Any) -> bool:
        """Saves full browser storage state (cookies + local storage) via Playwright."""
        try:
            await context.storage_state(path=str(self.session_file))
            logger.info(f"💾 Browser session saved successfully to: {self.session_file.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
            return False

    def get_storage_state_path(self) -> Optional[str]:
        """Returns storage state path if valid, otherwise None."""
        if self.session_exists():
            return str(self.session_file)
        return None

    def clear_session(self) -> bool:
        """Removes the stored session file safely."""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("🗑️ Stored session cleared successfully.")
            return True
        except Exception as e:
            logger.error(f"Error deleting session file: {e}")
            return False
