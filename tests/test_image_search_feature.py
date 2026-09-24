# -*- coding: utf-8 -*-
"""
tests/test_image_search_feature.py
Unit and integration tests for the Anime Image Search feature.
Tests:
1. Keyboard structure and presence of '📸 Rasm orqali qidirish'.
2. Uzbek, English, and Japanese title formatting.
3. Confidence levels (high, medium, low) and polite 2nd-image request logic.
4. Handlers and state integrity.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from keyboards.reply import get_main_menu
from services.image_search import (
    AnimeSearchResult,
    anime_image_search_service,
    POPULAR_ANIME_UZ,
    format_seconds
)
from handlers.user import format_anime_search_result, UserStates
from database.models import Anime


def test_keyboard_contains_image_search_button():
    """Asosiy menyuda '📸 Rasm orqali qidirish' tugmasi borligini tekshirish"""
    kb = get_main_menu(is_admin=False)
    all_buttons = [button.text for row in kb.keyboard for button in row]
    assert "📸 Rasm orqali qidirish" in all_buttons, "📸 Rasm orqali qidirish tugmasi menyuda topilmadi!"
    
    admin_kb = get_main_menu(is_admin=True)
    all_admin_buttons = [button.text for row in admin_kb.keyboard for button in row]
    assert "📸 Rasm orqali qidirish" in all_admin_buttons
    assert "⚙️ Admin Panel" in all_admin_buttons


def test_format_seconds():
    """Vaqtni soniyadan MM:SS ga o'tkazishni tekshirish"""
    assert format_seconds(0) == "00:00"
    assert format_seconds(65) == "01:05"
    assert format_seconds(1250) == "20:50"


def test_popular_anime_uzbek_dictionary():
    """Mashhur animelarning o'zbekcha tarjimalari mavjudligini tekshirish"""
    assert POPULAR_ANIME_UZ["naruto"] == "Naruto"
    assert POPULAR_ANIME_UZ["attack on titan"] == "Titanlar Hujumi"
    assert "Solo Leveling" in POPULAR_ANIME_UZ["solo leveling"]
    assert "Jujutsu Kaisen" in POPULAR_ANIME_UZ["jujutsu kaisen"]


def test_format_anime_search_result_three_languages():
    """3 ta tildagi nomlar to'g'ri chiqayotganini tekshirish"""
    result = AnimeSearchResult(
        status="high_confidence",
        similarity_percent=98.5,
        title_english="Attack on Titan",
        title_uzbek="Titanlar Hujumi",
        title_japanese="進撃の巨人",
        title_romaji="Shingeki no Kyojin",
        episode=1,
        timestamp="05:12 - 05:15",
        genres_uz="Jangari, Drama, Fantastika",
        anilist_url="https://anilist.co/anime/16498"
    )

    caption, kb = format_anime_search_result(result, is_second=False)
    
    # 3 ta til mavjudligi tekshiruvi:
    assert "🇺🇿 <b>O'zbekcha:</b> Titanlar Hujumi" in caption
    assert "🇬🇧 <b>Inglizcha:</b> Attack on Titan" in caption
    assert "🇯🇵 <b>Yaponcha:</b> 進撃の巨人 (Shingeki no Kyojin)" in caption
    assert "📊 <b>Aniqlik darajasi:</b> 98.5%" in caption
    assert "🎞 <b>Qism:</b> 1" in caption
    assert "⏱ <b>Kadr vaqti:</b> 05:12 - 05:15" in caption
    assert kb is not None


def test_format_anime_search_result_medium_confidence():
    """Rasm noaniq bo'lganda eng yaqinini chiqarib 2-rasm so'rash xabari borligini tekshirish"""
    result = AnimeSearchResult(
        status="medium_confidence",
        similarity_percent=72.0,
        title_english="Demon Slayer",
        title_uzbek="Demonlarni Qiruvchi Qilich",
        title_japanese="鬼滅の刃",
        title_romaji="Kimetsu no Yaiba",
        episode=19
    )

    caption, kb = format_anime_search_result(result, is_second=False)
    assert "🔎 <b>Rasm biroz noaniq, lekin eng yaqin anime topildi:</b>" in caption
    assert "🇺🇿 <b>O'zbekcha:</b> Demonlarni Qiruvchi Qilich" in caption
    assert "🇬🇧 <b>Inglizcha:</b> Demon Slayer" in caption
    assert "🇯🇵 <b>Yaponcha:</b> 鬼滅の刃 (Kimetsu no Yaiba)" in caption
    assert "2-rasmni" in caption


def test_format_anime_search_result_second_attempt():
    """2-rasm orqali topilganda sarlavha to'g'ri chiqishini tekshirish"""
    result = AnimeSearchResult(
        status="high_confidence",
        similarity_percent=95.0,
        title_english="Jujutsu Kaisen",
        title_uzbek="Sehrli Jang (Jujutsu Kaisen)",
        title_japanese="呪術廻戦",
        title_romaji="Jujutsu Kaisen",
        episode=1
    )

    caption, kb = format_anime_search_result(result, is_second=True)
    assert "🎉 <b>2-rasm orqali anime muvaffaqiyatli aniqlandi!</b>" in caption


def test_user_states_exist():
    """FSM holatlar mavjudligini tekshirish"""
    assert hasattr(UserStates, "waiting_for_anime_photo")
    assert hasattr(UserStates, "waiting_for_second_photo")


if __name__ == "__main__":
    print("Testlar bajarilmoqda...")
    test_keyboard_contains_image_search_button()
    test_format_seconds()
    test_popular_anime_uzbek_dictionary()
    test_format_anime_search_result_three_languages()
    test_format_anime_search_result_medium_confidence()
    test_format_anime_search_result_second_attempt()
    test_user_states_exist()
    print("✅ BARCHA TESTLAR 100% MUVAFFAQIYATLI O'TDI!")
