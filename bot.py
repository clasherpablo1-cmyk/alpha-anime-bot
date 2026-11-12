import sys
import os
import urllib.request
import urllib.parse
import traceback

def notify_cloud_early(text: str) -> None:
    try:
        token = os.environ.get("BOT_TOKEN", "8623305387:AAGAuI0_SfT1tVODQDpY6xz1NOw_y0AIirA")
        chat_id = os.environ.get("BACKUP_CHANNEL_ID", "-1003957205922")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": f"📡 [Render Early Boot]\n{text}"[:4000]
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"User-Agent": "RenderBoot/1.0"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

notify_cloud_early(f"🚀 bot.py boshlandi!\nPython: {sys.version.split()[0]}\nOS: {sys.platform}\nPORT: {os.environ.get('PORT', 'unset')}")

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import asyncio
    import logging
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
    notify_cloud_early("✅ Barcha modullar muvaffaqiyatli import qilindi!")
except Exception as imp_err:
    notify_cloud_early(f"❌ IMPORT XATOSI:\n{traceback.format_exc()}")
    raise

def notify_cloud_log(text: str) -> None:
    notify_cloud_early(text)
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

    # MongoDB Atlas Cloud Database initsializatsiyasi
    try:
        from database.mongo_manager import mongo_manager
        if mongo_manager.is_configured:
            connected = await mongo_manager.connect()
            if connected:
                # SQLite dan MongoDB Atlas ga barcha ma'lumotlarni sinxronlash
                asyncio.create_task(mongo_manager.sync_all_from_sqlite(db))
    except Exception as m_err:
        logger.warning(f"MongoDB Atlas initsializatsiyasida ogohlantirish: {m_err}")

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

    try:
        from database.mongo_manager import mongo_manager
        await mongo_manager.close()
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

    # 2. 24/7 Web Serverni fon rejimida birinchi bo'lib ishga tushirish (Render /health check darhol 200 berishi uchun)
    web_runner = None
    if config.WEB_SERVER_ENABLED:
        try:
            web_runner = await start_web_server(host=config.HOST, port=config.PORT)
            notify_cloud_log(f"✅ Web server ko'tarildi: {config.HOST}:{config.PORT}")
        except Exception as e:
            notify_cloud_log(f"❌ Web server xatosi: {e}")
            logger.error(f"Veb-serverni ishga tushirishda xatolik: {e}")

    # 3. Dastlabki ma'lumotlar bazasi va zaxira initsializatsiyasi (1 marta ishlaydi)
    try:
        await on_startup(bot)
        notify_cloud_log("✅ on_startup yakunlandi (DB & Cache tayyor).")
    except Exception as e:
        notify_cloud_log(f"❌ Startup initsializatsiyasida ogohlantirish: {e}")
        logger.error(f"Startup initsializatsiyasida ogohlantirish: {e}")

    # 4. Middlewares
    sub_middleware = SubscriptionCheckMiddleware()
    dp.message.middleware(sub_middleware)
    dp.callback_query.middleware(sub_middleware)

    # 5. Routerlarni ulash (Admin birinchi bo'lib tekshiriladi)
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # 6. Pollingni avto-tiklanish (Auto-Reconnect) va Render Blue-Green Conflict Guard bilan ishga tushirish
    from aiogram.exceptions import TelegramConflictError
    from aiogram.client.session.aiohttp import AiohttpSession

    # Eski to'planib qolgan webhook/xabarlarni tozalash (drop pending updates)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as dw_err:
        logger.debug(f"delete_webhook ogohlantirish: {dw_err}")

    try:
        while True:
            try:
                # Agar aiohttp sessiyasi kutilmaganda yopilgan bo'lsa
                if bot.session and getattr(bot.session, "_session", None) and bot.session._session.closed:
                    bot.session = AiohttpSession()

                logger.info("Telegram polling boshlanmoqda...")
                notify_cloud_log("⚡️ Telegram polling boshlanmoqda...")
                await dp.start_polling(
                    bot,
                    handle_signals=False,
                    close_bot_session=False
                )
                break
            except TelegramConflictError:
                notify_cloud_log("⚠️ TelegramConflictError ushlandi! 5 soniyada qayta uriniladi...")
                logger.warning("⚠️ Boshqa bot instansi hali faol (Render ko'chish jarayoni). 5 soniyadan so'ng qayta ulanadi...")
                await asyncio.sleep(5)
            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                notify_cloud_log(f"⚠️ Polling xatosi: {e}. 3s da qayta ulanadi...")
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
        notify_cloud_log(f"🟢 Render Container ishga tushdi!\nPython: {sys.version}\nOS: {sys.platform}\nPORT: {config.PORT}")
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
    except Exception as e:
        err_msg = traceback.format_exc()
        notify_cloud_log(f"❌ CRITICAL CRASH IN MAIN:\n{err_msg}")
        logger.critical(f"Botda halokatli xatolik: {err_msg}")
        sys.exit(1)
