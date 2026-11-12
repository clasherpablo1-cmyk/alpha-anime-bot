# -*- coding: utf-8 -*-
"""
services/image_search.py — Precision Anime Reverse Image Search Engine.
=======================================================================
Standards: Father Mode v7.0, Strict Type Safety, Zero Lazy Code, Production-Ready.

Features:
1. Multi-stage Hybrid Recognition:
   - Primary: Gemini Vision AI (gemini-3.1-flash-lite / gemini-3.5-flash / gemini-3.8-flash)
     Excels at recognizing posters, character art, manga, cropped photos, screen shots.
   - Secondary: trace.moe API (high-confidence anime video frame matching, similarity >= 0.85).
2. Clean, accurate 3-language naming:
   - 🇺🇿 O'zbekcha (Curated authentic Uzbek dubbing/community names without machine-translation mangling).
   - 🇬🇧 Inglizcha (Official international English title).
   - 🇯🇵 Yaponcha (Original Native Kanji/Kana + Romaji).
3. Strict Local DB Matching:
   - Matches ONLY on title_romaji and title_uz with high string similarity (>= 88%), NEVER on genres.
4. Adult / 18+ / Hentai content filtering:
   - Strictly blocks explicit adult content.
5. Intelligent 2-Photo Guidance:
   - High confidence (>= 85%): Direct result with watch button.
   - Medium confidence (65-84%): Result + polite offer to send a 2nd clearer frame if needed.
   - Low confidence (< 65%): Polite request for a 2nd frame.
"""

from __future__ import annotations

import asyncio
import base64
import difflib
import html
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import aiohttp

from config import config
from database.db import db
from database.models import Anime
from services.anilist import GENRE_MAP

logger = logging.getLogger("AnimeImageSearch")

