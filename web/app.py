"""
Flask web dashboard — mobile-friendly control panel.
Features: live status, inbox, analytics, QR, scheduler, contacts, templates.
"""

import asyncio
import base64
import json
import threading
import re
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify, redirect, url_for,
    session as flask_session,
)
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Shared reference to the bot's asyncio event loop (set by main.py)
class _BotLoop:
    _loop = None
    def set(self, loop): self._loop = loop
    def get(self): return self._loop

bot_loop = _BotLoop()

from pathlib import Path
import core.config

from core.config import (DASHBOARD_PORT, DASHBOARD_HOST, DASHBOARD_USER,
                         DASHBOARD_PASS, SUPPORTED_LANGUAGES)
from core.manager import manager
from core.lang import supported_langs, lang_info
from core import db

# ── App ──────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = "wa-multi-bot-secret-change-in-prod"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


# ── Auth ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not flask_session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (request.form.get("user") == DASHBOARD_USER and
                request.form.get("pass") == DASHBOARD_PASS):
            flask_session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    flask_session.pop("logged_in", None)
    return redirect(url_for("login"))


# ── Pages ────────────────────────────────────────────

@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html", langs=supported_langs())


@app.route("/inbox")
@login_required
def inbox_page():
    sessions_data = manager.status_summary()
    return render_template("inbox.html", sessions=sessions_data, langs=supported_langs())


@app.route("/analytics")
@login_required
def analytics_page():
    return render_template("analytics.html", langs=supported_langs())


@app.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html", langs=supported_langs())


@app.route("/groups")
@login_required
def groups_page():
    return render_template("groups.html", langs=supported_langs())


@app.route("/media")
@login_required
def media_page():
    return render_template("media.html", langs=supported_langs())


@app.route("/search")
@login_required
def search_page():
    return render_template("search.html", langs=supported_langs())


# ── API: Status ──────────────────────────────────────

@app.route("/api/status")
@login_required
def api_status():
    sessions = manager.status_summary()
    return jsonify({
        "sessions": sessions,
        "total": len(sessions),
        "connected": sum(1 for s in sessions if s["connected"]),
        "logs": manager.logs[-50:],
    })


@app.route("/api/sessions")
@login_required
def api_sessions():
    return jsonify(manager.status_summary())


# ── API: QR Code ─────────────────────────────────────

@app.route("/api/qr/<name>")
@login_required
def api_qr(name):
    """Get QR code data URL for a session."""
    sess = manager.get_session(name)
    if not sess or not sess.wapp:
        return jsonify({"qr": None})
    loop = bot_loop.get()
    if not loop:
        return jsonify({"qr": None})
    try:
        future = asyncio.run_coroutine_threadsafe(sess.wapp.get_qr_data(), loop)
        qr = future.result(timeout=10)
        return jsonify({"qr": qr})
    except Exception:
        return jsonify({"qr": None})


# ── API: Session Actions ─────────────────────────────

@app.route("/api/session/<name>", methods=["POST"])
@login_required
def api_session_action(name):
    action = request.json.get("action", "")
    sess = manager.get_session(name)
    if not sess:
        return jsonify({"error": "Session not found"}), 404

    if action == "restart":
        threading.Thread(target=_restart_session, args=(name,), daemon=True).start()
        return jsonify({"ok": True, "message": f"Restarting {name}…"})
    elif action == "toggle_autoreply":
        sess.auto_reply_on = not sess.auto_reply_on
        db.upsert_session(name, auto_reply=int(sess.auto_reply_on))
        return jsonify({"ok": True, "auto_reply": sess.auto_reply_on})
    elif action == "toggle_ai":
        sess.ai_reply_on = not sess.ai_reply_on
        db.upsert_session(name, ai_reply=int(sess.ai_reply_on))
        return jsonify({"ok": True, "ai_reply": sess.ai_reply_on})
    elif action == "set_lang":
        lang = request.json.get("lang", "en")
        if lang in supported_langs():
            sess.lang = lang
            db.upsert_session(name, language=lang)
            return jsonify({"ok": True, "lang": lang})
        return jsonify({"error": "Unsupported language"}), 400
    return jsonify({"error": "Unknown action"}), 400


# ── API: Logs ────────────────────────────────────────

@app.route("/api/logs")
@login_required
def api_logs():
    return jsonify(manager.logs[-100:])


# ── API: Inbox / Chat Messages ───────────────────────

@app.route("/api/chats/<session_name>")
@login_required
def api_chats(session_name):
    """Get all recent chats for a session."""
    return jsonify(db.get_all_chats(session_name))


