# ============================================================
#  WhatsApp Multi-Bot — Docker (Render / production)
# ============================================================

FROM python:3.12-slim

LABEL description="WhatsApp Multi-Bot — Multi-session WhatsApp automation"

# ── Install Chromium + system deps ─────────────────────
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-sandbox \
    chromium-chromedriver \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Find where chromium was actually installed
RUN CHROME=$(which chromium || which chromium-browser || echo /usr/bin/chromium) && \
    echo "Chromium at: $CHROME"

ENV CHROMIUM_PATH=/usr/bin/chromium
ENV BROWSER_MODE=local
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# ── Working directory ───────────────────────────────────
WORKDIR /app

# ── Install Python deps ────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy app source ────────────────────────────────────
COPY . .

# ── Data directories ───────────────────────────────────
RUN mkdir -p data/sessions data/stickers data/media

# ── Port ────────────────────────────────────────────────
EXPOSE 5000

# ── Start (gunicorn) ───────────────────────────────────
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "main:create_app()"]