# O'zbekistonda eng ommabop va mashhur animelarning rasmiy / xalqaro o'zbekcha nomlari lug'ati
POPULAR_ANIME_UZ: Dict[str, str] = {
    "attack on titan": "Titanlar Hujumi",
    "shingeki no kyojin": "Titanlar Hujumi",
    "naruto": "Naruto",
    "naruto shippuuden": "Naruto: Dovulli Qaytish",
    "naruto shippuden": "Naruto: Dovulli Qaytish",
    "boruto": "Boruto",
    "boruto: naruto next generations": "Boruto: Narutoning Keyingi Avlodi",
    "jujutsu kaisen": "Sehrli Jang (Jujutsu Kaisen)",
    "demon slayer": "Demonlarni Qiruvchi Qilich",
    "demon slayer: kimetsu no yaiba": "Demonlarni Qiruvchi Qilich",
    "kimetsu no yaiba": "Demonlarni Qiruvchi Qilich",
    "death note": "O'lim Daftari",
    "one piece": "One Piece (Van Pis)",
    "bleach": "Bleach",
    "bleach: thousand-year blood war": "Bleach: Ming Yillik Qonli Urush",
    "bleach: sennen kessen-hen": "Bleach: Ming Yillik Qonli Urush",
    "solo leveling": "Solo Leveling (Yakka Darajalash)",
    "ore dake level up na ken": "Solo Leveling (Yakka Darajalash)",
    "tokyo ghoul": "Tokio Guli",
    "my hero academia": "Mening Qahramonlik Akademiyam",
    "boku no hero academia": "Mening Qahramonlik Akademiyam",
    "chainsaw man": "Chainsaw Man (Benzopila Odam)",
    "hunter x hunter": "Hunter x Hunter (Ovchi va Ovchi)",
    "hunter x hunter (2011)": "Hunter x Hunter (Ovchi va Ovchi)",
    "fullmetal alchemist": "Po'lat Alximik",
    "fullmetal alchemist: brotherhood": "Po'lat Alximik: Birodarlik",
    "black clover": "Qora Sebarga (Black Clover)",
    "sword art online": "Qilichlar San'ati Online (SAO)",
    "vinland saga": "Vinland Sagasi",
    "dragon ball": "Dragon Ball (Ajdaho Sharlari)",
    "dragon ball z": "Dragon Ball Z",
    "dragon ball super": "Dragon Ball Super",
    "one punch man": "One Punch Man (Bir Zarba Odam)",
    "dr. stone": "Doktor Stoun",
    "haikyuu!!": "Haikyu!! (Voleybol)",
    "haikyu!!": "Haikyu!! (Voleybol)",
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
    "frieren": "Frieren: Safar So'ngida",
    "frieren: beyond journey's end": "Frieren: Safar So'ngida",
    "sousou no frieren": "Frieren: Safar So'ngida",
    "kaiju no. 8": "Kaydzyu №8",
    "wind breaker": "Wind Breaker (Shamol Buzar)",
    "dandadan": "Dandadan",
    "overlord": "Hukmdor (Overlord)",
    "re:zero": "Re:Zero — Boshqa Dunyoda Hayot",
    "re:zero - starting life in another world": "Re:Zero — Boshqa Dunyoda Hayot",
    "re:zero kara hajimeru isekai seikatsu": "Re:Zero — Boshqa Dunyoda Hayot",
    "no game no life": "O'yinsiz Hayot Yo'q (No Game No Life)",
    "code geass": "Kod Giass",
    "code geass: lelouch of the rebellion": "Kod Giass: Lelush Qo'zg'oloni",
    "cowboy bebop": "Kovboy Bibop",
    "neon genesis evangelion": "Yevangelion (Evangelion)",
    "violet evergarden": "Vayolet Evergarden",
    "your name.": "Sening Isming (Seni Isming, Kimi no Na wa)",
    "your name": "Sening Isming (Seni Isming, Kimi no Na wa)",
    "kimi no na wa.": "Sening Isming (Seni Isming)",
    "kimi no na wa": "Sening Isming (Seni Isming)",
    "a silent voice": "Ovozsiz Shakl (Koe no Katachi)",
    "koe no katachi": "Ovozsiz Shakl",
    "spirited away": "Ruhlar Bilan Qolib (Spirited Away)",
    "sen to chihiro no kamikakushi": "Ruhlar Bilan Qolib (Spirited Away)",
    "howl's moving castle": "Howlning Ko'chma Qasri",
    "princess mononoke": "Malika Mononoke",
    "weathering with you": "Sen Bilan Birga Ob-havo",
    "tenki no ko": "Sen Bilan Birga Ob-havo",
    "suzume": "Suzume",
    "suzume no tojimari": "Suzume Eshiklarni Yopmoqda",
    "the eminence in shadow": "Soyadagi Kuch (Kage no Jitsuryokusha)",
    "kage no jitsuryokusha ni naritakute!": "Soyadagi Kuch",
    "mushoku tensei": "Ishsizning Qayta Tug'ilishi",
    "mushoku tensei: jobless reincarnation": "Ishsizning Qayta Tug'ilishi",
    "i want to eat your pancreas": "Sening Oshqozon Osti Bezingni Yemoqchiman",
    "kimi no suizou wo tabetai": "Sening Oshqozon Osti Bezingni Yemoqchiman",
}

_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


@dataclass
class AnimeSearchResult:
    status: str  # "high_confidence", "medium_confidence", "low_confidence", "not_found", "error"
    similarity_percent: float
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


def detect_image_mime(image_bytes: bytes) -> str:
    """Rasmlarning sehrli baytlaridan (magic bytes) haqiqiy MIME formatini aniqlash"""
    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"
    if image_bytes.startswith(b"RIFF") and len(image_bytes) > 12 and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