@app.route("/api/chat/<session_name>/<path:peer>")
@login_required
def api_chat_history(session_name, peer):
    """Get message history for a specific contact."""
    return jsonify(db.get_chat_history(session_name, peer))


@app.route("/api/send", methods=["POST"])
@login_required
def api_send():
    """Send a message from the inbox."""
    data = request.json
    session_name = data.get("session", "")
    peer = data.get("peer", "")
    text = data.get("text", "")
    if not session_name or not peer or not text:
        return jsonify({"error": "Missing fields"}), 400
    sess = manager.get_session(session_name)
    if not sess or not sess.wapp:
        return jsonify({"error": "Session offline"}), 400
    loop = asyncio.new_event_loop()
    try:
        ok = loop.run_until_complete(sess.wapp.send_text(peer, text))
        if ok:
            db.save_message(session_name, peer, "out", text)
            db.upsert_chat(session_name, peer, last_msg=text[:80])
        return jsonify({"ok": ok})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        loop.close()


# ── API: Auto-Reply Rules ────────────────────────────

@app.route("/api/reply-rules", methods=["GET", "POST"])
@login_required
def api_reply_rules():
    if request.method == "POST":
        data = request.json
        db.save_reply_rules(data.get("rules", []), data.get("lang", "en"))
        return jsonify({"ok": True})
    lang = request.args.get("lang", "en")
    return jsonify({"rules": db.load_reply_rules(lang)})


# ── API: Scheduled Messages ──────────────────────────

@app.route("/api/scheduled/<session_name>")
@login_required
def api_scheduled(session_name):
    return jsonify(db.get_all_scheduled(session_name))


@app.route("/api/scheduled", methods=["POST"])
@login_required
def api_add_scheduled():
    data = request.json
    db.add_scheduled(data["session"], data["peer"], data["body"], data["send_at"])
    return jsonify({"ok": True})


# ── API: Contacts & Birthdays ────────────────────────

@app.route("/api/contacts/<session_name>")
@login_required
def api_contacts(session_name):
    return jsonify(db.get_contacts(session_name))


@app.route("/api/contacts", methods=["POST"])
@login_required
def api_add_contact():
    data = request.json
    db.upsert_contact(
        data["session"], data["peer"],
        name=data.get("name", ""),
        birthday=data.get("birthday", ""),
        notes=data.get("notes", ""),
    )
    return jsonify({"ok": True})


# ── API: Message Templates ───────────────────────────

@app.route("/api/templates", methods=["GET", "POST"])
@login_required
def api_templates():
    if request.method == "POST":
        data = request.json
        db.save_template(data["name"], data["body"], data.get("lang", "en"))
        return jsonify({"ok": True})
    lang = request.args.get("lang", "en")
    return jsonify({"templates": db.get_templates(lang)})


# ── API: Groups ──────────────────────────────────────

@app.route("/api/groups/<session_name>")
@login_required
def api_groups(session_name):
    """Get all group configs for a session."""
    return jsonify(db.get_all_groups(session_name))


@app.route("/api/group-config", methods=["POST"])
@login_required
def api_group_config():
    """Update group config (welcome msg, rules, anti-link)."""
    data = request.json
    db.upsert_group_config(
        data["session"], data["group_id"],
        welcome_msg=data.get("welcome_msg", ""),
        rules=data.get("rules", ""),
        anti_link=int(data.get("anti_link", False)),
    )
    return jsonify({"ok": True})


@app.route("/api/group-members/<session_name>/<path:group_id>")
@login_required
def api_group_members(session_name, group_id):
    """Get group members with activity stats."""
    return jsonify(db.get_group_members(session_name, group_id))


@app.route("/api/group-stats/<session_name>/<path:group_id>")
@login_required
def api_group_stats(session_name, group_id):
    return jsonify(db.get_group_stats(session_name, group_id))


# ── API: Admins ──────────────────────────────────────

@app.route("/api/admins/<session_name>")
@login_required
def api_admins(session_name):
    return jsonify(db.get_admins(session_name))


@app.route("/api/admins", methods=["POST"])
@login_required
def api_add_admin_api():
    data = request.json
    db.add_admin(data["session"], data["peer"], data.get("role", "admin"))
    return jsonify({"ok": True})


@app.route("/api/admins/<session_name>/<path:peer>", methods=["DELETE"])
@login_required
def api_remove_admin_api(session_name, peer):
    db.remove_admin(session_name, peer)
    return jsonify({"ok": True})


# ── API: Broadcast Lists ─────────────────────────────

