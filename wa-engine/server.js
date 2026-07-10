/**
 * WhatsApp Web Engine — Node.js microservice using whatsapp-web.js (Baileys)
 *
 * Communicates with the Python Flask dashboard via HTTP.
 * Runs on port 5001 by default.
 *
 * API:
 *   GET  /health              — Health check
 *   POST /start               — Start a WhatsApp session
 *   POST /stop                — Stop a session
 *   GET  /status              — All sessions status
 *   GET  /qr/:name            — Get QR code for a session (base64 PNG)
 *   GET  /poll/:name          — Get pending incoming messages
 *   POST /send                — Send a message
 *   POST /webhook             — Register webhook URL for incoming messages
 */

const express = require('express');
const cors = require('cors');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const path = require('path');
const fs = require('fs');

// ── Config ───────────────────────────────────────────
const PORT = process.env.WA_ENGINE_PORT || 5001;
const SESSIONS_DIR = path.join(__dirname, 'sessions');
const WEBHOOK_URL = process.env.WA_WEBHOOK_URL || '';

if (!fs.existsSync(SESSIONS_DIR)) fs.mkdirSync(SESSIONS_DIR, { recursive: true });

// ── State ────────────────────────────────────────────
const sessions = {};     // { name: { client, qr, ready, messages[], ... } }
let webhookUrl = WEBHOOK_URL;

// ── Express ──────────────────────────────────────────
const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// ── Helpers ──────────────────────────────────────────

function getSession(name) {
  if (!sessions[name]) {
    sessions[name] = {
      client: null,
      qr: null,
      ready: false,
      messages: [],
      started: false,
    };
  }
  return sessions[name];
}

// ── Create WhatsApp Client ───────────────────────────

function createClient(name) {
  const session = getSession(name);
  if (session.client) {
    try { session.client.destroy(); } catch(e) {}
  }

  const client = new Client({
    authStrategy: new LocalAuth({
      dataPath: path.join(SESSIONS_DIR, name),
    }),
    puppeteer: {
      headless: 'new',
      executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--no-first-run',
        '--single-process',
        '--disable-extensions',
        '--disable-background-networking',
        '--disable-software-rasterizer',
        '--disable-features=TranslateUI,BlinkGenPropertyTrees',
        '--disable-ipc-flooding-protection',
        '--memory-pressure-off',
        '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows',
        '--disable-hang-monitor',
        '--disable-sync',
        '--disable-default-apps',
        '--disable-component-update',
        '--disable-domain-reliability',
        '--disable-breakpad',
        '--disable-client-side-phishing-detection',
        '--no-zygote',
        '--window-size=360,640',
        '--max_old_space_size=128',
      ],
      defaultViewport: { width: 360, height: 640 },
    },
  });

  session.client = client;
  session.qr = null;
  session.ready = false;
  session.started = true;

  client.on('qr', async (qrCode) => {
    try {
      session.qr = await qrcode.toDataURL(qrCode);
      console.log(`[${name}] QR code generated`);
    } catch(e) {
      console.error(`[${name}] QR error:`, e.message);
    }
  });

  client.on('ready', () => {
    session.ready = true;
    session.qr = null;
    console.log(`[${name}] WhatsApp authenticated!`);
    sendWebhook({ type: 'ready', name });
  });

  client.on('authenticated', () => {
    console.log(`[${name}] Authenticated`);
  });

  client.on('auth_failure', (msg) => {
    console.error(`[${name}] Auth failure:`, msg);
  });

  client.on('disconnected', (reason) => {
    session.ready = false;
    console.log(`[${name}] Disconnected:`, reason);
    sendWebhook({ type: 'disconnected', name, reason });
    // Auto-reconnect after 5 seconds
    setTimeout(() => {
      if (session.started) {
        console.log(`[${name}] Reconnecting...`);
        client.initialize().catch(e => console.error(`[${name}] Reconnect error:`, e.message));
      }
    }, 5000);
  });

  client.on('message', async (msg) => {
    // Only process non-self messages with text
    if (msg.fromMe && !msg.hasMedia) return;
    if (!msg.body && !msg.hasMedia) return;

    const messageData = {
      id: msg.id._serialized,
      from: msg.from || msg.author,
      body: msg.body || '',
      timestamp: msg.timestamp || Math.floor(Date.now() / 1000),
      isGroup: msg.from ? msg.from.includes('@g.us') : false,
      fromMe: msg.fromMe || false,
      hasMedia: msg.hasMedia || false,
      type: msg.type || 'chat',
    };

    // Store for polling
    session.messages.push(messageData);
    // Keep max 200 messages
    if (session.messages.length > 200) {
      session.messages = session.messages.slice(-200);
    }

    // Also push via webhook
    sendWebhook({ type: 'message', name, message: messageData });

    console.log(`[${name}] ${msg.from ? msg.from.substring(0,15) : '?'}: ${(msg.body || '(media)').substring(0, 60)}`);
  });

  client.on('message_ack', (msg, ack) => {
    // Message delivery acknowledgment
  });

  client.initialize().catch(e => {
    console.error(`[${name}] Init error:`, e.message);
  });

  return client;
}

