import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from pydantic_core import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.admin import (
    process_anime_title,
    process_anime_title_uz,
    process_anime_code,
    handle_admin_quick_save,
    handle_cancel_admin_action,
    finalize_add_anime,
)
from services.anilist import anilist_service
from database.db import db
from database.models import Anime
from sqlalchemy import delete


def create_validated_status_mock():
    """Real aiogram kabi edit_text ga ReplyKeyboardMarkup berilsa TypeError/ValidationError otadigan mock"""
    mock = AsyncMock()

    async def validated_edit_text(*args, **kwargs):
        reply_markup = kwargs.get("reply_markup")
        if reply_markup is not None and not isinstance(reply_markup, InlineKeyboardMarkup):
            raise TypeError(f"Telegram edit_text only accepts InlineKeyboardMarkup, got {type(reply_markup)}")
        return mock

    mock.edit_text.side_effect = validated_edit_text
    return mock


@pytest.mark.asyncio
async def test_search_sening_isming_success():
    """Admin 'sening isming' kiritganda AniList muvaffaqiyatli topishi va preview_msg ko'rsatilishi kerak"""
    msg = AsyncMock()
    status_msg = create_validated_status_mock()
    msg.text = "sening isming"
    msg.answer.return_value = status_msg
    state = AsyncMock()
    
    state_data = {}
    async def update_data(**kwargs):
        state_data.update(kwargs)
    state.update_data.side_effect = update_data
    state.get_data.return_value = state_data

    await process_anime_title(msg, state)

    assert status_msg.edit_text.called
    args, kwargs = status_msg.edit_text.call_args
    preview_text = args[0] if args else kwargs.get("text", "")

    assert "AniList'dan ma'lumot topildi" in preview_text
    assert "Kimi no Na wa" in preview_text or "Your Name" in preview_text
    assert "Sening Isming" in preview_text
    assert "❌ Qidirishda xatolik yuz berdi" not in preview_text
    assert state_data.get("title_romaji") is not None
    assert state_data.get("code") is not None


@pytest.mark.asyncio
async def test_search_seni_isming_success():
    """Admin 'seni isming' (harf tushib qolgan yoki xalqona) kiritganda ham xato bermasdan topishi kerak"""
    msg = AsyncMock()
    status_msg = create_validated_status_mock()
    msg.text = "seni isming"
    msg.answer.return_value = status_msg
    state = AsyncMock()

    state_data = {}
    async def update_data(**kwargs):
        state_data.update(kwargs)
    state.update_data.side_effect = update_data
    state.get_data.return_value = state_data

    await process_anime_title(msg, state)

    assert status_msg.edit_text.called
    args, kwargs = status_msg.edit_text.call_args
    preview_text = args[0] if args else kwargs.get("text", "")

    assert "AniList'dan ma'lumot topildi" in preview_text
    assert "Kimi no Na wa" in preview_text or "Your Name" in preview_text
    assert "❌ Qidirishda xatolik yuz berdi" not in preview_text


@pytest.mark.asyncio
async def test_search_sening_isming_punctuation():
    """Tinish belgilari bilan ('sening isming.') kiritilganda ham aniq topilishi kerak"""
    msg = AsyncMock()
    status_msg = create_validated_status_mock()
    msg.text = "sening isming."
    msg.answer.return_value = status_msg
    state = AsyncMock()

    state_data = {}
    async def update_data(**kwargs):
        state_data.update(kwargs)
    state.update_data.side_effect = update_data
    state.get_data.return_value = state_data

    await process_anime_title(msg, state)

    assert status_msg.edit_text.called
    args, kwargs = status_msg.edit_text.call_args
    preview_text = args[0] if args else kwargs.get("text", "")

    assert "AniList'dan ma'lumot topildi" in preview_text
    assert "Kimi no Na wa" in preview_text or "Your Name" in preview_text
    assert "Sening Isming" in preview_text


