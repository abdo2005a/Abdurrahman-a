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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDm4bNXx3c3eDNXF1VPArZn2LxvPVcdznI")

_default_dir = "/data/bot_data" if os.path.exists("/data") else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "bot_data")
BASE_DIR  = os.environ.get("DATA_DIR", _default_dir)
FILES_DIR = os.path.join(BASE_DIR, "files")
os.makedirs(BASE_DIR,  exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

DATA_FILE       = os.path.join(BASE_DIR, "bot_data.json")
USERS_FILE      = os.path.join(BASE_DIR, "users.json")
MESSAGES_FILE   = os.path.join(BASE_DIR, "user_messages.json")
SETTINGS_FILE   = os.path.join(BASE_DIR, "settings.json")
ADMINS_FILE     = os.path.join(BASE_DIR, "admins.json")
BLOCKED_FILE    = os.path.join(BASE_DIR, "blocked.json")
AI_HISTORY_FILE = os.path.join(BASE_DIR, "ai_history.json")
# =============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
#  DİL SİSTEMİ  —  Süper Admin: TR  |  Diğer herkes: AR
# ═══════════════════════════════════════════════════════

TR = {
    "btn_menu":"📋 Menü","btn_mgmt":"👥 Yönetim","btn_content":"📁 İçerik",
    "btn_settings":"⚙️ Ayarlar","btn_maint":"🔧 Bakım","btn_chat":"🤖 AI Sohbet",
    "home":"🏠 ANA SAYFA","folder_list":"📁 Klasörler:","file_list":"📎 Dosyalar:",
    "empty":"📭 Henüz içerik yok","back":"◀️ Geri",
    "cancel":"❌ İptal","close":"◀️ Kapat",
    "maint_on":"🔧 Bakım: AÇIK","maint_off":"✅ Bakım: KAPALI",
    "mode_switched_browse":"📁 İçerik Gezgini moduna geçildi.",
    "mode_switched_chat":"🤖 AI Sohbet moduna geçildi. Mesajınızı yazın:",
    "ai_off":"🤖 Yapay zeka şu an kapalı.",
    "ai_unavail":"⚠️ Yapay zeka aktif değil.",
    "ai_error":"🤖 Şu an yanıt veremiyorum, lütfen sonra deneyin.",
    "admin_fwd":"📨 Talebiniz yöneticiye iletildi. En kısa sürede yanıt verilecek.",
    "ai_clear":"🗑 Sohbet geçmişi temizlendi.",
    "mgmt_panel":"👥 Yönetim Paneli","stats":"📊 İstatistik","users":"👥 Kullanıcılar",
    "add_admin":"👤 Admin Ekle","del_admin":"🚫 Admin Çıkar",
    "dm_user":"💬 Kullanıcıya Mesaj","broadcast":"📢 Herkese Duyuru",
    "stats_title":"📊 İSTATİSTİKLER",
    "user_list":"👥 Kullanıcı Listesi — birini seçin:",
    "no_users":"Henüz kullanıcı yok.","no_admins":"Eklenmiş admin yok.",
    "admin_enter_id":"Admin eklenecek kullanıcının ID'sini yazın:",
    "admin_added":"✅ Admin eklendi: {}","admin_exists":"❌ Zaten admin.",
    "invalid_id":"❌ Geçersiz ID.","del_admin_lbl":"Çıkarılacak admini seçin:",
    "admin_removed":"✅ Admin çıkarıldı: {}",
    "dm_select":"💬 Mesaj göndermek istediğin kullanıcıyı seç:",
    "dm_manual":"✏️ ID ile yaz","dm_enter_id":"Kullanıcı ID'sini yaz:",
    "dm_enter_msg":"💬 {} kişisine gönderilecek mesajı yaz:",
    "dm_sent":"✅ Mesaj gönderildi → {}","dm_fail":"❌ Gönderilemedi: {}",
    "dm_no_target":"❌ Hedef kullanıcı bulunamadı.",
    "broadcast_enter":"📢 Tüm kullanıcılara gönderilecek mesajı yaz:\n\n💡 Metin, foto, video veya dosya gönderebilirsin.",
    "broadcast_done":"📢 Duyuru tamamlandı!\n✅ Gönderildi: {}\n❌ Başarısız: {}",
    "admin_notif":"🔔 YENİ KULLANICI TALEBİ\n\n👤 {name}{un}\n🆔 {uid}\n📋 Talep: {summary}\n🕐 {time}",
    "reply_btn":"💬 Yanıtla (ID: {})","dm_prefix":"📩 Yönetici mesajı:\n\n{}",
    "content_mgmt":"📁 İçerik Yönetimi","add_folder":"➕ Klasör Ekle",
    "del_folder":"🗑 Klasör Sil","edit_folder":"✏️ Klasör Düzenle",
    "edit_file":"✏️ Dosya Düzenle","add_file":"📎 Dosya/Medya Ekle",
    "del_file":"🗑 Dosya Sil",
    "enter_folder_name":"📁 Yeni klasör adını yazın:",
    "no_folders":"Klasör yok.","no_files":"Dosya yok.",
    "del_folder_select":"Silinecek klasörü seçin:",
    "edit_folder_select":"Düzenlenecek klasörü seçin:",
    "add_file_prompt":"📎 Dosya, resim, video gönderin — veya link/metin yazın:",
    "del_file_select":"Silinecek dosyayı seçin:",
    "edit_file_select":"Düzenlenecek dosyayı seçin:",
    "folder_exists":"❌ '{}' zaten var!","folder_empty":"❌ Ad boş olamaz!",
    "folder_added":"✅ '{}' klasörü eklendi.","folder_deleted":"✅ '{}' silindi.",
    "folder_renamed":"✅ '{}' → '{}'","new_folder_name":"'{}' için yeni ad yazın:",
    "file_added":"✅ Eklendi: {}","file_deleted":"✅ '{}' silindi.",
    "file_renamed":"✅ Yeni ad: '{}'","new_file_name":"Yeni dosya adını yazın:",
    "unsupported":"❓ Desteklenmeyen tür.","send_fail":"❌ Gönderilemedi: {}",
    "file_notfound":"Dosya bulunamadı.",
    "media_sent":"✅ {}/{} medya gönderildi.",
    "send_media_btn":"🖼 Medyaları Gönder ({})","block_btn":"🚫 Engelle",
    "unblock_btn":"✅ Engeli Kaldır","msg_btn":"💬 Mesaj Gönder",
    "blocked_ok":"✅ {} engellendi.","unblocked_ok":"✅ Engel kaldırıldı: {}",
    "settings_title":"⚙️ BOT AYARLARI","set_name_btn":"📝 Bot Adı",
    "set_welcome_btn":"💬 Karşılama","set_photo_btn":"🖼 Bot Fotoğrafı",
    "set_ai_btn":"🤖 Yapay Zeka Aç/Kapat","set_blocked_btn":"🚫 Engellenenler",
    "set_name_prompt":"Yeni bot adını yazın (mevcut: {}):",
    "set_welcome_prompt":"Yeni karşılama mesajını yazın:",
    "set_photo_prompt":"Yeni bot fotoğrafını gönderin:",
    "set_photo_ok":"✅ Bot fotoğrafı güncellendi.",
    "set_photo_fail":"❌ Lütfen bir fotoğraf gönderin.",
    "set_name_ok":"✅ Bot adı: '{}'","set_welcome_ok":"✅ Karşılama mesajı güncellendi.",
    "ai_toggle_on":"🤖 Yapay Zeka: ✅ AÇIK","ai_toggle_off":"🤖 Yapay Zeka: ❌ KAPALI",
    "blocked_list":"🚫 Engellenenler ({})","no_blocked":"Kimse engellenmedi.",
    "maint_toggle":"Bakım Modu: {}","maint_on_str":"AÇIK 🔧","maint_off_str":"KAPALI ✅",
    "user_last":"🕐 Son:","user_msgs":"💬 Mesaj: {} | 📎 Medya: {}",
    "search_prompt":"🔍 Arama terimini girin:",
    "search_results":"🔍 Arama Sonuçları: '{}'",
    "search_no_results":"❌ '{}' için sonuç bulunamadı.",
    "my_stats":"📊 Senin İstatistiklerin",
}

AR = {
    "btn_menu":"📋 القائمة","btn_mgmt":"👥 الإدارة","btn_content":"📁 المحتوى",
    "btn_settings":"⚙️ الإعدادات","btn_maint":"🔧 الصيانة","btn_chat":"🤖 محادثة AI",
    "home":"🏠 الصفحة الرئيسية","folder_list":"📁 المجلدات:","file_list":"📎 الملفات:",
    "empty":"📭 لا يوجد محتوى بعد","back":"◀️ رجوع",
    "cancel":"❌ إلغاء","close":"◀️ إغلاق",
    "maint_on":"🔧 الصيانة: مفعّلة","maint_off":"✅ الصيانة: معطّلة",
    "mode_switched_browse":"📁 تم التبديل إلى وضع تصفح المحتوى.",
    "mode_switched_chat":"🤖 تم التبديل إلى وضع المحادثة. اكتب رسالتك:",
    "ai_off":"🤖 الذكاء الاصطناعي غير متاح حالياً.",
    "ai_unavail":"⚠️ الذكاء الاصطناعي غير مفعّل.",
    "ai_error":"🤖 لا أستطيع الرد الآن، يرجى المحاولة لاحقاً.",
    "admin_fwd":"📨 تم إرسال طلبك إلى المسؤول. سيتم الرد في أقرب وقت.",
    "ai_clear":"🗑 تم مسح سجل المحادثة.",
    "mgmt_panel":"👥 لوحة الإدارة","stats":"📊 الإحصائيات","users":"👥 المستخدمون",
    "add_admin":"👤 إضافة مشرف","del_admin":"🚫 إزالة مشرف",
    "dm_user":"💬 رسالة لمستخدم","broadcast":"📢 رسالة للجميع",
    "stats_title":"📊 الإحصائيات",
    "user_list":"👥 قائمة المستخدمين — اختر واحداً:",
    "no_users":"لا يوجد مستخدمون بعد.","no_admins":"لا يوجد مشرفون مضافون.",
    "admin_enter_id":"اكتب ID المستخدم لإضافته مشرفاً:",
    "admin_added":"✅ تمت إضافة المشرف: {}","admin_exists":"❌ هو مشرف بالفعل.",
    "invalid_id":"❌ ID غير صالح.","del_admin_lbl":"اختر المشرف للإزالة:",
    "admin_removed":"✅ تمت إزالة المشرف: {}",
    "dm_select":"💬 اختر المستخدم الذي تريد مراسلته:",
    "dm_manual":"✏️ أدخل ID يدوياً","dm_enter_id":"اكتب ID المستخدم:",
    "dm_enter_msg":"💬 اكتب الرسالة التي ستُرسل إلى {}:",
    "dm_sent":"✅ تم إرسال الرسالة → {}","dm_fail":"❌ فشل الإرسال: {}",
    "dm_no_target":"❌ لم يتم العثور على المستخدم.",
    "broadcast_enter":"📢 اكتب الرسالة التي ستُرسل لجميع المستخدمين:\n\n💡 يمكنك إرسال نص أو صورة أو فيديو أو ملف.",
    "broadcast_done":"📢 اكتمل الإرسال!\n✅ نجح: {}\n❌ فشل: {}",
    "admin_notif":"🔔 طلب مستخدم جديد\n\n👤 {name}{un}\n🆔 {uid}\n📋 الطلب: {summary}\n🕐 {time}",
    "reply_btn":"💬 رد (ID: {})","dm_prefix":"📩 رسالة من المسؤول:\n\n{}",
    "content_mgmt":"📁 إدارة المحتوى","add_folder":"➕ إضافة مجلد",
    "del_folder":"🗑 حذف مجلد","edit_folder":"✏️ تعديل مجلد",
    "edit_file":"✏️ تعديل ملف","add_file":"📎 إضافة ملف/وسائط",
    "del_file":"🗑 حذف ملف",
    "enter_folder_name":"📁 اكتب اسم المجلد الجديد:",
    "no_folders":"لا توجد مجلدات.","no_files":"لا توجد ملفات.",
    "del_folder_select":"اختر المجلد للحذف:",
    "edit_folder_select":"اختر المجلد للتعديل:",
    "add_file_prompt":"📎 أرسل ملفاً أو صورة أو فيديو — أو اكتب رابطاً/نصاً:",
    "del_file_select":"اختر الملف للحذف:",
    "edit_file_select":"اختر الملف للتعديل:",
    "folder_exists":"❌ '{}' موجود بالفعل!","folder_empty":"❌ لا يمكن أن يكون الاسم فارغاً!",
    "folder_added":"✅ تمت إضافة المجلد '{}'.","folder_deleted":"✅ تم حذف '{}'.",
    "folder_renamed":"✅ '{}' → '{}'","new_folder_name":"اكتب الاسم الجديد لـ '{}':",
    "file_added":"✅ تمت الإضافة: {}","file_deleted":"✅ تم حذف '{}'.",
    "file_renamed":"✅ الاسم الجديد: '{}'","new_file_name":"اكتب الاسم الجديد للملف:",
    "unsupported":"❓ نوع غير مدعوم.","send_fail":"❌ فشل الإرسال: {}",
    "file_notfound":"الملف غير موجود.",
    "media_sent":"✅ تم إرسال {}/{} وسائط.",
    "send_media_btn":"🖼 إرسال الوسائط ({})","block_btn":"🚫 حظر",
    "unblock_btn":"✅ إلغاء الحظر","msg_btn":"💬 إرسال رسالة",
    "blocked_ok":"✅ تم حظر {}.","unblocked_ok":"✅ تم إلغاء حظر: {}",
    "settings_title":"⚙️ إعدادات البوت","set_name_btn":"📝 اسم البوت",
    "set_welcome_btn":"💬 رسالة الترحيب","set_photo_btn":"🖼 صورة البوت",
    "set_ai_btn":"🤖 تشغيل/إيقاف AI","set_blocked_btn":"🚫 المحظورون",
    "set_name_prompt":"اكتب الاسم الجديد للبوت (الحالي: {}):",
    "set_welcome_prompt":"اكتب رسالة الترحيب الجديدة:",
    "set_photo_prompt":"أرسل الصورة الجديدة للبوت:",
    "set_photo_ok":"✅ تم تحديث صورة البوت.",
    "set_photo_fail":"❌ يرجى إرسال صورة.",
    "set_name_ok":"✅ اسم البوت: '{}'","set_welcome_ok":"✅ تم تحديث رسالة الترحيب.",
    "ai_toggle_on":"🤖 الذكاء الاصطناعي: ✅ مفعّل",
    "ai_toggle_off":"🤖 الذكاء الاصطناعي: ❌ معطّل",
    "blocked_list":"🚫 المحظورون ({})","no_blocked":"لا أحد محظور.",
    "maint_toggle":"وضع الصيانة: {}","maint_on_str":"مفعّل 🔧","maint_off_str":"معطّل ✅",
    "user_last":"🕐 آخر ظهور:","user_msgs":"💬 الرسائل: {} | 📎 الوسائط: {}",
    "search_prompt":"🔍 اكتب كلمة البحث:",
    "search_results":"🔍 نتائج البحث: '{}'",
    "search_no_results":"❌ لا توجد نتائج لـ '{}'.",
    "my_stats":"📊 إحصائياتي",
}

# ═══════════════════════════════════════════════════════
#  رسالة الترحيب الافتراضية (مهندسين المستقبل)
# ═══════════════════════════════════════════════════════
DEFAULT_WELCOME_AR = (
    "🎓 أهلاً وسهلاً بك في بوت مهندسي المستقبل! 🚀\n\n"
    "مرحباً بك في مجتمعنا الهندسي المتميّز.\n"
    "هذا البوت هو رفيقك الدراسي على طريق التفوّق —\n"
    "هنا ستجد كل ما تحتاجه:\n\n"
    "📁 ملفات المواد والمحاضرات\n"
    "🖼 الصور والمخططات الهندسية\n"
    "📚 المراجع والكتب التقنية\n"
    "🤖 مساعد ذكاء اصطناعي لمساعدتك في أسئلتك\n\n"
    "تذكّر: كل خطوة نحو العلم هي خطوة نحو المستقبل.\n"
    "‹‹ وَقُل رَّبِّ زِدْنِي عِلْمًا ›› 📖\n\n"
    "استخدم القائمة أدناه للبدء 👇"
)

def is_main_admin(uid): return int(uid) == ADMIN_ID

def L(uid, key, *args):
    lang = TR if is_main_admin(uid) else AR
    val  = lang.get(key, TR.get(key, key))
    return val.format(*args) if args else val

# ═══════════════════════════════════════════════════════
#  STATES
# ═══════════════════════════════════════════════════════
(WAIT_FOLDER, WAIT_DEL_FOLDER, WAIT_FILE, WAIT_DEL_FILE,
 WAIT_ADMIN_ID, WAIT_RENAME_FOLDER, WAIT_RENAME_FILE,
 WAIT_BOT_NAME, WAIT_WELCOME, WAIT_PHOTO,
 WAIT_DM_USER_ID, WAIT_DM_MSG, WAIT_BROADCAST_MSG,
 WAIT_SEARCH) = range(14)

# Tüm klavye buton metinleri
ALL_BTNS = {
    TR["btn_menu"], AR["btn_menu"],
    TR["btn_mgmt"], AR["btn_mgmt"],
    TR["btn_content"], AR["btn_content"],
    TR["btn_settings"],
    TR["btn_maint"], AR["btn_maint"],
    TR["btn_chat"], AR["btn_chat"],
}

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

def load_content():     return load_json(DATA_FILE,       {"folders": {}, "files": []})
def save_content(d):    save_json(DATA_FILE, d)
def load_users():       return load_json(USERS_FILE,      {})
def save_users(d):      save_json(USERS_FILE, d)
def load_messages():    return load_json(MESSAGES_FILE,   {})
def save_messages(d):   save_json(MESSAGES_FILE, d)
def load_admins():      return load_json(ADMINS_FILE,     [])
def save_admins(d):     save_json(ADMINS_FILE, d)
def load_blocked():     return load_json(BLOCKED_FILE,    [])
def save_blocked(d):    save_json(BLOCKED_FILE, d)
def load_ai_history():  return load_json(AI_HISTORY_FILE, {})
def save_ai_history(d): save_json(AI_HISTORY_FILE, d)

def load_settings():
    default = {
        "maintenance": False,
        "maintenance_text_tr": "🔧 Bot güncelleniyor...",
        "maintenance_text_ar": "🔧 البوت قيد التحديث، يرجى المحاولة لاحقاً...",
        "bot_name": "بوت مهندسي المستقبل",
        "welcome_msg": DEFAULT_WELCOME_AR,
        "bot_photo_id": None,
        "ai_enabled": True,
    }
    data = load_json(SETTINGS_FILE, default)
    for k, v in default.items():
        data.setdefault(k, v)
    return data

def save_settings(d): save_json(SETTINGS_FILE, d)

# ═══════════════════════════════════════════════════════
#  YARDIMCILAR
# ═══════════════════════════════════════════════════════

def is_admin(uid):   return int(uid) == ADMIN_ID or int(uid) in [int(x) for x in load_admins()]
def is_blocked(uid): return int(uid) in [int(x) for x in load_blocked()]

def get_user_mode(context): return context.user_data.get("mode", "browse")

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
    if is_admin(user.id): return
    msgs = load_messages()
    uid  = str(user.id)
    entry = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "type": msg_type, "content": str(content)[:300]}
    if file_id: entry["file_id"] = file_id
    msgs.setdefault(uid, []).append(entry)
    msgs[uid] = msgs[uid][-2000:]
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
        return dest
    except Exception as e:
        logger.warning(f"İndirme başarısız ({filename}): {e}")
        return None

