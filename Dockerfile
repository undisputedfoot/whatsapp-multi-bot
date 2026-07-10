# ============================================================
#  WhatsApp Multi-Bot — Docker (Render / production)
# ============================================================

FROM node:20-slim AS node-base

FROM python:3.12-slim

LABEL description="WhatsApp Multi-Bot — Multi-session WhatsApp automation"

# ── Install Node.js from node base ─────────────────────
COPY --from=node-base /usr/local/bin/node /usr/local/bin/node
COPY --from=node-base /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

# ── Install Chromium + system deps ─────────────────────
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROMIUM_PATH=/usr/bin/chromium
ENV BROWSER_MODE=local
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# ── Working directory ───────────────────────────────────
WORKDIR /app

# ── Copy WA engine (Node.js) ──────────────────────────
COPY wa-engine/ ./wa-engine/
RUN cd wa-engine && npm install --production

# ── Install Python deps ────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy app source ────────────────────────────────────
COPY . .

# ── Data directories ───────────────────────────────────
RUN mkdir -p data/sessions data/stickers data/media

# ── Port ────────────────────────────────────────────────
EXPOSE 5000

# ── Start (gunicorn with threads, not eventlet) ───────────────────
CMD ["gunicorn", "--worker-class", "gthread", "--threads", "4", "-w", "1", "-b", "0.0.0.0:5000", "main:create_app()"]
