# -*- coding: utf-8 -*-
"""
services/image_search.py — Anime Reverse Image Search Engine (trace.moe + Gemini 3.6 Flash Vision + AniList + DB Matcher).
======================================================================================================================
Standards: Father Mode v7.0, Strict Type Safety, Zero Lazy Code, Production-Ready.

Features:
1. 1-rasm orqali anime kadrini sekundiga aniqlash (trace.moe API).
2. O'zbekcha, Inglizcha va Yaponcha (Kanji + Romaji) nomlarni to'liq taqdim etish.
3. Rasm noaniq yoki qirqilgan bo'lsa ham eng yaqin variantni qidirish va topishga maksimal harakat qilish.
4. Agar 1-rasm juda noaniq bo'lsa, foydalanuvchidan muloyimlik bilan 2-rasmni so'rash.
5. Gemini 3.6 Flash Vision yordamida fan-art, manga, poster va xira rasmlarni chuqur sun'iy intellekt orqali aniqlash.
6. Mahalliy bot bazasi (SQLite/MongoDB) bilan integratsiya: agar anime botda mavjud bo'lsa, to'g'ridan-to'g'ri ko'rish tugmasini chiqarish.
"""

from __future__ import annotations

import asyncio
import base64
import html
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp

from config import config
from database.db import db
from database.models import Anime
from services.anilist import GENRE_MAP, translate_to_uzbek

logger = logging.getLogger("AnimeImageSearch")

