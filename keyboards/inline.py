from typing import Sequence, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Anime, Episode, RequiredChannel
from config import config, get_emoji_id


def get_subscription_keyboard(channels: Sequence[RequiredChannel]) -> InlineKeyboardMarkup:
    """Majburiy kanallar ro'yxati va tekshirish tugmasi"""
    keyboard_buttons: List[List[InlineKeyboardButton]] = []

    for ch in channels:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📢 {ch.channel_title}",
                url=ch.channel_url,
                icon_custom_emoji_id=get_emoji_id("btn_channel")
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(
            text="✅ Obunani tekshirish",
            callback_data="check_subscription",
            icon_custom_emoji_id=get_emoji_id("btn_check")
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_anime_episodes_keyboard(
    anime: Anime,
    page: int = 0,
    page_size: int = 20,
    is_admin: bool = False
) -> InlineKeyboardMarkup:
    """Animening yuklangan qismlarini tugmalar orqali chiqarish"""
    keyboard_buttons: List[List[InlineKeyboardButton]] = []
    
    # Tartiblangan qismlar
    episodes = sorted(anime.episodes, key=lambda e: e.episode_number)
    total_eps = len(episodes)

    if total_eps > 0:
        # Eng yuqorida 1-klik bilan barcha qismlarni yuklash tugmasi!
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📥 Barcha qismlarni yuklab olish ({total_eps} ta qism)",
                callback_data=f"dl_all_{anime.id}",
                icon_custom_emoji_id=get_emoji_id("btn_download")
            )
        ])

        start_idx = page * page_size
        end_idx = min(start_idx + page_size, total_eps)
        page_episodes = episodes[start_idx:end_idx]

        row: List[InlineKeyboardButton] = []
        for ep in page_episodes:
            btn_text = f"▶️ {ep.episode_number}-qism"
            callback = f"ep_{anime.id}_{ep.episode_number}"
            row.append(
                InlineKeyboardButton(
                    text=btn_text,
                    callback_data=callback,
                    icon_custom_emoji_id=get_emoji_id("btn_play")
                )
            )
            if len(row) == 4:
                keyboard_buttons.append(row)
                row = []
        if row:
            keyboard_buttons.append(row)

        # Pagination tugmalari (agar 20 tadan ko'p qism bo'lsa)
        nav_buttons: List[InlineKeyboardButton] = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Oldingi",
                    callback_data=f"page_{anime.id}_{page - 1}",
                    icon_custom_emoji_id=get_emoji_id("btn_prev")
                )
            )
        if end_idx < total_eps:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Keyingi ➡️",
                    callback_data=f"page_{anime.id}_{page + 1}",
                    icon_custom_emoji_id=get_emoji_id("btn_next")
                )
            )
        if nav_buttons:
            keyboard_buttons.append(nav_buttons)
    else:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="⏳ Hozircha qismlar yuklanmagan",
                callback_data="no_episodes",
                icon_custom_emoji_id=get_emoji_id("kutish")
            )
        ])

    # Kanalga havola tugmasi
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="📢 Bizning kanalimiz",
            url=config.CHANNEL_URL,
            icon_custom_emoji_id=get_emoji_id("btn_channel")
        )
    ])

    # Admin boshqaruv tugmalari (faqat adminlarga ko'rinadi)
    if is_admin:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="📢 Kanalga post chiqarish",
                callback_data=f"admin_post_{anime.code}",
                icon_custom_emoji_id=get_emoji_id("btn_channel")
            ),
            InlineKeyboardButton(
                text="⚡️ Ommaviy qism yuklash",
                callback_data=f"admin_batch_{anime.code}",
                icon_custom_emoji_id=get_emoji_id("btn_save")
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_anime_search_keyboard(animes: Sequence[Anime]) -> InlineKeyboardMarkup:
    """Qidiruv natijalari inline ro'yxati"""
    keyboard_buttons: List[List[InlineKeyboardButton]] = []

    for anime in animes:
        title = anime.title_uz
        if len(title) > 25:
            title = title[:25] + "..."
        year_str = f"({anime.year})" if anime.year else ""
        btn_text = f"🎬 {title} {year_str} [#{anime.code}]"

        keyboard_buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"anime_code_{anime.code}",
                icon_custom_emoji_id=get_emoji_id("btn_play")
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_admin_post_confirm_keyboard(anime_code: int) -> InlineKeyboardMarkup:
    """Kanalga post yuborishni tasdiqlash"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha, kanalga chiqarilsin",
                    callback_data=f"confirm_post_{anime_code}",
                    icon_custom_emoji_id=get_emoji_id("btn_check")
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancel_admin_action",
                    icon_custom_emoji_id=get_emoji_id("btn_cancel")
                )
            ]
        ]
    )


def get_anime_quick_save_keyboard() -> InlineKeyboardMarkup:
    """Anime topilganda 1-klik bilan tezkor saqlash va qism yuklashga o'tish"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡️ Saqlash va qism yuklash",
                    callback_data="admin_quick_save",
                    icon_custom_emoji_id=get_emoji_id("btn_save")
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Nomni o'zgartirish",
                    callback_data="admin_edit_title",
                    icon_custom_emoji_id=get_emoji_id("btn_edit")
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancel_admin_action",
                    icon_custom_emoji_id=get_emoji_id("btn_cancel")
                )
            ]
        ]
    )


def get_cancel_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancel_action",
                    icon_custom_emoji_id=get_emoji_id("btn_cancel")
                )
            ]
        ]
    )

