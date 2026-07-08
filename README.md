<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/WhatsApp-Web-25D366?logo=whatsapp" alt="WhatsApp Web">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/AI-OpenAI%2FGemini-8A2BE2" alt="AI">
  <a href="https://render.com/deploy?repo=https://github.com/undisputedfoot/whatsapp-multi-bot">
    <img src="https://img.shields.io/badge/Deploy_to-Render-46E3B7?logo=render&style=for-the-badge" alt="Deploy to Render">
  </a>
  <br>
  <h1>🤖 WhatsApp Multi-Bot</h1>
  <p><strong>Multi-account WhatsApp manager · AI-powered · Web dashboard · 8 languages</strong></p>
  <p>Run multiple WhatsApp accounts from one place. Read messages, send replies, automate everything from a beautiful mobile web dashboard. AI smart replies, group management, scheduled messages, and more — all <strong>free & open source</strong>.</p>
  <p>⚡ <strong>50+ features</strong> · ☁️ <strong>Deploy to Render in 1 click</strong></p>
</div>

---

## � Setup in 10 Seconds

### Windows — Double-click `setup.bat`
```
1. Double-click setup.bat    (installs Python + everything)
2. Double-click start_bot.bat (starts the bot)
3. Open http://localhost:5000  → login: admin / admin123
4. Scan the QR code with WhatsApp
```

### Android (Termux) — Copy-paste one command
```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USER/REPO/main/setup_termux.sh | bash
python main.py
```

### Manual — Two commands
```bash
pip install -r requirements.txt
python -m playwright install chromium && python main.py
```

---

## �📱 What Can It Do?

| Feature | Description |
|---|---|
| **Multiple Accounts** | Run unlimited WhatsApp accounts side-by-side |
| **💬 Web Inbox** | Read messages & reply from the dashboard |
| **🤖 AI Smart Replies** | OpenAI GPT / Google Gemini — toggle per session |
| **🧠 ChatGPT Personas** | Switch personalities: Friendly, Formal, Funny, Teacher, Spanish Tutor, Minimal, or custom |
| **⏱️ Human-like Typing** | Realistic typing delays + "typing..." indicator — feels like a real person |
| **🕐 Business Hours** | Only auto-reply during configured hours, closed message outside |
| **👥 Group Management** | Welcome messages, anti-link, admin commands, member tracking |
| **🛡️ Admin System** | Super-admin + DB-backed admins with role-based commands |
| **📨 Broadcast Lists** | Send bulk messages to named contact lists |
| **📅 Scheduled Messages** | "Send this at 9 AM tomorrow" |
| **🎂 Birthday Reminder** | Auto-wish contacts on their birthday |
| **🔌 Plugin System** | Drop `.py` files in `plugins/` — auto-loaded with `register()` hook |
| **📸 Media Gallery** | Auto-download images, view in `/media` dashboard |
| **🔍 Message Search** | Search all message history from the dashboard |
| **📥 Chat Export** | Download conversations as JSON |
| **🎮 Group Games** | `!trivia`, `!wyr`, `!poll` — interactive group fun |
| **🔄 Auto-Update** | `!update` command — git pulls + reinstalls + restarts |
| **🌤️ Weather Plugin** | Built-in example: `!weather London` |
| **📢 Tag All** | `!tagall` — mention all group members in one message |
| **⚠️ Warn System** | `!warn`, `!warns`, `!warnreset` — group moderation with kick thresholds |
| **⌨️ Custom Commands** | `!setcmd`, `!delcmd`, `!listcmds` — user-defined bot responses |
| **🗑️ Anti-Delete** | Detect deleted messages and forward to admin |
| **📥 Media Downloader** | `!yt`, `!yta`, `!tiktok`, `!instagram` — download media from popular platforms |
| **🔞 AntiWords** | `!antiword` — bad word filter with warn/kick actions (like Levanter) |
| **🚫 AntiFake** | `!antifake` — block numbers from specific country codes (like Levanter) |
| **🔍 ISON** | `!ison <number>` — check if a phone number is on WhatsApp (like Levanter) |
| **📊 MSGS** | `!msgs` — group message stats per user (like Levanter) |
| **📩 PM Mode** | `!pdm on/off` — restrict PMs to group members only (like Levanter) |
| **🔘 Toggle** | `!tog <cmd> on/off` — enable/disable commands (like Levanter) |
| **📋 Variables** | `!setvar`, `!getvar`, `!delvar`, `!listvars` — per-session storage (like Levanter) |
| **📘 Facebook DL** | `!fb <url>` — download Facebook videos (like Levanter) |
| **📸 Story DL** | `!story <user>` — download Instagram/FB stories (like Levanter) |
| **🖥️ Screenshot** | `!ss <url>`, `!fullss <url>` — capture web pages (like Levanter) |
| **📱 QR Code** | `!qr <text>` — generate QR codes (like Levanter) |
| **📇 JID/Block** | `!jid`, `!block`, `!fullpp` — profile commands (like Levanter) |
| **🎨 Sticker Info** | `!exif` — view sticker metadata (like Levanter) |
| **🖼️ Remove BG** | `!rmbg` — remove image backgrounds (like Levanter) |
| **📦 APK DL** | `!apk <app>` — search APKMirror (like Levanter) |
| **Auto-Reply** | Keyword matching per language |
| **🌐 8 Languages** | EN · ES · HI · AR · FR · PT · DE · JA |
| **📊 Analytics** | Message stats, doughnut chart, top contacts chart |
| **📝 Message Templates** | Save reusable messages |
| **📱 QR in Dashboard** | Scan from web UI |
| **Auto-Reconnect** | Self-heals on disconnect |