@pytest.mark.asyncio
async def test_search_not_found_clean_fallback():
    """Topilmagan anime kiritilganda status_msg to'g'ri edit_text qilinishi va InlineKeyboardMarkup ishlatilishi kerak"""
    msg = AsyncMock()
    status_msg = create_validated_status_mock()
    msg.text = "random_anime_nonexistent_xyz_998877"
    msg.answer.return_value = status_msg
    state = AsyncMock()

    state_data = {}
    async def update_data(**kwargs):
        state_data.update(kwargs)
    state.update_data.side_effect = update_data
    state.get_data.return_value = state_data

    await process_anime_title(msg, state)

    assert status_msg.edit_text.called
    args, kwargs = status_msg.edit_text.call_args
    text = args[0] if args else kwargs.get("text", "")
    reply_markup = kwargs.get("reply_markup")

    assert "AniList'da topilmadi" in text
    assert "❌ Qidirishda xatolik yuz berdi" not in text
    # ReplyKeyboardMarkup edit_text ga berilmagan bo'lishi shart
    assert not isinstance(reply_markup, ReplyKeyboardMarkup)
    assert isinstance(reply_markup, InlineKeyboardMarkup) or reply_markup is None


@pytest.mark.asyncio
async def test_title_uz_preserves_uzbek_name_on_dot():
    """Admin '.' yuborganda oldin topilgan O'zbekcha nom (title_uz) o'chib ketmasdan saqlanishi kerak"""
    msg = AsyncMock()
    msg.text = "."
    state = AsyncMock()
    state_data = {
        "title_uz": "Sening Isming",
        "title_romaji": "Kimi no Na wa.",
        "suggested_code": 105
    }
    async def update_data(**kwargs):
        state_data.update(kwargs)
    state.update_data.side_effect = update_data
    state.get_data.return_value = state_data

    await process_anime_title_uz(msg, state)

    assert state_data["title_uz"] == "Sening Isming"


@pytest.mark.asyncio
async def test_code_accepts_hash_format():
    """Admin '#123' kiritganda ham raqamli 123 qilib to'g'ri qabul qilinishi kerak"""
    msg = AsyncMock()
    msg.text = "#9999"
    state = AsyncMock()
    state_data = {
        "suggested_code": 9999,
        "poster_url": "https://example.com/poster.jpg"
    }
    async def update_data(**kwargs):
        state_data.update(kwargs)
    state.update_data.side_effect = update_data
    state.get_data.return_value = state_data

    with patch("handlers.admin.finalize_add_anime", new_callable=AsyncMock) as mock_finalize:
        await process_anime_code(msg, state)
        assert state_data.get("code") == 9999
        assert mock_finalize.called


@pytest.mark.asyncio
async def test_cancel_admin_action_callbacks():
    """cancel_admin_action hamda cancel_action har ikkisi ham bekor qilishni to'g'ri bajarishi kerak"""
    cb = AsyncMock()
    cb_msg = AsyncMock()
    cb.message = cb_msg
    state = AsyncMock()

    await handle_cancel_admin_action(cb, state)

    assert state.clear.called
    assert cb.answer.called
    assert cb_msg.delete.called


@pytest.mark.asyncio
async def test_admin_quick_save_flow():
    """1-klikda saqlash tugmasi to'g'ri ishlashi va bazada anime yaratilishi kerak"""
    test_code = 88887
    state = AsyncMock()
    state.get_data.return_value = {
        "code": test_code,
        "title_uz": "Sening Isming Test",
        "title_romaji": "Kimi no Na wa.",
        "year": 2016,
        "genres": "Drama, Romantika",
        "description": "Test tavsifi",
        "poster_url": "https://s4.anilist.co/file/cover.png",
        "total_episodes": 1,
        "status": "Tugallangan"
    }

    cb = AsyncMock()
    cb_msg = AsyncMock()
    cb.message = cb_msg

    await handle_admin_quick_save(cb, state)

    # Tasdiq xabari yuborilganini tekshirish
    assert cb_msg.answer.called
    args, kwargs = cb_msg.answer.call_args
    confirm_text = args[0] if args else kwargs.get("text", "")
    assert "Anime muvaffaqiyatli saqlandi" in confirm_text
    assert str(test_code) in confirm_text

    # Bazadan tekshirish
    anime = await db.get_anime_by_code(test_code)
    assert anime is not None
    assert anime.title_uz == "Sening Isming Test"

    # Tozalash
    async with db.session_factory() as session:
        await session.execute(delete(Anime).where(Anime.code == test_code))
        await session.commit()