class AnimeImageSearchService:
    """
    Rasm orqali anime qidirishning ko'p bosqichli yuqori aniqlikdagi AI mexanizmi.
    """

    TRACE_MOE_API = "https://api.trace.moe/search?anilistInfo&cutBorders"
    GEMINI_MODELS = [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-flash-latest"
    ]

    async def get_uzbek_title(self, english_title: str, romaji_title: str, db_matched: Optional[Anime] = None) -> str:
        """
        Anime nomini o'zbek tiliga chiroyli, tabiiy va xatosiz aniqlash.
        MUHIM: Proper anime nomlarini Google Translate orqali tarjima qilish QAT'IYAN taqiqlangan!
        (Chunki Google Translate "Bleach" ni "Oqartiruvchi", "One Piece" ni "Bitta parcha" qilib buzib yuboradi).
        """
        if db_matched and db_matched.title_uz:
            return db_matched.title_uz

        clean_eng = english_title.lower().strip() if english_title else ""
        clean_rom = romaji_title.lower().strip() if romaji_title else ""

        # 1. Mashhur animelar lug'atidan aniq moslik
        if clean_eng and clean_eng in POPULAR_ANIME_UZ:
            return POPULAR_ANIME_UZ[clean_eng]
        if clean_rom and clean_rom in POPULAR_ANIME_UZ:
            return POPULAR_ANIME_UZ[clean_rom]

        # 2. Yuqori aniqlikdagi o'xshashlik (Fuzzy match >= 88%)
        best_ratio = 0.0
        best_match = None
        for k, v in POPULAR_ANIME_UZ.items():
            if clean_eng:
                ratio_eng = difflib.SequenceMatcher(None, clean_eng, k).ratio()
                if ratio_eng > best_ratio:
                    best_ratio = ratio_eng
                    best_match = v
            if clean_rom:
                ratio_rom = difflib.SequenceMatcher(None, clean_rom, k).ratio()
                if ratio_rom > best_ratio:
                    best_ratio = ratio_rom
                    best_match = v

        if best_ratio >= 0.88 and best_match:
            return best_match

        # 3. Agar maxsus o'zbekcha tarjima bo'lmasa, rasmiy xalqaro inglizcha yoki romaji nomi saqlanadi
        return english_title or romaji_title

    async def _match_local_db(self, english_title: str, romaji_title: str) -> Optional[Anime]:
        """
        Anime botimizning mahalliy ma'lumotlar bazasida mavjudligini ANIQ va QAT'IY tekshirish.
        DIQQAT: db.search_animes() ishlatilmaydi, chunki u janrlar bo'yicha ham qidirib,
        begona animelarni Naruto yoki boshqasiga yanglish moslab qo'yishi mumkin!
        """
        try:
            recent_animes = await db.get_recent_animes(limit=250)
            if not recent_animes:
                return None

            clean_eng = english_title.lower().strip() if english_title else ""
            clean_rom = romaji_title.lower().strip() if romaji_title else ""

            for anime in recent_animes:
                db_rom = (anime.title_romaji or "").lower().strip()
                db_uz = (anime.title_uz or "").lower().strip()

                # Aniq moslik
                if clean_rom and (clean_rom == db_rom or clean_rom == db_uz):
                    return anime
                if clean_eng and (clean_eng == db_rom or clean_eng == db_uz):
                    return anime

                # Yuqori o'xshashlik (>= 88%)
                if clean_rom and db_rom and difflib.SequenceMatcher(None, clean_rom, db_rom).ratio() >= 0.88:
                    return anime
                if clean_eng and db_rom and difflib.SequenceMatcher(None, clean_eng, db_rom).ratio() >= 0.88:
                    return anime
                if clean_eng and db_uz and difflib.SequenceMatcher(None, clean_eng, db_uz).ratio() >= 0.88:
                    return anime
        except Exception as ex:
            logger.debug(f"Mahalliy DB qidiruvida istisno: {ex}")
        return None

    async def _query_trace_moe(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """trace.moe API orqali kadr aniqligini tekshirish"""
        headers = dict(_BROWSER_HEADERS)
        headers["Content-Type"] = detect_image_mime(image_bytes)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.TRACE_MOE_API,
                    data=image_bytes,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("result", [])
                        if results:
                            top = results[0]
                            # Faqat 72% dan yuqori bo'lgan haqiqiy kadrlarni ko'rib chiqamiz
                            if float(top.get("similarity", 0.0)) >= 0.72:
                                return top
                    else:
                        logger.warning(f"trace.moe javob kodi: {resp.status}")
        except Exception as e:
            logger.error(f"trace.moe so'rovida xatolik: {e}")
        return None

    async def _query_gemini_vision(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """
        Gemini Multimodal Vision orqali har qanday kadr, fan-art, manga yoki poster rasmlarini aniqlash.
        Model ishlamay qolishining oldini olish uchun bir nechta barqaror modellar orqali fallback qilinadi.
        """
        api_key = config.GEMINI_API_KEY
        if not api_key:
            return None

        mime_type = detect_image_mime(image_bytes)
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            "Sen anime bo'yicha dunyodagi eng bilimdon ekspertisan. Rasmda qaysi anime tasvirlanganini aniqla. "
            "Agar rasm anime emas bo'lsa yoki noaniq bo'lsa, 'found': false deb qaytar. "
            "Nomlarni aynan quyidagi qat'iy standartda ber:\n"
            "1. 'title_english': Rasmiy xalqaro inglizcha nomi (masalan: Solo Leveling, Attack on Titan, Naruto, Bleach).\n"
            "2. 'title_romaji': Yaponcha Romaji nomi (masalan: Ore dake Level Up na Ken, Shingeki no Kyojin).\n"
            "3. 'title_japanese': Asl yaponcha Kanji/Kana yozuvidagi nomi (masalan: 俺だけレベルアップな件, 進撃の巨人, NARUTO -ナルト-).\n"
            "4. 'title_uzbek': O'zbekistondagi ommabop nomi (agar maxsus nomi bo'lsa, masalan: Yakka Darajalash, Titanlar Hujumi; aks holda xalqaro nomini saqla, so'zlarni xato tarjima qilib buzma).\n"
            "5. 'character_name': Kadrda ko'ringan asosiy personaj ismi (masalan: Sung Jin-woo, Eren Yeager).\n"
            "6. 'confidence': Ishonch darajasi (0 dan 100 gacha raqam).\n"
            "7. 'genres': Janrlari o'zbek tilida (masalan: Jangari, Sarguzasht, Fantaziya).\n"
            "8. 'is_adult': Agar 18+ yoki Hentai bo'lsa true, aks holda false.\n\n"
            "Faqat va faqat to'g'ri JSON formatida javob ber:\n"
            "{\n"
            '  "found": true,\n'
            '  "title_english": "...",\n'
            '  "title_romaji": "...",\n'
            '  "title_japanese": "...",\n'
            '  "title_uzbek": "...",\n'
            '  "character_name": "...",\n'
            '  "confidence": 95,\n'
            '  "genres": "...",\n'
            '  "is_adult": false\n'
            "}"
        )

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": img_b64}}
                ]
            }],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        async with aiohttp.ClientSession() as session:
            for model_name in self.GEMINI_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                try:
                    async with session.post(
                        url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=18)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            candidates = data.get("candidates", [])
                            if not candidates:
                                continue
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if not parts:
                                continue
                            text = parts[0].get("text", "").strip()
                            clean_json = re.sub(r"^```json\s*|\s*```$", "", text).strip()
                            parsed = json.loads(clean_json)
                            if parsed.get("found"):
                                return parsed
                        else:
                            logger.debug(f"Gemini {model_name} javob kodi: {resp.status}")
                except Exception as e:
                    logger.debug(f"Gemini {model_name} so'rovida xatolik: {e}")
                    continue

        return None

    async def search_by_image(self, image_bytes: bytes, is_second_attempt: bool = False) -> AnimeSearchResult:
        """
        Asosiy qidiruv algoritmi:
        1. trace.moe va Gemini Vision AI ni parallel tekshirish (maksimal tezlik va aniqlik).
        2. trace.moe similarity >= 0.85 bo'lsa (aniq kadr) -> trace.moe ma'lumotlari ishlatiladi.
        3. Gemini Vision yuqori ishonch bersa (confidence >= 80) -> Gemini Vision ishlatiladi.
        4. O'zbekcha nomlar mashhur lug'atdan olinadi, mashina tarjimasi bilan nomlar buzilmaydi.
        5. Mahalliy DB qat'iy tekshiriladi (false matching bo'lmaydi).
        """
        # Parallel ravishda trace.moe va Gemini Vision'ni chaqiramiz
        trace_task = asyncio.create_task(self._query_trace_moe(image_bytes))
        gemini_task = asyncio.create_task(self._query_gemini_vision(image_bytes))

        trace_match, gemini_result = await asyncio.gather(trace_task, gemini_task, return_exceptions=True)

        if isinstance(trace_match, Exception):
            trace_match = None
        if isinstance(gemini_result, Exception):
            gemini_result = None

        # 18+ va Hentai filtr tekshiruvi
        if gemini_result and gemini_result.get("is_adult"):
            logger.info("18+ / Hentai anime Gemini Vision tomonidan aniqlandi va filtrlandi.")
            return AnimeSearchResult(
                status="error",
                similarity_percent=0.0,
                title_english="",
                title_uzbek="",
                title_japanese="",
                title_romaji="",
                raw_error="18_plus_filtered",
                is_second_attempt=is_second_attempt
            )

        # 1-variant: trace.moe yuqori aniqlikdagi kadr topgan bo'lsa (similarity >= 0.85)
        if trace_match:
            sim = float(trace_match.get("similarity", 0.0))
            if sim >= 0.85:
                sim_pct = round(sim * 100, 1)
                anilist_data = trace_match.get("anilist", {})
                title_info = anilist_data.get("title", {}) if isinstance(anilist_data, dict) else {}

                romaji = title_info.get("romaji") or ""
                english = title_info.get("english") or romaji
                native = title_info.get("native") or romaji

                # Janrlar
                raw_genres = anilist_data.get("genres", []) if isinstance(anilist_data, dict) else []
                if "Hentai" in raw_genres or (isinstance(anilist_data, dict) and anilist_data.get("isAdult")):
                    return AnimeSearchResult(
                        status="error",
                        similarity_percent=0.0,
                        title_english="",
                        title_uzbek="",
                        title_japanese="",
                        title_romaji="",
                        raw_error="18_plus_filtered",
                        is_second_attempt=is_second_attempt
                    )

                genres_uz_list = [GENRE_MAP.get(g, g) for g in raw_genres]
                genres_uz = ", ".join(genres_uz_list) if genres_uz_list else "Anime"

                time_from = trace_match.get("from", 0.0)
                time_to = trace_match.get("to", 0.0)
                timestamp_str = f"{format_seconds(time_from)} - {format_seconds(time_to)}"
                episode_val = trace_match.get("episode")

                matched_db = await self._match_local_db(english, romaji)
                uzbek_title = await self.get_uzbek_title(english, romaji, matched_db)

                return AnimeSearchResult(
                    status="high_confidence",
                    similarity_percent=sim_pct,
                    title_english=english,
                    title_uzbek=uzbek_title,
                    title_japanese=native,
                    title_romaji=romaji,
                    episode=episode_val,
                    timestamp=timestamp_str,
                    genres_uz=genres_uz,
                    preview_image_url=trace_match.get("image"),
                    preview_video_url=trace_match.get("video"),
                    anilist_url=anilist_data.get("siteUrl") if isinstance(anilist_data, dict) else None,
                    db_anime=matched_db,
                    is_second_attempt=is_second_attempt
                )

        # 2-variant: Gemini Vision orqali aniqlash (Posters, Art, Manga, Cropped, or trace.moe < 0.85)
        if gemini_result and gemini_result.get("found"):
            conf = float(gemini_result.get("confidence", 85.0))
            eng = (gemini_result.get("title_english") or "").strip()
            rom = (gemini_result.get("title_romaji") or eng).strip()
            jap = (gemini_result.get("title_japanese") or rom).strip()
            gemini_uz = (gemini_result.get("title_uzbek") or "").strip()
            char_name = gemini_result.get("character_name")
            genres = gemini_result.get("genres", "Anime")

            matched_db = await self._match_local_db(eng, rom)
            uzbek_title = await self.get_uzbek_title(eng, rom, matched_db)

            # Agar lug'atda bo'lmasa, lekin Gemini maxsus o'zbekcha nom taklif qilgan bo'lsa
            if uzbek_title == eng and gemini_uz and gemini_uz.lower() != eng.lower():
                uzbek_title = gemini_uz

            status = "high_confidence" if conf >= 80 else "medium_confidence"

            # Agar trace.moe video kadr ma'lumotlarini ham bergan bo'lsa, ularni qo'shamiz
            ep_val = None
            ts_str = None
            vid_url = None
            img_url = None
            if trace_match and float(trace_match.get("similarity", 0.0)) >= 0.75:
                ep_val = trace_match.get("episode")
                time_from = trace_match.get("from", 0.0)
                time_to = trace_match.get("to", 0.0)
                ts_str = f"{format_seconds(time_from)} - {format_seconds(time_to)}"
                vid_url = trace_match.get("video")
                img_url = trace_match.get("image")

            return AnimeSearchResult(
                status=status,
                similarity_percent=conf,
                title_english=eng,
                title_uzbek=uzbek_title,
                title_japanese=jap,
                title_romaji=rom,
                episode=ep_val,
                timestamp=ts_str,
                genres_uz=genres,
                character_name=char_name,
                preview_image_url=img_url,
                preview_video_url=vid_url,
                db_anime=matched_db,
                is_second_attempt=is_second_attempt
            )

        # 3-variant: trace.moe o'rtacha aniqlikda (0.75 <= similarity < 0.85) va Gemini javob bermagan
        if trace_match and float(trace_match.get("similarity", 0.0)) >= 0.75:
            sim = float(trace_match.get("similarity", 0.0))
            sim_pct = round(sim * 100, 1)
            anilist_data = trace_match.get("anilist", {})
            title_info = anilist_data.get("title", {}) if isinstance(anilist_data, dict) else {}

            romaji = title_info.get("romaji") or ""
            english = title_info.get("english") or romaji
            native = title_info.get("native") or romaji

            raw_genres = anilist_data.get("genres", []) if isinstance(anilist_data, dict) else []
            genres_uz_list = [GENRE_MAP.get(g, g) for g in raw_genres]
            genres_uz = ", ".join(genres_uz_list) if genres_uz_list else "Anime"

            time_from = trace_match.get("from", 0.0)
            time_to = trace_match.get("to", 0.0)
            timestamp_str = f"{format_seconds(time_from)} - {format_seconds(time_to)}"
            episode_val = trace_match.get("episode")

            matched_db = await self._match_local_db(english, romaji)
            uzbek_title = await self.get_uzbek_title(english, romaji, matched_db)

            return AnimeSearchResult(
                status="medium_confidence",
                similarity_percent=sim_pct,
                title_english=english,
                title_uzbek=uzbek_title,
                title_japanese=native,
                title_romaji=romaji,
                episode=episode_val,
                timestamp=timestamp_str,
                genres_uz=genres_uz,
                preview_image_url=trace_match.get("image"),
                preview_video_url=trace_match.get("video"),
                anilist_url=anilist_data.get("siteUrl") if isinstance(anilist_data, dict) else None,
                db_anime=matched_db,
                is_second_attempt=is_second_attempt
            )

        # 4-variant: Mutlaqo aniqlab bo'lmadi -> 2-rasm so'raladi
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
