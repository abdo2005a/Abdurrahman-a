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
CLASS_FILE       = os.path.join(BASE_DIR, "user_classes.json")
FAQ_FILE         = os.path.join(BASE_DIR, "faq.json")
AUTO_RULES_FILE  = os.path.join(BASE_DIR, "auto_rules.json")
FAVORITES_FILE   = os.path.join(BASE_DIR, "favorites.json")
NOTES_FILE       = os.path.join(BASE_DIR, "user_notes.json")
WARNS_FILE       = os.path.join(BASE_DIR, "user_warns.json")
ADMIN_LOG_FILE   = os.path.join(BASE_DIR, "admin_log.json")
SUBS_FILE        = os.path.join(BASE_DIR, "subscriptions.json")
RECENT_FILE      = os.path.join(BASE_DIR, "recently_viewed.json")
FOLDER_DESC_FILE = os.path.join(BASE_DIR, "folder_descs.json")
WHITELIST_FILE   = os.path.join(BASE_DIR, "whitelist.json")
SCHEDULED_FILE   = os.path.join(BASE_DIR, "scheduled.json")
TAGS_FILE        = os.path.join(BASE_DIR, "file_tags.json")
REMINDERS_FILE   = os.path.join(BASE_DIR, "reminders.json")
SEARCH_CACHE_FILE= os.path.join(BASE_DIR, "search_cache.json")
LEADERBOARD_FILE = os.path.join(BASE_DIR, "leaderboard.json")
ACHIEVEMENTS_FILE= os.path.join(BASE_DIR, "achievements.json")
FEEDBACK_FILE    = os.path.join(BASE_DIR, "feedback.json")
PINNED_MSG_FILE  = os.path.join(BASE_DIR, "pinned_msgs.json")
BROADCAST_LOG_FILE=os.path.join(BASE_DIR, "broadcast_log.json")
COUNTDOWN_FILE   = os.path.join(BASE_DIR, "countdowns.json")
ANON_Q_FILE      = os.path.join(BASE_DIR, "anon_questions.json")
USER_NOTES_FILE  = os.path.join(BASE_DIR, "personal_notes.json")
QUIZ_FILE        = os.path.join(BASE_DIR, "quizzes.json")
REPORT_FILE      = os.path.join(BASE_DIR, "file_reports.json")

# ── Arama / AI ayarları ──────────────────────────────────────
SEARCH_TIMEOUT   = 10   # saniye
SEARCH_CACHE_TTL = 3600 # 1 saat cache
MATH_SUBJECTS_AR = {
    "رياضيات","math","حساب","جبر","هندسة","مثلثات","تفاضل","تكامل",
    "معادلة","مشتقة","نهايات","مصفوفة","احتمال","إحصاء",
}
PHYSICS_SUBJECTS_AR = {
    "فيزياء","physics","ميكانيك","كهرباء","مغناطيس","موجات",
    "حرارة","ضوء","ذرة","نووي","قوة","طاقة","سرعة","تسارع",
}
CHEMISTRY_SUBJECTS_AR = {
    "كيمياء","chemistry","عناصر","مركبات","تفاعل","معادلة كيميائية",
    "حمض","قاعدة","اكسيد","كيمياء عضوية",
}
ALL_ACADEMIC_SUBJECTS = MATH_SUBJECTS_AR | PHYSICS_SUBJECTS_AR | CHEMISTRY_SUBJECTS_AR | {
    "برمجة","programming","algorithm","خوارزمية",
    "دوائر","circuits","إلكترونيات","electronics",
    "ميكاترونيك","mechatronics","تحكم","control",
    "مقاومة مواد","strength of materials","ديناميكا","dynamics",
    "احتراق","combustion","ترموديناميك","thermodynamics",
    "ميكانيكا طيران","fluid mechanics","اهتزازات",
}

MAX_WARNS        = 3
RECENT_MAX       = 15
RATE_LIMIT_SEC   = 3   # kullanıcı başına min mesaj aralığı
SPAM_LIMIT       = 10  # 60 saniyede max mesaj sayısı

# Sınıf tanımları (Türkçe ve Arapça)
CLASS_DEFS = {
    "1": {"tr": "1. Sınıf",  "ar": "الأول"},
    "2": {"tr": "2. Sınıf",  "ar": "الثاني"},
    "3": {"tr": "3. Sınıf",  "ar": "الثالث"},
    "4": {"tr": "4. Sınıf",  "ar": "الرابع"},
}

_rate_cache: dict = {}   # {uid: [timestamp, ...]}  — in-memory rate limit
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
    # ═══ SINIF SİSTEMİ ═══
    "class_select_prompt": (
        "👋 Hoş geldin!\n\n"
        "Lütfen sınıfını seçin. Bu seçim kalıcıdır ve size özel içerik gösterilmesi için kullanılır."
    ),
    "class_selected":   "✅ Sınıfın kaydedildi: {}",
    "class_change_btn": "🎓 Sınıfımı Değiştir",
    "class_change_prompt": "🎓 Yeni sınıfını seçin:",
    "class_changed":    "✅ Sınıf güncellendi: {}",
    "class_label":      "🎓 Sınıf: {}",
    "class_unknown":    "❓ Belirsiz",
    "class_filter_btn": "🎓 Sınıfa Göre Filtrele",
    # ═══ YENİ KULLANICI BİLDİRİMİ ═══
    "new_user_notif":   "🆕 Yeni kullanıcı!\n\n👤 {name}{un}\n🆔 {uid}\n🕐 {time}",
    # ═══ İÇ YAPAY ZEKA ═══
    "ai_btn":           "🤖 Asistan",
    "ai_welcome":       "🤖 Merhaba! Sana nasıl yardımcı olabilirim?",
    "ai_no_answer":     "❓ Bu konuyu anlayamadım. Daha açık bir soru yazar mısın?",
    "ai_faq_btn":       "❓ Sık Sorulan Sorular",
    "faq_add_btn":      "➕ Soru-Cevap Ekle",
    "faq_list_btn":     "📋 Mevcut Sorular",
    "faq_del_btn":      "🗑 Soru Sil",
    "faq_panel":        "❓ FAQ Yönetimi",
    "faq_enter_q":      "❓ Soruyu yazın (veya anahtar kelimeleri):",
    "faq_enter_a":      "💬 Cevabı yazın:",
    "faq_saved":        "✅ Soru-Cevap kaydedildi.",
    "faq_deleted":      "✅ Soru-Cevap silindi.",
    "faq_empty":        "Henüz soru-cevap yok.",
    "faq_list_title":   "📋 Mevcut Sorular ({} adet):",
    "auto_rule_btn":    "⚡ Otomatik Kurallar",
    "rule_add_btn":     "➕ Kural Ekle",
    "rule_list_btn":    "📋 Kurallar",
    "rule_del_btn":     "🗑 Kural Sil",
    "rule_panel":       "⚡ Otomatik Kural Yönetimi",
    "rule_enter_kw":    "🔍 Tetikleyici kelime(ler) yazın (virgülle ayırın):",
    "rule_enter_resp":  "💬 Bu anahtar kelimeye verilecek cevabı yazın:",
    "rule_saved":       "✅ Kural kaydedildi.",
    "rule_deleted":     "✅ Kural silindi.",
    "rule_empty":       "Henüz kural yok.",
    "suggest_btn":      "💡 Benim İçin Öneri",
    "suggest_title":    "💡 Sana Özel Öneriler:",
    "suggest_empty":    "Öneri üretmek için önce birkaç dosya görüntülemelisin.",
    # ═══ FAVORİLER ═══
    "btn_favorites":    "⭐ Favorilerim",
    "fav_added":        "⭐ Favorilere eklendi!",
    "fav_removed":      "💔 Favorilerden kaldırıldı.",
    "fav_list":         "⭐ FAVORİLERİM",
    "fav_empty":        "Henüz favori eklemedin.\n\nDosya görüntülerken ⭐ butonuna bas.",
    "fav_add_btn":      "⭐ Favoriye Ekle",
    "fav_remove_btn":   "💔 Favoriden Çıkar",
    # ═══ SON GÖRÜNTÜLENENLEr ═══
    "btn_recent":       "🕐 Son Görüntülenenler",
    "recent_list":      "🕐 SON GÖRÜNTÜLENENLEr",
    "recent_empty":     "Henüz dosya görüntülemedin.",
    # ═══ UYARI SİSTEMİ ═══
    "warn_btn":             "⚠️ Uyarı Ver",
    "warn_reason_prompt":   "⚠️ Uyarı sebebini yazın:",
    "user_warned":          "⚠️ {} kullanıcısına uyarı verildi. ({}/{})",
    "user_auto_blocked":    "🚫 {} otomatik engellendi! ({} uyarı)",
    "warn_msg_to_user":     "⚠️ BİR UYARI ALDINIZ\n\nSebep: {reason}\n\n🚨 Uyarı: {count}/{max}\n\n{count} üst sınıra ulaşırsa erişiminiz kısıtlanır.",
    "warn_count_label":     "⚠️ Uyarılar: {}/{}",
    "warn_clear_btn":       "🔓 Uyarıları Sıfırla",
    "warns_cleared":        "✅ {} uyarıları sıfırlandı.",
    "no_warns":             "✅ Uyarısı yok.",
    # ═══ KULLANICI NOTU ═══
    "note_btn":         "📝 Not Ekle/Güncelle",
    "note_prompt":      "📝 Bu kullanıcı için not yazın (boş = sil):",
    "note_saved":       "✅ Not kaydedildi.",
    "note_label":       "📝 Admin Notu: ",
    "note_cleared":     "✅ Not silindi.",
    # ═══ YEDEKLEME ═══
    "backup_btn":       "💾 Tam Yedek Al",
    "backup_sending":   "💾 Yedek hazırlanıyor...",
    "backup_done":      "✅ Yedek tamamlandı. {} dosya gönderildi.",
    "export_users_btn": "📤 Kullanıcıları Dışa Aktar",
    "export_done":      "✅ {} kullanıcı dışa aktarıldı.",
    # ═══ HEDEFLİ DUYURU ═══
    "bcast_targeted":   "🎯 Hedefli Duyuru",
    "bcast_all":        "📢 Tüm Kullanıcılar",
    "bcast_class":      "🎓 Sınıfa Göre",
    "bcast_active":     "✅ Aktifler (7 gün)",
    "bcast_new":        "🆕 Yeni Kullanıcılar (7 gün)",
    "bcast_class_select":"🎓 Hangi sınıfa gönderilsin?",
    "bcast_confirm":    "📢 {} kullanıcıya gönderilecek. Devam edilsin mi?",
    "bcast_target_set": "🎯 Hedef: {}",
    # ═══ KLASÖR ABONELİĞİ ═══
    "subscribe_btn":    "🔔 Abone Ol",
    "unsubscribe_btn":  "🔕 Aboneliği Kaldır",
    "subscribed_ok":    "🔔 Abone oldunuz! Yeni dosya eklenince bildirim alacaksınız.",
    "unsubscribed_ok":  "🔕 Abonelik kaldırıldı.",
    "sub_notif":        "🔔 Yeni dosya eklendi!\n📁 {folder}\n📎 {fname}",
    # ═══ KLASÖR AÇIKLAMASI ═══
    "folder_desc_btn":    "📝 Klasör Açıklaması",
    "folder_desc_prompt": "📝 Bu klasör için açıklama yazın (boş bırakırsan silinir):",
    "folder_desc_saved":  "✅ Açıklama kaydedildi.",
    "folder_desc_cleared":"✅ Açıklama silindi.",
    # ═══ DOSYA İŞLEMLERİ ═══
    "pin_file":           "📌 Dosya Sabitle",
    "unpin_file":         "📌 Sabitlemeyi Kaldır",
    "pin_select":         "📌 Sabitlenecek dosyayı seçin:",
    "unpin_select":       "📌 Sabitleme kaldırılacak dosyayı seçin:",
    "file_pinned":        "📌 Sabitlendi: '{}'",
    "file_unpinned":      "📌 Sabitleme kaldırıldı: '{}'",
    "move_file":          "📂 Dosya Taşı",
    "copy_file":          "📋 Dosya Kopyala",
    "move_select_file":   "📂 Taşınacak dosyayı seçin:",
    "copy_select_file":   "📋 Kopyalanacak dosyayı seçin:",
    "move_select_dest":   "📂 Hedef klasörü seçin:\n(Mevcut konum: {})",
    "file_moved":         "✅ '{}' → '{}' klasörüne taşındı.",
    "file_copied":        "✅ '{}' → '{}' klasörüne kopyalandı.",
    "no_dest":            "❌ Hedef klasör bulunamadı.",
    "sort_az":            "🔤 A-Z Sırala",
    "sort_views":         "👁 Görüntülemeye Göre Sırala",
    "sort_date":          "📅 Tarihe Göre Sırala",
    "files_sorted":       "✅ Dosyalar sıralandı.",
    # ═══ ETİKET SİSTEMİ ═══
    "tag_btn":            "🏷 Etiket Ekle",
    "tag_prompt":         "🏷 Etiket(ler) yazın (virgülle ayırın):",
    "tag_saved":          "✅ Etiketler kaydedildi.",
    "tag_search":         "🏷 Etikete Göre Ara",
    "tag_select_prompt":  "🏷 Aranacak etiketi yazın:",
    # ═══ ZAMANLAMA ═══
    "schedule_btn":       "⏰ Zamanlanmış Mesaj",
    "schedule_prompt":    "⏰ Kaç saat sonra gönderilsin? (0.5 - 72)",
    "schedule_msg_prompt":"💬 Gönderilecek mesajı yazın:",
    "schedule_saved":     "✅ Mesaj {} saat sonra gönderilecek.",
    "schedule_list":      "⏰ Zamanlanmış Mesajlar",
    "schedule_empty":     "Zamanlanmış mesaj yok.",
    "schedule_del":       "🗑 İptal Et",
    "schedule_canceled":  "✅ Zamanlanmış mesaj iptal edildi.",
    # ═══ HATIRLATICI ═══
    "reminder_btn":       "🔔 Hatırlatıcı Ekle",
    "reminder_text":      "📝 Hatırlatıcı metnini yazın:",
    "reminder_hour":      "⏰ Kaç saat sonra hatırlatılsın?",
    "reminder_saved":     "✅ Hatırlatıcı kaydedildi.",
    "reminder_msg":       "🔔 HATIRLATICI\n\n{}",
    # ═══ ADMIN LOG ═══
    "admin_log_btn":      "📋 İşlem Günlüğü",
    "admin_log_title":    "📋 SON ADMIN İŞLEMLERİ",
    "admin_log_empty":    "Henüz kayıt yok.",
    # ═══ GİZLİ MOD ═══
    "secret_mode_btn":    "🔒 Gizli Mod",
    "secret_on":          "🔒 Gizli Mod: AÇIK",
    "secret_off":         "🔓 Gizli Mod: KAPALI",
    "secret_add_btn":     "➕ Kullanıcı Ekle",
    "secret_del_btn":     "➖ Kullanıcı Çıkar",
    "secret_enter_id":    "Whitelist'e eklenecek kullanıcı ID'sini yazın:",
    "secret_added":       "✅ {} whitelist'e eklendi.",
    "secret_removed":     "✅ {} whitelist'ten çıkarıldı.",
    "secret_deny":        "🔒 Bu bot şu an gizli modda. Yöneticiyle iletişime geç.",
    "secret_list":        "🔒 Whitelist ({} kullanıcı):",
    # ═══ KULLANICI PROFİL ═══
    "profile_btn":        "👤 Profilim",
    "profile_title":      "👤 PROFİLİM",
    # ═══ SPAM KORUMA ═══
    "spam_warning":       "⚠️ Çok hızlı mesaj gönderiyorsun. Lütfen bekle.",
    # ═══ SELAMLAMA ═══
    "greeting_reply":     "👋 Merhaba! Ana menüye dönmek için /start yazabilirsin.",
    # ═══ STARTUP ═══
    "startup_msg":        "✅ Bot yeniden başladı! Tüm servisler aktif.",
    # ═══ WEB ARAMA YAPAY ZEKASI ═══
    "ai_searching":       "🔍 Araştırıyorum...",
    "ai_calculating":     "🧮 Hesaplıyorum...",
    "ai_search_result":   "🔍 *Arama Sonucu:*\n\n{result}\n\n📎 Kaynak: {source}",
    "ai_math_result":     "🧮 *Matematik Çözümü:*\n\n{result}",
    "ai_wiki_result":     "📖 *Vikipedi:*\n\n{result}\n\n🔗 {url}",
    "ai_no_web_result":   "❌ Bu soru için sonuç bulunamadı. Farklı bir ifadeyle tekrar dene.",
    "ai_web_error":       "⚠️ Arama sırasında hata oluştu. Lütfen tekrar dene.",
    "ai_typing":          "🤖 Yazıyor...",
    "ai_source_ddg":      "DuckDuckGo",
    "ai_source_wiki":     "Vikipedi",
    "ai_source_calc":     "Hesap Makinesi",
    "ai_subject_math":    "🧮 Matematik",
    "ai_subject_physics": "⚛️ Fizik",
    "ai_subject_chem":    "🧪 Kimya",
    "ai_subject_prog":    "💻 Programlama",
    "ai_subject_eng":     "⚙️ Mühendislik",
    "ai_detected":        "🎯 Konu: {} — Web'de arıyorum...",
    # ═══ LIDERBOARD / BAŞARI ═══
    "btn_leaderboard":    "🏆 Liderboard",
    "leaderboard_title":  "🏆 EN AKTİF KULLANICILAR",
    "leaderboard_empty":  "Henüz veri yok.",
    "achievement_unlocked":"🏅 Başarı Kazandınız: {}!",
    # ═══ GERİ BİLDİRİM ═══
    "feedback_btn":       "⭐ Geri Bildirim",
    "feedback_prompt":    "⭐ Bu dosya için puan verin (1-5 yıldız):",
    "feedback_saved":     "✅ Geri bildiriminiz kaydedildi!",
    "feedback_stats":     "⭐ Ortalama: {avg:.1f}/5 ({count} oy)",
    # ═══ SABİT MESAJ ═══
    "pin_msg_btn":        "📌 Mesaj Sabitle",
    "pin_msg_prompt":     "📌 Sabitlenecek mesajı yazın:",
    "pin_msg_saved":      "✅ Mesaj sabitlendi.",
    "pinned_msg_label":   "📌 SABİT MESAJ:\n{}",
    # ═══ BROADCAST LOG ═══
    "bcast_history_btn":  "📜 Duyuru Geçmişi",
    "bcast_history_title":"📜 SON DUYURULAR",
    "bcast_history_empty":"Henüz duyuru yok.",
    # ═══ TOPLU MESAJ SİLME ═══
    "clear_chat_btn":     "🧹 Sohbeti Temizle",
    "clear_chat_done":    "✅ Sohbet temizlendi.",
    # ═══ HIZLI CEVAP ═══
    "quick_reply_btn":    "⚡ Hızlı Cevap",
    "quick_reply_saved":  "✅ Hızlı cevap şablonu kaydedildi.",
    # ═══ YENİ ÖZELLİKLER ═══
    "btn_notes":          "📝 Notlarım",
    "btn_reminder":       "⏰ Hatırlatıcım",
    "notes_empty":        "Henüz not yok.",
    "notes_saved":        "✅ Not kaydedildi.",
    "notes_title":        "📝 KİŞİSEL NOTLARIM",
    "notes_prompt":       "📝 Notunuzu yazın:",
    "reminder_list":      "⏰ Hatırlatıcılarım ({} adet):",
    "reminder_none":      "Henüz hatırlatıcı yok.",
    "reminder_add_prompt":"⏰ Hatırlatıcı metni yaz:",
    "reminder_when":      "Ne zaman? (örn: 30d=30dk, 2s=2saat, 1g=1gün)",
    "reminder_saved":     "✅ {} sonra hatırlatacağım.",
    "reminder_fired":     "🔔 HATIRLATICI\n\n{}",
    "reminder_del":       "✅ Silindi.",
    "anon_q_btn":         "❓ Anonim Soru",
    "anon_q_prompt":      "❓ Sorunuzu yazın (anonim):",
    "anon_q_sent":        "✅ Sorunuz iletildi.",
    "anon_q_notify":      "❓ ORGANİK SORU (Anonim):\n\n{}",
    "file_report_btn":    "🚩 Sorun Bildir",
    "file_report_sent":   "✅ Raporunuz alındı.",
    "quiz_btn":           "📝 Mini Test",
    "quiz_none":          "Aktif test yok.",
    "countdown_btn":      "⏳ Yaklaşan Sınav",
    "countdown_none":     "Yaklaşan sınav eklenmemiş.",
    "countdown_add":      "➕ Sınav/Etkinlik Ekle",
    "countdown_prompt":   "Sınav adını yazın:",
    "countdown_date":     "Tarih yazın (ör: 20/05/2026):",
    "countdown_saved":    "✅ {} kaydedildi.",
    "class_stats_btn":    "📊 Sınıf İstatistikleri",
    "share_btn":          "🔗 Paylaş",
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
    # ═══ SINIF SİSTEMİ (AR) ═══
    "class_select_prompt": (
        "👋 أهلاً بك!\n\n"
        "يرجى اختيار سنتك الدراسية. سيُستخدم هذا لعرض المحتوى المناسب لك."
    ),
    "class_selected":    "✅ تم تسجيل سنتك الدراسية: {}",
    "class_change_btn":  "🎓 تغيير السنة الدراسية",
    "class_change_prompt":"🎓 اختر سنتك الدراسية الجديدة:",
    "class_changed":     "✅ تم تحديث السنة الدراسية: {}",
    "class_label":       "🎓 السنة: {}",
    "class_unknown":     "❓ غير محدد",
    "class_filter_btn":  "🎓 تصفية حسب السنة",
    # ═══ يدعم بالعربية ═══
    "new_user_notif":    "🆕 مستخدم جديد!\n\n👤 {name}{un}\n🆔 {uid}\n🕐 {time}",
    "ai_btn":            "🤖 المساعد",
    "ai_welcome":        "🤖 مرحباً! كيف أستطيع مساعدتك؟",
    "ai_no_answer":      "❓ لم أفهم سؤالك. هل يمكنك إعادة الصياغة؟",
    "ai_faq_btn":        "❓ الأسئلة الشائعة",
    "faq_add_btn":       "➕ إضافة سؤال وجواب",
    "faq_list_btn":      "📋 الأسئلة الموجودة",
    "faq_del_btn":       "🗑 حذف سؤال",
    "faq_panel":         "❓ إدارة الأسئلة الشائعة",
    "faq_enter_q":       "❓ اكتب السؤال أو الكلمات المفتاحية:",
    "faq_enter_a":       "💬 اكتب الإجابة:",
    "faq_saved":         "✅ تم حفظ السؤال والإجابة.",
    "faq_deleted":       "✅ تم حذف السؤال.",
    "faq_empty":         "لا توجد أسئلة وأجوبة بعد.",
    "faq_list_title":    "📋 الأسئلة الموجودة ({} سؤال):",
    "auto_rule_btn":     "⚡ القواعد التلقائية",
    "rule_add_btn":      "➕ إضافة قاعدة",
    "rule_list_btn":     "📋 القواعد",
    "rule_del_btn":      "🗑 حذف قاعدة",
    "rule_panel":        "⚡ إدارة القواعد التلقائية",
    "rule_enter_kw":     "🔍 اكتب الكلمات المفتاحية (مفصولة بفاصلة):",
    "rule_enter_resp":   "💬 اكتب الرد على هذه الكلمات المفتاحية:",
    "rule_saved":        "✅ تم حفظ القاعدة.",
    "rule_deleted":      "✅ تم حذف القاعدة.",
    "rule_empty":        "لا توجد قواعد بعد.",
    "suggest_btn":       "💡 اقتراحات لي",
    "suggest_title":     "💡 اقتراحات مخصصة لك:",
    "suggest_empty":     "شاهد بعض الملفات أولاً لتحصل على اقتراحات.",
    "btn_favorites":     "⭐ المفضلة",
    "fav_added":         "⭐ تمت الإضافة للمفضلة!",
    "fav_removed":       "💔 تمت الإزالة من المفضلة.",
    "fav_list":          "⭐ قائمة المفضلة",
    "fav_empty":         "لا توجد ملفات مفضلة بعد.\nاضغط ⭐ عند عرض الملفات.",
    "fav_add_btn":       "⭐ إضافة للمفضلة",
    "fav_remove_btn":    "💔 إزالة من المفضلة",
    "btn_recent":        "🕐 المشاهدة مؤخراً",
    "recent_list":       "🕐 المشاهدة مؤخراً",
    "recent_empty":      "لم تشاهد أي ملف بعد.",
    "warn_btn":              "⚠️ تحذير",
    "warn_reason_prompt":    "⚠️ اكتب سبب التحذير:",
    "user_warned":           "⚠️ تم تحذير {}. ({}/{})",
    "user_auto_blocked":     "🚫 تم حظر {} تلقائياً! ({} تحذيرات)",
    "warn_msg_to_user":      "⚠️ تلقّيت تحذيراً\n\nالسبب: {reason}\n\n🚨 التحذيرات: {count}/{max}\n\nعند الوصول للحد الأقصى سيتم تقييد وصولك.",
    "warn_count_label":      "⚠️ التحذيرات: {}/{}",
    "warn_clear_btn":        "🔓 مسح التحذيرات",
    "warns_cleared":         "✅ تم مسح تحذيرات {}.",
    "no_warns":              "✅ لا توجد تحذيرات.",
    "note_btn":          "📝 إضافة/تعديل ملاحظة",
    "note_prompt":       "📝 اكتب ملاحظتك عن هذا المستخدم (فارغ = حذف):",
    "note_saved":        "✅ تم حفظ الملاحظة.",
    "note_label":        "📝 ملاحظة المسؤول: ",
    "note_cleared":      "✅ تم حذف الملاحظة.",
    "backup_btn":        "💾 نسخ احتياطي كامل",
    "backup_sending":    "💾 جارٍ تجهيز النسخ الاحتياطية...",
    "backup_done":       "✅ اكتمل النسخ الاحتياطي. {} ملف.",
    "export_users_btn":  "📤 تصدير المستخدمين",
    "export_done":       "✅ تم تصدير {} مستخدم.",
    "bcast_targeted":    "🎯 إرسال موجّه",
    "bcast_all":         "📢 الجميع",
    "bcast_class":       "🎓 حسب السنة",
    "bcast_active":      "✅ النشطون (7 أيام)",
    "bcast_new":         "🆕 الجدد (7 أيام)",
    "bcast_class_select":"🎓 أي سنة تريد الإرسال إليها؟",
    "bcast_confirm":     "📢 سيتم الإرسال لـ {} مستخدم. هل تريد المتابعة؟",
    "bcast_target_set":  "🎯 الهدف: {}",
    "subscribe_btn":     "🔔 اشترك في المجلد",
    "unsubscribe_btn":   "🔕 إلغاء الاشتراك",
    "subscribed_ok":     "🔔 تم الاشتراك! ستصلك إشعارات عند إضافة ملفات جديدة.",
    "unsubscribed_ok":   "🔕 تم إلغاء الاشتراك.",
    "sub_notif":         "🔔 ملف جديد!\n📁 {folder}\n📎 {fname}",
    "folder_desc_btn":    "📝 وصف المجلد",
    "folder_desc_prompt": "📝 اكتب وصفاً لهذا المجلد (فارغ = حذف):",
    "folder_desc_saved":  "✅ تم حفظ الوصف.",
    "folder_desc_cleared":"✅ تم حذف الوصف.",
    "pin_file":           "📌 تثبيت ملف",
    "unpin_file":         "📌 إلغاء التثبيت",
    "pin_select":         "📌 اختر الملف للتثبيت:",
    "unpin_select":       "📌 اختر الملف لإلغاء التثبيت:",
    "file_pinned":        "📌 تم تثبيت '{}'",
    "file_unpinned":      "📌 تم إلغاء تثبيت '{}'",
    "move_file":          "📂 نقل ملف",
    "copy_file":          "📋 نسخ ملف",
    "move_select_file":   "📂 اختر الملف للنقل:",
    "copy_select_file":   "📋 اختر الملف للنسخ:",
    "move_select_dest":   "📂 اختر المجلد الهدف:\n(الموقع الحالي: {})",
    "file_moved":         "✅ تم نقل '{}' إلى '{}'.",
    "file_copied":        "✅ تم نسخ '{}' إلى '{}'.",
    "no_dest":            "❌ المجلد الهدف غير موجود.",
    "sort_az":            "🔤 ترتيب أبجدي",
    "sort_views":         "👁 حسب المشاهدات",
    "sort_date":          "📅 حسب التاريخ",
    "files_sorted":       "✅ تم ترتيب الملفات.",
    "tag_btn":            "🏷 إضافة وسوم",
    "tag_prompt":         "🏷 اكتب الوسوم (مفصولة بفاصلة):",
    "tag_saved":          "✅ تم حفظ الوسوم.",
    "tag_search":         "🏷 البحث بالوسم",
    "tag_select_prompt":  "🏷 اكتب الوسم للبحث:",
    "schedule_btn":       "⏰ رسالة مجدولة",
    "schedule_prompt":    "⏰ كم ساعة؟ (0.5 - 72)",
    "schedule_msg_prompt":"💬 اكتب الرسالة المجدولة:",
    "schedule_saved":     "✅ ستُرسل الرسالة بعد {} ساعة.",
    "schedule_list":      "⏰ الرسائل المجدولة",
    "schedule_empty":     "لا توجد رسائل مجدولة.",
    "schedule_del":       "🗑 إلغاء",
    "schedule_canceled":  "✅ تم إلغاء الرسالة المجدولة.",
    "reminder_btn":       "🔔 إضافة تذكير",
    "reminder_text":      "📝 اكتب نص التذكير:",
    "reminder_hour":      "⏰ بعد كم ساعة؟",
    "reminder_saved":     "✅ تم حفظ التذكير.",
    "reminder_msg":       "🔔 تذكير\n\n{}",
    "admin_log_btn":      "📋 سجل الإجراءات",
    "admin_log_title":    "📋 آخر إجراءات المسؤول",
    "admin_log_empty":    "لا توجد سجلات بعد.",
    "secret_mode_btn":    "🔒 الوضع السري",
    "secret_on":          "🔒 الوضع السري: مفعّل",
    "secret_off":         "🔓 الوضع السري: معطّل",
    "secret_add_btn":     "➕ إضافة مستخدم",
    "secret_del_btn":     "➖ إزالة مستخدم",
    "secret_enter_id":    "اكتب ID المستخدم للإضافة:",
    "secret_added":       "✅ تمت إضافة {} للقائمة البيضاء.",
    "secret_removed":     "✅ تمت إزالة {} من القائمة البيضاء.",
    "secret_deny":        "🔒 البوت في الوضع السري. تواصل مع المسؤول.",
    "secret_list":        "🔒 القائمة البيضاء ({} مستخدم):",
    "profile_btn":        "👤 ملفي الشخصي",
    "profile_title":      "👤 ملفي الشخصي",
    "spam_warning":       "⚠️ أنت تُرسل بسرعة كبيرة. الرجاء الانتظار.",
    # ═══ SELAMLAMA (AR) ═══
    "greeting_reply":     "👋 أهلاً وسهلاً! اكتب /start للعودة إلى القائمة الرئيسية.",
    "startup_msg":        "✅ البوت يعمل مجدداً! جميع الخدمات متاحة.",
    # ═══ WEB ARAMA YAPAY ZEKASI (AR) ═══
    "ai_searching":       "🔍 جارٍ البحث...",
    "ai_calculating":     "🧮 جارٍ الحساب...",
    "ai_search_result":   "🔍 *نتيجة البحث:*\n\n{result}\n\n📎 المصدر: {source}",
    "ai_math_result":     "🧮 *الحل الرياضي:*\n\n{result}",
    "ai_wiki_result":     "📖 *ويكيبيديا:*\n\n{result}\n\n🔗 {url}",
    "ai_no_web_result":   "❌ لم أجد نتيجة لهذا السؤال. جرب صياغة مختلفة.",
    "ai_web_error":       "⚠️ حدث خطأ أثناء البحث. حاول مرة أخرى.",
    "ai_typing":          "🤖 يكتب...",
    "ai_source_ddg":      "DuckDuckGo",
    "ai_source_wiki":     "ويكيبيديا",
    "ai_source_calc":     "الآلة الحاسبة",
    "ai_subject_math":    "🧮 رياضيات",
    "ai_subject_physics": "⚛️ فيزياء",
    "ai_subject_chem":    "🧪 كيمياء",
    "ai_subject_prog":    "💻 برمجة",
    "ai_subject_eng":     "⚙️ هندسة",
    "ai_detected":        "🎯 الموضوع: {} — جارٍ البحث على الويب...",
    "btn_leaderboard":    "🏆 المتصدرون",
    "leaderboard_title":  "🏆 أكثر المستخدمين نشاطاً",
    "leaderboard_empty":  "لا توجد بيانات بعد.",
    "achievement_unlocked":"🏅 حصلت على إنجاز: {}!",
    "feedback_btn":       "⭐ تقييم",
    "feedback_prompt":    "⭐ قيّم هذا الملف (1-5 نجوم):",
    "feedback_saved":     "✅ تم حفظ تقييمك!",
    "feedback_stats":     "⭐ المتوسط: {avg:.1f}/5 ({count} تقييم)",
    "pin_msg_btn":        "📌 تثبيت رسالة",
    "pin_msg_prompt":     "📌 اكتب الرسالة المراد تثبيتها:",
    "pin_msg_saved":      "✅ تم تثبيت الرسالة.",
    "pinned_msg_label":   "📌 الرسالة المثبتة:\n{}",
    "bcast_history_btn":  "📜 سجل الإعلانات",
    "bcast_history_title":"📜 آخر الإعلانات",
    "bcast_history_empty":"لا توجد إعلانات بعد.",
    "clear_chat_btn":     "🧹 مسح المحادثة",
    "clear_chat_done":    "✅ تم مسح المحادثة.",
    "quick_reply_btn":    "⚡ رد سريع",
    "quick_reply_saved":  "✅ تم حفظ قالب الرد السريع.",
    # ═══ مميزات جديدة ═══
    "btn_notes":          "📝 ملاحظاتي",
    "btn_reminder":       "⏰ تذكيراتي",
    "notes_empty":        "لا توجد ملاحظات بعد.",
    "notes_saved":        "✅ تم حفظ الملاحظة.",
    "notes_title":        "📝 ملاحظاتي الشخصية",
    "notes_prompt":       "📝 اكتب ملاحظتك:",
    "reminder_list":      "⏰ تذكيراتي ({} تذكير):",
    "reminder_none":      "لا توجد تذكيرات.",
    "reminder_add_prompt":"⏰ اكتب نص التذكير:",
    "reminder_when":      "متى؟ (مثال: 30d=30دق، 2s=2ساعة، 1g=يوم)",
    "reminder_saved":     "✅ سأذكرك بعد {}.",
    "reminder_fired":     "🔔 تذكير\n\n{}",
    "reminder_del":       "✅ تم الحذف.",
    "anon_q_btn":         "❓ سؤال مجهول",
    "anon_q_prompt":      "❓ اكتب سؤالك (مجهول الهوية):",
    "anon_q_sent":        "✅ تم إرسال سؤالك.",
    "anon_q_notify":      "❓ سؤال مجهول الهوية:\n\n{}",
    "file_report_btn":    "🚩 إبلاغ عن مشكلة",
    "file_report_sent":   "✅ تم استلام بلاغك.",
    "quiz_btn":           "📝 اختبار قصير",
    "quiz_none":          "لا يوجد اختبار نشط.",
    "countdown_btn":      "⏳ الامتحانات القادمة",
    "countdown_none":     "لا توجد امتحانات مضافة.",
    "countdown_add":      "➕ إضافة امتحان",
    "countdown_prompt":   "اكتب اسم الامتحان:",
    "countdown_date":     "اكتب التاريخ (مثال: 20/05/2026):",
    "countdown_saved":    "✅ تم حفظ {}.",
    "class_stats_btn":    "📊 إحصائيات الصف",
    "share_btn":          "🔗 مشاركة",
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