# ═══════════════════════════════════════════════════════
#  ARAMA FONKSİYONU
# ═══════════════════════════════════════════════════════

def search_content(query: str, node=None, path=None, results=None):
    """Tüm klasör ve dosyalarda arama yapar — recursive"""
    if node is None:
        node = load_content()
    if path is None:
        path = []
    if results is None:
        results = []

    q = query.lower()

    # Dosyaları tara
    for idx, f in enumerate(node.get("files", [])):
        name = f.get("caption", f.get("name", ""))
        if q in name.lower():
            results.append({"path": path[:], "name": name, "idx": idx, "type": f.get("type","")})

    # Klasörleri tara (recursive)
    for fname, folder in node.get("folders", {}).items():
        if q in fname.lower():
            results.append({"path": path[:], "name": fname, "idx": None, "type": "folder"})
        search_content(query, folder, path + [fname], results)

    return results

# ═══════════════════════════════════════════════════════
#  YAPAY ZEKA — Mühendislik odaklı
# ═══════════════════════════════════════════════════════

ENGINEERING_BOT_CONTEXT_AR = """
أنت مساعد ذكاء اصطناعي متخصص لبوت "مهندسي المستقبل" على تيليغرام.
هذا البوت مخصص لطلاب الهندسة — يحتوي على ملفات المواد الدراسية، المحاضرات، 
المراجع، الصور الهندسية، والموارد التعليمية اللازمة لرحلتهم الأكاديمية.

مهمتك:
- مساعدة الطلاب في أسئلتهم الهندسية والأكاديمية
- شرح المفاهيم الهندسية بأسلوب واضح ومبسط
- تقديم إرشادات دراسية ونصائح للتفوق
- المساعدة في فهم المسائل والمعادلات الرياضية والفيزيائية والهندسية
- الإجابة على أسئلة البرمجة والتقنية
- تحفيز الطلاب وتشجيعهم على الإبداع والابتكار

تحدث دائماً بالعربية. كن ودوداً، علمياً، ودقيقاً في معلوماتك.
إذا سأل المستخدم عن ملف أو محتوى معين في البوت، اقترح عليه استخدام زر القائمة أو /search للبحث.
إذا طلب المستخدم شيئاً لا تستطيع توفيره أو يحتاج تدخل المسؤول (مثل إضافة محتوى جديد، أو شكوى، أو طلب خاص)،
أضف [ADMIN_TALEP] في نهاية ردك مع ملخص قصير للطلب.
لا تضف [ADMIN_TALEP] للأسئلة العلمية والمحادثات العادية.
"""

