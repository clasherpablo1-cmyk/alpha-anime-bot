import html
import logging
from typing import Optional, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions, URLInputFile
from aiogram.exceptions import TelegramBadRequest
from database.models import Anime
from config import config, get_custom_emoji, get_emoji_id, CUSTOM_EMOJIS

logger = logging.getLogger(__name__)


def format_channel_post(anime: Anime) -> Tuple[str, InlineKeyboardMarkup]:
    """Kanalga yangi anime joylanganda e'lon qilish uchun foydalanuvchi so'ragan blockquote ko'rinishidagi post"""
    title_raw = anime.title_uz
    if anime.title_romaji and anime.title_romaji.lower() != anime.title_uz.lower():
        title_raw += f" ( {anime.title_romaji} )"
    elif anime.year:
        title_raw += f" ( {anime.year} )"
    title_display = html.escape(title_raw, quote=False)

    year_str = f"{anime.year}-yil" if anime.year else "Noma'lum"
    genres_str = html.escape(anime.genres or "Sarguzasht, Fantastika", quote=False)
    status_str = html.escape(anime.status or "Tugallangan", quote=False)
    total_episodes_str = f"{anime.total_episodes} ta" if anime.total_episodes else "Noma'lum"

    bot_url = f"https://t.me/{config.BOT_USERNAME}?start={anime.code}"

    # 1. Sarlavha bloki (🍥 emoji va blockquote)
    header_block = f"<blockquote>{get_custom_emoji('sarlavha', '🍥')} <b>{title_display}</b></blockquote>"

    # 2. Xususiyatlar jadval-qutisi (╭ ├ ╰ ramkasi bilan)
    details_block = (
        f"<blockquote>╭──────────────────────\n"
        f"├ {get_custom_emoji('reyting', '⚛️')} <b>Reyting -</b> 8.5 IMDb\n"
        f"├ {get_custom_emoji('qismlar', '🗃')} <b>Qismlar -</b> {total_episodes_str}\n"
        f"├ {get_custom_emoji('ovoz', '🎙')} <b>Ovoz -</b> O'zbekcha #Rasmiy\n"
        f"├ {get_custom_emoji('sifat', '🎼')} <b>Sifati -</b> 720p HD #Multi\n"
        f"├ {get_custom_emoji('janr', '🎭')} <b>Janr -</b> {genres_str}\n"
        f"├ {get_custom_emoji('kod', '🔑')} <b>Kodi -</b> <code>#{anime.code}</code>\n"
        f"╰──────────────────────</blockquote>"
    )

    # 3. Kengayuvchi (expandable) mazmuni
    desc_block = ""
    if anime.description:
        desc_raw = anime.description.strip()
        if len(desc_raw) > 300:
            desc_raw = desc_raw[:300] + "..."
        desc_str = html.escape(desc_raw, quote=False)
        desc_block = f"\n\n<blockquote expandable>{get_custom_emoji('tavsif', '📖')} <b>Qisqacha mazmuni:</b>\n<i>{desc_str}</i></blockquote>"

    clean_tag = "".join(c for c in anime.title_uz.lower() if c.isalnum())
    tags_line = f"\n\n#{clean_tag} #anime #kod_{anime.code}" if clean_tag else f"\n\n#anime #kod_{anime.code}"

    text = f"{header_block}\n\n{details_block}{desc_block}{tags_line}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Yuklab olish / Ko'rish",
                    url=bot_url,
                    icon_custom_emoji_id=get_emoji_id("btn_download")
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Kanalimiz",
                    url=config.CHANNEL_URL,
                    icon_custom_emoji_id=get_emoji_id("btn_channel")
                )
            ]
        ]
    )

    return text, keyboard


