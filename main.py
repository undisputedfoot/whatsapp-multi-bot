"""
WhatsApp Multi-Bot — Entry Point.

Run with:  python main.py
Or for production:  gunicorn -k eventlet -w 1 'main:create_app()'
"""

import asyncio
import os
import sys
import threading
import shutil
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── First-run wizard ────────────────────────────────

def _first_run_wizard():
    """Check dependencies and guide the user through setup on first launch."""
    first_run_file = os.path.join(os.path.dirname(__file__), ".first_run_done")
    if os.path.exists(first_run_file):
        return

    print("=" * 56)
    print("  👋 Welcome to WhatsApp Multi-Bot!")
    print("  Let's check everything is ready...")
    print("=" * 56)
    print()

    # Check .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env_example = os.path.join(os.path.dirname(__file__), ".env.example")
    if not os.path.exists(env_path) and os.path.exists(env_example):
        shutil.copy2(env_example, env_path)
        print("  ✅ Created .env from template")
        print("  ✏️  Edit .env to add your API keys and settings")

    # Check Chromium
    chromium_paths = [
        os.path.expanduser("~\\AppData\\Local\\ms-playwright"),
        os.path.expanduser("~/.cache/ms-playwright"),
        "/usr/lib/chromium",
    ]
    has_chromium = any(
        os.path.exists(p) and any(f.startswith("chromium") for f in os.listdir(p))
        for p in chromium_paths if os.path.exists(p)
    )

    if not has_chromium:
        print("  🌐 Downloading Chromium browser (one-time, ~150MB)...")
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True, capture_output=True, timeout=300,
            )
            print("  ✅ Chromium installed!")
        except Exception:
            print("  ⚠️  Could not auto-install Chromium.")
            print("  Run manually: python -m playwright install chromium")

    # Mark first run done
    with open(first_run_file, "w") as f:
        f.write("done")

    print()
    print("  🚀 Setup check complete! Starting bot...")
    print("=" * 56)
    print()


# ── Bot startup ─────────────────────────────────────

from core.config import BASE_DIR
from core.manager import manager
from core.lang import t
from web.app import app, run as run_web
from core import db


def start_bot():
    """Run the WhatsApp bot in a background event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    db.migrate()

    print("=" * 50)
    print("  🤖 WhatsApp Multi-Bot")
    print("  Multi-session · Multi-language · Automation")
    print("=" * 50)

    try:
        loop.run_until_complete(manager.start_all())
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(manager.stop_all())
    finally:
        loop.close()


def create_app():
    """Factory for gunicorn."""
    t_bot = threading.Thread(target=start_bot, daemon=True)
    t_bot.start()
    return app


# ── Main ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WhatsApp Multi-Bot")
    parser.add_argument("--no-web", action="store_true", help="Run bot without web dashboard")
    parser.add_argument("--port", type=int, default=None, help="Dashboard port")
    parser.add_argument("--host", type=str, default=None, help="Dashboard host")
    parser.add_argument("--setup", action="store_true", help="Run setup checks only, don't start bot")
    parser.add_argument("--reset-setup", action="store_true", help="Re-run the first-run wizard")
    args = parser.parse_args()

    # Reset first-run flag if requested
    if args.reset_setup:
        flag = os.path.join(os.path.dirname(__file__), ".first_run_done")
        if os.path.exists(flag):
            os.remove(flag)
        print("✅ First-run wizard will run again on next start.")
        sys.exit(0)

    # Always run first-run wizard (it checks if already done)
    _first_run_wizard()

    # If only setup, we're done
    if args.setup:
        print("✅ All checks passed! Ready to run.")
        sys.exit(0)

    if args.no_web:
        start_bot()
    else:
        # Start bot in background thread
        t_bot = threading.Thread(target=start_bot, daemon=True)
        t_bot.start()

        # Run web dashboard (blocking)
        run_web(host=args.host, port=args.port)
