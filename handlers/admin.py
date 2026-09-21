import re
import asyncio
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, URLInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import config
from database.db import db
from database.models import Anime
from services.post_generator import format_channel_post, format_channel_catalog, sync_channel_catalog
from keyboards.reply import get_admin_menu, get_main_menu, get_cancel_reply, get_batch_upload_menu
from keyboards.inline import get_admin_post_confirm_keyboard

logger = logging.getLogger(__name__)

admin_router = Router(name="admin_router")


# ------------------ FSM STATES ------------------
class BatchUploadStates(StatesGroup):
    waiting_for_anime_code = State()
    uploading_batch_episodes = State()
class AddAnimeStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_title_uz = State()
    waiting_for_code = State()
    waiting_for_custom_poster = State()
    confirm_save = State()


class AddEpisodeStates(StatesGroup):
    waiting_for_anime_code = State()
    waiting_for_ep_number = State()
    waiting_for_quality = State()
    waiting_for_video = State()


class PostToChannelStates(StatesGroup):
    waiting_for_code = State()


class BroadcastStates(StatesGroup):
    waiting_for_content = State()


class DeleteAnimeStates(StatesGroup):
    waiting_for_code = State()


# ------------------ ADMIN MENYUSI ------------------
@admin_router.message(Command("admin"))
@admin_router.message(F.text == "⚙️ Admin Panel")
async def handle_admin_panel(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user or not await db.is_admin(user.id):
        await message.answer("⛔️ Kechirasiz, sizda admin huquqlari mavjud emas.")
        return

    await state.clear()
    await message.answer(
        "🛠 <b>Admin Boshqaruv Paneliga xush kelibsiz!</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )


@admin_router.message(F.text == "🔙 Bosh menyuga qaytish")
async def handle_back_to_main(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    is_admin = await db.is_admin(user.id) if user else False
    await message.answer(
        "Bosh menyuga qaytdingiz.",
        reply_markup=get_main_menu(is_admin=is_admin)
    )


@admin_router.message(F.text == "❌ Bekor qilish")
async def handle_admin_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Amal bekor qilindi.", reply_markup=get_admin_menu())


# ------------------ STATISTIKA ------------------
@admin_router.message(F.text == "📊 Statistika")
async def handle_stats(message: Message) -> None:
    user = message.from_user
    if not user or not await db.is_admin(user.id):
        return

    stats = await db.get_statistics()
    text = (
        "📊 <b>LOYIHA STATISTIKASI:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Foydalanuvchilar:</b> {stats['users_count']} ta\n"
        f"🎬 <b>Animelar:</b> {stats['animes_count']} ta\n"
        f"🎞 <b>Yuklangan qismlar:</b> {stats['episodes_count']} ta\n"
        f"👁 <b>Umumiy ko'rishlar:</b> {stats['total_views']}\n"
        f"📥 <b>Yuklab olingan videolar:</b> {stats['total_downloads']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📢 Kanal: {config.CHANNEL_USERNAME}\n"
        f"🤖 Bot: @{config.BOT_USERNAME}"
    )
    await message.answer(text, parse_mode="HTML")


# ------------------ 1. YANGI ANIME QO'SHISH (WIZARD) ------------------
@admin_router.message(F.text == "➕ Yangi anime qo'shish")
async def start_add_anime(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user or not await db.is_admin(user.id):
        return

    await state.set_state(AddAnimeStates.waiting_for_title)
    await message.answer(
        "🎬 <b>Yangi anime qo'shish:</b>\n\n"
        "Animening nomini (inglizcha yoki yaponcha) yozing. Bot avtomatik AniList orqali ma'lumotlarni qidiradi.\n"
        "<i>Masalan: Solo Leveling, Naruto, Jujutsu Kaisen</i>",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@admin_router.message(AddAnimeStates.waiting_for_title)
async def process_anime_title(message: Message, state: FSMContext) -> None:
    title = message.text.strip() if message.text else ""
    if not title:
        return

    await message.answer("⏳ AniList bazasidan qidirilmoqda...")
    anilist_data = await anilist_service.search_anime(title)

    next_code = await db.get_next_anime_code()

    if anilist_data:
        romaji_title = anilist_data.get("title_romaji") or title
        await state.update_data(
            anilist_data=anilist_data,
            title_romaji=romaji_title,
            year=anilist_data.get("year"),
            genres=anilist_data.get("genres"),
            description=anilist_data.get("description"),
            poster_url=anilist_data.get("cover_image"),
            total_episodes=anilist_data.get("episodes", 12),
            status=anilist_data.get("status", "Tugallangan"),
            suggested_code=next_code
        )

        preview_msg = (
            f"✅ <b>AniList'dan ma'lumot topildi!</b>\n\n"
            f"🎬 <b>Nomi:</b> {romaji_title}\n"
            f"📅 <b>Yili:</b> {anilist_data.get('year')}\n"
            f"🎭 <b>Janrlar:</b> {anilist_data.get('genres')}\n"
            f"🎞 <b>Qismlar:</b> {anilist_data.get('episodes')} ta\n"
            f"🏢 <b>Studiya:</b> {anilist_data.get('studio')}\n\n"
            f"Endi ushbu animening <b>O'zbekcha nomini</b> kiriting:\n"
            f"<i>(Agar shunday qoldirmoqchi bo'lsangiz «.» nuqta yuboring)</i>"
        )
        await state.set_state(AddAnimeStates.waiting_for_title_uz)
        await message.answer(preview_msg, parse_mode="HTML")
    else:
        # Qo'lda kiritish
        await state.update_data(
            title_romaji=title,
            year=2024,
            genres="Sarguzasht, Jangari",
            description="Qiziqarli anime sarguzashti.",
            poster_url=None,
            total_episodes=12,
            status="Tugallangan",
            suggested_code=next_code
        )
        await state.set_state(AddAnimeStates.waiting_for_title_uz)
        await message.answer(
            f"ℹ️ AniList'da topilmadi. Animening o'zbekcha nomini kiriting:\n"
            f"(Kiritilgan nom: {title})",
            parse_mode="HTML"
        )


@admin_router.message(AddAnimeStates.waiting_for_title_uz)
async def process_anime_title_uz(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    text = message.text.strip()
    data = await state.get_data()

    title_uz = data["title_romaji"] if text == "." else text
    await state.update_data(title_uz=title_uz)

    suggested_code = data.get("suggested_code", 1)
    await state.set_state(AddAnimeStates.waiting_for_code)
    await message.answer(
        f"🔢 Anime uchun unikal raqamli kodni kiriting:\n\n"
        f"<i>Tavsiya etilayotgan kod: <code>{suggested_code}</code></i>\n"
        f"(Shu kodni qoldirish uchun «.» nuqta yuboring yoki o'zingiz istagan sonni kiriting)",
        parse_mode="HTML"
    )


@admin_router.message(AddAnimeStates.waiting_for_code)
async def process_anime_code(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    text = message.text.strip()
    data = await state.get_data()

    if text == ".":
        code = data.get("suggested_code", 1)
    elif text.isdigit():
        code = int(text)
    else:
        await message.answer("❌ Iltimos, faqat raqam kiriting!")
        return

    # Kod bandligini tekshirish
    existing = await db.get_anime_by_code(code)
    if existing:
        await message.answer(f"❌ <b>#{code}</b> kodi allaqachon «{existing.title_uz}» animesiga berilgan! Boshqa kod kiriting:")
        return

    await state.update_data(code=code)

    # Agar AniList'dan poster bo'lmasa, poster so'raymiz
    if not data.get("poster_url"):
        await state.set_state(AddAnimeStates.waiting_for_custom_poster)
        await message.answer(
            "🖼 Endi anime uchun poster (rasm) yuboring:\n"
            "<i>(Rasm yuborishni o'tkazib yuborish uchun «.» nuqta yozing)</i>",
            parse_mode="HTML"
        )
        return

    await finalize_add_anime(message, state)


@admin_router.message(AddAnimeStates.waiting_for_custom_poster)
async def process_custom_poster(message: Message, state: FSMContext) -> None:
    if message.photo:
        file_id = message.photo[-1].file_id
        await state.update_data(poster_url=file_id)
    elif message.text == ".":
        await state.update_data(poster_url=None)
    else:
        await message.answer("Iltimos, rasm yuboring yoki «.» yozing.")
        return

    await finalize_add_anime(message, state)


async def finalize_add_anime(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    anime = await db.add_anime(
        code=data["code"],
        title_uz=data["title_uz"],
        title_romaji=data.get("title_romaji"),
        year=data.get("year"),
        genres=data.get("genres"),
        description=data.get("description"),
        poster_file_id=data.get("poster_url"),
        total_episodes=data.get("total_episodes", 12),
        status=data.get("status", "Tugallangan")
    )

    confirm_text = (
        f"🎉 <b>Anime muvaffaqiyatli saqlandi!</b>\n\n"
        f"🎬 <b>Nomi:</b> {anime.title_uz}\n"
        f"🔑 <b>Kodi:</b> <code>{anime.code}</code>\n"
        f"📅 <b>Yili:</b> {anime.year}\n"
        f"🎭 <b>Janr:</b> {anime.genres}\n\n"
        f"📌 <i>Kanal katalogi avtomatik jimgina yangilandi!</i>\n"
        f"Endi ushbu anime uchun qismlarni yuklashingiz mumkin."
    )
    # Kanal katalogini avtomat yangilash
    try:
        await sync_channel_catalog(message.bot)
    except Exception:
        pass

    await message.answer(confirm_text, reply_markup=get_admin_menu(), parse_mode="HTML")


# ------------------ HELPER: EPISODE NUMBER EXTRACTOR ------------------
def extract_episode_number(filename: Optional[str], caption: Optional[str], fallback: int) -> int:
    """Fayl nomi yoki izohdan qism raqamini aqlli aniqlash"""
    text = f"{filename or ''} {caption or ''}"
    # 1. "S01E13", "S1E13"
    m_season = re.search(r's\d+e0*(\d+)', text, re.I)
    if m_season:
        return int(m_season.group(1))

    # 2. "E12", "E012", "Ep 12", "Episode 12", "12-qism", "qism 12", "qism_12"
    m_ep = re.search(r'(?:episodes?|ep|qism|e)\s*0*(\d+)', text, re.I)
    if m_ep:
        return int(m_ep.group(1))

    # 3. Fayl kengaytmasi oldidan yoki qavslar ichidagi raqam (masalan: "Naruto 012.mp4", "[AH] Naruto - 12")
    m_file = re.search(r'[\s_\-\[]0*(\d{1,4})[\s_\-\]\.]', text)
    if m_file:
        return int(m_file.group(1))

    # 4. Istalgan alohida turgan raqam
    m_num = re.search(r'\b0*(\d{1,4})\b', text)
    if m_num:
        return int(m_num.group(1))

    return fallback


# ------------------ 2. OMMAVIY QISM YUKLASH (BATCH MODE - 720 QISMLI REJIM) ------------------
@admin_router.message(F.text == "⚡️ Ommaviy qism yuklash")
async def start_batch_upload(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user or not await db.is_admin(user.id):
        return

    await state.set_state(BatchUploadStates.waiting_for_anime_code)
    await message.answer(
        "⚡️ <b>Ommaviy Qism Yuklash Rejimi (Batch Mode):</b>\n\n"
        "Qaysi animega qismlarni ommaviy yuklamoqchisiz? Anime kodini kiriting:\n"
        "<i>(Masalan: Naruto kodi yoki 1, 2...)</i>",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("admin_batch_"))
async def handle_callback_admin_batch(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        return
    code = int(callback.data.replace("admin_batch_", ""))
    anime = await db.get_anime_by_code(code)
    if not anime:
        await callback.answer("Anime topilmadi!", show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await enter_batch_upload_mode(callback.message, anime, state)


@admin_router.message(BatchUploadStates.waiting_for_anime_code)
async def process_batch_code(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Iltimos, raqamli anime kodini kiriting!")
        return

    code = int(message.text.strip())
    anime = await db.get_anime_by_code(code)
    if not anime:
        await message.answer(f"❌ #{code} kodli anime topilmadi!")
        return

    await enter_batch_upload_mode(message, anime, state)


async def enter_batch_upload_mode(message: Message, anime: Anime, state: FSMContext) -> None:
    current_eps = len(anime.episodes)
    await state.update_data(
        anime_id=anime.id,
        anime_code=anime.code,
        anime_title=anime.title_uz,
        count_uploaded=0
    )
    await state.set_state(BatchUploadStates.uploading_batch_episodes)
    await message.answer(
        f"⚡️ <b>{anime.title_uz}</b> [#{anime.code}] uchun <b>Ommaviy Yuklash</b> faollashdi!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Hozir bazada: <b>{current_eps} ta qism</b> mavjud.\n\n"
        f"🚀 <b>Ko'rsatma:</b>\n"
        f"Videolarni to'xtovsiz bittadan yoki guruhlab (10-50 tadan) botga yuboravering (yoki boshqa kanaldan forward qiling).\n"
        f"Bot avtomatik qism raqamini aniqlaydi va bazaga saqlaydi!\n\n"
        f"Tugatganingizda pastdagi «🏁 Ommaviy yuklashni tugatish» tugmasini bosing.",
        reply_markup=get_batch_upload_menu(),
        parse_mode="HTML"
    )


@admin_router.message(BatchUploadStates.uploading_batch_episodes, F.video)
async def process_batch_video(message: Message, state: FSMContext) -> None:
    if not message.video:
        return
    data = await state.get_data()
    anime_id = data["anime_id"]
    anime_title = data["anime_title"]

    filename = message.video.file_name or ""
    caption = message.caption or ""

    anime = await db.get_anime_by_id(anime_id)
    next_expected = len(anime.episodes) + 1 if anime else 1

    ep_number = extract_episode_number(filename, caption, fallback=next_expected)

    quality = "720p"
    if "1080" in f"{filename} {caption}":
        quality = "1080p"
    elif "480" in f"{filename} {caption}":
        quality = "480p"

    file_id = message.video.file_id
    await db.add_or_update_episode(
        anime_id=anime_id,
        episode_number=ep_number,
        video_file_id=file_id,
        quality=quality,
        caption=None
    )

    uploaded_so_far = data.get("count_uploaded", 0) + 1
    await state.update_data(count_uploaded=uploaded_so_far)

    await message.reply(
        f"⚡️ <b>{ep_number}-qism</b> saqlandi! ({quality})\n"
        f"<i>Ushbu seansda yuklandi: {uploaded_so_far} ta</i>",
        parse_mode="HTML"
    )


@admin_router.message(F.text == "🏁 Ommaviy yuklashni tugatish")
async def finish_batch_upload(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    title = data.get("anime_title", "Anime")
    uploaded = data.get("count_uploaded", 0)
    await state.clear()

    if uploaded > 0:
        # Faqat yangi qismlar haqiqatdan yuklangandagina katalog yangilanadi
        try:
            await sync_channel_catalog(message.bot)
        except Exception as e:
            logger.warning(f"Katalog sinxronlashda xatolik: {e}")

        await message.answer(
            f"🎉 <b>Ommaviy yuklash muvaffaqiyatli yakunlandi!</b>\n\n"
            f"🎬 Anime: <b>{title}</b>\n"
            f"🎞 Yuklangan yangi qismlar: <b>{uploaded} ta</b>\n\n"
            f"📌 <i>Kanal katalogidagi qismlar soni avtomatik yangilandi!</i>",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"⚡️ <b>Ommaviy yuklash yakunlandi.</b>\n"
            f"<i>Hech qanday yangi qism yuklanmadi.</i>",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )


# ------------------ 3. BITTA QISM YUKLASH (YAKKA TARTIBDA) ------------------
@admin_router.message(F.text == "🎬 Bitta qism yuklash")
@admin_router.message(F.text == "🎬 Qism yuklash")
async def start_add_episode(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user or not await db.is_admin(user.id):
        return

    await state.set_state(AddEpisodeStates.waiting_for_anime_code)
    await message.answer(
        "🎬 Qaysi animega qism yuklamoqchisiz? Anime kodini kiriting:\n"
        "<i>Masalan: 1, 5, 102...</i>",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("admin_add_ep_"))
async def handle_callback_add_ep(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        return
    code = int(callback.data.replace("admin_add_ep_", ""))
    anime = await db.get_anime_by_code(code)
    if not anime:
        await callback.answer("Anime topilmadi!", show_alert=True)
        return

    await callback.answer()
    await state.set_state(AddEpisodeStates.waiting_for_ep_number)
    await state.update_data(anime_id=anime.id, anime_code=anime.code, anime_title=anime.title_uz)

    next_ep = len(anime.episodes) + 1
    if callback.message:
        await callback.message.answer(
            f"🎬 <b>{anime.title_uz}</b> [#{anime.code}]\n\n"
            f"Nechanchi qismni yuklamoqchisiz?\n"
            f"<i>Keyingi kutilayotgan qism: <b>{next_ep}</b></i>\n"
            f"(Shu qism bo'lsa «.» nuqta yuboring yoki boshqa raqam yozing)",
            reply_markup=get_cancel_reply(),
            parse_mode="HTML"
        )


@admin_router.message(AddEpisodeStates.waiting_for_anime_code)
async def process_ep_anime_code(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Iltimos, raqamli anime kodini kiriting!")
        return

    code = int(message.text.strip())
    anime = await db.get_anime_by_code(code)
    if not anime:
        await message.answer(f"❌ <b>#{code}</b> kodli anime topilmadi! Qaytadan kiriting:")
        return

    next_ep = len(anime.episodes) + 1
    await state.update_data(anime_id=anime.id, anime_code=anime.code, anime_title=anime.title_uz)
    await state.set_state(AddEpisodeStates.waiting_for_ep_number)
    await message.answer(
        f"🎬 <b>{anime.title_uz}</b> tanlandi.\n\n"
        f"Nechanchi qismni yuklamoqchisiz?\n"
        f"<i>Kutilayotgan qism: <b>{next_ep}</b></i> (Shunday qoldirish uchun «.» yuboring)",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@admin_router.message(AddEpisodeStates.waiting_for_ep_number)
async def process_ep_number(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    text = message.text.strip()
    data = await state.get_data()

    if text == ".":
        anime = await db.get_anime_by_id(data["anime_id"])
        ep_num = len(anime.episodes) + 1 if anime else 1
    elif text.isdigit():
        ep_num = int(text)
    else:
        await message.answer("❌ Faqat raqam kiriting!", reply_markup=get_cancel_reply())
        return

    await state.update_data(episode_number=ep_num)
    await state.set_state(AddEpisodeStates.waiting_for_video)
    await message.answer(
        f"🎞 <b>{data['anime_title']}</b> — <b>{ep_num}-qism</b> uchun videofaylni yuboring:\n\n"
        f"<i>(Telegram orqali videoni shunchaki xabar sifatida yuboring)</i>",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@admin_router.message(AddEpisodeStates.waiting_for_video, F.video)
async def process_ep_video(message: Message, state: FSMContext) -> None:
    if not message.video:
        return

    data = await state.get_data()
    await state.clear()

    file_id = message.video.file_id
    anime_id = data["anime_id"]
    ep_num = data["episode_number"]

    episode = await db.add_or_update_episode(
        anime_id=anime_id,
        episode_number=ep_num,
        video_file_id=file_id,
        quality="720p",
        caption=message.caption
    )

    try:
        await sync_channel_catalog(message.bot)
    except Exception as e:
        logger.warning(f"Katalog yangilashda xatolik: {e}")

    await message.answer(
        f"✅ <b>{data['anime_title']}</b> animening <b>{ep_num}-qismi</b> muvaffaqiyatli saqlandi!\n"
        f"Foydalanuvchilar endi ushbu qismni bot orqali ko'ra olishadi.",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )


# ------------------ 3. KANALGA POST CHIQARISH (AUTO-POSTER) ------------------
@admin_router.message(F.text == "📢 Kanalga post chiqarish")
async def start_channel_post(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user or not await db.is_admin(user.id):
        return

    await state.set_state(PostToChannelStates.waiting_for_code)
    await message.answer(
        f"📢 Qaysi animeni <b>{config.CHANNEL_USERNAME}</b> kanaliga chiqarmoqchisiz?\n"
        f"Anime kodini kiriting:",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("admin_post_"))
async def handle_callback_admin_post(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        return
    code = int(callback.data.replace("admin_post_", ""))
    await show_post_preview(callback.message, code)
    await callback.answer()


@admin_router.message(PostToChannelStates.waiting_for_code)
async def process_post_code(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Iltimos, raqamli anime kodini kiriting!")
        return

    code = int(message.text.strip())
    await state.clear()
    await show_post_preview(message, code)


async def show_post_preview(message: Message, code: int) -> None:
    anime = await db.get_anime_by_code(code)
    if not anime:
        await message.answer(f"❌ #{code} kodli anime topilmadi!")
        return

    post_text, channel_kb = format_channel_post(anime)
    confirm_kb = get_admin_post_confirm_keyboard(anime.code)

    preview_note = (
        f"👀 <b>POST PREVIEW (Ko'rinishi):</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
    )

    poster = anime.poster_file_id
    if poster:
        try:
            if poster.startswith("http://") or poster.startswith("https://"):
                await message.answer_photo(
                    photo=URLInputFile(poster),
                    caption=post_text,
                    reply_markup=channel_kb,
                    parse_mode="HTML"
                )
            else:
                await message.answer_photo(
                    photo=poster,
                    caption=post_text,
                    reply_markup=channel_kb,
                    parse_mode="HTML"
                )
        except Exception:
            await message.answer(post_text, reply_markup=channel_kb, parse_mode="HTML")
    else:
        await message.answer(post_text, reply_markup=channel_kb, parse_mode="HTML")

    await message.answer(
        f"Ushbu postni <b>{config.CHANNEL_USERNAME}</b> kanaliga chiqarishni tasdiqlaysizmi?",
        reply_markup=confirm_kb,
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("confirm_post_"))
async def handle_confirm_post(callback: CallbackQuery) -> None:
    code = int(callback.data.replace("confirm_post_", ""))
    anime = await db.get_anime_by_code(code)
    if not anime:
        await callback.answer("Anime topilmadi!", show_alert=True)
        return

    post_text, channel_kb = format_channel_post(anime)
    bot = callback.bot

    try:
        poster = anime.poster_file_id
        if poster:
            if poster.startswith("http://") or poster.startswith("https://"):
                await bot.send_photo(
                    chat_id=config.CHANNEL_USERNAME,
                    photo=URLInputFile(poster),
                    caption=post_text,
                    reply_markup=channel_kb,
                    parse_mode="HTML"
                )
            else:
                await bot.send_photo(
                    chat_id=config.CHANNEL_USERNAME,
                    photo=poster,
                    caption=post_text,
                    reply_markup=channel_kb,
                    parse_mode="HTML"
                )
        else:
            await bot.send_message(
                chat_id=config.CHANNEL_USERNAME,
                text=post_text,
                reply_markup=channel_kb,
                parse_mode="HTML"
            )

        await callback.answer("✅ Post muvaffaqiyatli kanalga chiqarildi!", show_alert=True)
        if callback.message:
            await callback.message.edit_text(
                f"✅ <b>#{anime.code} — {anime.title_uz}</b> posti {config.CHANNEL_USERNAME} kanaliga chiqarildi!",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Kanalga post chiqarishda xatolik: {e}")
        await callback.answer(f"❌ Xatolik: {e}", show_alert=True)


@admin_router.callback_query(F.data == "cancel_admin_action")
async def handle_cancel_admin_action(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Bekor qilindi.")
    if callback.message:
        await callback.message.delete()


# ------------------ 4. BROADCAST (XABAR YUBORISH) ------------------
@admin_router.message(F.text == "✉️ Xabar yuborish (Broadcast)")
async def start_broadcast(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user or not await db.is_admin(user.id):
        return

    await state.set_state(BroadcastStates.waiting_for_content)
    await message.answer(
        "✉️ <b>Barcha foydalanuvchilarga xabar yuborish:</b>\n\n"
        "Tarqatmoqchi bo'lgan xabaringizni (matn, rasm yoki video) yuboring:",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@admin_router.message(BroadcastStates.waiting_for_content)
async def process_broadcast(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_ids = await db.get_all_user_ids()
    total_users = len(user_ids)

    if total_users == 0:
        await message.answer("Bazada hech qanday foydalanuvchi yo'q.", reply_markup=get_admin_menu())
        return

    status_msg = await message.answer(f"⏳ Xabar tarqatilmoqda... (0/{total_users})")

    sent = 0
    blocked = 0
    bot = message.bot

    for i, u_id in enumerate(user_ids, 1):
        try:
            await message.copy_to(chat_id=u_id)
            sent += 1
        except Exception:
            blocked += 1

        # Har 20 ta xabarda statusni yangilash va flood limitdan saqlanish
        if i % 20 == 0:
            try:
                await status_msg.edit_text(f"⏳ Xabar tarqatilmoqda... ({i}/{total_users})")
            except Exception:
                pass
            await asyncio.sleep(0.5)

    await status_msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"📬 Yuborildi: <b>{sent} ta</b>\n"
        f"🚫 Yetib bormadi (bloklagan): <b>{blocked} ta</b>\n"
        f"👥 Jami: <b>{total_users} ta</b>",
        parse_mode="HTML"
    )


# ------------------ 5. ANIMENI O'CHIRISH ------------------
@admin_router.message(F.text == "🗑 Animeni o'chirish")
async def start_delete_anime(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user or not await db.is_admin(user.id):
        return

    await state.set_state(DeleteAnimeStates.waiting_for_code)
    await message.answer(
        "🗑 O'chirmoqchi bo'lgan animengiz kodini kiriting:\n"
        "<i>(Barcha qismlari ham bazadan o'chib ketadi)</i>",
        reply_markup=get_cancel_reply(),
        parse_mode="HTML"
    )


@admin_router.message(DeleteAnimeStates.waiting_for_code)
async def process_delete_anime(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Iltimos, raqamli kod kiriting!")
        return

    code = int(message.text.strip())
    await state.clear()

    deleted = await db.delete_anime(code)
    if deleted:
        try:
            await sync_channel_catalog(message.bot)
        except Exception:
            pass
        await message.answer(f"✅ <b>#{code}</b> kodli anime va uning barcha qismlari o'chirildi.\n📌 <i>Kanal katalogi ham avtomatik yangilandi.</i>", reply_markup=get_admin_menu(), parse_mode="HTML")
    else:
        await message.answer(f"❌ <b>#{code}</b> kodli anime topilmadi.", reply_markup=get_admin_menu(), parse_mode="HTML")


# ------------------ 6. KANAL UCHUN KATALOG (NAVIGATSIYA) POSTI ------------------
@admin_router.message(F.text == "📋 Kanal katalog posti")
async def handle_channel_catalog_post(message: Message) -> None:
    user = message.from_user
    if not user or not await db.is_admin(user.id):
        return

    success = await sync_channel_catalog(message.bot)
    if success:
        await message.answer(
            f"✅ <b>Kanal Mundarijasi (Katalog)</b> muvaffaqiyatli sinxronlandi va {config.CHANNEL_USERNAME} kanaliga qadaldi!\n\n"
            f"⚡️ <b>Zo'r yangilik:</b> Endi har safar yangi anime yoki yangi qismlar yuklaganingizda, kanalga yangi post chiqib obunachilarni bezovta qilmaydi! Aynan mana shu qadalgan Katalog posti <b>avtomatik va jimgina o'zi yangilanib</b> boraveradi.",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer("⚠️ Hozircha bazada birorta ham anime yo'q yoki kanalga post chiqarishda xatolik bo'ldi.", reply_markup=get_admin_menu())