async def get_ai_response(user_id: str, message: str, lang: str = "ar") -> str:
    import aiohttp
    if not GEMINI_API_KEY:
        return AR["ai_unavail"] if lang == "ar" else TR["ai_unavail"]

    history = load_ai_history()
    uid_history = history.get(user_id, [])

    if lang == "tr":
        sys_prompt = (
            "Sen bu botun yardımcı yapay zeka asistanısın. Türkçe konuş. "
            "Bu bot mühendislik öğrencileri için tasarlanmış — ders dosyaları, "
            "notlar, referanslar ve teknik materyaller içeriyor. "
            "Kullanıcılara mühendislik soruları ve akademik konularda yardımcı ol. "
            "Eğer kullanıcı çok özel, teknik veya acil bir talep yaparsa "
            "(ödeme, özel işlem, şikayet veya bot ile çözülemeyen bir konu), "
            "cevabının sonuna [ADMIN_TALEP] ve talebi kısaca özetle ekle. "
            "Normal sohbet için [ADMIN_TALEP] ekleme."
        )
    else:
        sys_prompt = ENGINEERING_BOT_CONTEXT_AR

    # Gemini formatına çevir
    contents = []
    for h in uid_history[-18:]:
        role = "user" if h["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": h["content"]}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers={"content-type": "application/json"},
                json={
                    "system_instruction": {"parts": [{"text": sys_prompt}]},
                    "contents": contents,
                    "generationConfig": {"maxOutputTokens": 1000, "temperature": 0.7},
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data  = await resp.json()
                reply = data["candidates"][0]["content"]["parts"][0]["text"]

        uid_history.append({"role": "user",      "content": message})
        uid_history.append({"role": "assistant", "content": reply})
        history[user_id] = uid_history[-20:]
        save_ai_history(history)
        return reply
    except Exception as e:
        logger.error(f"Gemini hata: {e}")
        return AR["ai_error"] if lang == "ar" else TR["ai_error"]

async def notify_admin_request(context, user, summary: str):
    users = load_users()
    u    = users.get(str(user.id), {})
    name = u.get("full_name") or u.get("first_name") or f"ID:{user.id}"
    un   = f" @{u['username']}" if u.get("username") else ""
    text = TR["admin_notif"].format(
        name=name, un=un, uid=user.id,
        summary=summary, time=datetime.now().strftime("%Y-%m-%d %H:%M"))
    kb = [[InlineKeyboardButton(TR["reply_btn"].format(user.id), callback_data=f"dm_quick|{user.id}")]]
    try:
        await context.bot.send_message(ADMIN_ID, text, reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e:
        logger.error(f"Admin bildirim hatası: {e}")

async def handle_ai_message(msg, context, uid: str, text: str):
    """AI mesajını işle ve yanıtla"""
    s = load_settings()
    if not s.get("ai_enabled", True):
        await msg.reply_text(L(uid, "ai_off"))
        return
    await context.bot.send_chat_action(msg.chat_id, "typing")
    lang     = "tr" if is_main_admin(uid) else "ar"
    ai_reply = await get_ai_response(uid, text, lang)
    if "[ADMIN_TALEP]" in ai_reply:
        parts   = ai_reply.split("[ADMIN_TALEP]", 1)
        clean   = parts[0].strip()
        summary = parts[1].strip() if len(parts) > 1 else text
        if clean:
            await msg.reply_text(clean)
        await msg.reply_text(L(uid, "admin_fwd"))
        await notify_admin_request(context, msg.from_user if hasattr(msg, "from_user") else context.user_data.get("_user"), summary or text)
    else:
        await msg.reply_text(ai_reply)

# ═══════════════════════════════════════════════════════
#  KLAVYE
# ═══════════════════════════════════════════════════════

def reply_kb(uid):
    uid = str(uid)
    if is_main_admin(uid):
        return ReplyKeyboardMarkup([
            [KeyboardButton(TR["btn_mgmt"]),    KeyboardButton(TR["btn_content"])],
            [KeyboardButton(TR["btn_settings"]),KeyboardButton(TR["btn_maint"])],
            [KeyboardButton(TR["btn_chat"])],
        ], resize_keyboard=True)
    elif is_admin(uid):
        return ReplyKeyboardMarkup([
            [KeyboardButton(AR["btn_content"]), KeyboardButton(AR["btn_maint"])],
            [KeyboardButton(AR["btn_chat"])],
        ], resize_keyboard=True)
    else:
        # مستخدمون: القائمة + محادثة AI + بحث
        return ReplyKeyboardMarkup([
            [KeyboardButton(AR["btn_menu"]), KeyboardButton(AR["btn_chat"])],
        ], resize_keyboard=True)

def folder_text(folder, path, uid):
    uid = str(uid)
    header = "📂 " + " › ".join(path) if path else L(uid, "home")
    lines  = [header, "─" * 20]
    folds  = folder.get("folders", {})
    files  = folder.get("files",   [])
    if folds:
        lines.append(L(uid, "folder_list"))
        for f in folds: lines.append(f"  • {f}")
    if files:
        lines.append(L(uid, "file_list"))
        for f in files: lines.append(f"  • {f.get('caption', f.get('name', '?'))}")
    if not folds and not files:
        lines.append(L(uid, "empty"))
    if is_admin(uid):
        s = load_settings()
        lines.append("─" * 20)
        lines.append(L(uid, "maint_on") if s["maintenance"] else L(uid, "maint_off"))
    return "\n".join(lines)

def folder_kb(path, folder, uid):
    uid = str(uid)
    kb  = []
    for name in list(folder.get("folders", {}).keys())[:8]:
        kb.append([InlineKeyboardButton(f"📁 {name}", callback_data=f"open|{name}")])
    for idx, f in enumerate(folder.get("files", [])[:12]):
        cap = f.get("caption", f.get("name", "?"))
        kb.append([InlineKeyboardButton(f"📎 {cap}", callback_data=f"getfile|{idx}")])
    nav = []
    if path:
        nav.append(InlineKeyboardButton(L(uid, "back"), callback_data="nav|back"))
    # ✅ home_btn KALDIRILDI — sadece "Geri/رجوع" butonu var
    if nav: kb.append(nav)
    return InlineKeyboardMarkup(kb)

async def show_folder(query, context, path, note=""):
    content = load_content()
    folder  = get_folder(content, path)
    uid     = str(query.from_user.id)
    text    = folder_text(folder, path, uid)
    if note: text += f"\n\n{note}"
    try:
        await query.edit_message_text(text, reply_markup=folder_kb(path, folder, uid))
    except Exception:
        pass

async def show_folder_new(message, uid, path=None):
    path    = path or []
    content = load_content()
    folder  = get_folder(content, path)
    uid     = str(uid)
    await message.reply_text(
        folder_text(folder, path, uid),
        reply_markup=folder_kb(path, folder, uid))

async def _delete_last_inline(context, chat_id):
    msg_id = context.user_data.get("last_inline_msg")
    if msg_id:
        try: await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except: pass
        context.user_data.pop("last_inline_msg", None)

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
    context.user_data["mode"] = "browse"

    if is_blocked(uid) and not is_admin(uid): return

    await update.message.reply_text(
        "👋" if not is_admin(uid) else "✅",
        reply_markup=reply_kb(uid))

    if not is_admin(uid):
        if s["maintenance"]:
            await update.message.reply_text(s.get("maintenance_text_ar", "🔧 البوت قيد التحديث..."))
            return
        if s.get("bot_photo_id"):
            await update.message.reply_photo(s["bot_photo_id"], caption=s.get("welcome_msg") or None)
        elif s.get("welcome_msg"):
            await update.message.reply_text(s["welcome_msg"])

    await show_folder_new(update.message, uid)

# ═══════════════════════════════════════════════════════
#  /help — Kullanım kılavuzu
# ═══════════════════════════════════════════════════════

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = str(user.id)
    register_user(user)

    if is_main_admin(uid):
        text = (
            "📖 *دليل استخدام البوت — المسؤول*\n\n"
            "👥 *الإدارة:* إدارة المستخدمين والمشرفين\n"
            "📁 *المحتوى:* إضافة/حذف المجلدات والملفات\n"
            "⚙️ *الإعدادات:* اسم البوت، رسالة الترحيب، الصورة\n"
            "🔧 *الصيانة:* تفعيل/تعطيل وضع الصيانة\n"
            "🤖 *محادثة AI:* التحدث مع الذكاء الاصطناعي\n\n"
            "الأوامر:\n"
            "/start — إعادة التشغيل\n"
            "/help — هذه الرسالة\n"
            "/search — البحث في المحتوى\n"
            "/stats — الإحصائيات"
        )
    else:
        text = (
            "📖 *كيفية استخدام بوت مهندسي المستقبل*\n\n"
            "📋 *القائمة* — تصفح الملفات والمجلدات\n"
            "🤖 *محادثة AI* — اسأل مساعد الذكاء الاصطناعي\n\n"
            "الأوامر المتاحة:\n"
            "/start — بداية جديدة\n"
            "/help — هذه الرسالة\n"
            "/search — ابحث عن ملف أو مجلد\n"
            "/mystats — إحصائياتي\n\n"
            "💡 *نصيحة:* استخدم زر *محادثة AI* لأي سؤال هندسي أو دراسي!\n"
            "إذا لم تجد ما تبحث عنه، اكتب للمساعد وسيحوّل طلبك للمسؤول."
        )
    await update.message.reply_text(text, parse_mode="Markdown")

# ═══════════════════════════════════════════════════════
#  /search — Dosya/Klasör Arama
# ═══════════════════════════════════════════════════════

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = str(user.id)
    register_user(user)

    # Argüman varsa direkt ara
    args = context.args
    if args:
        query = " ".join(args)
        await _do_search(update.message, uid, query)
    else:
        await update.message.reply_text(
            L(uid, "search_prompt"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(L(uid, "cancel"), callback_data="close")
            ]])
        )
        context.user_data["action"] = "search"
        return WAIT_SEARCH

