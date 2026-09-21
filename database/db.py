from typing import List, Optional, Tuple, Sequence
from sqlalchemy import select, update, func, or_, desc
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import selectinload

from config import config
from .models import Base, User, Anime, Episode, RequiredChannel, SystemSetting


class DatabaseManager:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self) -> None:
        """Jadvallarni yaratish va dastlabki sozlamalarni kiritish"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Standart kanalni bazaga qo'shish (agar mavjud bo'lmasa)
        async with self.session_factory() as session:
            stmt = select(RequiredChannel).where(RequiredChannel.channel_id == config.CHANNEL_USERNAME)
            result = await session.execute(stmt)
            channel = result.scalar_one_or_none()
            if not channel and config.CHANNEL_USERNAME:
                new_channel = RequiredChannel(
                    channel_id=config.CHANNEL_USERNAME,
                    channel_title="Uzbekcha animelar",
                    channel_url=config.CHANNEL_URL,
                    is_active=True
                )
                session.add(new_channel)
                await session.commit()

    # ------------------ FOYDALANUVCHILAR ------------------
    async def get_or_create_user(
        self, user_id: int, username: Optional[str], full_name: str
    ) -> User:
        async with self.session_factory() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            is_config_admin = config.is_admin(user_id)

            if not user:
                user = User(
                    id=user_id,
                    username=username,
                    full_name=full_name,
                    is_admin=is_config_admin
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            else:
                updated = False
                if user.username != username:
                    user.username = username
                    updated = True
                if user.full_name != full_name:
                    user.full_name = full_name
                    updated = True
                if is_config_admin and not user.is_admin:
                    user.is_admin = True
                    updated = True
                if updated:
                    await session.commit()

            # MongoDB Atlas fon sinxronlash
            try:
                from .mongo_manager import mongo_manager
                if mongo_manager.is_configured:
                    asyncio.create_task(mongo_manager.upsert_user({
                        "id": user.id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "is_admin": user.is_admin
                    }))
            except Exception:
                pass

            return user

    async def set_user_admin(self, user_id: int, is_admin: bool = True) -> bool:
        async with self.session_factory() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                user.is_admin = is_admin
                await session.commit()
                return True
            return False

    async def is_admin(self, user_id: int) -> bool:
        if config.is_admin(user_id):
            return True
        async with self.session_factory() as session:
            stmt = select(User.is_admin).where(User.id == user_id)
            result = await session.execute(stmt)
            val = result.scalar_one_or_none()
            return bool(val)

    async def get_all_user_ids(self) -> List[int]:
        async with self.session_factory() as session:
            stmt = select(User.id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ------------------ ANIMELAR ------------------
    async def get_next_anime_code(self) -> int:
        """Yangi anime uchun keyingi unikal raqamli kodni hisoblash"""
        async with self.session_factory() as session:
            stmt = select(func.max(Anime.code))
            result = await session.execute(stmt)
            max_code = result.scalar_one_or_none()
            return (max_code or 0) + 1

    async def add_anime(
        self,
        code: int,
        title_uz: str,
        title_romaji: Optional[str] = None,
        year: Optional[int] = None,
        genres: Optional[str] = None,
        description: Optional[str] = None,
        poster_file_id: Optional[str] = None,
        total_episodes: int = 12,
        status: str = "Tugallangan"
    ) -> Anime:
        async with self.session_factory() as session:
            anime = Anime(
                code=code,
                title_uz=title_uz,
                title_romaji=title_romaji,
                year=year,
                genres=genres,
                description=description,
                poster_file_id=poster_file_id,
                total_episodes=total_episodes,
                status=status
            )
            session.add(anime)
            await session.commit()
            await session.refresh(anime)

            # MongoDB Atlas fon sinxronlash
            try:
                from .mongo_manager import mongo_manager
                if mongo_manager.is_configured:
                    asyncio.create_task(mongo_manager.upsert_anime({
                        "code": anime.code,
                        "title_uz": anime.title_uz,
                        "title_romaji": anime.title_romaji,
                        "year": anime.year,
                        "genres": anime.genres,
                        "description": anime.description,
                        "poster_file_id": anime.poster_file_id,
                        "total_episodes": anime.total_episodes,
                        "status": anime.status
                    }))
            except Exception:
                pass

            return anime

    async def get_anime_by_code(self, code: int) -> Optional[Anime]:
        async with self.session_factory() as session:
            stmt = (
                select(Anime)
                .where(Anime.code == code)
                .options(selectinload(Anime.episodes))
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_anime_by_id(self, anime_id: int) -> Optional[Anime]:
        async with self.session_factory() as session:
            stmt = (
                select(Anime)
                .where(Anime.id == anime_id)
                .options(selectinload(Anime.episodes))
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def search_animes(self, query: str, limit: int = 10) -> Sequence[Anime]:
        async with self.session_factory() as session:
            q_pattern = f"%{query.strip()}%"
            stmt = (
                select(Anime)
                .where(
                    or_(
                        Anime.title_uz.ilike(q_pattern),
                        Anime.title_romaji.ilike(q_pattern),
                        Anime.genres.ilike(q_pattern)
                    )
                )
                .options(selectinload(Anime.episodes))
                .order_by(desc(Anime.views_count))
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_random_anime(self) -> Optional[Anime]:
        async with self.session_factory() as session:
            stmt = (
                select(Anime)
                .options(selectinload(Anime.episodes))
                .order_by(func.random())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_recent_animes(self, limit: int = 10, offset: int = 0) -> Sequence[Anime]:
        async with self.session_factory() as session:
            stmt = (
                select(Anime)
                .options(selectinload(Anime.episodes))
                .order_by(desc(Anime.id))
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def increment_anime_views(self, anime_id: int) -> None:
        async with self.session_factory() as session:
            stmt = (
                update(Anime)
                .where(Anime.id == anime_id)
                .values(views_count=Anime.views_count + 1)
            )
            await session.execute(stmt)
            await session.commit()

    async def delete_anime(self, code: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(Anime).where(Anime.code == code)
            result = await session.execute(stmt)
            anime = result.scalar_one_or_none()
            if anime:
                await session.delete(anime)
                await session.commit()
                return True
            return False

    # ------------------ QISMLAR (EPISODES) ------------------
    async def add_or_update_episode(
        self,
        anime_id: int,
        episode_number: int,
        video_file_id: str,
        quality: str = "720p",
        caption: Optional[str] = None
    ) -> Episode:
        async with self.session_factory() as session:
            stmt = select(Episode).where(
                Episode.anime_id == anime_id,
                Episode.episode_number == episode_number,
                Episode.quality == quality
            )
            result = await session.execute(stmt)
            episode = result.scalar_one_or_none()

            if episode:
                episode.video_file_id = video_file_id
                if caption:
                    episode.caption = caption
            else:
                episode = Episode(
                    anime_id=anime_id,
                    episode_number=episode_number,
                    quality=quality,
                    video_file_id=video_file_id,
                    caption=caption
                )
                session.add(episode)

            await session.commit()
            await session.refresh(episode)

            # MongoDB Atlas fon sinxronlash
            try:
                from .mongo_manager import mongo_manager
                if mongo_manager.is_configured:
                    asyncio.create_task(mongo_manager.upsert_episode({
                        "anime_id": episode.anime_id,
                        "episode_number": episode.episode_number,
                        "quality": episode.quality,
                        "video_file_id": episode.video_file_id,
                        "caption": episode.caption,
                        "downloads_count": episode.downloads_count
                    }))
            except Exception:
                pass

            return episode

    async def get_episode(self, anime_id: int, episode_number: int, quality: Optional[str] = None) -> Optional[Episode]:
        async with self.session_factory() as session:
            stmt = select(Episode).where(
                Episode.anime_id == anime_id,
                Episode.episode_number == episode_number
            )
            if quality:
                stmt = stmt.where(Episode.quality == quality)
            stmt = stmt.order_by(desc(Episode.id))
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def increment_episode_downloads(self, episode_id: int) -> None:
        async with self.session_factory() as session:
            stmt = (
                update(Episode)
                .where(Episode.id == episode_id)
                .values(downloads_count=Episode.downloads_count + 1)
            )
            await session.execute(stmt)
            await session.commit()

    # ------------------ MAJBURIY KANALLAR ------------------
    async def get_required_channels(self) -> Sequence[RequiredChannel]:
        async with self.session_factory() as session:
            stmt = select(RequiredChannel).where(RequiredChannel.is_active == True)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def add_required_channel(self, channel_id: str, title: str, url: str) -> RequiredChannel:
        async with self.session_factory() as session:
            stmt = select(RequiredChannel).where(RequiredChannel.channel_id == channel_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.channel_title = title
                existing.channel_url = url
                existing.is_active = True
                await session.commit()
                return existing

            channel = RequiredChannel(
                channel_id=channel_id,
                channel_title=title,
                channel_url=url,
                is_active=True
            )
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            return channel

    # ------------------ STATISTIKA ------------------
    async def get_statistics(self) -> dict:
        async with self.session_factory() as session:
            users_count = (await session.execute(select(func.count(User.id)))).scalar_one() or 0
            animes_count = (await session.execute(select(func.count(Anime.id)))).scalar_one() or 0
            episodes_count = (await session.execute(select(func.count(Episode.id)))).scalar_one() or 0
            total_views = (await session.execute(select(func.sum(Anime.views_count)))).scalar_one() or 0
            total_downloads = (await session.execute(select(func.sum(Episode.downloads_count)))).scalar_one() or 0

            return {
                "users_count": users_count,
                "animes_count": animes_count,
                "episodes_count": episodes_count,
                "total_views": total_views,
                "total_downloads": total_downloads,
            }

    # ------------------ TIZIM SOZLAMALARI (SETTINGS) ------------------
    async def get_setting(self, key: str) -> Optional[str]:
        async with self.session_factory() as session:
            stmt = select(SystemSetting.value).where(SystemSetting.key == key)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def set_setting(self, key: str, value: str) -> None:
        async with self.session_factory() as session:
            stmt = select(SystemSetting).where(SystemSetting.key == key)
            result = await session.execute(stmt)
            setting = result.scalar_one_or_none()
            if setting:
                setting.value = value
            else:
                setting = SystemSetting(key=key, value=value)
                session.add(setting)
            await session.commit()

    async def close(self) -> None:
        """Baza ulanishlarini to'liq yopish va resurslarni ozod qilish"""
        if self.engine:
            await self.engine.dispose()


db = DatabaseManager(config.DATABASE_URL)