# ================================================================
#  VARSAYILAN KLASÖR YAPISI — Bot her başladığında eksikse oluşturur
# ================================================================

def _make_folder(*subs):
    """İçi boş klasör şablonu."""
    return {"folders": {s: {"folders": {}, "files": []} for s in subs}, "files": []}

DEFAULT_CONTENT = {
    "folders": {
        "الاول": {
            "folders": {
                "مواد كورس الأول": _make_folder(
                    "رياضيات", "اسس", "فيزياء", "انجليزي", "ورش", "حقوق", "حاسوب"
                ),
                "مواد كورس الثاني": _make_folder(
                    "اسس", "رياضيات", "فيزياء", "برمجة", "رسم", "عربي", "رقميه"
                ),
                "جدول": {"folders": {}, "files": []},
            },
            "files": [],
        },
        "الثاني": {
            "folders": {
                "مواد كورس الأول": _make_folder(
                    "رياضيات", "فيزياء", "اسس", "انجليزي", "ورش"
                ),
                "مواد كورس الثاني": _make_folder(
                    "رياضيات", "فيزياء", "ميكانيك", "برمجة", "رسم"
                ),
                "جدول": {"folders": {}, "files": []},
            },
            "files": [],
        },
        "الثالث": {
            "folders": {
                "مواد كورس الأول": _make_folder(
                    "رياضيات", "فيزياء", "اسس", "انجليزي"
                ),
                "مواد كورس الثاني": _make_folder(
                    "رياضيات", "فيزياء", "مواد متخصصة", "مشروع"
                ),
                "جدول": {"folders": {}, "files": []},
            },
            "files": [],
        },
        "الرابع": {
            "folders": {
                "مواد كورس الأول": _make_folder(
                    "مواد متخصصة", "مشروع تخرج", "انجليزي"
                ),
                "مواد كورس الثاني": _make_folder(
                    "مواد متخصصة", "مشروع تخرج", "تدريب عملي"
                ),
                "جدول": {"folders": {}, "files": []},
            },
            "files": [],
        },
    },
    "files": [],
}

def load_content():
    data = load_json(DATA_FILE, None)
    if data is None:
        # İlk çalışma — varsayılan yapıyı oluştur ve kaydet
        save_json(DATA_FILE, DEFAULT_CONTENT)
        logger.info("✅ Varsayılan klasör yapısı oluşturuldu.")
        return DEFAULT_CONTENT
    # Eksik ana klasörleri tamamla (güncelleme sonrası koruma)
    changed = False
    for name, val in DEFAULT_CONTENT["folders"].items():
        if name not in data.setdefault("folders", {}):
            data["folders"][name] = val
            changed = True
    if changed:
        save_json(DATA_FILE, data)
        logger.info("✅ Eksik klasörler tamamlandı.")
    return data

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

# ── Yeni veri dosyaları ───────────────────────────────────────
def load_classes():       return load_json(CLASS_FILE, {})
def save_classes(d):      save_json(CLASS_FILE, d)
def load_faq():           return load_json(FAQ_FILE, [])
def save_faq(d):          save_json(FAQ_FILE, d)
def load_auto_rules():    return load_json(AUTO_RULES_FILE, [])
def save_auto_rules(d):   save_json(AUTO_RULES_FILE, d)
def load_favorites():     return load_json(FAVORITES_FILE, {})
def save_favorites(d):    save_json(FAVORITES_FILE, d)
def load_notes():         return load_json(NOTES_FILE, {})
def save_notes(d):        save_json(NOTES_FILE, d)
def load_warns():         return load_json(WARNS_FILE, {})
def save_warns(d):        save_json(WARNS_FILE, d)
def load_admin_log():     return load_json(ADMIN_LOG_FILE, [])
def save_admin_log(d):    save_json(ADMIN_LOG_FILE, d)
def load_subs():          return load_json(SUBS_FILE, {})
def save_subs(d):         save_json(SUBS_FILE, d)
def load_recent():        return load_json(RECENT_FILE, {})
def save_recent(d):       save_json(RECENT_FILE, d)
def load_folder_descs():  return load_json(FOLDER_DESC_FILE, {})
def save_folder_descs(d): save_json(FOLDER_DESC_FILE, d)
def load_whitelist():     return load_json(WHITELIST_FILE, {"enabled": False, "users": []})
def save_whitelist(d):    save_json(WHITELIST_FILE, d)
def load_scheduled():     return load_json(SCHEDULED_FILE, [])
def save_scheduled(d):    save_json(SCHEDULED_FILE, d)
def load_tags():          return load_json(TAGS_FILE, {})
def save_tags(d):         save_json(TAGS_FILE, d)
def load_reminders():     return load_json(REMINDERS_FILE, [])
def save_reminders(d):    save_json(REMINDERS_FILE, d)
def load_search_cache():  return load_json(SEARCH_CACHE_FILE, {})
def save_search_cache(d): save_json(SEARCH_CACHE_FILE, d)
def load_leaderboard():   return load_json(LEADERBOARD_FILE, {})
def save_leaderboard(d):  save_json(LEADERBOARD_FILE, d)
def load_achievements():  return load_json(ACHIEVEMENTS_FILE, {})
def save_achievements(d): save_json(ACHIEVEMENTS_FILE, d)
def load_feedback():      return load_json(FEEDBACK_FILE, {})
def save_feedback(d):     save_json(FEEDBACK_FILE, d)
def load_pinned_msgs():   return load_json(PINNED_MSG_FILE, {})
def save_pinned_msgs(d):  save_json(PINNED_MSG_FILE, d)
def load_bcast_log():     return load_json(BROADCAST_LOG_FILE, [])
def save_bcast_log(d):    save_json(BROADCAST_LOG_FILE, d[-100:])
def load_countdowns():    return load_json(COUNTDOWN_FILE, [])
def save_countdowns(d):   save_json(COUNTDOWN_FILE, d)
def load_anon_q():        return load_json(ANON_Q_FILE, [])
def save_anon_q(d):       save_json(ANON_Q_FILE, d)
def load_personal_notes():return load_json(USER_NOTES_FILE, {})
def save_personal_notes(d):save_json(USER_NOTES_FILE, d)
def load_quizzes():       return load_json(QUIZ_FILE, [])
def save_quizzes(d):      save_json(QUIZ_FILE, d)
def load_reports():       return load_json(REPORT_FILE, [])
def save_reports(d):      save_json(REPORT_FILE, d)

