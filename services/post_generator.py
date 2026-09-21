import logging
from typing import Optional, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from database.models import Anime
from config import config

logger = logging.getLogger(__name__)


def format_channel_post(anime: Anime) -> Tuple[str, InlineKeyboardMarkup]:
    """Kanalga chiqarish uchun chiroyli bezatilgan post matni va inline tugmalar"""
    title_display = anime.title_uz
    if anime.title_romaji and anime.title_romaji.lower() != anime.title_uz.lower():
        title_display += f" / {anime.title_romaji}"

    year_str = f"{anime.year}-yil" if anime.year else "Noma'lum"
    genres_str = anime.genres or "Sarguzasht, Fantastika"
    status_str = anime.status or "Tugallangan"
    total_episodes_str = f"{anime.total_episodes} ta qism" if anime.total_episodes else "Noma'lum"
    
    desc_str = anime.description or "Ajoyib qiziqarli anime sarguzashtlari!"
    if len(desc_str) > 300:
        desc_str = desc_str[:300] + "..."

    bot_url = f"https://t.me/{config.BOT_USERNAME}?start={anime.code}"

    text = (
        f"🎬 <b>{title_display}</b>\n\n"
        f"▫️ <b>Qismlar:</b> {total_episodes_str}\n"
        f"▫️ <b>Holati:</b> {status_str}\n"
        f"▫️ <b>Chiqarilgan yili:</b> {year_str}\n"
        f"▫️ <b>Janr:</b> {genres_str}\n"
        f"▫️ <b>Ovoz:</b> O'zbekcha tarjima (Professional)\n"
        f"▫️ <b>Sifat:</b> 720p HD\n\n"
        f"📖 <b>Qisqacha mazmuni:</b>\n<i>{desc_str}</i>\n\n"
        f"🔑 <b>Anime kodi:</b> <code>{anime.code}</code>\n"
        f"👉 <b>Ko'rish uchun bot:</b> @{config.BOT_USERNAME}\n\n"
        f"📢 Bizning kanal: {config.CHANNEL_USERNAME}\n"
        f"#kod_{anime.code} #anime"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Qismlarni botda ko'rish",
                    url=bot_url
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Kanalga a'zo bo'lish",
                    url=config.CHANNEL_URL
                )
            ]
        ]
    )

    return text, keyboard


def format_episode_caption(anime_title: str, ep_number: int, quality: str = "720p") -> str:
    """O'zbek yoshlariga mos olovli, brendlangan video izohi"""
    clean_tag = "".join(c for c in anime_title.lower() if c.isalnum())
    tag = f"#{clean_tag}" if clean_tag else "#anime"

    text = (
        f"🎬 <b>{anime_title}</b> — <b>{ep_number}-qism</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💾 Sifati: <b>{quality} HD</b>\n"
        f"🇺🇿 Tili: <b>O'zbekcha tarjima</b>\n"
        f"📢 Bizning kanal: {config.CHANNEL_USERNAME}\n"
        f"🤖 Bot: @{config.BOT_USERNAME}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Do'stlaringiz bilan ulashing! Maroqli tomosha!</i> 🍿\n"
        f"{tag} #uzbekcha_anime #qism_{ep_number}"
    )
    return text


def format_channel_catalog(animes) -> Tuple[str, InlineKeyboardMarkup]:
    """Kanalga qadab qo'yish uchun barcha animelar matnli mundarijasi (ko'k giperhavolalar bilan)"""
    text = (
        f"🎌 <b>«UZBEKCHA ANIMELAR» MUNDARIJASI (KATALOG)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Animeni 1 ta tugma bilan yuklab olish yoki tomosha qilish uchun uning <b>ko'k nomini</b> bosing:</i>\n\n"
    )

    for anime in animes:
        bot_url = f"https://t.me/{config.BOT_USERNAME}?start={anime.code}"
        eps_count = len(anime.episodes)
        total_str = f"{eps_count}/{anime.total_episodes}" if anime.total_episodes else f"{eps_count}"
        
        text += (
            f"🔹 <a href=\"{bot_url}\"><b>{anime.title_uz}</b></a> — "
            f"<i>{total_str} ta qism</i> [#{anime.code}]\n"
        )

    text += (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>Bizning rasmiy bot:</b> @{config.BOT_USERNAME}\n"
        f"📢 <b>Kanalimiz:</b> {config.CHANNEL_USERNAME}\n"
        f"<i>Ro'yxat yangi animelar qo'shilishi bilan avtomatik yangilanib boradi!</i>"
    )

    # 100 lab ortiqcha tugmalar o'rniga faqat 1 ta toza, universal tugma!
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 Bot orqali barcha qismlarni yuklash",
                    url=f"https://t.me/{config.BOT_USERNAME}"
                )
            ]
        ]
    )

    return text, keyboard


