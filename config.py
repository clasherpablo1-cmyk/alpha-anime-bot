import os
from typing import List, Set, Optional, Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


# ==============================================================================
# TELEGRAM PREMIUM CUSTOM EMOJILAR (STIKER-EMOJILAR) SOZLAMALARI
# ==============================================================================
# Telegram Premium stiker to'plamlaridagi emoji_id larni kiritish uchun tayyor joylar.
# Masalan: "sarlavha": "5368324170671202286"
# Agar bo'sh ("") yoki placeholder bo'lsa, xavfsiz ravishda fallback emoji ishlatiladi.
# Shuningdek .env fayli orqali ham berish mumkin: EMOJI_SARLAVHA="5368324170671202286"
# ==============================================================================


class CustomEmojiDict(dict):
    """Katta-kichik harflar va bo'shliqlarga sezgir bo'lmagan (case-insensitive) lug'at"""
    def _normalize(self, key):
        if isinstance(key, str):
            return key.strip().lower()
        return key

    def __getitem__(self, key):
        norm = self._normalize(key)
        if norm in self:
            return super().__getitem__(norm)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        super().__setitem__(self._normalize(key), value)

    def __contains__(self, key):
        return super().__contains__(self._normalize(key))

    def get(self, key, default=None):
        norm = self._normalize(key)
        if norm in self:
            return super().__getitem__(norm)
        return default

    def setdefault(self, key, default=None):
        norm = self._normalize(key)
        return super().setdefault(norm, default)


