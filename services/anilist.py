import re
import html
import difflib
import urllib.parse
from typing import Optional, Dict, Any, List
import aiohttp

GENRE_MAP = {
    "Action": "Jangari",
    "Adventure": "Sarguzasht",
    "Comedy": "Komediya",
    "Drama": "Drama",
    "Ecchi": "Etchi",
    "Fantasy": "Fantastika",
    "Hentai": "Hentai",
    "Horror": "Qo'rqinchli",
    "Mahou Shoujo": "Sehrgar qizlar",
    "Mecha": "Mexa",
    "Music": "Musiqa",
    "Mystery": "Detektiv",
    "Psychological": "Psixologik",
    "Romance": "Romantika",
    "Sci-Fi": "Ilmiy-fantastika",
    "Slice of Life": "Kundalik hayot",
    "Sports": "Sport",
    "Supernatural": "G'ayritabiiy",
    "Thriller": "Triller",
}


_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}


async def translate_uz_to_en(text: str) -> str:
    """O'zbekcha yoki ruscha kiritilgan nomni inglizchaga tezkor tarjima qilish (0.2s)"""
    if not text or len(text.strip()) == 0:
        return text
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q=" + urllib.parse.quote(text)
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"User-Agent": _BROWSER_HEADERS["User-Agent"]}, timeout=aiohttp.ClientTimeout(total=2.5)) as r:
                if r.status == 200:
                    res = await r.json()
                    translated = "".join([part[0] for part in res[0] if part and len(part) > 0 and part[0]])
                    return translated.strip() if translated else text
    except Exception:
        pass
    return text


async def translate_to_uzbek(text: str) -> str:
    """Inglizcha tavsifni avtomatik ravishda o'zbek tiliga tarjima qilish"""
    if not text or len(text.strip()) == 0:
        return text
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=uz&dt=t&q=" + urllib.parse.quote(text)
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"User-Agent": _BROWSER_HEADERS["User-Agent"]}, timeout=aiohttp.ClientTimeout(total=3.5)) as r:
                if r.status == 200:
                    res = await r.json()
                    translated = "".join([part[0] for part in res[0] if part[0]])
                    return translated.strip()
    except Exception:
        pass
    return text


