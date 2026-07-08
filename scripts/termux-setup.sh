#!/usr/bin/env bash
# ============================================================
#  Termux Setup for Android — WhatsApp Multi-Bot
#  Run this ON YOUR PHONE using Termux:
#    curl -sSL https://raw.githubusercontent.com/YOUR_USER/REPO/main/scripts/termux-setup.sh | bash
#
#  Or manually:
#    pkg install git -y
#    git clone https://github.com/YOUR_USER/REPO
#    cd REPO && bash scripts/termux-setup.sh
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════╗"
echo "║   🤖 WhatsApp Multi-Bot for Termux   ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Update packages ────────────────────────────────
echo -e "${YELLOW}[1/6] Updating packages…${NC}"
pkg update -y && pkg upgrade -y

# ── 2. Install dependencies ───────────────────────────
echo -e "${YELLOW}[2/6] Installing Python & tools…${NC}"
pkg install -y python python-pip git chromium tur-repo x11-repo
pkg install -y which

# ── 3. Clone / update repo ────────────────────────────
REPO_DIR="$HOME/whatsapp-multi-bot"

if [ -d "$REPO_DIR" ]; then
    echo -e "${YELLOW}[3/6] Repository exists — updating…${NC}"
    cd "$REPO_DIR" && git pull
else
    echo -e "${YELLOW}[3/6] Cloning repository…${NC}"
    cd "$HOME"
    # Replace with your actual repo URL
    git clone https://github.com/YOUR_USER/whatsapp-multi-bot.git
    cd "$REPO_DIR"
fi

# ── 4. Install Python packages ────────────────────────
echo -e "${YELLOW}[4/6] Installing Python packages…${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# ── 5. Install Playwright Chromium ────────────────────
echo -e "${YELLOW}[5/6] Installing Playwright browser…${NC}"
python -m playwright install chromium

# ── 6. Create .env if missing ─────────────────────────
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[6/6] Creating .env from template…${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Edit .env to set your session names & preferences.${NC}"
else
    echo -e "${YELLOW}[6/6] .env already exists — keeping it.${NC}"
fi

# ── Done ──────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅  Setup Complete!                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}To start the bot:${NC}"
echo "  cd $REPO_DIR"
echo "  python main.py"
echo ""
echo -e "${CYAN}Then open the dashboard on your phone:${NC}"
echo "  http://localhost:5000"
echo ""
echo -e "${CYAN}To access from another device on the same WiFi:${NC}"
echo "  Find your phone's IP:  ifconfig  (look for wlan0)"
echo "  Then visit:  http://YOUR_IP:5000"
echo ""
echo -e "${YELLOW}📱  First run:${NC}"
echo "  1. Start the bot  →  python main.py"
echo "  2. Open the dashboard URL in Chrome"
echo "  3. Login with admin / admin123"
echo "  4. Scan the QR code shown in the terminal"
echo "  5. Done! Bot is live on your phone 📱"
echo ""
