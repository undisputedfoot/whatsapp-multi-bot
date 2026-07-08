"""
ChatGPT Persona Manager — per-session AI personalities.
Users can switch between different personas via !persona command.
"""

from .. import db
from ..config import PERSONA_DEFAULT, AI_SYSTEM_PROMPT


# Pre-built personas
BUILTIN_PERSONAS = {
    "default": {
        "name": "Default",
        "prompt": PERSONA_DEFAULT or AI_SYSTEM_PROMPT,
    },
    "friendly": {
        "name": "Friendly",
        "prompt": "You are a warm, friendly WhatsApp assistant. Use emojis, be encouraging, and chat like a good friend.",
    },
    "formal": {
        "name": "Formal",
        "prompt": "You are a professional business assistant. Respond formally and concisely. Avoid emojis. Use proper grammar.",
    },
    "funny": {
        "name": "Funny",
        "prompt": "You are a hilarious WhatsApp comedian. Be witty, use puns, and make the user laugh. Keep it clean and appropriate.",
    },
    "teacher": {
        "name": "Teacher",
        "prompt": "You are a patient, knowledgeable teacher. Explain concepts clearly. Use examples. Encourage learning.",
    },
    "spanish": {
        "name": "Spanish Tutor",
        "prompt": "You are a Spanish language tutor. Reply in Spanish, correct mistakes gently, and help the user learn. Be encouraging!",
    },
    "minimal": {
        "name": "Minimal",
        "prompt": "Reply as briefly as possible. One sentence max. No emojis. Just the facts.",
    },
}


class PersonaManager:
    """Manage AI personas per session."""

    def __init__(self, session_name: str):
        self.session = session_name
        self.current_persona = "default"

    def get_active_prompt(self) -> str:
        """Get the current persona's system prompt."""
        # Check custom DB-first
        personas = db.get_personas(self.session)
        for p in personas:
            if p["is_default"]:
                return p["prompt"]

        # Fall back to built-in
        persona = BUILTIN_PERSONAS.get(self.current_persona)
        if persona:
            return persona["prompt"]

        # Check custom named persona
        for p in personas:
            if p["name"].lower() == self.current_persona.lower():
                return p["prompt"]

        return PERSONA_DEFAULT or AI_SYSTEM_PROMPT

    def set_persona(self, name: str) -> bool:
        """Switch to a persona by name. Returns True if found."""
        name_lower = name.lower()
        # Check built-in
        if name_lower in BUILTIN_PERSONAS:
            self.current_persona = name_lower
            return True
        # Check custom
        personas = db.get_personas(self.session)
        for p in personas:
            if p["name"].lower() == name_lower:
                self.current_persona = p["name"]
                return True
        return False

    def list_personas(self) -> list[dict]:
        """List all available personas."""
        result = []
        for key, p in BUILTIN_PERSONAS.items():
            result.append({"name": p["name"], "key": key, "builtin": True})
        for p in db.get_personas(self.session):
            result.append({"name": p["name"], "key": p["name"], "builtin": False,
                          "prompt": p["prompt"][:60] + "..."})
        return result

    @staticmethod
    def get_all() -> dict:
        return BUILTIN_PERSONAS
