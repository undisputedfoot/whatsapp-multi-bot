# ============================================================
#  WhatsApp Multi-Bot — Docker (Render / production)
# ============================================================

FROM python:3.12-slim

LABEL description="WhatsApp Multi-Bot — Multi-session WhatsApp automation"

# ── System deps ─────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-sandbox \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV CHROMIUM_PATH=/usr/bin/chromium
ENV BROWSER_MODE=remote
ENV PYTHONUNBUFFERED=1

# ── Working directory ───────────────────────────────────
WORKDIR /app

# ── Install Python deps ────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Playwright browser ─────────────────────────────────
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

# ── Copy app source ────────────────────────────────────
COPY . .

# ── Data directories ───────────────────────────────────
RUN mkdir -p data/sessions data/stickers data/media data/bot.db

# ── Port ────────────────────────────────────────────────
EXPOSE 5000

# ── Start (gunicorn for production) ────────────────────
CMD ["sh", "-c", "gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 'main:create_app()'"]
