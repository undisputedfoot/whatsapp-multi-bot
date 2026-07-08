"""
Central configuration loader. Reads .env and provides typed access to all settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(key: str, default: str = "false") -> bool:
    return os.getenv(key, default).strip().lower() in ("1", "true", "yes")


def _list(key: str, default: str = "") -> list[str]:
    raw = os.getenv(key, default)
    return [s.strip() for s in raw.split(",") if s.strip()]


# ── Language ───────────────────────────────────────────
BOT_LANGUAGE = os.getenv("BOT_LANGUAGE", "en").strip().lower()
SUPPORTED_LANGUAGES = ["en", "es", "hi", "ar", "fr", "pt", "de", "ja"]

# ── Sessions ───────────────────────────────────────────
SESSION_NAMES: list[str] = _list("SESSION_NAMES", "main")

# ── Browser ────────────────────────────────────────────
BROWSER_MODE = os.getenv("BROWSER_MODE", "local").strip().lower()
CHROME_WS = os.getenv("CHROME_WS", "").strip()

# ── Feature toggles ────────────────────────────────────
AUTO_REPLY_ON = _bool("AUTO_REPLY_ON", "true")
AUTO_STATUS_VIEW = _bool("AUTO_STATUS_VIEW", "true")
READ_RECEIPTS = _bool("READ_RECEIPTS", "false")
AUTO_REJECT_CALLS = _bool("AUTO_REJECT_CALLS", "true")
STICKER_MAKER = _bool("STICKER_MAKER", "true")

CALL_REJECT_MSG = os.getenv("CALL_REJECT_MSG", "I'm unavailable. Please text me.")

# ── AI Replies ─────────────────────────────────────────
AI_PROVIDER = os.getenv("AI_PROVIDER", "none").strip().lower()
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
AI_SYSTEM_PROMPT = os.getenv("AI_SYSTEM_PROMPT",
    "You are a helpful WhatsApp assistant. Reply concisely and naturally.")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "z-ai/glm-5.2")

# ── Admin System ───────────────────────────────────────
# Comma-separated phone numbers (with country code, no +) who are bot super-admins
ADMIN_NUMBERS: list[str] = _list("ADMIN_NUMBERS", "")

# ── Group Management ──────────────────────────────────
GROUP_WELCOME_ON = _bool("GROUP_WELCOME_ON", "true")
GROUP_ANTI_LINK = _bool("GROUP_ANTI_LINK", "false")
GROUP_ANTI_LINK_ACTION = os.getenv("GROUP_ANTI_LINK_ACTION", "warn").strip().lower()  # warn | delete | kick
GROUP_AUTO_REPLY_IN_GROUPS = _bool("GROUP_AUTO_REPLY_IN_GROUPS", "false")

# ── Broadcast ─────────────────────────────────────────
BROADCAST_INTERVAL_SEC = int(os.getenv("BROADCAST_INTERVAL_SEC", "5"))

# ── Human-like Typing ─────────────────────────────────
HUMAN_TYPING = _bool("HUMAN_TYPING", "true")
TYPING_MIN_DELAY = int(os.getenv("TYPING_MIN_DELAY", "3"))   # seconds
TYPING_MAX_DELAY = int(os.getenv("TYPING_MAX_DELAY", "7"))

# ── Business Hours ─────────────────────────────────────
BIZ_HOURS_ENABLED = _bool("BIZ_HOURS_ENABLED", "false")
BIZ_HOURS_START = os.getenv("BIZ_HOURS_START", "09:00")
BIZ_HOURS_END = os.getenv("BIZ_HOURS_END", "18:00")
BIZ_HOURS_TZ = os.getenv("BIZ_HOURS_TZ", "UTC")
BIZ_HOURS_WEEKDAYS = os.getenv("BIZ_HOURS_WEEKDAYS", "1,2,3,4,5")  # 1=Mon..5=Fri
BIZ_CLOSED_MSG = os.getenv("BIZ_CLOSED_MSG",
    "We're currently closed. Our hours are {start}-{end} weekdays. We'll get back to you when we're open!")

# ── ChatGPT Personas ──────────────────────────────────
PERSONA_DEFAULT = os.getenv("PERSONA_DEFAULT",
    "You are a helpful WhatsApp assistant. Reply concisely and naturally.")

# ── Media Gallery ─────────────────────────────────────
MEDIA_AUTO_DOWNLOAD = _bool("MEDIA_AUTO_DOWNLOAD", "true")
MEDIA_DIR = BASE_DIR / "data" / "media"

# ── Plugin System ─────────────────────────────────────
PLUGINS_ENABLED = _bool("PLUGINS_ENABLED", "true")
PLUGIN_DIR = BASE_DIR / "plugins"

# ── Auto-Update ───────────────────────────────────────
AUTO_UPDATE = _bool("AUTO_UPDATE", "false")
UPDATE_BRANCH = os.getenv("UPDATE_BRANCH", "main")

# ── Security ──────────────────────────────────────────
SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))

# ── Dashboard ──────────────────────────────────────────
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5000"))
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_USER = os.getenv("DASHBOARD_USER", "admin")
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS", "admin123")

# ── Webhook ────────────────────────────────────────────
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# ── Paths ──────────────────────────────────────────────
SESSION_DIR = BASE_DIR / "data" / "sessions"
STICKER_DIR = BASE_DIR / "data" / "stickers"
MEDIA_DIR = BASE_DIR / "data" / "media"
PLUGIN_DIR = BASE_DIR / "plugins"
DB_PATH = BASE_DIR / "data" / "bot.db"

for d in (SESSION_DIR, STICKER_DIR, MEDIA_DIR, PLUGIN_DIR):
    d.mkdir(parents=True, exist_ok=True)