CUSTOM_EMOJIS: Dict[str, str] = CustomEmojiDict({
    # 1. Post va xabar elementlari
    "sarlavha": "5469759478452722926",   # Anime sarlavhasi (Fallback: 🍥)
    "reyting": "5431449001532594346",    # Reyting (Fallback: ⚛️)
    "qismlar": "5375464961822695044",    # Qismlar soni (Fallback: 🗃)
    "ovoz": "5382013970905309819",       # Ovoz / Dublyaj (Fallback: 🎙)
    "sifat": "5229095839334410849",      # Sifati (Fallback: 🎼)
    "janr": "5359441070201513074",       # Janrlar (Fallback: 🎭)
    "kod": "5330115548900501467",        # Anime kodi (Fallback: 🔑)
    "tavsif": "5226512880362332956",     # Tavsif / Mazmuni (Fallback: 📖)
    "qidiruv": "",                        # Qidiruv (Fallback: 🔍)
    "holat": "5424892643760937442",      # Holati (Fallback: 📌)
    "korishlar": "5424892643760937442",  # Ko'rishlar soni (Fallback: 👁)
    "katalog": "",                        # Katalog mundarijasi (Fallback: 🎌)
    "video": "5375464961822695044",      # Video / Qism (Fallback: 🎬)
    "yuklash": "5433811242135331842",    # Yuklash (Fallback: 📥)
    "kanal": "",                          # Kanal (Fallback: 📢)
    "bot": "5372981976804366741",        # Bot (Fallback: 🤖)
    "yangi": "5361979468887893611",      # Yangi animelar (Fallback: 🆕)
    "rasm": "",                           # Rasm qidiruvi (Fallback: 📸)
    "tasodifiy": "",                      # Tasodifiy anime (Fallback: 🎲)
    "admin": "",                          # Admin boshqaruvi (Fallback: ⚙️)
    "muvaffaqiyat": "5427009714745517609",# Muvaffaqiyat / Tasdiq (Fallback: ✅)
    "xato": "5465665476971471368",       # Xato / Bekor qilish (Fallback: ❌)
    "ogohlantirish": "",                  # Ogohlantirish (Fallback: ⚠️)
    "kutish": "5451732530048802485",     # Jarayon / Kutish (Fallback: ⏳)
    "chaqmoq": "5431449001532594346",    # Tezkor chaqmoq (Fallback: ⚡️)
    "olov": "5420315771991497307",       # Olov (Fallback: 🔥)
    "yulduz": "",                         # Yulduz (Fallback: ⭐)
    "popcorn": "5371081166013078244",    # Popcorn (Fallback: 🍿)
    "nuqta": "",                          # Ro'yxat nuqtasi (Fallback: 🔹)
    "pastga": "",                         # Pastga ko'rsatgich (Fallback: 👇)
    "tabrik": "5436040291507247633",     # Tabriklash (Fallback: 🎉)
    "salom": "5472055112702629499",      # Salomlashish (Fallback: 👋)
    "qahramon": "",                       # Personaj / Qahramon (Fallback: 👤)
    "vaqt": "",                           # Vaqt / Taymer (Fallback: ⏱)
    "statistika": "",                     # Statistika (Fallback: 📊)
    "til_uz": "",                         # O'zbek tili bayrog'i (Fallback: 🇺🇿)
    "til_en": "",                         # Ingliz tili bayrog'i (Fallback: 🇬🇧)
    "til_jp": "",                         # Yapon tili bayrog'i (Fallback: 🇯🇵)
    "maslahat": "5472146462362048818",    # Maslahat stikeri (Fallback: 💡)
    "taqiq": "",                          # Taqiq / Kirish mumkin emas (Fallback: ⛔️)
    "taqvim": "",                         # Yil / Sana taqvimi (Fallback: 📅)
    "studiya": "",                        # Studiya (Fallback: 🏢)
    "tahrir": "",                         # Tahrirlash / Yozish (Fallback: ✏️)
    "xabar": "",                          # Xabar / Maktub (Fallback: ✉️)
    "pochta": "",                         # Pochta qutisi / Yuborildi (Fallback: 📬)
    "ochirish": "",                       # O'chirish / Savatcha (Fallback: 🗑)
    "iltimos": "",                        # Iltimos / Rajo (Fallback: 🙏)
    "toj": "5467406098367521267",        # Toj / Super admin (Fallback: 👑)
    "raketa": "5445284980978621387",     # Tezkor start / Raketa (Fallback: 🚀)
    "info": "",                           # Ma'lumot / Info (Fallback: ℹ️)
    "qoshish": "",                        # Qo'shish / Plus (Fallback: ➕)

    # 2. Tugmalar uchun maxsus emoji_id lar (Inline va Reply Keyboard icon_custom_emoji_id)
    "btn_download": "5433811242135331842",# Yuklab olish tugmasi (Fallback: 📥)
    "btn_channel": "",                   # Kanalimiz tugmasi (Fallback: 📢)
    "btn_search": "",                    # Anime qidirish tugmasi (Fallback: 🔍)
    "btn_code": "",                      # Kod orqali qidirish tugmasi (Fallback: 🔢)
    "btn_photo": "",                     # Rasm orqali qidirish tugmasi (Fallback: 📸)
    "btn_random": "",                    # Tasodifiy anime tugmasi (Fallback: 🎲)
    "btn_all": "",                       # Barcha animelar tugmasi (Fallback: 🗂)
    "btn_new": "5361979468887893611",    # Yangi animelar tugmasi (Fallback: 🆕)
    "btn_info": "",                      # Bot haqida tugmasi (Fallback: ℹ️)
    "btn_admin": "",                     # Admin panel tugmasi (Fallback: ⚙️)
    "btn_check": "5427009714745517609",  # Tekshirish tugmasi (Fallback: ✅)
    "btn_cancel": "5465665476971471368", # Bekor qilish tugmasi (Fallback: ❌)
    "btn_play": "5375464961822695044",   # Qism ijro tugmasi (Fallback: ▶️)
    "btn_prev": "",                      # Oldingi sahifa tugmasi (Fallback: ⬅️)
    "btn_next": "",                      # Keyingi sahifa tugmasi (Fallback: ➡️)
    "btn_save": "5431449001532594346",   # Saqlash tugmasi (Fallback: ⚡️)
    "btn_edit": "",                      # Tahrirlash tugmasi (Fallback: ✏️)
})