# O'zbekistonda eng ommabop va mashhur animelarning rasmiy / xalqaro o'zbekcha nomlari lug'ati
POPULAR_ANIME_UZ: Dict[str, str] = {
    "attack on titan": "Titanlar Hujumi",
    "shingeki no kyojin": "Titanlar Hujumi",
    "naruto": "Naruto",
    "naruto shippuuden": "Naruto: Dovulli Qaytish",
    "naruto shippuden": "Naruto: Dovulli Qaytish",
    "boruto: naruto next generations": "Boruto: Narutoning Keyingi Avlodi",
    "jujutsu kaisen": "Sehrli Jang (Jujutsu Kaisen)",
    "demon slayer: kimetsu no yaiba": "Demonlarni Qiruvchi Qilich",
    "kimetsu no yaiba": "Demonlarni Qiruvchi Qilich",
    "death note": "O'lim Daftari",
    "one piece": "Van Pis (One Piece)",
    "bleach": "Bleach: Oqartiruvchi",
    "bleach: sennen kessen-hen": "Bleach: Ming Yillik Qonli Urush",
    "solo leveling": "Yakka Darajalash (Solo Leveling)",
    "ore dake level up na ken": "Yakka Darajalash (Solo Leveling)",
    "tokyo ghoul": "Tokio Guli",
    "my hero academia": "Mening Qahramonlik Akademiyam",
    "boku no hero academia": "Mening Qahramonlik Akademiyam",
    "chainsaw man": "Benzopila Odam (Chainsaw Man)",
    "hunter x hunter": "Ovchi va Ovchi (Hunter x Hunter)",
    "hunter x hunter (2011)": "Ovchi va Ovchi (Hunter x Hunter)",
    "fullmetal alchemist": "Po'lat Alximik",
    "fullmetal alchemist: brotherhood": "Po'lat Alximik: Birodarlik",
    "black clover": "Qora Yonbosh (Black Clover)",
    "sword art online": "Qilichlar San'ati Online (SAO)",
    "vinland saga": "Vinland Sagasi",
    "dragon ball": "Ajdaho Sharlari (Dragon Ball)",
    "dragon ball z": "Ajdaho Sharlari Z",
    "dragon ball super": "Ajdaho Sharlari Super",
    "one punch man": "Bir Zarba Odam (One Punch Man)",
    "dr. stone": "Doktor Stoun",
    "haikyuu!!": "Haykyu!! (Voleybol)",
    "spy x family": "Josus Oila (Spy x Family)",
    "blue lock": "Ko'k Qulf (Blue Lock)",
    "tokyo revengers": "Tokio Qasoskorlari",
    "cyberpunk: edgerunners": "Kiberpank: Chegarachilar",
    "steins;gate": "Shteyn Darvozasi (Steins;Gate)",
    "classroom of the elite": "Elita Sinfxonasi",
    "youkoso jitsuryoku shijou shugi no kyoushitsu e": "Elita Sinfxonasi",
    "mashle": "Mashl: Sehr va Mushaklar",
    "mashle: magic and muscles": "Mashl: Sehr va Mushaklar",
    "hell's paradise": "Jahannam Jannati (Jigokuraku)",
    "jigokuraku": "Jahannam Jannati (Jigokuraku)",
    "oshi no ko": "Yulduz Farzandi (Oshi no Ko)",
    "frieren: beyond journey's end": "Frieren: Safar So'ngida",
    "sousou no frieren": "Frieren: Safar So'ngida",
    "kaiju no. 8": "Kaydzyu №8",
    "wind breaker": "Shamol Buzar (Wind Breaker)",
    "dandadan": "Dandadan",
    "overlord": "Lord (Overlord)",
    "re:zero - starting life in another world": "Re:Zero — Boshqa Dunyoda Hayot",
    "re:zero kara hajimeru isekai seikatsu": "Re:Zero — Boshqa Dunyoda Hayot",
    "no game no life": "O'yinsiz Hayot Yo'q",
    "code geass: lelouch of the rebellion": "Kod Giass: Lelush Qo'zg'oloni",
    "code geass": "Kod Giass",
    "cowboy bebop": "Kovboy Bibop",
    "neon genesis evangelion": "Yangi Asr Yevangelioni",
    "violet evergarden": "Vayolet Evergarden",
    "your name.": "Sening Isming (Kimi no Na wa)",
    "kimi no na wa.": "Sening Isming",
    "a silent voice": "Ovozsiz Shakl (Koe no Katachi)",
    "koe no katachi": "Ovozsiz Shakl",
    "spirited away": "Ruhlar Bilan Birga",
    "sen to chihiro no kamikakushi": "Ruhlar Bilan Birga",
    "howl's moving castle": "Howlning Ko'chma Qasri",
    "princess mononoke": "Malika Mononoke",
    "weathering with you": "Sen Bilan Birga Ob-havo",
    "tenki no ko": "Sen Bilan Birga Ob-havo",
    "suzume": "Suzume",
    "suzume no tojimari": "Suzume Eshiklarni Yopmoqda",
    "the eminence in shadow": "Soyadagi Kuch (Kage no Jitsuryokusha)",
    "kage no jitsuryokusha ni naritakute!": "Soyadagi Kuch",
    "mushoku tensei: jobless reincarnation": "Ishsizning Qayta Tug'ilishi",
    "mushoku tensei": "Ishsizning Qayta Tug'ilishi",
}

_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


@dataclass
class AnimeSearchResult:
    status: str  # "high_confidence", "medium_confidence", "low_confidence", "not_found", "error"
    similarity_percent: float  # Masalan: 94.5%
    title_english: str
    title_uzbek: str
    title_japanese: str
    title_romaji: str
    episode: Optional[Union[int, str]] = None
    timestamp: Optional[str] = None
    genres_uz: str = ""
    preview_image_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    anilist_url: Optional[str] = None
    character_name: Optional[str] = None
    db_anime: Optional[Anime] = None
    is_second_attempt: bool = False
    raw_error: Optional[str] = None


def format_seconds(seconds: float) -> str:
    """Soniyani MM:SS formatiga o'tkazish"""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