async def _do_search(message, uid, query):
    results = search_content(query)
    if not results:
        await message.reply_text(L(uid, "search_no_results").format(query))
        return

    lines = [L(uid, "search_results").format(query), ""]
    kb = []
    for r in results[:10]:
        path_str = " › ".join(r["path"]) if r["path"] else "🏠"
        icon = "📁" if r["type"] == "folder" else "📎"
        lines.append(f"{icon} {r['name']}\n   📍 {path_str}")
        if r["type"] != "folder" and r["idx"] is not None:
            kb.append([InlineKeyboardButton(
                f"{icon} {r['name'][:40]}",
                callback_data=f"search_open|{'|'.join(r['path'])}|{r['idx']}"
            )])

    await message.reply_text("\n".join(lines)[:3000])
    if kb:
        kb.append([InlineKeyboardButton("◀️", callback_data="close")])
        await message.reply_text("👆 اختر للفتح:", reply_markup=InlineKeyboardMarkup(kb))

# ═══════════════════════════════════════════════════════
#  /mystats — Kullanıcı kendi istatistikleri
# ═══════════════════════════════════════════════════════

async def mystats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = str(user.id)
    register_user(user)

    msgs  = load_messages().get(uid, [])
    texts = [m for m in msgs if m.get("type") in ("msg", "text", "command")]
    media = [m for m in msgs if m.get("file_id")]
    views = [m for m in msgs if m.get("type") == "file_view"]
    users = load_users()
    u     = users.get(uid, {})

    name = u.get("full_name") or u.get("first_name") or f"ID:{uid}"
    text = (
        f"📊 *{L(uid,'my_stats')}*\n\n"
        f"👤 {name}\n"
        f"🆔 {uid}\n"
        f"🕐 آخر ظهور: {u.get('last_seen', '—')}\n\n"
        f"💬 الرسائل المكتوبة: {len(texts)}\n"
        f"📎 الوسائط المرسلة: {len(media)}\n"
        f"👁 الملفات المفتوحة: {len(views)}\n"
        f"📨 إجمالي التفاعلات: {len(msgs)}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ═══════════════════════════════════════════════════════
#  REPLY KEYBOARD BUTONLARI
# ═══════════════════════════════════════════════════════

async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = str(user.id)
    text = (update.message.text or "").strip()
    register_user(user)
    await _delete_last_inline(context, update.effective_chat.id)

    # ── Kullanıcı/Admin: Menü ────────────────────────
    if text in (TR["btn_menu"], AR["btn_menu"]):
        context.user_data["path"] = []
        context.user_data["mode"] = "browse"
        s = load_settings()
        if s["maintenance"] and not is_admin(uid):
            await update.message.reply_text(s.get("maintenance_text_ar", "🔧"))
            return
        await show_folder_new(update.message, uid)
        return

    # ── Herkes: AI Sohbet Butonu ──────────────────────
    if text in (TR["btn_chat"], AR["btn_chat"]):
        context.user_data["mode"] = "chat"
        await update.message.reply_text(L(uid, "mode_switched_chat"))
        return

    if not is_admin(uid): return

    # ── Tüm Adminler: İçerik ──────────────────────────
    if text in (TR["btn_content"], AR["btn_content"]):
        kb = [
            [InlineKeyboardButton(L(uid,"add_folder"), callback_data="cnt|add_folder"),
             InlineKeyboardButton(L(uid,"del_folder"),  callback_data="cnt|del_folder")],
            [InlineKeyboardButton(L(uid,"edit_folder"), callback_data="cnt|edit_folder"),
             InlineKeyboardButton(L(uid,"edit_file"),   callback_data="cnt|edit_file")],
            [InlineKeyboardButton(L(uid,"add_file"),    callback_data="cnt|add_file"),
             InlineKeyboardButton(L(uid,"del_file"),    callback_data="cnt|del_file")],
        ]
        sent = await update.message.reply_text(L(uid,"content_mgmt"), reply_markup=InlineKeyboardMarkup(kb))
        context.user_data["last_inline_msg"] = sent.message_id
        return

    # ── Tüm Adminler: Bakım ───────────────────────────
    if text in (TR["btn_maint"], AR["btn_maint"]):
        s = load_settings()
        s["maintenance"] = not s["maintenance"]
        save_settings(s)
        durum = L(uid,"maint_on_str") if s["maintenance"] else L(uid,"maint_off_str")
        await update.message.reply_text(L(uid,"maint_toggle").format(durum))
        return

    # ── Sadece Süper Admin ────────────────────────────
    if not is_main_admin(uid): return

    if text == TR["btn_mgmt"]:
        kb = [
            [InlineKeyboardButton(L(uid,"stats"), callback_data="mgmt|stats"),
             InlineKeyboardButton(L(uid,"users"), callback_data="mgmt|users")],
            [InlineKeyboardButton(L(uid,"add_admin"), callback_data="mgmt|add_admin"),
             InlineKeyboardButton(L(uid,"del_admin"), callback_data="mgmt|del_admin")],
            [InlineKeyboardButton(L(uid,"dm_user"),   callback_data="mgmt|dm_user"),
             InlineKeyboardButton(L(uid,"broadcast"), callback_data="mgmt|broadcast")],
        ]
        sent = await update.message.reply_text(L(uid,"mgmt_panel"), reply_markup=InlineKeyboardMarkup(kb))
        context.user_data["last_inline_msg"] = sent.message_id
        return

    if text == TR["btn_settings"]:
        s   = load_settings()
        txt = (f"{L(uid,'settings_title')}\n\n"
               f"📝 Ad: {s.get('bot_name','—')}\n"
               f"💬 Karşılama: {s.get('welcome_msg','—')[:50]}\n"
               f"🖼 Fotoğraf: {'✅' if s.get('bot_photo_id') else '❌'}\n"
               f"🤖 Yapay Zeka: {'✅ Açık' if s.get('ai_enabled',True) else '❌ Kapalı'}\n"
               f"🚫 Engellenenler: {len(load_blocked())} kişi")
        kb = [
            [InlineKeyboardButton(L(uid,"set_name_btn"),    callback_data="set|name")],
            [InlineKeyboardButton(L(uid,"set_welcome_btn"), callback_data="set|welcome")],
            [InlineKeyboardButton(L(uid,"set_photo_btn"),   callback_data="set|photo")],
            [InlineKeyboardButton(L(uid,"set_ai_btn"),      callback_data="set|toggle_ai")],
            [InlineKeyboardButton(L(uid,"set_blocked_btn"), callback_data="set|blocked")],
        ]
        sent = await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        context.user_data["last_inline_msg"] = sent.message_id
        return

# ═══════════════════════════════════════════════════════
#  CALLBACK
# ═══════════════════════════════════════════════════════

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user  = query.from_user
    uid   = str(user.id)
    adm   = is_admin(uid)
    cb    = query.data

    if is_blocked(uid) and not adm: return ConversationHandler.END
    if not adm:
        s = load_settings()
        if s["maintenance"]:
            await query.answer(s.get("maintenance_text_ar","🔧"), show_alert=True)
            return ConversationHandler.END

    content = load_content()
    path    = context.user_data.get("path", [])

    # ── Arama Sonucu Dosya Aç ────────────────────────
    if cb.startswith("search_open|"):
        parts = cb.split("|")
        # format: search_open|path1|path2|...|idx
        idx = int(parts[-1])
        file_path = parts[1:-1]
        folder = get_folder(content, file_path)
        files  = folder.get("files", [])
        if idx >= len(files):
            await query.answer(L(uid,"file_notfound"), show_alert=True)
            return ConversationHandler.END
        f     = files[idx]
        ftype = f.get("type",""); fid = f.get("file_id","")
        cap   = f.get("caption",""); url = f.get("url","")
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
            else: await query.message.reply_text(L(uid,"unsupported"))
        except Exception as e:
            await query.message.reply_text(L(uid,"send_fail").format(e))
        return ConversationHandler.END

    # ── Dosya Aç ─────────────────────────────────────
    if cb.startswith("getfile|"):
        idx    = int(cb.split("|")[1])
        folder = get_folder(content, path)
        files  = folder.get("files", [])
        if idx >= len(files):
            await query.answer(L(uid,"file_notfound"), show_alert=True)
            return ConversationHandler.END
        f     = files[idx]
        ftype = f.get("type",""); fid = f.get("file_id","")
        cap   = f.get("caption",""); url = f.get("url","")
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
            else: await query.message.reply_text(L(uid,"unsupported"))
        except Exception as e:
            await query.message.reply_text(L(uid,"send_fail").format(e))
        return ConversationHandler.END

    # ── Navigasyon ────────────────────────────────────
    if cb.startswith("nav|"):
        action = cb.split("|")[1]
        if action == "back" and path: path.pop()
        elif action == "root": path = []
        context.user_data["path"] = path
        await show_folder(query, context, path)
        return ConversationHandler.END

    if cb.startswith("open|"):
        path.append(cb.split("|",1)[1])
        context.user_data["path"] = path
        await show_folder(query, context, path)
        return ConversationHandler.END

    # ── Yönetim (sadece süper admin) ──────────────────
    if cb.startswith("mgmt|") and is_main_admin(uid):
        action = cb.split("|")[1]

        if action == "stats":
            u_d = load_users(); m_d = load_messages(); s = load_settings()
            total = sum(len(v) for v in m_d.values())
            def _cnt(node):
                c = 0
                for f in node.get("folders",{}).values(): c += 1 + _cnt(f)
                return c
            txt = (f"{L(uid,'stats_title')}\n\n"
                   f"👥 Kullanıcı: {len(u_d)}\n💬 Toplam mesaj: {total}\n"
                   f"📁 Klasör: {_cnt(content)}\n📎 Dosya: {len(content.get('files',[]))}\n"
                   f"🔧 Bakım: {'Açık' if s['maintenance'] else 'Kapalı'}\n"
                   f"🤖 Yapay Zeka: {'Açık' if s.get('ai_enabled',True) else 'Kapalı'}")
            await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(L(uid,"close"), callback_data="close")]]))
            return ConversationHandler.END

        if action == "users":
            u_d = load_users()
            if not u_d:
                await query.answer(L(uid,"no_users"), show_alert=True)
                return ConversationHandler.END
            kb = []
            for uid_, u in list(u_d.items())[-50:]:
                if int(uid_) == ADMIN_ID: continue
                name = u.get("full_name") or u.get("first_name") or f"ID:{uid_}"
                un   = f" @{u['username']}" if u.get("username") else ""
                kb.append([InlineKeyboardButton(f"👤 {name}{un}", callback_data=f"user|info|{uid_}")])
            kb.append([InlineKeyboardButton(L(uid,"close"), callback_data="close")])
            await query.edit_message_text(L(uid,"user_list"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "add_admin":
            context.user_data["action"] = "admin_add"
            await query.edit_message_text(L(uid,"admin_enter_id"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="close")]]))
            return WAIT_ADMIN_ID

        if action == "del_admin":
            admins = load_admins()
            if not admins:
                await query.answer(L(uid,"no_admins"), show_alert=True)
                return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🚫 {a}", callback_data=f"rem_admin|{a}")] for a in admins]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="close")])
            await query.edit_message_text(L(uid,"del_admin_lbl"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "dm_user":
            u_d = load_users(); kb = []
            for uid_, u in list(u_d.items())[-30:]:
                if int(uid_) == ADMIN_ID: continue
                name = u.get("full_name") or u.get("first_name") or f"ID:{uid_}"
                un   = f" @{u['username']}" if u.get("username") else ""
                kb.append([InlineKeyboardButton(f"👤 {name}{un}", callback_data=f"dm_pick|{uid_}")])
            kb.append([InlineKeyboardButton(L(uid,"dm_manual"), callback_data="dm_pick|manual")])
            kb.append([InlineKeyboardButton(L(uid,"cancel"),    callback_data="close")])
            await query.edit_message_text(L(uid,"dm_select"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "broadcast":
            context.user_data["action"] = "broadcast"
            await query.edit_message_text(L(uid,"broadcast_enter"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="close")]]))
            return WAIT_BROADCAST_MSG

    if cb.startswith("dm_pick|") and is_main_admin(uid):
        target = cb.split("|")[1]
        if target == "manual":
            context.user_data["action"] = "dm_manual_id"
            await query.edit_message_text(L(uid,"dm_enter_id"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="close")]]))
            return WAIT_DM_USER_ID
        context.user_data["dm_target"] = target; context.user_data["action"] = "dm_msg"
        u = load_users().get(target, {}); name = u.get("full_name") or u.get("first_name") or f"ID:{target}"
        await query.edit_message_text(L(uid,"dm_enter_msg").format(name),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="close")]]))
        return WAIT_DM_MSG

    if cb.startswith("dm_quick|") and is_main_admin(uid):
        target = cb.split("|")[1]
        context.user_data["dm_target"] = target; context.user_data["action"] = "dm_msg"
        await query.edit_message_text(L(uid,"dm_enter_msg").format(target),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="close")]]))
        return WAIT_DM_MSG

    if cb.startswith("rem_admin|") and is_main_admin(uid):
        rem = int(cb.split("|")[1]); admins = load_admins()
        if rem in admins: admins.remove(rem); save_admins(admins)
        await query.edit_message_text(L(uid,"admin_removed").format(rem))
        return ConversationHandler.END

    # ── Kullanıcı Detay ───────────────────────────────
    if cb.startswith("user|") and is_main_admin(uid):
        parts = cb.split("|"); action = parts[1]

        if action == "info":
            target = parts[2]; u_d = load_users(); m_d = load_messages()
            u      = u_d.get(target, {})
            name   = u.get("full_name") or u.get("first_name") or f"ID:{target}"
            un     = f"@{u['username']}" if u.get("username") else "—"
            msgs   = m_d.get(target, [])
            media  = [m for m in msgs if m.get("file_id")]
            texts  = [m for m in msgs if m.get("type") in ("msg","text","command")]
            ICONS  = {"msg":"💬","text":"💬","photo":"🖼","video":"🎥","document":"📄",
                      "audio":"🎵","voice":"🎙","animation":"🎞","sticker":"😊","command":"⚙️","file_view":"👁"}
            lines  = [f"👤 {name} ({un})", f"🆔 {target}",
                      f"{L(uid,'user_last')} {u.get('last_seen','—')}",
                      L(uid,"user_msgs").format(len(texts), len(media)), "─"*22]
            for m in msgs[-15:]:
                lines.append(f"{ICONS.get(m.get('type',''),'📨')} [{m.get('time','')[-8:]}] {m.get('content','')[:50]}")
            kb = []
            if media:
                kb.append([InlineKeyboardButton(L(uid,"send_media_btn").format(len(media)), callback_data=f"user|media|{target}")])
            kb.append([InlineKeyboardButton(L(uid,"msg_btn"), callback_data=f"dm_quick|{target}")])
            if int(target) not in [int(x) for x in load_blocked()]:
                kb.append([InlineKeyboardButton(L(uid,"block_btn"), callback_data=f"user|block|{target}")])
            else:
                kb.append([InlineKeyboardButton(L(uid,"unblock_btn"), callback_data=f"user|unblock|{target}")])
            kb.append([InlineKeyboardButton(L(uid,"back"), callback_data="mgmt|users")])
            await query.edit_message_text("\n".join(lines)[:4000], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "media":
            target = parts[2]; m_d = load_messages()
            media  = [m for m in m_d.get(target,[]) if m.get("file_id")]
            if not media:
                await query.answer(L(uid,"file_notfound"), show_alert=True)
                return ConversationHandler.END
            ICONS = {"photo":"🖼","video":"🎥","document":"📄","audio":"🎵","voice":"🎙","animation":"🎞","sticker":"😊"}
            sent  = 0
            for m in media[-30:]:
                fid = m["file_id"]; ftype = m.get("type","")
                cap = f"{ICONS.get(ftype,'📎')} [{m.get('time','')}]\n{m.get('content','')}]"[:200]
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
                    logger.warning(f"Medya: {e}")
            await query.message.reply_text(L(uid,"media_sent").format(sent, len(media[-30:])))
            return ConversationHandler.END

        if action == "block":
            target = parts[2]; blocked = load_blocked()
            if int(target) not in blocked: blocked.append(int(target)); save_blocked(blocked)
            await query.answer(L(uid,"blocked_ok").format(target), show_alert=True)
            query.data = f"user|info|{target}"; return await callback(update, context)

        if action == "unblock":
            target = parts[2]; blocked = load_blocked()
            if int(target) in blocked: blocked.remove(int(target)); save_blocked(blocked)
            await query.answer(L(uid,"unblocked_ok").format(target), show_alert=True)
            query.data = f"user|info|{target}"; return await callback(update, context)

    # ── İçerik (tüm adminler) ─────────────────────────
    if cb.startswith("cnt|") and adm:
        action = cb.split("|")[1]; folder = get_folder(content, path)

        if action == "add_folder":
            context.user_data["action"] = "add_folder"
            await query.edit_message_text(L(uid,"enter_folder_name"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")]]))
            return WAIT_FOLDER

        if action == "del_folder":
            folds = list(folder.get("folders",{}).keys())
            if not folds:
                await query.answer(L(uid,"no_folders"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🗑 {f}", callback_data=f"do|del_folder|{f}")] for f in folds]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"del_folder_select"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "edit_folder":
            folds = list(folder.get("folders",{}).keys())
            if not folds:
                await query.answer(L(uid,"no_folders"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"✏️ {f}", callback_data=f"do|pick_folder|{f}")] for f in folds]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"edit_folder_select"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "add_file":
            context.user_data["action"] = "add_file"
            await query.edit_message_text(L(uid,"add_file_prompt"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")]]))
            return WAIT_FILE

        if action == "del_file":
            files = folder.get("files",[])
            if not files:
                await query.answer(L(uid,"no_files"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🗑 {f.get('caption','?')}", callback_data=f"do|del_file|{i}")] for i,f in enumerate(files)]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"del_file_select"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "edit_file":
            files = folder.get("files",[])
            if not files:
                await query.answer(L(uid,"no_files"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"✏️ {f.get('caption','?')}", callback_data=f"do|pick_file|{i}")] for i,f in enumerate(files)]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"edit_file_select"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

    # ── Do ───────────────────────────────────────────
    if cb.startswith("do|") and adm:
        parts = cb.split("|",2); action = parts[1]; arg = parts[2] if len(parts)>2 else ""
        folder = get_folder(content, path)

        if action == "del_folder":
            if arg in folder.get("folders",{}): del folder["folders"][arg]; save_content(content)
            await show_folder(query, context, path, note=L(uid,"folder_deleted").format(arg))
            return ConversationHandler.END

        if action == "pick_folder":
            context.user_data["action"] = "rename_folder"; context.user_data["target"] = arg
            await query.edit_message_text(L(uid,"new_folder_name").format(arg),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")]]))
            return WAIT_RENAME_FOLDER

        if action == "del_file":
            idx = int(arg); files = folder.get("files",[])
            if 0 <= idx < len(files):
                removed = files.pop(idx); save_content(content)
                await show_folder(query, context, path, note=L(uid,"file_deleted").format(removed.get("caption","?")))
            return ConversationHandler.END

        if action == "pick_file":
            context.user_data["action"] = "rename_file"; context.user_data["target"] = int(arg)
            await query.edit_message_text(L(uid,"new_file_name"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")]]))
            return WAIT_RENAME_FILE

    # ── Ayarlar (sadece süper admin) ──────────────────
    if cb.startswith("set|") and is_main_admin(uid):
        action = cb.split("|")[1]

        if action == "name":
            context.user_data["action"] = "set_name"; s = load_settings()
            await query.edit_message_text(L(uid,"set_name_prompt").format(s.get("bot_name","—")),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="close")]]))
            return WAIT_BOT_NAME

        if action == "welcome":
            context.user_data["action"] = "set_welcome"
            await query.edit_message_text(L(uid,"set_welcome_prompt"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="close")]]))
            return WAIT_WELCOME

        if action == "photo":
            context.user_data["action"] = "set_photo"
            await query.edit_message_text(L(uid,"set_photo_prompt"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="close")]]))
            return WAIT_PHOTO

        if action == "toggle_ai":
            s = load_settings(); s["ai_enabled"] = not s.get("ai_enabled",True); save_settings(s)
            await query.edit_message_text(L(uid,"ai_toggle_on") if s["ai_enabled"] else L(uid,"ai_toggle_off"))
            return ConversationHandler.END

        if action == "blocked":
            blocked = load_blocked()
            txt = L(uid,"blocked_list").format(len(blocked)) + "\n\n"
            txt += "\n".join(f"🆔 {b}" for b in blocked) if blocked else L(uid,"no_blocked")
            await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(L(uid,"close"), callback_data="close")]]))
            return ConversationHandler.END

    if cb == "close":
        try: await query.delete_message()
        except: pass
        return ConversationHandler.END

    return ConversationHandler.END