class AniListService:
    API_URL = "https://graphql.anilist.co"

    QUERY_SEARCH = """
    query ($search: String) {
      Media(search: $search, type: ANIME, isAdult: false, sort: [POPULARITY_DESC]) {
        id
        title {
          romaji
          english
          native
        }
        startDate {
          year
        }
        episodes
        status
        genres
        isAdult
        averageScore
        description(asHtml: false)
        coverImage {
          extraLarge
          large
        }
        bannerImage
        studios(isMain: true) {
          nodes {
            name
          }
        }
      }
    }
    """

    @staticmethod
    def _clean_description(raw_text: Optional[str]) -> str:
        if not raw_text:
            return "Ajoyib qiziqarli anime sarguzashtlari!"
        # Clean HTML tags and line breaks
        text = re.sub(r"<br\s*/?>", "\n", raw_text)
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)
        # Limit length to 450 chars for Telegram caption limits
        if len(text) > 400:
            text = text[:400] + "..."
        return text.strip()

    async def _query_anilist(self, session: aiohttp.ClientSession, search_term: str) -> Optional[Dict[str, Any]]:
        """AniList GraphQL so'rovi (brauzer headerlari va 3.5s timeout bilan)"""
        try:
            async with session.post(
                self.API_URL,
                headers=_BROWSER_HEADERS,
                json={"query": self.QUERY_SEARCH, "variables": {"search": search_term.strip()}},
                timeout=aiohttp.ClientTimeout(total=3.5, connect=2.0)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", {}).get("Media")
        except Exception:
            pass
        return None

    async def search_anime(self, title: str) -> Optional[Dict[str, Any]]:
        """AniList orqali anime ma'lumotlarini tezkor (O'zbekcha / Ruscha / Inglizcha / Yaponcha) qidirish"""
        clean_title = title.strip()
        if not clean_title:
            return None

        # 1. Mashhur o'zbekcha nomlar lug'atidan tekshirish (0ms)
        resolved_title = None
        lower_title = clean_title.lower()
        norm_title = re.sub(r'[^\w\s]', '', lower_title).strip()
        try:
            from services.image_search import POPULAR_ANIME_UZ
            for romaji, uz in POPULAR_ANIME_UZ.items():
                uz_lower = uz.lower()
                norm_uz = re.sub(r'[^\w\s]', '', uz_lower).strip()
                norm_romaji = re.sub(r'[^\w\s]', '', romaji.lower()).strip()
                if (norm_title == norm_uz or 
                    norm_title in norm_uz or 
                    norm_uz in norm_title or
                    lower_title == uz_lower or
                    lower_title in uz_lower or
                    uz_lower in lower_title or
                    norm_title == norm_romaji or
                    norm_title in norm_romaji):
                    resolved_title = romaji
                    break
            if not resolved_title:
                import difflib
                for romaji, uz in POPULAR_ANIME_UZ.items():
                    main_uz = uz.split('(')[0].strip().lower()
                    norm_main = re.sub(r'[^\w\s]', '', main_uz).strip()
                    if len(norm_title) >= 4 and (
                        difflib.SequenceMatcher(None, norm_title, norm_main).ratio() >= 0.78 or
                        difflib.SequenceMatcher(None, lower_title, main_uz).ratio() >= 0.78
                    ):
                        resolved_title = romaji
                        break
        except Exception:
            pass

        try:
            async with aiohttp.ClientSession() as session:
                media = None
                # Lug'atdan topilgan bo'lsa
                if resolved_title:
                    media = await self._query_anilist(session, resolved_title)

                # Foydalanuvchi kiritgan asl nom bilan qidirish
                if not media:
                    media = await self._query_anilist(session, clean_title)

                # Agar topilmasa va o'zbekcha/ruscha yozilgan bo'lsa, inglizchaga tarjima qilib qidirish
                if not media:
                    translated_en = await translate_uz_to_en(clean_title)
                    if translated_en and translated_en.lower() != clean_title.lower():
                        media = await self._query_anilist(session, translated_en)

                if not media:
                    return None

                # 18+ / Kattalar uchun mo'ljallangan va Hentai kontentlarni qat'iy taqiqlash
                if media.get("isAdult") is True or "Hentai" in media.get("genres", []):
                    return None

                studios_nodes = media.get("studios", {}).get("nodes", [])
                studio_name = studios_nodes[0].get("name") if studios_nodes else "Noma'lum"

                # Janrlarni o'zbekchaga o'girish
                genres_raw = media.get("genres", [])
                genres_uz = [GENRE_MAP.get(g, g) for g in genres_raw]
                genres_str = ", ".join(genres_uz) if genres_uz else "Anime"

                # Tavsifni tozalash va o'zbek tiliga tarjima qilish
                clean_desc = self._clean_description(media.get("description"))
                desc_uz = await translate_to_uzbek(clean_desc)

                # O'zbekcha nomni aniqlash
                uz_canonical = None
                try:
                    from services.image_search import POPULAR_ANIME_UZ
                    r_title = (media.get("title", {}).get("romaji") or "").lower()
                    e_title = (media.get("title", {}).get("english") or "").lower()
                    candidate_keys = [
                        r_title,
                        e_title,
                        re.sub(r'[^\w\s]', '', r_title).strip(),
                        re.sub(r'[^\w\s]', '', e_title).strip(),
                        clean_title.lower(),
                        norm_title,
                    ]
                    for candidate_key in candidate_keys:
                        if candidate_key and candidate_key in POPULAR_ANIME_UZ:
                            uz_canonical = POPULAR_ANIME_UZ[candidate_key].split('(')[0].strip()
                            break
                    if not uz_canonical and resolved_title:
                        res_lower = resolved_title.lower()
                        if res_lower in POPULAR_ANIME_UZ:
                            uz_canonical = POPULAR_ANIME_UZ[res_lower].split('(')[0].strip()
                        elif re.sub(r'[^\w\s]', '', res_lower).strip() in POPULAR_ANIME_UZ:
                            uz_canonical = POPULAR_ANIME_UZ[re.sub(r'[^\w\s]', '', res_lower).strip()].split('(')[0].strip()
                except Exception:
                    pass

                title_uz_final = uz_canonical or clean_title.title()

                return {
                    "id": media.get("id"),
                    "title_romaji": media.get("title", {}).get("romaji") or media.get("title", {}).get("english") or clean_title,
                    "title_english": media.get("title", {}).get("english"),
                    "title_native": media.get("title", {}).get("native"),
                    "title_uz": title_uz_final,
                    "year": media.get("startDate", {}).get("year"),
                    "episodes": media.get("episodes") or 12,
                    "status": "Tugallangan" if media.get("status") == "FINISHED" else "Ongoing",
                    "genres": genres_str,
                    "rating": media.get("averageScore"),
                    "description": desc_uz,
                    "cover_image": media.get("coverImage", {}).get("extraLarge") or media.get("coverImage", {}).get("large"),
                    "banner_image": media.get("bannerImage"),
                    "studio": studio_name,
                    "searched_query": clean_title,
                }
        except Exception:
            return None


anilist_service = AniListService()
