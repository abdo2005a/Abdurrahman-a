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

BASE_DIR  = os.environ.get("DATA_DIR", "/data/bot_data")
FILES_DIR = os.path.join(BASE_DIR, "files")
os.makedirs(BASE_DIR,  exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

DATA_FILE     = os.path.join(BASE_DIR, "bot_data.json")
USERS_FILE    = os.path.join(BASE_DIR, "users.json")
MESSAGES_FILE = os.path.join(BASE_DIR, "user_messages.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
ADMINS_FILE   = os.path.join(BASE_DIR, "admins.json")
BLOCKED_FILE  = os.path.join(BASE_DIR, "blocked.json")
PENDING_FILE  = os.path.join(BASE_DIR, "pending_downloads.json")
# =============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Reply Keyboard buton metinleri ──
MENU_BTN_AR     = "📋 القائمة"
MGMT_BTN_TR     = "👥 Yönetim"
CONTENT_BTN_TR  = "📁 İçerik Yönetimi"
SETTINGS_BTN_TR = "⚙️ Bot Ayarları"
MAINT_BTN_TR    = "🔧 Bakım Modu"

ALL_REPLY_BTNS = {MENU_BTN_AR, MGMT_BTN_TR, CONTENT_BTN_TR, SETTINGS_BTN_TR, MAINT_BTN_TR}

# ConversationHandler states
(
    WAITING_FOLDER_NAME,
    WAITING_NEW_FOLDER_NAME,
    WAITING_FILE_CONTENT,
    WAITING_NEW_ITEM_NAME,
    WAITING_ADMIN_ID,
    WAITING_RENAME_FOLDER,
    WAITING_RENAME_FILE,
    WAITING_BOT_NAME,
    WAITING_BOT_WELCOME,
    WAITING_BOT_PHOTO,
) = range(10)


# ═══════════════════════════════════════════════════════
#  DİL SİSTEMİ
# ═══════════════════════════════════════════════════════

TR = {
    "home":                "🏠 ANA SAYFA",
    "folders_lbl":         "📁 Klasörler:",
    "files_lbl":           "📎 Dosyalar:",
    "no_content":          "📭 Henüz içerik yok",
    "admin_mode":          "👑 Admin Modu",
    "maint_on_lbl":        "🔧 Bakım: AÇIK",
    "maint_off_lbl":       "✅ Bakım: KAPALI",
    "maint_msg":           "🔧 Bot şu anda güncelleniyor, lütfen bekleyin...",
    "btn_add_folder":      "➕ Klasör Ekle",
    "btn_del_folder":      "🗑 Klasör Sil",
    "btn_edit_folder":     "✏️ Klasör Düzenle",
    "btn_add_file":        "📎 Dosya/Medya Ekle",
    "btn_del_file":        "🗑 Dosya Sil",
    "btn_edit_file":       "✏️ Dosya Düzenle",
    "btn_back":            "◀️ Geri",
    "btn_home":            "🏠 Ana Sayfa",
    "btn_cancel":          "❌ İptal",
    "btn_stats":           "📊 İstatistik",
    "btn_users":           "👥 Kullanıcılar",
    "btn_list_admins":     "📋 Admin Listesi",
    "btn_add_admin":       "👤 Admin Ekle",
    "btn_del_admin":       "🚫 Admin Çıkar",
    "btn_bot_settings":    "⚙️ Bot Ayarları",
    "btn_set_bot_name":    "📝 Bot Adı",
    "btn_set_welcome":     "💬 Karşılama Mesajı",
    "btn_set_photo":       "🖼 Bot Fotoğrafı",
    "btn_blocked":         "🚫 Engellenenler",
    "ask_folder_name":     "📁 Yeni klasör adını yazın:",
    "ask_file":            "📎 Dosya, resim, video gönderin — ya da link/metin yazın:",
    "ask_del_folder":      "Silinecek klasörü seçin:",
    "ask_del_file":        "Silinecek dosyayı seçin:",
    "ask_edit_folder":     "Düzenlenecek klasörü seçin:",
    "ask_edit_file":       "Düzenlenecek dosyayı seçin:",
    "ask_new_folder_name": "Yeni klasör adını yazın:",
    "ask_new_file_name":   "Yeni dosya adını yazın:",
    "ask_admin_id":        "Eklenecek admin ID'sini yazın:",
    "ask_remove_admin":    "Çıkarılacak admini seçin:",
    "ask_bot_name":        "Yeni bot adını yazın (mevcut: {}):",
    "ask_welcome_msg":     "Yeni karşılama mesajını yazın:",
    "ask_bot_photo":       "Yeni bot fotoğrafını gönderin:",
    "err_empty":           "❌ Ad boş olamaz!",
    "err_exists":          "❌ '{}' zaten var!",
    "err_no_folder":       "Klasör yok!",
    "err_no_file":         "Dosya yok!",
    "err_no_perm":         "⛔ Yetkin yok.",
    "err_file_send":       "❌ Dosya gönderilemedi.",
    "err_unknown_file":    "❓ Bilinmeyen tür.",
    "err_unsupported":     "❓ Desteklenmeyen tür.",
    "err_invalid_id":      "❌ Geçersiz ID.",
    "err_already_admin":   "❌ Zaten admin.",
    "err_admin_self":      "❌ Kendinizi çıkaramazsınız.",
    "ok_folder_added":     "✅ '{}' klasörü eklendi.",
    "ok_folder_deleted":   "✅ '{}' klasörü silindi.",
    "ok_folder_renamed":   "✅ '{}' → '{}'",
    "ok_file_added":       "✅ Eklendi: {}",
    "ok_file_deleted":     "✅ '{}' silindi.",
    "ok_file_renamed":     "✅ Yeni ad: '{}'",
    "ok_admin_added":      "✅ Admin eklendi: {}",
    "ok_admin_removed":    "✅ Admin çıkarıldı: {}",
    "ok_bot_name":         "✅ Bot adı: '{}'",
    "ok_welcome_msg":      "✅ Karşılama mesajı güncellendi.",
    "ok_bot_photo":        "✅ Bot fotoğrafı güncellendi.",
    "no_users":            "Henüz kullanıcı yok.",
    "users_title":         "👥 KULLANICI LİSTESİ\n",
    "no_admins":           "Ek admin yok.",
    "no_removable":        "Çıkarılacak admin yok.",
    "admins_title":        "👑 ADMİN LİSTESİ\n",
    "settings_title":      "⚙️ BOT AYARLARI\n",
}

AR = {
    "home":                "🏠 الصفحة الرئيسية",
    "folders_lbl":         "📁 المجلدات:",
    "files_lbl":           "📎 الملفات:",
    "no_content":          "📭 لا يوجد محتوى بعد",
    "admin_mode":          "👑 وضع المشرف",
    "maint_on_lbl":        "🔧 الصيانة: مفعّلة",
    "maint_off_lbl":       "✅ الصيانة: معطّلة",
    "maint_msg":           "🔧 البوت قيد التحديث، يرجى الانتظار...",
    "btn_add_folder":      "➕ إضافة مجلد",
    "btn_del_folder":      "🗑 حذف مجلد",
    "btn_edit_folder":     "✏️ تعديل مجلد",
    "btn_add_file":        "📎 إضافة ملف/وسائط",
    "btn_del_file":        "🗑 حذف ملف",
    "btn_edit_file":       "✏️ تعديل ملف",
    "btn_back":            "◀️ رجوع",
    "btn_home":            "🏠 الرئيسية",
    "btn_cancel":          "❌ إلغاء",
    "btn_stats":           "📊 الإحصائيات",
    "btn_users":           "👥 المستخدمون",
    "btn_list_admins":     "📋 قائمة المشرفين",
    "btn_add_admin":       "👤 إضافة مشرف",
    "btn_del_admin":       "🚫 إزالة مشرف",
    "btn_bot_settings":    "⚙️ إعدادات البوت",
    "btn_set_bot_name":    "📝 اسم البوت",
    "btn_set_welcome":     "💬 رسالة الترحيب",
    "btn_set_photo":       "🖼 صورة البوت",
    "btn_blocked":         "🚫 المحظورون",
    "ask_folder_name":     "📁 اكتب اسم المجلد الجديد:",
    "ask_file":            "📎 أرسل ملفاً أو صورة أو فيديو — أو اكتب رابطاً:",
    "ask_del_folder":      "اختر المجلد للحذف:",
    "ask_del_file":        "اختر الملف للحذف:",
    "ask_edit_folder":     "اختر المجلد للتعديل:",
    "ask_edit_file":       "اختر الملف للتعديل:",
    "ask_new_folder_name": "اكتب الاسم الجديد للمجلد:",
    "ask_new_file_name":   "اكتب الاسم الجديد للملف:",
    "ask_admin_id":        "اكتب معرف المشرف الجديد:",
    "ask_remove_admin":    "اختر المشرف للإزالة:",
    "ask_bot_name":        "اكتب الاسم الجديد للبوت (الحالي: {}):",
    "ask_welcome_msg":     "اكتب رسالة الترحيب الجديدة:",
    "ask_bot_photo":       "أرسل الصورة الجديدة للبوت:",
    "err_empty":           "❌ الاسم لا يمكن أن يكون فارغاً!",
    "err_exists":          "❌ '{}' موجود بالفعل!",
    "err_no_folder":       "لا يوجد مجلد!",
    "err_no_file":         "لا يوجد ملف!",
    "err_no_perm":         "⛔ ليس لديك صلاحية.",
    "err_file_send":       "❌ تعذّر إرسال الملف.",
    "err_unknown_file":    "❓ نوع غير معروف.",
    "err_unsupported":     "❓ نوع غير مدعوم.",
    "err_invalid_id":      "❌ معرف غير صالح.",
    "err_already_admin":   "❌ مشرف بالفعل.",
    "err_admin_self":      "❌ لا يمكنك إزالة نفسك.",
    "ok_folder_added":     "✅ تمت إضافة '{}'.",
    "ok_folder_deleted":   "✅ تم حذف '{}'.",
    "ok_folder_renamed":   "✅ '{}' → '{}'",
    "ok_file_added":       "✅ تمت الإضافة: {}",
    "ok_file_deleted":     "✅ تم حذف '{}'.",
    "ok_file_renamed":     "✅ الاسم الجديد: '{}'",
    "ok_admin_added":      "✅ تمت إضافة المشرف: {}",
    "ok_admin_removed":    "✅ تمت إزالة المشرف: {}",
    "ok_bot_name":         "✅ اسم البوت: '{}'",
    "ok_welcome_msg":      "✅ تم تحديث رسالة الترحيب.",
    "ok_bot_photo":        "✅ تم تحديث صورة البوت.",
    "no_users":            "لا يوجد مستخدمون بعد.",
    "users_title":         "👥 قائمة المستخدمين\n",
    "no_admins":           "لا يوجد مشرفون إضافيون.",
    "no_removable":        "لا يوجد مشرفون لإزالتهم.",
    "admins_title":        "👑 قائمة المشرفين\n",
    "settings_title":      "⚙️ إعدادات البوت\n",
}

def t(uid, key):
    d = TR if int(uid) == ADMIN_ID else AR
    return d.get(key, key)


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
def load_pending():   return load_json(PENDING_FILE,  [])
def save_pending(d):  save_json(PENDING_FILE, d)

def load_settings():
    default = {
        "maintenance":      False,
        "maintenance_text": AR["maint_msg"],
        "bot_name":         "Bot",
        "welcome_msg":      "",
        "bot_photo_id":     None,
    }
    data = load_json(SETTINGS_FILE, default)
    for k, v in default.items():
        data.setdefault(k, v)
    return data

def save_settings(d): save_json(SETTINGS_FILE, d)


# ═══════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════

def is_main_admin(uid): return int(uid) == ADMIN_ID
def is_admin(uid):
    return int(uid) == ADMIN_ID or int(uid) in [int(x) for x in load_admins()]
def is_blocked(uid):
    return int(uid) in [int(x) for x in load_blocked()]

def register_user(user):
    users = load_users()
    uid   = str(user.id)
    users[uid] = {
        "id":         user.id,
        "first_name": user.first_name or "",
        "last_name":  user.last_name  or "",
        "username":   user.username   or "",
        "full_name":  user.full_name  or "",
        "last_seen":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_users(users)

def log_message(user, msg_type, content, extra=None):
    if is_admin(user.id):
        return
    msgs = load_messages()
    uid  = str(user.id)
    entry = {
        "time":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type":    msg_type,
        "content": str(content)[:500],
    }
    if extra:
        entry.update(extra)
    msgs.setdefault(uid, []).append(entry)
    msgs[uid] = msgs[uid][-1000:]
    save_messages(msgs)

def get_current_folder(content, path):
    cur = content
    for name in path:
        cur = cur.setdefault("folders", {}).setdefault(name, {"folders": {}, "files": []})
    return cur

def format_folder(folder, path, uid, admin=False):
    header = t(uid, "home") if not path else "📂 " + " › ".join(path)
    lines  = [header, "─" * 22, ""]
    folds  = folder.get("folders", {})
    files  = folder.get("files",   [])
    if folds:
        lines.append(t(uid, "folders_lbl"))
        for f in folds: lines.append(f"   • {f}")
        lines.append("")
    if files:
        lines.append(t(uid, "files_lbl"))
        for f in files: lines.append(f"   • {f.get('caption', f.get('name', '?'))}")
        lines.append("")
    if not (folds or files):
        lines.append(t(uid, "no_content"))
        lines.append("")
    if admin:
        s      = load_settings()
        status = t(uid, "maint_on_lbl") if s["maintenance"] else t(uid, "maint_off_lbl")
        lines.append(f"{t(uid, 'admin_mode')} | {status}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════
#  REPLY KEYBOARD
# ═══════════════════════════════════════════════════════

def reply_kb(uid):
    if is_main_admin(uid):
        rows = [
            [KeyboardButton(MGMT_BTN_TR),    KeyboardButton(CONTENT_BTN_TR)],
            [KeyboardButton(SETTINGS_BTN_TR), KeyboardButton(MAINT_BTN_TR)],
        ]
    elif is_admin(uid):
        rows = [
            [KeyboardButton(MGMT_BTN_TR),    KeyboardButton(CONTENT_BTN_TR)],
            [KeyboardButton(MAINT_BTN_TR)],
        ]
    else:
        rows = [[KeyboardButton(MENU_BTN_AR)]]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False)


# ═══════════════════════════════════════════════════════
#  INLINE KEYBOARD — sadece içerik + navigasyon
# ═══════════════════════════════════════════════════════

def build_inline_keyboard(path, folder, uid, admin=False):
    kb = []
    sub = list(folder.get("folders", {}).keys())
    if sub:
        for i in range(0, min(len(sub), 8), 4):
            kb.append([InlineKeyboardButton(f"📁 {n}", callback_data=f"open_{n}") for n in sub[i:i+4]])
        if len(sub) > 8:
            kb.append([InlineKeyboardButton(f"… +{len(sub)-8}", callback_data="noop")])
    for idx, f in enumerate(folder.get("files", [])[:10]):
        cap = f.get("caption", f.get("name", "?"))
        kb.append([InlineKeyboardButton(f"📎 {cap}", callback_data=f"getfile_{idx}")])
    nav = []
    if path:
        nav.append(InlineKeyboardButton(t(uid, "btn_back"), callback_data="nav_back"))
        nav.append(InlineKeyboardButton(t(uid, "btn_home"), callback_data="nav_root"))
    if nav:
        kb.append(nav)
    return InlineKeyboardMarkup(kb)


# ═══════════════════════════════════════════════════════
#  DOSYA İNDİRME
# ═══════════════════════════════════════════════════════

async def download_to_disk(context, file_id: str, filename: str) -> Optional[str]:
    try:
        tg_file = await context.bot.get_file(file_id)
        safe    = "".join(c for c in filename if c.isalnum() or c in "._- ").strip() or \
                  f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        dest    = os.path.join(FILES_DIR, safe)
        base, ext = os.path.splitext(dest)
        n = 1
        while os.path.exists(dest):
            dest = f"{base}_{n}{ext}"; n += 1
        await tg_file.download_to_drive(dest)
        return dest
    except Exception as e:
        logger.warning(f"İndirme başarısız ({filename}): {e}")
        pending = load_pending()
        pending.append({"file_id": file_id, "filename": filename, "time": datetime.now().isoformat()})
        save_pending(pending)
        return None

async def process_pending_downloads(context):
    pending = load_pending()
    if not pending:
        return
    remaining = []
    for item in pending:
        result = await download_to_disk(context, item["file_id"], item["filename"])
        if result is None:
            remaining.append(item)
    save_pending(remaining)


# ═══════════════════════════════════════════════════════
#  REFRESH YARDIMCILARI
# ═══════════════════════════════════════════════════════

async def _refresh_inline(query, content, path, uid, extra=""):
    current = get_current_folder(content, path)
    text    = format_folder(current, path, uid, admin=True)
    if extra: text += f"\n\n{extra}"
    try:
        await query.edit_message_text(text, reply_markup=build_inline_keyboard(path, current, uid, admin=True))
    except Exception:
        pass

async def _send_home(update, uid, path=None):
    path    = path or []
    content = load_content()
    current = get_current_folder(content, path)
    text    = format_folder(current, path, uid, admin=is_admin(uid))
    msg     = update.message if hasattr(update, "message") else update
    kb      = build_inline_keyboard(path, current, uid, admin=is_admin(uid))
    # Eğer reply keyboard varsa birleştir
    try:
        await msg.edit_text(text, reply_markup=kb)
    except Exception:
        await msg.reply_text(text, reply_markup=kb)

async def _send_refresh(update, content, path, uid, extra=""):
    current = get_current_folder(content, path)
    text    = format_folder(current, path, uid, admin=True)
    if extra: text += f"\n\n{extra}"
    await update.message.reply_text(text, reply_markup=build_inline_keyboard(path, current, uid, admin=True))


# ═══════════════════════════════════════════════════════
#  DOSYA GÖNDERME
# ═══════════════════════════════════════════════════════

async def _send_file(query, f, uid):
    ftype, fid, cap, url = f.get("type"), f.get("file_id"), f.get("caption",""), f.get("url","")
    try:
        if   ftype == "photo":     await query.message.reply_photo(fid,     caption=cap)
        elif ftype == "video":     await query.message.reply_video(fid,     caption=cap)
        elif ftype == "animation": await query.message.reply_animation(fid, caption=cap)
        elif ftype == "document":  await query.message.reply_document(fid,  caption=cap)
        elif ftype == "audio":     await query.message.reply_audio(fid,     caption=cap)
        elif ftype == "voice":     await query.message.reply_voice(fid,     caption=cap)
        elif ftype == "link":      await query.message.reply_text(f"🔗 {cap}\n{url}" if cap != url else f"🔗 {url}")
        elif ftype == "text":      await query.message.reply_text(cap)
        else:                      await query.message.reply_text(t(uid, "err_unknown_file"))
    except Exception as e:
        logger.error(f"Dosya gönderilemedi: {e}")
        await query.message.reply_text(t(uid, "err_file_send"))


# ═══════════════════════════════════════════════════════
#  /start
# ═══════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = str(user.id)
    register_user(user)
    log_message(user, "command", "/start")
    s = load_settings()

    if is_blocked(uid) and not is_admin(uid):
        return

    context.user_data["path"] = []

    if not is_admin(uid):
        if s["maintenance"]:
            await update.message.reply_text(s["maintenance_text"], reply_markup=reply_kb(uid))
            return
        welcome = s.get("welcome_msg", "")
        photo   = s.get("bot_photo_id")
        content = load_content()
        current = get_current_folder(content, [])
        folder_text = format_folder(current, [], uid, admin=False)
        if photo:
            await update.message.reply_photo(photo, caption=welcome or None)
        if welcome and not photo:
            await update.message.reply_text(welcome, reply_markup=reply_kb(uid))
        await update.message.reply_text(
            folder_text,
            reply_markup=build_inline_keyboard([], current, uid, admin=False),
        )
        return

    content = load_content()
    current = get_current_folder(content, [])
    # Admin paneli: reply keyboard ayrı mesajda değil, önce reply_kb kur, sonra içerik
    await update.message.reply_text(
        "👑 Admin paneline hoş geldiniz.",
        reply_markup=reply_kb(uid),
    )
    await update.message.reply_text(
        format_folder(current, [], uid, admin=True),
        reply_markup=build_inline_keyboard([], current, uid, admin=True),
    )


# ═══════════════════════════════════════════════════════
#  REPLY KEYBOARD HANDLER — tüm butonlar burada
# ═══════════════════════════════════════════════════════

async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply Keyboard butonlarını işler. ConversationHandler dışında çalışır."""
    user = update.effective_user
    uid  = str(user.id)
    text = (update.message.text or "").strip()

    register_user(user)

    # ── Menü (kullanıcı) ──────────────────────────────────────
    if text == MENU_BTN_AR:
        context.user_data["path"] = []
        s2 = load_settings()
        if s2["maintenance"] and not is_admin(uid):
            await update.message.reply_text(s2["maintenance_text"])
            return
        content2 = load_content()
        current2 = get_current_folder(content2, [])
        await update.message.reply_text(
            format_folder(current2, [], uid, admin=False),
            reply_markup=build_inline_keyboard([], current2, uid, admin=False),
        )
        return

    if not is_admin(uid):
        return

    # ── Yönetim ───────────────────────────────────────────────
    if text == MGMT_BTN_TR:
        rows = [[
            InlineKeyboardButton(t(uid, "btn_stats"), callback_data="show_stats"),
            InlineKeyboardButton(t(uid, "btn_users"), callback_data="show_users"),
        ]]
        if is_main_admin(uid):
            rows.append([InlineKeyboardButton(t(uid, "btn_list_admins"), callback_data="show_admins")])
            rows.append([
                InlineKeyboardButton(t(uid, "btn_add_admin"), callback_data="admin_add"),
                InlineKeyboardButton(t(uid, "btn_del_admin"), callback_data="admin_remove"),
            ])
        rows.append([InlineKeyboardButton(t(uid, "btn_back"), callback_data="nav_root")])
        await update.message.reply_text("👥 Yönetim", reply_markup=InlineKeyboardMarkup(rows))
        return

    # ── İçerik Yönetimi ───────────────────────────────────────
    if text == CONTENT_BTN_TR:
        rows = [
            [
                InlineKeyboardButton(t(uid, "btn_add_folder"), callback_data="folder_add"),
                InlineKeyboardButton(t(uid, "btn_del_folder"), callback_data="folder_delete"),
            ],
            [
                InlineKeyboardButton(t(uid, "btn_edit_folder"), callback_data="folder_edit"),
                InlineKeyboardButton(t(uid, "btn_edit_file"),   callback_data="file_edit"),
            ],
            [
                InlineKeyboardButton(t(uid, "btn_add_file"), callback_data="file_add"),
                InlineKeyboardButton(t(uid, "btn_del_file"), callback_data="file_delete"),
            ],
            [InlineKeyboardButton(t(uid, "btn_back"), callback_data="nav_root")],
        ]
        await update.message.reply_text("📁 İçerik Yönetimi", reply_markup=InlineKeyboardMarkup(rows))
        return

    # ── Bot Ayarları ──────────────────────────────────────────
    if text == SETTINGS_BTN_TR and is_main_admin(uid):
        s   = load_settings()
        txt = (f"{t(uid,'settings_title')}\n"
               f"📝 Ad: {s.get('bot_name','—')}\n"
               f"💬 Karşılama:\n{s.get('welcome_msg','—')}\n"
               f"🖼 Fotoğraf: {'✅' if s.get('bot_photo_id') else '❌'}\n"
               f"🚫 Engellenenler: {len(load_blocked())} kişi")
        kb  = [
            [InlineKeyboardButton(t(uid,"btn_set_bot_name"), callback_data="set_bot_name")],
            [InlineKeyboardButton(t(uid,"btn_set_welcome"),  callback_data="set_welcome")],
            [InlineKeyboardButton(t(uid,"btn_set_photo"),    callback_data="set_photo")],
            [InlineKeyboardButton(t(uid,"btn_blocked"),      callback_data="show_blocked")],
            [InlineKeyboardButton(t(uid,"btn_back"),         callback_data="nav_root")],
        ]
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    # ── Bakım Modu ────────────────────────────────────────────
    if text == MAINT_BTN_TR:
        s = load_settings()
        s["maintenance"] = not s["maintenance"]
        save_settings(s)
        durum = "AÇIK 🔧" if s["maintenance"] else "KAPALI ✅"
        await update.message.reply_text(f"Bakım Modu: {durum}")
        return


# ═══════════════════════════════════════════════════════
#  CALLBACK (inline buton tıklamaları)
# ═══════════════════════════════════════════════════════

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user  = query.from_user
    uid   = str(user.id)
    admin = is_admin(uid)
    cb    = query.data

    if is_blocked(uid) and not admin:
        return ConversationHandler.END
    if not admin:
        s = load_settings()
        if s["maintenance"]:
            await query.answer(AR["maint_msg"], show_alert=True)
            return ConversationHandler.END

    content = load_content()
    path    = context.user_data.get("path", [])
    current = get_current_folder(content, path)

    if cb == "noop":
        return ConversationHandler.END

    # ── Dosya aç ──────────────────────────────────────────────
    if cb.startswith("getfile_"):
        idx   = int(cb[8:])
        files = current.get("files", [])
        if idx >= len(files):
            await query.answer(t(uid, "err_no_file"), show_alert=True)
            return ConversationHandler.END
        log_message(user, "file_view", files[idx].get("caption", ""))
        await _send_file(query, files[idx], uid)
        return ConversationHandler.END

    # ── Navigasyon ────────────────────────────────────────────
    if cb == "nav_back":
        if path: path.pop(); context.user_data["path"] = path
        cur = get_current_folder(content, path)
        try: await query.edit_message_text(format_folder(cur, path, uid, admin), reply_markup=build_inline_keyboard(path, cur, uid, admin))
        except: pass
        return ConversationHandler.END

    if cb == "nav_root":
        context.user_data["path"] = []
        cur = get_current_folder(content, [])
        try: await query.edit_message_text(format_folder(cur, [], uid, admin), reply_markup=build_inline_keyboard([], cur, uid, admin))
        except: pass
        return ConversationHandler.END

    if cb.startswith("open_"):
        name = cb[5:]; path.append(name); context.user_data["path"] = path
        cur  = get_current_folder(content, path)
        try: await query.edit_message_text(format_folder(cur, path, uid, admin), reply_markup=build_inline_keyboard(path, cur, uid, admin))
        except: pass
        return ConversationHandler.END

    # ── İstatistik ────────────────────────────────────────────
    if cb == "show_stats" and admin:
        u_d = load_users(); m_d = load_messages(); s = load_settings()
        total = sum(len(v) for v in m_d.values())
        def _cnt(node):
            c = 0
            for f in node.get("folders", {}).values(): c += 1 + _cnt(f)
            return c
        txt = (f"📊 İSTATİSTİKLER\n\n👥 Kullanıcı: {len(u_d)}\n💬 Mesaj: {total}\n"
               f"📁 Klasör: {_cnt(content)}\n📎 Dosya: {len(content.get('files',[]))}\n"
               f"🔧 Bakım: {'Açık' if s['maintenance'] else 'Kapalı'}")
        kb = [[InlineKeyboardButton(t(uid,"btn_back"), callback_data="nav_root")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END

    # ── Kullanıcılar ──────────────────────────────────────────
    if cb == "show_users" and admin:
        u_d = load_users()
        if not u_d:
            await query.answer(t(uid,"no_users"), show_alert=True); return ConversationHandler.END
        lines = ["👥 KULLANICI LİSTESİ\nBir kullanıcı seçin:\n"]
        kb = []
        for uid_, u in list(u_d.items())[-50:]:
            if int(uid_) == ADMIN_ID: continue
            name = u.get("full_name") or u.get("first_name") or f"ID:{uid_}"
            un   = f" @{u['username']}" if u.get("username") else ""
            kb.append([InlineKeyboardButton(f"👤 {name}{un}", callback_data=f"view_user_{uid_}")])
        kb.append([InlineKeyboardButton(t(uid,"btn_back"), callback_data="nav_root")])
        await query.edit_message_text("👥 Kullanıcı Listesi\nGörmek istediğiniz kullanıcıyı seçin:", reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END

    if cb.startswith("view_user_") and admin:
        target_uid = cb[10:]
        u_d  = load_users()
        msgs = load_messages()
        u    = u_d.get(target_uid, {})
        name = u.get("full_name") or u.get("first_name") or f"ID:{target_uid}"
        un   = f"@{u['username']}" if u.get("username") else "—"
        user_msgs = msgs.get(target_uid, [])
        total = len(user_msgs)
        # Son 20 mesajı göster
        recent = user_msgs[-20:]
        lines = [
            f"👤 {name} ({un})",
            f"🆔 {target_uid}",
            f"🕐 Son görülme: {u.get('last_seen','—')}",
            f"💬 Toplam mesaj: {total}",
            "─" * 24,
        ]
        type_icons = {
            "text": "💬", "msg": "💬", "photo": "🖼", "video": "🎥",
            "document": "📄", "audio": "🎵", "voice": "🎙", "animation": "🎞",
            "sticker": "😊", "command": "⚙️", "media": "📎", "file_view": "👁",
        }
        for m in recent:
            icon = type_icons.get(m.get("type",""), "📨")
            time_str = m.get("time","")[-8:]  # sadece saat
            content  = m.get("content","")[:60]
            lines.append(f"{icon} [{time_str}] {content}")
        text_out = "\n".join(lines)[:4000]
        kb = [
            [InlineKeyboardButton("🖼 Medyaları Gönder", callback_data=f"send_media_{target_uid}")],
            [InlineKeyboardButton("🚫 Engelle", callback_data=f"block_user_{target_uid}"),
             InlineKeyboardButton("◀️ Geri", callback_data="show_users")],
        ]
        await query.edit_message_text(text_out, reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END

    if cb.startswith("send_media_") and admin:
        target_uid = cb[11:]
        msgs = load_messages()
        user_msgs = msgs.get(target_uid, [])
        media_msgs = [m for m in user_msgs if m.get("file_id")]
        if not media_msgs:
            await query.answer("Bu kullanıcıdan medya yok.", show_alert=True)
            return ConversationHandler.END
        await query.answer(f"{len(media_msgs)} medya gönderiliyor...")
        sent = 0
        for m in media_msgs[-20:]:  # son 20 medya
            fid   = m.get("file_id")
            ftype = m.get("type","")
            cap   = f"[{m.get('time','')}] {m.get('content','')}"[:200]
            try:
                if ftype == "photo":      await query.message.reply_photo(fid, caption=cap)
                elif ftype == "video":    await query.message.reply_video(fid, caption=cap)
                elif ftype == "document": await query.message.reply_document(fid, caption=cap)
                elif ftype == "audio":    await query.message.reply_audio(fid, caption=cap)
                elif ftype == "voice":    await query.message.reply_voice(fid, caption=cap)
                elif ftype == "animation":await query.message.reply_animation(fid, caption=cap)
                elif ftype == "sticker":  await query.message.reply_sticker(fid)
                sent += 1
            except Exception as e:
                logger.warning(f"Medya gönderilemedi: {e}")
        await query.message.reply_text(f"✅ {sent}/{len(media_msgs[-20:])} medya gönderildi.")
        return ConversationHandler.END

    if cb.startswith("block_user_") and admin:
        target_uid = cb[11:]
        blocked = load_blocked()
        if int(target_uid) not in blocked:
            blocked.append(int(target_uid)); save_blocked(blocked)
            await query.answer(f"✅ {target_uid} engellendi.", show_alert=True)
        else:
            await query.answer("Zaten engelli.", show_alert=True)
        return ConversationHandler.END

    # ── Admin listesi ─────────────────────────────────────────
    if cb == "show_admins" and is_main_admin(uid):
        admins = load_admins()
        txt    = t(uid,"admins_title") + ("\n".join(f"🆔 {a}" for a in admins) if admins else t(uid,"no_admins"))
        kb     = [[InlineKeyboardButton(t(uid,"btn_back"), callback_data="nav_root")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END

    # ── Admin ekle/çıkar ──────────────────────────────────────
    if cb == "admin_add" and is_main_admin(uid):
        context.user_data["action"] = "admin_add"
        kb = [[InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")]]
        await query.edit_message_text(t(uid,"ask_admin_id"), reply_markup=InlineKeyboardMarkup(kb))
        return WAITING_ADMIN_ID

    if cb == "admin_remove" and is_main_admin(uid):
        admins = load_admins()
        if not admins:
            await query.answer(t(uid,"no_removable"), show_alert=True); return ConversationHandler.END
        kb = [[InlineKeyboardButton(f"🚫 {a}", callback_data=f"rem_admin_{a}")] for a in admins]
        kb.append([InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")])
        await query.edit_message_text(t(uid,"ask_remove_admin"), reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END

    if cb.startswith("rem_admin_") and is_main_admin(uid):
        rem = int(cb[10:]); admins = load_admins()
        if rem in admins: admins.remove(rem); save_admins(admins)
        await _refresh_inline(query, content, path, uid, t(uid,"ok_admin_removed").format(rem))
        return ConversationHandler.END

    # ── Bot ayarları ──────────────────────────────────────────
    if cb == "set_bot_name" and is_main_admin(uid):
        context.user_data["action"] = "set_bot_name"
        s  = load_settings()
        kb = [[InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")]]
        await query.edit_message_text(t(uid,"ask_bot_name").format(s.get("bot_name","—")), reply_markup=InlineKeyboardMarkup(kb))
        return WAITING_BOT_NAME

    if cb == "set_welcome" and is_main_admin(uid):
        context.user_data["action"] = "set_welcome"
        kb = [[InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")]]
        await query.edit_message_text(t(uid,"ask_welcome_msg"), reply_markup=InlineKeyboardMarkup(kb))
        return WAITING_BOT_WELCOME

    if cb == "set_photo" and is_main_admin(uid):
        context.user_data["action"] = "set_photo"
        kb = [[InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")]]
        await query.edit_message_text(t(uid,"ask_bot_photo"), reply_markup=InlineKeyboardMarkup(kb))
        return WAITING_BOT_PHOTO

    if cb == "show_blocked" and is_main_admin(uid):
        blocked = load_blocked()
        txt  = f"🚫 Engellenenler ({len(blocked)})\n\n"
        txt += "\n".join(f"🆔 {b}" for b in blocked) if blocked else "Henüz kimse engellenmedi."
        kb   = [[InlineKeyboardButton(t(uid,"btn_back"), callback_data="nav_root")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END

    if not admin:
        await query.answer(t(uid,"err_no_perm"), show_alert=True); return ConversationHandler.END

    # ── Klasör ekle ───────────────────────────────────────────
    if cb == "folder_add":
        context.user_data["action"] = "folder_add"
        kb = [[InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")]]
        await query.edit_message_text(t(uid,"ask_folder_name"), reply_markup=InlineKeyboardMarkup(kb))
        return WAITING_FOLDER_NAME

    if cb == "folder_delete":
        folders = list(current.get("folders",{}).keys())
        if not folders:
            await query.answer(t(uid,"err_no_folder"), show_alert=True); return ConversationHandler.END
        context.user_data["action"] = "folder_delete"
        kb = [[InlineKeyboardButton(f"🗑 {f}", callback_data=f"select_{f}")] for f in folders]
        kb.append([InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")])
        await query.edit_message_text(t(uid,"ask_del_folder"), reply_markup=InlineKeyboardMarkup(kb))
        return WAITING_NEW_FOLDER_NAME

    if cb == "folder_edit":
        folders = list(current.get("folders",{}).keys())
        if not folders:
            await query.answer(t(uid,"err_no_folder"), show_alert=True); return ConversationHandler.END
        context.user_data["action"] = "folder_edit"
        kb = [[InlineKeyboardButton(f"✏️ {f}", callback_data=f"editfolder_{f}")] for f in folders]
        kb.append([InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")])
        await query.edit_message_text(t(uid,"ask_edit_folder"), reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END

    if cb.startswith("editfolder_"):
        context.user_data["action"]        = "folder_rename"
        context.user_data["rename_target"] = cb[11:]
        kb = [[InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")]]
        await query.edit_message_text(t(uid,"ask_new_folder_name"), reply_markup=InlineKeyboardMarkup(kb))
        return WAITING_RENAME_FOLDER

    if cb == "file_add":
        context.user_data["action"] = "file_add"
        kb = [[InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")]]
        await query.edit_message_text(t(uid,"ask_file"), reply_markup=InlineKeyboardMarkup(kb))
        return WAITING_FILE_CONTENT

    if cb == "file_delete":
        files = current.get("files",[])
        if not files:
            await query.answer(t(uid,"err_no_file"), show_alert=True); return ConversationHandler.END
        context.user_data["action"] = "file_delete"
        kb = [[InlineKeyboardButton(f"🗑 {f.get('caption','?')}", callback_data=f"select_{i}")] for i,f in enumerate(files)]
        kb.append([InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")])
        await query.edit_message_text(t(uid,"ask_del_file"), reply_markup=InlineKeyboardMarkup(kb))
        return WAITING_NEW_ITEM_NAME

    if cb == "file_edit":
        files = current.get("files",[])
        if not files:
            await query.answer(t(uid,"err_no_file"), show_alert=True); return ConversationHandler.END
        context.user_data["action"] = "file_edit"
        kb = [[InlineKeyboardButton(f"✏️ {f.get('caption','?')}", callback_data=f"editfile_{i}")] for i,f in enumerate(files)]
        kb.append([InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")])
        await query.edit_message_text(t(uid,"ask_edit_file"), reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END

    if cb.startswith("editfile_"):
        context.user_data["action"]        = "file_rename"
        context.user_data["rename_target"] = int(cb[9:])
        kb = [[InlineKeyboardButton(t(uid,"btn_cancel"), callback_data="cancel")]]
        await query.edit_message_text(t(uid,"ask_new_file_name"), reply_markup=InlineKeyboardMarkup(kb))
        return WAITING_RENAME_FILE

    if cb.startswith("select_"):
        sel    = cb[7:]
        action = context.user_data.get("action","")
        if action == "folder_delete":
            if sel in current.get("folders",{}):
                del current["folders"][sel]; save_content(content)
            await _refresh_inline(query, content, path, uid, t(uid,"ok_folder_deleted").format(sel))
        elif action == "file_delete":
            idx   = int(sel); files = current.get("files",[])
            if 0 <= idx < len(files):
                removed = files.pop(idx); save_content(content)
                await _refresh_inline(query, content, path, uid, t(uid,"ok_file_deleted").format(removed.get("caption","?")))
        return ConversationHandler.END

    if cb == "cancel":
        context.user_data.pop("action", None); context.user_data.pop("rename_target", None)
        await _refresh_inline(query, content, path, uid)
        return ConversationHandler.END

    return ConversationHandler.END


# ═══════════════════════════════════════════════════════
#  METİN GİRİŞİ (sadece conversation state'lerinde)
# ═══════════════════════════════════════════════════════

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user    = update.effective_user
    uid     = str(user.id)
    text    = (update.message.text or "").strip()

    register_user(user)
    log_message(user, "text", text)

    if not is_admin(uid):
        return ConversationHandler.END

    content = load_content()
    path    = context.user_data.get("path", [])
    current = get_current_folder(content, path)
    action  = context.user_data.get("action", "")

    if action == "admin_add" and is_main_admin(uid):
        try:    new_id = int(text)
        except: await update.message.reply_text(t(uid,"err_invalid_id")); return WAITING_ADMIN_ID
        admins = load_admins()
        if new_id in admins or new_id == ADMIN_ID:
            await update.message.reply_text(t(uid,"err_already_admin"))
        else:
            admins.append(new_id); save_admins(admins)
            await _send_refresh(update, content, path, uid, t(uid,"ok_admin_added").format(new_id))
        context.user_data.pop("action", None); return ConversationHandler.END

    if action == "folder_add":
        if not text: await update.message.reply_text(t(uid,"err_empty")); return WAITING_FOLDER_NAME
        if text in current.get("folders",{}): await update.message.reply_text(t(uid,"err_exists").format(text)); return WAITING_FOLDER_NAME
        current.setdefault("folders",{})[text] = {"folders":{},"files":[]}; save_content(content)
        await _send_refresh(update, content, path, uid, t(uid,"ok_folder_added").format(text))
        context.user_data.pop("action", None); return ConversationHandler.END

    if action == "folder_rename":
        old   = context.user_data.get("rename_target","")
        if not text: await update.message.reply_text(t(uid,"err_empty")); return WAITING_RENAME_FOLDER
        folds = current.get("folders",{})
        if text in folds: await update.message.reply_text(t(uid,"err_exists").format(text)); return WAITING_RENAME_FOLDER
        if old in folds: folds[text] = folds.pop(old); save_content(content)
        await _send_refresh(update, content, path, uid, t(uid,"ok_folder_renamed").format(old, text))
        context.user_data.pop("action", None); context.user_data.pop("rename_target", None); return ConversationHandler.END

    if action == "file_rename":
        idx   = context.user_data.get("rename_target", 0)
        files = current.get("files",[])
        if not text: await update.message.reply_text(t(uid,"err_empty")); return WAITING_RENAME_FILE
        if 0 <= idx < len(files): files[idx]["caption"] = text; files[idx]["name"] = text; save_content(content)
        await _send_refresh(update, content, path, uid, t(uid,"ok_file_renamed").format(text))
        context.user_data.pop("action", None); context.user_data.pop("rename_target", None); return ConversationHandler.END

    if action == "file_add":
        if text.startswith("http://") or text.startswith("https://"):
            fobj = {"type":"link","url":text,"caption":text,"name":text}
        else:
            fobj = {"type":"text","caption":text,"name":text}
        current.setdefault("files",[]).append(fobj); save_content(content)
        await _send_refresh(update, content, path, uid, t(uid,"ok_file_added").format(fobj["caption"][:50]))
        context.user_data.pop("action", None); return ConversationHandler.END

    if action == "set_bot_name" and is_main_admin(uid):
        if not text: await update.message.reply_text(t(uid,"err_empty")); return WAITING_BOT_NAME
        s = load_settings(); s["bot_name"] = text; save_settings(s)
        await _send_refresh(update, content, path, uid, t(uid,"ok_bot_name").format(text))
        context.user_data.pop("action", None); return ConversationHandler.END

    if action == "set_welcome" and is_main_admin(uid):
        s = load_settings(); s["welcome_msg"] = text; save_settings(s)
        await _send_refresh(update, content, path, uid, t(uid,"ok_welcome_msg"))
        context.user_data.pop("action", None); return ConversationHandler.END

    return ConversationHandler.END


# ═══════════════════════════════════════════════════════
#  MEDYA GİRİŞİ
# ═══════════════════════════════════════════════════════

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    uid  = str(user.id)
    msg  = update.message

    register_user(user)

    # Kullanıcı medyasını logla (admin değilse)
    if not is_admin(uid):
        if msg.photo:
            log_message(user, "photo", msg.caption or "(fotoğraf)", extra={"file_id": msg.photo[-1].file_id})
        elif msg.video:
            log_message(user, "video", msg.caption or msg.video.file_name or "(video)", extra={"file_id": msg.video.file_id})
        elif msg.document:
            log_message(user, "document", msg.document.file_name or "(dosya)", extra={"file_id": msg.document.file_id})
        elif msg.audio:
            log_message(user, "audio", msg.audio.file_name or "(ses)", extra={"file_id": msg.audio.file_id})
        elif msg.voice:
            log_message(user, "voice", "(sesli mesaj)", extra={"file_id": msg.voice.file_id})
        elif msg.animation:
            log_message(user, "animation", "(GIF)", extra={"file_id": msg.animation.file_id})

    if is_blocked(uid) and not is_admin(uid):
        return ConversationHandler.END

    if not is_admin(uid):
        s = load_settings()
        if s["maintenance"]: await msg.reply_text(s["maintenance_text"])
        return ConversationHandler.END

    action = context.user_data.get("action","")

    if action == "set_photo" and is_main_admin(uid):
        if msg.photo:
            s = load_settings(); s["bot_photo_id"] = msg.photo[-1].file_id; save_settings(s)
            content = load_content(); path = context.user_data.get("path",[])
            await _send_refresh(update, content, path, uid, t(uid,"ok_bot_photo"))
            context.user_data.pop("action", None)
        else:
            await msg.reply_text(t(uid,"err_unsupported"))
        return ConversationHandler.END

    if action != "file_add":
        return ConversationHandler.END

    content = load_content()
    path    = context.user_data.get("path",[])
    current = get_current_folder(content, path)
    caption = msg.caption or ""
    fobj    = None
    now     = datetime.now().strftime("%Y%m%d%H%M%S")

    async def _save(fid, fname, ftype, cap):
        local = await download_to_disk(context, fid, fname)
        return {"type": ftype, "file_id": fid, "caption": cap, "name": fname,
                **( {"local_path": local} if local else {})}

    try:
        if msg.photo:
            fobj = await _save(msg.photo[-1].file_id, f"photo_{now}.jpg", "photo", caption or "صورة")
        elif msg.video:
            fname = msg.video.file_name or f"video_{now}.mp4"
            fobj  = await _save(msg.video.file_id, fname, "video", caption or fname)
        elif msg.animation:
            fobj = await _save(msg.animation.file_id, f"gif_{now}.gif", "animation", caption or "GIF")
        elif msg.document:
            fname = msg.document.file_name or f"doc_{now}"
            fobj  = await _save(msg.document.file_id, fname, "document", caption or fname)
        elif msg.audio:
            fname = msg.audio.file_name or f"audio_{now}.mp3"
            fobj  = await _save(msg.audio.file_id, fname, "audio", caption or msg.audio.title or fname)
        elif msg.voice:
            fobj = await _save(msg.voice.file_id, f"voice_{now}.ogg", "voice", caption or "رسالة صوتية")
    except Exception as e:
        logger.error(f"handle_media hata: {e}")

    if fobj:
        current.setdefault("files",[]).append(fobj); save_content(content)
        await _send_refresh(update, content, path, uid, t(uid,"ok_file_added").format(fobj["caption"]))
        context.user_data.pop("action", None)
    else:
        await msg.reply_text(t(uid,"err_unsupported"))

    return ConversationHandler.END


# ═══════════════════════════════════════════════════════
#  GENEL MESAJ HANDLER (kullanıcı mesajları)
# ═══════════════════════════════════════════════════════

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user
    uid  = str(user.id)
    msg  = update.message
    text = (msg.text or "").strip()

    register_user(user)

    # Sadece metin ve sticker logla (medya handle_media'da loglanıyor)
    if msg.sticker:
        log_message(user, "sticker", msg.sticker.emoji or "(sticker)",
                    extra={"file_id": msg.sticker.file_id})
    elif text:
        log_message(user, "msg", text)

    if is_admin(uid): return
    if is_blocked(uid): return

    s = load_settings()
    if s["maintenance"]:
        await update.message.reply_text(s["maintenance_text"])


# ═══════════════════════════════════════════════════════
#  STARTUP
# ═══════════════════════════════════════════════════════

async def on_startup(app):
    await process_pending_downloads(app.bot)


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(on_startup)
        .build()
    )

    media_f = (filters.PHOTO | filters.VIDEO | filters.Document.ALL |
               filters.AUDIO | filters.VOICE | filters.ANIMATION)
    text_f  = filters.TEXT & ~filters.COMMAND

    # Reply keyboard buton filtresi
    reply_btn_filter = filters.Regex(
        f"^({MENU_BTN_AR}|{MGMT_BTN_TR}|{CONTENT_BTN_TR}|{SETTINGS_BTN_TR}|{MAINT_BTN_TR})$"
    )

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(callback)],
        states={
            WAITING_FOLDER_NAME:     [MessageHandler(text_f & ~reply_btn_filter, handle_text)],
            WAITING_NEW_FOLDER_NAME: [MessageHandler(text_f & ~reply_btn_filter, handle_text), CallbackQueryHandler(callback)],
            WAITING_FILE_CONTENT:    [MessageHandler(text_f & ~reply_btn_filter, handle_text),
                                      MessageHandler(media_f, handle_media), CallbackQueryHandler(callback)],
            WAITING_NEW_ITEM_NAME:   [MessageHandler(text_f & ~reply_btn_filter, handle_text), CallbackQueryHandler(callback)],
            WAITING_ADMIN_ID:        [MessageHandler(text_f & ~reply_btn_filter, handle_text), CallbackQueryHandler(callback)],
            WAITING_RENAME_FOLDER:   [MessageHandler(text_f & ~reply_btn_filter, handle_text), CallbackQueryHandler(callback)],
            WAITING_RENAME_FILE:     [MessageHandler(text_f & ~reply_btn_filter, handle_text), CallbackQueryHandler(callback)],
            WAITING_BOT_NAME:        [MessageHandler(text_f & ~reply_btn_filter, handle_text), CallbackQueryHandler(callback)],
            WAITING_BOT_WELCOME:     [MessageHandler(text_f & ~reply_btn_filter, handle_text), CallbackQueryHandler(callback)],
            WAITING_BOT_PHOTO:       [MessageHandler(media_f, handle_media), CallbackQueryHandler(callback)],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(reply_btn_filter, handle_reply_buttons),
            CallbackQueryHandler(callback, pattern="^cancel$"),
        ],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(reply_btn_filter, handle_reply_buttons))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_any_message))

    print("✅ Bot başlatıldı!")
    print(f"👑 Admin ID : {ADMIN_ID}")
    print(f"💾 Veri     : {BASE_DIR}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
