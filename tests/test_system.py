import asyncio
import os
import sys

# Add root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from database.db import DatabaseManager
from services.anilist import anilist_service
from services.post_generator import format_channel_post, format_anime_card


async def run_tests():
    print("🚀 Tizim tekshiruvini boshlash...")
    test_db_file = "test_bot.db"
    if os.path.exists(test_db_file):
        os.remove(test_db_file)

    test_db = DatabaseManager(f"sqlite+aiosqlite:///{test_db_file}")

    try:
        # 1. Baza yaratish testi
        print("1️⃣ Ma'lumotlar bazasini initsializatsiya qilish...")
        await test_db.init_db()
        print("   ✅ Jadvallar muvaffaqiyatli yaratildi.")

        # 2. Foydalanuvchi yaratish testi
        print("2️⃣ Foydalanuvchi CRUD testi...")
        user = await test_db.get_or_create_user(12345678, "anime_fan", "Anime Muxlisi")
        assert user.id == 12345678
        assert user.is_admin is False

        await test_db.set_user_admin(12345678, True)
        is_admin = await test_db.is_admin(12345678)
        assert is_admin is True
        print("   ✅ Foydalanuvchi va Admin huquqi to'g'ri ishladi.")

        # 3. AniList API testi
        print("3️⃣ AniList API integratsiyasi testi...")
        anilist_res = await anilist_service.search_anime("Solo Leveling")
        if anilist_res:
            print(f"   ✅ AniList topdi: {anilist_res['title_romaji']} ({anilist_res['year']}), {anilist_res['episodes']} qism")
            titles = f"{anilist_res.get('title_romaji', '')} {anilist_res.get('title_english', '')}"
            assert "Solo Leveling" in titles or "Level Up" in titles
        else:
            print("   ⚠️ AniList API javob bermadi (tarmoq cheklovi bo'lishi mumkin), lekin kod buzilmadi.")

        # 4. Anime va qism qo'shish testi
        print("4️⃣ Anime va qismlar yaratish testi...")
        anime = await test_db.add_anime(
            code=1,
            title_uz="Yakkaxon yuksalish",
            title_romaji="Solo Leveling",
            year=2024,
            genres="Jangari, Fantastika",
            description="Sung Jinwoo sarguzashtlari.",
            poster_file_id="https://example.com/poster.jpg",
            total_episodes=12,
            status="Tugallangan"
        )
        assert anime.code == 1

        episode = await test_db.add_or_update_episode(
            anime_id=anime.id,
            episode_number=1,
            video_file_id="BAACAgIAAxkBAAIFZm...",
            quality="720p",
            caption="1-qism test"
        )
        assert episode.episode_number == 1

        # Kod bo'yicha olish
        fetched_anime = await test_db.get_anime_by_code(1)
        assert fetched_anime is not None
        assert len(fetched_anime.episodes) == 1
        print("   ✅ Anime va qism muvaffaqiyatli saqlandi va bog'landi.")

        # 5. Post formatlash testi
        print("5️⃣ Kanal posti formatlash testi...")
        post_text, kb = format_channel_post(fetched_anime)
        assert "#kod_1" in post_text
        assert "Yakkaxon yuksalish" in post_text
        assert len(kb.inline_keyboard) >= 2
        print("   ✅ Kanal posti va inline tugmalar to'g'ri shakllandi.")

        # 6. Statistika testi
        print("6️⃣ Statistika testi...")
        stats = await test_db.get_statistics()
        assert stats["users_count"] == 1
        assert stats["animes_count"] == 1
        assert stats["episodes_count"] == 1
        print(f"   ✅ Statistika: {stats}")

        print("\n🎉 Barcha testlar 100% muvaffaqiyatli o'tdi!")
    finally:
        await test_db.engine.dispose()
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(run_tests())
