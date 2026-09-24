import io
import re
import asyncio
import logging
from typing import Optional, Tuple
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, URLInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import config
from database.db import db
from database.models import Anime
from services.post_generator import format_anime_card, format_episode_caption
from services.anilist import anilist_service
from services.image_search import anime_image_search_service, AnimeSearchResult
from keyboards.reply import get_main_menu, get_cancel_reply
from keyboards.inline import (
    get_anime_episodes_keyboard,
    get_anime_search_keyboard,
    get_subscription_keyboard
)

logger = logging.getLogger(__name__)

user_router = Router(name="user_router")


class UserStates(StatesGroup):
    waiting_for_search_query = State()
    waiting_for_code = State()
    waiting_for_anime_photo = State()
    waiting_for_second_photo = State()


# ------------------ /start VA RO'YXATDAN O'TISH ------------------
@user_router.message(CommandStart())
async def handle_start(message: Message, command: CommandObject, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    if not user:
        return

    # Foydalanuvchini bazaga qo'shish yoki yangilash
    db_user = await db.get_or_create_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    is_admin = await db.is_admin(user.id)

    # Deep-link tekshiruvi: masalan t.me/Alpha_animelar_bot?start=105
    payload = command.args
    if payload and payload.isdigit():
        anime_code = int(payload)
        anime = await db.get_anime_by_code(anime_code)
        if anime:
            await send_anime_card(message, anime, is_admin)
            return

    welcome_text = (
        f"👋 Assalomu alaykum, <b>{user.full_name}</b>!\n\n"
        f"🎌 <b>«Uzbekcha animelar»</b> rasmiy botiga xush kelibsiz!\n\n"
        f"Bu yerda siz sara va yangi animelarni o'zbek tilida yuqori sifatda (HD) tomosha qilishingiz mumkin.\n\n"
        f"🔢 <i>Anime kodini yozib yuboring (masalan: <code>1</code>) yoki quyidagi menyudan foydalaning:</i>"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(is_admin=is_admin),
        parse_mode="HTML"
    )


# ------------------ ADMIN HUQUQINI OLISH (/claim_admin) ------------------
@user_router.message(Command("claim_admin"))
async def handle_claim_admin(message: Message, command: CommandObject) -> None:
    user = message.from_user
    if not user:
        return

    password = command.args.strip() if command.args else ""
    if password == config.ADMIN_SECRET_KEY:
        await db.set_user_admin(user.id, is_admin=True)
        await message.answer(
            f"🎉 Tabriklaymiz, <b>{user.full_name}</b>!\n"
            f"Sizga muvaffaqiyatli <b>Admin</b> huquqi berildi.\n"
            f"Endi /admin buyrug'i orqali boshqaruv paneliga kirishingiz mumkin.",
            reply_markup=get_main_menu(is_admin=True),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Parol noto'g'ri!\n"
            "Admin huquqini olish uchun to'g'ri kalit so'zni kiriting:\n"
            "<code>/claim_admin parol</code>",
            parse_mode="HTML"
        )


from middlewares.subscription import check_user_subscribed

# ------------------ OBUNANI QAYTA TEKSHIRISH CALLBACK ------------------
@user_router.callback_query(F.data == "check_subscription")
async def handle_check_subscription(callback: CallbackQuery, state: FSMContext) -> None:
    user = callback.from_user
    bot = callback.bot
    if not user or not bot:
        return

    channels = await db.get_required_channels()
    unsubscribed = []
    for ch in channels:
        is_sub = await check_user_subscribed(bot, user.id, ch.channel_id)
        if not is_sub:
            unsubscribed.append(ch)

    if unsubscribed:
        await callback.answer("❌ Hali kanallarga a'zo bo'lmadingiz! Avval obuna bo'ling.", show_alert=True)
    else:
        await callback.answer("✅ A'zoligingiz tasdiqlandi!", show_alert=False)
        is_admin = await db.is_admin(user.id)
        if callback.message:
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer(
                "✅ Rahmat! Obuna muvaffaqiyatli tasdiqlandi.\n"
                "Endi anime kodini yuborishingiz yoki menyudan foydalanishingiz mumkin:",
                reply_markup=get_main_menu(is_admin=is_admin)
            )


@user_router.message(Command("obuna"))
async def preview_subscription_prompt(message: Message) -> None:
    """Admin uchun obuna so'rovini qanday ko'rinishini tekshirish komandasi"""
    channels = await db.get_required_channels()
    sub_kb = get_subscription_keyboard(channels)
    await message.answer(
        "⚠️ <b>Botdan to'liq foydalanish uchun quyidagi kanalimizga obuna bo'ling!</b>\n\n"
        "<i>Kanalga a'zo bo'lgach, «✅ Obunani tekshirish» tugmasini bosing.</i>",
        reply_markup=sub_kb,
        parse_mode="HTML"
    )


# ------------------ ASOSIY MENYU BUYRUQLARI ------------------
@user_router.message(F.text == "❌ Bekor qilish")
async def handle_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    is_admin = await db.is_admin(message.from_user.id) if message.from_user else False
    await message.answer(
        "Amal bekor qilindi.",
        reply_markup=get_main_menu(is_admin=is_admin)
    )


@user_router.message(F.text == "🔍 Anime qidirish")
async def handle_search_button(message: Message, state: FSMContext) -> None:
    await state.set_state(UserStates.waiting_for_search_query)
    await message.answer(
        "🔎 Qidirayotgan animengiz nomini (o'zbekcha yoki inglizcha) yozib yuboring:\n\n"
        "<i>Masalan: Naruto, Solo Leveling, Demon Slayer...</i>",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@user_router.message(F.text == "🔢 Kod orqali qidirish")
async def handle_code_button(message: Message, state: FSMContext) -> None:
    await state.set_state(UserStates.waiting_for_code)
    await message.answer(
        "🔢 Anime kodini kiriting:\n\n"
        "<i>Masalan: 1, 5, 102...</i>",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@user_router.message(F.text == "📸 Rasm orqali qidirish")
async def handle_image_search_button(message: Message, state: FSMContext) -> None:
    await state.set_state(UserStates.waiting_for_anime_photo)
    await message.answer(
        "📸 <b>Rasm orqali anime qidirish</b>\n\n"
        "Iltimos, animedan olingan skrinshot yoki rasm yuboring.\n"
        "Bot uni darhol tahlil qilib, <b>O'zbekcha</b>, <b>Inglizcha</b> va <b>Yaponcha</b> nomlarini topib beradi!\n\n"
        "<i>💡 Maslahat: Kadr qanchalik tiniq bo'lsa, natija shunchalik aniq bo'ladi.</i>",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@user_router.message(F.text == "🎲 Tasodifiy anime")
async def handle_random_anime(message: Message) -> None:
    anime = await db.get_random_anime()
    if not anime:
        await message.answer("😔 Hozircha bazada animelar mavjud emas.")
        return
    is_admin = await db.is_admin(message.from_user.id) if message.from_user else False
    await send_anime_card(message, anime, is_admin)


@user_router.message(F.text == "🆕 Yangi animelar")
async def handle_recent_animes(message: Message) -> None:
    animes = await db.get_recent_animes(limit=10)
    if not animes:
        await message.answer("😔 Hozircha yangi animelar mavjud emas.")
        return
    kb = get_anime_search_keyboard(animes)
    await message.answer("🆕 <b>Oxirgi qo'shilgan sara animelar:</b>", reply_markup=kb, parse_mode="HTML")


@user_router.message(F.text == "📢 Bizning kanal")
async def handle_channel_info(message: Message) -> None:
    await message.answer(
        f"📢 <b>Rasmiy Telegram kanalimiz:</b>\n\n"
        f"👉 {config.CHANNEL_URL}\n\n"
        f"Eng so'nggi qismlar va yangiliklar aynan shu yerda chiqib boradi!",
        parse_mode="HTML"
    )


@user_router.message(F.text == "ℹ️ Bot haqida")
async def handle_about(message: Message) -> None:
    stats = await db.get_statistics()
    about_text = (
        f"🤖 <b>«Uzbekcha animelar» Boti</b>\n\n"
        f"Ushbu bot orqali siz sevimli animelaringizni o'zbek tilida yuqori sifatda bepul tomosha qilishingiz mumkin.\n\n"
        f"📊 <b>Bazada:</b>\n"
        f"• Animelar soni: <b>{stats['animes_count']} ta</b>\n"
        f"• Yuklangan qismlar: <b>{stats['episodes_count']} ta</b>\n"
        f"• Umumiy tomoshalar: <b>{stats['total_views']} marotaba</b>\n\n"
        f"Rasmiy kanal: {config.CHANNEL_USERNAME}"
    )
    await message.answer(about_text, parse_mode="HTML")


# ------------------ STATE ORQALI QIDIRUVNI ISHLASH ------------------
@user_router.message(UserStates.waiting_for_search_query)
async def process_search_query(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    query = message.text.strip()
    await state.clear()
    is_admin = await db.is_admin(message.from_user.id) if message.from_user else False

    animes = await db.search_animes(query, limit=10)
    if not animes:
        # Agar lokal bazada bo'lmasa, AniList orqali dunyo bazasidan qidiramiz
        anilist_info = await anilist_service.search_anime(query)
        if anilist_info:
            found_title = anilist_info.get("title_romaji") or anilist_info.get("title_english")
            year_str = f"({anilist_info.get('year')})" if anilist_info.get("year") else ""
            await message.answer(
                f"ℹ️ <b>Anime topildi, lekin hali botga yuklanmagan:</b>\n\n"
                f"🎬 <b>{found_title}</b> {year_str}\n"
                f"🎭 <b>Janr:</b> {anilist_info.get('genres')}\n"
                f"🎞 <b>Qismlar soni:</b> {anilist_info.get('episodes')} ta\n"
                f"📖 <i>{anilist_info.get('description')}</i>\n\n"
                f"⚠️ <i>Ushbu animening qismlari tez orada kanalimizga va botga joylanadi!</i>\n"
                f"📢 Bizni kuzatib boring: {config.CHANNEL_USERNAME}",
                reply_markup=get_main_menu(is_admin=is_admin),
                parse_mode="HTML"
            )
            return

        await message.answer(
            f"🔍 «<b>{query}</b>» bo'yicha hech qanday anime topilmadi.\n"
            f"Nomini to'g'ri yozganingizga ishonch hosil qiling yoki kod orqali qidiring.",
            reply_markup=get_main_menu(is_admin=is_admin),
            parse_mode="HTML"
        )
        return

    kb = get_anime_search_keyboard(animes)
    await message.answer(
        f"🔍 «<b>{query}</b>» bo'yicha topilgan animelar:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@user_router.message(UserStates.waiting_for_code)
async def process_code_input(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    text = message.text.strip()
    await state.clear()
    is_admin = await db.is_admin(message.from_user.id) if message.from_user else False

    match = re.search(r"\d+", text)
    if not match:
        await message.answer(
            "❌ Iltimos, faqat raqamli kod kiriting (masalan: <code>1</code>).",
            reply_markup=get_main_menu(is_admin=is_admin),
            parse_mode="HTML"
        )
        return

    code = int(match.group())
    anime = await db.get_anime_by_code(code)
    if not anime:
        await message.answer(
            f"❌ <b>#{code}</b> raqamli anime topilmadi.\nKodni qayta tekshirib ko'ring.",
            reply_markup=get_main_menu(is_admin=is_admin),
            parse_mode="HTML"
        )
        return

    await send_anime_card(message, anime, is_admin)


# ------------------ MATNDAN KODNI AVTOMATIK TUTIB OLISH ------------------
@user_router.message(F.text.regexp(r"^#?kod_?(\d+)$", mode="search"))
@user_router.message(F.text.regexp(r"^\d+$"))
async def handle_direct_code_text(message: Message) -> None:
    """Foydalanuvchi shunchaki '105' yoki '#kod_105' deb yozganda ishlaydi"""
    if not message.text:
        return
    match = re.search(r"\d+", message.text)
    if not match:
        return
    code = int(match.group())
    is_admin = await db.is_admin(message.from_user.id) if message.from_user else False

    anime = await db.get_anime_by_code(code)
    if not anime:
        await message.answer(
            f"❌ <b>#{code}</b> raqamli anime topilmadi.\nKodni qaytadan tekshirib ko'ring.",
            parse_mode="HTML"
        )
        return

    await send_anime_card(message, anime, is_admin)


# ------------------ RASM ORQALI ANIME QIDIRISH (REVERSE IMAGE SEARCH) ------------------
def format_anime_search_result(result: AnimeSearchResult, is_second: bool = False) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Rasm orqali qidiruv natijasini chiroyli va qulay formatlash.
    Uch tildagi nomlar: O'zbekcha, Inglizcha, Yaponcha (Kanji + Romaji).
    """
    lines = []
    if is_second:
        lines.append("🎉 <b>2-rasm orqali anime muvaffaqiyatli aniqlandi!</b>\n")
    elif result.status == "high_confidence":
        lines.append("🎯 <b>Anime muvaffaqiyatli topildi!</b>\n")
    else:
        lines.append("🔎 <b>Rasm biroz noaniq, lekin eng yaqin anime topildi:</b>\n")

    lines.append(f"🇺🇿 <b>O'zbekcha:</b> {result.title_uzbek}")
    lines.append(f"🇬🇧 <b>Inglizcha:</b> {result.title_english}")
    if result.title_japanese and result.title_romaji and result.title_japanese != result.title_romaji:
        lines.append(f"🇯🇵 <b>Yaponcha:</b> {result.title_japanese} ({result.title_romaji})")
    elif result.title_japanese or result.title_romaji:
        lines.append(f"🇯🇵 <b>Yaponcha:</b> {result.title_japanese or result.title_romaji}")

    if result.similarity_percent > 0:
        lines.append(f"\n📊 <b>Aniqlik darajasi:</b> {result.similarity_percent}%")
    if result.episode is not None:
        lines.append(f"🎞 <b>Qism:</b> {result.episode}")
    if result.timestamp:
        lines.append(f"⏱ <b>Kadr vaqti:</b> {result.timestamp}")
    if result.genres_uz:
        lines.append(f"🎭 <b>Janrlar:</b> {result.genres_uz}")
    if result.character_name:
        lines.append(f"👤 <b>Qahramon:</b> {result.character_name}")

    buttons = []
    if result.db_anime:
        lines.append(f"\n🎬 <i>Ushbu anime bizning bot bazamizda mavjud! Quyidagi tugma orqali tomosha qilishingiz mumkin.</i>")
        buttons.append([InlineKeyboardButton(text="🎬 Botda tomosha qilish", callback_data=f"anime_code_{result.db_anime.code}")])
    elif result.anilist_url:
        buttons.append([InlineKeyboardButton(text="🌐 AniList da ko'rish", url=result.anilist_url)])

    if not is_second and result.status == "medium_confidence":
        lines.append("\n⚠️ <i>Agar bu siz qidirgan anime bo'lmasa, iltimos, <b>2-rasmni</b> (aniqroq kadr yoki personaj yuzini) yuboring!</i>")

    kb = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    return "\n".join(lines), kb


async def _process_image_search(message: Message, state: FSMContext, is_second: bool = False) -> None:
    """Rasmni yuklab olib, trace.moe va Gemini Vision orqali qidirish jarayoni"""
    if not message.photo:
        return

    user = message.from_user
    is_admin = await db.is_admin(user.id) if user else False
    bot = message.bot
    if not bot:
        return

    status_msg = await message.answer(
        "🔍 <i>Rasm tahlil qilinmoqda, iltimos kuting...</i>",
        parse_mode="HTML"
    )

    try:
        # Eng katta sifatdagi rasmni yuklab olish
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        image_bytes = file_io.getvalue()

        # Qidiruv servisini ishga tushirish
        result = await anime_image_search_service.search_by_image(image_bytes, is_second_attempt=is_second)

        # 1-holat: Anime yuqori yoki o'rtacha ishonch bilan topildi
        if result.status in ("high_confidence", "medium_confidence"):
            caption, kb = format_anime_search_result(result, is_second=is_second)

            if result.status == "medium_confidence" and not is_second:
                await state.set_state(UserStates.waiting_for_second_photo)
                try:
                    await status_msg.edit_text(caption, reply_markup=kb, parse_mode="HTML")
                except Exception:
                    await message.answer(caption, reply_markup=kb, parse_mode="HTML")

                await message.answer(
                    "⚠️ <i>Agar bu siz qidirgan anime bo'lmasa, iltimos, <b>2-rasmni</b> (aniqroq kadr yoki personaj yuzini) yuboring!</i>",
                    reply_markup=get_cancel_reply(),
                    parse_mode="HTML"
                )
            else:
                await state.clear()
                try:
                    await status_msg.edit_text(caption, reply_markup=kb, parse_mode="HTML")
                except Exception:
                    await message.answer(caption, reply_markup=kb, parse_mode="HTML")

                await message.answer(
                    "Quyidagi menyudan foydalanishingiz mumkin:",
                    reply_markup=get_main_menu(is_admin=is_admin)
                )

        # 2-holat: 1-rasm juda noaniq bo'lib topilmadi -> muloyimlik bilan 2-rasm so'raladi
        elif not is_second:
            await state.set_state(UserStates.waiting_for_second_photo)
            try:
                await status_msg.delete()
            except Exception:
                pass

            await message.answer(
                "😔 <b>Kechirasiz, 1-rasm orqali animeni aniq topib bo'lmadi...</b>\n\n"
                "Rasm biroz xira, juda kichik yoki noaniq bo'lishi mumkin.\n\n"
                "🙏 <b>Iltimos, aniqroq bo'lishi uchun 2-rasmni yuboring!</b>\n"
                "<i>(Bosh qahramonning yuzi, yorug'roq kadr yoki yaqinroq lavha)</i>",
                reply_markup=get_cancel_reply(),
                parse_mode="HTML"
            )

        # 3-holat: 2-rasm ham topilmadi
        else:
            await state.clear()
            try:
                await status_msg.delete()
            except Exception:
                pass

            await message.answer(
                "😔 <b>Afsuski, 2-rasm orqali ham animeni aniqlash imkoni bo'lmadi.</b>\n\n"
                "💡 <i>Maslahat: Animening nomini matn orqali qidirib ko'ring yoki sifatliroq boshqa kadr yuboring.</i>",
                reply_markup=get_main_menu(is_admin=is_admin),
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Rasm qidiruvida kutilmagan xatolik: {e}", exc_info=True)
        await state.clear()
        try:
            await status_msg.delete()
        except Exception:
            pass
        await message.answer(
            "⚠️ <b>Rasm tahlilida kutilmagan xatolik yuz berdi.</b>\n"
            "Iltimos, birozdan so'ng qayta urinib ko'ring.",
            reply_markup=get_main_menu(is_admin=is_admin),
            parse_mode="HTML"
        )


@user_router.message(UserStates.waiting_for_anime_photo, F.photo)
async def handle_first_photo(message: Message, state: FSMContext) -> None:
    await _process_image_search(message, state, is_second=False)


@user_router.message(UserStates.waiting_for_second_photo, F.photo)
async def handle_second_photo(message: Message, state: FSMContext) -> None:
    await _process_image_search(message, state, is_second=True)


@user_router.message(UserStates.waiting_for_anime_photo, F.text)
async def handle_non_photo_first(message: Message) -> None:
    if message.text == "❌ Bekor qilish":
        return
    await message.answer(
        "📷 Iltimos, animedan olingan <b>rasm (skrinshot)</b> yuboring yoki bekor qilish uchun «❌ Bekor qilish» tugmasini bosing:",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@user_router.message(UserStates.waiting_for_second_photo, F.text)
async def handle_non_photo_second(message: Message) -> None:
    if message.text == "❌ Bekor qilish":
        return
    await message.answer(
        "📷 Iltimos, <b>2-rasmni</b> yuboring yoki to'xtatish uchun «❌ Bekor qilish» tugmasini bosing:",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@user_router.message(F.photo)
async def handle_direct_photo(message: Message, state: FSMContext) -> None:
    """Foydalanuvchi menyusiz to'g'ridan-to'g'ri rasm yuborganda ham avtomatik tahlil qilish"""
    current_state = await state.get_state()
    if current_state:
        return
    await _process_image_search(message, state, is_second=False)


# ------------------ INLINE CALLBACKS (ANIME VA QISMLAR) ------------------
@user_router.callback_query(F.data.startswith("anime_code_"))
async def handle_anime_code_callback(callback: CallbackQuery) -> None:
    if not callback.data:
        return
    code = int(callback.data.replace("anime_code_", ""))
    is_admin = await db.is_admin(callback.from_user.id) if callback.from_user else False

    anime = await db.get_anime_by_code(code)
    if not anime:
        await callback.answer("Anime topilmadi!", show_alert=True)
        return

    await callback.answer()
    if callback.message:
        await send_anime_card(callback.message, anime, is_admin)


@user_router.callback_query(F.data.startswith("page_"))
async def handle_episodes_page(callback: CallbackQuery) -> None:
    """Qismlar sahifasini o'zgartirish (pagination)"""
    if not callback.data:
        return
    parts = callback.data.split("_")
    anime_id = int(parts[1])
    page = int(parts[2])
    is_admin = await db.is_admin(callback.from_user.id) if callback.from_user else False

    anime = await db.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Anime topilmadi!", show_alert=True)
        return

    kb = get_anime_episodes_keyboard(anime, page=page, is_admin=is_admin)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
        await callback.answer()
    except Exception:
        await callback.answer()


@user_router.callback_query(F.data.startswith("ep_"))
async def handle_episode_download(callback: CallbackQuery) -> None:
    """Tanlangan qism videosini foydalanuvchiga yuborish"""
    if not callback.data or not callback.message:
        return
    parts = callback.data.split("_")
    anime_id = int(parts[1])
    episode_number = int(parts[2])

    anime = await db.get_anime_by_id(anime_id)
    episode = await db.get_episode(anime_id, episode_number)

    if not episode or not anime:
        await callback.answer("⚠️ Ushbu qism videosi hali yuklanmagan!", show_alert=True)
        return

    await callback.answer("⏳ Video yuborilmoqda...")

    caption_text = format_episode_caption(
        anime_title=anime.title_uz,
        ep_number=episode.episode_number,
        quality=episode.quality
    )

    try:
        await callback.message.answer_video(
            video=episode.video_file_id,
            caption=caption_text,
            parse_mode="HTML"
        )
        await db.increment_episode_downloads(episode.id)
    except Exception as e:
        await callback.message.answer(
            "❌ Videoni yuborishda xatolik yuz berdi. Iltimos, adminga murojaat qiling."
        )


@user_router.callback_query(F.data.startswith("dl_all_"))
async def handle_download_all_episodes(callback: CallbackQuery) -> None:
    """1-klik orqali barcha qismlarni ketma-ket yuborish"""
    if not callback.data or not callback.message:
        return
    anime_id = int(callback.data.replace("dl_all_", ""))
    anime = await db.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Anime topilmadi!", show_alert=True)
        return

    episodes = sorted(anime.episodes, key=lambda e: e.episode_number)
    total_eps = len(episodes)
    if total_eps == 0:
        await callback.answer("⚠️ Hozircha qismlar yuklanmagan!", show_alert=True)
        return

    await callback.answer(f"⏳ Jami {total_eps} ta qism yuborilmoqda...")

    status_msg = await callback.message.answer(
        f"📥 <b>{anime.title_uz}</b> — Barcha ({total_eps} ta) qismlar yuborilmoqda...\n"
        f"<i>Iltimos, ozroq kuting...</i> 🍿",
        parse_mode="HTML"
    )

    sent_count = 0
    for ep in episodes:
        caption = format_episode_caption(anime.title_uz, ep.episode_number, ep.quality)
        try:
            await callback.message.answer_video(
                video=ep.video_file_id,
                caption=caption,
                parse_mode="HTML"
            )
            await db.increment_episode_downloads(ep.id)
            sent_count += 1
            await asyncio.sleep(0.4)  # Telegram flood limitdan saqlanish
        except Exception:
            pass

    try:
        await status_msg.edit_text(
            f"✅ <b>{anime.title_uz}</b> animening barcha ({sent_count}/{total_eps}) qismlari yuborildi!\n\n"
            f"📢 Kanalimiz: {config.CHANNEL_USERNAME}\n"
            f"<i>Maroqli tomosha tilaymiz!</i> 🍿",
            parse_mode="HTML"
        )
    except Exception:
        pass


@user_router.callback_query(F.data == "no_episodes")
async def handle_no_episodes(callback: CallbackQuery) -> None:
    await callback.answer("⚠️ Bu animening qismlari tez orada yuklanadi!", show_alert=True)


# ------------------ YORDAMCHI FUNKSIYA: ANIME KARTASINI CHIQARISH ------------------
async def send_anime_card(message: Message, anime: Anime, is_admin: bool = False) -> None:
    """Anime kartochkasini rasm bilan birga yuborish"""
    await db.increment_anime_views(anime.id)
    text = format_anime_card(anime)
    kb = get_anime_episodes_keyboard(anime, page=0, is_admin=is_admin)

    poster = anime.poster_file_id
    if poster:
        try:
            if poster.startswith("http://") or poster.startswith("https://"):
                await message.answer_photo(
                    photo=URLInputFile(poster),
                    caption=text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
                return
            else:
                await message.answer_photo(
                    photo=poster,
                    caption=text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
                return
        except Exception:
            pass

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ------------------ HAR QANDAY BOSHQARILMAGAN MATN UCHUN JAVOB ------------------
@user_router.message()
async def handle_unknown_message(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state:
        return
    user = message.from_user
    is_admin = await db.is_admin(user.id) if user else False

    await message.answer(
        "Anime kodini kiriting (masalan: <code>1</code>) yoki quyidagi menyudan foydalaning:",
        reply_markup=get_main_menu(is_admin=is_admin),
        parse_mode="HTML"
    )
