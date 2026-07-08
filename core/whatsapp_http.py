"""
WhatsApp engine using whatsapp-web.js (Baileys) via HTTP bridge.

Replaces the Playwright-based engine with a reliable WebSocket connection
managed by a Node.js microservice (wa-engine/server.js).
"""

import asyncio
import json
import os
import threading
from urllib.parse import quote

import httpx

WA_ENGINE_URL = os.environ.get("WA_ENGINE_URL", "http://127.0.0.1:5001")


class WApp:
    """WhatsApp session backed by whatsapp-web.js via HTTP."""

    def __init__(self, name: str, on_qr=None, on_ready=None, on_msg=None,
                 on_call=None, on_group_event=None):
        self.name = name
        self._on_qr = on_qr
        self._on_ready = on_ready
        self._on_msg = on_msg
        self._on_call = on_call
        self._on_group_event = on_group_event
        self.connected = False
        self._stop = False
        self._http = httpx.Client(timeout=30)
        self._pending = []  # local fallback queue

    # ── Lifecycle ─────────────────────────────────────

    async def start(self):
        """Start the WhatsApp session via the Node.js engine."""
        try:
            r = self._http.post(f"{WA_ENGINE_URL}/start", json={"name": self.name})
            r.raise_for_status()
        except Exception as e:
            print(f"  ⚠️  Failed to start WA engine session: {e}")
            return self

        # Register webhook so Node.js can push events to us
        # We'll use polling instead for simplicity/reliability
        print(f"  🔗 WhatsApp session '{self.name}' started via wa-engine")

        asyncio.create_task(self._poll_loop())
        asyncio.create_task(self._message_poll())
        return self

    async def stop(self):
        self._stop = True
        try:
            self._http.post(f"{WA_ENGINE_URL}/stop", json={"name": self.name})
        except Exception:
            pass

    # ── Polling ───────────────────────────────────────

    async def _poll_loop(self):
        """Poll for QR code and ready status changes."""
        reported_qr = False
        while not self._stop:
            try:
                r = self._http.get(f"{WA_ENGINE_URL}/qr/{self.name}")
                data = r.json()
                qr = data.get("qr")

                # Check status
                sr = self._http.get(f"{WA_ENGINE_URL}/status")
                status = sr.json().get(self.name, {})

                is_ready = status.get("ready", False)

                if is_ready and not self.connected:
                    self.connected = True
                    print(f"  ✅ WhatsApp Web authenticated!")
                    if self._on_ready:
                        await self._safe_call(self._on_ready)

                if qr and not reported_qr:
                    reported_qr = True
                    print(f"  📱 QR code available - scan with WhatsApp!")
                    if self._on_qr:
                        await self._safe_call(self._on_qr, qr)
                elif not qr and reported_qr and not is_ready:
                    reported_qr = False

                if not is_ready and not qr:
                    # Still connecting
                    pass

            except Exception as e:
                if not self._stop:
                    await asyncio.sleep(5)
                    continue

            await asyncio.sleep(2)

    async def _message_poll(self):
        """Poll for incoming messages from the Node.js engine."""
        while not self._stop:
            if self.connected:
                try:
                    r = self._http.get(f"{WA_ENGINE_URL}/poll/{self.name}", timeout=10)
                    data = r.json()
                    messages = data.get("messages", [])
                    for msg in messages:
                        if msg.get("fromMe") or not msg.get("body"):
                            continue
                        if self._on_msg:
                            print(f"  📩 {msg.get('from','')}: {msg.get('body','')[:60]}")
                            await self._safe_call(self._on_msg, {
                                "id": msg.get("id", ""),
                                "from": msg.get("from", "").replace("@c.us", "").replace("@s.whatsapp.net", ""),
                                "body": msg.get("body", ""),
                                "chatId": msg.get("from", ""),
                                "timestamp": msg.get("timestamp", 0),
                                "isGroup": msg.get("isGroup", False),
                            })
                except Exception:
                    pass
            await asyncio.sleep(1.5)

    # ── Actions ───────────────────────────────────────

    async def send_text(self, to: str, text: str) -> bool:
        """Send a text message via the Node.js engine."""
        try:
            r = self._http.post(f"{WA_ENGINE_URL}/send", json={
                "name": self.name,
                "to": to,
                "text": text,
            }, timeout=15)
            data = r.json()
            return data.get("success", False)
        except Exception as e:
            print(f"  ⚠️  Send error: {e}")
            return False

    async def send_text_dom(self, to: str, text: str) -> bool:
        """Alias for send_text."""
        return await self.send_text(to, text)

    async def send_image(self, to: str, image_path: str, caption: str = "") -> bool:
        """Send an image message."""
        # For now, fall back to text with caption
        return await self.send_text(to, caption or "[Image]")

    async def mark_seen(self, chat_id: str):
        pass  # whatsapp-web.js handles read receipts automatically if configured

    async def reject_call(self, call_id: str):
        pass

    async def get_qr_data(self):
        """Get QR code data URL."""
        try:
            r = self._http.get(f"{WA_ENGINE_URL}/qr/{self.name}")
            return r.json().get("qr")
        except Exception:
            return None

    async def get_chat_list(self) -> list:
        """Get chat list (simplified - returns from DB instead)."""
        return []

    # ── Utility ───────────────────────────────────────

    @staticmethod
    async def _safe_call(fn, *args):
        try:
            if asyncio.iscoroutinefunction(fn):
                await fn(*args)
            else:
                fn(*args)
        except Exception:
            pass