# ═══════════════════════════════════════════════════════
#  METİN GİRİŞİ
# ═══════════════════════════════════════════════════════

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user   = update.effective_user; uid = str(user.id)
    text   = (update.message.text or "").strip()
    register_user(user); log_user_message(user,"msg",text)

    # ── Arama (tüm kullanıcılar) ──────────────────────
    action = context.user_data.get("action","")
    if action == "search":
        context.user_data.pop("action", None)
        await _do_search(update.message, uid, text)
        return ConversationHandler.END

    if not is_admin(uid): return ConversationHandler.END

    content = load_content(); path = context.user_data.get("path",[])
    folder  = get_folder(content,path)

    if action == "admin_add" and is_main_admin(uid):
        try: new_id = int(text)
        except: await update.message.reply_text(L(uid,"invalid_id")); return WAIT_ADMIN_ID
        admins = load_admins()
        if new_id in admins or new_id == ADMIN_ID:
            await update.message.reply_text(L(uid,"admin_exists"))
        else:
            admins.append(new_id); save_admins(admins)
            await update.message.reply_text(L(uid,"admin_added").format(new_id))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "dm_manual_id" and is_main_admin(uid):
        try: target_id = str(int(text))
        except: await update.message.reply_text(L(uid,"invalid_id")); return WAIT_DM_USER_ID
        context.user_data["dm_target"] = target_id; context.user_data["action"] = "dm_msg"
        await update.message.reply_text(L(uid,"dm_enter_msg").format(target_id))
        return WAIT_DM_MSG

    if action == "dm_msg" and is_main_admin(uid):
        target = context.user_data.get("dm_target")
        if not target:
            await update.message.reply_text(L(uid,"dm_no_target")); return ConversationHandler.END
        try:
            await context.bot.send_message(int(target), L(uid,"dm_prefix").format(text))
            await update.message.reply_text(L(uid,"dm_sent").format(target))
        except Exception as e:
            await update.message.reply_text(L(uid,"dm_fail").format(e))
        context.user_data.pop("action",None); context.user_data.pop("dm_target",None)
        return ConversationHandler.END

    if action == "broadcast" and is_main_admin(uid):
        users = load_users(); success = fail = 0
        for uid_,u in users.items():
            if int(uid_) == ADMIN_ID or is_blocked(uid_): continue
            try: await context.bot.send_message(int(uid_), f"📢\n\n{text}"); success += 1
            except: fail += 1
        await update.message.reply_text(L(uid,"broadcast_done").format(success,fail))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "set_name" and is_main_admin(uid):
        if not text: await update.message.reply_text(L(uid,"folder_empty")); return WAIT_BOT_NAME
        s = load_settings(); s["bot_name"] = text; save_settings(s)
        await update.message.reply_text(L(uid,"set_name_ok").format(text))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "set_welcome" and is_main_admin(uid):
        s = load_settings(); s["welcome_msg"] = text; save_settings(s)
        await update.message.reply_text(L(uid,"set_welcome_ok"))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "add_folder":
        if not text: await update.message.reply_text(L(uid,"folder_empty")); return WAIT_FOLDER
        if text in folder.get("folders",{}): await update.message.reply_text(L(uid,"folder_exists").format(text)); return WAIT_FOLDER
        folder.setdefault("folders",{})[text] = {"folders":{},"files":[]}; save_content(content)
        await update.message.reply_text(L(uid,"folder_added").format(text))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "rename_folder":
        old = context.user_data.get("target","")
        if not text: await update.message.reply_text(L(uid,"folder_empty")); return WAIT_RENAME_FOLDER
        if text in folder.get("folders",{}): await update.message.reply_text(L(uid,"folder_exists").format(text)); return WAIT_RENAME_FOLDER
        if old in folder.get("folders",{}):
            folder["folders"][text] = folder["folders"].pop(old); save_content(content)
        await update.message.reply_text(L(uid,"folder_renamed").format(old,text))
        context.user_data.pop("action",None); context.user_data.pop("target",None); return ConversationHandler.END

    if action == "rename_file":
        idx = context.user_data.get("target",0); files = folder.get("files",[])
        if not text: await update.message.reply_text(L(uid,"folder_empty")); return WAIT_RENAME_FILE
        if 0 <= idx < len(files):
            files[idx]["caption"] = text; files[idx]["name"] = text; save_content(content)
        await update.message.reply_text(L(uid,"file_renamed").format(text))
        context.user_data.pop("action",None); context.user_data.pop("target",None); return ConversationHandler.END

    if action == "add_file":
        if text.startswith("http://") or text.startswith("https://"):
            fobj = {"type":"link","url":text,"caption":text,"name":text}
        else:
            fobj = {"type":"text","caption":text,"name":text}
        folder.setdefault("files",[]).append(fobj); save_content(content)
        await update.message.reply_text(L(uid,"file_added").format(fobj["caption"][:50]))
        context.user_data.pop("action",None); return ConversationHandler.END

    return ConversationHandler.END

