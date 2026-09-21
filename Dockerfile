# Production 24/7 Docker image for Alpha Anime Bot
FROM python:3.12-slim

# Muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    PORT=8080

# Kerakli tizim paketlari
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kutubxonalarni o'rnatish (Keshdan unumli foydalanish)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllarini ko'chirish
COPY . /app/

# Web server portini ochish
EXPOSE 8080

# Health check (Render/Koyeb/Docker tekshiruvi uchun)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Botni ishga tushirish
CMD ["python", "bot.py"]
