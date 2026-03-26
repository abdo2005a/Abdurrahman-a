import json
import logging
import os
from datetime import datetime
from typing import Optional
from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler, ContextTypes
)

# ======================= KONFIGURASYON =======================
TOKEN    = "8574020136:AAEaxD4fk9DPQQPsZ0y0lkhdKZXVrONxQJU"
ADMIN_ID = 7731559022

# Railway Volume /data'ya mount edilmeli
_default_dir = "/data/bot_data" if os.path.exists("/data") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_data")
BASE_DIR  = os.environ.get("DATA_DIR", _default_dir)
FILES_DIR = os.path.join(BASE_DIR, "files")
os.makedirs(BASE_DIR,  exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

DATA_FILE     = os.path.join(BASE_DIR, "bot_data.json")
USERS_FILE    = os.path.join(BASE_DIR, "users.json")
MESSAGES_FILE = os.path.join(BASE_DIR, "user_messages.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
ADMINS_FILE   = os.path.join(BASE_DIR, "admins.json")
BLOCKED_FILE  = os.path.join(BASE_DIR, "blocked.json")
# =============================================================

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Reply keyboard buton metinleri
MENU_BTN     = "📋 القائمة"
MGMT_BTN     = "👥 Yönetim"
CONTENT_BTN  = "📁 İçerik"
SETTINGS_BTN = "⚙️ Ayarlar"
MAINT_BTN    = "🔧 Bakım"
ALL_BTNS     = {MENU_BTN, MGMT_BTN, CONTENT_BTN, SETTINGS_BTN, MAINT_BTN}

# ConversationHandler states
(WAIT_FOLDER, WAIT_DEL_FOLDER, WAIT_FILE, WAIT_DEL_FILE,
 WAIT_ADMIN_ID, WAIT_RENAME_FOLDER, WAIT_RENAME_FILE,
 WAIT_BOT_NAME, WAIT_WELCOME, WAIT_PHOTO) = range(10)


# ═══════════════════════════════════════════════════════
#  JSON YARDIMCILARI
# ═══════════════════════════════════════════════════════

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"load_json {path}: {e}")
    return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"save_json {path}: {e}")

def load_content():   return load_json(DATA_FILE,     {"folders": {}, "files": []})
def save_content(d):  save_json(DATA_FILE, d)
def load_users():     return load_json(USERS_FILE,    {})
def save_users(d):    save_json(USERS_FILE, d)
def load_messages():  return load_json(MESSAGES_FILE, {})
def save_messages(d): save_json(MESSAGES_FILE, d)
def load_admins():    return load_json(ADMINS_FILE,   [])
def save_admins(d):   save_json(ADMINS_FILE, d)
def load_blocked():   return load_json(BLOCKED_FILE,  [])
def save_blocked(d):  save_json(BLOCKED_FILE, d)

def load_settings():
    default = {"maintenance": False, "maintenance_text": "🔧 Bot güncelleniyor...",
                "bot_name": "Bot", "welcome_msg": "", "bot_photo_id": None}
    data = load_json(SETTINGS_FILE, default)
    for k, v in default.items():
        data.setdefault(k, v)
    return data

def save_settings(d): save_json(SETTINGS_FILE, d)


# ═══════════════════════════════════════════════════════
#  YARDIMCILAR
# ═══════════════════════════════════════════════════════

def is_main_admin(uid): return int(uid) == ADMIN_ID
def is_admin(uid):      return int(uid) == ADMIN_ID or int(uid) in [int(x) for x in load_admins()]
def is_blocked(uid):    return int(uid) in [int(x) for x in load_blocked()]

