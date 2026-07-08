#!/usr/bin/env bash
# 🤖 WhatsApp Multi-Bot - One-command Termux Setup
# Run: curl -sSL https://raw.githubusercontent.com/YOUR_USER/REPO/main/setup_termux.sh | bash
# Or: bash setup_termux.sh

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════╗"
echo "║   🤖 WhatsApp Multi-Bot for Termux   ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# 1. Update packages
echo -e "${YELLOW}[1/5] Updating packages...${NC}"
pkg update -y && pkg upgrade -y

# 2. Install Python and tools
echo -e "${YELLOW}[2/5] Installing Python...${NC}"
pkg install -y python python-pip git chromium

# 3. Clone repo
REPO_DIR="$HOME/whatsapp-multi-bot"
if [ -d "$REPO_DIR" ]; then
    echo -e "${YELLOW}[3/5] Updating repository...${NC}"
    cd "$REPO_DIR" && git pull
else
    echo -e "${YELLOW}[3/5] Downloading...${NC}"
    cd "$HOME"
    git clone https://github.com/YOUR_USER/whatsapp-multi-bot.git
    cd "$REPO_DIR"
fi

# 4. Install Python packages
echo -e "${YELLOW}[4/5] Installing Python packages...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 5. Install Playwright browser
echo -e "${YELLOW}[5/5] Installing browser...${NC}"
python -m playwright install chromium

# Setup .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env - edit it to add your API keys${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅  All Done!                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Start the bot:${NC}"
echo "  cd ~/whatsapp-multi-bot && python main.py"
echo ""
echo -e "${CYAN}Open in Chrome:${NC}"
echo "  http://localhost:5000"
echo "  Login: admin / admin123"
echo ""