async def post_anime_to_channel(bot, anime: Anime) -> bool:
    """Yangi anime qo'shilganda kanalga rasmli va 'Ko'rish' tugmali chiroyli post chiqarish"""
    try:
        text, kb = format_channel_post(anime)
        poster = anime.poster_file_id
        if poster:
            try:
                if poster.startswith("http://") or poster.startswith("https://"):
                    await bot.send_photo(
                        chat_id=config.CHANNEL_USERNAME,
                        photo=URLInputFile(poster),
                        caption=text,
                        reply_markup=kb,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_photo(
                        chat_id=config.CHANNEL_USERNAME,
                        photo=poster,
                        caption=text,
                        reply_markup=kb,
                        parse_mode="HTML"
                    )
                logger.info(f"Yangi anime #{anime.code} kanalga rasmi bilan muvaffaqiyatli post qilindi.")
                return True
            except Exception as photo_err:
                logger.warning(f"Kanalga rasm bilan post chiqarishda xato ({photo_err}), matnli yuborilmoqda...")

        await bot.send_message(
            chat_id=config.CHANNEL_USERNAME,
            text=text,
            reply_markup=kb,
            parse_mode="HTML",
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
        logger.info(f"Yangi anime #{anime.code} kanalga matnli post qilindi.")
        return True
    except Exception as e:
        logger.error(f"Kanalga yangi anime postini chiqarishda xatolik: {e}")
        return False


def format_episode_caption(anime_title: str, ep_number: int, quality: str = "720p") -> str:
    """O'zbek yoshlariga mos olovli, brendlangan video izohi"""
    clean_tag = "".join(c for c in anime_title.lower() if c.isalnum())
    tag = f"#{clean_tag}" if clean_tag else "#anime"
    safe_title = html.escape(anime_title, quote=False)
    safe_quality = html.escape(quality, quote=False)

    text = (
        f"{get_custom_emoji('video', '🎬')} <b>{safe_title}</b> — <b>{ep_number}-qism</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{get_custom_emoji('sifat', '💾')} Sifati: <b>{safe_quality} HD</b>\n"
        f"{get_custom_emoji('til_uz', '🇺🇿')} Tili: <b>O'zbekcha tarjima</b>\n"
        f"{get_custom_emoji('kanal', '📢')} Bizning kanal: {config.CHANNEL_USERNAME}\n"
        f"{get_custom_emoji('bot', '🤖')} Bot: @{config.BOT_USERNAME}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Do'stlaringiz bilan ulashing! Maroqli tomosha!</i> {get_custom_emoji('popcorn', '🍿')}\n"
        f"{tag} #uzbekcha_anime #qism_{ep_number}"
    )
    return text


def format_channel_catalog(animes) -> Tuple[str, InlineKeyboardMarkup]:
    """Kanalga qadab qo'yish uchun barcha animelar matnli mundarijasi (ko'k giperhavolalar bilan, 4000 belgi xavfsiz)"""
    header = (
        f"{get_custom_emoji('katalog', '🎌')} <b>«UZBEKCHA ANIMELAR» MUNDARIJASI (KATALOG)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Animeni 1 ta tugma bilan yuklab olish yoki tomosha qilish uchun uning <b>ko'k nomini</b> bosing:</i>\n\n"
    )

    footer = (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{get_custom_emoji('bot', '🤖')} <b>Bizning rasmiy bot:</b> @{config.BOT_USERNAME}\n"
        f"{get_custom_emoji('kanal', '📢')} <b>Kanalimiz:</b> {config.CHANNEL_USERNAME}\n"
        f"<i>Barcha animelar bir joyda jamlangan rasmiy mundarija!</i>"
    )

    # Maksimal hajm chegarasi Telegramda 4096 belgi
    available_chars = 3900 - len(header) - len(footer)
    lines = []
    overflow_count = 0

    for idx, anime in enumerate(animes):
        bot_url = f"https://t.me/{config.BOT_USERNAME}?start={anime.code}"
        try:
            eps_count = len(anime.episodes) if anime.episodes is not None else 0
        except Exception:
            eps_count = 0
        total_str = f"{eps_count}/{anime.total_episodes}" if anime.total_episodes else f"{eps_count}"
        safe_title = html.escape(anime.title_uz, quote=False)

        line = (
            f"{get_custom_emoji('nuqta', '🔹')} <a href=\"{bot_url}\"><b>{safe_title}</b></a> — "
            f"<i>{total_str} ta qism</i> [#{anime.code}]\n"
        )
        if len("".join(lines)) + len(line) < available_chars:
            lines.append(line)
        else:
            overflow_count = len(animes) - idx
            break

    if overflow_count > 0:
        lines.append(f"\n<i>...va yana {overflow_count} ta sara anime botimizda!</i>\n")

    text = header + "".join(lines) + footer

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 Bot orqali barcha qismlarni yuklash",
                    url=f"https://t.me/{config.BOT_USERNAME}",
                    icon_custom_emoji_id=get_emoji_id("btn_download")
                )
            ]
        ]
    )

    return text, keyboard