# Standart zaxira emojilar (Fallback emojis)
DEFAULT_FALLBACKS: Dict[str, str] = CustomEmojiDict({
    "sarlavha": "🍥",
    "reyting": "⚛️",
    "qismlar": "🗃",
    "ovoz": "🎙",
    "sifat": "🎼",
    "janr": "🎭",
    "kod": "🔑",
    "tavsif": "📖",
    "qidiruv": "🔍",
    "holat": "📌",
    "korishlar": "👁",
    "katalog": "🎌",
    "video": "🎬",
    "yuklash": "📥",
    "kanal": "📢",
    "bot": "🤖",
    "yangi": "🆕",
    "rasm": "📸",
    "tasodifiy": "🎲",
    "admin": "⚙️",
    "muvaffaqiyat": "✅",
    "xato": "❌",
    "ogohlantirish": "⚠️",
    "kutish": "⏳",
    "chaqmoq": "⚡️",
    "olov": "🔥",
    "yulduz": "⭐",
    "popcorn": "🍿",
    "nuqta": "🔹",
    "pastga": "👇",
    "tabrik": "🎉",
    "salom": "👋",
    "qahramon": "👤",
    "vaqt": "⏱",
    "statistika": "📊",
    "til_uz": "🇺🇿",
    "til_en": "🇬🇧",
    "til_jp": "🇯🇵",
    "maslahat": "💡",
    "taqiq": "⛔️",
    "taqvim": "📅",
    "studiya": "🏢",
    "tahrir": "✏️",
    "xabar": "✉️",
    "pochta": "📬",
    "ochirish": "🗑",
    "iltimos": "🙏",
    "toj": "👑",
    "raketa": "🚀",
    "info": "ℹ️",
    "qoshish": "➕",

    # Tugmalar
    "btn_download": "📥",
    "btn_channel": "📢",
    "btn_search": "🔍",
    "btn_code": "🔢",
    "btn_photo": "📸",
    "btn_random": "🎲",
    "btn_all": "🗂",
    "btn_new": "🆕",
    "btn_info": "ℹ️",
    "btn_admin": "⚙️",
    "btn_check": "✅",
    "btn_cancel": "❌",
    "btn_play": "▶️",
    "btn_prev": "⬅️",
    "btn_next": "➡️",
    "btn_save": "⚡️",
    "btn_edit": "✏️",
})

# Inglizcha va boshqa alternativ kalit so'zlar uchun aliaslar
_EMOJI_ALIASES: Dict[str, str] = {
    "title": "sarlavha",
    "rating": "reyting",
    "episodes": "qismlar",
    "voice": "ovoz",
    "audio": "ovoz",
    "quality": "sifat",
    "genre": "janr",
    "genres": "janr",
    "code": "kod",
    "description": "tavsif",
    "search": "qidiruv",
    "status": "holat",
    "views": "korishlar",
    "catalog": "katalog",
    "download": "yuklash",
    "channel": "kanal",
    "photo": "rasm",
    "image": "rasm",
    "random": "tasodifiy",
    "new": "yangi",
    "settings": "admin",
    "success": "muvaffaqiyat",
    "check": "muvaffaqiyat",
    "error": "xato",
    "cancel": "xato",
    "warning": "ogohlantirish",
    "wait": "kutish",
    "fire": "olov",
    "lightning": "chaqmoq",
    "star": "yulduz",
    "dot": "nuqta",
    "down": "pastga",
    "congrats": "tabrik",
    "wave": "salom",
    "character": "qahramon",
    "time": "vaqt",
    "stats": "statistika",
    "play": "btn_play",
    "prev": "btn_prev",
    "next": "btn_next",
    "save": "btn_save",
    "edit": "btn_edit",
    "calendar": "taqvim",
    "studio": "studiya",
    "ban": "taqiq",
    "delete": "ochirish",
    "message": "xabar",
    "mail": "pochta",
    "rocket": "raketa",
    "crown": "toj",
}


def is_valid_emoji_id(val: Optional[str]) -> bool:
    """Emoji ID mavjud, bo'sh emas, raqamli va placeholder emasligini tekshirish"""
    if val is None or not isinstance(val, (str, int)):
        return False
    s = str(val).strip()
    if not s or s.lower() in ("0", "none", "null", "", "false", "undefined"):
        return False
    upper = s.upper()
    if "YOUR_" in upper or "PLACEHOLDER" in upper or "EMOJI_ID" in upper:
        return False
    return s.isdigit() and int(s) > 0


