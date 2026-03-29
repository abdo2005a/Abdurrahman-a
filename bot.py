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
TOKEN          = "8574020136:AAEaxD4fk9DPQQPsZ0y0lkhdKZXVrONxQJU"
ADMIN_ID       = 7731559022


_default_dir = "/data/bot_data" if os.path.exists("/data") else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "bot_data")
BASE_DIR  = os.environ.get("DATA_DIR", _default_dir)
FILES_DIR = os.path.join(BASE_DIR, "files")
os.makedirs(BASE_DIR,  exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

DATA_FILE        = os.path.join(BASE_DIR, "bot_data.json")
USERS_FILE       = os.path.join(BASE_DIR, "users.json")
MESSAGES_FILE    = os.path.join(BASE_DIR, "user_messages.json")
SETTINGS_FILE    = os.path.join(BASE_DIR, "settings.json")
ADMINS_FILE      = os.path.join(BASE_DIR, "admins.json")
BLOCKED_FILE     = os.path.join(BASE_DIR, "blocked.json")
VIEW_COUNTS_FILE = os.path.join(BASE_DIR, "view_counts.json")
POLLS_FILE       = os.path.join(BASE_DIR, "polls.json")
# =============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
#  DİL SİSTEMİ
#  Süper Admin (ADMIN_ID) → Türkçe
#  Diğer adminler + kullanıcılar → Arapça
# ================================================================

TR = {
    # Klavye butonları
    "btn_content":   "📁 İçerik",
    "btn_mgmt":      "👥 Yönetim",
    "btn_settings":  "⚙️ Ayarlar",
    "btn_maint":     "🔧 Bakım",
    "btn_search":    "🔍 Ara",
    "btn_help":      "💬 Mesaj Gönder",
    # Genel
    "home":          "🏠 ANA SAYFA",
    "folder_list":   "📁 Klasörler:",
    "file_list":     "📎 Dosyalar:",
    "back":          "◀️ Geri",
    "cancel":        "❌ İptal",
    "close":         "✖️ Kapat",
    "maint_on":      "🔧 Bakım Modu: AÇIK",
    "maint_off":     "✅ Bakım Modu: KAPALI",
    # İçerik
    "content_mgmt":         "📁 İçerik Yönetimi",
    "add_folder":           "➕ Klasör Ekle",
    "add_file":             "📎 Dosya/Medya Ekle",
    "enter_folder_name":    "📁 Yeni klasör adını yazın:",
    "no_folders":           "Klasör yok.",
    "no_files":             "Dosya yok.",
    "add_file_prompt":       "📎 Dosya, resim, video gönderin veya link/metin yazın:\n\n📋 Bu klasördeki mevcut dosyalar:\n{}",
    "add_file_prompt_empty": "📎 Dosya, resim, video gönderin veya link/metin yazın:\n\n📭 Bu klasörde henüz dosya yok.",
    "del_folder":           "🗑 Klasör Sil",
    "rename_folder":        "✏️ Klasör Yeniden Adlandır",
    "del_file":             "🗑 Dosya Sil",
    "rename_file":          "✏️ Dosya Yeniden Adlandır",
    "del_folder_select":    "Silinecek klasörü seçin:",
    "rename_folder_select": "Yeniden adlandırılacak klasörü seçin:",
    "del_file_select":      "Silinecek dosyayı seçin:",
    "rename_file_select":   "Yeniden adlandırılacak dosyayı seçin:",
    # Onay
    "del_folder_confirm": "🗑 *'{}'* klasörünü silmek istediğinizden emin misiniz?\n⚠️ İçindeki tüm dosya ve alt klasörler de silinecek!",
    "del_file_confirm":   "🗑 *'{}'* dosyasını silmek istediğinizden emin misiniz?",
    "confirm_yes":        "✅ Evet, Sil",
    "confirm_no":         "❌ İptal",
    # Klasör/dosya işlemleri
    "folder_exists":  "❌ '{}' zaten var!",
    "folder_empty":   "❌ Ad boş olamaz!",
    "folder_added":   "✅ '{}' klasörü eklendi.",
    "folder_deleted": "✅ '{}' silindi.",
    "folder_renamed": "✅ '{}' → '{}'",
    "new_folder_name": "'{}' için yeni adı yazın:",
    "file_added":        "✅ Eklendi: {}",
    "file_exists_warn":  "⚠️ '{}' adında bir dosya zaten mevcut! Yine de eklendi.",
    "file_deleted":      "✅ '{}' silindi.",
    "file_renamed":      "✅ Yeni ad: '{}'",
    "new_file_name":     "Yeni dosya adını yazın:",
    "unsupported":       "❓ Desteklenmeyen tür.",
    "send_fail":         "❌ Gönderilemedi: {}",
    "file_notfound":     "Dosya bulunamadı.",
    "media_sent":        "✅ {}/{} medya gönderildi.",
    # Yönetim
    "mgmt_panel":    "👥 Yönetim Paneli",
    "stats":         "📊 İstatistik",
    "users":         "👥 Kullanıcılar",
    "add_admin":     "👤 Admin Ekle",
    "del_admin":     "🚫 Admin Çıkar",
    "dm_user":       "💬 Kullanıcıya Mesaj",
    "broadcast":     "📢 Herkese Duyuru",
    "stats_title":   "📊 İSTATİSTİKLER",
    "top_views":     "👁 En Çok Görüntülenen:\n",
    "total_views":   "👁 Toplam Görüntüleme: {}",
    "view_count":    " ({}x)",
    "user_list":     "👥 Kullanıcılar — birini seçin:",
    "no_users":      "Henüz kullanıcı yok.",
    "no_admins":     "Eklenmiş admin yok.",
    "admin_enter_id": "Admin eklenecek kullanıcı ID'sini yazın:",
    "admin_added":   "✅ Admin eklendi: {}",
    "admin_exists":  "❌ Zaten admin.",
    "invalid_id":    "❌ Geçersiz ID.",
    "del_admin_lbl": "Çıkarılacak admini seçin:",
    "admin_removed": "✅ Admin çıkarıldı: {}",
    "dm_select":     "💬 Mesaj göndermek istediğin kullanıcıyı seç:",
    "dm_manual":     "✏️ ID ile yaz",
    "dm_enter_id":   "Kullanıcı ID'sini yaz:",
    "dm_enter_msg":  "💬 {} kişisine gönderilecek mesajı yaz:",
    "dm_sent":       "✅ Mesaj gönderildi → {}",
    "dm_fail":       "❌ Gönderilemedi: {}",
    "dm_no_target":  "❌ Hedef kullanıcı bulunamadı.",
    "broadcast_enter": "📢 Tüm kullanıcılara mesaj yaz:\n💡 Metin, fotoğraf, video veya dosya.",
    "broadcast_done":  "📢 Duyuru tamamlandı!\n✅ Gönderildi: {}\n❌ Başarısız: {}",
    # Anket
    "poll_btn":           "📊 Anket",
    "poll_create":        "➕ Yeni Anket",
    "poll_type_select":   "📊 Anket türünü seç:",
    "poll_type_choice":   "🔘 Çoktan Seçmeli\n(Kullanıcılar şıklar arasından seçer)",
    "poll_type_open":     "✍️ Açık Uçlu\n(Kullanıcılar yazılı cevap verir)",
    "poll_results":       "📈 Sonuçlar",
    "poll_delete":        "🗑 Anketi Sil",
    "poll_panel":         "📊 Anket Yönetimi",
    "poll_enter_q":       "📝 Anket sorusunu yazın:",
    "poll_enter_opts":    "📋 Seçenekleri yazın (her satıra bir seçenek, max 6):\n\nÖrnek:\nEvet\nHayır\nFikirm yok",
    "poll_preview":       "📊 Anket Önizleme:\n\n❓ {q}\n\n{opts}\n\nGönderilsin mi?",
    "poll_send_btn":      "📤 Gönder",
    "poll_cancel_btn":    "❌ İptal",
    "poll_sent":          "📊 Anket gönderildi!\n✅ {s} kullanıcı\n❌ {f} başarısız",
    "poll_no_polls":      "Henüz anket yok.",
    "poll_voted":         "✅ Oyunuz kaydedildi!",
    "poll_already_voted": "❗ Bu ankete zaten oy verdiniz.",
    "poll_closed":        "📊 Bu anket sona erdi.",
    "poll_results_title": "📈 Anket Sonuçları:\n\n❓ {q}\n👥 Toplam oy: {total}\n\n{bars}",
    "poll_no_votes":      "Henüz oy yok.",
    "poll_deleted":       "✅ Anket silindi.",
    "poll_select":        "Seçmek istediğin anketi seç:",
    "poll_comment_prompt":"💬 İstersen bir yorum ekleyebilirsin (isteğe bağlı):\n\nYorum yazmak istemiyorsan /skip yaz.",
    "poll_comment_saved": "💬 Yorumun kaydedildi, teşekkürler!",
    "poll_comment_skip":  "✅ Tamam, yorum olmadan devam edildi.",
    "poll_comments_title":"💬 Kullanıcı Yorumları:",
    "poll_no_comments":   "Henüz yorum yok.",
    # (boş)
    "admin_notif":       "🔔 Kullanıcı talebi\n\n👤 {name}{un}\n🆔 {uid}\n📋 {summary}\n🕐 {time}",
    "new_user_notif":  "🆕 Yeni kullanıcı!\n\n👤 {name}{un}\n🆔 {uid}\n🕐 {time}",
    "reply_btn":     "💬 Yanıtla (ID: {})",
    "dm_prefix":     "📩 Yönetici mesajı:\n\n{}",
    "block_btn":     "🚫 Engelle",
    "unblock_btn":   "✅ Engeli Kaldır",
    "msg_btn":       "💬 Mesaj Gönder",
    "blocked_ok":    "✅ {} engellendi.",
    "unblocked_ok":  "✅ Engel kaldırıldı: {}",
    "send_media_btn": "🖼 Medyaları Gönder ({})",
    "user_last":     "🕐 Son görülme:",
    "user_msgs":     "💬 Mesaj: {} | 📎 Medya: {}",
    # Ayarlar
    "settings_title":     "⚙️ BOT AYARLARI",
    "set_name_btn":       "📝 Bot Adını Değiştir",
    "set_welcome_btn":    "💬 Karşılama Mesajı",
    "set_photo_btn":      "🖼 Bot Fotoğrafı",
    "set_blocked_btn":    "🚫 Engellenenler",
    "btn_mgmt_btn":       "🎛 Buton Yönetimi",
    "set_name_prompt":    "Yeni bot adını yazın (mevcut: {}):",
    "set_welcome_prompt": "Yeni karşılama mesajını yazın:",
    "set_photo_prompt":   "Yeni bot fotoğrafını gönderin:",
    "set_photo_ok":       "✅ Bot fotoğrafı güncellendi.",
    "set_photo_fail":     "❌ Lütfen bir fotoğraf gönderin.",
    "set_name_ok":        "✅ Bot adı: '{}'",
    "set_welcome_ok":     "✅ Karşılama mesajı güncellendi.",
    "blocked_list":       "🚫 Engellenenler ({})",
    "no_blocked":         "Kimse engellenmedi.",
    "maint_toggle":       "Bakım Modu: {}",
    "maint_on_str":       "AÇIK 🔧",
    "maint_off_str":      "KAPALI ✅",
    "btn_mgmt_title":     "🎛 Buton Görünürlük Ayarları",
    # Arama
    "search_prompt":  "🔍 Aramak istediğin kelimeyi yaz:",
    "search_results": "🔍 '{}' için sonuçlar:",
    "search_none":    "❌ '{}' için sonuç bulunamadı.",
    # Mesajlaşma
    "msg_to_admin_prompt": "💬 Mesajınızı yazın, doğrudan yöneticiye iletilecek:",
    "msg_to_admin_sent":   "✅ Mesajınız yöneticiye iletildi.",
    "admin_user_msg":      "💬 YENİ MESAJ\n\n👤 {name}{un}\n🆔 {uid}\n\n📝 {text}\n🕐 {time}",
    # Yardım
    "help_text": (
        "❓ *YARDIM — Süper Admin*\n\n"
        "📁 *İçerik* — Klasör/dosya ekle, sil, düzenle\n"
        "👥 *Yönetim* — Kullanıcılar, adminler, duyuru\n"
        "⚙️ *Ayarlar* — Bot adı, karşılama, fotoğraf\n"
        "🔧 *Bakım* — Bakım modunu aç/kapat\n"
        "🔍 *Ara* — Klasör ve dosyalarda ara\n\n"
        "Eklediğin adminler yalnızca klasör ve dosya ekleyebilir."
    ),
}

AR = {
    # Klavye butonları
    "btn_content":   "📁 المحتوى",
    "btn_mgmt":      "👥 الإدارة",
    "btn_settings":  "⚙️ الإعدادات",
    "btn_maint":     "🔧 الصيانة",
    "btn_search":    "🔍 بحث",
    "btn_help":      "💬 راسل المسؤول",
    # Genel
    "home":          "🏠 الصفحة الرئيسية",
    "folder_list":   "📁 المجلدات:",
    "file_list":     "📎 الملفات:",
    "back":          "◀️ رجوع",
    "cancel":        "❌ إلغاء",
    "close":         "✖️ إغلاق",
    "maint_on":      "🔧 وضع الصيانة: مفعّل",
    "maint_off":     "✅ وضع الصيانة: معطّل",
    # İçerik
    "content_mgmt":         "📁 إدارة المحتوى",
    "add_folder":           "➕ إضافة مجلد",
    "add_file":             "📎 إضافة ملف/وسائط",
    "enter_folder_name":    "📁 اكتب اسم المجلد الجديد:",
    "no_folders":           "لا توجد مجلدات.",
    "no_files":             "لا توجد ملفات.",
    "add_file_prompt":       "📎 أرسل ملفاً أو صورة أو فيديو، أو اكتب رابطاً/نصاً:\n\n📋 الملفات الموجودة:\n{}",
    "add_file_prompt_empty": "📎 أرسل ملفاً أو صورة أو فيديو، أو اكتب رابطاً/نصاً:\n\n📭 لا توجد ملفات في هذا المجلد بعد.",
    "del_folder":           "🗑 حذف مجلد",
    "rename_folder":        "✏️ إعادة تسمية مجلد",
    "del_file":             "🗑 حذف ملف",
    "rename_file":          "✏️ إعادة تسمية ملف",
    "del_folder_select":    "اختر المجلد للحذف:",
    "rename_folder_select": "اختر المجلد لإعادة التسمية:",
    "del_file_select":      "اختر الملف للحذف:",
    "rename_file_select":   "اختر الملف لإعادة التسمية:",
    # Onay
    "del_folder_confirm": "🗑 هل تريد حذف مجلد *'{}'*؟\n⚠️ سيتم حذف جميع الملفات والمجلدات الفرعية!",
    "del_file_confirm":   "🗑 هل تريد حذف *'{}'*؟",
    "confirm_yes":        "✅ نعم، احذف",
    "confirm_no":         "❌ إلغاء",
    # Klasör/dosya işlemleri
    "folder_exists":  "❌ '{}' موجود بالفعل!",
    "folder_empty":   "❌ لا يمكن أن يكون الاسم فارغاً!",
    "folder_added":   "✅ تمت إضافة المجلد '{}'.",
    "folder_deleted": "✅ تم حذف '{}'.",
    "folder_renamed": "✅ '{}' → '{}'",
    "new_folder_name": "اكتب الاسم الجديد لـ '{}':",
    "file_added":        "✅ تمت الإضافة: {}",
    "file_exists_warn":  "⚠️ يوجد ملف باسم '{}' بالفعل! تمت الإضافة على أي حال.",
    "file_deleted":      "✅ تم حذف '{}'.",
    "file_renamed":      "✅ الاسم الجديد: '{}'",
    "new_file_name":     "اكتب الاسم الجديد للملف:",
    "unsupported":       "❓ نوع غير مدعوم.",
    "send_fail":         "❌ فشل الإرسال: {}",
    "file_notfound":     "الملف غير موجود.",
    "media_sent":        "✅ تم إرسال {}/{} وسائط.",
    # Yönetim
    "mgmt_panel":    "👥 لوحة الإدارة",
    "stats":         "📊 الإحصائيات",
    "users":         "👥 المستخدمون",
    "add_admin":     "👤 إضافة مشرف",
    "del_admin":     "🚫 إزالة مشرف",
    "dm_user":       "💬 رسالة لمستخدم",
    "broadcast":     "📢 رسالة للجميع",
    "stats_title":   "📊 الإحصائيات",
    "top_views":     "👁 الأكثر مشاهدة:\n",
    "total_views":   "👁 إجمالي المشاهدات: {}",
    "view_count":    " ({}x)",
    "user_list":     "👥 المستخدمون — اختر واحداً:",
    "no_users":      "لا يوجد مستخدمون بعد.",
    "no_admins":     "لا يوجد مشرفون.",
    "admin_enter_id": "اكتب ID المستخدم لإضافته مشرفاً:",
    "admin_added":   "✅ تمت إضافة المشرف: {}",
    "admin_exists":  "❌ هو مشرف بالفعل.",
    "invalid_id":    "❌ ID غير صالح.",
    "del_admin_lbl": "اختر المشرف للإزالة:",
    "admin_removed": "✅ تمت إزالة المشرف: {}",
    "dm_select":     "💬 اختر المستخدم:",
    "dm_manual":     "✏️ أدخل ID يدوياً",
    "dm_enter_id":   "اكتب ID المستخدم:",
    "dm_enter_msg":  "💬 اكتب الرسالة لـ {}:",
    "dm_sent":       "✅ تم الإرسال → {}",
    "dm_fail":       "❌ فشل الإرسال: {}",
    "dm_no_target":  "❌ المستخدم غير موجود.",
    "broadcast_enter": "📢 اكتب الرسالة للجميع:\n💡 نص أو صورة أو فيديو أو ملف.",
    "broadcast_done":  "📢 اكتمل الإرسال!\n✅ نجح: {}\n❌ فشل: {}",
    # Anket
    "poll_btn":           "📊 استطلاع",
    "poll_create":        "➕ استطلاع جديد",
    "poll_type_select":   "📊 اختر نوع الاستطلاع:",
    "poll_type_choice":   "🔘 اختيار من متعدد\n(المستخدمون يختارون من الخيارات)",
    "poll_type_open":     "✍️ سؤال مفتوح\n(المستخدمون يكتبون إجابتهم)",
    "poll_results":       "📈 النتائج",
    "poll_delete":        "🗑 حذف الاستطلاع",
    "poll_panel":         "📊 إدارة الاستطلاعات",
    "poll_enter_q":       "📝 اكتب سؤال الاستطلاع:",
    "poll_enter_opts":    "📋 اكتب الخيارات (خيار في كل سطر، max 6):\n\nمثال:\nنعم\nلا\nلا أعرف",
    "poll_preview":       "📊 معاينة الاستطلاع:\n\n❓ {q}\n\n{opts}\n\nهل تريد الإرسال؟",
    "poll_send_btn":      "📤 إرسال",
    "poll_cancel_btn":    "❌ إلغاء",
    "poll_sent":          "📊 تم إرسال الاستطلاع!\n✅ {s} مستخدم\n❌ {f} فشل",
    "poll_no_polls":      "لا توجد استطلاعات بعد.",
    "poll_voted":         "✅ تم تسجيل صوتك!",
    "poll_already_voted": "❗ لقد صوّتت بالفعل في هذا الاستطلاع.",
    "poll_closed":        "📊 انتهى هذا الاستطلاع.",
    "poll_results_title": "📈 نتائج الاستطلاع:\n\n❓ {q}\n👥 مجموع الأصوات: {total}\n\n{bars}",
    "poll_no_votes":      "لا توجد أصوات بعد.",
    "poll_deleted":       "✅ تم حذف الاستطلاع.",
    "poll_select":        "اختر الاستطلاع:",
    "poll_comment_prompt":"💬 يمكنك إضافة تعليق (اختياري):\n\nإذا لم تريد التعليق اكتب /skip",
    "poll_comment_saved": "💬 تم حفظ تعليقك، شكراً!",
    "poll_comment_skip":  "✅ تم المتابعة بدون تعليق.",
    "poll_comments_title":"💬 تعليقات المستخدمين:",
    "poll_no_comments":   "لا توجد تعليقات بعد.",
    # (boş)
    "admin_notif":       "🔔 طلب مستخدم\n\n👤 {name}{un}\n🆔 {uid}\n📋 {summary}\n🕐 {time}",
    "new_user_notif":  "🆕 مستخدم جديد!\n\n👤 {name}{un}\n🆔 {uid}\n🕐 {time}",
    "reply_btn":     "💬 رد (ID: {})",
    "dm_prefix":     "📩 رسالة من المسؤول:\n\n{}",
    "block_btn":     "🚫 حظر",
    "unblock_btn":   "✅ إلغاء الحظر",
    "msg_btn":       "💬 إرسال رسالة",
    "blocked_ok":    "✅ تم حظر {}.",
    "unblocked_ok":  "✅ تم إلغاء حظر: {}",
    "send_media_btn": "🖼 إرسال الوسائط ({})",
    "user_last":     "🕐 آخر ظهور:",
    "user_msgs":     "💬 الرسائل: {} | 📎 الوسائط: {}",
    # Ayarlar
    "settings_title":     "⚙️ إعدادات البوت",
    "set_name_btn":       "📝 اسم البوت",
    "set_welcome_btn":    "💬 رسالة الترحيب",
    "set_photo_btn":      "🖼 صورة البوت",
    "set_blocked_btn":    "🚫 المحظورون",
    "btn_mgmt_btn":       "🎛 إدارة الأزرار",
    "set_name_prompt":    "اكتب الاسم الجديد للبوت (الحالي: {}):",
    "set_welcome_prompt": "اكتب رسالة الترحيب الجديدة:",
    "set_photo_prompt":   "أرسل الصورة الجديدة للبوت:",
    "set_photo_ok":       "✅ تم تحديث صورة البوت.",
    "set_photo_fail":     "❌ يرجى إرسال صورة.",
    "set_name_ok":        "✅ اسم البوت: '{}'",
    "set_welcome_ok":     "✅ تم تحديث رسالة الترحيب.",
    "blocked_list":       "🚫 المحظورون ({})",
    "no_blocked":         "لا أحد محظور.",
    "maint_toggle":       "وضع الصيانة: {}",
    "maint_on_str":       "مفعّل 🔧",
    "maint_off_str":      "معطّل ✅",
    "btn_mgmt_title":     "🎛 إعدادات ظهور الأزرار",
    # Arama
    "search_prompt":  "🔍 اكتب كلمة البحث:",
    "search_results": "🔍 نتائج '{}' :",
    "search_none":    "❌ لا توجد نتائج لـ '{}'.",
    # Mesajlaşma
    "msg_to_admin_prompt": "💬 اكتب رسالتك، وستصل مباشرة إلى المسؤول:",
    "msg_to_admin_sent":   "✅ تم إرسال رسالتك إلى المسؤول.",
    "admin_user_msg":      "💬 رسالة جديدة\n\n👤 {name}{un}\n🆔 {uid}\n\n📝 {text}\n🕐 {time}",
    # Yardım
    "help_text": (
        "❓ *المساعدة*\n\n"
        "📁 *المحتوى* — تصفح المجلدات والملفات\n"
        "🔍 *بحث* — ابحث عن ملف أو مجلد\n"
        "💬 *راسل المسؤول* — أرسل طلباً للمسؤول"
    ),
}

DEFAULT_WELCOME_AR = (
    "🎓 أهلاً وسهلاً في بوت مهندسي المستقبل! 🚀\n\n"
    "هذا البوت رفيقك الدراسي على طريق التفوّق.\n"
    "ستجد هنا كل ما تحتاجه:\n\n"
    "📁 ملفات المواد والمحاضرات\n"
    "🖼 الصور والمخططات الهندسية\n"
    "📚 المراجع والكتب التقنية\n\n"
    "﴿ وَقُل رَّبِّ زِدْنِي عِلْمًا ﴾ 📖\n\n"
    "استخدم الأزرار أدناه للبدء 👇"
)

# ================================================================
#  YARDIMCI FONKSİYONLAR
# ================================================================

def is_main_admin(uid): return int(uid) == ADMIN_ID

def L(uid, key, *args):
    lang = TR if is_main_admin(uid) else AR
    val  = lang.get(key, TR.get(key, key))
    return val.format(*args) if args else val

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

def load_content():      return load_json(DATA_FILE,        {"folders": {}, "files": []})
def save_content(d):     save_json(DATA_FILE, d)
def load_users():        return load_json(USERS_FILE,       {})
def save_users(d):       save_json(USERS_FILE, d)
def load_messages():     return load_json(MESSAGES_FILE,    {})
def save_messages(d):    save_json(MESSAGES_FILE, d)
def load_admins():       return load_json(ADMINS_FILE,      [])
def save_admins(d):      save_json(ADMINS_FILE, d)
def load_blocked():      return load_json(BLOCKED_FILE,     [])
def save_blocked(d):     save_json(BLOCKED_FILE, d)
def load_view_counts():  return load_json(VIEW_COUNTS_FILE, {})
def save_view_counts(d): save_json(VIEW_COUNTS_FILE, d)
def load_polls():        return load_json(POLLS_FILE, {})
def save_polls(d):       save_json(POLLS_FILE, d)

def make_poll_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def poll_bar(count, total):
    """Görsel oy barı."""
    if total == 0: pct = 0
    else: pct = count / total * 100
    filled = int(pct / 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"{bar}  {pct:.0f}%  ({count} oy)"

def build_poll_results_text(poll, uid, show_voters=False):
    """
    Anket sonuçlarını güzel formatta oluşturur.
    show_voters=True → kimin ne seçtiği de gösterilir (sadece admin için)
    """
    votes  = poll.get("votes", {})   # {uid: "seçenek"}
    opts   = poll.get("options", [])
    total  = len(votes)
    counts = {o: 0 for o in opts}
    voters = {o: [] for o in opts}   # {seçenek: [kullanıcı adları]}

    users_data = load_users()
    for voter_uid, chosen in votes.items():
        if chosen in counts:
            counts[chosen] += 1
            u    = users_data.get(str(voter_uid), {})
            name = u.get("full_name") or u.get("first_name") or f"ID:{voter_uid}"
            un   = f" @{u['username']}" if u.get("username") else ""
            voters[chosen].append(f"{name}{un}")

    lines = [
        f"📊 {'نتائج الاستطلاع' if not is_main_admin(uid) else 'Anket Sonuçları'}",
        f"",
        f"❓ {poll['question']}",
        f"",
        f"👥 {'مجموع الأصوات' if not is_main_admin(uid) else 'Toplam Oy'}: {total}",
        f"{'─' * 28}",
    ]

    for o in opts:
        lines.append(f"\n🔹 {o}")
        lines.append(f"   {poll_bar(counts[o], total)}")
        if show_voters and voters[o]:
            for v in voters[o][:10]:  # max 10 isim göster
                lines.append(f"   ├ 👤 {v}")
            if len(voters[o]) > 10:
                lines.append(f"   └ ... +{len(voters[o])-10} kişi daha")

    lines.append(f"\n{'─' * 28}")
    active_str = "✅ Aktif" if poll.get("active") else "🔴 Kapalı"
    if is_main_admin(uid):
        lines.append(active_str)

    return "\n".join(lines)

def load_settings():
    default = {
        "maintenance":      False,
        "maintenance_text": "🔧 البوت قيد التحديث، يرجى المحاولة لاحقاً...",
        "bot_name":         "بوت مهندسي المستقبل",
        "welcome_msg":      DEFAULT_WELCOME_AR,
        "bot_photo_id":     None,
        "user_buttons": {
            "btn_search": True,
            "btn_help":   True,
        },
    }
    data = load_json(SETTINGS_FILE, default)
    for k, v in default.items():
        data.setdefault(k, v)
    return data

def save_settings(d): save_json(SETTINGS_FILE, d)

def is_admin(uid):
    return int(uid) == ADMIN_ID or int(uid) in [int(x) for x in load_admins()]

def is_blocked(uid):
    return int(uid) in [int(x) for x in load_blocked()]

def register_user(user) -> bool:
    """Kullanıcıyı kaydeder. Yeni kullanıcıysa True döner."""
    users = load_users()
    uid   = str(user.id)
    is_new = uid not in users
    users[uid] = {
        "id":         user.id,
        "first_name": user.first_name or "",
        "last_name":  user.last_name  or "",
        "username":   user.username   or "",
        "full_name":  user.full_name  or "",
        "last_seen":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_users(users)
    return is_new

def log_user_message(user, msg_type: str, content: str, file_id: str = None):
    uid = str(user.id)
    if is_main_admin(uid): return  # sadece süper admin hariç, diğer adminler kaydedilir
    msgs = load_messages()
    entry = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "type": msg_type, "content": str(content)[:300]}
    if file_id: entry["file_id"] = file_id
    msgs.setdefault(uid, []).append(entry)
    msgs[uid] = msgs[uid][-2000:]
    save_messages(msgs)

def increment_view(f: dict):
    """Dosya görüntüleme sayacını artırır."""
    key  = f.get("file_id") or f.get("caption","unknown")
    name = f.get("caption", f.get("name","?"))
    vc   = load_view_counts()
    if key not in vc:
        vc[key] = {"count": 0, "name": name}
    vc[key]["count"] += 1
    vc[key]["name"]   = name   # isim güncellenmiş olabilir
    save_view_counts(vc)

def get_folder(content, path):
    cur = content
    for name in path:
        cur = cur.setdefault("folders", {}).setdefault(name, {"folders": {}, "files": []})
    return cur

def folder_file_names(folder: dict) -> list:
    return [f.get("caption", f.get("name", "")) for f in folder.get("files", [])]

def folder_item_count(folder: dict) -> str:
    """Klasör içindeki eleman sayısını kısa metin olarak döner."""
    n_files   = len(folder.get("files",   []))
    n_folders = len(folder.get("folders", {}))
    parts = []
    if n_folders: parts.append(f"{n_folders}📁")
    if n_files:   parts.append(f"{n_files}📎")
    return " ".join(parts) if parts else ""

async def download_file(context, file_id: str, filename: str) -> Optional[str]:
    """Dosyayı diske indir. Volume yoksa veya 20MB+ ise atla, file_id yeterli."""
    try:
        tg_file = await context.bot.get_file(file_id)
        # Telegram 20MB üzeri dosyalara get_file verir ama download bazen başarısız olur
        safe = "".join(c for c in filename if c.isalnum() or c in "._- ").strip() or \
               f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        dest = os.path.join(FILES_DIR, safe)
        base, ext = os.path.splitext(dest)
        n = 1
        while os.path.exists(dest):
            dest = f"{base}_{n}{ext}"; n += 1
        await tg_file.download_to_drive(dest)
        logger.info(f"✅ İndirildi: {dest}")
        return dest
    except Exception as e:
        logger.warning(f"⚠️ İndirme atlandı ({filename}): {e} — file_id kullanılacak")
        return None

# ================================================================
#  STATES
# ================================================================
(WAIT_FOLDER, WAIT_FILE,
 WAIT_ADMIN_ID, WAIT_RENAME_FOLDER, WAIT_RENAME_FILE,
 WAIT_BOT_NAME, WAIT_WELCOME, WAIT_PHOTO,
 WAIT_DM_USER_ID, WAIT_DM_MSG, WAIT_BROADCAST_MSG,
 WAIT_SEARCH, WAIT_USER_MSG,
 WAIT_POLL_QUESTION, WAIT_POLL_OPTIONS,
 WAIT_POLL_COMMENT) = range(16)

ALL_BTNS = {
    TR["btn_content"],  AR["btn_content"],
    TR["btn_mgmt"],
    TR["btn_settings"],
    TR["btn_maint"],    AR["btn_maint"],
    TR["btn_search"],   AR["btn_search"],
    TR["btn_help"],     AR["btn_help"],
}

# ================================================================
#  ARAMA
# ================================================================

def search_content(query: str, node=None, path=None, results=None):
    if node    is None: node    = load_content()
    if path    is None: path    = []
    if results is None: results = []
    q = query.lower()
    for idx, f in enumerate(node.get("files", [])):
        name = f.get("caption", f.get("name", ""))
        if q in name.lower():
            results.append({"path": path[:], "name": name, "idx": idx,
                            "type": f.get("type",""), "is_folder": False})
    for fname, folder in node.get("folders", {}).items():
        if q in fname.lower():
            results.append({"path": path[:], "name": fname, "idx": None,
                            "type": "folder", "is_folder": True})
        search_content(query, folder, path + [fname], results)
    return results

async def do_search(message, uid: str, query: str):
    results = search_content(query)
    if not results:
        await message.reply_text(L(uid, "search_none").format(query))
        return
    lines = [L(uid, "search_results").format(query), ""]
    kb    = []
    for r in results[:10]:
        path_str = " › ".join(r["path"]) if r["path"] else "🏠"
        icon = "📁" if r["is_folder"] else "📎"
        lines.append(f"{icon} {r['name']}\n   📍 {path_str}")
        if not r["is_folder"]:
            path_encoded = "~~".join(r["path"]) if r["path"] else ""
            kb.append([InlineKeyboardButton(
                f"{icon} {r['name'][:40]}",
                callback_data=f"srch|{path_encoded}|{r['idx']}")])
    await message.reply_text("\n".join(lines)[:3500])
    if kb:
        kb.append([InlineKeyboardButton(L(uid, "close"), callback_data="close")])
        await message.reply_text("👆", reply_markup=InlineKeyboardMarkup(kb))

# ================================================================
#  KLAVYELER
# ================================================================

def reply_kb(uid):
    uid = str(uid)
    if is_main_admin(uid):
        return ReplyKeyboardMarkup([
            [KeyboardButton(TR["btn_content"]),  KeyboardButton(TR["btn_mgmt"])],
            [KeyboardButton(TR["btn_settings"]), KeyboardButton(TR["btn_maint"])],
            [KeyboardButton(TR["btn_search"]),   KeyboardButton(TR["btn_help"])],
        ], resize_keyboard=True)
    elif is_admin(uid):
        return ReplyKeyboardMarkup([
            [KeyboardButton(AR["btn_content"]),  KeyboardButton(AR["btn_maint"])],
            [KeyboardButton(AR["btn_search"]),   KeyboardButton(AR["btn_help"])],
        ], resize_keyboard=True)
    else:
        s  = load_settings()
        ub = s.get("user_buttons", {})
        rows = []
        row1 = []
        if ub.get("btn_search", True): row1.append(KeyboardButton(AR["btn_search"]))
        if ub.get("btn_help",   True): row1.append(KeyboardButton(AR["btn_help"]))
        if row1: rows.append(row1)
        if not rows: rows = [[]]
        return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def folder_text(folder, path, uid):
    uid    = str(uid)
    header = "📂 " + " › ".join(path) if path else L(uid, "home")
    lines  = [header, "─" * 22]
    folds  = folder.get("folders", {})
    files  = folder.get("files",   [])
    if folds:
        lines.append(L(uid, "folder_list"))
        for name, sub in folds.items():
            cnt = folder_item_count(sub)
            lines.append(f"  • {name}" + (f"  ({cnt})" if cnt else ""))
    if files:
        lines.append(L(uid, "file_list"))
        for f in files:
            lines.append(f"  • {f.get('caption', f.get('name','?'))}")
    if is_admin(uid):
        s = load_settings()
        lines.append("─" * 22)
        lines.append(L(uid, "maint_on") if s["maintenance"] else L(uid, "maint_off"))
    return "\n".join(lines)

def folder_kb(path, folder, uid, page=0):
    uid        = str(uid)
    kb         = []
    all_folders = list(folder.get("folders", {}).items())
    all_files   = folder.get("files", [])

    # Sayfalama: her sayfada 20 klasör + 20 dosya
    PAGE_SIZE   = 20
    f_start     = page * PAGE_SIZE
    f_end       = f_start + PAGE_SIZE
    page_folders = all_folders[f_start:f_end]
    page_files   = all_files[f_start:f_end]

    for name, sub in page_folders:
        cnt   = folder_item_count(sub)
        label = f"📁 {name}" + (f" ({cnt})" if cnt else "")
        kb.append([InlineKeyboardButton(label, callback_data=f"open|{name}")])

    for idx, f in enumerate(page_files):
        real_idx = f_start + idx
        cap = f.get("caption", f.get("name","?"))
        kb.append([InlineKeyboardButton(f"📎 {cap}", callback_data=f"getfile|{real_idx}")])

    # Sayfa navigasyonu
    total_items = max(len(all_folders), len(all_files))
    total_pages = max(1, -(-total_items // PAGE_SIZE))  # ceiling division
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"page|{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if f_end < len(all_folders) or f_end < len(all_files):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"page|{page+1}"))
    if nav:
        kb.append(nav)

    if path:
        kb.append([InlineKeyboardButton(L(uid, "back"), callback_data="nav|back")])
    return InlineKeyboardMarkup(kb)

async def show_folder(query, context, path, note=""):
    content = load_content()
    folder  = get_folder(content, path)
    uid     = str(query.from_user.id)
    page    = context.user_data.get("page", 0)
    text    = folder_text(folder, path, uid)
    if note: text += f"\n\n{note}"
    try:
        await query.edit_message_text(text, reply_markup=folder_kb(path, folder, uid, page))
    except Exception:
        pass

async def show_folder_new(message, uid, path=None, page=0):
    path    = path or []
    content = load_content()
    folder  = get_folder(content, path)
    uid     = str(uid)
    await message.reply_text(
        folder_text(folder, path, uid),
        reply_markup=folder_kb(path, folder, uid, page))

async def _delete_last_inline(context, chat_id):
    msg_id = context.user_data.get("last_inline_msg")
    if msg_id:
        try: await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except: pass
        context.user_data.pop("last_inline_msg", None)

# ================================================================
#  DOSYA GÖNDERME
# ================================================================

async def _send_file(message, f: dict, uid: str):
    ftype = f.get("type",""); fid = f.get("file_id","")
    cap   = f.get("caption",""); url = f.get("url","")
    try:
        if   ftype == "photo":     await message.reply_photo(fid, caption=cap)
        elif ftype == "video":     await message.reply_video(fid, caption=cap)
        elif ftype == "animation": await message.reply_animation(fid, caption=cap)
        elif ftype == "document":  await message.reply_document(fid, caption=cap)
        elif ftype == "audio":     await message.reply_audio(fid, caption=cap)
        elif ftype == "voice":     await message.reply_voice(fid, caption=cap)
        elif ftype == "link":      await message.reply_text(f"🔗 {cap}\n{url}" if cap != url else f"🔗 {url}")
        elif ftype == "text":      await message.reply_text(cap)
        else: await message.reply_text(L(uid, "unsupported"))
        increment_view(f)   # görüntüleme sayacı
    except Exception as e:
        await message.reply_text(L(uid, "send_fail").format(e))

# ================================================================
#  /start   /menu
# ================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; uid = str(user.id)

    is_new = register_user(user)
    log_user_message(user, "command", "/start")

    if is_blocked(uid) and not is_admin(uid): return

    s = load_settings()
    context.user_data["path"] = []
    context.user_data["mode"] = "browse"
    context.user_data.pop("action", None)

    await update.message.reply_text("👋", reply_markup=reply_kb(uid))

    if not is_admin(uid):
        if s["maintenance"]:
            await update.message.reply_text(s.get("maintenance_text","🔧")); return
        if s.get("bot_photo_id"):
            await update.message.reply_photo(s["bot_photo_id"], caption=s.get("welcome_msg") or None)
        elif s.get("welcome_msg"):
            await update.message.reply_text(s["welcome_msg"])

    await show_folder_new(update.message, uid)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; uid = str(user.id)
    register_user(user)
    context.user_data["mode"]  = "browse"
    context.user_data["path"]  = []
    context.user_data.pop("action", None)
    await show_folder_new(update.message, uid)
# ================================================================
#  REPLY KLAVYE HANDLER
# ================================================================

async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; uid = str(user.id)
    text = (update.message.text or "").strip()
    register_user(user)
    await _delete_last_inline(context, update.effective_chat.id)

    # Buton basıldığında önceki aksiyonu temizle (takılma önleme)
    context.user_data.pop("action", None)

    # Kullanıcı/alt-admin buton seçimini admine bildir
    if not is_main_admin(uid) and not is_blocked(uid):
        log_user_message(user, "button", text)

    # ── Arama (herkes) ───────────────────────────────
    if text in (TR["btn_search"], AR["btn_search"]):
        context.user_data["action"] = "search"
        await update.message.reply_text(L(uid, "search_prompt"))
        return

    # ── Mesaj Gönder / Yardım (herkes) ──────────────
    if text in (TR["btn_help"], AR["btn_help"]):
        if is_admin(uid):
            await update.message.reply_text(L(uid, "help_text"), parse_mode="Markdown")
        else:
            context.user_data["action"] = "user_msg_to_admin"
            await update.message.reply_text(L(uid, "msg_to_admin_prompt"))
        return

    # ── Sadece adminler buradan devam ────────────────
    if not is_admin(uid): return

    # ── İçerik ──────────────────────────────────────
    if text in (TR["btn_content"], AR["btn_content"]):
        if is_main_admin(uid):
            kb = [
                [InlineKeyboardButton(L(uid,"add_folder"),    callback_data="cnt|add_folder"),
                 InlineKeyboardButton(L(uid,"del_folder"),    callback_data="cnt|del_folder")],
                [InlineKeyboardButton(L(uid,"rename_folder"), callback_data="cnt|rename_folder"),
                 InlineKeyboardButton(L(uid,"add_file"),      callback_data="cnt|add_file")],
                [InlineKeyboardButton(L(uid,"del_file"),      callback_data="cnt|del_file"),
                 InlineKeyboardButton(L(uid,"rename_file"),   callback_data="cnt|rename_file")],
                [InlineKeyboardButton(L(uid,"close"),         callback_data="close")],
            ]
        else:
            kb = [
                [InlineKeyboardButton(L(uid,"add_folder"), callback_data="cnt|add_folder"),
                 InlineKeyboardButton(L(uid,"add_file"),   callback_data="cnt|add_file")],
                [InlineKeyboardButton(L(uid,"close"),      callback_data="close")],
            ]
        sent = await update.message.reply_text(L(uid,"content_mgmt"), reply_markup=InlineKeyboardMarkup(kb))
        context.user_data["last_inline_msg"] = sent.message_id
        return

    # ── Bakım (tüm adminler) ─────────────────────────
    if text in (TR["btn_maint"], AR["btn_maint"]):
        s = load_settings(); s["maintenance"] = not s["maintenance"]; save_settings(s)
        durum = L(uid,"maint_on_str") if s["maintenance"] else L(uid,"maint_off_str")
        await update.message.reply_text(L(uid,"maint_toggle").format(durum))
        return

    # ── Sadece süper admin ───────────────────────────
    if not is_main_admin(uid): return

    if text == TR["btn_mgmt"]:
        kb = [
            [InlineKeyboardButton(TR["stats"],     callback_data="mgmt|stats"),
             InlineKeyboardButton(TR["users"],     callback_data="mgmt|users")],
            [InlineKeyboardButton(TR["add_admin"], callback_data="mgmt|add_admin"),
             InlineKeyboardButton(TR["del_admin"], callback_data="mgmt|del_admin")],
            [InlineKeyboardButton(TR["dm_user"],   callback_data="mgmt|dm_user"),
             InlineKeyboardButton(TR["broadcast"], callback_data="mgmt|broadcast")],
            [InlineKeyboardButton(TR["poll_btn"],  callback_data="mgmt|poll")],
            [InlineKeyboardButton(TR["close"],     callback_data="close")],
        ]
        sent = await update.message.reply_text(TR["mgmt_panel"], reply_markup=InlineKeyboardMarkup(kb))
        context.user_data["last_inline_msg"] = sent.message_id
        return

    if text == TR["btn_settings"]:
        s   = load_settings()
        txt = (
            f"{TR['settings_title']}\n\n"
            f"📝 Ad: {s.get('bot_name','—')}\n"
            f"💬 Karşılama: {str(s.get('welcome_msg','—'))[:60]}...\n"
            f"🖼 Fotoğraf: {'✅' if s.get('bot_photo_id') else '❌'}\n"
            f"🚫 Engellenenler: {len(load_blocked())} kişi"
        )
        kb = [
            [InlineKeyboardButton(TR["set_name_btn"],    callback_data="set|name"),
             InlineKeyboardButton(TR["set_welcome_btn"], callback_data="set|welcome")],
            [InlineKeyboardButton(TR["set_photo_btn"],   callback_data="set|photo"),
             InlineKeyboardButton(TR["set_blocked_btn"], callback_data="set|blocked")],
            [InlineKeyboardButton(TR["btn_mgmt_btn"],    callback_data="set|btn_mgmt")],
            [InlineKeyboardButton(TR["close"],           callback_data="close")],
        ]
        sent = await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        context.user_data["last_inline_msg"] = sent.message_id
        return

# ================================================================
#  CALLBACK HANDLER
# ================================================================

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user; uid = str(user.id); adm = is_admin(uid); cb = query.data

    if is_blocked(uid) and not adm: return ConversationHandler.END
    if not adm:
        s = load_settings()
        if s["maintenance"]:
            await query.answer(s.get("maintenance_text","🔧"), show_alert=True)
            return ConversationHandler.END

    content = load_content()
    path    = context.user_data.get("path", [])

    # ── Arama sonucu dosya aç ────────────────────────
    if cb.startswith("srch|"):
        parts        = cb.split("|")
        path_encoded = parts[1]
        idx          = int(parts[2])
        file_path    = path_encoded.split("~~") if path_encoded else []
        folder       = get_folder(content, file_path)
        files        = folder.get("files", [])
        if idx >= len(files):
            await query.answer(L(uid,"file_notfound"), show_alert=True); return ConversationHandler.END
        f = files[idx]
        await _send_file(query.message, f, uid)
        log_user_message(user, "file_view", f.get("caption",""))
        return ConversationHandler.END

    # ── Klasördeki dosyayı aç ────────────────────────
    if cb.startswith("getfile|"):
        idx    = int(cb.split("|")[1])
        folder = get_folder(content, path)
        files  = folder.get("files",[])
        if idx >= len(files):
            await query.answer(L(uid,"file_notfound"), show_alert=True); return ConversationHandler.END
        f = files[idx]
        await _send_file(query.message, f, uid)
        log_user_message(user, "file_view", f.get("caption",""))
        return ConversationHandler.END

    # ── Sayfa navigasyonu ─────────────────────────────
    if cb == "noop":
        return ConversationHandler.END

    if cb.startswith("page|"):
        page = int(cb.split("|")[1])
        context.user_data["page"] = page
        await show_folder(query, context, path)
        return ConversationHandler.END

    # ── Navigasyon ────────────────────────────────────
    if cb.startswith("nav|"):
        action = cb.split("|")[1]
        if action == "back" and path: path.pop()
        elif action == "root":        path = []
        context.user_data["path"] = path
        context.user_data["page"] = 0
        await show_folder(query, context, path)
        return ConversationHandler.END

    if cb.startswith("open|"):
        path.append(cb.split("|",1)[1])
        context.user_data["path"] = path
        context.user_data["page"] = 0
        await show_folder(query, context, path)
        return ConversationHandler.END

    # ── Yönetim (sadece süper admin) ──────────────────
    if cb.startswith("mgmt|") and is_main_admin(uid):
        action = cb.split("|")[1]

        if action == "stats":
            u_d   = load_users()
            m_d   = load_messages()
            s     = load_settings()
            vc    = load_view_counts()
            total_msg   = sum(len(v) for v in m_d.values())
            total_views = sum((v.get("count",0) if isinstance(v,dict) else 0) for v in vc.values())

            def _cnt(node):
                c = 0
                for sub in node.get("folders",{}).values(): c += 1 + _cnt(sub)
                return c

            txt = (
                f"{TR['stats_title']}\n\n"
                f"👥 Kullanıcı: {len(u_d)}\n"
                f"💬 Toplam mesaj: {total_msg}\n"
                f"📁 Klasör: {_cnt(content)}\n"
                f"📎 Kök dosya: {len(content.get('files',[]))}\n"
                f"🔧 Bakım: {'Açık' if s['maintenance'] else 'Kapalı'}\n"
                f"{TR['total_views'].format(total_views)}"
            )

            # En çok görüntülenen 5 dosya
            top = sorted(
                [(v.get("name","?"), v.get("count",0)) for v in vc.values() if isinstance(v,dict)],
                key=lambda x: x[1], reverse=True)[:5]
            if top:
                txt += f"\n\n{TR['top_views']}"
                for i,(name,cnt) in enumerate(top,1):
                    txt += f"{i}. {name[:30]}{TR['view_count'].format(cnt)}\n"

            await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(TR["close"], callback_data="close")]]))
            return ConversationHandler.END

        if action == "users":
            u_d = load_users()
            if not u_d:
                await query.answer(TR["no_users"], show_alert=True); return ConversationHandler.END
            kb = []
            for uid_, u in list(u_d.items())[-50:]:
                if int(uid_) == ADMIN_ID: continue
                name = u.get("full_name") or u.get("first_name") or f"ID:{uid_}"
                un   = f" @{u['username']}" if u.get("username") else ""
                kb.append([InlineKeyboardButton(f"👤 {name}{un}", callback_data=f"user|info|{uid_}")])
            kb.append([InlineKeyboardButton(TR["close"], callback_data="close")])
            await query.edit_message_text(TR["user_list"], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "add_admin":
            context.user_data["action"] = "admin_add"
            await query.edit_message_text(TR["admin_enter_id"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_ADMIN_ID

        if action == "del_admin":
            admins = load_admins()
            if not admins:
                await query.answer(TR["no_admins"], show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🚫 {a}", callback_data=f"rem_admin|{a}")] for a in admins]
            kb.append([InlineKeyboardButton(TR["cancel"], callback_data="close")])
            await query.edit_message_text(TR["del_admin_lbl"], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "dm_user":
            u_d = load_users(); kb = []
            for uid_, u in list(u_d.items())[-30:]:
                if int(uid_) == ADMIN_ID: continue
                name = u.get("full_name") or u.get("first_name") or f"ID:{uid_}"
                un   = f" @{u['username']}" if u.get("username") else ""
                kb.append([InlineKeyboardButton(f"👤 {name}{un}", callback_data=f"dm_pick|{uid_}")])
            kb.append([InlineKeyboardButton(TR["dm_manual"], callback_data="dm_pick|manual")])
            kb.append([InlineKeyboardButton(TR["cancel"],    callback_data="close")])
            await query.edit_message_text(TR["dm_select"], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "broadcast":
            context.user_data["action"] = "broadcast"
            await query.edit_message_text(TR["broadcast_enter"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_BROADCAST_MSG

        if action == "poll":
            polls = load_polls()
            kb = [[InlineKeyboardButton(TR["poll_create"], callback_data="poll|create")]]
            if polls:
                kb.append([InlineKeyboardButton(TR["poll_results"], callback_data="poll|list_results"),
                           InlineKeyboardButton(TR["poll_delete"],  callback_data="poll|list_delete")])
            kb.append([InlineKeyboardButton(TR["close"], callback_data="close")])
            active = sum(1 for p in polls.values() if p.get("active"))
            txt = f"{TR['poll_panel']}\n\n📊 Toplam anket: {len(polls)}\n✅ Aktif: {active}"
            await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

    if cb.startswith("rem_admin|") and is_main_admin(uid):
        target = int(cb.split("|")[1])
        admins = load_admins()
        if target in admins: admins.remove(target); save_admins(admins)
        await query.answer(TR["admin_removed"].format(target), show_alert=True)
        if admins:
            kb = [[InlineKeyboardButton(f"🚫 {a}", callback_data=f"rem_admin|{a}")] for a in admins]
            kb.append([InlineKeyboardButton(TR["cancel"], callback_data="close")])
            await query.edit_message_text(TR["del_admin_lbl"], reply_markup=InlineKeyboardMarkup(kb))
        else:
            await query.edit_message_text(TR["no_admins"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["close"], callback_data="close")]]))
        return ConversationHandler.END

    if cb.startswith("dm_pick|") and is_main_admin(uid):
        target = cb.split("|")[1]
        if target == "manual":
            context.user_data["action"] = "dm_manual_id"
            await query.edit_message_text(TR["dm_enter_id"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_DM_USER_ID
        context.user_data["dm_target"] = target; context.user_data["action"] = "dm_msg"
        u    = load_users().get(target,{}); name = u.get("full_name") or u.get("first_name") or f"ID:{target}"
        await query.edit_message_text(TR["dm_enter_msg"].format(name),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
        return WAIT_DM_MSG

    if cb.startswith("dm_quick|") and is_main_admin(uid):
        target = cb.split("|")[1]
        context.user_data["dm_target"] = target; context.user_data["action"] = "dm_msg"
        u    = load_users().get(target,{}); name = u.get("full_name") or u.get("first_name") or f"ID:{target}"
        try:
            await query.edit_message_text(TR["dm_enter_msg"].format(name),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
        except Exception:
            await context.bot.send_message(uid, TR["dm_enter_msg"].format(name))
        return WAIT_DM_MSG

    # ── Kullanıcı detay (süper admin) ────────────────
    if cb.startswith("user|") and is_main_admin(uid):
        parts  = cb.split("|")
        action = parts[1]

        if action == "info":
            target = parts[2]; u_d = load_users(); m_d = load_messages()
            u = u_d.get(target,{}); msgs = m_d.get(target,[])
            name  = u.get("full_name") or u.get("first_name") or "—"
            un    = f"@{u['username']}" if u.get("username") else "—"
            last  = u.get("last_seen","—")
            blkd  = is_blocked(target)
            total = len(msgs)
            media_cnt = sum(1 for m in msgs if m["type"] not in ("msg","command","button","search"))
            txt_cnt   = sum(1 for m in msgs if m["type"] == "msg")
            btn_cnt   = sum(1 for m in msgs if m["type"] == "button")
            srch_cnt  = sum(1 for m in msgs if m["type"] == "search")
            fview_cnt = sum(1 for m in msgs if m["type"] == "file_view")
            ICONS = {"msg":"✍️","photo":"🖼","video":"🎥","document":"📄",
                     "audio":"🎵","voice":"🎙","animation":"🎞","sticker":"😊",
                     "command":"⚙️","file_view":"👁","button":"🔘","search":"🔍",
                     "video_note":"⭕"}
            # Son 20 aktivite
            recent = []
            for m in msgs[-20:]:
                icon = ICONS.get(m.get("type",""),"📨")
                t    = m.get("time","")[-8:]
                c    = m.get("content","")[:55]
                recent.append(f"  {icon} {t}  {c}")

            info = (
                f"╔══════════════════════╗\n"
                f"  👤  {name}\n"
                f"  🔗  {un}\n"
                f"  🆔  {target}\n"
                f"  📅  Son: {last}\n"
                f"  🚫  Engel: {'Evet' if blkd else 'Hayır'}\n"
                f"╠══════════════════════╣\n"
                f"  📊  Toplam aktivite: {total}\n"
                f"  ✍️   Mesaj: {txt_cnt}  |  🔘 Buton: {btn_cnt}\n"
                f"  🖼   Medya: {media_cnt}  |  🔍 Arama: {srch_cnt}\n"
                f"  👁   Görüntüleme: {fview_cnt}\n"
                f"╠══════════════════════╣\n"
                f"  🕐  Son {len(recent)} Aktivite:\n\n"
                + ("\n".join(recent) if recent else "  —") +
                f"\n╚══════════════════════╝"
            )
            media_files = [m for m in msgs if m.get("file_id") and
                           m["type"] in ("photo","video","document","audio","voice","animation")]
            kb = [
                [InlineKeyboardButton("💬 Mesaj Gönder", callback_data=f"dm_quick|{target}"),
                 InlineKeyboardButton("🚫 Engelle" if not blkd else "✅ Engeli Kaldır",
                                      callback_data=f"user|{'block' if not blkd else 'unblock'}|{target}")],
            ]
            if media_files:
                kb.insert(0,[InlineKeyboardButton(f"🖼 Medyaları Gönder ({len(media_files)})",
                                                  callback_data=f"user|sendmedia|{target}")])
            kb.append([InlineKeyboardButton("◀️ Kapat", callback_data="close")])
            await query.edit_message_text(info[:4000], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "sendmedia":
            target = parts[2]; m_d = load_messages()
            msgs   = m_d.get(target,[])
            media  = [m for m in msgs if m.get("file_id") and
                      m["type"] in ("photo","video","document","audio","voice","animation")]
            sent = fail = 0
            for m in media[-30:]:
                ftype=m["type"]; fid=m["file_id"]; cap=m.get("content","")
                try:
                    if   ftype=="photo":     await query.message.reply_photo(fid, caption=cap)
                    elif ftype=="video":     await query.message.reply_video(fid, caption=cap)
                    elif ftype=="document":  await query.message.reply_document(fid, caption=cap)
                    elif ftype=="audio":     await query.message.reply_audio(fid, caption=cap)
                    elif ftype=="voice":     await query.message.reply_voice(fid)
                    elif ftype=="animation": await query.message.reply_animation(fid, caption=cap)
                    sent += 1
                except Exception as e: logger.warning(f"Medya: {e}")
            await query.message.reply_text(TR["media_sent"].format(sent, len(media[-30:])))
            return ConversationHandler.END

        if action == "block":
            target=parts[2]; blocked=load_blocked()
            if int(target) not in blocked: blocked.append(int(target)); save_blocked(blocked)
            await query.answer(TR["blocked_ok"].format(target), show_alert=True)
            query.data=f"user|info|{target}"; return await callback(update, context)

        if action == "unblock":
            target=parts[2]; blocked=load_blocked()
            if int(target) in blocked: blocked.remove(int(target)); save_blocked(blocked)
            await query.answer(TR["unblocked_ok"].format(target), show_alert=True)
            query.data=f"user|info|{target}"; return await callback(update, context)

    # ── İçerik yönetimi ───────────────────────────────
    if cb.startswith("cnt|") and adm:
        action = cb.split("|")[1]; folder = get_folder(content, path)

        if action == "add_folder":
            context.user_data["action"] = "add_folder"
            await query.edit_message_text(L(uid,"enter_folder_name"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")]]))
            return WAIT_FOLDER

        if action == "add_file":
            context.user_data["action"] = "add_file"
            existing = folder_file_names(folder)
            if existing:
                file_list = "\n".join(f"  • {n}" for n in existing[:20])
                prompt = L(uid,"add_file_prompt").format(file_list)
            else:
                prompt = L(uid,"add_file_prompt_empty")
            await query.edit_message_text(prompt,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")]]))
            return WAIT_FILE

        # Sil/Düzenle — SADECE süper admin
        if not is_main_admin(uid):
            await query.answer("⛔", show_alert=True); return ConversationHandler.END

        if action == "del_folder":
            folds = list(folder.get("folders",{}).keys())
            if not folds:
                await query.answer(L(uid,"no_folders"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🗑 {f}", callback_data=f"do|confirm_del_folder|{f}")] for f in folds]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"del_folder_select"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "rename_folder":
            folds = list(folder.get("folders",{}).keys())
            if not folds:
                await query.answer(L(uid,"no_folders"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"✏️ {f}", callback_data=f"do|pick_folder|{f}")] for f in folds]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"rename_folder_select"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "del_file":
            files = folder.get("files",[])
            if not files:
                await query.answer(L(uid,"no_files"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🗑 {f.get('caption','?')}", callback_data=f"do|confirm_del_file|{i}")]
                  for i,f in enumerate(files)]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"del_file_select"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "rename_file":
            files = folder.get("files",[])
            if not files:
                await query.answer(L(uid,"no_files"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"✏️ {f.get('caption','?')}", callback_data=f"do|pick_file|{i}")]
                  for i,f in enumerate(files)]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"rename_file_select"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

    # ── Do (sadece süper admin) ───────────────────────
    if cb.startswith("do|") and is_main_admin(uid):
        parts  = cb.split("|",2); action = parts[1]; arg = parts[2] if len(parts)>2 else ""
        folder = get_folder(content, path)

        # ── Silme Onayları ──────────────────────────
        if action == "confirm_del_folder":
            kb = [
                [InlineKeyboardButton(TR["confirm_yes"], callback_data=f"do|del_folder|{arg}"),
                 InlineKeyboardButton(TR["confirm_no"],  callback_data="nav|root")]
            ]
            await query.edit_message_text(
                L(uid,"del_folder_confirm").format(arg),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "confirm_del_file":
            idx   = int(arg)
            files = folder.get("files",[])
            if idx >= len(files):
                await query.answer(L(uid,"file_notfound"), show_alert=True); return ConversationHandler.END
            fname = files[idx].get("caption","?")
            kb = [
                [InlineKeyboardButton(TR["confirm_yes"], callback_data=f"do|del_file|{idx}"),
                 InlineKeyboardButton(TR["confirm_no"],  callback_data="nav|root")]
            ]
            await query.edit_message_text(
                L(uid,"del_file_confirm").format(fname),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        # ── Gerçek Silme ────────────────────────────
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
            await query.edit_message_text(TR["set_name_prompt"].format(s.get("bot_name","—")),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_BOT_NAME

        if action == "welcome":
            context.user_data["action"] = "set_welcome"
            await query.edit_message_text(TR["set_welcome_prompt"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_WELCOME

        if action == "photo":
            context.user_data["action"] = "set_photo"
            await query.edit_message_text(TR["set_photo_prompt"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_PHOTO

        if action == "blocked":
            blocked = load_blocked()
            txt  = TR["blocked_list"].format(len(blocked)) + "\n\n"
            txt += "\n".join(f"🆔 {b}" for b in blocked) if blocked else TR["no_blocked"]
            await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(TR["close"], callback_data="close")]]))
            return ConversationHandler.END

        if action == "btn_mgmt":
            s     = load_settings()
            ub    = s.get("user_buttons", {})
            track = s.get("track_activity", True)
            btn_defs = [
                ("btn_search", "🔍 Arama Butonu"),
                ("btn_help",   "💬 Mesaj Gönder Butonu"),
                
            ]
            kb = []
            for key, label in btn_defs:
                icon = "✅" if ub.get(key, True) else "❌"
                kb.append([InlineKeyboardButton(f"{icon} {label}", callback_data=f"set|toggle_btn|{key}")])
            track_icon = "✅" if track else "❌"
            kb.append([InlineKeyboardButton(f"{track_icon} 👁 Aktivite Takibi", callback_data="set|toggle_track")])
            kb.append([InlineKeyboardButton(TR["close"], callback_data="close")])
            await query.edit_message_text(
                TR["btn_mgmt_title"] + "\n\n✅ = Açık  |  ❌ = Kapalı\n"
                "Kullanıcıların göreceği butonları buradan yönet.",
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "toggle_track":
            s = load_settings()
            s["track_activity"] = not s.get("track_activity", True)
            save_settings(s)
            ub    = s.get("user_buttons", {})
            track = s["track_activity"]
            btn_defs = [
                ("btn_search", "🔍 Arama Butonu"),
                ("btn_help",   "💬 Mesaj Gönder Butonu"),
                
            ]
            kb = []
            for key, label in btn_defs:
                icon = "✅" if ub.get(key, True) else "❌"
                kb.append([InlineKeyboardButton(f"{icon} {label}", callback_data=f"set|toggle_btn|{key}")])
            track_icon = "✅" if track else "❌"
            kb.append([InlineKeyboardButton(f"{track_icon} 👁 Aktivite Takibi", callback_data="set|toggle_track")])
            kb.append([InlineKeyboardButton(TR["close"], callback_data="close")])
            status = "✅ AÇIK" if track else "❌ KAPALI"
            await query.edit_message_text(
                TR["btn_mgmt_title"] + f"\n\n👁 Aktivite Takibi → {status}\n\n✅ = Açık  |  ❌ = Kapalı",
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "toggle_btn":
            key = cb.split("|")[2]
            s   = load_settings()
            ub  = s.setdefault("user_buttons", {"btn_search": True, "btn_help": True})
            ub[key] = not ub.get(key, True)
            save_settings(s)
            track    = s.get("track_activity", True)
            btn_defs = [
                ("btn_search", "🔍 Arama Butonu"),
                ("btn_help",   "💬 Mesaj Gönder Butonu"),
                
            ]
            kb = []
            for k, label in btn_defs:
                icon = "✅" if ub.get(k, True) else "❌"
                kb.append([InlineKeyboardButton(f"{icon} {label}", callback_data=f"set|toggle_btn|{k}")])
            track_icon = "✅" if track else "❌"
            kb.append([InlineKeyboardButton(f"{track_icon} 👁 Aktivite Takibi", callback_data="set|toggle_track")])
            kb.append([InlineKeyboardButton(TR["close"], callback_data="close")])
            await query.edit_message_text(
                TR["btn_mgmt_title"] + "\n\n✅ = Açık  |  ❌ = Kapalı",
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

    if cb == "close":
        try: await query.delete_message()
        except: pass
        return ConversationHandler.END

    # ── Anket işlemleri ───────────────────────────────
    if cb.startswith("poll|") and is_main_admin(uid):
        action = cb.split("|")[1]

        if action == "create":
            kb = [
                [InlineKeyboardButton(TR["poll_type_choice"], callback_data="poll|type|choice")],
                [InlineKeyboardButton(TR["poll_type_open"],   callback_data="poll|type|open")],
                [InlineKeyboardButton(TR["cancel"],           callback_data="close")],
            ]
            await query.edit_message_text(
                TR["poll_type_select"],
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "type":
            poll_type = cb.split("|")[2]  # "choice" veya "open"
            context.user_data["poll_type"]   = poll_type
            context.user_data["action"]      = "poll_question"
            await query.edit_message_text(
                TR["poll_enter_q"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_POLL_QUESTION

        if action == "list_results":
            polls = load_polls()
            if not polls:
                await query.answer(TR["poll_no_polls"], show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"📊 {p['question'][:40]}", callback_data=f"poll|show_result|{pid}")]
                  for pid, p in polls.items()]
            kb.append([InlineKeyboardButton(TR["close"], callback_data="close")])
            await query.edit_message_text(TR["poll_select"], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "show_result":
            poll_id = cb.split("|")[2]
            polls   = load_polls()
            poll    = polls.get(poll_id)
            if not poll:
                await query.answer("Anket bulunamadı.", show_alert=True); return ConversationHandler.END

            poll_type = poll.get("type", "choice")

            if poll_type == "open":
                # Açık uçlu — cevapları göster
                answers = poll.get("answers", {})
                lines   = [
                    f"✍️ Açık Uçlu Anket Sonuçları",
                    f"❓ {poll['question']}",
                    f"👥 Toplam Cevap: {len(answers)}",
                    f"{'─'*28}",
                ]
                if answers:
                    for a in answers.values():
                        lines.append(
                            f"\n👤 {a['name']} {a.get('username','')}\n"
                            f"💬 {a['answer']}\n"
                            f"🕐 {a['time'][-5:]}"
                        )
                else:
                    lines.append("Henüz cevap yok.")
                kb = [[InlineKeyboardButton(TR["close"], callback_data="close")]]
                await query.edit_message_text("\n".join(lines)[:4000], reply_markup=InlineKeyboardMarkup(kb))
            else:
                txt = build_poll_results_text(poll, uid, show_voters=False)
                kb  = [
                    [InlineKeyboardButton("👥 Kim Ne Seçti?", callback_data=f"poll|voter_detail|{poll_id}")],
                    [InlineKeyboardButton(TR["close"], callback_data="close")],
                ]
                await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "voter_detail":
            poll_id = cb.split("|")[2]
            polls   = load_polls()
            poll    = polls.get(poll_id)
            if not poll:
                await query.answer("Anket bulunamadı.", show_alert=True); return ConversationHandler.END
            txt = build_poll_results_text(poll, uid, show_voters=True)
            kb  = [
                [InlineKeyboardButton("💬 Yorumlar", callback_data=f"poll|comments|{poll_id}")],
                [InlineKeyboardButton("📊 Genel Sonuç", callback_data=f"poll|show_result|{poll_id}")],
                [InlineKeyboardButton(TR["close"], callback_data="close")],
            ]
            await query.edit_message_text(txt[:4000], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "comments":
            poll_id  = cb.split("|")[2]
            polls    = load_polls()
            poll     = polls.get(poll_id)
            if not poll:
                await query.answer("Anket bulunamadı.", show_alert=True); return ConversationHandler.END
            comments = poll.get("comments", {})
            if not comments:
                await query.answer(TR["poll_no_comments"], show_alert=True)
                return ConversationHandler.END
            lines = [f"💬 Yorumlar — {poll['question'][:40]}\n{'─'*28}"]
            for c in comments.values():
                name = c.get("name","?")
                un   = f" {c['username']}" if c.get("username") else ""
                vote = c.get("vote","—")
                text_c = c.get("comment","")
                time_c = c.get("time","")[-5:]
                lines.append(
                    f"\n👤 {name}{un}\n"
                    f"🗳 {vote}\n"
                    f"💬 {text_c}\n"
                    f"🕐 {time_c}"
                )
            kb = [
                [InlineKeyboardButton("◀️ Geri", callback_data=f"poll|voter_detail|{poll_id}")],
                [InlineKeyboardButton(TR["close"], callback_data="close")],
            ]
            await query.edit_message_text("\n".join(lines)[:4000], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "list_delete":
            polls = load_polls()
            if not polls:
                await query.answer(TR["poll_no_polls"], show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🗑 {p['question'][:40]}", callback_data=f"poll|confirm_delete|{pid}")]
                  for pid, p in polls.items()]
            kb.append([InlineKeyboardButton(TR["close"], callback_data="close")])
            await query.edit_message_text(TR["poll_select"], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "confirm_delete":
            poll_id = cb.split("|")[2]
            polls   = load_polls()
            if poll_id in polls:
                del polls[poll_id]
                save_polls(polls)
            await query.answer(TR["poll_deleted"], show_alert=True)
            # Panele dön
            kb = [[InlineKeyboardButton(TR["poll_create"], callback_data="poll|create")]]
            if polls:
                kb.append([InlineKeyboardButton(TR["poll_results"], callback_data="poll|list_results"),
                           InlineKeyboardButton(TR["poll_delete"],  callback_data="poll|list_delete")])
            kb.append([InlineKeyboardButton(TR["close"], callback_data="close")])
            active = sum(1 for p in polls.values() if p.get("active"))
            txt = f"{TR['poll_panel']}\n\n📊 Toplam anket: {len(polls)}\n✅ Aktif: {active}"
            await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "send":
            poll_id   = cb.split("|")[2]
            polls     = load_polls()
            poll      = polls.get(poll_id)
            if not poll:
                await query.answer("Anket bulunamadı.", show_alert=True); return ConversationHandler.END
            users     = load_users()
            success = fail = 0
            q         = poll["question"]
            poll_type = poll.get("type", "choice")

            for uid_, _ in users.items():
                if int(uid_) == ADMIN_ID or is_blocked(uid_): continue
                try:
                    if poll_type == "open":
                        # Açık uçlu — "Cevapla" butonu
                        kb_u = [[InlineKeyboardButton(
                            "✍️ أكتب إجابتك" if not is_main_admin(uid_) else "✍️ Cevapla",
                            callback_data=f"open_ans|{poll_id}")]]
                        await context.bot.send_message(
                            int(uid_),
                            f"✍️ سؤال مفتوح!\n\n❓ {q}",
                            reply_markup=InlineKeyboardMarkup(kb_u))
                    else:
                        opts   = poll["options"]
                        poll_kb = [[InlineKeyboardButton(f"  {o}  ", callback_data=f"vote|{poll_id}|{i}")]
                                   for i, o in enumerate(opts)]
                        await context.bot.send_message(
                            int(uid_),
                            f"📊 استطلاع جديد!\n\n❓ {q}",
                            reply_markup=InlineKeyboardMarkup(poll_kb))
                    success += 1
                except: fail += 1

            poll["active"] = True
            save_polls(polls)
            await query.edit_message_text(
                TR["poll_sent"].format(s=success, f=fail),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["close"], callback_data="close")]]))
            return ConversationHandler.END

    # ── Açık uçlu anket cevap butonu ─────────────────
    if cb.startswith("open_ans|"):
        poll_id = cb.split("|")[1]
        polls   = load_polls()
        poll    = polls.get(poll_id)
        if not poll or not poll.get("active"):
            await query.answer(AR["poll_closed"], show_alert=True); return ConversationHandler.END
        answers = poll.get("answers", {})
        if uid in answers:
            await query.answer(AR["poll_already_voted"], show_alert=True); return ConversationHandler.END
        context.user_data["open_poll_id"] = poll_id
        context.user_data["action"]       = "open_poll_answer"
        await query.message.reply_text(
            f"✍️ {poll['question']}\n\n{'اكتب إجابتك:' if not is_main_admin(uid) else 'Cevabını yaz:'}")
        return WAIT_POLL_COMMENT

    # ── Kullanıcı oy kullanma ─────────────────────────
    if cb.startswith("vote|"):
        parts   = cb.split("|")
        poll_id = parts[1]
        opt_idx = int(parts[2])
        polls   = load_polls()
        poll    = polls.get(poll_id)
        if not poll:
            await query.answer(TR["poll_closed"] if is_main_admin(uid) else AR["poll_closed"],
                               show_alert=True); return ConversationHandler.END
        if not poll.get("active"):
            await query.answer(AR["poll_closed"], show_alert=True); return ConversationHandler.END
        votes = poll.setdefault("votes", {})
        if uid in votes:
            await query.answer(AR["poll_already_voted"], show_alert=True); return ConversationHandler.END

        # Oyu kaydet
        votes[uid] = poll["options"][opt_idx]
        save_polls(polls)
        await query.answer(AR["poll_voted"], show_alert=True)

        # Anket butonlarını güncel oy sayılarıyla güncelle
        opts   = poll["options"]
        total  = len(votes)
        counts = {o: 0 for o in opts}
        for v in votes.values():
            if v in counts: counts[v] += 1

        poll_kb = []
        for i, o in enumerate(opts):
            pct   = int(counts[o] / total * 100) if total else 0
            label = f"✅ {o}  {pct}%" if i == opt_idx else f"  {o}  {pct}%"
            poll_kb.append([InlineKeyboardButton(label, callback_data=f"vote|{poll_id}|{i}")])
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(poll_kb))
        except: pass

        # Yorum iste — isteğe bağlı
        context.user_data["poll_comment_id"] = poll_id
        context.user_data["action"] = "poll_comment"
        await query.message.reply_text(L(uid, "poll_comment_prompt"))
        return WAIT_POLL_COMMENT

    return ConversationHandler.END

# ================================================================
#  METİN GİRİŞ
# ================================================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user   = update.effective_user; uid = str(user.id)
    text   = (update.message.text or "").strip()
    register_user(user)

    action = context.user_data.get("action","")

    # ── Arama — herkes ──────────────────────────────
    if action == "search":
        context.user_data.pop("action",None)
        if not is_admin(uid):
            log_user_message(user, "search", text)
        await do_search(update.message, uid, text)
        return ConversationHandler.END

    # ── Kullanıcıdan admin'e mesaj ──────────────────
    if action == "user_msg_to_admin" and not is_admin(uid):
        log_user_message(user, "msg", text)
        await update.message.reply_text(L(uid,"msg_to_admin_sent"))
        context.user_data.pop("action",None)
        return ConversationHandler.END

    # ── Açık uçlu anket cevabı ────────────────────────
    if action == "open_poll_answer" and not is_admin(uid):
        poll_id = context.user_data.pop("open_poll_id", None)
        context.user_data.pop("action", None)
        if poll_id and text:
            polls = load_polls()
            poll  = polls.get(poll_id)
            if poll:
                users_d = load_users()
                u       = users_d.get(uid, {})
                name    = u.get("full_name") or u.get("first_name") or f"ID:{uid}"
                un      = f"@{u['username']}" if u.get("username") else ""
                poll.setdefault("answers", {})[uid] = {
                    "name":    name,
                    "username": un,
                    "answer":  text[:500],
                    "time":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                save_polls(polls)
                await update.message.reply_text(L(uid, "poll_comment_saved"))
        return ConversationHandler.END

    # ── Anket yorumu (kullanıcıdan) ───────────────────
    if action == "poll_comment" and not is_admin(uid):
        poll_id = context.user_data.pop("poll_comment_id", None)
        context.user_data.pop("action", None)
        if poll_id:
            polls = load_polls()
            poll  = polls.get(poll_id)
            if poll:
                # Yorumu kaydet: {uid: {"vote": "seçenek", "comment": "yorum", "time": ...}}
                comments = poll.setdefault("comments", {})
                users_d  = load_users()
                u        = users_d.get(uid, {})
                name     = u.get("full_name") or u.get("first_name") or f"ID:{uid}"
                un       = f"@{u['username']}" if u.get("username") else ""
                if text.strip() == "/skip":
                    await update.message.reply_text(L(uid, "poll_comment_skip"))
                else:
                    comments[uid] = {
                        "name":    name,
                        "username": un,
                        "vote":    poll.get("votes", {}).get(uid, "—"),
                        "comment": text[:300],
                        "time":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    save_polls(polls)
                    await update.message.reply_text(L(uid, "poll_comment_saved"))
        return ConversationHandler.END

    # ── Anket sorusu ──────────────────────────────────
    if action == "poll_question" and is_main_admin(uid):
        if not text:
            await update.message.reply_text(TR["poll_enter_q"]); return WAIT_POLL_QUESTION
        context.user_data["poll_question"] = text
        poll_type = context.user_data.get("poll_type", "choice")

        if poll_type == "open":
            # Açık uçlu — seçenek istemiyoruz, direkt kaydet
            q       = text
            poll_id = make_poll_id()
            polls   = load_polls()
            polls[poll_id] = {
                "question": q, "type": "open",
                "options": [], "votes": {}, "answers": {}, "active": False
            }
            save_polls(polls)
            kb = [
                [InlineKeyboardButton(TR["poll_send_btn"],   callback_data=f"poll|send|{poll_id}")],
                [InlineKeyboardButton(TR["poll_cancel_btn"], callback_data="close")],
            ]
            await update.message.reply_text(
                f"✍️ Açık Uçlu Anket Önizleme:\n\n❓ {q}\n\nKullanıcılar yazılı cevap verecek.\n\nGönderilsin mi?",
                reply_markup=InlineKeyboardMarkup(kb))
            context.user_data.pop("action", None)
            context.user_data.pop("poll_question", None)
            context.user_data.pop("poll_type", None)
            return ConversationHandler.END
        else:
            # Çoktan seçmeli — seçenek iste
            context.user_data["action"] = "poll_options"
            await update.message.reply_text(TR["poll_enter_opts"])
            return WAIT_POLL_OPTIONS

    # ── Anket seçenekleri ─────────────────────────────
    if action == "poll_options" and is_main_admin(uid):
        opts = [o.strip() for o in text.split("\n") if o.strip()][:6]
        if len(opts) < 2:
            await update.message.reply_text("❌ En az 2 seçenek girin!"); return WAIT_POLL_OPTIONS
        q       = context.user_data.get("poll_question", "?")
        poll_id = make_poll_id()
        # Anketi kaydet (henüz gönderilmedi)
        polls = load_polls()
        polls[poll_id] = {"question": q, "options": opts, "votes": {}, "active": False}
        save_polls(polls)
        opts_text = "\n".join(f"  {i+1}. {o}" for i, o in enumerate(opts))
        kb = [
            [InlineKeyboardButton(TR["poll_send_btn"],   callback_data=f"poll|send|{poll_id}")],
            [InlineKeyboardButton(TR["poll_cancel_btn"], callback_data="close")],
        ]
        await update.message.reply_text(
            TR["poll_preview"].format(q=q, opts=opts_text),
            reply_markup=InlineKeyboardMarkup(kb))
        context.user_data.pop("action", None)
        context.user_data.pop("poll_question", None)
        return ConversationHandler.END

    # ── Admin değilse: sadece action varsa işle, yoksa handle_any_message'a bırak ──
    if not is_admin(uid):
        # user_msg_to_admin zaten yukarıda handle edildi
        # Diğer durumlar handle_any_message'a düşsün (AI sohbet için)
        return ConversationHandler.END

    # ── Admin işlemleri ──────────────────────────────
    content = load_content(); path = context.user_data.get("path",[]); folder = get_folder(content,path)

    if action == "admin_add" and is_main_admin(uid):
        try: new_id = int(text)
        except: await update.message.reply_text(TR["invalid_id"]); return WAIT_ADMIN_ID
        admins = load_admins()
        if new_id in admins or new_id == ADMIN_ID:
            await update.message.reply_text(TR["admin_exists"])
        else:
            admins.append(new_id); save_admins(admins)
            await update.message.reply_text(TR["admin_added"].format(new_id))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "dm_manual_id" and is_main_admin(uid):
        try: target_id = str(int(text))
        except: await update.message.reply_text(TR["invalid_id"]); return WAIT_DM_USER_ID
        context.user_data["dm_target"] = target_id; context.user_data["action"] = "dm_msg"
        await update.message.reply_text(TR["dm_enter_msg"].format(target_id))
        return WAIT_DM_MSG

    if action == "dm_msg" and is_main_admin(uid):
        target = context.user_data.get("dm_target")
        if not target: await update.message.reply_text(TR["dm_no_target"]); return ConversationHandler.END
        try:
            await context.bot.send_message(int(target), TR["dm_prefix"].format(text))
            await update.message.reply_text(TR["dm_sent"].format(target))
        except Exception as e:
            await update.message.reply_text(TR["dm_fail"].format(e))
        context.user_data.pop("action",None); context.user_data.pop("dm_target",None)
        return ConversationHandler.END

    if action == "broadcast" and is_main_admin(uid):
        users = load_users(); success = fail = 0
        for uid_,u in users.items():
            if int(uid_) == ADMIN_ID or is_blocked(uid_): continue
            try: await context.bot.send_message(int(uid_), f"📢\n\n{text}"); success += 1
            except: fail += 1
        await update.message.reply_text(TR["broadcast_done"].format(success,fail))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "set_name" and is_main_admin(uid):
        if not text: await update.message.reply_text(TR["folder_empty"]); return WAIT_BOT_NAME
        s = load_settings(); s["bot_name"] = text; save_settings(s)
        await update.message.reply_text(TR["set_name_ok"].format(text))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "set_welcome" and is_main_admin(uid):
        s = load_settings(); s["welcome_msg"] = text; save_settings(s)
        await update.message.reply_text(TR["set_welcome_ok"])
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "add_folder":
        if not text: await update.message.reply_text(L(uid,"folder_empty")); return WAIT_FOLDER
        if text in folder.get("folders",{}):
            await update.message.reply_text(L(uid,"folder_exists").format(text)); return WAIT_FOLDER
        folder.setdefault("folders",{})[text] = {"folders":{},"files":[]}; save_content(content)
        kb = [[InlineKeyboardButton(L(uid,"close"), callback_data="nav|root")]]
        await update.message.reply_text(
            L(uid,"folder_added").format(text) + "\n\n📁 " +
            ("Başka klasör adı yazabilirsiniz. Bitirmek için ❌ İptal'e basın." if is_main_admin(uid) else
             "اكتب اسم مجلد آخر. اضغط ❌ إلغاء للإنهاء."),
            reply_markup=InlineKeyboardMarkup(kb))
        return WAIT_FOLDER  # art arda klasör eklemek için WAIT_FOLDER'da kal

    if action == "rename_folder" and is_main_admin(uid):
        old = context.user_data.get("target","")
        if not text: await update.message.reply_text(L(uid,"folder_empty")); return WAIT_RENAME_FOLDER
        if text in folder.get("folders",{}):
            await update.message.reply_text(L(uid,"folder_exists").format(text)); return WAIT_RENAME_FOLDER
        if old in folder.get("folders",{}):
            folder["folders"][text] = folder["folders"].pop(old); save_content(content)
        await update.message.reply_text(L(uid,"folder_renamed").format(old,text))
        context.user_data.pop("action",None); context.user_data.pop("target",None)
        return ConversationHandler.END

    if action == "rename_file" and is_main_admin(uid):
        idx = context.user_data.get("target",0); files = folder.get("files",[])
        if not text: await update.message.reply_text(L(uid,"folder_empty")); return WAIT_RENAME_FILE
        if 0 <= idx < len(files):
            files[idx]["caption"] = text; files[idx]["name"] = text; save_content(content)
        await update.message.reply_text(L(uid,"file_renamed").format(text))
        context.user_data.pop("action",None); context.user_data.pop("target",None)
        return ConversationHandler.END

    if action == "add_file":
        if text.startswith("http://") or text.startswith("https://"):
            fobj    = {"type":"link","url":text,"caption":text,"name":text}
            caption = text
        else:
            fobj    = {"type":"text","caption":text,"name":text}
            caption = text
        existing = folder_file_names(folder)
        if caption in existing:
            await update.message.reply_text(L(uid,"file_exists_warn").format(caption[:40]))
        folder.setdefault("files",[]).append(fobj); save_content(content)
        kb = [[InlineKeyboardButton(L(uid,"close"), callback_data="nav|root")]]
        await update.message.reply_text(
            L(uid,"file_added").format(caption[:50]) +
            "\n\n📎 " + ("Başka dosya/link yazabilirsiniz. Bitirmek için ❌ İptal'e basın." if is_main_admin(uid) else
                        "يمكنك إرسال ملف آخر. اضغط ❌ إلغاء للإنهاء."),
            reply_markup=InlineKeyboardMarkup(kb))
        return WAIT_FILE  # art arda ekleme için WAIT_FILE'da kal

    return ConversationHandler.END

# ================================================================
#  MEDYA GİRİŞ
# ================================================================

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user; uid = str(user.id); msg = update.message
    register_user(user)

    if not is_main_admin(uid):
        if is_blocked(uid): return ConversationHandler.END
        s = load_settings()
        if s["maintenance"] and not is_admin(uid):
            await msg.reply_text(s.get("maintenance_text","🔧")); return ConversationHandler.END
        if   msg.photo:
            fid = msg.photo[-1].file_id; cap = msg.caption or "(photo)"
            log_user_message(user,"photo", cap, file_id=fid)
        elif msg.video:
            fid = msg.video.file_id; cap = msg.caption or msg.video.file_name or "(video)"
            log_user_message(user,"video", cap, file_id=fid)
        elif msg.document:
            fid = msg.document.file_id; cap = msg.document.file_name or "(doc)"
            log_user_message(user,"document", cap, file_id=fid)
        elif msg.audio:
            fid = msg.audio.file_id; cap = msg.audio.file_name or "(audio)"
            log_user_message(user,"audio", cap, file_id=fid)
        elif msg.voice:
            fid = msg.voice.file_id
            log_user_message(user,"voice","(voice)", file_id=fid)
        elif msg.animation:
            fid = msg.animation.file_id
            log_user_message(user,"animation","(gif)", file_id=fid)
        elif msg.sticker:
            fid = msg.sticker.file_id; emoji = msg.sticker.emoji or "(sticker)"
            log_user_message(user,"sticker", emoji, file_id=fid)
        return ConversationHandler.END

    action = context.user_data.get("action","")

    if action == "broadcast" and is_main_admin(uid):
        users = load_users(); success = fail = 0; cap_text = msg.caption or ""
        for uid_,u in users.items():
            if int(uid_) == ADMIN_ID or is_blocked(uid_): continue
            try:
                if   msg.photo:     await context.bot.send_photo(int(uid_),    msg.photo[-1].file_id, caption=cap_text)
                elif msg.video:     await context.bot.send_video(int(uid_),    msg.video.file_id,     caption=cap_text)
                elif msg.document:  await context.bot.send_document(int(uid_), msg.document.file_id,  caption=cap_text)
                elif msg.audio:     await context.bot.send_audio(int(uid_),    msg.audio.file_id,     caption=cap_text)
                elif msg.voice:     await context.bot.send_voice(int(uid_),    msg.voice.file_id)
                elif msg.animation: await context.bot.send_animation(int(uid_),msg.animation.file_id, caption=cap_text)
                success += 1
            except: fail += 1
        await msg.reply_text(TR["broadcast_done"].format(success,fail))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "dm_msg" and is_main_admin(uid):
        target = context.user_data.get("dm_target"); cap_text = msg.caption or ""
        if not target: await msg.reply_text(TR["dm_no_target"]); return ConversationHandler.END
        try:
            if   msg.photo:     await context.bot.send_photo(int(target),    msg.photo[-1].file_id, caption=cap_text)
            elif msg.video:     await context.bot.send_video(int(target),    msg.video.file_id,     caption=cap_text)
            elif msg.document:  await context.bot.send_document(int(target), msg.document.file_id,  caption=cap_text)
            elif msg.audio:     await context.bot.send_audio(int(target),    msg.audio.file_id,     caption=cap_text)
            elif msg.voice:     await context.bot.send_voice(int(target),    msg.voice.file_id)
            elif msg.animation: await context.bot.send_animation(int(target),msg.animation.file_id, caption=cap_text)
            await msg.reply_text(TR["dm_sent"].format(target))
        except Exception as e:
            await msg.reply_text(TR["dm_fail"].format(e))
        context.user_data.pop("action",None); context.user_data.pop("dm_target",None)
        return ConversationHandler.END

    if action == "set_photo" and is_main_admin(uid):
        if not msg.photo:
            await msg.reply_text(TR["set_photo_fail"]); return WAIT_PHOTO
        fid = msg.photo[-1].file_id
        s = load_settings(); s["bot_photo_id"] = fid; save_settings(s)
        await msg.reply_text(TR["set_photo_ok"])
        context.user_data.pop("action",None); return ConversationHandler.END

    if action != "add_file": return ConversationHandler.END

    content = load_content(); path = context.user_data.get("path",[]); folder = get_folder(content,path)
    now  = datetime.now().strftime("%Y%m%d%H%M%S")
    cap  = msg.caption or ""
    fobj = None

    # ── Medya grubu (aynı anda birden fazla dosya) ───
    media_group_id = msg.media_group_id
    if media_group_id:
        # Grubun dosyalarını geçici olarak topla
        group_key = f"mg_{media_group_id}"
        if group_key not in context.user_data:
            context.user_data[group_key] = []
            # 2 saniye sonra hepsini kaydet
            async def _flush_group(gid, gkey, p, c):
                import asyncio
                await asyncio.sleep(2)
                items   = context.user_data.pop(gkey, [])
                if not items: return
                ct      = load_content()
                fld     = get_folder(ct, p)
                added   = 0
                for item in items:
                    fld.setdefault("files", []).append(item)
                    added += 1
                save_content(ct)
                kb = [[InlineKeyboardButton(L(str(user.id),"close"), callback_data="nav|root")]]
                try:
                    await context.bot.send_message(
                        user.id,
                        f"✅ {added} dosya eklendi!\n\n📎 " +
                        ("Daha fazla dosya gönderebilirsiniz." if is_main_admin(str(user.id)) else
                         "يمكنك إرسال المزيد من الملفات."),
                        reply_markup=InlineKeyboardMarkup(kb))
                except Exception as e:
                    logger.error(f"Grup flush hatası: {e}")
            import asyncio
            asyncio.create_task(_flush_group(media_group_id, group_key, path, content))

    try:
        if msg.photo:
            fid = msg.photo[-1].file_id; local = await download_file(context,fid,f"photo_{now}.jpg")
            fobj = {"type":"photo","file_id":fid,"caption":cap or f"photo_{now}","name":f"photo_{now}.jpg",
                    **({"local_path":local} if local else {})}
        elif msg.video:
            fname = msg.video.file_name or f"video_{now}.mp4"; fid = msg.video.file_id
            local = await download_file(context,fid,fname)
            fobj = {"type":"video","file_id":fid,"caption":cap or fname,"name":fname,
                    **({"local_path":local} if local else {})}
        elif msg.animation:
            fid = msg.animation.file_id; local = await download_file(context,fid,f"gif_{now}.gif")
            fobj = {"type":"animation","file_id":fid,"caption":cap or "GIF","name":f"gif_{now}.gif",
                    **({"local_path":local} if local else {})}
        elif msg.document:
            fname = msg.document.file_name or f"doc_{now}"; fid = msg.document.file_id
            local = await download_file(context,fid,fname)
            fobj = {"type":"document","file_id":fid,"caption":cap or fname,"name":fname,
                    **({"local_path":local} if local else {})}
        elif msg.audio:
            fname = msg.audio.file_name or f"audio_{now}.mp3"; fid = msg.audio.file_id
            local = await download_file(context,fid,fname)
            fobj = {"type":"audio","file_id":fid,"caption":cap or msg.audio.title or fname,"name":fname,
                    **({"local_path":local} if local else {})}
        elif msg.voice:
            fid = msg.voice.file_id; local = await download_file(context,fid,f"voice_{now}.ogg")
            fobj = {"type":"voice","file_id":fid,"caption":cap or "voice","name":f"voice_{now}.ogg",
                    **({"local_path":local} if local else {})}
    except Exception as e:
        logger.error(f"handle_media hata: {e}")

    if fobj:
        # Medya grubuysa listeye ekle, flush_group kaydedecek
        if media_group_id:
            context.user_data[f"mg_{media_group_id}"].append(fobj)
            return WAIT_FILE  # sessizce bekle, flush sonunda bildirim gönderir

        # Tekli dosya — direkt kaydet
        existing = folder_file_names(folder)
        fname_check = fobj.get("caption","")
        if fname_check and fname_check in existing:
            await msg.reply_text(L(uid,"file_exists_warn").format(fname_check[:40]))
        folder.setdefault("files",[]).append(fobj); save_content(content)
        kb = [[InlineKeyboardButton(L(uid,"close"), callback_data="nav|root")]]
        await msg.reply_text(
            L(uid,"file_added").format(fobj["caption"]) +
            "\n\n📎 " + ("Başka dosya gönderebilirsiniz. Bitirmek için ❌ İptal'e basın." if is_main_admin(uid) else
                        "يمكنك إرسال ملف آخر. اضغط ❌ إلغاء للإنهاء."),
            reply_markup=InlineKeyboardMarkup(kb))
        return WAIT_FILE
    else:
        await msg.reply_text(L(uid,"unsupported"))
    return ConversationHandler.END

# ================================================================
#  GENEL MESAJ HANDLER — fallback log + güvenlik
# ================================================================

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user; uid = str(user.id); msg = update.message
    text = (msg.text or "").strip()

    if text in ALL_BTNS: return

    register_user(user)
    if is_blocked(uid): return

    s = load_settings()
    if s["maintenance"] and not is_admin(uid):
        await msg.reply_text(s.get("maintenance_text","🔧")); return

    if is_main_admin(uid): return  # sadece süper admin hariç
    if text:
        log_user_message(user, "msg", text)

# ================================================================
#  MAIN
# ================================================================

def main():
    app = Application.builder().token(TOKEN).build()

    media_f = (filters.PHOTO | filters.VIDEO | filters.Document.ALL |
               filters.AUDIO | filters.VOICE | filters.ANIMATION | filters.Sticker.ALL)
    text_f  = filters.TEXT & ~filters.COMMAND

    import re
    escaped     = [re.escape(b) for b in ALL_BTNS]
    reply_btn_f = filters.Regex(f"^({'|'.join(escaped)})$")

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callback),
        ],
        states={
            WAIT_FOLDER:        [MessageHandler(text_f & ~reply_btn_f, handle_text)],
            WAIT_FILE:          [MessageHandler(text_f & ~reply_btn_f, handle_text),
                                 MessageHandler(media_f, handle_media), CallbackQueryHandler(callback)],
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
            WAIT_USER_MSG:      [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_POLL_QUESTION: [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_POLL_OPTIONS:  [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_POLL_COMMENT:  [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("menu",  menu_command),
            MessageHandler(reply_btn_f, handle_reply_buttons),
            MessageHandler(media_f, handle_media),
            CallbackQueryHandler(callback),
        ],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu",  menu_command))
    # Reply butonları en önce
    app.add_handler(MessageHandler(reply_btn_f, handle_reply_buttons))
    # ConversationHandler (admin işlemleri için)
    app.add_handler(conv)
    # Admin metin girişi (search, user_msg_to_admin, poll vb.)
    app.add_handler(MessageHandler(text_f & ~reply_btn_f, handle_text))
    # Medya
    app.add_handler(MessageHandler(media_f, handle_media))
    # AI sohbet + genel fallback
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_any_message))

    print("✅ Bot başlatıldı!")
    print(f"👑 Süper Admin  : {ADMIN_ID}")
    print(f"💾 Veri dizini  : {BASE_DIR}")
    print("─" * 40)
    print("📌 Yeni özellikler:")
    print("  🆕 Yeni kullanıcı bildirimi")
    print("  🗑 Silme onay ekranı")
    print("  📊 Dosya görüntüleme sayacı")
    print("  🔢 Klasör eleman sayısı")
    if "/data" in BASE_DIR:
        print("✅ Railway Volume aktif")
    else:
        print("⚠️  Volume YOK → Railway: Volumes → Mount /data")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
