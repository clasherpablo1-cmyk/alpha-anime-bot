import asyncio
import time
import datetime
import logging
from typing import Optional
import aiohttp
from aiohttp import web

from config import config
from database.db import db

logger = logging.getLogger("AnimeWebServer")

START_TIME = time.time()


def get_uptime_seconds() -> int:
    """Bot ishga tushganidan beri o'tgan soniyalar"""
    return int(time.time() - START_TIME)


def get_uptime_human() -> str:
    """Inson o'qiy oladigan uptime formati"""
    total_seconds = get_uptime_seconds()
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} kun")
    if hours > 0:
        parts.append(f"{hours} soat")
    if minutes > 0:
        parts.append(f"{minutes} daq")
    parts.append(f"{seconds} soniya")
    return ", ".join(parts)


async def handle_health(request: web.Request) -> web.Response:
    """Render/Koyeb/Railway va UptimeRobot uchun JSON health tekshiruvi"""
    try:
        stats = await db.get_statistics()
    except Exception:
        stats = {"animes_count": 0, "episodes_count": 0, "users_count": 0, "total_views": 0}

    try:
        from database.mongo_manager import mongo_manager
        mongo_status = {
            "configured": mongo_manager.is_configured,
            "connected": mongo_manager._is_connected,
            "circuit_breaker": mongo_manager.circuit_breaker.get_status()
        }
    except Exception:
        mongo_status = {"configured": False, "connected": False}

    payload = {
        "status": "ok",
        "bot": config.BOT_USERNAME,
        "channel": config.CHANNEL_USERNAME,
        "uptime_seconds": get_uptime_seconds(),
        "uptime_human": get_uptime_human(),
        "database": stats,
        "mongodb": mongo_status,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    return web.json_response(payload, status=200)


async def handle_ping(request: web.Request) -> web.Response:
    """O'ta yengil ping tekshiruvi"""
    return web.json_response({"status": "pong", "time": time.time()}, status=200)


async def handle_dashboard(request: web.Request) -> web.Response:
    """Chiroyli dark-mode veb-dashboard"""
    try:
        stats = await db.get_statistics()
    except Exception:
        stats = {"animes_count": 0, "episodes_count": 0, "users_count": 0, "total_views": 0}

    uptime_str = get_uptime_human()

    html = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alpha Anime Bot — 24/7 Cloud Dashboard</title>
    <link rel="icon" href="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" type="image/png">
    <style>
        :root {{
            --bg-main: #0B0E14;
            --bg-card: #151922;
            --border: #232936;
            --primary: #FF2E93;
            --secondary: #00F0FF;
            --text-main: #F1F5F9;
            --text-muted: #94A3B8;
            --online: #10B981;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        body {{
            background-color: var(--bg-main);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 24px 16px;
            background-image: radial-gradient(circle at 50% 0%, rgba(255, 46, 147, 0.12) 0%, transparent 60%),
                              radial-gradient(circle at 100% 100%, rgba(0, 240, 255, 0.08) 0%, transparent 60%);
        }}
        .container {{
            max-width: 840px;
            width: 100%;
        }}
        .header {{
            text-align: center;
            margin-bottom: 32px;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--online);
            padding: 6px 16px;
            border-radius: 9999px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 16px;
            animation: pulse 2s infinite ease-in-out;
        }}
        .badge-dot {{
            width: 8px;
            height: 8px;
            background: var(--online);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--online);
        }}
        h1 {{
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(135deg, #FFF 30%, var(--text-muted) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: var(--text-muted);
            font-size: 16px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(255, 46, 147, 0.4);
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: 800;
            color: #FFF;
            margin-bottom: 4px;
        }}
        .stat-label {{
            font-size: 13px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .info-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 14px;
        }}
        .info-row:last-child {{
            border-bottom: none;
        }}
        .info-label {{
            color: var(--text-muted);
        }}
        .info-val {{
            font-weight: 600;
            color: #FFF;
        }}
        .actions {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 700;
            font-size: 14px;
            transition: all 0.2s ease;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, var(--primary), #D91B74);
            color: #FFF;
            box-shadow: 0 4px 20px rgba(255, 46, 147, 0.35);
        }}
        .btn-primary:hover {{
            box-shadow: 0 6px 25px rgba(255, 46, 147, 0.5);
            transform: translateY(-1px);
        }}
        .btn-secondary {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            color: var(--text-main);
        }}
        .btn-secondary:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}
        .footer {{
            margin-top: 32px;
            text-align: center;
            font-size: 13px;
            color: var(--text-muted);
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="badge">
                <span class="badge-dot"></span>
                24/7 ONLINE • TIZIM FAOLLASHTIRILGAN
            </div>
            <h1>🎌 Alpha Anime Bot Cloud</h1>
            <p class="subtitle">O'zbek tilidagi animelar ekotizimi uchun doimiy ishchi veb-server</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['animes_count']}</div>
                <div class="stat-label">🎬 Animelar</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['episodes_count']}</div>
                <div class="stat-label">🎞 Qismlar</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['users_count']}</div>
                <div class="stat-label">👥 Foydalanuvchilar</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['total_views']}</div>
                <div class="stat-label">👁 Ko'rishlar</div>
            </div>
        </div>

        <div class="info-card">
            <div class="info-row">
                <span class="info-label">🤖 Bot manzili</span>
                <span class="info-val">@{config.BOT_USERNAME}</span>
            </div>
            <div class="info-row">
                <span class="info-label">📢 Asosiy kanal</span>
                <span class="info-val">{config.CHANNEL_USERNAME}</span>
            </div>
            <div class="info-row">
                <span class="info-label">⏱ Uzluksiz ishlash vaqti (Uptime)</span>
                <span class="info-val" style="color: var(--online);">{uptime_str}</span>
            </div>
            <div class="info-row">
                <span class="info-label">⚡️ Veb monitoring (UptimeRobot / Health)</span>
                <span class="info-val"><a href="/health" style="color: var(--secondary); text-decoration: none;">/health (200 OK)</a></span>
            </div>
        </div>

        <div class="actions">
            <a href="https://t.me/{config.BOT_USERNAME}" target="_blank" class="btn btn-primary">
                🚀 Botga O'tish
            </a>
            <a href="{config.CHANNEL_URL}" target="_blank" class="btn btn-secondary">
                📢 Kanalga Qo'shilish
            </a>
            <a href="/health" target="_blank" class="btn btn-secondary">
                📊 JSON Health API
            </a>
        </div>

        <div class="footer">
            Alpha Anime Cloud Engine • clasherpablo4 • 24/7 Resilient Architecture
        </div>
    </div>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html", status=200)