def get_custom_emoji(key: str, fallback: str = "") -> str:
    """
    Markazlashgan Premium Custom Emoji helper funksiyasi:
    Agar ko'rsatilgan 'key' uchun CUSTOM_EMOJIS ichida haqiqiy emoji_id mavjud bo'lsa:
        <tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>
    Aks holda:
        fallback belgisi (yoki DEFAULT_FALLBACKS dagi standart belgi)
    """
    if not key:
        return fallback or ""
    clean_key = str(key).strip().lower()
    resolved_key = _EMOJI_ALIASES.get(clean_key, clean_key)
    fb = fallback if fallback else DEFAULT_FALLBACKS.get(resolved_key, DEFAULT_FALLBACKS.get(clean_key, ""))
    raw_val = CUSTOM_EMOJIS.get(resolved_key, CUSTOM_EMOJIS.get(clean_key))
    if is_valid_emoji_id(raw_val):
        emoji_id = str(raw_val).strip()
        safe_fb = fb if fb else "✨"
        return f'<tg-emoji emoji-id="{emoji_id}">{safe_fb}</tg-emoji>'
    return fb


def get_emoji_id(key: str) -> Optional[str]:
    """
    Tugmalar (icon_custom_emoji_id) uchun sof emoji_id ni olish.
    Agar kiritilmagan yoki placeholder bo'lsa, None qaytaradi.
    """
    if not key:
        return None
    clean_key = str(key).strip().lower()
    resolved_key = _EMOJI_ALIASES.get(clean_key, clean_key)
    raw_val = CUSTOM_EMOJIS.get(resolved_key, CUSTOM_EMOJIS.get(clean_key))
    if is_valid_emoji_id(raw_val):
        return str(raw_val).strip()
    return None


# Environment o'zgaruvchilari orqali yuklash (EMOJI_SARLAVHA="...", CUSTOM_EMOJI_SARLAVHA="...")
for _env_name, _env_val in os.environ.items():
    if not _env_val:
        continue
    for _prefix in ("EMOJI_", "CUSTOM_EMOJI_"):
        if _env_name.startswith(_prefix):
            _raw_k = _env_name[len(_prefix):].lower()
            _resolved_k = _EMOJI_ALIASES.get(_raw_k, _raw_k)
            CUSTOM_EMOJIS[_resolved_k] = _env_val.strip()


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram bot API token")
    BOT_USERNAME: str = Field(default="Alpha_animelar_bot", description="Bot username")
    CHANNEL_USERNAME: str = Field(default="@uzbekcha_animelar_alpha", description="Asosiy kanal username")
    CHANNEL_URL: str = Field(default="https://t.me/uzbekcha_animelar_alpha", description="Asosiy kanal havolasi")
    
    ADMIN_IDS_RAW: str = Field(default="6444010235,8477471260", alias="ADMIN_IDS", description="Vergul bilan ajratilgan admin ID lari")
    ADMIN_SECRET_KEY: str = Field(default="anime2026", description="Admin huquqini olish paroli")
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///bot_database.db", description="Database URI")
    
    # MongoDB Atlas Cloud Database sozlamalari
    MONGODB_URI: str = Field(default="", description="MongoDB Atlas Connection URI (cloud.mongodb.com)")
    MONGODB_DB_NAME: str = Field(default="AlphaAnimeBotDB", description="MongoDB Database nomi")

    # 24/7 Web Server & Cloud Hosting sozlamalari
    PORT: int = Field(default=8080, description="Cloud web server porti (Render, Koyeb, Railway)")
    HOST: str = Field(default="0.0.0.0", description="Web server hosti")
    WEB_SERVER_ENABLED: bool = Field(default=True, description="Veb-serverni faollashtirish")
    WEBHOOK_URL: str = Field(default="", description="Webhook URL (kerak bo'lganda)")

    # Telegram Cloud Zaxiralash (@acacafagag) sozlamalari
    BACKUP_CHANNEL_ID: str = Field(default="-1003957205922", description="Zaxira yuboriladigan kanal ID")
    BACKUP_INTERVAL_MINUTES: int = Field(default=30, description="Avtomatik zaxiralash oralig'i (daqiqa)")
    AUTO_RESTORE_ENABLED: bool = Field(default=True, description="Avtomatik tiklash imkoniyati")

    # AI Vision & Anime Reverse Search sozlamalari
    GEMINI_API_KEY: str = Field(default="", description="Gemini Multimodal Vision API kaliti")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def admin_ids(self) -> Set[int]:
        ids = {6444010235, 8477471260}
        if self.ADMIN_IDS_RAW:
            for item in self.ADMIN_IDS_RAW.split(","):
                cleaned = item.strip()
                if cleaned.isdigit():
                    ids.add(int(cleaned))
        return ids

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids


config = Settings()

