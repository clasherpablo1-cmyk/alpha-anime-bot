# -*- coding: utf-8 -*-
"""
tests/test_custom_emoji.py
Unit tests for Telegram Premium Custom Emoji stickers functionality,
centralized helper functions, fallback behavior, and post formatting.
"""

import pytest
from unittest.mock import patch
from config import CUSTOM_EMOJIS, DEFAULT_FALLBACKS, get_custom_emoji, get_emoji_id, is_valid_emoji_id
from services.post_generator import format_channel_post, format_anime_card, format_channel_catalog, format_episode_caption
from database.models import Anime


def test_custom_emoji_dictionary_keys():
    """Barcha zarur bo'lgan Premium stiker kalitlari CUSTOM_EMOJIS lug'atida mavjudligini tekshirish"""
    required_keys = [
        "sarlavha", "reyting", "qismlar", "ovoz", "sifat",
        "janr", "kod", "tavsif", "qidiruv",
        "btn_download", "btn_channel", "btn_search", "btn_code"
    ]
    for key in required_keys:
        assert key in CUSTOM_EMOJIS, f"'{key}' kaliti CUSTOM_EMOJIS lug'atida topilmadi!"


def test_custom_emoji_fallback_when_empty():
    """Emoji ID bo'sh bo'lganda standart fallback belgi qaytishi kerak"""
    with patch.dict(CUSTOM_EMOJIS, {"sarlavha": "", "reyting": "", "kod": ""}):
        assert get_custom_emoji("sarlavha") == "🍥"
        assert get_custom_emoji("reyting") == "⚛️"
        assert get_custom_emoji("kod") == "🔑"
        assert get_custom_emoji("non_existent_key", fallback="❓") == "❓"


def test_custom_emoji_fallback_when_placeholder():
    """Emoji ID placeholder (0, None, YOUR_EMOJI_ID) bo'lganda ham xavfsiz fallback qaytishi kerak"""
    with patch.dict(CUSTOM_EMOJIS, {
        "sarlavha": "YOUR_EMOJI_ID",
        "reyting": "0",
        "kod": "PLACEHOLDER_ID"
    }):
        assert get_custom_emoji("sarlavha") == "🍥"
        assert get_custom_emoji("reyting") == "⚛️"
        assert get_custom_emoji("kod") == "🔑"


def test_custom_emoji_formatted_tag_when_id_present():
    """Haqiqiy emoji_id kiritilganda to'g'ri <tg-emoji> tegi shakllanishi kerak"""
    test_id = "5368324170671202286"
    with patch.dict(CUSTOM_EMOJIS, {"sarlavha": test_id}):
        result = get_custom_emoji("sarlavha", "🍥")
        assert result == f'<tg-emoji emoji-id="{test_id}">🍥</tg-emoji>'


def test_get_emoji_id_helper():
    """Tugmalar uchun emoji_id olish helper funksiyasi to'g'ri ishlashi"""
    with patch.dict(CUSTOM_EMOJIS, {"btn_download": "987654321", "btn_channel": ""}):
        assert get_emoji_id("btn_download") == "987654321"
        assert get_emoji_id("btn_channel") is None
        assert get_emoji_id("non_existent") is None


def test_post_generator_with_custom_emojis():
    """Kanal posti va bot xabarlarida custom emojilar to'g'ri ulanishi"""
    custom_map = {
        "sarlavha": "1001",
        "reyting": "1002",
        "qismlar": "1003",
        "ovoz": "1004",
        "sifat": "1005",
        "janr": "1006",
        "kod": "1007",
        "tavsif": "1008",
        "btn_download": "2001",
        "btn_channel": "2002",
    }
    anime = Anime(
        id=1,
        code=99,
        title_uz="Attack on Titan",
        title_romaji="Shingeki no Kyojin",
        year=2013,
        genres="Action, Drama",
        status="Tugallangan",
        total_episodes=25,
        description="Devorlar ortidagi insoniyat kurashi.",
        poster_file_id="https://example.com/poster.jpg"
    )

    with patch.dict(CUSTOM_EMOJIS, custom_map):
        post_text, kb = format_channel_post(anime)
        card_text = format_anime_card(anime)

        # Kanal postidagi teglarni tekshirish
        assert '<tg-emoji emoji-id="1001">🍥</tg-emoji>' in post_text
        assert '<tg-emoji emoji-id="1002">⚛️</tg-emoji>' in post_text
        assert '<tg-emoji emoji-id="1003">🗃</tg-emoji>' in post_text
        assert '<tg-emoji emoji-id="1004">🎙</tg-emoji>' in post_text
        assert '<tg-emoji emoji-id="1005">🎼</tg-emoji>' in post_text
        assert '<tg-emoji emoji-id="1006">🎭</tg-emoji>' in post_text
        assert '<tg-emoji emoji-id="1007">🔑</tg-emoji>' in post_text
        assert '<tg-emoji emoji-id="1008">📖</tg-emoji>' in post_text

        # Tugmadagi custom emoji id tekshirish
        buttons = kb.inline_keyboard
        assert buttons[0][0].icon_custom_emoji_id == "2001"
        assert buttons[1][0].icon_custom_emoji_id == "2002"

        # Anime kartochkasidagi teglarni tekshirish
        assert '<tg-emoji emoji-id="1001">🍥</tg-emoji>' in card_text
        assert '<tg-emoji emoji-id="1002">⚛️</tg-emoji>' in card_text
        assert '<tg-emoji emoji-id="1003">🗃</tg-emoji>' in card_text