# ═══════════════════════════════════════════════════════
#  MEDYA GİRİŞİ
# ═══════════════════════════════════════════════════════

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user; uid = str(user.id); msg = update.message
    register_user(user)

    if not is_admin(uid):
        if is_blocked(uid): return ConversationHandler.END
        s = load_settings()
        if s["maintenance"]:
            await msg.reply_text(s.get("maintenance_text_ar","🔧")); return ConversationHandler.END
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        if msg.photo:      log_user_message(user,"photo",   msg.caption or "(photo)",  file_id=msg.photo[-1].file_id)
        elif msg.video:    log_user_message(user,"video",   msg.caption or "(video)",  file_id=msg.video.file_id)
        elif msg.document: log_user_message(user,"document",msg.document.file_name or "(doc)", file_id=msg.document.file_id)
        elif msg.audio:    log_user_message(user,"audio",   msg.audio.file_name or "(audio)", file_id=msg.audio.file_id)
        elif msg.voice:    log_user_message(user,"voice",   "(voice)",                 file_id=msg.voice.file_id)
        elif msg.animation:log_user_message(user,"animation","(gif)",                 file_id=msg.animation.file_id)
        elif msg.sticker:  log_user_message(user,"sticker", msg.sticker.emoji or "(sticker)", file_id=msg.sticker.file_id)
        return ConversationHandler.END

    action = context.user_data.get("action","")

    if action == "broadcast" and is_main_admin(uid):
        users = load_users(); success = fail = 0; cap_text = msg.caption or ""
        for uid_,u in users.items():
            if int(uid_) == ADMIN_ID or is_blocked(uid_): continue
            try:
                if msg.photo:     await context.bot.send_photo(int(uid_),    msg.photo[-1].file_id, caption=cap_text)
                elif msg.video:   await context.bot.send_video(int(uid_),    msg.video.file_id,     caption=cap_text)
                elif msg.document:await context.bot.send_document(int(uid_), msg.document.file_id,  caption=cap_text)
                elif msg.animation:await context.bot.send_animation(int(uid_),msg.animation.file_id,caption=cap_text)
                success += 1
            except: fail += 1
        await msg.reply_text(L(uid,"broadcast_done").format(success,fail))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "dm_msg" and is_main_admin(uid):
        target = context.user_data.get("dm_target")
        if not target: return ConversationHandler.END
        try:
            cap_text = (msg.caption or "") + "\n\n📩"
            if msg.photo:     await context.bot.send_photo(int(target),    msg.photo[-1].file_id, caption=cap_text)
            elif msg.video:   await context.bot.send_video(int(target),    msg.video.file_id,     caption=cap_text)
            elif msg.document:await context.bot.send_document(int(target), msg.document.file_id,  caption=cap_text)
            elif msg.voice:   await context.bot.send_voice(int(target),    msg.voice.file_id)
            await msg.reply_text(L(uid,"dm_sent").format(target))
        except Exception as e:
            await msg.reply_text(L(uid,"dm_fail").format(e))
        context.user_data.pop("action",None); context.user_data.pop("dm_target",None)
        return ConversationHandler.END

    if action == "set_photo" and is_main_admin(uid):
        if msg.photo:
            s = load_settings(); s["bot_photo_id"] = msg.photo[-1].file_id; save_settings(s)
            await msg.reply_text(L(uid,"set_photo_ok"))
            context.user_data.pop("action",None)
        else:
            await msg.reply_text(L(uid,"set_photo_fail"))
        return ConversationHandler.END

    if action != "add_file": return ConversationHandler.END

    content = load_content(); path = context.user_data.get("path",[]); folder = get_folder(content,path)
    now = datetime.now().strftime("%Y%m%d%H%M%S"); cap = msg.caption or ""; fobj = None
    try:
        if msg.photo:
            fid = msg.photo[-1].file_id; local = await download_file(context,fid,f"photo_{now}.jpg")
            fobj = {"type":"photo","file_id":fid,"caption":cap or "صورة","name":f"photo_{now}.jpg",**({"local_path":local} if local else {})}
        elif msg.video:
            fname = msg.video.file_name or f"video_{now}.mp4"; fid = msg.video.file_id
            local = await download_file(context,fid,fname)
            fobj = {"type":"video","file_id":fid,"caption":cap or fname,"name":fname,**({"local_path":local} if local else {})}
        elif msg.animation:
            fid = msg.animation.file_id; local = await download_file(context,fid,f"gif_{now}.gif")
            fobj = {"type":"animation","file_id":fid,"caption":cap or "GIF","name":f"gif_{now}.gif",**({"local_path":local} if local else {})}
        elif msg.document:
            fname = msg.document.file_name or f"doc_{now}"; fid = msg.document.file_id
            local = await download_file(context,fid,fname)
            fobj = {"type":"document","file_id":fid,"caption":cap or fname,"name":fname,**({"local_path":local} if local else {})}
        elif msg.audio:
            fname = msg.audio.file_name or f"audio_{now}.mp3"; fid = msg.audio.file_id
            local = await download_file(context,fid,fname)
            fobj = {"type":"audio","file_id":fid,"caption":cap or msg.audio.title or fname,"name":fname,**({"local_path":local} if local else {})}
        elif msg.voice:
            fid = msg.voice.file_id; local = await download_file(context,fid,f"voice_{now}.ogg")
            fobj = {"type":"voice","file_id":fid,"caption":cap or "رسالة صوتية","name":f"voice_{now}.ogg",**({"local_path":local} if local else {})}
    except Exception as e:
        logger.error(f"handle_media hata: {e}")

    if fobj:
        folder.setdefault("files",[]).append(fobj); save_content(content)
        await msg.reply_text(L(uid,"file_added").format(fobj["caption"]))
        context.user_data.pop("action",None)
    else:
        await msg.reply_text(L(uid,"unsupported"))
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════
#  LOG HANDLER'LAR (group=-1)
# ═══════════════════════════════════════════════════════