class AnimeImageSearchService:
    """
    Rasm orqali anime qidirishning ko'p bosqichli yuqori aniqlikdagi mexanizmi.
    """

    TRACE_MOE_API = "https://api.trace.moe/search?anilistInfo&cutBorders"

    async def get_uzbek_title(self, english_title: str, romaji_title: str, db_matched: Optional[Anime] = None) -> str:
        """Anime nomini o'zbek tiliga chiroyli va tabiiy tarjima qilish"""
        if db_matched and db_matched.title_uz:
            return db_matched.title_uz

        # 1. Mashhur animelar lug'atidan qidirish
        clean_eng = english_title.lower().strip()
        clean_rom = romaji_title.lower().strip()
        
        if clean_eng in POPULAR_ANIME_UZ:
            return POPULAR_ANIME_UZ[clean_eng]
        if clean_rom in POPULAR_ANIME_UZ:
            return POPULAR_ANIME_UZ[clean_rom]

        for k, v in POPULAR_ANIME_UZ.items():
            if k in clean_eng or k in clean_rom or clean_eng in k:
                return v

        # 2. Google Translate orqali tarjima qilish
        translated = await translate_to_uzbek(english_title or romaji_title)
        if translated and translated.strip() != english_title.strip():
            return translated.strip()

        # 3. Agar tarjima o'zgarmasa, chiroyli sarlavha holida qaytarish
        return english_title or romaji_title

    async def _query_trace_moe(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """trace.moe API ga kadr rasm ma'lumotlarini yuborib eng yaqin qismlarni topish"""
        headers = dict(_BROWSER_HEADERS)
        headers["Content-Type"] = "image/jpeg"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.TRACE_MOE_API,
                    data=image_bytes,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("result", [])
                        if results:
                            return results[0]
                    else:
                        logger.warning(f"trace.moe javob kodi: {resp.status}")
        except Exception as e:
            logger.error(f"trace.moe so'rovida xatolik: {e}")
        return None

    async def _query_gemini_vision(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """trace.moe topa olmaganda yoki fan-art/manga bo'lganda Gemini Vision orqali aniqlash"""
        api_key = config.GEMINI_API_KEY
        if not api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            "Sen eng bilimdon yapon anime ekspertisan. Berilgan rasm (kadr, poster, manga, fan-art) "
            "qaysi animedan ekanligini aniqla. Javobni FAQAT to'liq JSON formatida qaytar:\n"
            "{\n"
            '  "found": true,\n'
            '  "title_english": "English title",\n'
            '  "title_romaji": "Romaji title",\n'
            '  "title_japanese": "Native Japanese with Kanji",\n'
            '  "title_uzbek": "O\'zbekcha nomi",\n'
            '  "character_name": "Personaj ismi",\n'
            '  "confidence": 85,\n'
            '  "genres": "Jangari, Sarguzasht",\n'
            '  "episode": "Noma\'lum yoki taxminiy qism"\n'
            "}"
        )

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                ]
            }],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=25)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(text)
                        if parsed.get("found"):
                            return parsed
                    else:
                        logger.warning(f"Gemini Vision javob kodi: {resp.status}")
        except Exception as e:
            logger.error(f"Gemini Vision so'rovida xatolik: {e}")
        return None

    async def _match_local_db(self, english_title: str, romaji_title: str) -> Optional[Anime]:
        """Anime botimizning mahalliy ma'lumotlar bazasida mavjudligini tekshirish"""
        try:
            # 1. Inglizcha nom bo'yicha
            if english_title:
                matches = await db.search_animes(english_title, limit=3)
                if matches:
                    return matches[0]

            # 2. Romaji nom bo'yicha
            if romaji_title:
                matches = await db.search_animes(romaji_title, limit=3)
                if matches:
                    return matches[0]
        except Exception as ex:
            logger.debug(f"Mahalliy DB qidiruvida istisno: {ex}")
        return None

    async def search_by_image(self, image_bytes: bytes, is_second_attempt: bool = False) -> AnimeSearchResult:
        """
        Asosiy qidiruv funksiyasi:
        1. trace.moe orqali kadr aniqligini tekshirish.
        2. Aniqlik darajasini tasniflash (yuqori, o'rtacha, past).
        3. Noaniq bo'lsa Gemini Vision orqali qayta tekshirib ko'rish.
        4. O'zbekcha, yaponcha va inglizcha nomlarni boyitish.
        5. Bot bazasi bilan tekshirish.
        """
        top_match = await self._query_trace_moe(image_bytes)

        if top_match:
            similarity = float(top_match.get("similarity", 0.0))
            sim_percent = round(similarity * 100, 1)
            anilist_data = top_match.get("anilist", {}) or {}
            title_info = anilist_data.get("title", {}) or {}

            romaji = title_info.get("romaji") or ""
            english = title_info.get("english") or romaji or "Noma'lum"
            native = title_info.get("native") or romaji or ""

            # Janrlar
            raw_genres = anilist_data.get("genres", [])
            genres_uz_list = [GENRE_MAP.get(g, g) for g in raw_genres]
            genres_uz = ", ".join(genres_uz_list) if genres_uz_list else "Anime"

            # Kadr vaqti
            time_from = top_match.get("from", 0.0)
            time_to = top_match.get("to", 0.0)
            timestamp_str = f"{format_seconds(time_from)} - {format_seconds(time_to)}"
            episode_val = top_match.get("episode")

            # Mahalliy baza bilan moslik
            matched_db = await self._match_local_db(english, romaji)
            uzbek_title = await self.get_uzbek_title(english, romaji, matched_db)

            # Rasm va video preview
            preview_img = top_match.get("image")
            preview_vid = top_match.get("video")
            site_url = anilist_data.get("siteUrl")

            # 1. YUQORI ANIQLIK (similarity >= 82%)
            if similarity >= 0.82:
                return AnimeSearchResult(
                    status="high_confidence",
                    similarity_percent=sim_percent,
                    title_english=english,
                    title_uzbek=uzbek_title,
                    title_japanese=native,
                    title_romaji=romaji,
                    episode=episode_val,
                    timestamp=timestamp_str,
                    genres_uz=genres_uz,
                    preview_image_url=preview_img,
                    preview_video_url=preview_vid,
                    anilist_url=site_url,
                    db_anime=matched_db,
                    is_second_attempt=is_second_attempt
                )

            # 2. O'RTACHA ANIQLIK (65% <= similarity < 82%) - Rasm biroz xira yoki qirqilgan, ammo topishga harakat qildi
            elif similarity >= 0.65:
                return AnimeSearchResult(
                    status="medium_confidence",
                    similarity_percent=sim_percent,
                    title_english=english,
                    title_uzbek=uzbek_title,
                    title_japanese=native,
                    title_romaji=romaji,
                    episode=episode_val,
                    timestamp=timestamp_str,
                    genres_uz=genres_uz,
                    preview_image_url=preview_img,
                    preview_video_url=preview_vid,
                    anilist_url=site_url,
                    db_anime=matched_db,
                    is_second_attempt=is_second_attempt
                )

        # 3. Agar trace.moe past natija bersa yoki topa olmasa -> Gemini Vision yordamga keladi
        gemini_result = await self._query_gemini_vision(image_bytes)
        if gemini_result:
            conf = float(gemini_result.get("confidence", 70.0))
            eng = gemini_result.get("title_english") or "Noma'lum"
            rom = gemini_result.get("title_romaji") or eng
            jap = gemini_result.get("title_japanese") or rom
            uz = gemini_result.get("title_uzbek") or eng
            char_name = gemini_result.get("character_name")
            ep = gemini_result.get("episode")
            genres = gemini_result.get("genres", "Anime")

            matched_db = await self._match_local_db(eng, rom)
            if not uz or uz == eng:
                uz = await self.get_uzbek_title(eng, rom, matched_db)

            return AnimeSearchResult(
                status="high_confidence" if conf >= 85 else "medium_confidence",
                similarity_percent=conf,
                title_english=eng,
                title_uzbek=uz,
                title_japanese=jap,
                title_romaji=rom,
                episode=ep,
                genres_uz=genres,
                character_name=char_name,
                db_anime=matched_db,
                is_second_attempt=is_second_attempt
            )

        # 4. MUTLAQO ANIQLAB BO'LMADI (Juda xira, qorong'i yoki kadr emas) -> 2-rasm so'rash kerak
        return AnimeSearchResult(
            status="low_confidence",
            similarity_percent=0.0,
            title_english="",
            title_uzbek="",
            title_japanese="",
            title_romaji="",
            is_second_attempt=is_second_attempt
        )


anime_image_search_service = AnimeImageSearchService()
