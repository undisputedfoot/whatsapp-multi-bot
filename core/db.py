"""
Lightweight SQLite store — sessions, chats, messages, scheduled tasks, contacts, and settings.
"""

import sqlite3
import json
from datetime import datetime
from .config import DB_PATH


def _conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def migrate():
    """Create / migrate all tables."""
    with _conn() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            name       TEXT PRIMARY KEY,
            status     TEXT DEFAULT 'offline',
            language   TEXT DEFAULT 'en',
            auto_reply INTEGER DEFAULT 1,
            ai_reply   INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS chats (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session    TEXT NOT NULL,
            peer       TEXT NOT NULL,
            name       TEXT,
            last_msg   TEXT,
            unread     INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(session, peer)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session    TEXT NOT NULL,
            peer       TEXT,
            direction  TEXT,
            body       TEXT,
            msg_id     TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS auto_reply_rules (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            keywords TEXT NOT NULL,
            response TEXT NOT NULL,
            lang     TEXT DEFAULT 'en'
        );

        CREATE TABLE IF NOT EXISTS scheduled_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session    TEXT NOT NULL,
            peer       TEXT NOT NULL,
            body       TEXT NOT NULL,
            send_at    TEXT NOT NULL,
            status     TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session     TEXT NOT NULL,
            peer        TEXT NOT NULL,
            name        TEXT,
            birthday    TEXT,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            UNIQUE(session, peer)
        );

        CREATE TABLE IF NOT EXISTS message_templates (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT UNIQUE NOT NULL,
            body    TEXT NOT NULL,
            lang    TEXT DEFAULT 'en'
        );

        CREATE TABLE IF NOT EXISTS group_config (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session     TEXT NOT NULL,
            group_id    TEXT NOT NULL,
            welcome_msg TEXT DEFAULT '',
            rules       TEXT DEFAULT '',
            anti_link   INTEGER DEFAULT 0,
            auto_reply  INTEGER DEFAULT 0,
            UNIQUE(session, group_id)
        );

        CREATE TABLE IF NOT EXISTS group_members (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session     TEXT NOT NULL,
            group_id    TEXT NOT NULL,
            peer        TEXT NOT NULL,
            role        TEXT DEFAULT 'member',
            msg_count   INTEGER DEFAULT 0,
            last_active TEXT,
            UNIQUE(session, group_id, peer)
        );

        CREATE TABLE IF NOT EXISTS admins (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session     TEXT NOT NULL,
            peer        TEXT NOT NULL,
            role        TEXT DEFAULT 'admin',
            added_at    TEXT DEFAULT (datetime('now')),
            UNIQUE(session, peer)
        );

        CREATE TABLE IF NOT EXISTS broadcast_lists (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            session TEXT NOT NULL,
            name    TEXT NOT NULL,
            members TEXT NOT NULL,  -- JSON array of peer numbers
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS media (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session     TEXT NOT NULL,
            peer        TEXT,
            file_path   TEXT NOT NULL,
            mime_type   TEXT,
            caption     TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS personas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session     TEXT NOT NULL,
            name        TEXT NOT NULL,
            prompt      TEXT NOT NULL,
            is_default  INTEGER DEFAULT 0,
            UNIQUE(session, name)
        );

        CREATE TABLE IF NOT EXISTS plugins (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT UNIQUE NOT NULL,
            enabled     INTEGER DEFAULT 1,
            version     TEXT DEFAULT '1.0',
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS business_hours (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session     TEXT NOT NULL,
            enabled     INTEGER DEFAULT 0,
            start_time  TEXT DEFAULT '09:00',
            end_time    TEXT DEFAULT '18:00',
            weekdays    TEXT DEFAULT '1,2,3,4,5',
            timezone    TEXT DEFAULT 'UTC',
            closed_msg  TEXT DEFAULT '',
            UNIQUE(session)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        """)


# ── Sessions ──────────────────────────────────────────

def upsert_session(name: str, **cols):
    cols["updated_at"] = datetime.utcnow().isoformat()
    sets = ", ".join(f"{k}=:{k}" for k in cols)
    with _conn() as db:
        db.execute(
            f"INSERT INTO sessions (name, {', '.join(cols)}) "
            f"VALUES (:name, {', '.join(':'+k for k in cols)}) "
            f"ON CONFLICT(name) DO UPDATE SET {sets}",
            {"name": name, **cols},
        )


def get_session(name: str) -> dict | None:
    with _conn() as db:
        row = db.execute("SELECT * FROM sessions WHERE name=?", (name,)).fetchone()
    return dict(row) if row else None


def all_sessions() -> list[dict]:
    with _conn() as db:
        return [dict(r) for r in db.execute("SELECT * FROM sessions ORDER BY name").fetchall()]


# ── Messages ──────────────────────────────────────────

def save_message(session: str, peer: str, direction: str, body: str, msg_id: str = ""):
    with _conn() as db:
        db.execute(
            "INSERT INTO messages (session, peer, direction, body, msg_id) VALUES (?, ?, ?, ?, ?)",
            (session, peer, direction, body, msg_id),
        )


def get_chat_history(session: str, peer: str, limit: int = 50) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM messages WHERE session=? AND peer=? ORDER BY created_at DESC LIMIT ?",
            (session, peer, limit),
        ).fetchall()
    return [dict(r) for r in rows][::-1]


def get_all_chats(session: str) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM chats WHERE session=? ORDER BY updated_at DESC", (session,)
        ).fetchall()
    return [dict(r) for r in rows]


def upsert_chat(session: str, peer: str, name: str = "", last_msg: str = "", unread: int = 0):
    with _conn() as db:
        db.execute(
            """INSERT INTO chats (session, peer, name, last_msg, unread, updated_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT(session, peer) DO UPDATE SET
               name=excluded.name, last_msg=excluded.last_msg,
               unread=excluded.unread, updated_at=datetime('now')""",
            (session, peer, name, last_msg, unread),
        )


# ── Auto-reply rules ─────────────────────────────────

def save_reply_rules(rules: list[dict], lang: str = "en"):
    with _conn() as db:
        db.execute("DELETE FROM auto_reply_rules WHERE lang=?", (lang,))
        for r in rules:
            db.execute(
                "INSERT INTO auto_reply_rules (keywords, response, lang) VALUES (?, ?, ?)",
                (json.dumps(r.get("keywords", [])), r["response"], lang),
            )


def load_reply_rules(lang: str = "en") -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT keywords, response FROM auto_reply_rules WHERE lang=?", (lang,)
        ).fetchall()
    return [{"keywords": json.loads(r["keywords"]), "response": r["response"]} for r in rows]


# ── Scheduled messages ───────────────────────────────

def add_scheduled(session: str, peer: str, body: str, send_at: str):
    with _conn() as db:
        db.execute(
            "INSERT INTO scheduled_messages (session, peer, body, send_at) VALUES (?, ?, ?, ?)",
            (session, peer, body, send_at),
        )


def get_pending_scheduled() -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM scheduled_messages WHERE status='pending' AND send_at <= datetime('now')"
        ).fetchall()
    return [dict(r) for r in rows]


def mark_scheduled_sent(msg_id: int):
    with _conn() as db:
        db.execute("UPDATE scheduled_messages SET status='sent' WHERE id=?", (msg_id,))


def get_all_scheduled(session: str) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM scheduled_messages WHERE session=? ORDER BY send_at DESC", (session,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Contacts & Birthdays ─────────────────────────────

def upsert_contact(session: str, peer: str, name: str = "", birthday: str = "", notes: str = ""):
    with _conn() as db:
        db.execute(
            """INSERT INTO contacts (session, peer, name, birthday, notes)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(session, peer) DO UPDATE SET
               name=excluded.name, birthday=excluded.birthday, notes=excluded.notes""",
            (session, peer, name, birthday, notes),
        )


def get_contacts(session: str) -> list[dict]:
    with _conn() as db:
        rows = db.execute("SELECT * FROM contacts WHERE session=? ORDER BY name", (session,)).fetchall()
    return [dict(r) for r in rows]


def get_todays_birthdays(session: str) -> list[dict]:
    today = datetime.utcnow().strftime("%m-%d")
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM contacts WHERE session=? AND birthday=?", (session, today)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Media Gallery ────────────────────────────────────

def save_media(session: str, file_path: str, peer: str = "", mime_type: str = "", caption: str = ""):
    with _conn() as db:
        db.execute(
            "INSERT INTO media (session, peer, file_path, mime_type, caption) VALUES (?, ?, ?, ?, ?)",
            (session, peer, file_path, mime_type, caption),
        )


def get_media(session: str, limit: int = 50) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM media WHERE session=? ORDER BY created_at DESC LIMIT ?",
            (session, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Personas ─────────────────────────────────────────

def save_persona(session: str, name: str, prompt: str, is_default: bool = False):
    with _conn() as db:
        if is_default:
            db.execute("UPDATE personas SET is_default=0 WHERE session=?", (session,))
        db.execute(
            "INSERT INTO personas (session, name, prompt, is_default) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(session, name) DO UPDATE SET prompt=excluded.prompt, is_default=excluded.is_default",
            (session, name, prompt, int(is_default)),
        )


def get_personas(session: str) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM personas WHERE session=? ORDER BY is_default DESC, name", (session,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_default_persona(session: str) -> str | None:
    with _conn() as db:
        row = db.execute(
            "SELECT prompt FROM personas WHERE session=? AND is_default=1", (session,)
        ).fetchone()
    return row["prompt"] if row else None


# ── Plugins ──────────────────────────────────────────

def register_plugin(name: str, version: str = "1.0"):
    with _conn() as db:
        db.execute(
            "INSERT INTO plugins (name, version) VALUES (?, ?) "
            "ON CONFLICT(name) DO UPDATE SET version=excluded.version",
            (name, version),
        )


def get_plugins() -> list[dict]:
    with _conn() as db:
        return [dict(r) for r in db.execute("SELECT * FROM plugins ORDER BY name").fetchall()]


def toggle_plugin(name: str, enabled: bool):
    with _conn() as db:
        db.execute("UPDATE plugins SET enabled=? WHERE name=?", (int(enabled), name))


# ── Business Hours ────────────────────────────────────

def upsert_business_hours(session: str, **cols):
    cols["session"] = session
    sets = ", ".join(f"{k}=:{k}" for k in cols if k != "session")
    with _conn() as db:
        db.execute(
            f"INSERT INTO business_hours (session, {', '.join(k for k in cols if k != 'session')}) "
            f"VALUES (:session, {', '.join(':'+k for k in cols if k != 'session')}) "
            f"ON CONFLICT(session) DO UPDATE SET {sets}",
            cols,
        )


def get_business_hours(session: str) -> dict | None:
    with _conn() as db:
        row = db.execute("SELECT * FROM business_hours WHERE session=?", (session,)).fetchone()
    return dict(row) if row else None


# ── Message Search ─────────────────────────────────────

def search_messages(session: str, query: str, limit: int = 50) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM messages WHERE session=? AND body LIKE ? ORDER BY created_at DESC LIMIT ?",
            (session, f"%{query}%", limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Message templates ────────────────────────────────

def save_template(name: str, body: str, lang: str = "en"):
    with _conn() as db:
        db.execute(
            "INSERT INTO message_templates (name, body, lang) VALUES (?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET body=excluded.body, lang=excluded.lang",
            (name, body, lang),
        )


def get_templates(lang: str = "en") -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT name, body FROM message_templates WHERE lang=? ORDER BY name", (lang,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Settings ──────────────────────────────────────────

def set_setting(key: str, value: str):
    with _conn() as db:
        db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?",
            (key, value, value),
        )


def get_setting(key: str, default: str = "") -> str:
    with _conn() as db:
        row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


# ── Group Configuration ───────────────────────────────

def upsert_group_config(session: str, group_id: str, **cols):
    sets = ", ".join(f"{k}=:{k}" for k in cols)
    cols["session"] = session
    cols["group_id"] = group_id
    with _conn() as db:
        db.execute(
            f"INSERT INTO group_config (session, group_id, {', '.join(k for k in cols if k not in ('session','group_id'))}) "
            f"VALUES (:session, :group_id, {', '.join(':'+k for k in cols if k not in ('session','group_id'))}) "
            f"ON CONFLICT(session, group_id) DO UPDATE SET {sets}",
            cols,
        )


def get_group_config(session: str, group_id: str) -> dict | None:
    with _conn() as db:
        row = db.execute(
            "SELECT * FROM group_config WHERE session=? AND group_id=?", (session, group_id)
        ).fetchone()
    return dict(row) if row else None


def get_all_groups(session: str) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM group_config WHERE session=? ORDER BY group_id", (session,)
        ).fetchall()
    return [dict(r) for r in rows]


def upsert_group_member(session: str, group_id: str, peer: str, role: str = "member"):
    with _conn() as db:
        db.execute(
            """INSERT INTO group_members (session, group_id, peer, role, last_active)
               VALUES (?, ?, ?, ?, datetime('now'))
               ON CONFLICT(session, group_id, peer) DO UPDATE SET
               role=excluded.role, last_active=datetime('now'),
               msg_count=msg_count+1""",
            (session, group_id, peer, role),
        )


def get_group_members(session: str, group_id: str) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM group_members WHERE session=? AND group_id=? ORDER BY msg_count DESC",
            (session, group_id),
        ).fetchall()
    return [dict(r) for r in rows]


def get_group_stats(session: str, group_id: str) -> dict:
    with _conn() as db:
        total = db.execute(
            "SELECT COUNT(*) as c FROM group_members WHERE session=? AND group_id=?",
            (session, group_id),
        ).fetchone()["c"]
        admins = db.execute(
            "SELECT COUNT(*) as c FROM group_members WHERE session=? AND group_id=? AND role='admin'",
            (session, group_id),
        ).fetchone()["c"]
    return {"total_members": total, "admins": admins}


# ── Admin system ──────────────────────────────────────

def add_admin(session: str, peer: str, role: str = "admin"):
    with _conn() as db:
        db.execute(
            "INSERT INTO admins (session, peer, role) VALUES (?, ?, ?) "
            "ON CONFLICT(session, peer) DO UPDATE SET role=excluded.role",
            (session, peer, role),
        )


def remove_admin(session: str, peer: str):
    with _conn() as db:
        db.execute("DELETE FROM admins WHERE session=? AND peer=?", (session, peer))


def get_admins(session: str) -> list[dict]:
    with _conn() as db:
        rows = db.execute("SELECT * FROM admins WHERE session=? ORDER BY role", (session,)).fetchall()
    return [dict(r) for r in rows]


def is_admin(session: str, peer: str) -> bool:
    with _conn() as db:
        row = db.execute(
            "SELECT 1 FROM admins WHERE session=? AND peer=?", (session, peer)
        ).fetchone()
        return row is not None


# ── Broadcast lists ───────────────────────────────────

def save_broadcast_list(session: str, name: str, members: list[str]):
    with _conn() as db:
        db.execute(
            "INSERT INTO broadcast_lists (session, name, members) VALUES (?, ?, ?) "
            "ON CONFLICT(session, name) DO UPDATE SET members=excluded.members",
            (session, name, json.dumps(members)),
        )


def get_broadcast_lists(session: str) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM broadcast_lists WHERE session=? ORDER BY name", (session,)
        ).fetchall()
    return [{"id": r["id"], "name": r["name"], "members": json.loads(r["members"])} for r in rows]


def delete_broadcast_list(list_id: int):
    with _conn() as db:
        db.execute("DELETE FROM broadcast_lists WHERE id=?", (list_id,))


# ── Analytics ─────────────────────────────────────────

def message_stats(session: str, days: int = 7) -> dict:
    with _conn() as db:
        inbound = db.execute(
            "SELECT COUNT(*) as c FROM messages WHERE session=? AND direction='in' AND created_at >= datetime('now', ?)",
            (session, f'-{days} days'),
        ).fetchone()["c"]
        outbound = db.execute(
            "SELECT COUNT(*) as c FROM messages WHERE session=? AND direction='out' AND created_at >= datetime('now', ?)",
            (session, f'-{days} days'),
        ).fetchone()["c"]
        top = db.execute(
            "SELECT peer, COUNT(*) as c FROM messages WHERE session=? AND created_at >= datetime('now', ?) GROUP BY peer ORDER BY c DESC LIMIT 10",
            (session, f'-{days} days'),
        ).fetchall()
    return {"inbound": inbound, "outbound": outbound, "total": inbound + outbound, "top_contacts": [dict(r) for r in top]}
