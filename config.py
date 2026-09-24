from typing import List, Set
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram bot API token")
    BOT_USERNAME: str = Field(default="Alpha_animelar_bot", description="Bot username")
    CHANNEL_USERNAME: str = Field(default="@uzbekcha_animelar_alpha", description="Asosiy kanal username")
    CHANNEL_URL: str = Field(default="https://t.me/uzbekcha_animelar_alpha", description="Asosiy kanal havolasi")
    
    ADMIN_IDS_RAW: str = Field(default="", alias="ADMIN_IDS", description="Vergul bilan ajratilgan admin ID lari")
    ADMIN_SECRET_KEY: str = Field(default="anime2026", description="Admin huquqini olish paroli")
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///bot_database.db", description="Database URI")
    
    # MongoDB Atlas Cloud Database sozlamalari
    MONGODB_URI: str = Field(default="", description="MongoDB Atlas Connection URI (cloud.mongodb.com)")
    MONGODB_DB_NAME: str = Field(default="AlphaAnimeBotDB", description="MongoDB Database nomi")

    # 24/7 Web Server & Cloud Hosting sozlamalari
    PORT: int = Field(default=8080, description="Cloud web server porti (Render, Koyeb, Railway)")
    HOST: str = Field(default="0.0.0.0", description="Web server hosti")
    WEB_SERVER_ENABLED: bool = Field(default=True, description="Veb-serverni faollashtirish")
    WEBHOOK_URL: str = Field(default="", description="Webhook URL (kerak bo'lganda)")

    # Telegram Cloud Zaxiralash (@acacafagag) sozlamalari
    BACKUP_CHANNEL_ID: str = Field(default="-1003957205922", description="Zaxira yuboriladigan kanal ID")
    BACKUP_INTERVAL_MINUTES: int = Field(default=30, description="Avtomatik zaxiralash oralig'i (daqiqa)")
    AUTO_RESTORE_ENABLED: bool = Field(default=True, description="Avtomatik tiklash imkoniyati")

    # AI Vision & Anime Reverse Search sozlamalari
    GEMINI_API_KEY: str = Field(default="", description="Gemini Multimodal Vision API kaliti")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def admin_ids(self) -> Set[int]:
        ids = set()
        if self.ADMIN_IDS_RAW:
            for item in self.ADMIN_IDS_RAW.split(","):
                cleaned = item.strip()
                if cleaned.isdigit():
                    ids.add(int(cleaned))
        return ids

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids


config = Settings()
