# 🚀 How to Run the WhatsApp Bot (No Tech Skills Needed)

## Windows — Just Two Clicks

### Step 1: Install Everything
> Double-click the file named **`setup.bat`**

A black window will open and install everything automatically. Wait until it says "Done!" — usually 2-3 minutes.

### Step 2: Start the Bot
> Double-click the file named **`start_bot.bat`**

A black window will open. The bot is now running!

### Step 3: Connect Your WhatsApp
> Open your browser and go to: **http://localhost:5000**

- Username: `admin`
- Password: `admin123`
- Click on a session card → scan the QR code with your WhatsApp phone app

### That's it! 🎉

---

## 📱 How to use (via WhatsApp)

Just send these commands from WhatsApp:

| Command | What it does |
|---------|-------------|
| `!help` | Show all commands |
| `!ping` | Check if bot is online |
| `!ai on` | Turn on AI smart replies |
| `!weather London` | Get weather |
| `!yt <link>` | Download YouTube video |
| `!tiktok <link>` | Download TikTok video |
| `!tagall` | Mention everyone in a group |
| `!warn @person` | Warn someone in a group |
| `!antiword add badword` | Block a bad word |
| `!ss google.com` | Take website screenshot |
| `!qr hello` | Make a QR code |
| `!fb <link>` | Download Facebook video |
| `!story username` | Get Instagram stories |
| `!pdm on` | Block unknown PMs |
| `!setcmd !hello Hello there!` | Create your own command |

---

## 📱 On Android (Termux)

### First time only:
```
curl -sSL https://raw.githubusercontent.com/undisputedfoot/whatsapp-multi-bot/main/setup_termux.sh | bash
```

### Every time after:
```
python main.py
```

---

## 🔧 If Something Goes Wrong

1. **Bot won't start?** — Make sure you ran `setup.bat` first
2. **QR code not showing?** — Refresh the browser page (F5)
3. **WhatsApp disconnected?** — Just scan the QR code again
4. **Want to stop the bot?** — Close the black window

---

## 🎯 Quick Tips

- Leave the black window open — that's the bot running
- The bot works 24/7 as long as the window is open
- You can connect multiple WhatsApp accounts — just scan again
- All your settings are saved automatically
