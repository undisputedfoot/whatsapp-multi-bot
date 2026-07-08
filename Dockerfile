# ============================================================
#  WhatsApp Multi-Bot — Docker
#  Build:  docker build -t whatsapp-multi-bot .
#  Run:    docker run -it -p 5000:5000 -v $(pwd)/data:/app/data whatsapp-multi-bot
# ============================================================

FROM python:3.12-slim

LABEL description="WhatsApp Multi-Bot — Multi-session WhatsApp automation"

# ── Install Chromium ──────────────────────────────────────
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-sandbox \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV CHROMIUM_PATH=/usr/bin/chromium

# ── Working directory ─────────────────────────────────────
WORKDIR /app

# ── Install Python deps ──────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Install Playwright system deps & browser ─────────────
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

# ── Copy source ──────────────────────────────────────────
COPY . .

# ── Create data directories ──────────────────────────────
RUN mkdir -p data/sessions data/stickers

# ── Expose dashboard ─────────────────────────────────────
EXPOSE 5000

# ── Start ────────────────────────────────────────────────
CMD ["python", "main.py"]
