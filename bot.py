import asyncio
import logging
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import config
from database.db import db
from middlewares.subscription import SubscriptionCheckMiddleware
from handlers.admin import admin_router
from handlers.user import user_router

from services.web_server import start_web_server
from services.backup_service import backup_service

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AnimeBot")


async def on_startup(bot: Bot) -> None:
    logger.info("Ma'lumotlar bazasi initsializatsiya qilinmoqda...")
    await db.init_db()

    # Ephemeral hosting tiklash tekshiruvi (agar baza bo'sh bo'lsa @acacafagag dan tiklaydi)
    try:
        await backup_service.restore_latest_backup_if_needed(bot)
    except Exception as bkp_err:
        logger.warning(f"Zaxirani dastlabki tekshirishda ogohlantirish: {bkp_err}")

    # Avtomatik davriy zaxira siklini fonda ishga tushirish (har 30 daqiqada @acacafagag kanaliga)
    asyncio.create_task(
        backup_service.start_periodic_backup_loop(
            bot,
            interval_minutes=config.BACKUP_INTERVAL_MINUTES
        )
    )

    # Bot profili, kirish ekrani tavsifi va buyruqlarini avtomatik sozlash
    try:
        await bot.set_my_description(
            description=(
                "🎌 «Uzbekcha animelar» — O'zbekistondagi eng sara va yangi animelarni "
                "o'zbek tilida yuqori sifatda (HD) tomosha qilish uchun rasmiy bot!\n\n"
                "⚡️ Imkoniyatlar:\n"
                "• 1-klik bilan barcha qismlarni yuklab olish\n"
                "• Kod orqali bir zumda topish (#kod)\n"
                "• Eng mashhur animelar (Naruto, Solo Leveling, Mushoku Tensei...)\n"
                "• Tezkor yuklash va mutlaqo bepul!\n\n"
                "👇 Boshlash uchun pastdagi «Boshlash / Start» tugmasini bosing:"
            )
        )
        await bot.set_my_short_description(
            short_description="🎌 O'zbek tilidagi eng sara va yangi animelar boti. Yuqori sifat (HD) va tezkor tomosha!"
        )
        await bot.set_my_commands([
            BotCommand(command="start", description="Botni ishga tushirish"),
            BotCommand(command="help", description="Yordam va ma'lumot"),
            BotCommand(command="admin", description="Admin boshqaruv paneli")
        ])
        logger.info("Bot tavsiflari va komandalari muvaffaqiyatli o'rnatildi.")
    except Exception as e:
        logger.warning(f"Bot profilini yangilashda xatolik: {e}")

    bot_info = await bot.get_me()
    logger.info(f"Bot muvaffaqiyatli ishga tushdi: @{bot_info.username} (ID: {bot_info.id})")
    logger.info(f"Asosiy kanal: {config.CHANNEL_USERNAME}")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Bot to'xtatilmoqda...")
    try:
        logger.info("To'xtashdan oldin so'nggi zaxira @acacafagag kanaliga yuborilmoqda...")
        await backup_service.send_backup(bot, delete_old=True)
    except Exception as e:
        logger.warning(f"So'nggi zaxirani yuborishda ogohlantirish: {e}")

    try:
        await db.close()
    except Exception:
        pass
    await bot.session.close()


async def main() -> None:
    # 1. Bot va Dispatcher yaratish
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 2. Lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # 3. Middlewares
    sub_middleware = SubscriptionCheckMiddleware()
    dp.message.middleware(sub_middleware)
    dp.callback_query.middleware(sub_middleware)

    # 4. Routerlarni ulash (Admin birinchi bo'lib tekshiriladi)
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # 5. 24/7 Web Serverni fon rejimida ishga tushirish (Render, Koyeb, Railway, UptimeRobot uchun)
    web_runner = None
    if config.WEB_SERVER_ENABLED:
        try:
            web_runner = await start_web_server(host=config.HOST, port=config.PORT)
        except Exception as e:
            logger.error(f"Veb-serverni ishga tushirishda xatolik: {e}")

    # 6. Eski to'planib qolgan xabarlarni tozalash (drop pending updates)
    await bot.delete_webhook(drop_pending_updates=True)

    # 7. Pollingni avto-tiklanish (Auto-Reconnect) bilan ishga tushirish
    try:
        while True:
            try:
                logger.info("Telegram polling boshlanmoqda...")
                await dp.start_polling(bot, handle_signals=False)
                break
            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                logger.error(f"Tarmoq uzilishi: {e}. 3 soniyadan so'ng qayta ulanadi...")
                await asyncio.sleep(3)
    finally:
        if web_runner:
            try:
                await web_runner.cleanup()
                logger.info("Veb-server to'xtatildi.")
            except Exception as e:
                logger.warning(f"Veb-serverni tozalashda xatolik: {e}")
        await on_shutdown(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
