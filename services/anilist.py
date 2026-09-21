import re
import html
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


async def translate_to_uzbek(text: str) -> str:
    """Inglizcha tavsifni avtomatik ravishda o'zbek tiliga tarjima qilish"""
    if not text or len(text.strip()) == 0:
        return text
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=uz&dt=t&q=" + urllib.parse.quote(text)
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=5)) as r:
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
      Media(search: $search, type: ANIME) {
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

    async def search_anime(self, title: str) -> Optional[Dict[str, Any]]:
        """AniList orqali anime ma'lumotlarini qidirish va o'zbekchaga o'girish"""
        variables = {"search": title.strip()}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_URL,
                    json={"query": self.QUERY_SEARCH, "variables": variables},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    media = data.get("data", {}).get("Media")
                    if not media:
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

                    return {
                        "id": media.get("id"),
                        "title_romaji": media.get("title", {}).get("romaji") or media.get("title", {}).get("english"),
                        "title_english": media.get("title", {}).get("english"),
                        "title_native": media.get("title", {}).get("native"),
                        "year": media.get("startDate", {}).get("year"),
                        "episodes": media.get("episodes") or 12,
                        "status": "Tugallangan" if media.get("status") == "FINISHED" else "Ongoing",
                        "genres": genres_str,
                        "rating": media.get("averageScore"),
                        "description": desc_uz,
                        "cover_image": media.get("coverImage", {}).get("extraLarge") or media.get("coverImage", {}).get("large"),
                        "banner_image": media.get("bannerImage"),
                        "studio": studio_name,
                    }
        except Exception:
            return None


anilist_service = AniListService()