async def start_self_ping_loop(url: Optional[str] = None, interval_seconds: int = 480) -> None:
    """Render.com 15 daqiqada uyquga (sleep) ketmasligi uchun o'z-o'ziga
    muntazam HTTP ping yuborib turuvchi mustaqil Keep-Alive mexanizmi."""
    target_url = url or "https://alpha-anime-bot.onrender.com/ping"
    logger.info(f"⏰ O'z-o'zini uyg'otib turuvchi Keep-Alive tsikli faollashdi: {target_url} (Har {interval_seconds}s)")
    
    # Server to'liq ko'tarilishi uchun boshida 90 soniya kutamiz
    await asyncio.sleep(90)
    
    while True:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(target_url) as resp:
                    if resp.status == 200:
                        logger.info(f"🟢 [SELF-KEEP-ALIVE OK] Server muvaffaqiyatli uyg'otildi: {target_url} (Status: 200)")
                    else:
                        logger.warning(f"🟡 [SELF-KEEP-ALIVE WARN] Server javobi: {resp.status} - {target_url}")
        except Exception as e:
            logger.debug(f"Self-ping xabari (qayta uriniladi): {e}")
        
        await asyncio.sleep(interval_seconds)


async def start_web_server(host: str = "0.0.0.0", port: int = 8080) -> web.AppRunner:
    """Aiohttp veb-serverini parallel fon rejimida ishga tushirish"""
    app = web.Application()
    app.router.add_get("/", handle_dashboard)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/ping", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    logger.info(f"🚀 24/7 Web Server muvaffaqiyatli ishga tushdi: http://{host}:{port}")
    logger.info(f"📊 Health Check endpointi faol: http://{host}:{port}/health")
    
    # 24/7 Sleep bo'lmasligi uchun avtomatik self-ping tsiklini ishga tushirish
    asyncio.create_task(start_self_ping_loop())
    
    return runner
