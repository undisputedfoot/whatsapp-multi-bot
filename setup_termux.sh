#!/usr/bin/env bash
# 🤖 WhatsApp Multi-Bot - One-command Termux Setup
# Run: curl -sSL https://raw.githubusercontent.com/undisputedfoot/whatsapp-multi-bot/main/setup_termux.sh | bash
# Or: bash setup_termux.sh

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════╗"
echo "║   🤖 WhatsApp Multi-Bot for Termux   ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# 1. Update packages
echo -e "${YELLOW}[1/6] Updating packages...${NC}"
pkg update -y && pkg upgrade -y

# 2. Install Python and tools
echo -e "${YELLOW}[2/6] Installing Python & repos...${NC}"
pkg install -y x11-repo tur-repo
pkg install -y python python-pip git

# 3. Install Chromium browser
echo -e "${YELLOW}[3/6] Installing Chromium browser...${NC}"
pkg install -y chromium chromedriver 2>/dev/null && {
    echo -e "${GREEN}✅ Chromium + chromedriver installed${NC}"
    pip install selenium -q
    echo -e "${GREEN}✅ Selenium installed${NC}"
} || {
    echo -e "${RED}❌ Could not install Chromium.${NC}"
    echo -e "${YELLOW}   Run: pkg install x11-repo tur-repo && pkg install chromium${NC}"
    exit 1
}

# 4. Clone repo
REPO_DIR="$HOME/whatsapp-multi-bot"
if [ -d "$REPO_DIR" ]; then
    echo -e "${YELLOW}[4/6] Updating repository...${NC}"
    cd "$REPO_DIR" && git pull
else
    echo -e "${YELLOW}[4/6] Downloading...${NC}"
    cd "$HOME"
    git clone https://github.com/undisputedfoot/whatsapp-multi-bot.git
    cd "$REPO_DIR"
fi

# 5. Install Python packages
echo -e "${YELLOW}[5/6] Installing Python packages...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✅ Python packages installed${NC}"

# 6. Setup .env
echo -e "${YELLOW}[6/6] Setting up configuration...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env from template${NC}"
    echo -e "${YELLOW}   ✏️  Edit .env to add your API keys: nano .env${NC}"
else
    echo -e "${GREEN}✅ .env already exists${NC}"
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
echo -e "${YELLOW}📱  Need to keep it running?${NC}"
echo "  pkg install termux-api"
echo "  termux-wake-lock"
echo ""