async def log_user_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user
    if is_admin(user.id) or is_blocked(str(user.id)): return
    register_user(user)
    msg = update.message; now = datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        if msg.photo:      log_user_message(user,"photo",   msg.caption or "(photo)",  file_id=msg.photo[-1].file_id); await download_file(context,msg.photo[-1].file_id,f"photo_{user.id}_{now}.jpg")
        elif msg.video:    log_user_message(user,"video",   msg.caption or "(video)",  file_id=msg.video.file_id);     await download_file(context,msg.video.file_id,msg.video.file_name or f"video_{user.id}_{now}.mp4")
        elif msg.document: log_user_message(user,"document",msg.document.file_name or "(doc)", file_id=msg.document.file_id); await download_file(context,msg.document.file_id,msg.document.file_name or f"doc_{user.id}_{now}")
        elif msg.audio:    log_user_message(user,"audio",   msg.audio.file_name or "(audio)", file_id=msg.audio.file_id); await download_file(context,msg.audio.file_id,msg.audio.file_name or f"audio_{user.id}_{now}.mp3")
        elif msg.voice:    log_user_message(user,"voice",   "(voice)",                 file_id=msg.voice.file_id);     await download_file(context,msg.voice.file_id,f"voice_{user.id}_{now}.ogg")
        elif msg.animation:log_user_message(user,"animation","(gif)",                 file_id=msg.animation.file_id)
        elif msg.sticker:  log_user_message(user,"sticker", msg.sticker.emoji or "(sticker)", file_id=msg.sticker.file_id)
        elif msg.video_note: log_user_message(user,"video_note","(videonote)",         file_id=msg.video_note.file_id); await download_file(context,msg.video_note.file_id,f"vn_{user.id}_{now}.mp4")
    except Exception as e:
        logger.error(f"log_user_media: {e}")

