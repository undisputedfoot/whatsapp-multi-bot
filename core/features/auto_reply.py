"""
Auto-reply engine — keyword matching with multi-language rules.
Users can customise rules via the web dashboard (stored in DB).
"""

import json
from ..lang import t
from .. import db


# ── Default rules per language ────────────────────────

DEFAULT_RULES = {
    "en": [
        {"keywords": ["hello", "hi", "hey", "good morning", "good evening"], "response": "Hello! How can I help you today?"},
        {"keywords": ["bye", "goodbye", "see you", "later"], "response": "Goodbye! Have a great day!"},
        {"keywords": ["thanks", "thank you", "thx", "appreciate"], "response": "You're welcome! 😊"},
        {"keywords": ["help", "support", "issue", "problem"], "response": "I'm here to help! Type *!help* to see what I can do."},
        {"keywords": ["price", "cost", "rate", "pricing"], "response": "Please contact our team for pricing. Type *!help* for more info."},
        {"keywords": ["address", "location", "where"], "response": "We're located at 123 Main Street. Visit our website for directions!"},
    ],
    "es": [
        {"keywords": ["hola", "buenos días", "buenas", "hey"], "response": "¡Hola! ¿Cómo puedo ayudarte hoy?"},
        {"keywords": ["adiós", "chao", "nos vemos", "luego"], "response": "¡Adiós! ¡Que tengas un buen día!"},
        {"keywords": ["gracias", "muchas gracias", "te agradezco"], "response": "¡De nada! 😊"},
        {"keywords": ["ayuda", "soporte", "problema"], "response": "¡Estoy aquí para ayudar! Escribe *!help* para ver lo que puedo hacer."},
    ],
    "hi": [
        {"keywords": ["नमस्ते", "नमस्कार", "हैलो", "हाय"], "response": "नमस्ते! आज मैं आपकी कैसे मदद कर सकता हूँ?"},
        {"keywords": ["अलविदा", "फिर मिलेंगे", "बाद में"], "response": "अलविदा! आपका दिन शुभ हो!"},
        {"keywords": ["धन्यवाद", "शुक्रिया", "थैंक्यू"], "response": "आपका स्वागत है! 😊"},
        {"keywords": ["मदद", "सहायता", "समस्या"], "response": "मैं मदद के लिए यहाँ हूँ! *!help* टाइप करें।"},
    ],
    "ar": [
        {"keywords": ["مرحبا", "أهلا", "السلام عليكم"], "response": "مرحباً! كيف يمكنني مساعدتك اليوم؟"},
        {"keywords": ["وداعا", "مع السلامة", "بعدين"], "response": "وداعاً! أتمنى لك يوماً سعيداً!"},
        {"keywords": ["شكرا", "شكراً لك", "متشكر"], "response": "عفواً! 😊"},
        {"keywords": ["مساعدة", "الدعم", "مشكلة"], "response": "أنا هنا للمساعدة! اكتب *!help* لترى ما يمكنني فعله."},
    ],
}


class AutoReply:
    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)

    def _rules(self, lang: str) -> list[dict]:
        """Get rules: custom from DB first, then defaults."""
        custom = db.load_reply_rules(lang)
        return custom if custom else DEFAULT_RULES.get(lang, DEFAULT_RULES["en"])

    async def handle(self, body: str, sender: str, wapp, lang: str) -> bool:
        """Try to match *body* against rules. Returns True if replied."""
        lower = body.lower()
        for rule in self._rules(lang):
            for kw in rule["keywords"]:
                if kw.lower() in lower:
                    await wapp.send_text(sender, rule["response"])
                    self._log("auto_reply", f"Matched '{kw}' → replied to {sender}")
                    return True
        return False

    async def send_default(self, sender: str, wapp, lang: str):
        """Fallback when no rule matches."""
        await wapp.send_text(sender, t(lang, "greeting"))
        self._log("auto_reply", f"Default reply sent to {sender}")