def register_user(user):
    users = load_users()
    uid   = str(user.id)
    users[uid] = {
        "id": user.id, "first_name": user.first_name or "",
        "last_name": user.last_name or "", "username": user.username or "",
        "full_name": user.full_name or "",
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_users(users)

def log_user_message(user, msg_type: str, content: str, file_id: str = None):
    """Admin olmayan kullanıcıların mesajlarını kaydet"""
    if is_admin(user.id):
        return
    msgs = load_messages()
    uid  = str(user.id)
    entry = {
        "time":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type":    msg_type,
        "content": str(content)[:300],
    }
    if file_id:
        entry["file_id"] = file_id
    msgs.setdefault(uid, []).append(entry)
    msgs[uid] = msgs[uid][-2000:]  # son 2000 kayıt
    save_messages(msgs)

def get_folder(content, path):
    cur = content
    for name in path:
        cur = cur.setdefault("folders", {}).setdefault(name, {"folders": {}, "files": []})
    return cur

async def download_file(context, file_id: str, filename: str) -> Optional[str]:
    try:
        safe = "".join(c for c in filename if c.isalnum() or c in "._- ").strip() or \
               f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        dest = os.path.join(FILES_DIR, safe)
        base, ext = os.path.splitext(dest)
        n = 1
        while os.path.exists(dest):
            dest = f"{base}_{n}{ext}"; n += 1
        tg_file = await context.bot.get_file(file_id)
        await tg_file.download_to_drive(dest)
        logger.info(f"Dosya kaydedildi: {dest}")
        return dest
    except Exception as e:
        logger.warning(f"İndirme başarısız ({filename}): {e}")
        return None


# ═══════════════════════════════════════════════════════
#  KLAVYE OLUŞTURUCULAR
# ═══════════════════════════════════════════════════════

def reply_kb(uid):
    if is_main_admin(uid):
        return ReplyKeyboardMarkup([
            [KeyboardButton(MGMT_BTN), KeyboardButton(CONTENT_BTN)],
            [KeyboardButton(SETTINGS_BTN), KeyboardButton(MAINT_BTN)],
        ], resize_keyboard=True)
    elif is_admin(uid):
        return ReplyKeyboardMarkup([
            [KeyboardButton(MGMT_BTN), KeyboardButton(CONTENT_BTN)],
            [KeyboardButton(MAINT_BTN)],
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([[KeyboardButton(MENU_BTN)]], resize_keyboard=True)

def folder_text(folder, path, is_adm=False):
    header = "🏠 ANA SAYFA" if not path else "📂 " + " › ".join(path)
    lines  = [header, "─" * 20]
    folds  = folder.get("folders", {})
    files  = folder.get("files",   [])
    if folds:
        lines.append("📁 Klasörler:")
        for f in folds: lines.append(f"  • {f}")
    if files:
        lines.append("📎 Dosyalar:")
        for f in files: lines.append(f"  • {f.get('caption', f.get('name', '?'))}")
    if not folds and not files:
        lines.append("📭 Henüz içerik yok")
    if is_adm:
        s = load_settings()
        lines.append("─" * 20)
        lines.append(f"{'🔧 Bakım: AÇIK' if s['maintenance'] else '✅ Bakım: KAPALI'}")
    return "\n".join(lines)

def folder_kb(path, folder, is_adm=False):
    kb = []
    for name in list(folder.get("folders", {}).keys())[:8]:
        kb.append([InlineKeyboardButton(f"📁 {name}", callback_data=f"open|{name}")])
    for idx, f in enumerate(folder.get("files", [])[:12]):
        cap = f.get("caption", f.get("name", "?"))
        kb.append([InlineKeyboardButton(f"📎 {cap}", callback_data=f"getfile|{idx}")])
    nav = []
    if path:
        nav.append(InlineKeyboardButton("◀️ Geri", callback_data="nav|back"))
        nav.append(InlineKeyboardButton("🏠 Ana", callback_data="nav|root"))
    if nav:
        kb.append(nav)
    return InlineKeyboardMarkup(kb)


# ═══════════════════════════════════════════════════════
#  ORTAK EKRAN GÖNDER / DÜZENLE
# ═══════════════════════════════════════════════════════

async def show_folder(query, context, path, note=""):
    """Mevcut mesajı düzenle - yeni mesaj GÖNDERME"""
    content = load_content()
    folder  = get_folder(content, path)
    uid     = str(query.from_user.id)
    adm     = is_admin(uid)
    text    = folder_text(folder, path, adm)
    if note:
        text += f"\n\n{note}"
    kb = folder_kb(path, folder, adm)
    try:
        await query.edit_message_text(text, reply_markup=kb)
    except Exception:
        pass

async def show_folder_new(message, uid, path=None):
    """Yeni mesaj gönder (sadece /start ve menü butonu için)"""
    path    = path or []
    content = load_content()
    folder  = get_folder(content, path)
    adm     = is_admin(uid)
    text    = folder_text(folder, path, adm)
    await message.reply_text(text, reply_markup=folder_kb(path, folder, adm))


# ═══════════════════════════════════════════════════════
#  /start
# ═══════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = str(user.id)
    register_user(user)
    log_user_message(user, "command", "/start")
    s = load_settings()
    context.user_data["path"] = []

    if is_blocked(uid) and not is_admin(uid):
        return

    # Reply keyboard'u bir kere kur
    await update.message.reply_text(".", reply_markup=reply_kb(uid),
                                     reply_to_message_id=None)

    if not is_admin(uid):
        if s["maintenance"]:
            await update.message.reply_text(s["maintenance_text"])
            return
        if s.get("bot_photo_id"):
            await update.message.reply_photo(s["bot_photo_id"],
                                              caption=s.get("welcome_msg") or None)
        elif s.get("welcome_msg"):
            await update.message.reply_text(s["welcome_msg"])

    await show_folder_new(update.message, uid)


# ═══════════════════════════════════════════════════════
#  REPLY KEYBOARD BUTONLARI
#  — Sadece reply_kb'yi güncellemesi gereken işlemler
#  — Her biri mevcut mesajı DÜZENLEMEYE çalışmaz,
#    inline mesajı YENI gönderir ama bir kez
# ═══════════════════════════════════════════════════════

async def _delete_last_inline(context, chat_id):
    """Önceki inline mesajı sil"""
    msg_id = context.user_data.get("last_inline_msg")
    if msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
        context.user_data.pop("last_inline_msg", None)


async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = str(user.id)
    text = (update.message.text or "").strip()
    register_user(user)

    # Önceki inline mesajı sil
    await _delete_last_inline(context, update.effective_chat.id)

    # ── Menü (kullanıcı) ──────────────────────────────
    if text == MENU_BTN:
        context.user_data["path"] = []
        s = load_settings()
        if s["maintenance"] and not is_admin(uid):
            await update.message.reply_text(s["maintenance_text"])
            return
        await show_folder_new(update.message, uid)
        return

    if not is_admin(uid):
        return

    # ── Yönetim ───────────────────────────────────────
    if text == MGMT_BTN:
        kb = []
        kb.append([
            InlineKeyboardButton("📊 İstatistik", callback_data="mgmt|stats"),
            InlineKeyboardButton("👥 Kullanıcılar", callback_data="mgmt|users"),
        ])
        if is_main_admin(uid):
            kb.append([
                InlineKeyboardButton("👤 Admin Ekle", callback_data="mgmt|add_admin"),
                InlineKeyboardButton("🚫 Admin Çıkar", callback_data="mgmt|del_admin"),
            ])
        sent = await update.message.reply_text("👥 Yönetim Paneli", reply_markup=InlineKeyboardMarkup(kb))
        context.user_data["last_inline_msg"] = sent.message_id
        return

    # ── İçerik Yönetimi ──────────────────────────────
    if text == CONTENT_BTN:
        kb = [
            [InlineKeyboardButton("➕ Klasör Ekle", callback_data="cnt|add_folder"),
             InlineKeyboardButton("🗑 Klasör Sil",  callback_data="cnt|del_folder")],
            [InlineKeyboardButton("✏️ Klasör Düzenle", callback_data="cnt|edit_folder"),
             InlineKeyboardButton("✏️ Dosya Düzenle",  callback_data="cnt|edit_file")],
            [InlineKeyboardButton("📎 Dosya/Medya Ekle", callback_data="cnt|add_file"),
             InlineKeyboardButton("🗑 Dosya Sil",        callback_data="cnt|del_file")],
        ]
        sent = await update.message.reply_text("📁 İçerik Yönetimi", reply_markup=InlineKeyboardMarkup(kb))
        context.user_data["last_inline_msg"] = sent.message_id
        return

    # ── Bot Ayarları ──────────────────────────────────
    if text == SETTINGS_BTN and is_main_admin(uid):
        s   = load_settings()
        txt = (f"⚙️ BOT AYARLARI\n\n"
               f"📝 Ad: {s.get('bot_name','—')}\n"
               f"💬 Karşılama: {s.get('welcome_msg','—')[:50]}\n"
               f"🖼 Fotoğraf: {'✅' if s.get('bot_photo_id') else '❌'}\n"
               f"🚫 Engellenenler: {len(load_blocked())} kişi")
        kb = [
            [InlineKeyboardButton("📝 Bot Adı",        callback_data="set|name")],
            [InlineKeyboardButton("💬 Karşılama",       callback_data="set|welcome")],
            [InlineKeyboardButton("🖼 Bot Fotoğrafı",   callback_data="set|photo")],
            [InlineKeyboardButton("🚫 Engellenenler",   callback_data="set|blocked")],
        ]
        sent = await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        context.user_data["last_inline_msg"] = sent.message_id
        return

    # ── Bakım Modu ────────────────────────────────────
    if text == MAINT_BTN:
        s = load_settings()
        s["maintenance"] = not s["maintenance"]
        save_settings(s)
        durum = "AÇIK 🔧" if s["maintenance"] else "KAPALI ✅"
        await update.message.reply_text(f"Bakım Modu: {durum}")
        return


# ═══════════════════════════════════════════════════════
#  CALLBACK — Tüm inline butonlar
# ═══════════════════════════════════════════════════════

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user  = query.from_user
    uid   = str(user.id)
    adm   = is_admin(uid)
    cb    = query.data

    if is_blocked(uid) and not adm:
        return ConversationHandler.END
    if not adm:
        s = load_settings()
        if s["maintenance"]:
            await query.answer("🔧 Bot güncelleniyor...", show_alert=True)
            return ConversationHandler.END

    content = load_content()
    path    = context.user_data.get("path", [])

    # ── Dosya Aç ──────────────────────────────────────
    if cb.startswith("getfile|"):
        idx    = int(cb.split("|")[1])
        folder = get_folder(content, path)
        files  = folder.get("files", [])
        if idx >= len(files):
            await query.answer("Dosya bulunamadı.", show_alert=True)
            return ConversationHandler.END
        f     = files[idx]
        ftype = f.get("type", "")
        fid   = f.get("file_id", "")
        cap   = f.get("caption", "")
        url   = f.get("url", "")
        log_user_message(user, "file_view", cap)
        try:
            if   ftype == "photo":     await query.message.reply_photo(fid, caption=cap)
            elif ftype == "video":     await query.message.reply_video(fid, caption=cap)
            elif ftype == "animation": await query.message.reply_animation(fid, caption=cap)
            elif ftype == "document":  await query.message.reply_document(fid, caption=cap)
            elif ftype == "audio":     await query.message.reply_audio(fid, caption=cap)
            elif ftype == "voice":     await query.message.reply_voice(fid, caption=cap)
            elif ftype == "link":      await query.message.reply_text(f"🔗 {cap}\n{url}" if cap != url else f"🔗 {url}")
            elif ftype == "text":      await query.message.reply_text(cap)
            else: await query.message.reply_text("❓ Bilinmeyen tür.")
        except Exception as e:
            await query.message.reply_text(f"❌ Gönderilemedi: {e}")
        return ConversationHandler.END

    # ── Navigasyon ────────────────────────────────────
    if cb.startswith("nav|"):
        action = cb.split("|")[1]
        if action == "back" and path:
            path.pop()
        elif action == "root":
            path = []
        context.user_data["path"] = path
        await show_folder(query, context, path)
        return ConversationHandler.END

    if cb.startswith("open|"):
        name = cb.split("|", 1)[1]
        path.append(name)
        context.user_data["path"] = path
        await show_folder(query, context, path)
        return ConversationHandler.END

    # ── Yönetim ──────────────────────────────────────
    if cb.startswith("mgmt|") and adm:
        action = cb.split("|")[1]

        if action == "stats":
            u_d   = load_users()
            m_d   = load_messages()
            total = sum(len(v) for v in m_d.values())
            s     = load_settings()
            def _cnt(node):
                c = 0
                for f in node.get("folders", {}).values(): c += 1 + _cnt(f)
                return c
            txt = (f"📊 İSTATİSTİKLER\n\n"
                   f"👥 Kullanıcı: {len(u_d)}\n"
                   f"💬 Toplam mesaj: {total}\n"
                   f"📁 Klasör: {_cnt(content)}\n"
                   f"📎 Dosya: {len(content.get('files',[]))}\n"
                   f"🔧 Bakım: {'Açık' if s['maintenance'] else 'Kapalı'}")
            kb = [[InlineKeyboardButton("◀️ Kapat", callback_data="close")]]
            await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "users":
            u_d = load_users()
            if not u_d:
                await query.answer("Henüz kullanıcı yok.", show_alert=True)
                return ConversationHandler.END
            kb = []
            for uid_, u in list(u_d.items())[-50:]:
                if int(uid_) == ADMIN_ID: continue
                name = u.get("full_name") or u.get("first_name") or f"ID:{uid_}"
                un   = f" @{u['username']}" if u.get("username") else ""
                kb.append([InlineKeyboardButton(f"👤 {name}{un}", callback_data=f"user|info|{uid_}")])
            kb.append([InlineKeyboardButton("◀️ Kapat", callback_data="close")])
            await query.edit_message_text("👥 Kullanıcı Listesi — birini seçin:", reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "add_admin" and is_main_admin(uid):
            context.user_data["action"] = "admin_add"
            await query.edit_message_text(
                "Admin eklenecek kullanıcının ID'sini yazın:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="close")]]))
            return WAIT_ADMIN_ID

        if action == "del_admin" and is_main_admin(uid):
            admins = load_admins()
            if not admins:
                await query.answer("Eklenmiş admin yok.", show_alert=True)
                return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🚫 {a}", callback_data=f"rem_admin|{a}")] for a in admins]
            kb.append([InlineKeyboardButton("❌ İptal", callback_data="close")])
            await query.edit_message_text("Çıkarılacak admini seçin:", reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

    # ── Admin işlemleri ───────────────────────────────
    if cb.startswith("rem_admin|") and is_main_admin(uid):
        rem    = int(cb.split("|")[1])
        admins = load_admins()
        if rem in admins: admins.remove(rem); save_admins(admins)
        await query.edit_message_text(f"✅ Admin çıkarıldı: {rem}")
        return ConversationHandler.END

    # ── Kullanıcı Detay ───────────────────────────────
    if cb.startswith("user|") and adm:
        parts = cb.split("|")
        action = parts[1]

        if action == "info":
            target = parts[2]
            u_d    = load_users()
            m_d    = load_messages()
            u      = u_d.get(target, {})
            name   = u.get("full_name") or u.get("first_name") or f"ID:{target}"
            un     = f"@{u['username']}" if u.get("username") else "—"
            msgs   = m_d.get(target, [])
            media  = [m for m in msgs if m.get("file_id")]
            texts  = [m for m in msgs if m.get("type") in ("msg", "text", "command")]

            ICONS = {"msg": "💬", "text": "💬", "photo": "🖼", "video": "🎥",
                     "document": "📄", "audio": "🎵", "voice": "🎙",
                     "animation": "🎞", "sticker": "😊", "command": "⚙️", "file_view": "👁"}

            lines = [
                f"👤 {name} ({un})",
                f"🆔 {target}",
                f"🕐 Son: {u.get('last_seen','—')}",
                f"💬 Mesaj: {len(texts)} | 📎 Medya: {len(media)}",
                "─" * 22,
            ]
            # Son 15 mesaj
            for m in msgs[-15:]:
                icon = ICONS.get(m.get("type",""), "📨")
                t    = m.get("time","")[-8:]
                c    = m.get("content","")[:50]
                lines.append(f"{icon} [{t}] {c}")

            kb = []
            if media:
                kb.append([InlineKeyboardButton(f"🖼 Medyaları Gönder ({len(media)})", callback_data=f"user|media|{target}")])
            if int(target) not in [int(x) for x in load_blocked()]:
                kb.append([InlineKeyboardButton("🚫 Engelle", callback_data=f"user|block|{target}")])
            else:
                kb.append([InlineKeyboardButton("✅ Engeli Kaldır", callback_data=f"user|unblock|{target}")])
            kb.append([InlineKeyboardButton("◀️ Geri", callback_data="mgmt|users")])
            await query.edit_message_text("\n".join(lines)[:4000], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "media":
            target = parts[2]
            m_d    = load_messages()
            msgs   = m_d.get(target, [])
            media  = [m for m in msgs if m.get("file_id")]
            if not media:
                await query.answer("Medya bulunamadı.", show_alert=True)
                return ConversationHandler.END

            await query.answer(f"{len(media)} medya gönderiliyor...")
            ICONS = {"photo": "🖼", "video": "🎥", "document": "📄",
                     "audio": "🎵", "voice": "🎙", "animation": "🎞", "sticker": "😊"}
            sent = 0
            for m in media[-30:]:
                fid   = m["file_id"]
                ftype = m.get("type", "")
                cap   = f"{ICONS.get(ftype,'📎')} [{m.get('time','')}]\n{m.get('content','')}"[:200]
                try:
                    if   ftype == "photo":     await query.message.reply_photo(fid, caption=cap)
                    elif ftype == "video":     await query.message.reply_video(fid, caption=cap)
                    elif ftype == "document":  await query.message.reply_document(fid, caption=cap)
                    elif ftype == "audio":     await query.message.reply_audio(fid, caption=cap)
                    elif ftype == "voice":     await query.message.reply_voice(fid, caption=cap)
                    elif ftype == "animation": await query.message.reply_animation(fid, caption=cap)
                    elif ftype == "sticker":   await query.message.reply_sticker(fid)
                    sent += 1
                except Exception as e:
                    logger.warning(f"Medya gönderilemedi: {e}")
            await query.message.reply_text(f"✅ {sent}/{len(media[-30:])} medya gönderildi.")
            return ConversationHandler.END

        if action == "block":
            target  = parts[2]
            blocked = load_blocked()
            if int(target) not in blocked:
                blocked.append(int(target)); save_blocked(blocked)
            await query.answer(f"✅ {target} engellendi.", show_alert=True)
            # Kullanıcı bilgisini yenile
            context.user_data["cb_target"] = target
            query.data = f"user|info|{target}"
            return await callback(update, context)

        if action == "unblock":
            target  = parts[2]
            blocked = load_blocked()
            if int(target) in blocked:
                blocked.remove(int(target)); save_blocked(blocked)
            await query.answer(f"✅ Engel kaldırıldı: {target}", show_alert=True)
            query.data = f"user|info|{target}"
            return await callback(update, context)

    # ── İçerik Yönetimi ───────────────────────────────
    if cb.startswith("cnt|") and adm:
        action = cb.split("|")[1]
        folder = get_folder(content, path)

        if action == "add_folder":
            context.user_data["action"] = "add_folder"
            await query.edit_message_text(
                "📁 Yeni klasör adını yazın:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="nav|root")]]))
            return WAIT_FOLDER

        if action == "del_folder":
            folds = list(folder.get("folders", {}).keys())
            if not folds:
                await query.answer("Klasör yok.", show_alert=True)
                return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🗑 {f}", callback_data=f"do|del_folder|{f}")] for f in folds]
            kb.append([InlineKeyboardButton("❌ İptal", callback_data="nav|root")])
            await query.edit_message_text("Silinecek klasörü seçin:", reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "edit_folder":
            folds = list(folder.get("folders", {}).keys())
            if not folds:
                await query.answer("Klasör yok.", show_alert=True)
                return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"✏️ {f}", callback_data=f"do|pick_folder|{f}")] for f in folds]
            kb.append([InlineKeyboardButton("❌ İptal", callback_data="nav|root")])
            await query.edit_message_text("Düzenlenecek klasörü seçin:", reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "add_file":
            context.user_data["action"] = "add_file"
            await query.edit_message_text(
                "📎 Dosya, resim, video gönderin — veya link/metin yazın:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="nav|root")]]))
            return WAIT_FILE

        if action == "del_file":
            files = folder.get("files", [])
            if not files:
                await query.answer("Dosya yok.", show_alert=True)
                return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🗑 {f.get('caption','?')}", callback_data=f"do|del_file|{i}")] for i, f in enumerate(files)]
            kb.append([InlineKeyboardButton("❌ İptal", callback_data="nav|root")])
            await query.edit_message_text("Silinecek dosyayı seçin:", reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "edit_file":
            files = folder.get("files", [])
            if not files:
                await query.answer("Dosya yok.", show_alert=True)
                return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"✏️ {f.get('caption','?')}", callback_data=f"do|pick_file|{i}")] for i, f in enumerate(files)]
            kb.append([InlineKeyboardButton("❌ İptal", callback_data="nav|root")])
            await query.edit_message_text("Düzenlenecek dosyayı seçin:", reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

    # ── Do (işlem gerçekleştir) ───────────────────────
    if cb.startswith("do|") and adm:
        parts  = cb.split("|", 2)
        action = parts[1]
        arg    = parts[2] if len(parts) > 2 else ""
        folder = get_folder(content, path)

        if action == "del_folder":
            if arg in folder.get("folders", {}):
                del folder["folders"][arg]; save_content(content)
            await show_folder(query, context, path, note=f"✅ '{arg}' silindi.")
            return ConversationHandler.END

        if action == "pick_folder":
            context.user_data["action"]  = "rename_folder"
            context.user_data["target"]  = arg
            await query.edit_message_text(
                f"'{arg}' için yeni ad yazın:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="nav|root")]]))
            return WAIT_RENAME_FOLDER

        if action == "del_file":
            idx   = int(arg)
            files = folder.get("files", [])
            if 0 <= idx < len(files):
                removed = files.pop(idx); save_content(content)
                await show_folder(query, context, path, note=f"✅ '{removed.get('caption','?')}' silindi.")
            return ConversationHandler.END

        if action == "pick_file":
            context.user_data["action"] = "rename_file"
            context.user_data["target"] = int(arg)
            await query.edit_message_text(
                "Yeni dosya adını yazın:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="nav|root")]]))
            return WAIT_RENAME_FILE

    # ── Bot Ayarları ──────────────────────────────────
    if cb.startswith("set|") and is_main_admin(uid):
        action = cb.split("|")[1]

        if action == "name":
            context.user_data["action"] = "set_name"
            s = load_settings()
            await query.edit_message_text(
                f"Yeni bot adını yazın (mevcut: {s.get('bot_name','—')}):",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="close")]]))
            return WAIT_BOT_NAME

        if action == "welcome":
            context.user_data["action"] = "set_welcome"
            await query.edit_message_text(
                "Yeni karşılama mesajını yazın:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="close")]]))
            return WAIT_WELCOME

        if action == "photo":
            context.user_data["action"] = "set_photo"
            await query.edit_message_text(
                "Yeni bot fotoğrafını gönderin:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="close")]]))
            return WAIT_PHOTO

        if action == "blocked":
            blocked = load_blocked()
            txt  = f"🚫 Engellenenler ({len(blocked)})\n\n"
            txt += "\n".join(f"🆔 {b}" for b in blocked) if blocked else "Kimse engellenmedi."
            kb   = [[InlineKeyboardButton("◀️ Kapat", callback_data="close")]]
            await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

    # ── Kapat ─────────────────────────────────────────
    if cb == "close":
        try: await query.delete_message()
        except: pass
        return ConversationHandler.END

    return ConversationHandler.END


# ═══════════════════════════════════════════════════════
#  METİN GİRİŞİ (ConversationHandler states)
# ═══════════════════════════════════════════════════════

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user   = update.effective_user
    uid    = str(user.id)
    text   = (update.message.text or "").strip()
    register_user(user)
    log_user_message(user, "msg", text)

    if not is_admin(uid):
        return ConversationHandler.END

    content = load_content()
    path    = context.user_data.get("path", [])
    folder  = get_folder(content, path)
    action  = context.user_data.get("action", "")

    if action == "admin_add" and is_main_admin(uid):
        try:    new_id = int(text)
        except: await update.message.reply_text("❌ Geçersiz ID."); return WAIT_ADMIN_ID
        admins = load_admins()
        if new_id in admins or new_id == ADMIN_ID:
            await update.message.reply_text("❌ Zaten admin.")
        else:
            admins.append(new_id); save_admins(admins)
            await update.message.reply_text(f"✅ Admin eklendi: {new_id}")
        context.user_data.pop("action", None)
        return ConversationHandler.END

    if action == "add_folder":
        if not text:
            await update.message.reply_text("❌ Ad boş olamaz!"); return WAIT_FOLDER
        if text in folder.get("folders", {}):
            await update.message.reply_text(f"❌ '{text}' zaten var!"); return WAIT_FOLDER
        folder.setdefault("folders", {})[text] = {"folders": {}, "files": []}
        save_content(content)
        await update.message.reply_text(f"✅ '{text}' klasörü eklendi.")
        context.user_data.pop("action", None)
        return ConversationHandler.END

    if action == "rename_folder":
        old = context.user_data.get("target", "")
        if not text:
            await update.message.reply_text("❌ Ad boş olamaz!"); return WAIT_RENAME_FOLDER
        if text in folder.get("folders", {}):
            await update.message.reply_text(f"❌ '{text}' zaten var!"); return WAIT_RENAME_FOLDER
        if old in folder.get("folders", {}):
            folder["folders"][text] = folder["folders"].pop(old)
            save_content(content)
        await update.message.reply_text(f"✅ '{old}' → '{text}'")
        context.user_data.pop("action", None); context.user_data.pop("target", None)
        return ConversationHandler.END

    if action == "rename_file":
        idx   = context.user_data.get("target", 0)
        files = folder.get("files", [])
        if not text:
            await update.message.reply_text("❌ Ad boş olamaz!"); return WAIT_RENAME_FILE
        if 0 <= idx < len(files):
            files[idx]["caption"] = text; files[idx]["name"] = text
            save_content(content)
        await update.message.reply_text(f"✅ Yeni ad: '{text}'")
        context.user_data.pop("action", None); context.user_data.pop("target", None)
        return ConversationHandler.END

    if action == "add_file":
        if text.startswith("http://") or text.startswith("https://"):
            fobj = {"type": "link", "url": text, "caption": text, "name": text}
        else:
            fobj = {"type": "text", "caption": text, "name": text}
        folder.setdefault("files", []).append(fobj)
        save_content(content)
        await update.message.reply_text(f"✅ Eklendi: {fobj['caption'][:50]}")
        context.user_data.pop("action", None)
        return ConversationHandler.END

    if action == "set_name" and is_main_admin(uid):
        if not text:
            await update.message.reply_text("❌ Ad boş olamaz!"); return WAIT_BOT_NAME
        s = load_settings(); s["bot_name"] = text; save_settings(s)
        await update.message.reply_text(f"✅ Bot adı: '{text}'")
        context.user_data.pop("action", None)
        return ConversationHandler.END

    if action == "set_welcome" and is_main_admin(uid):
        s = load_settings(); s["welcome_msg"] = text; save_settings(s)
        await update.message.reply_text("✅ Karşılama mesajı güncellendi.")
        context.user_data.pop("action", None)
        return ConversationHandler.END

    return ConversationHandler.END


# ═══════════════════════════════════════════════════════
#  MEDYA GİRİŞİ
# ═══════════════════════════════════════════════════════

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    uid  = str(user.id)
    msg  = update.message
    register_user(user)

    # ── Kullanıcı medyasını kaydet (admin değilse) ────
    if not is_admin(uid):
        if is_blocked(uid): return ConversationHandler.END
        s = load_settings()
        if s["maintenance"]:
            await msg.reply_text(s["maintenance_text"])
            return ConversationHandler.END

        if msg.photo:
            fid = msg.photo[-1].file_id
            log_user_message(user, "photo", msg.caption or "(fotoğraf)", file_id=fid)
            await download_file(context, fid, f"photo_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
        elif msg.video:
            fid = msg.video.file_id
            log_user_message(user, "video", msg.caption or msg.video.file_name or "(video)", file_id=fid)
            await download_file(context, fid, msg.video.file_name or f"video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4")
        elif msg.document:
            fid = msg.document.file_id
            log_user_message(user, "document", msg.document.file_name or "(dosya)", file_id=fid)
            await download_file(context, fid, msg.document.file_name or f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        elif msg.audio:
            fid = msg.audio.file_id
            log_user_message(user, "audio", msg.audio.file_name or "(ses)", file_id=fid)
            await download_file(context, fid, msg.audio.file_name or f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3")
        elif msg.voice:
            fid = msg.voice.file_id
            log_user_message(user, "voice", "(sesli mesaj)", file_id=fid)
            await download_file(context, fid, f"voice_{datetime.now().strftime('%Y%m%d%H%M%S')}.ogg")
        elif msg.animation:
            fid = msg.animation.file_id
            log_user_message(user, "animation", "(GIF)", file_id=fid)
        elif msg.sticker:
            fid = msg.sticker.file_id
            log_user_message(user, "sticker", msg.sticker.emoji or "(sticker)", file_id=fid)
        return ConversationHandler.END

    # ── Admin: dosya ekleme modu ──────────────────────
    action = context.user_data.get("action", "")

    if action == "set_photo" and is_main_admin(uid):
        if msg.photo:
            s = load_settings(); s["bot_photo_id"] = msg.photo[-1].file_id; save_settings(s)
            await msg.reply_text("✅ Bot fotoğrafı güncellendi.")
            context.user_data.pop("action", None)
        else:
            await msg.reply_text("❌ Lütfen bir fotoğraf gönderin.")
        return ConversationHandler.END

    if action != "add_file":
        return ConversationHandler.END

    content = load_content()
    path    = context.user_data.get("path", [])
    folder  = get_folder(content, path)
    now     = datetime.now().strftime("%Y%m%d%H%M%S")
    cap     = msg.caption or ""
    fobj    = None

    try:
        if msg.photo:
            fid  = msg.photo[-1].file_id
            local = await download_file(context, fid, f"photo_{now}.jpg")
            fobj  = {"type": "photo", "file_id": fid, "caption": cap or "صورة", "name": f"photo_{now}.jpg",
                     **({"local_path": local} if local else {})}
        elif msg.video:
            fname = msg.video.file_name or f"video_{now}.mp4"
            fid   = msg.video.file_id
            local = await download_file(context, fid, fname)
            fobj  = {"type": "video", "file_id": fid, "caption": cap or fname, "name": fname,
                     **({"local_path": local} if local else {})}
        elif msg.animation:
            fid  = msg.animation.file_id
            local = await download_file(context, fid, f"gif_{now}.gif")
            fobj  = {"type": "animation", "file_id": fid, "caption": cap or "GIF", "name": f"gif_{now}.gif",
                     **({"local_path": local} if local else {})}
        elif msg.document:
            fname = msg.document.file_name or f"doc_{now}"
            fid   = msg.document.file_id
            local = await download_file(context, fid, fname)
            fobj  = {"type": "document", "file_id": fid, "caption": cap or fname, "name": fname,
                     **({"local_path": local} if local else {})}
        elif msg.audio:
            fname = msg.audio.file_name or f"audio_{now}.mp3"
            fid   = msg.audio.file_id
            local = await download_file(context, fid, fname)
            fobj  = {"type": "audio", "file_id": fid, "caption": cap or msg.audio.title or fname, "name": fname,
                     **({"local_path": local} if local else {})}
        elif msg.voice:
            fid  = msg.voice.file_id
            local = await download_file(context, fid, f"voice_{now}.ogg")
            fobj  = {"type": "voice", "file_id": fid, "caption": cap or "رسالة صوتية", "name": f"voice_{now}.ogg",
                     **({"local_path": local} if local else {})}
    except Exception as e:
        logger.error(f"handle_media hata: {e}")

    if fobj:
        folder.setdefault("files", []).append(fobj)
        save_content(content)
        await msg.reply_text(f"✅ Eklendi: {fobj['caption']}")
        context.user_data.pop("action", None)
    else:
        await msg.reply_text("❓ Desteklenmeyen tür.")

    return ConversationHandler.END


# ═══════════════════════════════════════════════════════
#  KULLANICI MESAJ LOGLAYICILARI (group=-1, her mesajdan önce)
# ═══════════════════════════════════════════════════════

async def log_user_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcı medyasını logla ve diske kaydet - conv'dan bağımsız"""
    if not update.message: return
    user = update.effective_user
    if is_admin(user.id): return
    if is_blocked(str(user.id)): return
    register_user(user)
    msg = update.message
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        if msg.photo:
            fid = msg.photo[-1].file_id
            log_user_message(user, "photo", msg.caption or "(fotoğraf)", file_id=fid)
            await download_file(context, fid, f"photo_{user.id}_{now}.jpg")
        elif msg.video:
            fid = msg.video.file_id
            name = msg.video.file_name or f"video_{user.id}_{now}.mp4"
            log_user_message(user, "video", msg.caption or name, file_id=fid)
            await download_file(context, fid, name)
        elif msg.document:
            fid = msg.document.file_id
            name = msg.document.file_name or f"doc_{user.id}_{now}"
            log_user_message(user, "document", name, file_id=fid)
            await download_file(context, fid, name)
        elif msg.audio:
            fid = msg.audio.file_id
            name = msg.audio.file_name or f"audio_{user.id}_{now}.mp3"
            log_user_message(user, "audio", name, file_id=fid)
            await download_file(context, fid, name)
        elif msg.voice:
            fid = msg.voice.file_id
            log_user_message(user, "voice", "(sesli mesaj)", file_id=fid)
            await download_file(context, fid, f"voice_{user.id}_{now}.ogg")
        elif msg.animation:
            fid = msg.animation.file_id
            log_user_message(user, "animation", "(GIF)", file_id=fid)
        elif msg.sticker:
            fid = msg.sticker.file_id
            log_user_message(user, "sticker", msg.sticker.emoji or "(sticker)", file_id=fid)
        elif msg.video_note:
            fid = msg.video_note.file_id
            log_user_message(user, "video_note", "(yuvarlak video)", file_id=fid)
            await download_file(context, fid, f"videonote_{user.id}_{now}.mp4")
    except Exception as e:
        logger.error(f"log_user_media hata: {e}")


async def log_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcı metin mesajlarını logla"""
    if not update.message: return
    user = update.effective_user
    if is_admin(user.id): return
    if is_blocked(str(user.id)): return
    register_user(user)
    text = (update.message.text or "").strip()
    if text and text not in ALL_BTNS:
        log_user_message(user, "msg", text)


# ═══════════════════════════════════════════════════════
#  GENEL MESAJ HANDLER
# ═══════════════════════════════════════════════════════

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user
    uid  = str(user.id)
    msg  = update.message
    text = (msg.text or "").strip()

    # Reply buton metinleri bu handler'a düşmemeli
    if text in ALL_BTNS:
        return

    register_user(user)

    if not is_admin(uid):
        # Medya türlerini logla (handle_media'ya ulaşmadıysa burada yakala)
        if msg.photo:
            fid = msg.photo[-1].file_id
            log_user_message(user, "photo", msg.caption or "(fotoğraf)", file_id=fid)
        elif msg.video:
            fid = msg.video.file_id
            log_user_message(user, "video", msg.caption or msg.video.file_name or "(video)", file_id=fid)
        elif msg.document:
            fid = msg.document.file_id
            log_user_message(user, "document", msg.document.file_name or "(dosya)", file_id=fid)
        elif msg.audio:
            fid = msg.audio.file_id
            log_user_message(user, "audio", msg.audio.file_name or "(ses)", file_id=fid)
        elif msg.voice:
            fid = msg.voice.file_id
            log_user_message(user, "voice", "(sesli mesaj)", file_id=fid)
        elif msg.animation:
            fid = msg.animation.file_id
            log_user_message(user, "animation", "(GIF)", file_id=fid)
        elif msg.sticker:
            log_user_message(user, "sticker", msg.sticker.emoji or "(sticker)", file_id=msg.sticker.file_id)
        elif text:
            log_user_message(user, "msg", text)

    if is_admin(uid): return
    if is_blocked(uid): return

    s = load_settings()
    if s["maintenance"]:
        await msg.reply_text(s["maintenance_text"])


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    app = Application.builder().token(TOKEN).build()

    media_f      = (filters.PHOTO | filters.VIDEO | filters.Document.ALL |
                    filters.AUDIO | filters.VOICE | filters.ANIMATION | filters.Sticker.ALL)
    text_f       = filters.TEXT & ~filters.COMMAND
    reply_btn_f  = filters.Regex(f"^({MENU_BTN}|{MGMT_BTN}|{CONTENT_BTN}|{SETTINGS_BTN}|{MAINT_BTN})$")

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(callback)],
        states={
            WAIT_FOLDER:        [MessageHandler(text_f & ~reply_btn_f, handle_text)],
            WAIT_DEL_FOLDER:    [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_FILE:          [MessageHandler(text_f & ~reply_btn_f, handle_text),
                                  MessageHandler(media_f, handle_media), CallbackQueryHandler(callback)],
            WAIT_DEL_FILE:      [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_ADMIN_ID:      [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_RENAME_FOLDER: [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_RENAME_FILE:   [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_BOT_NAME:      [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_WELCOME:       [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_PHOTO:         [MessageHandler(media_f, handle_media), CallbackQueryHandler(callback)],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(reply_btn_f, handle_reply_buttons),
            MessageHandler(media_f, handle_media),
            CallbackQueryHandler(callback, pattern="^(close|nav\\||mgmt\\||cnt\\||set\\||user\\||do\\||open\\||getfile\\||rem_admin\\|)"),
        ],
        allow_reentry=True,
    )

    # group=-1: Her mesajdan ÖNCE çalışır, kullanıcı medyasını loglar
    app.add_handler(MessageHandler(media_f, log_user_media), group=-1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~reply_btn_f, log_user_text), group=-1)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(reply_btn_f, handle_reply_buttons))
    app.add_handler(conv)
    app.add_handler(MessageHandler(media_f, handle_media))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_any_message))

    print("✅ Bot başlatıldı!")
    print(f"👑 Admin ID : {ADMIN_ID}")
    print(f"💾 Veri     : {BASE_DIR}")
    if "/data" in BASE_DIR:
        print("✅ Railway Volume aktif - dosyalar kalıcı!")
    else:
        print("⚠️  Volume YOK → Railway Settings → Volumes → Mount: /data")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
