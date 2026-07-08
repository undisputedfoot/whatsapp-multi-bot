"""
Auto-Update — git pull, reinstall deps, and restart the bot.
Triggered via !update command (admin only).
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from ..config import BASE_DIR, UPDATE_BRANCH


class AutoUpdater:
    """Self-update capability via git."""

    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)

    async def update(self) -> str:
        """Run git pull and reinstall dependencies. Returns status message."""
        try:
            self._log("update", "🔄 Checking for updates...")

            # Git pull
            result = subprocess.run(
                ["git", "pull", "origin", UPDATE_BRANCH],
                cwd=BASE_DIR,
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return f"❌ Git pull failed:\n{result.stderr[:200]}"

            output = result.stdout.strip()
            if "Already up to date" in output:
                return "✅ Already up to date!"

            # Reinstall deps if requirements changed
            req_file = BASE_DIR / "requirements.txt"
            if req_file.exists():
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                    capture_output=True, timeout=60,
                )

            self._log("update", "✅ Update complete. Restarting...")
            return "✅ Update complete! Restarting bot..."

        except subprocess.TimeoutExpired:
            return "❌ Update timed out."
        except FileNotFoundError:
            return "❌ Git not installed. Install git to use auto-update."
        except Exception as e:
            return f"❌ Update failed: {e}"