def get_personal_note(uid: str) -> str:
    return load_personal_notes().get(str(uid), "")

def set_personal_note(uid: str, text: str):
    d = load_personal_notes()
    d[str(uid)] = text[:2000]
    save_personal_notes(d)

def add_reminder(uid: str, text: str, fire_ts: float):
    rems = load_reminders()
    rems.append({"uid": str(uid), "text": text, "fire_ts": fire_ts,
                 "created": datetime.now().strftime("%Y-%m-%d %H:%M")})
    save_reminders(rems)

def get_user_reminders(uid: str) -> list:
    return [r for r in load_reminders() if str(r.get("uid")) == str(uid)]

def delete_reminder(uid: str, idx: int):
    rems = load_reminders()
    user_rems = [(i, r) for i, r in enumerate(rems) if str(r.get("uid")) == str(uid)]
    if 0 <= idx < len(user_rems):
        rems.pop(user_rems[idx][0])
    save_reminders(rems)

def parse_time_input(text: str) -> int:
    """'30d'→30dk, '2s'→120dk, '1g'→1440dk. None dönerse geçersiz."""
    import re
    text = text.strip().lower()
    m = re.match(r'^(\d+(?:\.\d+)?)\s*([dsghmDSGHM]?)$', text)
    if not m: return 0
    val, unit = float(m.group(1)), m.group(2)
    if unit in ('d',):   return int(val)           # dakika
    if unit in ('s',):   return int(val * 60)       # saat→dk
    if unit in ('g', 'h'): return int(val * 1440)  # gün→dk
    if unit in ('m',):   return int(val)
    return int(val)

def add_countdown(name: str, date_str: str, cls: str = "") -> bool:
    """date_str: 'DD/MM/YYYY' formatında."""
    try:
        from datetime import datetime as dt
        target = dt.strptime(date_str.strip(), "%d/%m/%Y")
        cd = load_countdowns()
        cd.append({"name": name, "date": date_str, "ts": target.timestamp(),
                   "cls": cls, "created": datetime.now().strftime("%Y-%m-%d")})
        save_countdowns(cd)
        return True
    except: return False

def get_countdowns(cls: str = "") -> list:
    """Gelecekteki geri sayımları döndür."""
    import time
    now = time.time()
    cd  = load_countdowns()
    result = []
    for c in cd:
        if c.get("ts", 0) > now:
            if not cls or not c.get("cls") or c.get("cls") == cls:
                days_left = int((c["ts"] - now) / 86400)
                result.append({**c, "days_left": days_left})
    return sorted(result, key=lambda x: x["ts"])

# ================================================================
#  WEB ARAMA & YAPAY ZEKA MOTORU
#  Dışarıya bağlı değil — DuckDuckGo + Wikipedia + Python hesap
# ================================================================

import re as _re
import asyncio
import html as _html

def _detect_subject(text: str) -> Optional[str]:
    """Metnin hangi akademik konuya ait olduğunu tespit eder."""
    norm = text.lower()
    if any(kw in norm for kw in MATH_SUBJECTS_AR):     return "math"
    if any(kw in norm for kw in PHYSICS_SUBJECTS_AR):  return "physics"
    if any(kw in norm for kw in CHEMISTRY_SUBJECTS_AR):return "chemistry"
    if any(kw in norm for kw in {"برمجة","programming","algorithm","code"}): return "programming"
    if any(kw in norm for kw in ALL_ACADEMIC_SUBJECTS): return "engineering"
    return None

def _is_question(text: str) -> bool:
    """Soru mu yoksa rastgele mesaj mı?"""
    question_indicators = [
        "?", "؟", "كيف", "ما", "من", "متى", "أين", "لماذا", "كم",
        "احسب", "اوجد", "حل", "اشرح", "ما هو", "ما هي",
        "solve", "calculate", "find", "explain", "what is", "how to",
        "define", "عرف", "اثبت", "prove",
    ]
    norm = text.lower()
    return any(ind in norm for ind in question_indicators) or len(text.split()) >= 4

_GREETINGS = {
    "slm", "selam", "merhaba", "mrb", "hey", "hi", "hello",
    "سلام", "سلاموا", "هاي", "هلو", "أهلا", "اهلا", "اهلاً",
    "السلام عليكم", "سلام عليكم", "وعليكم السلام", "مرحبا", "مرحباً",
    "صباح الخير", "مساء الخير", "صباح النور", "مساء النور",
    "هلا", "هلا والله", "ايش الاخبار", "كيف الحال",
}

def _is_greeting(text: str) -> bool:
    """Selamlama mesajı mı?"""
    norm = text.strip().lower()
    return norm in _GREETINGS or any(norm.startswith(g + " ") or norm == g for g in _GREETINGS)

def _try_math_eval(expr: str) -> Optional[str]:
    """
    Saf matematik ifadelerini Python ile hesapla.
    Güvenli: sadece sayı + operatörler.
    """
    # Arapça sayıları çevir
    ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    expr = expr.translate(ar_digits)

    # Basit ifade mi?
    clean = _re.sub(r'[0-9\s\+\-\*\/\(\)\.\,\^√πe]+', '', expr)
    if clean and not any(kw in clean.lower() for kw in ["sin","cos","tan","log","sqrt","pi","pow"]):
        return None

    # Python uyumlu hale getir
    expr2 = expr
    expr2 = expr2.replace("^", "**")
    expr2 = expr2.replace("√", "sqrt(").replace("×", "*").replace("÷", "/")
    expr2 = expr2.replace(",", ".")

    try:
        import math
        safe_env = {
            "__builtins__": {},
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "log": math.log, "log10": math.log10,
            "pi": math.pi, "e": math.e, "pow": math.pow, "abs": abs,
            "round": round, "floor": math.floor, "ceil": math.ceil,
        }
        # Güvenli eval
        result = eval(compile(expr2, "<string>", "eval"), safe_env)
        if isinstance(result, (int, float)):
            if isinstance(result, float) and result.is_integer():
                return str(int(result))
            return f"{result:.6g}"
    except Exception:
        pass
    return None

async def web_search_ddg(query: str) -> Optional[dict]:
    """
    DuckDuckGo Instant Answer API — ücretsiz, kayıt gerektirmez.
    Sonuç: {"text": ..., "source": ...} veya None
    """
    import aiohttp, urllib.parse

    # Cache kontrolü
    cache = load_search_cache()
    cache_key = query[:100]
    if cache_key in cache:
        entry = cache[cache_key]
        import time
        if time.time() - entry.get("ts", 0) < SEARCH_CACHE_TTL:
            return entry.get("result")

    url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&no_redirect=1"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=SEARCH_TIMEOUT),
                                   headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status != 200: return None
                data = await resp.json(content_type=None)

        # AbstractText → en iyi sonuç
        text = data.get("AbstractText","").strip()
        source = data.get("AbstractSource","") or "DuckDuckGo"
        url_result = data.get("AbstractURL","")

        # Answer (hesap sonucu vb.)
        if not text:
            text = data.get("Answer","").strip()
            source = "DuckDuckGo"

        # Definition
        if not text:
            text = data.get("Definition","").strip()
            source = data.get("DefinitionSource","") or "DuckDuckGo"

        # Related Topics
        if not text:
            topics = data.get("RelatedTopics",[])
            for t in topics[:3]:
                if isinstance(t, dict) and t.get("Text"):
                    text = t["Text"][:400].strip()
                    source = "DuckDuckGo"
                    break

        if not text: return None

        # HTML temizle
        text = _html.unescape(text)
        text = _re.sub(r'<[^>]+>', '', text)
        text = text[:800]

        result = {"text": text, "source": source, "url": url_result}

        # Cache'e kaydet
        import time
        cache[cache_key] = {"result": result, "ts": time.time()}
        save_search_cache(cache)
        return result

    except Exception as e:
        logger.warning(f"DDG arama hatası: {e}")
        return None

async def web_search_wikipedia(query: str, lang: str = "ar") -> Optional[dict]:
    """
    Wikipedia API — ücretsiz özet.
    lang: "ar" (Arapça) veya "en" (İngilizce)
    """
    import aiohttp, urllib.parse

    cache = load_search_cache()
    cache_key = f"wiki_{lang}_{query[:80]}"
    if cache_key in cache:
        entry = cache[cache_key]
        import time
        if time.time() - entry.get("ts",0) < SEARCH_CACHE_TTL:
            return entry.get("result")

    # Önce arama, sonra özet
    search_url = (
        f"https://{lang}.wikipedia.org/w/api.php"
        f"?action=query&list=search&srsearch={urllib.parse.quote(query)}"
        f"&format=json&srlimit=1"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=SEARCH_TIMEOUT)) as r:
                if r.status != 200: return None
                data = await r.json()

        results = data.get("query",{}).get("search",[])
        if not results: return None
        title = results[0]["title"]

        # Özet al
        summary_url = (
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/"
            f"{urllib.parse.quote(title)}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(summary_url, timeout=aiohttp.ClientTimeout(total=SEARCH_TIMEOUT)) as r:
                if r.status != 200: return None
                sdata = await r.json()

        text    = sdata.get("extract","")[:600]
        page_url= sdata.get("content_urls",{}).get("desktop",{}).get("page","")
        if not text: return None

        result = {"text": text, "source": "Wikipedia", "url": page_url}
        import time
        cache[cache_key] = {"result": result, "ts": time.time()}
        save_search_cache(cache)
        return result

    except Exception as e:
        logger.warning(f"Wikipedia arama hatası: {e}")
        return None

async def smart_ai_answer(uid: str, text: str) -> tuple[str, str] | None:
    """
    Akıllı AI yanıt motoru.
    Sıra: FAQ → Kural → Matematik hesap → Wikipedia → DuckDuckGo
    Döndürür: (yanıt_metni, kaynak_etiketi) veya None
    """
    # 1. Önce FAQ ve kurallar
    rule = ai_match_rules(text)
    if rule: return (rule, "rule")
    faq  = ai_match_faq(text)
    if faq: return (faq, "faq")

    # Soru değilse ya da çok kısa mesajsa AI'ya bırakma
    if not _is_question(text) or len(text.strip()) < 5:
        return None

    # 2. Saf matematik ifadesi mi?
    math_expr = _re.sub(r'[^\d\+\-\*\/\(\)\.\,\^\s√×÷sincotaglqrpie٠-٩]', '', text.lower())
    if len(math_expr.strip()) > 1:
        calc = _try_math_eval(text)
        if calc:
            return (f"= **{calc}**", "calc")

    # 3. Konuya göre Wikipedia'da ara
    subject = _detect_subject(text)
    if subject:
        # Önce Arapça Wikipedia
        wiki = await web_search_wikipedia(text, lang="ar")
        if wiki and wiki.get("text"):
            return (wiki["text"], f"Wikipedia — {wiki.get('url','')}")
        # İngilizce Wikipedia fallback
        wiki_en = await web_search_wikipedia(text, lang="en")
        if wiki_en and wiki_en.get("text"):
            return (wiki_en["text"], f"Wikipedia — {wiki_en.get('url','')}")

    # 4. DuckDuckGo genel arama
    ddg = await web_search_ddg(text)
    if ddg and ddg.get("text"):
        src = ddg.get("url","") or ddg.get("source","DuckDuckGo")
        return (ddg["text"], src)

    return None

def _subject_label(uid: str, subject: Optional[str]) -> str:
    labels = {
        "math":        "ai_subject_math",
        "physics":     "ai_subject_physics",
        "chemistry":   "ai_subject_chem",
        "programming": "ai_subject_prog",
        "engineering": "ai_subject_eng",
    }
    key = labels.get(subject, "")
    return L(uid, key) if key else ""

# ── Başarı Sistemi ─────────────────────────────────────────────
ACHIEVEMENT_DEFS = {
    "first_view":   {"name": "أول ملف 👁", "desc": "شاهدت أول ملف", "threshold": 1,  "metric": "views"},
    "ten_views":    {"name": "10 ملفات 📚", "desc": "شاهدت 10 ملفات", "threshold": 10, "metric": "views"},
    "fifty_views":  {"name": "50 ملف 🌟",   "desc": "شاهدت 50 ملف",  "threshold": 50, "metric": "views"},
    "first_fav":    {"name": "مفضلة ⭐",    "desc": "أضفت أول مفضلة", "threshold": 1,  "metric": "favs"},
    "explorer":     {"name": "مستكشف 🗺",   "desc": "فتحت 5 مجلدات", "threshold": 5,  "metric": "folders"},
}

def check_achievements(uid: str, context_data: dict):
    """Yeni başarılar kazanıldıysa listelerini döndür."""
    achs = load_achievements()
    user_achs = achs.get(str(uid), [])
    new_unlocked = []
    for key, defn in ACHIEVEMENT_DEFS.items():
        if key in user_achs: continue
        metric = defn["metric"]
        value  = context_data.get(metric, 0)
        if value >= defn["threshold"]:
            user_achs.append(key)
            new_unlocked.append(defn["name"])
    if new_unlocked:
        achs[str(uid)] = user_achs
        save_achievements(achs)
    return new_unlocked

# ── Liderboard ────────────────────────────────────────────────
def update_leaderboard(uid: str, points: int = 1):
    lb = load_leaderboard()
    uid = str(uid)
    lb[uid] = lb.get(uid, 0) + points
    save_leaderboard(lb)

def get_leaderboard(top_n: int = 10) -> list:
    lb    = load_leaderboard()
    users = load_users()
    result = []
    for uid, pts in sorted(lb.items(), key=lambda x: x[1], reverse=True)[:top_n]:
        u    = users.get(uid, {})
        name = u.get("full_name") or u.get("first_name") or f"ID:{uid}"
        result.append((name, pts))
    return result

# ── Dosya Geri Bildirimi ──────────────────────────────────────
def add_feedback(file_key: str, uid: str, stars: int):
    fb  = load_feedback()
    key = file_key[:100]
    if key not in fb:
        fb[key] = {}
    fb[key][str(uid)] = stars
    save_feedback(fb)

def get_feedback_stats(file_key: str) -> dict:
    fb    = load_feedback()
    votes = fb.get(file_key[:100], {})
    if not votes: return {"avg": 0, "count": 0}
    avg = sum(votes.values()) / len(votes)
    return {"avg": avg, "count": len(votes)}

# ── Sabit Mesaj ───────────────────────────────────────────────
def get_pinned_msg() -> str:
    msgs = load_pinned_msgs()
    return msgs.get("global", "")

def set_pinned_msg(text: str):
    msgs = load_pinned_msgs()
    if text.strip():
        msgs["global"] = text.strip()
    else:
        msgs.pop("global", None)
    save_pinned_msgs(msgs)

# ── Sınıf sistemi ─────────────────────────────────────────────
def get_user_class(uid: str) -> str:
    """Kullanıcının seçtiği sınıfı döndürür. None = seçmemiş."""
    return load_classes().get(str(uid))

def set_user_class(uid: str, cls: str):
    classes = load_classes()
    classes[str(uid)] = cls
    save_classes(classes)

def class_label(uid: str) -> str:
    """Kullanıcının sınıfını görüntülenebilir metin olarak döndürür."""
    cls = get_user_class(str(uid))
    if not cls: return L(uid, "class_unknown")
    d = CLASS_DEFS.get(cls, {})
    return d.get("ar", cls) if not is_main_admin(uid) else d.get("tr", cls)

def users_by_class(cls: str) -> list:
    """Belirli bir sınıftaki kullanıcı ID listesi."""
    classes = load_classes()
    return [uid for uid, c in classes.items() if c == cls]

# ── Spam / Rate-limit ─────────────────────────────────────────
def check_rate_limit(uid: str) -> bool:
    """True = geçebilir, False = spam."""
    import time
    now  = time.time()
    lst  = _rate_cache.get(uid, [])
    lst  = [t for t in lst if now - t < 60]   # son 60 saniye
    if len(lst) >= SPAM_LIMIT:
        _rate_cache[uid] = lst
        return False
    lst.append(now)
    _rate_cache[uid] = lst
    return True

# ── İç Yapay Zeka (FAQ + Kural motoru) ───────────────────────
def _normalize(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r'[؟?!.,،\-]+', ' ', text)
    # Arapça hareke kaldır
    text = re.sub(r'[\u064B-\u065F]', '', text)
    return ' '.join(text.split())

def ai_match_faq(text: str) -> Optional[str]:
    """FAQ'dan eşleşme ara. Bulunursa cevabı döndürür."""
    norm  = _normalize(text)
    faqs  = load_faq()
    best  = None
    best_score = 0
    for item in faqs:
        for kw in item.get("keywords", []):
            kw_norm = _normalize(kw)
            if kw_norm in norm or norm in kw_norm:
                score = len(kw_norm)
                if score > best_score:
                    best_score = score
                    best = item["answer"]
    return best

def ai_match_rules(text: str) -> Optional[str]:
    """Otomatik kural motorunda eşleşme ara."""
    norm  = _normalize(text)
    rules = load_auto_rules()
    for rule in rules:
        for kw in rule.get("keywords", []):
            if _normalize(kw) in norm:
                return rule["response"]
    return None

def ai_recommend_files(uid: str, n: int = 5) -> list:
    """
    Kullanıcının sınıfı + görüntüleme geçmişine göre dosya önerir.
    Basit kural: sınıfla eşleşen klasördeki en çok görüntülenen dosyalar.
    """
    cls = get_user_class(uid)
    if not cls: return []
    cls_name_ar = CLASS_DEFS.get(cls, {}).get("ar", "")
    content = load_content()
    vc      = load_view_counts()
    recent_keys = {
        (r["file"].get("file_id") or r["file"].get("caption","?"))
        for r in get_recently_viewed(uid)
    }

    candidates = []
    # Kullanıcının sınıfıyla eşleşen klasörleri tara
    for folder_name, folder in content.get("folders", {}).items():
        # Sınıf klasörüyle eşleşiyor mu?
        if cls_name_ar and cls_name_ar not in folder_name and cls not in folder_name:
            continue
        for f in folder.get("files", []):
            key   = f.get("file_id") or f.get("caption","?")
            count = vc.get(key, {}).get("count", 0) if isinstance(vc.get(key), dict) else 0
            if key not in recent_keys:
                candidates.append((f, count, folder_name))
        for sub_name, sub in folder.get("folders", {}).items():
            for f in sub.get("files", []):
                key   = f.get("file_id") or f.get("caption","?")
                count = vc.get(key, {}).get("count", 0) if isinstance(vc.get(key), dict) else 0
                if key not in recent_keys:
                    candidates.append((f, count, f"{folder_name} › {sub_name}"))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:n]

def ai_respond(uid: str, text: str) -> Optional[str]:
    """
    Gelen mesaja yanıt üret. None = yanıt yok (normal bot akışına bırak).
    Öncelik: kurallar > FAQ > öneri teklifi
    """
    rule = ai_match_rules(text)
    if rule: return rule
    faq  = ai_match_faq(text)
    if faq: return faq
    return None