async def log_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user
    if is_admin(user.id) or is_blocked(str(user.id)): return
    register_user(user)
    text = (update.message.text or "").strip()
    if text and text not in ALL_BTNS:
        log_user_message(user,"msg",text)

# ═══════════════════════════════════════════════════════
#  GENEL MESAJ HANDLER (AI sohbet dahil)
# ═══════════════════════════════════════════════════════

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user; uid = str(user.id); msg = update.message
    text = (msg.text or "").strip()
    if text in ALL_BTNS: return
    register_user(user)

    if not is_admin(uid):
        if msg.photo:      log_user_message(user,"photo",   msg.caption or "(photo)",  file_id=msg.photo[-1].file_id)
        elif msg.video:    log_user_message(user,"video",   msg.caption or "(video)",  file_id=msg.video.file_id)
        elif msg.document: log_user_message(user,"document",msg.document.file_name or "(doc)", file_id=msg.document.file_id)
        elif msg.audio:    log_user_message(user,"audio",   msg.audio.file_name or "(audio)", file_id=msg.audio.file_id)
        elif msg.voice:    log_user_message(user,"voice",   "(voice)",                 file_id=msg.voice.file_id)
        elif msg.animation:log_user_message(user,"animation","(gif)",                 file_id=msg.animation.file_id)
        elif msg.sticker:  log_user_message(user,"sticker", msg.sticker.emoji or "(sticker)", file_id=msg.sticker.file_id)
        elif text:         log_user_message(user,"msg",text)

    if is_admin(uid): return
    if is_blocked(uid): return

    s = load_settings()
    if s["maintenance"]:
        await msg.reply_text(s.get("maintenance_text_ar","🔧 البوت قيد التحديث...")); return

    # ── AI sohbet ─────────────────────────────────────
    if text and s.get("ai_enabled", True):
        await context.bot.send_chat_action(msg.chat_id, "typing")
        lang     = "tr" if is_main_admin(uid) else "ar"
        ai_reply = await get_ai_response(uid, text, lang)
        if "[ADMIN_TALEP]" in ai_reply:
            parts   = ai_reply.split("[ADMIN_TALEP]",1)
            clean   = parts[0].strip(); summary = parts[1].strip() if len(parts)>1 else text
            if clean: await msg.reply_text(clean)
            await msg.reply_text(L(uid,"admin_fwd"))
            await notify_admin_request(context, user, summary or text)
        else:
            await msg.reply_text(ai_reply)
    elif text and not s.get("ai_enabled", True):
        pass  # AI kapalıysa sessiz kal

# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    app = Application.builder().token(TOKEN).build()

    media_f     = (filters.PHOTO | filters.VIDEO | filters.Document.ALL |
                   filters.AUDIO | filters.VOICE | filters.ANIMATION | filters.Sticker.ALL)
    text_f      = filters.TEXT & ~filters.COMMAND

    import re
    escaped     = [re.escape(b) for b in ALL_BTNS]
    reply_btn_f = filters.Regex(f"^({'|'.join(escaped)})$")

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
            WAIT_DM_USER_ID:    [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_DM_MSG:        [MessageHandler(text_f & ~reply_btn_f, handle_text),
                                  MessageHandler(media_f, handle_media), CallbackQueryHandler(callback)],
            WAIT_BROADCAST_MSG: [MessageHandler(text_f & ~reply_btn_f, handle_text),
                                  MessageHandler(media_f, handle_media), CallbackQueryHandler(callback)],
            WAIT_SEARCH:        [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(reply_btn_f, handle_reply_buttons),
            MessageHandler(media_f, handle_media),
            CallbackQueryHandler(callback),
        ],
        allow_reentry=True,
    )

    app.add_handler(MessageHandler(media_f, log_user_media), group=-1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~reply_btn_f, log_user_text), group=-1)

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("help",    help_command))
    app.add_handler(CommandHandler("search",  search_command))
    app.add_handler(CommandHandler("mystats", mystats_command))
    app.add_handler(MessageHandler(reply_btn_f, handle_reply_buttons))
    app.add_handler(conv)
    app.add_handler(MessageHandler(media_f, handle_media))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_any_message))

    print("✅ Bot başlatıldı!")
    print(f"👑 Süper Admin ID : {ADMIN_ID}")
    print(f"💾 Veri           : {BASE_DIR}")
    print(f"🤖 Yapay Zeka     : {'✅ Gemini Aktif' if GEMINI_API_KEY else '⚠️ Pasif (GEMINI_API_KEY eksik)'}")
    if "/data" in BASE_DIR:
        print("✅ Railway Volume aktif")
    else:
        print("⚠️  Volume YOK → Railway Settings → Volumes → Mount: /data")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
