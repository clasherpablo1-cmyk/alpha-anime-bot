from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class Anime(Base):
    __tablename__ = "animes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title_uz: Mapped[str] = mapped_column(String(255), index=True)
    title_romaji: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    genres: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    poster_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_episodes: Mapped[int] = mapped_column(Integer, default=12)
    status: Mapped[str] = mapped_column(String(50), default="Tugallangan")  # "Ongoing" yoki "Tugallangan"
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    episodes: Mapped[List["Episode"]] = relationship(
        "Episode",
        back_populates="anime",
        cascade="all, delete-orphan",
        order_by="Episode.episode_number"
    )


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anime_id: Mapped[int] = mapped_column(Integer, ForeignKey("animes.id", ondelete="CASCADE"), index=True)
    episode_number: Mapped[int] = mapped_column(Integer, index=True)
    quality: Mapped[str] = mapped_column(String(20), default="720p")
    video_file_id: Mapped[str] = mapped_column(String(255))
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    anime: Mapped["Anime"] = relationship("Anime", back_populates="episodes")


class RequiredChannel(Base):
    __tablename__ = "required_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[str] = mapped_column(String(128), unique=True)  # Masalan: @uzbekcha_animelar_alpha yoki -100...
    channel_title: Mapped[str] = mapped_column(String(255))
    channel_url: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
