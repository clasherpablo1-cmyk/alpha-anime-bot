#!/usr/bin/env python3
"""
==============================================================================
🔥 Alpha Anime Bot — 24/7 Self-Healing Supervisor / Watchdog
==============================================================================
Ushbu skript botni fonda uzluksiz kuzatib boradi.
Agar kutilmagan tarmoq uzilishi, xatolik yoki tizim qayta yuklanishi yuz bersa,
botni zudlik bilan qayta tiriltiradi (auto-restart).
"""

import sys
import time
import signal
import logging
import subprocess
from datetime import datetime

# Windows uchun UTF-8 sozlamasi
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [WATCHDOG 24/7] - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Watchdog247")

running = True
current_process = None


def signal_handler(sig, frame):
    global running, current_process
    logger.info("Watchdog to'xtatish signali qabul qilindi. Bot yopilmoqda...")
    running = False
    if current_process and current_process.poll() is None:
        current_process.terminate()
        try:
            current_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            current_process.kill()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def run_supervisor():
    global current_process, running
    logger.info("=" * 60)
    logger.info("🚀 24/7 ALPHA ANIME BOT SUPERVISOR ISHGA TUSHDI")
    logger.info(f"Boshlangan vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("Python talqini: " + sys.version.split()[0])
    logger.info("=" * 60)

    restart_count = 0
    last_restart_time = time.time()

    while running:
        logger.info(f"▶️ Bot ishga tushirilmoqda (Qayta yuklanishlar soni: {restart_count})...")
        start_time = time.time()

        try:
            # Botni alohida jarayonda ishga tushirish
            current_process = subprocess.Popen(
                [sys.executable, "bot.py"],
                stdout=None,
                stderr=None
            )
            current_process.wait()
            exit_code = current_process.returncode
        except Exception as e:
            logger.error(f"Botni ishga tushirishda xatolik: {e}")
            exit_code = -1

        run_duration = time.time() - start_time
        logger.warning(f"⚠️ Bot to'xtadi. Chiqish kodi: {exit_code}. Ishlagan vaqti: {int(run_duration)} soniya.")

        if not running:
            break

        restart_count += 1

        # Agar bot 10 soniyadan kam ishlab to'xtagan bo'lsa (rapid crash), ozroq kutish
        if run_duration < 10:
            logger.warning("Bot juda tez to'xtadi. Xatoliklar takrorlanmasligi uchun 5 soniya kutilmoqda...")
            time.sleep(5)
        else:
            time.sleep(2)

        logger.info("🔄 Bot qayta ishga tushirilmoqda...")


if __name__ == "__main__":
    run_supervisor()
