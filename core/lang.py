"""
Multi-language engine — English, Spanish, Hindi, Arabic.
Every user-facing string lives here.
"""

STRINGS = {
    "en": {
        "name": "English",
        "native": "English",
        "bot_starting": "🤖 WhatsApp Multi-Bot starting up…",
        "session_init": "🔄 Initialising session: {name}",
        "session_ready": "✅ {name} is connected!",
        "qr_scan": "📱 Scan the QR code for {name}",
        "session_down": "⚠️ {name} disconnected — reconnecting…",
        "call_rejected": "📞 Call from {number} rejected.",
        "status_viewed": "👁️ Viewed {name}'s status",
        "sticker_ok": "✅ Sticker created!",
        "sticker_fail": "❌ Could not create sticker. Reply to an image/video.",
        "sticker_working": "⏳ Making your sticker…",
        "auto_on": "✅ Auto-reply ON",
        "auto_off": "✅ Auto-reply OFF",
        "ai_on": "✅ AI replies ON",
        "ai_off": "✅ AI replies OFF",
        "help_title": "📋 *Available Commands*",
        "help_body": (
            "!help         — this message\n"
            "!ping         — bot health check\n"
            "!sticker      — sticker from replied media\n"
            "!lang xx      — switch language\n"
            "!autoreply    — on/off/status\n"
            "!ai           — on/off/status\n"
            "!schedule     — schedule a message\n"
            "!sessions     — list active sessions\n\n"
            "📋 *Group Commands:*\n"
            "!grouprules   — show group rules\n"
            "!groupwelcome — set welcome msg (admin)\n"
            "!grouplink on/off — anti-link (admin)\n"
            "!promote @user — promote to admin (admin)\n"
            "!demote @user — demote (admin)\n"
            "!kick @user   — remove from group (admin)\n"
            "!groupstats   — group activity stats\n\n"
            "🛡️ *Admin System:*\n"
            "!admins       — list bot admins\n"
            "!addadmin +123 — add bot admin (super)\n"
            "!removeadmin +123 — remove (super)\n\n"
            "📨 *Broadcast:*\n"
            "!broadcast listname text\n"
        ),
        "pong": "🏓 Pong!  {n} session(s) active.",
        "session_list": "📡 Sessions:\n{sessions}",
        "no_sessions": "No active sessions.",
        "not_found": "Sorry, I didn't understand. Try !help",
        "bye": "Goodbye!",
        "greeting": "Hello! How can I help?",
        "schedule_help": "Send a date + message like:\n!schedule 2025-12-25 09:00 Merry Christmas!",
        "schedule_done": "✅ Scheduled for {time}",
        "schedule_list": "📅 Scheduled:\n{items}",
        "schedule_empty": "No scheduled messages.",
        "birthday_wish": "🎂 Happy Birthday {name}! 🎉",
        "lang_prompt": "Supported: en, es, hi, ar, fr, pt, de, ja",
    },
    "es": {
        "name": "Spanish",
        "native": "Español",
        "bot_starting": "🤖 WhatsApp Multi-Bot iniciando…",
        "session_init": "🔄 Iniciando sesión: {name}",
        "session_ready": "✅ ¡{name} conectada!",
        "qr_scan": "📱 Escanea el código QR para {name}",
        "session_down": "⚠️ {name} desconectada — reconectando…",
        "call_rejected": "📞 Llamada de {number} rechazada.",
        "status_viewed": "👁️ Estado visto de {name}",
        "sticker_ok": "✅ ¡Sticker creado!",
        "sticker_fail": "❌ No se pudo crear el sticker. Responde a una imagen/video.",
        "sticker_working": "⏳ Creando sticker…",
        "auto_on": "✅ Respuesta automática ACTIVADA",
        "auto_off": "✅ Respuesta automática DESACTIVADA",
        "help_title": "📋 *Comandos Disponibles*",
        "help_body": (
            "!help     — este mensaje\n"
            "!ping     — estado del bot\n"
            "!sticker  — sticker desde multimedia\n"
            "!lang xx  — cambiar idioma (en/es/hi/ar)\n"
            "!autoreply on/off/status\n"
            "!sessions — sesiones activas"
        ),
        "pong": "🏓 ¡Pong!  {n} sesión(es) activa(s).",
        "session_list": "📡 Sesiones:\n{sessions}",
        "no_sessions": "No hay sesiones activas.",
        "not_found": "Lo siento, no entendí. Prueba !help",
        "bye": "¡Adiós!",
        "greeting": "¡Hola! ¿Cómo puedo ayudarte?",
    },
    "hi": {
        "name": "Hindi",
        "native": "हिन्दी",
        "bot_starting": "🤖 WhatsApp मल्टी-बॉट शुरू हो रहा है…",
        "session_init": "🔄 सत्र आरंभ: {name}",
        "session_ready": "✅ {name} कनेक्टेड!",
        "qr_scan": "📱 {name} के लिए QR कोड स्कैन करें",
        "session_down": "⚠️ {name} डिस्कनेक्ट — पुनः कनेक्ट…",
        "call_rejected": "📞 {number} से कॉल अस्वीकृत।",
        "status_viewed": "👁️ {name} का स्टेटस देखा",
        "sticker_ok": "✅ स्टिकर बन गया!",
        "sticker_fail": "❌ स्टिकर नहीं बना। इमेज/वीडियो का रिप्लाई करें।",
        "sticker_working": "⏳ स्टिकर बन रहा है…",
        "auto_on": "✅ ऑटो-रिप्लाई चालू",
        "auto_off": "✅ ऑटो-रिप्लाई बंद",
        "help_title": "📋 *उपलब्ध कमांड*",
        "help_body": (
            "!help     — यह संदेश\n"
            "!ping     — बॉट की स्थिति\n"
            "!sticker  — मीडिया से स्टिकर\n"
            "!lang xx  — भाषा बदलें (en/es/hi/ar)\n"
            "!autoreply on/off/status\n"
            "!sessions — सक्रिय सत्र"
        ),
        "pong": "🏓 पोंग!  {n} सत्र सक्रिय।",
        "session_list": "📡 सत्र:\n{sessions}",
        "no_sessions": "कोई सक्रिय सत्र नहीं।",
        "not_found": "क्षमा करें, समझ नहीं आया। !help टाइप करें।",
        "bye": "अलविदा!",
        "greeting": "नमस्ते! कैसे मदद करूँ?",
    },
    "ar": {
        "name": "Arabic",
        "native": "العربية",
        "bot_starting": "🤖 واتساب مالتى-بوت قيد التشغيل…",
        "session_init": "🔄 جلسة {name} قيد الإعداد…",
        "session_ready": "✅ {name} متصلة!",
        "qr_scan": "📱 امسح رمز QR لـ {name}",
        "session_down": "⚠️ {name} غير متصلة — إعادة الاتصال…",
        "call_rejected": "📞 مكالمة من {number} مرفوضة.",
        "status_viewed": "👁️ تم عرض حالة {name}",
        "sticker_ok": "✅ تم إنشاء الملصق!",
        "sticker_fail": "❌ فشل إنشاء الملصق. رد على صورة/فيديو.",
        "sticker_working": "⏳ جاري إنشاء الملصق…",
        "auto_on": "✅ الرد التلقائي مفعّل",
        "auto_off": "✅ الرد التلقائي معطّل",
        "help_title": "📋 *الأوامر المتاحة*",
        "help_body": (
            "!help     — هذه الرسالة\n"
            "!ping     — فحص البوت\n"
            "!sticker  — ملصق من وسائط\n"
            "!lang xx  — تغيير اللغة (en/es/hi/ar)\n"
            "!autoreply on/off/status\n"
            "!sessions — الجلسات النشطة"
        ),
        "pong": "🏓 بونغ!  {n} جلسة نشطة.",
        "session_list": "📡 الجلسات:\n{sessions}",
        "no_sessions": "لا توجد جلسات نشطة.",
        "not_found": "عذراً، لم أفهم. جرب !help",
        "bye": "مع السلامة!",
        "greeting": "مرحباً! كيف يمكنني المساعدة؟",
        "schedule_help": "أرسل تاريخاً ورسالة مثل:\n!schedule 2025-12-25 09:00 عيد ميلاد مجيد!",
        "schedule_done": "✅ تم الجدولة لـ {time}",
        "schedule_list": "📅 المجدول:\n{items}",
        "schedule_empty": "لا توجد رسائل مجدولة.",
        "birthday_wish": "🎂 عيد ميلاد سعيد {name}! 🎉",
        "lang_prompt": "المدعومة: en, es, hi, ar, fr, pt, de, ja",
    },
    "fr": {
        "name": "French",
        "native": "Français",
        "bot_starting": "🤖 WhatsApp Multi-Bot démarre…",
        "session_init": "🔄 Initialisation de {name}…",
        "session_ready": "✅ {name} est connecté !",
        "qr_scan": "📱 Scannez le QR code pour {name}",
        "session_down": "⚠️ {name} déconnecté — reconnexion…",
        "call_rejected": "📞 Appel de {number} rejeté.",
        "status_viewed": "👁️ Statut de {name} vu",
        "sticker_ok": "✅ Sticker créé !",
        "sticker_fail": "❌ Échec du sticker. Répondez à une image/vidéo.",
        "sticker_working": "⏳ Création du sticker…",
        "auto_on": "✅ Réponse auto. ACTIVÉE",
        "auto_off": "✅ Réponse auto. DÉSACTIVÉE",
        "ai_on": "✅ Réponses IA ACTIVÉES",
        "ai_off": "✅ Réponses IA DÉSACTIVÉES",
        "help_title": "📋 *Commandes Disponibles*",
        "help_body": (
            "!help       — cette aide\n"
            "!ping       — état du bot\n"
            "!sticker    — sticker depuis un média\n"
            "!lang xx    — changer la langue\n"
            "!autoreply  — on/off/status\n"
            "!ai         — on/off/status\n"
            "!schedule   — messages programmés\n"
            "!sessions   — sessions actives"
        ),
        "pong": "🏓 Pong !  {n} session(s) active(s).",
        "session_list": "📡 Sessions :\n{sessions}",
        "no_sessions": "Aucune session active.",
        "not_found": "Désolé, je n'ai pas compris. Essayez !help",
        "bye": "Au revoir !",
        "greeting": "Bonjour ! Comment puis-je vous aider ?",
        "schedule_help": "Envoyez une date + message comme :\n!schedule 2025-12-25 09:00 Joyeux Noël !",
        "schedule_done": "✅ Programmée pour {time}",
        "schedule_list": "📅 Programmées :\n{items}",
        "schedule_empty": "Aucun message programmé.",
        "birthday_wish": "🎂 Joyeux Anniversaire {name} ! 🎉",
        "lang_prompt": "Supportées : en, es, hi, ar, fr, pt, de, ja",
    },
    "pt": {
        "name": "Portuguese",
        "native": "Português",
        "bot_starting": "🤖 WhatsApp Multi-Bot iniciando…",
        "session_init": "🔄 Iniciando sessão: {name}…",
        "session_ready": "✅ {name} está conectado!",
        "qr_scan": "📱 Escaneie o QR code para {name}",
        "session_down": "⚠️ {name} desconectado — reconectando…",
        "call_rejected": "📞 Chamada de {number} rejeitada.",
        "status_viewed": "👁️ Status de {name} visto",
        "sticker_ok": "✅ Sticker criado!",
        "sticker_fail": "❌ Erro ao criar sticker. Responda a uma imagem/vídeo.",
        "sticker_working": "⏳ Criando sticker…",
        "auto_on": "✅ Resposta automática LIGADA",
        "auto_off": "✅ Resposta automática DESLIGADA",
        "ai_on": "✅ Respostas IA LIGADAS",
        "ai_off": "✅ Respostas IA DESLIGADAS",
        "help_title": "📋 *Comandos Disponíveis*",
        "help_body": (
            "!help       — esta ajuda\n"
            "!ping       — verificar bot\n"
            "!sticker    — sticker de mídia\n"
            "!lang xx    — trocar idioma\n"
            "!autoreply  — on/off/status\n"
            "!ai         — on/off/status\n"
            "!schedule   — mensagens agendadas\n"
            "!sessions   — sessões ativas"
        ),
        "pong": "🏓 Pong!  {n} sessão(ões) ativa(s).",
        "session_list": "📡 Sessões:\n{sessions}",
        "no_sessions": "Nenhuma sessão ativa.",
        "not_found": "Desculpe, não entendi. Tente !help",
        "bye": "Tchau!",
        "greeting": "Olá! Como posso ajudar?",
        "schedule_help": "Envie data + mensagem como:\n!schedule 2025-12-25 09:00 Feliz Natal!",
        "schedule_done": "✅ Agendada para {time}",
        "schedule_list": "📅 Agendadas:\n{items}",
        "schedule_empty": "Nenhuma mensagem agendada.",
        "birthday_wish": "🎂 Feliz Aniversário {name}! 🎉",
        "lang_prompt": "Suportados: en, es, hi, ar, fr, pt, de, ja",
    },
    "de": {
        "name": "German",
        "native": "Deutsch",
        "bot_starting": "🤖 WhatsApp Multi-Bot startet…",
        "session_init": "🔄 Initialisiere {name}…",
        "session_ready": "✅ {name} ist verbunden!",
        "qr_scan": "📱 Scanne den QR-Code für {name}",
        "session_down": "⚠️ {name} getrennt — Verbinde neu…",
        "call_rejected": "📞 Anruf von {number} abgelehnt.",
        "status_viewed": "👁️ Status von {name} angesehen",
        "sticker_ok": "✅ Sticker erstellt!",
        "sticker_fail": "❌ Sticker-Fehler. Antworte auf ein Bild/Video.",
        "sticker_working": "⏳ Erstelle Sticker…",
        "auto_on": "✅ Auto-Antwort EIN",
        "auto_off": "✅ Auto-Antwort AUS",
        "ai_on": "✅ KI-Antworten EIN",
        "ai_off": "✅ KI-Antworten AUS",
        "help_title": "📋 *Verfügbare Befehle*",
        "help_body": (
            "!help       — diese Hilfe\n"
            "!ping       — Bot-Status\n"
            "!sticker    — Sticker aus Medien\n"
            "!lang xx    — Sprache wechseln\n"
            "!autoreply  — on/off/status\n"
            "!ai         — on/off/status\n"
            "!schedule   — geplante Nachrichten\n"
            "!sessions   — aktive Sitzungen"
        ),
        "pong": "🏓 Pong!  {n} Sitzung(en) aktiv.",
        "session_list": "📡 Sitzungen:\n{sessions}",
        "no_sessions": "Keine aktiven Sitzungen.",
        "not_found": "Entschuldigung, nicht verstanden. Versuche !help",
        "bye": "Tschüss!",
        "greeting": "Hallo! Wie kann ich helfen?",
        "schedule_help": "Sende Datum + Nachricht wie:\n!schedule 2025-12-25 09:00 Frohe Weihnachten!",
        "schedule_done": "✅ Geplant für {time}",
        "schedule_list": "📅 Geplant:\n{items}",
        "schedule_empty": "Keine geplanten Nachrichten.",
        "birthday_wish": "🎂 Alles Gute zum Geburtstag {name}! 🎉",
        "lang_prompt": "Unterstützt: en, es, hi, ar, fr, pt, de, ja",
    },
    "ja": {
        "name": "Japanese",
        "native": "日本語",
        "bot_starting": "🤖 WhatsApp Multi-Bot 起動中…",
        "session_init": "🔄 セッション {name} を初期化中…",
        "session_ready": "✅ {name} が接続されました！",
        "qr_scan": "📱 {name} のQRコードをスキャン",
        "session_down": "⚠️ {name} が切断されました — 再接続中…",
        "call_rejected": "📞 {number} からの着信を拒否しました。",
        "status_viewed": "👁️ {name} のステータスを表示",
        "sticker_ok": "✅ ステッカーを作成しました！",
        "sticker_fail": "❌ ステッカーの作成に失敗。画像/動画に返信してください。",
        "sticker_working": "⏳ ステッカーを作成中…",
        "auto_on": "✅ 自動返信 ON",
        "auto_off": "✅ 自動返信 OFF",
        "ai_on": "✅ AI返信 ON",
        "ai_off": "✅ AI返信 OFF",
        "help_title": "📋 *使用可能なコマンド*",
        "help_body": (
            "!help       — このヘルプ\n"
            "!ping       — ボットの状態\n"
            "!sticker    — メディアからステッカー\n"
            "!lang xx    — 言語を変更\n"
            "!autoreply  — on/off/status\n"
            "!ai         — on/off/status\n"
            "!schedule   — 予約メッセージ\n"
            "!sessions   — アクティブなセッション"
        ),
        "pong": "🏓 ポン！ {n} セッションがアクティブです。",
        "session_list": "📡 セッション:\n{sessions}",
        "no_sessions": "アクティブなセッションがありません。",
        "not_found": "すみません、理解できませんでした。!help を試してください。",
        "bye": "さようなら！",
        "greeting": "こんにちは！どのようにお手伝いできますか？",
        "schedule_help": "日付とメッセージを送信:\n!schedule 2025-12-25 09:00 メリークリスマス！",
        "schedule_done": "✅ {time} に予約しました",
        "schedule_list": "📅 予約:\n{items}",
        "schedule_empty": "予約メッセージはありません。",
        "birthday_wish": "🎂 {name} さん、お誕生日おめでとう！🎉",
        "lang_prompt": "対応言語: en, es, hi, ar, fr, pt, de, ja",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Translate *key* into *lang*, substituting {placeholders}."""
    text = STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def supported_langs() -> list[str]:
    return list(STRINGS.keys())


def lang_info(code: str) -> dict | None:
    data = STRINGS.get(code)
    if data:
        return {"code": code, "name": data["name"], "native": data["native"]}
    return None