@app.route("/api/broadcast-lists/<session_name>")
@login_required
def api_broadcast_lists(session_name):
    return jsonify(db.get_broadcast_lists(session_name))


@app.route("/api/broadcast-lists", methods=["POST"])
@login_required
def api_save_broadcast_list():
    data = request.json
    db.save_broadcast_list(data["session"], data["name"], data["members"])
    return jsonify({"ok": True})


@app.route("/api/broadcast-lists/<int:list_id>", methods=["DELETE"])
@login_required
def api_delete_broadcast_list(list_id):
    db.delete_broadcast_list(list_id)
    return jsonify({"ok": True})


# ── API: Media Gallery ───────────────────────────────

@app.route("/api/media/<session_name>")
@login_required
def api_media(session_name):
    return jsonify(db.get_media(session_name))


@app.route("/media-file/<path:filepath>")
@login_required
def api_media_file(filepath):
    """Serve media files."""
    from flask import send_file
    from core.config import MEDIA_DIR
    full_path = MEDIA_DIR / filepath
    if full_path.exists():
        return send_file(str(full_path))
    return "File not found", 404


# ── API: Message Search ─────────────────────────────

@app.route("/api/search/<session_name>")
@login_required
def api_search(session_name):
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    return jsonify(db.search_messages(session_name, q))


# ── API: Personas ────────────────────────────────────

@app.route("/api/personas/<session_name>")
@login_required
def api_personas(session_name):
    from core.features.persona_manager import PersonaManager
    pm = PersonaManager(session_name)
    return jsonify(pm.list_personas())


@app.route("/api/personas", methods=["POST"])
@login_required
def api_save_persona():
    data = request.json
    db.save_persona(data["session"], data["name"], data["prompt"],
                    data.get("is_default", False))
    return jsonify({"ok": True})


# ── API: Business Hours ──────────────────────────────

@app.route("/api/business-hours/<session_name>")
@login_required
def api_business_hours(session_name):
    cfg = db.get_business_hours(session_name)
    return jsonify(cfg or {})


@app.route("/api/business-hours", methods=["POST"])
@login_required
def api_save_business_hours():
    data = request.json
    db.upsert_business_hours(
        data["session"],
        enabled=int(data.get("enabled", False)),
        start_time=data.get("start_time", "09:00"),
        end_time=data.get("end_time", "18:00"),
        weekdays=data.get("weekdays", "1,2,3,4,5"),
        timezone=data.get("timezone", "UTC"),
        closed_msg=data.get("closed_msg", ""),
    )
    return jsonify({"ok": True})


# ── API: Plugins ─────────────────────────────────────

@app.route("/api/plugins")
@login_required
def api_plugins():
    return jsonify({"plugins": db.get_plugins(), "available": [
        {"name": p.stem} for p in Path(core.config.PLUGIN_DIR).glob("*.py")
        if p.stem != "__init__"
    ]})


@app.route("/api/plugins/<name>/toggle", methods=["POST"])
@login_required
def api_toggle_plugin(name):
    data = request.json
    db.toggle_plugin(name, data.get("enabled", True))
    return jsonify({"ok": True})


# ── API: Chat Export ─────────────────────────────────

@app.route("/api/export/<session_name>/<path:peer>")
@login_required
def api_export_chat(session_name, peer):
    """Export chat as JSON."""
    msgs = db.get_chat_history(session_name, peer, limit=1000)
    from flask import Response
    import json
    return Response(
        json.dumps(msgs, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=chat-{peer}.json"},
    )


# ── API: Analytics ───────────────────────────────────

@app.route("/api/analytics/<session_name>")
@login_required
def api_analytics(session_name):
    days = int(request.args.get("days", 7))
    stats = db.message_stats(session_name, days)
    scheduled = len(db.get_all_scheduled(session_name))
    contacts = len(db.get_contacts(session_name))
    stats["scheduled"] = scheduled
    stats["contacts"] = contacts
    return jsonify(stats)


# ── Helpers ──────────────────────────────────────────

def _restart_session(name: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    sess = manager.get_session(name)
    if sess:
        loop.run_until_complete(sess.stop())
        loop.run_until_complete(sess.start())
    loop.close()


@socketio.on("connect")
def handle_connect():
    emit("status", {"msg": "Connected"})


# ── Serve ────────────────────────────────────────────

def run(host: str = None, port: int = None):
    host = host or DASHBOARD_HOST
    port = port or DASHBOARD_PORT
    print(f"🌐 Dashboard: http://{host}:{port}")
    print(f"   Login: {DASHBOARD_USER} / {DASHBOARD_PASS}")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
