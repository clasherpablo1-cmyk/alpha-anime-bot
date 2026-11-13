from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import get_emoji_id


def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy foydalanuvchi menyusi"""
    keyboard = [
        [
            KeyboardButton(text="🔍 Anime qidirish", icon_custom_emoji_id=get_emoji_id("btn_search")),
            KeyboardButton(text="🔢 Kod orqali qidirish", icon_custom_emoji_id=get_emoji_id("btn_code")),
        ],
        [
            KeyboardButton(text="📸 Rasm orqali qidirish", icon_custom_emoji_id=get_emoji_id("btn_photo")),
            KeyboardButton(text="🎲 Tasodifiy anime", icon_custom_emoji_id=get_emoji_id("btn_random")),
        ],
        [
            KeyboardButton(text="🗂 Barcha animelar", icon_custom_emoji_id=get_emoji_id("btn_all")),
            KeyboardButton(text="🆕 Yangi animelar", icon_custom_emoji_id=get_emoji_id("btn_new")),
        ],
        [
            KeyboardButton(text="📢 Bizning kanal", icon_custom_emoji_id=get_emoji_id("btn_channel")),
            KeyboardButton(text="ℹ️ Bot haqida", icon_custom_emoji_id=get_emoji_id("btn_info")),
        ]
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Admin Panel", icon_custom_emoji_id=get_emoji_id("btn_admin"))])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Quyidagi bo'limlardan birini tanlang..."
    )


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Admin boshqaruv menyusi"""
    keyboard = [
        [
            KeyboardButton(text="➕ Yangi anime qo'shish", icon_custom_emoji_id=get_emoji_id("btn_new")),
            KeyboardButton(text="⚡️ Ommaviy qism yuklash", icon_custom_emoji_id=get_emoji_id("btn_save")),
        ],
        [
            KeyboardButton(text="🎬 Bitta qism yuklash", icon_custom_emoji_id=get_emoji_id("btn_play")),
            KeyboardButton(text="📢 Kanalga post chiqarish", icon_custom_emoji_id=get_emoji_id("btn_channel")),
        ],
        [
            KeyboardButton(text="📋 Kanal katalog posti", icon_custom_emoji_id=get_emoji_id("btn_all")),
            KeyboardButton(text="📊 Statistika", icon_custom_emoji_id=get_emoji_id("btn_info")),
        ],
        [
            KeyboardButton(text="✉️ Xabar yuborish (Broadcast)", icon_custom_emoji_id=get_emoji_id("btn_channel")),
            KeyboardButton(text="💾 Zaxira (Backup)", icon_custom_emoji_id=get_emoji_id("btn_save")),
        ],
        [
            KeyboardButton(text="🗑 Animeni o'chirish", icon_custom_emoji_id=get_emoji_id("btn_cancel")),
            KeyboardButton(text="🔙 Bosh menyuga qaytish", icon_custom_emoji_id=get_emoji_id("btn_prev"))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Admin boshqaruv buyrug'ini tanlang..."
    )


def get_batch_upload_menu() -> ReplyKeyboardMarkup:
    """Ommaviy yuklash vaqtidagi tugmalar"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏁 Ommaviy yuklashni tugatish", icon_custom_emoji_id=get_emoji_id("btn_check"))],
            [KeyboardButton(text="❌ Bekor qilish", icon_custom_emoji_id=get_emoji_id("btn_cancel"))]
        ],
        resize_keyboard=True
    )


def get_cancel_reply() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish", icon_custom_emoji_id=get_emoji_id("btn_cancel"))]],
        resize_keyboard=True
    )

