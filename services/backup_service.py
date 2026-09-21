# -*- coding: utf-8 -*-
"""
services/backup_service.py — Autonomous Telegram Cloud Backup & Auto-Restore System for Anime Bot.
================================================================================================
Standards: Father Mode v7.0, Strict Type Safety, Zero Lazy Code, Production-Ready.

Features:
1. Complete Database Archival:
   - Backs up the SQLite database (bot_database.db) containing all animes, episodes, and users.
   - Generates structured catalog JSON (anime_catalog.json) and manifest metadata (backup_meta.json).
   - Packages into a lightweight, highly compressed ZIP archive.
2. Direct Delivery to @acacafagag (-1003957205922):
   - Uploads directly via Telegram Bot API using sendDocument.
   - Automatically deletes old backup messages so the channel stays clean ("Eski zaxiralar avtomatik tozalandi").
   - Uses the exact professional Uzbek caption styling matching the user's Minecraft bot.
3. Cloud Ephemeral Persistence & Auto-Restore:
   - On container startup (e.g. Render 24/7 web service), checks if local DB is missing or empty.
   - If needed, automatically downloads and restores the latest backup from the backup channel.
4. Autonomous Periodic & Event-Driven Triggers:
   - Runs automatically every 30 minutes in the background.
   - Triggers instantly upon adding new anime, episodes, or via admin /backup command.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import sqlite3
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import aiofiles
from aiogram import Bot
from aiogram.types import BufferedInputFile

from config import config
from database.db import db
from database.models import Anime, Episode, User

logger = logging.getLogger("AnimeBackupService")

_BASE_DIR = Path(__file__).resolve().parent.parent
_DB_PATH = _BASE_DIR / "bot_database.db"
_BACKUP_LOCK = asyncio.Lock()


class BackupService:
    """
    Manages automated cloud backups to Telegram channel @acacafagag
    and provides disaster recovery / auto-restore capabilities for 24/7 hosting.
    """

    def __init__(self, channel_id: Optional[str] = None) -> None:
        self.channel_id = channel_id or config.BACKUP_CHANNEL_ID
        self.last_backup_time: float = 0.0

    async def create_backup_zip(self) -> Tuple[bytes, str, Dict[str, Any]]:
        """
        Generates an in-memory ZIP archive containing the SQLite database,
        JSON catalog dump, and manifest metadata.
        """
        stats = await db.get_statistics()
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d_%H-%M")
        now_display = now_dt.strftime("%d.%m.%Y %H:%M:%S")

        # 1. Read SQLite DB safely
        db_bytes = b""
        if _DB_PATH.exists():
            async with aiofiles.open(_DB_PATH, "rb") as f:
                db_bytes = await f.read()

        # 2. Generate structured catalog export
        catalog_data = []
        try:
            animes = await db.get_recent_animes(limit=500)
            for a in animes:
                episodes_list = [
                    {
                        "episode_number": ep.episode_number,
                        "quality": ep.quality,
                        "video_file_id": ep.video_file_id,
                        "downloads_count": ep.downloads_count,
                    }
                    for ep in (a.episodes or [])
                ]
                catalog_data.append({
                    "code": a.code,
                    "title_uz": a.title_uz,
                    "title_romaji": a.title_romaji,
                    "year": a.year,
                    "genres": a.genres,
                    "total_episodes": a.total_episodes,
                    "views_count": a.views_count,
                    "status": a.status,
                    "episodes": episodes_list,
                })
        except Exception as e:
            logger.warning(f"Katalogni eksport qilishda ogohlantirish: {e}")

        meta = {
            "title": "Uzbekcha Animelar (Alpha) Database Backup",
            "backup_time": now_display,
            "bot_username": f"@{config.BOT_USERNAME}",
            "channel_username": config.CHANNEL_USERNAME,
            "total_animes": stats["animes_count"],
            "total_episodes": stats["episodes_count"],
            "total_users": stats["users_count"],
            "total_views": stats["total_views"],
            "total_downloads": stats["total_downloads"],
            "database_driver": "SQLite 3 + aiosqlite (Telegram Cloud Sync)",
            "version": "1.0",
        }

        # 3. Create ZIP archive
        mem = io.BytesIO()
        with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            if db_bytes:
                zf.writestr("bot_database.db", db_bytes)
            zf.writestr("anime_catalog.json", json.dumps(catalog_data, indent=2, ensure_ascii=False))
            zf.writestr("backup_meta.json", json.dumps(meta, indent=2, ensure_ascii=False))

        zip_bytes = mem.getvalue()
        mem.close()
        zip_filename = f"anime_backup_AlphaAnime_{now_str}.zip"

        return zip_bytes, zip_filename, stats

    def format_backup_caption(self, stats: Dict[str, Any], now_display: str) -> str:
        """
        Formats the exact professional Uzbek caption matching the other bot's style.
        """
        caption = (
            "📦 <b>UZBEKCHA ANIMELAR (ALPHA) — ENG SO'NGGI BAZA ZAXIRA ARXIVI</b> ⚡️✨\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏰ <b>Zaxira Vaqti:</b> <code>{now_display}</code>\n"
            f"🎬 <b>Jami Animelar:</b> <b>{stats.get('animes_count', 0)} ta</b>\n"
            f"🎞 <b>Jami Qismlar:</b> <b>{stats.get('episodes_count', 0)} ta (HD)</b>\n"
            f"👥 <b>Jami Foydalanuvchilar:</b> <b>{stats.get('users_count', 0)} ta</b>\n"
            f"📥 <b>Jami Yuklanishlar:</b> <b>{stats.get('total_downloads', 0)} ta</b>\n"
            f"👁 <b>Ko'rishlar Soni:</b> <b>{stats.get('total_views', 0)} ta</b>\n"
            "🍃 <b>Baza Holati:</b> 100% Jonli & Yangilangan (SQLite + Telegram Cloud Backup)\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🧹 <i>Eski zaxiralar avtomatik tozalandi. Bazada faqat eng so'nggi ma'lumotlar saqlanmoqda.</i>"
        )
        return caption

    async def send_backup(self, bot: Bot, delete_old: bool = True) -> bool:
        """
        Creates and delivers the latest database backup ZIP to the backup channel.
        Optionally deletes the previous backup message to keep the channel clean.
        """
        async with _BACKUP_LOCK:
            now_display = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            try:
                zip_bytes, zip_filename, stats = await self.create_backup_zip()
                caption = self.format_backup_caption(stats, now_display)
                input_file = BufferedInputFile(zip_bytes, filename=zip_filename)

                # 1. Delete old backup message if present
                if delete_old:
                    last_msg_id = await db.get_setting("last_backup_message_id")
                    if last_msg_id and str(last_msg_id).isdigit():
                        try:
                            await bot.delete_message(
                                chat_id=self.channel_id,
                                message_id=int(last_msg_id)
                            )
                            logger.info(f"Eski zaxira xabari o'chirildi: ID {last_msg_id}")
                        except Exception as del_err:
                            logger.debug(f"Eski zaxira xabarini o'chirishda ogohlantirish (e'tiborga olinmaydi): {del_err}")

                # 2. Send new backup document
                sent_msg = await bot.send_document(
                    chat_id=self.channel_id,
                    document=input_file,
                    caption=caption,
                    parse_mode="HTML"
                )

                # 3. Save new message ID and file ID in system settings
                if sent_msg.document:
                    await db.set_setting("last_backup_file_id", sent_msg.document.file_id)
                await db.set_setting("last_backup_message_id", str(sent_msg.message_id))
                await db.set_setting("last_backup_timestamp", str(datetime.now().timestamp()))
                self.last_backup_time = datetime.now().timestamp()

                logger.info(
                    f"✅ Zaxira muvaffaqiyatli yuborildi! Xabar ID: {sent_msg.message_id}, "
                    f"Fayl: {zip_filename} ({len(zip_bytes) / 1024:.1f} KB)"
                )
                return True

            except Exception as e:
                logger.error(f"Zaxirani @acacafagag kanaliga yuborishda xatolik: {e}", exc_info=True)
                return False

    async def restore_from_zip_bytes(self, zip_bytes: bytes) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Extracts and restores bot_database.db and anime_catalog.json from an in-memory ZIP.
        Disposes old DB connections, replaces files atomically, and re-inits DB.
        """
        async with _BACKUP_LOCK:
            try:
                mem = io.BytesIO(zip_bytes)
                with zipfile.ZipFile(mem, "r") as zf:
                    file_list = zf.namelist()
                    if "bot_database.db" not in file_list:
                        return False, "Arxiv ichida 'bot_database.db' fayli topilmadi!", {}

                    db_content = zf.read("bot_database.db")
                    catalog_content = zf.read("anime_catalog.json") if "anime_catalog.json" in file_list else None

                # 1. Close active database connections
                await db.close()

                # 2. Write database file atomically
                temp_db = _DB_PATH.with_suffix(".tmp")
                async with aiofiles.open(temp_db, "wb") as f:
                    await f.write(db_content)

                if temp_db.exists():
                    if _DB_PATH.exists():
                        try:
                            os.remove(_DB_PATH)
                        except Exception:
                            pass
                    os.replace(temp_db, _DB_PATH)

                # 3. Write catalog if present
                if catalog_content:
                    catalog_path = _BASE_DIR / "anime_catalog.json"
                    async with aiofiles.open(catalog_path, "wb") as f:
                        await f.write(catalog_content)

                # 4. Reconnect and re-init database
                await db.init_db()
                stats = await db.get_statistics()
                logger.info(f"✅ Baza muvaffaqiyatli tiklandi: {stats['animes_count']} ta anime, {stats['episodes_count']} ta qism.")
                return True, f"Baza muvaffaqiyatli tiklandi: {stats['animes_count']} ta anime, {stats['episodes_count']} ta qism", stats
            except Exception as e:
                logger.error(f"Zaxiradan tiklashda jiddiy xatolik: {e}", exc_info=True)
                return False, f"Xatolik: {e}", {}

    async def restore_latest_backup_if_needed(self, bot: Bot) -> bool:
        """
        Disaster Recovery / Auto-Restore:
        If bot_database.db does not exist or has 0 animes, attempts to find
        the latest backup from @acacafagag, download it, and restore the database.
        """
        # Check if local database already has data
        if _DB_PATH.exists() and _DB_PATH.stat().st_size > 4096:
            try:
                stats = await db.get_statistics()
                if stats["animes_count"] > 0:
                    logger.info(f"Lokal baza faol ({stats['animes_count']} ta anime, {stats['episodes_count']} ta qism). Tiklash talab etilmaydi.")
                    return True
            except Exception:
                pass

        logger.info("⚠️ Baza bo'sh yoki topilmadi. Zaxira kanalidan (@acacafagag) oxirgi arxiv tekshirilmoqda...")

        try:
            last_file_id = await db.get_setting("last_backup_file_id")
            if last_file_id:
                logger.info(f"Oxirgi zaxira fayli yuklab olinmoqda (File ID: {last_file_id})...")
                file_io = io.BytesIO()
                await bot.download(last_file_id, destination=file_io)
                ok, msg, stats = await self.restore_from_zip_bytes(file_io.getvalue())
                return ok
            return False
        except Exception as e:
            logger.warning(f"Zaxiradan avto-tiklashda ogohlantirish: {e}")
            return False

    async def start_periodic_backup_loop(self, bot: Bot, interval_minutes: int = 30) -> None:
        """
        Runs continuously in the background, executing a backup every 30 minutes.
        """
        logger.info(f"⏰ Avtomatik davriy zaxiralash faollashdi (Har {interval_minutes} daqiqada @acacafagag kanaliga).")
        # Sleep for a short delay on startup before first automated periodic backup
        await asyncio.sleep(60)

        while True:
            try:
                logger.info("Davriy zaxira yaratilmoqda...")
                await self.send_backup(bot=bot, delete_old=True)
            except Exception as e:
                logger.error(f"Davriy zaxira siklida xatolik: {e}")

            await asyncio.sleep(interval_minutes * 60)


# Global singleton instance
backup_service = BackupService()