def format_anime_card(anime: Anime) -> str:
    """Bot ichida foydalanuvchiga anime haqida to'liq ma'lumot chiqarish"""
    title_display = anime.title_uz
    if anime.title_romaji:
        title_display += f" ({anime.title_romaji})"

    year_str = f"{anime.year}" if anime.year else "Noma'lum"
    genres_str = anime.genres or "Anime"
    status_str = anime.status or "Tugallangan"
    total_episodes_str = f"{len(anime.episodes)} / {anime.total_episodes}"

    text = (
        f"🎬 <b>{title_display}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔑 <b>Kodi:</b> <code>{anime.code}</code>\n"
        f"📅 <b>Yili:</b> {year_str}\n"
        f"🎭 <b>Janrlari:</b> {genres_str}\n"
        f"📌 <b>Holati:</b> {status_str}\n"
        f"🎞 <b>Yuklangan qismlar:</b> {total_episodes_str}\n"
        f"👁 <b>Ko'rishlar soni:</b> {anime.views_count}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📖 <b>Mazmuni:</b>\n<i>{anime.description or 'Tavsif berilmagan.'}</i>\n\n"
        f"👇 <i>Qismni tanlang yoki barcha qismlarni bir bosishda yuklab oling:</i>"
    )
    return text


async def sync_channel_catalog(bot) -> bool:
    """Kanalga chiqarilgan katalog (mundarija) postini avtomatik yangilash (odamlarga bildirishnoma bormasdan jimgina yangilanadi)"""
    from database.db import db
    animes = await db.get_recent_animes(limit=100)
    if not animes:
        return False

    text, kb = format_channel_catalog(animes)
    catalog_msg_id_str = await db.get_setting("channel_catalog_msg_id")

    needs_new_post = True
    if catalog_msg_id_str and catalog_msg_id_str.isdigit():
        catalog_msg_id = int(catalog_msg_id_str)
        try:
            # Mavjud xabarni tahrirlaymiz (yangi xabar bormaydi, obunachilarni bezovta qilmaydi!)
            await bot.edit_message_text(
                chat_id=config.CHANNEL_USERNAME,
                message_id=catalog_msg_id,
                text=text,
                reply_markup=kb,
                parse_mode="HTML"
            )
            return True
        except TelegramBadRequest as e:
            err = str(e).lower()
            if "message is not modified" in err:
                # Xabar mazmuni o'zgarmagan — post allaqachon ayni shu holatda!
                # Yangi post yuborish QAT'IYAN taqiqlanadi!
                return True
            elif "message to edit not found" in err or "message can't be edited" in err:
                # Xabar kanaldan o'chirib yuborilgan, yangisini chiqarishga ruxsat
                logger.info(f"Eski katalog posti topilmadi ({e}), yangi post yaratiladi...")
                needs_new_post = True
            else:
                logger.warning(f"Katalog postini tahrirlashda TelegramBadRequest: {e}")
                return False
        except Exception as e:
            logger.error(f"Katalog postini tahrirlashda kutilmagan xato: {e}")
            return False
    else:
        needs_new_post = True

    # Faqatgina xabar umuman mavjud bo'lmaganda yoki kanaldan o'chirilgandagina yangi post chiqariladi
    if needs_new_post:
        try:
            new_msg = await bot.send_message(
                chat_id=config.CHANNEL_USERNAME,
                text=text,
                reply_markup=kb,
                parse_mode="HTML"
            )
            try:
                await bot.pin_chat_message(
                    chat_id=config.CHANNEL_USERNAME,
                    message_id=new_msg.message_id,
                    disable_notification=True
                )
            except Exception as e:
                logger.warning(f"Katalog postini qadashda xatolik: {e}")
            await db.set_setting("channel_catalog_msg_id", str(new_msg.message_id))
            return True
        except Exception as e:
            logger.error(f"Kanalga yangi katalog chiqarishda xatolik: {e}")
            return False

    return False