def test_custom_emoji_dict_case_insensitivity():
    """CUSTOM_EMOJIS lug'ati katta-kichik harflarga qaramasdan ishlashi kerak"""
    with patch.dict(CUSTOM_EMOJIS, {"sarlavha": "5368324170671202286"}):
        assert CUSTOM_EMOJIS["sarlavha"] == "5368324170671202286"
        assert CUSTOM_EMOJIS["Sarlavha"] == "5368324170671202286"
        assert CUSTOM_EMOJIS["SARLAVHA"] == "5368324170671202286"
        assert CUSTOM_EMOJIS.get("Sarlavha") == "5368324170671202286"
        assert "Sarlavha" in CUSTOM_EMOJIS

        # get_custom_emoji va get_emoji_id bilan tekshirish
        assert '<tg-emoji emoji-id="5368324170671202286">🍥</tg-emoji>' in get_custom_emoji("Sarlavha")
        assert '<tg-emoji emoji-id="5368324170671202286">🍥</tg-emoji>' in get_custom_emoji("SARLAVHA")
        assert get_emoji_id("Sarlavha") == "5368324170671202286"


def test_is_valid_emoji_id_validation():
    """is_valid_emoji_id funksiyasi barcha holatlarni aniq filtrlashi kerak"""
    assert is_valid_emoji_id("5368324170671202286") is True
    assert is_valid_emoji_id(5368324170671202286) is True
    assert is_valid_emoji_id("123456") is True

    # Noto'g'ri / placeholder holatlar:
    assert is_valid_emoji_id(None) is False
    assert is_valid_emoji_id("") is False
    assert is_valid_emoji_id("   ") is False
    assert is_valid_emoji_id("0") is False
    assert is_valid_emoji_id("None") is False
    assert is_valid_emoji_id("null") is False
    assert is_valid_emoji_id("YOUR_EMOJI_ID") is False
    assert is_valid_emoji_id("PLACEHOLDER") is False
    assert is_valid_emoji_id("abc") is False
    assert is_valid_emoji_id("-100") is False


def test_custom_emoji_empty_fallback_safety():
    """Key topilmaganda yoki fallback bo'sh bo'lganda Telegram API xato bermasligi uchun xavfsiz belgi qo'yilishi"""
    with patch.dict(CUSTOM_EMOJIS, {"custom_unknown": "99999"}):
        res = get_custom_emoji("custom_unknown", fallback="")
        assert res == '<tg-emoji emoji-id="99999">✨</tg-emoji>'
        assert "</tg-emoji>" in res
        assert "<tg-emoji emoji-id=\"99999\"></tg-emoji>" != res


def test_episode_caption_and_catalog_with_custom_emojis():
    """Qism posti va kanal katalog posti ham custom emojilarni to'g'ri qo'llashi kerak"""
    custom_map = {
        "video": "3001",
        "sifat": "3002",
        "til_uz": "3003",
        "kanal": "3004",
        "bot": "3005",
        "popcorn": "3006",
        "katalog": "4001",
        "nuqta": "4002"
    }
    with patch.dict(CUSTOM_EMOJIS, custom_map):
        caption = format_episode_caption("Solo Leveling", 1, "1080p")
        assert '<tg-emoji emoji-id="3001">🎬</tg-emoji>' in caption
        assert '<tg-emoji emoji-id="3002">💾</tg-emoji>' in caption
        assert '<tg-emoji emoji-id="3003">🇺🇿</tg-emoji>' in caption
        assert '<tg-emoji emoji-id="3004">📢</tg-emoji>' in caption
        assert '<tg-emoji emoji-id="3005">🤖</tg-emoji>' in caption
        assert '<tg-emoji emoji-id="3006">🍿</tg-emoji>' in caption

        animes = [
            Anime(
                id=1,
                code=10,
                title_uz="Naruto",
                title_romaji="Naruto",
                year=2002,
                genres="Ninja",
                status="Tugallangan",
                total_episodes=220,
                description="Ninja bolakay",
                poster_file_id="https://example.com/naruto.jpg"
            )
        ]
        catalog_text, catalog_kb = format_channel_catalog(animes)
        assert '<tg-emoji emoji-id="4001">🎌</tg-emoji>' in catalog_text
        assert '<tg-emoji emoji-id="4002">🔹</tg-emoji>' in catalog_text
        assert '<tg-emoji emoji-id="3005">🤖</tg-emoji>' in catalog_text

