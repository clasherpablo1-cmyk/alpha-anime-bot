import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery
from database.models import Anime, Episode
from services.post_generator import format_channel_post, post_anime_to_channel
from keyboards.reply import get_main_menu


def test_format_channel_post_content_and_button():
    anime = Anime(
        id=99,
        code=77,
        title_uz="Sening Isming",
        title_romaji="Kimi no Na wa.",
        year=2016,
        genres="Drama, Romantika",
        status="Tugallangan",
        total_episodes=1,
        description="Mitsuha va Taki haqidagi ajoyib sevgi qissasi.",
        poster_file_id="https://example.com/poster.jpg"
    )
    text, kb = format_channel_post(anime)
    
    assert "YANGI ANIME BOTGA JOYLANDI!" in text
    assert "Sening Isming" in text
    assert "2016-yil" in text
    assert "Drama, Romantika" in text
    assert "Mitsuha va Taki" in text
    assert "#kod_77" in text
    
    # Check button
    buttons = kb.inline_keyboard[0]
    view_btn = buttons[0]
    assert "Ko'rish" in view_btn.text
    assert "start=77" in view_btn.url


@pytest.mark.asyncio
async def test_post_anime_to_channel_mock_bot():
    bot = AsyncMock()
    anime = Anime(
        id=99,
        code=77,
        title_uz="Sening Isming",
        title_romaji="Kimi no Na wa.",
        year=2016,
        genres="Drama, Romantika",
        status="Tugallangan",
        total_episodes=1,
        description="Tavsif",
        poster_file_id="https://example.com/poster.jpg"
    )
    
    success = await post_anime_to_channel(bot, anime)
    assert success is True
    bot.send_photo.assert_called_once()
    call_kwargs = bot.send_photo.call_args[1]
    assert "caption" in call_kwargs
    assert "YANGI ANIME BOTGA JOYLANDI!" in call_kwargs["caption"]
    assert "reply_markup" in call_kwargs


def test_main_menu_has_all_animes_button():
    menu = get_main_menu(is_admin=False)
    button_texts = [btn.text for row in menu.keyboard for btn in row]
    assert "🗂 Barcha animelar" in button_texts
    assert "🆕 Yangi animelar" in button_texts
    assert "🔍 Anime qidirish" in button_texts
    assert "🔢 Kod orqali qidirish" in button_texts


@pytest.mark.asyncio
async def test_send_all_episodes_direct():
    from handlers.user import send_all_episodes_direct
    from database.db import db

    message = AsyncMock(spec=Message)
    status_msg = AsyncMock()
    message.answer = AsyncMock(return_value=status_msg)
    message.answer_video = AsyncMock()

    anime = Anime(
        id=1,
        code=1,
        title_uz="Naruto",
        title_romaji="Naruto",
        episodes=[
            Episode(id=101, anime_id=1, episode_number=1, video_file_id="file_1", quality="720p"),
            Episode(id=102, anime_id=1, episode_number=2, video_file_id="file_2", quality="720p")
        ]
    )

    with patch.object(db, "increment_episode_downloads", new_callable=AsyncMock) as mock_inc:
        await send_all_episodes_direct(message, anime)
        assert message.answer_video.call_count == 2
        assert mock_inc.call_count == 2
        status_msg.edit_text.assert_called_once()
        assert "barcha (2/2) qismlari yetkazildi" in status_msg.edit_text.call_args[0][0]