# ── Admin İşlem Günlüğü ───────────────────────────────────────
def log_admin_action(admin_uid: str, action: str, detail: str = ""):
    log = load_admin_log()
    log.append({
        "uid":    str(admin_uid),
        "action": action,
        "detail": str(detail)[:80],
        "time":   datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_admin_log(log[-500:])

# ── Uyarı Sistemi ─────────────────────────────────────────────
def get_warns(uid: str) -> list:
    return load_warns().get(str(uid), [])

def add_warn(uid: str, reason: str, by_uid: str) -> int:
    warns = load_warns()
    uid   = str(uid)
    warns.setdefault(uid, []).append({
        "reason": reason, "by": by_uid,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_warns(warns)
    return len(warns[uid])

def clear_warns(uid: str):
    warns = load_warns()
    warns.pop(str(uid), None)
    save_warns(warns)

# ── Kullanıcı Notu ────────────────────────────────────────────
def get_note(uid: str) -> str:
    return load_notes().get(str(uid), "")

def set_note(uid: str, note: str):
    notes = load_notes()
    if note.strip():
        notes[str(uid)] = note.strip()
    else:
        notes.pop(str(uid), None)
    save_notes(notes)

# ── Favoriler ─────────────────────────────────────────────────
def get_favorites(uid: str) -> list:
    return load_favorites().get(str(uid), [])

def toggle_favorite(uid: str, f: dict) -> bool:
    """True=eklendi, False=çıkarıldı."""
    favs = load_favorites()
    uid  = str(uid)
    key  = f.get("file_id") or f.get("caption","?")
    lst  = favs.get(uid, [])
    match = [x for x in lst if (x.get("file_id") or x.get("caption","?")) == key]
    if match:
        for x in match: lst.remove(x)
        favs[uid] = lst
        save_favorites(favs)
        return False
    lst.append(f)
    favs[uid] = lst[-50:]
    save_favorites(favs)
    return True

def is_in_favorites(uid: str, f: dict) -> bool:
    key  = f.get("file_id") or f.get("caption","?")
    return any((x.get("file_id") or x.get("caption","?")) == key for x in get_favorites(uid))

# ── Son Görüntülenenler ───────────────────────────────────────
def add_recently_viewed(uid: str, f: dict):
    recent = load_recent()
    uid    = str(uid)
    lst    = recent.get(uid, [])
    key    = f.get("file_id") or f.get("caption","?")
    lst    = [x for x in lst if (x["file"].get("file_id") or x["file"].get("caption","?")) != key]
    lst.append({"file": f, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
    recent[uid] = lst[-RECENT_MAX:]
    save_recent(recent)

def get_recently_viewed(uid: str) -> list:
    return load_recent().get(str(uid), [])

# ── Klasör Aboneliği ──────────────────────────────────────────
def path_key(path: list) -> str:
    return "~~".join(path) if path else "__root__"

def is_subscribed(uid: str, path: list) -> bool:
    return path_key(path) in load_subs().get(str(uid), [])

def toggle_sub(uid: str, path: list) -> bool:
    subs = load_subs(); uid = str(uid); key = path_key(path)
    lst  = subs.setdefault(uid, [])
    if key in lst: lst.remove(key); subs[uid]=lst; save_subs(subs); return False
    lst.append(key); subs[uid]=lst; save_subs(subs); return True

def get_folder_subscribers(path: list) -> list:
    key = path_key(path)
    return [uid for uid, lst in load_subs().items() if key in lst]

# ── Klasör Açıklaması ─────────────────────────────────────────
def get_folder_desc(path: list) -> str:
    return load_folder_descs().get(path_key(path), "")

def set_folder_desc(path: list, desc: str):
    descs = load_folder_descs(); key = path_key(path)
    if desc.strip(): descs[key] = desc.strip()
    else: descs.pop(key, None)
    save_folder_descs(descs)

# ── Whitelist / Gizli Mod ─────────────────────────────────────
def is_whitelisted(uid: str) -> bool:
    wl = load_whitelist()
    if not wl.get("enabled"): return True
    return int(uid) == ADMIN_ID or is_admin(uid) or int(uid) in [int(x) for x in wl.get("users",[])]

# ── Tüm Klasör Yolları ────────────────────────────────────────
def all_folder_paths(node=None, prefix=None) -> list:
    if node is None:   node = load_content()
    if prefix is None: prefix = []
    result = []
    for name, sub in node.get("folders", {}).items():
        p = prefix + [name]
        result.append(p)
        result.extend(all_folder_paths(sub, p))
    return result

# ── Etkin Kullanıcı Filtresi ──────────────────────────────────
def active_users(days: int = 7) -> list:
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    users  = load_users()
    return [uid for uid, u in users.items()
            if u.get("last_seen","") >= cutoff and int(uid) != ADMIN_ID]

def new_users(days: int = 7) -> list:
    from datetime import timedelta
    msgs   = load_messages()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    users  = load_users()
    new    = []
    for uid, u in users.items():
        if int(uid) == ADMIN_ID: continue
        first_seen = None
        for m in msgs.get(uid, []):
            if m.get("type") == "command" and "/start" in m.get("content",""):
                first_seen = m.get("time","")[:10]; break
        if first_seen and first_seen >= cutoff:
            new.append(uid)
    return new

# ── Dosya görüntüleme sayacı ──────────────────────────────────
def get_file_view_count(f: dict) -> int:
    key = f.get("file_id") or f.get("caption","unknown")
    vc  = load_view_counts()
    v   = vc.get(key)
    return v.get("count", 0) if isinstance(v, dict) else 0

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
 WAIT_POLL_QUESTION, WAIT_POLL_OPTIONS, WAIT_POLL_COMMENT,
 WAIT_WARN_REASON, WAIT_USER_NOTE, WAIT_FOLDER_DESC,
 WAIT_FAQ_Q, WAIT_FAQ_A,
 WAIT_RULE_KW, WAIT_RULE_RESP,
 WAIT_SCHEDULE_HOURS, WAIT_SCHEDULE_MSG,
 WAIT_TAG, WAIT_SECRET_ID) = range(27)

ALL_BTNS = {
    TR["btn_content"],   AR["btn_content"],
    TR["btn_mgmt"],
    TR["btn_settings"],
    TR["btn_maint"],     AR["btn_maint"],
    TR["btn_search"],    AR["btn_search"],
    TR["btn_help"],      AR["btn_help"],
    TR["btn_favorites"], AR["btn_favorites"],
    TR["btn_recent"],    AR["btn_recent"],
    TR["ai_btn"],        AR["ai_btn"],
    TR["profile_btn"],   AR["profile_btn"],
    TR["btn_leaderboard"],AR["btn_leaderboard"],
    TR["btn_notes"],     AR["btn_notes"],
    TR["btn_reminder"],  AR["btn_reminder"],
    TR["anon_q_btn"],    AR["anon_q_btn"],
    TR["countdown_btn"], AR["countdown_btn"],
    TR["quiz_btn"],      AR["quiz_btn"],
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
        kb.append([InlineKeyboardButton(L(uid, "back"),  callback_data="nav|root")])
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
        # Satır 1: Ara + Mesaj Gönder
        row1 = []
        if ub.get("btn_search",   True): row1.append(KeyboardButton(AR["btn_search"]))
        if ub.get("btn_help",     True): row1.append(KeyboardButton(AR["btn_help"]))
        if row1: rows.append(row1)
        # Satır 2: AI Asistan + Profilim
        row2 = []
        if ub.get("ai_btn",       True): row2.append(KeyboardButton(AR["ai_btn"]))
        row2.append(KeyboardButton(AR["profile_btn"]))
        if row2: rows.append(row2)
        # Satır 3: Favoriler + Son Görüntülenen
        row3 = []
        if ub.get("btn_favorites",True): row3.append(KeyboardButton(AR["btn_favorites"]))
        if ub.get("btn_recent",   True): row3.append(KeyboardButton(AR["btn_recent"]))
        if row3: rows.append(row3)
        # Satır 4: Notlarım + Hatırlatıcım
        row4 = []
        if ub.get("btn_notes",    True): row4.append(KeyboardButton(AR["btn_notes"]))
        if ub.get("btn_reminder", True): row4.append(KeyboardButton(AR["btn_reminder"]))
        if row4: rows.append(row4)
        # Satır 5: Anonim Soru + Geri Sayım
        row5 = []
        if ub.get("anon_q_btn",   True): row5.append(KeyboardButton(AR["anon_q_btn"]))
        if ub.get("countdown_btn",True): row5.append(KeyboardButton(AR["countdown_btn"]))
        if row5: rows.append(row5)
        # Satır 6: Liderboard + Test
        row6 = []
        if ub.get("btn_leaderboard", True): row6.append(KeyboardButton(AR["btn_leaderboard"]))
        if ub.get("quiz_btn",     True): row6.append(KeyboardButton(AR["quiz_btn"]))
        if row6: rows.append(row6)
        if not rows: rows = [[]]
        return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def folder_text(folder, path, uid):
    uid    = str(uid)
    header = "📂 " + " › ".join(path) if path else L(uid, "home")
    lines  = [header, "─" * 22]
    # Klasör açıklaması
    desc = get_folder_desc(path)
    if desc:
        lines.append(f"💬 {desc}")
        lines.append("─" * 22)

    folds  = folder.get("folders", {})
    files  = folder.get("files",   [])

    # Kullanıcılar ana sayfada yalnızca kendi sınıf klasörlerini görür
    if not path and not is_admin(uid):
        cls    = get_user_class(uid)
        cls_ar = CLASS_DEFS.get(cls, {}).get("ar", "") if cls else ""
        if cls_ar:
            folds = {
                name: sub for name, sub in folds.items()
                if cls_ar in name or name in cls_ar
            }

    if folds:
        lines.append(L(uid, "folder_list"))
        for name, sub in folds.items():
            cnt = folder_item_count(sub)
            lines.append(f"  • {name}" + (f"  ({cnt})" if cnt else ""))
    if files:
        lines.append(L(uid, "file_list"))
        pinned = [f for f in files if f.get("pinned")]
        normal = [f for f in files if not f.get("pinned")]
        for f in pinned + normal:
            pin = "📌" if f.get("pinned") else "  "
            lines.append(f" {pin} {f.get('caption', f.get('name','?'))}")
    if is_admin(uid):
        s = load_settings()
        lines.append("─" * 22)
        lines.append(L(uid, "maint_on") if s["maintenance"] else L(uid, "maint_off"))
    return "\n".join(lines)

def folder_kb(path, folder, uid, page=0):
    uid         = str(uid)
    kb          = []
    raw_folders = folder.get("folders", {})
    # Kullanıcı ana sayfada sadece kendi sınıfını görür
    if not path and not is_admin(uid):
        cls    = get_user_class(uid)
        cls_ar = CLASS_DEFS.get(cls, {}).get("ar", "") if cls else ""
        if cls_ar:
            raw_folders = {
                name: sub for name, sub in raw_folders.items()
                if cls_ar in name or name in cls_ar
            }
    all_folders = list(raw_folders.items())
    PAGE_SIZE   = 20
    f_start     = page * PAGE_SIZE
    f_end       = f_start + PAGE_SIZE
    page_folders = all_folders[f_start:f_end]

    for name, sub in page_folders:
        cnt   = folder_item_count(sub)
        label = f"📁 {name}" + (f" ({cnt})" if cnt else "")
        kb.append([InlineKeyboardButton(label, callback_data=f"open|{name}")])

    # Dosyalar
    files = folder.get("files", [])
    for idx, f in enumerate(files[:12]):
        cap = f.get("caption", f.get("name", "?"))
        kb.append([InlineKeyboardButton(f"📎 {cap}", callback_data=f"getfile|{idx}")])

    # Sayfa navigasyonu
    total_pages = max(1, -(-len(all_folders) // PAGE_SIZE))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"page|{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if f_end < len(all_folders):
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
    await _send_file_get_msg(message, f, uid)

async def _send_file_get_msg(message, f: dict, uid: str):
    """Dosyayı gönderir ve gönderilen mesajı döndürür."""
    ftype = f.get("type",""); fid = f.get("file_id","")
    cap   = f.get("caption",""); url = f.get("url","")
    sent  = None
    try:
        if   ftype == "photo":     sent = await message.reply_photo(fid, caption=cap)
        elif ftype == "video":     sent = await message.reply_video(fid, caption=cap)
        elif ftype == "animation": sent = await message.reply_animation(fid, caption=cap)
        elif ftype == "document":  sent = await message.reply_document(fid, caption=cap)
        elif ftype == "audio":     sent = await message.reply_audio(fid, caption=cap)
        elif ftype == "voice":     sent = await message.reply_voice(fid, caption=cap)
        elif ftype == "link":      sent = await message.reply_text(f"🔗 {cap}\n{url}" if cap != url else f"🔗 {url}")
        elif ftype == "text":      sent = await message.reply_text(cap)
        else: sent = await message.reply_text(L(uid, "unsupported"))
        increment_view(f)
    except Exception as e:
        await message.reply_text(L(uid, "send_fail").format(e))
    return sent

# ================================================================
#  /start   /menu
# ================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; uid = str(user.id)

    is_new = register_user(user)
    log_user_message(user, "command", "/start")

    if is_blocked(uid) and not is_admin(uid): return

    # Gizli mod kontrolü
    if not is_admin(uid) and not is_whitelisted(uid):
        await update.message.reply_text(L(uid, "secret_deny")); return

    s = load_settings()
    context.user_data["path"] = []
    context.user_data["mode"] = "browse"
    context.user_data.pop("action", None)

    # /start mesajını sil
    try: await update.message.delete()
    except: pass

    # Bakım modu kontrolü (kullanıcılar için)
    if not is_admin(uid) and s["maintenance"]:
        await update.message.chat.send_message(
            s.get("maintenance_text", "🔧"),
            reply_markup=reply_kb(uid))
        return

    # Klavyeyi gönder
    await update.message.chat.send_message("👋", reply_markup=reply_kb(uid))

    # Yeni kullanıcı bildirimi (admin'e)
    if is_new and not is_admin(uid):
        u  = load_users().get(uid, {})
        un = f" @{u['username']}" if u.get("username") else ""
        try:
            await context.bot.send_message(
                ADMIN_ID,
                TR["new_user_notif"].format(
                    name=u.get("full_name") or u.get("first_name") or f"ID:{uid}",
                    un=un, uid=uid,
                    time=datetime.now().strftime("%Y-%m-%d %H:%M")),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(TR["msg_btn"], callback_data=f"dm_quick|{uid}")
                ]])
            )
        except Exception as e:
            logger.warning(f"Yeni kullanıcı bildirimi gönderilemedi: {e}")

    if is_admin(uid):
        # Admin — normal klasör göster
        await show_folder_new(update.message, uid)
        return

    # ── KULLANICI AKIŞI ──────────────────────────────────────
    cls = get_user_class(uid)

    if not cls:
        # Sınıf seçmemiş — karşılama + sınıf seçimi göster
        if s.get("bot_photo_id"):
            try:
                await update.message.chat.send_photo(
                    s["bot_photo_id"],
                    caption=s.get("welcome_msg") or "")
            except: pass
        elif s.get("welcome_msg"):
            # Karşılama mesajını sabit tut (silinmez)
            await update.message.chat.send_message(s["welcome_msg"])

        kb = [
            [InlineKeyboardButton(CLASS_DEFS["1"]["ar"], callback_data="class_pick|1"),
             InlineKeyboardButton(CLASS_DEFS["2"]["ar"], callback_data="class_pick|2")],
            [InlineKeyboardButton(CLASS_DEFS["3"]["ar"], callback_data="class_pick|3"),
             InlineKeyboardButton(CLASS_DEFS["4"]["ar"], callback_data="class_pick|4")],
        ]
        await update.message.chat.send_message(
            L(uid, "class_select_prompt"),
            reply_markup=InlineKeyboardMarkup(kb))
    else:
        # Sınıf seçmiş — direkt KENDI sınıfının klasörüne git
        cls_ar   = CLASS_DEFS[cls]["ar"]
        content  = load_content()
        # Sınıfa ait klasör adını bul (الاول, الثاني vb.)
        cls_folder_name = None
        for fname in content.get("folders", {}):
            if cls_ar in fname or fname in cls_ar:
                cls_folder_name = fname
                break

        if cls_folder_name:
            context.user_data["path"] = [cls_folder_name]
            await show_folder_new(update.message, uid, path=[cls_folder_name])
        else:
            # Eşleşen klasör bulunamadı — genel göster
            await show_folder_new(update.message, uid)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; uid = str(user.id)
    register_user(user)
    context.user_data["mode"]  = "browse"
    context.user_data.pop("action", None)

    if is_admin(uid):
        context.user_data["path"] = []
        await show_folder_new(update.message, uid)
        return

    # Kullanıcılar — kendi sınıf klasörüne git
    cls = get_user_class(uid)
    if cls:
        cls_ar   = CLASS_DEFS[cls]["ar"]
        content  = load_content()
        cls_fname = None
        for fname in content.get("folders", {}):
            if cls_ar in fname or fname in cls_ar:
                cls_fname = fname; break
        if cls_fname:
            context.user_data["path"] = [cls_fname]
            await show_folder_new(update.message, uid, path=[cls_fname])
            return
    context.user_data["path"] = []
    await show_folder_new(update.message, uid)
# ================================================================
#  REPLY KLAVYE HANDLER
# ================================================================

async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; uid = str(user.id)
    text = (update.message.text or "").strip()
    register_user(user)
    await _delete_last_inline(context, update.effective_chat.id)
    # Kullanıcının buton mesajını sil
    try: await update.message.delete()
    except: pass

    # Kullanıcının buton mesajını sil (sohbet temizliği)
    try: await update.message.delete()
    except: pass

    # Buton basıldığında önceki aksiyonu temizle (takılma önleme)
    context.user_data.pop("action", None)

    # Kullanıcı/alt-admin buton seçimini kaydet
    if not is_main_admin(uid) and not is_blocked(uid):
        log_user_message(user, "button", text)

    # ── Arama (herkes) ───────────────────────────────
    if text in (TR["btn_search"], AR["btn_search"]):
        context.user_data["action"] = "search"
        await update.message.reply_text(L(uid, "search_prompt"))
        return

    # ── Asistan (kullanıcılar) ───────────────────────
    if text in (TR["ai_btn"], AR["ai_btn"]):
        if not is_admin(uid):
            context.user_data["action"] = "ai_chat"
            recs = ai_recommend_files(uid, 3)
            txt  = L(uid,"ai_welcome") + "\n\n"
            if recs:
                txt += L(uid,"suggest_title") + "\n"
                for f, cnt, folder_name in recs:
                    txt += f"  📎 {f.get('caption','?')} ({folder_name})\n"
                txt += "\n"
            txt += ("💬 اكتب سؤالك الآن وسأجيب عليه فوراً 👇" 
                    if not is_main_admin(uid) else "💬 Sorunuzu yazın 👇")
            kb = [
                [InlineKeyboardButton("❓ الأسئلة الشائعة", callback_data="ai|faq")],
                [InlineKeyboardButton("◀️ رجوع", callback_data="nav|root")],
            ]
            sent = await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            context.user_data["last_inline_msg"] = sent.message_id
        return

    # ── Profil (kullanıcılar) ────────────────────────
    if text in (TR["profile_btn"], AR["profile_btn"]):
        if not is_admin(uid):
            u    = load_users().get(uid, {})
            name = u.get("full_name") or u.get("first_name") or "—"
            cls  = class_label(uid)
            favs = len(get_favorites(uid))
            rcnt = len(get_recently_viewed(uid))
            warns_list = get_warns(uid)
            txt = (
                f"👤 *{name}*\n"
                f"🆔 {uid}\n"
                f"🎓 {L(uid,'class_label').format(cls)}\n"
                f"⭐ {L(uid,'fav_list')}: {favs}\n"
                f"🕐 {L(uid,'recent_list')}: {rcnt}\n"
                f"⚠️ {L(uid,'warn_count_label').format(len(warns_list), MAX_WARNS)}"
            )
            kb = [[InlineKeyboardButton(L(uid,"class_change_btn"), callback_data="class_change")]]
            await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return

    # ── Favoriler ────────────────────────────────────
    if text in (TR["btn_favorites"], AR["btn_favorites"]):
        if not is_admin(uid):
            favs = get_favorites(uid)
            if not favs:
                await update.message.reply_text(L(uid,"fav_empty")); return
            kb = []
            for idx, f in enumerate(favs[:15]):
                cap = f.get("caption", f.get("name","?"))[:35]
                kb.append([InlineKeyboardButton(f"⭐ {cap}", callback_data=f"fav|open|{idx}")])
            kb.append([InlineKeyboardButton(L(uid,"back"),  callback_data="nav|root")])
            await update.message.reply_text(L(uid,"fav_list"), reply_markup=InlineKeyboardMarkup(kb))
        return

    # ── Son Görüntülenenler ──────────────────────────
    if text in (TR["btn_recent"], AR["btn_recent"]):
        if not is_admin(uid):
            recent = get_recently_viewed(uid)
            if not recent:
                await update.message.reply_text(L(uid,"recent_empty")); return
            kb = []
            for entry in reversed(recent[-10:]):
                f   = entry["file"]
                cap = f.get("caption", f.get("name","?"))[:35]
                t   = entry.get("time","")[-5:]
                key = f.get("file_id") or f.get("caption","?")
                kb.append([InlineKeyboardButton(f"🕐 {t} — {cap}", callback_data=f"recent|open|{key}")])
            kb.append([InlineKeyboardButton(L(uid,"back"),  callback_data="nav|root")])
            await update.message.reply_text(L(uid,"recent_list"), reply_markup=InlineKeyboardMarkup(kb))
        return

    # ── Liderboard (herkes) ──────────────────────────
    if text in (TR["btn_leaderboard"], AR["btn_leaderboard"]):
        lb    = get_leaderboard(10)
        lines = [L(uid,"leaderboard_title"), "─"*22]
        medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        for i,(name,pts) in enumerate(lb):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            lines.append(f"{medal} {name[:25]}  —  {pts} pts")
        if not lb: lines.append(L(uid,"leaderboard_empty"))
        own_pts = load_leaderboard().get(uid, 0)
        lines.append(f"\n{'─'*22}\n👤 {L(uid,'profile_title')}: {own_pts} pts")
        await update.message.reply_text("\n".join(lines))
        return

    # ── Notlarım ─────────────────────────────────────
    if text in (TR["btn_notes"], AR["btn_notes"]):
        if not is_admin(uid):
            note = get_personal_note(uid)
            kb = [
                [InlineKeyboardButton("✏️ " + ("Notu Düzenle" if is_main_admin(uid) else "تعديل الملاحظة"),
                                      callback_data="notes|edit")],
                [InlineKeyboardButton("🗑 " + ("Sil" if is_main_admin(uid) else "حذف"),
                                      callback_data="notes|del")],
                [InlineKeyboardButton(L(uid,"back"), callback_data="nav|root")],
            ]
            txt = (
                f"📝 {L(uid,'notes_title')}\n{'─'*22}\n\n"
                + (note if note else L(uid,"notes_empty"))
            )
            sent = await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            context.user_data["last_inline_msg"] = sent.message_id
        return

    # ── Hatırlatıcım ─────────────────────────────────
    if text in (TR["btn_reminder"], AR["btn_reminder"]):
        if not is_admin(uid):
            rems = get_user_reminders(uid)
            if not rems:
                kb = [
                    [InlineKeyboardButton("➕ " + ("Ekle" if is_main_admin(uid) else "إضافة"),
                                          callback_data="reminder|add")],
                    [InlineKeyboardButton(L(uid,"back"), callback_data="nav|root")],
                ]
                await update.message.reply_text(L(uid,"reminder_none"), reply_markup=InlineKeyboardMarkup(kb))
            else:
                import time
                now = time.time()
                lines = [L(uid,"reminder_list").format(len(rems))]
                kb = []
                for i, r in enumerate(rems[:10]):
                    left = int((r["fire_ts"] - now) / 60)
                    left_str = f"{left}dk" if left < 60 else f"{left//60}sa"
                    lines.append(f"\n🔔 {r['text'][:40]}\n   ⏰ {left_str} kaldı")
                    kb.append([InlineKeyboardButton(f"🗑 {r['text'][:25]}", callback_data=f"reminder|del|{i}")])
                kb.append([InlineKeyboardButton("➕ Yeni", callback_data="reminder|add")])
                kb.append([InlineKeyboardButton(L(uid,"back"), callback_data="nav|root")])
                sent = await update.message.reply_text(
                    "\n".join(lines), reply_markup=InlineKeyboardMarkup(kb))
                context.user_data["last_inline_msg"] = sent.message_id
        return

    # ── Anonim Soru ──────────────────────────────────
    if text in (TR["anon_q_btn"], AR["anon_q_btn"]):
        if not is_admin(uid):
            context.user_data["action"] = "anon_q"
            await update.message.reply_text(L(uid,"anon_q_prompt"))
        return

    # ── Geri Sayım / Yaklaşan Sınavlar ──────────────
    if text in (TR["countdown_btn"], AR["countdown_btn"]):
        cls = get_user_class(uid) if not is_admin(uid) else ""
        cds = get_countdowns(cls)
        if not cds:
            await update.message.reply_text(L(uid,"countdown_none"))
        else:
            lines = [f"⏳ {'Yaklaşan Sınavlar' if is_main_admin(uid) else 'الامتحانات القادمة'}",
                     "─"*22]
            for c in cds[:8]:
                days = c["days_left"]
                if days == 0:
                    when = "🔴 اليوم!" if not is_main_admin(uid) else "🔴 Bugün!"
                elif days == 1:
                    when = "🟠 غداً" if not is_main_admin(uid) else "🟠 Yarın"
                elif days <= 7:
                    when = f"🟡 {days} {'أيام' if not is_main_admin(uid) else 'gün'}"
                else:
                    when = f"🟢 {days} {'يوم' if not is_main_admin(uid) else 'gün'}"
                lines.append(f"\n📅 {c['name']}\n   {when} — {c['date']}")
            await update.message.reply_text("\n".join(lines))
        return

    # ── Mini Test (Quiz) ─────────────────────────────
    if text in (TR["quiz_btn"], AR["quiz_btn"]):
        if not is_admin(uid):
            quizzes = [q for q in load_quizzes() if q.get("active")]
            cls = get_user_class(uid)
            quizzes = [q for q in quizzes if not q.get("cls") or q.get("cls") == cls]
            if not quizzes:
                await update.message.reply_text(L(uid,"quiz_none"))
            else:
                q = quizzes[0]
                opts = q.get("options", [])
                kb = [[InlineKeyboardButton(f"{'ABCD'[i]}. {o}", callback_data=f"quiz|ans|{q['id']}|{i}")]
                      for i, o in enumerate(opts)]
                kb.append([InlineKeyboardButton(L(uid,"back"), callback_data="nav|root")])
                await update.message.reply_text(
                    f"📝 {q.get('question','?')}\n{'─'*22}",
                    reply_markup=InlineKeyboardMarkup(kb))
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
                [InlineKeyboardButton(L(uid,"pin_file"),      callback_data="extra|pin"),
                 InlineKeyboardButton(L(uid,"move_file"),     callback_data="extra|move")],
                [InlineKeyboardButton(L(uid,"copy_file"),     callback_data="extra|copy"),
                 InlineKeyboardButton(L(uid,"sort_az"),       callback_data="extra|sort_az")],
                [InlineKeyboardButton(L(uid,"sort_views"),    callback_data="extra|sort_views"),
                 InlineKeyboardButton(L(uid,"folder_desc_btn"),callback_data="extra|folder_desc")],
                [InlineKeyboardButton(L(uid,"back"),          callback_data="nav|root")],
            ]
        else:
            kb = [
                [InlineKeyboardButton(L(uid,"add_folder"), callback_data="cnt|add_folder"),
                 InlineKeyboardButton(L(uid,"add_file"),   callback_data="cnt|add_file")],
                [InlineKeyboardButton(L(uid,"back"),       callback_data="nav|root")],
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
            [InlineKeyboardButton(TR["stats"],            callback_data="mgmt|stats"),
             InlineKeyboardButton(TR["users"],            callback_data="mgmt|users")],
            [InlineKeyboardButton(TR["add_admin"],        callback_data="mgmt|add_admin"),
             InlineKeyboardButton(TR["del_admin"],        callback_data="mgmt|del_admin")],
            [InlineKeyboardButton(TR["dm_user"],          callback_data="mgmt|dm_user"),
             InlineKeyboardButton(TR["broadcast"],        callback_data="mgmt|broadcast")],
            [InlineKeyboardButton(TR["bcast_targeted"],   callback_data="bcast|panel"),
             InlineKeyboardButton("🎓 Sınıf İstat.",     callback_data="mgmt|class_stats")],
            [InlineKeyboardButton(TR["poll_btn"],         callback_data="mgmt|poll"),
             InlineKeyboardButton(TR["admin_log_btn"],    callback_data="admin|log")],
            [InlineKeyboardButton(TR["backup_btn"],       callback_data="backup|do"),
             InlineKeyboardButton(TR["export_users_btn"], callback_data="export|users")],
            [InlineKeyboardButton(TR["bcast_history_btn"],callback_data="bcast|history"),
             InlineKeyboardButton("🏆 Liderboard",       callback_data="misc|leaderboard")],
            [InlineKeyboardButton("⏳ Sınav Ekle",       callback_data="countdown|add"),
             InlineKeyboardButton("❓ Anonim Sorular",   callback_data="admin|anon_q")],
            [InlineKeyboardButton("📝 Quiz Oluştur",     callback_data="admin|quiz_create"),
             InlineKeyboardButton("📊 Sınıf Analizi",   callback_data="admin|class_analysis")],
            [InlineKeyboardButton("◀️ Geri",              callback_data="nav|root")],
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
            f"📄 Açıklama: {str(s.get('bot_description','—'))[:40]}...\n"
            f"🖼 Fotoğraf: {'✅' if s.get('bot_photo_id') else '❌'}\n"
            f"🔧 Bakım metni: {str(s.get('maintenance_text','—'))[:40]}\n"
            f"🚫 Engellenenler: {len(load_blocked())} kişi"
        )
        kb = [
            [InlineKeyboardButton("📝 Bot Adı",          callback_data="set|name"),
             InlineKeyboardButton("💬 Karşılama",         callback_data="set|welcome")],
            [InlineKeyboardButton("🖼 Bot Fotoğrafı",    callback_data="set|photo"),
             InlineKeyboardButton("📄 Bot Açıklaması",   callback_data="set|set_description")],
            [InlineKeyboardButton("🔧 Bakım Metni",      callback_data="set|maint_text"),
             InlineKeyboardButton(TR["set_blocked_btn"], callback_data="set|blocked")],
            [InlineKeyboardButton(TR["btn_mgmt_btn"],    callback_data="set|btn_mgmt"),
             InlineKeyboardButton(TR["secret_mode_btn"], callback_data="secret|panel")],
            [InlineKeyboardButton("❓ FAQ Yönetimi",     callback_data="faqmgmt|panel"),
             InlineKeyboardButton("⚡ Otomatik Kurallar",callback_data="rulemgmt|panel")],
            [InlineKeyboardButton(TR["pin_msg_btn"],      callback_data="set|pin_msg"),
             InlineKeyboardButton(TR["bcast_history_btn"],callback_data="bcast|history")],
            [InlineKeyboardButton("◀️ Geri",             callback_data="nav|root")],
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

    # ── Sınıf Seçimi ─────────────────────────────────
    if cb.startswith("class_pick|"):
        cls = cb.split("|")[1]
        if cls in CLASS_DEFS:
            set_user_class(uid, cls)
            cls_ar    = CLASS_DEFS[cls]["ar"]
            cls_tr    = CLASS_DEFS[cls]["tr"]
            cls_name  = cls_ar if not is_main_admin(uid) else cls_tr
            # Sınıfa ait klasörü bul ve oraya git
            content2  = load_content()
            cls_folder = None
            for fname in content2.get("folders", {}):
                if cls_ar in fname or fname in cls_ar:
                    cls_folder = fname
                    break
            confirm_text = L(uid, "class_selected").format(cls_name)
            if cls_folder:
                context.user_data["path"] = [cls_folder]
                await query.edit_message_text(confirm_text)
                # Klasörü yeni mesaj olarak göster
                await show_folder_new(query.message, uid, path=[cls_folder])
            else:
                await query.edit_message_text(confirm_text)
                await show_folder_new(query.message, uid)
        return ConversationHandler.END

    if cb == "class_change":
        kb = [
            [InlineKeyboardButton(CLASS_DEFS["1"]["ar"], callback_data="class_pick|1"),
             InlineKeyboardButton(CLASS_DEFS["2"]["ar"], callback_data="class_pick|2")],
            [InlineKeyboardButton(CLASS_DEFS["3"]["ar"], callback_data="class_pick|3"),
             InlineKeyboardButton(CLASS_DEFS["4"]["ar"], callback_data="class_pick|4")],
            [InlineKeyboardButton(L(uid,"cancel"), callback_data="close")],
        ]
        await query.edit_message_text(L(uid,"class_change_prompt"), reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END

    # ── Favoriler ─────────────────────────────────────
    if cb.startswith("fav|"):
        action = cb.split("|")[1]
        if action == "open":
            idx  = int(cb.split("|")[2])
            favs = get_favorites(uid)
            if idx < len(favs):
                f = favs[idx]
                await _send_file(query.message, f, uid)
                log_user_message(user, "file_view", f.get("caption",""))
        elif action == "toggle":
            key  = cb.split("|")[2]
            # key = file_id or caption, find in recently viewed or content
            recent = get_recently_viewed(uid)
            for entry in recent:
                f = entry["file"]
                fk = f.get("file_id") or f.get("caption","?")
                if fk == key:
                    added = toggle_favorite(uid, f)
                    await query.answer(L(uid,"fav_added") if added else L(uid,"fav_removed"), show_alert=True)
                    return ConversationHandler.END
            await query.answer("❓", show_alert=True)
        return ConversationHandler.END

    # ── Son Görüntülenenler ───────────────────────────
    if cb.startswith("recent|"):
        action = cb.split("|")[1]
        if action == "open":
            key    = cb.split("|",2)[2]
            recent = get_recently_viewed(uid)
            for entry in recent:
                f = entry["file"]
                fk = f.get("file_id") or f.get("caption","?")
                if fk == key:
                    await _send_file(query.message, f, uid)
                    log_user_message(user, "file_view", f.get("caption",""))
                    return ConversationHandler.END
            await query.answer(L(uid,"file_notfound"), show_alert=True)
        return ConversationHandler.END

    # ── Klasör Aboneliği ──────────────────────────────
    if cb == "sub|toggle":
        added = toggle_sub(uid, path)
        await query.answer(L(uid,"subscribed_ok") if added else L(uid,"unsubscribed_ok"), show_alert=True)
        await show_folder(query, context, path)
        return ConversationHandler.END

    # ── İç Yapay Zeka / FAQ ───────────────────────────
    if cb.startswith("ai|") and not is_admin(uid):
        action = cb.split("|")[1]
        if action == "faq":
            faqs = load_faq()
            if not faqs:
                await query.answer(L(uid,"faq_empty"), show_alert=True)
                return ConversationHandler.END
            lines = [L(uid,"faq_list_title").format(len(faqs))]
            for item in faqs[:15]:
                q = item.get("keywords",["?"])[0]
                lines.append(f"\n❓ {q}\n💬 {item.get('answer','')[:80]}")
            await query.edit_message_text(
                "\n".join(lines)[:4000],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"back"),  callback_data="nav|root")]]))
        return ConversationHandler.END

    # ── FAQ Yönetimi (admin) ──────────────────────────
    if cb.startswith("faqmgmt|") and is_main_admin(uid):
        action = cb.split("|")[1]
        if action == "panel":
            faqs = load_faq()
            kb = [
                [InlineKeyboardButton(TR["faq_add_btn"],  callback_data="faqmgmt|add"),
                 InlineKeyboardButton(TR["faq_list_btn"], callback_data="faqmgmt|list")],
                [InlineKeyboardButton(TR["faq_del_btn"],  callback_data="faqmgmt|del")],
                [InlineKeyboardButton("◀️ Geri",          callback_data="nav|root")],
            ]
            await query.edit_message_text(
                f"{TR['faq_panel']}\n\n📋 Toplam: {len(faqs)} soru",
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END
        if action == "add":
            context.user_data["action"] = "faq_q"
            await query.edit_message_text(TR["faq_enter_q"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_FAQ_Q
        if action == "list":
            faqs = load_faq()
            if not faqs:
                await query.answer(TR["faq_empty"], show_alert=True); return ConversationHandler.END
            lines = [f"{TR['faq_list_title'].format(len(faqs))}"]
            for i, item in enumerate(faqs):
                q = ", ".join(item.get("keywords",[]))[:50]
                a = item.get("answer","")[:60]
                lines.append(f"\n{i+1}. ❓ {q}\n   💬 {a}")
            await query.edit_message_text(
                "\n".join(lines)[:4000],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")]]))
            return ConversationHandler.END
        if action == "del":
            faqs = load_faq()
            if not faqs:
                await query.answer(TR["faq_empty"], show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🗑 {item.get('keywords',['?'])[0][:40]}",
                                        callback_data=f"faqmgmt|del_confirm|{i}")]
                  for i, item in enumerate(faqs)]
            kb.append([InlineKeyboardButton(TR["cancel"], callback_data="close")])
            await query.edit_message_text("Silinecek soruyu seçin:", reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END
        if action == "del_confirm":
            idx  = int(cb.split("|")[2])
            faqs = load_faq()
            if 0 <= idx < len(faqs):
                faqs.pop(idx); save_faq(faqs)
            await query.answer(TR["faq_deleted"], show_alert=True)
            try: await query.delete_message()
            except: pass
            return ConversationHandler.END

    # ── Otomatik Kural Yönetimi (admin) ──────────────
    if cb.startswith("rulemgmt|") and is_main_admin(uid):
        action = cb.split("|")[1]
        if action == "panel":
            rules = load_auto_rules()
            kb = [
                [InlineKeyboardButton(TR["rule_add_btn"],  callback_data="rulemgmt|add"),
                 InlineKeyboardButton(TR["rule_list_btn"], callback_data="rulemgmt|list")],
                [InlineKeyboardButton(TR["rule_del_btn"],  callback_data="rulemgmt|del")],
                [InlineKeyboardButton("◀️ Geri",           callback_data="nav|root")],
            ]
            await query.edit_message_text(
                f"{TR['rule_panel']}\n\n⚡ Toplam: {len(rules)} kural",
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END
        if action == "add":
            context.user_data["action"] = "rule_kw"
            await query.edit_message_text(TR["rule_enter_kw"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_RULE_KW
        if action == "list":
            rules = load_auto_rules()
            if not rules:
                await query.answer(TR["rule_empty"], show_alert=True); return ConversationHandler.END
            lines = [f"⚡ Kurallar ({len(rules)} adet):"]
            for i, r in enumerate(rules):
                kws  = ", ".join(r.get("keywords",[]))[:40]
                resp = r.get("response","")[:50]
                lines.append(f"\n{i+1}. 🔍 {kws}\n   💬 {resp}")
            await query.edit_message_text(
                "\n".join(lines)[:4000],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")]]))
            return ConversationHandler.END
        if action == "del":
            rules = load_auto_rules()
            if not rules:
                await query.answer(TR["rule_empty"], show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🗑 {', '.join(r.get('keywords',[]))[:40]}",
                                        callback_data=f"rulemgmt|del_confirm|{i}")]
                  for i, r in enumerate(rules)]
            kb.append([InlineKeyboardButton(TR["cancel"], callback_data="close")])
            await query.edit_message_text("Silinecek kuralı seçin:", reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END
        if action == "del_confirm":
            idx   = int(cb.split("|")[2])
            rules = load_auto_rules()
            if 0 <= idx < len(rules):
                rules.pop(idx); save_auto_rules(rules)
            await query.answer(TR["rule_deleted"], show_alert=True)
            try: await query.delete_message()
            except: pass
            return ConversationHandler.END

    # ── Yedekleme (admin) ────────────────────────────
    if cb == "backup|do" and is_main_admin(uid):
        await query.answer(TR["backup_sending"], show_alert=False)
        files_to_send = [
            (DATA_FILE,     "bot_data.json"),
            (USERS_FILE,    "users.json"),
            (MESSAGES_FILE, "user_messages.json"),
            (SETTINGS_FILE, "settings.json"),
            (POLLS_FILE,    "polls.json"),
            (CLASS_FILE,    "user_classes.json"),
            (FAQ_FILE,      "faq.json"),
            (VIEW_COUNTS_FILE, "view_counts.json"),
        ]
        sent_count = 0
        for fpath, fname in files_to_send:
            if os.path.exists(fpath):
                try:
                    with open(fpath, "rb") as f:
                        await context.bot.send_document(
                            int(uid), f, filename=fname,
                            caption=f"💾 {fname}")
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"Yedek gönderilemedi {fname}: {e}")
        await context.bot.send_message(int(uid), TR["backup_done"].format(sent_count))
        log_admin_action(uid, "BACKUP", f"{sent_count} dosya yedeklendi")
        return ConversationHandler.END

    # ── Kullanıcı dışa aktar (admin) ────────────────
    if cb == "export|users" and is_main_admin(uid):
        users   = load_users()
        classes = load_classes()
        lines = ["ID,Ad,Kullanıcı Adı,Sınıf,Son Görülme"]
        for uid_, u in users.items():
            if int(uid_) == ADMIN_ID: continue
            cls  = CLASS_DEFS.get(classes.get(uid_,""), {}).get("tr","—")
            name = u.get("full_name") or u.get("first_name","—")
            un   = u.get("username","—")
            last = u.get("last_seen","—")
            lines.append(f"{uid_},{name},{un},{cls},{last}")
        csv_text = "\n".join(lines).encode("utf-8-sig")
        import io
        await context.bot.send_document(
            int(uid),
            io.BytesIO(csv_text),
            filename="kullanici_listesi.csv",
            caption=TR["export_done"].format(len(lines)-1))
        log_admin_action(uid, "EXPORT_USERS", f"{len(lines)-1} kullanıcı")
        return ConversationHandler.END

    # ── Hedefli Duyuru ────────────────────────────────
    if cb.startswith("bcast|") and is_main_admin(uid):
        action = cb.split("|")[1]
        if action == "panel":
            kb = [
                [InlineKeyboardButton(TR["bcast_all"],    callback_data="bcast|target|all"),
                 InlineKeyboardButton(TR["bcast_active"], callback_data="bcast|target|active")],
                [InlineKeyboardButton(TR["bcast_new"],    callback_data="bcast|target|new"),
                 InlineKeyboardButton(TR["bcast_class"],  callback_data="bcast|class_select")],
                [InlineKeyboardButton("◀️ Geri",          callback_data="nav|root")],
            ]
            await query.edit_message_text(TR["bcast_targeted"], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END
        if action == "class_select":
            kb = [[InlineKeyboardButton(CLASS_DEFS[c]["tr"], callback_data=f"bcast|target|class_{c}")]
                  for c in CLASS_DEFS]
            kb.append([InlineKeyboardButton(TR["cancel"], callback_data="close")])
            await query.edit_message_text(TR["bcast_class_select"], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END
        if action == "target":
            t = cb.split("|")[2]
            if t == "all":
                targets = [uid_ for uid_ in load_users() if int(uid_) != ADMIN_ID and not is_blocked(uid_)]
                label   = TR["bcast_all"]
            elif t == "active":
                targets = [uid_ for uid_ in active_users(7) if not is_blocked(uid_)]
                label   = TR["bcast_active"]
            elif t == "new":
                targets = [uid_ for uid_ in new_users(7) if not is_blocked(uid_)]
                label   = TR["bcast_new"]
            elif t.startswith("class_"):
                cls     = t.split("_")[1]
                targets = [uid_ for uid_ in users_by_class(cls) if not is_blocked(uid_)]
                label   = CLASS_DEFS.get(cls,{}).get("tr","?")
            else:
                targets = []
                label   = "?"
            context.user_data["bcast_targets"] = targets
            context.user_data["bcast_label"]   = label
            context.user_data["action"]        = "broadcast_targeted"
            await query.edit_message_text(
                TR["bcast_confirm"].format(len(targets)) + f"\n\n{TR['bcast_target_set'].format(label)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Evet, Gönder", callback_data="bcast|confirm"),
                     InlineKeyboardButton(TR["cancel"],      callback_data="close")],
                ]))
            return ConversationHandler.END
        if action == "confirm":
            targets = context.user_data.get("bcast_targets", [])
            label   = context.user_data.get("bcast_label","")
            context.user_data.pop("bcast_targets", None)
            context.user_data.pop("bcast_label",   None)
            context.user_data["action"] = "broadcast"
            await query.edit_message_text(
                TR["broadcast_enter"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            context.user_data["broadcast_targets"] = targets
            return WAIT_BROADCAST_MSG

    # ── Admin İşlem Günlüğü (admin) ──────────────────
    if cb == "admin|log" and is_main_admin(uid):
        log  = load_admin_log()
        if not log:
            await query.answer(TR["admin_log_empty"], show_alert=True); return ConversationHandler.END
        lines = [TR["admin_log_title"]]
        for entry in reversed(log[-30:]):
            lines.append(
                f"🕐 {entry['time']}\n"
                f"  ⚙️ {entry['action']}"
                + (f": {entry['detail']}" if entry.get('detail') else "")
            )
        await query.edit_message_text(
            "\n".join(lines)[:4000],
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")]]))
        return ConversationHandler.END

    # ── Anonim Sorular (admin görüntüle) ─────────────
    if cb == "admin|anon_q" and is_main_admin(uid):
        qs = load_anon_q()
        if not qs:
            await query.answer("❓ Henüz anonim soru yok.", show_alert=True)
            return ConversationHandler.END
        lines = [f"❓ ANONİM SORULAR ({len(qs)} adet)", "─"*24]
        kb = []
        for i, q in enumerate(qs[-20:]):
            cls_name = CLASS_DEFS.get(q.get("cls",""),{}).get("ar","?")
            lines.append(f"\n{i+1}. [{cls_name}] {q['text'][:80]}\n   🕐 {q.get('time','')}")
            kb.append([InlineKeyboardButton(
                f"📢 رد على #{i+1}", callback_data=f"anon|reply|{len(qs)-20+i}")])
        kb.append([InlineKeyboardButton("🗑 Tümünü Temizle", callback_data="anon|clear")])
        kb.append([InlineKeyboardButton("◀️ Geri", callback_data="nav|root")])
        await query.edit_message_text("\n".join(lines)[:4000], reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END

    if cb.startswith("anon|") and is_main_admin(uid):
        parts = cb.split("|")
        if parts[1] == "clear":
            save_anon_q([])
            await query.answer("✅ Temizlendi", show_alert=True)
            await query.delete_message()
        elif parts[1] == "reply" and len(parts) > 2:
            idx = int(parts[2])
            qs = load_anon_q()
            q_text = qs[idx]["text"] if 0 <= idx < len(qs) else "?"
            context.user_data["action"] = "anon_reply"
            context.user_data["anon_q_text"] = q_text
            await query.edit_message_text(
                f"❓ {q_text}\n\n{'─'*22}\nCevabınızı yazın:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ İptal", callback_data="nav|root")
                ]]))
            return WAIT_FOLDER
        return ConversationHandler.END

    # ── Quiz Oluştur (admin) ──────────────────────────
    if cb == "admin|quiz_create" and is_main_admin(uid):
        context.user_data["action"] = "quiz_question"
        await query.edit_message_text(
            "📝 Quiz sorusunu yazın:\n\n"
            "Format:\n"
            "Soru metni\n"
            "A. Seçenek 1\n"
            "B. Seçenek 2\n"
            "C. Seçenek 3\n"
            "D. Seçenek 4\n"
            "CEVAP: A",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ İptal", callback_data="nav|root")
            ]]))
        return WAIT_FOLDER

    # ── Sınıf Analizi (admin) ─────────────────────────
    if cb == "admin|class_analysis" and is_main_admin(uid):
        users_d = load_users()
        msgs_d  = load_messages()
        lines   = ["📊 SINIF ANALİZİ", "═"*24]
        for cls_id, cls_def in CLASS_DEFS.items():
            cls_users = users_by_class(cls_id)
            cls_msgs  = sum(len(msgs_d.get(u,"")) for u in cls_users)
            active_7  = sum(1 for u in cls_users
                           if u in msgs_d and msgs_d[u] and
                           msgs_d[u][-1].get("time","") >= (datetime.now().replace(
                               hour=0,minute=0,second=0).strftime("%Y-%m-%d")))
            lines.append(
                f"\n🎓 {cls_def['ar']}\n"
                f"  👥 {len(cls_users)} öğrenci\n"
                f"  💬 {cls_msgs} kayıt\n"
                f"  🟢 {active_7} bugün aktif"
            )
        await query.edit_message_text(
            "\n".join(lines)[:4000],
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Geri", callback_data="nav|root")
            ]]))
        return ConversationHandler.END

    # ── Gizli Mod / Whitelist (admin) ────────────────
    if cb.startswith("secret|") and is_main_admin(uid):
        action = cb.split("|")[1]
        wl = load_whitelist()
        if action == "panel":
            mode_txt = TR["secret_on"] if wl.get("enabled") else TR["secret_off"]
            toggle_lbl = "🔓 Kapat" if wl.get("enabled") else "🔒 Aç"
            kb = [
                [InlineKeyboardButton(toggle_lbl,          callback_data="secret|toggle"),
                 InlineKeyboardButton(TR["secret_add_btn"],callback_data="secret|add")],
                [InlineKeyboardButton(TR["secret_list"].format(len(wl.get("users",[]))),
                                                           callback_data="secret|list")],
                [InlineKeyboardButton("◀️ Geri",           callback_data="nav|root")],
            ]
            await query.edit_message_text(mode_txt, reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END
        if action == "toggle":
            wl["enabled"] = not wl.get("enabled", False)
            save_whitelist(wl)
            mode_txt = TR["secret_on"] if wl["enabled"] else TR["secret_off"]
            await query.answer(mode_txt, show_alert=True)
            toggle_lbl = "🔓 Kapat" if wl["enabled"] else "🔒 Aç"
            kb = [
                [InlineKeyboardButton(toggle_lbl,          callback_data="secret|toggle"),
                 InlineKeyboardButton(TR["secret_add_btn"],callback_data="secret|add")],
                [InlineKeyboardButton(TR["secret_list"].format(len(wl.get("users",[]))),
                                                           callback_data="secret|list")],
                [InlineKeyboardButton("◀️ Geri",           callback_data="nav|root")],
            ]
            await query.edit_message_text(mode_txt, reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END
        if action == "add":
            context.user_data["action"] = "secret_add_id"
            await query.edit_message_text(TR["secret_enter_id"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_SECRET_ID
        if action == "list":
            users_list = wl.get("users", [])
            u_data     = load_users()
            lines = [TR["secret_list"].format(len(users_list))]
            for wuid in users_list:
                u    = u_data.get(str(wuid), {})
                name = u.get("full_name") or u.get("first_name") or f"ID:{wuid}"
                lines.append(f"  👤 {name} ({wuid})")
            await query.edit_message_text(
                "\n".join(lines)[:3000],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")]]))
            return ConversationHandler.END

    # ── Sınıf İstatistikleri (admin) ─────────────────
    if cb == "mgmt|class_stats" and is_main_admin(uid):
        classes = load_classes()
        counts  = {c: 0 for c in CLASS_DEFS}
        none_c  = 0
        for cls in classes.values():
            if cls in counts: counts[cls] += 1
            else: none_c += 1
        lines = ["🎓 SINIF İSTATİSTİKLERİ", "─"*24]
        for c, cnt in counts.items():
            label = CLASS_DEFS[c]["tr"]
            bar   = "█" * min(cnt, 20)
            lines.append(f"{label}: {cnt} kişi  {bar}")
        lines.append(f"❓ Seçmemiş: {none_c} kişi")
        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")]]))
        return ConversationHandler.END

    # ── İçerik işlemleri — pin/move/copy/sort/folder_desc ──
    if cb.startswith("extra|") and is_main_admin(uid):
        action = cb.split("|")[1]
        folder = get_folder(content, path)

        if action == "sort_az":
            files = folder.get("files", [])
            files.sort(key=lambda f: f.get("caption", f.get("name","")).lower())
            save_content(content)
            await show_folder(query, context, path, note=L(uid,"files_sorted"))
            log_admin_action(uid, "SORT_AZ", "›".join(path))
            return ConversationHandler.END

        if action == "sort_views":
            files = folder.get("files", [])
            vc    = load_view_counts()
            files.sort(key=lambda f: vc.get(f.get("file_id") or f.get("caption",""),{}).get("count",0), reverse=True)
            save_content(content)
            await show_folder(query, context, path, note=L(uid,"files_sorted"))
            return ConversationHandler.END

        if action == "folder_desc":
            context.user_data["action"] = "folder_desc"
            desc = get_folder_desc(path)
            prompt = L(uid,"folder_desc_prompt")
            if desc:
                prompt += f"\n\nMevcut: {desc[:100]}"
            await query.edit_message_text(prompt,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")]]))
            return WAIT_FOLDER_DESC

        if action == "pin":
            files = folder.get("files", [])
            if not files:
                await query.answer(L(uid,"no_files"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"📌 {f.get('caption','?')[:35]}", callback_data=f"extra|do_pin|{i}")]
                  for i,f in enumerate(files)]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"pin_select"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "do_pin":
            idx   = int(cb.split("|")[2])
            files = folder.get("files",[])
            if 0 <= idx < len(files):
                files[idx]["pinned"] = not files[idx].get("pinned", False)
                save_content(content)
                fname  = files[idx].get("caption","?")
                is_pin = files[idx]["pinned"]
                await show_folder(query, context, path,
                    note=L(uid,"file_pinned" if is_pin else "file_unpinned").format(fname))
                log_admin_action(uid, "PIN_FILE" if is_pin else "UNPIN_FILE", fname)
            return ConversationHandler.END

        if action == "move":
            files = folder.get("files",[])
            if not files:
                await query.answer(L(uid,"no_files"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"📂 {f.get('caption','?')[:35]}", callback_data=f"extra|do_move_sel|{i}")]
                  for i,f in enumerate(files)]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"move_select_file"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "do_move_sel":
            context.user_data["move_idx"] = int(cb.split("|")[2])
            # Hedef klasörleri listele
            all_paths = all_folder_paths()
            kb = []
            for p in all_paths[:20]:
                if p == path: continue
                label = " › ".join(p)
                penc  = "~~".join(p)
                kb.append([InlineKeyboardButton(f"📁 {label}", callback_data=f"extra|do_move_dest|{penc}")])
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(
                L(uid,"move_select_dest").format(" › ".join(path) or "🏠"),
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "do_move_dest":
            dest_enc = cb.split("|",2)[2]
            dest_path = dest_enc.split("~~") if dest_enc else []
            src_idx   = context.user_data.pop("move_idx", -1)
            src_files = folder.get("files",[])
            if 0 <= src_idx < len(src_files):
                f     = src_files.pop(src_idx)
                dest_folder = get_folder(content, dest_path)
                dest_folder.setdefault("files",[]).append(f)
                save_content(content)
                fname = f.get("caption","?")
                dest_name = " › ".join(dest_path) or "🏠"
                await show_folder(query, context, path, note=L(uid,"file_moved").format(fname, dest_name))
                log_admin_action(uid, "MOVE_FILE", f"{fname} → {dest_name}")
                # Abonelere bildir
                for sub_uid in get_folder_subscribers(dest_path):
                    try:
                        await context.bot.send_message(
                            int(sub_uid),
                            L(sub_uid,"sub_notif").format(folder=dest_name, fname=fname))
                    except: pass
            return ConversationHandler.END

        if action == "copy":
            files = folder.get("files",[])
            if not files:
                await query.answer(L(uid,"no_files"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"📋 {f.get('caption','?')[:35]}", callback_data=f"extra|do_copy_sel|{i}")]
                  for i,f in enumerate(files)]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"copy_select_file"), reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "do_copy_sel":
            context.user_data["copy_idx"] = int(cb.split("|")[2])
            all_paths = all_folder_paths()
            kb = []
            for p in all_paths[:20]:
                label = " › ".join(p)
                penc  = "~~".join(p)
                kb.append([InlineKeyboardButton(f"📁 {label}", callback_data=f"extra|do_copy_dest|{penc}")])
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(
                L(uid,"move_select_dest").format(" › ".join(path) or "🏠"),
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "do_copy_dest":
            import copy as _copy
            dest_enc  = cb.split("|",2)[2]
            dest_path = dest_enc.split("~~") if dest_enc else []
            src_idx   = context.user_data.pop("copy_idx", -1)
            src_files = folder.get("files",[])
            if 0 <= src_idx < len(src_files):
                f    = _copy.deepcopy(src_files[src_idx])
                dest_folder = get_folder(content, dest_path)
                dest_folder.setdefault("files",[]).append(f)
                save_content(content)
                fname = f.get("caption","?")
                dest_name = " › ".join(dest_path) or "🏠"
                await show_folder(query, context, path, note=L(uid,"file_copied").format(fname, dest_name))
                log_admin_action(uid, "COPY_FILE", f"{fname} → {dest_name}")
            return ConversationHandler.END

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
        # Geri gidince o klasörün dosyalarını sil
        if action == "back" and path:
            folder_key = "|".join(path)
            folder_msgs = context.user_data.get("folder_msgs", {})
            msg_ids = folder_msgs.pop(folder_key, [])
            for mid in msg_ids:
                try:
                    await context.bot.delete_message(chat_id=query.message.chat_id, message_id=mid)
                except: pass
            path.pop()
        elif action == "root":
            # Ana sayfaya dönünce tüm klasör mesajlarını temizle
            folder_msgs = context.user_data.get("folder_msgs", {})
            for folder_key, msg_ids in list(folder_msgs.items()):
                for mid in msg_ids:
                    try:
                        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=mid)
                    except: pass
            context.user_data["folder_msgs"] = {}
            path = []

        context.user_data["path"] = path
        context.user_data["page"] = 0
        context.user_data.pop("action", None)  # ai_chat ve diğer modları temizle

        # Status mesajlarını sil (dosya/klasör ekleme sayacı)
        for key in ("add_file_status_id", "add_folder_status_id"):
            mid = context.user_data.pop(key, None)
            if mid:
                try:
                    await context.bot.delete_message(chat_id=query.message.chat_id, message_id=mid)
                except: pass
        for k in ("add_file_count", "add_folder_count"):
            context.user_data.pop(k, None)
        # action'ı temizle
        context.user_data.pop("action", None)

        # Mevcut mesajı (prompt) düzenleyerek ana sayfayı göster
        await show_folder(query, context, path)
        return ConversationHandler.END

    if cb.startswith("open|"):
        path.append(cb.split("|",1)[1])
        context.user_data["path"] = path
        context.user_data["page"] = 0
        content2 = load_content()
        folder2  = get_folder(content2, path)
        files    = folder2.get("files", [])

        # Önce klasör görünümünü göster
        await show_folder(query, context, path)

        # Dosyalar varsa otomatik gönder ve mesaj ID'lerini kaydet
        if files:
            sent_ids = []
            for f in files:
                try:
                    sent_msg = await _send_file_get_msg(query.message, f, uid)
                    if sent_msg:
                        sent_ids.append(sent_msg.message_id)
                    if not is_admin(uid):
                        log_user_message(user, "file_view", f.get("caption",""))
                except Exception as e:
                    logger.error(f"Dosya gönderme hatası: {e}")
            # Gönderilen mesaj ID'lerini path ile eşleştirerek sakla
            folder_key = "|".join(path)
            folder_msgs = context.user_data.setdefault("folder_msgs", {})
            folder_msgs[folder_key] = sent_ids
        return ConversationHandler.END

    # ── Yönetim (sadece süper admin) ──────────────────
    if cb.startswith("mgmt|") and is_main_admin(uid):
        action = cb.split("|")[1]

        if action == "stats":
            u_d   = load_users()
            m_d   = load_messages()
            s     = load_settings()
            vc    = load_view_counts()
            ct    = load_content()
            total_msg   = sum(len(v) for v in m_d.values())
            total_views = sum((v.get("count",0) if isinstance(v,dict) else 0) for v in vc.values())

            # Aktivite türlerine göre sayım
            type_counts = {}
            for msgs in m_d.values():
                for m in msgs:
                    t = m.get("type","?")
                    type_counts[t] = type_counts.get(t, 0) + 1

            # Klasör istatistikleri
            def _folder_stats(node, depth=0):
                lines = []
                for name, sub in node.get("folders",{}).items():
                    fc   = len(sub.get("files",[]))
                    sc   = len(sub.get("folders",{}))
                    indent = "  " * depth
                    lines.append(f"{indent}📁 {name}  ({sc}📁 {fc}📎)")
                    lines.extend(_folder_stats(sub, depth+1))
                return lines

            folder_lines = _folder_stats(ct)

            # En aktif kullanıcılar
            top_users = sorted(
                [(uid_, len(msgs)) for uid_, msgs in m_d.items()],
                key=lambda x: x[1], reverse=True)[:5]

            # En çok görüntülenen dosyalar
            top_files = sorted(
                [(v.get("name","?"), v.get("count",0)) for v in vc.values() if isinstance(v,dict)],
                key=lambda x: x[1], reverse=True)[:5]

            txt = (
                f"📊 DETAYLI İSTATİSTİKLER\n{'═'*28}\n\n"
                f"👥 Toplam kullanıcı: {len(u_d)}\n"
                f"💬 Toplam kayıt: {total_msg}\n"
                f"👁 Toplam görüntüleme: {total_views}\n"
                f"🔧 Bakım: {'Açık' if s['maintenance'] else 'Kapalı'}\n\n"
                f"{'─'*28}\n"
                f"📨 Aktivite Dağılımı:\n"
                f"  ✍️ Mesaj: {type_counts.get('msg',0)}\n"
                f"  🔘 Buton: {type_counts.get('button',0)}\n"
                f"  🔍 Arama: {type_counts.get('search',0)}\n"
                f"  👁 Dosya görüntüleme: {type_counts.get('file_view',0)}\n"
                f"  🖼 Fotoğraf: {type_counts.get('photo',0)}\n"
                f"  📄 Dosya: {type_counts.get('document',0)}\n"
                f"  🎥 Video: {type_counts.get('video',0)}\n\n"
                f"{'─'*28}\n"
                f"📁 Klasör Yapısı:\n" +
                ("\n".join(folder_lines) if folder_lines else "  Boş") +
                f"\n\n{'─'*28}\n"
                f"🏆 En Aktif Kullanıcılar:\n"
            )
            users_data = load_users()
            for uid_, cnt in top_users:
                u = users_data.get(uid_, {})
                name = u.get("full_name") or u.get("first_name") or f"ID:{uid_}"
                txt += f"  👤 {name[:20]} — {cnt} kayıt\n"

            if top_files:
                txt += f"\n{'─'*28}\n🔥 En Çok Görüntülenen:\n"
                for i,(fname,cnt) in enumerate(top_files,1):
                    txt += f"  {i}. {fname[:25]} — {cnt}×\n"

            kb = [
                [InlineKeyboardButton("📊 Kullanıcı Listesi", callback_data="mgmt|users")],
                [InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")],
            ]
            await query.edit_message_text(txt[:4000], reply_markup=InlineKeyboardMarkup(kb))
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
            kb.append([InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")])
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
            kb.append([InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")])
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
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")]]))
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
            cls   = class_label(target)
            warns_list = get_warns(target)
            note  = get_note(target)

            type_counts = {}
            for m in msgs:
                t = m.get("type","?")
                type_counts[t] = type_counts.get(t, 0) + 1

            searches = [m.get("content","") for m in msgs if m.get("type") == "search"][-5:]
            viewed   = [m.get("content","") for m in msgs if m.get("type") == "file_view"]
            from collections import Counter
            top_viewed = Counter(viewed).most_common(3)
            media_cnt = sum(1 for m in msgs if m.get("type") in ("photo","video","document","audio","voice","animation"))

            ICONS = {"msg":"✍️","photo":"🖼","video":"🎥","document":"📄",
                     "audio":"🎵","voice":"🎙","animation":"🎞","sticker":"😊",
                     "command":"⚙️","file_view":"👁","button":"🔘","search":"🔍"}

            recent = []
            for m in msgs[-10:]:
                icon = ICONS.get(m.get("type",""),"📨")
                t    = m.get("time","")[-8:]
                c    = m.get("content","")[:40]
                recent.append(f"  {icon} {t}  {c}")

            info = (
                f"╔══════════════════════════╗\n"
                f"  👤  {name}\n"
                f"  🔗  {un}\n"
                f"  🆔  {target}\n"
                f"  🎓  {TR['class_label'].format(cls)}\n"
                f"  📅  {last}\n"
                f"  🚫  Engel: {'✅' if blkd else '❌'}\n"
                f"  ⚠️   Uyarı: {len(warns_list)}/{MAX_WARNS}\n"
            )
            if note:
                info += f"  📝  Not: {note[:60]}\n"
            info += (
                f"╠══════════════════════════╣\n"
                f"  📊  Toplam: {total}\n"
                f"  ✍️   Mesaj: {type_counts.get('msg',0)}\n"
                f"  🔍  Arama: {type_counts.get('search',0)}\n"
                f"  👁   Görüntüleme: {type_counts.get('file_view',0)}\n"
                f"  🖼   Medya: {media_cnt}\n"
            )
            if searches:
                info += f"╠══════════════════════════╣\n  🔍  Son Aramalar:\n"
                for s_ in searches: info += f"     • {s_[:35]}\n"
            if top_viewed:
                info += f"  👁   Çok Açılan:\n"
                for fname, cnt in top_viewed: info += f"     • {fname[:30]} ({cnt}×)\n"
            if recent:
                info += f"╠══════════════════════════╣\n  🕐  Son Aktivite:\n"
                for line in recent[-5:]: info += f"{line}\n"
            info += "╚══════════════════════════╝"

            media_files = [m for m in msgs if m.get("file_id") and
                           m["type"] in ("photo","video","document","audio","voice","animation")]
            kb = [
                [InlineKeyboardButton(TR["unblock_btn"] if blkd else TR["block_btn"],
                                      callback_data=f"user|{'unblock' if blkd else 'block'}|{target}"),
                 InlineKeyboardButton(TR["msg_btn"], callback_data=f"dm_quick|{target}")],
                [InlineKeyboardButton(TR["warn_btn"],    callback_data=f"user|warn|{target}"),
                 InlineKeyboardButton(TR["note_btn"],    callback_data=f"user|note|{target}")],
            ]
            if warns_list:
                kb.append([InlineKeyboardButton(TR["warn_clear_btn"], callback_data=f"user|clear_warns|{target}")])
            if media_files:
                kb.insert(0,[InlineKeyboardButton(TR["send_media_btn"].format(len(media_files)),
                                                  callback_data=f"user|sendmedia|{target}")])
            kb.append([InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")])
            await query.edit_message_text(info[:4000], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "warn":
            target = parts[2]
            context.user_data["warn_target"] = target
            context.user_data["action"]      = "warn_reason"
            u    = load_users().get(target,{}); name = u.get("full_name") or u.get("first_name") or f"ID:{target}"
            await query.edit_message_text(
                f"{TR['warn_reason_prompt']}\n\n👤 {name}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_WARN_REASON

        if action == "note":
            target = parts[2]
            context.user_data["note_target"] = target
            context.user_data["action"]      = "user_note"
            existing = get_note(target)
            prompt   = TR["note_prompt"]
            if existing:
                prompt += f"\n\nMevcut: {existing[:80]}"
            await query.edit_message_text(prompt,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_USER_NOTE

        if action == "clear_warns":
            target = parts[2]
            clear_warns(target)
            await query.answer(TR["warns_cleared"].format(target), show_alert=True)
            query.data = f"user|info|{target}"; return await callback(update, context)

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
            # Toplu seçim için seçili klasörler
            sel = context.user_data.get("del_folder_sel", set())
            kb  = []
            for f in folds:
                icon  = "☑️" if f in sel else "⬜️"
                kb.append([InlineKeyboardButton(f"{icon} 📁 {f}", callback_data=f"dsel|folder|{f}")])
            action_row = []
            if sel:
                action_row.append(InlineKeyboardButton(f"🗑 {len(sel)} Klasörü Sil", callback_data="do|bulk_del_folder"))
            action_row.append(InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root"))
            kb.append(action_row)
            await query.edit_message_text(
                f"🗑 {'Silmek istediğin klasörleri seç:' if is_main_admin(uid) else 'اختر المجلدات للحذف:'}\n{'─'*24}",
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "del_file":
            files = folder.get("files",[])
            if not files:
                await query.answer(L(uid,"no_files"), show_alert=True); return ConversationHandler.END
            sel = context.user_data.get("del_file_sel", set())
            kb  = []
            for i, f in enumerate(files):
                cap  = f.get("caption", f.get("name","?"))[:35]
                icon = "☑️" if i in sel else "⬜️"
                kb.append([InlineKeyboardButton(f"{icon} 📎 {cap}", callback_data=f"dsel|file|{i}")])
            action_row = []
            if sel:
                action_row.append(InlineKeyboardButton(f"🗑 {len(sel)} Dosyayı Sil", callback_data="do|bulk_del_file"))
            action_row.append(InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root"))
            kb.append(action_row)
            await query.edit_message_text(
                f"🗑 {'Silmek istediğin dosyaları seç:' if is_main_admin(uid) else 'اختر الملفات للحذف:'}\n{'─'*24}",
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "rename_folder":
            folds = list(folder.get("folders",{}).keys())
            if not folds:
                await query.answer(L(uid,"no_folders"), show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"✏️ {f}", callback_data=f"do|pick_folder|{f}")] for f in folds]
            kb.append([InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root")])
            await query.edit_message_text(L(uid,"rename_folder_select"), reply_markup=InlineKeyboardMarkup(kb))
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
    # ── Checkbox toggle (seç/kaldır) ─────────────────
    if cb.startswith("dsel|") and is_main_admin(uid):
        parts    = cb.split("|")
        sel_type = parts[1]   # "folder" veya "file"
        val      = parts[2]   # klasör adı veya dosya index

        if sel_type == "folder":
            sel = context.user_data.setdefault("del_folder_sel", set())
            if val in sel: sel.discard(val)
            else:          sel.add(val)
            context.user_data["del_folder_sel"] = sel
            # Ekranı yenile
            folder2 = get_folder(content, path)
            folds   = list(folder2.get("folders",{}).keys())
            kb      = []
            for f in folds:
                icon = "☑️" if f in sel else "⬜️"
                kb.append([InlineKeyboardButton(f"{icon} 📁 {f}", callback_data=f"dsel|folder|{f}")])
            action_row = []
            if sel:
                action_row.append(InlineKeyboardButton(f"🗑 {len(sel)} Klasörü Sil", callback_data="do|bulk_del_folder"))
            action_row.append(InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root"))
            kb.append(action_row)
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
            except: pass

        elif sel_type == "file":
            idx = int(val)
            sel = context.user_data.setdefault("del_file_sel", set())
            if idx in sel: sel.discard(idx)
            else:          sel.add(idx)
            context.user_data["del_file_sel"] = sel
            folder2 = get_folder(content, path)
            files   = folder2.get("files",[])
            kb      = []
            for i, f in enumerate(files):
                cap  = f.get("caption", f.get("name","?"))[:35]
                icon = "☑️" if i in sel else "⬜️"
                kb.append([InlineKeyboardButton(f"{icon} 📎 {cap}", callback_data=f"dsel|file|{i}")])
            action_row = []
            if sel:
                action_row.append(InlineKeyboardButton(f"🗑 {len(sel)} Dosyayı Sil", callback_data="do|bulk_del_file"))
            action_row.append(InlineKeyboardButton(L(uid,"cancel"), callback_data="nav|root"))
            kb.append(action_row)
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
            except: pass
        return ConversationHandler.END

    if cb.startswith("do|") and is_main_admin(uid):
        parts  = cb.split("|",2); action = parts[1]; arg = parts[2] if len(parts)>2 else ""
        folder = get_folder(content, path)

        # ── Toplu Silme ──────────────────────────────
        if action == "bulk_del_folder":
            sel   = context.user_data.pop("del_folder_sel", set())
            count = 0
            for name in sel:
                if name in folder.get("folders",{}):
                    del folder["folders"][name]; count += 1
            if count: save_content(content)
            await show_folder(query, context, path,
                note=f"✅ {count} {'klasör silindi.' if is_main_admin(uid) else 'مجلد تم حذفه.'}")
            return ConversationHandler.END

        if action == "bulk_del_file":
            sel     = context.user_data.pop("del_file_sel", set())
            files   = folder.get("files",[])
            # Büyükten küçüğe sil ki indexler bozulmasın
            for idx in sorted(sel, reverse=True):
                if 0 <= idx < len(files): files.pop(idx)
            save_content(content)
            await show_folder(query, context, path,
                note=f"✅ {len(sel)} {'dosya silindi.' if is_main_admin(uid) else 'ملف تم حذفه.'}")
            return ConversationHandler.END

        # ── Silme Onayları (tekli — eski uyumluluk) ──
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

        if action == "set_description":
            context.user_data["action"] = "set_description"
            s = load_settings()
            await query.edit_message_text(
                f"📄 Bot açıklamasını yaz (BotFather'daki 'about' kısmı):\n\nMevcut: {s.get('bot_description','—')[:100]}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_BOT_NAME  # aynı state kullan

        if action == "maint_text":
            context.user_data["action"] = "set_maint_text"
            await query.edit_message_text(
                "🔧 Bakım modu mesajını yaz (kullanıcılara gösterilecek):",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
            return WAIT_WELCOME

        if action == "blocked":
            blocked = load_blocked()
            txt  = TR["blocked_list"].format(len(blocked)) + "\n\n"
            txt += "\n".join(f"🆔 {b}" for b in blocked) if blocked else TR["no_blocked"]
            await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")]]))
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
            kb.append([InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")])
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
            kb.append([InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")])
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
            kb.append([InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")])
            await query.edit_message_text(
                TR["btn_mgmt_title"] + "\n\n✅ = Açık  |  ❌ = Kapalı",
                reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

    # ── AI Cevap Puanlama ────────────────────────────
    if cb.startswith("rate|") and not is_admin(uid):
        parts_r = cb.split("|")
        file_key = parts_r[1]
        stars    = int(parts_r[2])
        add_feedback(file_key, uid, stars)
        star_str = "⭐" * stars + "☆" * (5 - stars)
        await query.answer(f"{star_str} — {L(uid,'feedback_saved')}", show_alert=False)
        # Liderboard puan
        update_leaderboard(uid, stars)
        return ConversationHandler.END

    # ── Liderboard ────────────────────────────────────
    if cb == "misc|leaderboard":
        lb    = get_leaderboard(10)
        lines = [L(uid,"leaderboard_title"), "─"*22]
        medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        for i,(name,pts) in enumerate(lb):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            lines.append(f"{medal} {name[:25]}  —  {pts} pts")
        if not lb:
            lines.append(L(uid,"leaderboard_empty"))
        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(L(uid,"back"),  callback_data="nav|root")]]))
        return ConversationHandler.END

    # ── Sabit Mesaj Ayarla (admin) ────────────────────
    if cb == "set|pin_msg" and is_main_admin(uid):
        context.user_data["action"] = "set_pin_msg"
        pinned = get_pinned_msg()
        prompt = TR["pin_msg_prompt"]
        if pinned:
            prompt += f"\n\nMevcut: {pinned[:100]}"
        await query.edit_message_text(prompt,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TR["cancel"], callback_data="close")]]))
        return WAIT_WELCOME   # aynı state kullan

    # ── Duyuru Geçmişi (admin) ───────────────────────
    if cb == "bcast|history" and is_main_admin(uid):
        log_ = load_bcast_log()
        if not log_:
            await query.answer(TR["bcast_history_empty"], show_alert=True); return ConversationHandler.END
        lines = [TR["bcast_history_title"]]
        for entry in reversed(log_[-20:]):
            lines.append(
                f"\n📢 {entry.get('time','')}\n"
                f"   👥 {entry.get('count',0)} kişi\n"
                f"   📝 {entry.get('text','')[:60]}"
            )
        await query.edit_message_text(
            "\n".join(lines)[:4000],
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")]]))
        return ConversationHandler.END

    if cb == "close":
        try: await query.delete_message()
        except: pass
        return ConversationHandler.END

    # ── Notlar ───────────────────────────────────────
    if cb.startswith("notes|") and not is_admin(uid):
        action = cb.split("|")[1]
        if action == "edit":
            context.user_data["action"] = "edit_note"
            await query.edit_message_text(
                L(uid,"notes_prompt"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(L(uid,"back"), callback_data="nav|root")
                ]]))
            return WAIT_FOLDER  # Metin bekliyoruz
        if action == "del":
            set_personal_note(uid, "")
            await query.answer("✅", show_alert=False)
            await query.edit_message_text(L(uid,"notes_empty"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✏️ يكتب", callback_data="notes|edit"),
                    InlineKeyboardButton(L(uid,"back"), callback_data="nav|root"),
                ]]))
        return ConversationHandler.END

    # ── Hatırlatıcı ──────────────────────────────────
    if cb.startswith("reminder|") and not is_admin(uid):
        parts  = cb.split("|")
        action = parts[1]
        if action == "add":
            context.user_data["action"] = "reminder_text"
            await query.edit_message_text(
                L(uid,"reminder_add_prompt"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(L(uid,"back"), callback_data="nav|root")
                ]]))
            return WAIT_FOLDER
        if action == "del" and len(parts) > 2:
            idx = int(parts[2])
            delete_reminder(uid, idx)
            await query.answer(L(uid,"reminder_del"), show_alert=True)
            await query.delete_message()
        return ConversationHandler.END

    # ── Admin: Sınav/Etkinlik Ekle ───────────────────
    if cb.startswith("countdown|") and is_main_admin(uid):
        action = cb.split("|")[1]
        if action == "add":
            context.user_data["action"] = "countdown_name"
            await query.edit_message_text(
                L(uid,"countdown_prompt"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(L(uid,"back"), callback_data="nav|root")
                ]]))
            return WAIT_FOLDER
        if action == "del" and len(cb.split("|")) > 2:
            idx = int(cb.split("|")[2])
            cd = load_countdowns()
            if 0 <= idx < len(cd): cd.pop(idx)
            save_countdowns(cd)
            await query.answer("✅ Silindi", show_alert=True)
            await query.delete_message()
        return ConversationHandler.END

    # ── Quiz cevabı ──────────────────────────────────
    if cb.startswith("quiz|ans|") and not is_admin(uid):
        parts   = cb.split("|")
        qid     = parts[2]
        ans_idx = int(parts[3])
        quizzes = load_quizzes()
        q = next((x for x in quizzes if x.get("id") == qid), None)
        if not q:
            await query.answer("❌ Sona erdi", show_alert=True)
            return ConversationHandler.END
        answered = q.setdefault("answered", {})
        if uid in answered:
            await query.answer("✅ Zaten cevapladın", show_alert=True)
            return ConversationHandler.END
        answered[uid] = ans_idx
        correct = q.get("correct", -1)
        is_correct = (ans_idx == correct)
        save_quizzes(quizzes)
        if is_correct:
            update_leaderboard(uid, 5)
            await query.answer("✅ صحيح! +5 pts 🎉", show_alert=True)
        else:
            correct_text = q["options"][correct] if 0 <= correct < len(q["options"]) else "?"
            await query.answer(f"❌ خطأ. الجواب: {correct_text}", show_alert=True)
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
            kb.append([InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")])
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
                kb = [[InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")]]
                await query.edit_message_text("\n".join(lines)[:4000], reply_markup=InlineKeyboardMarkup(kb))
            else:
                txt = build_poll_results_text(poll, uid, show_voters=False)
                kb  = [
                    [InlineKeyboardButton("👥 Kim Ne Seçti?", callback_data=f"poll|voter_detail|{poll_id}")],
                    [InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")],
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
                [InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")],
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
                [InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")],
            ]
            await query.edit_message_text("\n".join(lines)[:4000], reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END

        if action == "list_delete":
            polls = load_polls()
            if not polls:
                await query.answer(TR["poll_no_polls"], show_alert=True); return ConversationHandler.END
            kb = [[InlineKeyboardButton(f"🗑 {p['question'][:40]}", callback_data=f"poll|confirm_delete|{pid}")]
                  for pid, p in polls.items()]
            kb.append([InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")])
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
            kb.append([InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")])
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
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Geri",   callback_data="nav|root")]]))
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

    # ── Kişisel Not Düzenleme ───────────────────────
    if action == "edit_note" and not is_admin(uid):
        set_personal_note(uid, text)
        await update.message.reply_text(L(uid,"notes_saved"))
        context.user_data.pop("action",None)
        return ConversationHandler.END

    # ── Hatırlatıcı — Metin ─────────────────────────
    if action == "reminder_text" and not is_admin(uid):
        context.user_data["reminder_text"] = text
        context.user_data["action"] = "reminder_when"
        await update.message.reply_text(L(uid,"reminder_when"))
        return WAIT_FOLDER

    # ── Hatırlatıcı — Zaman ─────────────────────────
    if action == "reminder_when" and not is_admin(uid):
        minutes = parse_time_input(text)
        if not minutes:
            await update.message.reply_text(
                "❌ " + ("Geçersiz format. Örn: 30d, 2s, 1g" if is_main_admin(uid)
                         else "تنسيق خاطئ. مثال: 30d, 2s, 1g"))
            return WAIT_FOLDER
        import time
        fire_ts = time.time() + (minutes * 60)
        rem_text = context.user_data.pop("reminder_text", text)
        add_reminder(uid, rem_text, fire_ts)
        if minutes < 60:
            label = f"{minutes} دقيقة" if not is_main_admin(uid) else f"{minutes} dakika"
        elif minutes < 1440:
            label = f"{minutes//60} ساعة" if not is_main_admin(uid) else f"{minutes//60} saat"
        else:
            label = f"{minutes//1440} يوم" if not is_main_admin(uid) else f"{minutes//1440} gün"
        await update.message.reply_text(L(uid,"reminder_saved").format(label))
        context.user_data.pop("action",None)
        return ConversationHandler.END

    # ── Anonim Soru ─────────────────────────────────
    if action == "anon_q" and not is_admin(uid):
        qs = load_anon_q()
        cls = get_user_class(uid)
        qs.append({"text": text, "cls": cls,
                   "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
        save_anon_q(qs)
        cls_name = CLASS_DEFS.get(cls,{}).get("ar","") if cls else ""
        notif = (
            f"❓ سؤال مجهول الهوية\n"
            f"{'─'*20}\n"
            f"{text}\n"
            f"{'─'*20}\n"
            f"🎓 {cls_name}  🕐 {datetime.now().strftime('%H:%M')}"
        )
        kb_admin = [[InlineKeyboardButton("📢 رد علني", callback_data=f"anon|reply|{len(qs)-1}")]]
        try:
            await context.bot.send_message(ADMIN_ID, notif, reply_markup=InlineKeyboardMarkup(kb_admin))
        except: pass
        await update.message.reply_text(L(uid,"anon_q_sent"))
        context.user_data.pop("action",None)
        return ConversationHandler.END

    # ── Sınav Adı (Admin) ───────────────────────────
    if action == "countdown_name" and is_main_admin(uid):
        context.user_data["countdown_name"] = text
        context.user_data["action"] = "countdown_date"
        await update.message.reply_text(L(uid,"countdown_date"))
        return WAIT_FOLDER

    # ── Sınav Tarihi (Admin) ─────────────────────────
    if action == "countdown_date" and is_main_admin(uid):
        name = context.user_data.pop("countdown_name","?")
        ok   = add_countdown(name, text)
        if ok:
            await update.message.reply_text(L(uid,"countdown_saved").format(name))
        else:
            await update.message.reply_text("❌ Geçersiz tarih. Örn: 20/05/2026")
        context.user_data.pop("action",None)
        return ConversationHandler.END

    # ── Quiz Sorusu (Admin) ──────────────────────────
    if action == "quiz_question" and is_main_admin(uid):
        import re as _re2
        lines = text.strip().split("\n")
        # Format: Soru\nA. ...\nB. ...\nC. ...\nD. ...\nCEVAP: A
        try:
            question = lines[0].strip()
            opts = []
            correct_idx = 0
            for line in lines[1:]:
                line = line.strip()
                m = _re2.match(r'^([A-Da-d])[.)]\s*(.+)$', line)
                if m:
                    opts.append(m.group(2).strip())
                elif line.upper().startswith("CEVAP:") or line.upper().startswith("الجواب:"):
                    ans_letter = line.split(":")[-1].strip().upper()
                    correct_idx = "ABCD".index(ans_letter) if ans_letter in "ABCD" else 0
            if len(opts) < 2:
                await update.message.reply_text("❌ En az 2 seçenek gerekli.\nFormat:\nSoru\nA. Seç1\nB. Seç2\nCEVAP: A")
                return WAIT_FOLDER
            qid = f"q_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            quizzes = load_quizzes()
            quizzes.append({
                "id": qid, "question": question, "options": opts,
                "correct": correct_idx, "active": True,
                "answered": {}, "created": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            save_quizzes(quizzes)
            await update.message.reply_text(
                f"✅ Quiz oluşturuldu!\n\n"
                f"❓ {question}\n"
                f"{'─'*20}\n" +
                "\n".join(f"{'ABCD'[i]}. {o}" for i,o in enumerate(opts)) +
                f"\n{'─'*20}\n✅ Doğru: {'ABCD'[correct_idx]}")
        except Exception as e:
            await update.message.reply_text(f"❌ Hata: {e}")
        context.user_data.pop("action",None)
        return ConversationHandler.END

    # ── Anonim Soruya Cevap (Admin) ──────────────────
    if action == "anon_reply" and is_main_admin(uid):
        q_text = context.user_data.pop("anon_q_text","")
        # Tüm kullanıcılara gönder (ya da sadece alakalı sınıfa)
        users_d = load_users()
        reply_msg = (
            f"💡 رد على سؤال مجهول\n"
            f"{'─'*22}\n"
            f"❓ {q_text[:100]}\n\n"
            f"💬 {text}\n"
            f"{'─'*22}\n"
            f"🕐 {datetime.now().strftime('%H:%M')}"
        )
        success = 0
        for uid_, _ in users_d.items():
            if int(uid_) == ADMIN_ID or is_blocked(uid_): continue
            try:
                await context.bot.send_message(int(uid_), reply_msg)
                success += 1
            except: pass
        await update.message.reply_text(f"✅ {success} kullanıcıya gönderildi.")
        context.user_data.pop("action",None)
        return ConversationHandler.END

    # ── Kullanıcıdan admin'e mesaj ──────────────────
    if action == "user_msg_to_admin" and not is_admin(uid):
        log_user_message(user, "msg", text)
        users_d = load_users()
        u       = users_d.get(uid, {})
        name    = u.get("full_name") or u.get("first_name") or f"ID:{uid}"
        un      = f" @{u['username']}" if u.get("username") else ""
        notif   = f"💬 رسالة جديدة\n\n👤 {name}{un}\n🆔 {uid}\n\n📝 {text}\n🕐 {datetime.now().strftime('%H:%M')}"
        kb_admin = [[InlineKeyboardButton(f"💬 رد (ID: {uid})", callback_data=f"dm_quick|{uid}")]]
        try:
            await context.bot.send_message(ADMIN_ID, notif, reply_markup=InlineKeyboardMarkup(kb_admin))
        except Exception as e:
            logger.error(f"Admin bildirim hatası: {e}")
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

    # ── FAQ Soru Girişi (admin) ───────────────────────
    if action == "faq_q" and is_main_admin(uid):
        if not text: await update.message.reply_text(TR["faq_enter_q"]); return WAIT_FAQ_Q
        context.user_data["faq_q_text"] = text
        context.user_data["action"]     = "faq_a"
        await update.message.reply_text(TR["faq_enter_a"])
        return WAIT_FAQ_A

    if action == "faq_a" and is_main_admin(uid):
        q    = context.user_data.pop("faq_q_text", "")
        kws  = [kw.strip() for kw in q.split(",") if kw.strip()]
        if not kws: kws = [q]
        faqs = load_faq()
        faqs.append({"keywords": kws, "answer": text})
        save_faq(faqs)
        await update.message.reply_text(TR["faq_saved"])
        log_admin_action(uid, "FAQ_ADD", kws[0][:40])
        context.user_data.pop("action", None)
        return ConversationHandler.END

    # ── Otomatik Kural Girişi (admin) ────────────────
    if action == "rule_kw" and is_main_admin(uid):
        if not text: await update.message.reply_text(TR["rule_enter_kw"]); return WAIT_RULE_KW
        context.user_data["rule_kws"] = [kw.strip() for kw in text.split(",") if kw.strip()]
        context.user_data["action"]   = "rule_resp"
        await update.message.reply_text(TR["rule_enter_resp"])
        return WAIT_RULE_RESP

    if action == "rule_resp" and is_main_admin(uid):
        kws   = context.user_data.pop("rule_kws", [])
        rules = load_auto_rules()
        rules.append({"keywords": kws, "response": text})
        save_auto_rules(rules)
        await update.message.reply_text(TR["rule_saved"])
        log_admin_action(uid, "RULE_ADD", ", ".join(kws[:3]))
        context.user_data.pop("action", None)
        return ConversationHandler.END

    # ── Uyarı Sebebi (admin) ─────────────────────────
    if action == "warn_reason" and is_main_admin(uid):
        target = context.user_data.pop("warn_target","")
        if target:
            count = add_warn(target, text, uid)
            await update.message.reply_text(TR["user_warned"].format(target, count, MAX_WARNS))
            log_admin_action(uid, "WARN", f"→{target}: {text[:40]}")
            # Kullanıcıya bildir
            try:
                await context.bot.send_message(
                    int(target),
                    AR["warn_msg_to_user"].format(reason=text, count=count, max=MAX_WARNS))
            except: pass
            # Otomatik engel
            if count >= MAX_WARNS:
                blocked = load_blocked()
                if int(target) not in blocked:
                    blocked.append(int(target)); save_blocked(blocked)
                await update.message.reply_text(TR["user_auto_blocked"].format(target, MAX_WARNS))
                log_admin_action(uid, "AUTO_BAN", f"→{target}")
        context.user_data.pop("action", None)
        return ConversationHandler.END

    # ── Kullanıcı Notu (admin) ───────────────────────
    if action == "user_note" and is_main_admin(uid):
        target = context.user_data.pop("note_target","")
        if target:
            set_note(target, text)
            msg = TR["note_saved"] if text.strip() else TR["note_cleared"]
            await update.message.reply_text(msg)
            log_admin_action(uid, "NOTE", f"→{target}")
        context.user_data.pop("action", None)
        return ConversationHandler.END

    # ── Klasör Açıklaması (admin) ────────────────────
    if action == "folder_desc" and is_main_admin(uid):
        path = context.user_data.get("path", [])
        set_folder_desc(path, text)
        msg = L(uid,"folder_desc_saved") if text.strip() else L(uid,"folder_desc_cleared")
        await update.message.reply_text(msg)
        log_admin_action(uid, "FOLDER_DESC", "›".join(path))
        context.user_data.pop("action", None)
        return ConversationHandler.END

    # ── Whitelist Kullanıcı Ekle (admin) ─────────────
    if action == "secret_add_id" and is_main_admin(uid):
        try:
            new_id = int(text.strip())
            wl     = load_whitelist()
            users_list = wl.setdefault("users", [])
            if new_id not in users_list:
                users_list.append(new_id); save_whitelist(wl)
            await update.message.reply_text(TR["secret_added"].format(new_id))
            log_admin_action(uid, "WHITELIST_ADD", str(new_id))
        except:
            await update.message.reply_text(TR["invalid_id"])
        context.user_data.pop("action", None)
        return ConversationHandler.END

    # ── Hedefli Broadcast (admin) ────────────────────
    if action == "broadcast_targeted" and is_main_admin(uid):
        targets = context.user_data.pop("broadcast_targets", [])
        success = fail = 0
        for uid_ in targets:
            try:
                bcast_msg = (
                    f"╔══════════════════════╗\n"
                    f"  📢  إعلان رسمي\n"
                    f"╠══════════════════════╣\n\n"
                    f"{text}\n\n"
                    f"╚══════════════════════╝\n"
                    f"  🕐  {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                await context.bot.send_message(int(uid_), bcast_msg); success += 1
            except: fail += 1
        await update.message.reply_text(TR["broadcast_done"].format(success, fail))
        log_admin_action(uid, "BROADCAST_TARGETED", f"{success} gönderildi")
        # Duyuru log kaydet
        bcast_log = load_bcast_log()
        bcast_log.append({
            "time":  datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text":  text[:100],
            "count": success,
            "type":  "targeted"
        })
        save_bcast_log(bcast_log)
        context.user_data.pop("action", None)
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

    # ── Admin değilse: AI motorunu çalıştır ─────────────────
    if not is_admin(uid):
        if not text: return ConversationHandler.END

        # Spam koruması
        if not check_rate_limit(uid):
            await update.message.reply_text(L(uid, "spam_warning"))
            return ConversationHandler.END

        # Selamlama kontrolü
        if _is_greeting(text):
            log_user_message(user, "msg", text)
            await update.message.reply_text(L(uid, "greeting_reply"))
            return ConversationHandler.END

        # Sabit mesaj (ilk kez)
        if context.user_data.get("shown_pinned") is None:
            pinned = get_pinned_msg()
            if pinned:
                context.user_data["shown_pinned"] = True
                await update.message.reply_text(L(uid, "pinned_msg_label").format(pinned))

        subject    = _detect_subject(text)
        is_q       = _is_question(text)
        subj_label = _subject_label(uid, subject)
        ai_mode    = context.user_data.get("action") == "ai_chat"

        # AI chat modunda VEYA soru/konu tespit edilirse AI'ya gönder
        if ai_mode or ((subject or is_q) and len(text.strip()) >= 3):
            typing_msg = None
            try:
                typing_msg = await update.message.reply_text(
                    L(uid,"ai_detected").format(subj_label) if subject
                    else L(uid,"ai_searching"))
            except Exception: pass

            try:
                answer = await smart_ai_answer(uid, text)
            except Exception as e:
                logger.warning(f"AI yanıt hatası: {e}")
                answer = None

            if typing_msg:
                try: await typing_msg.delete()
                except: pass

            if answer:
                ans_text, source = answer
                if source == "calc":
                    reply_text = L(uid,"ai_math_result").format(result=ans_text)
                elif source in ("rule","faq"):
                    reply_text = ans_text
                elif "Wikipedia" in source:
                    url = source.replace("Wikipedia — ","")
                    reply_text = L(uid,"ai_wiki_result").format(result=ans_text, url=url or "Wikipedia")
                else:
                    reply_text = L(uid,"ai_search_result").format(
                        result=ans_text, source=source or "Web")
                if len(reply_text) > 4000:
                    reply_text = reply_text[:3997] + "..."
                file_key = text[:50]
                kb_rate = [[
                    InlineKeyboardButton("⭐1", callback_data=f"rate|{file_key}|1"),
                    InlineKeyboardButton("⭐2", callback_data=f"rate|{file_key}|2"),
                    InlineKeyboardButton("⭐3", callback_data=f"rate|{file_key}|3"),
                    InlineKeyboardButton("⭐4", callback_data=f"rate|{file_key}|4"),
                    InlineKeyboardButton("⭐5", callback_data=f"rate|{file_key}|5"),
                ]]
                # ai_chat modunda geri butonu ekle
                if ai_mode:
                    kb_rate.append([InlineKeyboardButton("◀️ رجوع", callback_data="nav|root")])
                try:
                    await update.message.reply_text(
                        reply_text, parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(kb_rate))
                except Exception:
                    await update.message.reply_text(
                        reply_text,
                        reply_markup=InlineKeyboardMarkup(kb_rate))
                update_leaderboard(uid, 1)
            else:
                # Yanıt bulunamadı
                await update.message.reply_text(
                    L(uid, "ai_no_web_result") + 
                    ("\n\n💬 يمكنك إعادة الصياغة أو طرح سؤال مختلف."
                     if not is_main_admin(uid) else "\n\nBaşka türlü sormayı deneyin."),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("◀️ رجوع", callback_data="nav|root")
                    ]])
                )
                return ConversationHandler.END
        else:
            # Kısa/konu dışı mesaj — sadece kaydet
            log_user_message(user, "msg", text)
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
        dm_formatted = (
            f"💌  رسالة شخصية\n"
            f"{'─'*22}\n"
            f"{text}\n"
            f"{'─'*22}\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        try:
            await context.bot.send_message(int(target), dm_formatted)
            await update.message.reply_text(TR["dm_sent"].format(target))
        except Exception as e:
            await update.message.reply_text(TR["dm_fail"].format(e))
        context.user_data.pop("action",None); context.user_data.pop("dm_target",None)
        return ConversationHandler.END

    if action == "broadcast" and is_main_admin(uid):
        users = load_users(); success = fail = 0
        for uid_,u in users.items():
            if int(uid_) == ADMIN_ID or is_blocked(uid_): continue
            try:
                bcast_msg = (
                    f"╔══════════════════════╗\n"
                    f"  📢  إعلان رسمي\n"
                    f"╠══════════════════════╣\n\n"
                    f"{text}\n\n"
                    f"╚══════════════════════╝\n"
                    f"  🕐  {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                await context.bot.send_message(int(uid_), bcast_msg); success += 1
            except: fail += 1
        await update.message.reply_text(TR["broadcast_done"].format(success,fail))
        # Log kaydet
        bcast_log = load_bcast_log()
        bcast_log.append({
            "time":  datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text":  text[:100],
            "count": success,
            "type":  "all"
        })
        save_bcast_log(bcast_log)
        log_admin_action(uid, "BROADCAST_ALL", f"{success} gönderildi")
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "set_name" and is_main_admin(uid):
        if not text: await update.message.reply_text(TR["folder_empty"]); return WAIT_BOT_NAME
        s = load_settings(); s["bot_name"] = text; save_settings(s)
        await update.message.reply_text(TR["set_name_ok"].format(text))
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "set_description" and is_main_admin(uid):
        if not text: await update.message.reply_text(TR["folder_empty"]); return WAIT_BOT_NAME
        s = load_settings(); s["bot_description"] = text; save_settings(s)
        await update.message.reply_text(f"✅ Açıklama güncellendi: {text[:80]}")
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "set_welcome" and is_main_admin(uid):
        s = load_settings(); s["welcome_msg"] = text; save_settings(s)
        await update.message.reply_text(TR["set_welcome_ok"])
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "set_maint_text" and is_main_admin(uid):
        s = load_settings(); s["maintenance_text"] = text; save_settings(s)
        await update.message.reply_text(f"✅ Bakım mesajı güncellendi.")
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "set_pin_msg" and is_main_admin(uid):
        set_pinned_msg(text)
        msg_txt = TR["pin_msg_saved"] if text.strip() else "✅ Sabit mesaj silindi."
        await update.message.reply_text(msg_txt)
        log_admin_action(uid, "PIN_MSG", text[:50])
        context.user_data.pop("action",None); return ConversationHandler.END

    if action == "add_folder":
        if not text: await update.message.reply_text(L(uid,"folder_empty")); return WAIT_FOLDER
        if text in folder.get("folders",{}):
            await update.message.reply_text(L(uid,"folder_exists").format(text)); return WAIT_FOLDER
        folder.setdefault("folders",{})[text] = {"folders":{},"files":[]}; save_content(content)
        count     = context.user_data.get("add_folder_count", 0) + 1
        context.user_data["add_folder_count"] = count
        status_id = context.user_data.get("add_folder_status_id")
        kb = [[InlineKeyboardButton(L(uid,"close"), callback_data="nav|root")]]
        status_text = (
            f"{'✅ Klasörler ekleniyor...' if is_main_admin(uid) else '✅ جارٍ إضافة المجلدات...'}\n"
            f"{'─'*20}\n"
            f"📁 {count} {'klasör eklendi' if is_main_admin(uid) else 'مجلد تمت إضافته'}\n\n"
            f"{'Devam yaz, bitince Kapat.' if is_main_admin(uid) else 'اكتب المزيد أو اضغط إغلاق.'}"
        )
        if status_id:
            try:
                await context.bot.edit_message_text(
                    status_text, chat_id=update.effective_chat.id,
                    message_id=status_id, reply_markup=InlineKeyboardMarkup(kb))
            except:
                sent = await update.message.reply_text(status_text, reply_markup=InlineKeyboardMarkup(kb))
                context.user_data["add_folder_status_id"] = sent.message_id
        else:
            sent = await update.message.reply_text(status_text, reply_markup=InlineKeyboardMarkup(kb))
            context.user_data["add_folder_status_id"] = sent.message_id
        return WAIT_FOLDER

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
        else:
            fobj    = {"type":"text","caption":text,"name":text}
        folder.setdefault("files",[]).append(fobj); save_content(content)
        count     = context.user_data.get("add_file_count", 0) + 1
        context.user_data["add_file_count"] = count
        status_id = context.user_data.get("add_file_status_id")
        kb = [[InlineKeyboardButton(L(uid,"close"), callback_data="nav|root")]]
        status_text = (
            f"{'✅ Dosyalar ekleniyor...' if is_main_admin(uid) else '✅ جارٍ إضافة الملفات...'}\n"
            f"{'─'*20}\n"
            f"📎 {count} {'dosya/link eklendi' if is_main_admin(uid) else 'ملف/رابط تمت إضافته'}\n\n"
            f"{'Devam gönder, bitince Kapat.' if is_main_admin(uid) else 'أرسل المزيد أو اضغط إغلاق.'}"
        )
        if status_id:
            try:
                await context.bot.edit_message_text(
                    status_text, chat_id=update.effective_chat.id,
                    message_id=status_id, reply_markup=InlineKeyboardMarkup(kb))
            except:
                sent = await update.message.reply_text(status_text, reply_markup=InlineKeyboardMarkup(kb))
                context.user_data["add_file_status_id"] = sent.message_id
        else:
            sent = await update.message.reply_text(status_text, reply_markup=InlineKeyboardMarkup(kb))
            context.user_data["add_file_status_id"] = sent.message_id
        return WAIT_FILE

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
        users = load_users(); success = fail = 0
        cap_raw  = msg.caption or ""
        cap_text = (
            f"📢  إعلان رسمي\n"
            f"{'─'*22}\n"
            f"{cap_raw}\n"
            f"{'─'*22}\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ) if cap_raw else None
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
        target = context.user_data.get("dm_target"); cap_raw = msg.caption or ""
        if not target: await msg.reply_text(TR["dm_no_target"]); return ConversationHandler.END
        cap_text = (
            f"💌  رسالة شخصية\n"
            f"{'─'*22}\n"
            f"{cap_raw}\n"
            f"{'─'*22}\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ) if cap_raw else None
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
            return WAIT_FILE

        # Tekli dosya — direkt kaydet
        folder.setdefault("files",[]).append(fobj); save_content(content)

        # Sayacı güncelle veya yeni mesaj gönder
        status_id = context.user_data.get("add_file_status_id")
        count     = context.user_data.get("add_file_count", 0) + 1
        context.user_data["add_file_count"] = count
        kb = [[InlineKeyboardButton(L(uid,"close"), callback_data="nav|root")]]
        status_text = (
            f"{'✅ Dosyalar ekleniyor...' if is_main_admin(uid) else '✅ جارٍ إضافة الملفات...'}\n"
            f"{'─'*20}\n"
            f"📎 {count} {'dosya eklendi' if is_main_admin(uid) else 'ملف تمت إضافته'}\n\n"
            f"{'📤 Devam gönder, bitince Kapat.' if is_main_admin(uid) else '📤 أرسل المزيد أو اضغط إغلاق.'}"
        )
        if status_id:
            try:
                await context.bot.edit_message_text(
                    status_text, chat_id=msg.chat_id,
                    message_id=status_id, reply_markup=InlineKeyboardMarkup(kb))
            except:
                sent = await msg.reply_text(status_text, reply_markup=InlineKeyboardMarkup(kb))
                context.user_data["add_file_status_id"] = sent.message_id
        else:
            sent = await msg.reply_text(status_text, reply_markup=InlineKeyboardMarkup(kb))
            context.user_data["add_file_status_id"] = sent.message_id
        return WAIT_FILE
    else:
        await msg.reply_text(L(uid,"unsupported"))
    return ConversationHandler.END

# ================================================================
#  GENEL MESAJ HANDLER — fallback log + güvenlik
# ================================================================

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback handler — sadece loglama ve güvenlik için."""
    if not update.message: return
    user = update.effective_user; uid = str(user.id); msg = update.message
    text = (msg.text or "").strip()

    if text in ALL_BTNS: return
    register_user(user)
    if is_blocked(uid): return

    s = load_settings()
    if s["maintenance"] and not is_admin(uid):
        await msg.reply_text(s.get("maintenance_text","🔧")); return

    # Sadece log — AI handle_text'te işlendi
    if not is_admin(uid) and text:
        log_user_message(user, "msg", text)

# ================================================================
#  MAIN
# ================================================================

def main():
    # Railway health check
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class _H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
        def log_message(self, *a): pass
    _port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=lambda: HTTPServer(("0.0.0.0", _port), _H).serve_forever(), daemon=True).start()
    logger.info(f"Health check port: {_port}")

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
            WAIT_WARN_REASON:   [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_USER_NOTE:     [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_FOLDER_DESC:   [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_FAQ_Q:         [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_FAQ_A:         [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_RULE_KW:       [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_RULE_RESP:     [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_SCHEDULE_HOURS:[MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_SCHEDULE_MSG:  [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_TAG:           [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
            WAIT_SECRET_ID:     [MessageHandler(text_f & ~reply_btn_f, handle_text), CallbackQueryHandler(callback)],
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
    # ÖNEMLİ: Reply butonları conv'dan ÖNCE kayıtlı olmalı
    app.add_handler(MessageHandler(reply_btn_f, handle_reply_buttons))
    app.add_handler(conv)
    app.add_handler(MessageHandler(text_f & ~reply_btn_f, handle_text))
    app.add_handler(MessageHandler(media_f, handle_media))
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

    # ── Hatırlatıcı Kontrol Job'u ─────────────────
    async def _check_reminders(ctx):
        import time
        now  = time.time()
        rems = load_reminders()
        fired = []
        remaining = []
        for r in rems:
            if r.get("fire_ts", 0) <= now:
                fired.append(r)
            else:
                remaining.append(r)
        if fired:
            save_reminders(remaining)
            for r in fired:
                try:
                    uid_ = r.get("uid","")
                    lang = AR if not is_main_admin(uid_) else TR
                    msg  = lang["reminder_fired"].format(r.get("text",""))
                    await ctx.bot.send_message(int(uid_), msg)
                except Exception as e:
                    logger.warning(f"Hatırlatıcı gönderilemedi: {e}")

    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(_check_reminders, interval=60, first=10)
        print("✅ Hatırlatıcı job başlatıldı (60sn aralık)")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