def format_anime_card(anime: Anime) -> str:
    """Bot ichida foydalanuvchiga anime haqida zamonaviy blockquote formatida to'liq ma'lumot chiqarish"""
    title_raw = anime.title_uz
    if anime.title_romaji and anime.title_romaji.lower() != anime.title_uz.lower():
        title_raw += f" ( {anime.title_romaji} )"
    elif anime.year:
        title_raw += f" ( {anime.year} )"
    title_display = html.escape(title_raw, quote=False)

    genres_str = html.escape(anime.genres or "Anime", quote=False)
    status_str = html.escape(anime.status or "Tugallangan", quote=False)
    try:
        loaded_eps_count = len(anime.episodes) if anime.episodes is not None else 0
    except Exception:
        loaded_eps_count = 0
    total_episodes_str = f"{loaded_eps_count} / {anime.total_episodes} ta"

    desc_raw = anime.description or "Ajoyib qiziqarli anime sarguzashtlari!"
    if len(desc_raw) > 300:
        desc_raw = desc_raw[:300] + "..."
    desc_str = html.escape(desc_raw, quote=False)

    text = (
        f"<blockquote>{get_custom_emoji('sarlavha', '🍥')} <b>{title_display}</b></blockquote>\n\n"
        f"<blockquote>╭──────────────────────\n"
        f"├ {get_custom_emoji('reyting', '⚛️')} <b>Reyting -</b> 8.5 IMDb\n"
        f"├ {get_custom_emoji('qismlar', '🗃')} <b>Qismlar -</b> {total_episodes_str}\n"
        f"├ {get_custom_emoji('ovoz', '🎙')} <b>Ovoz -</b> O'zbekcha #Rasmiy\n"
        f"├ {get_custom_emoji('sifat', '🎼')} <b>Sifati -</b> 720p HD #Multi\n"
        f"├ {get_custom_emoji('janr', '🎭')} <b>Janr -</b> {genres_str}\n"
        f"├ {get_custom_emoji('holat', '📌')} <b>Holati -</b> {status_str}\n"
        f"├ {get_custom_emoji('kod', '🔑')} <b>Kodi -</b> <code>#{anime.code}</code>\n"
        f"├ {get_custom_emoji('korishlar', '👁')} <b>Ko'rishlar -</b> {anime.views_count}\n"
        f"╰──────────────────────</blockquote>\n\n"
        f"<blockquote expandable>{get_custom_emoji('tavsif', '📖')} <b>Qisqacha mazmuni:</b>\n<i>{desc_str}</i></blockquote>\n\n"
        f"{get_custom_emoji('pastga', '👇')} <i>Qismni tanlang yoki barcha qismlarni bir bosishda yuklab oling:</i>"
    )
    return text


async def sync_channel_catalog(bot) -> bool:
    """Kanalga chiqarilgan katalog (mundarija) postini yangilash (odamlarga bildirishnoma bormasdan jimgina tahrirlanadi)"""
    from database.db import db
    animes = await db.get_recent_animes(limit=100)
    if not animes:
        return False

    text, kb = format_channel_catalog(animes)
    catalog_msg_id_str = await db.get_setting("channel_catalog_msg_id")

    # Agar bazada xabar ID saqlanmagan bo'lsa, kanalning hozirgi qadalgan xabarini tekshirib ko'ramiz
    if not (catalog_msg_id_str and catalog_msg_id_str.isdigit()):
        try:
            chat = await bot.get_chat(config.CHANNEL_USERNAME)
            if chat.pinned_message:
                catalog_msg_id_str = str(chat.pinned_message.message_id)
                await db.set_setting("channel_catalog_msg_id", catalog_msg_id_str)
                logger.info(f"Kanal qadalgan posti bazaga bog'landi: ID {catalog_msg_id_str}")
        except Exception as chat_err:
            logger.warning(f"Kanal qadalgan xabarini aniqlashda xatolik: {chat_err}")

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
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True)
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
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True)
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