---

## 🚀 One-Click Deploy

### 📱 Android (Termux) — Run on Your Phone!

```bash
# Install Termux from F-Droid, then:
pkg install git -y
git clone https://github.com/undisputedfoot/whatsapp-multi-bot
cd whatsapp-multi-bot
bash scripts/termux-setup.sh
python main.py
# Open http://localhost:5000 in Chrome
```

### ☁️ One-Click Deploy to Render (Free)

[![Deploy to Render](https://img.shields.io/badge/Deploy_to-Render-46E3B7?logo=render&style=for-the-badge)](https://render.com/deploy?repo=https://github.com/undisputedfoot/whatsapp-multi-bot)

Click the button above → connect your GitHub → **deploy is automatic**.

After deployment:
1. Go to your Render dashboard → open the app URL
2. Login: `admin` / `admin123`
3. Go to **Dashboard** tab → click the 📱 button on your session card
4. Scan the QR with WhatsApp → **done!**

> **Note:** On Render free tier, the bot will sleep after inactivity. Use a free uptime monitor like [UptimeRobot](https://uptimerobot.com) to keep it awake.

---

## 💻 Desktop Setup

### 🪟 Windows — Just double-click
```
1. Double-click  setup.bat     ← installs everything automatically
2. Double-click  start_bot.bat  ← starts the bot
3. Open http://localhost:5000  ← login: admin / admin123
```

### 🐧 Linux / macOS
```bash
git clone https://github.com/YOUR_USER/whatsapp-multi-bot
cd whatsapp-multi-bot
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
python main.py
```

---

## 🐳 Docker

```bash
docker compose up -d
```

---

## 🆕 New Features

### 💬 Web Inbox
Read all your WhatsApp conversations and reply directly from the web dashboard. No need to pick up your phone for every message.

### 🤖 AI Smart Replies
Enable AI replies per session. When someone messages you, the bot responds using OpenAI GPT or Google Gemini. Just set `AI_API_KEY` in `.env`:
```env
AI_PROVIDER=openai     # or "gemini" or "none"
AI_API_KEY=sk-...      # your API key
AI_MODEL=gpt-4o-mini   # or gemini-1.5-flash
```
Toggle with `!ai on/off` in chat or from the dashboard.

### 📅 Scheduled Messages
Send `!schedule 2025-12-25 09:00 Merry Christmas!` in any chat — the bot will queue it and send at the right time.

### 🎂 Birthday Reminders
Save contacts' birthdays from the Settings page. The bot auto-sends birthday wishes on the day.

### 📊 Analytics Dashboard
See message counts, top contacts, and activity trends for each session.

### 📝 Message Templates
Save common messages and reuse them from the settings panel.

### 📱 QR Code in Dashboard
Scan the QR code directly from the web UI — no terminal needed.

---

## ⚙️ Configuration

```env
# Language (en, es, hi, ar, fr, pt, de, ja)
BOT_LANGUAGE=en
# Multiple sessions
SESSION_NAMES=main,work,family
# AI (optional)
AI_PROVIDER=none
AI_API_KEY=
# Admin numbers (comma-separated, no +)
ADMIN_NUMBERS=15551234567,15559876543
# Group features
GROUP_WELCOME_ON=true
GROUP_ANTI_LINK=false
# Dashboard
DASHBOARD_USER=admin
DASHBOARD_PASS=admin123
```

---

## 🤖 AI Providers

The bot supports **4 AI providers** for smart replies:

| Provider | Config Value | API Key | Best For |
|---|---|---|---|
| **OpenAI** | `openai` | `AI_API_KEY` | GPT-4o, GPT-4o-mini |
| **OpenRouter** | `openrouter` | `AI_API_KEY` | Access 200+ models via one API |
| **Groq** | `groq` | `GROQ_API_KEY` | Lightning-fast inference (Llama, Mixtral) |
| **Google Gemini** | `gemini` | `AI_API_KEY` | Gemini Pro, Gemini Flash |

Set `AI_PROVIDER=openrouter` in `.env` to use OpenRouter (recommended — gives access to many models through one key).

```env
# OpenRouter (recommended — one key for 200+ models)
AI_PROVIDER=openrouter
AI_API_KEY=sk-or-...
AI_MODEL=openai/gpt-4o-mini

# OR Groq (blazing fast)
AI_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

# OR OpenAI
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini
```

Toggle AI on/off per session with `!ai on` / `!ai off` in WhatsApp, or from the dashboard.

---

## 🌐 Multi-Language (8 Languages)

| Command | Language |
|---|---|
| `!lang en` | 🇬🇧 English |
| `!lang es` | 🇪🇸 Spanish |
| `!lang hi` | 🇮🇳 Hindi |
| `!lang ar` | 🇸🇦 Arabic |
| `!lang fr` | 🇫🇷 French |
| `!lang pt` | 🇵🇹 Portuguese |
| `!lang de` | 🇩🇪 German |
| `!lang ja` | 🇯🇵 Japanese |

---

## 📋 Chat Commands

### General

| Command | What it does |
|---|---|
| `!help` | Show all commands |
| `!ping` | Is the bot alive? |
| `!sticker` | Create a sticker |
| `!lang xx` | Switch language |
| `!autoreply on/off/status` | Toggle keyword auto-reply |
| `!ai on/off/status` | Toggle AI replies |
| `!persona <name>` | Switch ChatGPT persona (friendly, formal, funny, etc.) |
| `!schedule DATE TIME MSG` | Schedule a message |
| `!update` | Git pull + restart *(admin)* |
| `!plugins` | List loaded plugins |
| `!weather <city>` | Get weather (from example plugin) |
| `!sessions` | List active sessions |

### 👥 Group Commands (in-group only)

| Command | What it does |
|---|---|
| `!grouprules` | Show group rules |
| `!groupwelcome <msg>` | Set welcome message *(admin)* |
| `!grouplink on/off` | Enable/disable anti-link *(admin)* |
| `!promote @user` | Promote to group admin *(admin)* |
| `!demote @user` | Demote from admin *(admin)* |
| `!kick @user` | Remove from group *(admin)* |
| `!groupstats` | Group activity stats |
| `!trivia` | Start a trivia game |
| `!wyr` | Would You Rather question |
| `!poll Q? \| Opt1 \| Opt2 \| Opt3` | Create a poll |

### 🛡️ Admin System

| Command | What it does |
|---|---|
| `!admins` | List all bot admins |
| `!addadmin +1234567` | Add a bot admin *(super-admin only)* |
| `!removeadmin +123` | Remove admin *(super-admin only)* |

### 📨 Broadcast

| Command | What it does |
|---|---|
| `!broadcast listname text` | Send message to a broadcast list *(admin)* |

---

## 🏗️ Project Structure

```
whatsapp-multi-bot/
├── main.py                  # Entry point
├── .env                     # Configuration
├── requirements.txt
├── Dockerfile / docker-compose.yml
├── core/
│   ├── whatsapp.py          # WhatsApp Web engine (Playwright Store injection)
│   ├── manager.py           # Multi-session manager
│   ├── config.py / lang.py  # Config & 8-language translations
│   ├── db.py                # SQLite (messages, contacts, scheduler, etc.)
│   └── features/
        ├── auto_reply.py      # Keyword auto-reply engine
        ├── ai_reply.py        # OpenAI / Gemini integration
        ├── scheduler.py       # Message scheduler + birthday reminders
        ├── auto_status.py     # Auto status viewer
        ├── read_receipts.py   # Blue ticks
        ├── call_blocker.py    # Call rejection
        ├── sticker_maker.py   # Stickers
        ├── group_manager.py   # Group welcome, anti-link, admin cmds
        ├── typing_engine.py   # Human-like typing delays
        ├── business_hours.py  # Business hours auto-reply
        ├── persona_manager.py # ChatGPT persona switcher
        ├── group_games.py     # Trivia, WYR, polls
        ├── plugin_loader.py   # Plugin discovery & loading
        └── auto_update.py     # Git pull + restart
├── plugins/
│   ├── __init__.py
│   └── weather.py         # Example: !weather command
├── web/
│   ├── app.py               # Flask + REST API + SocketIO
│   └── templates/
│       ├── dashboard.html   # Session status + QR viewer
│       ├── inbox.html       # Read & reply to messages        ├── groups.html      # Admin & broadcast management│       ├── analytics.html   # Stats & charts
│       └── settings.html    # Rules, templates, contacts
├── scripts/
│   └── termux-setup.sh      # Android one-command setup
└── data/                    # Sessions, DB, stickers
```

---

## 📄 License

MIT

---

<div align="center">
  <sub>⭐ Star this repo if you find it useful!</sub>
</div>
