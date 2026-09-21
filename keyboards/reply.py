from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy foydalanuvchi menyusi"""
    keyboard = [
        [
            KeyboardButton(text="🔍 Anime qidirish"),
            KeyboardButton(text="🔢 Kod orqali qidirish"),
        ],
        [
            KeyboardButton(text="🎲 Tasodifiy anime"),
            KeyboardButton(text="🆕 Yangi animelar"),
        ],
        [
            KeyboardButton(text="📢 Bizning kanal"),
            KeyboardButton(text="ℹ️ Bot haqida"),
        ]
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Admin Panel")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Quyidagi bo'limlardan birini tanlang..."
    )


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Admin boshqaruv menyusi"""
    keyboard = [
        [
            KeyboardButton(text="➕ Yangi anime qo'shish"),
            KeyboardButton(text="⚡️ Ommaviy qism yuklash"),
        ],
        [
            KeyboardButton(text="🎬 Bitta qism yuklash"),
            KeyboardButton(text="📢 Kanalga post chiqarish"),
        ],
        [
            KeyboardButton(text="📋 Kanal katalog posti"),
            KeyboardButton(text="📊 Statistika"),
        ],
        [
            KeyboardButton(text="✉️ Xabar yuborish (Broadcast)"),
            KeyboardButton(text="🗑 Animeni o'chirish"),
        ],
        [
            KeyboardButton(text="🔙 Bosh menyuga qaytish")
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
            [KeyboardButton(text="🏁 Ommaviy yuklashni tugatish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )


def get_cancel_reply() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