// ── Webhook ──────────────────────────────────────────

async function sendWebhook(data) {
  if (!webhookUrl) return;
  try {
    const http = webhookUrl.startsWith('https') ? require('https') : require('http');
    const payload = JSON.stringify(data);
    const url = new URL(webhookUrl);
    const opts = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) },
    };
    return new Promise((resolve) => {
      const req = http.request(opts, (res) => { res.resume(); resolve(); });
      req.on('error', () => resolve());
      req.write(payload);
      req.end();
    });
  } catch(e) {
    // Silently fail
  }
}

// ── API Routes ───────────────────────────────────────

// Health
app.get('/health', (req, res) => {
  res.json({ ok: true, sessions: Object.keys(sessions).length });
});

// Start session
app.post('/start', (req, res) => {
  const { name } = req.body;
  if (!name) return res.status(400).json({ error: 'Missing name' });

  const session = getSession(name);
  if (session.client) {
    return res.json({ status: 'already_running', name });
  }

  createClient(name);
  res.json({ status: 'started', name });
});

// Stop session
app.post('/stop', (req, res) => {
  const { name } = req.body;
  const session = sessions[name];
  if (!session || !session.client) {
    return res.status(404).json({ error: 'Session not found' });
  }
  session.started = false;
  session.client.destroy().catch(() => {});
  delete sessions[name];
  res.json({ status: 'stopped', name });
});

// Status
app.get('/status', (req, res) => {
  const result = {};
  for (const [name, session] of Object.entries(sessions)) {
    result[name] = {
      ready: session.ready || false,
      started: session.started || false,
      hasQR: !!session.qr,
    };
  }
  res.json(result);
});

// QR code
app.get('/qr/:name', (req, res) => {
  const session = sessions[req.params.name];
  if (!session) return res.json({ qr: null });
  res.json({ qr: session.qr || null });
});

// Poll for pending messages
app.get('/poll/:name', (req, res) => {
  const session = sessions[req.params.name];
  if (!session) return res.json({ messages: [] });
  const messages = session.messages;
  session.messages = [];
  res.json({ messages, ready: session.ready || false });
});

// Send message
app.post('/send', async (req, res) => {
  const { name, to, text, mentions } = req.body;
  if (!name || !to || !text) return res.status(400).json({ error: 'Missing fields' });

  const session = sessions[name];
  if (!session || !session.client || !session.ready) {
    return res.status(400).json({ error: 'Session not ready' });
  }

  try {
    const chatId = to.includes('@') ? to : `${to}@c.us`;
    const opts = {};
    if (mentions && Array.isArray(mentions) && mentions.length > 0) {
      opts.mentions = mentions.map(m => m.includes('@') ? m : `${m}@c.us`);
    }
    const response = await session.client.sendMessage(chatId, text, opts);
    res.json({ success: true, id: response.id._serialized });
  } catch(e) {
    res.status(500).json({ error: e.message });
  }
});

// Register webhook
app.post('/webhook', (req, res) => {
  const { url } = req.body;
  if (url) webhookUrl = url;
  res.json({ webhook: webhookUrl });
});

// ── Start Server ─────────────────────────────────────

app.listen(PORT, () => {
  console.log(`WA Engine running on port ${PORT}`);
  console.log(`Webhook: ${webhookUrl || 'not set'}`);

  // Auto-start sessions from env
  const autoSessions = (process.env.WA_SESSIONS || 'main').split(',');
  for (const name of autoSessions) {
    const n = name.trim();
    if (n) {
      console.log(`Auto-starting session: ${n}`);
      createClient(n);
    }
  }
});
